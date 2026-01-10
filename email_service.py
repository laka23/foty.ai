# email_service.py - COMPLETE FIXED VERSION

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ==================== EMAIL CONFIGURATION ====================
EMAIL_CONFIG = {
    'smtp_server': 'smtp.eorient.shop',
    'smtp_port': 587,  
    'sender_email': 'foty.ai@eorient.shop',
    'sender_password': '5jtbId7yLmbW',  
    'sender_name': 'FOTY.AI Team'
}

TEAM_EMAIL = 'foty.ai@eorient.shop'

# ==================== EMAIL SENDING FUNCTION ====================
def send_email(to_email, subject, html_content, cc_email=None):
    """Generic email sending function with TLS (Port 587)"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if cc_email:
            msg['Cc'] = cc_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Use SMTP with STARTTLS (port 587)
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()  # Upgrade to TLS
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        
        recipients = [to_email]
        if cc_email:
            recipients.append(cc_email)
        
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

# ==================== EMAIL TEMPLATES ====================
def get_welcome_email_template(user_name, user_email):
    """Welcome email for new users"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #1e90ff, #0066cc);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 30px;
            }}
            .button {{
                display: inline-block;
                background: #1e90ff;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚽ Welcome to FOTY.AI!</h1>
            </div>
            <div class="content">
                <h2>Hello {user_name}!</h2>
                <p>Thank you for joining FOTY.AI - Your AI-Powered Football Performance Analyzer!</p>
                
                <p>We're excited to help you improve your football skills with cutting-edge AI technology.</p>
                
                <h3>🎯 What You Can Do:</h3>
                <ul>
                    <li>Upload your football videos for AI analysis</li>
                    <li>Get detailed performance scores and feedback</li>
                    <li>Receive personalized training recommendations</li>
                    <li>Track your progress over time</li>
                </ul>
                
                <p style="text-align: center;">
                    <a href="" class="button">Start Analyzing Now</a>
                </p>
                
                <p><strong>Your Account Details:</strong></p>
                <ul>
                    <li>Email: {user_email}</li>
                    <li>Registration Date: {datetime.now().strftime('%B %d, %Y')}</li>
                </ul>
                
                <p>If you have any questions, feel free to contact our support team.</p>
                
                <p>Best regards,<br><strong>The FOTY.AI Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; 2024 FOTY.AI. All rights reserved.</p>
                <p>This email was sent to {user_email}</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_password_reset_template(user_name, reset_token):
    """Password reset email"""
    reset_link = f"http://eorient.shop/reset-password?token={reset_token}"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #fbbf24, #f59e0b);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 30px;
            }}
            .button {{
                display: inline-block;
                background: #fbbf24;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .warning {{
                background: #fff3cd;
                border-left: 4px solid #fbbf24;
                padding: 15px;
                margin: 20px 0;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Password Reset Request</h1>
            </div>
            <div class="content">
                <h2>Hello {user_name}!</h2>
                <p>We received a request to reset your password for your FOTY.AI account.</p>
                
                <p style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset Your Password</a>
                </p>
                
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong>
                    <ul>
                        <li>This link will expire in 1 hour</li>
                        <li>If you didn't request this, please ignore this email</li>
                        <li>Never share this link with anyone</li>
                    </ul>
                </div>
                
                <p><strong>Or copy this link:</strong></p>
                <p style="word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 5px;">
                    {reset_link}
                </p>
                
                <p>If you're having trouble, contact our support team.</p>
                
                <p>Best regards,<br><strong>The FOTY.AI Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; 2024 FOTY.AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_contact_message_template(name, email, message):
    """Template for contact form messages to team"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #4ade80, #22c55e);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 30px;
            }}
            .info-box {{
                background: #f8f9fa;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
            }}
            .message-box {{
                background: #fff;
                border: 1px solid #e5e7eb;
                border-radius: 5px;
                padding: 20px;
                margin: 20px 0;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📧 New Contact Message</h1>
            </div>
            <div class="content">
                <h2>Customer Inquiry</h2>
                <p>You have received a new message from a customer:</p>
                
                <div class="info-box">
                    <p><strong>From:</strong> {name}</p>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <div class="message-box">
                    <h3>Message:</h3>
                    <p>{message}</p>
                </div>
                
                <p style="background: #e0f2fe; padding: 15px; border-radius: 5px;">
                    <strong>💡 Action Required:</strong> Please respond to this customer within 24 hours.
                </p>
            </div>
            <div class="footer">
                <p>&copy; 2024 FOTY.AI Team Dashboard</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_contact_auto_reply_template(customer_name):
    """Auto-reply for contact form"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #1e90ff, #0066cc);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 30px;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Message Received!</h1>
            </div>
            <div class="content">
                <h2>Hello {customer_name}!</h2>
                <p>Thank you for contacting FOTY.AI. We have received your message and our team will get back to you shortly.</p>
                
                <p style="background: #dbeafe; padding: 15px; border-radius: 5px;">
                    <strong>⏱️ Expected Response Time:</strong> Within 24-48 hours
                </p>
                
                <p>In the meantime, feel free to explore our platform and start analyzing your football performance!</p>
                
                <p>Best regards,<br><strong>The FOTY.AI Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; 2024 FOTY.AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_account_deletion_template(user_name, user_email, reason="Administrative action"):
    """Account deletion notification"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 20px auto;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #ef4444, #dc2626);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 30px;
            }}
            .alert-box {{
                background: #fee;
                border-left: 4px solid #ef4444;
                padding: 15px;
                margin: 20px 0;
            }}
            .info-box {{
                background: #f8f9fa;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
            }}
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚫 Account Deletion Notice</h1>
            </div>
            <div class="content">
                <h2>Dear {user_name},</h2>
                
                <div class="alert-box">
                    <h3>⚠️ Your Account Has Been Deleted</h3>
                    <p>We regret to inform you that your FOTY.AI account has been permanently deleted.</p>
                </div>
                
                <div class="info-box">
                    <p><strong>Account Email:</strong> {user_email}</p>
                    <p><strong>Deletion Date:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                    <p><strong>Reason:</strong> {reason}</p>
                </div>
                
                <h3>What This Means:</h3>
                <ul>
                    <li>Your account and all associated data have been permanently removed</li>
                    <li>You can no longer access the FOTY.AI platform with this email</li>
                    <li>All your video analyses and progress history have been deleted</li>
                    <li>This action cannot be undone</li>
                </ul>
                
                <h3>📞 Need Help?</h3>
                <p>If you believe this was done in error, please contact our support team at info@eorient.shop</p>
                
                <p style="background: #e0f2fe; padding: 15px; border-radius: 5px;">
                    <strong>💡 Want to Return?</strong><br>
                    You can create a new account at any time by visiting our registration page.
                </p>
                
                <p>We're sorry to see you go. Thank you for using FOTY.AI.</p>
                
                <p>Best regards,<br><strong>The FOTY.AI Team</strong></p>
            </div>
            <div class="footer">
                <p>&copy; 2024 FOTY.AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

# ==================== WRAPPER FUNCTIONS ====================
def send_welcome_email(user_name, user_email):
    """Send welcome email to new user"""
    subject = "🎉 Welcome to FOTY.AI - Let's Analyze Your Football Skills!"
    html_content = get_welcome_email_template(user_name, user_email)
    return send_email(user_email, subject, html_content)

def send_password_reset_email(user_name, user_email, reset_token):
    """Send password reset email"""
    subject = "🔐 Password Reset Request - FOTY.AI"
    html_content = get_password_reset_template(user_name, reset_token)
    return send_email(user_email, subject, html_content)

def send_contact_message_to_team(customer_name, customer_email, message):
    """Send customer message to team"""
    subject = f"📧 New Contact Message from {customer_name}"
    html_content = get_contact_message_template(customer_name, customer_email, message)
    return send_email(TEAM_EMAIL, subject, html_content)

def send_contact_auto_reply(customer_name, customer_email):
    """Send automatic reply to customer"""
    subject = "✅ We Received Your Message - FOTY.AI"
    html_content = get_contact_auto_reply_template(customer_name)
    return send_email(customer_email, subject, html_content)

def send_account_deletion_notification(user_name, user_email, reason="Administrative action"):
    """Send account deletion notification to user"""
    subject = "🚫 Your FOTY.AI Account Has Been Deleted"
    html_content = get_account_deletion_template(user_name, user_email, reason)
    return send_email(user_email, subject, html_content)