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
    # Placeholder: select the first claim (could be improved with LLM or heuristics)
    return key_claims[0] if key_claims else "No claims provided"

def generate_code_for_claim(claim: str) -> str:
    # Placeholder: map claim keywords to code snippets (could use LLM for real implementation)
    if "semantic agent" in claim.lower():
        return (
            "# Example: Semantic Agent Implementation\n"
            "class SemanticAgent:\n"
            "    def __init__(self, knowledge):\n"
            "        self.knowledge = knowledge\n"
            "    def reason(self, problem):\n"
            "        return f'Reasoning about: {problem} using {self.knowledge}'\n"
            "\n"
            "agent = SemanticAgent(['optimization', 'AI'])\n"
            "print(agent.reason('Optimize neural network'))\n"
        )
    # Add more mappings as needed
    return (
        f"# Demo implementation for claim:\n# {claim}\nprint('This is a placeholder for the implementation of the above claim.')\n"
    )

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
            generated_code = generate_code_for_claim(selected_claim)

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
            # Editorial feedback integration
            if accepted_suggestions:
                notebook["cells"].append({
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "## Integrated Editorial Suggestions\n\n",
                        *[f"- {s}\n" for s in accepted_suggestions]
                    ]
                })
            if rejected_suggestions:
                notebook["cells"].append({
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        "## Rejected Editorial Suggestions\n\n",
                        *[f"- {s} (reason: not aligned with demonstration goals)\n" for s in rejected_suggestions]
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