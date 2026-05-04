#!/usr/bin/env python3
"""
Incremental Processor for Patent Automation System
Handles checking existing assets and only running tasks for missing outputs
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

def clean_patent_id(patent_id: str) -> str:
    """Return patent ID as-is (no prefix removal)"""
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

# Add retry tracking
class TaskRetryTracker:
    """Track retry attempts for individual tasks to prevent infinite loops"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_tracking_file = Path("output/task_retry_tracking.json")
        self.retry_counts = self._load_retry_counts()
    
    def _load_retry_counts(self) -> Dict[str, int]:
        """Load existing retry counts from file"""
        if self.retry_tracking_file.exists():
            try:
                with open(self.retry_tracking_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_retry_counts(self):
        """Save retry counts to file"""
        try:
            self.retry_tracking_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.retry_tracking_file, 'w') as f:
                json.dump(self.retry_counts, f, indent=2)
        except Exception as e:
            logging.warning(f"Failed to save retry counts: {e}")
    
    def get_task_key(self, patent_id: str, task_name: str) -> str:
        """Generate unique key for task retry tracking"""
        return f"{patent_id}_{task_name}"
    
    def can_retry_task(self, patent_id: str, task_name: str) -> bool:
        """Check if task can be retried (hasn't exceeded max retries)"""
        task_key = self.get_task_key(patent_id, task_name)
        current_count = self.retry_counts.get(task_key, 0)
        return current_count < self.max_retries
    
    def record_task_attempt(self, patent_id: str, task_name: str):
        """Record a task attempt (increment retry count)"""
        task_key = self.get_task_key(patent_id, task_name)
        self.retry_counts[task_key] = self.retry_counts.get(task_key, 0) + 1
        self._save_retry_counts()
        
        current_count = self.retry_counts[task_key]
        logging.info(f"Task retry: {task_key} attempt {current_count}/{self.max_retries}")
    
    def reset_task_retries(self, patent_id: str, task_name: str = None):
        """Reset retry count for a specific task or all tasks for a patent"""
        if task_name:
            task_key = self.get_task_key(patent_id, task_name)
            if task_key in self.retry_counts:
                del self.retry_counts[task_key]
        else:
            # Reset all tasks for this patent
            keys_to_remove = [key for key in self.retry_counts.keys() if key.startswith(f"{patent_id}_")]
            for key in keys_to_remove:
                del self.retry_counts[key]
        
        self._save_retry_counts()
    
    def get_retry_status(self, patent_id: str, task_name: str) -> Dict[str, Any]:
        """Get retry status for a task"""
        task_key = self.get_task_key(patent_id, task_name)
        current_count = self.retry_counts.get(task_key, 0)
        
        return {
            'task_key': task_key,
            'current_attempts': current_count,
            'max_attempts': self.max_retries,
            'can_retry': current_count < self.max_retries,
            'exhausted': current_count >= self.max_retries
        }
    
    def clear_all_retries(self):
        """Clear all retry tracking (for force regeneration)"""
        self.retry_counts = {}
        if self.retry_tracking_file.exists():
            self.retry_tracking_file.unlink()
        logging.info("Cleared all task retry tracking")

class IncrementalProcessor:
    """Handles incremental processing of patent assets"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.retry_tracker = TaskRetryTracker(max_retries=3)
        self.asset_status_cache: Dict[str, AssetStatus] = {}
        self.force_regenerate: Set[str] = set()
    
    def force_regenerate_all(self):
        """Force regeneration of all assets"""
        self.logger.info("🔄 Force regeneration enabled - clearing all retry tracking")
        self.retry_tracker.clear_all_retries()
        self.force_regenerate.clear()
        self.asset_status_cache.clear()
        self.logger.info("🔄 Force regeneration set for all assets")
    
    def should_skip_task(self, patent_id: str, task_name: str, output_file: str) -> bool:
        """
        Determine if a task should be skipped based on existing files and retry limits
        
        Returns True if task should be skipped, False if it should run
        """
        # Check if file exists and is valid
        if self._is_valid_output_file(output_file):
            return True  # Skip - file exists and is valid
        
        # Check retry limits
        if not self.retry_tracker.can_retry_task(patent_id, task_name):
            retry_status = self.retry_tracker.get_retry_status(patent_id, task_name)
            self.logger.warning(f"⚠️  Task {task_name} for {patent_id} has exceeded retry limit ({retry_status['current_attempts']}/{retry_status['max_attempts']})")
            return True  # Skip - exceeded retry limit
        
        return False  # Don't skip - file missing/invalid and retries available

    def record_task_execution(self, patent_id: str, task_name: str):
        """Record that a task is being executed (for retry tracking)"""
        self.retry_tracker.record_task_attempt(patent_id, task_name)

    def _is_valid_output_file(self, file_path: str) -> bool:
        """Check if an asset file exists and has meaningful content"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
            
        # Check file size
        try:
            file_size = file_path.stat().st_size
            if file_size < 100: # Minimum size for a valid file
                self.logger.warning(f"File {file_path} exists but is too small ({file_size} bytes)")
                return False
        except OSError:
            return False
            
        # For specific file types, do additional validation
        if file_path.suffix == '.ipynb':
            return self._validate_notebook_file(file_path)
        elif file_path.suffix == '.md':
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
                    self.logger.warning(f"Notebook {file_path} has no cells")
                    return False
                return True
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.logger.warning(f"Notebook {file_path} is not valid JSON")
            return False
        except Exception as e:
            self.logger.warning(f"Error validating notebook {file_path}: {e}")
            return False
    
    def _validate_markdown_file(self, file_path: Path) -> bool:
        """Validate that a markdown file has meaningful content"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # Check if it has substantial content (not just headers)
                lines = content.split('\n')
                non_empty_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
                
                # More lenient validation - check for minimal content or patent-related indicators
                if len(non_empty_lines) < 5:  # Reduced from 10 to 5 lines
                    # Check if it contains patent-related content indicators
                    content_lower = content.lower()
                    patent_indicators = ["patent", "invention", "claim", "analysis", "review", "technical", "application"]
                    has_patent_content = any(indicator in content_lower for indicator in patent_indicators)
                    
                    if not has_patent_content:
                        self.logger.warning(f"Markdown file {file_path} has insufficient content")
                        return False
                
                return True
        except Exception as e:
            self.logger.warning(f"Error validating markdown file {file_path}: {e}")
            return False
    
    def get_asset_status(self, patent_id: str, task_name: str, output_file: str) -> AssetStatus:
        """Get the status of a specific asset"""
        cache_key = f"{patent_id}_{task_name}"
        
        # Check cache first
        if cache_key in self.asset_status_cache and cache_key not in self.force_regenerate:
            return self.asset_status_cache[cache_key]
        
        # Check if file exists and is valid
        file_path = Path(output_file)
        exists = self._is_valid_output_file(output_file)
        
        if exists:
            try:
                stat = file_path.stat()
                file_size = stat.st_size
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                status = "exists"
            except OSError:
                file_size = 0
                last_modified = None
                status = "missing"
        else:
            file_size = 0
            last_modified = None
            status = "missing"
        
        # Create asset status
        asset_status = AssetStatus(
            patent_id=patent_id,
            task_name=task_name,
            output_file=output_file,
            exists=exists,
            file_size=file_size,
            last_modified=last_modified,
            status=status
        )
        
        # Cache the result
        self.asset_status_cache[cache_key] = asset_status
        
        return asset_status

    def should_run_task(self, patent_id: str, task_name: str, output_file: str) -> bool:
        """
        Determine if a task should be run based on existing files, force regeneration, and retry limits
        
        Returns True if task should run, False if it should be skipped
        """
        # Check force regeneration first
        cache_key = f"{patent_id}_{task_name}"
        if cache_key in self.force_regenerate:
            self.logger.info(f"🔄 Force regeneration for {patent_id} - {task_name}")
            return True
        
        # Use the new retry-aware logic
        if self.should_skip_task(patent_id, task_name, output_file):
            return False
        
        # If we get here, the task should run
        self.record_task_execution(patent_id, task_name)
        return True

    def check_asset_exists(self, output_file: str, min_size_bytes: int = 100) -> bool:
        """Check if an asset file exists and has meaningful content"""
        return self._is_valid_output_file(output_file)

    def force_regenerate_asset(self, patent_id: str, task_name: str):
        """Force regeneration of a specific asset"""
        cache_key = f"{patent_id}_{task_name}"
        self.force_regenerate.add(cache_key)
        self.logger.info(f"🔄 Force regeneration set for {patent_id} - {task_name}")
    
    def get_missing_assets_summary(self, patent_ideas: List[Dict], tasks_config: Dict, phase: str = None) -> Dict[str, Any]:
        """Get a summary of missing assets across all patents and tasks"""
        summary = {
            'total_patents': len(patent_ideas),
            'total_tasks': len([k for k in tasks_config.keys() if k != 'task_generation' and not k.startswith('colab_demo')]),
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
                # Skip metadata sections and task_generation config entry
                metadata_sections = ['task_dependencies', 'quality_gates', 'resource_management', 
                                   'error_recovery_strategies', 'task_priority', 'task_generation']
                if task_name in metadata_sections:
                    continue
                    
                # Skip colab demo tasks (per user request - found examples to be weak)
                if task_name.startswith('colab_demo'):
                    continue
                    
                # Use passed phase parameter, fall back to patent_idea phase, then 'unknown'
                phase_to_use = phase or patent_idea.get('phase', 'unknown')
                output_file = task_config['output_file'].format(
                    phase=phase_to_use,
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
                # Log completion calculation for debugging
                self.logger.debug(f"Patent {patent_id}: {len(patent_summary['existing_tasks'])}/{total_tasks} tasks complete ({patent_summary['completion_percentage']:.1f}%)")
            else:
                self.logger.warning(f"Patent {patent_id}: No tasks found for completion calculation")
            
            summary['patent_summary'][patent_id] = patent_summary
        
        return summary
    
    def print_missing_assets_report(self, patent_ideas: List[Dict], tasks_config: Dict, phase: str = None):
        """Print a detailed report of missing assets"""
        summary = self.get_missing_assets_summary(patent_ideas, tasks_config, phase)
        
        self.logger.info("=" * 80)
        self.logger.info("📊 INCREMENTAL PROCESSING REPORT")
        self.logger.info("=" * 80)
        
        total_assets = summary['total_patents'] * summary['total_tasks']
        existing_assets = len(summary['existing_assets'])
        missing_assets = len(summary['missing_assets'])
        
        self.logger.info(f"Total Patents: {summary['total_patents']}")
        self.logger.info(f"Total Tasks: {summary['total_tasks']}")
        self.logger.info(f"Existing Assets: {existing_assets}")
        self.logger.info(f"Missing Assets: {missing_assets}")
        if total_assets > 0:
            self.logger.info(f"Completion Rate: {(existing_assets/total_assets)*100:.1f}%")
        else:
            self.logger.info("Completion Rate: N/A (no patents to process)")
        
        if missing_assets > 0:
            self.logger.info("\n🔄 MISSING ASSETS:")
            for asset in summary['missing_assets']:
                self.logger.info(f"  - {asset['patent_id']} - {asset['task_name']}")
        
        self.logger.info("\n📈 PATENT COMPLETION SUMMARY:")
        for patent_id, patent_data in summary['patent_summary'].items():
            completion = patent_data['completion_percentage']
            status_icon = "✅" if completion == 100 else "🔄" if completion > 0 else "❌"
            self.logger.info(f"  {status_icon} {patent_id}: {completion:.1f}% complete")
            if patent_data['missing_tasks']:
                self.logger.info(f"     Missing: {', '.join(patent_data['missing_tasks'])}")
        
        self.logger.info("=" * 80)
    
    def filter_tasks_for_incremental_processing(self, tasks: List, patent_ideas: List[Dict]) -> List:
        """Filter tasks to only include those with missing assets"""
        filtered_tasks = []
        
        for task in tasks:
            # Extract patent_id and task_name from task description or output_file
            # This is a simplified approach - you might need to adjust based on your task structure
            task_name = getattr(task, 'description', '').split('\n')[0].split(':')[0].strip()
            
            # Try to get output_file from task, with fallback
            output_file = ''
            if hasattr(task, 'output_file'):
                output_file = task.output_file
            elif hasattr(task, 'expected_output'):
                # Fallback to expected_output if output_file not available
                output_file = str(task.expected_output)
            
            # Find the patent_id from the output_file path (exact match to avoid substring issues)
            patent_id = None
            for patent_idea in patent_ideas:
                # Use exact match with word boundaries to avoid P000 matching P004
                if f"/{patent_idea['id']}_" in output_file or output_file.endswith(f"/{patent_idea['id']}."):
                    patent_id = patent_idea['id']
                    break
            
            # Fallback: if no exact match found, try alternative patterns
            if not patent_id:
                import re
                for patent_idea in patent_ideas:
                    # Match patent ID at word boundaries (e.g., P000_ or P000.)
                    pattern = rf'\b{re.escape(patent_idea["id"])}\b'
                    if re.search(pattern, output_file):
                        patent_id = patent_idea['id']
                        break
            
            if patent_id and self.should_run_task(patent_id, task_name, output_file):
                filtered_tasks.append(task)
                self.logger.info(f"🔄 Including task: {task_name} for patent {patent_id}")
            else:
                self.logger.info(f"⏭️ Skipping task: {task_name} for patent {patent_id} (asset exists)")
        
        return filtered_tasks 