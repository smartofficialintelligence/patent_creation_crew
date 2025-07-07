# Resource management and monitoring for local laptop use

import os
import psutil
import time
import signal
import threading
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ResourceManager:
    """Resource management and monitoring for local laptop use"""
    
    def __init__(self, 
                 max_memory_gb: float = 12.0,  # Optimized for 16GB M1 Mac Pro (75% of total RAM)
                 max_cpu_percent: float = 85.0,  # Slightly higher for M1 efficiency
                 max_disk_gb: float = 4.0,  # More generous disk space for outputs
                 timeout_minutes: int = 120,  # Longer timeout for complex processing
                 check_interval: int = 30):
        
        self.max_memory_gb = max_memory_gb
        self.max_cpu_percent = max_cpu_percent
        self.max_disk_gb = max_disk_gb
        self.timeout_minutes = timeout_minutes
        self.check_interval = check_interval
        
        self.start_time = None
        self.monitoring = False
        self.monitor_thread = None
        self.stop_event = threading.Event()
        
        # Resource usage tracking
        self.peak_memory_gb = 0.0
        self.peak_cpu_percent = 0.0
        self.total_processing_time = 0.0
        
        # Alert callbacks
        self.memory_alert_callback = None
        self.cpu_alert_callback = None
        self.timeout_callback = None
        
    def start_monitoring(self):
        """Start resource monitoring"""
        if self.monitoring:
            return
            
        self.start_time = datetime.now()
        self.monitoring = True
        self.stop_event.clear()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info(f"🔍 Resource monitoring started (Memory: {self.max_memory_gb}GB, CPU: {self.max_cpu_percent}%, Timeout: {self.timeout_minutes}min)")
        
    def stop_monitoring(self):
        """Stop resource monitoring"""
        if not self.monitoring:
            return
            
        self.monitoring = False
        self.stop_event.set()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
        self.total_processing_time = (datetime.now() - self.start_time).total_seconds() / 60.0
        
        logger.info(f"⏹️ Resource monitoring stopped. Total time: {self.total_processing_time:.1f} minutes")
        self._log_resource_summary()
        
    def _monitor_resources(self):
        """Monitor system resources"""
        while self.monitoring and not self.stop_event.is_set():
            try:
                # Check memory usage
                memory_gb = psutil.virtual_memory().used / (1024**3)
                self.peak_memory_gb = max(self.peak_memory_gb, memory_gb)
                
                if memory_gb > self.max_memory_gb:
                    logger.warning(f"⚠️ High memory usage: {memory_gb:.1f}GB (limit: {self.max_memory_gb}GB)")
                    if self.memory_alert_callback:
                        self.memory_alert_callback(memory_gb)
                
                # Check CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.peak_cpu_percent = max(self.peak_cpu_percent, cpu_percent)
                
                if cpu_percent > self.max_cpu_percent:
                    logger.warning(f"⚠️ High CPU usage: {cpu_percent:.1f}% (limit: {self.max_cpu_percent}%)")
                    if self.cpu_alert_callback:
                        self.cpu_alert_callback(cpu_percent)
                
                # Check disk usage
                disk_usage = psutil.disk_usage('.').used / (1024**3)
                if disk_usage > self.max_disk_gb:
                    logger.warning(f"⚠️ High disk usage: {disk_usage:.1f}GB (limit: {self.max_disk_gb}GB)")
                
                # Check timeout
                if self.start_time:
                    elapsed_minutes = (datetime.now() - self.start_time).total_seconds() / 60.0
                    if elapsed_minutes > self.timeout_minutes:
                        logger.error(f"⏰ Processing timeout reached: {elapsed_minutes:.1f} minutes (limit: {self.timeout_minutes} minutes)")
                        if self.timeout_callback:
                            self.timeout_callback(elapsed_minutes)
                        break
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                time.sleep(self.check_interval)
                
    def _log_resource_summary(self):
        """Log resource usage summary"""
        logger.info(f"""
📊 RESOURCE USAGE SUMMARY:
=========================
Peak Memory Usage: {self.peak_memory_gb:.1f}GB / {self.max_memory_gb}GB ({(self.peak_memory_gb/self.max_memory_gb)*100:.1f}%)
Peak CPU Usage: {self.peak_cpu_percent:.1f}% / {self.max_cpu_percent}% ({(self.peak_cpu_percent/self.max_cpu_percent)*100:.1f}%)
Total Processing Time: {self.total_processing_time:.1f} minutes / {self.timeout_minutes} minutes ({(self.total_processing_time/self.timeout_minutes)*100:.1f}%)
""")
        
    def get_current_status(self) -> Dict:
        """Get current resource status"""
        memory_gb = psutil.virtual_memory().used / (1024**3)
        cpu_percent = psutil.cpu_percent()
        disk_usage = psutil.disk_usage('.').used / (1024**3)
        
        elapsed_minutes = 0
        if self.start_time:
            elapsed_minutes = (datetime.now() - self.start_time).total_seconds() / 60.0
            
        return {
            'memory_gb': memory_gb,
            'memory_percent': (memory_gb / self.max_memory_gb) * 100,
            'cpu_percent': cpu_percent,
            'cpu_percent_of_limit': (cpu_percent / self.max_cpu_percent) * 100,
            'disk_gb': disk_usage,
            'disk_percent': (disk_usage / self.max_disk_gb) * 100,
            'elapsed_minutes': elapsed_minutes,
            'timeout_percent': (elapsed_minutes / self.timeout_minutes) * 100,
            'peak_memory_gb': self.peak_memory_gb,
            'peak_cpu_percent': self.peak_cpu_percent,
            'total_processing_time': self.total_processing_time
        }
        
    def set_alert_callbacks(self, 
                           memory_callback: Optional[Callable] = None,
                           cpu_callback: Optional[Callable] = None,
                           timeout_callback: Optional[Callable] = None):
        """Set alert callback functions"""
        self.memory_alert_callback = memory_callback
        self.cpu_alert_callback = cpu_callback
        self.timeout_callback = timeout_callback

class ProgressTracker:
    """Track progress of patent processing"""
    
    def __init__(self, total_patents: int, total_tasks: int):
        self.total_patents = total_patents
        self.total_tasks = total_tasks
        self.completed_patents = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = datetime.now()
        self.task_start_times = {}
        self.task_durations = {}
        
    def start_task(self, task_name: str, patent_id: str):
        """Start tracking a task"""
        task_key = f"{patent_id}_{task_name}"
        self.task_start_times[task_key] = datetime.now()
        logger.info(f"🔄 Starting task: {task_name} for patent {patent_id}")
        
    def complete_task(self, task_name: str, patent_id: str, success: bool = True):
        """Complete tracking a task"""
        task_key = f"{patent_id}_{task_name}"
        
        if task_key in self.task_start_times:
            duration = (datetime.now() - self.task_start_times[task_key]).total_seconds()
            self.task_durations[task_key] = duration
            
            if success:
                self.completed_tasks += 1
                logger.info(f"✅ Completed task: {task_name} for patent {patent_id} ({duration:.1f}s)")
            else:
                self.failed_tasks += 1
                logger.error(f"❌ Failed task: {task_name} for patent {patent_id} ({duration:.1f}s)")
                
        self._log_progress()
        
    def complete_patent(self, patent_id: str):
        """Mark a patent as completed"""
        self.completed_patents += 1
        logger.info(f"🎉 Completed patent {patent_id} ({self.completed_patents}/{self.total_patents})")
        self._log_progress()
        
    def _log_progress(self):
        """Log current progress"""
        elapsed = (datetime.now() - self.start_time).total_seconds() / 60.0
        patents_progress = (self.completed_patents / self.total_patents) * 100
        tasks_progress = (self.completed_tasks / self.total_tasks) * 100
        
        logger.info(f"""
📈 PROGRESS UPDATE:
==================
Patents: {self.completed_patents}/{self.total_patents} ({patents_progress:.1f}%)
Tasks: {self.completed_tasks}/{self.total_tasks} ({tasks_progress:.1f}%)
Failed Tasks: {self.failed_tasks}
Elapsed Time: {elapsed:.1f} minutes
""")
        
    def get_summary(self) -> Dict:
        """Get processing summary"""
        total_time = (datetime.now() - self.start_time).total_seconds() / 60.0
        avg_task_time = sum(self.task_durations.values()) / len(self.task_durations) if self.task_durations else 0
        
        return {
            'total_patents': self.total_patents,
            'completed_patents': self.completed_patents,
            'patent_success_rate': (self.completed_patents / self.total_patents) * 100,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'task_success_rate': (self.completed_tasks / self.total_tasks) * 100,
            'total_time_minutes': total_time,
            'avg_task_time_seconds': avg_task_time,
            'estimated_remaining_minutes': (total_time / max(self.completed_tasks, 1)) * (self.total_tasks - self.completed_tasks)
        }

class ErrorHandler:
    """Handle errors gracefully with recovery options"""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 30):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.error_counts = {}
        self.recovery_actions = {}
        
    def handle_error(self, error: Exception, context: str, patent_id: str = None) -> bool:
        """Handle an error with retry logic"""
        error_key = f"{context}_{patent_id}" if patent_id else context
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        logger.error(f"❌ Error in {context} for patent {patent_id}: {str(error)}")
        
        if self.error_counts[error_key] <= self.max_retries:
            logger.info(f"🔄 Retrying {context} for patent {patent_id} (attempt {self.error_counts[error_key]}/{self.max_retries})")
            time.sleep(self.retry_delay)
            return True  # Retry
        else:
            logger.error(f"💥 Max retries exceeded for {context} for patent {patent_id}")
            return False  # Give up
            
    def add_recovery_action(self, context: str, action: Callable):
        """Add a recovery action for a specific context"""
        self.recovery_actions[context] = action
        
    def execute_recovery(self, context: str, *args, **kwargs):
        """Execute recovery action for a context"""
        if context in self.recovery_actions:
            try:
                self.recovery_actions[context](*args, **kwargs)
                logger.info(f"🔧 Executed recovery action for {context}")
            except Exception as e:
                logger.error(f"❌ Recovery action failed for {context}: {e}")
        else:
            logger.warning(f"⚠️ No recovery action defined for {context}")

# Global instances
resource_manager = ResourceManager()
progress_tracker = None
error_handler = ErrorHandler()

def initialize_monitoring(total_patents: int, total_tasks: int):
    """Initialize monitoring for a processing run"""
    global progress_tracker
    
    # Initialize progress tracker
    progress_tracker = ProgressTracker(total_patents, total_tasks)
    
    # Set up resource manager alert callbacks
    def memory_alert(memory_gb):
        logger.warning(f"⚠️ Memory usage alert: {memory_gb:.1f}GB")
        
    def cpu_alert(cpu_percent):
        logger.warning(f"⚠️ CPU usage alert: {cpu_percent:.1f}%")
        
    def timeout_alert(elapsed_minutes):
        logger.error(f"⏰ Processing timeout alert: {elapsed_minutes:.1f} minutes")
        
    resource_manager.set_alert_callbacks(memory_alert, cpu_alert, timeout_alert)
    
    # Start monitoring
    resource_manager.start_monitoring()
    
    logger.info(f"🚀 Monitoring initialized for {total_patents} patents, {total_tasks} tasks")

def cleanup_monitoring():
    """Clean up monitoring resources"""
    if resource_manager:
        resource_manager.stop_monitoring()
    
    if progress_tracker:
        summary = progress_tracker.get_summary()
        logger.info(f"""
📊 FINAL PROCESSING SUMMARY:
============================
{summary}
""")

def get_status_report() -> Dict:
    """Get comprehensive status report"""
    status = {
        'resource_status': resource_manager.get_current_status() if resource_manager else {},
        'progress_summary': progress_tracker.get_summary() if progress_tracker else {},
        'error_summary': error_handler.error_counts if error_handler else {}
    }
    return status 