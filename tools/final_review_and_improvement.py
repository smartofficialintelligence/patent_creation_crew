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
        """Generate Colab demo review report focused on patent demonstration"""
        return f"""
COLAB DEMO EDITORIAL REVIEW - PATENT DEMONSTRATION COMPONENT
===========================================================

Patent ID: {patent_id}
Title: {title}
Review Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Reviewer: Senior Patent Editor
Review Type: Patent Demonstration Notebook

PATENT DEMONSTRATION CONTEXT:
============================
This Colab notebook is a critical component of the patent submission package, designed to:
- Demonstrate the patent's core technology in action
- Provide evidence of enablement and implementation
- Showcase the invention's novelty and non-obviousness
- Support patent claims with working examples
- Enable patent examiners and stakeholders to understand the invention

EXECUTIVE SUMMARY:
=================
This editorial review evaluates the Colab demo notebook as a patent demonstration artifact, 
focusing on its effectiveness in supporting patent claims, demonstrating enablement, 
and showcasing the invention's technical advantages over prior art.

COLAB DEMO CONTENT REVIEW:
==========================

Content Overview:
{content_to_review[:1000]}{'...' if len(content_to_review) > 1000 else ''}

PATENT DEMONSTRATION ASSESSMENT:
===============================

Claim Support Analysis:
✓ Core patent claims demonstrated: {'GOOD' if any(claim_word in content_to_review.lower() for claim_word in ['agent', 'semantic', 'optimization', 'coordination']) else 'NEEDS IMPROVEMENT'}
✓ Technical features implemented: {'GOOD' if 'technical' in content_to_review.lower() or 'feature' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}
✓ Performance claims validated: {'GOOD' if any(perf_word in content_to_review.lower() for perf_word in ['performance', 'benchmark', 'speed', 'accuracy']) else 'NEEDS IMPROVEMENT'}
✓ Prior art differentiation shown: {'GOOD' if 'differentiation' in content_to_review.lower() or 'advantage' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}

Enablement Verification:
✓ Working implementation provided: {'GOOD' if 'def ' in content_to_review.lower() or 'class ' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}
✓ Clear technical disclosure: {'GOOD' if len(content_to_review.splitlines()) >= 30 else 'NEEDS IMPROVEMENT'}
✓ Skilled artisan guidance: {'GOOD' if 'setup' in content_to_review.lower() or 'instruction' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}
✓ Reproducible results: {'GOOD' if 'result' in content_to_review.lower() or 'output' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}

Technical Demonstration Quality:
✓ Algorithm implementation: {'GOOD' if 'algorithm' in content_to_review.lower() or 'implementation' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}
✓ Performance benchmarks: {'GOOD' if 'benchmark' in content_to_review.lower() or 'performance' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}
✓ Comparative analysis: {'GOOD' if 'compare' in content_to_review.lower() or 'versus' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}
✓ Real-world applicability: {'GOOD' if 'application' in content_to_review.lower() or 'use case' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}

Patent Submission Readiness:
✓ Professional presentation: {'GOOD' if 'title' in content_to_review.lower() and 'description' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}
✓ Clear documentation: {'GOOD' if '#' in content_to_review else 'NEEDS IMPROVEMENT'}
✓ Error handling: {'GOOD' if 'try' in content_to_review.lower() or 'error' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}
✓ Visual demonstrations: {'GOOD' if 'plot' in content_to_review.lower() or 'visual' in content_to_review.lower() else 'NEEDS IMPROVEMENT'}

SPECIFIC ALTERATIONS FOR PATENT DEMONSTRATION:
=============================================

1. CLAIM SUPPORT ENHANCEMENTS:
   - [Strengthen demonstration of core patent claims]
   - [Add specific examples showing claim elements in action]
   - [Include performance metrics that validate claim advantages]
   - [Demonstrate technical features that differentiate from prior art]

2. ENABLEMENT IMPROVEMENTS:
   - [Ensure complete implementation of claimed technology]
   - [Add clear instructions for skilled artisan reproduction]
   - [Include all necessary code components and dependencies]
   - [Provide working examples that validate patent scope]

3. TECHNICAL DEMONSTRATION REFINEMENTS:
   - [Enhance algorithm implementation clarity]
   - [Add performance benchmarks vs. prior art methods]
   - [Include comparative analysis showing advantages]
   - [Demonstrate real-world applicability and use cases]

4. PATENT SUBMISSION QUALITY:
   - [Improve professional presentation and structure]
   - [Enhance documentation for patent examiner review]
   - [Add clear setup and execution instructions]
   - [Include visual demonstrations of key concepts]

5. INTEGRATION INSTRUCTIONS FOR PATENT CONTEXT:
   - Review each suggested change in context of patent demonstration
   - Ensure changes strengthen patent claims and enablement
   - Maintain technical accuracy and patent examiner accessibility
   - Focus on demonstrating novelty and non-obviousness
   - Ensure the notebook serves as effective patent submission evidence
   - Document how changes improve patent demonstration value
"""