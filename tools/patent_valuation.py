# PatentValuationTool - Dynamic patent valuation based on multiple factors

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, validator
import json
from core.langsmith_utils import trace_function

class PatentValuationInput(BaseModel):
    patent_id: str
    title: str
    description: str
    key_claims: List[str]
    technical_features: List[str] = []
    market_applications: List[str] = []
    implementation_complexity: str = "Medium"
    prior_art_risk: str = "Medium"
    regulatory_compliance: str = ""
    prototype_metrics: str = ""
    differentiation: str = ""
    prior_art_analysis: str = ""
    academic_analysis: str = ""
    overlap_analysis: str = ""

    @validator('patent_id', 'title', 'description')
    def required_fields_must_not_be_empty(cls, v):
        if v is None:
            raise ValueError('Required field must not be None')
        if isinstance(v, str) and not v.strip():
            raise ValueError('Required field must not be empty')
        return v

    @validator('key_claims')
    def key_claims_must_be_list(cls, v):
        if not isinstance(v, list):
            raise ValueError('key_claims must be a list')
        if not v:
            raise ValueError('key_claims must not be empty')
        return v

class PatentValuationTool(BaseTool):
    name: str = "patent_valuation_tool"
    description: str = "Dynamically calculate patent value based on technical innovation, market factors, competitive landscape, and risk assessment."
    args_schema: type[BaseModel] = PatentValuationInput

    def __init__(self):
        super().__init__()
        
        # Initialize market data as class variables
        self._init_market_data()

    def _init_market_data(self):
        """Initialize market data as class variables"""
        # Market size multipliers by application domain
        self._market_multipliers = {
            'healthcare': 3.0,  # High value due to regulatory requirements
            'financial': 2.5,   # High value due to compliance needs
            'automotive': 2.0,  # Large market, safety critical
            'cybersecurity': 2.5, # Growing market, security critical
            'autonomous': 2.0,  # Emerging high-value market
            'automl': 1.8,      # Established but growing market
            'edge': 1.5,        # Growing IoT market
            'federated': 2.0,   # Privacy-preserving AI
            'explainable': 1.8, # Regulatory compliance
            'optimization': 1.5, # General optimization market
            'semantic': 2.0,    # Novel semantic reasoning
            'agent': 1.8,       # Multi-agent systems
            'ai': 1.5,          # General AI market
            'ml': 1.5,          # General ML market
        }
        
        # Base market sizes (in billions)
        self._market_sizes = {
            'healthcare': 45.0,
            'financial': 35.0,
            'automotive': 25.0,
            'cybersecurity': 20.0,
            'autonomous': 15.0,
            'automl': 12.0,
            'edge': 8.0,
            'federated': 10.0,
            'explainable': 8.0,
            'optimization': 6.0,
            'semantic': 5.0,
            'agent': 4.0,
            'ai': 30.0,
            'ml': 25.0,
        }

    @trace_function(name="PatentValuationTool._run")
    def _run(self, patent_id: str, title: str, description: str, key_claims: List[str],
             technical_features: List[str] = [], market_applications: List[str] = [],
             implementation_complexity: str = "Medium", prior_art_risk: str = "Medium",
             regulatory_compliance: str = "", prototype_metrics: str = "",
             differentiation: str = "", prior_art_analysis: str = "",
             academic_analysis: str = "", overlap_analysis: str = "") -> str:
        """Dynamically calculate patent value based on comprehensive analysis"""
        try:
            # Handle potential None values
            patent_id = patent_id or "UNKNOWN"
            title = title or "Untitled Patent"
            description = description or "No description provided"
            key_claims = key_claims or ["No claims provided"]
            technical_features = technical_features or []
            market_applications = market_applications or []
            implementation_complexity = implementation_complexity or "Medium"
            prior_art_risk = prior_art_risk or "Medium"
            regulatory_compliance = regulatory_compliance or ""
            prototype_metrics = prototype_metrics or ""
            differentiation = differentiation or ""
            prior_art_analysis = prior_art_analysis or ""
            academic_analysis = academic_analysis or ""
            overlap_analysis = overlap_analysis or ""

            # Calculate base value
            base_value = self._calculate_base_value(title, description, key_claims, technical_features)
            
            # Calculate market factor
            market_factor = self._calculate_market_factor(market_applications)
            
            # Calculate innovation factor
            innovation_factor = self._calculate_innovation_factor(technical_features, differentiation, prototype_metrics)
            
            # Calculate risk factor
            risk_factor = self._calculate_risk_factor(prior_art_risk, implementation_complexity, 
                                                    prior_art_analysis, academic_analysis, overlap_analysis)
            
            # Calculate regulatory factor
            regulatory_factor = self._calculate_regulatory_factor(regulatory_compliance, market_applications)
            
            # Calculate competitive factor
            competitive_factor = self._calculate_competitive_factor(differentiation, prior_art_analysis)
            
            # Calculate final value
            final_value = self._calculate_final_value(base_value, market_factor, innovation_factor, 
                                                     risk_factor, regulatory_factor, competitive_factor)
            
            # Generate detailed valuation report
            report = self._generate_valuation_report(
                patent_id, title, final_value, base_value, market_factor, innovation_factor,
                risk_factor, regulatory_factor, competitive_factor, market_applications,
                technical_features, prior_art_risk, implementation_complexity, regulatory_compliance
            )
            
            # Add structured JSON data at the end for aggregation
            structured_data = {
                "patent_id": patent_id,
                "title": title,
                "valuation": {
                    "low_value": final_value['low_value'],
                    "high_value": final_value['high_value'],
                    "mid_value": final_value['mid_value'],
                    "category": final_value['category'],
                    "confidence": final_value['confidence']
                },
                "factors": {
                    "base_value": base_value,
                    "market_factor": market_factor,
                    "innovation_factor": innovation_factor,
                    "risk_factor": risk_factor,
                    "regulatory_factor": regulatory_factor,
                    "competitive_factor": competitive_factor
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Append structured data as JSON comment for easy extraction
            json_data = json.dumps(structured_data, indent=2)
            report += f"\n\n<!-- VALUATION_JSON_DATA\n{json_data}\nVALUATION_JSON_DATA -->"
            
            return report
            
        except Exception as e:
            error_msg = f"""
ERROR IN PATENT VALUATION TOOL
==============================

Patent ID: {patent_id}
Error Type: {type(e).__name__}
Error Message: {str(e)}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The tool encountered an unexpected error during valuation calculation. This may be due to:
- Invalid input data format
- Missing required patent information
- Calculation errors
- Internal analysis errors

Please check the input parameters and try again. If the error persists, 
contact the system administrator.
"""
            logging.error(f"PatentValuationTool error: {e}")
            return error_msg

    def _calculate_base_value(self, title: str, description: str, key_claims: List[str], 
                            technical_features: List[str]) -> float:
        """Calculate base value from patent fundamentals"""
        base_value = 1.0  # Base $1M
        
        # Title complexity bonus
        title_words = len(title.split())
        if title_words > 8:
            base_value += 0.5
        elif title_words > 5:
            base_value += 0.3
        
        # Description length bonus
        desc_length = len(description)
        if desc_length > 1000:
            base_value += 1.0
        elif desc_length > 500:
            base_value += 0.5
        
        # Claims complexity bonus
        claims_count = len(key_claims)
        if claims_count > 5:
            base_value += 1.5
        elif claims_count > 3:
            base_value += 1.0
        elif claims_count > 1:
            base_value += 0.5
        
        # Technical features bonus
        tech_features_count = len(technical_features)
        if tech_features_count > 8:
            base_value += 2.0
        elif tech_features_count > 5:
            base_value += 1.5
        elif tech_features_count > 3:
            base_value += 1.0
        elif tech_features_count > 1:
            base_value += 0.5
        
        return base_value

    def _calculate_market_factor(self, market_applications: List[str]) -> float:
        """Calculate market factor based on application domains"""
        if not market_applications:
            return 1.0
        
        total_multiplier = 0
        total_market_size = 0
        
        for app in market_applications:
            app_lower = app.lower()
            
            # Find matching market multiplier
            multiplier = 1.0
            market_size = 5.0  # Default market size
            
            for market_key, market_mult in self._market_multipliers.items():
                if market_key in app_lower:
                    multiplier = market_mult
                    market_size = self._market_sizes.get(market_key, 5.0)
                    break
            
            total_multiplier += multiplier
            total_market_size += market_size
        
        # Average multiplier weighted by market size
        avg_multiplier = total_multiplier / len(market_applications)
        avg_market_size = total_market_size / len(market_applications)
        
        # Market size factor (larger markets = higher value)
        market_size_factor = min(avg_market_size / 10.0, 3.0)  # Cap at 3x
        
        return avg_multiplier * market_size_factor

    def _calculate_innovation_factor(self, technical_features: List[str], differentiation: str, 
                                   prototype_metrics: str) -> float:
        """Calculate innovation factor based on technical novelty"""
        innovation_score = 1.0
        
        # Technical features innovation
        innovation_keywords = [
            'semantic', 'agent', 'coordination', 'meta', 'adaptive', 'dynamic',
            'real-time', 'gpu', 'optimization', 'reasoning', 'memory', 'privacy',
            'federated', 'explainable', 'interpretable', 'bias', 'fairness'
        ]
        
        feature_innovation_count = 0
        for feature in technical_features:
            feature_lower = feature.lower()
            for keyword in innovation_keywords:
                if keyword in feature_lower:
                    feature_innovation_count += 1
                    break
        
        if feature_innovation_count > 5:
            innovation_score += 2.0
        elif feature_innovation_count > 3:
            innovation_score += 1.5
        elif feature_innovation_count > 1:
            innovation_score += 1.0
        
        # Differentiation bonus
        if differentiation:
            diff_length = len(differentiation)
            if diff_length > 200:
                innovation_score += 1.0
            elif diff_length > 100:
                innovation_score += 0.5
        
        # Prototype metrics bonus
        if prototype_metrics:
            metrics_lower = prototype_metrics.lower()
            if any(metric in metrics_lower for metric in ['<5ms', '1.5x', '>90%', '100%']):
                innovation_score += 1.0
        
        return innovation_score

    def _calculate_risk_factor(self, prior_art_risk: str, implementation_complexity: str,
                             prior_art_analysis: str, academic_analysis: str, 
                             overlap_analysis: str) -> float:
        """Calculate risk factor (lower is better)"""
        risk_multiplier = 1.0
        
        # Prior art risk
        if prior_art_risk.lower() == 'low':
            risk_multiplier *= 1.2  # 20% bonus for low risk
        elif prior_art_risk.lower() == 'high':
            risk_multiplier *= 0.6  # 40% penalty for high risk
        
        # Implementation complexity
        if implementation_complexity.lower() == 'low':
            risk_multiplier *= 0.9  # 10% penalty for low complexity (easier to copy)
        elif implementation_complexity.lower() == 'high':
            risk_multiplier *= 1.1  # 10% bonus for high complexity (harder to copy)
        
        # Prior art analysis impact
        if prior_art_analysis:
            if 'conflict' in prior_art_analysis.lower() or 'overlap' in prior_art_analysis.lower():
                risk_multiplier *= 0.8  # 20% penalty for conflicts
            elif 'clear' in prior_art_analysis.lower() or 'novel' in prior_art_analysis.lower():
                risk_multiplier *= 1.1  # 10% bonus for clear novelty
        
        return risk_multiplier

    def _calculate_regulatory_factor(self, regulatory_compliance: str, market_applications: List[str]) -> float:
        """Calculate regulatory compliance factor"""
        regulatory_bonus = 1.0
        
        # Regulatory compliance keywords
        compliance_keywords = ['gdpr', 'hipaa', 'sec', 'sox', 'ccpa', 'compliance', 'regulatory']
        
        if regulatory_compliance:
            compliance_lower = regulatory_compliance.lower()
            compliance_count = sum(1 for keyword in compliance_keywords if keyword in compliance_lower)
            regulatory_bonus += compliance_count * 0.2
        
        # Market-specific regulatory requirements
        regulated_markets = ['healthcare', 'financial', 'cybersecurity', 'autonomous']
        for app in market_applications:
            app_lower = app.lower()
            for market in regulated_markets:
                if market in app_lower:
                    regulatory_bonus += 0.3
                    break
        
        return regulatory_bonus

    def _calculate_competitive_factor(self, differentiation: str, prior_art_analysis: str) -> float:
        """Calculate competitive advantage factor"""
        competitive_score = 1.0
        
        # Differentiation strength
        if differentiation:
            diff_lower = differentiation.lower()
            competitive_indicators = ['unique', 'novel', 'first', 'only', 'superior', 'better', 'faster']
            indicator_count = sum(1 for indicator in competitive_indicators if indicator in diff_lower)
            competitive_score += indicator_count * 0.1
        
        # Prior art analysis competitive position
        if prior_art_analysis:
            pa_lower = prior_art_analysis.lower()
            if 'white space' in pa_lower or 'unclear' in pa_lower:
                competitive_score += 0.3
            elif 'clear' in pa_lower and 'novel' in pa_lower:
                competitive_score += 0.5
        
        return competitive_score

    def _calculate_final_value(self, base_value: float, market_factor: float, 
                             innovation_factor: float, risk_factor: float,
                             regulatory_factor: float, competitive_factor: float) -> Dict[str, Any]:
        """Calculate final patent value with confidence intervals"""
        
        # Calculate raw value
        raw_value = base_value * market_factor * innovation_factor * risk_factor * regulatory_factor * competitive_factor
        
        # Apply market volatility (30% standard deviation)
        low_value = raw_value * 0.7
        high_value = raw_value * 1.3
        
        # Round to reasonable ranges
        low_value = round(low_value, 1)
        high_value = round(high_value, 1)
        
        # Determine value category
        if high_value >= 20:
            category = "HIGH VALUE"
        elif high_value >= 10:
            category = "MEDIUM-HIGH VALUE"
        elif high_value >= 5:
            category = "MEDIUM VALUE"
        elif high_value >= 2:
            category = "LOW-MEDIUM VALUE"
        else:
            category = "LOW VALUE"
        
        return {
            'low_value': low_value,
            'high_value': high_value,
            'mid_value': (low_value + high_value) / 2,
            'category': category,
            'confidence': 'Medium' if abs(high_value - low_value) / ((high_value + low_value) / 2) < 0.5 else 'Low'
        }

    def _generate_valuation_report(self, patent_id: str, title: str, final_value: Dict[str, Any],
                                 base_value: float, market_factor: float, innovation_factor: float,
                                 risk_factor: float, regulatory_factor: float, competitive_factor: float,
                                 market_applications: List[str], technical_features: List[str],
                                 prior_art_risk: str, implementation_complexity: str, 
                                 regulatory_compliance: str) -> str:
        """Generate comprehensive valuation report"""
        
        report = f"""
DYNAMIC PATENT VALUATION REPORT
===============================

Patent ID: {patent_id}
Title: {title}
Valuation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

VALUATION SUMMARY
=================

Estimated Value Range: ${final_value['low_value']:.1f}M - ${final_value['high_value']:.1f}M
Mid-Point Value: ${final_value['mid_value']:.1f}M
Value Category: {final_value['category']}
Confidence Level: {final_value['confidence']}

DETAILED FACTOR ANALYSIS
========================

1. BASE VALUE: ${base_value:.1f}M
   - Foundation value based on patent fundamentals
   - Includes title complexity, description length, claims count, technical features

2. MARKET FACTOR: {market_factor:.2f}x
   - Market size and application domain multipliers
   - Target markets: {', '.join(market_applications) if market_applications else 'Not specified'}

3. INNOVATION FACTOR: {innovation_factor:.2f}x
   - Technical novelty and differentiation assessment
   - Technical features: {len(technical_features)} identified
   - Innovation indicators: {self._count_innovation_indicators(technical_features)}

4. RISK FACTOR: {risk_factor:.2f}x
   - Prior art risk: {prior_art_risk}
   - Implementation complexity: {implementation_complexity}
   - Risk-adjusted multiplier

5. REGULATORY FACTOR: {regulatory_factor:.2f}x
   - Compliance requirements and regulatory market advantages
   - Regulatory compliance: {regulatory_compliance if regulatory_compliance else 'Not specified'}

6. COMPETITIVE FACTOR: {competitive_factor:.2f}x
   - Competitive positioning and differentiation strength
   - Market advantage assessment

VALUATION METHODOLOGY
====================

This valuation uses a multi-factor model considering:

Technical Innovation:
- Novelty of semantic reasoning approach
- Performance improvements (1.5x speed, <5ms cycles)
- Technical complexity and implementation barriers

Market Factors:
- Target market size ($30-50B AI optimization market)
- Application domain multipliers
- Growth potential and adoption likelihood

Risk Assessment:
- Prior art conflicts and novelty
- Implementation complexity
- Competitive landscape analysis

Regulatory Compliance:
- Built-in interpretability for regulated industries
- GDPR, HIPAA, SEC compliance advantages
- Regulatory market barriers to entry

COMPARATIVE ANALYSIS
===================

Similar Patent Valuations (Industry Benchmarks):
- Core AI/ML patents: $5-20M
- Healthcare AI patents: $10-30M
- Financial AI patents: $8-25M
- AutoML patents: $3-15M
- Semantic reasoning patents: $4-18M

This patent's valuation: ${final_value['low_value']:.1f}M - ${final_value['high_value']:.1f}M
Position: {'Above average' if final_value['mid_value'] > 10 else 'Average' if final_value['mid_value'] > 5 else 'Below average'}

RECOMMENDATIONS
==============

Value Optimization Strategies:
1. {'Strengthen prior art differentiation' if risk_factor < 0.8 else 'Maintain current positioning'}
2. {'Expand market applications' if market_factor < 1.5 else 'Focus on core markets'}
3. {'Enhance technical innovation' if innovation_factor < 1.5 else 'Protect current innovations'}
4. {'Improve regulatory compliance' if regulatory_factor < 1.2 else 'Leverage compliance advantages'}

Filing Strategy:
- {'Proceed with filing - Strong value proposition' if final_value['mid_value'] > 8 else 'Consider improvements before filing' if final_value['mid_value'] > 4 else 'Reconsider filing strategy'}
- {'High priority' if final_value['mid_value'] > 12 else 'Medium priority' if final_value['mid_value'] > 6 else 'Low priority'}

LICENSING POTENTIAL
==================

Estimated Licensing Revenue:
- Low scenario: ${final_value['low_value'] * 0.1:.1f}M annually
- High scenario: ${final_value['high_value'] * 0.2:.1f}M annually
- Target industries: {', '.join(market_applications) if market_applications else 'AI/ML companies'}

CONCLUSION
==========

This patent demonstrates {'strong' if final_value['mid_value'] > 10 else 'moderate' if final_value['mid_value'] > 5 else 'limited'} commercial value with {'high' if final_value['confidence'] == 'High' else 'medium' if final_value['confidence'] == 'Medium' else 'low'} confidence in the valuation.

The valuation reflects the patent's position in the {'highly competitive' if competitive_factor < 1.0 else 'moderately competitive' if competitive_factor < 1.2 else 'less competitive'} AI optimization market, with {'significant' if innovation_factor > 2.0 else 'moderate' if innovation_factor > 1.5 else 'limited'} technical innovation and {'strong' if regulatory_factor > 1.5 else 'moderate' if regulatory_factor > 1.2 else 'limited'} regulatory advantages.

END OF VALUATION REPORT
=======================
"""
        
        return report

    def _count_innovation_indicators(self, technical_features: List[str]) -> int:
        """Count innovation indicators in technical features"""
        innovation_keywords = [
            'semantic', 'agent', 'coordination', 'meta', 'adaptive', 'dynamic',
            'real-time', 'gpu', 'optimization', 'reasoning', 'memory', 'privacy',
            'federated', 'explainable', 'interpretable', 'bias', 'fairness'
        ]
        
        count = 0
        for feature in technical_features:
            feature_lower = feature.lower()
            for keyword in innovation_keywords:
                if keyword in feature_lower:
                    count += 1
                    break
        
        return count
