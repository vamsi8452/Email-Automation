"""
Test script for email classification functionality in email_automation.py

This script tests the email classification logic with sample emails
without connecting to Gmail or sending any actual messages.
"""

import logging
import sys
from email_automation import classify_email

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def test_email_classification():
    """Test email classification with various sample emails"""
    
    logger.info("Testing email classification...")
    
    # Test cases: list of (email_data, expected_classification) tuples
    test_cases = [
        # Promotional/Ad emails
        ({
            "subject": "Limited time offer: 50% off all items!",
            "from": "marketing@example.com",
            "body": "Check out our latest sale with amazing discounts. Click here to unsubscribe."
        }, "ad"),
        
        ({
            "subject": "Your weekly newsletter",
            "from": "newsletter@updates.com",
            "body": "Here are this week's top stories..."
        }, "ad"),
        
        # Recruiter emails
        ({
            "subject": "Job opportunity at Tech Company",
            "from": "recruiter@linkedin.com",
            "body": "Based on your profile, we think you'd be a great fit for this position..."
        }, "recruiter"),
        
        ({
            "subject": "Your application status",
            "from": "careers@google.com",
            "body": "Thank you for your interest in the software engineer position."
        }, "recruiter"),
        
        ({
            "subject": "Follow-up on your resume",
            "from": "john@company.com",
            "body": "We reviewed your qualifications and would like to schedule an interview."
        }, "recruiter"),
        
        # Personal emails
        ({
            "subject": "Coffee next week?",
            "from": "friend@gmail.com",
            "body": "Hey, are you free to catch up over coffee next Tuesday?"
        }, "personal"),
        
        ({
            "subject": "Question about your project",
            "from": "professor@university.edu",
            "body": "I was looking at your research and had a question about your methodology."
        }, "personal"),
        
        ({
            "subject": "Family reunion plans",
            "from": "mom@familydomain.com",
            "body": "We're planning the family reunion for next summer. Are you available in July?"
        }, "personal")
    ]
    
    # Run tests
    passed = 0
    for i, (email_data, expected) in enumerate(test_cases, 1):
        logger.info(f"\nTest case #{i}:")
        logger.info(f"Subject: {email_data['subject']}")
        logger.info(f"From: {email_data['from']}")
        logger.info(f"Body: {email_data['body'][:50]}...")
        
        result = classify_email(email_data)
        logger.info(f"Classification: {result} (Expected: {expected})")
        
        if result == expected:
            logger.info("✓ PASSED")
            passed += 1
        else:
            logger.error("✗ FAILED")
    
    # Show summary
    logger.info(f"\nResults: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)

if __name__ == "__main__":
    success = test_email_classification()
    print("\nAll tests passed!" if success else "\nSome tests failed!")