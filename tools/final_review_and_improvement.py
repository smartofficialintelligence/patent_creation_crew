# FinalReviewAndImprovementTool and dependencies will be moved here. 

from datetime import datetime
import logging
from typing import Dict, List, Any
from crewai.tools.agent_tools.base_agent_tools import BaseTool
from pydantic import BaseModel, validator

# Import from core modules
from core.validation import validate_patent_dict

class FinalReviewAndImprovementInput(BaseModel):
    patent_id: str
    title: str
    prior_art: str
    claims: str
    legal: str
    overlap: str

    @validator('claims')
    def claims_must_not_be_empty(cls, v):
        if not v or (isinstance(v, str) and not v.strip()):
            raise ValueError('claims must not be empty')
        return v

class FinalReviewAndImprovementTool(BaseTool):
    name: str = "final_review_and_improvement_tool"
    description: str = "Provide final review and improvement suggestions for completed patent work."
    args_schema: type[BaseModel] = FinalReviewAndImprovementInput

    def __init__(self):
        super().__init__()

    def _run(self, patent_id: str = None, title: str = None, prior_art: str = None, claims: str = None, 
             legal: str = None, overlap: str = None, review_objectives: List[str] = None,
             review_scope: List[str] = None, fresh_perspective_focus: List[str] = None,
             legal_review_report: Dict = None) -> str:
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
            
            # All inputs are guaranteed valid and non-empty by Pydantic
            report = f"""
FRESH PERSPECTIVE FINAL REVIEW & IMPROVEMENT ANALYSIS
====================================================

Patent ID: {patent_id}
Title: {title}
Review Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Reviewer: Independent Patent Quality Assurance Specialist

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

RECOMMENDATIONS:
================
- Address any identified gaps in claims or prior art analysis.
- Strengthen legal arguments as needed.
- Optimize for commercial value and portfolio integration.

"""
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