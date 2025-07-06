#!/usr/bin/env python3
"""
Script to remove fake filing information from all files in tier_1 folder
"""

import os
import re
from pathlib import Path

def clean_fake_filing_info(content: str) -> str:
    """Remove fake filing information from document content"""
    
    # Remove Application Number lines
    content = re.sub(r'Application Number:.*?\n', '', content)
    
    # Remove Filing Date lines
    content = re.sub(r'Filing Date:.*?\n', '', content)
    
    # Remove Patent ID lines
    content = re.sub(r'Patent ID:.*?\n', '', content)
    
    # Remove Inventor lines (since they're part of the fake filing info)
    content = re.sub(r'Inventor:.*?\n', '', content)
    
    # Replace "PROVISIONAL PATENT APPLICATION" headers with "PATENT ANALYSIS DOCUMENT"
    content = re.sub(r'PROVISIONAL PATENT APPLICATION', 'PATENT ANALYSIS DOCUMENT', content)
    
    # Clean up any double newlines that might result
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    return content

def clean_files_in_tier():
    """Clean all files in tier_1 folder to remove fake filing information"""
    tier_dir = Path("patent_output/tier_1")
    
    if not tier_dir.exists():
        print("❌ tier_1 directory not found")
        return
    
    cleaned_count = 0
    
    # Get all files in the directory
    for file_path in tier_dir.iterdir():
        if file_path.is_file() and file_path.suffix in ['.md', '.txt']:
            try:
                # Read the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if file contains fake filing information
                if any(keyword in content for keyword in ['Application Number:', 'Filing Date:', 'Patent ID:', 'Inventor:']):
                    # Clean the content
                    cleaned_content = clean_fake_filing_info(content)
                    
                    # Write back the cleaned content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_content)
                    
                    print(f"✅ Cleaned: {file_path.name}")
                    cleaned_count += 1
                else:
                    print(f"⏭️  No fake info found: {file_path.name}")
                    
            except Exception as e:
                print(f"❌ Failed to clean {file_path.name}: {e}")
    
    print(f"\n🎉 Cleaned {cleaned_count} files successfully!")

if __name__ == "__main__":
    print("🔄 Cleaning fake filing information from tier_1 files...")
    clean_files_in_tier() 