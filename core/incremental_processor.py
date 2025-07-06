#!/usr/bin/env python3
"""
Incremental Processor for Patent Automation System
Handles checking existing assets and only running tasks for missing outputs
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

def clean_patent_id(patent_id: str) -> str:
    """Remove NEW- prefix from patent ID for file naming"""
    if patent_id.startswith("NEW-"):
        return patent_id[4:]  # Remove "NEW-" prefix
    return patent_id

@dataclass
class AssetStatus:
    """Status of a specific asset for a patent"""
    patent_id: str
    task_name: str
    output_file: str
    exists: bool
    file_size: int
    last_modified: Optional[datetime]
    status: str  # 'exists', 'missing', 'failed', 'in_progress'

class IncrementalProcessor:
    def __init__(self, output_base_dir: str = "patent_output"):
        self.output_base_dir = Path(output_base_dir)
        self.asset_status_cache: Dict[str, AssetStatus] = {}
        self.force_regenerate: Set[str] = set()
        
    def check_asset_exists(self, output_file: str, min_size_bytes: int = 100) -> bool:
        """Check if an asset file exists and has meaningful content"""
        file_path = Path(output_file)
        
        if not file_path.exists():
            return False
            
        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size < min_size_bytes:
                logger.warning(f"File {output_file} exists but is too small ({file_size} bytes)")
                return False
        except OSError:
            return False
            
        # For specific file types, do additional validation
        if output_file.endswith('.ipynb'):
            return self._validate_notebook_file(file_path)
        elif output_file.endswith('.md'):
            return self._validate_markdown_file(file_path)
            
        return True
    
    def _validate_notebook_file(self, file_path: Path) -> bool:
        """Validate that a notebook file is properly formatted"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # Check if it's valid JSON (notebook format)
                json.loads(content)
                # Check if it has cells
                notebook = json.loads(content)
                if 'cells' not in notebook or len(notebook['cells']) == 0:
                    logger.warning(f"Notebook {file_path} has no cells")
                    return False
                return True
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning(f"Notebook {file_path} is not valid JSON")
            return False
        except Exception as e:
            logger.warning(f"Error validating notebook {file_path}: {e}")
            return False
    
    def _validate_markdown_file(self, file_path: Path) -> bool:
        """Validate that a markdown file has meaningful content"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # Check if it has substantial content (not just headers)
                lines = content.split('\n')
                non_empty_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
                if len(non_empty_lines) < 10:  # At least 10 non-header lines
                    logger.warning(f"Markdown file {file_path} has insufficient content")
                    return False
                return True
        except Exception as e:
            logger.warning(f"Error validating markdown file {file_path}: {e}")
            return False
    
    def get_asset_status(self, patent_id: str, task_name: str, output_file: str) -> AssetStatus:
        """Get the status of a specific asset"""
        cache_key = f"{patent_id}_{task_name}"
        
        if cache_key in self.asset_status_cache:
            return self.asset_status_cache[cache_key]
        
        # Check if file exists
        exists = self.check_asset_exists(output_file)
        file_size = 0
        last_modified = None
        
        if exists:
            try:
                file_path = Path(output_file)
                stat = file_path.stat()
                file_size = stat.st_size
                last_modified = datetime.fromtimestamp(stat.st_mtime)
            except OSError:
                exists = False
        
        # Determine status
        if cache_key in self.force_regenerate:
            status = "missing"  # Force regeneration
        elif exists:
            status = "exists"
        else:
            status = "missing"
        
        asset_status = AssetStatus(
            patent_id=patent_id,
            task_name=task_name,
            output_file=output_file,
            exists=exists,
            file_size=file_size,
            last_modified=last_modified,
            status=status
        )
        
        self.asset_status_cache[cache_key] = asset_status
        return asset_status
    
    def should_run_task(self, patent_id: str, task_name: str, output_file: str) -> bool:
        """Determine if a task should be run based on asset status"""
        asset_status = self.get_asset_status(patent_id, task_name, output_file)
        
        if asset_status.status == "exists":
            logger.info(f"✅ Asset exists for {patent_id} - {task_name}: {output_file}")
            return False
        else:
            logger.info(f"🔄 Asset missing for {patent_id} - {task_name}: {output_file}")
            return True
    
    def force_regenerate_asset(self, patent_id: str, task_name: str):
        """Force regeneration of a specific asset"""
        cache_key = f"{patent_id}_{task_name}"
        self.force_regenerate.add(cache_key)
        logger.info(f"🔄 Force regeneration set for {patent_id} - {task_name}")
    
    def force_regenerate_all(self):
        """Force regeneration of all assets"""
        self.force_regenerate.clear()
        self.asset_status_cache.clear()
        logger.info("🔄 Force regeneration set for all assets")
    
    def get_missing_assets_summary(self, patent_ideas: List[Dict], tasks_config: Dict) -> Dict[str, Any]:
        """Get a summary of missing assets across all patents and tasks"""
        summary = {
            'total_patents': len(patent_ideas),
            'total_tasks': len([k for k in tasks_config.keys() if k != 'task_generation']),
            'missing_assets': [],
            'existing_assets': [],
            'patent_summary': {}
        }
        
        for patent_idea in patent_ideas:
            patent_id = patent_idea['id']
            patent_summary = {
                'patent_id': patent_id,
                'title': patent_idea.get('title', 'Unknown'),
                'missing_tasks': [],
                'existing_tasks': [],
                'completion_percentage': 0
            }
            
            for task_name, task_config in tasks_config.items():
                if task_name == 'task_generation':
                    continue
                    
                output_file = task_config['output_file'].format(
                    tier=patent_idea.get('tier', 'unknown'),
                    id=clean_patent_id(patent_id)
                )
                
                asset_status = self.get_asset_status(patent_id, task_name, output_file)
                
                if asset_status.status == "exists":
                    patent_summary['existing_tasks'].append(task_name)
                    summary['existing_assets'].append({
                        'patent_id': patent_id,
                        'task_name': task_name,
                        'output_file': output_file,
                        'file_size': asset_status.file_size,
                        'last_modified': asset_status.last_modified.isoformat() if asset_status.last_modified else None
                    })
                else:
                    patent_summary['missing_tasks'].append(task_name)
                    summary['missing_assets'].append({
                        'patent_id': patent_id,
                        'task_name': task_name,
                        'output_file': output_file
                    })
            
            # Calculate completion percentage
            total_tasks = len(patent_summary['existing_tasks']) + len(patent_summary['missing_tasks'])
            if total_tasks > 0:
                patent_summary['completion_percentage'] = (len(patent_summary['existing_tasks']) / total_tasks) * 100
            
            summary['patent_summary'][patent_id] = patent_summary
        
        return summary
    
    def print_missing_assets_report(self, patent_ideas: List[Dict], tasks_config: Dict):
        """Print a detailed report of missing assets"""
        summary = self.get_missing_assets_summary(patent_ideas, tasks_config)
        
        logger.info("=" * 80)
        logger.info("📊 INCREMENTAL PROCESSING REPORT")
        logger.info("=" * 80)
        
        total_assets = summary['total_patents'] * summary['total_tasks']
        existing_assets = len(summary['existing_assets'])
        missing_assets = len(summary['missing_assets'])
        
        logger.info(f"Total Patents: {summary['total_patents']}")
        logger.info(f"Total Tasks: {summary['total_tasks']}")
        logger.info(f"Existing Assets: {existing_assets}")
        logger.info(f"Missing Assets: {missing_assets}")
        if total_assets > 0:
            logger.info(f"Completion Rate: {(existing_assets/total_assets)*100:.1f}%")
        else:
            logger.info("Completion Rate: N/A (no patents to process)")
        
        if missing_assets > 0:
            logger.info("\n🔄 MISSING ASSETS:")
            for asset in summary['missing_assets']:
                logger.info(f"  - {asset['patent_id']} - {asset['task_name']}")
        
        logger.info("\n📈 PATENT COMPLETION SUMMARY:")
        for patent_id, patent_data in summary['patent_summary'].items():
            completion = patent_data['completion_percentage']
            status_icon = "✅" if completion == 100 else "🔄" if completion > 0 else "❌"
            logger.info(f"  {status_icon} {patent_id}: {completion:.1f}% complete")
            if patent_data['missing_tasks']:
                logger.info(f"     Missing: {', '.join(patent_data['missing_tasks'])}")
        
        logger.info("=" * 80)
    
    def filter_tasks_for_incremental_processing(self, tasks: List, patent_ideas: List[Dict]) -> List:
        """Filter tasks to only include those with missing assets"""
        filtered_tasks = []
        
        for task in tasks:
            # Extract patent_id and task_name from task description or output_file
            # This is a simplified approach - you might need to adjust based on your task structure
            task_name = getattr(task, 'description', '').split('\n')[0].split(':')[0].strip()
            output_file = getattr(task, 'output_file', '')
            
            # Find the patent_id from the output_file path
            patent_id = None
            for patent_idea in patent_ideas:
                if patent_idea['id'] in output_file:
                    patent_id = patent_idea['id']
                    break
            
            if patent_id and self.should_run_task(patent_id, task_name, output_file):
                filtered_tasks.append(task)
                logger.info(f"🔄 Including task: {task_name} for patent {patent_id}")
            else:
                logger.info(f"⏭️ Skipping task: {task_name} for patent {patent_id} (asset exists)")
        
        return filtered_tasks 