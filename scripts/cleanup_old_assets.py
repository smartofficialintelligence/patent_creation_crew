#!/usr/bin/env python3
"""
Script to clean up old patent assets that are no longer in the new tier structure
"""

import os
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_old_assets():
    """Move old patent assets to a backup location"""
    
    # Define the new Tier 1 patents
    new_tier_1_patents = ['P000', 'P001', 'P002', 'P003', 'P004']
    
    # Create backup directory
    backup_dir = Path("patent_output/backup_old_assets")
    backup_dir.mkdir(exist_ok=True)
    
    # Check tier_1 folder for old assets
    tier_1_dir = Path("patent_output/tier_1")
    if tier_1_dir.exists():
        moved_count = 0
        for file_path in tier_1_dir.iterdir():
            if file_path.is_file():
                # Extract patent ID from filename
                filename = file_path.name
                patent_id = filename.split('_')[0]
                
                # If this patent is not in the new Tier 1, move it to backup
                if patent_id not in new_tier_1_patents:
                    backup_file = backup_dir / filename
                    shutil.move(str(file_path), str(backup_file))
                    logger.info(f"📦 Moved {filename} to backup (not in new Tier 1)")
                    moved_count += 1
        
        if moved_count > 0:
            logger.info(f"✅ Moved {moved_count} old assets from tier_1 to backup")
        else:
            logger.info("✅ No old assets found in tier_1")
    
    # Check tier_2 folder - these are all old assets
    tier_2_dir = Path("patent_output/tier_2")
    if tier_2_dir.exists():
        moved_count = 0
        for file_path in tier_2_dir.iterdir():
            if file_path.is_file():
                filename = file_path.name
                backup_file = backup_dir / filename
                shutil.move(str(file_path), str(backup_file))
                logger.info(f"📦 Moved {filename} to backup (from old tier_2)")
                moved_count += 1
        
        if moved_count > 0:
            logger.info(f"✅ Moved {moved_count} old assets from tier_2 to backup")
    
    # Check tier_3 folder - these are all old assets
    tier_3_dir = Path("patent_output/tier_3")
    if tier_3_dir.exists():
        moved_count = 0
        for file_path in tier_3_dir.iterdir():
            if file_path.is_file():
                filename = file_path.name
                backup_file = backup_dir / filename
                shutil.move(str(file_path), str(backup_file))
                logger.info(f"📦 Moved {filename} to backup (from old tier_3)")
                moved_count += 1
        
        if moved_count > 0:
            logger.info(f"✅ Moved {moved_count} old assets from tier_3 to backup")
    
    # Move loose files in patent_output root
    output_dir = Path("patent_output")
    moved_count = 0
    for file_path in output_dir.iterdir():
        if file_path.is_file() and file_path.suffix in ['.json', '.md', '.ipynb']:
            filename = file_path.name
            backup_file = backup_dir / filename
            shutil.move(str(file_path), str(backup_file))
            logger.info(f"📦 Moved {filename} to backup (loose file)")
            moved_count += 1
    
    if moved_count > 0:
        logger.info(f"✅ Moved {moved_count} loose files to backup")
    
    # Remove empty directories
    for tier_dir in [tier_2_dir, tier_3_dir]:
        if tier_dir.exists() and not any(tier_dir.iterdir()):
            tier_dir.rmdir()
            logger.info(f"🗑️ Removed empty directory: {tier_dir}")
    
    logger.info("🎉 Cleanup completed! Old assets moved to patent_output/backup_old_assets/")
    logger.info("📁 New Tier 1 folder is now clean and ready for the new patent structure")

if __name__ == "__main__":
    cleanup_old_assets() 