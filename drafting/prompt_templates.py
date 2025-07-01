"""
Legal Document Drafting - Prompt Templates and Document Templates
This module contains all the prompts and document templates for legal document drafting.
"""

import yaml
from typing import Dict, List, Any

# NDA Template Questions - these will be asked to gather information
NDA_QUESTIONS = {
    "disclosing_party": {
        "question": "Who is the Disclosing Party (the party sharing confidential information)?",
        "type": "text",
        "required": True,
        "examples": ["ABC Corporation", "John Smith", "XYZ LLC"]
    },
    "receiving_party": {
        "question": "Who is the Receiving Party (the party receiving confidential information)?",
        "type": "text", 
        "required": True,
        "examples": ["DEF Inc.", "Jane Doe", "123 Consulting LLC"]
    },
    "purpose": {
        "question": "What is the purpose of sharing this confidential information?",
        "type": "text",
        "required": True,
        "examples": ["Potential business partnership", "Employment discussions", "Investment evaluation"]
    },
    "duration": {
        "question": "How long should this NDA remain in effect?",
        "type": "text",
        "required": True,
        "examples": ["2 years", "5 years", "Indefinitely", "Until project completion"]
    },
    "jurisdiction": {
        "question": "Which jurisdiction/state law should govern this agreement?",
        "type": "text",
        "required": True,
        "examples": ["California", "New York", "Ontario, Canada", "Texas"]
    },
    "disclosing_party_address": {
        "question": "What is the full address of the Disclosing Party?",
        "type": "text",
        "required": False,
        "examples": ["123 Main St, City, State, ZIP", "456 Business Ave, Suite 100, City, State, ZIP"]
    },
    "receiving_party_address": {
        "question": "What is the full address of the Receiving Party?",
        "type": "text",
        "required": False,
        "examples": ["789 Oak St, City, State, ZIP", "321 Corporate Blvd, City, State, ZIP"]
    },
    "specific_exclusions": {
        "question": "Are there any specific types of information that should be excluded from confidentiality? (Optional)",
        "type": "text",
        "required": False,
        "examples": ["Publicly available information", "Information already known", "Information independently developed"]
    }
}

# Contract Template Questions
CONTRACT_QUESTIONS = {
    "party_1": {
        "question": "Who is the first party to this contract?",
        "type": "text",
        "required": True,
        "examples": ["ABC Company", "John Smith"]
    },
    "party_2": {
        "question": "Who is the second party to this contract?",
        "type": "text",
        "required": True,
        "examples": ["XYZ Corporation", "Jane Doe"]
    },
    "contract_type": {
        "question": "What type of contract is this?",
        "type": "text",
        "required": True,
        "examples": ["Service Agreement", "Employment Contract", "Sales Agreement"]
    },
    "services_or_goods": {
        "question": "What services or goods are being provided?",
        "type": "text",
        "required": True,
        "examples": ["Web development services", "Consulting services", "Software licensing"]
    },
    "payment_terms": {
        "question": "What are the payment terms?",
        "type": "text",
        "required": True,
        "examples": ["$5,000 upon completion", "Monthly payments of $1,000", "50% upfront, 50% on delivery"]
    },
    "duration": {
        "question": "What is the duration or term of this contract?",
        "type": "text",
        "required": True,
        "examples": ["6 months", "1 year", "Until project completion"]
    },
    "jurisdiction": {
        "question": "Which jurisdiction should govern this contract?",
        "type": "text",
        "required": True,
        "examples": ["California", "New York", "Ontario, Canada"]
    }
}

# Lease Agreement Questions
LEASE_QUESTIONS = {
    "landlord": {
        "question": "Who is the landlord?",
        "type": "text",
        "required": True,
        "examples": ["Property Management LLC", "John Smith"]
    },
    "tenant": {
        "question": "Who is the tenant?",
        "type": "text",
        "required": True,
        "examples": ["Jane Doe", "ABC Corporation"]
    },
    "property_address": {
        "question": "What is the full address of the property being leased?",
        "type": "text",
        "required": True,
        "examples": ["123 Main St, Apt 4B, City, State, ZIP"]
    },
    "monthly_rent": {
        "question": "What is the monthly rent amount?",
        "type": "text",
        "required": True,
        "examples": ["$1,500", "$2,000", "$850"]
    },
    "lease_term": {
        "question": "What is the lease term?",
        "type": "text",
        "required": True,
        "examples": ["12 months", "6 months", "Month-to-month"]
    },
    "security_deposit": {
        "question": "What is the security deposit amount?",
        "type": "text",
        "required": True,
        "examples": ["$1,500", "One month's rent", "$500"]
    },
    "start_date": {
        "question": "When does the lease start?",
        "type": "text",
        "required": True,
        "examples": ["January 1, 2025", "February 15, 2025"]
    }
}

# Document type to questions mapping
DOCUMENT_QUESTIONS = {
    "nda": NDA_QUESTIONS,
    "non-disclosure agreement": NDA_QUESTIONS,
    "contract": CONTRACT_QUESTIONS,
    "service agreement": CONTRACT_QUESTIONS,
    "lease": LEASE_QUESTIONS,
    "lease agreement": LEASE_QUESTIONS,
    "rental agreement": LEASE_QUESTIONS
}

# Base NDA Template
NDA_TEMPLATE = """
NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement ("Agreement") is entered into on {date} between {disclosing_party}{disclosing_party_address_formatted} ("Disclosing Party") and {receiving_party}{receiving_party_address_formatted} ("Receiving Party").

WHEREAS, the Disclosing Party possesses certain confidential and proprietary information; and

WHEREAS, the Receiving Party desires to review, examine, inspect or obtain access to such confidential information for the purpose of {purpose};

NOW, THEREFORE, in consideration of the mutual covenants and agreements contained herein, the parties agree as follows:

1. DEFINITION OF CONFIDENTIAL INFORMATION
For purposes of this Agreement, "Confidential Information" shall mean all non-public, confidential or proprietary information of Disclosing Party, whether oral or written, whether or not marked, designated or otherwise identified as "confidential," including without limitation: technical data, trade secrets, know-how, research, product plans, products, services, customers, customer lists, markets, software, developments, inventions, processes, formulas, technology, designs, drawings, engineering, hardware configuration information, marketing, finances or other business information.

2. NON-DISCLOSURE
Receiving Party agrees to:
a) Hold and maintain the Confidential Information in strict confidence;
b) Not disclose the Confidential Information to any third parties without prior written consent of Disclosing Party;
c) Not use the Confidential Information for any purpose other than {purpose};
d) Take reasonable precautions to protect the confidentiality of such information.

3. EXCLUSIONS
The obligations of confidentiality shall not apply to information that:
a) Is or becomes publicly available through no breach of this Agreement by Receiving Party;
b) Is rightfully known by Receiving Party prior to disclosure;
c) Is rightfully received by Receiving Party from a third party without breach of confidentiality;
d) Is independently developed by Receiving Party without use of Confidential Information.

{specific_exclusions_formatted}

4. TERM
This Agreement shall remain in effect for {duration} from the date first written above, unless terminated earlier by mutual written consent of the parties.

5. RETURN OF MATERIALS
Upon termination of this Agreement or upon request by Disclosing Party, Receiving Party shall promptly return or destroy all documents, materials, and other tangible manifestations of Confidential Information.

6. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with the laws of {jurisdiction}.

7. ENTIRE AGREEMENT
This Agreement constitutes the entire agreement between the parties and supersedes all prior negotiations, representations, or agreements relating to the subject matter hereof.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

DISCLOSING PARTY:                    RECEIVING PARTY:

_________________________           _________________________
{disclosing_party}                   {receiving_party}

Date: _______________               Date: _______________
"""

# Basic Contract Template
CONTRACT_TEMPLATE = """
{contract_type}

This {contract_type} ("Agreement") is entered into on {date} between {party_1} ("Party 1") and {party_2} ("Party 2").

WHEREAS, Party 1 desires to engage Party 2 for {services_or_goods}; and

WHEREAS, Party 2 agrees to provide such {services_or_goods} under the terms and conditions set forth herein;

NOW, THEREFORE, in consideration of the mutual covenants contained herein, the parties agree as follows:

1. SCOPE OF WORK
Party 2 shall provide {services_or_goods} as detailed in this Agreement.

2. PAYMENT TERMS
In consideration for the services/goods provided, Party 1 agrees to pay {payment_terms}.

3. TERM
This Agreement shall commence on {date} and shall continue for {duration}, unless terminated earlier in accordance with the provisions herein.

4. TERMINATION
Either party may terminate this Agreement with thirty (30) days written notice to the other party.

5. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with the laws of {jurisdiction}.

6. ENTIRE AGREEMENT
This Agreement constitutes the entire agreement between the parties and supersedes all prior negotiations, representations, or agreements.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.

PARTY 1:                           PARTY 2:

_________________________         _________________________
{party_1}                         {party_2}

Date: _______________             Date: _______________
"""

# Lease Agreement Template
LEASE_TEMPLATE = """
RESIDENTIAL LEASE AGREEMENT

This Lease Agreement ("Lease") is entered into on {date} between {landlord} ("Landlord") and {tenant} ("Tenant").

PROPERTY: The Landlord hereby leases to Tenant the following described property: {property_address} ("Premises").

TERMS:

1. LEASE TERM
This lease shall commence on {start_date} and continue for {lease_term}.

2. RENT
Tenant agrees to pay rent in the amount of {monthly_rent} per month, due on the first day of each month.

3. SECURITY DEPOSIT
Tenant has deposited with Landlord the sum of {security_deposit} as a security deposit.

4. USE OF PREMISES
The Premises shall be used and occupied by Tenant exclusively as a residential dwelling.

5. MAINTENANCE AND REPAIRS
Tenant shall maintain the Premises in good condition and shall be responsible for minor repairs and maintenance.

6. GOVERNING LAW
This Lease shall be governed by the laws of the jurisdiction where the property is located.

7. ENTIRE AGREEMENT
This Lease constitutes the entire agreement between the parties.

IN WITNESS WHEREOF, the parties have executed this Lease as of the date first written above.

LANDLORD:                          TENANT:

_________________________         _________________________
{landlord}                        {tenant}

Date: _______________             Date: _______________
"""

# Document templates mapping
DOCUMENT_TEMPLATES = {
    "nda": NDA_TEMPLATE,
    "non-disclosure agreement": NDA_TEMPLATE,
    "contract": CONTRACT_TEMPLATE,
    "service agreement": CONTRACT_TEMPLATE,
    "lease": LEASE_TEMPLATE,
    "lease agreement": LEASE_TEMPLATE,
    "rental agreement": LEASE_TEMPLATE
}

# System prompts for the AI
SYSTEM_PROMPT = """You are a professional legal document drafting assistant. Your role is to help users create legal documents by:

1. Understanding what type of document they need
2. Asking relevant questions to gather necessary information
3. Generating complete, professional legal documents

Always maintain a professional, helpful tone. Ask one question at a time to avoid overwhelming the user. Be thorough but efficient in gathering information."""

DOCUMENT_IDENTIFICATION_PROMPT = """
Match the user's request as closely as possible based on phrasing, context, or keywords. If uncertain, respond with:
‘Just to clarify, could you tell me the type of legal document you want to create? For example, an NDA, Employment Agreement, or something else?’
Examples:
- “Can you help me draft a contract between my startup and a freelancer?” → Type: Contract/Service Agreement
- “I need a document to make sure someone keeps our app idea confidential” → Type: NDA
- “I want to rent out my property and need something legally binding” → Type: Lease Agreement
- “I’m hiring my first employee and need paperwork” → Type: Employment Agreement”


User request: {user_input}

Respond with just the document type in lowercase (e.g., "nda", "contract", "lease")."""

QUESTION_GENERATION_PROMPT = """You are helping draft a {document_type}. Based on the conversation so far and the required information, generate the next most important question to ask the user.

Already collected information: {collected_info}

Required information still needed: {missing_info}

Generate a single, clear question to ask the user. Be conversational and professional. AND USE today's date in the question."""

DOCUMENT_GENERATION_PROMPT = """Generate a complete {document_type} using the following information:

{collected_info}

Use the provided template and fill in all the necessary details. Ensure the document is professional, legally sound, and properly formatted. Add today's date where {date} appears in the template."""

def get_questions_for_document(document_type: str) -> Dict[str, Any]:
    """Get the questions dictionary for a specific document type."""
    return DOCUMENT_QUESTIONS.get(document_type.lower(), {})

def get_template_for_document(document_type: str) -> str:
    """Get the template for a specific document type."""
    return DOCUMENT_TEMPLATES.get(document_type.lower(), "")

def get_missing_required_fields(document_type: str, collected_info: Dict[str, Any]) -> List[str]:
    """Get list of required fields that are still missing."""
    questions = get_questions_for_document(document_type)
    missing = []
    for field, config in questions.items():
        if config.get("required", False) and field not in collected_info:
            missing.append(field)
    return missing

def format_collected_info_for_display(collected_info: Dict[str, Any]) -> str:
    """Format collected information for display in prompts."""
    if not collected_info:
        return "None"
    
    formatted = []
    for key, value in collected_info.items():
        formatted.append(f"- {key.replace('_', ' ').title()}: {value}")
    return "\n".join(formatted)