import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form handling"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if not name or not email or not message:
            return render_template('contact.html', error="Please fill in all fields")
        
        # Send email
        try:
            send_contact_email(name, email, message)
            flash("Your message has been sent successfully!", "success")
            return redirect(url_for('main.landing_page'))  # Updated to use main.landing_page
        except Exception as e:
            current_app.logger.error(f"Email sending failed: {str(e)}")
            return render_template('contact.html', 
                                  error="There was an error sending your message. Please try again later.",
                                  name=name, 
                                  email=email, 
                                  message=message)
    
    return render_template('contact.html')

def send_contact_email(name, email, message):
    """Send contact form email to info@rametric.com"""
    recipient = "info@rametric.com"
    subject = "APPOP REQUEST"
    
    # Create the email
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = recipient
    msg['Subject'] = subject
    
    # Email body
    body = f"""
    New contact form submission from The Metric website:
    
    Name: {name}
    Email: {email}
    
    Message:
    {message}
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Email sending logic
    # For production, configure these settings in your app config
    smtp_server = current_app.config.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = current_app.config.get('SMTP_PORT', 587)
    smtp_username = current_app.config.get('SMTP_USERNAME', 'your-email@gmail.com')
    smtp_password = current_app.config.get('SMTP_PASSWORD', 'your-app-password')
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        raise