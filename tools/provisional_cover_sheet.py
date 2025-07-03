# ProvisionalCoverSheetTool and dependencies will be moved here. 

from datetime import datetime
from typing import Dict, Any
from langchain.tools import BaseTool
from crewai.tools.base_tool import BaseTool
from pydantic import BaseModel

# Import from core modules
from core.validation import validate_patent_dict

import logging
from typing import Dict, List, Any
from langchain.tools import BaseTool

class ProvisionalCoverSheetInput(BaseModel):
    patent_id: str = None
    title: str = None
    inventor: str = None
    filing_date: str = None
    entity_status: str = None

class ProvisionalCoverSheetTool(BaseTool):
    name: str = "provisional_cover_sheet_tool"
    description: str = "Generate USPTO-compliant provisional patent application cover sheets and filing documentation."
    args_schema: type[BaseModel] = ProvisionalCoverSheetInput

    def __init__(self):
        super().__init__()

    def _run(self, *args, **kwargs) -> str:
        """Generate USPTO-compliant provisional patent application cover sheet"""
        
        # Handle both positional and keyword arguments
        if args and isinstance(args[0], dict):
            patent_data = args[0]
        elif 'patent_data' in kwargs:
            patent_data = kwargs['patent_data']
        else:
            patent_data = {
                'id': kwargs.get('id', ''),
                'title': kwargs.get('title', ''),
                'description': kwargs.get('description', ''),
                'key_claims': kwargs.get('key_claims', ''),
                'technical_features': kwargs.get('technical_features', ''),
                'market_applications': kwargs.get('market_applications', ''),
                'value_estimate': kwargs.get('value_estimate', ''),
                'differentiation': kwargs.get('differentiation', '')
            }
        
        # Validate input
        validated_data = validate_patent_dict(patent_data)
        
        patent_id = validated_data['id']
        title = validated_data['title']
        description = validated_data['description']
        inventors = validated_data.get('inventors', ['Primary Inventor'])
        assignee = validated_data.get('assignee', 'Patent Holder')
        attorney_docket = validated_data.get('attorney_docket', f'PAT-{patent_id}')
        
        # Generate filing date (today's date)
        filing_date = datetime.now().strftime('%m/%d/%Y')
        
        # Calculate page count estimate (rough estimate: 1 page per 500 words)
        word_count = len(description.split())
        estimated_pages = max(1, (word_count // 500) + 1)
        
        # Generate cover sheet content
        cover_sheet = f"""
PROVISIONAL APPLICATION FOR PATENT COVER SHEET
==============================================

[37 CFR 1.51(c)(1)]

PATENT APPLICATION INFORMATION:
==============================

Application Number: [To be assigned by USPTO]
Attorney Docket Number: {attorney_docket}
Filing Date: {filing_date}
Application Type: Provisional Application for Patent

TITLE OF INVENTION:
==================
{title}

INVENTOR INFORMATION:
====================
"""
        
        for i, inventor in enumerate(inventors, 1):
            cover_sheet += f"""
Inventor {i}: {inventor}
- Residence: [City, State, Country]
- Citizenship: [Country of Citizenship]
"""
        
        cover_sheet += f"""
ASSIGNEE INFORMATION:
====================
Assignee: {assignee}
Address: [Assignee Address]
City, State, ZIP: [City, State, ZIP Code]
Country: [Country]

CORRESPONDENCE INFORMATION:
==========================
Correspondence Address: [Attorney/Agent Address]
City, State, ZIP: [City, State, ZIP Code]
Country: [Country]
Telephone: [Phone Number]
Email: [Email Address]

APPLICATION DETAILS:
===================
Total Number of Pages: {estimated_pages} (estimated)
Number of Drawing Sheets: [Number of drawing sheets, if any]
Number of Claims: {len(validated_data['key_claims'])}
Number of Figures: [Number of figures, if any]

DECLARATION STATEMENTS:
======================

1. ENTITLEMENT TO PRIORITY:
   ☐ This application claims priority to a foreign application
   ☐ This application claims priority to a U.S. application
   ☐ This application claims priority to a PCT application
   ☐ No priority claimed

2. SMALL ENTITY STATUS:
   ☐ Small Entity (qualifying for reduced fees)
   ☐ Micro Entity (qualifying for further reduced fees)
   ☐ Large Entity (standard fees apply)

3. GOVERNMENT INTEREST:
   ☐ This invention was made with Government support
   ☐ No Government support

4. FOREIGN FILING LICENSE:
   ☐ Foreign filing license requested
   ☐ No foreign filing license needed

5. SEQUENCE LISTING:
   ☐ Sequence listing submitted on paper
   ☐ Sequence listing submitted electronically
   ☐ No sequence listing

6. COMPUTER PROGRAM LISTING:
   ☐ Computer program listing submitted on paper
   ☐ Computer program listing submitted electronically
   ☐ No computer program listing

7. BIOLOGICAL MATERIAL:
   ☐ Biological material deposited
   ☐ No biological material deposited

FEES:
=====
Filing Fee (Provisional): $[Fee amount based on entity status]
Total Fees: $[Total fee amount]

PAYMENT METHOD:
===============
☐ Credit Card
☐ Deposit Account
☐ Electronic Funds Transfer
☐ Other: [Specify]

SIGNATURE SECTION:
==================

I hereby declare that:
1. I am the applicant or authorized to file this application
2. I have reviewed the application and believe it to be complete
3. I understand that a provisional application will not be examined
4. I understand that a non-provisional application must be filed within 12 months

Signature: _____________________________
Name: [Signature Name]
Title: [Title]
Date: {filing_date}

NOTARY SECTION (if required):
============================
State of: [State]
County of: [County]

On this [Day] day of [Month], [Year], before me personally appeared [Name], 
who proved to me on the basis of satisfactory evidence to be the person whose 
name is subscribed to the within instrument and acknowledged to me that he/she 
executed the same in his/her authorized capacity, and that by his/her signature 
on the instrument the person, or the entity upon behalf of which the person acted, 
executed the instrument.

Notary Public: _________________________
Commission Expires: [Date]

USPTO COVER SHEET CHECKLIST:
============================
☐ Application title matches specification
☐ All inventors listed with correct information
☐ Assignee information complete (if applicable)
☐ Correspondence address provided
☐ Entity status selected
☐ Appropriate declarations checked
☐ Fees calculated correctly
☐ Payment method selected
☐ Signature and date included
☐ Notary section completed (if required)

IMPORTANT NOTES:
===============
1. This cover sheet must be filed with the provisional application
2. All information must be accurate and complete
3. Fees must be paid at time of filing
4. Provisional applications are not examined
5. Non-provisional application must be filed within 12 months
6. Keep copy of filing receipt for future reference

END OF PROVISIONAL APPLICATION COVER SHEET
"""
        
        return cover_sheet 