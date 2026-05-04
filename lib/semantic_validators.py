"""
Semantic Validators for Patent Automation
Provides specialized validation for semantic text content, patent documents, and technical analyses
"""

import re
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import json
from datetime import datetime
import os

from .quality_validation import ValidationIssue, ValidationLevel, ValidationReport, BaseValidator, ValidationResult

logger = logging.getLogger(__name__)

@dataclass
class SemanticRule:
    """Represents a semantic validation rule"""
    name: str
    pattern: str
    required: bool = False
    context_keywords: List[str] = None
    min_occurrences: int = 1
    max_occurrences: Optional[int] = None
    description: str = ""
    
    def __post_init__(self):
        if self.context_keywords is None:
            self.context_keywords = []

class PatentDocumentValidator(BaseValidator):
    """Specialized validator for patent documents"""
    
    def __init__(self):
        super().__init__()
        self.patent_sections = {
            'title': SemanticRule(
                name="title",
                pattern=r'^#\s+(.+)$',
                required=True,
                min_occurrences=1,
                max_occurrences=1,
                description="Patent title"
            ),
            'background': SemanticRule(
                name="background",
                pattern=r'(?i)background|prior\s+art|field\s+of\s+(the\s+)?invention',
                required=True,
                description="Background section"
            ),
            'summary': SemanticRule(
                name="summary",
                pattern=r'(?i)summary|brief\s+description',
                required=True,
                description="Summary section"
            ),
            'detailed_description': SemanticRule(
                name="detailed_description",
                pattern=r'(?i)detailed\s+description|description\s+of\s+(the\s+)?invention',
                required=True,
                description="Detailed description section"
            ),
            'claims': SemanticRule(
                name="claims",
                pattern=r'(?i)claims?',
                required=True,
                description="Claims section"
            ),
            'abstract': SemanticRule(
                name="abstract",
                pattern=r'(?i)abstract',
                required=False,
                description="Abstract section"
            )
        }
        
        self.technical_indicators = [
            'method', 'system', 'apparatus', 'device', 'process', 'algorithm',
            'protocol', 'architecture', 'framework', 'implementation', 'optimization',
            'interface', 'component', 'mechanism', 'technique', 'approach'
        ]
        
        self.claim_patterns = {
            'independent_claim': r'^\s*(\d+)\.\s+(.+)$',
            'dependent_claim': r'^\s*(\d+)\.\s+(?:the\s+)?(?:method|system|apparatus|device)\s+(?:of|according\s+to)\s+claim\s+(\d+)',
            'means_plus_function': r'means\s+for\s+\w+',
            'step_plus_function': r'step\s+(?:of|for)\s+\w+'
        }
    
    def validate(self, file_path: str) -> ValidationReport:
        """Validate patent document"""
        issues = []
        metadata = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Patent-specific validations
            issues.extend(self._validate_patent_sections(file_path, content))
            issues.extend(self._validate_claims_structure(file_path, content))
            issues.extend(self._validate_technical_content(file_path, content))
            issues.extend(self._validate_enablement(file_path, content))
            issues.extend(self._validate_novelty_indicators(file_path, content))
            
            # Extract metadata
            metadata = self._extract_patent_metadata(content)
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Failed to read patent document: {str(e)}",
                file_path=file_path,
                issue_type="file_access"
            ))
        
        # Determine result
        result = self._determine_result(issues)
        
        return ValidationReport(
            file_path=file_path,
            file_type="patent_document",
            result=result,
            issues=issues,
            metadata=metadata,
            validation_time=datetime.now(),
            file_size=self._get_file_size(file_path),
            checksum=self._calculate_checksum(file_path)
        )
    
    def _validate_patent_sections(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate required patent sections"""
        issues = []
        
        for section_name, rule in self.patent_sections.items():
            matches = re.findall(rule.pattern, content, re.MULTILINE)
            
            if rule.required and len(matches) < rule.min_occurrences:
                issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    message=f"Missing required section: {rule.description}",
                    file_path=file_path,
                    issue_type="missing_section",
                    suggestion=f"Add {rule.description} section to patent document"
                ))
            elif rule.max_occurrences and len(matches) > rule.max_occurrences:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Too many instances of {rule.description}: {len(matches)}",
                    file_path=file_path,
                    issue_type="duplicate_section",
                    suggestion=f"Consolidate {rule.description} sections"
                ))
        
        return issues
    
    def _validate_claims_structure(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate patent claims structure"""
        issues = []
        
        # Find claims section
        claims_match = re.search(r'(?i)claims?\s*\n(.*?)(?=\n\s*#{1,3}\s|\Z)', content, re.DOTALL)
        if not claims_match:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message="No claims section found in patent document",
                file_path=file_path,
                issue_type="missing_claims_section",
                suggestion="Add claims section with numbered claims"
            ))
            return issues
        
        claims_content = claims_match.group(1)
        
        # Find all numbered claims
        numbered_claims = re.findall(self.claim_patterns['independent_claim'], claims_content, re.MULTILINE)
        
        if not numbered_claims:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message="No properly formatted numbered claims found",
                file_path=file_path,
                issue_type="invalid_claims_format",
                suggestion="Format claims as numbered list (1. First claim, 2. Second claim, etc.)"
            ))
            return issues
        
        # Validate claim numbering
        claim_numbers = [int(match[0]) for match in numbered_claims]
        expected_numbers = list(range(1, len(claim_numbers) + 1))
        
        if claim_numbers != expected_numbers:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Claims numbering issue: found {claim_numbers}, expected {expected_numbers}",
                file_path=file_path,
                issue_type="claim_numbering",
                suggestion="Ensure claims are numbered sequentially starting from 1"
            ))
        
        # Check for independent vs dependent claims
        dependent_claims = re.findall(self.claim_patterns['dependent_claim'], claims_content, re.MULTILINE)
        
        if len(numbered_claims) == 1 and len(dependent_claims) == 0:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Only one claim found - consider adding dependent claims",
                file_path=file_path,
                issue_type="single_claim",
                suggestion="Add dependent claims to strengthen patent protection"
            ))
        
        # Check for overly broad claims
        for i, (claim_num, claim_text) in enumerate(numbered_claims):
            if len(claim_text.split()) < 10:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Claim {claim_num} appears too short ({len(claim_text.split())} words)",
                    file_path=file_path,
                    issue_type="short_claim",
                    suggestion="Ensure claims have sufficient technical detail"
                ))
            elif len(claim_text.split()) > 200:
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    message=f"Claim {claim_num} is very long ({len(claim_text.split())} words)",
                    file_path=file_path,
                    issue_type="long_claim",
                    suggestion="Consider breaking long claims into multiple dependent claims"
                ))
        
        return issues
    
    def _validate_technical_content(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate technical content quality"""
        issues = []
        
        # Check for technical indicators
        technical_count = 0
        for indicator in self.technical_indicators:
            technical_count += len(re.findall(rf'\b{indicator}\b', content, re.IGNORECASE))
        
        if technical_count < 10:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Low technical content density ({technical_count} technical terms)",
                file_path=file_path,
                issue_type="low_technical_density",
                suggestion="Add more technical details and explanations"
            ))
        
        # Check for implementation examples
        implementation_indicators = ['example', 'embodiment', 'implementation', 'instance', 'figure']
        impl_count = sum(len(re.findall(rf'\b{indicator}\b', content, re.IGNORECASE)) 
                        for indicator in implementation_indicators)
        
        if impl_count < 3:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Few implementation examples found",
                file_path=file_path,
                issue_type="few_examples",
                suggestion="Add more examples and embodiments to strengthen enablement"
            ))
        
        # Check for technical figures references
        figure_refs = re.findall(r'(?i)figure?\s*\d+|fig\.?\s*\d+', content)
        if not figure_refs:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="No figure references found",
                file_path=file_path,
                issue_type="no_figure_refs",
                suggestion="Consider adding technical diagrams and figure references"
            ))
        
        return issues
    
    def _validate_enablement(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate enablement sufficiency"""
        issues = []
        
        # Check for enablement keywords
        enablement_keywords = [
            'skilled artisan', 'skilled in the art', 'person skilled', 'ordinary skill',
            'implementation', 'embodiment', 'example', 'detailed description',
            'method comprises', 'system includes', 'apparatus comprises'
        ]
        
        enablement_count = 0
        for keyword in enablement_keywords:
            enablement_count += len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE))
        
        if enablement_count < 5:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Insufficient enablement language",
                file_path=file_path,
                issue_type="insufficient_enablement",
                suggestion="Add more detailed implementation descriptions for skilled artisan"
            ))
        
        # Check for step-by-step descriptions
        step_patterns = [
            r'(?i)step\s+\d+', r'(?i)first.*second.*third', r'(?i)initially.*then.*finally',
            r'(?i)comprises.*steps', r'(?i)method.*includes'
        ]
        
        step_count = sum(len(re.findall(pattern, content)) for pattern in step_patterns)
        
        if step_count < 2:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Few step-by-step descriptions found",
                file_path=file_path,
                issue_type="few_steps",
                suggestion="Add more detailed step-by-step process descriptions"
            ))
        
        return issues
    
    def _validate_novelty_indicators(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate novelty and differentiation indicators"""
        issues = []
        
        # Check for prior art discussion
        prior_art_keywords = [
            'prior art', 'existing', 'conventional', 'traditional', 'known',
            'current', 'previous', 'background', 'related work'
        ]
        
        prior_art_count = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) 
                             for keyword in prior_art_keywords)
        
        if prior_art_count < 5:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Limited prior art discussion",
                file_path=file_path,
                issue_type="limited_prior_art",
                suggestion="Add more discussion of prior art and background"
            ))
        
        # Check for novelty indicators
        novelty_keywords = [
            'novel', 'new', 'innovative', 'improved', 'enhanced', 'advanced',
            'unique', 'different', 'superior', 'advantageous', 'unexpected'
        ]
        
        novelty_count = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) 
                           for keyword in novelty_keywords)
        
        if novelty_count < 3:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Few novelty indicators found",
                file_path=file_path,
                issue_type="few_novelty_indicators",
                suggestion="Highlight novel and innovative aspects more clearly"
            ))
        
        return issues
    
    def _extract_patent_metadata(self, content: str) -> Dict[str, Any]:
        """Extract patent-specific metadata"""
        metadata = {}
        
        # Count claims
        claims_match = re.search(r'(?i)claims?\s*\n(.*?)(?=\n\s*#{1,3}\s|\Z)', content, re.DOTALL)
        if claims_match:
            claims_content = claims_match.group(1)
            numbered_claims = re.findall(self.claim_patterns['independent_claim'], claims_content, re.MULTILINE)
            dependent_claims = re.findall(self.claim_patterns['dependent_claim'], claims_content, re.MULTILINE)
            
            metadata['total_claims'] = len(numbered_claims)
            metadata['independent_claims'] = len(numbered_claims) - len(dependent_claims)
            metadata['dependent_claims'] = len(dependent_claims)
        
        # Technical density
        technical_count = sum(len(re.findall(rf'\b{indicator}\b', content, re.IGNORECASE)) 
                             for indicator in self.technical_indicators)
        metadata['technical_density'] = technical_count / len(content.split()) if content else 0
        
        # Figure references
        figure_refs = re.findall(r'(?i)figure?\s*\d+|fig\.?\s*\d+', content)
        metadata['figure_references'] = len(figure_refs)
        
        return metadata

    def _determine_result(self, issues: List[ValidationIssue]) -> ValidationResult:
        """Determine validation result based on issues"""
        if any(issue.level == ValidationLevel.CRITICAL for issue in issues):
            return ValidationResult.FAIL
        elif any(issue.level == ValidationLevel.WARNING for issue in issues):
            return ValidationResult.PARTIAL
        else:
            return ValidationResult.PASS

    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file"""
        try:
            import hashlib
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception:
            return "unknown"

class TechnicalAnalysisValidator(BaseValidator):
    """Validator for technical analysis documents (prior art, legal review, etc.)"""
    
    def __init__(self):
        super().__init__()
        self.analysis_types = {
            'prior_art': {
                'required_sections': ['search methodology', 'findings', 'analysis', 'recommendations'],
                'technical_indicators': ['patent', 'publication', 'search', 'database', 'novelty'],
                'min_references': 5
            },
            'legal_review': {
                'required_sections': ['compliance', 'analysis', 'risk', 'recommendation'],
                'technical_indicators': ['claim', 'patent', 'legal', 'compliance', 'risk'],
                'min_references': 3
            },
            'valuation': {
                'required_sections': ['methodology', 'analysis', 'valuation', 'conclusion'],
                'technical_indicators': ['market', 'value', 'revenue', 'cost', 'roi'],
                'min_references': 2
            }
        }
    
    def validate(self, file_path: str) -> ValidationReport:
        """Validate technical analysis document"""
        issues = []
        metadata = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine analysis type from filename
            analysis_type = self._determine_analysis_type(file_path)
            
            if analysis_type:
                issues.extend(self._validate_analysis_structure(file_path, content, analysis_type))
                issues.extend(self._validate_analysis_content(file_path, content, analysis_type))
                metadata = self._extract_analysis_metadata(content, analysis_type)
            else:
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    message="Could not determine analysis type from filename",
                    file_path=file_path,
                    issue_type="unknown_analysis_type"
                ))
            
            # General quality checks
            issues.extend(self._validate_general_quality(file_path, content))
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Failed to read analysis document: {str(e)}",
                file_path=file_path,
                issue_type="file_access"
            ))
        
        result = self._determine_result(issues)
        
        return ValidationReport(
            file_path=file_path,
            file_type="technical_analysis",
            result=result,
            issues=issues,
            metadata=metadata,
            validation_time=datetime.now(),
            file_size=self._get_file_size(file_path),
            checksum=self._calculate_checksum(file_path)
        )
    
    def _determine_analysis_type(self, file_path: str) -> Optional[str]:
        """Determine analysis type from filename"""
        filename = Path(file_path).name.lower()
        
        if 'prior_art' in filename:
            return 'prior_art'
        elif 'legal' in filename:
            return 'legal_review'
        elif 'valuation' in filename:
            return 'valuation'
        
        return None
    
    def _validate_analysis_structure(self, file_path: str, content: str, analysis_type: str) -> List[ValidationIssue]:
        """Validate analysis document structure"""
        issues = []
        
        config = self.analysis_types[analysis_type]
        
        for section in config['required_sections']:
            if not re.search(rf'(?i){section}', content):
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Missing recommended section: {section}",
                    file_path=file_path,
                    issue_type="missing_section",
                    suggestion=f"Add {section} section to {analysis_type} document"
                ))
        
        return issues
    
    def _validate_analysis_content(self, file_path: str, content: str, analysis_type: str) -> List[ValidationIssue]:
        """Validate analysis content quality"""
        issues = []
        
        config = self.analysis_types[analysis_type]
        
        # Check for technical indicators
        indicator_count = 0
        for indicator in config['technical_indicators']:
            indicator_count += len(re.findall(rf'\b{indicator}\b', content, re.IGNORECASE))
        
        if indicator_count < config['min_references']:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Low technical indicator count ({indicator_count} < {config['min_references']})",
                file_path=file_path,
                issue_type="low_technical_content",
                suggestion=f"Add more {analysis_type}-specific technical content"
            ))
        
        # Check for specific analysis type requirements
        if analysis_type == 'prior_art':
            issues.extend(self._validate_prior_art_specifics(file_path, content))
        elif analysis_type == 'legal_review':
            issues.extend(self._validate_legal_review_specifics(file_path, content))
        elif analysis_type == 'valuation':
            issues.extend(self._validate_valuation_specifics(file_path, content))
        
        return issues
    
    def _validate_prior_art_specifics(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate prior art analysis specifics"""
        issues = []
        
        # Check for search databases
        databases = ['lens', 'google patents', 'espacenet', 'uspto', 'wipo', 'arxiv']
        database_mentions = sum(1 for db in databases if db in content.lower())
        
        if database_mentions < 2:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Few patent databases mentioned",
                file_path=file_path,
                issue_type="limited_databases",
                suggestion="Mention more patent databases searched"
            ))
        
        # Check for novelty assessment
        novelty_keywords = ['novelty', 'novel', 'non-obvious', 'inventive step', 'patentable']
        novelty_count = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) 
                           for keyword in novelty_keywords)
        
        if novelty_count < 3:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Limited novelty assessment",
                file_path=file_path,
                issue_type="limited_novelty_assessment",
                suggestion="Add more detailed novelty and patentability analysis"
            ))
        
        return issues
    
    def _validate_legal_review_specifics(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate legal review specifics"""
        issues = []
        
        # Check for legal standards
        legal_standards = ['uspto', 'patent law', 'claim construction', 'prosecution', 'validity']
        legal_count = sum(len(re.findall(rf'\b{standard}\b', content, re.IGNORECASE)) 
                         for standard in legal_standards)
        
        if legal_count < 3:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Few legal standards mentioned",
                file_path=file_path,
                issue_type="limited_legal_standards",
                suggestion="Reference more patent law standards and requirements"
            ))
        
        # Check for risk assessment
        risk_keywords = ['risk', 'challenge', 'rejection', 'invalidity', 'infringement']
        risk_count = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) 
                        for keyword in risk_keywords)
        
        if risk_count < 2:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Limited risk assessment",
                file_path=file_path,
                issue_type="limited_risk_assessment",
                suggestion="Add more detailed risk analysis"
            ))
        
        return issues
    
    def _validate_valuation_specifics(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate valuation report specifics"""
        issues = []
        
        # Check for monetary values
        monetary_patterns = [r'\$[\d,]+[KMB]?', r'USD\s+[\d,]+', r'[\d,]+\s+(?:million|billion|thousand)']
        monetary_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                            for pattern in monetary_patterns)
        
        if monetary_count < 2:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Few monetary values found",
                file_path=file_path,
                issue_type="limited_monetary_values",
                suggestion="Include specific valuation amounts and ranges"
            ))
        
        # Check for market analysis
        market_keywords = ['market', 'industry', 'segment', 'competition', 'revenue', 'growth']
        market_count = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) 
                          for keyword in market_keywords)
        
        if market_count < 5:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Limited market analysis",
                file_path=file_path,
                issue_type="limited_market_analysis",
                suggestion="Add more market and industry analysis"
            ))
        
        return issues
    
    def _validate_general_quality(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate general document quality"""
        issues = []
        
        # Check for conclusions/recommendations
        conclusion_keywords = ['conclusion', 'recommendation', 'summary', 'findings']
        conclusion_count = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) 
                              for keyword in conclusion_keywords)
        
        if conclusion_count < 1:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="No clear conclusions or recommendations found",
                file_path=file_path,
                issue_type="no_conclusions",
                suggestion="Add clear conclusions and recommendations section"
            ))
        
        return issues
    
    def _extract_analysis_metadata(self, content: str, analysis_type: str) -> Dict[str, Any]:
        """Extract analysis-specific metadata"""
        metadata = {'analysis_type': analysis_type}
        
        # Count references and citations
        references = re.findall(r'(?i)(?:patent|publication|paper|article|reference)', content)
        metadata['reference_count'] = len(references)
        
        # Count recommendations
        recommendations = re.findall(r'(?i)recommend|suggest|advise|propose', content)
        metadata['recommendation_count'] = len(recommendations)
        
        return metadata
    
    def _determine_result(self, issues: List[ValidationIssue]) -> ValidationResult:
        """Determine validation result based on issues"""
        if any(issue.level == ValidationLevel.CRITICAL for issue in issues):
            return ValidationResult.FAIL
        elif any(issue.level == ValidationLevel.WARNING for issue in issues):
            return ValidationResult.PARTIAL
        else:
            return ValidationResult.PASS

# Register validators
semantic_validators = {
    'patent_document': PatentDocumentValidator(),
    'technical_analysis': TechnicalAnalysisValidator()
} 