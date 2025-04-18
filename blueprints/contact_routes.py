import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, g

# This is imported into app.py, so we don't need to create the blueprint there
contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form handling"""
    # Get language preference
    lang = request.args.get('lang', session.get('lang', 'en'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Form validation
        if not name or not email or not message:
            error_msg = "Veuillez remplir tous les champs" if lang == 'fr' else "Please fill in all fields"
            return render_template('contact.html', 
                                  error=error_msg,
                                  name=name, 
                                  email=email, 
                                  message=message,
                                  lang=lang)
        
        # For development/demo - log the message but don't try to send email
        current_app.logger.info(f"Contact form submission: Name: {name}, Email: {email}, Message: {message}")
        
        # Store message in a file as fallback
        try:
            store_message_in_file(name, email, message)
        except Exception as e:
            current_app.logger.warning(f"Failed to store message in file: {str(e)}")
            
        # Try to send email
        try:
            send_contact_email(name, email, message)
            success_msg = "Votre message a été envoyé avec succès!" if lang == 'fr' else "Your message has been sent successfully!"
            flash(success_msg, "success")
            return redirect(url_for('main.index'))  # Redirect to landing page
        except Exception as e:
            current_app.logger.error(f"Email sending failed: {str(e)}")
            error_msg = "Une erreur s'est produite lors de l'envoi de votre message. Nous avons enregistré votre demande et vous contacterons bientôt." if lang == 'fr' else "There was an issue sending your email, but we've recorded your request and will contact you soon."
            
            # Even if email fails, show success to user since we stored the message
            flash(error_msg, "warning")
            return redirect(url_for('main.index'))
    
    # GET request - show the contact form
    return render_template('contact.html', lang=lang)

def store_message_in_file(name, email, message):
    """Store the contact message in a text file as backup"""
    import datetime
    import os
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(logs_dir, f"contact_{timestamp}.txt")
    
    with open(filename, 'w') as f:
        f.write(f"APPOP REQUEST\n")
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Name: {name}\n")
        f.write(f"Email: {email}\n\n")
        f.write(f"Message:\n{message}\n")
    
    return True

def send_contact_email(name, email, message):
    """Send contact form email to info@rametric.com"""
    recipient = "info@rametric.com"
    subject = "APPOP REQUEST"
    
    # Create the email
    msg = MIMEMultipart()
    msg['From'] = current_app.config.get('MAIL_DEFAULT_SENDER', email) 
    msg['To'] = recipient
    msg['Subject'] = subject
    msg['Reply-To'] = email  # Ensure replies go to the person who filled the form
    
    # Email body
    body = f"""
    New contact form submission from The Metric website:
    
    Name: {name}
    Email: {email}
    
    Message:
    {message}
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Get email settings from environment or config
    smtp_server = current_app.config.get('SMTP_SERVER', os.environ.get('SMTP_SERVER', 'smtp.gmail.com'))
    smtp_port = int(current_app.config.get('SMTP_PORT', os.environ.get('SMTP_PORT', 587)))
    smtp_username = current_app.config.get('SMTP_USERNAME', os.environ.get('SMTP_USERNAME', ''))
    smtp_password = current_app.config.get('SMTP_PASSWORD', os.environ.get('SMTP_PASSWORD', ''))
    
    # Log email attempt (without password)
    current_app.logger.info(f"Attempting to send email via {smtp_server}:{smtp_port} with username {smtp_username}")
    
    # Check if we have the required credentials
    if not smtp_username or not smtp_password:
        current_app.logger.warning("Missing SMTP credentials, email cannot be sent")
        raise ValueError("Missing email configuration")
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()  # Can help with some SMTP servers
        server.starttls()
        server.ehlo()  # Some servers need EHLO again after TLS
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        current_app.logger.info("Email sent successfully")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {str(e)}")
        raise