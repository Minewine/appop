"""
Utility functions for the application.
"""
import os
import uuid
import json
from datetime import datetime
from config import Config
from flask import current_app

def allowed_file(filename):
    """
    Check if a filename has an allowed extension
    
    Args:
        filename: The filename to check
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    if not filename:
        return False
        
    # Get the allowed extensions from app config or use default
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf'})
    
    # Check if '.' exists and the extension is allowed
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_report_id():
    """
    Generate a unique ID for a new report
    
    Returns:
        str: A unique identifier (UUID)
    """
    return str(uuid.uuid4())

def save_analysis_report(report_data, report_id=None):
    """Saves an analysis report to a JSON file.

    Args:
        report_data (dict): The report data to save.
        report_id (str, optional): The ID of the report. If None, a new ID is generated.

    Returns:
        str: The ID of the saved report.
    """
    if not report_id:
        report_id = generate_report_id()
    
    # Add metadata
    report_data['report_id'] = report_id
    report_data['timestamp'] = datetime.now().isoformat()
    
    # Create the reports directory if it doesn't exist
    os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)
    
    # Save the report to a JSON file
    report_path = os.path.join(Config.REPORTS_FOLDER, f"{report_id}.json")
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    return report_id

def get_analysis_report(report_id):
    """Retrieves an analysis report from a JSON file.

    Args:
        report_id (str): The ID of the report to retrieve.

    Returns:
        dict: The report data or None if not found.
    """
    report_path = os.path.join(Config.REPORTS_FOLDER, f"{report_id}.json")
    if not os.path.exists(report_path):
        return None
    
    with open(report_path, 'r') as f:
        return json.load(f)

def get_all_reports():
    """Retrieves all analysis reports.

    Returns:
        list: A list of report data dictionaries, sorted by timestamp (newest first).
    """
    reports = []
    
    if not os.path.exists(Config.REPORTS_FOLDER):
        return reports
    
    # Load all JSON files in the reports directory
    for filename in os.listdir(Config.REPORTS_FOLDER):
        if filename.endswith('.json'):
            report_path = os.path.join(Config.REPORTS_FOLDER, filename)
            try:
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
                    reports.append(report_data)
            except Exception as e:
                print(f"Error loading report {filename}: {e}")
    
    # Sort reports by timestamp (newest first)
    reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return reports

def extract_ats_score(analysis_text):
    """Extract the ATS compatibility score from the analysis text.
    
    Args:
        analysis_text (str): The text of the analysis
        
    Returns:
        int or None: The score as an integer (0-100) or None if not found
    """
    import re
    
    # Look for patterns like "Overall ATS Compatibility Score: 75%" or "ATS Compatibility Score: 75/100"
    patterns = [
        r'ATS\s+Compatibility\s+Score:?\s*(\d+)[%\s]',
        r'Compatibility\s+Score:?\s*(\d+)[%\s]',
        r'ATS\s+Score:?\s*(\d+)[%\s]',
        r'Score:?\s*(\d+)[%\s/100]'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            try:
                score = int(match.group(1))
                # Validate score is in range 0-100
                if 0 <= score <= 100:
                    return score
            except ValueError:
                continue
    
    return None

def get_sample_files():
    """Get available sample CV and job description files.
    
    Returns:
        dict: Dictionary with 'cvs' and 'jds' lists containing sample file info
    """
    samples = {
        'cvs': [],
        'jds': []
    }
    
    # Check if samples directory exists
    if not os.path.exists(Config.SAMPLE_FOLDER):
        return samples
    
    # Get CV samples
    cv_dir = os.path.join(Config.SAMPLE_FOLDER, 'cvs')
    if os.path.exists(cv_dir):
        for filename in os.listdir(cv_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(cv_dir, filename)
                samples['cvs'].append({
                    'name': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'description': filename.replace('.pdf', '').replace('_', ' ')
                })
    
    # Get JD samples
    jd_dir = os.path.join(Config.SAMPLE_FOLDER, 'jds')
    if os.path.exists(jd_dir):
        for filename in os.listdir(jd_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(jd_dir, filename)
                samples['jds'].append({
                    'name': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'description': filename.replace('.pdf', '').replace('_', ' ')
                })
    
    return samples