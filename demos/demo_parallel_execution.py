#!/usr/bin/env python3
"""
Demo script showcasing the parallel execution system for patent automation
"""

import logging
import sys
import os

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.parallel_execution import ParallelExecutionManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_parallel_execution():
    """Demonstrate parallel execution capabilities"""
    
    print("🚀 PARALLEL EXECUTION DEMO")
    print("=" * 60)
    
    # Create parallel execution manager
    manager = ParallelExecutionManager(max_workers=4)
    
    # Load task dependencies from configuration
    print("📋 Loading task dependencies...")
    dependencies = manager.load_task_dependencies("config/tasks.yaml")
    
    print(f"✅ Loaded {len(dependencies)} tasks:")
    for task_name, deps in dependencies.items():
        dep_str = f" (depends on: {', '.join(deps)})" if deps else " (no dependencies)"
        print(f"   • {task_name}{dep_str}")
    
    print("\n🔗 Analyzing dependencies and creating execution groups...")
    
    # Create execution groups
    execution_groups = manager.create_dependency_graph(dependencies)
    optimized_groups = manager.optimize_execution_groups(execution_groups)
    
    print(f"✅ Created {len(optimized_groups)} execution groups:")
    
    for i, group in enumerate(optimized_groups):
        parallel_indicator = "🔄 PARALLEL" if len(group) > 1 else "➡️ SEQUENTIAL"
        print(f"   Group {i+1}: {parallel_indicator}")
        for task in group:
            print(f"     • {task}")
    
    # Calculate performance metrics
    total_tasks = sum(len(group) for group in optimized_groups)
    sequential_time_units = total_tasks
    parallel_time_units = len(optimized_groups)
    
    theoretical_speedup = sequential_time_units / parallel_time_units
    time_savings = ((sequential_time_units - parallel_time_units) / sequential_time_units) * 100
    
    print(f"\n📊 PERFORMANCE ANALYSIS:")
    print(f"   Sequential execution: {sequential_time_units} time units")
    print(f"   Parallel execution: {parallel_time_units} time units")
    print(f"   Theoretical speedup: {theoretical_speedup:.1f}x")
    print(f"   Time savings: {time_savings:.1f}%")
    
    # Count parallel opportunities
    parallel_groups = sum(1 for group in optimized_groups if len(group) > 1)
    parallel_tasks = sum(len(group) for group in optimized_groups if len(group) > 1)
    
    print(f"\n🎯 PARALLEL OPPORTUNITIES:")
    print(f"   Groups with parallel execution: {parallel_groups}/{len(optimized_groups)}")
    print(f"   Tasks that can run in parallel: {parallel_tasks}/{total_tasks}")
    
    # Show usage instructions
    print(f"\n🛠️  HOW TO USE PARALLEL EXECUTION:")
    print(f"   # Enable parallel execution with default 4 workers")
    print(f"   python run_patent_automation.py --parallel")
    print(f"   ")
    print(f"   # Enable parallel execution with custom worker count")
    print(f"   python run_patent_automation.py --parallel --max-workers 8")
    print(f"   ")
    print(f"   # Combine with other options")
    print(f"   python run_patent_automation.py --parallel --tier tier_1 --test")
    
    return True

def demo_execution_flow():
    """Demonstrate execution flow visualization"""
    
    print("\n🔄 EXECUTION FLOW VISUALIZATION")
    print("=" * 60)
    
    manager = ParallelExecutionManager(max_workers=4)
    dependencies = manager.load_task_dependencies("config/tasks.yaml")
    execution_groups = manager.create_dependency_graph(dependencies)
    
    print("Sequential Flow (Traditional):")
    print("prior_art_research → claims_refinement → patent_document → architecture_diagram → ...")
    print("(Each task waits for the previous one to complete)")
    
    print("\nParallel Flow (Optimized):")
    for i, group in enumerate(execution_groups):
        if len(group) == 1:
            print(f"Step {i+1}: {group[0]}")
        else:
            print(f"Step {i+1}: {' + '.join(group)} (parallel)")
    
    print("\n✨ Benefits of Parallel Execution:")
    print("   • Reduced total execution time")
    print("   • Better resource utilization")
    print("   • Maintained dependency safety")
    print("   • Automatic failure handling")
    print("   • Compatible with existing CrewAI workflow")
    
    return True

def main():
    """Main demo function"""
    print("🎬 PATENT AUTOMATION PARALLEL EXECUTION DEMO")
    print("=" * 80)
    
    try:
        demo_parallel_execution()
        demo_execution_flow()
        
        print("\n🎉 Demo completed successfully!")
        print("Ready to use parallel execution in your patent automation workflow!")
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 