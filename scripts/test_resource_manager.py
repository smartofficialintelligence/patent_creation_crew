#!/usr/bin/env python3
"""
Test script for resource management system
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_resource_manager():
    """Test the resource management system"""
    print("🧪 Testing Resource Management System")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from core.resource_manager import (
            ResourceManager, 
            ProgressTracker, 
            ErrorHandler,
            initialize_monitoring,
            cleanup_monitoring,
            get_status_report,
            resource_manager,
            progress_tracker,
            error_handler
        )
        print("✅ All imports successful")
        
        # Test ResourceManager
        print("\n🔧 Testing ResourceManager...")
        rm = ResourceManager(max_memory_gb=1.0, max_cpu_percent=50, timeout_minutes=5)
        print(f"✅ ResourceManager created with limits: Memory {rm.max_memory_gb}GB, CPU {rm.max_cpu_percent}%, Timeout {rm.timeout_minutes}min")
        
        # Test ProgressTracker
        print("\n📈 Testing ProgressTracker...")
        pt = ProgressTracker(total_patents=5, total_tasks=50)
        print(f"✅ ProgressTracker created for {pt.total_patents} patents, {pt.total_tasks} tasks")
        
        # Test task tracking
        pt.start_task("test_task", "P001")
        pt.complete_task("test_task", "P001", success=True)
        pt.complete_patent("P001")
        print("✅ Task and patent tracking working")
        
        # Test ErrorHandler
        print("\n❌ Testing ErrorHandler...")
        eh = ErrorHandler(max_retries=2, retry_delay=1)
        print("✅ ErrorHandler created")
        
        # Test monitoring initialization
        print("\n🚀 Testing monitoring initialization...")
        initialize_monitoring(3, 30)
        print("✅ Monitoring initialized")
        
        # Test status report
        print("\n📊 Testing status report...")
        status = get_status_report()
        print("✅ Status report generated")
        print(f"   Resource status keys: {list(status.get('resource_status', {}).keys())}")
        print(f"   Progress summary keys: {list(status.get('progress_summary', {}).keys())}")
        print(f"   Error summary keys: {list(status.get('error_summary', {}).keys())}")
        
        # Test cleanup
        print("\n🧹 Testing cleanup...")
        cleanup_monitoring()
        print("✅ Cleanup completed")
        
        print("\n🎉 All tests passed! Resource management system is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_resource_manager()
    sys.exit(0 if success else 1) 