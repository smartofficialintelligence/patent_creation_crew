#!/usr/bin/env python3
"""
Cleanup script for monitoring data files
Removes excessive monitoring data JSON files to keep output directory clean
"""

import os
import glob
import argparse
from datetime import datetime, timedelta

def cleanup_monitoring_data(output_dir="output", dry_run=False, keep_recent_hours=24):
    """Clean up excessive monitoring data files"""
    
    # Find all monitoring data files
    monitoring_files = glob.glob(os.path.join(output_dir, "monitoring_data_*.json"))
    summary_files = glob.glob(os.path.join(output_dir, "monitoring_summary_*.json"))
    
    print(f"🔍 Found {len(monitoring_files)} monitoring data files")
    print(f"🔍 Found {len(summary_files)} monitoring summary files")
    
    if not monitoring_files and not summary_files:
        print("✅ No monitoring files to clean up")
        return
    
    # Calculate cutoff time for keeping recent files
    cutoff_time = datetime.now() - timedelta(hours=keep_recent_hours)
    
    files_to_remove = []
    files_to_keep = []
    total_size = 0
    
    # Check monitoring data files (these are the problematic ones)
    for file_path in monitoring_files:
        try:
            # Extract timestamp from filename
            filename = os.path.basename(file_path)
            timestamp_str = filename.replace("monitoring_data_", "").replace(".json", "")
            file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            
            file_size = os.path.getsize(file_path)
            total_size += file_size
            
            if file_time < cutoff_time:
                files_to_remove.append((file_path, file_size))
            else:
                files_to_keep.append((file_path, file_size))
                
        except (ValueError, OSError) as e:
            print(f"⚠️  Error processing {file_path}: {e}")
            files_to_remove.append((file_path, 0))
    
    # Keep summary files (they're useful and not excessive)
    for file_path in summary_files:
        try:
            file_size = os.path.getsize(file_path)
            total_size += file_size
            files_to_keep.append((file_path, file_size))
        except OSError:
            pass
    
    # Report findings
    remove_size = sum(size for _, size in files_to_remove)
    keep_size = sum(size for _, size in files_to_keep)
    
    print(f"\n📊 Analysis:")
    print(f"   Total files: {len(monitoring_files) + len(summary_files)}")
    print(f"   Files to remove: {len(files_to_remove)} ({remove_size / 1024:.1f} KB)")
    print(f"   Files to keep: {len(files_to_keep)} ({keep_size / 1024:.1f} KB)")
    print(f"   Total size: {total_size / 1024:.1f} KB")
    
    if not files_to_remove:
        print("✅ No files need to be removed")
        return
    
    if dry_run:
        print(f"\n🧪 DRY RUN - Would remove {len(files_to_remove)} files:")
        for file_path, size in files_to_remove:
            print(f"   - {os.path.basename(file_path)} ({size / 1024:.1f} KB)")
        print("\nRun without --dry-run to actually remove files")
        return
    
    # Remove files
    removed_count = 0
    removed_size = 0
    
    print(f"\n🗑️  Removing {len(files_to_remove)} files...")
    
    for file_path, size in files_to_remove:
        try:
            os.remove(file_path)
            removed_count += 1
            removed_size += size
            print(f"   ✅ Removed: {os.path.basename(file_path)}")
        except OSError as e:
            print(f"   ❌ Error removing {file_path}: {e}")
    
    print(f"\n🎉 Cleanup complete!")
    print(f"   Removed: {removed_count} files ({removed_size / 1024:.1f} KB)")
    print(f"   Freed up space: {removed_size / 1024:.1f} KB")

def main():
    parser = argparse.ArgumentParser(description="Clean up monitoring data files")
    parser.add_argument("--output-dir", default="output", 
                       help="Output directory to clean (default: output)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be removed without actually removing")
    parser.add_argument("--keep-recent-hours", type=int, default=24,
                       help="Keep files from the last N hours (default: 24)")
    parser.add_argument("--remove-all", action="store_true",
                       help="Remove all monitoring data files (keep only summaries)")
    
    args = parser.parse_args()
    
    print("🧹 MONITORING DATA CLEANUP")
    print("=" * 50)
    
    if args.remove_all:
        print("⚠️  WARNING: --remove-all will remove ALL monitoring_data_*.json files")
        if not args.dry_run:
            confirm = input("Are you sure? (y/N): ")
            if confirm.lower() != 'y':
                print("Cancelled")
                return
        args.keep_recent_hours = 0  # Remove everything
    
    cleanup_monitoring_data(
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        keep_recent_hours=args.keep_recent_hours
    )

if __name__ == "__main__":
    main() 