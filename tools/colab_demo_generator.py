import os
import json
from typing import Dict, Any, List
from crewai.tools import BaseTool
import logging
from datetime import datetime
import nbformat

# Import from lib modules
from lib.validation import validate_patent_dict

# --- New helper functions for dynamic claim analysis and editorial review ---
def select_claim_to_demonstrate(key_claims: List[str]) -> str:
    """
    Select the most implementable claim for demonstration.
    Prioritizes claims that can showcase substantial code implementations.
    """
    if not key_claims:
        return "No claims provided"
    
    # Priority keywords for selecting claims (in order of preference)
    priority_keywords = [
        ['semantic', 'agent', 'reasoning'],       # Semantic agent claims
        ['multi-agent', 'coordination'],          # Multi-agent coordination
        ['gpu', 'acceleration', 'processing'],    # GPU acceleration
        ['optimization', 'system'],               # General optimization
        ['method', 'architecture'],               # Method/architecture claims
    ]
    
    # Score each claim based on priority keywords
    claim_scores = []
    for i, claim in enumerate(key_claims):
        score = 0
        claim_lower = claim.lower()
        
        # Check each priority keyword set
        for priority_level, keywords in enumerate(priority_keywords):
            if any(keyword in claim_lower for keyword in keywords):
                # Higher priority = higher score (reverse priority_level)
                score = len(priority_keywords) - priority_level
                # Bonus for multiple matching keywords
                matches = sum(1 for keyword in keywords if keyword in claim_lower)
                score += matches * 0.5
                break
        
        claim_scores.append((score, i, claim))
    
    # Select the highest scoring claim
    claim_scores.sort(key=lambda x: x[0], reverse=True)
    selected_claim = claim_scores[0][2]
    
    print(f"Selected claim for demonstration: {selected_claim}")
    return selected_claim

def generate_code_for_claim(claim: str, accepted_suggestions: List[str] = None) -> str:
    """
    Generate substantive code implementation for a patent claim.
    Integrates accepted editorial suggestions into the actual implementation.
    """
    accepted_suggestions = accepted_suggestions or []
    
    # Check for improvement suggestions
    needs_error_handling = any("error handling" in s.lower() for s in accepted_suggestions)
    needs_documentation = any("documentation" in s.lower() for s in accepted_suggestions)
    needs_benchmarks = any("benchmark" in s.lower() or "performance" in s.lower() for s in accepted_suggestions)
    needs_visualization = any("visualiz" in s.lower() for s in accepted_suggestions)
    
    # Enhanced pattern matching for claim types
    claim_lower = claim.lower()
    
    # Check for semantic agent claims (more flexible matching)
    if any(keyword in claim_lower for keyword in ['semantic', 'agent', 'reasoning', 'autonomous']):
        code = []
        
        # Add comprehensive imports
        code.append("import time\nimport logging\nimport numpy as np\nimport matplotlib.pyplot as plt\nfrom typing import Dict, List, Any, Optional\nfrom dataclasses import dataclass\nfrom abc import ABC, abstractmethod\n")
        
        # Add error handling classes if requested
        if needs_error_handling:
            code.append("""
class OptimizationError(Exception):
    \"\"\"Custom exception for optimization failures\"\"\"
    pass

class AgentCommunicationError(Exception):
    \"\"\"Custom exception for agent communication failures\"\"\"
    pass
""")
        
        # Add documentation if requested
        if needs_documentation:
            code.append('"""\nSemantic Agent Optimization System\n\nThis implementation demonstrates a semantic agent system for neural network optimization\nusing natural language reasoning and priority-weighted decision protocols.\n\nKey Features:\n- Semantic reasoning engine with natural language processing\n- Multi-agent coordination with priority weighting\n- Performance monitoring and benchmarking\n- Error handling and fault tolerance\n"""\n')
        
        # Main implementation with error handling
        code.append("""
@dataclass
class OptimizationResult:
    \"\"\"Result of an optimization operation\"\"\"
    parameters: Dict[str, float]
    performance_score: float
    decision_time_ms: float
    reasoning_trace: List[str]

class SemanticAgent:
    \"\"\"
    A semantic agent that performs optimization using natural language reasoning
    and coordinates with other agents through priority-weighted protocols.
    \"\"\"
    
    def __init__(self, knowledge_base: List[str], agent_id: str = "agent_1", priority: float = 1.0):
        self.knowledge_base = knowledge_base
        self.agent_id = agent_id
        self.priority = priority
        self.optimization_history = []
        self.performance_metrics = []
        
        # Initialize logging if error handling is enabled
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"SemanticAgent_{agent_id}")
        
    def reason(self, problem: str, context: Dict[str, Any] = None) -> str:
        \"\"\"
        Perform semantic reasoning about an optimization problem
        \"\"\"
        try:
            start_time = time.time()
            
            # Simulate semantic reasoning process
            reasoning_steps = []
            reasoning_steps.append(f"Analyzing problem: {problem}")
            
            # Apply knowledge base
            relevant_knowledge = [k for k in self.knowledge_base if any(word in k.lower() for word in problem.lower().split())]
            reasoning_steps.append(f"Relevant knowledge: {relevant_knowledge}")
            
            # Generate reasoning conclusion
            conclusion = f"Optimization approach: Apply {relevant_knowledge[0] if relevant_knowledge else 'general optimization'} to {problem}"
            reasoning_steps.append(f"Conclusion: {conclusion}")
            
            decision_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log performance if benchmarking enabled
            if hasattr(self, 'performance_metrics'):
                self.performance_metrics.append({
                    'problem': problem,
                    'decision_time_ms': decision_time,
                    'reasoning_steps': len(reasoning_steps)
                })
            
            return conclusion
            
        except Exception as e:
            self.logger.error(f"Reasoning failed for problem '{problem}': {str(e)}")
            raise OptimizationError(f"Failed to reason about problem: {str(e)}")
    
    def optimize_neural_network(self, network_config: Dict[str, Any]) -> OptimizationResult:
        \"\"\"
        Optimize neural network parameters using semantic reasoning
        \"\"\"
        try:
            start_time = time.time()
            
            # Simulate optimization process
            reasoning_trace = []
            reasoning_trace.append("Starting neural network optimization")
            
            # Apply semantic reasoning to determine optimization strategy
            problem_description = f"Optimize neural network with {network_config.get('layers', 'unknown')} layers"
            strategy = self.reason(problem_description)
            reasoning_trace.append(f"Strategy: {strategy}")
            
            # Simulate parameter optimization
            optimized_params = {}
            for param_name, current_value in network_config.items():
                if isinstance(current_value, (int, float)):
                    # Apply semantic optimization logic
                    if "learning_rate" in param_name.lower():
                        optimized_params[param_name] = current_value * 0.9  # Reduce learning rate
                    elif "batch_size" in param_name.lower():
                        optimized_params[param_name] = min(current_value * 2, 128)  # Increase batch size
                    else:
                        optimized_params[param_name] = current_value
                else:
                    optimized_params[param_name] = current_value
            
            reasoning_trace.append(f"Optimized parameters: {optimized_params}")
            
            # Calculate performance score (simulated)
            performance_score = np.random.uniform(0.85, 0.95)  # Simulate improvement
            decision_time = (time.time() - start_time) * 1000
            
            reasoning_trace.append(f"Performance score: {performance_score:.3f}")
            reasoning_trace.append(f"Decision time: {decision_time:.2f}ms")
            
            result = OptimizationResult(
                parameters=optimized_params,
                performance_score=performance_score,
                decision_time_ms=decision_time,
                reasoning_trace=reasoning_trace
            )
            
            self.optimization_history.append(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {str(e)}")
            raise OptimizationError(f"Neural network optimization failed: {str(e)}")
    
    def get_performance_stats(self) -> Dict[str, float]:
        \"\"\"Get performance statistics for benchmarking\"\"\"
        if not self.performance_metrics:
            return {"avg_decision_time_ms": 0, "total_decisions": 0}
        
        avg_time = np.mean([m['decision_time_ms'] for m in self.performance_metrics])
        return {
            "avg_decision_time_ms": avg_time,
            "total_decisions": len(self.performance_metrics),
            "sub_5ms_decisions": sum(1 for m in self.performance_metrics if m['decision_time_ms'] < 5)
        }
""")
        
        # Add demonstration code
        code.append("""
# Demonstration of the semantic agent system
print("=== Semantic Agent Optimization System Demo ===\\n")

# Initialize semantic agent with knowledge base
agent = SemanticAgent(
    knowledge_base=['neural_network_optimization', 'gradient_descent', 'hyperparameter_tuning'],
    agent_id="demo_agent",
    priority=1.0
)

# Example neural network configuration
network_config = {
    'layers': 3,
    'learning_rate': 0.01,
    'batch_size': 32,
    'epochs': 100,
    'optimizer': 'adam'
}

print("Original network configuration:")
for key, value in network_config.items():
    print(f"  {key}: {value}")

# Perform optimization
try:
    result = agent.optimize_neural_network(network_config)
    
    print("\\n=== Optimization Results ===")
    print(f"Performance Score: {result.performance_score:.3f}")
    print(f"Decision Time: {result.decision_time_ms:.2f}ms")
    print(f"Sub-5ms requirement: {'✓ PASSED' if result.decision_time_ms < 5 else '✗ FAILED'}")
    
    print("\\nOptimized parameters:")
    for key, value in result.parameters.items():
        print(f"  {key}: {value}")
    
    print("\\nReasoning trace:")
    for i, step in enumerate(result.reasoning_trace, 1):
        print(f"  {i}. {step}")
        
except OptimizationError as e:
    print(f"Optimization failed: {e}")
""")
        
        # Add benchmarking code if requested
        if needs_benchmarks:
            code.append("""
# Performance benchmarking
print("\\n=== Performance Benchmarking ===")
benchmark_results = []

for i in range(10):
    config = {
        'layers': np.random.randint(2, 6),
        'learning_rate': np.random.uniform(0.001, 0.1),
        'batch_size': np.random.choice([16, 32, 64, 128])
    }
    
    result = agent.optimize_neural_network(config)
    benchmark_results.append(result.decision_time_ms)

avg_time = np.mean(benchmark_results)
std_time = np.std(benchmark_results)
sub_5ms_count = sum(1 for t in benchmark_results if t < 5)

print(f"Average decision time: {avg_time:.2f}ms ± {std_time:.2f}ms")
print(f"Sub-5ms decisions: {sub_5ms_count}/10 ({sub_5ms_count*10}%)")
print(f"Performance requirement: {'✓ PASSED' if avg_time < 5 else '✗ FAILED'}")
""")
        
        # Add visualization if requested
        if needs_visualization:
            code.append("""
# Performance visualization
if len(benchmark_results) > 0:
    plt.figure(figsize=(10, 6))
    
    # Decision time histogram
    plt.subplot(1, 2, 1)
    plt.hist(benchmark_results, bins=5, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(x=5, color='red', linestyle='--', label='5ms target')
    plt.xlabel('Decision Time (ms)')
    plt.ylabel('Frequency')
    plt.title('Decision Time Distribution')
    plt.legend()
    
    # Performance trend
    plt.subplot(1, 2, 2)
    plt.plot(range(1, len(benchmark_results) + 1), benchmark_results, 'o-', color='green')
    plt.axhline(y=5, color='red', linestyle='--', label='5ms target')
    plt.xlabel('Test Number')
    plt.ylabel('Decision Time (ms)')
    plt.title('Performance Trend')
    plt.legend()
    
    plt.tight_layout()
    plt.show()
    
    print("\\n📊 Interactive visualization displayed above")
""")
        
        return "\n".join(code)
    
    # Add more sophisticated claim mappings
    elif any(keyword in claim_lower for keyword in ['multi-agent', 'coordination', 'voting', 'priority']):
        return generate_multi_agent_code(accepted_suggestions)
    elif any(keyword in claim_lower for keyword in ['gpu', 'acceleration', 'processing', 'millisecond']):
        return generate_gpu_code(accepted_suggestions)
    
    # Default implementation with improvements
    base_code = f"# Demo implementation for claim:\n# {claim}\n\n"
    if needs_documentation:
        base_code += f'"""\nImplementation of: {claim}\n\nThis code demonstrates the key aspects of the patent claim\nwith proper error handling and performance monitoring.\n"""\n\n'
    
    if needs_error_handling:
        base_code += "try:\n    "
        base_code += f"print('Implementing: {claim}')\n    "
        base_code += "# TODO: Add specific implementation details\n"
        base_code += "except Exception as e:\n    "
        base_code += "print(f'Implementation error: {e}')\n"
    else:
        base_code += f"print('Implementing: {claim}')\n"
        base_code += "# TODO: Add specific implementation details\n"
    
    return base_code

def generate_multi_agent_code(accepted_suggestions: List[str]) -> str:
    """Generate code for multi-agent coordination claims"""
    # Similar structure to semantic agent but focused on coordination
    return """
# Multi-Agent Coordination Protocol Implementation
import threading
import queue
import time
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class AgentDecision:
    agent_id: str
    decision: str
    priority: float
    confidence: float
    timestamp: float

class CoordinationProtocol:
    def __init__(self):
        self.agents = {}
        self.decision_queue = queue.PriorityQueue()
        self.coordination_lock = threading.Lock()
    
    def register_agent(self, agent_id: str, priority: float):
        self.agents[agent_id] = priority
    
    def aggregate_decisions(self, decisions: List[AgentDecision]) -> str:
        # Priority-weighted decision aggregation
        weighted_score = {}
        for decision in decisions:
            if decision.decision not in weighted_score:
                weighted_score[decision.decision] = 0
            weighted_score[decision.decision] += decision.priority * decision.confidence
        
        return max(weighted_score.items(), key=lambda x: x[1])[0]

# Demo the coordination protocol
protocol = CoordinationProtocol()
protocol.register_agent("agent_1", 1.0)
protocol.register_agent("agent_2", 0.8)

decisions = [
    AgentDecision("agent_1", "optimize_learning_rate", 1.0, 0.9, time.time()),
    AgentDecision("agent_2", "optimize_batch_size", 0.8, 0.7, time.time())
]

final_decision = protocol.aggregate_decisions(decisions)
print(f"Coordinated decision: {final_decision}")
"""

def generate_gpu_code(accepted_suggestions: List[str]) -> str:
    """Generate code for GPU acceleration claims"""
    return """
# GPU-Accelerated Semantic Reasoning Implementation
import numpy as np
import time
try:
    import cupy as cp  # GPU acceleration library
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    print("CuPy not available - falling back to CPU implementation")

class GPUSemanticProcessor:
    def __init__(self):
        self.use_gpu = GPU_AVAILABLE
        self.device = "GPU" if self.use_gpu else "CPU"
        
    def process_semantic_vectors(self, vectors: np.ndarray) -> np.ndarray:
        start_time = time.time()
        
        if self.use_gpu:
            # GPU implementation
            gpu_vectors = cp.asarray(vectors)
            result = cp.dot(gpu_vectors, gpu_vectors.T)
            result = cp.asnumpy(result)  # Convert back to numpy
        else:
            # CPU fallback
            result = np.dot(vectors, vectors.T)
        
        processing_time = (time.time() - start_time) * 1000
        print(f"Semantic processing on {self.device}: {processing_time:.2f}ms")
        
        return result

# Demo GPU acceleration
processor = GPUSemanticProcessor()
test_vectors = np.random.rand(1000, 512)  # Simulate semantic embeddings
result = processor.process_semantic_vectors(test_vectors)
print(f"Processed {test_vectors.shape[0]} semantic vectors")
print(f"Result shape: {result.shape}")
"""

def parse_editorial_feedback(feedback: str) -> List[str]:
    # Placeholder: split feedback into lines/suggestions
    return [line.strip() for line in feedback.split('\n') if line.strip()]

def should_accept_suggestion(suggestion: str) -> bool:
    # Placeholder: accept all suggestions containing 'improve', reject those with 'remove'
    if 'remove' in suggestion.lower():
        return False
    return True

class ColabDemoGeneratorTool(BaseTool):
    name: str = "Colab Demo Generator Tool"
    description: str = "Generates Colab-compatible notebooks with code demos, benchmarks, and technical implementations for patents"
    
    def _run(self, patent_id: str, title: str, description: str, key_claims: List[str], 
             technical_features: List[str], market_applications: List[str], 
             editorial_feedback: str = None, tier: str = None) -> str:
        try:
            patent_id = patent_id or "UNKNOWN"
            title = title or "Untitled Patent"
            description = description or "No description provided"
            key_claims = key_claims or ["No claims provided"]
            technical_features = technical_features or ["No technical features specified"]
            market_applications = market_applications or ["No market applications specified"]
            tier = tier or "tier_1"

            # --- Dynamic claim analysis and code generation ---
            selected_claim = select_claim_to_demonstrate(key_claims)

            # --- Editorial review logic ---
            accepted_suggestions = []
            rejected_suggestions = []
            if editorial_feedback:
                suggestions = parse_editorial_feedback(editorial_feedback)
                for suggestion in suggestions:
                    if should_accept_suggestion(suggestion):
                        accepted_suggestions.append(suggestion)
                    else:
                        rejected_suggestions.append(suggestion)
            
            # Generate code with accepted suggestions integrated
            generated_code = generate_code_for_claim(selected_claim, accepted_suggestions)

            # --- Build notebook dynamically ---
            notebook = {
                "cells": [],
                "metadata": {
                    "colab": {"name": f"{patent_id} - {title}", "provenance": [], "gpuType": "T4"},
                    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                    "language_info": {"name": "python", "version": "3.8.0"}
                },
                "nbformat": 4,
                "nbformat_minor": 4
            }
            # Title and description
            notebook["cells"].append({
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# {patent_id}: {title}\n\n",
                    f"## Patent Description\n{description}\n\n",
                    f"## Key Claims\n",
                    *[f"- {claim}\n" for claim in key_claims],
                    f"\n## Technical Features\n",
                    *[f"- {feature}\n" for feature in technical_features],
                    f"\n## Market Applications\n",
                    *[f"- {app}\n" for app in market_applications],
                ]
            })
            # Claim being demonstrated
            notebook["cells"].append({
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"## Demonstrated Claim\n\n",
                    f"{selected_claim}\n"
                ]
            })
            # Generated code cell
            notebook["cells"].append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [generated_code]
            })
            
            # Editorial feedback integration logic:
            # - Initial notebook: Shows editorial process information for transparency
            # - Final notebook: Clean and submission-ready (no editorial comments)
            # - Editorial suggestions are still integrated into the generated code above
            if editorial_feedback:
                # Final notebook: Clean and submission-ready (no editorial comments)
                pass  # No editorial suggestions in final notebook
            else:
                # Initial notebook: Include editorial process information for transparency
                notebook["cells"].append({
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "## Editorial Review Process\n\n",
                        "This notebook will undergo editorial review to enhance:\n",
                        "- Code quality and best practices implementation\n", 
                        "- Educational content clarity and completeness\n",
                        "- Performance demonstration accuracy\n",
                        "- Interactive functionality and user experience\n",
                        "- Technical accuracy and patent claim alignment\n\n",
                        "The final version will integrate accepted improvements while maintaining\n",
                        "technical accuracy and patent demonstration effectiveness.\n"
                    ]
                })

            # Output file logic
            if editorial_feedback:
                notebook_file = f"output/{tier}/{patent_id}_colab_demo_final.ipynb"
                log_message = f"✅ Final Colab notebook generated with editorial feedback: {notebook_file}"
            else:
                notebook_file = f"output/{tier}/{patent_id}_colab_demo.ipynb"
                log_message = f"✅ Initial Colab notebook generated: {notebook_file}"
            os.makedirs(os.path.dirname(notebook_file), exist_ok=True)
            try:
                nb_node = nbformat.from_dict(notebook)
                nbformat.validate(nb_node)
                with open(notebook_file, 'w', encoding='utf-8') as f:
                    nbformat.write(nb_node, f)
            except Exception as nb_exc:
                error_msg = f"Notebook validation or writing failed: {nb_exc}"
                logging.error(error_msg)
                return error_msg
            return log_message
        except Exception as e:
            error_msg = f"""
ERROR IN COLAB DEMO GENERATOR TOOL
==================================

Patent ID: {patent_id}
Error Type: {type(e).__name__}
Error Message: {str(e)}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The tool encountered an unexpected error during Colab notebook generation. This may be due to:
- Invalid input data format
- Missing required patent information
- File system errors
- JSON serialization errors
- Internal processing errors

Please check the input parameters and try again. If the error persists, 
contact the system administrator.

Input Parameters Received:
- patent_id: {patent_id}
- title: {title[:100]}{'...' if len(title) > 100 else ''}
- description length: {len(description) if description else 0} characters
- key_claims count: {len(key_claims) if key_claims else 0}
- technical_features count: {len(technical_features) if technical_features else 0}
- market_applications count: {len(market_applications) if market_applications else 0}
"""
            logging.error(f"ColabDemoGeneratorTool error: {e}")
            return error_msg