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
from core.patent_data import PATENT_IDEAS, PATENT_CONFIG
from core.retry_manager import RetryManager
from core.incremental_processor import IncrementalProcessor

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

def clear_output_directories():
    """Clear output directories before starting"""
    output_dir = Path("patent_output")
    if output_dir.exists():
        try:
            shutil.rmtree(output_dir)
            output_dir.mkdir(exist_ok=True)
            logger.info("🧹 Cleared output directories")
        except Exception as e:
            logger.warning(f"Could not clear output directories: {e}")

def setup_output_directories():
    """Create output directories"""
    base_dir = Path("patent_output")
    base_dir.mkdir(exist_ok=True)
    
    for tier in ['tier_1', 'tier_2', 'tier_3']:
        tier_dir = base_dir / tier
        tier_dir.mkdir(exist_ok=True)
    
    logger.info("✅ Output directories created")

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
            # Import and instantiate tools
            if tool_name == 'real_patent_search_tool':
                from tools.real_patent_search import RealPatentSearchTool
                lens_api_key = os.getenv('LENS_API_KEY')
                epo_api_key = os.getenv('EPO_API_KEY')
                tools.append(RealPatentSearchTool(lens_api_key=lens_api_key, epo_api_key=epo_api_key))
            elif tool_name == 'arxiv_search_tool':
                from tools.arxiv_search import ArxivSearchTool
                tools.append(ArxivSearchTool())
            elif tool_name == 'consolidated_risk_assessment_tool':
                from tools.consolidated_risk_assessment import ConsolidatedRiskAssessmentTool
                tools.append(ConsolidatedRiskAssessmentTool())
            elif tool_name == 'vector_based_overlap_analysis_tool':
                from tools.vector_based_overlap_analysis import VectorBasedOverlapAnalysisTool
                tools.append(VectorBasedOverlapAnalysisTool())
            elif tool_name == 'patent_document_tool':
                from tools.patent_document import PatentDocumentTool
                tools.append(PatentDocumentTool())
            elif tool_name == 'smart_claim_refinement_tool':
                from tools.smart_claim_refinement import SmartClaimRefinementTool
                tools.append(SmartClaimRefinementTool())
            elif tool_name == 'final_review_and_improvement_tool':
                from tools.final_review_and_improvement import FinalReviewAndImprovementTool
                tools.append(FinalReviewAndImprovementTool())
            elif tool_name == 'provisional_cover_sheet_tool':
                from tools.provisional_cover_sheet import ProvisionalCoverSheetTool
                tools.append(ProvisionalCoverSheetTool())
            elif tool_name == 'patent_valuation_tool':
                from tools.patent_valuation import PatentValuationTool
                tools.append(PatentValuationTool())
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
                            tier=tier, id=patent_idea['id']
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

def _format_task_description(template: str, patent_idea: Dict, tier: str) -> str:
    """Format task description with patent data"""
    # Variable mapping for template substitution with safe defaults
    variables = {
        'title': patent_idea.get('title', 'Untitled Patent'),
        'id': patent_idea.get('id', 'UNKNOWN'),
        'description': patent_idea.get('description', 'No description provided'),
        'claims_list': '\n'.join(f'- {claim}' for claim in patent_idea.get('key_claims', ['No claims provided'])),
        'value_estimate': patent_idea.get('value_estimate', '$2-15M'),
        'market_applications': ', '.join(patent_idea.get('market_applications', ['AI optimization'])),
        'technical_features': ', '.join(patent_idea.get('technical_features', [])),
        'differentiation': patent_idea.get('differentiation', 'TBD'),
        'tier_name': PATENT_CONFIG['portfolio_tiers'].get(tier, {}).get('name', 'Unknown Tier'),
        'description_length': len(patent_idea.get('description', '').split()),
        'claims_count': len(patent_idea.get('key_claims', []))
    }
    
    # Replace variables in template
    formatted_description = template
    for var_name, value in variables.items():
        formatted_description = formatted_description.replace(f'{{{var_name}}}', str(value))
    
    return formatted_description

def run_patent_automation(tier_filter: Optional[str] = None, max_patents_per_tier: Optional[int] = None, clear_cache: bool = True, incremental: bool = True, force_regenerate: bool = False):
    """Run patent automation for specified tiers using CrewAI YAML configuration"""
    
    logger.info("🤖 Starting Patent Automation System with CrewAI Native YAML Configuration")
    logger.info("=" * 80)
    logger.info(f"Target Portfolio: {PATENT_CONFIG['target_portfolio_size']} patents")
    logger.info(f"Total Investment: ${PATENT_CONFIG['target_portfolio_size'] * PATENT_CONFIG['filing_cost_per_patent']:,}")
    logger.info(f"Expected Value: ~$90M (ROI: ~13,800x)")
    logger.info(f"Incremental Processing: {'Enabled' if incremental else 'Disabled'}")
    logger.info(f"Force Regenerate: {'Yes' if force_regenerate else 'No'}")
    
    # Validate environment
    if not validate_environment():
        return False
    
    # Initialize incremental processor
    incremental_processor = IncrementalProcessor()
    if force_regenerate:
        incremental_processor.force_regenerate_all()
        logger.info("🔄 Force regeneration enabled - will recreate all assets")
    
    # Clear cache and outputs to prevent context size growth (only if not incremental or force regenerate)
    if clear_cache and (not incremental or force_regenerate):
        clear_vector_cache()
        if force_regenerate:
            clear_output_directories()
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
    
    # Process each tier
    processing_results = {}
    total_patents_processed = 0
    
    tiers_to_process = [tier_filter] if tier_filter else ['tier_1', 'tier_2', 'tier_3']
    
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
        logger.info(f"   Value Range: {tier_info['value_range']}")
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
                incremental_processor.print_missing_assets_report(patent_ideas, tasks_config)
                
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
                continue
            
            # Create crew with agents and tasks
            crew = Crew(
                agents=list(agents.values()),
                tasks=tasks,
                process="sequential",
                verbose=True,
                memory=True,
                max_rpm=30
            )
            
            # Run the crew
            result = crew.kickoff()
            
            logger.info(f"✅ Successfully processed {tier_info['name']}")
            processing_results[tier_key] = {
                'success': True,
                'patents_processed': len(patent_ideas),
                'tier_info': tier_info,
                'result': result
            }
            total_patents_processed += len(patent_ideas)
                
        except Exception as e:
            logger.error(f"❌ Error processing {tier_info['name']}: {e}")
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
    
    if total_patents > 0:
        estimated_value = total_patents * 5000000  # $5M average per patent
        logger.info(f"💰 Estimated Portfolio Value: ${estimated_value:,}")
    
    # Show retry manager summary
    logger.info("=" * 80)
    logger.info("🔄 RETRY MANAGER SUMMARY")
    logger.info("=" * 80)
    
    summary = retry_manager.get_execution_summary()
    logger.info(f"Total Tool Executions: {summary['total_executions']}")
    logger.info(f"Successful: {summary['successful']}")
    logger.info(f"Failed: {summary['failed']}")
    logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
    logger.info(f"Average Retries: {summary['average_retries']:.1f}")
    
    if summary['failed'] > 0:
        logger.warning(f"⚠️ {summary['failed']} tool executions failed. Run recovery manager for details:")
        logger.warning("   python scripts/recovery_manager.py --show-failed")
        logger.warning("   python scripts/recovery_manager.py --report")
    
    return True

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Patent Automation System with CrewAI Native YAML Configuration')
    parser.add_argument('--tier', type=str, choices=['tier_1', 'tier_2', 'tier_3'], 
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
    
    args = parser.parse_args()
    
    # Handle test mode
    if args.test:
        logger.info("🧪 Running in TEST MODE")
        if not args.max_per_tier:
            args.max_per_tier = 1
            logger.info("   Auto-limiting to 1 patent per tier for testing")
    
    # Handle status-only mode
    if args.show_status:
        logger.info("📊 STATUS MODE - Showing asset status without running automation")
        incremental_processor = IncrementalProcessor()
        
        # Load tasks configuration
        with open('config/tasks.yaml', 'r') as f:
            tasks_config = yaml.safe_load(f)
        
        # Show status for all tiers
        for tier_key in ['tier_1', 'tier_2', 'tier_3']:
            if tier_key in PATENT_IDEAS:
                patent_ideas = PATENT_IDEAS[tier_key]
                if args.max_per_tier:
                    patent_ideas = patent_ideas[:args.max_per_tier]
                
                tier_info = PATENT_CONFIG['portfolio_tiers'][tier_key]
                logger.info(f"\n🎯 {tier_info['name']} Status:")
                incremental_processor.print_missing_assets_report(patent_ideas, tasks_config)
        
        return True
    
    # Run the automation
    success = run_patent_automation(
        args.tier, 
        args.max_per_tier, 
        clear_cache=not args.no_clear_cache,
        incremental=not args.no_incremental,
        force_regenerate=args.force_regenerate
    )
    
    if success:
        logger.info("🎉 Patent automation completed successfully!")
        sys.exit(0)
    else:
        logger.error("💥 Patent automation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 