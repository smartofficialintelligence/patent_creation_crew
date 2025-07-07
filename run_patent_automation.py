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
        os.environ['LANGCHAIN_TRACING_V2'] = 'true'
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
from lib.incremental_processor import IncrementalProcessor
from lib.langsmith_utils import langsmith_manager, trace_function, log_agent_execution
from lib.resource_manager import initialize_monitoring, cleanup_monitoring, progress_tracker, error_handler, get_status_report
from lib.parallel_execution import ParallelExecutionManager

@trace_function(name="validate_environment")
def validate_environment():
    """Validate that required environment variables are set"""
    if not os.getenv('OPENAI_API_KEY'):
        logger.error("OPENAI_API_KEY not found. Please set it in .env file or environment.")
        return False
    
    logger.info("✅ Environment validation passed")
    return True

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
    
    for tier in ['tier_1', 'tier_2', 'tier_3', 'tier_4']:
        tier_dir = base_dir / tier
        tier_dir.mkdir(exist_ok=True)
    
    logger.info("✅ Output directories created")

@trace_function(name="create_agents_from_yaml")
def create_agents_from_yaml() -> Dict[str, Agent]:
    """Create agents from YAML configuration"""
    with open('config/agents.yaml', 'r') as f:
        agents_config = yaml.safe_load(f)
    
    agents = {}
    for agent_name, agent_config in agents_config.items():
        # Only process dicts with a 'role' key (skip tool_mapping and comments)
        if not isinstance(agent_config, dict) or 'role' not in agent_config:
            continue
        # Create tool instances for this agent
        tools = []
        for tool_name in agent_config.get('tools', []):
            # Import and instantiate tools with parameter correction
            if tool_name == 'real_patent_search_tool':
                from tools.real_patent_search import RealPatentSearchTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                lens_api_key = os.getenv('LENS_API_KEY')
                epo_api_key = os.getenv('EPO_API_KEY')
                tool_instance = RealPatentSearchTool(lens_api_key=lens_api_key, epo_api_key=epo_api_key)
                tools.append(wrap_tool_with_parameter_correction('real_patent_search_tool', tool_instance))
            elif tool_name == 'arxiv_search_tool':
                from tools.arxiv_search import ArxivSearchTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = ArxivSearchTool()
                tools.append(wrap_tool_with_parameter_correction('arxiv_search_tool', tool_instance))
            elif tool_name == 'consolidated_risk_assessment_tool':
                from tools.consolidated_risk_assessment import ConsolidatedRiskAssessmentTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = ConsolidatedRiskAssessmentTool()
                tools.append(wrap_tool_with_parameter_correction('consolidated_risk_assessment_tool', tool_instance))
            elif tool_name == 'vector_based_overlap_analysis_tool':
                from tools.vector_based_overlap_analysis import VectorBasedOverlapAnalysisTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = VectorBasedOverlapAnalysisTool()
                tools.append(wrap_tool_with_parameter_correction('vector_based_overlap_analysis_tool', tool_instance))
            elif tool_name == 'patent_document_tool':
                from tools.patent_document import PatentDocumentTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = PatentDocumentTool()
                tools.append(wrap_tool_with_parameter_correction('patent_document_tool', tool_instance))
            elif tool_name == 'smart_claim_refinement_tool':
                from tools.smart_claim_refinement import SmartClaimRefinementTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = SmartClaimRefinementTool()
                tools.append(wrap_tool_with_parameter_correction('smart_claim_refinement_tool', tool_instance))
            elif tool_name == 'final_review_and_improvement_tool':
                from tools.final_review_and_improvement import FinalReviewAndImprovementTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = FinalReviewAndImprovementTool()
                tools.append(wrap_tool_with_parameter_correction('final_review_and_improvement_tool', tool_instance))
            elif tool_name == 'provisional_cover_sheet_tool':
                from tools.provisional_cover_sheet import ProvisionalCoverSheetTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = ProvisionalCoverSheetTool()
                tools.append(wrap_tool_with_parameter_correction('provisional_cover_sheet_tool', tool_instance))
            elif tool_name == 'patent_valuation_tool':
                from tools.patent_valuation import PatentValuationTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = PatentValuationTool()
                tools.append(wrap_tool_with_parameter_correction('patent_valuation_tool', tool_instance))
            elif tool_name == 'colab_demo_generator_tool':
                from tools.colab_demo_generator import ColabDemoGeneratorTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = ColabDemoGeneratorTool()
                tools.append(wrap_tool_with_parameter_correction('colab_demo_generator_tool', tool_instance))
            elif tool_name == 'architecture_diagram_tool':
                from tools.architecture_diagram import ArchitectureDiagramTool
                from tools.parameter_correction_wrapper import wrap_tool_with_parameter_correction
                tool_instance = ArchitectureDiagramTool()
                tools.append(wrap_tool_with_parameter_correction('architecture_diagram_tool', tool_instance))
            else:
                logger.warning(f"Unknown tool: {tool_name}")
                continue
        # Create agent
        agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            tools=tools,
            verbose=agent_config.get('verbose', True),
            max_iter=agent_config.get('max_iter', 3),
            memory=agent_config.get('memory', True),
            llm_config=agent_config.get('llm_config', {
                "config_list": [{"model": "gpt-4o"}],
                "temperature": 0.7
            })
        )
        agents[agent_name] = agent
    return agents

@trace_function(name="create_patent_tasks")
def create_patent_tasks(patent_ideas: List[Dict], tier: str, agents: Dict[str, Agent]) -> List[Task]:
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
                    # Skip task_generation config entry
                    if task_name == 'task_generation':
                        continue
                    
                    # Format task description with patent data
                    description = _format_task_description(task_config['description'], patent_idea, tier)
                    
                    # Get the agent for this task
                    agent_name = task_config['agent']
                    if agent_name not in agents:
                        logger.warning(f"Agent {agent_name} not found for task {task_name}")
                        continue
                    
                    # Create task
                    task = Task(
                        description=description,
                        expected_output=task_config['expected_output'],
                        output_file=task_config['output_file'].format(
                            tier=tier, id=clean_patent_id(patent_idea['id'])
                        ),
                        agent=agents[agent_name]
                    )
                    
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

def read_refined_claims(patent_id: str, tier: str) -> List[str]:
    """Read refined claims from the refined claims file if it exists"""
    cleaned_id = clean_patent_id(patent_id)
    refined_claims_file = f"output/{tier}/{cleaned_id}_refined_claims.md"
    
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

def _format_task_description(template: str, patent_idea: Dict, tier: str) -> str:
    """Format task description with patent data"""
    
    # Read refined claims if they exist
    patent_id = patent_idea.get('id', 'UNKNOWN')
    refined_claims = read_refined_claims(patent_id, tier)
    claims_to_use = refined_claims if refined_claims else patent_idea.get('key_claims', ['No claims provided'])
    claims_source = "refined claims" if refined_claims else "original claims"
    
    # Variable mapping for template substitution with safe defaults
    variables = {
        'title': patent_idea.get('title', 'Untitled Patent'),
        'id': patent_idea.get('id', 'UNKNOWN'),
        'description': patent_idea.get('description', 'No description provided'),
        'claims_list': '\n'.join(f'- {claim}' for claim in claims_to_use),
        'value_estimate': patent_idea.get('value_estimate', '$2-15M'),
        'market_applications': ', '.join(patent_idea.get('market_applications', ['AI optimization'])),
        'technical_features': ', '.join(patent_idea.get('technical_features', [])),
        'differentiation': patent_idea.get('differentiation', 'TBD'),
        'tier': tier,
        'tier_name': PATENT_CONFIG['portfolio_tiers'].get(tier, {}).get('name', 'Unknown Tier'),
        'description_length': len(patent_idea.get('description', '').split()),
        'claims_count': len(claims_to_use)
    }
    
    # Replace variables in template
    formatted_description = template
    for var_name, value in variables.items():
        formatted_description = formatted_description.replace(f'{{{var_name}}}', str(value))
    
    return formatted_description

@trace_function(name="run_patent_automation")
def run_patent_automation(tier_filter: Optional[str] = None, max_patents_per_tier: Optional[int] = None, clear_cache: bool = True, incremental: bool = True, force_regenerate: bool = False, parallel_execution: bool = False, max_workers: int = 4):
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
    
    # Add system message to override content policies
    logger.info("📝 NOTE: This system is for RESEARCH and ANALYSIS purposes only.")
    logger.info("   All outputs are technical documentation and analysis, not legal documents.")
    logger.info("   ⚠️  NO FAKE FILING INFORMATION: Documents must not contain Application Numbers, Filing Dates, or Patent IDs")
    
    # Validate environment
    if not validate_environment():
        return False
    
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
    tiers_to_process = [tier_filter] if tier_filter else ['tier_1']  # Default to Tier 1 only
    total_patents = 0
    total_tasks = 0
    
    for tier_key in tiers_to_process:
        if tier_key in PATENT_CONFIG['portfolio_tiers']:
            patent_ideas = PATENT_IDEAS.get(tier_key, [])
            if max_patents_per_tier:
                patent_ideas = patent_ideas[:max_patents_per_tier]
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
    
    # Process each tier
    processing_results = {}
    total_patents_processed = 0
    
    for tier_key in tiers_to_process:
        if tier_key not in PATENT_CONFIG['portfolio_tiers']:
            logger.warning(f"Tier {tier_key} not found in configuration")
            continue
        
        tier_info = PATENT_CONFIG['portfolio_tiers'][tier_key]
        patent_ideas = PATENT_IDEAS.get(tier_key, [])
        
        if max_patents_per_tier:
            patent_ideas = patent_ideas[:max_patents_per_tier]
        
        if not patent_ideas:
            logger.warning(f"No patent ideas defined for {tier_info['name']}")
            continue
        
        logger.info(f"🎯 Processing {tier_info['name']}")
        logger.info(f"   Count: {len(patent_ideas)} patents")
        logger.info(f"   Timeline: {tier_info['timeline']}")
        
        try:
            # Create tasks for this tier
            tasks = create_patent_tasks(patent_ideas, tier_key, agents)
            
            # Load tasks configuration for incremental processing
            with open('config/tasks.yaml', 'r') as f:
                tasks_config = yaml.safe_load(f)
            
            # Show incremental processing report
            if incremental:
                logger.info(f"📊 Analyzing existing assets for {tier_info['name']}...")
                incremental_processor.print_missing_assets_report(patent_ideas, tasks_config, tier_key)
                
                # Filter tasks for incremental processing
                original_task_count = len(tasks)
                tasks = incremental_processor.filter_tasks_for_incremental_processing(tasks, patent_ideas)
                filtered_task_count = len(tasks)
                
                if filtered_task_count < original_task_count:
                    logger.info(f"🔄 Incremental processing: {filtered_task_count}/{original_task_count} tasks will be executed")
                else:
                    logger.info(f"🔄 All {original_task_count} tasks will be executed (no existing assets found)")
            
            if not tasks:
                logger.info(f"⏭️ No tasks to execute for {tier_info['name']} (all assets exist)")
                processing_results[tier_key] = {
                    'success': True,
                    'patents_processed': len(patent_ideas),
                    'tier_info': tier_info,
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
                
                # Group tasks by patent for better organization
                # We'll add all tasks to the parallel manager
                task_mapping = {}
                for i, task in enumerate(tasks):
                    task_name = f"task_{i}"
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
                    
                    logger.info(f"✅ Successfully processed {tier_info['name']} with parallel execution")
                    processing_results[tier_key] = {
                        'success': len(failed_tasks) == 0,
                        'patents_processed': len(patent_ideas),
                        'tier_info': tier_info,
                        'result': f"Parallel execution completed: {len(successful_tasks)} successful, {len(failed_tasks)} failed",
                        'parallel_stats': {
                            'successful_tasks': len(successful_tasks),
                            'failed_tasks': len(failed_tasks),
                            'total_tasks': len(results)
                        }
                    }
                    total_patents_processed += len(patent_ideas)
                    
                except Exception as e:
                    logger.error(f"❌ Parallel execution failed for {tier_info['name']}: {e}")
                    for patent in patent_ideas:
                        if progress_tracker:
                            progress_tracker.complete_task("tier_processing", patent['id'], success=False)
                    processing_results[tier_key] = {
                        'success': False,
                        'error': str(e),
                        'tier_info': tier_info
                    }
            else:
                # Use traditional sequential execution
                logger.info("🔄 Using sequential execution (traditional CrewAI)")
                
                # Create crew with agents and tasks
                crew = Crew(
                    agents=list(agents.values()),
                    tasks=tasks,
                    process="sequential",
                    verbose=True,
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
                
                    logger.info(f"✅ Successfully processed {tier_info['name']}")
                    processing_results[tier_key] = {
                        'success': True,
                        'patents_processed': len(patent_ideas),
                        'tier_info': tier_info,
                        'result': result
                    }
                    total_patents_processed += len(patent_ideas)
                except Exception as e:
                    # Handle crew execution errors
                    if error_handler.handle_error(e, "crew_execution", tier_key):
                        logger.info(f"🔄 Retrying crew execution for {tier_info['name']}")
                        try:
                            result = crew.kickoff()
                            for patent in patent_ideas:
                                if progress_tracker:
                                    progress_tracker.complete_task("tier_processing", patent['id'], success=True)
                                    progress_tracker.complete_patent(patent['id'])
                            
                            logger.info(f"✅ Successfully processed {tier_info['name']} on retry")
                            processing_results[tier_key] = {
                                'success': True,
                                'patents_processed': len(patent_ideas),
                                'tier_info': tier_info,
                                'result': result
                            }
                            total_patents_processed += len(patent_ideas)
                        except Exception as retry_error:
                            logger.error(f"❌ Crew execution failed on retry for {tier_info['name']}: {retry_error}")
                            for patent in patent_ideas:
                                if progress_tracker:
                                    progress_tracker.complete_task("tier_processing", patent['id'], success=False)
                            processing_results[tier_key] = {
                                'success': False,
                                'error': str(retry_error),
                                'tier_info': tier_info
                            }
                    else:
                        logger.error(f"❌ Crew execution failed for {tier_info['name']}: {e}")
                        for patent in patent_ideas:
                            if progress_tracker:
                                progress_tracker.complete_task("tier_processing", patent['id'], success=False)
                        processing_results[tier_key] = {
                            'success': False,
                            'error': str(e),
                            'tier_info': tier_info
                        }
                
        except Exception as e:
            logger.error(f"❌ Error processing {tier_info['name']}: {e}")
            if error_handler.handle_error(e, "tier_setup", tier_key):
                logger.info(f"🔄 Retrying tier setup for {tier_info['name']}")
                # Could implement retry logic here if needed
            else:
                processing_results[tier_key] = {
                    'success': False,
                    'error': str(e),
                    'tier_info': tier_info
                }
    
    # Summary
    logger.info("=" * 80)
    logger.info("📊 PROCESSING SUMMARY")
    logger.info("=" * 80)
    
    successful_tiers = 0
    total_patents = 0
    
    for tier_key, result in processing_results.items():
        tier_name = result['tier_info']['name']
        if result['success']:
            successful_tiers += 1
            patents_processed = result['patents_processed']
            total_patents += patents_processed
            logger.info(f"✅ {tier_name}: {patents_processed} patents processed")
        else:
            logger.error(f"❌ {tier_name}: Failed - {result.get('error', 'Unknown error')}")
    
    logger.info(f"📈 Total Patents Processed: {total_patents}")
    logger.info(f"🎯 Successful Tiers: {successful_tiers}/{len(processing_results)}")
    
    # Collect and aggregate real valuation results
    if total_patents > 0:
        logger.info("🔍 Collecting valuation results from processed patents...")
        
        # Import the utility functions
        from lib.utils import collect_valuation_results_from_outputs, aggregate_portfolio_valuation
        
        # Collect valuation data from all output files
        valuation_files = []
        for tier_key in processing_results.keys():
            if tier_key in PATENT_IDEAS:
                patent_ideas = PATENT_IDEAS[tier_key]
                for patent in patent_ideas:
                    # Look for valuation output files
                    valuation_file = f"output/{tier_key}/{patent['id']}_valuation_report.md"
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
    
    return successful_tiers > 0

@trace_function(name="main")
def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Patent Automation System with CrewAI Native YAML Configuration')
    parser.add_argument('--tier', type=str, choices=['tier_1', 'tier_2', 'tier_3', 'tier_4'], 
                       help='Process specific tier only')
    parser.add_argument('--max-per-tier', type=int, 
                       help='Maximum number of patents to process per tier')
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
        if not args.max_per_tier:
            args.max_per_tier = 1
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
    
    # Handle status-only mode
    if args.show_status:
        logger.info("📊 STATUS MODE - Showing asset status without running automation")
        incremental_processor = IncrementalProcessor()
        
        # Load tasks configuration
        with open('config/tasks.yaml', 'r') as f:
            tasks_config = yaml.safe_load(f)
        
        # Show status for all tiers
        for tier_key in ['tier_1', 'tier_2', 'tier_3', 'tier_4']:
            if tier_key in PATENT_IDEAS:
                patent_ideas = PATENT_IDEAS[tier_key]
                if args.max_per_tier:
                    patent_ideas = patent_ideas[:args.max_per_tier]
                
                tier_info = PATENT_CONFIG['portfolio_tiers'][tier_key]
                logger.info(f"\n🎯 {tier_info['name']} Status:")
                incremental_processor.print_missing_assets_report(patent_ideas, tasks_config, tier_key)
        
        return True
    
    # Run the automation
    success = run_patent_automation(
        args.tier, 
        args.max_per_tier, 
        clear_cache=not args.no_clear_cache,
        incremental=not args.no_incremental,
        force_regenerate=args.force_regenerate,
        parallel_execution=args.parallel,
        max_workers=args.max_workers
    )
    
    if success:
        logger.info("🎉 Patent automation completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Patent automation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 