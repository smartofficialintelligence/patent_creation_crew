#!/usr/bin/env python3
"""
Run Patent Automation with Agent/Model Tracking
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the tracker
from scripts.agent_model_tracker import setup_comprehensive_tracking, get_tracker

def run_with_tracking(args):
    """Run patent automation with comprehensive tracking"""
    print("🔍 PATENT AUTOMATION WITH AGENT TRACKING")
    print("=" * 70)
    
    # Setup tracking
    setup_comprehensive_tracking()
    tracker = get_tracker()
    
    # Import and run automation
    try:
        from run_patent_automation import run_patent_automation
        
        # Parse basic arguments for tracking
        tier_filter = None
        max_per_tier = None
        optimization_level = "balanced"
        
        for i, arg in enumerate(args):
            if arg == "--tier" and i + 1 < len(args):
                tier_filter = args[i + 1]
            elif arg == "--max-per-tier" and i + 1 < len(args):
                max_per_tier = int(args[i + 1])
            elif arg == "--optimization-level" and i + 1 < len(args):
                optimization_level = args[i + 1]
        
        print(f"🎯 Running with tracking: tier={tier_filter}, max={max_per_tier}, opt={optimization_level}")
        print("📊 Real-time agent tracking enabled...")
        print()
        
        start_time = datetime.now()
        
        # Run automation
        success = run_patent_automation(
            tier_filter=tier_filter,
            max_patents_per_tier=max_per_tier,
            optimization_level=optimization_level
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate final report
        print("\n" + "=" * 70)
        print("🏁 EXECUTION COMPLETE - AGENT TRACKING SUMMARY")
        print("=" * 70)
        print(f"⏱️  Total Duration: {duration:.1f} seconds")
        print()
        print(tracker.get_summary_report())
        
        # Save detailed report
        report_file = tracker.save_detailed_report()
        print(f"\n📊 Detailed tracking report: {report_file}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error running automation with tracking: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point"""
    # Pass through all command line arguments
    automation_args = sys.argv[1:]
    
    if not automation_args:
        print("Usage: python scripts/run_with_tracking.py [automation arguments]")
        print("Example: python scripts/run_with_tracking.py --tier tier_1 --max-per-tier 1")
        return
    
    success = run_with_tracking(automation_args)
    
    if success:
        print("\n🎉 Automation completed successfully with tracking!")
        sys.exit(0)
    else:
        print("\n💥 Automation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 