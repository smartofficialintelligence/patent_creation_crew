"""
Validation Pipeline Integration
Integrates quality validation into the main patent automation execution pipeline
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import json

from .quality_validation import QualityValidationManager, ValidationReport, ValidationResult
from .semantic_validators import semantic_validators
from .media_validators import media_validators, CascadeFailurePrevention

logger = logging.getLogger(__name__)

class ValidationPipeline:
    """Main validation pipeline that integrates with the patent automation system"""
    
    def __init__(self):
        self.quality_manager = QualityValidationManager()
        self.cascade_prevention = CascadeFailurePrevention()
        
        # Register specialized validators
        self.quality_manager.validators.update({
            '.ipynb': media_validators['patent_notebook']
        })
        
        # Add specialized validators for specific file patterns
        self.specialized_validators = {
            'patent_application': semantic_validators['patent_document'],
            'prior_art_analysis': semantic_validators['technical_analysis'],
            'legal_review': semantic_validators['technical_analysis'],
            'valuation_report': semantic_validators['technical_analysis'],
            'architecture_diagram': media_validators['architecture_diagram'],
            'colab_demo': media_validators['patent_notebook']
        }
        
        self.validation_history = []
        self.critical_failures = []
        
    def validate_task_output(self, task_name: str, output_file: str, 
                           dependencies: List[str] = None) -> ValidationReport:
        """Validate output from a specific task"""
        logger.info(f"Validating output for task: {task_name}")
        
        # Check cascade failure prevention
        if dependencies:
            cascade_issues = self.cascade_prevention.check_dependencies(task_name, dependencies)
            if cascade_issues:
                logger.warning(f"Cascade failure risks detected for {task_name}")
                for issue in cascade_issues:
                    logger.warning(f"  - {issue}")
        
        # Determine appropriate validator
        validator = self._select_validator(task_name, output_file)
        
        # Perform validation
        if validator:
            report = validator.validate(output_file)
        else:
            report = self.quality_manager.validate_file(output_file)
        
        # Log results
        self._log_validation_result(task_name, report)
        
        # Store in history
        self.validation_history.append({
            'task': task_name,
            'report': report,
            'timestamp': datetime.now()
        })
        
        # Track critical failures
        if report.result == ValidationResult.FAIL:
            self.critical_failures.append({
                'task': task_name,
                'file': output_file,
                'issues': report.critical_issues,
                'timestamp': datetime.now()
            })
        
        return report
    
    def validate_workflow_stage(self, stage_name: str, output_files: List[str], 
                               tier: str = None, patent_id: str = None) -> Dict[str, ValidationReport]:
        """Validate all outputs from a workflow stage"""
        logger.info(f"Validating workflow stage: {stage_name}")
        
        reports = {}
        
        for output_file in output_files:
            if os.path.exists(output_file):
                task_name = self._infer_task_name(output_file)
                report = self.validate_task_output(task_name, output_file)
                reports[output_file] = report
            else:
                logger.warning(f"Output file not found: {output_file}")
                # Create missing file report
                reports[output_file] = self._create_missing_file_report(output_file)
        
        # Check workflow integrity if we have tier and patent_id
        if tier and patent_id:
            integrity_issues = self.cascade_prevention.validate_workflow_integrity(
                "output", tier, patent_id
            )
            if integrity_issues:
                logger.warning(f"Workflow integrity issues detected: {len(integrity_issues)}")
        
        return reports
    
    def validate_complete_workflow(self, tier: str, patent_id: str) -> Dict[str, Any]:
        """Validate complete patent workflow outputs"""
        logger.info(f"Validating complete workflow: {tier}/{patent_id}")
        
        # Use quality manager's workflow validation
        workflow_reports = self.quality_manager.validate_patent_workflow_outputs(tier, patent_id)
        
        # Generate summary
        summary = self.quality_manager.generate_summary_report(list(workflow_reports.values()))
        
        # Check for critical failures that would prevent downstream processing
        cascade_failures = self._check_cascade_failures(workflow_reports)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(workflow_reports, summary)
        
        validation_result = {
            'workflow_id': f"{tier}/{patent_id}",
            'validation_time': datetime.now(),
            'file_reports': workflow_reports,
            'summary': summary,
            'cascade_failures': cascade_failures,
            'recommendations': recommendations,
            'overall_status': self._determine_overall_status(workflow_reports),
            'quality_score': summary['quality_summary']['average_quality_score']
        }
        
        # Save validation report
        self._save_validation_report(validation_result, tier, patent_id)
        
        return validation_result
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of all validation activities"""
        return {
            'total_validations': len(self.validation_history),
            'critical_failures': len(self.critical_failures),
            'recent_validations': self.validation_history[-10:] if self.validation_history else [],
            'failure_rate': (len(self.critical_failures) / len(self.validation_history) * 100) 
                           if self.validation_history else 0,
            'most_common_issues': self._get_common_issues()
        }
    
    def _select_validator(self, task_name: str, output_file: str) -> Optional[Any]:
        """Select appropriate validator based on task and file"""
        # Check for specialized validators first
        for pattern, validator in self.specialized_validators.items():
            if pattern in task_name.lower() or pattern in Path(output_file).name.lower():
                return validator
        
        # Check for architecture diagrams
        if 'architecture' in task_name.lower() or 'diagram' in task_name.lower():
            return media_validators['architecture_diagram']
        
        # Check for notebooks
        if output_file.endswith('.ipynb'):
            return media_validators['patent_notebook']
        
        return None
    
    def _infer_task_name(self, output_file: str) -> str:
        """Infer task name from output file path"""
        filename = Path(output_file).stem
        
        # Common patterns
        if 'patent_application' in filename:
            return 'patent_document'
        elif 'prior_art' in filename:
            return 'prior_art_research'
        elif 'legal_review' in filename:
            return 'legal_review'
        elif 'valuation' in filename:
            return 'patent_valuation'
        elif 'architecture' in filename:
            return 'architecture_diagram'
        elif 'colab' in filename:
            return 'colab_demo'
        elif 'claims' in filename:
            return 'claims_refinement'
        
        return 'unknown_task'
    
    def _log_validation_result(self, task_name: str, report: ValidationReport):
        """Log validation results"""
        if report.result == ValidationResult.PASS:
            logger.info(f"✅ {task_name} validation PASSED (Quality: {report.quality_score:.1f})")
        elif report.result == ValidationResult.PARTIAL:
            logger.warning(f"⚠️  {task_name} validation PARTIAL (Quality: {report.quality_score:.1f}) - {len(report.warning_issues)} warnings")
        else:
            logger.error(f"❌ {task_name} validation FAILED (Quality: {report.quality_score:.1f}) - {len(report.critical_issues)} critical issues")
            
            # Log critical issues
            for issue in report.critical_issues:
                logger.error(f"  CRITICAL: {issue.message}")
                if issue.suggestion:
                    logger.error(f"    Suggestion: {issue.suggestion}")
    
    def _create_missing_file_report(self, file_path: str) -> ValidationReport:
        """Create validation report for missing file"""
        from .quality_validation import ValidationIssue, ValidationLevel
        
        return ValidationReport(
            file_path=file_path,
            file_type="missing",
            result=ValidationResult.FAIL,
            issues=[ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message="Output file is missing",
                file_path=file_path,
                issue_type="missing_file",
                suggestion="Check if the task completed successfully"
            )],
            metadata={},
            validation_time=datetime.now(),
            file_size=0,
            checksum="missing"
        )
    
    def _check_cascade_failures(self, reports: Dict[str, ValidationReport]) -> List[str]:
        """Check for cascade failures that would prevent downstream processing"""
        cascade_failures = []
        
        critical_files = [
            'patent_application', 'prior_art_analysis', 'legal_review'
        ]
        
        for file_pattern in critical_files:
            matching_reports = [r for path, r in reports.items() if file_pattern in path.lower()]
            
            if not matching_reports:
                cascade_failures.append(f"Missing critical file: {file_pattern}")
            else:
                for report in matching_reports:
                    if report.result == ValidationResult.FAIL:
                        cascade_failures.append(f"Critical failure in {file_pattern}: {report.file_path}")
        
        return cascade_failures
    
    def _generate_recommendations(self, reports: Dict[str, ValidationReport], 
                                 summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Quality-based recommendations
        avg_quality = summary['quality_summary']['average_quality_score']
        if avg_quality < 50:
            recommendations.append("CRITICAL: Overall quality is very low - consider regenerating all outputs")
        elif avg_quality < 70:
            recommendations.append("WARNING: Quality is below acceptable threshold - review and improve outputs")
        
        # Failure-based recommendations
        failed_files = summary.get('critical_failures', [])
        if failed_files:
            recommendations.append(f"CRITICAL: Fix {len(failed_files)} failed files before proceeding")
        
        # Issue-based recommendations
        issue_summary = summary.get('issue_summary', {})
        critical_count = issue_summary.get('critical', 0)
        warning_count = issue_summary.get('warning', 0)
        
        if critical_count > 0:
            recommendations.append(f"Fix {critical_count} critical issues to prevent cascade failures")
        
        if warning_count > 10:
            recommendations.append(f"Consider addressing {warning_count} warning issues to improve quality")
        
        # File-type specific recommendations
        file_types = summary.get('file_type_summary', {})
        for file_type, stats in file_types.items():
            if stats['failed'] > 0:
                recommendations.append(f"Review {file_type} files - {stats['failed']} failed validation")
        
        return recommendations
    
    def _determine_overall_status(self, reports: Dict[str, ValidationReport]) -> str:
        """Determine overall workflow status"""
        if not reports:
            return "NO_OUTPUTS"
        
        failed_count = sum(1 for r in reports.values() if r.result == ValidationResult.FAIL)
        partial_count = sum(1 for r in reports.values() if r.result == ValidationResult.PARTIAL)
        
        if failed_count > 0:
            return "FAILED"
        elif partial_count > len(reports) * 0.5:  # More than 50% partial
            return "PARTIAL"
        else:
            return "PASSED"
    
    def _save_validation_report(self, validation_result: Dict[str, Any], tier: str, patent_id: str):
        """Save validation report to file"""
        try:
            output_dir = Path(f"output/{tier}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = output_dir / f"{patent_id}_validation_report.json"
            
            # Convert datetime objects to strings for JSON serialization
            serializable_result = self._make_json_serializable(validation_result)
            
            with open(report_file, 'w') as f:
                json.dump(serializable_result, f, indent=2)
            
            logger.info(f"Validation report saved: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save validation report: {e}")
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._make_json_serializable(obj.__dict__)
        else:
            return obj
    
    def _get_common_issues(self) -> List[Dict[str, Any]]:
        """Get most common validation issues"""
        issue_counts = {}
        
        for validation in self.validation_history:
            report = validation['report']
            for issue in report.issues:
                issue_type = issue.issue_type
                if issue_type not in issue_counts:
                    issue_counts[issue_type] = {
                        'count': 0,
                        'level': issue.level.value,
                        'example_message': issue.message
                    }
                issue_counts[issue_type]['count'] += 1
        
        # Sort by count and return top 5
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1]['count'], reverse=True)
        return [{'issue_type': k, **v} for k, v in sorted_issues[:5]]

class ValidationIntegrationTool:
    """Tool for integrating validation into CrewAI workflows"""
    
    def __init__(self):
        self.pipeline = ValidationPipeline()
    
    def validate_current_task(self, task_name: str, output_file: str, 
                             dependencies: List[str] = None) -> Dict[str, Any]:
        """Validate current task output (for use in CrewAI agents)"""
        
        if not os.path.exists(output_file):
            return {
                'status': 'error',
                'message': f"Output file not found: {output_file}",
                'suggestions': ['Check if the task completed successfully']
            }
        
        # Run validation
        report = self.pipeline.validate_task_output(task_name, output_file, dependencies)
        
        # Format response for agents
        return {
            'status': report.result.value,
            'quality_score': report.quality_score,
            'is_valid': report.is_valid,
            'critical_issues': len(report.critical_issues),
            'warning_issues': len(report.warning_issues),
            'file_size': report.file_size,
            'issues': [
                {
                    'level': issue.level.value,
                    'message': issue.message,
                    'suggestion': issue.suggestion,
                    'type': issue.issue_type
                }
                for issue in report.issues
            ],
            'metadata': report.metadata,
            'recommendations': self._generate_task_recommendations(report)
        }
    
    def _generate_task_recommendations(self, report: ValidationReport) -> List[str]:
        """Generate task-specific recommendations"""
        recommendations = []
        
        if report.critical_issues:
            recommendations.append("CRITICAL: Fix all critical issues before proceeding")
            
        if report.quality_score < 50:
            recommendations.append("Quality is very low - consider regenerating output")
        elif report.quality_score < 70:
            recommendations.append("Quality could be improved - review suggestions")
        
        # Add specific suggestions from issues
        for issue in report.issues[:3]:  # Top 3 issues
            if issue.suggestion:
                recommendations.append(f"TIP: {issue.suggestion}")
        
        return recommendations

# Global instances
validation_pipeline = ValidationPipeline()
validation_tool = ValidationIntegrationTool() 