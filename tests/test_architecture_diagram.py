import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.architecture_diagram import ArchitectureDiagramTool

if __name__ == "__main__":
    tool = ArchitectureDiagramTool()
    # Sample data for testing
    patent_id = "TEST001"
    title = "Test Patent for Architecture Diagrams"
    description = "A test patent for demonstrating the architecture diagram tool."
    key_claims = [
        "A method for generating architecture diagrams using dual approaches.",
        "Integration of programmatic and LLM-based diagram generation."
    ]
    technical_features = [
        "Programmatic diagram generation",
        "LLM-based creative diagrams",
        "Dual approach validation"
    ]
    market_applications = [
        "Patent documentation",
        "Technical visualization",
        "System architecture"
    ]
    tier = "tier_1"

    result = tool._run(
        patent_id=patent_id,
        title=title,
        description=description,
        key_claims=key_claims,
        technical_features=technical_features,
        market_applications=market_applications,
        tier=tier
    )
    print(result) 