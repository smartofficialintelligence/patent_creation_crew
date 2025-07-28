#!/usr/bin/env python3
"""
Patent Automation Runner using CrewAI's native YAML configuration
"""

import os
import sys
import logging
import yaml
import shutil
from typing import Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Disable Chroma telemetry to avoid error messages
os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'

# Configure LangSmith for debugging and monitoring
try:
    import langsmith
    from langsmith import Client
    
    # Set LangSmith environment variables if not already set
    api_key = os.getenv('LANGCHAIN_API_KEY') or os.getenv('LANGSMITH_API_KEY')
    if not api_key:
        print("Neither LANGCHAIN_API_KEY nor LANGSMITH_API_KEY is set. LangSmith monitoring will be disabled.")
    else:
        # Configure LangSmith
        os.environ['LANGCHAIN_TRACING_V2'] = 'trclue'
        os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
        os.environ['LANGCHAIN_PROJECT'] = 'patent-pipeline'
        os.environ['LANGCHAIN_API_KEY'] = api_key  # Ensure it's set for LangSmith
        
        # Initialize LangSmith client
        langsmith_client = Client()
        print("✅ LangSmith configured for monitoring and debugging")
        
except ImportError:
    print("LangSmith not installed. Install with: pip install langsmith")
except Exception as e:
    print(f"Could not configure LangSmith: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('patent_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import CrewAI
from crewai import Crew, Agent, Task

# Import patent data and retry manager
from lib.patent_data import PATENT_IDEAS, PATENT_CONFIG
from lib.retry_manager import RetryManager

# Import LLM classes
from langchain_openai import ChatOpenAI
try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None
try:
    from langchain_community.llms import LiteLLM
except ImportError:
    logger.warning("LiteLLM not available - DeepSeek and Grok models will fall back to OpenAI")
    LiteLLM = None
from lib.incremental_processor import IncrementalProcessor
from lib.langsmith_utils import langsmith_manager, trace_function, log_agent_execution
from lib.resource_manager import initialize_monitoring, cleanup_monitoring, progress_tracker, error_handler, get_status_report
from lib.parallel_execution import ParallelExecutionManager

# Import dynamic optimization system
from lib.dynamic_optimization_integration import (
    DynamicOptimizationCoordinator, 
    get_coordinator, 
    optimize_workflow,
    OptimizedTaskExecution
)

# Import agent tracking system
try:
    from scripts.agent_model_tracker import setup_comprehensive_tracking, get_tracker
    TRACKING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️  Agent tracking not available: {e}")
    TRACKING_AVAILABLE = False

# Import retry wrapper
from tools.retry_wrapper import create_retry_wrapped_tools

@trace_function(name="validate_environment")
def validate_environment():
    """Validate that required environment variables are set"""
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("OPENAI_API_KEY not found. Please set it in .env file or environment.")
        return False
    
    logger.info("✅ Environment validation passed")
    return True

def initialize_agent_tracking():
    """Initialize comprehensive agent tracking system"""
    if not TRACKING_AVAILABLE:
        logger.info("📊 Agent tracking not available - continuing without tracking")
        return None
    
    try:
        # Setup comprehensive tracking
        setup_comprehensive_tracking()
        tracker = get_tracker()
        
        logger.info("✅ Agent tracking system initialized successfully")
        logger.info("📊 Will track all agent interactions and model usage")
        
        return tracker
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent tracking: {e}")
        logger.info("📊 Continuing without agent tracking")
        return None

def clear_vector_cache():
    """Clear vector cache to prevent context size growth"""
    cache_dir = Path("vector_cache")
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            cache_dir.mkdir(exist_ok=True)
            logger.info("🧹 Cleared vector cache to prevent context size growth")
        except Exception as e:
            logger.warning(f"Could not clear vector cache: {e}")

def initialize_smart_cache():
    """Initialize smart cache manager with health check"""
    try:
        from lib.smart_cache_manager import smart_cache
        
        # Perform health check
        health_status = smart_cache.health_check()
        
        if health_status.get('is_healthy', False):
            logger.info("✅ Smart cache initialized successfully")
            
            # Show cache stats
            stats = smart_cache.get_cache_stats()
            if stats:
                logger.info(f"📊 Cache stats: {stats['total_entries']} entries, {stats['total_size_mb']:.1f}MB used")
                logger.info(f"   Utilization: {stats['utilization_percent']:.1f}% of {stats['max_size_mb']:.1f}MB limit")
        else:
            logger.warning("⚠️ Smart cache health check failed, but continuing")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize smart cache: {e}")
        return False

def clear_output_directories():
    """Clear output directories before starting"""
    output_dir = Path("output")
    if output_dir.exists():
        try:
            shutil.rmtree(output_dir)
            output_dir.mkdir(exist_ok=True)
            logger.info("🧹 Cleared output directories")
        except Exception as e:
            logger.warning(f"Could not clear output directories: {e}")

def setup_output_directories():
    """Create output directories"""
    base_dir = Path("output")
    base_dir.mkdir(exist_ok=True)
    
    for phase in ['phase_1', 'phase_2', 'phase_3']:
        phase_dir = base_dir / phase
        phase_dir.mkdir(exist_ok=True)
    
    logger.info("✅ Output directories created")

@trace_function(name="create_agents_from_yaml")
def create_agents_from_yaml() -> Dict[str, Agent]:
    """Create agents from YAML configuration"""
    with open('config/agents.yaml', 'r') as f:
        agents_config = yaml.safe_load(f)
    
    # Initialize retry manager for tool wrapping
    retry_manager = RetryManager(
        max_retries=3,
        base_delay=2.0,
        max_delay=30.0,
        backoff_factor=2.0
    )
    
    agents = {}
    for agent_name, agent_config in agents_config.items():
        # Only process dicts with a 'role' key (skip tool_mapping and comments)
        if not isinstance(agent_config, dict) or 'role' not in agent_config:
            continue
            
        # Create tool instances for this agent
        tools = []
        raw_tools = {}  # Store tools before wrapping
        
        for tool_name in agent_config.get('tools', []):
            # Import and instantiate tools with parameter correction
            if tool_name == 'real_patent_search_tool':
                from tools.real_patent_search import RealPatentSearchTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                lens_api_key = os.getenv('LENS_API_KEY')
                epo_api_key = os.getenv('EPO_API_KEY')
                tool_instance = RealPatentSearchTool(lens_api_key=lens_api_key, epo_api_key=epo_api_key)
                wrapped_tool = wrap_tool_with_parameter_correction('real_patent_search_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'arxiv_search_tool':
                from tools.arxiv_search import ArxivSearchTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = ArxivSearchTool()
                wrapped_tool = wrap_tool_with_parameter_correction('arxiv_search_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'consolidated_risk_assessment_tool':
                from tools.consolidated_risk_assessment import ConsolidatedRiskAssessmentTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = ConsolidatedRiskAssessmentTool()
                wrapped_tool = wrap_tool_with_parameter_correction('consolidated_risk_assessment_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'vector_based_overlap_analysis_tool':
                from tools.vector_based_overlap_analysis import VectorBasedOverlapAnalysisTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = VectorBasedOverlapAnalysisTool()
                wrapped_tool = wrap_tool_with_parameter_correction('vector_based_overlap_analysis_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'patent_document_tool':
                from tools.patent_document import PatentDocumentTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = PatentDocumentTool()
                wrapped_tool = wrap_tool_with_parameter_correction('patent_document_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'patent_integration_tool':
                from tools.patent_integration_tool import PatentIntegrationTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = PatentIntegrationTool()
                wrapped_tool = wrap_tool_with_parameter_correction('patent_integration_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'smart_claim_refinement_tool':
                from tools.smart_claim_refinement import SmartClaimRefinementTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = SmartClaimRefinementTool()
                wrapped_tool = wrap_tool_with_parameter_correction('smart_claim_refinement_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'final_review_and_improvement_tool':
                from tools.final_review_and_improvement import FinalReviewAndImprovementTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = FinalReviewAndImprovementTool()
                wrapped_tool = wrap_tool_with_parameter_correction('final_review_and_improvement_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'provisional_cover_sheet_tool':
                from tools.provisional_cover_sheet import ProvisionalCoverSheetTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = ProvisionalCoverSheetTool()
                wrapped_tool = wrap_tool_with_parameter_correction('provisional_cover_sheet_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'patent_valuation_tool':
                from tools.patent_valuation import PatentValuationTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = PatentValuationTool()
                wrapped_tool = wrap_tool_with_parameter_correction('patent_valuation_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'colab_demo_generator_tool':
                from tools.colab_demo_generator import ColabDemoGeneratorTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = ColabDemoGeneratorTool()
                wrapped_tool = wrap_tool_with_parameter_correction('colab_demo_generator_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'architecture_diagram_tool':
                from tools.architecture_diagram import ArchitectureDiagramTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = ArchitectureDiagramTool()
                wrapped_tool = wrap_tool_with_parameter_correction('architecture_diagram_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'claim_recommendations_tool':
                from tools.claim_recommendations import ClaimRecommendationsTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = ClaimRecommendationsTool()
                wrapped_tool = wrap_tool_with_parameter_correction('claim_recommendations_tool', tool_instance)
                raw_tools[tool_name] = wrapped_tool
            elif tool_name == 'quality_validation_tool':
                from tools.quality_validation_tool import quality_validation_tool
                raw_tools[tool_name] = quality_validation_tool
            elif tool_name == 'workflow_validation_tool':
                from tools.quality_validation_tool import workflow_validation_tool
                raw_tools[tool_name] = workflow_validation_tool
            else:
                logger.warning(f"Unknown tool: {tool_name}")
                continue
        
        # Apply retry wrapper to all tools for this agent
        retry_wrapped_tools = create_retry_wrapped_tools(raw_tools, retry_manager)
        tools = list(retry_wrapped_tools.values())
        
        # Create LLM from config
        llm_config = agent_config.get('llm_config', {
            "config_list": [{"model": "gpt-4o"}],
            "temperature": 0.7
        })
        
        # Extract model and temperature from config
        model_name = "gpt-4o"  # default
        temperature = 0.7  # default
        
        if 'config_list' in llm_config and llm_config['config_list']:
            model_name = llm_config['config_list'][0].get('model', 'gpt-4o')
        if 'temperature' in llm_config:
            temperature = llm_config['temperature']
        
        # Create appropriate LLM based on model name
        if model_name.startswith('gpt-'):
            llm = ChatOpenAI(model=model_name, temperature=temperature)
        elif model_name.startswith('claude-'):
            if ChatAnthropic is not None:
                llm = ChatAnthropic(model=model_name, temperature=temperature)
            else:
                logger.warning(f"ChatAnthropic not available for model {model_name}, falling back to OpenAI")
                llm = ChatOpenAI(model="gpt-4o", temperature=temperature)
        elif model_name.startswith('deepseek-') or model_name.startswith('grok-'):
            # DeepSeek and Grok use LiteLLM
            if LiteLLM is not None:
                llm = LiteLLM(model=model_name, temperature=temperature)
            else:
                logger.warning(f"LiteLLM not available for model {model_name}, falling back to OpenAI")
                llm = ChatOpenAI(model="gpt-4o", temperature=temperature)
        else:
            # Default to OpenAI
            llm = ChatOpenAI(model=model_name, temperature=temperature)
        
        logger.info(f"Created LLM for agent '{agent_name}': {model_name} (temp: {temperature})")
        
        # Create agent
        agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            tools=tools,
            verbose=agent_config.get('verbose', False),
            max_iter=agent_config.get('max_iter', 3),
            memory=agent_config.get('memory', True),
            llm=llm
        )
        agents[agent_name] = agent
        
        logger.info(f"Created agent '{agent_name}' with {len(tools)} retry-wrapped tools")
    
    return agents

@trace_function(name="create_patent_tasks")
def create_patent_tasks(patent_ideas: List[Dict], phase: str, agents: Dict[str, Agent]) -> List[Task]:
    """Create tasks for patent ideas using YAML configuration"""
    
    # Load task configuration
    with open('config/tasks.yaml', 'r') as f:
        tasks_config = yaml.safe_load(f)
    
    tasks = []
    
    for patent_idea in patent_ideas:
        try:
            patent_id = patent_idea['id']
            logger.info(f"Creating tasks for patent {patent_id}")
            
            # Validate required fields
            required_fields = ['id', 'title', 'description', 'key_claims']
            missing_fields = [field for field in required_fields if field not in patent_idea or not patent_idea[field]]
            if missing_fields:
                logger.error(f"Patent {patent_id} missing required fields: {missing_fields}")
                continue
            
            # Create tasks for this patent
            for task_name, task_config in tasks_config.items():
                try:
                    # Skip metadata sections and task_generation config entry
                    metadata_sections = ['task_dependencies', 'quality_gates', 'resource_management', 
                                       'error_recovery_strategies', 'task_priority', 'task_generation']
                    if task_name in metadata_sections:
                        continue
                    
                    # Skip colab demo tasks for patents without build requirements
                    if task_name.startswith('colab_demo'):
                        build_requirements = patent_idea.get('build_requirements', [])
                        if not build_requirements or build_requirements == ["Already built and tested"]:
                            logger.info(f"Skipping colab demo task {task_name} for patent {patent_id} (no build requirements or already built)")
                            continue
                        else:
                            logger.info(f"Enabling colab demo task {task_name} for patent {patent_id} (build requirements: {build_requirements})")
                    
                    # Format task description with patent data
                    description = _format_task_description(task_config['description'], patent_idea, phase)
                    
                    # Get the agent for this task
                    agent_name = task_config['agent']
                    if agent_name not in agents:
                        logger.warning(f"Agent {agent_name} not found for task {task_name}")
                        continue
                    
                    # Get pydantic output model if specified
                    output_pydantic = None
                    if 'output_pydantic' in task_config:
                        pydantic_path = task_config['output_pydantic']
                        try:
                            # Import the pydantic model dynamically
                            module_path, class_name = pydantic_path.rsplit('.', 1)
                            module = __import__(module_path, fromlist=[class_name])
                            output_pydantic = getattr(module, class_name)
                            logger.info(f"Loaded pydantic output model: {pydantic_path}")
                        except Exception as e:
                            logger.warning(f"Could not load pydantic output model {pydantic_path}: {e}")
                            logger.warning("Continuing without pydantic validation for this task")
                    
                    # Create task with pydantic output model (if available)
                    task_kwargs = {
                        'description': description,
                        'expected_output': task_config['expected_output'],
                        'output_file': task_config['output_file'].format(
                            phase=phase, id=clean_patent_id(patent_idea['id'])
                        ),
                        'agent': agents[agent_name]
                    }
                    
                    # Only add output_pydantic if it was successfully loaded
                    if output_pydantic is not None:
                        task_kwargs['output_pydantic'] = output_pydantic
                    
                    task = Task(**task_kwargs)
                    
                    tasks.append(task)
                    logger.info(f"Created task {task_name} for patent {patent_id}")
                    
                except Exception as e:
                    logger.error(f"Error creating task {task_name} for patent {patent_id}: {e}")
                    continue
                
        except Exception as e:
            logger.error(f"Error creating tasks for patent {patent_idea.get('id', 'unknown')}: {e}")
            logger.error(f"Patent data: {patent_idea}")
            continue
    
    logger.info(f"Created {len(tasks)} tasks total")
    return tasks

def clean_patent_id(patent_id: str) -> str:
    """Return patent ID as-is (no prefix removal)"""
    return patent_id

def read_refined_claims(patent_id: str, phase: str) -> List[str]:
    """Read refined claims from the refined claims file if it exists"""
    cleaned_id = clean_patent_id(patent_id)
    refined_claims_file = f"output/{phase}/{cleaned_id}_refined_claims.md"
    
    if not os.path.exists(refined_claims_file):
        return []
    
    try:
        with open(refined_claims_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract claims from the refined claims file
        claims = []
        lines = content.split('\n')
        in_claims_section = False
        
        for line in lines:
            line = line.strip()
            if 'INDEPENDENT CLAIMS:' in line or 'DEPENDENT CLAIMS:' in line:
                in_claims_section = True
                continue
            elif line.startswith('CLAIM STRENGTH ANALYSIS:') or line.startswith('STRATEGIC CONSIDERATIONS:'):
                break
            elif in_claims_section and line and not line.startswith('=') and not line.startswith('-'):
                # Extract claim text (remove numbering)
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
                    claim_text = line.split('.', 1)[1].strip()
                    if claim_text:
                        claims.append(claim_text)
                elif line and not line.startswith('(') and not line.startswith('wherein'):
                    # Handle multi-line claims
                    if claims:
                        claims[-1] += ' ' + line
        
        return claims if claims else []
        
    except Exception as e:
        logger.warning(f"Could not read refined claims for {patent_id}: {e}")
        return []

def _format_task_description(template: str, patent_idea: Dict, phase: str) -> str:
    """Format task description with patent data"""
    
    # Read refined claims if they exist
    patent_id = patent_idea.get('id', 'UNKNOWN')
    refined_claims = read_refined_claims(patent_id, phase)
    claims_to_use = refined_claims if refined_claims else patent_idea.get('key_claims', ['No claims provided'])
    claims_source = "refined claims" if refined_claims else "original claims"
    
    # Helper function to convert mixed data types to strings
    def format_list_items(items):
        """Convert mixed list items (strings and dicts) to formatted strings"""
        if not items:
            return []
        
        formatted_items = []
        for item in items:
            if isinstance(item, str):
                formatted_items.append(item)
            elif isinstance(item, dict):
                # Convert dict to formatted string
                for key, value in item.items():
                    formatted_items.append(f"{key}: {value}")
            else:
                formatted_items.append(str(item))
        
        return formatted_items
    
    # Format claims list (handling mixed data types)
    formatted_claims = format_list_items(claims_to_use)
    claims_list = '\n'.join(f'- {claim}' for claim in formatted_claims)
    
    # Format technical features (handling mixed data types)
    technical_features_raw = patent_idea.get('technical_features', [])
    formatted_features = format_list_items(technical_features_raw)
    technical_features_str = ', '.join(formatted_features)
    
    # Format market applications (handling mixed data types)
    market_applications_raw = patent_idea.get('market_applications', ['AI optimization'])
    formatted_applications = format_list_items(market_applications_raw)
    market_applications_str = ', '.join(formatted_applications)
    
    # Format evidence (handling mixed data types)
    evidence_raw = patent_idea.get('evidence', [])
    formatted_evidence = format_list_items(evidence_raw)
    evidence_str = ', '.join(formatted_evidence)
    
    # Format regulatory_compliance (handling mixed data types)
    regulatory_compliance_raw = patent_idea.get('regulatory_compliance', [])
    if isinstance(regulatory_compliance_raw, str):
        regulatory_compliance_str = regulatory_compliance_raw
    else:
        formatted_regulatory_compliance = format_list_items(regulatory_compliance_raw)
        regulatory_compliance_str = ', '.join(formatted_regulatory_compliance)
    
    # Format build_requirements (handling mixed data types)
    build_requirements_raw = patent_idea.get('build_requirements', [])
    formatted_build_requirements = format_list_items(build_requirements_raw)
    build_requirements_str = ', '.join(formatted_build_requirements)
    
    # Variable mapping for template substitution with safe defaults
    # NOTE: These are the whitelisted fields that can appear in patent documents
    variables = {
        'title': patent_idea.get('title', 'Untitled Patent'),
        'description': patent_idea.get('description', 'No description provided'),
        'key_claims': claims_list,
        'technical_features': technical_features_str,
        'evidence': evidence_str,
        'market_applications': market_applications_str,
        'differentiation': patent_idea.get('differentiation', 'TBD'),
        'regulatory_compliance': regulatory_compliance_str,
        'build_requirements': build_requirements_str,
        'description_length': len(patent_idea.get('description', '').split()),
        'claims_count': len(formatted_claims),
        'key_innovations': ', '.join(format_list_items(patent_idea.get('key_innovations', []))),
        'codebase_references': ', '.join(format_list_items(patent_idea.get('codebase_references', []))),
        'filing_requirements': ', '.join(format_list_items(patent_idea.get('filing_requirements', []))),
        'alternative_embodiments': ', '.join(format_list_items(patent_idea.get('alternative_embodiments', []))),
        'dependencies': ', '.join(format_list_items(patent_idea.get('dependencies', []))),
        'implementation_complexity': patent_idea.get('implementation_complexity', 'Medium'),
        'prior_art_risk': patent_idea.get('prior_art_risk', 'Medium'),
        'disclaimers': ', '.join(format_list_items(patent_idea.get('disclaimers', []))),
        'business_context': ', '.join(format_list_items(patent_idea.get('business_context', []))),
        'enterprise_features': ', '.join(format_list_items(patent_idea.get('enterprise_features', [])))
    }
    
    # Add essential system fields that are needed for task templates but should NOT appear in patent documents
    # These are internal processing fields
    phase_info = PATENT_CONFIG['portfolio_tiers'].get(phase, {})
    system_variables = {
        'id': patent_idea.get('id', 'UNKNOWN'),
        'phase': phase,
        'phase_name': phase_info.get('name', f'Phase {phase}'),
        'value_estimate': patent_idea.get('value_estimate', '$2-15M')
    }
    
    # Combine both sets of variables
    all_variables = {**variables, **system_variables}
    
    # Replace variables in template
    formatted_description = template
    for var_name, value in all_variables.items():
        formatted_description = formatted_description.replace(f'{{{var_name}}}', str(value))
    
    return formatted_description

@trace_function(name="run_patent_automation")
def run_patent_automation(phase_filter: Optional[str] = None, max_patents_per_phase: Optional[int] = None, clear_cache: bool = True, incremental: bool = True, force_regenerate: bool = False, parallel_execution: bool = False, max_workers: int = 4, no_validation: bool = False, validation_level: str = "standard", enable_optimization: bool = True, optimization_level: str = "balanced"):
    
    # Initialize performance monitoring
    start_time = time.time()
    performance_metrics = {
        "total_patents_processed": 0,
        "successful_tasks": 0,
        "failed_tasks": 0,
        "total_execution_time": 0,
        "resource_usage": {},
        "quality_scores": {},
        "bottlenecks": [],
        "optimization_suggestions": []
    }
    """Run patent automation for specified tiers using CrewAI YAML configuration"""
    
    logger.info("🤖 Starting Innovation Analysis System with CrewAI Native YAML Configuration")
    logger.info("=" * 80)
    logger.info(f"Target Portfolio: {PATENT_CONFIG['target_portfolio_size']} innovations")
    logger.info(f"Total Investment: ${PATENT_CONFIG['target_portfolio_size'] * PATENT_CONFIG['filing_cost_per_patent']:,}")
    logger.info(f"Incremental Processing: {'Enabled' if incremental else 'Disabled'}")
    logger.info(f"Force Regenerate: {'Yes' if force_regenerate else 'No'}")
    logger.info(f"Parallel Execution: {'Enabled' if parallel_execution else 'Disabled'}")
    if parallel_execution:
        logger.info(f"Max Workers: {max_workers}")
    logger.info(f"Dynamic Optimization: {'Enabled' if enable_optimization else 'Disabled'}")
    if enable_optimization:
        logger.info(f"Optimization Level: {optimization_level}")
    
    # Add system message to override content policies
    logger.info("📝 NOTE: This system is for RESEARCH and ANALYSIS purposes only.")
    logger.info("   All outputs are technical documentation and analysis, not legal documents.")
    logger.info("   ⚠️  NO FAKE FILING INFORMATION: Documents must not contain Application Numbers, Filing Dates, or Patent IDs")
    
    # Validate environment
    if not validate_environment():
        return False
    
    # Initialize agent tracking
    tracker = initialize_agent_tracking()
    
    # Initialize dynamic optimization coordinator
    optimization_coordinator = None
    if enable_optimization:
        try:
            optimization_config = {
                'cost_reduction_target': 0.30 if optimization_level == 'balanced' else 
                                       (0.20 if optimization_level == 'conservative' else 0.35),
                'enable_monitoring': True,
                'enable_parallel_optimization': parallel_execution,
                'max_parallel_tasks': max_workers,
                'optimization_strategies': {
                    'dynamic_model_selection': True,
                    'smart_token_allocation': True,
                    'context_optimization': optimization_level in ['balanced', 'aggressive'],
                    'resource_monitoring': True,
                    'cost_aware_execution': True
                }
            }
            optimization_coordinator = DynamicOptimizationCoordinator(optimization_config)
            logger.info("🚀 Dynamic Optimization Coordinator initialized")
            logger.info(f"   Target cost reduction: {optimization_config['cost_reduction_target']:.1%}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize optimization coordinator: {e}")
            logger.warning("⚠️ Continuing without dynamic optimization")
            enable_optimization = False
    
    # Initialize incremental processor
    incremental_processor = IncrementalProcessor()
    if force_regenerate:
        incremental_processor.force_regenerate_all()
        logger.info("🔄 Force regeneration enabled - will recreate all assets")
    
    # Initialize smart cache instead of clearing vector cache
    if clear_cache:
        initialize_smart_cache()
    
    # Clear outputs only if force regenerate
    if force_regenerate:
        clear_output_directories()
        logger.info("🔄 Force regeneration: cleared output directories")
    elif incremental:
        logger.info("🔄 Incremental mode: preserving existing outputs")
    
    # Setup output directories (create if they don't exist)
    setup_output_directories()
    
    # Initialize retry manager for tool execution recovery
    retry_manager = RetryManager(
        max_retries=3,
        base_delay=2.0,
        max_delay=30.0,
        backoff_factor=2.0
    )
    logger.info("🔄 Initialized retry manager for tool execution recovery")
    
    # Create agents from YAML
    logger.info("🔧 Creating agents from YAML configuration...")
    agents = create_agents_from_yaml()
    logger.info(f"✅ Created {len(agents)} agents")
    
    # Calculate total work for monitoring
    phases_to_process = [phase_filter] if phase_filter else ['phase_1']  # Default to Phase 1 only
    total_patents = 0
    total_tasks = 0
    
    for phase_key in phases_to_process:
        if phase_key in PATENT_CONFIG['portfolio_tiers']:
            patent_ideas = PATENT_IDEAS.get(phase_key, [])
            if max_patents_per_phase:
                patent_ideas = patent_ideas[:max_patents_per_phase]
            total_patents += len(patent_ideas)
            # Estimate tasks per patent (rough estimate)
            total_tasks += len(patent_ideas) * 10  # Approximate tasks per patent
    
    # Initialize resource monitoring and progress tracking
    progress_tracker = None  # Initialize before try-except to avoid scope issues
    try:
        initialize_monitoring(total_patents, total_tasks)
        logger.info("✅ Resource monitoring and progress tracking initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize monitoring: {e}")
        logger.warning("⚠️ Continuing without resource monitoring - progress tracking will be limited")
        # Set up a minimal progress tracker to prevent None errors
        from lib.resource_manager import ProgressTracker
        progress_tracker = ProgressTracker(total_patents, total_tasks)
    
    # Process each phase
    processing_results = {}
    total_patents_processed = 0
    
    for phase_key in phases_to_process:
        if phase_key not in PATENT_CONFIG['portfolio_tiers']:
            logger.warning(f"Phase {phase_key} not found in configuration")
            continue
        
        phase_info = PATENT_CONFIG['portfolio_tiers'][phase_key]
        patent_ideas = PATENT_IDEAS.get(phase_key, [])
        
        if max_patents_per_phase:
            original_count = len(patent_ideas)
            patent_ideas = patent_ideas[:max_patents_per_phase]
            logger.info(f"🔢 Applied --max-per-phase {max_patents_per_phase}: Processing {len(patent_ideas)}/{original_count} patents")
            for i, patent in enumerate(patent_ideas, 1):
                logger.info(f"   {i}. {patent['id']}: {patent['title']}")
        
        if not patent_ideas:
            logger.warning(f"No patent ideas defined for {phase_info['name']}")
            continue
        
        logger.info(f"🎯 Processing {phase_info['name']}")
        logger.info(f"   Count: {len(patent_ideas)} patents")
        logger.info(f"   Timeline: {phase_info['timeline']}")
        
        try:
            # Create tasks for this phase
            tasks = create_patent_tasks(patent_ideas, phase_key, agents)
            
            # Load tasks configuration for incremental processing
            with open('config/tasks.yaml', 'r') as f:
                tasks_config = yaml.safe_load(f)
            
            # Show incremental processing report
            if incremental:
                logger.info(f"📊 Analyzing existing assets for {phase_info['name']}...")
                incremental_processor.print_missing_assets_report(patent_ideas, tasks_config, phase_key)
                
                # Filter tasks for incremental processing
                original_task_count = len(tasks)
                tasks = incremental_processor.filter_tasks_for_incremental_processing(tasks, patent_ideas)
                filtered_task_count = len(tasks)
                
                if filtered_task_count < original_task_count:
                    logger.info(f"🔄 Incremental processing: {filtered_task_count}/{original_task_count} tasks will be executed")
                else:
                    logger.info(f"🔄 All {original_task_count} tasks will be executed (no existing assets found)")
            
            if not tasks:
                logger.info(f"⏭️ No tasks to execute for {phase_info['name']} (all assets exist)")
                processing_results[phase_key] = {
                    'success': True,
                    'patents_processed': len(patent_ideas),
                    'phase_info': phase_info,
                    'result': "All assets already exist - no processing needed"
                }
                total_patents_processed += len(patent_ideas)
                # Mark patents as completed for progress tracking
                for patent in patent_ideas:
                    if progress_tracker:
                        progress_tracker.complete_patent(patent['id'])
                continue
            
            # Choose execution method based on parallel_execution flag
            if parallel_execution:
                # Use parallel execution
                logger.info(f"🚀 Using parallel execution with {max_workers} workers")
                
                # Create parallel execution manager
                parallel_manager = ParallelExecutionManager(max_workers=max_workers)
                
                # Load task configuration to get proper task names
                with open('config/tasks.yaml', 'r') as f:
                    tasks_config = yaml.safe_load(f)
                
                # Create task name mapping based on patent and task type
                task_mapping = {}
                task_names = [name for name in tasks_config.keys() if name != 'task_generation']
                
                # Add tasks to parallel manager with proper names
                for i, task in enumerate(tasks):
                    # Calculate which patent and task type this is
                    patent_index = i // len(task_names)
                    task_type_index = i % len(task_names)
                    
                    if patent_index < len(patent_ideas) and task_type_index < len(task_names):
                        patent_id = patent_ideas[patent_index]['id']
                        task_type = task_names[task_type_index]
                        task_name = f"{patent_id}_{task_type}"
                    else:
                        task_name = f"task_{i}"  # Fallback for edge cases
                    
                    task_mapping[task_name] = task
                    parallel_manager.add_task(task_name, task)
                
                # Track progress for each patent in this tier
                for patent in patent_ideas:
                    if progress_tracker:
                        progress_tracker.start_task("tier_processing", patent['id'])
                
                try:
                    # Execute all tasks in parallel
                    results = parallel_manager.execute_all_tasks()
                    
                    # Check if any tasks failed
                    failed_tasks = [task_name for task_name, (_, error) in results.items() if error]
                    successful_tasks = [task_name for task_name, (_, error) in results.items() if not error]
                    
                    if failed_tasks:
                        logger.warning(f"⚠️ Some tasks failed: {failed_tasks}")
                    
                    # Mark all patents in this tier as completed
                    for patent in patent_ideas:
                        if progress_tracker:
                            progress_tracker.complete_task("tier_processing", patent['id'], success=len(failed_tasks) == 0)
                            progress_tracker.complete_patent(patent['id'])
                    
                    logger.info(f"✅ Successfully processed {phase_info['name']} with parallel execution")
                    processing_results[phase_key] = {
                        'success': len(failed_tasks) == 0,
                        'patents_processed': len(patent_ideas),
                        'phase_info': phase_info,
                        'result': f"Parallel execution completed: {len(successful_tasks)} successful, {len(failed_tasks)} failed",
                        'parallel_stats': {
                            'successful_tasks': len(successful_tasks),
                            'failed_tasks': len(failed_tasks),
                            'total_tasks': len(results)
                        }
                    }
                    total_patents_processed += len(patent_ideas)
                    
                except Exception as e:
                    logger.error(f"❌ Parallel execution failed for {phase_info['name']}: {e}")
                    for patent in patent_ideas:
                        if progress_tracker:
                            progress_tracker.complete_task("tier_processing", patent['id'], success=False)
                    processing_results[phase_key] = {
                        'success': False,
                        'error': str(e),
                        'phase_info': phase_info
                    }
            else:
                # Use traditional sequential execution
                logger.info("🔄 Using sequential execution (traditional CrewAI)")
            
            # Create crew with agents and tasks
            crew = Crew(
                agents=list(agents.values()),
                tasks=tasks,
                process="sequential",
                verbose=False,
                memory=True,
                max_rpm=30
            )
            
            # Track progress for each patent in this tier
            for patent in patent_ideas:
                if progress_tracker:
                    progress_tracker.start_task("tier_processing", patent['id'])
            
            # Run the crew with error handling
            try:
                result = crew.kickoff()
                # Mark all patents in this tier as completed
                for patent in patent_ideas:
                    if progress_tracker:
                        progress_tracker.complete_task("tier_processing", patent['id'], success=True)
                        progress_tracker.complete_patent(patent['id'])
                
                logger.info(f"✅ Successfully processed {phase_info['name']}")
                processing_results[phase_key] = {
                    'success': True,
                    'patents_processed': len(patent_ideas),
                    'phase_info': phase_info,
                    'result': result
                }
                total_patents_processed += len(patent_ideas)
            except Exception as e:
                # Handle crew execution errors
                if error_handler.handle_error(e, "crew_execution", phase_key):
                    logger.info(f"🔄 Retrying crew execution for {phase_info['name']}")
                    try:
                        result = crew.kickoff()
                        for patent in patent_ideas:
                            if progress_tracker:
                                progress_tracker.complete_task("tier_processing", patent['id'], success=True)
                                progress_tracker.complete_patent(patent['id'])
                        
                        logger.info(f"✅ Successfully processed {phase_info['name']} on retry")
                        processing_results[phase_key] = {
                            'success': True,
                            'patents_processed': len(patent_ideas),
                            'phase_info': phase_info,
                            'result': result
                        }
                        total_patents_processed += len(patent_ideas)
                    except Exception as retry_error:
                        logger.error(f"❌ Crew execution failed on retry for {phase_info['name']}: {retry_error}")
                        for patent in patent_ideas:
                            if progress_tracker:
                                progress_tracker.complete_task("tier_processing", patent['id'], success=False)
                        processing_results[phase_key] = {
                            'success': False,
                            'error': str(retry_error),
                            'phase_info': phase_info
                        }
                else:
                    logger.error(f"❌ Crew execution failed for {phase_info['name']}: {e}")
                    for patent in patent_ideas:
                        if progress_tracker:
                            progress_tracker.complete_task("tier_processing", patent['id'], success=False)
                    processing_results[phase_key] = {
                        'success': False,
                        'error': str(e),
                        'phase_info': phase_info
                    }
                
        except Exception as e:
            logger.error(f"❌ Error processing {phase_info['name']}: {e}")
            if error_handler.handle_error(e, "phase_setup", phase_key):
                logger.info(f"🔄 Retrying phase setup for {phase_info['name']}")
                # Could implement retry logic here if needed
            else:
                processing_results[phase_key] = {
                    'success': False,
                    'error': str(e),
                    'phase_info': phase_info
                }
    
    # Quality Validation Phase (can be skipped with --no-validation)
    validation_results = {}
    if not no_validation:
        logger.info("=" * 80)
        logger.info("🔍 QUALITY VALIDATION PHASE")
        logger.info("=" * 80)
        
        try:
            from lib.validation_pipeline import validation_pipeline
            
            for phase_key, result in processing_results.items():
                if result['success'] and 'patents_processed' in result:
                    phase_info = result['phase_info']
                    patent_ideas = PATENT_IDEAS.get(phase_key, [])
                    if max_patents_per_phase:
                        patent_ideas = patent_ideas[:max_patents_per_phase]
                    
                    logger.info(f"🔍 Validating outputs for {phase_info['name']}...")
                    
                    # Validate each patent's outputs
                    phase_validation_results = {}
                    for patent in patent_ideas:
                        try:
                            patent_validation = validation_pipeline.validate_complete_workflow(phase_key, patent['id'])
                            phase_validation_results[patent['id']] = patent_validation
                            
                            # Log validation status
                            status = patent_validation['overall_status']
                            quality_score = patent_validation['quality_score']
                            
                            if status == 'PASSED':
                                logger.info(f"✅ {patent['id']}: Quality validation PASSED (Score: {quality_score:.1f})")
                            elif status == 'PARTIAL':
                                logger.warning(f"⚠️  {patent['id']}: Quality validation PARTIAL (Score: {quality_score:.1f})")
                            else:
                                logger.error(f"❌ {patent['id']}: Quality validation FAILED (Score: {quality_score:.1f})")
                                
                                # Log critical issues
                                cascade_failures = patent_validation.get('cascade_failures', [])
                                if cascade_failures:
                                    logger.error(f"   🚨 CASCADE FAILURE RISKS:")
                                    for failure in cascade_failures:
                                        logger.error(f"      - {failure}")
                        
                        except Exception as e:
                            logger.error(f"❌ Validation failed for {patent['id']}: {e}")
                            tier_validation_results[patent['id']] = {
                                'overall_status': 'ERROR',
                                'quality_score': 0,
                                'error': str(e)
                            }
                    
                    validation_results[phase_key] = phase_validation_results
                    
                    # Phase-level summary
                    total_patents = len(phase_validation_results)
                    passed_patents = len([v for v in phase_validation_results.values() 
                                        if v.get('overall_status') == 'PASSED'])
                    partial_patents = len([v for v in phase_validation_results.values() 
                                         if v.get('overall_status') == 'PARTIAL'])
                    failed_patents = len([v for v in phase_validation_results.values() 
                                        if v.get('overall_status') in ['FAILED', 'ERROR']])
                    
                    avg_quality = sum(v.get('quality_score', 0) for v in phase_validation_results.values()) / total_patents if total_patents > 0 else 0
                    
                    logger.info(f"📊 {phase_info['name']} Quality Summary:")
                    logger.info(f"   ✅ Passed: {passed_patents}/{total_patents} ({passed_patents/total_patents*100:.1f}%)")
                    logger.info(f"   ⚠️  Partial: {partial_patents}/{total_patents}")
                    logger.info(f"   ❌ Failed: {failed_patents}/{total_patents}")
                    logger.info(f"   📈 Average Quality Score: {avg_quality:.1f}/100")
                    
                    # Warning for cascade failures
                    if failed_patents > 0:
                        logger.warning(f"⚠️  {failed_patents} patents failed quality validation - may cause cascade failures")
            
            # Overall validation summary
            all_validations = []
            for tier_results in validation_results.values():
                all_validations.extend(tier_results.values())
            
            if all_validations:
                total_validations = len(all_validations)
                passed_validations = len([v for v in all_validations if v.get('overall_status') == 'PASSED'])
                partial_validations = len([v for v in all_validations if v.get('overall_status') == 'PARTIAL'])
                failed_validations = len([v for v in all_validations if v.get('overall_status') in ['FAILED', 'ERROR']])
                
                overall_avg_quality = sum(v.get('quality_score', 0) for v in all_validations) / total_validations if total_validations > 0 else 0
                
                logger.info("=" * 60)
                logger.info("🏆 OVERALL QUALITY VALIDATION SUMMARY")
                logger.info("=" * 60)
                logger.info(f"📊 Total Patents Validated: {total_validations}")
                logger.info(f"✅ Quality Validation Pass Rate: {passed_validations/total_validations*100:.1f}%")
                logger.info(f"📈 Overall Average Quality Score: {overall_avg_quality:.1f}/100")
                
                if failed_validations > 0:
                    logger.warning(f"🚨 QUALITY ALERT: {failed_validations} patents failed validation")
                    logger.warning("   Manual review recommended before submission")
                elif partial_validations > total_validations * 0.5:
                    logger.warning(f"⚠️  QUALITY NOTICE: {partial_validations} patents have quality issues")
                    logger.warning("   Consider addressing warnings to improve submission quality")
                else:
                    logger.info("🎉 QUALITY EXCELLENT: Most patents passed validation with high quality")
        
        except ImportError:
            logger.warning("⚠️  Quality validation system not available - skipping validation phase")
        except Exception as e:
            logger.error(f"❌ Quality validation phase failed: {e}")
            logger.warning("⚠️  Manual quality review recommended")
    else:
        logger.info("⚠️  Quality validation phase skipped (--no-validation flag)")
    
    # Summary
    logger.info("=" * 80)
    logger.info("📊 PROCESSING SUMMARY")
    logger.info("=" * 80)
    
    successful_tiers = 0
    successful_phases = 0
    total_patents = 0
    
    for phase_key, result in processing_results.items():
        phase_name = result['phase_info']['name']
        if result['success']:
            successful_phases += 1
            patents_processed = result['patents_processed']
            total_patents += patents_processed
            logger.info(f"✅ {phase_name}: {patents_processed} patents processed")
        else:
            logger.error(f"❌ {phase_name}: Failed - {result.get('error', 'Unknown error')}")
    
    logger.info(f"📈 Total Patents Processed: {total_patents}")
    logger.info(f"🎯 Successful Phases: {successful_phases}/{len(processing_results)}")
    
    # Collect and aggregate real valuation results
    if total_patents > 0:
        logger.info("🔍 Collecting valuation results from processed patents...")
        
        # Import the utility functions
        from lib.utils import collect_valuation_results_from_outputs, aggregate_portfolio_valuation
        
        # Collect valuation data from all output files
        valuation_files = []
        for phase_key in processing_results.keys():
            if phase_key in PATENT_IDEAS:
                patent_ideas = PATENT_IDEAS[phase_key]
                for patent in patent_ideas:
                    # Look for valuation output files
                    valuation_file = f"output/{phase_key}/{patent['id']}_valuation_report.md"
                    valuation_files.append(valuation_file)
        
        valuation_data_list = collect_valuation_results_from_outputs(valuation_files)
        
        if valuation_data_list:
            portfolio_summary = aggregate_portfolio_valuation(valuation_data_list)
            
            logger.info("💰 REAL PORTFOLIO VALUATION (Based on Expert Analysis)")
            logger.info("=" * 60)
            logger.info(f"Total Patents Valued: {portfolio_summary['total_patents']}")
            logger.info(f"Portfolio Value Range: ${portfolio_summary['total_low_value']:.1f}M - ${portfolio_summary['total_high_value']:.1f}M")
            logger.info(f"Portfolio Mid-Point Value: ${portfolio_summary['total_mid_value']:.1f}M")
            logger.info(f"Average Patent Value: ${portfolio_summary['average_mid_value']:.1f}M")
            
            # Calculate ROI
            total_investment = total_patents * PATENT_CONFIG['filing_cost_per_patent']
            roi_low = (portfolio_summary['total_low_value'] * 1000000) / total_investment if total_investment > 0 else 0
            roi_high = (portfolio_summary['total_high_value'] * 1000000) / total_investment if total_investment > 0 else 0
            roi_mid = (portfolio_summary['total_mid_value'] * 1000000) / total_investment if total_investment > 0 else 0
            
            logger.info(f"ROI Range: {roi_low:.0f}x - {roi_high:.0f}x")
            logger.info(f"ROI Mid-Point: {roi_mid:.0f}x")
            
            # Show value distribution
            if portfolio_summary['value_categories']:
                logger.info("Value Distribution:")
                for category, count in portfolio_summary['value_categories'].items():
                    logger.info(f"  {category}: {count} patents")
            
            # Show confidence levels
            if portfolio_summary['confidence_levels']:
                logger.info("Confidence Levels:")
                for confidence, count in portfolio_summary['confidence_levels'].items():
                    logger.info(f"  {confidence}: {count} patents")
        else:
            logger.warning("⚠️ No valuation data found in outputs")
    
    # Clean up monitoring and show final status
    try:
        cleanup_monitoring()
    except Exception as e:
        logger.warning(f"⚠️ Error during monitoring cleanup: {e}")
    
    # Show final status report
    try:
        status_report = get_status_report()
        logger.info("=" * 80)
        logger.info("📊 FINAL STATUS REPORT")
        logger.info("=" * 80)
        logger.info(f"Resource Usage: Memory {status_report['resource_status'].get('peak_memory_gb', 0):.1f}GB, CPU {status_report['resource_status'].get('peak_cpu_percent', 0):.1f}%")
        logger.info(f"Processing Time: {status_report['progress_summary'].get('total_time_minutes', 0):.1f} minutes")
        logger.info(f"Success Rate: {status_report['progress_summary'].get('patent_success_rate', 0):.1f}% patents, {status_report['progress_summary'].get('task_success_rate', 0):.1f}% tasks")
        if status_report['error_summary']:
            logger.info(f"Errors Encountered: {len(status_report['error_summary'])} different error types")
    except Exception as e:
        logger.warning(f"⚠️ Could not generate status report: {e}")
        logger.info("📊 Basic processing summary:")
        logger.info(f"📈 Total Patents Processed: {total_patents}")
        logger.info(f"🎯 Successful Tiers: {successful_tiers}/{len(processing_results)}")
    
    # Note: Optimization report generation moved to main() function where args is available
    
    # Generate agent tracking report if available
    if TRACKING_AVAILABLE:
        try:
            tracker = get_tracker()
            if tracker:
                logger.info("=" * 80)
                logger.info("🔍 AGENT TRACKING REPORT")
                logger.info("=" * 80)
                
                # Generate and display summary report
                summary_report = tracker.get_summary_report()
                print(summary_report)
                
                # Save detailed report to file
                report_file = tracker.save_detailed_report()
                logger.info(f"📊 Detailed agent tracking report saved to: {report_file}")
                
                # Show brief usage summary
                usage_stats = tracker.get_usage_stats()
                if usage_stats:
                    logger.info(f"🏷️  Models used: {', '.join(usage_stats.get('models_used', []))}")
                    logger.info(f"📞 Total API calls: {usage_stats.get('total_calls', 0)}")
                    logger.info(f"🎯 Agents tracked: {usage_stats.get('agents_tracked', 0)}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Could not generate agent tracking report: {e}")
    else:
        logger.info("📊 Agent tracking not available - no tracking report generated")
    
    return successful_tiers > 0

@trace_function(name="main")
def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Patent Automation System with CrewAI Native YAML Configuration')
    parser.add_argument('--phase', type=str, choices=['phase_1', 'phase_2', 'phase_3'], 
                       help='Process specific phase only')
    parser.add_argument('--max-per-phase', type=int, 
                                                help='Maximum number of patents to process per phase')
    parser.add_argument('--test', action='store_true', 
                       help='Run in test mode (limited patents)')
    parser.add_argument('--no-clear-cache', action='store_true',
                       help='Do not clear vector cache and output directories (use with caution)')
    parser.add_argument('--no-incremental', action='store_true',
                       help='Disable incremental processing (recreate all assets)')
    parser.add_argument('--force-regenerate', action='store_true',
                       help='Force regeneration of all assets (overrides incremental mode)')
    parser.add_argument('--show-status', action='store_true',
                       help='Show status of existing assets without running automation')
    parser.add_argument('--clear-logs', action='store_true',
                       help='Clear the log file before starting automation')
    
    # Resource management arguments
    parser.add_argument('--max-memory', type=float, default=12.0,
                       help='Maximum memory usage in GB (default: 12.0 for M1 Mac Pro)')
    parser.add_argument('--max-cpu', type=float, default=85.0,
                       help='Maximum CPU usage percentage (default: 85.0 for M1 efficiency)')
    parser.add_argument('--max-disk', type=float, default=4.0,
                       help='Maximum disk usage in GB (default: 4.0 for generous outputs)')
    parser.add_argument('--timeout', type=int, default=120,
                       help='Maximum processing time in minutes (default: 120 for complex processing)')
    parser.add_argument('--no-monitoring', action='store_true',
                       help='Disable resource monitoring and progress tracking')
    
    # Parallel execution arguments
    parser.add_argument('--parallel', action='store_true',
                       help='Enable parallel task execution for improved performance')
    parser.add_argument('--max-workers', type=int, default=4,
                       help='Maximum number of parallel workers (default: 4)')
    
    # Quality validation arguments
    parser.add_argument('--no-validation', action='store_true',
                       help='Skip quality validation phase (not recommended)')
    parser.add_argument('--validation-only', action='store_true',
                       help='Run quality validation only on existing outputs')
    parser.add_argument('--validation-level', type=str, choices=['quick', 'standard', 'thorough'],
                       default='standard', help='Level of quality validation (default: standard)')
    
    # Dynamic optimization arguments
    parser.add_argument('--no-optimization', action='store_true',
                       help='Disable dynamic optimization (may increase costs)')
    parser.add_argument('--optimization-level', type=str, choices=['conservative', 'balanced', 'aggressive'],
                       default='balanced', help='Level of cost optimization (default: balanced)')
    parser.add_argument('--optimization-target', type=float, default=0.30,
                       help='Target cost reduction percentage (default: 0.30 for 30 percent)')
    parser.add_argument('--optimization-report', action='store_true',
                       help='Generate detailed optimization report after execution')
    
    args = parser.parse_args()
    
    # Configure resource management if monitoring is enabled
    if not args.no_monitoring:
        from lib.resource_manager import resource_manager
        resource_manager.max_memory_gb = args.max_memory
        resource_manager.max_cpu_percent = args.max_cpu
        resource_manager.max_disk_gb = args.max_disk
        resource_manager.timeout_minutes = args.timeout
        logger.info(f"🔧 Resource monitoring configured: Memory {args.max_memory}GB, CPU {args.max_cpu}%, Disk {args.max_disk}GB, Timeout {args.timeout}min")
    else:
        logger.info("⚠️ Resource monitoring disabled")
    
    # Handle test mode
    if args.test:
        logger.info("🧪 Running in TEST MODE")
        if not args.max_per_phase:
            args.max_per_phase = 1
            logger.info("   Auto-limiting to 1 patent per tier for testing")
    
    # Handle log clearing
    if args.clear_logs:
        log_file = Path("patent_automation.log")
        if log_file.exists():
            try:
                log_file.unlink()
                print("🧹 Cleared patent_automation.log")
            except Exception as e:
                print(f"⚠️ Could not clear log file: {e}")
        else:
            print("📝 No existing log file to clear")
    
    # Handle validation-only mode
    if args.validation_only:
        logger.info("🔍 VALIDATION-ONLY MODE - Running quality validation on existing outputs")
        
        try:
            from lib.validation_pipeline import validation_pipeline
            
            # Determine phases to validate
            phases_to_validate = [args.phase] if args.phase else ['phase_1', 'phase_2', 'phase_3']
            
            overall_results = {}
            for phase_key in phases_to_validate:
                if phase_key in PATENT_IDEAS:
                    patent_ideas = PATENT_IDEAS[phase_key]
                    if args.max_per_phase:
                        patent_ideas = patent_ideas[:args.max_per_phase]
                    
                    logger.info(f"🔍 Validating {phase_key} outputs...")
                    
                    phase_results = {}
                    for patent in patent_ideas:
                        try:
                            validation_result = validation_pipeline.validate_complete_workflow(phase_key, patent['id'])
                            phase_results[patent['id']] = validation_result
                            
                            status = validation_result['overall_status']
                            quality_score = validation_result['quality_score']
                            
                            if status == 'PASSED':
                                logger.info(f"✅ {patent['id']}: PASSED (Quality: {quality_score:.1f})")
                            elif status == 'PARTIAL':
                                logger.warning(f"⚠️  {patent['id']}: PARTIAL (Quality: {quality_score:.1f})")
                            else:
                                logger.error(f"❌ {patent['id']}: FAILED (Quality: {quality_score:.1f})")
                        
                        except Exception as e:
                            logger.error(f"❌ Validation failed for {patent['id']}: {e}")
                    
                    overall_results[phase_key] = phase_results
            
            # Generate overall validation summary
            if overall_results:
                all_validations = []
                for phase_results in overall_results.values():
                    all_validations.extend(phase_results.values())
                
                total_validations = len(all_validations)
                passed_validations = len([v for v in all_validations if v.get('overall_status') == 'PASSED'])
                failed_validations = len([v for v in all_validations if v.get('overall_status') in ['FAILED', 'ERROR']])
                
                logger.info("=" * 80)
                logger.info("🏆 VALIDATION-ONLY SUMMARY")
                logger.info("=" * 80)
                logger.info(f"📊 Total Patents Validated: {total_validations}")
                logger.info(f"✅ Pass Rate: {passed_validations/total_validations*100:.1f}%")
                logger.info(f"❌ Failed: {failed_validations}")
                
                if failed_validations == 0:
                    logger.info("🎉 All patents passed quality validation!")
                    return True
                else:
                    logger.warning(f"🚨 {failed_validations} patents failed validation")
                    return False
            else:
                logger.warning("⚠️ No validation results generated")
                return False
                
        except ImportError:
            logger.error("❌ Quality validation system not available")
            return False
        except Exception as e:
            logger.error(f"❌ Validation-only mode failed: {e}")
            return False
    
    # Handle status-only mode
    if args.show_status:
        logger.info("📊 STATUS MODE - Showing asset status without running automation")
        incremental_processor = IncrementalProcessor()
        
        # Load tasks configuration
        with open('config/tasks.yaml', 'r') as f:
            tasks_config = yaml.safe_load(f)
        
        # Show status for all phases
        for phase_key in ['phase_1', 'phase_2', 'phase_3']:
            if phase_key in PATENT_IDEAS:
                patent_ideas = PATENT_IDEAS[phase_key]
                if args.max_per_phase:
                    patent_ideas = patent_ideas[:args.max_per_phase]
                
                phase_info = PATENT_CONFIG['portfolio_tiers'][phase_key]
                logger.info(f"\n🎯 {phase_info['name']} Status:")
                incremental_processor.print_missing_assets_report(patent_ideas, tasks_config, phase_key)
        
        return True
    
    # Run the automation
    success = run_patent_automation(
        phase_filter=args.phase, 
        max_patents_per_phase=args.max_per_phase, 
        clear_cache=not args.no_clear_cache,
        incremental=not args.no_incremental,
        force_regenerate=args.force_regenerate,
        parallel_execution=args.parallel,
        max_workers=args.max_workers,
        no_validation=args.no_validation,
        validation_level=args.validation_level,
        enable_optimization=not args.no_optimization,
        optimization_level=args.optimization_level
    )
    
    # Generate optimization report if requested
    if args.optimization_report and not args.no_optimization:
        try:
            from lib.dynamic_optimization_integration import get_coordinator
            coordinator = get_coordinator()
            report_file = coordinator.generate_optimization_report()
            logger.info(f"📊 Optimization report generated: {report_file}")
        except Exception as e:
            logger.warning(f"⚠️ Could not generate optimization report: {e}")
    
    if success:
        logger.info("🎉 Patent automation completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Patent automation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 