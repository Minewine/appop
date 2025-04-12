from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
from services.pdf_service import extract_pdf_text
from services.ai_service import query_openrouter, analyze_cv_with_jd
from services.utils import allowed_file, generate_report_id
from blueprints.auth import add_report_to_user

# Create the blueprint instance
analysis_bp = Blueprint('analysis', __name__)

# Authentication check decorator
def login_required(view_func):
    def wrapped_view(*args, **kwargs):
        if 'user_email' not in session:
            # Store the requested URL in the session for redirection after login
            session['next'] = request.url
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('auth.login', next=request.url, lang=session.get('lang', 'en')))
        return view_func(*args, **kwargs)
    # Preserve the original function's name and docstring
    wrapped_view.__name__ = view_func.__name__
    wrapped_view.__doc__ = view_func.__doc__
    return wrapped_view

@analysis_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle file uploads and start analysis"""
    # Get language preference from query param or session
    lang = request.args.get('lang', session.get('lang', 'en'))
    # Store language preference in session
    session['lang'] = lang
    
    if request.method == 'POST':
        # Debug log
        current_app.logger.info("Processing upload form submission")
        current_app.logger.info(f"Files in request: {list(request.files.keys())}")
        
        # Check if CV file is uploaded
        if 'cv_file' not in request.files:
            flash('Please upload your CV/Resume', 'error')
            return redirect(request.url)
            
        cv_file = request.files['cv_file']
        
        # Check if CV filename is empty
        if cv_file.filename == '':
            flash('No CV/Resume file selected', 'error')
            return redirect(request.url)
        
        # Validate CV file
        if not allowed_file(cv_file.filename):
            flash('Please upload your CV in PDF format', 'error')
            return redirect(request.url)
            
        try:
            # Generate report ID
            report_id = generate_report_id()
            
            # Create uploads directory if it doesn't exist
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Process CV file
            cv_filename = secure_filename(cv_file.filename)
            cv_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], f"cv_{report_id}_{cv_filename}")
            cv_file.save(cv_filepath)
            
            # Extract text from CV
            current_app.logger.info(f"Extracting text from CV: {cv_filepath}")
            cv_text = extract_pdf_text(cv_filepath)
            
            if not cv_text or len(cv_text) < 10:
                current_app.logger.error(f"Failed to extract text from CV or CV is too short")
                flash('Could not extract text from your CV. Please ensure it is a valid PDF with text content.', 'error')
                return redirect(request.url)
            
            current_app.logger.info(f"Successfully extracted {len(cv_text)} characters from CV")
            
            # Get job description from file or text input
            jd_text = ""
            jd_filename = ""
            
            if 'jd_file' in request.files and request.files['jd_file'].filename != '':
                jd_file = request.files['jd_file']
                jd_filename = secure_filename(jd_file.filename)
                jd_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], f"jd_{report_id}_{jd_filename}")
                jd_file.save(jd_filepath)
                jd_text = extract_pdf_text(jd_filepath)
            elif 'jd_text' in request.form and request.form['jd_text'].strip():
                jd_text = request.form['jd_text'].strip()
                jd_filename = "manual_entry.txt"
            
            # Store data in session
            session['cv_text'] = cv_text
            session['cv_filename'] = cv_filename
            session['report_id'] = report_id
            
            if jd_text:
                session['jd_text'] = jd_text
                session['jd_filename'] = jd_filename
                
                # Log successful upload with both CV and JD
                current_app.logger.info(f"Successfully uploaded CV and JD. Report ID: {report_id}")
                flash('Files uploaded successfully! Analyzing CV-Job match.', 'success')
                return redirect(url_for('analysis.analyze', report_id=report_id, analysis_type='cv_jd_match'))
            else:
                # Log successful upload with CV only
                current_app.logger.info(f"Successfully uploaded CV only. Report ID: {report_id}")
                flash('CV uploaded successfully! Performing basic CV analysis.', 'success')
                return redirect(url_for('analysis.analyze', report_id=report_id, analysis_type='cv_only'))
                
        except Exception as e:
            current_app.logger.error(f"Error processing upload: {str(e)}")
            flash(f"An error occurred during file processing: {str(e)}", 'error')
            return redirect(request.url)
    
    return render_template('upload.html', lang=lang)

@analysis_bp.route('/analyze/<report_id>', methods=['GET', 'POST'])
@login_required
def analyze(report_id):
    """Process the uploaded files and show analysis options or results"""
    # Get language preference from session
    lang = session.get('lang', 'en')
    
    # Check if necessary data is in session
    if 'cv_text' not in session or not session.get('cv_text'):
        flash('No CV content found. Please upload your CV again.', 'warning')
        return redirect(url_for('analysis.upload', lang=lang))
    
    # For GET requests, immediately process the analysis without showing the form
    # Retrieve session data
    cv_text = session.get('cv_text', '')
    cv_filename = session.get('cv_filename', 'document.pdf')
    jd_text = session.get('jd_text', '')
    jd_filename = session.get('jd_filename', '')
    
    # Determine analysis type
    analysis_type = request.args.get('analysis_type', 'cv_only')
    if request.method == 'POST':
        analysis_type = request.form.get('analysis_type', 'cv_only')
    
    # Log analysis attempt
    current_app.logger.info(f"Starting analysis for report_id: {report_id}, type: {analysis_type}")
    current_app.logger.info(f"CV: {cv_filename} ({len(cv_text)} chars)")
    if jd_text:
        current_app.logger.info(f"JD: {jd_filename} ({len(jd_text)} chars)")
    
    try:
        # Perform analysis based on type
        if analysis_type == 'cv_only' or not jd_text:
            # Basic CV analysis when no job description available
            result = query_openrouter(cv_text, "ats_cv_analysis", lang)
        else:
            # CV-JD match analysis
            result = analyze_cv_with_jd(cv_text, jd_text, lang)
        
        if not result or "Error:" in result:
            raise Exception(f"Analysis failed: {result}")
        
        # Save results to file
        os.makedirs(current_app.config['REPORTS_FOLDER'], exist_ok=True)
        report_path = os.path.join(current_app.config['REPORTS_FOLDER'], f"{report_id}.json")
        report_data = {
            'cv_filename': cv_filename,
            'jd_filename': jd_filename if jd_text else None,
            'analysis_type': analysis_type,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f)
        
        current_app.logger.info(f"Analysis complete and saved to {report_path}")
        
        # Add report to user's profile if logged in
        if 'user_email' in session:
            add_report_to_user(session['user_email'], report_id)
            current_app.logger.info(f"Report {report_id} saved to user profile: {session['user_email']}")
        
        # Redirect to report page
        return redirect(url_for('analysis.report', report_id=report_id))
        
    except Exception as e:
        current_app.logger.error(f"Analysis error: {str(e)}")
        flash(f"An error occurred during analysis: {str(e)}", 'error')
        return redirect(url_for('analysis.upload', lang=lang))
    
    # This line should only be reached if something unexpected happens
    # But we'll render the loading/processing page just in case
    return render_template('analyze.html', report_id=report_id, lang=lang)

@analysis_bp.route('/report/<report_id>')
@login_required
def report(report_id):
    """Display the analysis report"""
    # Get language preference from session
    lang = session.get('lang', 'en')
    
    report_path = os.path.join(current_app.config['REPORTS_FOLDER'], f"{report_id}.json")
    
    if not os.path.exists(report_path):
        flash('Report not found', 'error')
        return redirect(url_for('main.index'))
        
    with open(report_path, 'r') as f:
        report_data = json.load(f)
    
    # Create a simple template for now, later you can make it more sophisticated
    return render_template('report.html', report=report_data, lang=lang)

@analysis_bp.route('/process', methods=['POST'])
@login_required
def process():
    """Handle direct processing of CV and job description"""
    # Get language preference
    lang = request.form.get('lang', 'en')
    
    # Check if CV file is uploaded
    if 'cv_file' not in request.files:
        flash('Please upload your CV/Resume', 'error')
        return redirect(url_for('analysis.upload', lang=lang))
        
    cv_file = request.files['cv_file']
    
    # Check if CV filename is empty
    if cv_file.filename == '':
        flash('No CV/Resume file selected', 'error')
        return redirect(url_for('analysis.upload', lang=lang))
    
    # Validate CV file
    if not allowed_file(cv_file.filename):
        flash('Please upload your CV in PDF format', 'error')
        return redirect(url_for('analysis.upload', lang=lang))
        
    try:
        # Generate report ID
        report_id = generate_report_id()
        current_app.logger.info(f"Processing files for report ID: {report_id}")
        
        # Create uploads directory if it doesn't exist
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Process CV file
        cv_filename = secure_filename(cv_file.filename)
        cv_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], f"cv_{report_id}_{cv_filename}")
        cv_file.save(cv_filepath)
        
        # Extract text from CV
        cv_text = extract_pdf_text(cv_filepath)
        
        if not cv_text or len(cv_text) < 10:
            current_app.logger.error(f"Failed to extract text from CV or CV is too short")
            flash('Could not extract text from your CV. Please ensure it is a valid PDF with text content.', 'error')
            return redirect(url_for('analysis.upload', lang=lang))
            
        current_app.logger.info(f"Extracted {len(cv_text)} chars from CV: {cv_filename}")
        
        # Get job description from file or text input
        jd_text = ""
        jd_filename = ""
        
        if 'jd_file' in request.files and request.files['jd_file'].filename != '':
            jd_file = request.files['jd_file']
            jd_filename = secure_filename(jd_file.filename)
            jd_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], f"jd_{report_id}_{jd_filename}")
            jd_file.save(jd_filepath)
            jd_text = extract_pdf_text(jd_filepath)
            current_app.logger.info(f"Extracted {len(jd_text)} chars from JD: {jd_filename}")
        elif 'jd_text' in request.form and request.form['jd_text'].strip():
            jd_text = request.form['jd_text'].strip()
            jd_filename = "manual_entry.txt"
            current_app.logger.info(f"Received {len(jd_text)} chars of JD text from form")
        
        # Determine analysis type based on inputs
        analysis_type = 'cv_jd_match' if jd_text else 'cv_only'
        
        # Perform analysis immediately
        current_app.logger.info(f"Starting {analysis_type} analysis...")
        
        if analysis_type == 'cv_only':
            result = query_openrouter(cv_text, "ats_cv_analysis", lang)
        else:
            result = analyze_cv_with_jd(cv_text, jd_text, lang)
            
        if not result or "Error:" in result:
            raise Exception(f"Analysis failed: {result}")
        
        # Save results to file
        os.makedirs(current_app.config['REPORTS_FOLDER'], exist_ok=True)
        report_path = os.path.join(current_app.config['REPORTS_FOLDER'], f"{report_id}.json")
        report_data = {
            'cv_filename': cv_filename,
            'jd_filename': jd_filename if jd_text else None,
            'analysis_type': analysis_type,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f)
        
        current_app.logger.info(f"Analysis completed and saved to {report_path}")
        
        # Add report to user's profile
        if 'user_email' in session:
            add_report_to_user(session['user_email'], report_id)
            current_app.logger.info(f"Report {report_id} saved to user profile: {session['user_email']}")
        
        # Return success and redirect to report
        flash('Analysis complete!', 'success')
        return redirect(url_for('analysis.report', report_id=report_id))
        
    except Exception as e:
        current_app.logger.error(f"Process error: {str(e)}")
        flash(f"An error occurred during processing: {str(e)}", 'error')
        return redirect(url_for('analysis.upload', lang=lang))