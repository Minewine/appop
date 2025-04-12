from flask import Blueprint, render_template, current_app, jsonify, abort, session, request
import os
import json
from datetime import datetime

# Create the blueprint instance
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """Dashboard main page showing report overview"""
    # Get language preference from session
    lang = session.get('lang', 'en')
    
    reports = []
    reports_dir = current_app.config['REPORTS_FOLDER']
    
    # List all report files and extract basic info
    if os.path.exists(reports_dir):
        for filename in os.listdir(reports_dir):
            if filename.endswith('.json'):
                report_path = os.path.join(reports_dir, filename)
                try:
                    with open(report_path, 'r') as f:
                        report_data = json.load(f)
                        report_id = filename.replace('.json', '')
                        reports.append({
                            'id': report_id,
                            'filename': report_data.get('filename', 'Unknown'),
                            'analysis_type': report_data.get('analysis_type', 'Unknown'),
                            'timestamp': report_data.get('timestamp', datetime.now().isoformat())
                        })
                except Exception as e:
                    current_app.logger.error(f"Error reading report {filename}: {e}")
    
    # Sort reports by timestamp, newest first
    reports.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('dashboard/index.html', reports=reports, lang=lang)

@dashboard_bp.route('/report/<report_id>')
def view_report(report_id):
    """View a specific report details"""
    # Get language preference from session
    lang = session.get('lang', 'en')
    
    report_path = os.path.join(current_app.config['REPORTS_FOLDER'], f"{report_id}.json")
    
    if not os.path.exists(report_path):
        abort(404)
        
    with open(report_path, 'r') as f:
        report_data = json.load(f)
        
    return render_template('dashboard/view_report.html', report=report_data, report_id=report_id, lang=lang)

@dashboard_bp.route('/api/reports')
def api_reports():
    """API endpoint to fetch report data for dashboard"""
    reports = []
    reports_dir = current_app.config['REPORTS_FOLDER']
    
    if os.path.exists(reports_dir):
        for filename in os.listdir(reports_dir):
            if filename.endswith('.json'):
                report_path = os.path.join(reports_dir, filename)
                try:
                    with open(report_path, 'r') as f:
                        report_data = json.load(f)
                        report_id = filename.replace('.json', '')
                        reports.append({
                            'id': report_id,
                            'filename': report_data.get('filename', 'Unknown'),
                            'analysis_type': report_data.get('analysis_type', 'Unknown'),
                            'timestamp': report_data.get('timestamp')
                        })
                except Exception:
                    pass
    
    return jsonify(reports)