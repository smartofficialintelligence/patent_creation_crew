"""
Parallel Execution System for Patent Automation
Implements intelligent parallel task execution with dependency awareness
"""

import asyncio
import threading
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import yaml
from crewai import Task, Agent, Crew

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ParallelTask:
    """Wrapper for CrewAI Task with parallel execution metadata"""
    task: Task
    task_name: str
    dependencies: List[str]
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[Exception] = None
    
    @property
    def execution_time(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

class ParallelExecutionManager:
    """Manages parallel execution of tasks with dependency resolution"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.tasks: Dict[str, ParallelTask] = {}
        self.execution_groups: List[List[str]] = []
        self.completed_tasks: Set[str] = set()
        self.failed_tasks: Set[str] = set()
        
    def load_task_dependencies(self, tasks_config_path: str = "config/tasks.yaml") -> Dict[str, List[str]]:
        """Load task dependencies from YAML configuration"""
        try:
            with open(tasks_config_path, 'r') as f:
                tasks_config = yaml.safe_load(f)
            
            dependencies = {}
            for task_name, task_config in tasks_config.items():
                if task_name == 'task_generation':
                    continue
                    
                # Extract dependencies from context field
                context_deps = task_config.get('context', [])
                dependencies[task_name] = context_deps
                
            return dependencies
        except Exception as e:
            logger.error(f"Error loading task dependencies: {e}")
            return {}
    
    def create_dependency_graph(self, dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """Create execution groups based on dependency analysis"""
        # Start with tasks that have no dependencies
        remaining_tasks = set(dependencies.keys())
        execution_groups = []
        
        while remaining_tasks:
            # Find tasks that can run now (all dependencies satisfied)
            ready_tasks = []
            
            for task_name in remaining_tasks:
                task_deps = dependencies.get(task_name, [])
                
                # Check if all dependencies are completed
                deps_satisfied = all(dep in self.completed_tasks for dep in task_deps)
                
                if deps_satisfied:
                    ready_tasks.append(task_name)
            
            if not ready_tasks:
                # Handle circular dependencies or missing dependencies
                logger.warning(f"Circular dependency detected or missing dependencies for: {remaining_tasks}")
                # Add remaining tasks to final group to avoid infinite loop
                execution_groups.append(list(remaining_tasks))
                break
            
            # Create parallel execution group
            execution_groups.append(ready_tasks)
            
            # Mark these tasks as completed for dependency resolution
            for task_name in ready_tasks:
                self.completed_tasks.add(task_name)
                remaining_tasks.remove(task_name)
        
        # Reset completed tasks for actual execution
        self.completed_tasks.clear()
        
        return execution_groups
    
    def optimize_execution_groups(self, execution_groups: List[List[str]]) -> List[List[str]]:
        """Optimize execution groups for better parallelism"""
        optimized_groups = []
        
        for group in execution_groups:
            if len(group) <= self.max_workers:
                # Group fits within worker limit
                optimized_groups.append(group)
            else:
                # Split large groups into sub-groups
                for i in range(0, len(group), self.max_workers):
                    sub_group = group[i:i + self.max_workers]
                    optimized_groups.append(sub_group)
        
        return optimized_groups
    
    def add_task(self, task_name: str, task: Task, dependencies: List[str] = None):
        """Add a task to the parallel execution system"""
        if dependencies is None:
            dependencies = []
            
        parallel_task = ParallelTask(
            task=task,
            task_name=task_name,
            dependencies=dependencies,
            status=TaskStatus.PENDING
        )
        
        self.tasks[task_name] = parallel_task
        logger.info(f"Added task {task_name} with dependencies: {dependencies}")
    
    def execute_task(self, task_name: str) -> Tuple[str, Any, Optional[Exception]]:
        """Execute a single task"""
        if task_name not in self.tasks:
            error = Exception(f"Task {task_name} not found")
            return task_name, None, error
        
        parallel_task = self.tasks[task_name]
        
        try:
            logger.info(f"🚀 Starting task: {task_name}")
            parallel_task.status = TaskStatus.RUNNING
            parallel_task.start_time = time.time()
            
            # Execute the CrewAI task
            # Note: CrewAI tasks are typically executed within a Crew context
            # For individual task execution, we'll create a minimal crew
            temp_crew = Crew(
                agents=[parallel_task.task.agent],
                tasks=[parallel_task.task],
                process="sequential",
                verbose=False
            )
            
            result = temp_crew.kickoff()
            
            parallel_task.end_time = time.time()
            parallel_task.result = result
            parallel_task.status = TaskStatus.COMPLETED
            
            logger.info(f"✅ Completed task: {task_name} ({parallel_task.execution_time:.2f}s)")
            return task_name, result, None
            
        except Exception as e:
            parallel_task.end_time = time.time()
            parallel_task.error = e
            parallel_task.status = TaskStatus.FAILED
            
            logger.error(f"❌ Failed task: {task_name} - {str(e)}")
            return task_name, None, e
    
    def execute_group_parallel(self, task_group: List[str]) -> Dict[str, Tuple[Any, Optional[Exception]]]:
        """Execute a group of tasks in parallel"""
        if not task_group:
            return {}
        
        logger.info(f"🔄 Executing parallel group: {task_group}")
        
        results = {}
        
        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=min(len(task_group), self.max_workers)) as executor:
            # Submit all tasks in the group
            future_to_task = {
                executor.submit(self.execute_task, task_name): task_name
                for task_name in task_group
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    task_name_result, result, error = future.result()
                    results[task_name] = (result, error)
                    
                    if error:
                        self.failed_tasks.add(task_name)
                        logger.error(f"Task {task_name} failed: {error}")
                    else:
                        self.completed_tasks.add(task_name)
                        logger.info(f"Task {task_name} completed successfully")
                        
                except Exception as e:
                    results[task_name] = (None, e)
                    self.failed_tasks.add(task_name)
                    logger.error(f"Task {task_name} execution failed: {e}")
        
        return results
    
    def execute_all_tasks(self) -> Dict[str, Tuple[Any, Optional[Exception]]]:
        """Execute all tasks using parallel execution strategy"""
        logger.info("🎯 Starting parallel execution of all tasks")
        
        # Load base dependencies and create execution groups
        base_dependencies = self.load_task_dependencies()
        
        # Create patent-specific dependency mapping
        patent_dependencies = {}
        for task_name in self.tasks.keys():
            if '_' in task_name:
                # Extract patent ID and task type (e.g., "P000_prior_art_research" -> "prior_art_research")
                parts = task_name.split('_', 1)
                if len(parts) == 2:
                    patent_id, task_type = parts
                    
                    # Get base dependencies for this task type
                    base_deps = base_dependencies.get(task_type, [])
                    
                    # Create patent-specific dependencies
                    patent_specific_deps = [f"{patent_id}_{dep}" for dep in base_deps]
                    patent_dependencies[task_name] = patent_specific_deps
                else:
                    # Handle fallback task names
                    patent_dependencies[task_name] = []
            else:
                # Handle generic task names
                patent_dependencies[task_name] = base_dependencies.get(task_name, [])
        
        # Update task dependencies
        for task_name, task_deps in patent_dependencies.items():
            if task_name in self.tasks:
                self.tasks[task_name].dependencies = task_deps
        
        # Create execution groups using patent-specific dependencies
        execution_groups = self.create_dependency_graph(patent_dependencies)
        optimized_groups = self.optimize_execution_groups(execution_groups)
        
        logger.info(f"📊 Execution plan: {len(optimized_groups)} groups")
        for i, group in enumerate(optimized_groups):
            logger.info(f"  Group {i+1}: {group}")
        
        # Execute groups sequentially, tasks within groups in parallel
        all_results = {}
        
        for group_idx, task_group in enumerate(optimized_groups):
            logger.info(f"🔄 Processing group {group_idx + 1}/{len(optimized_groups)}")
            
            # Filter to only include tasks that we have
            available_tasks = [task for task in task_group if task in self.tasks]
            
            if not available_tasks:
                logger.warning(f"No available tasks in group {group_idx + 1}")
                continue
            
            # Check if dependencies are satisfied
            ready_tasks = []
            for task_name in available_tasks:
                task_deps = self.tasks[task_name].dependencies
                deps_satisfied = all(dep in self.completed_tasks for dep in task_deps)
                
                if deps_satisfied:
                    ready_tasks.append(task_name)
                else:
                    logger.warning(f"Task {task_name} dependencies not satisfied: {task_deps}")
            
            if ready_tasks:
                # Execute ready tasks in parallel
                group_results = self.execute_group_parallel(ready_tasks)
                all_results.update(group_results)
                
                # Stop if critical failures occur
                if any(error for _, error in group_results.values()):
                    logger.warning("Critical failures detected, evaluating continuation...")
                    # Continue execution for now, but log warnings
        
        # Generate execution summary
        self.log_execution_summary(all_results)
        
        return all_results
    
    def log_execution_summary(self, results: Dict[str, Tuple[Any, Optional[Exception]]]):
        """Log execution summary and performance metrics"""
        total_tasks = len(results)
        successful_tasks = sum(1 for _, error in results.values() if error is None)
        failed_tasks = total_tasks - successful_tasks
        
        logger.info("=" * 60)
        logger.info("📊 PARALLEL EXECUTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tasks: {total_tasks}")
        logger.info(f"Successful: {successful_tasks}")
        logger.info(f"Failed: {failed_tasks}")
        logger.info(f"Success Rate: {(successful_tasks/total_tasks)*100:.1f}%")
        
        # Calculate total execution time and theoretical sequential time
        total_parallel_time = 0
        total_sequential_time = 0
        
        for task_name, parallel_task in self.tasks.items():
            if parallel_task.execution_time:
                total_sequential_time += parallel_task.execution_time
                # For parallel time, we need to consider the longest running task in each group
                # This is a simplified calculation
                total_parallel_time = max(total_parallel_time, parallel_task.execution_time)
        
        if total_sequential_time > 0:
            time_savings = ((total_sequential_time - total_parallel_time) / total_sequential_time) * 100
            logger.info(f"Time Savings: {time_savings:.1f}%")
            logger.info(f"Theoretical Sequential Time: {total_sequential_time:.2f}s")
            logger.info(f"Parallel Execution Time: {total_parallel_time:.2f}s")
        
        logger.info("=" * 60)
        
        # Log failed tasks
        if failed_tasks > 0:
            logger.warning("❌ Failed Tasks:")
            for task_name, (_, error) in results.items():
                if error:
                    logger.warning(f"  - {task_name}: {str(error)}")

def create_parallel_execution_manager(max_workers: int = 4) -> ParallelExecutionManager:
    """Factory function to create a parallel execution manager"""
    return ParallelExecutionManager(max_workers=max_workers) 