"""
Quality Validation Framework for Patent Automation
Provides comprehensive validation for semantic tasks, mixed media outputs, and cascade failure prevention
"""

import os
import json
import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import hashlib
from datetime import datetime
import traceback

# Import validation libraries
try:
    import nbformat
    from nbformat.validator import ValidationError as NBValidationError
    NBFORMAT_AVAILABLE = True
except ImportError:
    NBFORMAT_AVAILABLE = False

try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import markdown
    from bs4 import BeautifulSoup
    MD_VALIDATION_AVAILABLE = True
except ImportError:
    MD_VALIDATION_AVAILABLE = False

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation severity levels"""
    CRITICAL = "critical"  # Must fix - prevents downstream processing
    WARNING = "warning"   # Should fix - may impact quality
    INFO = "info"        # Nice to fix - cosmetic improvements

class ValidationResult(Enum):
    """Validation result status"""
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"  # Some validations passed, some failed

@dataclass
class ValidationIssue:
    """Represents a single validation issue"""
    level: ValidationLevel
    message: str
    file_path: str
    issue_type: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    
    def __str__(self) -> str:
        location = f":{self.line_number}" if self.line_number else ""
        return f"[{self.level.value.upper()}] {self.file_path}{location}: {self.message}"

@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    file_path: str
    file_type: str
    result: ValidationResult
    issues: List[ValidationIssue]
    metadata: Dict[str, Any]
    validation_time: datetime
    file_size: int
    checksum: str
    
    @property
    def critical_issues(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == ValidationLevel.CRITICAL]
    
    @property
    def warning_issues(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == ValidationLevel.WARNING]
    
    @property
    def info_issues(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == ValidationLevel.INFO]
    
    @property
    def is_valid(self) -> bool:
        """Check if file passes validation (no critical issues)"""
        return len(self.critical_issues) == 0
    
    @property
    def quality_score(self) -> float:
        """Calculate quality score based on issues (0-100)"""
        if not self.issues:
            return 100.0
        
        total_penalty = 0
        for issue in self.issues:
            if issue.level == ValidationLevel.CRITICAL:
                total_penalty += 50
            elif issue.level == ValidationLevel.WARNING:
                total_penalty += 10
            elif issue.level == ValidationLevel.INFO:
                total_penalty += 2
        
        return max(0, 100 - total_penalty)

class BaseValidator:
    """Base class for file validators"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        
    def validate(self, file_path: str) -> ValidationReport:
        """Main validation method - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement validate method")
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Could not calculate checksum for {file_path}: {e}")
            return "unknown"
    
    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception as e:
            logger.warning(f"Could not get file size for {file_path}: {e}")
            return 0

class MarkdownValidator(BaseValidator):
    """Validator for Markdown files (.md)"""
    
    def __init__(self):
        super().__init__()
        self.required_sections = {
            'patent_application': [
                'title', 'background', 'summary', 'detailed description', 
                'claims', 'abstract'
            ],
            'prior_art_analysis': [
                'search methodology', 'findings', 'novelty assessment', 
                'recommendations'
            ],
            'legal_review': [
                'compliance assessment', 'claim analysis', 'risk evaluation',
                'recommendations'
            ],
            'valuation_report': [
                'executive summary', 'technical assessment', 'market analysis',
                'valuation methodology', 'conclusion'
            ]
        }
    
    def validate(self, file_path: str) -> ValidationReport:
        """Validate Markdown file"""
        issues = []
        metadata = {}
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic content validation
            issues.extend(self._validate_basic_content(file_path, content))
            
            # Structure validation
            issues.extend(self._validate_structure(file_path, content))
            
            # Semantic validation
            issues.extend(self._validate_semantic_content(file_path, content))
            
            # Patent-specific validation
            issues.extend(self._validate_patent_specific(file_path, content))
            
            # Metadata extraction
            metadata = self._extract_metadata(content)
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Failed to read file: {str(e)}",
                file_path=file_path,
                issue_type="file_access"
            ))
        
        # Determine overall result
        result = ValidationResult.FAIL if any(issue.level == ValidationLevel.CRITICAL for issue in issues) else \
                ValidationResult.PARTIAL if any(issue.level == ValidationLevel.WARNING for issue in issues) else \
                ValidationResult.PASS
        
        return ValidationReport(
            file_path=file_path,
            file_type="markdown",
            result=result,
            issues=issues,
            metadata=metadata,
            validation_time=datetime.now(),
            file_size=self._get_file_size(file_path),
            checksum=self._calculate_checksum(file_path)
        )
    
    def _validate_basic_content(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate basic content requirements"""
        issues = []
        
        # Check minimum length
        if len(content.strip()) < 100:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message="Content too short (< 100 characters)",
                file_path=file_path,
                issue_type="content_length",
                suggestion="Ensure document contains substantive content"
            ))
        
        # Check for placeholder text
        placeholder_patterns = [
            r'\[.*TODO.*\]', r'\[.*PLACEHOLDER.*\]', r'\[.*TBD.*\]',
            r'lorem ipsum', r'CHANGE.*THIS', r'REPLACE.*WITH'
        ]
        
        for pattern in placeholder_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Found placeholder text: {match.group()}",
                    file_path=file_path,
                    issue_type="placeholder_text",
                    line_number=line_num,
                    suggestion="Replace placeholder with actual content"
                ))
        
        # Check for empty sections
        if '##' in content:
            sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
            for i, section in enumerate(sections[1:], 1):  # Skip first split part
                section_content = section.split('\n', 1)[1] if '\n' in section else ""
                if len(section_content.strip()) < 50:
                    section_title = section.split('\n')[0].strip()
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Section '{section_title}' appears to be empty or too short",
                        file_path=file_path,
                        issue_type="empty_section",
                        suggestion="Add substantive content to this section"
                    ))
        
        return issues
    
    def _validate_structure(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate document structure"""
        issues = []
        
        # Check for title (# or title: in YAML front matter)
        if not re.search(r'^#\s+', content, re.MULTILINE) and not re.search(r'^title:', content, re.MULTILINE):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Document missing title",
                file_path=file_path,
                issue_type="missing_title",
                suggestion="Add a title using # Title or YAML front matter"
            ))
        
        # Check for proper heading hierarchy
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        if headings:
            prev_level = 0
            for i, (hashes, title) in enumerate(headings):
                current_level = len(hashes)
                if current_level > prev_level + 1:
                    line_num = self._find_line_number(content, f"{hashes} {title}")
                    issues.append(ValidationIssue(
                        level=ValidationLevel.INFO,
                        message=f"Heading level skip: {title} (h{current_level} after h{prev_level})",
                        file_path=file_path,
                        issue_type="heading_hierarchy",
                        line_number=line_num,
                        suggestion="Use proper heading hierarchy (h1 -> h2 -> h3, etc.)"
                    ))
                prev_level = current_level
        
        return issues
    
    def _validate_semantic_content(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate semantic content quality"""
        issues = []
        
        # Check for patent-related content quality
        file_name = os.path.basename(file_path).lower()
        
        if 'patent' in file_name:
            # Check for essential patent elements
            patent_elements = {
                'technical field': r'(technical\s+field|field\s+of\s+(the\s+)?invention)',
                'background': r'background',
                'summary': r'(summary|brief\s+description)',
                'claims': r'claims?',
                'detailed description': r'detailed\s+description'
            }
            
            for element, pattern in patent_elements.items():
                if not re.search(pattern, content, re.IGNORECASE):
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Missing essential patent element: {element}",
                        file_path=file_path,
                        issue_type="missing_patent_element",
                        suggestion=f"Add {element} section to patent document"
                    ))
        
        # Check for technical depth
        technical_indicators = [
            'algorithm', 'method', 'system', 'process', 'implementation',
            'architecture', 'protocol', 'interface', 'optimization'
        ]
        
        technical_count = sum(len(re.findall(indicator, content, re.IGNORECASE)) 
                            for indicator in technical_indicators)
        
        if technical_count < 5:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Document may lack technical depth",
                file_path=file_path,
                issue_type="technical_depth",
                suggestion="Consider adding more technical details and explanations"
            ))
        
        return issues
    
    def _validate_patent_specific(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate patent-specific requirements"""
        issues = []
        
        file_name = os.path.basename(file_path).lower()
        
        # Patent application specific validation
        if 'patent_application' in file_name:
            # Check for claims structure
            if 'claims' in content.lower():
                # Look for numbered claims
                claim_pattern = r'^\s*(\d+)\.\s+(.+)$'
                claims = re.findall(claim_pattern, content, re.MULTILINE)
                
                if not claims:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.CRITICAL,
                        message="No properly formatted claims found",
                        file_path=file_path,
                        issue_type="missing_claims",
                        suggestion="Format claims as numbered list (1. First claim, 2. Second claim, etc.)"
                    ))
                elif len(claims) < 1:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message="Very few claims found - consider adding more dependent claims",
                        file_path=file_path,
                        issue_type="insufficient_claims",
                        suggestion="Add dependent claims to strengthen patent protection"
                    ))
        
        # Legal review specific validation
        elif 'legal_review' in file_name:
            required_elements = ['compliance', 'risk', 'recommendation']
            for element in required_elements:
                if element not in content.lower():
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Legal review missing {element} analysis",
                        file_path=file_path,
                        issue_type="missing_legal_element",
                        suggestion=f"Add {element} section to legal review"
                    ))
        
        # Valuation report specific validation
        elif 'valuation' in file_name:
            if not re.search(r'\$[\d,]+[KMB]?', content):
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message="No monetary values found in valuation report",
                    file_path=file_path,
                    issue_type="missing_valuation",
                    suggestion="Include specific valuation amounts in the report"
                ))
        
        return issues
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from content"""
        metadata = {
            'word_count': len(content.split()),
            'line_count': len(content.splitlines()),
            'heading_count': len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE)),
            'has_yaml_frontmatter': content.startswith('---'),
            'sections': []
        }
        
        # Extract section titles
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        metadata['sections'] = [title.strip() for _, title in headings]
        
        return metadata
    
    def _find_line_number(self, content: str, search_text: str) -> int:
        """Find line number of text in content"""
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if search_text in line:
                return i
        return 0

class ImageValidator(BaseValidator):
    """Validator for image files (.png, .jpg, .jpeg, .svg)"""
    
    def validate(self, file_path: str) -> ValidationReport:
        """Validate image file"""
        issues = []
        metadata = {}
        
        try:
            # Check if file exists and is readable
            if not os.path.exists(file_path):
                issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    message="Image file does not exist",
                    file_path=file_path,
                    issue_type="file_not_found"
                ))
                return self._create_failed_report(file_path, "image", issues)
            
            file_size = os.path.getsize(file_path)
            
            # Check file size
            if file_size < 100:  # Very small file, likely corrupted
                issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    message=f"Image file too small ({file_size} bytes) - likely corrupted",
                    file_path=file_path,
                    issue_type="corrupted_image",
                    suggestion="Regenerate the image file"
                ))
            elif file_size > 10 * 1024 * 1024:  # > 10MB
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message=f"Image file very large ({file_size/1024/1024:.1f}MB)",
                    file_path=file_path,
                    issue_type="large_image",
                    suggestion="Consider compressing the image"
                ))
            
            # Check if it's actually an image (not text)
            if self._is_text_file(file_path):
                issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    message="Image file contains text instead of binary image data",
                    file_path=file_path,
                    issue_type="text_instead_of_image",
                    suggestion="Check GraphViz rendering - file may contain DOT source instead of PNG"
                ))
            
            # Validate with PIL if available
            if PIL_AVAILABLE:
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                        metadata.update({
                            'width': width,
                            'height': height,
                            'format': img.format,
                            'mode': img.mode
                        })
                        
                        # Check dimensions
                        if width < 100 or height < 100:
                            issues.append(ValidationIssue(
                                level=ValidationLevel.WARNING,
                                message=f"Image dimensions very small ({width}x{height})",
                                file_path=file_path,
                                issue_type="small_dimensions",
                                suggestion="Increase image size for better readability"
                            ))
                        elif width > 4000 or height > 4000:
                            issues.append(ValidationIssue(
                                level=ValidationLevel.INFO,
                                message=f"Image dimensions very large ({width}x{height})",
                                file_path=file_path,
                                issue_type="large_dimensions",
                                suggestion="Consider reducing image size for web compatibility"
                            ))
                        
                        # Check aspect ratio
                        aspect_ratio = width / height
                        if aspect_ratio > 5 or aspect_ratio < 0.2:
                            issues.append(ValidationIssue(
                                level=ValidationLevel.INFO,
                                message=f"Unusual aspect ratio ({aspect_ratio:.2f})",
                                file_path=file_path,
                                issue_type="aspect_ratio",
                                suggestion="Consider adjusting image proportions"
                            ))
                        
                except Exception as e:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.CRITICAL,
                        message=f"Cannot open image with PIL: {str(e)}",
                        file_path=file_path,
                        issue_type="invalid_image_format"
                    ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Validation error: {str(e)}",
                file_path=file_path,
                issue_type="validation_error"
            ))
        
        # Determine result
        result = ValidationResult.FAIL if any(issue.level == ValidationLevel.CRITICAL for issue in issues) else \
                ValidationResult.PARTIAL if any(issue.level == ValidationLevel.WARNING for issue in issues) else \
                ValidationResult.PASS
        
        return ValidationReport(
            file_path=file_path,
            file_type="image",
            result=result,
            issues=issues,
            metadata=metadata,
            validation_time=datetime.now(),
            file_size=self._get_file_size(file_path),
            checksum=self._calculate_checksum(file_path)
        )
    
    def _is_text_file(self, file_path: str) -> bool:
        """Check if file contains text instead of binary image data"""
        try:
            with open(file_path, 'rb') as f:
                # Read first 1024 bytes
                sample = f.read(1024)
                
            # Check if it looks like text (high ratio of printable characters)
            try:
                decoded = sample.decode('utf-8')
                printable_count = sum(1 for c in decoded if c.isprintable() or c.isspace())
                text_ratio = printable_count / len(decoded) if decoded else 0
                return text_ratio > 0.8  # 80% printable characters suggests text
            except UnicodeDecodeError:
                return False  # Binary data, likely a real image
                
        except Exception:
            return False
    
    def _create_failed_report(self, file_path: str, file_type: str, issues: List[ValidationIssue]) -> ValidationReport:
        """Create a failed validation report"""
        return ValidationReport(
            file_path=file_path,
            file_type=file_type,
            result=ValidationResult.FAIL,
            issues=issues,
            metadata={},
            validation_time=datetime.now(),
            file_size=0,
            checksum="unknown"
        )

class NotebookValidator(BaseValidator):
    """Validator for Jupyter notebooks (.ipynb)"""
    
    def validate(self, file_path: str) -> ValidationReport:
        """Validate Jupyter notebook"""
        issues = []
        metadata = {}
        
        try:
            # Read and parse notebook
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook_data = json.load(f)
            
            # Validate with nbformat if available
            if NBFORMAT_AVAILABLE:
                try:
                    nb = nbformat.from_dict(notebook_data)
                    nbformat.validate(nb)
                except NBValidationError as e:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.CRITICAL,
                        message=f"Notebook format validation failed: {str(e)}",
                        file_path=file_path,
                        issue_type="invalid_notebook_format"
                    ))
                except Exception as e:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Notebook validation warning: {str(e)}",
                        file_path=file_path,
                        issue_type="notebook_validation_warning"
                    ))
            
            # Validate notebook structure
            issues.extend(self._validate_notebook_structure(file_path, notebook_data))
            
            # Validate notebook content
            issues.extend(self._validate_notebook_content(file_path, notebook_data))
            
            # Extract metadata
            metadata = self._extract_notebook_metadata(notebook_data)
            
        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Invalid JSON format: {str(e)}",
                file_path=file_path,
                issue_type="invalid_json"
            ))
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Failed to read notebook: {str(e)}",
                file_path=file_path,
                issue_type="read_error"
            ))
        
        # Determine result
        result = ValidationResult.FAIL if any(issue.level == ValidationLevel.CRITICAL for issue in issues) else \
                ValidationResult.PARTIAL if any(issue.level == ValidationLevel.WARNING for issue in issues) else \
                ValidationResult.PASS
        
        return ValidationReport(
            file_path=file_path,
            file_type="notebook",
            result=result,
            issues=issues,
            metadata=metadata,
            validation_time=datetime.now(),
            file_size=self._get_file_size(file_path),
            checksum=self._calculate_checksum(file_path)
        )
    
    def _validate_notebook_structure(self, file_path: str, notebook_data: Dict) -> List[ValidationIssue]:
        """Validate notebook structure"""
        issues = []
        
        # Check required fields
        required_fields = ['cells', 'metadata', 'nbformat']
        for field in required_fields:
            if field not in notebook_data:
                issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    message=f"Missing required field: {field}",
                    file_path=file_path,
                    issue_type="missing_required_field"
                ))
        
        # Check cells exist and are valid
        cells = notebook_data.get('cells', [])
        if not cells:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Notebook has no cells",
                file_path=file_path,
                issue_type="empty_notebook",
                suggestion="Add content cells to the notebook"
            ))
        
        # Validate individual cells
        for i, cell in enumerate(cells):
            if not isinstance(cell, dict):
                issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    message=f"Cell {i} is not a valid dictionary",
                    file_path=file_path,
                    issue_type="invalid_cell_structure"
                ))
                continue
            
            # Check required cell fields
            required_cell_fields = ['cell_type', 'source']
            for field in required_cell_fields:
                if field not in cell:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Cell {i} missing field: {field}",
                        file_path=file_path,
                        issue_type="missing_cell_field"
                    ))
        
        return issues
    
    def _validate_notebook_content(self, file_path: str, notebook_data: Dict) -> List[ValidationIssue]:
        """Validate notebook content quality"""
        issues = []
        
        cells = notebook_data.get('cells', [])
        code_cells = [cell for cell in cells if cell.get('cell_type') == 'code']
        markdown_cells = [cell for cell in cells if cell.get('cell_type') == 'markdown']
        
        # Check for documentation
        if not markdown_cells:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Notebook has no markdown cells (documentation)",
                file_path=file_path,
                issue_type="no_documentation",
                suggestion="Add markdown cells to document the notebook"
            ))
        
        # Check for executable code
        if not code_cells:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Notebook has no code cells",
                file_path=file_path,
                issue_type="no_code",
                suggestion="Add code cells to demonstrate functionality"
            ))
        
        # Check code cell content
        empty_code_cells = 0
        for i, cell in enumerate(code_cells):
            source = cell.get('source', [])
            if isinstance(source, list):
                source_text = ''.join(source)
            else:
                source_text = str(source)
            
            if not source_text.strip():
                empty_code_cells += 1
            elif source_text.strip().startswith('#') and len(source_text.strip().split('\n')) == 1:
                # Only a comment
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    message=f"Code cell {i} contains only comments",
                    file_path=file_path,
                    issue_type="comment_only_cell",
                    suggestion="Add executable code to demonstrate functionality"
                ))
        
        if empty_code_cells > 0:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"{empty_code_cells} empty code cells found",
                file_path=file_path,
                issue_type="empty_code_cells",
                suggestion="Remove empty cells or add content"
            ))
        
        # Check for patent-specific content
        all_text = self._extract_all_text(cells)
        
        patent_keywords = ['patent', 'claim', 'invention', 'demonstration', 'enablement']
        patent_keyword_count = sum(1 for keyword in patent_keywords if keyword.lower() in all_text.lower())
        
        if patent_keyword_count < 2:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Notebook may lack patent-specific context",
                file_path=file_path,
                issue_type="missing_patent_context",
                suggestion="Add patent claim demonstrations and explanations"
            ))
        
        return issues
    
    def _extract_notebook_metadata(self, notebook_data: Dict) -> Dict[str, Any]:
        """Extract metadata from notebook"""
        cells = notebook_data.get('cells', [])
        
        metadata = {
            'total_cells': len(cells),
            'code_cells': len([c for c in cells if c.get('cell_type') == 'code']),
            'markdown_cells': len([c for c in cells if c.get('cell_type') == 'markdown']),
            'raw_cells': len([c for c in cells if c.get('cell_type') == 'raw']),
            'nbformat_version': notebook_data.get('nbformat'),
            'kernel_info': notebook_data.get('metadata', {}).get('kernelspec', {}),
            'colab_info': notebook_data.get('metadata', {}).get('colab', {})
        }
        
        # Extract total lines of code
        code_lines = 0
        for cell in cells:
            if cell.get('cell_type') == 'code':
                source = cell.get('source', [])
                if isinstance(source, list):
                    code_lines += len(source)
                else:
                    code_lines += len(str(source).splitlines())
        
        metadata['total_code_lines'] = code_lines
        
        return metadata
    
    def _extract_all_text(self, cells: List[Dict]) -> str:
        """Extract all text content from notebook cells"""
        all_text = []
        
        for cell in cells:
            source = cell.get('source', [])
            if isinstance(source, list):
                all_text.extend(source)
            else:
                all_text.append(str(source))
        
        return '\n'.join(all_text)

class QualityValidationManager:
    """Main quality validation manager"""
    
    def __init__(self):
        self.validators = {
            '.md': MarkdownValidator(),
            '.markdown': MarkdownValidator(),
            '.png': ImageValidator(),
            '.jpg': ImageValidator(),
            '.jpeg': ImageValidator(),
            '.svg': ImageValidator(),
            '.ipynb': NotebookValidator()
        }
        self.validation_history: List[ValidationReport] = []
        
    def validate_file(self, file_path: str) -> ValidationReport:
        """Validate a single file"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in self.validators:
            # Create basic validation for unknown file types
            return self._validate_unknown_file(file_path)
        
        validator = self.validators[file_ext]
        
        try:
            report = validator.validate(file_path)
            self.validation_history.append(report)
            return report
        except Exception as e:
            logger.error(f"Validation failed for {file_path}: {e}")
            traceback.print_exc()
            
            # Create error report
            error_report = ValidationReport(
                file_path=file_path,
                file_type=file_ext[1:],  # Remove the dot
                result=ValidationResult.FAIL,
                issues=[ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    message=f"Validation system error: {str(e)}",
                    file_path=file_path,
                    issue_type="system_error"
                )],
                metadata={},
                validation_time=datetime.now(),
                file_size=0,
                checksum="unknown"
            )
            
            self.validation_history.append(error_report)
            return error_report
    
    def validate_directory(self, directory_path: str, recursive: bool = True) -> List[ValidationReport]:
        """Validate all supported files in a directory"""
        reports = []
        
        pattern = "**/*" if recursive else "*"
        
        for file_path in Path(directory_path).glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.validators:
                report = self.validate_file(str(file_path))
                reports.append(report)
        
        return reports
    
    def validate_patent_workflow_outputs(self, tier: str, patent_id: str) -> Dict[str, ValidationReport]:
        """Validate all outputs for a specific patent workflow"""
        output_dir = Path(f"output/{tier}")
        reports = {}
        
        # Expected output files for a patent workflow
        expected_files = [
            f"{patent_id}_prior_art_analysis.md",
            f"{patent_id}_refined_claims.md", 
            f"{patent_id}_patent_application.md",
            f"{patent_id}_architecture_diagrams.md",
            f"{patent_id}_legal_review.md",
            f"{patent_id}_associate_editor_review.md",
            f"{patent_id}_editorial_review.md",
            f"{patent_id}_patent_application_final.md",
            f"{patent_id}_colab_demo_concept_review.md",
            f"{patent_id}_colab_demo_log.md",
            f"{patent_id}_colab_demo_editorial_review.md",
            f"{patent_id}_colab_demo_integration_log.md",
            f"{patent_id}_cover_sheet.md",
            f"{patent_id}_valuation_report.md",
            f"{patent_id}_colab_demo.ipynb",
            f"{patent_id}_colab_demo_final.ipynb"
        ]
        
        # Also check for architecture diagram images
        expected_files.extend([
            "system_architecture_programmatic.png",
            "component_interaction_programmatic.png", 
            "data_flow_programmatic.png",
            "agent_coordination_programmatic.png",
            "technical_features_programmatic.png",
            "performance_optimization_programmatic.png",
            "prior_art_differentiation_programmatic.png"
        ])
        
        for file_name in expected_files:
            file_path = output_dir / file_name
            
            if file_path.exists():
                report = self.validate_file(str(file_path))
                reports[file_name] = report
            else:
                # Create report for missing file
                reports[file_name] = ValidationReport(
                    file_path=str(file_path),
                    file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
                    result=ValidationResult.FAIL,
                    issues=[ValidationIssue(
                        level=ValidationLevel.CRITICAL,
                        message="Expected output file is missing",
                        file_path=str(file_path),
                        issue_type="missing_file",
                        suggestion="Check if the corresponding task completed successfully"
                    )],
                    metadata={},
                    validation_time=datetime.now(),
                    file_size=0,
                    checksum="missing"
                )
        
        return reports
    
    def _validate_unknown_file(self, file_path: str) -> ValidationReport:
        """Basic validation for unknown file types"""
        issues = []
        
        if not os.path.exists(file_path):
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message="File does not exist",
                file_path=file_path,
                issue_type="file_not_found"
            ))
        else:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    message="File is empty",
                    file_path=file_path,
                    issue_type="empty_file"
                ))
        
        result = ValidationResult.FAIL if any(issue.level == ValidationLevel.CRITICAL for issue in issues) else \
                ValidationResult.PARTIAL if any(issue.level == ValidationLevel.WARNING for issue in issues) else \
                ValidationResult.PASS
        
        file_ext = Path(file_path).suffix
        
        return ValidationReport(
            file_path=file_path,
            file_type=file_ext[1:] if file_ext else "unknown",
            result=result,
            issues=issues,
            metadata={'file_type': 'unsupported'},
            validation_time=datetime.now(),
            file_size=self._get_file_size(file_path) if os.path.exists(file_path) else 0,
            checksum=self._calculate_checksum(file_path) if os.path.exists(file_path) else "missing"
        )
    
    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return "unknown"
    
    def generate_summary_report(self, reports: List[ValidationReport]) -> Dict[str, Any]:
        """Generate summary report from multiple validation reports"""
        if not reports:
            return {
                'total_files': 0,
                'validation_summary': {},
                'quality_summary': {},
                'issue_summary': {}
            }
        
        total_files = len(reports)
        passed = len([r for r in reports if r.result == ValidationResult.PASS])
        partial = len([r for r in reports if r.result == ValidationResult.PARTIAL])
        failed = len([r for r in reports if r.result == ValidationResult.FAIL])
        
        # Count issues by type and level
        all_issues = []
        for report in reports:
            all_issues.extend(report.issues)
        
        critical_issues = [i for i in all_issues if i.level == ValidationLevel.CRITICAL]
        warning_issues = [i for i in all_issues if i.level == ValidationLevel.WARNING]
        info_issues = [i for i in all_issues if i.level == ValidationLevel.INFO]
        
        # Calculate average quality score
        quality_scores = [r.quality_score for r in reports]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Group by file type
        file_types = {}
        for report in reports:
            ft = report.file_type
            if ft not in file_types:
                file_types[ft] = {'total': 0, 'passed': 0, 'failed': 0, 'issues': 0}
            file_types[ft]['total'] += 1
            if report.result == ValidationResult.PASS:
                file_types[ft]['passed'] += 1
            elif report.result == ValidationResult.FAIL:
                file_types[ft]['failed'] += 1
            file_types[ft]['issues'] += len(report.issues)
        
        return {
            'total_files': total_files,
            'validation_summary': {
                'passed': passed,
                'partial': partial, 
                'failed': failed,
                'pass_rate': (passed / total_files * 100) if total_files > 0 else 0
            },
            'quality_summary': {
                'average_quality_score': avg_quality,
                'files_above_90': len([r for r in reports if r.quality_score >= 90]),
                'files_below_50': len([r for r in reports if r.quality_score < 50])
            },
            'issue_summary': {
                'total_issues': len(all_issues),
                'critical': len(critical_issues),
                'warning': len(warning_issues),
                'info': len(info_issues)
            },
            'file_type_summary': file_types,
            'critical_failures': [r.file_path for r in reports if len(r.critical_issues) > 0]
        }

# Global instance
quality_validator = QualityValidationManager() 