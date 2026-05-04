"""
Tool Parameter Mapping Utility
Provides clear parameter mappings for all tools to prevent parameter name mismatches.
"""

from typing import Dict, List, Any

# Parameter mappings for each tool
TOOL_PARAMETER_MAPPINGS = {
    "patent_document_tool": {
        "description": "Create comprehensive patent application documents with technical specifications and claims.",
        "required_parameters": {
            "patent_id": "str - The unique identifier for the patent",
            "title": "str - The title of the patent (NOT patent_title)",
            "description": "str - Detailed description of the invention",
            "key_claims": "List[str] - List of patent claims"
        },
        "optional_parameters": {
            "technical_features": "List[str] - Technical features of the invention",
            "market_applications": "List[str] - Market applications for the invention",
            "differentiation": "str - How this invention differs from prior art"
        },
        "common_mistakes": {
            "patent_title": "Use 'title' instead",
            "inventor_information": "Not a valid parameter",
            "value_estimate": "Not a valid parameter for this tool"
        }
    },
    
    "enhanced_prior_art_search_tool": {
        "description": "Conduct comprehensive prior art search using real patent databases and academic literature.",
        "required_parameters": {
            "patent_id": "str - The unique identifier for the patent",
            "title": "str - The title of the patent",
            "description": "str - Description of the invention",
            "key_claims": "List[str] - List of patent claims to search against"
        },
        "optional_parameters": {
            "technical_features": "List[str] - Technical features to search for",
            "market_applications": "List[str] - Market applications to consider",
            "value_estimate": "str - Estimated value for context"
        },
        "common_mistakes": {
            "patent_title": "Use 'title' instead",
            "inventor_information": "Not a valid parameter"
        }
    },
    
    "smart_claim_refinement_tool": {
        "description": "Refine and optimize patent claims for maximum strength and commercial value.",
        "required_parameters": {
            "patent_id": "str - The unique identifier for the patent",
            "title": "str - The title of the patent",
            "description": "str - Description of the invention",
            "key_claims": "List[str] - Original claims to refine"
        },
        "optional_parameters": {
            "technical_features": "List[str] - Technical features to emphasize",
            "market_applications": "List[str] - Market applications to target",
            "value_target": "str - Target value for the patent",
            "differentiation": "str - How to differentiate from prior art"
        },
        "common_mistakes": {
            "patent_title": "Use 'title' instead",
            "value_estimate": "Use 'value_target' instead"
        }
    },
    
    "vector_based_overlap_analysis_tool": {
        "description": "Perform semantic overlap analysis between patent claims and prior art using sentence transformers.",
        "required_parameters": {
            "patent_id": "str - The unique identifier for the patent",
            "title": "str - The title of the patent",
            "description": "str - Description of the invention",
            "key_claims": "List[str] - Claims to analyze",
            "prior_art_data": "List[Dict] - Prior art data to compare against"
        },
        "optional_parameters": {
            "technical_features": "List[str] - Technical features to consider"
        },
        "common_mistakes": {
            "patent_title": "Use 'title' instead"
        }
    },
    
    "consolidated_risk_assessment_tool": {
        "description": "Comprehensive risk assessment for patent validity and commercial success.",
        "required_parameters": {
            "patent_id": "str - The unique identifier for the patent",
            "title": "str - The title of the patent",
            "description": "str - Description of the invention",
            "key_claims": "List[str] - Claims to assess"
        },
        "optional_parameters": {
            "technical_features": "List[str] - Technical features to consider",
            "market_applications": "List[str] - Market applications to assess",
            "prior_art_data": "List[Dict] - Prior art data for risk analysis"
        },
        "common_mistakes": {
            "patent_title": "Use 'title' instead"
        }
    },
    
    "provisional_cover_sheet_tool": {
        "description": "Generate USPTO-compliant provisional patent application cover sheet.",
        "required_parameters": {
            "patent_id": "str - The unique identifier for the patent",
            "title": "str - The title of the patent",
            "description": "str - Description of the invention",
            "key_claims": "List[str] - Claims for the application"
        },
        "optional_parameters": {
            "technical_features": "List[str] - Technical features to list",
            "market_applications": "List[str] - Market applications to include",
            "value_estimate": "str - Estimated value for fee calculation"
        },
        "common_mistakes": {
            "patent_title": "Use 'title' instead"
        }
    },
    
    "colab_demo_generator_tool": {
        "description": "Generate interactive Google Colab demo notebook for patent demonstration.",
        "required_parameters": {
            "patent_id": "str - The unique identifier for the patent",
            "title": "str - The title of the patent",
            "description": "str - Description of the invention",
            "key_claims": "List[str] - Claims to demonstrate"
        },
        "optional_parameters": {
            "technical_features": "List[str] - Technical features to showcase",
            "market_applications": "List[str] - Market applications to demonstrate",
            "differentiation": "str - How to differentiate from existing solutions"
        },
        "common_mistakes": {
            "patent_title": "Use 'title' instead"
        }
    }
}

def get_tool_parameters(tool_name: str) -> Dict[str, Any]:
    """Get parameter information for a specific tool."""
    return TOOL_PARAMETER_MAPPINGS.get(tool_name, {})

def get_common_mistakes(tool_name: str) -> Dict[str, str]:
    """Get common parameter mistakes for a specific tool."""
    tool_info = TOOL_PARAMETER_MAPPINGS.get(tool_name, {})
    return tool_info.get("common_mistakes", {})

def validate_tool_parameters(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and correct tool parameters."""
    tool_info = TOOL_PARAMETER_MAPPINGS.get(tool_name, {})
    common_mistakes = tool_info.get("common_mistakes", {})
    
    corrected_params = parameters.copy()
    
    # Fix common mistakes
    for wrong_param, correct_param in common_mistakes.items():
        if wrong_param in corrected_params:
            if correct_param.startswith("Use '"):
                # Extract the correct parameter name
                correct_param_name = correct_param.split("'")[1]
                corrected_params[correct_param_name] = corrected_params.pop(wrong_param)
            else:
                # Remove invalid parameter
                corrected_params.pop(wrong_param)
    
    return corrected_params

def get_tool_parameter_guide(tool_name: str) -> str:
    """Get a formatted parameter guide for a tool."""
    tool_info = TOOL_PARAMETER_MAPPINGS.get(tool_name, {})
    if not tool_info:
        return f"No parameter information available for {tool_name}"
    
    guide = f"Tool: {tool_name}\n"
    guide += f"Description: {tool_info.get('description', 'N/A')}\n\n"
    
    required = tool_info.get("required_parameters", {})
    if required:
        guide += "Required Parameters:\n"
        for param, desc in required.items():
            guide += f"  - {param}: {desc}\n"
        guide += "\n"
    
    optional = tool_info.get("optional_parameters", {})
    if optional:
        guide += "Optional Parameters:\n"
        for param, desc in optional.items():
            guide += f"  - {param}: {desc}\n"
        guide += "\n"
    
    mistakes = tool_info.get("common_mistakes", {})
    if mistakes:
        guide += "Common Mistakes to Avoid:\n"
        for wrong, correction in mistakes.items():
            guide += f"  - {wrong}: {correction}\n"
    
    return guide 