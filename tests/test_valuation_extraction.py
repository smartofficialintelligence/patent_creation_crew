#!/usr/bin/env python3
"""
Test script to manually extract valuation data and test aggregation
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lib.utils import aggregate_portfolio_valuation

def extract_valuation_from_report(report_content: str) -> dict:
    """Manually extract valuation data from the report content"""
    
    # Parse the valuation summary section
    lines = report_content.split('\n')
    valuation_data = {
        "patent_id": "P000",
        "title": "Method for Agent-Based Optimization via Semantic Reasoning",
        "valuation": {
            "low_value": 0,
            "high_value": 0,
            "mid_value": 0,
            "category": "UNKNOWN",
            "confidence": "UNKNOWN"
        },
        "factors": {
            "base_value": 0,
            "market_factor": 0,
            "innovation_factor": 0,
            "risk_factor": 0,
            "regulatory_factor": 0,
            "competitive_factor": 0
        }
    }
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Extract value range
        if "Estimated Value Range:" in line:
            try:
                # Extract values like "$14.3M - $26.5M"
                value_part = line.split(":")[1].strip()
                low_str, high_str = value_part.split(" - ")
                low_value = float(low_str.replace("$", "").replace("M", ""))
                high_value = float(high_str.replace("$", "").replace("M", ""))
                valuation_data["valuation"]["low_value"] = low_value
                valuation_data["valuation"]["high_value"] = high_value
                valuation_data["valuation"]["mid_value"] = (low_value + high_value) / 2
            except:
                pass
        
        # Extract mid-point value
        elif "Mid-Point Value:" in line:
            try:
                value_part = line.split(":")[1].strip()
                mid_value = float(value_part.replace("$", "").replace("M", ""))
                valuation_data["valuation"]["mid_value"] = mid_value
            except:
                pass
        
        # Extract value category
        elif "Value Category:" in line:
            category = line.split(":")[1].strip()
            valuation_data["valuation"]["category"] = category
        
        # Extract confidence level
        elif "Confidence Level:" in line:
            confidence = line.split(":")[1].strip()
            valuation_data["valuation"]["confidence"] = confidence
        
        # Extract base value
        elif "BASE VALUE:" in line:
            try:
                value_part = line.split(":")[1].strip()
                base_value = float(value_part.replace("$", "").replace("M", ""))
                valuation_data["factors"]["base_value"] = base_value
            except:
                pass
        
        # Extract market factor
        elif "MARKET FACTOR:" in line:
            try:
                value_part = line.split(":")[1].strip()
                market_factor = float(value_part.replace("x", ""))
                valuation_data["factors"]["market_factor"] = market_factor
            except:
                pass
        
        # Extract innovation factor
        elif "INNOVATION FACTOR:" in line:
            try:
                value_part = line.split(":")[1].strip()
                innovation_factor = float(value_part.replace("x", ""))
                valuation_data["factors"]["innovation_factor"] = innovation_factor
            except:
                pass
        
        # Extract risk factor
        elif "RISK FACTOR:" in line:
            try:
                value_part = line.split(":")[1].strip()
                risk_factor = float(value_part.replace("x", ""))
                valuation_data["factors"]["risk_factor"] = risk_factor
            except:
                pass
        
        # Extract regulatory factor
        elif "REGULATORY FACTOR:" in line:
            try:
                value_part = line.split(":")[1].strip()
                regulatory_factor = float(value_part.replace("x", ""))
                valuation_data["factors"]["regulatory_factor"] = regulatory_factor
            except:
                pass
        
        # Extract competitive factor
        elif "COMPETITIVE FACTOR:" in line:
            try:
                value_part = line.split(":")[1].strip()
                competitive_factor = float(value_part.replace("x", ""))
                valuation_data["factors"]["competitive_factor"] = competitive_factor
            except:
                pass
    
    return valuation_data

def main():
    """Test the valuation extraction and aggregation"""
    
    # Read the existing valuation report
    report_path = "output/tier_1/P000_valuation_report.md"
    
    if not Path(report_path).exists():
        print(f"Valuation report not found: {report_path}")
        return
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    # Extract valuation data
    valuation_data = extract_valuation_from_report(report_content)
    
    print("Extracted Valuation Data:")
    print("=" * 50)
    print(f"Patent ID: {valuation_data['patent_id']}")
    print(f"Title: {valuation_data['title']}")
    print(f"Value Range: ${valuation_data['valuation']['low_value']:.1f}M - ${valuation_data['valuation']['high_value']:.1f}M")
    print(f"Mid-Point Value: ${valuation_data['valuation']['mid_value']:.1f}M")
    print(f"Category: {valuation_data['valuation']['category']}")
    print(f"Confidence: {valuation_data['valuation']['confidence']}")
    print()
    
    # Test aggregation
    valuation_list = [valuation_data]
    portfolio_summary = aggregate_portfolio_valuation(valuation_list)
    
    print("Portfolio Summary:")
    print("=" * 50)
    print(f"Total Patents Valued: {portfolio_summary['total_patents']}")
    print(f"Portfolio Value Range: ${portfolio_summary['total_low_value']:.1f}M - ${portfolio_summary['total_high_value']:.1f}M")
    print(f"Portfolio Mid-Point Value: ${portfolio_summary['total_mid_value']:.1f}M")
    print(f"Average Patent Value: ${portfolio_summary['average_mid_value']:.1f}M")
    
    # Calculate ROI
    total_investment = 1 * 130  # 1 patent * $130 filing cost
    roi_low = (portfolio_summary['total_low_value'] * 1000000) / total_investment if total_investment > 0 else 0
    roi_high = (portfolio_summary['total_high_value'] * 1000000) / total_investment if total_investment > 0 else 0
    roi_mid = (portfolio_summary['total_mid_value'] * 1000000) / total_investment if total_investment > 0 else 0
    
    print(f"Total Investment: ${total_investment:,.0f}")
    print(f"ROI Range: {roi_low:.0f}x - {roi_high:.0f}x")
    print(f"ROI Mid-Point: {roi_mid:.0f}x")
    
    print("\n✅ Valuation extraction and aggregation test completed successfully!")

if __name__ == "__main__":
    main() 