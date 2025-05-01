# Email Automation Script for Job Seekers

This Python script automates email processing to help postgraduate job seekers manage their inbox efficiently. The script connects to Gmail via IMAP, classifies emails into different categories, and processes them accordingly.

## Features

- **Automatic Email Classification**:
  - Ads/promotions: Automatically moved to trash
  - Recruiter emails: Send SMS alerts for immediate attention
  - Personal emails: Generate and send AI-powered friendly responses

- **Smart Detection**:
  - Identifies recruiter emails based on sender domains and job-related keywords
  - Recognizes promotional content to reduce inbox clutter
  - Treats remaining emails as personal communications

- **Notifications**:
  - Sends SMS alerts when recruiter emails arrive using Twilio
  - Keeps you informed about job opportunities even when away from email

- **AI-Generated Responses**:
  - Uses OpenAI's GPT models to create personalized, contextual responses
  - Maintains a warm, professional tone for personal communications
  - Acknowledges email content intelligently

## Prerequisites

- Python 3.6+
- Gmail account with [App Password](https://myaccount.google.com/apppasswords) enabled
- [Twilio](https://www.twilio.com/) account for SMS capabilities
- [OpenAI](https://platform.openai.com/) API key for response generation

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/email-automation.git
   cd email-automation
   ```

2. Install required packages:
   ```bash
   pip install python-dotenv openai twilio schedule
   ```

3. Create a `.env` file in the project root with the following environment variables:
   ```
   # Gmail credentials
   GMAIL_USERNAME=your.email@gmail.com
   GMAIL_APP_PASSWORD=your-16-char-app-password
   
   # Twilio credentials
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   USER_PHONE_NUMBER=+1234567890
   
   # OpenAI API key
   OPENAI_API_KEY=your_openai_api_key
   ```

4. Setting up Gmail App Password:
   - Enable 2-Step Verification at [Google Account Security](https://myaccount.google.com/security)
   - Generate an App Password at [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" as the app and your device name
   - Use the generated 16-character password without spaces

## Usage

Run the script to start automated email processing:

```bash
python email_automation.py
```

The script will:
1. Connect to your Gmail account
2. Check for unread emails
3. Classify and process each email based on its category
4. Continue monitoring for new emails every 2 minutes

To stop the script, press `Ctrl+C` in the terminal.

## Customization

You can customize the email classification by editing the keyword lists in the `classify_email()` function:

- `ad_indicators`: Keywords that indicate promotional content
- `ad_domains`: Sender domains typically associated with ads
- `recruiter_indicators`: Job-related terms indicating recruiting emails
- `recruiter_domains`: Domains typically used by recruiters

## Troubleshooting

- **Authentication Issues**: Ensure you're using an App Password, not your regular Gmail password
- **Gmail Access**: Check that "Less secure app access" or IMAP is enabled in your Gmail settings
- **SMS Not Sending**: Verify your Twilio credentials and phone number format (include country code)

## License

This project is licensed under the MIT License - see the LICENSE file for details.