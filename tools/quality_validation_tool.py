"""
Quality Validation Tool for CrewAI Agents
Provides quality validation capabilities to CrewAI agents during task execution
"""

import os
import logging
from typing import Dict, List, Optional, Any
from crewai.tools import BaseTool
from pathlib import Path

# Import validation pipeline
try:
    from lib.validation_pipeline import validation_tool, validation_pipeline
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    logging.warning("Validation pipeline not available - using fallback validation")

logger = logging.getLogger(__name__)

class QualityValidationTool(BaseTool):
    """Tool for validating task outputs during CrewAI execution"""
    
    name: str = "Quality Validation Tool"
    description: str = """
    Validates the quality of task outputs including semantic content, diagrams, and notebooks.
    Prevents cascade failures by checking output quality before downstream processing.
    
    Use this tool to:
    - Validate patent documents for completeness and quality
    - Check architecture diagrams for technical accuracy
    - Verify notebook demonstrations work correctly
    - Ensure outputs meet quality standards before proceeding
    """
    
    def _run(self, task_name: str, output_file: str, 
             dependencies: Optional[List[str]] = None,
             validation_level: str = "standard") -> str:
        """
        Validate task output and return detailed quality report
        
        Args:
            task_name: Name of the task being validated
            output_file: Path to the output file to validate
            dependencies: List of dependency files (optional)
            validation_level: Level of validation ("quick", "standard", "thorough")
        
        Returns:
            Detailed validation report with quality score and recommendations
        """
        try:
            # Check if validation is available
            if not VALIDATION_AVAILABLE:
                return self._fallback_validation(task_name, output_file)
            
            # Normalize file path
            if not os.path.isabs(output_file):
                output_file = os.path.abspath(output_file)
            
            # Run validation
            validation_result = validation_tool.validate_current_task(
                task_name=task_name,
                output_file=output_file,
                dependencies=dependencies or []
            )
            
            # Format comprehensive report
            return self._format_validation_report(task_name, validation_result, validation_level)
            
        except Exception as e:
            error_msg = f"Validation failed for {task_name}: {str(e)}"
            logger.error(error_msg)
            return f"""
VALIDATION ERROR
===============
Task: {task_name}
File: {output_file}
Error: {str(e)}

The validation system encountered an error. Please check:
1. File exists and is readable
2. File format is supported
3. No permission issues

Proceeding with caution - manual review recommended.
"""

    def _format_validation_report(self, task_name: str, result: Dict[str, Any], 
                                 validation_level: str) -> str:
        """Format validation results into a comprehensive report"""
        
        status = result.get('status', 'unknown')
        quality_score = result.get('quality_score', 0)
        is_valid = result.get('is_valid', False)
        critical_issues = result.get('critical_issues', 0)
        warning_issues = result.get('warning_issues', 0)
        issues = result.get('issues', [])
        recommendations = result.get('recommendations', [])
        metadata = result.get('metadata', {})
        
        # Status emoji
        status_emoji = {
            'pass': '✅',
            'partial': '⚠️',
            'fail': '❌',
            'error': '🚨'
        }.get(status, '❓')
        
        report = f"""
{status_emoji} QUALITY VALIDATION REPORT
=====================================
Task: {task_name}
Status: {status.upper()}
Quality Score: {quality_score:.1f}/100
Valid for Next Stage: {'YES' if is_valid else 'NO'}

ISSUE SUMMARY
=============
🔴 Critical Issues: {critical_issues}
🟡 Warning Issues: {warning_issues}
📊 Overall Assessment: {'PASSED' if is_valid else 'NEEDS ATTENTION'}
"""

        # Add detailed issues if any
        if issues:
            report += "\nDETAILED ISSUES\n===============\n"
            
            # Group issues by level
            critical = [i for i in issues if i['level'] == 'critical']
            warnings = [i for i in issues if i['level'] == 'warning']
            info = [i for i in issues if i['level'] == 'info']
            
            if critical:
                report += "\n🔴 CRITICAL ISSUES (Must Fix):\n"
                for i, issue in enumerate(critical[:5], 1):  # Limit to top 5
                    report += f"{i}. {issue['message']}\n"
                    if issue.get('suggestion'):
                        report += f"   💡 Suggestion: {issue['suggestion']}\n"
                
                if len(critical) > 5:
                    report += f"   ... and {len(critical) - 5} more critical issues\n"
            
            if warnings and validation_level in ['standard', 'thorough']:
                report += "\n🟡 WARNING ISSUES (Should Fix):\n"
                for i, issue in enumerate(warnings[:3], 1):  # Limit to top 3
                    report += f"{i}. {issue['message']}\n"
                    if issue.get('suggestion'):
                        report += f"   💡 Suggestion: {issue['suggestion']}\n"
                
                if len(warnings) > 3:
                    report += f"   ... and {len(warnings) - 3} more warnings\n"
            
            if info and validation_level == 'thorough':
                report += "\n📋 INFORMATIONAL NOTES:\n"
                for i, issue in enumerate(info[:2], 1):  # Limit to top 2
                    report += f"{i}. {issue['message']}\n"
        
        # Add recommendations
        if recommendations:
            report += "\nRECOMMENDATIONS\n===============\n"
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
        
        # Add metadata if available
        if metadata and validation_level == 'thorough':
            report += "\nFILE METADATA\n=============\n"
            if 'word_count' in metadata:
                report += f"Word Count: {metadata['word_count']}\n"
            if 'total_claims' in metadata:
                report += f"Patent Claims: {metadata['total_claims']}\n"
            if 'width' in metadata and 'height' in metadata:
                report += f"Image Dimensions: {metadata['width']}x{metadata['height']}\n"
            if 'total_cells' in metadata:
                report += f"Notebook Cells: {metadata['total_cells']} ({metadata.get('code_cells', 0)} code)\n"
        
        # Add next steps
        report += "\nNEXT STEPS\n==========\n"
        if is_valid:
            report += "✅ Output quality is acceptable - safe to proceed with next task\n"
            if warning_issues > 0:
                report += "💡 Consider addressing warnings to improve quality\n"
        else:
            report += "❌ STOP - Critical issues must be fixed before proceeding\n"
            report += "🔄 Regenerate output after addressing critical issues\n"
            report += "⚠️  Proceeding with failed validation may cause cascade failures\n"
        
        return report

    def _fallback_validation(self, task_name: str, output_file: str) -> str:
        """Fallback validation when main system is unavailable"""
        
        if not os.path.exists(output_file):
            return f"""
❌ FALLBACK VALIDATION FAILED
============================
Task: {task_name}
File: {output_file}

CRITICAL ISSUE: Output file does not exist
This will cause cascade failures in downstream tasks.

REQUIRED ACTION: Check task execution and regenerate output file.
"""
        
        file_size = os.path.getsize(output_file)
        file_ext = Path(output_file).suffix.lower()
        
        issues = []
        
        # Basic file checks
        if file_size < 100:
            issues.append("File is very small (< 100 bytes) - likely corrupted or empty")
        
        # File type specific checks
        if file_ext == '.md':
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                if len(content.strip()) < 200:
                    issues.append("Markdown content is very short")
                if '[TODO]' in content or '[PLACEHOLDER]' in content:
                    issues.append("Contains placeholder text that needs completion")
            except Exception as e:
                issues.append(f"Cannot read markdown file: {e}")
        
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            # Basic image validation
            if file_size > 10 * 1024 * 1024:  # > 10MB
                issues.append("Image file is very large")
        
        elif file_ext == '.ipynb':
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    import json
                    notebook = json.load(f)
                    if 'cells' not in notebook:
                        issues.append("Invalid notebook format")
                    elif len(notebook['cells']) == 0:
                        issues.append("Notebook has no cells")
            except Exception as e:
                issues.append(f"Cannot read notebook: {e}")
        
        # Generate basic report
        status = "FAIL" if issues else "BASIC_PASS"
        
        report = f"""
🔍 FALLBACK VALIDATION REPORT
============================
Task: {task_name}
File: {output_file}
Size: {file_size:,} bytes
Status: {status}

"""
        
        if issues:
            report += "DETECTED ISSUES:\n"
            for i, issue in enumerate(issues, 1):
                report += f"{i}. {issue}\n"
            
            report += "\nRECOMMENDATION: Review and fix issues before proceeding\n"
        else:
            report += "✅ Basic validation passed - file exists and appears valid\n"
            report += "⚠️  Limited validation only - full quality check recommended\n"
        
        return report

class WorkflowValidationTool(BaseTool):
    """Tool for validating complete workflow stages"""
    
    name: str = "Workflow Validation Tool"
    description: str = """
    Validates complete workflow stages and checks for cascade failure risks.
    Use this tool to validate entire workflow outputs before final submission.
    """
    
    def _run(self, tier: str, patent_id: str, stage: str = "complete") -> str:
        """
        Validate complete workflow or specific stage
        
        Args:
            tier: Patent tier (e.g., 'tier_1')
            patent_id: Patent ID (e.g., 'P000')
            stage: Stage to validate ('complete', 'documents', 'media')
        """
        try:
            if not VALIDATION_AVAILABLE:
                return f"❌ Workflow validation not available - using basic checks for {tier}/{patent_id}"
            
            # Run complete workflow validation
            result = validation_pipeline.validate_complete_workflow(tier, patent_id)
            
            return self._format_workflow_report(result, stage)
            
        except Exception as e:
            return f"""
WORKFLOW VALIDATION ERROR
========================
Tier: {tier}
Patent: {patent_id}
Error: {str(e)}

Manual review of outputs recommended.
"""
    
    def _format_workflow_report(self, result: Dict[str, Any], stage: str) -> str:
        """Format complete workflow validation report"""
        
        workflow_id = result.get('workflow_id', 'Unknown')
        overall_status = result.get('overall_status', 'UNKNOWN')
        quality_score = result.get('quality_score', 0)
        summary = result.get('summary', {})
        cascade_failures = result.get('cascade_failures', [])
        recommendations = result.get('recommendations', [])
        
        # Status emoji
        status_emoji = {
            'PASSED': '✅',
            'PARTIAL': '⚠️',
            'FAILED': '❌',
            'NO_OUTPUTS': '📭'
        }.get(overall_status, '❓')
        
        report = f"""
{status_emoji} WORKFLOW VALIDATION REPORT
=================================
Workflow: {workflow_id}
Overall Status: {overall_status}
Quality Score: {quality_score:.1f}/100
Stage: {stage.upper()}

SUMMARY STATISTICS
==================
"""
        
        # Add validation summary
        val_summary = summary.get('validation_summary', {})
        report += f"📊 Files Processed: {val_summary.get('total_files', 0)}\n"
        report += f"✅ Passed: {val_summary.get('passed', 0)}\n"
        report += f"⚠️  Partial: {val_summary.get('partial', 0)}\n"
        report += f"❌ Failed: {val_summary.get('failed', 0)}\n"
        report += f"📈 Pass Rate: {val_summary.get('pass_rate', 0):.1f}%\n"
        
        # Add issue summary
        issue_summary = summary.get('issue_summary', {})
        if issue_summary:
            report += f"\nISSUE BREAKDOWN\n===============\n"
            report += f"🔴 Critical: {issue_summary.get('critical', 0)}\n"
            report += f"🟡 Warning: {issue_summary.get('warning', 0)}\n"
            report += f"📋 Info: {issue_summary.get('info', 0)}\n"
        
        # Add cascade failure warnings
        if cascade_failures:
            report += f"\n🚨 CASCADE FAILURE RISKS\n=======================\n"
            for i, failure in enumerate(cascade_failures, 1):
                report += f"{i}. {failure}\n"
        
        # Add recommendations
        if recommendations:
            report += f"\nRECOMMENDATIONS\n===============\n"
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
        
        # Add final verdict
        report += f"\nFINAL VERDICT\n=============\n"
        if overall_status == 'PASSED':
            report += "✅ Workflow validation PASSED - ready for submission\n"
        elif overall_status == 'PARTIAL':
            report += "⚠️  Workflow has quality issues but can proceed with caution\n"
            report += "💡 Address warnings to improve submission quality\n"
        elif overall_status == 'FAILED':
            report += "❌ Workflow validation FAILED - DO NOT PROCEED\n"
            report += "🔄 Fix critical issues before resubmission\n"
        else:
            report += "❓ Workflow status unclear - manual review required\n"
        
        return report

# Export tools for CrewAI
quality_validation_tool = QualityValidationTool()
workflow_validation_tool = WorkflowValidationTool() 