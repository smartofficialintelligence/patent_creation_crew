"""
Tests for Quality Validation System
Tests semantic validators, media validators, and cascade failure prevention
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import the modules we're testing
from lib.quality_validation import (
    QualityValidationManager, ValidationIssue, ValidationLevel, 
    ValidationResult, ValidationReport, BaseValidator
)
from lib.semantic_validators import (
    PatentDocumentValidator, TechnicalAnalysisValidator, 
    ClaimsValidator, semantic_validators
)
from lib.media_validators import (
    ArchitectureDiagramValidator, PatentNotebookValidator, 
    CascadeFailurePrevention, media_validators
)
from lib.validation_pipeline import ValidationPipeline, ValidationIntegrationTool
from tools.quality_validation_tool import QualityValidationTool, WorkflowValidationTool

class TestQualityValidationManager:
    """Test the main quality validation manager"""
    
    def test_manager_initialization(self):
        """Test that the manager initializes correctly"""
        manager = QualityValidationManager()
        assert manager.output_dir == "output"
        assert len(manager.validators) > 0
        assert '.md' in manager.validators
        assert '.txt' in manager.validators
        assert '.json' in manager.validators
    
    def test_validate_file_nonexistent(self):
        """Test validation of non-existent file"""
        manager = QualityValidationManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_file = os.path.join(temp_dir, "nonexistent.md")
            
            report = manager.validate_file(nonexistent_file)
            
            assert report.result == ValidationResult.FAIL
            assert len(report.critical_issues) > 0
            assert any("does not exist" in issue.message.lower() for issue in report.critical_issues)
    
    def test_validate_file_empty(self):
        """Test validation of empty file"""
        manager = QualityValidationManager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("")
            temp_file = f.name
        
        try:
            report = manager.validate_file(temp_file)
            
            assert report.result in [ValidationResult.FAIL, ValidationResult.PARTIAL]
            assert len(report.issues) > 0
            assert any("empty" in issue.message.lower() for issue in report.issues)
        finally:
            os.unlink(temp_file)
    
    def test_validate_file_valid_markdown(self):
        """Test validation of valid markdown file"""
        manager = QualityValidationManager()
        
        valid_content = """# Patent Application
        
## Background
This is a well-formed patent document with proper structure.

## Claims
1. A method for improving system performance
2. The method of claim 1, wherein the system includes advanced algorithms

## Technical Description
The invention provides significant improvements over prior art through novel approaches.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(valid_content)
            temp_file = f.name
        
        try:
            report = manager.validate_file(temp_file)
            
            assert report.result in [ValidationResult.PASS, ValidationResult.PARTIAL]
            assert report.quality_score > 50
            assert report.file_size > 0
            assert report.checksum != ""
        finally:
            os.unlink(temp_file)
    
    def test_workflow_validation(self):
        """Test workflow validation with mock files"""
        manager = QualityValidationManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock output directory structure
            tier_dir = os.path.join(temp_dir, "tier_1")
            os.makedirs(tier_dir)
            
            # Create some mock files
            patent_file = os.path.join(tier_dir, "P001_patent_application.md")
            with open(patent_file, 'w') as f:
                f.write("# Patent Application\n\nThis is a test patent.")
            
            analysis_file = os.path.join(tier_dir, "P001_prior_art_analysis.md")
            with open(analysis_file, 'w') as f:
                f.write("# Prior Art Analysis\n\nThis is a test analysis.")
            
            # Temporarily set output directory
            original_output_dir = manager.output_dir
            manager.output_dir = temp_dir
            
            try:
                reports = manager.validate_patent_workflow_outputs("tier_1", "P001")
                
                assert len(reports) >= 2
                assert any("patent_application" in path for path in reports.keys())
                assert any("prior_art_analysis" in path for path in reports.keys())
                
                # Test summary report
                summary = manager.generate_summary_report(list(reports.values()))
                assert 'validation_summary' in summary
                assert 'file_type_summary' in summary
                assert 'quality_summary' in summary
                
            finally:
                manager.output_dir = original_output_dir

class TestSemanticValidators:
    """Test semantic validators for patent documents"""
    
    def test_patent_document_validator(self):
        """Test patent document validator"""
        validator = PatentDocumentValidator()
        
        # Test valid patent document
        valid_content = """# Patent Application: Advanced System

## Background of the Invention
This invention relates to advanced computational systems that improve performance.

## Summary of the Invention
The invention provides a novel method for system optimization.

## Claims
1. A method for improving system performance comprising:
   - Step A: Initialize the system
   - Step B: Apply optimization algorithms
   
2. The method of claim 1, wherein the optimization algorithms include machine learning.

## Detailed Description
The system implements advanced algorithms to achieve significant performance improvements.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(valid_content)
            temp_file = f.name
        
        try:
            report = validator.validate(temp_file)
            
            assert report.result in [ValidationResult.PASS, ValidationResult.PARTIAL]
            assert report.quality_score > 50
            assert 'total_claims' in report.metadata
            assert report.metadata['total_claims'] >= 2
            
        finally:
            os.unlink(temp_file)
    
    def test_patent_document_validator_missing_sections(self):
        """Test patent document validator with missing sections"""
        validator = PatentDocumentValidator()
        
        # Test document missing required sections
        incomplete_content = """# Patent Application
        
This is just a title with no proper sections.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(incomplete_content)
            temp_file = f.name
        
        try:
            report = validator.validate(temp_file)
            
            assert report.result in [ValidationResult.FAIL, ValidationResult.PARTIAL]
            assert len(report.issues) > 0
            
            # Check for missing sections issues
            missing_sections_issues = [
                issue for issue in report.issues 
                if 'missing' in issue.message.lower() and 'section' in issue.message.lower()
            ]
            assert len(missing_sections_issues) > 0
            
        finally:
            os.unlink(temp_file)
    
    def test_claims_validator(self):
        """Test claims validator"""
        validator = ClaimsValidator()
        
        # Test valid claims
        valid_claims = """# Patent Claims

## Independent Claims
1. A method for processing data comprising:
   - Receiving input data
   - Processing the data using novel algorithms
   - Generating optimized output

## Dependent Claims
2. The method of claim 1, wherein the algorithms include machine learning.
3. The method of claim 1, wherein the processing includes real-time analysis.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(valid_claims)
            temp_file = f.name
        
        try:
            report = validator.validate(temp_file)
            
            assert report.result in [ValidationResult.PASS, ValidationResult.PARTIAL]
            assert 'total_claims' in report.metadata
            assert report.metadata['total_claims'] >= 3
            
        finally:
            os.unlink(temp_file)

class TestMediaValidators:
    """Test media validators for diagrams and notebooks"""
    
    def test_architecture_diagram_validator_missing_file(self):
        """Test architecture diagram validator with missing file"""
        validator = ArchitectureDiagramValidator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_file = os.path.join(temp_dir, "missing_diagram.png")
            
            report = validator.validate(missing_file)
            
            assert report.result == ValidationResult.FAIL
            assert len(report.critical_issues) > 0
            assert any("does not exist" in issue.message.lower() for issue in report.critical_issues)
    
    @patch('lib.media_validators.PIL_AVAILABLE', True)
    def test_architecture_diagram_validator_small_file(self):
        """Test architecture diagram validator with very small file"""
        validator = ArchitectureDiagramValidator()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            f.write(b"tiny")  # Write very small content
            temp_file = f.name
        
        try:
            report = validator.validate(temp_file)
            
            assert report.result == ValidationResult.FAIL
            assert len(report.critical_issues) > 0
            assert any("very small" in issue.message.lower() for issue in report.critical_issues)
            
        finally:
            os.unlink(temp_file)
    
    def test_patent_notebook_validator_valid(self):
        """Test patent notebook validator with valid notebook"""
        validator = PatentNotebookValidator()
        
        # Create a valid notebook structure
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["# Patent Description\n", "This notebook demonstrates the patent invention."]
                },
                {
                    "cell_type": "markdown", 
                    "source": ["## Key Claims\n", "1. A novel method for processing\n", "2. The method of claim 1 with improvements"]
                },
                {
                    "cell_type": "code",
                    "source": ["import numpy as np\n", "def patent_algorithm():\n", "    return 'innovation'"]
                },
                {
                    "cell_type": "markdown",
                    "source": ["## Performance Results\n", "The algorithm shows significant improvements."]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook_content, f)
            temp_file = f.name
        
        try:
            report = validator.validate(temp_file)
            
            assert report.result in [ValidationResult.PASS, ValidationResult.PARTIAL]
            assert 'total_cells' in report.metadata
            assert report.metadata['total_cells'] == 4
            assert 'code_cells' in report.metadata
            assert report.metadata['code_cells'] == 1
            
        finally:
            os.unlink(temp_file)
    
    def test_patent_notebook_validator_missing_sections(self):
        """Test patent notebook validator with missing sections"""
        validator = PatentNotebookValidator()
        
        # Create notebook missing required sections
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["# Simple Notebook\n", "This is incomplete."]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook_content, f)
            temp_file = f.name
        
        try:
            report = validator.validate(temp_file)
            
            assert report.result in [ValidationResult.FAIL, ValidationResult.PARTIAL]
            assert len(report.issues) > 0
            
            # Check for missing sections
            missing_sections_issues = [
                issue for issue in report.issues 
                if 'missing' in issue.message.lower() and 'section' in issue.message.lower()
            ]
            assert len(missing_sections_issues) > 0
            
        finally:
            os.unlink(temp_file)

class TestCascadeFailurePrevention:
    """Test cascade failure prevention system"""
    
    def test_check_dependencies(self):
        """Test dependency checking"""
        cfp = CascadeFailurePrevention()
        
        # Test missing dependencies
        available_outputs = ['prior_art_analysis']
        issues = cfp.check_dependencies('legal_review', available_outputs)
        
        assert len(issues) > 0
        assert any('patent_document' in issue.message for issue in issues)
    
    def test_check_dependencies_satisfied(self):
        """Test dependency checking with satisfied dependencies"""
        cfp = CascadeFailurePrevention()
        
        # Test satisfied dependencies
        available_outputs = ['patent_document', 'prior_art_analysis']
        issues = cfp.check_dependencies('legal_review', available_outputs)
        
        assert len(issues) == 0
    
    def test_validate_workflow_integrity(self):
        """Test workflow integrity validation"""
        cfp = CascadeFailurePrevention()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create tier directory but no files
            tier_dir = os.path.join(temp_dir, "tier_1")
            os.makedirs(tier_dir)
            
            issues = cfp.validate_workflow_integrity(temp_dir, "tier_1", "P001")
            
            assert len(issues) > 0
            assert any('missing critical' in issue.message.lower() for issue in issues)

class TestValidationPipeline:
    """Test validation pipeline integration"""
    
    def test_validation_pipeline_initialization(self):
        """Test validation pipeline initialization"""
        pipeline = ValidationPipeline()
        
        assert pipeline.quality_manager is not None
        assert pipeline.cascade_prevention is not None
        assert len(pipeline.specialized_validators) > 0
    
    def test_validation_integration_tool(self):
        """Test validation integration tool"""
        tool = ValidationIntegrationTool()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Patent\n\nThis is a test patent document.")
            temp_file = f.name
        
        try:
            result = tool.validate_current_task("patent_document", temp_file)
            
            assert 'status' in result
            assert 'quality_score' in result
            assert 'is_valid' in result
            assert 'issues' in result
            assert 'recommendations' in result
            
        finally:
            os.unlink(temp_file)

class TestQualityValidationTools:
    """Test CrewAI quality validation tools"""
    
    def test_quality_validation_tool_initialization(self):
        """Test QualityValidationTool initialization"""
        tool = QualityValidationTool()
        
        assert tool.name == "Quality Validation Tool"
        assert "validates the quality" in tool.description.lower()
    
    def test_quality_validation_tool_missing_file(self):
        """Test QualityValidationTool with missing file"""
        tool = QualityValidationTool()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_file = os.path.join(temp_dir, "missing.md")
            
            result = tool._run("test_task", missing_file)
            
            assert "VALIDATION ERROR" in result or "FALLBACK VALIDATION" in result
            assert "does not exist" in result.lower()
    
    def test_workflow_validation_tool_initialization(self):
        """Test WorkflowValidationTool initialization"""
        tool = WorkflowValidationTool()
        
        assert tool.name == "Workflow Validation Tool"
        assert "validates complete workflow" in tool.description.lower()

class TestValidationConfiguration:
    """Test validation configuration and integration"""
    
    def test_semantic_validators_registry(self):
        """Test semantic validators registry"""
        assert 'patent_document' in semantic_validators
        assert 'technical_analysis' in semantic_validators
        assert 'claims_validation' in semantic_validators
        
        # Test that validators are properly instantiated
        for validator_name, validator in semantic_validators.items():
            assert hasattr(validator, 'validate')
            assert callable(validator.validate)
    
    def test_media_validators_registry(self):
        """Test media validators registry"""
        assert 'architecture_diagram' in media_validators
        assert 'patent_notebook' in media_validators
        assert 'cascade_prevention' in media_validators
        
        # Test that validators are properly instantiated
        for validator_name, validator in media_validators.items():
            if validator_name != 'cascade_prevention':
                assert hasattr(validator, 'validate')
                assert callable(validator.validate)

class TestValidationReporting:
    """Test validation reporting and metrics"""
    
    def test_validation_issue_creation(self):
        """Test ValidationIssue creation"""
        issue = ValidationIssue(
            level=ValidationLevel.CRITICAL,
            message="Test issue",
            file_path="test.md",
            issue_type="test_type",
            suggestion="Fix the issue"
        )
        
        assert issue.level == ValidationLevel.CRITICAL
        assert issue.message == "Test issue"
        assert issue.file_path == "test.md"
        assert issue.issue_type == "test_type"
        assert issue.suggestion == "Fix the issue"
    
    def test_validation_report_creation(self):
        """Test ValidationReport creation"""
        issues = [
            ValidationIssue(
                level=ValidationLevel.WARNING,
                message="Warning issue",
                file_path="test.md",
                issue_type="warning"
            ),
            ValidationIssue(
                level=ValidationLevel.CRITICAL,
                message="Critical issue",
                file_path="test.md",
                issue_type="critical"
            )
        ]
        
        report = ValidationReport(
            file_path="test.md",
            file_type="patent_document",
            result=ValidationResult.PARTIAL,
            issues=issues,
            metadata={'test': 'data'},
            validation_time=datetime.now(),
            file_size=1024,
            checksum="abc123"
        )
        
        assert report.result == ValidationResult.PARTIAL
        assert len(report.issues) == 2
        assert len(report.critical_issues) == 1
        assert len(report.warning_issues) == 1
        assert report.is_valid == False  # PARTIAL with critical issues
        assert report.quality_score < 100  # Should be reduced due to issues

# Integration test
class TestEndToEndValidation:
    """End-to-end validation tests"""
    
    def test_complete_validation_workflow(self):
        """Test complete validation workflow"""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create output directory structure
            tier_dir = os.path.join(temp_dir, "tier_1")
            os.makedirs(tier_dir)
            
            # Create patent document
            patent_content = """# Patent Application: Advanced System

## Background of the Invention
This invention relates to advanced computational systems.

## Summary of the Invention
The invention provides a novel method for system optimization.

## Claims
1. A method for improving system performance
2. The method of claim 1, wherein the system includes ML algorithms

## Detailed Description
The system implements advanced algorithms to achieve improvements.
"""
            
            patent_file = os.path.join(tier_dir, "P001_patent_application.md")
            with open(patent_file, 'w') as f:
                f.write(patent_content)
            
            # Create notebook
            notebook_content = {
                "cells": [
                    {
                        "cell_type": "markdown",
                        "source": ["# Patent Description\n", "This demonstrates the patent."]
                    },
                    {
                        "cell_type": "markdown",
                        "source": ["## Key Claims\n", "1. Novel processing method"]
                    },
                    {
                        "cell_type": "code",
                        "source": ["def patent_algorithm():\n", "    return 'innovation'"]
                    },
                    {
                        "cell_type": "markdown",
                        "source": ["## Performance Results\n", "Significant improvements shown."]
                    }
                ],
                "metadata": {"kernelspec": {"name": "python3"}},
                "nbformat": 4,
                "nbformat_minor": 4
            }
            
            notebook_file = os.path.join(tier_dir, "P001_colab_demo.ipynb")
            with open(notebook_file, 'w') as f:
                json.dump(notebook_content, f)
            
            # Run validation pipeline
            pipeline = ValidationPipeline()
            original_output_dir = pipeline.quality_manager.output_dir
            pipeline.quality_manager.output_dir = temp_dir
            
            try:
                # Validate complete workflow
                result = pipeline.validate_complete_workflow("tier_1", "P001")
                
                assert 'workflow_id' in result
                assert 'overall_status' in result
                assert 'quality_score' in result
                assert 'file_reports' in result
                assert 'summary' in result
                
                # Check that files were validated
                assert len(result['file_reports']) >= 2
                
                # Check overall status
                assert result['overall_status'] in ['PASSED', 'PARTIAL', 'FAILED']
                
            finally:
                pipeline.quality_manager.output_dir = original_output_dir

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 