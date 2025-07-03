# create_enhanced_patent_tasks and task factory logic will be moved here. 

from typing import List, Dict
from agents.crew_agents import create_enhanced_agents
from core.utils import should_skip_task, log_skip_reason

# Import global variables from main script
import sys
import os

# Try to import global variables from main script
try:
    # Add parent directory to path to import from main script
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from patent_automation_system import FINAL_REVIEW_ONLY, SKIP_IP_VALIDATION
except ImportError:
    # Fallback values if import fails
    FINAL_REVIEW_ONLY = False
    SKIP_IP_VALIDATION = False
PATENT_CONFIG = {
    'portfolio_tiers': {
        'tier_1': {'name': 'Tier 1', 'timeline': '12 months'},
        'tier_2': {'name': 'Tier 2', 'timeline': '18 months'},
        'tier_3': {'name': 'Tier 3', 'timeline': '24 months'}
    },
    'filing_cost_per_patent': 5000
}

# Placeholders for Task class (should be imported from CrewAI or your task framework)
try:
    from crewai import Task
except ImportError:
    Task = object  # fallback for static analysis

# The actual function

def create_enhanced_patent_tasks(patent_ideas: List[Dict], tier: str) -> List[Task]:
    """Create enhanced tasks with better context and error handling and resume support"""
    
    agents = create_enhanced_agents()
    patent_researcher, patent_writer, claims_specialist, legal_reviewer, final_reviewer, cover_sheet_specialist = agents
    
    tasks = []
    
    for i, patent_idea in enumerate(patent_ideas):
        try:
            patent_id = patent_idea['id']
            
            # Enhanced prior art research task
            if FINAL_REVIEW_ONLY:
                log_skip_reason('prior_art', patent_id, 'Final review only mode')
                research_task = None
            elif should_skip_task('prior_art', patent_id, tier):
                log_skip_reason('prior_art', patent_id, 'File already exists')
                research_task = None
            elif SKIP_IP_VALIDATION:
                log_skip_reason('prior_art', patent_id, 'IP validation skipped')
                research_task = None
            else:
                research_task = Task(
                description=f"""
                Conduct comprehensive prior art search and patentability analysis for:
                
                PATENT: {patent_idea['title']}
                ID: {patent_idea['id']}
                DESCRIPTION: {patent_idea['description']}
                
                RESEARCH REQUIREMENTS:
                        1. Search Google Patents API for real patent data
                2. Review academic literature (arXiv, IEEE, ACM)
                3. Analyze patent applications and published research
                        4. Assess novelty and non-obviousness using real data
                        5. Identify potential prior art conflicts from actual patents
                        6. Provide differentiation strategy recommendations based on real findings
                
                SEARCH FOCUS:
                - Agent-based optimization systems
                - Semantic reasoning in AI/ML
                - Multi-agent coordination protocols  
                - Neural network optimization alternatives
                - AutoML and hyperparameter optimization
                - Explainable AI and interpretable optimization
                
                KEY CLAIMS TO ANALYZE:
                {chr(10).join(f"- {claim}" for claim in patent_idea['key_claims'])}
                
                DELIVERABLE: Comprehensive prior art analysis with specific recommendations
                for claim refinement and prosecution strategy.
                """,
                agent=patent_researcher,
                expected_output="""Detailed prior art search report including:
                - List of relevant patents with relevance scores
                - Academic literature analysis
                - Novelty assessment (1-10 scale)
                - Patentability analysis with statutory requirements
                - Prior art differentiation strategy
                - Risk assessment and mitigation recommendations
                - Specific search methodology and databases used""",
                output_file=f"patent_output/{tier}/{patent_idea['id']}_prior_art_analysis.md"
            )
            
            # Enhanced claims refinement task
            if FINAL_REVIEW_ONLY:
                log_skip_reason('claims', patent_id, 'Final review only mode')
                claims_task = None
            elif should_skip_task('claims', patent_id, tier):
                log_skip_reason('claims', patent_id, 'File already exists')
                claims_task = None
            else:
                claims_task = Task(
                description=f"""
                Refine and optimize patent claims for maximum strength and commercial value:
                
                PATENT: {patent_idea['title']} (ID: {patent_idea['id']})
                
                ORIGINAL CLAIMS:
                {chr(10).join(f"{i+1}. {claim}" for i, claim in enumerate(patent_idea['key_claims']))}
                
                REFINEMENT OBJECTIVES:
                1. Maximize claim breadth while ensuring validity
                2. Avoid identified prior art conflicts  
                3. Include specific technical differentiators
                4. Structure for optimal licensing value
                5. Ensure enforceability and detectability
                6. Plan prosecution and amendment strategy
                
                TECHNICAL FOCUS AREAS:
                - Semantic reasoning vs. mathematical optimization
                - Performance specifications (sub-5ms coordination)
                - Interpretability and explainability features
                - GPU optimization and scalability
                - Agent coordination protocols
                - Memory and learning capabilities
                
                VALUE TARGET: {patent_idea.get('value_estimate', '$2-15M')}
                MARKET APPLICATIONS: {', '.join(patent_idea.get('market_applications', ['AI optimization']))}
                
                Use prior art analysis to inform claim refinement strategy.
                """,
                agent=claims_specialist,
                expected_output="""Refined patent claims package including:
                - Independent claims with maximum defensible breadth
                - Dependent claims covering key technical features
                - Alternative claim formulations for prosecution flexibility
                - Prior art differentiation analysis
                - Claim strength assessment (breadth vs. validity)
                - Amendment strategy and fallback positions
                - Commercial value optimization analysis""",
                        context=[research_task] if research_task else [],
                output_file=f"patent_output/{tier}/{patent_idea['id']}_refined_claims.md"
            )
            
            # Enhanced document creation task with export support
            if FINAL_REVIEW_ONLY:
                log_skip_reason('patent_application', patent_id, 'Final review only mode')
                document_task = None
            elif should_skip_task('patent_application', patent_id, tier):
                log_skip_reason('patent_application', patent_id, 'File already exists')
                document_task = None
            else:
                document_task = Task(
                description=f"""
                Create comprehensive provisional patent application:
                
                PATENT: {patent_idea['title']} (ID: {patent_idea['id']})
                TIER: {tier} ({PATENT_CONFIG['portfolio_tiers'][tier]['name']})
                
                DOCUMENT REQUIREMENTS:
                1. Professional USPTO-compliant format
                2. Comprehensive technical description
                3. Clear enablement for skilled artisan
                4. Strong claims section with refined claims
                5. Commercial value proposition
                6. Implementation examples and code
                7. Prior art differentiation discussion
                8. Regulatory compliance considerations
                
                PATENT DATA:
                - Description: {patent_idea['description']}
                - Technical Features: {', '.join(patent_idea.get('technical_features', []))}
                - Market Applications: {', '.join(patent_idea.get('market_applications', []))}
                - Value Estimate: {patent_idea.get('value_estimate', 'TBD')}
                - Differentiation: {patent_idea.get('differentiation', 'TBD')}
                
                QUALITY STANDARDS:
                - USPTO provisional patent format compliance
                - Clear technical disclosure sufficient for continuation
                - Professional language and structure
                - Complete enablement for implementation
                - Strategic claim positioning for portfolio value
                
                Incorporate refined claims and prior art analysis findings.
                """,
                agent=patent_writer,
                expected_output="""Complete provisional patent application including:
                - Title page with inventor and filing information
                - Cross-reference to related applications
                - Field of invention and background
                - Summary of invention with key advantages
                - Detailed technical description with examples
                - Refined claims section (independent and dependent)
                - Commercial value and market analysis
                - Prior art differentiation section
                - Conclusion and filing recommendations""",
                        context=[task for task in [research_task, claims_task] if task is not None],
                output_file=f"patent_output/{tier}/{patent_idea['id']}_patent_application.md"
            )
            
            # Enhanced legal review task
            if FINAL_REVIEW_ONLY:
                log_skip_reason('legal_review', patent_id, 'Final review only mode')
                review_task = None
            elif should_skip_task('legal_review', patent_id, tier):
                log_skip_reason('legal_review', patent_id, 'File already exists')
                review_task = None
            else:
                review_task = Task(
                description=f"""
                Comprehensive legal review and filing strategy analysis:
                
                PATENT: {patent_idea['title']} (ID: {patent_idea['id']})
                
                REVIEW SCOPE:
                1. Patent law compliance (35 USC 101, 102, 103, 112)
                2. Claim strength and enforceability analysis
                3. Prior art conflict assessment
                4. Commercial licensing potential evaluation
                5. Portfolio strategy optimization
                6. International filing recommendations
                7. Prosecution timeline and budget planning
                
                PORTFOLIO CONTEXT:
                - Target Portfolio Value: $2-600M (expected ~$90M)
                - Filing Budget: ${PATENT_CONFIG['filing_cost_per_patent']} per provisional
                - Timeline: {PATENT_CONFIG['portfolio_tiers'][tier]['timeline']}
                
                LEGAL REQUIREMENTS:
                - 35 USC 101: Patentable subject matter (software/AI compliance)
                - 35 USC 102: Novelty (prior art analysis)
                - 35 USC 103: Non-obviousness (inventive step)
                - 35 USC 112: Enablement and written description
                
                COMMERCIAL ANALYSIS:
                - Licensing potential and market value
                - Competitive landscape assessment
                - Portfolio positioning and strategy
                - International filing recommendations
                - Prosecution cost-benefit analysis
                
                Use prior art analysis and refined claims to inform legal strategy.
                """,
                agent=legal_reviewer,
                expected_output="""Comprehensive legal review report including:
                - Patent law compliance assessment
                - Claim strength and enforceability analysis
                - Prior art conflict evaluation
                - Commercial licensing potential assessment
                - Portfolio strategy recommendations
                - International filing strategy
                - Prosecution timeline and budget
                - Risk assessment and mitigation strategies
                - Filing recommendations and next steps""",
                        context=[task for task in [research_task, claims_task, document_task] if task is not None],
                output_file=f"patent_output/{tier}/{patent_idea['id']}_legal_review.md"
            )
            
            # Enhanced final review task
            if should_skip_task('final_review', patent_id, tier):
                log_skip_reason('final_review', patent_id, 'File already exists')
                final_review_task = None
            else:
                final_review_task = Task(
                description=f"""
                Independent quality assurance review and improvement recommendations:
                
                PATENT: {patent_idea['title']} (ID: {patent_idea['id']})
                
                REVIEW OBJECTIVES:
                1. Fresh perspective analysis of completed work
                2. Quality gap identification and improvement opportunities
                3. Cross-functional review (technical, legal, commercial)
                4. Risk assessment and mitigation recommendations
                5. Iterative refinement suggestions
                6. Quality scoring and confidence assessment
                
                REVIEW SCOPE:
                - Prior art analysis completeness and accuracy
                - Claims refinement quality and strategic positioning
                - Patent application completeness and compliance
                - Legal review thoroughness and strategy
                - Commercial value optimization opportunities
                - Portfolio integration and positioning
                
                QUALITY METRICS:
                - Technical accuracy and completeness
                - Legal compliance and strategy
                - Commercial value optimization
                - Risk assessment and mitigation
                - Portfolio integration
                - Overall confidence level
                
                Provide actionable improvement recommendations for maximum patent value.
                """,
                agent=final_reviewer,
                expected_output="""Independent quality assurance report including:
                - Fresh perspective analysis of completed work
                - Quality gap identification and improvement opportunities
                - Cross-functional review assessment
                - Risk assessment and mitigation recommendations
                - Iterative refinement suggestions
                - Quality scoring and confidence assessment
                - Actionable improvement recommendations
                - Overall patent value optimization strategy""",
                        context=[task for task in [research_task, claims_task, document_task, review_task] if task is not None],
                output_file=f"patent_output/{tier}/{patent_idea['id']}_final_review.md"
            )
            
            # Enhanced cover sheet generation task
            if should_skip_task('cover_sheet', patent_id, tier):
                log_skip_reason('cover_sheet', patent_id, 'File already exists')
                cover_sheet_task = None
            else:
                cover_sheet_task = Task(
                description=f"""
                Generate USPTO-compliant provisional patent application cover sheet:
                
                PATENT: {patent_idea['title']} (ID: {patent_idea['id']})
                
                COVER SHEET REQUIREMENTS:
                1. USPTO provisional application cover sheet format
                2. Complete inventor and assignee information
                3. Accurate fee calculation and payment method
                4. Entity status determination and documentation
                5. Filing checklist and quality assurance
                6. USPTO form completion and compliance
                
                FILING INFORMATION:
                - Application type: Provisional Application for Patent
                - Inventor information: [To be filled from patent data]
                - Assignee information: [To be filled from patent data]
                - Correspondence address: [To be filled from patent data]
                - Entity status: [To be determined]
                - Fee calculation: [To be calculated]
                
                COMPLIANCE REQUIREMENTS:
                - 37 CFR 1.51(c)(1) compliance
                - Complete inventor and assignee information
                - Accurate fee calculation
                - Proper entity status determination
                - Filing checklist completion
                - Quality assurance verification
                
                Generate professional, USPTO-compliant cover sheet for filing.
                """,
                agent=cover_sheet_specialist,
                expected_output="""USPTO-compliant provisional application cover sheet including:
                - Complete inventor and assignee information
                - Accurate fee calculation and payment method
                - Entity status determination and documentation
                - Filing checklist and quality assurance
                - USPTO form completion and compliance
                - Professional formatting and presentation
                - Filing-ready documentation""",
                        context=[task for task in [research_task, claims_task, document_task, review_task, final_review_task] if task is not None],
                output_file=f"patent_output/{tier}/{patent_idea['id']}_cover_sheet.md"
            )
            
            # Add all tasks to the list
            all_tasks = [task for task in [research_task, claims_task, document_task, review_task, final_review_task, cover_sheet_task] if task is not None]
            tasks.extend(all_tasks)
            
        except Exception as e:
            print(f"Error creating tasks for patent {patent_idea.get('id', 'unknown')}: {str(e)}")
            continue
    
    return tasks 