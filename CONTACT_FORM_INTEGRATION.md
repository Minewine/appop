# Contact Form Integration Instructions

This document explains how to integrate the new contact form functionality into your existing application.

## Files Created

1. `/templates/contact.html` - The contact form template
2. `/routes/contact.py` - The contact form route handlers

## Integration Steps

### 1. Update your main application file

In your main app initialization file (likely `app.py` or similar), add:

```python
# Import the contact blueprint
from routes.contact import contact_bp

# Register the blueprint with your app
app.register_blueprint(contact_bp, url_prefix='/appop')
```

### 2. Configure Email Settings

Add these configuration parameters to your app configuration:

```python
# Email configuration
app.config['SMTP_SERVER'] = 'your-smtp-server.com'  # e.g., smtp.gmail.com
app.config['SMTP_PORT'] = 587  # Common TLS port
app.config['SMTP_USERNAME'] = 'your-email@example.com'
app.config['SMTP_PASSWORD'] = 'your-email-password'  # Use environment variables for security
```

For Gmail, you'll need to use an App Password if you have 2FA enabled.

### 3. Testing the Contact Form

1. Start your application
2. Visit the landing page
3. Click the "Request More Information" button
4. Fill out and submit the contact form
5. Verify that emails are sent to info@rametric.com

## Troubleshooting

If emails are not being sent:

1. Check your SMTP settings
2. Verify that your email provider allows sending from scripts
3. Look for error logs in your Flask application

For more secure configuration, consider using environment variables for sensitive values:

```python
import os

app.config['SMTP_PASSWORD'] = os.environ.get('EMAIL_PASSWORD')
```