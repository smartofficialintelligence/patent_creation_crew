# Patent data and configuration for the CrewAI Patent Automation System

import yaml
from pathlib import Path
from typing import Dict, List, Any

# Portfolio configuration - Updated for new structure
PATENT_CONFIG = {
    "inventor": "Patrick Kuehn",
    "base_filing_date": "June 28-29, 2025",
    "expiration_date": "June 28-29, 2026",
    "filing_cost_per_patent": 130,
    "target_portfolio_size": 9,  # Updated based on new YAML
    "portfolio_tiers": {
        "phase_1": {
            "name": "Phase 1 - Critical Foundation",
            "count": 4,
            "timeline": "Weeks 1-2",
            "priority": "CRITICAL"
        },
        "phase_2": {
            "name": "Phase 2 - Competitive Differentiation", 
            "count": 3,
            "timeline": "Months 2-3",
            "priority": "HIGH"
        },
        "phase_3": {
            "name": "Phase 3 - Market Expansion",
            "count": 2,
            "timeline": "Months 4-6",
            "priority": "MEDIUM"
        }
    }
}

def load_patents_from_yaml(yaml_file: str = "config/provisional_patents.yaml") -> Dict[str, List[Dict[str, Any]]]:
    """
    Load patents from YAML file and group them by phase.
    
    Args:
        yaml_file: Path to the YAML file containing patent data
        
    Returns:
        Dictionary with phase keys and lists of patents as values
    """
    yaml_path = Path(yaml_file)
    
    if not yaml_path.exists():
        print(f"Warning: {yaml_file} not found. Using empty patent data.")
        return {
            "phase_1": [],
            "phase_2": [],
            "phase_3": []
        }
    
    try:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Initialize empty phase structure
        patent_ideas = {
            "phase_1": [],
            "phase_2": [],
            "phase_3": []
        }
        
        # Group patents by phase
        patents = data.get('patents', [])
        for patent in patents:
            phase = patent.get('phase', 'phase_1')  # Default to phase_1 if not specified
            
            # Validate phase
            if phase not in patent_ideas:
                print(f"Warning: Invalid phase '{phase}' for patent {patent.get('id', 'unknown')}. Using phase_1.")
                phase = 'phase_1'
            
            # Remove the phase field from the patent data since it's now used for grouping
            patent_copy = patent.copy()
            patent_copy.pop('phase', None)
            
            patent_ideas[phase].append(patent_copy)
        
        return patent_ideas
        
    except Exception as e:
        print(f"Error loading patents from {yaml_file}: {e}")
        print("Using empty patent data.")
        return {
            "phase_1": [],
            "phase_2": [],
            "phase_3": []
        }

# Load patents from YAML file
PATENT_IDEAS = load_patents_from_yaml()

# Print loading summary
print(f"Loaded patents from YAML:")
for phase, patents in PATENT_IDEAS.items():
    print(f"  {phase}: {len(patents)} patents")
    for patent in patents:
        print(f"    - {patent.get('id', 'unknown')}: {patent.get('title', 'No title')}") 