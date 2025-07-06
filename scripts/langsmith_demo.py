#!/usr/bin/env python3
"""
LangSmith Demo Script for Patent Pipeline
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from core.langsmith_utils import trace_function, log_agent_execution, log_tool_execution, langsmith_manager

@trace_function(name="demo_patent_analysis")
def demo_patent_analysis(patent_id: str, title: str, description: str):
    """Demo function showing LangSmith tracing"""
    print(f"🔍 Analyzing patent: {patent_id}")
    print(f"Title: {title}")
    print(f"Description: {description[:100]}...")
    
    # Simulate some analysis steps
    analysis_steps = [
        "prior_art_search",
        "claim_analysis", 
        "risk_assessment",
        "valuation"
    ]
    
    results = {}
    for step in analysis_steps:
        print(f"  📋 Running {step}...")
        
        # Log tool execution
        inputs = {"patent_id": patent_id, "step": step}
        outputs = {"status": "completed", "score": 0.85}
        log_tool_execution(step, inputs, outputs)
        
        results[step] = outputs
    
    return results

@trace_function(name="demo_agent_workflow")
def demo_agent_workflow():
    """Demo function showing agent execution logging"""
    print("🤖 Running demo agent workflow...")
    
    # Simulate agent executions
    agents = ["patent_researcher", "claims_specialist", "valuation_expert"]
    tasks = ["search_prior_art", "refine_claims", "assess_value"]
    
    for agent, task in zip(agents, tasks):
        print(f"  👤 {agent} executing {task}...")
        
        # Log agent execution
        inputs = {
            "agent": agent,
            "task": task,
            "patent_data": {"id": "demo_patent", "title": "Demo Invention"}
        }
        outputs = {
            "status": "completed",
            "result": f"Successfully completed {task}",
            "confidence": 0.92
        }
        log_agent_execution(agent, task, inputs, outputs)

def main():
    """Main demo function"""
    print("🚀 LangSmith Demo for Patent Pipeline")
    print("=" * 50)
    
    # Check if LangSmith is enabled
    if langsmith_manager.is_enabled():
        print("✅ LangSmith is enabled and configured")
        print(f"📊 Project: {os.getenv('LANGCHAIN_PROJECT', 'patent-pipeline')}")
        print(f"🔗 Endpoint: {os.getenv('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')}")
    else:
        print("⚠️  LangSmith is not enabled")
        print("   Set LANGCHAIN_API_KEY in your .env file to enable tracing")
        print("   Get your API key from: https://smith.langchain.com/")
        return
    
    print("\n" + "=" * 50)
    
    # Demo patent analysis
    demo_patent_analysis(
        patent_id="DEMO-001",
        title="Semantic Agent Optimization System",
        description="A novel approach to optimization using semantic reasoning agents instead of traditional mathematical methods."
    )
    
    print("\n" + "=" * 50)
    
    # Demo agent workflow
    demo_agent_workflow()
    
    print("\n" + "=" * 50)
    print("✅ Demo completed!")
    print("📊 Check your LangSmith dashboard to see the traces:")
    print("   https://smith.langchain.com/")
    print("\n💡 Tips:")
    print("   - Use the @trace_function decorator to trace any function")
    print("   - Use log_agent_execution() to log agent activities")
    print("   - Use log_tool_execution() to log tool usage")
    print("   - Configure sampling rates in config/langsmith_config.yaml")

if __name__ == "__main__":
    main() 