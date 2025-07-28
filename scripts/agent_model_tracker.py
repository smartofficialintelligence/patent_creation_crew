#!/usr/bin/env python3
"""
Agent Model Tracker
Monitor which agents are using which models during execution
"""

import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class AgentModelTracker:
    """Track agent model usage during execution"""
    
    def __init__(self):
        self.agent_model_usage = defaultdict(list)
        self.model_usage_summary = defaultdict(int)
        self.execution_timeline = []
        self.start_time = datetime.now()
        
    def track_agent_call(self, agent_name: str, model: str, task: str, timestamp: datetime = None):
        """Track an agent model call"""
        if timestamp is None:
            timestamp = datetime.now()
            
        usage_entry = {
            'timestamp': timestamp.isoformat(),
            'agent': agent_name,
            'model': model,
            'task': task,
            'elapsed_time': (timestamp - self.start_time).total_seconds()
        }
        
        self.agent_model_usage[agent_name].append(usage_entry)
        self.model_usage_summary[model] += 1
        self.execution_timeline.append(usage_entry)
        
        print(f"🤖 AGENT CALL: {agent_name} → {model} (Task: {task})")
        
    def get_summary_report(self) -> str:
        """Generate a summary report of agent model usage"""
        report = []
        report.append("🔍 AGENT MODEL USAGE SUMMARY")
        report.append("=" * 60)
        
        # Agent-by-agent breakdown
        report.append("\n📋 By Agent:")
        for agent_name, calls in self.agent_model_usage.items():
            models_used = set(call['model'] for call in calls)
            report.append(f"  🤖 {agent_name}:")
            for model in models_used:
                count = len([c for c in calls if c['model'] == model])
                report.append(f"     - {model}: {count} calls")
        
        # Model usage summary
        report.append("\n📊 By Model:")
        for model, count in sorted(self.model_usage_summary.items()):
            agents_using = set(call['agent'] for call in self.execution_timeline if call['model'] == model)
            report.append(f"  🔧 {model}: {count} calls")
            report.append(f"     Used by: {', '.join(sorted(agents_using))}")
        
        # Timeline
        report.append("\n⏰ Execution Timeline:")
        for entry in self.execution_timeline[-10:]:  # Last 10 calls
            report.append(f"  {entry['elapsed_time']:6.1f}s: {entry['agent']} → {entry['model']}")
        
        return "\n".join(report)
    
    def save_detailed_report(self, filename: str = None):
        """Save detailed JSON report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/agent_model_tracking_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        report_data = {
            'summary': {
                'start_time': self.start_time.isoformat(),
                'total_calls': len(self.execution_timeline),
                'unique_agents': len(self.agent_model_usage),
                'unique_models': len(self.model_usage_summary)
            },
            'agent_usage': dict(self.agent_model_usage),
            'model_summary': dict(self.model_usage_summary),
            'timeline': self.execution_timeline
        }
        
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📊 Detailed tracking report saved: {filename}")
        return filename

# Global tracker instance
_tracker = AgentModelTracker()

def get_tracker() -> AgentModelTracker:
    """Get the global tracker instance"""
    return _tracker

def track_agent_call(agent_name: str, model: str, task: str):
    """Track an agent call (convenience function)"""
    _tracker.track_agent_call(agent_name, model, task)

def monkey_patch_crewai_logging():
    """Monkey patch CrewAI to capture agent calls"""
    try:
        # Hook into CrewAI Agent execution
        from crewai import Agent
        
        original_execute_task = getattr(Agent, 'execute_task', None)
        if original_execute_task:
            def tracked_execute_task(self, task, context=None, tools=None):
                # Extract model from agent config
                model = "unknown"
                if hasattr(self, 'llm_config') and self.llm_config:
                    if 'config_list' in self.llm_config and self.llm_config['config_list']:
                        model = self.llm_config['config_list'][0].get('model', 'unknown')
                elif hasattr(self, 'llm') and hasattr(self.llm, 'model'):
                    model = getattr(self.llm, 'model', 'unknown')
                
                # Track the call
                track_agent_call(self.role, model, getattr(task, 'description', 'unknown_task')[:50])
                
                # Call original method
                return original_execute_task(self, task, context, tools)
            
            Agent.execute_task = tracked_execute_task
            print("✅ CrewAI agent tracking enabled")
        
    except ImportError:
        print("⚠️ CrewAI not available for tracking")
    except Exception as e:
        print(f"⚠️ Error setting up CrewAI tracking: {e}")

def monkey_patch_langchain_logging():
    """Monkey patch LangChain to capture LLM calls"""
    try:
        # Hook into LangChain LLM calls
        import langchain
        from langchain.llms.base import BaseLLM
        from langchain.chat_models.base import BaseChatModel
        
        # Track BaseLLM calls
        original_generate = getattr(BaseLLM, '_generate', None)
        if original_generate:
            def tracked_generate(self, prompts, stop=None, run_manager=None, **kwargs):
                model = getattr(self, 'model_name', getattr(self, 'model', 'unknown_llm'))
                track_agent_call("LangChain_LLM", model, f"generate_{len(prompts)}_prompts")
                return original_generate(self, prompts, stop, run_manager, **kwargs)
            
            BaseLLM._generate = tracked_generate
        
        # Track BaseChatModel calls
        original_chat_generate = getattr(BaseChatModel, '_generate', None)
        if original_chat_generate:
            def tracked_chat_generate(self, messages, stop=None, run_manager=None, **kwargs):
                model = getattr(self, 'model_name', getattr(self, 'model', 'unknown_chat'))
                track_agent_call("LangChain_Chat", model, f"chat_{len(messages)}_messages")
                return original_chat_generate(self, messages, stop, run_manager, **kwargs)
            
            BaseChatModel._generate = tracked_chat_generate
        
        print("✅ LangChain LLM tracking enabled")
        
    except ImportError:
        print("⚠️ LangChain not available for tracking")
    except Exception as e:
        print(f"⚠️ Error setting up LangChain tracking: {e}")

def monkey_patch_litellm_logging():
    """Monkey patch LiteLLM to capture model calls"""
    try:
        import litellm
        
        original_completion = getattr(litellm, 'completion', None)
        if original_completion:
            def tracked_completion(model=None, messages=None, **kwargs):
                # Extract caller information from stack if possible
                import inspect
                frame = inspect.currentframe()
                caller_info = "unknown_caller"
                
                try:
                    # Look up the stack for CrewAI or agent-related calls
                    for i in range(1, 10):
                        caller_frame = frame
                        for _ in range(i):
                            if caller_frame.f_back:
                                caller_frame = caller_frame.f_back
                        
                        filename = caller_frame.f_code.co_filename
                        function_name = caller_frame.f_code.co_name
                        
                        if 'crewai' in filename.lower() or 'agent' in filename.lower():
                            caller_info = f"{function_name}@{os.path.basename(filename)}"
                            break
                except:
                    pass
                
                track_agent_call("LiteLLM", model or "unknown_model", caller_info)
                return original_completion(model=model, messages=messages, **kwargs)
            
            litellm.completion = tracked_completion
            print("✅ LiteLLM tracking enabled")
        
    except ImportError:
        print("⚠️ LiteLLM not available for tracking")
    except Exception as e:
        print(f"⚠️ Error setting up LiteLLM tracking: {e}")

def setup_comprehensive_tracking():
    """Set up comprehensive agent and model tracking"""
    print("🔧 Setting up comprehensive agent/model tracking...")
    
    # Enable detailed logging for relevant modules
    logging.getLogger('crewai').setLevel(logging.WARNING)
    logging.getLogger('langchain').setLevel(logging.WARNING)
    logging.getLogger('litellm').setLevel(logging.WARNING)  # LiteLLM is chatty
    logging.getLogger('openai').setLevel(logging.WARNING)
    
    # Monkey patch various systems
    monkey_patch_crewai_logging()
    monkey_patch_langchain_logging()
    monkey_patch_litellm_logging()
    
    print("✅ Comprehensive tracking setup complete")

def main():
    """Main function for testing the tracker"""
    print("🔍 AGENT MODEL TRACKER TEST")
    print("=" * 60)
    
    # Setup tracking
    setup_comprehensive_tracking()
    
    # Simulate some calls for testing
    tracker = get_tracker()
    tracker.track_agent_call("patent_researcher", "gpt-4o", "prior_art_research")
    tracker.track_agent_call("patent_writer", "claude-sonnet-4", "patent_document")
    tracker.track_agent_call("claims_specialist", "deepseek-v2", "claims_refinement")
    tracker.track_agent_call("legal_reviewer", "grok-3", "legal_review")
    
    # Show summary
    print("\n" + tracker.get_summary_report())
    
    # Save detailed report
    report_file = tracker.save_detailed_report()
    print(f"\n📁 Report saved to: {report_file}")

if __name__ == "__main__":
    main() 