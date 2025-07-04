#!/usr/bin/env python3
"""
Recovery Manager Script for Patent Automation System
Handles failed tool executions and provides recovery options
"""

import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import the retry manager
from core.retry_manager import RetryManager, RetryStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RecoveryManager:
    def __init__(self, recovery_file: str = "patent_output/recovery_data.json"):
        self.retry_manager = RetryManager(recovery_file=recovery_file)
        self.recovery_file = Path(recovery_file)
    
    def show_failed_executions(self):
        """Show all failed executions"""
        failed_executions = self.retry_manager.get_failed_executions()
        
        if not failed_executions:
            logger.info("✅ No failed executions found")
            return
        
        logger.info(f"❌ Found {len(failed_executions)} failed executions:")
        logger.info("=" * 80)
        
        for i, record in enumerate(failed_executions, 1):
            logger.info(f"{i}. Patent: {record.patent_id}")
            logger.info(f"   Tool: {record.tool_name}")
            logger.info(f"   Status: {record.status.value}")
            logger.info(f"   Attempts: {record.retry_count}/{record.max_retries}")
            logger.info(f"   Error: {record.error_summary}")
            logger.info(f"   Created: {record.created_at}")
            logger.info(f"   Duration: {record.total_duration:.1f}s")
            logger.info("-" * 40)
    
    def show_execution_summary(self):
        """Show summary of all executions"""
        summary = self.retry_manager.get_execution_summary()
        
        logger.info("📊 Execution Summary")
        logger.info("=" * 50)
        logger.info(f"Total Executions: {summary['total_executions']}")
        logger.info(f"Successful: {summary['successful']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Pending: {summary['pending']}")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        logger.info(f"Average Retries: {summary['average_retries']:.1f}")
        
        if summary['total_executions'] > 0:
            if summary['success_rate'] >= 90:
                logger.info("🎉 Excellent success rate!")
            elif summary['success_rate'] >= 75:
                logger.info("✅ Good success rate")
            elif summary['success_rate'] >= 50:
                logger.info("⚠️ Moderate success rate - consider reviewing failures")
            else:
                logger.error("💥 Poor success rate - significant issues detected")
    
    def reset_failed_executions(self, patent_id: Optional[str] = None, tool_name: Optional[str] = None):
        """Reset failed executions to allow retry"""
        failed_executions = self.retry_manager.get_failed_executions()
        
        if not failed_executions:
            logger.info("No failed executions to reset")
            return
        
        # Filter by patent_id and tool_name if provided
        if patent_id:
            failed_executions = [r for r in failed_executions if r.patent_id == patent_id]
        if tool_name:
            failed_executions = [r for r in failed_executions if r.tool_name == tool_name]
        
        if not failed_executions:
            logger.info("No failed executions match the specified criteria")
            return
        
        logger.info(f"Resetting {len(failed_executions)} failed executions...")
        
        for record in failed_executions:
            self.retry_manager.reset_execution(record.patent_id, record.tool_name)
            logger.info(f"Reset: {record.patent_id} - {record.tool_name}")
        
        logger.info("✅ Reset complete. Failed executions can now be retried.")
    
    def show_detailed_execution(self, patent_id: str, tool_name: str):
        """Show detailed information about a specific execution"""
        record_id = self.retry_manager.get_record_id(patent_id, tool_name)
        
        if record_id not in self.retry_manager.execution_records:
            logger.error(f"No execution record found for {patent_id} - {tool_name}")
            return
        
        record = self.retry_manager.execution_records[record_id]
        
        logger.info(f"📋 Detailed Execution Report")
        logger.info("=" * 60)
        logger.info(f"Patent ID: {record.patent_id}")
        logger.info(f"Tool: {record.tool_name}")
        logger.info(f"Status: {record.status.value}")
        logger.info(f"Created: {record.created_at}")
        logger.info(f"Completed: {record.completed_at or 'Not completed'}")
        logger.info(f"Total Duration: {record.total_duration:.1f}s")
        logger.info(f"Retry Count: {record.retry_count}/{record.max_retries}")
        
        if record.error_summary:
            logger.info(f"Error Summary: {record.error_summary}")
        
        logger.info("\n📝 Attempt History:")
        logger.info("-" * 40)
        
        for i, attempt in enumerate(record.attempts, 1):
            logger.info(f"Attempt {i}:")
            logger.info(f"  Timestamp: {attempt.timestamp}")
            logger.info(f"  Success: {attempt.success}")
            logger.info(f"  Duration: {attempt.duration:.1f}s")
            if not attempt.success:
                logger.info(f"  Error Type: {attempt.error_type}")
                logger.info(f"  Error Message: {attempt.error_message[:100]}...")
            logger.info("")
    
    def export_recovery_data(self, output_file: str):
        """Export recovery data to a file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.retry_manager.execution_records, f, indent=2, default=str)
            logger.info(f"✅ Recovery data exported to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export recovery data: {e}")
    
    def clear_recovery_data(self):
        """Clear all recovery data"""
        if self.recovery_file.exists():
            try:
                self.recovery_file.unlink()
                logger.info("✅ Recovery data cleared")
            except Exception as e:
                logger.error(f"Failed to clear recovery data: {e}")
        else:
            logger.info("No recovery data file found")
    
    def generate_recovery_report(self, output_file: str = "patent_output/recovery_report.md"):
        """Generate a comprehensive recovery report"""
        summary = self.retry_manager.get_execution_summary()
        failed_executions = self.retry_manager.get_failed_executions()
        
        report = f"""# Patent Automation Recovery Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Executions**: {summary['total_executions']}
- **Successful**: {summary['successful']}
- **Failed**: {summary['failed']}
- **Pending**: {summary['pending']}
- **Success Rate**: {summary['success_rate']:.1f}%
- **Average Retries**: {summary['average_retries']:.1f}

## Failed Executions

"""
        
        if failed_executions:
            for record in failed_executions:
                report += f"""
### {record.patent_id} - {record.tool_name}

- **Status**: {record.status.value}
- **Attempts**: {record.retry_count}/{record.max_retries}
- **Error**: {record.error_summary}
- **Created**: {record.created_at}
- **Duration**: {record.total_duration:.1f}s

"""
        else:
            report += "No failed executions found.\n"
        
        report += f"""
## Recommendations

"""
        
        if summary['success_rate'] >= 90:
            report += "- Excellent performance - no action required\n"
        elif summary['success_rate'] >= 75:
            report += "- Good performance - review failed executions for patterns\n"
        elif summary['success_rate'] >= 50:
            report += "- Moderate performance - consider investigating common failure causes\n"
        else:
            report += "- Poor performance - significant investigation required\n"
            report += "- Check API keys and network connectivity\n"
            report += "- Review error patterns for systematic issues\n"
        
        report += f"""
## Next Steps

1. Review failed executions above
2. Reset failed executions if appropriate: `python scripts/recovery_manager.py --reset-failed`
3. Re-run automation for failed patents
4. Monitor success rate in future runs

## Technical Details

- Recovery data file: {self.recovery_file}
- Max retries per tool: {self.retry_manager.max_retries}
- Base retry delay: {self.retry_manager.base_delay}s
- Max retry delay: {self.retry_manager.max_delay}s
"""
        
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report)
            logger.info(f"✅ Recovery report generated: {output_file}")
        except Exception as e:
            logger.error(f"Failed to generate recovery report: {e}")

def main():
    parser = argparse.ArgumentParser(description='Recovery Manager for Patent Automation System')
    parser.add_argument('--show-failed', action='store_true', help='Show all failed executions')
    parser.add_argument('--show-summary', action='store_true', help='Show execution summary')
    parser.add_argument('--reset-failed', action='store_true', help='Reset all failed executions')
    parser.add_argument('--reset-patent', type=str, help='Reset failed executions for specific patent')
    parser.add_argument('--reset-tool', type=str, help='Reset failed executions for specific tool')
    parser.add_argument('--show-detail', nargs=2, metavar=('PATENT_ID', 'TOOL_NAME'), 
                       help='Show detailed execution info for patent and tool')
    parser.add_argument('--export', type=str, help='Export recovery data to file')
    parser.add_argument('--clear', action='store_true', help='Clear all recovery data')
    parser.add_argument('--report', type=str, default='patent_output/recovery_report.md',
                       help='Generate recovery report (default: patent_output/recovery_report.md)')
    
    args = parser.parse_args()
    
    recovery_manager = RecoveryManager()
    
    if args.show_failed:
        recovery_manager.show_failed_executions()
    
    if args.show_summary:
        recovery_manager.show_execution_summary()
    
    if args.reset_failed:
        recovery_manager.reset_failed_executions()
    
    if args.reset_patent:
        recovery_manager.reset_failed_executions(patent_id=args.reset_patent)
    
    if args.reset_tool:
        recovery_manager.reset_failed_executions(tool_name=args.reset_tool)
    
    if args.show_detail:
        recovery_manager.show_detailed_execution(args.show_detail[0], args.show_detail[1])
    
    if args.export:
        recovery_manager.export_recovery_data(args.export)
    
    if args.clear:
        recovery_manager.clear_recovery_data()
    
    if args.report:
        recovery_manager.generate_recovery_report(args.report)
    
    # Default action if no arguments provided
    if not any([args.show_failed, args.show_summary, args.reset_failed, args.reset_patent, 
                args.reset_tool, args.show_detail, args.export, args.clear, args.report]):
        recovery_manager.show_execution_summary()
        print("\nUse --help for available options")

if __name__ == "__main__":
    main() 