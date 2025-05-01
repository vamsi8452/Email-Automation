"""
Test script for Gmail authentication

This script tests authentication with Gmail's IMAP server using credentials from .env
It will only attempt to login, not fetch or process any emails
"""

import imaplib
import os
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables explicitly from .env file
env_path = os.path.join(os.getcwd(), '.env')
logger.info(f"Loading .env from: {env_path}")
logger.info(f"File exists: {os.path.exists(env_path)}")

# Force reload of environment variables
os.environ.clear()
load_dotenv(env_path)

# Gmail credentials
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME")
# Ensure that Gmail username is a complete email address
if GMAIL_USERNAME and '@' not in GMAIL_USERNAME:
    GMAIL_USERNAME = f"{GMAIL_USERNAME}@gmail.com"
    logger.debug(f"Modified Gmail username to include domain: {GMAIL_USERNAME}")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def test_gmail_auth():
    """
    Test authentication with Gmail's IMAP server
    """
    logger.info("=== Gmail Authentication Test ===")
    
    # Log configuration (without exposing passwords)
    logger.info(f"Using Gmail username: {GMAIL_USERNAME}")
    logger.info(f"App Password length: {len(GMAIL_PASSWORD) if GMAIL_PASSWORD else 0} characters")
    
    try:
        # Connect to Gmail's IMAP server
        logger.info("Connecting to imap.gmail.com...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        
        # Try authentication
        logger.info("Attempting to authenticate...")
        mail.login(GMAIL_USERNAME, GMAIL_PASSWORD)
        
        # If we get here, authentication was successful
        logger.info("Authentication SUCCESSFUL! ✓")
        logger.info("Logging out...")
        mail.logout()
        return True
        
    except imaplib.IMAP4.error as e:
        logger.error(f"Authentication FAILED: {e}")
        logger.error("")
        logger.error("Possible solutions:")
        logger.error("1. Verify your Gmail username is correct")
        logger.error("2. Make sure 2-Step Verification is enabled for your Google Account")
        logger.error("3. Generate a new App Password specifically for this application")
        logger.error("4. Ensure the App Password has no spaces when added to .env")
        logger.error("5. Check if 'Less secure app access' is turned on (for older accounts)")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_gmail_auth()