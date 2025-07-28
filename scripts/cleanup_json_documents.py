#!/usr/bin/env python3
"""
Script to clean up JSON-wrapped documents from patent automation output
Extracts content from JSON format and writes clean text files
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def extract_json_content(file_path: str) -> Tuple[str, bool]:
    """
    Extract content from JSON-wrapped file
    Returns (content, was_json_wrapped)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Try to parse as JSON
        try:
            data = json.loads(content)
            
            # Check for known JSON field names
            json_fields = [
                'valuation_content',
                'patent_content', 
                'analysis_content',
                'final_review_content',
                'editorial_feedback_content',
                'legal_review_content',
                'refined_claims_content',
                'cover_sheet_content',
                'diagram_content',
                'content'
            ]
            
            # Find the field that contains content
            for field in json_fields:
                if field in data and isinstance(data[field], str):
                    # Replace \n with actual newlines
                    clean_content = data[field].replace('\\n', '\n')
                    return clean_content, True
            
            # If no known field found, return original content
            return content, False
            
        except json.JSONDecodeError:
            # Not JSON, return as-is
            return content, False
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return "", False

def clean_document_file(file_path: str, dry_run: bool = False) -> bool:
    """
    Clean a single document file
    Returns True if file was cleaned, False if no changes needed
    """
    content, was_json = extract_json_content(file_path)
    
    if not was_json:
        return False
    
    if dry_run:
        print(f"Would clean: {file_path}")
        return True
    
    # Write clean content back to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing {file_path}: {e}")
        return False

def find_json_wrapped_files(output_dir: str = "output") -> List[str]:
    """
    Find all files that appear to be JSON-wrapped documents
    """
    json_wrapped_files = []
    
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith('.md') or file.endswith('.txt'):
                file_path = os.path.join(root, file)
                
                # Skip certain files
                if any(skip in file for skip in ['_log.md', '_tracking.json', '.DS_Store']):
                    continue
                
                # Check if file is JSON-wrapped
                _, was_json = extract_json_content(file_path)
                if was_json:
                    json_wrapped_files.append(file_path)
    
    return json_wrapped_files

def main():
    """Main cleanup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up JSON-wrapped documents")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned without making changes')
    parser.add_argument('--output-dir', default='output', help='Output directory to clean (default: output)')
    
    args = parser.parse_args()
    
    print("🧹 JSON Document Cleanup Tool")
    print("=" * 50)
    
    # Find all JSON-wrapped files
    json_files = find_json_wrapped_files(args.output_dir)
    
    if not json_files:
        print("✅ No JSON-wrapped files found!")
        return
    
    print(f"Found {len(json_files)} JSON-wrapped files:")
    for file_path in json_files:
        print(f"  - {file_path}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No changes will be made")
        for file_path in json_files:
            clean_document_file(file_path, dry_run=True)
        return
    
    # Confirm before proceeding
    response = input(f"\nProceed with cleaning {len(json_files)} files? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cancelled")
        return
    
    # Clean files
    print("\n🧹 Cleaning files...")
    cleaned_count = 0
    
    for file_path in json_files:
        if clean_document_file(file_path):
            cleaned_count += 1
            print(f"✅ Cleaned: {file_path}")
        else:
            print(f"❌ Failed: {file_path}")
    
    print(f"\n🎉 Cleanup complete!")
    print(f"   Files cleaned: {cleaned_count}")
    print(f"   Files failed: {len(json_files) - cleaned_count}")

if __name__ == "__main__":
    main() 