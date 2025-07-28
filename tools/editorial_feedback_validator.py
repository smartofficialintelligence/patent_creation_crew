#!/usr/bin/env python3
"""
Editorial Feedback Effectiveness Validator
Prevents wasted API calls from ineffective editorial iterations
"""

import os
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
try:
    from crewai.tools import BaseTool
except ImportError:
    from crewai.tools.agent_tools import Tool as BaseTool
from pydantic import BaseModel
import difflib

logger = logging.getLogger(__name__)

class EditorialEffectivenessAnalysis(BaseModel):
    """Analysis result for editorial feedback effectiveness"""
    is_effective: bool
    effectiveness_score: float  # 0.0 to 1.0
    content_similarity: float   # How similar pre/post content is
    validation_improvement: bool # Did validation improve?
    issues_addressed: int       # How many issues were addressed
    new_issues_introduced: int  # How many new issues appeared
    recommended_action: str     # What to do next
    reasoning: str             # Why this recommendation

class EditorialFeedbackValidator(BaseTool):
    """Tool to validate effectiveness of editorial feedback and prevent ineffective loops"""
    
    name: str = "editorial_feedback_validator"
    description: str = "Validates effectiveness of editorial feedback integration to prevent wasted iterations"
    
    def __init__(self):
        super().__init__()
        self.feedback_history = {}  # Track feedback effectiveness history
        
    def _run(self, patent_id: str, title: str, 
             original_content: str, updated_content: str,
             original_validation: Dict, updated_validation: Dict,
             editorial_feedback: str, iteration_count: int = 1) -> str:
        """
        Analyze effectiveness of editorial feedback integration
        
        Args:
            patent_id: Patent identifier
            title: Patent title
            original_content: Content before editorial feedback
            updated_content: Content after editorial feedback
            original_validation: Validation result before feedback
            updated_validation: Validation result after feedback  
            editorial_feedback: The editorial feedback that was applied
            iteration_count: Current iteration number
        """
        
        try:
            analysis = self._analyze_effectiveness(
                patent_id, original_content, updated_content,
                original_validation, updated_validation,
                editorial_feedback, iteration_count
            )
            
            # Log analysis for monitoring
            self._log_effectiveness_analysis(patent_id, analysis)
            
            # Determine recommended action
            action_plan = self._generate_action_plan(analysis, iteration_count)
            
            return self._format_effectiveness_report(analysis, action_plan)
            
        except Exception as e:
            logger.error(f"Editorial feedback validation failed for {patent_id}: {e}")
            return self._generate_error_response(patent_id, str(e))
    
    def _analyze_effectiveness(self, patent_id: str, original_content: str, 
                             updated_content: str, original_validation: Dict,
                             updated_validation: Dict, editorial_feedback: str,
                             iteration_count: int) -> EditorialEffectivenessAnalysis:
        """Analyze how effective the editorial feedback was"""
        
        # 1. Calculate content similarity (lower = more change)
        content_similarity = self._calculate_content_similarity(original_content, updated_content)
        
        # 2. Check validation improvement
        validation_improved = self._check_validation_improvement(original_validation, updated_validation)
        
        # 3. Count issues addressed vs introduced
        issues_addressed = self._count_issues_addressed(original_validation, updated_validation)
        issues_introduced = self._count_new_issues(original_validation, updated_validation)
        
        # 4. Calculate effectiveness score
        effectiveness_score = self._calculate_effectiveness_score(
            content_similarity, validation_improved, issues_addressed, issues_introduced
        )
        
        # 5. Determine if feedback was effective
        is_effective = effectiveness_score >= 0.6 and validation_improved
        
        # 6. Generate recommendation
        recommended_action, reasoning = self._determine_recommendation(
            is_effective, effectiveness_score, content_similarity, 
            validation_improved, iteration_count
        )
        
        return EditorialEffectivenessAnalysis(
            is_effective=is_effective,
            effectiveness_score=effectiveness_score,
            content_similarity=content_similarity,
            validation_improvement=validation_improved,
            issues_addressed=issues_addressed,
            new_issues_introduced=issues_introduced,
            recommended_action=recommended_action,
            reasoning=reasoning
        )
    
    def _calculate_content_similarity(self, original: str, updated: str) -> float:
        """Calculate similarity between original and updated content (0.0 = completely different, 1.0 = identical)"""
        if not original or not updated:
            return 0.0
            
        # Use difflib to calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, original, updated).ratio()
        return similarity
    
    def _check_validation_improvement(self, original_val: Dict, updated_val: Dict) -> bool:
        """Check if validation improved after editorial feedback"""
        original_valid = original_val.get('is_valid', False)
        updated_valid = updated_val.get('is_valid', False)
        
        original_issues = len(original_val.get('issues', []))
        updated_issues = len(updated_val.get('issues', []))
        
        # Improved if:
        # 1. Became valid, or
        # 2. Reduced number of issues
        return updated_valid or (updated_issues < original_issues)
    
    def _count_issues_addressed(self, original_val: Dict, updated_val: Dict) -> int:
        """Count how many validation issues were addressed"""
        original_issues = set(original_val.get('issues', []))
        updated_issues = set(updated_val.get('issues', []))
        
        # Issues that were in original but not in updated
        addressed = original_issues - updated_issues
        return len(addressed)
    
    def _count_new_issues(self, original_val: Dict, updated_val: Dict) -> int:
        """Count how many new validation issues were introduced"""
        original_issues = set(original_val.get('issues', []))
        updated_issues = set(updated_val.get('issues', []))
        
        # Issues that are in updated but not in original
        new_issues = updated_issues - original_issues
        return len(new_issues)
    
    def _calculate_effectiveness_score(self, content_similarity: float, 
                                     validation_improved: bool,
                                     issues_addressed: int, 
                                     issues_introduced: int) -> float:
        """Calculate overall effectiveness score (0.0 to 1.0)"""
        
        # Base score from content change (more change = potentially better)
        change_score = 1.0 - content_similarity
        
        # Validation improvement bonus
        validation_score = 1.0 if validation_improved else 0.0
        
        # Issues resolution score
        if issues_addressed > 0:
            resolution_score = min(1.0, issues_addressed / 5.0)  # Cap at 5 issues
        else:
            resolution_score = 0.0
            
        # Penalty for new issues
        penalty = min(0.5, issues_introduced / 10.0)  # Max 50% penalty
        
        # Weighted combination
        effectiveness = (
            change_score * 0.2 +      # 20% weight on content change
            validation_score * 0.4 +  # 40% weight on validation improvement  
            resolution_score * 0.4     # 40% weight on issue resolution
        ) - penalty
        
        return max(0.0, min(1.0, effectiveness))
    
    def _determine_recommendation(self, is_effective: bool, effectiveness_score: float,
                                content_similarity: float, validation_improved: bool,
                                iteration_count: int) -> Tuple[str, str]:
        """Determine what action to take next"""
        
        if is_effective and validation_improved:
            return "CONTINUE", f"Editorial feedback was effective (score: {effectiveness_score:.2f}). Validation improved."
        
        if iteration_count >= 3:
            return "ESCALATE", f"Reached max iterations ({iteration_count}). Manual review required."
        
        if content_similarity > 0.95:
            return "REGENERATE_FEEDBACK", f"Minimal content change (similarity: {content_similarity:.2f}). Editorial feedback may be too generic."
        
        if not validation_improved and effectiveness_score < 0.3:
            return "RESET_APPROACH", f"Editorial feedback ineffective (score: {effectiveness_score:.2f}). Try different editorial strategy."
        
        if effectiveness_score < 0.5:
            return "REFINE_FEEDBACK", f"Moderate effectiveness (score: {effectiveness_score:.2f}). Refine editorial approach."
        
        return "RETRY_ONCE", f"Borderline effectiveness (score: {effectiveness_score:.2f}). One more attempt recommended."
    
    def _log_effectiveness_analysis(self, patent_id: str, analysis: EditorialEffectivenessAnalysis):
        """Log effectiveness analysis for monitoring"""
        log_file = f"output/{patent_id}_editorial_effectiveness_log.md"
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n## Editorial Effectiveness Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**Effectiveness Score:** {analysis.effectiveness_score:.2f}\n")
                f.write(f"**Content Similarity:** {analysis.content_similarity:.2f}\n")
                f.write(f"**Validation Improved:** {analysis.validation_improvement}\n")
                f.write(f"**Issues Addressed:** {analysis.issues_addressed}\n")
                f.write(f"**New Issues:** {analysis.new_issues_introduced}\n")
                f.write(f"**Recommended Action:** {analysis.recommended_action}\n")
                f.write(f"**Reasoning:** {analysis.reasoning}\n")
                f.write("---\n")
                
        except Exception as e:
            logger.warning(f"Could not log effectiveness analysis for {patent_id}: {e}")
    
    def _generate_action_plan(self, analysis: EditorialEffectivenessAnalysis, 
                            iteration_count: int) -> Dict[str, Any]:
        """Generate specific action plan based on analysis"""
        
        action_plan = {
            "primary_action": analysis.recommended_action,
            "reasoning": analysis.reasoning,
            "effectiveness_score": analysis.effectiveness_score,
            "should_continue_iterations": False,
            "should_escalate": False,
            "should_change_strategy": False,
            "specific_recommendations": []
        }
        
        if analysis.recommended_action == "CONTINUE":
            action_plan["should_continue_iterations"] = True
            action_plan["specific_recommendations"] = [
                "Editorial feedback was effective",
                "Continue with current editorial approach",
                "Monitor for continued improvement"
            ]
            
        elif analysis.recommended_action == "ESCALATE":
            action_plan["should_escalate"] = True
            action_plan["specific_recommendations"] = [
                "Manual review required - automated iterations ineffective",
                "Consider human editorial intervention",
                "Review editorial feedback quality and specificity"
            ]
            
        elif analysis.recommended_action == "REGENERATE_FEEDBACK":
            action_plan["should_change_strategy"] = True
            action_plan["specific_recommendations"] = [
                "Editorial feedback too generic - no meaningful changes produced",
                "Request more specific, actionable feedback",
                "Focus on concrete textual alterations",
                "Avoid high-level suggestions"
            ]
            
        elif analysis.recommended_action == "RESET_APPROACH":
            action_plan["should_change_strategy"] = True
            action_plan["specific_recommendations"] = [
                "Current editorial approach ineffective",
                "Try different editorial strategy (different agent/model)",
                "Focus on specific validation issues",
                "Consider regenerating base document instead of editing"
            ]
            
        return action_plan
    
    def _format_effectiveness_report(self, analysis: EditorialEffectivenessAnalysis,
                                   action_plan: Dict[str, Any]) -> str:
        """Format the effectiveness analysis report"""
        
        return f"""
EDITORIAL FEEDBACK EFFECTIVENESS ANALYSIS
=========================================

📊 EFFECTIVENESS METRICS:
========================
Overall Effectiveness Score: {analysis.effectiveness_score:.2f}/1.0
Content Similarity: {analysis.content_similarity:.2f} (lower = more change)
Validation Improvement: {'✅ YES' if analysis.validation_improvement else '❌ NO'}
Issues Addressed: {analysis.issues_addressed}
New Issues Introduced: {analysis.new_issues_introduced}

🎯 RECOMMENDATION:
==================
Primary Action: {analysis.recommended_action}
Reasoning: {analysis.reasoning}

📋 ACTION PLAN:
===============
Should Continue Iterations: {'✅ YES' if action_plan['should_continue_iterations'] else '❌ NO'}
Should Escalate: {'⚠️ YES' if action_plan['should_escalate'] else '✅ NO'}
Should Change Strategy: {'⚠️ YES' if action_plan['should_change_strategy'] else '✅ NO'}

SPECIFIC RECOMMENDATIONS:
{chr(10).join(f'• {rec}' for rec in action_plan['specific_recommendations'])}

💡 NEXT STEPS:
==============
{self._generate_next_steps(analysis.recommended_action)}

EFFECTIVENESS ANALYSIS COMPLETE
==============================
"""
    
    def _generate_next_steps(self, recommended_action: str) -> str:
        """Generate specific next steps based on recommendation"""
        
        next_steps = {
            "CONTINUE": "✅ Proceed with next editorial iteration using current approach",
            "ESCALATE": "🚨 Stop automated iterations. Require human review and intervention",
            "REGENERATE_FEEDBACK": "🔄 Request new, more specific editorial feedback with concrete alterations",
            "RESET_APPROACH": "🔄 Try different editorial strategy or regenerate base document",
            "REFINE_FEEDBACK": "🔧 Modify editorial approach to be more targeted and specific",
            "RETRY_ONCE": "⚠️ One more attempt with current approach, then escalate"
        }
        
        return next_steps.get(recommended_action, "❓ Unknown recommendation - manual review required")
    
    def _generate_error_response(self, patent_id: str, error_message: str) -> str:
        """Generate error response when analysis fails"""
        
        return f"""
EDITORIAL EFFECTIVENESS ANALYSIS ERROR
=====================================

Patent ID: {patent_id}
Error: {error_message}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🚨 FALLBACK RECOMMENDATION:
===========================
Due to analysis error, recommend MANUAL REVIEW to prevent potential API waste.

ERROR ANALYSIS REQUIRED - HUMAN INTERVENTION NEEDED
==================================================
""" 