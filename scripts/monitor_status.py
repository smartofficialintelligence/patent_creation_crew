#!/usr/bin/env python3
"""
Status monitoring script for patent automation system
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.resource_manager import get_status_report, resource_manager

def main():
    """Show current status of the patent automation system"""
    
    print("🔍 Patent Automation System Status")
    print("=" * 50)
    
    # Check if monitoring is active
    if resource_manager and resource_manager.monitoring:
        print("✅ Resource monitoring is ACTIVE")
        status = get_status_report()
        
        # Resource status
        resource_status = status.get('resource_status', {})
        if resource_status:
            print(f"\n📊 RESOURCE USAGE:")
            print(f"   Memory: {resource_status.get('memory_gb', 0):.1f}GB / {resource_status.get('memory_percent', 0):.1f}% of limit")
            print(f"   CPU: {resource_status.get('cpu_percent', 0):.1f}% / {resource_status.get('cpu_percent_of_limit', 0):.1f}% of limit")
            print(f"   Disk: {resource_status.get('disk_gb', 0):.1f}GB / {resource_status.get('disk_percent', 0):.1f}% of limit")
            print(f"   Time: {resource_status.get('elapsed_minutes', 0):.1f}min / {resource_status.get('timeout_percent', 0):.1f}% of limit")
            
            # Peak usage
            print(f"\n📈 PEAK USAGE:")
            print(f"   Peak Memory: {resource_status.get('peak_memory_gb', 0):.1f}GB")
            print(f"   Peak CPU: {resource_status.get('peak_cpu_percent', 0):.1f}%")
        
        # Progress status
        progress_summary = status.get('progress_summary', {})
        if progress_summary:
            print(f"\n📈 PROGRESS:")
            print(f"   Patents: {progress_summary.get('completed_patents', 0)}/{progress_summary.get('total_patents', 0)} ({progress_summary.get('patent_success_rate', 0):.1f}%)")
            print(f"   Tasks: {progress_summary.get('completed_tasks', 0)}/{progress_summary.get('total_tasks', 0)} ({progress_summary.get('task_success_rate', 0):.1f}%)")
            print(f"   Failed Tasks: {progress_summary.get('failed_tasks', 0)}")
            print(f"   Total Time: {progress_summary.get('total_time_minutes', 0):.1f} minutes")
            print(f"   Avg Task Time: {progress_summary.get('avg_task_time_seconds', 0):.1f} seconds")
            
            # Estimated remaining time
            remaining = progress_summary.get('estimated_remaining_minutes', 0)
            if remaining > 0:
                print(f"   Estimated Remaining: {remaining:.1f} minutes")
        
        # Error status
        error_summary = status.get('error_summary', {})
        if error_summary:
            print(f"\n❌ ERRORS:")
            for error_key, count in error_summary.items():
                print(f"   {error_key}: {count} occurrences")
        else:
            print(f"\n✅ No errors encountered")
            
    else:
        print("⚠️ Resource monitoring is NOT ACTIVE")
        print("   Run the main automation script to start monitoring")
    
    # Check log file
    log_file = Path("patent_automation.log")
    if log_file.exists():
        log_size = log_file.stat().st_size / 1024  # KB
        log_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        print(f"\n📝 LOG FILE:")
        print(f"   Size: {log_size:.1f} KB")
        print(f"   Last Modified: {log_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show last few lines
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"\n📋 LAST LOG ENTRIES:")
                    for line in lines[-5:]:  # Last 5 lines
                        print(f"   {line.strip()}")
        except Exception as e:
            print(f"   Could not read log file: {e}")
    else:
        print(f"\n📝 No log file found")
    
    # Check output directories
    output_dir = Path("patent_output")
    if output_dir.exists():
        print(f"\n📁 OUTPUT DIRECTORY:")
        total_files = 0
        for tier_dir in output_dir.iterdir():
            if tier_dir.is_dir():
                files = list(tier_dir.glob("*"))
                print(f"   {tier_dir.name}: {len(files)} files")
                total_files += len(files)
        print(f"   Total files: {total_files}")
    else:
        print(f"\n📁 No output directory found")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main() 