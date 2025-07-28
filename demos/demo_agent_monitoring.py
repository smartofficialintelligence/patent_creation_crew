#!/usr/bin/env python3
"""
Demo: Real-Time Agent Monitoring
Shows how to track agents and models during execution with comprehensive monitoring
"""

import sys
import os
import time
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.agent_model_tracker import setup_comprehensive_tracking, get_tracker
from lib.resource_monitoring_system import start_monitoring, track_agent_start, track_agent_completion, get_agent_summary, get_model_usage_report

async def simulate_agent_execution():
    """Simulate multiple agents running with different models"""
    print("🚀 AGENT MONITORING DEMO")
    print("=" * 70)
    
    # Setup both tracking systems
    print("📊 Setting up comprehensive tracking...")
    setup_comprehensive_tracking()
    tracker = get_tracker()
    start_monitoring()
    
    # Define agent configurations
    agents = [
        {"name": "patent_researcher", "model": "gpt-4o", "task": "prior_art_research"},
        {"name": "technical_writer", "model": "claude-sonnet-4", "task": "technical_writing"},
        {"name": "market_analyst", "model": "deepseek-v2", "task": "market_analysis"},
        {"name": "legal_reviewer", "model": "grok-3", "task": "legal_review"},
        {"name": "cost_optimizer", "model": "gpt-4o-mini", "task": "cost_optimization"}
    ]
    
    print(f"🤖 Simulating {len(agents)} agents with different models...")
    print()
    
    # Track agent executions
    for i, agent in enumerate(agents):
        print(f"⏳ Starting {agent['name']} ({agent['model']})...")
        
        # Track agent start
        track_agent_start(agent['name'], agent['model'], agent['task'])
        
        # Simulate some work
        work_duration = 2 + (i * 0.5)  # Varying work duration
        await asyncio.sleep(work_duration)
        
        # Simulate cost and token usage
        simulated_cost = 0.05 + (i * 0.02)
        simulated_tokens = 1000 + (i * 500)
        simulated_response_time = 1500 + (i * 200)
        
        # Track agent completion
        track_agent_completion(
            agent['name'],
            cost=simulated_cost,
            tokens=simulated_tokens,
            response_time_ms=simulated_response_time
        )
        
        print(f"✅ Completed {agent['name']} - Cost: ${simulated_cost:.4f}, Tokens: {simulated_tokens}")
        print()
    
    # Add some background model usage
    print("📈 Adding background model usage...")
    from lib.resource_monitoring_system import track_model_usage
    track_model_usage("gpt-4o-mini", 0.01, 200)  # Context management
    track_model_usage("gpt-4o-mini", 0.005, 150)  # Validation
    track_model_usage("gpt-4o", 0.03, 800)  # Additional research
    
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE AGENT TRACKING RESULTS")
    print("=" * 70)
    
    # Get results from both systems
    print("\n🔍 AGENT MODEL TRACKER RESULTS:")
    print(tracker.get_summary_report())
    
    print("\n📊 RESOURCE MONITOR RESULTS:")
    print(get_model_usage_report())
    
    print("\n📈 DETAILED AGENT SUMMARY:")
    agent_summary = get_agent_summary()
    
    print(f"Total Agent Executions: {agent_summary['total_agent_executions']}")
    print(f"Active Agents: {agent_summary['active_agents']}")
    print()
    
    print("Agent Performance:")
    for agent_name, stats in agent_summary['agent_performance'].items():
        print(f"  🤖 {agent_name}:")
        print(f"     Model: {stats['model']}")
        print(f"     Executions: {stats['executions']}")
        print(f"     Total Cost: ${stats['total_cost']:.4f}")
        print(f"     Total Tokens: {stats['total_tokens']:,}")
        print(f"     Avg Duration: {stats['total_duration']:.1f}s")
        print(f"     Avg Response Time: {stats['avg_response_time']:.1f}ms")
        print()
    
    print("Model Usage Summary:")
    for model, stats in agent_summary['model_usage'].items():
        print(f"  🔧 {model}:")
        print(f"     Usage Count: {stats['usage_count']}")
        print(f"     Total Cost: ${stats['total_cost']:.4f}")
        print(f"     Total Tokens: {stats['total_tokens']:,}")
        print(f"     Avg Cost/Call: ${stats['avg_cost_per_call']:.4f}")
        print(f"     Avg Tokens/Call: {stats['avg_tokens_per_call']:.0f}")
        print()
    
    # Save detailed reports
    print("💾 Saving detailed reports...")
    tracker_report = tracker.save_detailed_report()
    print(f"📄 Agent Tracker Report: {tracker_report}")
    
    print("\n🎉 Agent monitoring demo completed!")
    print("=" * 70)

def run_live_monitoring():
    """Run live monitoring during patent automation"""
    print("🔥 LIVE MONITORING MODE")
    print("=" * 70)
    print("This will show real-time agent tracking during actual patent automation.")
    print()
    
    response = input("Do you want to run live monitoring with patent automation? (y/n): ")
    if response.lower() != 'y':
        print("Live monitoring skipped.")
        return
    
    print("🚀 Starting live monitoring...")
    print("Run this command in another terminal:")
    print("python scripts/run_with_tracking.py --tier tier_1 --max-per-tier 1")
    print()
    print("The tracking will show:")
    print("- Which agents are running")
    print("- What models they're using")
    print("- Real-time cost and token usage")
    print("- Performance metrics")
    print()

async def main():
    """Main demo function"""
    print("🎯 AGENT MONITORING DEMO OPTIONS")
    print("=" * 50)
    print("1. Simulate agent execution with comprehensive tracking")
    print("2. Show live monitoring setup")
    print("3. Both simulation and live monitoring info")
    print()
    
    choice = input("Choose option (1-3): ").strip()
    
    if choice == "1":
        await simulate_agent_execution()
    elif choice == "2":
        run_live_monitoring()
    elif choice == "3":
        await simulate_agent_execution()
        print("\n" + "=" * 70)
        run_live_monitoring()
    else:
        print("Invalid choice. Running simulation...")
        await simulate_agent_execution()

if __name__ == "__main__":
    asyncio.run(main()) 