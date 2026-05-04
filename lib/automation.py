# Orchestration functions will be moved here. 

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import patent data from patent_data module
try:
    from core.patent_data import PATENT_IDEAS, PATENT_CONFIG
except ImportError:
    # Fallback if import fails
    PATENT_IDEAS = {}  # Set appropriately in your main config
    PATENT_CONFIG = {
        'portfolio_tiers': {
            'tier_1': {'name': 'Tier 1', 'timeline': '12 months'},
            'tier_2': {'name': 'Tier 2', 'timeline': '18 months'},
            'tier_3': {'name': 'Tier 3', 'timeline': '24 months'}
        }
    }

# Placeholders for logger (should be configured in your main script)
try:
    logger = logging.getLogger(__name__)
except:
    logger = logging.getLogger()

# Placeholders for any missing imports
try:
    from tasks.crew_tasks import create_enhanced_patent_tasks
    from agents.crew_agents import create_enhanced_agents
    from core.validation import validate_patent_data
    from core.utils import check_file_exists, should_skip_task, log_skip_reason
    from core.export import export_report
except ImportError:
    pass

# Placeholders for Crew class (should be imported from CrewAI or your crew framework)
try:
    from crewai import Crew
except ImportError:
    Crew = object  # fallback for static analysis

# The actual functions

def setup_output_directories():
    """Create output directories for patent processing"""
    import os
    
    # Create main output directory
    os.makedirs("output", exist_ok=True)
    
    # Create tier-specific directories
    for tier in ['tier_1', 'tier_2', 'tier_3']:
        os.makedirs(f"output/{tier}", exist_ok=True)
    
    logger.info("✅ Output directories created")

def create_enhanced_patent_crew(tier: str, patent_ideas: List[Dict]) -> Crew:
    """Create enhanced CrewAI crew for patent processing"""
    
    # Create agents
    agents = create_enhanced_agents()
    
    # Create tasks
    tasks = create_enhanced_patent_tasks(patent_ideas, tier)
    
    # Create crew
    crew = Crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        memory=True
    )
    
    return crew

def run_cover_sheet_only(tier_filter: Optional[str] = None, max_patents_per_tier: Optional[int] = None):
    """Run only cover sheet generation for existing patents"""
    
    logger.info("📄 Running Cover Sheet Generation Only Mode")
    logger.info("=" * 80)
    logger.info("This will only generate USPTO-compliant cover sheets for patents that don't have them yet.")
    
    # Validate environment and data
    if not validate_patent_data(PATENT_IDEAS):
        logger.error("❌ Patent data validation failed")
        return False
    
    # Setup output directories
    setup_output_directories()
    
    # Process each tier
    processing_results = {}
    total_patents_processed = 0
    
    for tier_key in ['tier_1', 'tier_2', 'tier_3']:
        if tier_filter and tier_key != tier_filter:
            continue
        
        tier_info = PATENT_CONFIG['portfolio_tiers'][tier_key]
        patent_ideas = PATENT_IDEAS.get(tier_key, [])
        
        if max_patents_per_tier:
            patent_ideas = patent_ideas[:max_patents_per_tier]
        
        if not patent_ideas:
            logger.warning(f"No patent ideas defined for {tier_info['name']}")
            continue
        
        logger.info(f"🎯 Processing cover sheet generation for {tier_info['name']}")
        logger.info(f"   Count: {len(patent_ideas)} patents")
        
        # Filter patents that need cover sheet generation
        patents_needing_cover_sheet = []
        for patent in patent_ideas:
            cover_sheet_file = f"patent_output/{tier_key}/{patent['id']}_cover_sheet.md"
            if not check_file_exists(cover_sheet_file):
                patents_needing_cover_sheet.append(patent)
            else:
                logger.info(f"⏭️  Skipping {patent['id']}: cover sheet already exists")
        
        if not patents_needing_cover_sheet:
            logger.info(f"✅ All patents in {tier_info['name']} already have cover sheets")
            continue
        
        logger.info(f"📋 Found {len(patents_needing_cover_sheet)} patents needing cover sheets")
        
        try:
            # Create and run crew for this tier (only cover sheet tasks)
            crew = create_enhanced_patent_crew(tier_key, patents_needing_cover_sheet)
            
            logger.info(f"Starting cover sheet generation for {tier_info['name']}")
            start_time = datetime.now()
            
            results = crew.kickoff()
            
            end_time = datetime.now()
            processing_time = end_time - start_time
            
            logger.info(f"✅ Completed cover sheet generation for {tier_info['name']} in {processing_time}")
            
            # Save tier results
            tier_results = {
                'tier': tier_key,
                'tier_info': tier_info,
                'patent_count': len(patents_needing_cover_sheet),
                'processing_time': str(processing_time),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'patents_processed': [p['id'] for p in patents_needing_cover_sheet],
                'status': 'COMPLETED',
                'results_summary': str(results)[:1000],
                'mode': 'COVER_SHEET_ONLY'
            }
            
            # Save to JSON
            results_file = Path(f"patent_output/{tier_key}/cover_sheet_results.json")
            with open(results_file, 'w') as f:
                json.dump(tier_results, f, indent=2)
            
            processing_results[tier_key] = tier_results
            total_patents_processed += len(patents_needing_cover_sheet)
            
        except Exception as e:
            logger.error(f"❌ Error processing {tier_info['name']}: {e}")
            processing_results[tier_key] = {
                'tier': tier_key,
                'tier_info': tier_info,
                'patent_count': len(patents_needing_cover_sheet),
                'status': 'ERROR',
                'error': str(e),
                'mode': 'COVER_SHEET_ONLY'
            }
    
    # Generate summary
    generate_enhanced_portfolio_summary(processing_results, total_patents_processed)
    
    return len(processing_results) > 0

def run_final_review_only(tier_filter: Optional[str] = None, max_patents_per_tier: Optional[int] = None):
    """Run only final review and improvement analysis for existing patents"""
    
    logger.info("🔍 Running Final Review Only Mode")
    logger.info("=" * 80)
    logger.info("This will only run final review and improvement analysis for patents that don't have them yet.")
    
    # Validate environment and data
    if not validate_patent_data(PATENT_IDEAS):
        logger.error("❌ Patent data validation failed")
        return False
    
    # Setup output directories
    setup_output_directories()
    
    # Process each tier
    processing_results = {}
    total_patents_processed = 0
    
    for tier_key in ['tier_1', 'tier_2', 'tier_3']:
        if tier_filter and tier_key != tier_filter:
            continue
        
        tier_info = PATENT_CONFIG['portfolio_tiers'][tier_key]
        patent_ideas = PATENT_IDEAS.get(tier_key, [])
        
        if max_patents_per_tier:
            patent_ideas = patent_ideas[:max_patents_per_tier]
        
        if not patent_ideas:
            logger.warning(f"No patent ideas defined for {tier_info['name']}")
            continue
        
        logger.info(f"🎯 Processing final review for {tier_info['name']}")
        logger.info(f"   Count: {len(patent_ideas)} patents")
        
        # Filter patents that need final review
        patents_needing_review = []
        for patent in patent_ideas:
            final_review_file = f"patent_output/{tier_key}/{patent['id']}_final_review.md"
            if not check_file_exists(final_review_file):
                patents_needing_review.append(patent)
            else:
                logger.info(f"⏭️  Skipping {patent['id']}: final review already exists")
        
        if not patents_needing_review:
            logger.info(f"✅ All patents in {tier_info['name']} already have final review")
            continue
        
        logger.info(f"📋 Found {len(patents_needing_review)} patents needing final review")
        
        try:
            # Create and run crew for this tier (only final review tasks)
            crew = create_enhanced_patent_crew(tier_key, patents_needing_review)
            
            logger.info(f"Starting final review for {tier_info['name']}")
            start_time = datetime.now()
            
            results = crew.kickoff()
            
            end_time = datetime.now()
            processing_time = end_time - start_time
            
            logger.info(f"✅ Completed final review for {tier_info['name']} in {processing_time}")
            
            # Save tier results
            tier_results = {
                'tier': tier_key,
                'tier_info': tier_info,
                'patent_count': len(patents_needing_review),
                'processing_time': str(processing_time),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'patents_processed': [p['id'] for p in patents_needing_review],
                'status': 'COMPLETED',
                'results_summary': str(results)[:1000],
                'mode': 'FINAL_REVIEW_ONLY'
            }
            
            # Save to JSON
            results_file = Path(f"patent_output/{tier_key}/final_review_results.json")
            with open(results_file, 'w') as f:
                json.dump(tier_results, f, indent=2)
            
            processing_results[tier_key] = tier_results
            total_patents_processed += len(patents_needing_review)
            
        except Exception as e:
            logger.error(f"❌ Error processing {tier_info['name']}: {e}")
            processing_results[tier_key] = {
                'tier': tier_key,
                'tier_info': tier_info,
                'patent_count': len(patents_needing_review),
                'status': 'ERROR',
                'error': str(e),
                'mode': 'FINAL_REVIEW_ONLY'
            }
    
    # Generate summary
    generate_enhanced_portfolio_summary(processing_results, total_patents_processed)
    
    return len(processing_results) > 0

def run_consolidated_risk_assessment(tier_filter: Optional[str] = None, max_patents_per_tier: Optional[int] = None):
    """Run consolidated risk assessment for existing patents"""
    
    logger.info("⚠️  Running Consolidated Risk Assessment Mode")
    logger.info("=" * 80)
    logger.info("This will run comprehensive risk assessment consolidating all analysis.")
    
    # Validate environment and data
    if not validate_patent_data(PATENT_IDEAS):
        logger.error("❌ Patent data validation failed")
        return False
    
    # Setup output directories
    setup_output_directories()
    
    # Process each tier
    processing_results = {}
    total_patents_processed = 0
    
    for tier_key in ['tier_1', 'tier_2', 'tier_3']:
        if tier_filter and tier_key != tier_filter:
            continue
        
        tier_info = PATENT_CONFIG['portfolio_tiers'][tier_key]
        patent_ideas = PATENT_IDEAS.get(tier_key, [])
        
        if max_patents_per_tier:
            patent_ideas = patent_ideas[:max_patents_per_tier]
        
        if not patent_ideas:
            logger.warning(f"No patent ideas defined for {tier_info['name']}")
            continue
        
        logger.info(f"🎯 Processing risk assessment for {tier_info['name']}")
        logger.info(f"   Count: {len(patent_ideas)} patents")
        
        # Filter patents that need risk assessment
        patents_needing_assessment = []
        for patent in patent_ideas:
            risk_assessment_file = f"patent_output/{tier_key}/{patent['id']}_consolidated_risk_assessment.md"
            if not check_file_exists(risk_assessment_file):
                patents_needing_assessment.append(patent)
            else:
                logger.info(f"⏭️  Skipping {patent['id']}: risk assessment already exists")
        
        if not patents_needing_assessment:
            logger.info(f"✅ All patents in {tier_info['name']} already have risk assessment")
            continue
        
        logger.info(f"📋 Found {len(patents_needing_assessment)} patents needing risk assessment")
        
        try:
            # Create and run crew for this tier (only risk assessment tasks)
            crew = create_enhanced_patent_crew(tier_key, patents_needing_assessment)
            
            logger.info(f"Starting risk assessment for {tier_info['name']}")
            start_time = datetime.now()
            
            results = crew.kickoff()
            
            end_time = datetime.now()
            processing_time = end_time - start_time
            
            logger.info(f"✅ Completed risk assessment for {tier_info['name']} in {processing_time}")
            
            # Save tier results
            tier_results = {
                'tier': tier_key,
                'tier_info': tier_info,
                'patent_count': len(patents_needing_assessment),
                'processing_time': str(processing_time),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'patents_processed': [p['id'] for p in patents_needing_assessment],
                'status': 'COMPLETED',
                'results_summary': str(results)[:1000],
                'mode': 'CONSOLIDATED_RISK_ASSESSMENT'
            }
            
            # Save to JSON
            results_file = Path(f"patent_output/{tier_key}/risk_assessment_results.json")
            with open(results_file, 'w') as f:
                json.dump(tier_results, f, indent=2)
            
            processing_results[tier_key] = tier_results
            total_patents_processed += len(patents_needing_assessment)
            
        except Exception as e:
            logger.error(f"❌ Error processing {tier_info['name']}: {e}")
            processing_results[tier_key] = {
                'tier': tier_key,
                'tier_info': tier_info,
                'patent_count': len(patents_needing_assessment),
                'status': 'ERROR',
                'error': str(e),
                'mode': 'CONSOLIDATED_RISK_ASSESSMENT'
            }
    
    # Generate summary
    generate_enhanced_portfolio_summary(processing_results, total_patents_processed)
    
    return len(processing_results) > 0

def run_ip_validation_only(tier_filter: Optional[str] = None, max_patents_per_tier: Optional[int] = None):
    """Run only IP validation (prior art search) for existing patents"""
    
    logger.info("🔍 Running IP Validation Only Mode")
    logger.info("=" * 80)
    logger.info("This will only run prior art search and IP validation for patents that don't have them yet.")
    
    # Validate environment and data
    if not validate_patent_data(PATENT_IDEAS):
        logger.error("❌ Patent data validation failed")
        return False
    
    # Setup output directories
    setup_output_directories()
    
    # Process each tier
    processing_results = {}
    total_patents_processed = 0
    
    for tier_key in ['tier_1', 'tier_2', 'tier_3']:
        if tier_filter and tier_key != tier_filter:
            continue
        
        tier_info = PATENT_CONFIG['portfolio_tiers'][tier_key]
        patent_ideas = PATENT_IDEAS.get(tier_key, [])
        
        if max_patents_per_tier:
            patent_ideas = patent_ideas[:max_patents_per_tier]
        
        if not patent_ideas:
            logger.warning(f"No patent ideas defined for {tier_info['name']}")
            continue
        
        logger.info(f"🎯 Processing IP validation for {tier_info['name']}")
        logger.info(f"   Count: {len(patent_ideas)} patents")
        
        # Filter patents that need IP validation
        patents_needing_validation = []
        for patent in patent_ideas:
            prior_art_file = f"patent_output/{tier_key}/{patent['id']}_prior_art_analysis.md"
            if not check_file_exists(prior_art_file):
                patents_needing_validation.append(patent)
            else:
                logger.info(f"⏭️  Skipping {patent['id']}: prior art analysis already exists")
        
        if not patents_needing_validation:
            logger.info(f"✅ All patents in {tier_info['name']} already have IP validation")
            continue
        
        logger.info(f"📋 Found {len(patents_needing_validation)} patents needing IP validation")
        
        try:
            # Create and run crew for this tier (only IP validation tasks)
            crew = create_enhanced_patent_crew(tier_key, patents_needing_validation)
            
            logger.info(f"Starting IP validation for {tier_info['name']}")
            start_time = datetime.now()
            
            results = crew.kickoff()
            
            end_time = datetime.now()
            processing_time = end_time - start_time
            
            logger.info(f"✅ Completed IP validation for {tier_info['name']} in {processing_time}")
            
            # Save tier results
            tier_results = {
                'tier': tier_key,
                'tier_info': tier_info,
                'patent_count': len(patents_needing_validation),
                'processing_time': str(processing_time),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'patents_processed': [p['id'] for p in patents_needing_validation],
                'status': 'COMPLETED',
                'results_summary': str(results)[:1000],
                'mode': 'IP_VALIDATION_ONLY'
            }
            
            # Save to JSON
            results_file = Path(f"patent_output/{tier_key}/ip_validation_results.json")
            with open(results_file, 'w') as f:
                json.dump(tier_results, f, indent=2)
            
            processing_results[tier_key] = tier_results
            total_patents_processed += len(patents_needing_validation)
            
        except Exception as e:
            logger.error(f"❌ Error processing {tier_info['name']}: {e}")
            processing_results[tier_key] = {
                'tier': tier_key,
                'tier_info': tier_info,
                'patent_count': len(patents_needing_validation),
                'status': 'ERROR',
                'error': str(e),
                'mode': 'IP_VALIDATION_ONLY'
            }
    
    # Generate summary
    generate_enhanced_portfolio_summary(processing_results, total_patents_processed)
    
    return len(processing_results) > 0

def run_enhanced_patent_automation(tier_filter: Optional[str] = None, max_patents_per_tier: Optional[int] = None):
    """Run full enhanced patent automation pipeline"""
    
    logger.info("🚀 Running Enhanced Patent Automation Pipeline")
    logger.info("=" * 80)
    logger.info("This will run the complete patent automation pipeline including:")
    logger.info("- Prior art search and IP validation")
    logger.info("- Claims refinement and optimization")
    logger.info("- Patent application generation")
    logger.info("- Legal review and strategy")
    logger.info("- Final review and quality assurance")
    logger.info("- Cover sheet generation")
    
    # Validate environment and data
    if not validate_patent_data(PATENT_IDEAS):
        logger.error("❌ Patent data validation failed")
        return False
    
    # Setup output directories
    setup_output_directories()
    
    # Process each tier
    processing_results = {}
    total_patents_processed = 0
    
    for tier_key in ['tier_1', 'tier_2', 'tier_3']:
        logger.info(f"🔍 Checking tier: {tier_key}")
        if tier_filter and tier_key != tier_filter:
            logger.info(f"⏭️  Skipping {tier_key} - filtered to {tier_filter}")
            continue
        
        tier_info = PATENT_CONFIG['portfolio_tiers'][tier_key]
        patent_ideas = PATENT_IDEAS.get(tier_key, [])
        logger.info(f"📋 Found {len(patent_ideas)} patents in {tier_key}")
        
        if max_patents_per_tier:
            patent_ideas = patent_ideas[:max_patents_per_tier]
            logger.info(f"📊 Limited to {len(patent_ideas)} patents (max_per_tier: {max_patents_per_tier})")
        
        if not patent_ideas:
            logger.warning(f"No patent ideas defined for {tier_info['name']}")
            continue
        
        logger.info(f"🎯 Processing full automation for {tier_info['name']}")
        logger.info(f"   Count: {len(patent_ideas)} patents")
        
        try:
            # Create and run crew for this tier
            crew = create_enhanced_patent_crew(tier_key, patent_ideas)
            
            logger.info(f"Starting full automation for {tier_info['name']}")
            start_time = datetime.now()
            
            results = crew.kickoff()
            
            end_time = datetime.now()
            processing_time = end_time - start_time
            
            logger.info(f"✅ Completed full automation for {tier_info['name']} in {processing_time}")
            
            # Save tier results
            tier_results = {
                'tier': tier_key,
                'tier_info': tier_info,
                'patent_count': len(patent_ideas),
                'processing_time': str(processing_time),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'patents_processed': [p['id'] for p in patent_ideas],
                'status': 'COMPLETED',
                'results_summary': str(results)[:1000],
                'mode': 'FULL_AUTOMATION'
            }
            
            # Save to JSON
            results_file = Path(f"patent_output/{tier_key}/full_automation_results.json")
            with open(results_file, 'w') as f:
                json.dump(tier_results, f, indent=2)
            
            processing_results[tier_key] = tier_results
            total_patents_processed += len(patent_ideas)
            
        except Exception as e:
            logger.error(f"❌ Error processing {tier_info['name']}: {e}")
            processing_results[tier_key] = {
                'tier': tier_key,
                'tier_info': tier_info,
                'patent_count': len(patent_ideas),
                'status': 'ERROR',
                'error': str(e),
                'mode': 'FULL_AUTOMATION'
            }
    
    # Generate summary
    generate_enhanced_portfolio_summary(processing_results, total_patents_processed)
    
    return len(processing_results) > 0

def generate_enhanced_portfolio_summary(processing_results: Dict, total_patents_processed: int):
    """Generate enhanced portfolio summary with detailed analysis"""
    
    logger.info("📊 Generating Enhanced Portfolio Summary")
    logger.info("=" * 80)
    
    # Calculate summary statistics
    total_tiers = len(processing_results)
    successful_tiers = sum(1 for r in processing_results.values() if r.get('status') == 'COMPLETED')
    failed_tiers = total_tiers - successful_tiers
    
    total_patents = sum(r.get('patent_count', 0) for r in processing_results.values())
    successful_patents = sum(r.get('patent_count', 0) for r in processing_results.values() if r.get('status') == 'COMPLETED')
    
    # Fix: Compute success rate before f-string
    if total_patents > 0:
        success_rate = f"{(successful_patents/total_patents*100):.1f}%"
    else:
        success_rate = "0%"
    
    # Generate summary report
    summary = f"""
ENHANCED PATENT PORTFOLIO AUTOMATION SUMMARY
============================================

Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Tiers Processed: {total_tiers}
Successful Tiers: {successful_tiers}
Failed Tiers: {failed_tiers}
Total Patents: {total_patents}
Successfully Processed: {successful_patents}
Success Rate: {success_rate}

TIER DETAILS:
============
"""
    
    for tier_key, results in processing_results.items():
        tier_info = results.get('tier_info', {})
        status = results.get('status', 'UNKNOWN')
        patent_count = results.get('patent_count', 0)
        processing_time = results.get('processing_time', 'N/A')
        
        summary += f"""
{tier_info.get('name', tier_key)}:
- Status: {status}
- Patents: {patent_count}
- Processing Time: {processing_time}
"""
        
        if status == 'ERROR':
            summary += f"- Error: {results.get('error', 'Unknown error')}\n"
    
    summary += f"""
OVERALL ASSESSMENT:
==================

Portfolio Status: {'✅ SUCCESS' if successful_tiers == total_tiers else '⚠️ PARTIAL SUCCESS' if successful_tiers > 0 else '❌ FAILED'}

Recommendations:
"""
    
    if successful_tiers == total_tiers:
        summary += """
✅ All tiers processed successfully
✅ Portfolio automation completed
✅ Ready for filing and prosecution
"""
    elif successful_tiers > 0:
        summary += """
⚠️ Partial success - some tiers failed
🔧 Review failed tiers and retry
📋 Check error logs for specific issues
"""
    else:
        summary += """
❌ All tiers failed
🔧 Review configuration and dependencies
📋 Check error logs for root cause
🛠️ Verify API keys and network connectivity
"""
    
    # Save summary
    summary_file = Path("patent_output/portfolio_summary.md")
    with open(summary_file, 'w') as f:
        f.write(summary)
    
    logger.info("✅ Portfolio summary generated")
    logger.info(f"📄 Summary saved to: {summary_file}")
    
    return summary 