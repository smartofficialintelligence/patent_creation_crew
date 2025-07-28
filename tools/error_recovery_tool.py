"""
Error Recovery Tool for Patent Automation System
Handles failed tasks and provides recovery options
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from crewai.tools import BaseTool
except ImportError:
    from crewai.tools.agent_tools import Tool as BaseTool

from lib.pydantic_output_models import GenericAnalysisOutput


class ErrorRecoveryInput(BaseTool):
    """Input model for error recovery tool"""
    
    patent_id: str
    failed_task: str
    error_message: str
    task_context: Dict[str, Any]
    retry_attempts: int = 0
    max_retry_attempts: int = 3


class ErrorRecoveryTool(BaseTool):
    """Tool for handling failed tasks and providing recovery options"""
    
    name: str = "error_recovery_tool"
    description: str = """
    Handles failed tasks and provides recovery options.
    
    Parameters:
    - patent_id: Patent identifier
    - failed_task: Name of the failed task
    - error_message: Error message from the failed task
    - task_context: Context information about the task
    - retry_attempts: Number of retry attempts made
    - max_retry_attempts: Maximum number of retry attempts
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _run(self, patent_id: str, failed_task: str, error_message: str,
             task_context: Dict[str, Any], retry_attempts: int = 0,
             max_retry_attempts: int = 3) -> str:
        """
        Handle failed task and provide recovery options
        
        Args:
            patent_id: Patent identifier
            failed_task: Name of the failed task
            error_message: Error message from the failed task
            task_context: Context information about the task
            retry_attempts: Number of retry attempts made
            max_retry_attempts: Maximum number of retry attempts
            
        Returns:
            Error recovery report with recommendations
        """
        
        recovery_results = {
            "patent_id": patent_id,
            "failed_task": failed_task,
            "error_message": error_message,
            "retry_attempts": retry_attempts,
            "max_retry_attempts": max_retry_attempts,
            "root_cause": "",
            "recovery_strategies": [],
            "recommendations": [],
            "fallback_solutions": [],
            "recovery_actions": []
        }
        
        # Analyze error and identify root cause
        root_cause = self._analyze_error(error_message, task_context)
        recovery_results["root_cause"] = root_cause
        
        # Generate recovery strategies
        recovery_strategies = self._generate_recovery_strategies(
            failed_task, root_cause, retry_attempts, max_retry_attempts
        )
        recovery_results["recovery_strategies"] = recovery_strategies
        
        # Generate fallback solutions
        fallback_solutions = self._generate_fallback_solutions(
            failed_task, root_cause, task_context
        )
        recovery_results["fallback_solutions"] = fallback_solutions
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            failed_task, root_cause, retry_attempts, max_retry_attempts
        )
        recovery_results["recommendations"] = recommendations
        
        # Document recovery actions
        recovery_actions = self._document_recovery_actions(
            failed_task, recovery_strategies, fallback_solutions
        )
        recovery_results["recovery_actions"] = recovery_actions
        
        # Create recovery report
        report = self._create_recovery_report(recovery_results)
        
        return report
    
    def _analyze_error(self, error_message: str, task_context: Dict[str, Any]) -> str:
        """Analyze error message and identify root cause"""
        
        error_lower = error_message.lower()
        
        # Common error patterns
        if "timeout" in error_lower or "timed out" in error_lower:
            return "TIMEOUT_ERROR"
        elif "memory" in error_lower or "out of memory" in error_lower:
            return "MEMORY_ERROR"
        elif "network" in error_lower or "connection" in error_lower:
            return "NETWORK_ERROR"
        elif "permission" in error_lower or "access denied" in error_lower:
            return "PERMISSION_ERROR"
        elif "not found" in error_lower or "file not found" in error_lower:
            return "FILE_NOT_FOUND_ERROR"
        elif "syntax" in error_lower or "parsing" in error_lower:
            return "SYNTAX_ERROR"
        elif "import" in error_lower or "module" in error_lower:
            return "IMPORT_ERROR"
        elif "api" in error_lower or "rate limit" in error_lower:
            return "API_ERROR"
        elif "validation" in error_lower or "invalid" in error_lower:
            return "VALIDATION_ERROR"
        else:
            return "UNKNOWN_ERROR"
    
    def _generate_recovery_strategies(self, failed_task: str, root_cause: str,
                                    retry_attempts: int, max_retry_attempts: int) -> List[str]:
        """Generate recovery strategies based on error type"""
        
        strategies = []
        
        if retry_attempts < max_retry_attempts:
            if root_cause == "TIMEOUT_ERROR":
                strategies.extend([
                    "Retry with extended timeout",
                    "Split task into smaller subtasks",
                    "Use parallel processing",
                    "Optimize task parameters"
                ])
            elif root_cause == "MEMORY_ERROR":
                strategies.extend([
                    "Reduce memory usage",
                    "Process data in smaller chunks",
                    "Use memory-efficient algorithms",
                    "Clear cache and temporary files"
                ])
            elif root_cause == "NETWORK_ERROR":
                strategies.extend([
                    "Retry with exponential backoff",
                    "Use alternative API endpoints",
                    "Implement offline fallback",
                    "Check network connectivity"
                ])
            elif root_cause == "API_ERROR":
                strategies.extend([
                    "Retry with rate limiting",
                    "Use alternative API provider",
                    "Implement request throttling",
                    "Check API credentials and limits"
                ])
            elif root_cause == "VALIDATION_ERROR":
                strategies.extend([
                    "Validate input parameters",
                    "Use default values for missing parameters",
                    "Implement input sanitization",
                    "Check data format requirements"
                ])
            else:
                strategies.extend([
                    "Retry with different parameters",
                    "Use alternative approach",
                    "Implement error handling",
                    "Request human intervention"
                ])
        else:
            strategies.append("Maximum retry attempts reached - use fallback solutions")
        
        return strategies
    
    def _generate_fallback_solutions(self, failed_task: str, root_cause: str,
                                   task_context: Dict[str, Any]) -> List[str]:
        """Generate fallback solutions for failed tasks"""
        
        fallbacks = []
        
        # Task-specific fallbacks
        if "prior_art" in failed_task.lower():
            fallbacks.extend([
                "Use cached prior art data",
                "Generate synthetic prior art analysis",
                "Use simplified search parameters",
                "Skip prior art research for this iteration"
            ])
        elif "patent_document" in failed_task.lower():
            fallbacks.extend([
                "Generate simplified patent document",
                "Use template-based document generation",
                "Focus on core claims only",
                "Generate outline for manual completion"
            ])
        elif "claims" in failed_task.lower():
            fallbacks.extend([
                "Use original claims without refinement",
                "Generate basic claim structure",
                "Focus on independent claims only",
                "Use template-based claim generation"
            ])
        elif "diagram" in failed_task.lower():
            fallbacks.extend([
                "Use text-based diagram descriptions",
                "Generate simplified architecture text",
                "Skip diagram generation for this iteration",
                "Use placeholder diagram references"
            ])
        elif "valuation" in failed_task.lower():
            fallbacks.extend([
                "Use estimated valuation based on patent type",
                "Generate basic value assessment",
                "Use industry standard valuation",
                "Skip valuation for this iteration"
            ])
        else:
            fallbacks.extend([
                "Generate simplified output",
                "Use template-based generation",
                "Skip task for this iteration",
                "Request manual intervention"
            ])
        
        return fallbacks
    
    def _generate_recommendations(self, failed_task: str, root_cause: str,
                                retry_attempts: int, max_retry_attempts: int) -> List[str]:
        """Generate recommendations for error prevention"""
        
        recommendations = []
        
        if root_cause == "TIMEOUT_ERROR":
            recommendations.extend([
                "Increase timeout limits for long-running tasks",
                "Implement task splitting for large operations",
                "Add progress monitoring for long tasks",
                "Use asynchronous processing where possible"
            ])
        elif root_cause == "MEMORY_ERROR":
            recommendations.extend([
                "Implement memory monitoring and cleanup",
                "Use streaming processing for large datasets",
                "Optimize data structures for memory efficiency",
                "Add memory limits and garbage collection"
            ])
        elif root_cause == "NETWORK_ERROR":
            recommendations.extend([
                "Implement robust retry mechanisms",
                "Add network connectivity checks",
                "Use multiple API endpoints for redundancy",
                "Implement offline caching strategies"
            ])
        elif root_cause == "API_ERROR":
            recommendations.extend([
                "Implement proper rate limiting",
                "Add API quota monitoring",
                "Use multiple API providers",
                "Implement graceful degradation"
            ])
        elif root_cause == "VALIDATION_ERROR":
            recommendations.extend([
                "Add comprehensive input validation",
                "Implement parameter sanitization",
                "Add default value handling",
                "Improve error messages and logging"
            ])
        
        # General recommendations
        recommendations.extend([
            "Add comprehensive error logging",
            "Implement circuit breaker patterns",
            "Add health checks for external services",
            "Implement graceful degradation strategies"
        ])
        
        return recommendations
    
    def _document_recovery_actions(self, failed_task: str, recovery_strategies: List[str],
                                 fallback_solutions: List[str]) -> List[str]:
        """Document recovery actions taken"""
        
        actions = []
        
        # Document retry attempts
        actions.append(f"Task '{failed_task}' failed - initiating recovery process")
        
        # Document recovery strategies
        for strategy in recovery_strategies:
            actions.append(f"Recovery strategy: {strategy}")
        
        # Document fallback solutions
        for fallback in fallback_solutions:
            actions.append(f"Fallback solution: {fallback}")
        
        # Document timestamp
        actions.append(f"Recovery initiated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return actions
    
    def _create_recovery_report(self, results: Dict[str, Any]) -> str:
        """Create comprehensive recovery report"""
        
        report = f"""
# Error Recovery Report

## Failed Task Information
- **Patent ID**: {results['patent_id']}
- **Failed Task**: {results['failed_task']}
- **Retry Attempts**: {results['retry_attempts']}/{results['max_retry_attempts']}
- **Error Message**: {results['error_message']}

## Root Cause Analysis
**Identified Cause**: {results['root_cause']}

## Recovery Strategies
"""
        
        for strategy in results["recovery_strategies"]:
            report += f"- 🔧 {strategy}\n"
        
        report += "\n## Fallback Solutions\n"
        for fallback in results["fallback_solutions"]:
            report += f"- 🛡️ {fallback}\n"
        
        report += "\n## Recommendations for Prevention\n"
        for rec in results["recommendations"]:
            report += f"- 💡 {rec}\n"
        
        report += "\n## Recovery Actions Taken\n"
        for action in results["recovery_actions"]:
            report += f"- ⏱️ {action}\n"
        
        report += f"\n## Recovery Status\n"
        if results["retry_attempts"] < results["max_retry_attempts"]:
            report += "🔄 **RETRYING** - Attempting recovery with modified parameters"
        else:
            report += "⚠️ **FALLBACK** - Using fallback solutions due to max retry attempts"
        
        return report 