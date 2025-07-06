#!/usr/bin/env python3
"""
Context Management Script for Patent Automation System
Helps prevent context size growth and manage vector cache
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_directory_size(directory: Path) -> int:
    """Get total size of directory in bytes"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        logger.warning(f"Error calculating size for {directory}: {e}")
    return total_size

def format_size(size_bytes: int) -> str:
    """Format bytes to human readable size"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

def clear_vector_cache():
    """Clear vector cache directory"""
    cache_dir = Path("vector_cache")
    if cache_dir.exists():
        try:
            size_before = get_directory_size(cache_dir)
            shutil.rmtree(cache_dir)
            cache_dir.mkdir(exist_ok=True)
            logger.info(f"🧹 Cleared vector cache ({format_size(size_before)} removed)")
            return True
        except Exception as e:
            logger.error(f"Failed to clear vector cache: {e}")
            return False
    else:
        logger.info("Vector cache directory does not exist")
        return True

def clear_output_directories():
    """Clear patent output directories"""
    output_dir = Path("output")
    if output_dir.exists():
        try:
            size_before = get_directory_size(output_dir)
            shutil.rmtree(output_dir)
            output_dir.mkdir(exist_ok=True)
            
            # Recreate tier directories
            for tier in ['tier_1', 'tier_2', 'tier_3']:
                (output_dir / tier).mkdir(exist_ok=True)
            
            logger.info(f"🧹 Cleared output directories ({format_size(size_before)} removed)")
            return True
        except Exception as e:
            logger.error(f"Failed to clear output directories: {e}")
            return False
    else:
        logger.info("Output directory does not exist")
        return True

def show_system_status():
    """Show current system status and sizes"""
    logger.info("📊 System Status Report")
    logger.info("=" * 50)
    
    # Check vector cache
    cache_dir = Path("vector_cache")
    if cache_dir.exists():
        cache_size = get_directory_size(cache_dir)
        cache_files = len(list(cache_dir.rglob("*")))
        logger.info(f"Vector Cache: {format_size(cache_size)} ({cache_files} files)")
    else:
        logger.info("Vector Cache: Not found")
    
    # Check output directories
    output_dir = Path("output")
    if output_dir.exists():
        output_size = get_directory_size(output_dir)
        output_files = len(list(output_dir.rglob("*")))
        logger.info(f"Output Directory: {format_size(output_size)} ({output_files} files)")
    else:
        logger.info("Output Directory: Not found")
    
    # Check log file
    log_file = Path("patent_automation.log")
    if log_file.exists():
        log_size = log_file.stat().st_size
        logger.info(f"Log File: {format_size(log_size)}")
    else:
        logger.info("Log File: Not found")

def estimate_context_impact():
    """Estimate the impact of cache on context size"""
    logger.info("🔍 Context Size Impact Analysis")
    logger.info("=" * 50)
    
    cache_dir = Path("vector_cache")
    if cache_dir.exists():
        # Count embedding files
        embedding_files = list(cache_dir.glob("*.pkl"))
        total_embeddings = len(embedding_files)
        
        if total_embeddings > 0:
            # Rough estimate: each embedding file can add 1000-5000 tokens to context
            estimated_tokens = total_embeddings * 3000  # conservative estimate
            logger.info(f"Found {total_embeddings} embedding files")
            logger.info(f"Estimated context impact: ~{estimated_tokens:,} tokens")
            
            if estimated_tokens > 50000:
                logger.warning("⚠️  High context impact detected! Consider clearing cache.")
            elif estimated_tokens > 20000:
                logger.info("⚠️  Moderate context impact detected.")
            else:
                logger.info("✅ Low context impact detected.")
        else:
            logger.info("No embedding files found in cache")
    else:
        logger.info("Vector cache directory not found")

def main():
    parser = argparse.ArgumentParser(description='Manage context and cache for Patent Automation System')
    parser.add_argument('--clear-cache', action='store_true', help='Clear vector cache')
    parser.add_argument('--clear-outputs', action='store_true', help='Clear output directories')
    parser.add_argument('--clear-all', action='store_true', help='Clear both cache and outputs')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--analyze', action='store_true', help='Analyze context impact')
    
    args = parser.parse_args()
    
    if args.status:
        show_system_status()
    
    if args.analyze:
        estimate_context_impact()
    
    if args.clear_cache:
        clear_vector_cache()
    
    if args.clear_outputs:
        clear_output_directories()
    
    if args.clear_all:
        clear_vector_cache()
        clear_output_directories()
    
    # Default action if no arguments provided
    if not any([args.clear_cache, args.clear_outputs, args.clear_all, args.status, args.analyze]):
        show_system_status()
        print("\nUse --help for available options")

if __name__ == "__main__":
    main() 