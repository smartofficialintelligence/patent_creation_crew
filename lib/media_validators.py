"""
Media Validators for Patent Automation
Provides specialized validation for mixed media content including diagrams, notebooks, and other media files
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import hashlib

from .quality_validation import ValidationIssue, ValidationLevel, ValidationReport, BaseValidator, ValidationResult

# Import optional dependencies
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import nbformat
    from nbformat.validator import ValidationError as NBValidationError
    NBFORMAT_AVAILABLE = True
except ImportError:
    NBFORMAT_AVAILABLE = False

logger = logging.getLogger(__name__)

class ArchitectureDiagramValidator(BaseValidator):
    """Specialized validator for architecture diagrams"""
    
    def __init__(self):
        super().__init__()
        self.expected_diagram_types = [
            'system_architecture', 'component_interaction', 'data_flow',
            'agent_coordination', 'technical_features', 'performance_optimization',
            'prior_art_differentiation'
        ]
        
        self.min_dimensions = {
            'width': 400,
            'height': 300
        }
        
        self.max_dimensions = {
            'width': 4000,
            'height': 3000
        }
        
        self.preferred_formats = ['PNG', 'SVG', 'PDF']
        
    def validate(self, file_path: str) -> ValidationReport:
        """Validate architecture diagram"""
        issues = []
        metadata = {}
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    message="Architecture diagram file does not exist",
                    file_path=file_path,
                    issue_type="file_not_found",
                    suggestion="Check if diagram generation completed successfully"
                ))
                return self._create_failed_report(file_path, issues)
            
            # Basic file validation
            issues.extend(self._validate_file_properties(file_path))
            
            # Image-specific validation
            if PIL_AVAILABLE and file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                issues.extend(self._validate_image_properties(file_path))
                metadata.update(self._extract_image_metadata(file_path))
            
            # Patent-specific diagram validation
            issues.extend(self._validate_diagram_context(file_path))
            
            # Content validation (check for text instead of image)
            issues.extend(self._validate_diagram_content(file_path))
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Diagram validation error: {str(e)}",
                file_path=file_path,
                issue_type="validation_error"
            ))
        
        # Determine result
        result = self._determine_result(issues)
        
        return ValidationReport(
            file_path=file_path,
            file_type="architecture_diagram",
            result=result,
            issues=issues,
            metadata=metadata,
            validation_time=datetime.now(),
            file_size=self._get_file_size(file_path),
            checksum=self._calculate_checksum(file_path)
        )
    
    def _validate_file_properties(self, file_path: str) -> List[ValidationIssue]:
        """Validate basic file properties"""
        issues = []
        
        file_size = os.path.getsize(file_path)
        
        # Check file size
        if file_size < 1000:  # Less than 1KB
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Diagram file very small ({file_size} bytes) - likely corrupted or empty",
                file_path=file_path,
                issue_type="small_file",
                suggestion="Regenerate the diagram file"
            ))
        elif file_size > 10 * 1024 * 1024:  # Greater than 10MB
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Diagram file very large ({file_size/1024/1024:.1f}MB)",
                file_path=file_path,
                issue_type="large_file",
                suggestion="Consider optimizing or compressing the diagram"
            ))
        
        # Check file format
        file_ext = Path(file_path).suffix.upper()
        if file_ext[1:] not in self.preferred_formats:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message=f"Diagram format {file_ext} not in preferred formats {self.preferred_formats}",
                file_path=file_path,
                issue_type="format_preference",
                suggestion="Consider using PNG or SVG format for better compatibility"
            ))
        
        return issues
    
    def _validate_image_properties(self, file_path: str) -> List[ValidationIssue]:
        """Validate image-specific properties"""
        issues = []
        
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                
                # Check dimensions
                if width < self.min_dimensions['width'] or height < self.min_dimensions['height']:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Diagram dimensions ({width}x{height}) below minimum ({self.min_dimensions['width']}x{self.min_dimensions['height']})",
                        file_path=file_path,
                        issue_type="small_dimensions",
                        suggestion="Increase diagram size for better readability"
                    ))
                
                if width > self.max_dimensions['width'] or height > self.max_dimensions['height']:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.INFO,
                        message=f"Diagram dimensions ({width}x{height}) above maximum ({self.max_dimensions['width']}x{self.max_dimensions['height']})",
                        file_path=file_path,
                        issue_type="large_dimensions",
                        suggestion="Consider reducing diagram size for better performance"
                    ))
                
                # Check aspect ratio
                aspect_ratio = width / height
                if aspect_ratio > 4 or aspect_ratio < 0.25:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.INFO,
                        message=f"Unusual aspect ratio ({aspect_ratio:.2f})",
                        file_path=file_path,
                        issue_type="unusual_aspect_ratio",
                        suggestion="Consider adjusting diagram proportions"
                    ))
                
                # Check color mode
                if img.mode not in ['RGB', 'RGBA', 'L']:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        message=f"Unusual color mode: {img.mode}",
                        file_path=file_path,
                        issue_type="unusual_color_mode",
                        suggestion="Consider using RGB or RGBA color mode"
                    ))
                
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Cannot read image file: {str(e)}",
                file_path=file_path,
                issue_type="image_read_error",
                suggestion="Check if file is a valid image format"
            ))
        
        return issues
    
    def _validate_diagram_context(self, file_path: str) -> List[ValidationIssue]:
        """Validate diagram context and naming"""
        issues = []
        
        filename = Path(file_path).stem.lower()
        
        # Check if filename matches expected diagram types
        diagram_type_found = False
        for diagram_type in self.expected_diagram_types:
            if diagram_type in filename:
                diagram_type_found = True
                break
        
        if not diagram_type_found:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message=f"Diagram type not clear from filename: {filename}",
                file_path=file_path,
                issue_type="unclear_diagram_type",
                suggestion=f"Include diagram type in filename: {', '.join(self.expected_diagram_types)}"
            ))
        
        # Check for programmatic suffix (indicates generated diagram)
        if 'programmatic' not in filename:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Diagram may not be programmatically generated",
                file_path=file_path,
                issue_type="manual_diagram",
                suggestion="Consider using programmatically generated diagrams for consistency"
            ))
        
        return issues
    
    def _validate_diagram_content(self, file_path: str) -> List[ValidationIssue]:
        """Validate diagram content (check for text instead of image)"""
        issues = []
        
        try:
            # Check if file contains text (DOT source) instead of binary image
            with open(file_path, 'rb') as f:
                sample = f.read(1024)
            
            # Check if it looks like text
            try:
                decoded = sample.decode('utf-8')
                # Check for GraphViz DOT syntax
                if any(keyword in decoded.lower() for keyword in ['digraph', 'graph', 'node', 'edge', 'rankdir']):
                    issues.append(ValidationIssue(
                        level=ValidationLevel.CRITICAL,
                        message="Diagram file contains GraphViz DOT source instead of rendered image",
                        file_path=file_path,
                        issue_type="dot_source_instead_of_image",
                        suggestion="Ensure GraphViz renders to PNG/SVG format, not DOT source"
                    ))
                elif decoded.strip().startswith('<?xml') or '<svg' in decoded:
                    # SVG file - this is valid
                    pass
                else:
                    # Check for high ratio of printable characters (suggests text)
                    printable_count = sum(1 for c in decoded if c.isprintable() or c.isspace())
                    text_ratio = printable_count / len(decoded) if decoded else 0
                    if text_ratio > 0.8:
                        issues.append(ValidationIssue(
                            level=ValidationLevel.WARNING,
                            message="Diagram file appears to contain text instead of image data",
                            file_path=file_path,
                            issue_type="text_instead_of_image",
                            suggestion="Check diagram generation process"
                        ))
            except UnicodeDecodeError:
                # Binary data - likely a valid image
                pass
        
        except Exception as e:
            logger.warning(f"Could not validate diagram content for {file_path}: {e}")
        
        return issues
    
    def _extract_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract image metadata"""
        metadata = {}
        
        if PIL_AVAILABLE:
            try:
                with Image.open(file_path) as img:
                    metadata.update({
                        'width': img.width,
                        'height': img.height,
                        'format': img.format,
                        'mode': img.mode,
                        'aspect_ratio': img.width / img.height if img.height > 0 else 0
                    })
                    
                    # Extract EXIF data if available
                    if hasattr(img, '_getexif') and img._getexif():
                        metadata['has_exif'] = True
                    
            except Exception as e:
                logger.warning(f"Could not extract image metadata from {file_path}: {e}")
        
        return metadata
    
    def _create_failed_report(self, file_path: str, issues: List[ValidationIssue]) -> ValidationReport:
        """Create a failed validation report"""
        return ValidationReport(
            file_path=file_path,
            file_type="architecture_diagram",
            result=ValidationResult.FAIL,
            issues=issues,
            metadata={},
            validation_time=datetime.now(),
            file_size=0,
            checksum="unknown"
        )
    
    def _determine_result(self, issues: List[ValidationIssue]) -> ValidationResult:
        """Determine validation result based on issues"""
        if any(issue.level == ValidationLevel.CRITICAL for issue in issues):
            return ValidationResult.FAIL
        elif any(issue.level == ValidationLevel.WARNING for issue in issues):
            return ValidationResult.PARTIAL
        else:
            return ValidationResult.PASS

class PatentNotebookValidator(BaseValidator):
    """Specialized validator for patent demonstration notebooks"""
    
    def __init__(self):
        super().__init__()
        self.required_sections = [
            'Patent Description',
            'Key Claims', 
            'Demonstrated Claim',
            'Implementation',
            'Performance Results'
        ]
        
        self.patent_keywords = [
            'patent', 'claim', 'invention', 'demonstration', 'enablement',
            'prior art', 'novelty', 'technical', 'implementation'
        ]
        
        self.code_quality_indicators = [
            'import', 'def ', 'class ', 'try:', 'except:', 'if __name__',
            'print(', 'assert', 'test'
        ]
        
    def validate(self, file_path: str) -> ValidationReport:
        """Validate patent demonstration notebook"""
        issues = []
        metadata = {}
        
        try:
            # Read notebook
            with open(file_path, 'r', encoding='utf-8') as f:
                notebook_data = json.load(f)
            
            # Basic notebook validation
            if NBFORMAT_AVAILABLE:
                issues.extend(self._validate_notebook_format(file_path, notebook_data))
            
            # Patent-specific validation
            issues.extend(self._validate_patent_content(file_path, notebook_data))
            issues.extend(self._validate_demonstration_quality(file_path, notebook_data))
            issues.extend(self._validate_code_quality(file_path, notebook_data))
            
            # Extract metadata
            metadata = self._extract_notebook_metadata(notebook_data)
            
        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Invalid JSON format in notebook: {str(e)}",
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
        result = self._determine_result(issues)
        
        return ValidationReport(
            file_path=file_path,
            file_type="patent_notebook",
            result=result,
            issues=issues,
            metadata=metadata,
            validation_time=datetime.now(),
            file_size=self._get_file_size(file_path),
            checksum=self._calculate_checksum(file_path)
        )
    
    def _validate_notebook_format(self, file_path: str, notebook_data: Dict) -> List[ValidationIssue]:
        """Validate notebook format"""
        issues = []
        
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
        
        return issues
    
    def _validate_patent_content(self, file_path: str, notebook_data: Dict) -> List[ValidationIssue]:
        """Validate patent-specific content"""
        issues = []
        
        cells = notebook_data.get('cells', [])
        all_text = self._extract_all_text(cells)
        
        # Check for required sections
        missing_sections = []
        for section in self.required_sections:
            if section.lower() not in all_text.lower():
                missing_sections.append(section)
        
        if missing_sections:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Missing recommended sections: {', '.join(missing_sections)}",
                file_path=file_path,
                issue_type="missing_sections",
                suggestion="Add missing sections to improve patent demonstration"
            ))
        
        # Check for patent keywords
        patent_keyword_count = sum(1 for keyword in self.patent_keywords 
                                  if keyword.lower() in all_text.lower())
        
        if patent_keyword_count < 5:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"Few patent-related keywords found ({patent_keyword_count})",
                file_path=file_path,
                issue_type="low_patent_context",
                suggestion="Add more patent-specific context and explanations"
            ))
        
        # Check for claim demonstration
        if 'claim' not in all_text.lower():
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message="No patent claim demonstration found",
                file_path=file_path,
                issue_type="no_claim_demonstration",
                suggestion="Add clear demonstration of patent claims"
            ))
        
        return issues
    
    def _validate_demonstration_quality(self, file_path: str, notebook_data: Dict) -> List[ValidationIssue]:
        """Validate demonstration quality"""
        issues = []
        
        cells = notebook_data.get('cells', [])
        code_cells = [cell for cell in cells if cell.get('cell_type') == 'code']
        
        if not code_cells:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message="No code cells found in demonstration notebook",
                file_path=file_path,
                issue_type="no_code_cells",
                suggestion="Add code cells to demonstrate patent implementation"
            ))
            return issues
        
        # Check for empty code cells
        empty_cells = 0
        for cell in code_cells:
            source = cell.get('source', [])
            if isinstance(source, list):
                source_text = ''.join(source)
            else:
                source_text = str(source)
            
            if not source_text.strip():
                empty_cells += 1
        
        if empty_cells > 0:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                message=f"{empty_cells} empty code cells found",
                file_path=file_path,
                issue_type="empty_code_cells",
                suggestion="Remove empty cells or add demonstration code"
            ))
        
        # Check for performance metrics
        all_text = self._extract_all_text(cells)
        performance_keywords = ['performance', 'benchmark', 'timing', 'speed', 'efficiency', 'ms', 'seconds']
        performance_count = sum(1 for keyword in performance_keywords 
                               if keyword.lower() in all_text.lower())
        
        if performance_count < 2:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="Few performance metrics found",
                file_path=file_path,
                issue_type="few_performance_metrics",
                suggestion="Add performance benchmarks to demonstrate patent advantages"
            ))
        
        return issues
    
    def _validate_code_quality(self, file_path: str, notebook_data: Dict) -> List[ValidationIssue]:
        """Validate code quality in notebook"""
        issues = []
        
        cells = notebook_data.get('cells', [])
        code_cells = [cell for cell in cells if cell.get('cell_type') == 'code']
        
        if not code_cells:
            return issues
        
        # Combine all code
        all_code = []
        for cell in code_cells:
            source = cell.get('source', [])
            if isinstance(source, list):
                all_code.extend(source)
            else:
                all_code.append(str(source))
        
        code_text = '\n'.join(all_code)
        
        # Check for code quality indicators
        quality_count = sum(1 for indicator in self.code_quality_indicators 
                           if indicator in code_text)
        
        if quality_count < 3:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message=f"Few code quality indicators found ({quality_count})",
                file_path=file_path,
                issue_type="low_code_quality",
                suggestion="Add imports, functions, error handling, and tests"
            ))
        
        # Check for error handling
        if 'try:' not in code_text and 'except:' not in code_text:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="No error handling found in code",
                file_path=file_path,
                issue_type="no_error_handling",
                suggestion="Add try-except blocks for robust demonstration"
            ))
        
        # Check for documentation
        if '"""' not in code_text and "'''" not in code_text:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                message="No docstrings found in code",
                file_path=file_path,
                issue_type="no_docstrings",
                suggestion="Add docstrings to explain patent implementation"
            ))
        
        return issues
    
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
    
    def _extract_notebook_metadata(self, notebook_data: Dict) -> Dict[str, Any]:
        """Extract notebook metadata"""
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
        
        # Count code lines
        code_lines = 0
        for cell in cells:
            if cell.get('cell_type') == 'code':
                source = cell.get('source', [])
                if isinstance(source, list):
                    code_lines += len(source)
                else:
                    code_lines += len(str(source).splitlines())
        
        metadata['total_code_lines'] = code_lines
        
        # Check for patent-specific metadata
        all_text = self._extract_all_text(cells)
        metadata['patent_keywords_count'] = sum(1 for keyword in self.patent_keywords 
                                               if keyword.lower() in all_text.lower())
        
        return metadata
    
    def _determine_result(self, issues: List[ValidationIssue]) -> ValidationResult:
        """Determine validation result based on issues"""
        if any(issue.level == ValidationLevel.CRITICAL for issue in issues):
            return ValidationResult.FAIL
        elif any(issue.level == ValidationLevel.WARNING for issue in issues):
            return ValidationResult.PARTIAL
        else:
            return ValidationResult.PASS

class CascadeFailurePrevention:
    """Prevents cascade failures by checking dependencies before execution"""
    
    def __init__(self):
        self.dependency_graph = {
            'patent_document': ['prior_art_analysis', 'claims_refinement'],
            'architecture_diagram': ['patent_document'],
            'colab_demo': ['patent_document', 'claims_refinement'],
            'legal_review': ['patent_document', 'prior_art_analysis'],
            'valuation': ['patent_document', 'legal_review']
        }
    
    def check_dependencies(self, task: str, available_outputs: List[str]) -> List[ValidationIssue]:
        """Check if dependencies are met and valid"""
        issues = []
        
        if task not in self.dependency_graph:
            return issues
        
        required_deps = self.dependency_graph[task]
        
        for dep in required_deps:
            if dep not in available_outputs:
                issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    message=f"Missing dependency: {dep} required for {task}",
                    file_path=f"workflow/{task}",
                    issue_type="missing_dependency",
                    suggestion=f"Complete {dep} task before executing {task}"
                ))
        
        return issues
    
    def validate_workflow_integrity(self, output_dir: str, tier: str, patent_id: str) -> List[ValidationIssue]:
        """Validate complete workflow integrity"""
        issues = []
        
        # Check for critical output files
        critical_files = [
            f"{patent_id}_patent_application.md",
            f"{patent_id}_prior_art_analysis.md",
            f"{patent_id}_legal_review.md"
        ]
        
        missing_critical = []
        for file_name in critical_files:
            file_path = os.path.join(output_dir, tier, file_name)
            if not os.path.exists(file_path):
                missing_critical.append(file_name)
        
        if missing_critical:
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message=f"Missing critical workflow outputs: {', '.join(missing_critical)}",
                file_path=f"workflow/{tier}/{patent_id}",
                issue_type="missing_critical_outputs",
                suggestion="Check workflow execution for failures"
            ))
        
        return issues

# Register media validators
media_validators = {
    'architecture_diagram': ArchitectureDiagramValidator(),
    'patent_notebook': PatentNotebookValidator(),
    'cascade_prevention': CascadeFailurePrevention()
} 