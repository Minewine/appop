"""
PDF service module for extracting text from PDF files.
"""
import os
import fitz  # PyMuPDF
import re
from flask import current_app

def extract_pdf_text(filepath, preserve_layout=True):
    """
    Extract text from a PDF file using PyMuPDF (fitz)
    
    Args:
        filepath: Path to the PDF file
        preserve_layout: Whether to attempt to preserve document layout
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            current_app.logger.error(f"PDF file not found: {filepath}")
            return ""
            
        current_app.logger.info(f"Opening PDF file: {filepath}")
        
        # Open the PDF
        doc = fitz.open(filepath)
        
        # Extract text from each page
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            
            if preserve_layout:
                # Extract text with layout preservation (better for CVs and structured documents)
                page_text = page.get_text("dict")
                blocks = page_text.get("blocks", [])
                
                # Process each block of text
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            if "spans" in line:
                                for span in line["spans"]:
                                    text += span.get("text", "") + " "
                            text += "\n"  # Line break after each line
                    text += "\n"  # Extra line break between blocks for better separation
            else:
                # Simple text extraction
                page_text = page.get_text()
                text += page_text
            
        # Log text extraction metrics
        current_app.logger.info(f"Extracted {len(text)} characters from {len(doc)} pages")
        
        # Basic validation - check if we actually got text
        if not text or len(text) < 10:
            current_app.logger.warning(f"Very little text extracted from PDF: {len(text)} chars")
            
        return text
        
    except Exception as e:
        current_app.logger.error(f"Error extracting text from PDF: {e}")
        return f"Error extracting text: {str(e)}"
    finally:
        # Close the document
        if 'doc' in locals():
            doc.close()

def extract_cv_sections(cv_text):
    """Attempts to identify and extract common sections from a CV.
    
    Args:
        cv_text (str): The full text of the CV
        
    Returns:
        dict: A dictionary with key section titles and their content
    """
    sections = {}
    
    # Common section titles in CVs - expanded with more variations
    section_patterns = {
        'summary': r'(?:professional\s+)?summary|profile|objective|about\s+me|personal\s+statement',
        'experience': r'(?:work|professional|career)\s+experience|employment(?:\s+history)?|work\s+history',
        'education': r'education(?:al)?\s+(?:background|history|qualifications)?',
        'skills': r'(?:technical|key|core)?\s*skills|competencies|expertise|proficiencies',
        'projects': r'projects|portfolio|key\s+achievements',
        'certifications': r'certifications?|accreditations?|licenses|qualifications',
        'languages': r'languages?|language\s+proficiency',
        'references': r'references|testimonials',
        'publications': r'publications|papers|research|articles',
        'awards': r'awards|honors|achievements|recognition',
        'volunteer': r'volunteer(?:ing)?|community\s+service',
        'interests': r'interests|hobbies|activities',
        'personal': r'personal\s+details|personal\s+information'
    }
    
    # Convert the text to lowercase for case-insensitive matching but preserve original
    lower_text = cv_text.lower()
    
    # Find the positions of each section header with improved regex
    section_positions = {}
    for section_name, pattern in section_patterns.items():
        # Look for section headers with common formatting patterns
        # This handles headers that might be followed by colon, all caps, underlined with dashes, etc.
        matches = re.finditer(r'(?:^|\n)(?:[^a-z\n]*)?(?:\s*)(' + pattern + r')(?:\s*:|\s*\n|$)', lower_text, re.IGNORECASE)
        for match in matches:
            section_positions[match.start()] = (section_name, match)
    
    # Sort the positions to maintain the order in the document
    positions = sorted(section_positions.keys())
    
    # Extract each section's content
    for i, pos in enumerate(positions):
        section_name, match = section_positions[pos]
        
        # Get the actual header from the original text to preserve case
        header_start = match.start()
        header_end = match.end()
        actual_header = cv_text[header_start:header_end].strip()
        
        # Find the actual content start (after the header)
        start = match.end()
        
        # Determine the end position (either the start of the next section or end of text)
        if i < len(positions) - 1:
            end = positions[i + 1]
        else:
            end = len(lower_text)
        
        # Extract the section text from the original text (preserving case)
        section_text = cv_text[start:end].strip()
        
        # Store both the original header and content
        sections[section_name] = {
            'header': actual_header,
            'content': section_text
        }
    
    return sections

def extract_cv_metrics(cv_text):
    """Extract basic metrics from a CV.
    
    Args:
        cv_text (str): The full text of the CV
        
    Returns:
        dict: A dictionary with various metrics
    """
    metrics = {
        'word_count': len(cv_text.split()),
        'character_count': len(cv_text),
        'sentence_count': len(re.findall(r'[.!?]+', cv_text)),
        'section_count': 0,
    }
    
    # Count potential sections based on common section patterns
    section_patterns = [
        r'summary|profile|objective',
        r'experience|employment',
        r'education',
        r'skills|competencies',
        r'projects|portfolio',
        r'certifications',
        r'languages',
        r'references'
    ]
    
    for pattern in section_patterns:
        if re.search(r'\b' + pattern + r'\b', cv_text.lower()):
            metrics['section_count'] += 1
    
    return metrics

def extract_jd_requirements(jd_text):
    """Extract potential requirements from a job description.
    
    Args:
        jd_text (str): The full text of the job description
        
    Returns:
        dict: A dictionary with categorized requirements
    """
    requirements = {
        'required_skills': [],
        'preferred_skills': [],
        'experience': [],
        'education': [],
        'responsibilities': [],
        'other': []
    }
    
    # Common section indicators in job descriptions
    section_indicators = {
        'required_skills': r'required(?:\s+skills)?|requirements|qualifications|you\s+(?:should|must)\s+have',
        'preferred_skills': r'preferred(?:\s+skills)?|nice\s+to\s+have|desirable|plus|bonus',
        'experience': r'experience|background|history',
        'education': r'education|degree|academic|qualification',
        'responsibilities': r'responsibilities|duties|you\s+will|role|job\s+description|position\s+description|what\s+you\'ll\s+do'
    }
    
    # Find sections in text
    lower_text = jd_text.lower()
    found_sections = {}
    
    for category, pattern in section_indicators.items():
        matches = re.finditer(r'(?:^|\n)\s*(' + pattern + r')(?:\s*:|\s*\n)', lower_text)
        for match in matches:
            found_sections[match.start()] = (category, match)
    
    # Sort sections by position
    positions = sorted(found_sections.keys())
    
    # Extract content from each section
    for i, pos in enumerate(positions):
        category, match = found_sections[pos]
        start = match.end()
        
        if i < len(positions) - 1:
            end = positions[i + 1]
        else:
            end = len(jd_text)
        
        section_text = jd_text[start:end].strip()
        
        # Look for bullet points or numbered items
        items = re.findall(r'(?:^|\n)(?:\s*[\•\-\*\★\✓\➢\+\d+\.]+\s*)([^\n]+)', section_text)
        
        if items:
            requirements[category].extend([item.strip() for item in items if len(item.strip()) > 5])
        else:
            # If no bullet points, split by sentences and find relevant ones
            sentences = re.split(r'(?<=[.!?])\s+', section_text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10 and not sentence.endswith(':'):
                    requirements[category].append(sentence)
    
    # If we couldn't find structured sections, try a more general approach
    if all(len(items) == 0 for items in requirements.values()):
        general_items = re.findall(r'(?:^|\n)(?:\s*[\•\-\*\★\✓\➢\+\d+\.]+\s*)([^\n]+)', jd_text)
        
        for item in general_items:
            item = item.strip()
            if len(item) < 10:
                continue
                
            # Categorize based on keywords
            item_lower = item.lower()
            
            if any(term in item_lower for term in ["degree", "education", "diploma", "bachelor", "master", "phd"]):
                requirements['education'].append(item)
            elif any(term in item_lower for term in ["experience", "years of", "worked with", "background in"]):
                requirements['experience'].append(item)
            elif any(term in item_lower for term in ["preferred", "nice to have", "plus", "ideally"]):
                requirements['preferred_skills'].append(item)
            elif any(term in item_lower for term in ["responsible", "duties", "will", "task"]):
                requirements['responsibilities'].append(item)
            else:
                requirements['required_skills'].append(item)
    
    # Clean and deduplicate
    for category in requirements:
        requirements[category] = list(dict.fromkeys([r.strip() for r in requirements[category] if len(r.strip()) > 5]))
    
    return requirements

def detect_document_type(text):
    """
    Attempts to detect if a document is a CV/resume or a job description
    
    Args:
        text: Text content of the document
        
    Returns:
        str: 'cv', 'job_description', or 'unknown'
    """
    text_lower = text.lower()
    
    # CV/Resume indicators
    cv_indicators = [
        r'\b(?:curriculum\s+vitae|resume|cv)\b',
        r'\b(?:work\s+experience|employment\s+history|professional\s+experience)\b',
        r'\b(?:education|qualifications|academic\s+background)\b',
        r'\b(?:skills|competencies|expertise)\b',
        r'\b(?:references|referees)\b',
        r'\b(?:personal\s+details|personal\s+information)\b',
        r'\bemail\b.{0,20}@',  # Looks for email addresses
        r'\b(?:phone|tel|mobile)\b.{0,20}\d{3,}',  # Looks for phone numbers
    ]
    
    # Job description indicators
    jd_indicators = [
        r'\b(?:job\s+description|position\s+description|role\s+description)\b',
        r'\b(?:we\s+are\s+looking\s+for|we\s+seek|seeking\s+a)\b',
        r'\b(?:responsibilities|duties|you\s+will\s+be\s+responsible)\b',
        r'\b(?:qualifications|requirements|the\s+ideal\s+candidate)\b',
        r'\b(?:we\s+offer|benefits|package|salary)\b',
        r'\b(?:apply|application|to\s+apply|send\s+your)\b',
        r'\b(?:company|organization|firm)\s+(?:is|are|description|overview)\b',
        r'\b(?:position|opportunity|opening|vacancy)\b',
    ]
    
    # Count matches for each type
    cv_score = sum(1 for pattern in cv_indicators if re.search(pattern, text_lower))
    jd_score = sum(1 for pattern in jd_indicators if re.search(pattern, text_lower))
    
    # Normalize scores (percentage of indicators matched)
    cv_score_norm = cv_score / len(cv_indicators)
    jd_score_norm = jd_score / len(jd_indicators)
    
    # Decision logic based on scores
    if cv_score_norm > 0.3 and cv_score_norm > jd_score_norm:
        return 'cv'
    elif jd_score_norm > 0.3 and jd_score_norm > cv_score_norm:
        return 'job_description'
    else:
        return 'unknown'