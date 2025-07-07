#!/usr/bin/env python3
"""
Incremental Processing Manager for Patent Automation System
CLI tool for managing incremental processing and asset status
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.incremental_processor import IncrementalProcessor
from lib.patent_data import PATENT_IDEAS, PATENT_CONFIG
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_tasks_config():
    """Load tasks configuration from YAML"""
    try:
        with open('config/tasks.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load tasks configuration: {e}")
        return {}

def show_status(tier_filter=None, max_per_tier=None):
    """Show status of all assets"""
    logger.info("📊 INCREMENTAL PROCESSING STATUS")
    logger.info("=" * 80)
    
    incremental_processor = IncrementalProcessor()
    tasks_config = load_tasks_config()
    
    if not tasks_config:
        return False
    
    total_missing = 0
    total_existing = 0
    
    for tier_key in ['tier_1', 'tier_2', 'tier_3']:
        if tier_filter and tier_key != tier_filter:
            continue
            
        if tier_key not in PATENT_IDEAS:
            continue
            
        patent_ideas = PATENT_IDEAS[tier_key]
        if max_per_tier:
            patent_ideas = patent_ideas[:max_per_tier]
        
        tier_info = PATENT_CONFIG['portfolio_tiers'][tier_key]
        logger.info(f"\n🎯 {tier_info['name']} ({tier_key})")
        logger.info("-" * 60)
        
        summary = incremental_processor.get_missing_assets_summary(patent_ideas, tasks_config, tier_key)
        
        missing_count = len(summary['missing_assets'])
        existing_count = len(summary['existing_assets'])
        total_missing += missing_count
        total_existing += existing_count
        
        logger.info(f"Patents: {len(patent_ideas)}")
        logger.info(f"Missing Assets: {missing_count}")
        logger.info(f"Existing Assets: {existing_count}")
        
        if missing_count > 0:
            logger.info("\n🔄 Missing Assets:")
            for asset in summary['missing_assets']:
                logger.info(f"  - {asset['patent_id']} - {asset['task_name']}")
        
        logger.info("\n📈 Patent Completion:")
        for patent_id, patent_data in summary['patent_summary'].items():
            completion = patent_data['completion_percentage']
            status_icon = "✅" if completion == 100 else "🔄" if completion > 0 else "❌"
            logger.info(f"  {status_icon} {patent_id}: {completion:.1f}% complete")
            if patent_data['missing_tasks']:
                logger.info(f"     Missing: {', '.join(patent_data['missing_tasks'])}")
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 OVERALL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Missing Assets: {total_missing}")
    logger.info(f"Total Existing Assets: {total_existing}")
    total_assets = total_missing + total_existing
    if total_assets > 0:
        completion_rate = (total_existing / total_assets) * 100
        logger.info(f"Overall Completion Rate: {completion_rate:.1f}%")
    
    return True

def force_regenerate_specific(patent_id, task_name):
    """Force regeneration of a specific asset"""
    logger.info(f"🔄 Force regenerating {task_name} for patent {patent_id}")
    
    incremental_processor = IncrementalProcessor()
    incremental_processor.force_regenerate_asset(patent_id, task_name)
    
    logger.info(f"✅ Force regeneration set for {patent_id} - {task_name}")
    logger.info("Run the automation script to execute the regeneration")
    
    return True

def force_regenerate_all():
    """Force regeneration of all assets"""
    logger.info("🔄 Force regenerating ALL assets")
    
    incremental_processor = IncrementalProcessor()
    incremental_processor.force_regenerate_all()
    
    logger.info("✅ Force regeneration set for all assets")
    logger.info("Run the automation script to execute the regeneration")
    
    return True

def show_missing_only(tier_filter=None, max_per_tier=None):
    """Show only missing assets"""
    logger.info("🔄 MISSING ASSETS ONLY")
    logger.info("=" * 80)
    
    incremental_processor = IncrementalProcessor()
    tasks_config = load_tasks_config()
    
    if not tasks_config:
        return False
    
    missing_assets = []
    
    for tier_key in ['tier_1', 'tier_2', 'tier_3']:
        if tier_filter and tier_key != tier_filter:
            continue
            
        if tier_key not in PATENT_IDEAS:
            continue
            
        patent_ideas = PATENT_IDEAS[tier_key]
        if max_per_tier:
            patent_ideas = patent_ideas[:max_per_tier]
        
        tier_info = PATENT_CONFIG['portfolio_tiers'][tier_key]
        summary = incremental_processor.get_missing_assets_summary(patent_ideas, tasks_config, tier_key)
        
        if summary['missing_assets']:
            logger.info(f"\n🎯 {tier_info['name']} ({tier_key}) - Missing Assets:")
            for asset in summary['missing_assets']:
                missing_assets.append(asset)
                logger.info(f"  - {asset['patent_id']} - {asset['task_name']}")
    
    if not missing_assets:
        logger.info("✅ No missing assets found!")
    
    return True

def show_task_completion(tier_filter=None, max_per_tier=None):
    """Show completion status by task type"""
    logger.info("📊 TASK COMPLETION STATUS")
    logger.info("=" * 80)
    
    incremental_processor = IncrementalProcessor()
    tasks_config = load_tasks_config()
    
    if not tasks_config:
        return False
    
    task_stats = {}
    
    for tier_key in ['tier_1', 'tier_2', 'tier_3']:
        if tier_filter and tier_key != tier_filter:
            continue
            
        if tier_key not in PATENT_IDEAS:
            continue
            
        patent_ideas = PATENT_IDEAS[tier_key]
        if max_per_tier:
            patent_ideas = patent_ideas[:max_per_tier]
        
        summary = incremental_processor.get_missing_assets_summary(patent_ideas, tasks_config, tier_key)
        
        # Count by task type
        for asset in summary['existing_assets']:
            task_name = asset['task_name']
            if task_name not in task_stats:
                task_stats[task_name] = {'completed': 0, 'missing': 0}
            task_stats[task_name]['completed'] += 1
        
        for asset in summary['missing_assets']:
            task_name = asset['task_name']
            if task_name not in task_stats:
                task_stats[task_name] = {'completed': 0, 'missing': 0}
            task_stats[task_name]['missing'] += 1
    
    # Display task completion statistics
    for task_name, stats in sorted(task_stats.items()):
        total = stats['completed'] + stats['missing']
        completion_rate = (stats['completed'] / total) * 100 if total > 0 else 0
        status_icon = "✅" if completion_rate == 100 else "🔄" if completion_rate > 0 else "❌"
        
        logger.info(f"{status_icon} {task_name}: {stats['completed']}/{total} ({completion_rate:.1f}%)")
    
    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Incremental Processing Manager for Patent Automation System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show status of all assets
  python scripts/incremental_manager.py --status
  
  # Show only missing assets
  python scripts/incremental_manager.py --missing-only
  
  # Show task completion statistics
  python scripts/incremental_manager.py --task-stats
  
  # Force regenerate a specific asset
  python scripts/incremental_manager.py --force-regenerate patent_001 prior_art_research
  
  # Force regenerate all assets
  python scripts/incremental_manager.py --force-regenerate-all
  
  # Show status for specific tier
  python scripts/incremental_manager.py --status --tier tier_1
  
  # Show status with limited patents
  python scripts/incremental_manager.py --status --max-per-tier 2
        """
    )
    
    # Action arguments
    parser.add_argument('--status', action='store_true',
                       help='Show status of all assets')
    parser.add_argument('--missing-only', action='store_true',
                       help='Show only missing assets')
    parser.add_argument('--task-stats', action='store_true',
                       help='Show completion statistics by task type')
    parser.add_argument('--force-regenerate', nargs=2, metavar=('PATENT_ID', 'TASK_NAME'),
                       help='Force regeneration of a specific asset')
    parser.add_argument('--force-regenerate-all', action='store_true',
                       help='Force regeneration of all assets')
    
    # Filter arguments
    parser.add_argument('--tier', type=str, choices=['tier_1', 'tier_2', 'tier_3'],
                       help='Filter by specific tier')
    parser.add_argument('--max-per-tier', type=int,
                       help='Maximum number of patents to process per tier')
    
    args = parser.parse_args()
    
    # Validate that at least one action is specified
    actions = [args.status, args.missing_only, args.task_stats, 
               args.force_regenerate, args.force_regenerate_all]
    
    if not any(actions):
        parser.print_help()
        return False
    
    # Execute requested actions
    try:
        if args.status:
            show_status(args.tier, args.max_per_tier)
        
        if args.missing_only:
            show_missing_only(args.tier, args.max_per_tier)
        
        if args.task_stats:
            show_task_completion(args.tier, args.max_per_tier)
        
        if args.force_regenerate:
            patent_id, task_name = args.force_regenerate
            force_regenerate_specific(patent_id, task_name)
        
        if args.force_regenerate_all:
            force_regenerate_all()
        
        return True
        
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 