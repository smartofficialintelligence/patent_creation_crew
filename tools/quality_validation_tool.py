"""
Quality Validation Tool for Patent Automation System
Validates output quality and completeness for all generated documents
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    from crewai.tools import BaseTool
except ImportError:
    from crewai.tools.agent_tools import Tool as BaseTool

from lib.pydantic_output_models import GenericAnalysisOutput


class QualityValidationInput(BaseTool):
    """Input model for quality validation tool"""
    
    patent_id: str
    title: str
    phase: str
    quality_gates: Dict[str, Any]
    required_files: List[str]
    quality_threshold: float = 0.7


class QualityValidationTool(BaseTool):
    """Tool for validating output quality and completeness"""
    
    name: str = "quality_validation_tool"
    description: str = """
    Validates output quality and completeness for all generated documents.
    
    Parameters:
    - patent_id: Patent identifier
    - title: Patent title
    - phase: Processing phase
    - quality_gates: Quality gate requirements
    - required_files: List of required output files
    - quality_threshold: Minimum quality score (0.0-1.0)
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _run(self, patent_id: str, title: str, phase: str, 
             quality_gates: Dict[str, Any], required_files: List[str], 
             quality_threshold: float = 0.7) -> str:
        """
        Validate output quality and completeness
        
        Args:
            patent_id: Patent identifier
            title: Patent title
            phase: Processing phase
            quality_gates: Quality gate requirements
            required_files: List of required output files
            quality_threshold: Minimum quality score
            
        Returns:
            Quality validation report
        """
        
        output_dir = Path(f"output/{phase}")
        validation_results = {
            "patent_id": patent_id,
            "title": title,
            "phase": phase,
            "overall_score": 0.0,
            "file_completeness": {},
            "content_quality": {},
            "technical_accuracy": {},
            "format_compliance": {},
            "recommendations": [],
            "errors": [],
            "warnings": []
        }
        
        # Check file completeness
        file_completeness_score = self._check_file_completeness(
            output_dir, required_files, validation_results
        )
        
        # Check content quality
        content_quality_score = self._check_content_quality(
            output_dir, patent_id, validation_results
        )
        
        # Check technical accuracy
        technical_accuracy_score = self._check_technical_accuracy(
            output_dir, patent_id, validation_results
        )
        
        # Check format compliance
        format_compliance_score = self._check_format_compliance(
            output_dir, patent_id, validation_results
        )
        
        # Calculate overall score
        validation_results["overall_score"] = (
            file_completeness_score * 0.3 +
            content_quality_score * 0.3 +
            technical_accuracy_score * 0.2 +
            format_compliance_score * 0.2
        )
        
        # Generate recommendations
        self._generate_recommendations(validation_results, quality_threshold)
        
        # Create validation report
        report = self._create_validation_report(validation_results)
        
        return report
    
    def _check_file_completeness(self, output_dir: Path, required_files: List[str], 
                                results: Dict[str, Any]) -> float:
        """Check if all required files are present"""
        
        score = 0.0
        total_files = len(required_files)
        present_files = 0
        
        for file_pattern in required_files:
            file_path = output_dir / file_pattern.format(patent_id=results["patent_id"])
            if file_path.exists():
                present_files += 1
                results["file_completeness"][str(file_path)] = {
                    "status": "present",
                    "size": file_path.stat().st_size if file_path.exists() else 0
                }
            else:
                results["file_completeness"][str(file_path)] = {
                    "status": "missing",
                    "size": 0
                }
                results["errors"].append(f"Missing required file: {file_path}")
        
        score = present_files / total_files if total_files > 0 else 0.0
        return score
    
    def _check_content_quality(self, output_dir: Path, patent_id: str, 
                             results: Dict[str, Any]) -> float:
        """Check content quality of generated files"""
        
        score = 0.0
        total_files = 0
        quality_scores = []
        
        for file_path in output_dir.glob(f"{patent_id}_*.md"):
            total_files += 1
            file_score = self._analyze_file_content(file_path)
            quality_scores.append(file_score)
            
            results["content_quality"][str(file_path)] = {
                "score": file_score,
                "word_count": self._count_words(file_path),
                "has_technical_content": self._has_technical_content(file_path),
                "has_claims": self._has_claims(file_path)
            }
        
        score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        return score
    
    def _check_technical_accuracy(self, output_dir: Path, patent_id: str, 
                                results: Dict[str, Any]) -> float:
        """Check technical accuracy of content"""
        
        score = 0.0
        total_files = 0
        accuracy_scores = []
        
        for file_path in output_dir.glob(f"{patent_id}_*.md"):
            total_files += 1
            file_score = self._analyze_technical_accuracy(file_path)
            accuracy_scores.append(file_score)
            
            results["technical_accuracy"][str(file_path)] = {
                "score": file_score,
                "has_code_examples": self._has_code_examples(file_path),
                "has_diagrams": self._has_diagrams(file_path),
                "has_technical_specs": self._has_technical_specs(file_path)
            }
        
        score = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0
        return score
    
    def _check_format_compliance(self, output_dir: Path, patent_id: str, 
                               results: Dict[str, Any]) -> float:
        """Check format compliance"""
        
        score = 0.0
        total_files = 0
        compliance_scores = []
        
        for file_path in output_dir.glob(f"{patent_id}_*.md"):
            total_files += 1
            file_score = self._analyze_format_compliance(file_path)
            compliance_scores.append(file_score)
            
            results["format_compliance"][str(file_path)] = {
                "score": file_score,
                "is_markdown": self._is_valid_markdown(file_path),
                "has_proper_structure": self._has_proper_structure(file_path),
                "no_json_content": self._no_json_content(file_path)
            }
        
        score = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0.0
        return score
    
    def _analyze_file_content(self, file_path: Path) -> float:
        """Analyze content quality of a file"""
        
        if not file_path.exists():
            return 0.0
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Basic quality checks
            word_count = len(content.split())
            if word_count < 100:
                return 0.3
            elif word_count < 500:
                return 0.6
            elif word_count < 1000:
                return 0.8
            else:
                return 1.0
                
        except Exception:
            return 0.0
    
    def _analyze_technical_accuracy(self, file_path: Path) -> float:
        """Analyze technical accuracy of a file"""
        
        if not file_path.exists():
            return 0.0
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Technical accuracy indicators
            technical_indicators = [
                "algorithm", "implementation", "architecture", "system",
                "component", "module", "function", "class", "method",
                "optimization", "performance", "efficiency", "scalability"
            ]
            
            indicator_count = sum(1 for indicator in technical_indicators 
                                if indicator.lower() in content.lower())
            
            return min(1.0, indicator_count / 5.0)
            
        except Exception:
            return 0.0
    
    def _analyze_format_compliance(self, file_path: Path) -> float:
        """Analyze format compliance of a file"""
        
        if not file_path.exists():
            return 0.0
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Format compliance checks
            score = 0.0
            
            # Check if it's markdown
            if content.startswith('#') or '##' in content:
                score += 0.4
            
            # Check for proper structure
            if any(section in content.lower() for section in ['background', 'claims', 'description']):
                score += 0.3
            
            # Check for no JSON content
            if not content.strip().startswith('{') and not content.strip().startswith('['):
                score += 0.3
            
            return score
            
        except Exception:
            return 0.0
    
    def _count_words(self, file_path: Path) -> int:
        """Count words in a file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            return len(content.split())
        except Exception:
            return 0
    
    def _has_technical_content(self, file_path: Path) -> bool:
        """Check if file has technical content"""
        try:
            content = file_path.read_text(encoding='utf-8').lower()
            technical_terms = ['algorithm', 'implementation', 'system', 'architecture']
            return any(term in content for term in technical_terms)
        except Exception:
            return False
    
    def _has_claims(self, file_path: Path) -> bool:
        """Check if file has claims"""
        try:
            content = file_path.read_text(encoding='utf-8').lower()
            return 'claim' in content or 'claims' in content
        except Exception:
            return False
    
    def _has_code_examples(self, file_path: Path) -> bool:
        """Check if file has code examples"""
        try:
            content = file_path.read_text(encoding='utf-8')
            return '```' in content or 'def ' in content or 'class ' in content
        except Exception:
            return False
    
    def _has_diagrams(self, file_path: Path) -> bool:
        """Check if file has diagrams"""
        try:
            content = file_path.read_text(encoding='utf-8')
            return 'diagram' in content.lower() or 'figure' in content.lower()
        except Exception:
            return False
    
    def _has_technical_specs(self, file_path: Path) -> bool:
        """Check if file has technical specifications"""
        try:
            content = file_path.read_text(encoding='utf-8').lower()
            spec_terms = ['specification', 'requirements', 'technical', 'implementation']
            return any(term in content for term in spec_terms)
        except Exception:
            return False
    
    def _is_valid_markdown(self, file_path: Path) -> bool:
        """Check if file is valid markdown"""
        try:
            content = file_path.read_text(encoding='utf-8')
            return content.startswith('#') or '##' in content or '**' in content
        except Exception:
            return False
    
    def _has_proper_structure(self, file_path: Path) -> bool:
        """Check if file has proper structure"""
        try:
            content = file_path.read_text(encoding='utf-8').lower()
            structure_indicators = ['background', 'claims', 'description', 'summary']
            return any(indicator in content for indicator in structure_indicators)
        except Exception:
            return False
    
    def _no_json_content(self, file_path: Path) -> bool:
        """Check if file doesn't contain JSON content"""
        try:
            content = file_path.read_text(encoding='utf-8')
            return not (content.strip().startswith('{') or content.strip().startswith('['))
        except Exception:
            return True
    
    def _generate_recommendations(self, results: Dict[str, Any], quality_threshold: float):
        """Generate recommendations based on validation results"""
        
        if results["overall_score"] < quality_threshold:
            results["recommendations"].append(
                f"Overall quality score ({results['overall_score']:.2f}) is below threshold ({quality_threshold})"
            )
        
        # File completeness recommendations
        missing_files = [f for f, info in results["file_completeness"].items() 
                        if info["status"] == "missing"]
        if missing_files:
            results["recommendations"].append(f"Missing files: {', '.join(missing_files)}")
        
        # Content quality recommendations
        low_quality_files = [f for f, info in results["content_quality"].items() 
                           if info["score"] < 0.5]
        if low_quality_files:
            results["recommendations"].append(f"Low quality content in: {', '.join(low_quality_files)}")
        
        # Technical accuracy recommendations
        low_accuracy_files = [f for f, info in results["technical_accuracy"].items() 
                            if info["score"] < 0.5]
        if low_accuracy_files:
            results["recommendations"].append(f"Low technical accuracy in: {', '.join(low_accuracy_files)}")
        
        # Format compliance recommendations
        non_compliant_files = [f for f, info in results["format_compliance"].items() 
                              if info["score"] < 0.5]
        if non_compliant_files:
            results["recommendations"].append(f"Format compliance issues in: {', '.join(non_compliant_files)}")
    
    def _create_validation_report(self, results: Dict[str, Any]) -> str:
        """Create comprehensive validation report"""
        
        report = f"""
# Quality Validation Report

## Patent Information
- **Patent ID**: {results['patent_id']}
- **Title**: {results['title']}
- **Phase**: {results['phase']}

## Overall Quality Score
**Score**: {results['overall_score']:.2f}/1.00

## File Completeness
"""
        
        for file_path, info in results["file_completeness"].items():
            status_icon = "✅" if info["status"] == "present" else "❌"
            report += f"- {status_icon} {file_path} ({info['status']}, {info['size']} bytes)\n"
        
        report += "\n## Content Quality Analysis\n"
        for file_path, info in results["content_quality"].items():
            report += f"- {file_path}: {info['score']:.2f}/1.00 ({info['word_count']} words)\n"
        
        report += "\n## Technical Accuracy Analysis\n"
        for file_path, info in results["technical_accuracy"].items():
            report += f"- {file_path}: {info['score']:.2f}/1.00\n"
        
        report += "\n## Format Compliance Analysis\n"
        for file_path, info in results["format_compliance"].items():
            report += f"- {file_path}: {info['score']:.2f}/1.00\n"
        
        if results["errors"]:
            report += "\n## Errors\n"
            for error in results["errors"]:
                report += f"- ❌ {error}\n"
        
        if results["warnings"]:
            report += "\n## Warnings\n"
            for warning in results["warnings"]:
                report += f"- ⚠️ {warning}\n"
        
        if results["recommendations"]:
            report += "\n## Recommendations\n"
            for rec in results["recommendations"]:
                report += f"- 💡 {rec}\n"
        
        report += f"\n## Summary\n"
        if results["overall_score"] >= 0.8:
            report += "✅ **EXCELLENT** - All quality standards met"
        elif results["overall_score"] >= 0.6:
            report += "⚠️ **GOOD** - Minor improvements recommended"
        elif results["overall_score"] >= 0.4:
            report += "⚠️ **FAIR** - Significant improvements needed"
        else:
            report += "❌ **POOR** - Major quality issues detected"
        
        return report 