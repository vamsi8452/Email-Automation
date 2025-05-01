import os
from dotenv import load_dotenv

# Load environment variables explicitly from .env file
print(f"Current working directory: {os.getcwd()}")
env_path = os.path.join(os.getcwd(), '.env')
print(f"Looking for .env file at: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")

# Force reload of environment variables
os.environ.clear()
load_dotenv(env_path)

# Get the App Password from .env
password = os.getenv("GMAIL_APP_PASSWORD")

# Check password details
print(f"App Password length: {len(password) if password else 0}")
print(f"Password characters (first and last 2): {password[:2]}...{password[-2:] if len(password) >= 2 else ''}")
print(f"All characters: {' '.join(password)}")

# Check if it has any spaces
if ' ' in password:
    print("Warning: App Password contains spaces!")
else:
    print("App Password does not contain spaces")

# Count any special characters
special_chars = sum(1 for char in password if not char.isalnum())
if special_chars > 0:
    print(f"Warning: App Password contains {special_chars} special characters!")
else:
    print("App Password does not contain special characters")