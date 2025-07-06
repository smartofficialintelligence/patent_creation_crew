# ArxivSearchTool and dependencies will be moved here. 

import re
import time
import logging
from datetime import datetime
from typing import Dict, Any, List
from crewai.tools import BaseTool
from pydantic import BaseModel, validator

# Import from core modules
from core.validation import validate_patent_dict

# Optional import for arXiv
try:
    import arxiv
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False
    print("⚠️ ArXiv library not available. Install arxiv-python package for academic search.")

class ArxivSearchInput(BaseModel):
    patent_id: str
    title: str
    description: str
    key_claims: List[str]
    technical_features: List[str] = []

    @validator('patent_id', 'title', 'description')
    def required_fields_must_not_be_empty(cls, v):
        if v is None:
            raise ValueError('Required field must not be None')
        if isinstance(v, str) and not v.strip():
            raise ValueError('Required field must not be empty')
        return v

    @validator('key_claims')
    def key_claims_must_be_list(cls, v):
        if not isinstance(v, list):
            raise ValueError('key_claims must be a list')
        if not v:
            raise ValueError('key_claims must not be empty')
        return v

class ArxivSearchTool(BaseTool):
    name: str = "arxiv_search_tool"
    description: str = "Search academic papers on arXiv for relevant research and prior art analysis."
    args_schema: type[BaseModel] = ArxivSearchInput
    max_results: int = 20
    sort_by: str = "relevance"

    def __init__(self, max_results: int = 20, sort_by: str = "relevance"):
        super().__init__()
        self.max_results = max_results
        self.sort_by = sort_by

    def _run(self, patent_id: str = None, title: str = None, description: str = None, key_claims: List[str] = None, 
             technical_features: List[str] = None, query: str = None) -> str:
        """Search arXiv for academic papers related to the patent."""
        try:
            # Handle different parameter formats from agents
            if query and not description:
                description = query
                
            # Handle potential None values or empty strings
            patent_id = patent_id or "UNKNOWN"
            title = title or "Untitled Patent"
            description = description or "No description provided"
            key_claims = key_claims or ["No claims provided"]
            technical_features = technical_features or ["No technical features specified"]
            
            # All inputs are guaranteed valid by Pydantic
            patent_data = {
                'id': patent_id,
                'title': title,
                'description': description,
                'key_claims': key_claims,
                'technical_features': technical_features
            }
            
            search_queries = self._generate_search_queries(patent_data)
            all_results = []
            
            for query in search_queries[:3]:  # Limit to top 3 queries
                try:
                    papers = self._search_arxiv(query)
                    all_results.extend(papers)
                    time.sleep(1)  # Rate limiting
                except Exception as e:
                    logging.warning(f"arXiv search failed for query '{query}': {e}")
                    continue
            
            # Deduplicate results
            unique_results = self._deduplicate_results(all_results)
            
            # Analyze results
            analysis = self._analyze_academic_results(unique_results, patent_data)
            
            return self._generate_academic_report(analysis, patent_data)
            
        except Exception as e:
            error_msg = f"""
ERROR IN ARXIV SEARCH TOOL
==========================

Patent ID: {patent_id}
Error Type: {type(e).__name__}
Error Message: {str(e)}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

The tool encountered an unexpected error during arXiv search processing. This may be due to:
- ArXiv API connectivity issues
- Invalid search parameters
- Rate limiting
- Internal processing error

Please check the input parameters and try again. If the error persists, 
contact the system administrator.

Input Parameters Received:
- patent_id: {patent_id}
- title: {title[:100]}{'...' if len(title) > 100 else ''}
- description length: {len(description) if description else 0} characters
- key_claims count: {len(key_claims) if key_claims else 0}
- technical_features count: {len(technical_features) if technical_features else 0}

ArXiv Status:
- ArXiv Library Available: {ARXIV_AVAILABLE}
- Max Results: {self.max_results}
- Sort By: {self.sort_by}
"""
            logging.error(f"ArxivSearchTool error: {e}")
            return error_msg
    
    def _generate_search_queries(self, patent_data: Dict) -> List[str]:
        """Generate arXiv search queries from patent data"""
        queries = []
        
        title = patent_data.get('title', '').lower()
        description = patent_data.get('description', '').lower()
        claims = patent_data.get('key_claims', [])
        features = patent_data.get('technical_features', [])
        
        # Core concept queries
        core_terms = ['agent', 'optimization', 'semantic', 'reasoning', 'coordination', 'neural']
        for term in core_terms:
            if term in title or term in description:
                queries.append(f'all:"{term}"')
        
        # Multi-term queries
        if 'agent' in title and 'optimization' in title:
            queries.append('all:"agent-based optimization"')
            queries.append('all:"multi-agent optimization"')
        
        if 'semantic' in title and 'reasoning' in title:
            queries.append('all:"semantic reasoning"')
            queries.append('all:"semantic AI"')
        
        # Technical feature queries
        for feature in features:
            if isinstance(feature, str) and len(feature) > 3:
                queries.append(f'all:"{feature}"')
        
        # Claim-based queries
        for claim in claims[:3]:  # Use first 3 claims
            claim_terms = re.findall(r'\b\w+\b', claim.lower())
            important_terms = [term for term in claim_terms if len(term) > 4]
            if important_terms:
                queries.append(f'all:"{important_terms[0]}"')
        
        # Remove duplicates and limit
        unique_queries = list(set(queries))[:10]
        return unique_queries
    
    def _search_arxiv(self, query: str) -> List[Dict]:
        """Search arXiv using the arxiv-python library"""
        results = []
        
        try:
            # Configure search
            search = arxiv.Search(
                query=query,
                max_results=self.max_results,
                sort_by=arxiv.SortCriterion.Relevance if self.sort_by == "relevance" else arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            # Execute search
            for result in search.results():
                paper_data = {
                    'title': result.title,
                    'authors': [author.name for author in result.authors],
                    'summary': result.summary,
                    'published_date': result.published.strftime('%Y-%m-%d') if result.published else 'Unknown',
                    'arxiv_id': result.entry_id.split('/')[-1],
                    'categories': result.categories,
                    'pdf_url': result.pdf_url,
                    'relevance_score': 0.0  # Will be calculated later
                }
                results.append(paper_data)
                
        except Exception as e:
            logging.error(f"ArXiv search error for query '{query}': {e}")
        
        return results
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate papers based on arXiv ID"""
        seen_ids = set()
        unique_results = []
        
        for result in results:
            arxiv_id = result.get('arxiv_id')
            if arxiv_id and arxiv_id not in seen_ids:
                seen_ids.add(arxiv_id)
                unique_results.append(result)
        
        return unique_results
    
    def _analyze_academic_results(self, papers: List[Dict], patent_data: Dict) -> Dict:
        """Analyze academic papers for relevance and impact"""
        
        analyzed_papers = []
        total_papers = len(papers)
        
        for paper in papers:
            # Calculate relevance score based on content overlap
            relevance_score = self._calculate_paper_relevance(paper, patent_data)
            paper['relevance_score'] = relevance_score
            
            # Categorize by relevance
            if relevance_score >= 7.0:
                paper['relevance_level'] = 'HIGH'
            elif relevance_score >= 4.0:
                paper['relevance_level'] = 'MEDIUM'
            else:
                paper['relevance_level'] = 'LOW'
            
            analyzed_papers.append(paper)
        
        # Sort by relevance
        analyzed_papers.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Calculate statistics
        high_relevance = [p for p in analyzed_papers if p['relevance_level'] == 'HIGH']
        medium_relevance = [p for p in analyzed_papers if p['relevance_level'] == 'MEDIUM']
        low_relevance = [p for p in analyzed_papers if p['relevance_level'] == 'LOW']
        
        return {
            'total_papers': total_papers,
            'high_relevance': high_relevance,
            'medium_relevance': medium_relevance,
            'low_relevance': low_relevance,
            'all_papers': analyzed_papers,
            'search_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _calculate_paper_relevance(self, paper: Dict, patent_data: Dict) -> float:
        """Calculate relevance score for a paper (0-10)"""
        score = 0.0
        
        title = paper.get('title', '').lower()
        summary = paper.get('summary', '').lower()
        categories = paper.get('categories', [])
        
        patent_title = patent_data.get('title', '').lower()
        patent_desc = patent_data.get('description', '').lower()
        patent_claims = patent_data.get('key_claims', [])
        patent_features = patent_data.get('technical_features', [])
        
        # Title relevance (weight: 3.0)
        title_overlap = self._calculate_text_overlap(title, patent_title)
        score += title_overlap * 3.0
        
        # Summary relevance (weight: 4.0)
        summary_overlap = self._calculate_text_overlap(summary, patent_desc)
        score += summary_overlap * 4.0
        
        # Technical feature overlap (weight: 2.0)
        feature_overlap = 0.0
        for feature in patent_features:
            if isinstance(feature, str) and feature.lower() in summary:
                feature_overlap += 1.0
        feature_overlap = min(feature_overlap / max(len(patent_features), 1), 1.0)
        score += feature_overlap * 2.0
        
        # Category relevance (weight: 1.0)
        relevant_categories = ['cs.ai', 'cs.lg', 'cs.ne', 'cs.sy', 'stat.ml']
        category_score = sum(1 for cat in categories if cat in relevant_categories) / len(relevant_categories)
        score += category_score * 1.0
        
        return min(score, 10.0)
    
    def _calculate_text_overlap(self, text1: str, text2: str) -> float:
        """Calculate text overlap between two strings"""
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _generate_academic_report(self, analysis: Dict, patent_data: Dict) -> str:
        """Generate comprehensive academic literature report"""
        
        report = f"""
ARXIV ACADEMIC LITERATURE SEARCH REPORT
=======================================

Patent: {patent_data.get('title', 'Unknown')}
Search Date: {analysis['search_date']}
Total Papers Found: {analysis['total_papers']}

SEARCH SUMMARY:
==============

Papers by Relevance Level:
- High Relevance: {len(analysis['high_relevance'])} papers
- Medium Relevance: {len(analysis['medium_relevance'])} papers  
- Low Relevance: {len(analysis['low_relevance'])} papers

HIGH RELEVANCE PAPERS:
=====================

"""
        
        if analysis['high_relevance']:
            for i, paper in enumerate(analysis['high_relevance'][:5], 1):  # Show top 5
                report += f"""
{i}. {paper['title']}
   Authors: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}
   arXiv ID: {paper['arxiv_id']}
   Published: {paper['published_date']}
   Categories: {', '.join(paper['categories'][:3])}
   Relevance Score: {paper['relevance_score']:.1f}/10
   
   Summary: {paper['summary'][:300]}{'...' if len(paper['summary']) > 300 else ''}
   
   PDF: {paper['pdf_url']}
"""
        else:
            report += "No high relevance papers found.\n"
        
        report += f"""
MEDIUM RELEVANCE PAPERS:
=======================

"""
        
        if analysis['medium_relevance']:
            for i, paper in enumerate(analysis['medium_relevance'][:3], 1):  # Show top 3
                report += f"""
{i}. {paper['title']}
   Authors: {', '.join(paper['authors'][:2])}{'...' if len(paper['authors']) > 2 else ''}
   Relevance Score: {paper['relevance_score']:.1f}/10
   Categories: {', '.join(paper['categories'][:2])}
"""
        else:
            report += "No medium relevance papers found.\n"
        
        # Academic impact analysis
        report += f"""
ACADEMIC IMPACT ANALYSIS:
========================

Research Trends:
- Papers in AI/ML categories: {len([p for p in analysis['all_papers'] if any(cat in ['cs.ai', 'cs.lg', 'stat.ml'] for cat in p.get('categories', []))])}
- Recent papers (2023+): {len([p for p in analysis['all_papers'] if p.get('published_date', '') >= '2023-01-01'])}
- Multi-author collaborations: {len([p for p in analysis['all_papers'] if len(p.get('authors', [])) > 3])}

Novelty Assessment:
- Academic novelty score: {self._calculate_academic_novelty(analysis):.1f}/10
- Research gap identification: {'Strong' if len(analysis['high_relevance']) < 3 else 'Moderate'}
- Commercial opportunity: {'High' if len(analysis['high_relevance']) < 5 else 'Moderate'}

RECOMMENDATIONS:
===============

Academic Strategy:
"""
        
        if len(analysis['high_relevance']) == 0:
            report += "- ✅ Strong academic novelty - limited prior research in this specific area\n"
            report += "- 🎯 Opportunity to establish academic leadership in this field\n"
        elif len(analysis['high_relevance']) < 3:
            report += "- ⚠️ Moderate academic novelty - some related research exists\n"
            report += "- 📚 Review high-relevance papers for differentiation opportunities\n"
        else:
            report += "- ⚠️ Limited academic novelty - significant prior research exists\n"
            report += "- 🔍 Focus on specific technical differentiators and applications\n"
        
        report += f"""
Patent Strategy:
- Academic novelty supports patent novelty: {'Yes' if len(analysis['high_relevance']) < 3 else 'Partially'}
- Research gap supports broad claims: {'Yes' if len(analysis['high_relevance']) < 2 else 'No'}
- Academic citations potential: {'High' if len(analysis['medium_relevance']) > 5 else 'Moderate'}

CONCLUSION:
==========
Academic literature search completed successfully.
Total papers analyzed: {analysis['total_papers']}
Recommendation: {'PROCEED' if len(analysis['high_relevance']) < 3 else 'REVIEW CLAIMS'}

END OF ACADEMIC LITERATURE REPORT
"""
        
        return report
    
    def _calculate_academic_novelty(self, analysis: Dict) -> float:
        """Calculate academic novelty score based on search results"""
        high_relevance_count = len(analysis['high_relevance'])
        medium_relevance_count = len(analysis['medium_relevance'])
        
        # Higher novelty if fewer relevant papers exist
        if high_relevance_count == 0:
            return 9.0
        elif high_relevance_count <= 2:
            return 7.0
        elif high_relevance_count <= 5:
            return 5.0
        else:
            return 3.0 