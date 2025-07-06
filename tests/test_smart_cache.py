#!/usr/bin/env python3
"""
Test script for Smart Cache Manager

This script tests the smart cache functionality to ensure it works correctly.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.smart_cache_manager import smart_cache
import tempfile
import shutil
import json
import time

def test_basic_caching():
    """Test basic cache get/set operations"""
    print("🧪 Testing basic caching operations...")
    
    # Test data
    test_data = {
        "patent_id": "TEST001",
        "title": "Test Patent",
        "results": [{"id": 1, "title": "Result 1"}, {"id": 2, "title": "Result 2"}]
    }
    
    # Test cache key
    cache_key = "test_patent_search"
    
    # Set data in cache
    success = smart_cache.set(
        cache_key,
        test_data,
        "patent_data",
        "test",
        {"test": True, "timestamp": time.time()}
    )
    
    if not success:
        print("❌ Failed to set data in cache")
        return False
    
    print("✅ Data set in cache successfully")
    
    # Get data from cache
    retrieved_data = smart_cache.get(cache_key, "patent_data")
    
    if retrieved_data is None:
        print("❌ Failed to retrieve data from cache")
        return False
    
    if retrieved_data != test_data:
        print("❌ Retrieved data doesn't match original data")
        print(f"Original: {test_data}")
        print(f"Retrieved: {retrieved_data}")
        return False
    
    print("✅ Data retrieved from cache successfully")
    return True

def test_cache_stats():
    """Test cache statistics"""
    print("🧪 Testing cache statistics...")
    
    stats = smart_cache.get_cache_stats()
    
    if not stats:
        print("❌ Failed to get cache statistics")
        return False
    
    required_keys = ['total_entries', 'total_size_bytes', 'cache_enabled']
    for key in required_keys:
        if key not in stats:
            print(f"❌ Missing required stat key: {key}")
            return False
    
    print("✅ Cache statistics retrieved successfully")
    print(f"   Total entries: {stats['total_entries']}")
    print(f"   Total size: {stats['total_size_mb']:.1f}MB")
    print(f"   Cache enabled: {stats['cache_enabled']}")
    
    return True

def test_health_check():
    """Test cache health check"""
    print("🧪 Testing cache health check...")
    
    health_status = smart_cache.health_check()
    
    if not health_status:
        print("❌ Failed to perform health check")
        return False
    
    if 'is_healthy' not in health_status:
        print("❌ Health status missing 'is_healthy' key")
        return False
    
    print("✅ Health check completed successfully")
    print(f"   Cache healthy: {health_status['is_healthy']}")
    
    return True

def test_cache_key_generation():
    """Test cache key generation methods"""
    print("🧪 Testing cache key generation...")
    
    # Test patent cache key
    patent_key = smart_cache.get_patent_cache_key("TEST001", ["agent", "optimization"])
    if not patent_key.startswith("patent_TEST001_"):
        print("❌ Patent cache key format incorrect")
        return False
    
    # Test academic cache key
    academic_key = smart_cache.get_academic_cache_key("TEST001", ["machine learning"])
    if not academic_key.startswith("academic_TEST001_"):
        print("❌ Academic cache key format incorrect")
        return False
    
    # Test embedding cache key
    embedding_key = smart_cache.get_embedding_cache_key("test text", "test-model")
    if not embedding_key.startswith("embedding_test-model_"):
        print("❌ Embedding cache key format incorrect")
        return False
    
    print("✅ Cache key generation working correctly")
    return True

def test_cache_clear():
    """Test cache clearing functionality"""
    print("🧪 Testing cache clearing...")
    
    # Add some test data
    test_data = {"test": "data"}
    smart_cache.set("test_clear", test_data, "patent_data", "test")
    
    # Check that data exists
    if smart_cache.get("test_clear", "patent_data") is None:
        print("❌ Test data not found before clearing")
        return False
    
    # Clear patent_data cache
    smart_cache.clear_cache("patent_data")
    
    # Check that data is gone
    if smart_cache.get("test_clear", "patent_data") is not None:
        print("❌ Test data still exists after clearing")
        return False
    
    print("✅ Cache clearing working correctly")
    return True

def test_cache_compression():
    """Test that cache compression works correctly"""
    print("🧪 Testing cache compression...")
    
    # Large test data
    large_data = {
        "patent_id": "LARGE001",
        "title": "Large Patent Data",
        "abstract": "A" * 10000,  # 10KB of data
        "results": [{"id": i, "data": "x" * 100} for i in range(100)]
    }
    
    cache_key = "test_large_data"
    
    # Set large data
    success = smart_cache.set(cache_key, large_data, "patent_data", "test")
    if not success:
        print("❌ Failed to set large data in cache")
        return False
    
    # Retrieve large data
    retrieved_data = smart_cache.get(cache_key, "patent_data")
    if retrieved_data != large_data:
        print("❌ Large data not retrieved correctly")
        return False
    
    print("✅ Cache compression working correctly")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Smart Cache Tests")
    print("=" * 50)
    
    tests = [
        test_basic_caching,
        test_cache_stats,
        test_health_check,
        test_cache_key_generation,
        test_cache_clear,
        test_cache_compression
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Smart cache system is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the smart cache implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 