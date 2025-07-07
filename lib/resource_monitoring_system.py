"""
Resource Monitoring System
Real-time tracking of costs, performance, and optimization effectiveness
"""

import os
import json
import time
import psutil
import logging
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque, defaultdict
import threading
import queue
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class MetricType(Enum):
    """Types of metrics to monitor"""
    COST = "cost"
    TOKENS = "tokens"
    TIME = "time"
    MEMORY = "memory"
    CPU = "cpu"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"

@dataclass
class MetricSample:
    """Single metric sample"""
    timestamp: datetime
    metric_type: MetricType
    value: float
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Alert:
    """System alert"""
    timestamp: datetime
    level: AlertLevel
    metric_type: MetricType
    message: str
    value: float
    threshold: float
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceProfile:
    """Performance profile for a task or workflow"""
    task_name: str
    avg_cost: float
    avg_tokens: int
    avg_time_ms: float
    avg_memory_mb: float
    avg_quality: float
    efficiency_score: float
    sample_count: int
    last_updated: datetime

class ResourceMonitor:
    """Real-time resource monitoring system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.metrics = deque(maxlen=self.config['max_metrics_history'])
        self.alerts = deque(maxlen=self.config['max_alerts_history'])
        self.profiles = {}  # Task performance profiles
        self.thresholds = self.config['thresholds']
        self.monitoring_active = False
        self.monitoring_thread = None
        self.metric_queue = queue.Queue()
        
        # Current session tracking
        self.session_start = datetime.now()
        self.session_metrics = {
            'total_cost': 0.0,
            'total_tokens': 0,
            'total_time_ms': 0.0,
            'task_count': 0,
            'optimization_count': 0,
            'cost_savings': 0.0
        }
        
        # Real-time statistics
        self.realtime_stats = {
            'current_cost_rate': 0.0,
            'current_token_rate': 0.0,
            'avg_response_time': 0.0,
            'system_cpu_percent': 0.0,
            'system_memory_percent': 0.0,
            'cost_trend': 'stable'
        }
        
        logger.info("📊 Resource Monitor initialized")
        logger.info(f"   Monitoring intervals: {self.config['monitoring_interval_seconds']}s")
        logger.info(f"   Alert thresholds: {len(self.thresholds)} configured")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default monitoring configuration"""
        return {
            'monitoring_interval_seconds': 5,
            'max_metrics_history': 10000,
            'max_alerts_history': 1000,
            'enable_system_monitoring': True,
            'enable_cost_monitoring': True,
            'enable_performance_monitoring': True,
            'alert_cooldown_seconds': 300,  # 5 minutes
            'thresholds': {
                'cost_per_minute': {
                    'warning': 0.50,    # $0.50 per minute
                    'critical': 1.00,   # $1.00 per minute
                    'emergency': 2.00   # $2.00 per minute
                },
                'tokens_per_minute': {
                    'warning': 10000,
                    'critical': 20000,
                    'emergency': 50000
                },
                'memory_percent': {
                    'warning': 80,
                    'critical': 90,
                    'emergency': 95
                },
                'cpu_percent': {
                    'warning': 80,
                    'critical': 90,
                    'emergency': 95
                },
                'response_time_ms': {
                    'warning': 5000,     # 5 seconds
                    'critical': 10000,   # 10 seconds
                    'emergency': 30000   # 30 seconds
                },
                'quality_score': {
                    'warning': 0.8,      # Below 80%
                    'critical': 0.7,     # Below 70%
                    'emergency': 0.6     # Below 60%
                },
                'daily_cost_budget': {
                    'warning': 80.0,     # $80 per day
                    'critical': 100.0,   # $100 per day
                    'emergency': 150.0   # $150 per day
                }
            },
            'optimization_targets': {
                'cost_reduction_target': 0.30,  # 30% reduction
                'efficiency_target': 0.85,      # 85% efficiency
                'quality_preservation': 0.90    # 90% quality preservation
            }
        }
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("🔄 Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        # Save final monitoring data summary
        session_duration = datetime.now() - self.session_start
        total_time_minutes = session_duration.total_seconds() / 60
        
        logger.info("⏹️  Resource monitoring stopped. Total time: {:.1f} minutes".format(total_time_minutes))
        
        # Only save if there's meaningful data to save
        if self.session_metrics['task_count'] > 0 or len(self.metrics) > 100:
            final_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_report_file = f"output/monitoring_summary_{final_timestamp}.json"
            self._save_monitoring_data(final_report_file)
            logger.info(f"📊 Final monitoring summary saved: {final_report_file}")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        last_alert_times = defaultdict(lambda: datetime.min)
        
        while self.monitoring_active:
            try:
                # Collect system metrics
                if self.config['enable_system_monitoring']:
                    self._collect_system_metrics()
                
                # Process queued metrics
                self._process_metric_queue()
                
                # Update real-time statistics
                self._update_realtime_stats()
                
                # Check thresholds and generate alerts
                self._check_thresholds(last_alert_times)
                
                # Save periodic data
                self._save_periodic_data()
                
                time.sleep(self.config['monitoring_interval_seconds'])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1)
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        timestamp = datetime.now()
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=None)
        self.metrics.append(MetricSample(
            timestamp=timestamp,
            metric_type=MetricType.CPU,
            value=cpu_percent
        ))
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics.append(MetricSample(
            timestamp=timestamp,
            metric_type=MetricType.MEMORY,
            value=memory.percent
        ))
        
        # Update real-time stats
        self.realtime_stats['system_cpu_percent'] = cpu_percent
        self.realtime_stats['system_memory_percent'] = memory.percent
    
    def _process_metric_queue(self):
        """Process metrics from the queue"""
        while not self.metric_queue.empty():
            try:
                metric = self.metric_queue.get_nowait()
                self.metrics.append(metric)
                
                # Update session metrics
                self._update_session_metrics(metric)
                
            except queue.Empty:
                break
    
    def _update_session_metrics(self, metric: MetricSample):
        """Update session-level metrics"""
        if metric.metric_type == MetricType.COST:
            self.session_metrics['total_cost'] += metric.value
        elif metric.metric_type == MetricType.TOKENS:
            self.session_metrics['total_tokens'] += int(metric.value)
        elif metric.metric_type == MetricType.TIME:
            self.session_metrics['total_time_ms'] += metric.value
        
        # Count tasks and optimizations
        if 'task_completed' in metric.context:
            self.session_metrics['task_count'] += 1
        if 'optimization_applied' in metric.context:
            self.session_metrics['optimization_count'] += 1
            if 'cost_savings' in metric.context:
                self.session_metrics['cost_savings'] += metric.context['cost_savings']
    
    def _update_realtime_stats(self):
        """Update real-time statistics"""
        now = datetime.now()
        window_minutes = 5  # 5-minute window
        cutoff_time = now - timedelta(minutes=window_minutes)
        
        # Filter recent metrics
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return
        
        # Calculate rates
        cost_metrics = [m for m in recent_metrics if m.metric_type == MetricType.COST]
        token_metrics = [m for m in recent_metrics if m.metric_type == MetricType.TOKENS]
        time_metrics = [m for m in recent_metrics if m.metric_type == MetricType.TIME]
        
        if cost_metrics:
            total_cost = sum(m.value for m in cost_metrics)
            self.realtime_stats['current_cost_rate'] = total_cost / window_minutes
        
        if token_metrics:
            total_tokens = sum(m.value for m in token_metrics)
            self.realtime_stats['current_token_rate'] = total_tokens / window_minutes
        
        if time_metrics:
            avg_time = np.mean([m.value for m in time_metrics])
            self.realtime_stats['avg_response_time'] = avg_time
        
        # Determine cost trend
        self._calculate_cost_trend()
    
    def _calculate_cost_trend(self):
        """Calculate cost trend (increasing/decreasing/stable)"""
        now = datetime.now()
        recent_window = now - timedelta(minutes=5)
        older_window = now - timedelta(minutes=10)
        
        recent_costs = [m.value for m in self.metrics 
                       if m.metric_type == MetricType.COST and m.timestamp >= recent_window]
        older_costs = [m.value for m in self.metrics 
                      if m.metric_type == MetricType.COST and 
                      older_window <= m.timestamp < recent_window]
        
        if not recent_costs or not older_costs:
            self.realtime_stats['cost_trend'] = 'unknown'
            return
        
        recent_avg = np.mean(recent_costs)
        older_avg = np.mean(older_costs)
        
        change_percent = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        
        if change_percent > 0.1:
            self.realtime_stats['cost_trend'] = 'increasing'
        elif change_percent < -0.1:
            self.realtime_stats['cost_trend'] = 'decreasing'
        else:
            self.realtime_stats['cost_trend'] = 'stable'
    
    def _check_thresholds(self, last_alert_times: Dict[str, datetime]):
        """Check thresholds and generate alerts"""
        now = datetime.now()
        cooldown = timedelta(seconds=self.config['alert_cooldown_seconds'])
        
        # Check cost rate
        if self.config['enable_cost_monitoring']:
            cost_rate = self.realtime_stats['current_cost_rate']
            self._check_metric_threshold(
                'cost_per_minute', cost_rate, last_alert_times, now, cooldown
            )
        
        # Check token rate
        token_rate = self.realtime_stats['current_token_rate']
        self._check_metric_threshold(
            'tokens_per_minute', token_rate, last_alert_times, now, cooldown
        )
        
        # Check system resources
        memory_percent = self.realtime_stats['system_memory_percent']
        self._check_metric_threshold(
            'memory_percent', memory_percent, last_alert_times, now, cooldown
        )
        
        cpu_percent = self.realtime_stats['system_cpu_percent']
        self._check_metric_threshold(
            'cpu_percent', cpu_percent, last_alert_times, now, cooldown
        )
        
        # Check response time
        response_time = self.realtime_stats['avg_response_time']
        self._check_metric_threshold(
            'response_time_ms', response_time, last_alert_times, now, cooldown
        )
        
        # Check daily budget
        session_duration_hours = (now - self.session_start).total_seconds() / 3600
        if session_duration_hours > 0:
            daily_cost_projection = self.session_metrics['total_cost'] * (24 / session_duration_hours)
            self._check_metric_threshold(
                'daily_cost_budget', daily_cost_projection, last_alert_times, now, cooldown
            )
    
    def _check_metric_threshold(self, metric_name: str, value: float, 
                               last_alert_times: Dict[str, datetime],
                               now: datetime, cooldown: timedelta):
        """Check individual metric threshold"""
        if metric_name not in self.thresholds:
            return
        
        thresholds = self.thresholds[metric_name]
        
        # Determine alert level
        alert_level = None
        threshold_value = None
        
        if 'emergency' in thresholds and value >= thresholds['emergency']:
            alert_level = AlertLevel.EMERGENCY
            threshold_value = thresholds['emergency']
        elif 'critical' in thresholds and value >= thresholds['critical']:
            alert_level = AlertLevel.CRITICAL
            threshold_value = thresholds['critical']
        elif 'warning' in thresholds and value >= thresholds['warning']:
            alert_level = AlertLevel.WARNING
            threshold_value = thresholds['warning']
        
        # For quality scores, thresholds are reversed (alert when below)
        if metric_name == 'quality_score':
            if 'emergency' in thresholds and value <= thresholds['emergency']:
                alert_level = AlertLevel.EMERGENCY
                threshold_value = thresholds['emergency']
            elif 'critical' in thresholds and value <= thresholds['critical']:
                alert_level = AlertLevel.CRITICAL
                threshold_value = thresholds['critical']
            elif 'warning' in thresholds and value <= thresholds['warning']:
                alert_level = AlertLevel.WARNING
                threshold_value = thresholds['warning']
        
        # Generate alert if needed
        if alert_level and threshold_value is not None:
            alert_key = f"{metric_name}_{alert_level.value}"
            
            # Check cooldown
            if now - last_alert_times[alert_key] > cooldown:
                self._generate_alert(metric_name, alert_level, value, threshold_value)
                last_alert_times[alert_key] = now
    
    def _generate_alert(self, metric_name: str, level: AlertLevel, 
                       value: float, threshold: float):
        """Generate an alert"""
        
        # Create alert message
        if metric_name == 'cost_per_minute':
            message = f"Cost rate ${value:.3f}/min exceeds ${threshold:.3f}/min threshold"
        elif metric_name == 'tokens_per_minute':
            message = f"Token rate {value:.0f}/min exceeds {threshold:.0f}/min threshold"
        elif metric_name == 'memory_percent':
            message = f"Memory usage {value:.1f}% exceeds {threshold:.1f}% threshold"
        elif metric_name == 'cpu_percent':
            message = f"CPU usage {value:.1f}% exceeds {threshold:.1f}% threshold"
        elif metric_name == 'response_time_ms':
            message = f"Response time {value:.0f}ms exceeds {threshold:.0f}ms threshold"
        elif metric_name == 'quality_score':
            message = f"Quality score {value:.2f} below {threshold:.2f} threshold"
        elif metric_name == 'daily_cost_budget':
            message = f"Projected daily cost ${value:.2f} exceeds ${threshold:.2f} budget"
        else:
            message = f"{metric_name} value {value:.2f} exceeds threshold {threshold:.2f}"
        
        # Determine metric type
        metric_type_map = {
            'cost_per_minute': MetricType.COST,
            'tokens_per_minute': MetricType.TOKENS,
            'memory_percent': MetricType.MEMORY,
            'cpu_percent': MetricType.CPU,
            'response_time_ms': MetricType.TIME,
            'quality_score': MetricType.QUALITY,
            'daily_cost_budget': MetricType.COST
        }
        
        metric_type = metric_type_map.get(metric_name, MetricType.COST)
        
        # Create alert
        alert = Alert(
            timestamp=datetime.now(),
            level=level,
            metric_type=metric_type,
            message=message,
            value=value,
            threshold=threshold,
            context={
                'metric_name': metric_name,
                'session_duration_hours': (datetime.now() - self.session_start).total_seconds() / 3600,
                'total_session_cost': self.session_metrics['total_cost']
            }
        )
        
        self.alerts.append(alert)
        
        # Log alert
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.CRITICAL: logger.error,
            AlertLevel.EMERGENCY: logger.critical
        }[level]
        
        log_method(f"🚨 {level.value.upper()}: {message}")
    
    def _save_periodic_data(self):
        """Save monitoring data periodically"""
        # Only save monitoring data when monitoring stops, not during execution
        # This prevents cluttering the output directory with JSON files
        pass
    
    def track_task_start(self, task_name: str, task_id: str, estimated_cost: float = 0,
                        estimated_tokens: int = 0) -> str:
        """Track task start"""
        timestamp = datetime.now()
        
        # Add metrics
        if estimated_cost > 0:
            self.metric_queue.put(MetricSample(
                timestamp=timestamp,
                metric_type=MetricType.COST,
                value=estimated_cost,
                context={'task_name': task_name, 'task_id': task_id, 'event': 'task_start'}
            ))
        
        if estimated_tokens > 0:
            self.metric_queue.put(MetricSample(
                timestamp=timestamp,
                metric_type=MetricType.TOKENS,
                value=estimated_tokens,
                context={'task_name': task_name, 'task_id': task_id, 'event': 'task_start'}
            ))
        
        logger.debug(f"Task started: {task_name} ({task_id})")
        return task_id
    
    def track_task_completion(self, task_name: str, task_id: str, 
                            actual_cost: float, actual_tokens: int, 
                            execution_time_ms: float, quality_score: float = None):
        """Track task completion"""
        timestamp = datetime.now()
        
        # Add metrics
        self.metric_queue.put(MetricSample(
            timestamp=timestamp,
            metric_type=MetricType.COST,
            value=actual_cost,
            context={'task_name': task_name, 'task_id': task_id, 'event': 'task_completion', 'task_completed': True}
        ))
        
        self.metric_queue.put(MetricSample(
            timestamp=timestamp,
            metric_type=MetricType.TOKENS,
            value=actual_tokens,
            context={'task_name': task_name, 'task_id': task_id, 'event': 'task_completion'}
        ))
        
        self.metric_queue.put(MetricSample(
            timestamp=timestamp,
            metric_type=MetricType.TIME,
            value=execution_time_ms,
            context={'task_name': task_name, 'task_id': task_id, 'event': 'task_completion'}
        ))
        
        if quality_score is not None:
            self.metric_queue.put(MetricSample(
                timestamp=timestamp,
                metric_type=MetricType.QUALITY,
                value=quality_score,
                context={'task_name': task_name, 'task_id': task_id, 'event': 'task_completion'}
            ))
        
        # Update performance profile
        self._update_performance_profile(task_name, actual_cost, actual_tokens, 
                                        execution_time_ms, quality_score)
        
        logger.debug(f"Task completed: {task_name} ({task_id}) - Cost: ${actual_cost:.3f}, "
                    f"Tokens: {actual_tokens}, Time: {execution_time_ms:.1f}ms")
    
    def track_optimization(self, optimization_type: str, cost_savings: float, 
                          token_savings: int, context: Dict[str, Any] = None):
        """Track optimization application"""
        timestamp = datetime.now()
        context = context or {}
        context.update({
            'optimization_type': optimization_type,
            'cost_savings': cost_savings,
            'token_savings': token_savings,
            'optimization_applied': True
        })
        
        # Track efficiency metric
        efficiency_score = min(cost_savings / 0.01, 10.0)  # Cap at 10x efficiency
        
        self.metric_queue.put(MetricSample(
            timestamp=timestamp,
            metric_type=MetricType.EFFICIENCY,
            value=efficiency_score,
            context=context
        ))
        
        logger.info(f"Optimization applied: {optimization_type} - "
                   f"Saved: ${cost_savings:.3f}, {token_savings} tokens")
    
    def _update_performance_profile(self, task_name: str, cost: float, tokens: int,
                                   time_ms: float, quality_score: float = None):
        """Update performance profile for a task"""
        if task_name not in self.profiles:
            self.profiles[task_name] = PerformanceProfile(
                task_name=task_name,
                avg_cost=cost,
                avg_tokens=tokens,
                avg_time_ms=time_ms,
                avg_memory_mb=0.0,
                avg_quality=quality_score or 0.0,
                efficiency_score=1.0,
                sample_count=1,
                last_updated=datetime.now()
            )
        else:
            profile = self.profiles[task_name]
            n = profile.sample_count
            
            # Update running averages
            profile.avg_cost = (profile.avg_cost * n + cost) / (n + 1)
            profile.avg_tokens = int((profile.avg_tokens * n + tokens) / (n + 1))
            profile.avg_time_ms = (profile.avg_time_ms * n + time_ms) / (n + 1)
            
            if quality_score is not None:
                profile.avg_quality = (profile.avg_quality * n + quality_score) / (n + 1)
            
            # Calculate efficiency (lower cost and time, higher quality = better)
            cost_efficiency = min(0.01 / max(profile.avg_cost, 0.001), 10.0)
            time_efficiency = min(1000 / max(profile.avg_time_ms, 100), 10.0)
            quality_efficiency = profile.avg_quality
            
            profile.efficiency_score = (cost_efficiency + time_efficiency + quality_efficiency) / 3
            profile.sample_count += 1
            profile.last_updated = datetime.now()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get current session summary"""
        session_duration = datetime.now() - self.session_start
        
        # Calculate optimization effectiveness
        cost_reduction = 0.0
        if self.session_metrics['total_cost'] > 0:
            cost_reduction = self.session_metrics['cost_savings'] / self.session_metrics['total_cost']
        
        # Recent alerts
        recent_alerts = [a for a in self.alerts 
                        if a.timestamp > datetime.now() - timedelta(hours=1)]
        
        return {
            'session_duration_hours': session_duration.total_seconds() / 3600,
            'total_cost': self.session_metrics['total_cost'],
            'total_tokens': self.session_metrics['total_tokens'],
            'total_tasks': self.session_metrics['task_count'],
            'optimizations_applied': self.session_metrics['optimization_count'],
            'cost_savings': self.session_metrics['cost_savings'],
            'cost_reduction_percentage': cost_reduction * 100,
            'avg_cost_per_task': (self.session_metrics['total_cost'] / 
                                 max(self.session_metrics['task_count'], 1)),
            'current_cost_rate': self.realtime_stats['current_cost_rate'],
            'current_token_rate': self.realtime_stats['current_token_rate'],
            'cost_trend': self.realtime_stats['cost_trend'],
            'system_cpu_percent': self.realtime_stats['system_cpu_percent'],
            'system_memory_percent': self.realtime_stats['system_memory_percent'],
            'recent_alerts_count': len(recent_alerts),
            'target_achievement': {
                'cost_reduction_target': self.config['optimization_targets']['cost_reduction_target'],
                'cost_reduction_actual': cost_reduction,
                'target_met': cost_reduction >= self.config['optimization_targets']['cost_reduction_target']
            }
        }
    
    def get_performance_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get performance profiles for all tasks"""
        return {
            name: {
                'avg_cost': profile.avg_cost,
                'avg_tokens': profile.avg_tokens,
                'avg_time_ms': profile.avg_time_ms,
                'avg_quality': profile.avg_quality,
                'efficiency_score': profile.efficiency_score,
                'sample_count': profile.sample_count,
                'last_updated': profile.last_updated.isoformat()
            }
            for name, profile in self.profiles.items()
        }
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]
        
        return [
            {
                'timestamp': alert.timestamp.isoformat(),
                'level': alert.level.value,
                'metric_type': alert.metric_type.value,
                'message': alert.message,
                'value': alert.value,
                'threshold': alert.threshold,
                'context': alert.context
            }
            for alert in recent_alerts
        ]
    
    def _save_monitoring_data(self, output_file: str = None):
        """Save monitoring data to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/monitoring_data_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        data = {
            'session_summary': self.get_session_summary(),
            'performance_profiles': self.get_performance_profiles(),
            'recent_alerts': self.get_recent_alerts(),
            'realtime_stats': self.realtime_stats,
            'config': self.config,
            'export_timestamp': datetime.now().isoformat()
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.debug(f"Monitoring data saved: {output_file}")

# Global monitor instance
_monitor = None

def get_monitor() -> ResourceMonitor:
    """Get global monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = ResourceMonitor()
    return _monitor

def start_monitoring():
    """Start monitoring"""
    monitor = get_monitor()
    monitor.start_monitoring()

def track_task_start(task_name: str, task_id: str, **kwargs) -> str:
    """Track task start"""
    monitor = get_monitor()
    return monitor.track_task_start(task_name, task_id, **kwargs)

def track_task_completion(task_name: str, task_id: str, **kwargs):
    """Track task completion"""
    monitor = get_monitor()
    return monitor.track_task_completion(task_name, task_id, **kwargs)

def track_optimization(optimization_type: str, **kwargs):
    """Track optimization"""
    monitor = get_monitor()
    return monitor.track_optimization(optimization_type, **kwargs) 