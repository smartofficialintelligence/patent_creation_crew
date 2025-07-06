import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.real_patent_search import RealPatentSearchTool

if __name__ == "__main__":
    # Note: This test will fail without API keys, but it will test the file path logic
    tool = RealPatentSearchTool()
    # Sample data for testing
    patent_id = "TEST001"
    title = "Test Patent for Real Patent Search"
    description = "A test patent for demonstrating the real patent search tool."
    key_claims = [
        "A method for real patent searching using multiple APIs.",
        "Integration of Lens.org and EPO OPS search capabilities."
    ]
    technical_features = [
        "Multi-API search",
        "Real-time patent data",
        "Comprehensive analysis"
    ]
    market_applications = [
        "Patent research",
        "Prior art analysis",
        "IP strategy"
    ]
    differentiation = "Real API integration vs. simulated results"
    tier = "tier_1"

    result = tool._run(
        patent_id=patent_id,
        title=title,
        description=description,
        key_claims=key_claims,
        technical_features=technical_features,
        market_applications=market_applications,
        differentiation=differentiation,
        tier=tier
    )
    print(result) 