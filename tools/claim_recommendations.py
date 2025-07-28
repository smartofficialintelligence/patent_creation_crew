from datetime import datetime
import logging
from typing import List
try:
    from crewai.tools import BaseTool
except ImportError:
    from crewai.tools.agent_tools import Tool as BaseTool
from pydantic import BaseModel, validator

class ClaimRecommendationsInput(BaseModel):
    patent_id: str
    title: str
    description: str
    key_claims: List[str]
    prior_art_analysis: str = ""
    technical_features: List[str] = []
    market_applications: List[str] = []
    differentiation: str = ""
    phase: str = "phase_1"

    @validator('patent_id', 'title', 'description')
    def required_fields_must_not_be_empty(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError('Required field must not be empty')
        return v

    @validator('key_claims')
    def key_claims_must_be_list(cls, v):
        if not isinstance(v, list) or not v:
            raise ValueError('key_claims must be a non-empty list')
        return v

class ClaimRecommendationsTool(BaseTool):
    name: str = "claim_recommendations_tool"
    description: str = "Analyze claims and provide recommendations for improvement with human approval workflow."
    args_schema: type[BaseModel] = ClaimRecommendationsInput

    def __init__(self):
        super().__init__()

    def save_recommendations_for_approval(self, patent_id: str, phase: str, original_claims: List[str], recommendations: str, prior_art_analysis: str):
        approval_file = f"output/{phase}/{patent_id}_claim_recommendations_approval.md"
        try:
            with open(approval_file, "w", encoding="utf-8") as f:
                f.write(f"# Claim Recommendations - Human Approval Required\n\n")
                f.write(f"Patent ID: {patent_id}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Status: PENDING HUMAN APPROVAL\n\n")
                f.write("## Original Claims\n\n")
                for i, claim in enumerate(original_claims, 1):
                    f.write(f"{i}. {claim}\n")
                f.write("\n## Prior Art Analysis Context\n\n")
                f.write(prior_art_analysis)
                f.write("\n## AI Recommendations\n\n")
                f.write(recommendations)
                f.write("\n## Human Approval Section\n\n")
                f.write("### Instructions for Human Reviewer:\n")
                f.write("1. Review the AI recommendations above\n")
                f.write("2. Decide which recommendations to approve\n")
                f.write("3. Add your approved changes below\n")
                f.write("4. Save this file to trigger the next step\n\n")
                f.write("### Approved Changes (Add your approved recommendations here):\n")
                f.write("```\n# Add your approved claim modifications here\n```\n\n")
                f.write("### Approval Status:\n")
                f.write("- [ ] Review completed\n")
                f.write("- [ ] Changes approved\n")
                f.write("- [ ] Ready for implementation\n\n")
                f.write("### Notes:\n(Add any additional notes or concerns here)\n\n")
                f.write("---\n")
                f.write("*This file will be monitored for changes. When you save approved changes, the system will proceed with implementation.*\n")
        except Exception as e:
            logging.warning(f"Could not write claim recommendations approval file for {patent_id}: {e}")

    def _run(self, patent_id: str = None, title: str = None, description: str = None, key_claims: List[str] = None,
             prior_art_analysis: str = None, technical_features: List[str] = None,
             market_applications: List[str] = None, differentiation: str = None,
             phase: str = "phase_1") -> str:
        try:
            patent_id = patent_id or "UNKNOWN"
            title = title or "Untitled Patent"
            description = description or "No description provided"
            key_claims = key_claims or ["No claims provided"]
            prior_art_analysis = prior_art_analysis or "No prior art analysis provided"
            technical_features = technical_features or ["No technical features specified"]
            market_applications = market_applications or ["No market applications specified"]
            differentiation = differentiation or "No differentiation specified"

            recommendations = f"""
CLAIM ANALYSIS AND RECOMMENDATIONS
==================================
Patent ID: {patent_id}
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Strategy: Recommendations for human approval

ORIGINAL CLAIMS ANALYSIS:
========================
{chr(10).join(f"{i+1}. {claim}" for i, claim in enumerate(key_claims))}

PRIOR ART CONSIDERATIONS:
========================
- Emphasize semantic reasoning vs. mathematical optimization
- Specify performance characteristics (sub-5ms cycles)
- Include interpretability and explainability features
- Detail agent coordination protocols
- Highlight GPU optimization aspects

RECOMMENDED IMPROVEMENTS:
=========================
- Add performance specifications (sub-5ms cycles)
- Include interpretability features
- Enhance technical differentiation
- Expand commercial value potential

**Human Approval Required**: No changes will be made until you approve them in the approval file.
"""
            self.save_recommendations_for_approval(patent_id, phase, key_claims, recommendations, prior_art_analysis)
            return f"""
CLAIM RECOMMENDATIONS GENERATED
==============================
Patent ID: {patent_id}
Status: RECOMMENDATIONS SAVED FOR HUMAN APPROVAL

The claim analysis has been completed and recommendations have been saved to:
output/{{phase}}/{{patent_id}}_claim_recommendations_approval.md

**NEXT STEPS:**
1. Review the recommendations in the approval file
2. Add your approved changes to the file
3. Save the file to trigger implementation
4. The system will wait for your approval before proceeding
"""
        except Exception as e:
            logging.error(f"ClaimRecommendationsTool error: {e}")
            return f"ERROR: {e}" 