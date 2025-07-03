#!/usr/bin/env python3
"""
Script to remove all remaining tool classes from patent_automation_system.py
"""

import re

def remove_tool_classes():
    """Remove all remaining tool classes from the main file"""
    
    with open('patent_automation_system.py', 'r') as f:
        content = f.read()
    
    # List of tool classes to remove
    tool_classes = [
        'FinalReviewAndImprovementTool',
        'RealPatentSearchTool', 
        'VectorBasedOverlapAnalysisTool',
        'ArxivSearchTool',
        'ConsolidatedRiskAssessmentTool',
        'ColabDemoGeneratorTool'
    ]
    
    # Pattern to match tool class definitions and their content
    for tool_class in tool_classes:
        # Pattern to match the entire class definition
        pattern = rf'class {tool_class}\(.*?\):.*?(?=class |def |# |$)'
        
        # Remove the class
        content = re.sub(pattern, f'# {tool_class} moved to tools/{tool_class.lower()}.py', content, flags=re.DOTALL)
    
    # Clean up any remaining indented code that might be orphaned
    lines = content.split('\n')
    cleaned_lines = []
    skip_until_next_class = False
    
    for line in lines:
        if line.strip().startswith('# ') and 'moved to tools/' in line:
            cleaned_lines.append(line)
            skip_until_next_class = True
        elif line.strip().startswith('class ') or line.strip().startswith('def ') or line.strip().startswith('# Main CLI'):
            skip_until_next_class = False
            cleaned_lines.append(line)
        elif not skip_until_next_class:
            cleaned_lines.append(line)
    
    # Write the cleaned content back
    with open('patent_automation_system.py', 'w') as f:
        f.write('\n'.join(cleaned_lines))
    
    print("✅ Removed all remaining tool classes from patent_automation_system.py")

if __name__ == "__main__":
    remove_tool_classes() 