#!/usr/bin/env python3
"""
Smart Cache Management Script

This script provides utilities to manage the smart cache system:
- View cache statistics
- Clear cache (all or specific types)
- Perform health checks
- Monitor cache usage
- Analyze cache performance
"""

import argparse
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.smart_cache_manager import smart_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_cache_stats():
    """Display detailed cache statistics"""
    logger.info("📊 Smart Cache Statistics")
    logger.info("=" * 50)
    
    stats = smart_cache.get_cache_stats()
    
    if not stats:
        logger.error("❌ Could not retrieve cache statistics")
        return
    
    print(f"Cache Status: {'✅ Enabled' if stats['cache_enabled'] else '❌ Disabled'}")
    print(f"Total Entries: {stats['total_entries']}")
    print(f"Total Size: {stats['total_size_mb']:.1f}MB / {stats['max_size_mb']:.1f}MB")
    print(f"Utilization: {stats['utilization_percent']:.1f}%")
    
    if stats['oldest_entry']:
        print(f"Oldest Entry: {stats['oldest_entry']}")
    if stats['newest_entry']:
        print(f"Newest Entry: {stats['newest_entry']}")
    
    print("\n📁 Content Type Breakdown:")
    for content_type, type_stats in stats['type_stats'].items():
        print(f"  {content_type}: {type_stats['count']} entries, {type_stats['size_bytes'] / (1024*1024):.1f}MB")

def perform_health_check():
    """Perform cache health check"""
    logger.info("🔍 Performing Smart Cache Health Check")
    logger.info("=" * 50)
    
    health_status = smart_cache.health_check()
    
    if health_status.get('is_healthy', False):
        print("✅ Cache Health: GOOD")
        print(f"Corrupted Entries: {health_status['corrupted_entries']}")
        print(f"Last Check: {health_status['last_check']}")
        
        if health_status['stats']:
            stats = health_status['stats']
            print(f"Total Entries: {stats['total_entries']}")
            print(f"Cache Size: {stats['total_size_mb']:.1f}MB")
    else:
        print("❌ Cache Health: POOR")
        if 'error' in health_status:
            print(f"Error: {health_status['error']}")
        print(f"Last Check: {health_status['last_check']}")

def clear_cache(cache_type=None):
    """Clear cache (all or specific type)"""
    if cache_type:
        logger.info(f"🧹 Clearing {cache_type} cache...")
        smart_cache.clear_cache(cache_type)
        print(f"✅ Cleared {cache_type} cache")
    else:
        logger.info("🧹 Clearing all cache...")
        smart_cache.clear_cache()
        print("✅ Cleared all cache")

def show_cache_performance():
    """Show cache performance metrics"""
    logger.info("⚡ Cache Performance Analysis")
    logger.info("=" * 50)
    
    stats = smart_cache.get_cache_stats()
    
    if not stats:
        logger.error("❌ Could not retrieve cache statistics")
        return
    
    # Calculate performance metrics
    total_entries = stats['total_entries']
    total_size_mb = stats['total_size_mb']
    utilization = stats['utilization_percent']
    
    print(f"Cache Efficiency Metrics:")
    print(f"  Average Entry Size: {total_size_mb / max(total_entries, 1):.2f}MB per entry")
    print(f"  Space Utilization: {utilization:.1f}%")
    
    # Performance recommendations
    print(f"\n💡 Performance Recommendations:")
    
    if utilization > 80:
        print("  ⚠️  High cache utilization - consider increasing cache size or clearing old entries")
    elif utilization < 20:
        print("  ℹ️  Low cache utilization - cache size may be oversized")
    else:
        print("  ✅ Cache utilization is optimal")
    
    if total_entries > 1000:
        print("  ⚠️  Large number of entries - consider implementing cache expiration")
    
    # Content type analysis
    if stats['type_stats']:
        print(f"\n📈 Content Type Analysis:")
        for content_type, type_stats in stats['type_stats'].items():
            avg_size = type_stats['size_bytes'] / max(type_stats['count'], 1) / (1024*1024)
            print(f"  {content_type}: {type_stats['count']} entries, avg {avg_size:.2f}MB each")

def show_cache_commands():
    """Show available cache management commands"""
    logger.info("🛠️  Available Cache Management Commands")
    logger.info("=" * 50)
    
    print("Basic Commands:")
    print("  python scripts/manage_smart_cache.py --stats")
    print("  python scripts/manage_smart_cache.py --health")
    print("  python scripts/manage_smart_cache.py --clear")
    print("  python scripts/manage_smart_cache.py --clear-type patent_data")
    print("  python scripts/manage_smart_cache.py --performance")
    
    print("\nCache Types:")
    print("  - patent_data: Patent search results from external APIs")
    print("  - academic_papers: Academic paper search results from arXiv")
    print("  - embeddings: Sentence transformer embeddings")
    print("  - models: Cached ML models")
    print("  - vector_results: Vector analysis results")
    
    print("\nExamples:")
    print("  # View cache statistics")
    print("  python scripts/manage_smart_cache.py --stats")
    print("")
    print("  # Clear only patent data cache")
    print("  python scripts/manage_smart_cache.py --clear-type patent_data")
    print("")
    print("  # Check cache health")
    print("  python scripts/manage_smart_cache.py --health")

def main():
    parser = argparse.ArgumentParser(
        description='Smart Cache Management for Patent Automation System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/manage_smart_cache.py --stats
  python scripts/manage_smart_cache.py --health
  python scripts/manage_smart_cache.py --clear
  python scripts/manage_smart_cache.py --clear-type patent_data
  python scripts/manage_smart_cache.py --performance
        """
    )
    
    parser.add_argument('--stats', action='store_true', 
                       help='Show cache statistics')
    parser.add_argument('--health', action='store_true', 
                       help='Perform cache health check')
    parser.add_argument('--clear', action='store_true', 
                       help='Clear all cache')
    parser.add_argument('--clear-type', type=str, 
                       choices=['patent_data', 'academic_papers', 'embeddings', 'models', 'vector_results'],
                       help='Clear specific cache type')
    parser.add_argument('--performance', action='store_true', 
                       help='Show cache performance analysis')
    parser.add_argument('--help-commands', action='store_true', 
                       help='Show available commands and examples')
    
    args = parser.parse_args()
    
    # Default action if no arguments provided
    if not any([args.stats, args.health, args.clear, args.clear_type, args.performance, args.help_commands]):
        show_cache_stats()
        return
    
    if args.help_commands:
        show_cache_commands()
    elif args.stats:
        show_cache_stats()
    elif args.health:
        perform_health_check()
    elif args.clear:
        clear_cache()
    elif args.clear_type:
        clear_cache(args.clear_type)
    elif args.performance:
        show_cache_performance()

if __name__ == "__main__":
    main() 