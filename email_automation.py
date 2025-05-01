"""
Gmail Email Automation Script

This script connects to Gmail via IMAP, classifies emails into different categories,
and processes them accordingly:
- Ads/promotions: Moved to trash
- Recruiter emails: Send SMS alerts via Twilio
- Personal emails: Generate and send AI responses

Requirements:
pip install python-dotenv openai twilio schedule
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import os
import time
import schedule
import logging
from dotenv import load_dotenv
from twilio.rest import Client
from openai import OpenAI

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG level for more verbose output
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables explicitly from .env file
env_path = os.path.join(os.getcwd(), '.env')
logger.debug(f"Loading .env from: {env_path}")
logger.debug(f"File exists: {os.path.exists(env_path)}")

# Force reload of environment variables
os.environ.clear()
load_dotenv(env_path)

# Gmail credentials
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME")
# Ensure that Gmail username is a complete email address
if GMAIL_USERNAME and '@' not in GMAIL_USERNAME:
    GMAIL_USERNAME = f"{GMAIL_USERNAME}@gmail.com"
    logger.debug(f"Modified Gmail username to include domain: {GMAIL_USERNAME}")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")  # App password for Gmail

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# Ensure phone numbers are in proper format with + prefix
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
if TWILIO_PHONE_NUMBER and not TWILIO_PHONE_NUMBER.startswith('+'):
    TWILIO_PHONE_NUMBER = f"+{TWILIO_PHONE_NUMBER}"
    logger.debug(f"Formatted Twilio phone number: {TWILIO_PHONE_NUMBER}")
    
USER_PHONE_NUMBER = os.getenv("USER_PHONE_NUMBER")
if USER_PHONE_NUMBER and not USER_PHONE_NUMBER.startswith('+'):
    USER_PHONE_NUMBER = f"+{USER_PHONE_NUMBER}"
    logger.debug(f"Formatted user phone number: {USER_PHONE_NUMBER}")

# OpenAI credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# Do not change this unless explicitly requested by the user
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def connect_to_gmail():
    """
    Establish an IMAP connection to Gmail.
    
    Returns:
        mail: IMAP4_SSL connection object
    """
    try:
        # Log credentials being used (without exposing the password)
        logger.debug(f"Attempting to connect to Gmail using username: {GMAIL_USERNAME}")
        if not GMAIL_USERNAME or not GMAIL_PASSWORD:
            logger.error("Gmail username or password is missing")
            raise ValueError("Gmail credentials are missing or invalid")
            
        # Connect to Gmail's IMAP server
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        
        try:
            # Attempt to login with credentials
            mail.login(GMAIL_USERNAME, GMAIL_PASSWORD)
        except imaplib.IMAP4.error as login_error:
            error_msg = str(login_error)
            if "AUTHENTICATIONFAILED" in error_msg:
                logger.error("Authentication failed. Possible causes:")
                logger.error("1. Incorrect Gmail username (should be complete email: user@gmail.com)")
                logger.error("2. Incorrect App Password (not regular password)")
                logger.error("3. 2-Step Verification not enabled for this Google account")
                logger.error("4. App Password not generated for 'Mail' application")
            raise
            
        # Select inbox after successful login
        mail.select("inbox")
        logger.info("Successfully connected to Gmail")
        return mail
    except Exception as e:
        logger.error(f"Failed to connect to Gmail: {e}")
        raise


def fetch_unread_emails(mail):
    """
    Fetch unread emails from Gmail inbox.
    
    Args:
        mail: IMAP4_SSL connection object
    
    Returns:
        list: List of (email_id, email_data) tuples
    """
    try:
        status, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()
        
        emails = []
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            emails.append((email_id, msg_data))
        
        logger.info(f"Fetched {len(emails)} unread emails")
        return emails
    except Exception as e:
        logger.error(f"Failed to fetch unread emails: {e}")
        return []


def parse_email(msg_data):
    """
    Parse email data to extract subject, sender, and body.
    
    Args:
        msg_data: Email message data
    
    Returns:
        dict: Dictionary containing email parts
    """
    email_message = email.message_from_bytes(msg_data[0][1])
    
    subject = email_message["Subject"] or ""
    from_address = email_message["From"] or ""
    
    # Extract email body
    body = ""
    if email_message.is_multipart():
        for part in email_message.get_payload():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                break
    else:
        body = email_message.get_payload(decode=True).decode("utf-8", errors="ignore")
    
    return {
        "subject": subject,
        "from": from_address,
        "body": body,
        "message_id": email_message["Message-ID"],
        "to": email_message["To"],
        "date": email_message["Date"]
    }


def classify_email(email_data):
    """
    Classify email into one of three categories:
    - Ads/promotions
    - Recruiter emails
    - Personal emails
    
    Args:
        email_data: Dictionary containing email data
    
    Returns:
        str: Email classification
    """
    subject = email_data["subject"].lower() if email_data["subject"] else ""
    from_address = email_data["from"].lower() if email_data["from"] else ""
    body = email_data["body"].lower() if email_data["body"] else ""
    
    # Check if it's an ad/promotion/spam
    ad_indicators = [
        "unsubscribe", "promotion", "offer", "discount", "sale", "newsletter", 
        "limited time", "exclusive offer", "free trial", "clearance", 
        "subscribe", "marketing", "promo code", "coupon", "advertisement",
        "deal", "off selected", "price drop", "click here", "buy now"
    ]
    
    ad_domains = [
        "marketing", "newsletter", "info@", "noreply@", "promotions@", 
        "offers@", "updates@", "news@", "email@", "mail@", "contact@"
    ]
    
    # Check ad indicators in subject or body
    for indicator in ad_indicators:
        if indicator in body or indicator in subject:
            logger.debug(f"Classified as ad based on indicator: {indicator}")
            return "ad"
    
    # Check ad-related sender domains/addresses
    for domain in ad_domains:
        if domain in from_address:
            logger.debug(f"Classified as ad based on sender: {domain}")
            return "ad"
    
    # Check if it's a recruiter email
    recruiter_indicators = [
        "job opportunity", "job opening", "position", "career", "recruitment",
        "talent acquisition", "hiring", "interview", "job application", 
        "job description", "resume", "cv", "job title", "qualifications",
        "job requirements", "salary", "apply online"
    ]
    
    recruiter_domains = [
        "linkedin.com", "indeed.com", "monster.com", "dice.com", "ziprecruiter.com", 
        "greenhouse.io", "lever.co", "taleo.net", "smartrecruiters.com", "recruiter",
        "talent", "careers", "workday.com", "jobs", "employment", "staffing", 
        "recruiting", "hr@", "recruit@", "talent@", "jobs@", "careers@"
    ]
    
    # Check recruiter indicators in subject or body
    for indicator in recruiter_indicators:
        if indicator in body or indicator in subject:
            logger.debug(f"Classified as recruiter based on indicator: {indicator}")
            return "recruiter"
            
    # Check recruiter domains in sender address
    for domain in recruiter_domains:
        if domain in from_address:
            logger.debug(f"Classified as recruiter based on sender: {domain}")
            return "recruiter"
    
    # If no match, classify as personal
    logger.debug("No classification match, treating as personal email")
    return "personal"


def move_to_trash(mail, email_id):
    """
    Move an email to trash (Gmail's Bin/Trash folder).
    
    Args:
        mail: IMAP4_SSL connection object
        email_id: ID of the email to move
    """
    try:
        # Add the Trash/Bin label and mark as deleted
        mail.store(email_id, '+X-GM-LABELS', '\\Trash')
        mail.store(email_id, '+FLAGS', '\\Deleted')
        logger.info(f"Moved email {email_id} to trash")
    except Exception as e:
        logger.error(f"Failed to move email {email_id} to trash: {e}")


def send_sms_alert(email_data):
    """
    Send SMS alert for recruiter emails using Twilio.
    
    Args:
        email_data: Dictionary containing email data
    """
    try:
        # Create a message with key information
        message_body = f"New recruiter email!\nFrom: {email_data['from']}\nSubject: {email_data['subject']}"
        
        # Send SMS using Twilio
        message = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=USER_PHONE_NUMBER
        )
        
        logger.info(f"SMS alert sent for recruiter email. SID: {message.sid}")
    except Exception as e:
        logger.error(f"Failed to send SMS alert: {e}")


def generate_ai_response(email_data):
    """
    Generate a friendly response to a personal email using OpenAI.
    
    Args:
        email_data: Dictionary containing email data
    
    Returns:
        str: Generated response
    """
    try:
        # Extract sender's name from email address
        sender_name = re.search(r'(.*?)\s*<', email_data['from'])
        if sender_name:
            sender_name = sender_name.group(1).strip()
        else:
            sender_name = email_data['from'].split('@')[0]
        
        # Create prompt for OpenAI
        prompt = f"""
        You are a personal assistant replying to an email. Write a friendly, thoughtful response that 
        acknowledges the content and maintains a warm, professional tone.
        
        Original email details:
        From: {email_data['from']}
        Subject: {email_data['subject']}
        Body: {email_data['body'][:500]}...
        
        Your response should:
        1. Start with a greeting using their name if available
        2. Acknowledge the content of their email
        3. Provide a thoughtful, personalized response
        4. End with a friendly closing
        
        Write only the response body, no additional instructions or explanations.
        """
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # The newest OpenAI model is "gpt-4o" which was released May 13, 2024
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract and return the generated response
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to generate AI response: {e}")
        return f"Thank you for your email. I'll get back to you shortly. (Automated response)"


def send_email_reply(email_data, response_body):
    """
    Send an email reply using SMTP.
    
    Args:
        email_data: Dictionary containing original email data
        response_body: Body of the response email
    """
    try:
        # Create a multipart message
        msg = MIMEMultipart()
        
        # Extract the email address to reply to
        match = re.search(r'<(.*?)>', email_data['from'])
        if match:
            reply_to = match.group(1)
        else:
            reply_to = email_data['from']
        
        # Set the headers
        msg['From'] = GMAIL_USERNAME
        msg['To'] = reply_to
        msg['Subject'] = f"Re: {email_data['subject']}"
        
        # Add in-reply-to and references headers if message_id exists
        if email_data.get('message_id'):
            msg['In-Reply-To'] = email_data['message_id']
            msg['References'] = email_data['message_id']
        
        # Attach the response body
        msg.attach(MIMEText(response_body, 'plain'))
        
        # Connect to Gmail's SMTP server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USERNAME, GMAIL_PASSWORD)
        
        # Send the email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Sent reply to {reply_to}")
    except Exception as e:
        logger.error(f"Failed to send email reply: {e}")


def process_emails():
    """
    Main function to process emails:
    1. Connect to Gmail
    2. Fetch unread emails
    3. Classify and process each email accordingly
    """
    try:
        # Log the current configuration (without exposing sensitive information)
        logger.debug("======= Email Automation Configuration =======")
        logger.debug(f"Gmail Username: {GMAIL_USERNAME}")
        logger.debug(f"Gmail Password: {'*' * 8 if GMAIL_PASSWORD else 'NOT SET'}")
        logger.debug(f"OpenAI API Key: {'*' * 8 if OPENAI_API_KEY else 'NOT SET'}")
        logger.debug(f"Twilio Account SID: {'*' * 8 if TWILIO_ACCOUNT_SID else 'NOT SET'}")
        logger.debug(f"Twilio Auth Token: {'*' * 8 if TWILIO_AUTH_TOKEN else 'NOT SET'}")
        logger.debug(f"Twilio Phone Number: {TWILIO_PHONE_NUMBER}")
        logger.debug(f"User Phone Number: {USER_PHONE_NUMBER}")
        logger.debug("============================================")
        
        # Check if required environment variables are set
        if not all([GMAIL_USERNAME, GMAIL_PASSWORD, OPENAI_API_KEY, 
                   TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, 
                   TWILIO_PHONE_NUMBER, USER_PHONE_NUMBER]):
            logger.error("Missing required environment variables. Check your .env file.")
            logger.error("Make sure all credentials are properly set in .env file")
            return
        
        # Connect to Gmail
        mail = connect_to_gmail()
        
        # Fetch unread emails
        emails = fetch_unread_emails(mail)
        
        if not emails:
            logger.info("No new emails to process")
            return
        
        # Process each email
        for email_id, msg_data in emails:
            try:
                # Parse email
                email_data = parse_email(msg_data)
                
                # Classify email
                category = classify_email(email_data)
                logger.info(f"Classified email '{email_data['subject']}' as '{category}'")
                
                # Process based on classification
                if category == "ad":
                    move_to_trash(mail, email_id)
                
                elif category == "recruiter":
                    send_sms_alert(email_data)
                    # Keep recruiter emails in inbox, just mark as read
                    mail.store(email_id, '+FLAGS', '\\Seen')
                
                elif category == "personal":
                    # Generate and send reply
                    response = generate_ai_response(email_data)
                    send_email_reply(email_data, response)
                    # Mark as read
                    mail.store(email_id, '+FLAGS', '\\Seen')
            
            except Exception as e:
                logger.error(f"Error processing email {email_id}: {e}")
        
        # Logout from Gmail
        mail.logout()
        
    except Exception as e:
        logger.error(f"Error in process_emails: {e}")


def run_scheduler():
    """
    Setup and run the scheduler to process emails every 2 minutes.
    """
    # Schedule the job to run every 2 minutes
    schedule.every(2).minutes.do(process_emails)
    
    logger.info("Email automation started. Running every 2 minutes.")
    
    # Run the scheduled job indefinitely
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    try:
        # Run process_emails once at startup
        process_emails()
        
        # Then start the scheduler
        run_scheduler()
    except KeyboardInterrupt:
        logger.info("Email automation stopped by user.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
