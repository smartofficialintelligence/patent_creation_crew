# Miscellaneous helpers will be moved here. 

import os
import re
import logging
from typing import List, Dict, Optional
import shutil

# Placeholders for any global variables or settings
RESUME_MODE = False  # Set appropriately in your main config
FORCE_OVERWRITE = False  # Set appropriately in your main config
EXPORT_FORMATS = ['md']  # Set appropriately in your main config
MARKDOWN_AVAILABLE = False  # Set appropriately in your main config
JINJA2_AVAILABLE = False  # Set appropriately in your main config

# Placeholders for logger (should be configured in your main script)
try:
    logger = logging.getLogger(__name__)
except:
    logger = logging.getLogger()

# Placeholders for any missing imports
try:
    import markdown
    from jinja2 import Template
    MARKDOWN_AVAILABLE = True
    JINJA2_AVAILABLE = True
except ImportError:
    pass

# The actual functions

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists"""
    return os.path.exists(filepath)

def should_skip_task(task_type: str, patent_id: str, tier: str) -> bool:
    """Determine if a task should be skipped based on existing files and resume mode"""
    if not RESUME_MODE:
        return False
    
    if FORCE_OVERWRITE:
        return False
    
    # Define file patterns for each task type
    file_patterns = {
        'prior_art': f"patent_output/{tier}/{patent_id}_prior_art_analysis.md",
        'claims': f"patent_output/{tier}/{patent_id}_refined_claims.md",
        'patent_application': f"patent_output/{tier}/{patent_id}_patent_application.md",
        'legal_review': f"patent_output/{tier}/{patent_id}_legal_review.md",
        'overlap_analysis': f"patent_output/{tier}/{patent_id}_overlap_analysis.md",
        'associate_editor_review': f"patent_output/{tier}/{patent_id}_associate_editor_review.md",
        'editorial_review': f"patent_output/{tier}/{patent_id}_editorial_review.md",
        'patent_integration': f"patent_output/{tier}/{patent_id}_patent_application_final.md",
        'cover_sheet': f"patent_output/{tier}/{patent_id}_cover_sheet.md"
    }
    
    if task_type in file_patterns:
        return check_file_exists(file_patterns[task_type])
    
    return False

def log_skip_reason(task_type: str, patent_id: str, reason: str):
    """Log why a task was skipped"""
    logger.info(f"⏭️  Skipping {task_type} for {patent_id}: {reason}")

def export_report(content: str, filename: str, formats: List[str] = None) -> Dict[str, str]:
    """Export report content to multiple formats"""
    global EXPORT_FORMATS
    if formats is None:
        formats = EXPORT_FORMATS
    
    exported_files = {}
    
    # Always save as Markdown (base format)
    if 'md' in formats or not formats:
        md_file = f"{filename}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(content)
        exported_files['md'] = md_file
    
    # Export to HTML if requested and available
    if 'html' in formats and MARKDOWN_AVAILABLE and JINJA2_AVAILABLE:
        try:
            html_file = f"{filename}.html"
            html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])
            
            # Create a styled HTML template
            html_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; margin: 40px; }
        h1, h2, h3 { color: #2c3e50; }
        h1 { border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; margin-top: 30px; }
        code { background-color: #f8f9fa; padding: 2px 4px; border-radius: 3px; }
        pre { background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .highlight { background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; }
        .success { background-color: #d4edda; padding: 10px; border-left: 4px solid #28a745; }
        .error { background-color: #f8d7da; padding: 10px; border-left: 4px solid #dc3545; }
    </style>
</head>
<body>
    {{ content }}
</body>
</html>
"""
            template = Template(html_template)
            full_html = template.render(title=filename.split('/')[-1], content=html_content)
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(full_html)
            exported_files['html'] = html_file
        except Exception as e:
            logging.warning(f"HTML export failed: {e}")
    
    # Export to PDF if requested and available
    if 'pdf' in formats and 'html' in exported_files:
        try:
            from weasyprint import HTML, CSS
            pdf_file = f"{filename}.pdf"
            html_file = exported_files['html']
            
            # Read the HTML file
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Convert to PDF
            HTML(string=html_content).write_pdf(pdf_file)
            exported_files['pdf'] = pdf_file
        except Exception as e:
            logging.warning(f"PDF export failed: {e}")
    
    return exported_files

def highlight_overlapping_terms(claims: List[str], prior_art_data: List[Dict]) -> str:
    """Highlight overlapping terms between claims and prior art for conflict analysis"""
    
    # Extract key terms from claims
    claim_terms = set()
    for claim in claims:
        # Extract technical terms (words with 4+ characters, excluding common words)
        words = re.findall(r'\b\w{4,}\b', claim.lower())
        # Filter out common words
        common_words = {'method', 'system', 'comprising', 'wherein', 'further', 'including', 'based', 'using', 'through', 'within', 'between', 'among', 'during', 'while', 'before', 'after', 'when', 'where', 'which', 'that', 'this', 'with', 'from', 'into', 'onto', 'upon', 'about', 'against', 'toward', 'towards', 'without', 'under', 'over', 'above', 'below', 'behind', 'beneath', 'beside', 'beyond', 'across', 'along', 'around', 'throughout', 'despite', 'except', 'excepting', 'excluding', 'following', 'including', 'like', 'minus', 'near', 'off', 'onto', 'opposite', 'outside', 'past', 'per', 'plus', 'regarding', 'round', 'save', 'since', 'than', 'versus', 'via', 'worth'}
        technical_terms = [word for term in words if term not in common_words]
        claim_terms.update(technical_terms)
    
    # Extract terms from prior art
    prior_art_terms = {}
    for patent in prior_art_data:
        patent_id = patent.get('patent_number', 'Unknown')
        title_terms = set(re.findall(r'\b\w{4,}\b', patent.get('title', '').lower()))
        abstract_terms = set(re.findall(r'\b\w{4,}\b', patent.get('abstract', '').lower()))
        all_terms = title_terms.union(abstract_terms)
        # Filter common words
        all_terms = {term for term in all_terms if term not in common_words}
        prior_art_terms[patent_id] = all_terms
    
    # Find overlapping terms
    overlaps = {}
    for patent_id, patent_terms in prior_art_terms.items():
        overlap = claim_terms.intersection(patent_terms)
        if overlap:
            overlaps[patent_id] = {
                'overlapping_terms': list(overlap),
                'overlap_count': len(overlap),
                'patent_title': next((p.get('title', 'Unknown') for p in prior_art_data if p.get('patent_number') == patent_id), 'Unknown'),
                'relevance_score': next((p.get('relevance_score', 0) for p in prior_art_data if p.get('patent_number') == patent_id), 0)
            }
    
    # Generate overlap report
    report = f"""
OVERLAPPING TERMS ANALYSIS
==========================

Patent Claims Analysis:
- Total unique technical terms in claims: {len(claim_terms)}
- Key claim terms: {', '.join(sorted(list(claim_terms))[:20])}{'...' if len(claim_terms) > 20 else ''}

Prior Art Overlap Analysis:
- Patents analyzed: {len(prior_art_data)}
- Patents with term overlaps: {len(overlaps)}

OVERLAP DETAILS:
"""
    
    if overlaps:
        # Sort by overlap count and relevance score
        sorted_overlaps = sorted(overlaps.items(), 
                               key=lambda x: (x[1]['overlap_count'], x[1]['relevance_score']), 
                               reverse=True)
        
        for patent_id, overlap_data in sorted_overlaps:
            report += f"""
Patent: {patent_id} - "{overlap_data['patent_title']}"
- Overlap Count: {overlap_data['overlap_count']} terms
- Relevance Score: {overlap_data['relevance_score']:.1f}/10
- Overlapping Terms: {', '.join(overlap_data['overlapping_terms'])}
"""
    else:
        report += "\n✅ No significant term overlaps found with prior art.\n"
    
    # Risk assessment
    high_risk_overlaps = [p for p in overlaps.values() if p['overlap_count'] >= 3 and p['relevance_score'] >= 6.0]
    medium_risk_overlaps = [p for p in overlaps.values() if p['overlap_count'] >= 2 and p['relevance_score'] >= 4.0]
    
    report += f"""
RISK ASSESSMENT:
===============

High Risk Overlaps (≥3 terms, ≥6.0 relevance): {len(high_risk_overlaps)}
Medium Risk Overlaps (≥2 terms, ≥4.0 relevance): {len(medium_risk_overlaps)}

RECOMMENDATIONS:
===============

"""
    
    if high_risk_overlaps:
        report += """
⚠️ HIGH RISK - IMMEDIATE ACTION REQUIRED:
- Consider claim refinement to avoid overlapping terms
- Focus on semantic reasoning and performance differentiators
- Emphasize unique technical features (GPU optimization, sub-5ms cycles)
- Consider alternative claim language for overlapping concepts
"""
    elif medium_risk_overlaps:
        report += """
⚠️ MEDIUM RISK - MONITOR AND REFINE:
- Monitor overlapping terms during prosecution
- Consider claim amendments to reduce overlap
- Emphasize unique technical differentiators
- Focus on performance and implementation specifics
"""
    else:
        report += """
✅ LOW RISK - PROCEED WITH CONFIDENCE:
- Minimal term overlap with prior art
- Strong differentiation potential
- Focus on commercial value optimization
- Proceed with filing strategy
"""
    
    return report 

def print_log_errors(logfile='patent_automation.log'):
    """Print all error, fail, exception, and warning lines from the log file."""
    keywords = [r'error', r'fail', r'exception', r'warning']
    pattern = re.compile(r'(' + '|'.join(keywords) + r')', re.IGNORECASE)
    try:
        with open(logfile, 'r') as f:
            for line in f:
                if pattern.search(line):
                    print(line.strip())
    except FileNotFoundError:
        print(f"Log file not found: {logfile}")
    except Exception as e:
        print(f"Error reading log file: {e}")

def clear_outputs():
    """Delete all files and subfolders in 'patent_output' and 'vector_cache', but keep the directories themselves."""
    for folder in ['patent_output', 'vector_cache']:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
    print("All output and cache directories cleared.") 

def extract_valuation_data_from_output(output_text: str) -> Optional[Dict]:
    """
    Extract structured valuation data from tool output text.
    
    Args:
        output_text: The output text from the patent_valuation_tool
        
    Returns:
        Dict containing valuation data if found, None otherwise
    """
    try:
        # Look for the JSON data marker
        start_marker = "<!-- VALUATION_JSON_DATA\n"
        end_marker = "\nVALUATION_JSON_DATA -->"
        
        start_idx = output_text.find(start_marker)
        if start_idx == -1:
            return None
            
        end_idx = output_text.find(end_marker, start_idx)
        if end_idx == -1:
            return None
            
        # Extract the JSON data
        json_start = start_idx + len(start_marker)
        json_text = output_text[json_start:end_idx].strip()
        
        # Parse the JSON
        import json
        valuation_data = json.loads(json_text)
        return valuation_data
        
    except Exception as e:
        logging.warning(f"Failed to extract valuation data: {e}")
        return None

def aggregate_portfolio_valuation(valuation_data_list: List[Dict]) -> Dict:
    """
    Aggregate valuation data from multiple patents into portfolio summary.
    
    Args:
        valuation_data_list: List of valuation data dictionaries
        
    Returns:
        Dict containing aggregated portfolio valuation
    """
    if not valuation_data_list:
        return {
            "total_patents": 0,
            "total_low_value": 0,
            "total_high_value": 0,
            "total_mid_value": 0,
            "average_mid_value": 0,
            "value_categories": {},
            "confidence_levels": {}
        }
    
    total_low = sum(data["valuation"]["low_value"] for data in valuation_data_list)
    total_high = sum(data["valuation"]["high_value"] for data in valuation_data_list)
    total_mid = sum(data["valuation"]["mid_value"] for data in valuation_data_list)
    
    # Count categories and confidence levels
    categories = {}
    confidence_levels = {}
    
    for data in valuation_data_list:
        category = data["valuation"]["category"]
        confidence = data["valuation"]["confidence"]
        
        categories[category] = categories.get(category, 0) + 1
        confidence_levels[confidence] = confidence_levels.get(confidence, 0) + 1
    
    return {
        "total_patents": len(valuation_data_list),
        "total_low_value": total_low,
        "total_high_value": total_high,
        "total_mid_value": total_mid,
        "average_mid_value": total_mid / len(valuation_data_list) if valuation_data_list else 0,
        "value_categories": categories,
        "confidence_levels": confidence_levels
    }

def collect_valuation_results_from_outputs(output_files: List[str]) -> List[Dict]:
    """
    Collect valuation results from output files.
    
    Args:
        output_files: List of file paths to check for valuation data
        
    Returns:
        List of valuation data dictionaries
    """
    valuation_data_list = []
    
    for file_path in output_files:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # First try to extract structured JSON data
                valuation_data = extract_valuation_data_from_output(content)
                
                # If JSON extraction fails, try manual extraction from report content
                if not valuation_data:
                    valuation_data = extract_valuation_from_report_content(content, file_path)
                
                if valuation_data:
                    valuation_data_list.append(valuation_data)
                    
        except Exception as e:
            logging.warning(f"Failed to read file {file_path}: {e}")
            continue
    
    return valuation_data_list

def extract_valuation_from_report_content(content: str, file_path: str) -> Optional[Dict]:
    """
    Manually extract valuation data from report content when JSON data is not available.
    
    Args:
        content: The report content
        file_path: The file path for context
        
    Returns:
        Dict containing valuation data if found, None otherwise
    """
    try:
        # Extract patent ID from filename
        import re
        patent_id_match = re.search(r'([A-Z]\d+)_valuation_report\.md', file_path)
        patent_id = patent_id_match.group(1) if patent_id_match else "UNKNOWN"
        
        # Parse the valuation summary section
        lines = content.split('\n')
        valuation_data = {
            "patent_id": patent_id,
            "title": "Unknown Title",
            "valuation": {
                "low_value": 0,
                "high_value": 0,
                "mid_value": 0,
                "category": "UNKNOWN",
                "confidence": "UNKNOWN"
            },
            "factors": {
                "base_value": 0,
                "market_factor": 0,
                "innovation_factor": 0,
                "risk_factor": 0,
                "regulatory_factor": 0,
                "competitive_factor": 0
            }
        }
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Extract title
            if "Title:" in line and "Title:" in line.split(":")[0]:
                title = line.split("Title:")[1].strip()
                valuation_data["title"] = title
            
            # Extract value range
            elif "Estimated Value Range:" in line:
                try:
                    value_part = line.split(":")[1].strip()
                    low_str, high_str = value_part.split(" - ")
                    low_value = float(low_str.replace("$", "").replace("M", ""))
                    high_value = float(high_str.replace("$", "").replace("M", ""))
                    valuation_data["valuation"]["low_value"] = low_value
                    valuation_data["valuation"]["high_value"] = high_value
                    valuation_data["valuation"]["mid_value"] = (low_value + high_value) / 2
                except:
                    pass
            
            # Extract mid-point value
            elif "Mid-Point Value:" in line:
                try:
                    value_part = line.split(":")[1].strip()
                    mid_value = float(value_part.replace("$", "").replace("M", ""))
                    valuation_data["valuation"]["mid_value"] = mid_value
                except:
                    pass
            
            # Extract value category
            elif "Value Category:" in line:
                category = line.split(":")[1].strip()
                valuation_data["valuation"]["category"] = category
            
            # Extract confidence level
            elif "Confidence Level:" in line:
                confidence = line.split(":")[1].strip()
                valuation_data["valuation"]["confidence"] = confidence
            
            # Extract base value
            elif "BASE VALUE:" in line:
                try:
                    value_part = line.split(":")[1].strip()
                    base_value = float(value_part.replace("$", "").replace("M", ""))
                    valuation_data["factors"]["base_value"] = base_value
                except:
                    pass
            
            # Extract market factor
            elif "MARKET FACTOR:" in line:
                try:
                    value_part = line.split(":")[1].strip()
                    market_factor = float(value_part.replace("x", ""))
                    valuation_data["factors"]["market_factor"] = market_factor
                except:
                    pass
            
            # Extract innovation factor
            elif "INNOVATION FACTOR:" in line:
                try:
                    value_part = line.split(":")[1].strip()
                    innovation_factor = float(value_part.replace("x", ""))
                    valuation_data["factors"]["innovation_factor"] = innovation_factor
                except:
                    pass
            
            # Extract risk factor
            elif "RISK FACTOR:" in line:
                try:
                    value_part = line.split(":")[1].strip()
                    risk_factor = float(value_part.replace("x", ""))
                    valuation_data["factors"]["risk_factor"] = risk_factor
                except:
                    pass
            
            # Extract regulatory factor
            elif "REGULATORY FACTOR:" in line:
                try:
                    value_part = line.split(":")[1].strip()
                    regulatory_factor = float(value_part.replace("x", ""))
                    valuation_data["factors"]["regulatory_factor"] = regulatory_factor
                except:
                    pass
            
            # Extract competitive factor
            elif "COMPETITIVE FACTOR:" in line:
                try:
                    value_part = line.split(":")[1].strip()
                    competitive_factor = float(value_part.replace("x", ""))
                    valuation_data["factors"]["competitive_factor"] = competitive_factor
                except:
                    pass
        
        # Only return if we found meaningful valuation data
        if valuation_data["valuation"]["mid_value"] > 0:
            return valuation_data
        else:
            return None
            
    except Exception as e:
        logging.warning(f"Failed to extract valuation from report content: {e}")
        return None 