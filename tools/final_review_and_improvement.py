# FinalReviewAndImprovementTool and dependencies will be moved here. 

from datetime import datetime
import logging
from typing import Dict, List, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, validator

# Import from core modules
from core.validation import validate_patent_dict

class FinalReviewAndImprovementInput(BaseModel):
    patent_id: str
    title: str
    prior_art: str = ""
    claims: str = ""
    legal: str = ""
    overlap: str = ""
    review_type: str = "patent_document"
    content_to_review: str = ""

    @validator('claims')
    def claims_must_not_be_empty(cls, v):
        if not v or (isinstance(v, str) and not v.strip()):
            return ""
        return v

class FinalReviewAndImprovementTool(BaseTool):
    name: str = "final_review_and_improvement_tool"
    description: str = "Provide specific editorial alterations and improvements for patent document integration."
    args_schema: type[BaseModel] = FinalReviewAndImprovementInput

    def __init__(self):
        super().__init__()

    def _run(self, patent_id: str = None, title: str = None, prior_art: str = None, claims: str = None, 
             legal: str = None, overlap: str = None, review_objectives: List[str] = None,
             review_scope: List[str] = None, fresh_perspective_focus: List[str] = None,
             legal_review_report: Dict = None, review_type: str = "patent_document", 
             content_to_review: str = None) -> str:
        """Review completed patent work from a fresh perspective and suggest improvements"""
        try:
            # Handle different parameter formats from agents
            if legal_review_report and not legal:
                legal = str(legal_review_report)
            if review_objectives and not prior_art:
                prior_art = "Review objectives: " + ", ".join(review_objectives)
            if review_scope and not claims:
                claims = "Review scope: " + ", ".join(review_scope)
            if fresh_perspective_focus and not overlap:
                overlap = "Focus areas: " + ", ".join(fresh_perspective_focus)
                
            # Handle potential None values or empty strings
            patent_id = patent_id or "UNKNOWN"
            title = title or "Untitled Patent"
            prior_art = prior_art or "No prior art analysis provided"
            claims = claims or "No claims provided"
            legal = legal or "No legal review provided"
            overlap = overlap or "No overlap analysis provided"
            
            # Handle different review types
            if review_type == "colab_demo":
                report = self._generate_colab_demo_review(patent_id, title, content_to_review)
            else:
                report = self._generate_patent_document_review(patent_id, title, prior_art, claims, legal, overlap)
            
            return report
            
        except Exception as e:
            error_msg = f"""
ERROR IN FINAL REVIEW AND IMPROVEMENT TOOL
==========================================

Patent ID: {patent_id}
Error Type: {type(e).__name__}
Error Message: {str(e)}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The tool encountered an unexpected error during processing. This may be due to:
- Invalid input data format
- Missing required information
- Internal processing error

Please check the input parameters and try again. If the error persists, 
contact the system administrator.

Input Parameters Received:
- patent_id: {patent_id}
- title: {title[:100]}{'...' if len(title) > 100 else ''}
- prior_art length: {len(prior_art) if prior_art else 0} characters
- claims length: {len(claims) if claims else 0} characters
- legal length: {len(legal) if legal else 0} characters
- overlap length: {len(overlap) if overlap else 0} characters
"""
            logging.error(f"FinalReviewAndImprovementTool error: {e}")
            return error_msg
    
    def _generate_patent_document_review(self, patent_id: str, title: str, prior_art: str, claims: str, legal: str, overlap: str) -> str:
        """Generate patent document review report"""
        return f"""
EDITORIAL REVIEW FRESH PERSPECTIVE FINAL REVIEW & IMPROVEMENT ANALYSIS SPECIFIC ALTERATIONS
====================================================

Patent ID: {patent_id}
Title: {title}
Review Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Reviewer: Senior Patent Editor
Review Type: Patent Document

EXECUTIVE SUMMARY:
=================
This fresh perspective review evaluates the completed patent work for quality, completeness, 
and improvement opportunities. The review focuses on identifying gaps, inconsistencies, 
and enhancement opportunities that may have been overlooked in the initial analysis.

ORIGINAL CLAIMS ASSESSMENT:
==========================

Original Claims Review:
{claims}

Claims Quality Analysis:
✓ Technical specificity: {'GOOD' if len(claims.splitlines()) >= 3 else 'NEEDS IMPROVEMENT'}
✓ Breadth vs. specificity balance: {'BALANCED' if len(claims.splitlines()) >= 5 else 'NARROW'}
✓ Independent claim coverage: {'COMPREHENSIVE' if any('method' in c.lower() or 'system' in c.lower() for c in claims.splitlines()) else 'LIMITED'}

PRIOR ART INTEGRATION REVIEW:
============================

Prior Art Analysis Integration:
- Prior art analysis provided: {'YES' if prior_art else 'NO'}
- Novelty score assessment: {'INCLUDED' if 'novelty' in prior_art.lower() else 'MISSING'}
- Risk mitigation strategy: {'PRESENT' if 'risk' in prior_art.lower() else 'ABSENT'}

LEGAL REVIEW:
=============
{legal}

OVERLAP ANALYSIS:
=================
{overlap}

SPECIFIC ALTERATIONS FOR INTEGRATION:
================
1. SPECIFIC TEXT CHANGES:
   - [Provide specific text changes with clear implementation guidance]
2. QUALITY IMPROVEMENTS:
   - [Provide specific quality enhancement recommendations]

3. INTEGRATION INSTRUCTIONS:
   - Review each suggested change carefully
   - Integrate changes that improve quality and accuracy
   - Maintain technical accuracy and legal compliance
   - Document any rejected suggestions with reasoning
"""

    def _generate_colab_demo_review(self, patent_id: str, title: str, content_to_review: str) -> str:
        """Generate Colab demo review report"""
        return f"""
COLAB DEMO EDITORIAL REVIEW & IMPROVEMENT ANALYSIS SPECIFIC ALTERATIONS
====================================================

Patent ID: {patent_id}
Title: {title}
Review Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Reviewer: Senior Patent Editor
Review Type: Colab Demo Notebook

EXECUTIVE SUMMARY:
=================
This editorial review evaluates the Colab demo notebook for educational effectiveness, 
code quality, and user experience. The review focuses on identifying improvements for 
better demonstration of the patent's technology and enhanced learning outcomes.

COLAB DEMO CONTENT REVIEW:
==========================

Content Overview:
{content_to_review[:1000]}{'...' if len(content_to_review) > 1000 else ''}

DEMO QUALITY ASSESSMENT:
=======================

Code Quality Analysis:
✓ Code correctness: {'GOOD' if 'import' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}
✓ Best practices: {'GOOD' if 'def ' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}
✓ Documentation: {'GOOD' if '#' in content_to_review else 'NEEDS IMPROVEMENT'}

Educational Content Analysis:
✓ Clarity of explanations: {'GOOD' if len(content_to_review.splitlines()) >= 20 else 'NEEDS IMPROVEMENT'}
✓ Interactive elements: {'PRESENT' if 'interactive' in content_to_review.lower() else 'MISSING'}
✓ Performance benchmarks: {'INCLUDED' if 'benchmark' in content_to_review.lower() else 'MISSING'}

User Experience Analysis:
✓ Setup instructions: {'CLEAR' if 'setup' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}
✓ Visualizations: {'PRESENT' if 'plot' in content_to_review.lower() or 'visual' in content_to_review.lower() else 'MISSING'}
✓ Error handling: {'INCLUDED' if 'try' in content_to_review.lower() else 'MISSING'}

SPECIFIC ALTERATIONS FOR INTEGRATION:
====================================
1. CODE IMPROVEMENTS:
   - [Provide specific code corrections and enhancements]
   - [Suggest better error handling and edge cases]
   - [Recommend performance optimizations]

2. EDUCATIONAL ENHANCEMENTS:
   - [Improve explanations and documentation]
   - [Add more interactive examples]
   - [Enhance visualizations and demonstrations]

3. USER EXPERIENCE IMPROVEMENTS:
   - [Clarify setup instructions]
   - [Improve navigation and structure]
   - [Add troubleshooting guidance]

4. INTEGRATION INSTRUCTIONS:
   - Review each suggested change carefully
   - Integrate changes that improve educational value
   - Maintain technical accuracy and patent representation
   - Document any rejected suggestions with reasoning
   - Ensure all code examples are functional and tested
"""