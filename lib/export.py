# export_report and export helpers will be moved here. 

import logging
from typing import List, Dict

# Placeholders for any global variables or settings
EXPORT_FORMATS = ['md']  # Set appropriately in your main config
MARKDOWN_AVAILABLE = False  # Set appropriately in your main config
JINJA2_AVAILABLE = False  # Set appropriately in your main config

# Placeholders for any missing imports
try:
    import markdown
    from jinja2 import Template
    MARKDOWN_AVAILABLE = True
    JINJA2_AVAILABLE = True
except ImportError:
    pass

# The actual function

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