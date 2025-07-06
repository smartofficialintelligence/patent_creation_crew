#!/usr/bin/env python3
"""
Test script for the retry and recovery system
Demonstrates how the system handles tool failures and recovery
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

from lib.retry_manager import RetryManager, RetryStatus
from scripts.recovery_manager import RecoveryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def simulate_failing_tool(patent_id: str, should_fail: bool = True) -> str:
    """Simulate a tool that sometimes fails"""
    if should_fail:
        raise Exception(f"Simulated failure for patent {patent_id}")
    return f"Success for patent {patent_id}"

def test_retry_system():
    """Test the retry and recovery system"""
    logger.info("🧪 Testing Retry and Recovery System")
    logger.info("=" * 50)
    
    # Initialize retry manager
    retry_manager = RetryManager(
        max_retries=3,
        base_delay=1.0,  # Shorter delays for testing
        max_delay=5.0,
        backoff_factor=2.0,
        recovery_file="test_recovery_data.json"
    )
    
    # Test 1: Successful execution
    logger.info("\n📋 Test 1: Successful execution")
    try:
        result = retry_manager.execute_with_retry(
            patent_id="test_patent_001",
            tool_name="test_tool",
            tool_function=lambda: "Success!"
        )
        logger.info(f"✅ Result: {result}")
    except Exception as e:
        logger.error(f"❌ Test 1 failed: {e}")
    
    # Test 2: Failing execution (should retry and eventually fail)
    logger.info("\n📋 Test 2: Failing execution (should retry)")
    try:
        result = retry_manager.execute_with_retry(
            patent_id="test_patent_002",
            tool_name="failing_tool",
            tool_function=lambda: simulate_failing_tool("test_patent_002", should_fail=True)
        )
        logger.info(f"✅ Result: {result[:100]}...")
    except Exception as e:
        logger.error(f"❌ Test 2 failed: {e}")
    
    # Test 3: Intermittent failure (should succeed on retry)
    logger.info("\n📋 Test 3: Intermittent failure (should succeed on retry)")
    attempt_count = 0
    def intermittent_tool():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:  # Fail first 2 attempts
            raise Exception(f"Simulated intermittent failure (attempt {attempt_count})")
        return "Success after retries!"
    
    try:
        result = retry_manager.execute_with_retry(
            patent_id="test_patent_003",
            tool_name="intermittent_tool",
            tool_function=intermittent_tool
        )
        logger.info(f"✅ Result: {result}")
    except Exception as e:
        logger.error(f"❌ Test 3 failed: {e}")
    
    # Show summary
    logger.info("\n📊 Retry Manager Summary")
    logger.info("=" * 30)
    summary = retry_manager.get_execution_summary()
    for key, value in summary.items():
        logger.info(f"{key}: {value}")
    
    # Show failed executions
    logger.info("\n❌ Failed Executions")
    logger.info("=" * 20)
    failed = retry_manager.get_failed_executions()
    for record in failed:
        logger.info(f"- {record.patent_id} ({record.tool_name}): {record.error_summary}")
    
    # Test recovery manager
    logger.info("\n🔄 Testing Recovery Manager")
    logger.info("=" * 30)
    
    recovery_manager = RecoveryManager(recovery_file="test_recovery_data.json")
    recovery_manager.show_execution_summary()
    
    # Generate test report
    logger.info("\n📄 Generating Test Report")
    recovery_manager.generate_recovery_report("test_recovery_report.md")
    
    # Cleanup
    logger.info("\n🧹 Cleaning up test files")
    try:
        os.remove("test_recovery_data.json")
        os.remove("test_recovery_report.md")
        logger.info("✅ Test files cleaned up")
    except FileNotFoundError:
        pass
    
    logger.info("\n🎉 Retry system test completed!")

if __name__ == "__main__":
    test_retry_system() 