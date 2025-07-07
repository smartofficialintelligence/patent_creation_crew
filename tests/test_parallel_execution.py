#!/usr/bin/env python3
"""
Test script for parallel execution system
"""

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to path so we can import from lib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.parallel_execution import ParallelExecutionManager, TaskStatus
from crewai import Agent, Task

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_dependency_analysis():
    """Test dependency analysis and execution group creation"""
    logger.info("🧪 Testing dependency analysis...")
    
    # Create parallel execution manager
    manager = ParallelExecutionManager(max_workers=2)
    
    # Load task dependencies
    dependencies = manager.load_task_dependencies("config/tasks.yaml")
    
    # Verify dependencies were loaded
    assert len(dependencies) > 0, "No dependencies loaded"
    logger.info(f"✅ Loaded {len(dependencies)} task dependencies")
    
    # Test dependency graph creation
    execution_groups = manager.create_dependency_graph(dependencies)
    
    # Verify execution groups were created
    assert len(execution_groups) > 0, "No execution groups created"
    logger.info(f"✅ Created {len(execution_groups)} execution groups")
    
    # Log execution groups
    for i, group in enumerate(execution_groups):
        logger.info(f"   Group {i+1}: {group}")
    
    # Test optimization
    optimized_groups = manager.optimize_execution_groups(execution_groups)
    logger.info(f"✅ Optimized to {len(optimized_groups)} groups")
    
    return True

def test_parallel_task_creation():
    """Test parallel task creation and management"""
    logger.info("🧪 Testing parallel task creation...")
    
    # Create a simple agent for testing
    test_agent = Agent(
        role="Test Agent",
        goal="Test parallel execution",
        backstory="A test agent for parallel execution testing",
        verbose=True
    )
    
    # Create a simple task
    test_task = Task(
        description="Test task for parallel execution",
        expected_output="Test output",
        agent=test_agent
    )
    
    # Create parallel execution manager
    manager = ParallelExecutionManager(max_workers=2)
    
    # Add task to manager
    manager.add_task("test_task", test_task, dependencies=[])
    
    # Verify task was added
    assert "test_task" in manager.tasks, "Task not added to manager"
    assert manager.tasks["test_task"].status == TaskStatus.PENDING, "Task not in pending state"
    
    logger.info("✅ Parallel task creation successful")
    return True

def test_dependency_graph_with_real_config():
    """Test dependency graph creation with real configuration"""
    logger.info("🧪 Testing dependency graph with real configuration...")
    
    manager = ParallelExecutionManager(max_workers=4)
    
    # Load real dependencies
    dependencies = manager.load_task_dependencies("config/tasks.yaml")
    
    # Expected task structure based on tasks.yaml
    expected_tasks = [
        "prior_art_research",
        "claims_refinement", 
        "patent_document",
        "architecture_diagram",
        "legal_review",
        "associate_editor_review",
        "editorial_review",
        "patent_integration",
        "colab_demo_concept_review",
        "colab_demo_generation",
        "colab_demo_editorial_review",
        "colab_demo_integration",
        "cover_sheet",
        "patent_valuation"
    ]
    
    # Verify all expected tasks are present
    for task_name in expected_tasks:
        assert task_name in dependencies, f"Task {task_name} not found in dependencies"
    
    # Create execution groups
    execution_groups = manager.create_dependency_graph(dependencies)
    
    # Verify that prior_art_research is in the first group (no dependencies)
    assert "prior_art_research" in execution_groups[0], "prior_art_research should be in first group"
    
    # Verify that claims_refinement comes after prior_art_research
    prior_art_group = next(i for i, group in enumerate(execution_groups) if "prior_art_research" in group)
    claims_group = next(i for i, group in enumerate(execution_groups) if "claims_refinement" in group)
    assert claims_group > prior_art_group, "claims_refinement should come after prior_art_research"
    
    # Log parallel opportunities
    parallel_opportunities = sum(1 for group in execution_groups if len(group) > 1)
    total_groups = len(execution_groups)
    
    logger.info(f"✅ Parallel opportunities: {parallel_opportunities}/{total_groups} groups can run tasks in parallel")
    
    # Calculate theoretical speedup
    sequential_tasks = sum(len(group) for group in execution_groups)
    parallel_time_units = len(execution_groups)  # Assuming each group takes 1 time unit
    theoretical_speedup = sequential_tasks / parallel_time_units
    
    logger.info(f"✅ Theoretical speedup: {theoretical_speedup:.1f}x ({sequential_tasks} tasks → {parallel_time_units} time units)")
    
    return True

def test_parallel_execution_safety():
    """Test parallel execution safety and error handling"""
    logger.info("🧪 Testing parallel execution safety...")
    
    # Test with invalid configuration
    manager = ParallelExecutionManager(max_workers=2)
    
    # Test with missing dependencies file
    dependencies = manager.load_task_dependencies("nonexistent_file.yaml")
    assert len(dependencies) == 0, "Should handle missing file gracefully"
    
    # Test with circular dependencies
    circular_deps = {
        "task_a": ["task_b"],
        "task_b": ["task_a"]
    }
    
    execution_groups = manager.create_dependency_graph(circular_deps)
    assert len(execution_groups) > 0, "Should handle circular dependencies"
    
    logger.info("✅ Parallel execution safety tests passed")
    return True

def main():
    """Run all parallel execution tests"""
    logger.info("🚀 Starting parallel execution tests...")
    
    tests = [
        test_dependency_analysis,
        test_parallel_task_creation,
        test_dependency_graph_with_real_config,
        test_parallel_execution_safety
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                logger.info(f"✅ {test.__name__} PASSED")
            else:
                failed += 1
                logger.error(f"❌ {test.__name__} FAILED")
        except Exception as e:
            failed += 1
            logger.error(f"❌ {test.__name__} ERROR: {e}")
    
    logger.info("=" * 60)
    logger.info(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All parallel execution tests PASSED!")
        return True
    else:
        logger.error("💥 Some parallel execution tests FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 