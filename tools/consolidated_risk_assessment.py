# ConsolidatedRiskAssessmentTool and dependencies will be moved here. 

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List
from crewai.tools import BaseTool
from pydantic import BaseModel, validator
import logging

# Import from core modules
from core.validation import validate_patent_dict

class ConsolidatedRiskAssessmentInput(BaseModel):
    patent_id: str
    title: str
    prior_art_analysis: str = ""
    academic_analysis: str = ""
    overlap_analysis: str = ""
    vector_analysis: str = ""
    final_review: str = ""

    @validator('patent_id', 'title')
    def required_fields_must_not_be_empty(cls, v):
        if not v or (isinstance(v, str) and not v.strip()):
            raise ValueError('Required field must not be empty')
        return v

class ConsolidatedRiskAssessmentTool(BaseTool):
    name: str = "consolidated_risk_assessment_tool"
    description: str = "Generate comprehensive risk assessment by analyzing prior art, academic literature, overlap analysis, and vector analysis results."
    args_schema: type[BaseModel] = ConsolidatedRiskAssessmentInput

    def __init__(self):
        super().__init__()

    def _run(self, patent_id: str, title: str, prior_art_analysis: str = "", 
             academic_analysis: str = "", overlap_analysis: str = "", 
             vector_analysis: str = "", final_review: str = "", 
             refined_claims: str = "", legal_review: str = "") -> str:
        try:
            # Handle potential None values or empty strings
            patent_id = patent_id or "UNKNOWN"
            title = title or "Untitled Patent"
            prior_art_analysis = prior_art_analysis or "No prior art analysis provided"
            academic_analysis = academic_analysis or "No academic analysis provided"
            overlap_analysis = overlap_analysis or "No overlap analysis provided"
            vector_analysis = vector_analysis or "No vector analysis provided"
            final_review = final_review or "No final review provided"
            refined_claims = refined_claims or "No refined claims provided"
            legal_review = legal_review or "No legal review provided"
            
            report = f"""
CONSOLIDATED RISK ASSESSMENT & FINAL SUMMARY
============================================

Patent ID: {patent_id}
Title: {title}
Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Report Type: Comprehensive Risk Consolidation

EXECUTIVE SUMMARY
=================

This consolidated assessment provides a holistic view of all identified risks, 
academic literature findings, and strategic recommendations for patent filing 
and commercialization.

OVERALL RISK PROFILE
===================

"""
            
            # Calculate overall risk metrics
            risk_metrics = self._calculate_risk_metrics(prior_art_analysis, academic_analysis, 
                                                       overlap_analysis, vector_analysis)
            
            report += f"""
Risk Assessment Summary:
- Overall Patent Risk Level: {risk_metrics['overall_patent_risk']}
- Academic Literature Risk: {risk_metrics['academic_risk']}
- Term Overlap Risk: {risk_metrics['overlap_risk']}
- Vector Analysis Risk: {risk_metrics['vector_risk']}
- Filing Readiness Score: {risk_metrics['filing_readiness']}/10

Risk Distribution:
- High Risk Items: {risk_metrics['high_risk_count']}
- Medium Risk Items: {risk_metrics['medium_risk_count']}
- Low Risk Items: {risk_metrics['low_risk_count']}

PRIOR ART RISK ANALYSIS
=======================

"""
            
            if prior_art_analysis:
                report += self._extract_prior_art_summary(prior_art_analysis)
            else:
                report += "⚠️ Prior art analysis not performed - critical risk assessment missing\n"
            
            report += f"""
ACADEMIC LITERATURE RISK ANALYSIS
=================================

"""
            
            if academic_analysis:
                report += self._extract_academic_summary(academic_analysis)
            else:
                report += "⚠️ Academic literature analysis not performed - research gap assessment missing\n"
            
            report += f"""
TERM OVERLAP RISK ANALYSIS
==========================

"""
            
            if overlap_analysis:
                report += self._extract_overlap_summary(overlap_analysis)
            else:
                report += "⚠️ Term overlap analysis not performed - claim differentiation assessment missing\n"
            
            report += f"""
VECTOR-BASED SEMANTIC RISK ANALYSIS
===================================

"""
            
            if vector_analysis:
                report += self._extract_vector_summary(vector_analysis)
            else:
                report += "ℹ️ Vector analysis not performed - using term-based analysis only\n"
            
            report += f"""
QUALITY ASSESSMENT
==================

"""
            
            if final_review:
                report += self._extract_quality_summary(final_review)
            else:
                report += "⚠️ Final quality review not performed - comprehensive assessment missing\n"
            
            report += f"""
CRITICAL FINDINGS & RISKS
=========================

"""
            
            critical_findings = self._identify_critical_findings(prior_art_analysis, academic_analysis, 
                                                               overlap_analysis, vector_analysis)
            
            if critical_findings['high_priority']:
                report += "🚨 HIGH PRIORITY RISKS:\n"
                for finding in critical_findings['high_priority']:
                    report += f"- {finding}\n"
                report += "\n"
            
            if critical_findings['medium_priority']:
                report += "⚠️ MEDIUM PRIORITY CONCERNS:\n"
                for finding in critical_findings['medium_priority']:
                    report += f"- {finding}\n"
                report += "\n"
            
            if critical_findings['low_priority']:
                report += "ℹ️ LOW PRIORITY OBSERVATIONS:\n"
                for finding in critical_findings['low_priority']:
                    report += f"- {finding}\n"
                report += "\n"
            
            report += f"""
STRATEGIC RECOMMENDATIONS
=========================

IMMEDIATE ACTIONS (Next 30 Days):
"""
            
            immediate_actions = self._generate_immediate_actions(risk_metrics, critical_findings)
            for action in immediate_actions:
                report += f"- {action}\n"
            
            report += f"""
SHORT-TERM STRATEGY (Next 90 Days):
"""
            
            short_term = self._generate_short_term_strategy(risk_metrics, critical_findings)
            for item in short_term:
                report += f"- {item}\n"
            
            report += f"""
LONG-TERM STRATEGY (Next 12 Months):
"""
            
            long_term = self._generate_long_term_strategy(risk_metrics, critical_findings)
            for item in long_term:
                report += f"- {item}\n"
            
            report += f"""
COMPETITIVE INTELLIGENCE SUMMARY
================================

Key Competitors Identified:
"""
            
            competitors = self._extract_competitor_intelligence(prior_art_analysis, academic_analysis)
            for competitor in competitors:
                report += f"- {competitor}\n"
            
            report += f"""
ACADEMIC LANDSCAPE SUMMARY
==========================

"""
            
            research_trends = self._extract_research_trends(academic_analysis)
            for trend in research_trends:
                report += f"- {trend}\n"
            
            report += f"""
FILING STRATEGY RECOMMENDATION
==============================

{self._generate_filing_strategy(risk_metrics, critical_findings)}

COMMERCIAL VALUE ASSESSMENT
===========================

{self._assess_commercial_value(risk_metrics, critical_findings)}

FINAL RECOMMENDATION
====================

{self._generate_final_recommendation(risk_metrics, critical_findings)}

ASSESSMENT METRICS
==================

- Confidence Level: {self._calculate_confidence_level(risk_metrics)}/10
- Priority Level: {self._get_priority_level(risk_metrics)}
- Assessment Completeness: {'Complete' if all([prior_art_analysis, academic_analysis, overlap_analysis]) else 'Partial'}

END OF CONSOLIDATED RISK ASSESSMENT
==================================
"""
            
            return report
            
        except Exception as e:
            error_msg = f"""
ERROR IN CONSOLIDATED RISK ASSESSMENT TOOL
=========================================

Patent ID: {patent_id}
Error Type: {type(e).__name__}
Error Message: {str(e)}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The tool encountered an unexpected error during consolidated risk assessment. This may be due to:
- Invalid input data format
- Missing required analysis components
- Text processing errors
- Internal calculation errors

Please check the input parameters and try again. If the error persists, 
contact the system administrator.

Input Parameters Received:
- patent_id: {patent_id}
- title: {title[:100]}{'...' if len(title) > 100 else ''}
- prior_art_analysis length: {len(prior_art_analysis) if prior_art_analysis else 0} characters
- academic_analysis length: {len(academic_analysis) if academic_analysis else 0} characters
- overlap_analysis length: {len(overlap_analysis) if overlap_analysis else 0} characters
- vector_analysis length: {len(vector_analysis) if vector_analysis else 0} characters
- final_review length: {len(final_review) if final_review else 0} characters
- refined_claims length: {len(refined_claims) if refined_claims else 0} characters
- legal_review length: {len(legal_review) if legal_review else 0} characters
"""
            logging.error(f"ConsolidatedRiskAssessmentTool error: {e}")
            return error_msg
    
    def _calculate_risk_metrics(self, prior_art: str, academic: str, overlap: str, vector: str) -> Dict:
        """Calculate comprehensive risk metrics from all analyses"""
        metrics = {
            'overall_patent_risk': 'UNKNOWN',
            'academic_risk': 'UNKNOWN',
            'overlap_risk': 'UNKNOWN',
            'vector_risk': 'UNKNOWN',
            'filing_readiness': 0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0
        }
        
        # Prior art risk assessment
        if prior_art:
            if 'HIGH' in prior_art.upper() and 'RISK' in prior_art.upper():
                metrics['overall_patent_risk'] = 'HIGH'
                metrics['high_risk_count'] += 1
            elif 'MEDIUM' in prior_art.upper() and 'RISK' in prior_art.upper():
                metrics['overall_patent_risk'] = 'MEDIUM'
                metrics['medium_risk_count'] += 1
            elif 'LOW' in prior_art.upper() and 'RISK' in prior_art.upper():
                metrics['overall_patent_risk'] = 'LOW'
                metrics['low_risk_count'] += 1
        
        # Academic risk assessment
        if academic:
            if 'high relevance' in academic.lower() and len(re.findall(r'high relevance.*?papers?', academic.lower())) > 3:
                metrics['academic_risk'] = 'HIGH'
                metrics['high_risk_count'] += 1
            elif 'medium relevance' in academic.lower():
                metrics['academic_risk'] = 'MEDIUM'
                metrics['medium_risk_count'] += 1
            else:
                metrics['academic_risk'] = 'LOW'
                metrics['low_risk_count'] += 1
        
        # Overlap risk assessment
        if overlap:
            if 'high risk' in overlap.lower():
                metrics['overlap_risk'] = 'HIGH'
                metrics['high_risk_count'] += 1
            elif 'medium risk' in overlap.lower():
                metrics['overlap_risk'] = 'MEDIUM'
                metrics['medium_risk_count'] += 1
            else:
                metrics['overlap_risk'] = 'LOW'
                metrics['low_risk_count'] += 1
        
        # Vector risk assessment
        if vector:
            if 'high risk' in vector.lower():
                metrics['vector_risk'] = 'HIGH'
                metrics['high_risk_count'] += 1
            elif 'medium risk' in vector.lower():
                metrics['vector_risk'] = 'MEDIUM'
                metrics['medium_risk_count'] += 1
            else:
                metrics['vector_risk'] = 'LOW'
                metrics['low_risk_count'] += 1
        
        # Calculate filing readiness score
        readiness_score = 0
        if prior_art: readiness_score += 2
        if academic: readiness_score += 2
        if overlap: readiness_score += 2
        if vector: readiness_score += 1
        if metrics['high_risk_count'] == 0: readiness_score += 3
        elif metrics['high_risk_count'] <= 1: readiness_score += 1
        
        metrics['filing_readiness'] = min(10, readiness_score)
        
        return metrics
    
    def _extract_prior_art_summary(self, prior_art: str) -> str:
        """Extract key information from prior art analysis"""
        summary = ""
        
        # Extract novelty score
        novelty_match = re.search(r'novelty.*?(\d+\.?\d*)/10', prior_art, re.IGNORECASE)
        if novelty_match:
            summary += f"Novelty Score: {novelty_match.group(1)}/10\n"
        
        # Extract risk level
        if 'HIGH' in prior_art.upper() and 'RISK' in prior_art.upper():
            summary += "Risk Level: HIGH - Significant prior art conflicts identified\n"
        elif 'MEDIUM' in prior_art.upper() and 'RISK' in prior_art.upper():
            summary += "Risk Level: MEDIUM - Some prior art concerns, manageable\n"
        elif 'LOW' in prior_art.upper() and 'RISK' in prior_art.upper():
            summary += "Risk Level: LOW - Limited prior art conflicts\n"
        
        # Extract key patents
        patent_matches = re.findall(r'(\w+\s+\d+,\d+,\d+).*?"([^"]+)"', prior_art)
        if patent_matches:
            summary += f"Key Prior Art Patents: {len(patent_matches)} identified\n"
            for i, (patent_num, title) in enumerate(patent_matches[:3], 1):
                summary += f"  {i}. {patent_num} - {title[:50]}...\n"
        
        return summary
    
    def _extract_academic_summary(self, academic: str) -> str:
        """Extract key information from academic analysis"""
        summary = ""
        
        # Extract paper counts
        high_match = re.search(r'high relevance.*?(\d+)', academic, re.IGNORECASE)
        medium_match = re.search(r'medium relevance.*?(\d+)', academic, re.IGNORECASE)
        
        if high_match:
            summary += f"High Relevance Papers: {high_match.group(1)}\n"
        if medium_match:
            summary += f"Medium Relevance Papers: {medium_match.group(1)}\n"
        
        # Extract novelty assessment
        novelty_match = re.search(r'academic novelty.*?(\d+\.?\d*)/10', academic, re.IGNORECASE)
        if novelty_match:
            summary += f"Academic Novelty Score: {novelty_match.group(1)}/10\n"
        
        # Extract research trends
        if 'research gap' in academic.lower():
            summary += "Research Gap: Identified - opportunity for academic leadership\n"
        
        return summary
    
    def _extract_overlap_summary(self, overlap: str) -> str:
        """Extract key information from overlap analysis"""
        summary = ""
        
        # Extract overlap counts
        high_match = re.search(r'high risk.*?(\d+)', overlap, re.IGNORECASE)
        medium_match = re.search(r'medium risk.*?(\d+)', overlap, re.IGNORECASE)
        
        if high_match:
            summary += f"High Risk Overlaps: {high_match.group(1)}\n"
        if medium_match:
            summary += f"Medium Risk Overlaps: {medium_match.group(1)}\n"
        
        # Extract risk level
        if 'HIGH RISK' in overlap.upper():
            summary += "Overall Risk: HIGH - Immediate claim refinement needed\n"
        elif 'MEDIUM RISK' in overlap.upper():
            summary += "Overall Risk: MEDIUM - Some claim modifications recommended\n"
        else:
            summary += "Overall Risk: LOW - Claims appear well-differentiated\n"
        
        return summary
    
    def _extract_vector_summary(self, vector: str) -> str:
        """Extract key information from vector analysis"""
        summary = ""
        
        # Extract risk score
        risk_match = re.search(r'risk score.*?(\d+\.?\d*)', vector, re.IGNORECASE)
        if risk_match:
            summary += f"Vector Risk Score: {risk_match.group(1)}\n"
        
        # Extract risk level
        if 'HIGH RISK' in vector.upper():
            summary += "Semantic Risk: HIGH - Significant semantic overlap detected\n"
        elif 'MEDIUM RISK' in vector.upper():
            summary += "Semantic Risk: MEDIUM - Moderate semantic overlap\n"
        else:
            summary += "Semantic Risk: LOW - Limited semantic overlap\n"
        
        return summary
    
    def _extract_quality_summary(self, final_review: str) -> str:
        """Extract key information from final review"""
        summary = ""
        
        # Extract quality score
        score_match = re.search(r'quality score.*?(\d+)/10', final_review, re.IGNORECASE)
        if score_match:
            summary += f"Quality Score: {score_match.group(1)}/10\n"
        
        # Extract classification
        if 'EXCELLENT' in final_review.upper():
            summary += "Quality Classification: EXCELLENT - Ready for filing\n"
        elif 'GOOD' in final_review.upper():
            summary += "Quality Classification: GOOD - Minor improvements needed\n"
        elif 'FAIR' in final_review.upper():
            summary += "Quality Classification: FAIR - Significant improvements needed\n"
        else:
            summary += "Quality Classification: POOR - Major improvements required\n"
        
        return summary
    
    def _identify_critical_findings(self, prior_art: str, academic: str, overlap: str, vector: str) -> Dict:
        """Identify critical findings across all analyses"""
        findings = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': []
        }
        
        # High priority findings
        if prior_art and 'HIGH' in prior_art.upper() and 'RISK' in prior_art.upper():
            findings['high_priority'].append("High prior art risk - significant conflicts identified")
        
        if overlap and 'HIGH RISK' in overlap.upper():
            findings['high_priority'].append("High term overlap risk - immediate claim refinement needed")
        
        if vector and 'HIGH RISK' in vector.upper():
            findings['high_priority'].append("High semantic overlap risk - major claim restructuring may be required")
        
        if academic and len(re.findall(r'high relevance.*?papers?', academic.lower())) > 5:
            findings['high_priority'].append("Extensive academic literature - limited novelty window")
        
        # Medium priority findings
        if prior_art and 'MEDIUM' in prior_art.upper() and 'RISK' in prior_art.upper():
            findings['medium_priority'].append("Medium prior art risk - some conflicts need addressing")
        
        if overlap and 'MEDIUM RISK' in overlap.upper():
            findings['medium_priority'].append("Medium term overlap - claim modifications recommended")
        
        if academic and len(re.findall(r'medium relevance.*?papers?', academic.lower())) > 3:
            findings['medium_priority'].append("Moderate academic literature - review for differentiation opportunities")
        
        # Low priority findings
        if not prior_art:
            findings['low_priority'].append("Prior art analysis not performed")
        
        if not academic:
            findings['low_priority'].append("Academic literature analysis not performed")
        
        if not overlap:
            findings['low_priority'].append("Term overlap analysis not performed")
        
        return findings
    
    def _generate_immediate_actions(self, risk_metrics: Dict, critical_findings: Dict) -> List[str]:
        """Generate immediate action items"""
        actions = []
        
        if risk_metrics['high_risk_count'] > 0:
            actions.append("Address high-risk findings before filing")
        
        if not any('prior art' in finding.lower() for finding in critical_findings['low_priority']):
            actions.append("Conduct comprehensive prior art search")
        
        if risk_metrics['overall_patent_risk'] == 'HIGH':
            actions.append("Refine claims to address prior art conflicts")
        
        if risk_metrics['overlap_risk'] == 'HIGH':
            actions.append("Restructure claims to avoid term overlaps")
        
        if risk_metrics['filing_readiness'] < 7:
            actions.append("Complete missing analyses before filing")
        
        if not actions:
            actions.append("Proceed with filing preparation")
        
        return actions
    
    def _generate_short_term_strategy(self, risk_metrics: Dict, critical_findings: Dict) -> List[str]:
        """Generate short-term strategy recommendations"""
        strategy = []
        
        if risk_metrics['academic_risk'] == 'HIGH':
            strategy.append("Monitor academic literature for new publications")
        
        if risk_metrics['overall_patent_risk'] == 'MEDIUM':
            strategy.append("Develop claim amendment strategy for potential office actions")
        
        strategy.append("Prepare prosecution timeline and budget")
        strategy.append("Identify potential licensing partners")
        
        return strategy
    
    def _generate_long_term_strategy(self, risk_metrics: Dict, critical_findings: Dict) -> List[str]:
        """Generate long-term strategy recommendations"""
        strategy = []
        
        strategy.append("Plan continuation application strategy")
        strategy.append("Develop international filing strategy (EP, CN, JP)")
        strategy.append("Consider portfolio expansion opportunities")
        strategy.append("Monitor competitive landscape for new entrants")
        
        return strategy
    
    def _extract_competitor_intelligence(self, prior_art: str, academic: str) -> List[str]:
        """Extract competitor intelligence from analyses"""
        competitors = []
        
        if prior_art:
            # Extract assignee names from prior art
            assignee_matches = re.findall(r'assignee.*?:\s*([^\n]+)', prior_art, re.IGNORECASE)
            competitors.extend([assignee.strip() for assignee in assignee_matches[:5]])
        
        if academic:
            # Extract author affiliations from academic papers
            author_matches = re.findall(r'authors.*?at\s+([^\n]+)', academic, re.IGNORECASE)
            competitors.extend([author.strip() for author in author_matches[:3]])
        
        return list(set(competitors))  # Remove duplicates
    
    def _extract_research_trends(self, academic: str) -> List[str]:
        """Extract research trends from academic analysis"""
        trends = []
        
        if academic:
            if 'AI/ML' in academic:
                trends.append("Strong AI/ML research activity in this domain")
            if '2023+' in academic:
                trends.append("Recent research activity indicates growing interest")
            if 'multi-author' in academic:
                trends.append("Collaborative research suggests field maturity")
        
        return trends
    
    def _generate_filing_strategy(self, risk_metrics: Dict, critical_findings: Dict) -> str:
        """Generate filing strategy recommendations"""
        if risk_metrics['filing_readiness'] >= 8 and risk_metrics['high_risk_count'] == 0:
            return "PROCEED WITH FILING - All analyses complete, low risk profile"
        elif risk_metrics['filing_readiness'] >= 6 and risk_metrics['high_risk_count'] <= 1:
            return "PROCEED WITH CAUTION - Address identified risks before filing"
        else:
            return "DELAY FILING - Complete missing analyses and address high-risk findings"
    
    def _assess_commercial_value(self, risk_metrics: Dict, critical_findings: Dict) -> str:
        """Assess commercial value based on risk profile"""
        if risk_metrics['high_risk_count'] == 0 and risk_metrics['filing_readiness'] >= 8:
            return "HIGH COMMERCIAL VALUE - Strong patent position with broad claims"
        elif risk_metrics['high_risk_count'] <= 1:
            return "MODERATE COMMERCIAL VALUE - Good position with some limitations"
        else:
            return "LIMITED COMMERCIAL VALUE - Significant risks may limit enforcement"
    
    def _generate_final_recommendation(self, risk_metrics: Dict, critical_findings: Dict) -> str:
        """Generate final recommendation"""
        if risk_metrics['filing_readiness'] >= 8 and risk_metrics['high_risk_count'] == 0:
            return "✅ PROCEED WITH FILING - Patent is ready for submission"
        elif risk_metrics['filing_readiness'] >= 6:
            return "⚠️ PROCEED WITH IMPROVEMENTS - Address identified issues before filing"
        else:
            return "❌ COMPLETE ANALYSIS FIRST - Insufficient data for filing decision"
    
    def _calculate_confidence_level(self, risk_metrics: Dict) -> int:
        """Calculate confidence level based on completeness of analysis"""
        confidence = 50  # Base confidence
        
        if risk_metrics['filing_readiness'] >= 8:
            confidence += 30
        elif risk_metrics['filing_readiness'] >= 6:
            confidence += 20
        
        if risk_metrics['high_risk_count'] == 0:
            confidence += 20
        
        return min(95, confidence)
    
    def _get_priority_level(self, risk_metrics: Dict) -> str:
        """Get priority level based on risk metrics"""
        if risk_metrics['high_risk_count'] > 0:
            return "HIGH"
        elif risk_metrics['medium_risk_count'] > 2:
            return "MEDIUM"
        else:
            return "LOW" 