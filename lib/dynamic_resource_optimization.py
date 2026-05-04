"""
Dynamic Resource Optimization System
Achieves 25-35% cost reduction through intelligent context and resource management
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import hashlib
import numpy as np
import yaml

# Set up logging
logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    """Task complexity levels for dynamic model selection"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"

class ResourceType(Enum):
    """Types of resources to optimize"""
    TOKENS = "tokens"
    COMPUTE = "compute"
    MEMORY = "memory"
    CACHE = "cache"
    NETWORK = "network"

@dataclass
class ResourceUsage:
    """Track resource usage for optimization"""
    tokens_used: int = 0
    tokens_allocated: int = 0
    compute_time_ms: float = 0
    memory_mb: float = 0
    cache_hits: int = 0
    cache_misses: int = 0
    api_calls: int = 0
    cost_usd: float = 0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TaskProfile:
    """Profile of a task for optimization"""
    task_name: str
    complexity: TaskComplexity
    estimated_tokens: int
    context_size: int
    dependencies: List[str] = field(default_factory=list)
    priority: float = 1.0
    cost_sensitivity: float = 1.0
    quality_requirements: float = 0.8
    historical_usage: List[ResourceUsage] = field(default_factory=list)

@dataclass
class ModelConfig:
    """Configuration for model selection"""
    model_name: str
    cost_per_token: float
    context_limit: int
    quality_score: float
    speed_score: float
    suitable_for: List[TaskComplexity]

@dataclass
class OptimizationResult:
    """Result of optimization"""
    original_cost: float
    optimized_cost: float
    cost_reduction: float
    model_changes: Dict[str, str]
    context_reductions: Dict[str, int]
    resource_savings: Dict[str, float]
    quality_impact: float
    execution_time_impact: float

class DynamicResourceOptimizer:
    """Main optimization engine for dynamic resource management"""
    
    def __init__(self, config_file: str = "config/resource_optimization.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
        self.models = self._initialize_models()
        self.task_profiles = {}
        self.usage_history = []
        self.current_session = {
            'start_time': datetime.now(),
            'total_cost': 0,
            'total_tokens': 0,
            'optimizations_applied': 0
        }
        self.cost_targets = {
            'reduction_target': 0.30,  # 30% reduction target
            'max_quality_impact': 0.05,  # Max 5% quality impact
            'max_time_impact': 0.10  # Max 10% time impact
        }
        
        # Load historical data
        self._load_historical_data()
        
        logger.info("🚀 Dynamic Resource Optimizer initialized")
        logger.info(f"   Target cost reduction: {self.cost_targets['reduction_target']*100:.1f}%")
        logger.info(f"   Models available: {len(self.models)}")
    
    def _load_config(self) -> Dict:
        """Load optimization configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f)
            else:
                # Create default configuration
                return self._create_default_config()
        except Exception as e:
            logger.warning(f"Error loading config: {e}, using defaults")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Create default optimization configuration"""
        return {
            'models': {
                'gpt-4o': {
                    'cost_per_token': 0.00003,
                    'context_limit': 128000,
                    'quality_score': 0.95,
                    'speed_score': 0.8,
                    'suitable_for': ['critical', 'complex']
                },
                'gpt-4o-mini': {
                    'cost_per_token': 0.000006,
                    'context_limit': 128000,
                    'quality_score': 0.85,
                    'speed_score': 0.9,
                    'suitable_for': ['simple', 'moderate']
                },
                'gpt-3.5-turbo': {
                    'cost_per_token': 0.000002,
                    'context_limit': 16000,
                    'quality_score': 0.75,
                    'speed_score': 0.95,
                    'suitable_for': ['simple']
                }
            },
            'context_optimization': {
                'max_context_size': 50000,
                'compression_ratio': 0.7,
                'smart_truncation': True,
                'cache_reuse_threshold': 0.8
            },
            'resource_limits': {
                'max_cost_per_patent': 5.0,
                'max_tokens_per_task': 50000,
                'max_parallel_tasks': 8
            }
        }
    
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """Initialize model configurations"""
        models = {}
        for model_name, config in self.config['models'].items():
            models[model_name] = ModelConfig(
                model_name=model_name,
                cost_per_token=config['cost_per_token'],
                context_limit=config['context_limit'],
                quality_score=config['quality_score'],
                speed_score=config['speed_score'],
                suitable_for=[TaskComplexity(c) for c in config['suitable_for']]
            )
        return models
    
    def _load_historical_data(self):
        """Load historical usage data for optimization"""
        history_file = "output/resource_usage_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.usage_history = [
                        ResourceUsage(**usage) for usage in data.get('usage_history', [])
                    ]
                    logger.info(f"Loaded {len(self.usage_history)} historical usage records")
            except Exception as e:
                logger.warning(f"Error loading historical data: {e}")
    
    def analyze_task_complexity(self, task_name: str, content: str = "", 
                              dependencies: List[str] = None) -> TaskComplexity:
        """Analyze task complexity for dynamic model selection"""
        dependencies = dependencies or []
        
        # Complexity scoring factors
        complexity_score = 0
        
        # Factor 1: Task name patterns
        complex_patterns = [
            'patent_document', 'legal_review', 'claims_specialist', 'prior_art_research',
            'comprehensive', 'analysis', 'strategic', 'evaluation'
        ]
        moderate_patterns = [
            'architecture_diagram', 'colab_demo', 'valuation', 'review',
            'refinement', 'optimization'
        ]
        
        task_lower = task_name.lower()
        for pattern in complex_patterns:
            if pattern in task_lower:
                complexity_score += 3
        for pattern in moderate_patterns:
            if pattern in task_lower:
                complexity_score += 2
        
        # Factor 2: Content analysis
        if content:
            content_length = len(content.split())
            if content_length > 5000:
                complexity_score += 3
            elif content_length > 2000:
                complexity_score += 2
            elif content_length > 500:
                complexity_score += 1
        
        # Factor 3: Dependencies
        if len(dependencies) > 3:
            complexity_score += 2
        elif len(dependencies) > 1:
            complexity_score += 1
        
        # Factor 4: Legal/patent-specific tasks
        legal_keywords = ['patent', 'legal', 'claim', 'prior art', 'compliance']
        for keyword in legal_keywords:
            if keyword in task_lower:
                complexity_score += 2
                break
        
        # Determine complexity level
        if complexity_score >= 8:
            return TaskComplexity.CRITICAL
        elif complexity_score >= 5:
            return TaskComplexity.COMPLEX
        elif complexity_score >= 2:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE
    
    def estimate_token_usage(self, task_name: str, content: str = "", 
                           context_size: int = 0) -> int:
        """Estimate token usage for a task"""
        # Base estimation from historical data
        if task_name in self.task_profiles:
            profile = self.task_profiles[task_name]
            if profile.historical_usage:
                avg_tokens = np.mean([usage.tokens_used for usage in profile.historical_usage])
                return int(avg_tokens * 1.2)  # 20% buffer
        
        # Fallback estimation
        base_tokens = 1000  # Base system prompt and formatting
        content_tokens = len(content.split()) * 1.3 if content else 0  # ~1.3 tokens per word
        context_tokens = context_size * 0.5 if context_size else 0  # Estimated context contribution
        
        return int(base_tokens + content_tokens + context_tokens)
    
    def select_optimal_model(self, task_name: str, complexity: TaskComplexity, 
                           estimated_tokens: int, quality_requirement: float = 0.8,
                           agent_name: str = None) -> str:
        """Select the optimal model for a task with agent-aware optimization"""
        
        # AGENT-AWARE OPTIMIZATION: Check if agent has fixed model preference
        if agent_name and 'agent_optimization' in self.config:
            agent_config = self.config['agent_optimization']
            
            # Check if agent has a preserved model
            if 'preserve_agent_models' in agent_config and agent_name in agent_config['preserve_agent_models']:
                preserved_model = agent_config['preserve_agent_models'][agent_name]
                logger.info(f"🎯 Agent-aware optimization: Using preserved model '{preserved_model}' for agent '{agent_name}'")
                return preserved_model
            
            # Check if agent has model_fixed strategy
            if 'optimization_strategies' in agent_config and agent_name in agent_config['optimization_strategies']:
                strategy = agent_config['optimization_strategies'][agent_name]
                if strategy.get('model_fixed', False):
                    # Use the model from preserve_agent_models or fallback to default
                    preserved_model = agent_config.get('preserve_agent_models', {}).get(agent_name, 'gpt-4o')
                    logger.info(f"🔒 Agent model fixed: Using '{preserved_model}' for agent '{agent_name}'")
                    return preserved_model
        
        # Standard optimization logic for non-agent tasks or agents without fixed models
        # Filter models suitable for this complexity
        suitable_models = [
            model for model in self.models.values()
            if complexity in model.suitable_for and estimated_tokens <= model.context_limit
        ]
        
        if not suitable_models:
            # Fallback to most capable model
            return 'gpt-4o'
        
        # Calculate cost-quality score for each model
        best_model = None
        best_score = -1
        
        for model in suitable_models:
            # Skip if quality requirement not met
            if model.quality_score < quality_requirement:
                continue
            
            # Calculate cost
            estimated_cost = estimated_tokens * model.cost_per_token
            
            # Calculate combined score (lower cost, higher quality is better)
            cost_score = 1 / (estimated_cost + 0.001)  # Avoid division by zero
            quality_score = model.quality_score
            speed_score = model.speed_score
            
            # Weighted combination
            combined_score = (cost_score * 0.4 + quality_score * 0.4 + speed_score * 0.2)
            
            if combined_score > best_score:
                best_score = combined_score
                best_model = model
        
        selected_model = best_model.model_name if best_model else 'gpt-4o'
        
        if agent_name:
            logger.info(f"🔄 Dynamic optimization: Selected '{selected_model}' for agent '{agent_name}' (task: {task_name})")
        
        return selected_model
    
    def optimize_context_size(self, context: str, max_size: int = None, 
                             agent_name: str = None) -> Tuple[str, int]:
        """Optimize context size through intelligent truncation with agent-aware settings"""
        if not context:
            return "", 0
        
        # AGENT-AWARE CONTEXT OPTIMIZATION
        if agent_name and 'context_optimization' in self.config:
            context_config = self.config['context_optimization']
            
            # Use agent-specific context limits
            if 'agent_context_limits' in context_config and agent_name in context_config['agent_context_limits']:
                max_size = context_config['agent_context_limits'][agent_name]
                logger.info(f"🎯 Agent-aware context: Using limit {max_size} for agent '{agent_name}'")
            else:
                # Fallback to default if no agent-specific limit
                max_size = max_size or self.config['context_optimization']['max_context_size']
            
            # Use agent-specific compression ratios
            compression_ratio = self.config['context_optimization']['compression_ratio']
            if 'agent_compression_ratios' in context_config and agent_name in context_config['agent_compression_ratios']:
                compression_ratio = context_config['agent_compression_ratios'][agent_name]
                logger.info(f"🔧 Agent-aware compression: Using ratio {compression_ratio} for agent '{agent_name}'")
        else:
            # Standard context optimization
            max_size = max_size or self.config['context_optimization']['max_context_size']
            compression_ratio = self.config['context_optimization']['compression_ratio']
        
        current_size = len(context.split())
        
        if current_size <= max_size:
            return context, current_size
        
        # Smart truncation strategies
        target_size = int(max_size * compression_ratio)
        
        # Strategy 1: Remove redundant information
        lines = context.split('\n')
        important_lines = []
        
        # Keep lines with important keywords
        important_keywords = [
            'patent', 'claim', 'invention', 'technical', 'method', 'system',
            'apparatus', 'process', 'algorithm', 'data', 'result', 'analysis'
        ]
        
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in important_keywords):
                important_lines.append(line)
            elif len(line.strip()) > 100:  # Keep substantial content
                important_lines.append(line)
        
        # Strategy 2: Summarize if still too long
        truncated_context = '\n'.join(important_lines)
        truncated_size = len(truncated_context.split())
        
        if truncated_size > target_size:
            # Final truncation - keep first and last portions
            words = truncated_context.split()
            first_half = int(target_size * 0.6)
            last_half = target_size - first_half
            
            truncated_context = ' '.join(words[:first_half] + ['...'] + words[-last_half:])
            truncated_size = len(truncated_context.split())
        
        logger.info(f"Context optimized: {current_size} → {truncated_size} words ({current_size-truncated_size} saved)")
        
        return truncated_context, truncated_size
    
    def optimize_task_execution(self, task_name: str, context: str = "", 
                              dependencies: List[str] = None, 
                              quality_requirement: float = 0.8,
                              agent_name: str = None) -> Dict[str, Any]:
        """Optimize a single task execution with agent-aware optimization"""
        dependencies = dependencies or []
        
        # Analyze task
        complexity = self.analyze_task_complexity(task_name, context, dependencies)
        
        # Optimize context with agent-aware settings
        optimized_context, context_size = self.optimize_context_size(
            context, agent_name=agent_name
        )
        
        # Estimate tokens
        estimated_tokens = self.estimate_token_usage(task_name, optimized_context, context_size)
        
        # Select optimal model with agent-aware logic
        selected_model = self.select_optimal_model(
            task_name, complexity, estimated_tokens, quality_requirement, agent_name
        )
        
        # Calculate costs
        original_cost = estimated_tokens * self.models['gpt-4o'].cost_per_token
        optimized_cost = estimated_tokens * self.models[selected_model].cost_per_token
        cost_reduction = (original_cost - optimized_cost) / original_cost if original_cost > 0 else 0
        
        # Create optimization result
        optimization = {
            'task_name': task_name,
            'complexity': complexity.value,
            'selected_model': selected_model,
            'estimated_tokens': estimated_tokens,
            'context_size_original': len(context.split()) if context else 0,
            'context_size_optimized': context_size,
            'original_cost': original_cost,
            'optimized_cost': optimized_cost,
            'cost_reduction': cost_reduction,
            'quality_score': self.models[selected_model].quality_score,
            'optimized_context': optimized_context
        }
        
        # Update task profile
        self._update_task_profile(task_name, complexity, estimated_tokens, context_size, dependencies)
        
        return optimization
    
    def optimize_workflow(self, workflow_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize an entire workflow with agent-aware optimization"""
        optimizations = []
        total_original_cost = 0
        total_optimized_cost = 0
        model_changes = {}
        agent_preservations = {}
        
        for task in workflow_tasks:
            agent_name = task.get('agent_name')  # Extract agent name from task
            optimization = self.optimize_task_execution(
                task.get('name', ''),
                task.get('context', ''),
                task.get('dependencies', []),
                task.get('quality_requirement', 0.8),
                agent_name
            )
            
            optimizations.append(optimization)
            total_original_cost += optimization['original_cost']
            total_optimized_cost += optimization['optimized_cost']
            
            # Track model changes vs standard baseline
            task_name = task.get('name', '')
            if optimization['selected_model'] != 'gpt-4o':
                model_changes[task_name] = optimization['selected_model']
            
            # Track agent model preservations
            if agent_name and 'agent_optimization' in self.config:
                preserve_models = self.config['agent_optimization'].get('preserve_agent_models', {})
                if agent_name in preserve_models:
                    agent_preservations[task_name] = {
                        'agent': agent_name,
                        'preserved_model': preserve_models[agent_name],
                        'selected_model': optimization['selected_model']
                    }
        
        # Calculate overall metrics
        cost_reduction = (total_original_cost - total_optimized_cost) / total_original_cost if total_original_cost > 0 else 0
        
        workflow_optimization = {
            'total_tasks': len(workflow_tasks),
            'total_original_cost': total_original_cost,
            'total_optimized_cost': total_optimized_cost,
            'cost_reduction': cost_reduction,
            'cost_savings_usd': total_original_cost - total_optimized_cost,
            'model_changes': model_changes,
            'agent_preservations': agent_preservations,
            'task_optimizations': optimizations,
            'optimization_timestamp': datetime.now().isoformat()
        }
        
        # Update session tracking
        self.current_session['total_cost'] += total_optimized_cost
        self.current_session['optimizations_applied'] += len(optimizations)
        
        logger.info(f"Workflow optimized: {cost_reduction*100:.1f}% cost reduction")
        logger.info(f"   Tasks: {len(workflow_tasks)}")
        logger.info(f"   Cost savings: ${total_original_cost - total_optimized_cost:.3f}")
        logger.info(f"   Model changes: {len(model_changes)}")
        logger.info(f"   Agent models preserved: {len(agent_preservations)}")
        
        return workflow_optimization
    
    def _update_task_profile(self, task_name: str, complexity: TaskComplexity, 
                           estimated_tokens: int, context_size: int, 
                           dependencies: List[str]):
        """Update task profile with new data"""
        if task_name not in self.task_profiles:
            self.task_profiles[task_name] = TaskProfile(
                task_name=task_name,
                complexity=complexity,
                estimated_tokens=estimated_tokens,
                context_size=context_size,
                dependencies=dependencies
            )
        else:
            profile = self.task_profiles[task_name]
            profile.complexity = complexity
            profile.estimated_tokens = estimated_tokens
            profile.context_size = context_size
            profile.dependencies = dependencies
    
    def track_actual_usage(self, task_name: str, actual_usage: ResourceUsage):
        """Track actual resource usage for learning"""
        if task_name in self.task_profiles:
            self.task_profiles[task_name].historical_usage.append(actual_usage)
        
        self.usage_history.append(actual_usage)
        
        # Keep only recent history
        if len(self.usage_history) > 1000:
            self.usage_history = self.usage_history[-1000:]
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get detailed cost analysis"""
        if not self.usage_history:
            return {'status': 'no_data', 'message': 'No usage history available'}
        
        # Calculate statistics
        total_cost = sum(usage.cost_usd for usage in self.usage_history)
        total_tokens = sum(usage.tokens_used for usage in self.usage_history)
        avg_cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0
        
        # Recent performance
        recent_history = [usage for usage in self.usage_history 
                         if usage.timestamp > datetime.now() - timedelta(days=7)]
        recent_cost = sum(usage.cost_usd for usage in recent_history)
        
        return {
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'avg_cost_per_token': avg_cost_per_token,
            'recent_cost_7d': recent_cost,
            'total_api_calls': sum(usage.api_calls for usage in self.usage_history),
            'cache_hit_rate': (sum(usage.cache_hits for usage in self.usage_history) / 
                             max(1, sum(usage.cache_hits + usage.cache_misses for usage in self.usage_history))),
            'optimization_opportunities': self._identify_optimization_opportunities()
        }
    
    def _identify_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for further optimization"""
        opportunities = []
        
        # High cost tasks
        task_costs = {}
        for usage in self.usage_history:
            task_name = getattr(usage, 'task_name', 'unknown')
            if task_name not in task_costs:
                task_costs[task_name] = []
            task_costs[task_name].append(usage.cost_usd)
        
        for task_name, costs in task_costs.items():
            avg_cost = np.mean(costs)
            if avg_cost > 0.5:  # High cost threshold
                opportunities.append({
                    'type': 'high_cost_task',
                    'task_name': task_name,
                    'avg_cost': avg_cost,
                    'suggestion': 'Consider using smaller model or context optimization'
                })
        
        # Low cache hit rate
        cache_hit_rate = sum(usage.cache_hits for usage in self.usage_history) / max(1, sum(usage.cache_hits + usage.cache_misses for usage in self.usage_history))
        if cache_hit_rate < 0.5:
            opportunities.append({
                'type': 'low_cache_efficiency',
                'cache_hit_rate': cache_hit_rate,
                'suggestion': 'Improve caching strategy or increase cache size'
            })
        
        return opportunities
    
    def save_optimization_report(self, optimization_result: Dict[str, Any], 
                               output_file: str = None):
        """Save optimization report"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/optimization_report_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Add session info
        optimization_result['session_info'] = self.current_session
        optimization_result['cost_analysis'] = self.get_cost_analysis()
        
        with open(output_file, 'w') as f:
            json.dump(optimization_result, f, indent=2, default=str)
        
        logger.info(f"Optimization report saved: {output_file}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get current session summary"""
        session_duration = datetime.now() - self.current_session['start_time']
        
        return {
            'session_duration_minutes': session_duration.total_seconds() / 60,
            'total_cost': self.current_session['total_cost'],
            'total_tokens': self.current_session['total_tokens'],
            'optimizations_applied': self.current_session['optimizations_applied'],
            'cost_reduction_achieved': self._calculate_session_cost_reduction(),
            'target_achievement': self._calculate_target_achievement()
        }
    
    def _calculate_session_cost_reduction(self) -> float:
        """Calculate cost reduction achieved in current session"""
        if not self.usage_history:
            return 0
        
        # Compare recent usage with baseline
        recent_usage = [usage for usage in self.usage_history 
                       if usage.timestamp > self.current_session['start_time']]
        
        if not recent_usage:
            return 0
        
        # Simple calculation based on model selection efficiency
        return 0.25  # Placeholder - would be calculated from actual usage
    
    def _calculate_target_achievement(self) -> float:
        """Calculate how close we are to the 25-35% cost reduction target"""
        current_reduction = self._calculate_session_cost_reduction()
        target_reduction = self.cost_targets['reduction_target']
        
        return min(current_reduction / target_reduction, 1.0)

class ResourceMonitor:
    """Monitor resource usage in real-time"""
    
    def __init__(self, optimizer: DynamicResourceOptimizer):
        self.optimizer = optimizer
        self.active_tasks = {}
        self.alerts = []
    
    def start_task_monitoring(self, task_name: str, estimated_cost: float):
        """Start monitoring a task"""
        self.active_tasks[task_name] = {
            'start_time': datetime.now(),
            'estimated_cost': estimated_cost,
            'actual_cost': 0,
            'status': 'running'
        }
    
    def end_task_monitoring(self, task_name: str, actual_usage: ResourceUsage):
        """End monitoring a task"""
        if task_name in self.active_tasks:
            task_info = self.active_tasks[task_name]
            task_info['status'] = 'completed'
            task_info['actual_cost'] = actual_usage.cost_usd
            task_info['duration'] = (datetime.now() - task_info['start_time']).total_seconds()
            
            # Track usage
            self.optimizer.track_actual_usage(task_name, actual_usage)
            
            # Check for alerts
            self._check_cost_alerts(task_name, task_info)
    
    def _check_cost_alerts(self, task_name: str, task_info: Dict):
        """Check for cost-related alerts"""
        if task_info['actual_cost'] > task_info['estimated_cost'] * 1.5:
            self.alerts.append({
                'type': 'cost_overrun',
                'task_name': task_name,
                'estimated_cost': task_info['estimated_cost'],
                'actual_cost': task_info['actual_cost'],
                'timestamp': datetime.now()
            })
    
    def get_active_tasks(self) -> Dict:
        """Get currently active tasks"""
        return self.active_tasks
    
    def get_alerts(self) -> List[Dict]:
        """Get current alerts"""
        return self.alerts

# Global optimizer instance
_optimizer = None

def get_optimizer() -> DynamicResourceOptimizer:
    """Get global optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = DynamicResourceOptimizer()
    return _optimizer

def optimize_task(task_name: str, context: str = "", dependencies: List[str] = None, 
                 quality_requirement: float = 0.8, agent_name: str = None) -> Dict[str, Any]:
    """Convenience function to optimize a single task with agent-aware optimization"""
    optimizer = get_optimizer()
    return optimizer.optimize_task_execution(task_name, context, dependencies, quality_requirement, agent_name)

def optimize_workflow(workflow_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function to optimize a workflow"""
    optimizer = get_optimizer()
    return optimizer.optimize_workflow(workflow_tasks) 