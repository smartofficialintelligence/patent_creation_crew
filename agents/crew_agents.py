# create_enhanced_agents and agent factory logic will be moved here. 

import os
from tools.real_patent_search import RealPatentSearchTool
from tools.arxiv_search import ArxivSearchTool
from tools.consolidated_risk_assessment import ConsolidatedRiskAssessmentTool
from tools.vector_based_overlap_analysis import VectorBasedOverlapAnalysisTool
from tools.patent_document import PatentDocumentTool
from tools.smart_claim_refinement import SmartClaimRefinementTool
from tools.final_review_and_improvement import FinalReviewAndImprovementTool
from tools.provisional_cover_sheet import ProvisionalCoverSheetTool

# Placeholders for any global variables or settings
USE_VECTOR_ANALYSIS = True  # Set appropriately in your main config
DISABLE_VECTOR_ANALYSIS = False  # Set appropriately in your main config

# Placeholders for Agent class (should be imported from CrewAI or your agent framework)
try:
    from crewai import Agent
except ImportError:
    Agent = object  # fallback for static analysis

# The actual function

def create_enhanced_agents():
    """Create enhanced CrewAI agents with improved prompting and capabilities"""
    
    lens_api_key = os.getenv('LENS_API_KEY')
    epo_api_key = os.getenv('EPO_API_KEY')
    
    # Create tool instances with proper initialization
    real_patent_search_tool = RealPatentSearchTool(lens_api_key=lens_api_key, epo_api_key=epo_api_key)
    arxiv_search_tool = ArxivSearchTool()
    consolidated_risk_tool = ConsolidatedRiskAssessmentTool()
    vector_analysis_tool = VectorBasedOverlapAnalysisTool() if USE_VECTOR_ANALYSIS and not DISABLE_VECTOR_ANALYSIS else None
    patent_document_tool = PatentDocumentTool()
    smart_claim_tool = SmartClaimRefinementTool()
    final_review_tool = FinalReviewAndImprovementTool()
    cover_sheet_tool = ProvisionalCoverSheetTool()
    
    # Build tools list for patent researcher
    researcher_tools = [real_patent_search_tool, arxiv_search_tool, consolidated_risk_tool]
    if vector_analysis_tool:
        researcher_tools.append(vector_analysis_tool)
    
    patent_researcher = Agent(
        role='Senior Patent Research Specialist',
        goal='Conduct comprehensive prior art searches and provide detailed patentability analysis for agent-based optimization technologies',
        backstory="""You are a world-class patent researcher with 15+ years of experience in AI, 
        machine learning, and software patents. You have deep expertise in:
        - USPTO, EPO, and international patent databases
        - AI optimization technologies and multi-agent systems
        - Patent classification systems and search strategies
        - Academic literature and technical publication analysis
        - Competitive intelligence and technology landscape mapping
        
        You excel at identifying subtle technical distinctions and crafting strong prior art 
        differentiation strategies. You understand both the technical and legal aspects of 
        patentability.""",
        tools=researcher_tools,
        verbose=True,
        max_iter=3,
        memory=True
    )

    patent_writer = Agent(
        role='Senior Patent Document Specialist',
        goal='Create comprehensive, legally compliant patent applications that maximize commercial value and enforceability',
        backstory="""You are an expert technical patent writer with 12+ years of experience 
        drafting AI and software patents. Your expertise includes:
        - USPTO patent prosecution requirements and best practices
        - Technical specification writing for complex AI systems
        - Claim drafting strategies for maximum breadth and validity
        - Commercial value optimization through strategic claim structure
        - Regulatory compliance and explainable AI requirements
        
        You consistently produce patent applications that successfully navigate prosecution 
        and provide strong competitive positioning. You understand how to balance technical 
        detail with legal protection.""",
        tools=[patent_document_tool],
        verbose=True,
        max_iter=3,
        memory=True
    )

    claims_specialist = Agent(
        role='Patent Claims Strategist',
        goal='Craft optimally broad yet defensible patent claims that maximize licensing value while avoiding prior art conflicts',
        backstory="""You are a patent claims specialist with 20+ years of experience in 
        high-value technology patents. Your expertise includes:
        - Strategic claim drafting for maximum commercial impact
        - Prior art navigation and differentiation strategies  
        - Patent prosecution and amendment strategies
        - Licensing and enforcement considerations
        - International patent portfolio development
        
        You have successfully crafted claims for patents worth hundreds of millions in 
        licensing revenue. You understand the nuances of claim scope, validity, and 
        commercial value optimization.""",
        tools=[smart_claim_tool],
        verbose=True,
        max_iter=3,
        memory=True
    )

    legal_reviewer = Agent(
        role='Patent Portfolio Legal Strategist',
        goal='Ensure patent applications meet all legal requirements and optimize portfolio strategy for maximum commercial value',
        backstory="""You are a senior patent attorney specializing in AI and software 
        technologies with 18+ years of experience. Your expertise includes:
        - Patent law compliance and prosecution strategy
        - Portfolio development and monetization strategies
        - Technology transfer and licensing negotiations
        - Patent litigation and enforcement
        - International patent strategy and filing decisions
        
        You have managed patent portfolios worth billions in valuation and successfully 
        negotiated licensing deals generating hundreds of millions in revenue. You understand 
        the intersection of technical innovation, legal protection, and commercial value.""",
        verbose=True,
        max_iter=2,
        memory=True
    )
    
    final_reviewer = Agent(
        role='Independent Patent Quality Assurance Specialist',
        goal='Provide fresh perspective review and iterative improvement suggestions for completed patent work',
        backstory="""You are an independent patent quality assurance specialist with 15+ years 
        of experience in patent review and improvement. Your expertise includes:
        - Fresh perspective analysis of completed patent work
        - Quality gap identification and improvement recommendations
        - Iterative refinement strategies for patent applications
        - Cross-functional review of technical, legal, and commercial aspects
        - Quality scoring and confidence assessment
        - Risk mitigation and enhancement opportunities
        
        You have reviewed thousands of patent applications and helped improve their quality, 
        leading to higher grant rates and commercial success. You excel at identifying 
        overlooked opportunities and providing actionable improvement recommendations.""",
        tools=[final_review_tool],
        verbose=True,
        max_iter=3,
        memory=True
    )

    cover_sheet_specialist = Agent(
        role='USPTO Filing Specialist',
        goal='Generate USPTO-compliant provisional patent application cover sheets and filing documentation',
        backstory="""You are a USPTO filing specialist with 12+ years of experience in 
        patent application preparation and filing. Your expertise includes:
        - USPTO provisional application requirements and procedures
        - Cover sheet preparation and compliance
        - Fee calculation and payment methods
        - Entity status determination and documentation
        - Filing checklist and quality assurance
        - USPTO form completion and submission
        
        You have successfully filed thousands of provisional and non-provisional patent 
        applications with the USPTO. You understand all filing requirements, fee structures, 
        and compliance procedures to ensure successful patent application submission.""",
        tools=[cover_sheet_tool],
        verbose=True,
        max_iter=2,
        memory=True
    )
    
    return patent_researcher, patent_writer, claims_specialist, legal_reviewer, final_reviewer, cover_sheet_specialist 