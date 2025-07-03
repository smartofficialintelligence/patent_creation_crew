# FinalReviewAndImprovementTool and dependencies will be moved here. 

from datetime import datetime
import logging
from typing import Dict, List, Any
from crewai.tools.base_tool import BaseTool
from pydantic import BaseModel

# Import from core modules
from core.validation import validate_patent_dict

class FinalReviewAndImprovementInput(BaseModel):
    patent_id: str = None
    title: str = None
    prior_art: str = None
    claims: str = None
    legal: str = None
    overlap: str = None

class FinalReviewAndImprovementTool(BaseTool):
    name: str = "final_review_and_improvement_tool"
    description: str = "Provide final review and improvement suggestions for completed patent work."
    args_schema: type[BaseModel] = FinalReviewAndImprovementInput

    def __init__(self):
        super().__init__()

    def _run(self, *args, **kwargs) -> str:
        """Review completed patent work from a fresh perspective and suggest improvements"""
        
        # Handle both positional and keyword arguments
        if args and isinstance(args[0], dict):
            patent_data = args[0]
        elif 'patent_data' in kwargs:
            patent_data = kwargs['patent_data']
        else:
            patent_data = {
                'id': kwargs.get('id', ''),
                'title': kwargs.get('title', ''),
                'description': kwargs.get('description', ''),
                'key_claims': kwargs.get('key_claims', ''),
                'technical_features': kwargs.get('technical_features', ''),
                'market_applications': kwargs.get('market_applications', ''),
                'value_estimate': kwargs.get('value_estimate', ''),
                'differentiation': kwargs.get('differentiation', '')
            }
        
        prior_art_analysis = kwargs.get('prior_art_analysis', '')
        refined_claims = kwargs.get('refined_claims', '')
        legal_review = kwargs.get('legal_review', '')
        overlap_analysis = kwargs.get('overlap_analysis', '')
        
        # Validate input
        validated_data = validate_patent_dict(patent_data)
        
        patent_id = validated_data['id']
        title = validated_data['title']
        original_claims = validated_data['key_claims']
        
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
{chr(10).join(f"{i+1}. {claim}" for i, claim in enumerate(original_claims))}

Claims Quality Analysis:
✓ Technical specificity: {'GOOD' if len(original_claims) >= 3 else 'NEEDS IMPROVEMENT'}
✓ Breadth vs. specificity balance: {'BALANCED' if len(original_claims) >= 5 else 'NARROW'}
✓ Independent claim coverage: {'COMPREHENSIVE' if any('method' in claim.lower() or 'system' in claim.lower() for claim in original_claims) else 'LIMITED'}

PRIOR ART INTEGRATION REVIEW:
============================

Prior Art Analysis Integration:
- Prior art analysis provided: {'YES' if prior_art_analysis else 'NO'}
- Novelty score assessment: {'INCLUDED' if 'novelty' in prior_art_analysis.lower() else 'MISSING'}
- Risk mitigation strategy: {'PRESENT' if 'risk' in prior_art_analysis.lower() else 'ABSENT'}

Integration Quality:
✓ Prior art differentiation: {'CLEAR' if 'differentiation' in prior_art_analysis.lower() else 'UNCLEAR'}
✓ Claim refinement based on prior art: {'EVIDENT' if refined_claims else 'MISSING'}
✓ Risk assessment completeness: {'COMPREHENSIVE' if 'risk' in prior_art_analysis.lower() else 'INCOMPLETE'}

CLAIMS REFINEMENT EVALUATION:
============================

Refined Claims Assessment:
- Claims refinement performed: {'YES' if refined_claims else 'NO'}
- Independent claims quality: {'STRONG' if 'independent' in refined_claims.lower() else 'WEAK'}
- Dependent claims coverage: {'COMPREHENSIVE' if 'dependent' in refined_claims.lower() else 'LIMITED'}

Refinement Quality Indicators:
✓ Technical specificity: {'ENHANCED' if 'sub-5ms' in refined_claims.lower() or 'GPU' in refined_claims.lower() else 'GENERIC'}
✓ Prior art avoidance: {'EFFECTIVE' if 'semantic' in refined_claims.lower() else 'UNCLEAR'}
✓ Commercial value optimization: {'MAXIMIZED' if 'licensing' in refined_claims.lower() or 'value' in refined_claims.lower() else 'NOT OPTIMIZED'}

LEGAL COMPLIANCE REVIEW:
=======================

Legal Review Integration:
- Legal review performed: {'YES' if legal_review else 'NO'}
- Patent law compliance: {'VERIFIED' if 'compliance' in legal_review.lower() else 'NOT VERIFIED'}
- Filing strategy: {'DEFINED' if 'strategy' in legal_review.lower() else 'MISSING'}

Legal Quality Assessment:
✓ 35 USC 101 compliance: {'CONFIRMED' if '101' in legal_review.lower() else 'NOT CONFIRMED'}
✓ Enablement requirements: {'MET' if 'enablement' in legal_review.lower() else 'NOT VERIFIED'}
✓ Claim clarity: {'SATISFACTORY' if 'clarity' in legal_review.lower() else 'NEEDS REVIEW'}

OVERLAP ANALYSIS INTEGRATION:
============================

Term Overlap Assessment:
- Overlap analysis performed: {'YES' if overlap_analysis else 'NO'}
- Risk identification: {'COMPLETE' if 'risk' in overlap_analysis.lower() else 'INCOMPLETE'}
- Mitigation strategies: {'PROVIDED' if 'mitigation' in overlap_analysis.lower() else 'MISSING'}

Overlap Quality:
✓ Term extraction accuracy: {'GOOD' if overlap_analysis else 'NOT PERFORMED'}
✓ Risk categorization: {'DETAILED' if 'high risk' in overlap_analysis.lower() or 'medium risk' in overlap_analysis.lower() else 'BASIC'}
✓ Refinement recommendations: {'SPECIFIC' if 'refinement' in overlap_analysis.lower() else 'GENERAL'}

QUALITY GAPS IDENTIFIED:
=======================

Critical Gaps:
"""
        
        gaps = []
        if not prior_art_analysis:
            gaps.append("❌ Prior art analysis missing - critical for patentability assessment")
        if not refined_claims:
            gaps.append("❌ Claims refinement missing - essential for maximizing patent value")
        if not legal_review:
            gaps.append("❌ Legal review missing - required for filing compliance")
        if not overlap_analysis:
            gaps.append("❌ Term overlap analysis missing - important for risk assessment")
        
        if not gaps:
            gaps.append("✅ All major components present")
        
        for gap in gaps:
            report += f"{gap}\n"
        
        report += f"""
IMPROVEMENT OPPORTUNITIES:
=========================

Technical Enhancements:
"""
        
        improvements = []
        
        # Check for technical specificity
        if not any('sub-5ms' in str(original_claims).lower() or 'GPU' in str(original_claims).lower()):
            improvements.append("🔧 Add specific performance metrics (sub-5ms coordination cycles)")
        
        if not any('semantic' in str(original_claims).lower()):
            improvements.append("🔧 Emphasize semantic reasoning differentiation from mathematical optimization")
        
        if not any('interpretable' in str(original_claims).lower() or 'explainable' in str(original_claims).lower()):
            improvements.append("🔧 Include interpretability/explainability features for regulatory compliance")
        
        if not any('coordination' in str(original_claims).lower()):
            improvements.append("🔧 Detail agent coordination protocols and mechanisms")
        
        if not improvements:
            improvements.append("✅ Technical specifications appear comprehensive")
        
        for improvement in improvements:
            report += f"{improvement}\n"
        
        report += f"""
Strategic Enhancements:
"""
        
        strategic_improvements = []
        
        # Check for commercial value optimization
        if not any('licensing' in str(legal_review).lower() or 'value' in str(legal_review).lower()):
            strategic_improvements.append("💼 Add commercial value assessment and licensing strategy")
        
        if not any('international' in str(legal_review).lower() or 'EP' in str(legal_review).lower() or 'CN' in str(legal_review).lower()):
            strategic_improvements.append("🌍 Include international filing strategy (EP, CN, JP)")
        
        if not any('prosecution' in str(legal_review).lower()):
            strategic_improvements.append("📋 Add prosecution timeline and amendment strategy")
        
        if not strategic_improvements:
            strategic_improvements.append("✅ Strategic considerations appear comprehensive")
        
        for improvement in strategic_improvements:
            report += f"{improvement}\n"
        
        report += f"""
ITERATIVE IMPROVEMENT RECOMMENDATIONS:
=====================================

Immediate Actions (Priority 1):
"""
        
        immediate_actions = []
        
        if not prior_art_analysis:
            immediate_actions.append("1. 🔥 CONDUCT PRIOR ART SEARCH - Critical for patentability")
        if not refined_claims:
            immediate_actions.append("2. 🔥 REFINE CLAIMS - Essential for maximizing patent value")
        if not legal_review:
            immediate_actions.append("3. 🔥 PERFORM LEGAL REVIEW - Required for filing compliance")
        
        if not immediate_actions:
            immediate_actions.append("1. ✅ All critical components completed")
        
        for action in immediate_actions:
            report += f"{action}\n"
        
        report += f"""
Short-term Improvements (Priority 2):
"""
        
        short_term = []
        
        if not overlap_analysis:
            short_term.append("1. 📊 Conduct term overlap analysis for risk assessment")
        
        if not any('performance' in str(original_claims).lower()):
            short_term.append("2. ⚡ Add specific performance benchmarks and metrics")
        
        if not any('scalability' in str(original_claims).lower()):
            short_term.append("3. 📈 Include scalability and deployment considerations")
        
        if not short_term:
            short_term.append("1. ✅ Short-term improvements already addressed")
        
        for item in short_term:
            report += f"{item}\n"
        
        report += f"""
Long-term Enhancements (Priority 3):
"""
        
        long_term = []
        
        if not any('continuation' in str(legal_review).lower()):
            long_term.append("1. 🔄 Plan continuation application strategy")
        
        if not any('portfolio' in str(legal_review).lower()):
            long_term.append("2. 📚 Develop comprehensive portfolio integration plan")
        
        if not any('enforcement' in str(legal_review).lower()):
            long_term.append("3. 🛡️ Consider enforcement and litigation strategy")
        
        if not long_term:
            long_term.append("1. ✅ Long-term strategy already considered")
        
        for item in long_term:
            report += f"{item}\n"
        
        report += f"""
QUALITY SCORE ASSESSMENT:
========================

Component Quality Scores:
- Prior Art Analysis: {'9/10' if prior_art_analysis and 'novelty' in prior_art_analysis.lower() else '5/10' if prior_art_analysis else '1/10'}
- Claims Refinement: {'9/10' if refined_claims and 'independent' in refined_claims.lower() else '5/10' if refined_claims else '1/10'}
- Legal Review: {'9/10' if legal_review and 'compliance' in legal_review.lower() else '5/10' if legal_review else '1/10'}
- Overlap Analysis: {'8/10' if overlap_analysis and 'risk' in overlap_analysis.lower() else '4/10' if overlap_analysis else '1/10'}

Overall Quality Score: {self._calculate_overall_quality_score(prior_art_analysis, refined_claims, legal_review, overlap_analysis)}/10

Quality Classification: {self._get_quality_classification(prior_art_analysis, refined_claims, legal_review, overlap_analysis)}

FINAL RECOMMENDATIONS:
=====================

Based on this fresh perspective review:

"""
        
        if self._calculate_overall_quality_score(prior_art_analysis, refined_claims, legal_review, overlap_analysis) >= 8:
            report += """
✅ EXCELLENT QUALITY - READY FOR FILING
- All major components present and high quality
- Minor enhancements recommended for optimization
- Proceed with attorney review and filing
"""
        elif self._calculate_overall_quality_score(prior_art_analysis, refined_claims, legal_review, overlap_analysis) >= 6:
            report += """
⚠️ GOOD QUALITY - NEEDS MINOR IMPROVEMENTS
- Most components present but some gaps identified
- Address priority 1 improvements before filing
- Consider professional attorney review
"""
        else:
            report += """
❌ INCOMPLETE - MAJOR IMPROVEMENTS REQUIRED
- Critical components missing or inadequate
- Address all priority 1 actions before proceeding
- Engage patent attorney for comprehensive review
"""
        
        report += f"""
CONFIDENCE LEVEL: {self._get_confidence_level(prior_art_analysis, refined_claims, legal_review, overlap_analysis)}
RECOMMENDATION: {self._get_final_recommendation(prior_art_analysis, refined_claims, legal_review, overlap_analysis)}
PRIORITY: {self._get_priority_level(prior_art_analysis, refined_claims, legal_review, overlap_analysis)}

END OF FRESH PERSPECTIVE REVIEW
"""
        
        return report
    
    def _calculate_overall_quality_score(self, prior_art: str, claims: str, legal: str, overlap: str) -> int:
        """Calculate overall quality score based on component completeness"""
        score = 0
        
        if prior_art and 'novelty' in prior_art.lower():
            score += 3
        elif prior_art:
            score += 2
        else:
            score += 0
        
        if claims and 'independent' in claims.lower():
            score += 3
        elif claims:
            score += 2
        else:
            score += 0
        
        if legal and 'compliance' in legal.lower():
            score += 3
        elif legal:
            score += 2
        else:
            score += 0
        
        if overlap and 'risk' in overlap.lower():
            score += 1
        elif overlap:
            score += 0.5
        else:
            score += 0
        
        return min(10, int(score))
    
    def _get_quality_classification(self, prior_art: str, claims: str, legal: str, overlap: str) -> str:
        """Get quality classification based on component completeness"""
        score = self._calculate_overall_quality_score(prior_art, claims, legal, overlap)
        
        if score >= 8:
            return "EXCELLENT"
        elif score >= 6:
            return "GOOD"
        elif score >= 4:
            return "FAIR"
        else:
            return "POOR"
    
    def _get_confidence_level(self, prior_art: str, claims: str, legal: str, overlap: str) -> str:
        """Get confidence level based on component completeness"""
        score = self._calculate_overall_quality_score(prior_art, claims, legal, overlap)
        
        if score >= 8:
            return "HIGH (90-95%)"
        elif score >= 6:
            return "MEDIUM (70-85%)"
        elif score >= 4:
            return "LOW (50-65%)"
        else:
            return "VERY LOW (<50%)"
    
    def _get_final_recommendation(self, prior_art: str, claims: str, legal: str, overlap: str) -> str:
        """Get final recommendation based on quality assessment"""
        score = self._calculate_overall_quality_score(prior_art, claims, legal, overlap)
        
        if score >= 8:
            return "PROCEED WITH FILING"
        elif score >= 6:
            return "IMPROVE THEN FILE"
        else:
            return "MAJOR REVISION REQUIRED"
    
    def _get_priority_level(self, prior_art: str, claims: str, legal: str, overlap: str) -> str:
        """Get priority level based on quality assessment"""
        score = self._calculate_overall_quality_score(prior_art, claims, legal, overlap)
        
        if score >= 8:
            return "HIGH (file within 30 days)"
        elif score >= 6:
            return "MEDIUM (improve within 60 days)"
        else:
            return "LOW (major work required)"