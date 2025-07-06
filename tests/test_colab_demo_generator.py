import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.colab_demo_generator import ColabDemoGeneratorTool

if __name__ == "__main__":
    tool = ColabDemoGeneratorTool()
    # Sample data for testing
    patent_id = "TEST001"
    title = "Test Patent for Semantic Optimization"
    description = "A test patent for demonstrating the Colab demo generator tool."
    key_claims = [
        "A method for semantic optimization using agent-based reasoning.",
        "Integration of memory and coordination protocols."
    ]
    technical_features = [
        "Semantic agent framework",
        "Memory integration",
        "Coordination protocols"
    ]
    market_applications = [
        "AI optimization",
        "Robotics",
        "Data science"
    ]
    editorial_feedback = None  # Or provide a string for final version

    result = tool._run(
        patent_id=patent_id,
        title=title,
        description=description,
        key_claims=key_claims,
        technical_features=technical_features,
        market_applications=market_applications,
        editorial_feedback=editorial_feedback,
        tier="tier_1"
    )
    print(result) 