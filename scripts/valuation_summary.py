#!/usr/bin/env python3
"""
Valuation Summary Script

Extract and display aggregated valuation results from existing patent outputs.
This script can be run independently to see the current portfolio valuation
without running the full automation.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lib.utils import collect_valuation_results_from_outputs, aggregate_portfolio_valuation
from lib.patent_data import PATENT_IDEAS, PATENT_CONFIG

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_valuation_files(tier_filter: str = None) -> list:
    """Find all valuation output files in the patent_output directory."""
    valuation_files = []
    output_dir = Path("patent_output")
    
    if not output_dir.exists():
        logger.warning("patent_output directory not found")
        return valuation_files
    
    # Determine which tiers to process
    tiers_to_check = [tier_filter] if tier_filter else ['tier_1', 'tier_2', 'tier_3', 'tier_4']
    
    for tier in tiers_to_check:
        tier_dir = output_dir / tier
        if not tier_dir.exists():
            continue
            
        # Look for valuation files
        for file_path in tier_dir.glob("*_valuation_report.md"):
            valuation_files.append(str(file_path))
    
    return valuation_files

def display_individual_valuations(valuation_data_list: list):
    """Display individual patent valuations."""
    if not valuation_data_list:
        return
        
    logger.info("\n📋 INDIVIDUAL PATENT VALUATIONS")
    logger.info("=" * 60)
    
    for data in sorted(valuation_data_list, key=lambda x: x['patent_id']):
        patent_id = data['patent_id']
        title = data['title'][:60] + "..." if len(data['title']) > 60 else data['title']
        valuation = data['valuation']
        
        logger.info(f"Patent {patent_id}: {title}")
        logger.info(f"  Value: ${valuation['low_value']:.1f}M - ${valuation['high_value']:.1f}M")
        logger.info(f"  Mid-Point: ${valuation['mid_value']:.1f}M")
        logger.info(f"  Category: {valuation['category']}")
        logger.info(f"  Confidence: {valuation['confidence']}")
        logger.info("")

def main():
    """Main function to run the valuation summary."""
    parser = argparse.ArgumentParser(description='Display aggregated patent valuation results')
    parser.add_argument('--tier', type=str, choices=['tier_1', 'tier_2', 'tier_3', 'tier_4'],
                       help='Show results for specific tier only')
    parser.add_argument('--detailed', action='store_true',
                       help='Show detailed individual patent valuations')
    parser.add_argument('--investment', type=float, default=None,
                       help='Specify total investment amount for ROI calculation')
    
    args = parser.parse_args()
    
    logger.info("🔍 Patent Valuation Summary")
    logger.info("=" * 50)
    
    # Find valuation files
    valuation_files = find_valuation_files(args.tier)
    
    if not valuation_files:
        logger.warning("No valuation files found!")
        logger.info("Make sure you have run the patent automation first.")
        return
    
    logger.info(f"Found {len(valuation_files)} valuation files")
    
    # Collect valuation data
    valuation_data_list = collect_valuation_results_from_outputs(valuation_files)
    
    if not valuation_data_list:
        logger.warning("No valuation data could be extracted from files!")
        return
    
    # Aggregate results
    portfolio_summary = aggregate_portfolio_valuation(valuation_data_list)
    
    # Display portfolio summary
    logger.info("\n💰 PORTFOLIO VALUATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total Patents Valued: {portfolio_summary['total_patents']}")
    logger.info(f"Portfolio Value Range: ${portfolio_summary['total_low_value']:.1f}M - ${portfolio_summary['total_high_value']:.1f}M")
    logger.info(f"Portfolio Mid-Point Value: ${portfolio_summary['total_mid_value']:.1f}M")
    logger.info(f"Average Patent Value: ${portfolio_summary['average_mid_value']:.1f}M")
    
    # Calculate ROI if investment amount is provided
    if args.investment:
        total_investment = args.investment
    else:
        # Use default filing cost per patent
        total_investment = portfolio_summary['total_patents'] * PATENT_CONFIG['filing_cost_per_patent']
    
    roi_low = (portfolio_summary['total_low_value'] * 1000000) / total_investment if total_investment > 0 else 0
    roi_high = (portfolio_summary['total_high_value'] * 1000000) / total_investment if total_investment > 0 else 0
    roi_mid = (portfolio_summary['total_mid_value'] * 1000000) / total_investment if total_investment > 0 else 0
    
    logger.info(f"Total Investment: ${total_investment:,.0f}")
    logger.info(f"ROI Range: {roi_low:.0f}x - {roi_high:.0f}x")
    logger.info(f"ROI Mid-Point: {roi_mid:.0f}x")
    
    # Show value distribution
    if portfolio_summary['value_categories']:
        logger.info("\n📊 Value Distribution:")
        for category, count in portfolio_summary['value_categories'].items():
            percentage = (count / portfolio_summary['total_patents']) * 100
            logger.info(f"  {category}: {count} patents ({percentage:.1f}%)")
    
    # Show confidence levels
    if portfolio_summary['confidence_levels']:
        logger.info("\n🎯 Confidence Levels:")
        for confidence, count in portfolio_summary['confidence_levels'].items():
            percentage = (count / portfolio_summary['total_patents']) * 100
            logger.info(f"  {confidence}: {count} patents ({percentage:.1f}%)")
    
    # Show detailed individual valuations if requested
    if args.detailed:
        display_individual_valuations(valuation_data_list)
    
    logger.info("\n✅ Valuation summary complete!")

if __name__ == "__main__":
    main() 