"""
Smart Token Allocation System
Intelligent token budgeting and allocation for cost optimization
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

class AllocationStrategy(Enum):
    """Token allocation strategies"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"

class PriorityLevel(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class TokenBudget:
    """Token budget for a specific scope"""
    total_tokens: int
    allocated_tokens: int = 0
    used_tokens: int = 0
    reserved_tokens: int = 0
    emergency_tokens: int = 0
    
    @property
    def available_tokens(self) -> int:
        return self.total_tokens - self.allocated_tokens - self.reserved_tokens
    
    @property
    def utilization_rate(self) -> float:
        return self.used_tokens / self.total_tokens if self.total_tokens > 0 else 0
    
    @property
    def allocation_rate(self) -> float:
        return self.allocated_tokens / self.total_tokens if self.total_tokens > 0 else 0

@dataclass
class TokenAllocation:
    """Token allocation for a specific task"""
    task_id: str
    task_name: str
    priority: PriorityLevel
    base_allocation: int
    bonus_allocation: int = 0
    emergency_allocation: int = 0
    quality_multiplier: float = 1.0
    complexity_multiplier: float = 1.0
    deadline_multiplier: float = 1.0
    
    @property
    def total_allocation(self) -> int:
        return self.base_allocation + self.bonus_allocation + self.emergency_allocation
    
    @property
    def effective_allocation(self) -> int:
        multiplier = self.quality_multiplier * self.complexity_multiplier * self.deadline_multiplier
        return int(self.total_allocation * multiplier)

@dataclass
class AllocationHistory:
    """Historical allocation data"""
    timestamp: datetime
    task_id: str
    allocated_tokens: int
    used_tokens: int
    efficiency_score: float
    cost_usd: float
    quality_score: float

class SmartTokenAllocator:
    """Smart token allocation system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.budgets = {}  # Budget per scope (patent, tier, session)
        self.allocations = {}  # Active allocations
        self.history = []  # Historical allocations
        self.strategy = AllocationStrategy.ADAPTIVE
        self.session_start = datetime.now()
        
        # Initialize budgets
        self._initialize_budgets()
        
        # Load historical data
        self._load_historical_data()
        
        logger.info("🎯 Smart Token Allocator initialized")
        logger.info(f"   Strategy: {self.strategy.value}")
        logger.info(f"   Budgets: {len(self.budgets)}")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'allocation_strategy': 'adaptive',
            'base_allocations': {
                'patent_document': 25000,
                'patent_researcher': 20000,
                'claims_specialist': 15000,
                'legal_reviewer': 12000,
                'final_reviewer': 10000,
                'cover_sheet_specialist': 5000,
                'architecture_diagram': 8000,
                'colab_demo': 12000,
                'valuation': 10000
            },
            'priority_multipliers': {
                'LOW': 0.8,
                'MEDIUM': 1.0,
                'HIGH': 1.3,
                'CRITICAL': 1.8
            },
            'complexity_multipliers': {
                'simple': 0.7,
                'moderate': 1.0,
                'complex': 1.4,
                'critical': 2.0
            },
            'quality_multipliers': {
                0.7: 0.8,
                0.8: 1.0,
                0.9: 1.3,
                0.95: 1.6
            },
            'emergency_reserve': 0.15,  # 15% emergency reserve
            'efficiency_threshold': 0.8,
            'reallocation_threshold': 0.3,
            'budget_buffer': 0.1  # 10% buffer
        }
    
    def _initialize_budgets(self):
        """Initialize token budgets for different scopes"""
        # Session budget
        self.budgets['session'] = TokenBudget(
            total_tokens=self.config.get('session_budget', 1000000),
            emergency_tokens=int(self.config.get('session_budget', 1000000) * 0.1)
        )
        
        # Patent budget (per patent)
        self.budgets['patent'] = TokenBudget(
            total_tokens=self.config.get('patent_budget', 200000),
            emergency_tokens=int(self.config.get('patent_budget', 200000) * 0.1)
        )
        
        # Task budget (per task type)
        for task_name, base_tokens in self.config['base_allocations'].items():
            self.budgets[f'task_{task_name}'] = TokenBudget(
                total_tokens=base_tokens,
                emergency_tokens=int(base_tokens * 0.1)
            )
    
    def _load_historical_data(self):
        """Load historical allocation data"""
        history_file = "output/token_allocation_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.history = [
                        AllocationHistory(**item) for item in data.get('history', [])
                    ]
                    logger.info(f"Loaded {len(self.history)} historical allocations")
            except Exception as e:
                logger.warning(f"Error loading historical data: {e}")
    
    def estimate_token_requirement(self, task_name: str, context_size: int = 0, 
                                 complexity: str = 'moderate', 
                                 quality_requirement: float = 0.8) -> int:
        """Estimate token requirement for a task"""
        # Base allocation
        base_tokens = self.config['base_allocations'].get(task_name, 10000)
        
        # Apply multipliers
        complexity_multiplier = self.config['complexity_multipliers'].get(complexity, 1.0)
        quality_multiplier = self._get_quality_multiplier(quality_requirement)
        
        # Context factor
        context_factor = 1.0 + (context_size / 50000)  # Add 100% for every 50k context
        
        # Historical efficiency
        efficiency_factor = self._get_efficiency_factor(task_name)
        
        # Calculate estimate
        estimated_tokens = int(
            base_tokens * 
            complexity_multiplier * 
            quality_multiplier * 
            context_factor * 
            efficiency_factor
        )
        
        logger.debug(f"Token estimate for {task_name}: {estimated_tokens}")
        logger.debug(f"  Base: {base_tokens}, Complexity: {complexity_multiplier:.2f}")
        logger.debug(f"  Quality: {quality_multiplier:.2f}, Context: {context_factor:.2f}")
        logger.debug(f"  Efficiency: {efficiency_factor:.2f}")
        
        return estimated_tokens
    
    def _get_quality_multiplier(self, quality_requirement: float) -> float:
        """Get quality multiplier based on requirement"""
        quality_multipliers = self.config['quality_multipliers']
        
        # Find closest quality level
        closest_level = min(quality_multipliers.keys(), 
                          key=lambda x: abs(x - quality_requirement))
        
        return quality_multipliers[closest_level]
    
    def _get_efficiency_factor(self, task_name: str) -> float:
        """Get efficiency factor based on historical data"""
        if not self.history:
            return 1.0
        
        # Filter historical data for this task
        task_history = [h for h in self.history if task_name in h.task_id]
        
        if not task_history:
            return 1.0
        
        # Calculate average efficiency
        efficiencies = [h.efficiency_score for h in task_history]
        avg_efficiency = np.mean(efficiencies)
        
        # Convert to allocation factor (lower efficiency = need more tokens)
        efficiency_factor = 1.0 / max(avg_efficiency, 0.1)
        
        return min(efficiency_factor, 2.0)  # Cap at 2x
    
    def allocate_tokens(self, task_name: str, task_id: str, 
                       priority: PriorityLevel = PriorityLevel.MEDIUM,
                       complexity: str = 'moderate',
                       quality_requirement: float = 0.8,
                       context_size: int = 0,
                       deadline_urgency: float = 1.0) -> TokenAllocation:
        """Allocate tokens for a specific task"""
        
        # Estimate base requirement
        base_tokens = self.estimate_token_requirement(
            task_name, context_size, complexity, quality_requirement
        )
        
        # Apply priority multiplier
        priority_multiplier = self.config['priority_multipliers'].get(priority.name, 1.0)
        
        # Calculate allocation
        allocation = TokenAllocation(
            task_id=task_id,
            task_name=task_name,
            priority=priority,
            base_allocation=base_tokens,
            quality_multiplier=self._get_quality_multiplier(quality_requirement),
            complexity_multiplier=self.config['complexity_multipliers'].get(complexity, 1.0),
            deadline_multiplier=deadline_urgency
        )
        
        # Apply adaptive adjustments
        if self.strategy == AllocationStrategy.ADAPTIVE:
            allocation = self._apply_adaptive_adjustments(allocation)
        
        # Check budget availability
        if not self._check_budget_availability(allocation):
            allocation = self._optimize_allocation(allocation)
        
        # Reserve tokens
        self._reserve_tokens(allocation)
        
        # Store allocation
        self.allocations[task_id] = allocation
        
        logger.info(f"Allocated {allocation.effective_allocation} tokens for {task_name} ({task_id})")
        logger.info(f"  Priority: {priority.name}, Complexity: {complexity}")
        logger.info(f"  Quality: {quality_requirement:.2f}, Deadline: {deadline_urgency:.2f}")
        
        return allocation
    
    def _apply_adaptive_adjustments(self, allocation: TokenAllocation) -> TokenAllocation:
        """Apply adaptive adjustments based on current conditions"""
        
        # Check current utilization
        session_utilization = self.budgets['session'].utilization_rate
        
        if session_utilization > 0.8:
            # High utilization - reduce allocation
            allocation.base_allocation = int(allocation.base_allocation * 0.9)
            logger.debug(f"Reduced allocation due to high utilization: {session_utilization:.2f}")
        elif session_utilization < 0.3:
            # Low utilization - can afford to increase
            allocation.bonus_allocation = int(allocation.base_allocation * 0.1)
            logger.debug(f"Bonus allocation due to low utilization: {session_utilization:.2f}")
        
        # Time-based adjustments
        session_duration = (datetime.now() - self.session_start).total_seconds() / 3600
        if session_duration > 2:  # After 2 hours, be more conservative
            allocation.base_allocation = int(allocation.base_allocation * 0.95)
        
        return allocation
    
    def _check_budget_availability(self, allocation: TokenAllocation) -> bool:
        """Check if budget is available for allocation"""
        required_tokens = allocation.effective_allocation
        
        # Check session budget
        session_budget = self.budgets['session']
        if session_budget.available_tokens < required_tokens:
            logger.warning(f"Insufficient session budget: {session_budget.available_tokens} < {required_tokens}")
            return False
        
        # Check patent budget
        patent_budget = self.budgets['patent']
        if patent_budget.available_tokens < required_tokens:
            logger.warning(f"Insufficient patent budget: {patent_budget.available_tokens} < {required_tokens}")
            return False
        
        return True
    
    def _optimize_allocation(self, allocation: TokenAllocation) -> TokenAllocation:
        """Optimize allocation when budget is insufficient"""
        
        # Strategy 1: Reduce base allocation
        if allocation.priority != PriorityLevel.CRITICAL:
            allocation.base_allocation = int(allocation.base_allocation * 0.8)
            logger.info(f"Reduced base allocation to {allocation.base_allocation}")
        
        # Strategy 2: Remove bonus allocation
        if allocation.bonus_allocation > 0:
            allocation.bonus_allocation = 0
            logger.info("Removed bonus allocation")
        
        # Strategy 3: Use emergency tokens if critical
        if allocation.priority == PriorityLevel.CRITICAL:
            emergency_tokens = min(
                allocation.base_allocation * 0.2,
                self.budgets['session'].emergency_tokens
            )
            allocation.emergency_allocation = int(emergency_tokens)
            logger.info(f"Added emergency allocation: {emergency_tokens}")
        
        return allocation
    
    def _reserve_tokens(self, allocation: TokenAllocation):
        """Reserve tokens for allocation"""
        tokens_to_reserve = allocation.effective_allocation
        
        # Reserve from session budget
        self.budgets['session'].allocated_tokens += tokens_to_reserve
        
        # Reserve from patent budget
        self.budgets['patent'].allocated_tokens += tokens_to_reserve
        
        # Reserve from task budget
        task_budget_key = f'task_{allocation.task_name}'
        if task_budget_key in self.budgets:
            self.budgets[task_budget_key].allocated_tokens += tokens_to_reserve
    
    def track_usage(self, task_id: str, tokens_used: int, 
                   cost_usd: float, quality_score: float):
        """Track actual token usage"""
        
        if task_id not in self.allocations:
            logger.warning(f"No allocation found for task {task_id}")
            return
        
        allocation = self.allocations[task_id]
        
        # Update budgets
        self.budgets['session'].used_tokens += tokens_used
        self.budgets['patent'].used_tokens += tokens_used
        
        task_budget_key = f'task_{allocation.task_name}'
        if task_budget_key in self.budgets:
            self.budgets[task_budget_key].used_tokens += tokens_used
        
        # Calculate efficiency
        efficiency_score = min(allocation.effective_allocation / max(tokens_used, 1), 2.0)
        
        # Store in history
        history_entry = AllocationHistory(
            timestamp=datetime.now(),
            task_id=task_id,
            allocated_tokens=allocation.effective_allocation,
            used_tokens=tokens_used,
            efficiency_score=efficiency_score,
            cost_usd=cost_usd,
            quality_score=quality_score
        )
        
        self.history.append(history_entry)
        
        # Log usage
        logger.info(f"Token usage tracked for {task_id}:")
        logger.info(f"  Allocated: {allocation.effective_allocation}, Used: {tokens_used}")
        logger.info(f"  Efficiency: {efficiency_score:.2f}, Cost: ${cost_usd:.3f}")
        logger.info(f"  Quality: {quality_score:.2f}")
        
        # Check for reallocation opportunities
        self._check_reallocation_opportunities(allocation, efficiency_score)
    
    def _check_reallocation_opportunities(self, allocation: TokenAllocation, 
                                        efficiency_score: float):
        """Check for reallocation opportunities"""
        
        # If efficiency is very low, consider reallocating
        if efficiency_score < self.config['efficiency_threshold']:
            logger.warning(f"Low efficiency detected for {allocation.task_name}: {efficiency_score:.2f}")
            
            # Reduce future allocations for this task type
            task_budget_key = f'task_{allocation.task_name}'
            if task_budget_key in self.budgets:
                budget = self.budgets[task_budget_key]
                budget.total_tokens = int(budget.total_tokens * 0.9)
                logger.info(f"Reduced future budget for {allocation.task_name}")
        
        # If efficiency is very high, consider increasing allocation
        elif efficiency_score > 1.5:
            logger.info(f"High efficiency detected for {allocation.task_name}: {efficiency_score:.2f}")
            
            # Increase future allocations for this task type
            task_budget_key = f'task_{allocation.task_name}'
            if task_budget_key in self.budgets:
                budget = self.budgets[task_budget_key]
                budget.total_tokens = int(budget.total_tokens * 1.1)
                logger.info(f"Increased future budget for {allocation.task_name}")
    
    def get_allocation_summary(self) -> Dict[str, Any]:
        """Get allocation summary"""
        
        total_allocated = sum(alloc.effective_allocation for alloc in self.allocations.values())
        total_used = sum(self.budgets[key].used_tokens for key in self.budgets)
        
        # Calculate efficiency metrics
        if self.history:
            avg_efficiency = np.mean([h.efficiency_score for h in self.history])
            avg_cost = np.mean([h.cost_usd for h in self.history])
            avg_quality = np.mean([h.quality_score for h in self.history])
        else:
            avg_efficiency = avg_cost = avg_quality = 0
        
        return {
            'total_allocated': total_allocated,
            'total_used': total_used,
            'utilization_rate': total_used / max(total_allocated, 1),
            'active_allocations': len(self.allocations),
            'avg_efficiency': avg_efficiency,
            'avg_cost': avg_cost,
            'avg_quality': avg_quality,
            'budget_status': {
                name: {
                    'total': budget.total_tokens,
                    'allocated': budget.allocated_tokens,
                    'used': budget.used_tokens,
                    'available': budget.available_tokens,
                    'utilization': budget.utilization_rate
                }
                for name, budget in self.budgets.items()
            }
        }
    
    def optimize_remaining_allocations(self) -> Dict[str, int]:
        """Optimize remaining token allocations"""
        
        optimizations = {}
        
        # Check for underutilized budgets
        for name, budget in self.budgets.items():
            if budget.utilization_rate < 0.3 and budget.allocated_tokens > 0:
                # Reallocate some tokens
                tokens_to_reallocate = int(budget.allocated_tokens * 0.2)
                budget.allocated_tokens -= tokens_to_reallocate
                optimizations[name] = tokens_to_reallocate
                logger.info(f"Reallocated {tokens_to_reallocate} tokens from {name}")
        
        return optimizations
    
    def save_allocation_data(self, output_file: str = None):
        """Save allocation data"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/token_allocation_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        data = {
            'config': self.config,
            'budgets': {
                name: {
                    'total_tokens': budget.total_tokens,
                    'allocated_tokens': budget.allocated_tokens,
                    'used_tokens': budget.used_tokens,
                    'reserved_tokens': budget.reserved_tokens,
                    'emergency_tokens': budget.emergency_tokens
                }
                for name, budget in self.budgets.items()
            },
            'allocations': {
                task_id: {
                    'task_name': alloc.task_name,
                    'priority': alloc.priority.name,
                    'base_allocation': alloc.base_allocation,
                    'bonus_allocation': alloc.bonus_allocation,
                    'emergency_allocation': alloc.emergency_allocation,
                    'effective_allocation': alloc.effective_allocation
                }
                for task_id, alloc in self.allocations.items()
            },
            'history': [
                {
                    'timestamp': h.timestamp.isoformat(),
                    'task_id': h.task_id,
                    'allocated_tokens': h.allocated_tokens,
                    'used_tokens': h.used_tokens,
                    'efficiency_score': h.efficiency_score,
                    'cost_usd': h.cost_usd,
                    'quality_score': h.quality_score
                }
                for h in self.history
            ],
            'session_summary': self.get_allocation_summary()
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Allocation data saved: {output_file}")
    
    def get_cost_projection(self, remaining_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get cost projection for remaining tasks"""
        
        total_estimated_tokens = 0
        total_estimated_cost = 0
        
        for task in remaining_tasks:
            estimated_tokens = self.estimate_token_requirement(
                task.get('name', ''),
                task.get('context_size', 0),
                task.get('complexity', 'moderate'),
                task.get('quality_requirement', 0.8)
            )
            
            # Estimate cost based on model selection
            model_cost_per_token = 0.00003  # gpt-4o default
            if task.get('model') == 'gpt-4o-mini':
                model_cost_per_token = 0.000006
            elif task.get('model') == 'gpt-3.5-turbo':
                model_cost_per_token = 0.000002
            
            estimated_cost = estimated_tokens * model_cost_per_token
            
            total_estimated_tokens += estimated_tokens
            total_estimated_cost += estimated_cost
        
        return {
            'total_estimated_tokens': total_estimated_tokens,
            'total_estimated_cost': total_estimated_cost,
            'remaining_budget_tokens': self.budgets['session'].available_tokens,
            'budget_sufficient': total_estimated_tokens <= self.budgets['session'].available_tokens,
            'cost_per_task': total_estimated_cost / max(len(remaining_tasks), 1),
            'tasks_count': len(remaining_tasks)
        }

# Global allocator instance
_allocator = None

def get_allocator() -> SmartTokenAllocator:
    """Get global allocator instance"""
    global _allocator
    if _allocator is None:
        _allocator = SmartTokenAllocator()
    return _allocator

def allocate_tokens(task_name: str, task_id: str, **kwargs) -> TokenAllocation:
    """Convenience function to allocate tokens"""
    allocator = get_allocator()
    return allocator.allocate_tokens(task_name, task_id, **kwargs)

def track_usage(task_id: str, tokens_used: int, cost_usd: float, quality_score: float):
    """Convenience function to track usage"""
    allocator = get_allocator()
    return allocator.track_usage(task_id, tokens_used, cost_usd, quality_score) 