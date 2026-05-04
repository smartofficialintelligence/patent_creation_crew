#!/usr/bin/env python3
"""
Pydantic Output Models for Patent Automation System
These models define how CrewAI should parse tool outputs into clean text content.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class PriorArtAnalysisOutput(BaseModel):
    """Output model for prior art research results"""
    content: str = Field(description="Complete prior art analysis report")
    
    def __str__(self) -> str:
        return self.content

    def model_dump_json(self, **kwargs):
        return self.content

class PatentDocumentOutput(BaseModel):
    """Output model for patent document generation"""
    content: str = Field(description="Complete patent document content")
    
    def __str__(self) -> str:
        return self.content
    
    def model_dump_json(self, **kwargs):
        return self.content

class ClaimsRefinementOutput(BaseModel):
    """Output model for refined patent claims"""
    content: str = Field(description="Refined patent claims content")
    
    def __str__(self) -> str:
        return self.content
    
    def model_dump_json(self, **kwargs):
        return self.content

class LegalReviewOutput(BaseModel):
    """Output model for legal review analysis"""
    content: str = Field(description="Legal review and analysis content")
    
    def __str__(self) -> str:
        return self.content
    
    def model_dump_json(self, **kwargs):
        return self.content

class FinalReviewOutput(BaseModel):
    """Output model for editorial review feedback"""
    content: str = Field(description="Editorial review and feedback content")
    
    def __str__(self) -> str:
        return self.content
    
    def model_dump_json(self, **kwargs):
        return self.content

class GenericAnalysisOutput(BaseModel):
    """Generic output model for analysis tasks"""
    content: str = Field(description="Analysis or report content")
    
    def __str__(self) -> str:
        return self.content
    
    def model_dump_json(self, **kwargs):
        return self.content

class ValuationOutput(BaseModel):
    """Output model for patent valuation reports"""
    valuation_content: str = Field(description="Patent valuation report content")
    
    def __str__(self) -> str:
        return self.valuation_content
    
    def model_dump_json(self, **kwargs):
        return self.valuation_content

class ArchitectureOutput(BaseModel):
    """Output model for architecture diagrams"""
    content: str = Field(description="Architecture diagram content and descriptions")
    
    def __str__(self) -> str:
        return self.content
    
    def model_dump_json(self, **kwargs):
        return self.content

class ColabDemoOutput(BaseModel):
    """Output model for Colab demo generation"""
    content: str = Field(description="Colab demo notebook content and log")
    
    def __str__(self) -> str:
        return self.content
    
    def model_dump_json(self, **kwargs):
        return self.content

class DiagramOutput(BaseModel):
    """Output model for diagram generation"""
    content: str = Field(description="Diagram content and descriptions")
    
    def __str__(self) -> str:
        return self.content
    
    def model_dump_json(self, **kwargs):
        return self.content

class EditorialFeedbackOutput(BaseModel):
    """Output model for editorial feedback"""
    content: str = Field(description="Editorial feedback content")
    
    def __str__(self) -> str:
        return self.content
    
    def model_dump_json(self, **kwargs):
        return self.content

class CoverSheetOutput(BaseModel):
    """Output model for cover sheet generation"""
    content: str = Field(description="Cover sheet content")
    
    def __str__(self) -> str:
        return self.content
    
    def model_dump_json(self, **kwargs):
        return self.content

class ValuationReportOutput(BaseModel):
    """Output model for valuation reports"""
    content: str = Field(description="Valuation report content")
    
    def __str__(self) -> str:
        return self.content
    
    def model_dump_json(self, **kwargs):
        return self.content

# Export all models
__all__ = [
    'PriorArtAnalysisOutput',
    'PatentDocumentOutput', 
    'ClaimsRefinementOutput',
    'LegalReviewOutput',
    'FinalReviewOutput',
    'GenericAnalysisOutput',
    'ValuationOutput',
    'ArchitectureOutput',
    'ColabDemoOutput',
    'DiagramOutput',
    'EditorialFeedbackOutput',
    'CoverSheetOutput',
    'ValuationReportOutput'
] 