from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, send_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid
from services.pdf_service import extract_pdf_text
from services.ai_service import query_openrouter
from services.utils import allowed_file, generate_report_id
import io

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Check if both files were uploaded
        if 'resume' not in request.files or 'jobDescription' not in request.files:
            flash('Both resume and job description files are required', 'error')
            return redirect(request.url)
        
        resume_file = request.files['resume']
        job_file = request.files['jobDescription']
        
        # Check if files are selected
        if resume_file.filename == '' or job_file.filename == '':
            flash('Please select both files', 'error')
            return redirect(request.url)
        
        # Check if files have allowed extensions
        if not (allowed_file(resume_file.filename) and allowed_file(job_file.filename)):
            flash('Invalid file format. Please use PDF or DOCX files.', 'error')
            return redirect(request.url)
        
        try:
            # Save resume file
            resume_filename = secure_filename(resume_file.filename)
            resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], resume_filename)
            resume_file.save(resume_path)
            
            # Save job description file
            job_filename = secure_filename(job_file.filename)
            job_path = os.path.join(current_app.config['UPLOAD_FOLDER'], job_filename)
            job_file.save(job_path)
            
            # Extract text from files
            resume_text = extract_pdf_text(resume_path)
            job_text = extract_pdf_text(job_path)
            
            # Generate a unique report ID
            report_id = str(uuid.uuid4())
            
            # Process with AI service to generate analysis
            analysis_result = query_openrouter(resume_text, job_text)
            
            # Create report object
            report = {
                'id': report_id,
                'date': datetime.now().strftime('%d %b %Y, %H:%M'),
                'job_title': 'Software Engineer',  # You would extract this from the job description
                'score': 85,  # This would come from your analysis
                'company': 'Tech Corp',  # You would extract this from the job description
                'stats': {
                    'keyword_match': 80,
                    'skill_match': 85,
                    'experience_match': 90,
                    'education_match': 75
                },
                'sections': {
                    'summary': '<p>Strong match for the position with excellent technical skills.</p>',
                    'keyword_analysis': '<p>Your resume matches 80% of the required keywords.</p>',
                    'skills_gap': '<p>Consider adding experience with Kubernetes.</p>',
                    'ats_compatibility': '<p>Your resume is ATS-friendly.</p>',
                    'recommendations': '<p>Highlight your cloud experience more prominently.</p>',
                    'improved_resume': '<p>See the optimized version of your resume.</p>'
                }
            }
            
            # Store the report in session for retrieval in the report view
            # In a real application, you'd save this to a database instead
            current_app.logger.info(f"Storing report {report_id} in session")
            if 'reports' not in session:
                session['reports'] = {}
            session['reports'][report_id] = report
            session.modified = True
            
            # Redirect to the report view
            return redirect(url_for('analysis.view_report', report_id=report_id))
            
        except Exception as e:
            current_app.logger.error(f"Error processing files: {str(e)}")
            flash(f'Error processing files: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show upload form
    return render_template('upload.html', lang={
        'upload_header': 'Upload Documents for Analysis'
    })

@analysis_bp.route('/report/<report_id>')
def view_report(report_id):
    # In a real application, you would retrieve the report from your database
    # For this example, we're retrieving from session
    reports = session.get('reports', {})
    report = reports.get(report_id)
    
    if not report:
        flash('Report not found', 'error')
        return redirect(url_for('analysis.upload'))
    
    return render_template('report.html', report=report)

@analysis_bp.route('/download_pdf/<report_id>')
def download_pdf(report_id):
    """Generate and download a PDF version of the report"""
    try:
        # Get report data
        reports = session.get('reports', {})
        report = reports.get(report_id)
        
        if not report:
            flash('Report not found', 'error')
            return redirect(url_for('analysis.upload'))
        
        # In a real app, you would generate a PDF here using a library like WeasyPrint, pdfkit, etc.
        # For this demo, we'll just create a simple text file
        
        pdf_content = f"""
        Analysis Report
        ==============
        
        Date: {report['date']}
        Job Title: {report['job_title']}
        Company: {report['company']}
        Overall Score: {report['score']}%
        
        Executive Summary
        ----------------
        {report['sections']['summary']}
        
        Keyword Analysis
        ---------------
        {report['sections']['keyword_analysis']}
        
        Skills Gap Analysis
        -----------------
        {report['sections']['skills_gap']}
        
        ATS Compatibility
        ---------------
        {report['sections']['ats_compatibility']}
        
        Recommendations
        -------------
        {report['sections']['recommendations']}
        """
        
        # Create a BytesIO object for the file
        pdf_io = io.BytesIO()
        pdf_io.write(pdf_content.encode('utf-8'))
        pdf_io.seek(0)
        
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'resume_analysis_report_{report_id}.pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error generating PDF: {str(e)}")
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('analysis.view_report', report_id=report_id))

@analysis_bp.route('/download_improved_resume/<report_id>')
def download_improved_resume(report_id):
    """Download the improved resume"""
    try:
        # Get report data
        reports = session.get('reports', {})
        report = reports.get(report_id)
        
        if not report:
            flash('Report not found', 'error')
            return redirect(url_for('analysis.upload'))
        
        # In a real app, you would generate an improved resume DOCX file
        # For this demo, we'll create a simple text file
        
        resume_content = f"""
        IMPROVED RESUME
        ==============
        
        Based on job: {report['job_title']} at {report['company']}
        
        This is an improved version of your resume with the following enhancements:
        
        1. Added keywords highlighted in the job description
        2. Improved formatting for better ATS compatibility
        3. Emphasized relevant skills and experiences
        4. Addressed the skills gaps mentioned in our analysis
        
        {report['sections']['improved_resume']}
        """
        
        # Create a BytesIO object for the file
        resume_io = io.BytesIO()
        resume_io.write(resume_content.encode('utf-8'))
        resume_io.seek(0)
        
        return send_file(
            resume_io,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=f'improved_resume_{report_id}.docx'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error generating improved resume: {str(e)}")
        flash(f'Error generating improved resume: {str(e)}', 'error')
        return redirect(url_for('analysis.view_report', report_id=report_id))