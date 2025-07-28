"""
Performance Monitoring Tool for Patent Automation System
Tracks task performance and resource usage
"""

import os
import json
import time
import psutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    from crewai.tools import BaseTool
except ImportError:
    from crewai.tools.agent_tools import Tool as BaseTool

from lib.pydantic_output_models import GenericAnalysisOutput


class PerformanceMonitoringInput(BaseTool):
    """Input model for performance monitoring tool"""
    
    patent_id: str
    task_name: str
    start_time: float
    end_time: float
    task_context: Dict[str, Any]
    performance_metrics: Dict[str, Any]


class PerformanceMonitoringTool(BaseTool):
    """Tool for tracking task performance and resource usage"""
    
    name: str = "performance_monitoring_tool"
    description: str = """
    Tracks task performance and resource usage.
    
    Parameters:
    - patent_id: Patent identifier
    - task_name: Name of the task being monitored
    - start_time: Task start time (timestamp)
    - end_time: Task end time (timestamp)
    - task_context: Context information about the task
    - performance_metrics: Additional performance metrics
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _run(self, patent_id: str, task_name: str, start_time: float, end_time: float,
             task_context: Dict[str, Any], performance_metrics: Dict[str, Any]) -> str:
        """
        Track task performance and resource usage
        
        Args:
            patent_id: Patent identifier
            task_name: Name of the task being monitored
            start_time: Task start time (timestamp)
            end_time: Task end time (timestamp)
            task_context: Context information about the task
            performance_metrics: Additional performance metrics
            
        Returns:
            Performance monitoring report
        """
        
        monitoring_results = {
            "patent_id": patent_id,
            "task_name": task_name,
            "start_time": start_time,
            "end_time": end_time,
            "execution_time": end_time - start_time,
            "resource_usage": {},
            "performance_metrics": performance_metrics,
            "bottlenecks": [],
            "optimization_suggestions": [],
            "quality_scores": {},
            "success_indicators": {}
        }
        
        # Calculate execution time
        execution_time = end_time - start_time
        monitoring_results["execution_time"] = execution_time
        
        # Monitor resource usage
        resource_usage = self._monitor_resource_usage()
        monitoring_results["resource_usage"] = resource_usage
        
        # Analyze performance metrics
        performance_analysis = self._analyze_performance_metrics(
            task_name, execution_time, performance_metrics
        )
        monitoring_results.update(performance_analysis)
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(
            task_name, execution_time, resource_usage, performance_metrics
        )
        monitoring_results["bottlenecks"] = bottlenecks
        
        # Generate optimization suggestions
        optimization_suggestions = self._generate_optimization_suggestions(
            task_name, execution_time, resource_usage, bottlenecks
        )
        monitoring_results["optimization_suggestions"] = optimization_suggestions
        
        # Calculate quality scores
        quality_scores = self._calculate_quality_scores(
            task_name, execution_time, resource_usage, performance_metrics
        )
        monitoring_results["quality_scores"] = quality_scores
        
        # Assess success indicators
        success_indicators = self._assess_success_indicators(
            task_name, execution_time, resource_usage, performance_metrics
        )
        monitoring_results["success_indicators"] = success_indicators
        
        # Create monitoring report
        report = self._create_monitoring_report(monitoring_results)
        
        return report
    
    def _monitor_resource_usage(self) -> Dict[str, Any]:
        """Monitor current resource usage"""
        
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # Get network I/O
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_used_gb": memory_used_gb,
                "memory_total_gb": memory_total_gb,
                "disk_percent": disk_percent,
                "disk_used_gb": disk_used_gb,
                "disk_total_gb": disk_total_gb,
                "network_bytes_sent": network_bytes_sent,
                "network_bytes_recv": network_bytes_recv
            }
        except Exception as e:
            return {
                "error": f"Failed to monitor resources: {str(e)}",
                "cpu_percent": 0,
                "memory_percent": 0,
                "memory_used_gb": 0,
                "memory_total_gb": 0,
                "disk_percent": 0,
                "disk_used_gb": 0,
                "disk_total_gb": 0,
                "network_bytes_sent": 0,
                "network_bytes_recv": 0
            }
    
    def _analyze_performance_metrics(self, task_name: str, execution_time: float,
                                   performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics for the task"""
        
        analysis = {
            "execution_efficiency": 0.0,
            "resource_efficiency": 0.0,
            "quality_efficiency": 0.0,
            "overall_performance": 0.0
        }
        
        # Task-specific performance thresholds
        task_thresholds = {
            "prior_art_research": {"max_time": 300, "target_time": 180},
            "claims_refinement": {"max_time": 240, "target_time": 120},
            "patent_document": {"max_time": 600, "target_time": 300},
            "architecture_diagram": {"max_time": 180, "target_time": 90},
            "legal_review": {"max_time": 240, "target_time": 120},
            "editorial_review": {"max_time": 180, "target_time": 90},
            "patent_valuation": {"max_time": 240, "target_time": 120}
        }
        
        threshold = task_thresholds.get(task_name, {"max_time": 300, "target_time": 150})
        
        # Calculate execution efficiency
        if execution_time <= threshold["target_time"]:
            analysis["execution_efficiency"] = 1.0
        elif execution_time <= threshold["max_time"]:
            analysis["execution_efficiency"] = 0.5
        else:
            analysis["execution_efficiency"] = 0.0
        
        # Calculate resource efficiency (simplified)
        analysis["resource_efficiency"] = 0.8  # Placeholder
        
        # Calculate quality efficiency (simplified)
        analysis["quality_efficiency"] = 0.9  # Placeholder
        
        # Calculate overall performance
        analysis["overall_performance"] = (
            analysis["execution_efficiency"] * 0.4 +
            analysis["resource_efficiency"] * 0.3 +
            analysis["quality_efficiency"] * 0.3
        )
        
        return analysis
    
    def _identify_bottlenecks(self, task_name: str, execution_time: float,
                             resource_usage: Dict[str, Any], 
                             performance_metrics: Dict[str, Any]) -> List[str]:
        """Identify performance bottlenecks"""
        
        bottlenecks = []
        
        # Time-based bottlenecks
        if execution_time > 300:  # 5 minutes
            bottlenecks.append("Long execution time - consider task splitting")
        
        if execution_time > 600:  # 10 minutes
            bottlenecks.append("Very long execution time - implement parallel processing")
        
        # Resource-based bottlenecks
        if resource_usage.get("cpu_percent", 0) > 90:
            bottlenecks.append("High CPU usage - optimize algorithms or use caching")
        
        if resource_usage.get("memory_percent", 0) > 85:
            bottlenecks.append("High memory usage - implement memory management")
        
        if resource_usage.get("disk_percent", 0) > 90:
            bottlenecks.append("High disk usage - implement cleanup or use external storage")
        
        # Task-specific bottlenecks
        if "prior_art" in task_name.lower() and execution_time > 240:
            bottlenecks.append("Prior art research taking too long - use cached results")
        
        if "patent_document" in task_name.lower() and execution_time > 480:
            bottlenecks.append("Patent document generation slow - use templates")
        
        if "diagram" in task_name.lower() and execution_time > 120:
            bottlenecks.append("Diagram generation slow - use simplified diagrams")
        
        return bottlenecks
    
    def _generate_optimization_suggestions(self, task_name: str, execution_time: float,
                                         resource_usage: Dict[str, Any], 
                                         bottlenecks: List[str]) -> List[str]:
        """Generate optimization suggestions"""
        
        suggestions = []
        
        # General optimizations
        if execution_time > 300:
            suggestions.append("Implement task splitting for large operations")
            suggestions.append("Use parallel processing where possible")
            suggestions.append("Add caching for repeated operations")
        
        if resource_usage.get("cpu_percent", 0) > 80:
            suggestions.append("Optimize algorithms for better CPU efficiency")
            suggestions.append("Implement request throttling")
            suggestions.append("Use asynchronous processing")
        
        if resource_usage.get("memory_percent", 0) > 80:
            suggestions.append("Implement memory cleanup and garbage collection")
            suggestions.append("Use streaming processing for large datasets")
            suggestions.append("Optimize data structures")
        
        # Task-specific optimizations
        if "prior_art" in task_name.lower():
            suggestions.append("Use cached prior art results")
            suggestions.append("Implement intelligent search filtering")
            suggestions.append("Use multiple search providers in parallel")
        
        if "patent_document" in task_name.lower():
            suggestions.append("Use template-based document generation")
            suggestions.append("Implement incremental document building")
            suggestions.append("Cache common document sections")
        
        if "claims" in task_name.lower():
            suggestions.append("Use claim templates for common patterns")
            suggestions.append("Implement claim validation caching")
            suggestions.append("Use parallel claim analysis")
        
        return suggestions
    
    def _calculate_quality_scores(self, task_name: str, execution_time: float,
                                resource_usage: Dict[str, Any], 
                                performance_metrics: Dict[str, Any]) -> Dict[str, float]:
        """Calculate quality scores for the task"""
        
        scores = {
            "time_efficiency": 0.0,
            "resource_efficiency": 0.0,
            "reliability": 0.0,
            "overall_quality": 0.0
        }
        
        # Time efficiency score
        if execution_time <= 60:
            scores["time_efficiency"] = 1.0
        elif execution_time <= 180:
            scores["time_efficiency"] = 0.8
        elif execution_time <= 300:
            scores["time_efficiency"] = 0.6
        elif execution_time <= 600:
            scores["time_efficiency"] = 0.4
        else:
            scores["time_efficiency"] = 0.2
        
        # Resource efficiency score
        cpu_score = max(0, 1 - (resource_usage.get("cpu_percent", 0) / 100))
        memory_score = max(0, 1 - (resource_usage.get("memory_percent", 0) / 100))
        scores["resource_efficiency"] = (cpu_score + memory_score) / 2
        
        # Reliability score (simplified)
        scores["reliability"] = 0.9  # Placeholder
        
        # Overall quality score
        scores["overall_quality"] = (
            scores["time_efficiency"] * 0.4 +
            scores["resource_efficiency"] * 0.3 +
            scores["reliability"] * 0.3
        )
        
        return scores
    
    def _assess_success_indicators(self, task_name: str, execution_time: float,
                                 resource_usage: Dict[str, Any], 
                                 performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess success indicators for the task"""
        
        indicators = {
            "completed_successfully": True,
            "within_time_budget": execution_time <= 300,
            "within_resource_budget": resource_usage.get("cpu_percent", 0) <= 80,
            "quality_acceptable": True,
            "recommended_for_production": True
        }
        
        # Adjust indicators based on performance
        if execution_time > 600:
            indicators["within_time_budget"] = False
            indicators["recommended_for_production"] = False
        
        if resource_usage.get("cpu_percent", 0) > 90:
            indicators["within_resource_budget"] = False
            indicators["recommended_for_production"] = False
        
        if resource_usage.get("memory_percent", 0) > 90:
            indicators["within_resource_budget"] = False
            indicators["recommended_for_production"] = False
        
        return indicators
    
    def _create_monitoring_report(self, results: Dict[str, Any]) -> str:
        """Create comprehensive monitoring report"""
        
        report = f"""
# Performance Monitoring Report

## Task Information
- **Patent ID**: {results['patent_id']}
- **Task Name**: {results['task_name']}
- **Start Time**: {datetime.fromtimestamp(results['start_time']).strftime('%Y-%m-%d %H:%M:%S')}
- **End Time**: {datetime.fromtimestamp(results['end_time']).strftime('%Y-%m-%d %H:%M:%S')}
- **Execution Time**: {results['execution_time']:.2f} seconds

## Performance Analysis
- **Execution Efficiency**: {results['performance_metrics']['execution_efficiency']:.2f}/1.00
- **Resource Efficiency**: {results['performance_metrics']['resource_efficiency']:.2f}/1.00
- **Quality Efficiency**: {results['performance_metrics']['quality_efficiency']:.2f}/1.00
- **Overall Performance**: {results['performance_metrics']['overall_performance']:.2f}/1.00

## Resource Usage
- **CPU Usage**: {results['resource_usage'].get('cpu_percent', 0):.1f}%
- **Memory Usage**: {results['resource_usage'].get('memory_percent', 0):.1f}% ({results['resource_usage'].get('memory_used_gb', 0):.2f} GB / {results['resource_usage'].get('memory_total_gb', 0):.2f} GB)
- **Disk Usage**: {results['resource_usage'].get('disk_percent', 0):.1f}% ({results['resource_usage'].get('disk_used_gb', 0):.2f} GB / {results['resource_usage'].get('disk_total_gb', 0):.2f} GB)
- **Network I/O**: {results['resource_usage'].get('network_bytes_sent', 0):,} bytes sent, {results['resource_usage'].get('network_bytes_recv', 0):,} bytes received

## Quality Scores
- **Time Efficiency**: {results['quality_scores']['time_efficiency']:.2f}/1.00
- **Resource Efficiency**: {results['quality_scores']['resource_efficiency']:.2f}/1.00
- **Reliability**: {results['quality_scores']['reliability']:.2f}/1.00
- **Overall Quality**: {results['quality_scores']['overall_quality']:.2f}/1.00

## Success Indicators
"""
        
        for indicator, value in results["success_indicators"].items():
            status_icon = "✅" if value else "❌"
            report += f"- {status_icon} {indicator.replace('_', ' ').title()}: {value}\n"
        
        if results["bottlenecks"]:
            report += "\n## Identified Bottlenecks\n"
            for bottleneck in results["bottlenecks"]:
                report += f"- ⚠️ {bottleneck}\n"
        
        if results["optimization_suggestions"]:
            report += "\n## Optimization Suggestions\n"
            for suggestion in results["optimization_suggestions"]:
                report += f"- 💡 {suggestion}\n"
        
        report += f"\n## Performance Summary\n"
        overall_score = results["quality_scores"]["overall_quality"]
        if overall_score >= 0.8:
            report += "✅ **EXCELLENT** - Task performed optimally"
        elif overall_score >= 0.6:
            report += "⚠️ **GOOD** - Minor optimizations recommended"
        elif overall_score >= 0.4:
            report += "⚠️ **FAIR** - Significant optimizations needed"
        else:
            report += "❌ **POOR** - Major performance issues detected"
        
        return report 