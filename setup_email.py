#!/usr/bin/env python3
"""
Email Configuration Setup Script for TaxBot

This script helps you configure email settings for the DIAN tax bot.
It will prompt you for email credentials and update the .env file.
"""

import os
import getpass
from pathlib import Path

def setup_email_config():
    print("=== TaxBot Email Configuration Setup ===")
    print()
    print("This script will help you configure email notifications for the DIAN tax bot.")
    print("You'll need:")
    print("1. A Gmail account")
    print("2. An App Password (not your regular password)")
    print("   - Go to Google Account settings")
    print("   - Security > 2-Step Verification > App passwords")
    print("   - Generate an app password for 'Mail'")
    print()
    
    # Get email configuration
    sender_email = input("Enter your Gmail address: ").strip()
    if not sender_email or "@gmail.com" not in sender_email:
        print("Please enter a valid Gmail address.")
        return False
    
    print("\nEnter your Gmail App Password (not your regular password):")
    app_password = getpass.getpass("App Password: ").strip()
    if not app_password:
        print("App password is required.")
        return False
    
    print("\nEnter recipient email addresses (comma-separated):")
    recipients = input("Recipients: ").strip()
    if not recipients:
        print("At least one recipient is required.")
        return False
    
    # Validate recipients
    recipient_list = [email.strip() for email in recipients.split(",") if email.strip()]
    if not recipient_list:
        print("No valid recipients provided.")
        return False
    
    # Update .env file
    env_path = Path(".env")
    env_content = f"""# Ollama API Configuration
OLLAMA_API_KEY=c6f1e109560b4b098ff80b99c5942d42.DdN4aonYSge8plew0dvp3XO_
OLLAMA_MODEL=llama3

# Email Configuration
DIAN_EMAIL_SENDER={sender_email}
DIAN_EMAIL_PASSWORD={app_password}
DIAN_EMAIL_RECIPIENTS={','.join(recipient_list)}
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"\n✅ Email configuration saved to {env_path}")
        print(f"📧 Sender: {sender_email}")
        print(f"📬 Recipients: {', '.join(recipient_list)}")
        print("\nYou can now run the tax bot and it will send email notifications!")
        return True
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False

if __name__ == "__main__":
    setup_email_config()