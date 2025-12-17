#!/usr/bin/env python3
"""
Test script to verify Twilio configuration and send OTP
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from twilio.rest import Client
import secrets

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Get Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

print("=" * 70)
print("TWILIO CONFIGURATION TEST & OTP SENDER")
print("=" * 70)

# Step 1: Verify credentials
print("\n📋 Step 1: Verifying Twilio Credentials...")
print(f"  ✓ Account SID: {TWILIO_ACCOUNT_SID[:5]}...{TWILIO_ACCOUNT_SID[-4:]}")
print(f"  ✓ Auth Token: {TWILIO_AUTH_TOKEN[:5]}...{TWILIO_AUTH_TOKEN[-4:]}")
print(f"  ✓ Twilio Phone: {TWILIO_PHONE_NUMBER}")

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
    print("\n❌ Missing Twilio credentials in .env file")
    sys.exit(1)

# Step 2: Initialize Twilio Client
print("\n🔌 Step 2: Initializing Twilio Client...")
try:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    print("  ✓ Twilio client initialized successfully")
except Exception as e:
    print(f"  ❌ Failed to initialize Twilio client: {str(e)}")
    sys.exit(1)

# Step 3: Test Twilio Connection
print("\n🧪 Step 3: Testing Twilio API Connection...")
try:
    # Get account info to verify connection
    account = client.api.accounts(TWILIO_ACCOUNT_SID).fetch()
    print(f"  ✓ Connected to Twilio API")
    print(f"  ✓ Account Status: {account.status}")
    print(f"  ✓ Account Balance: ${account.balance}")
except Exception as e:
    print(f"  ❌ Failed to connect to Twilio API: {str(e)}")
    sys.exit(1)

# Step 4: Generate OTP
print("\n🔐 Step 4: Generating OTP...")
OTP_LENGTH = int(os.getenv('OTP_LENGTH', 6))
otp_code = str(int(secrets.token_hex(3), 16) % (10 ** OTP_LENGTH)).zfill(OTP_LENGTH)
print(f"  ✓ OTP Generated: {otp_code}")

# Step 5: Send OTP via SMS
print("\n📱 Step 5: Sending OTP to 9677151810...")
try:
    mobile_number = "9677151810"
    phone_with_country = f"+91{mobile_number}"
    
    message_body = f"""Tamil Nadu Police - TOR UNVEIL
Your OTP: {otp_code}
Valid for 2 minutes
Do not share this OTP with anyone"""
    
    message = client.messages.create(
        body=message_body,
        from_=TWILIO_PHONE_NUMBER,
        to=phone_with_country
    )
    
    print(f"  ✓ SMS sent successfully!")
    print(f"  ✓ Message SID: {message.sid}")
    print(f"  ✓ To: {phone_with_country}")
    print(f"  ✓ Status: {message.status}")
    print(f"\n📧 Message Content:")
    print(f"  {message_body}")
    
except Exception as e:
    print(f"  ❌ Failed to send SMS: {str(e)}")
    sys.exit(1)

# Step 6: Display API Endpoint Info
print("\n" + "=" * 70)
print("✅ TWILIO CONFIGURATION VERIFIED & OTP SENT SUCCESSFULLY!")
print("=" * 70)

print("\n📝 Test Details:")
print(f"  • OTP Code: {otp_code}")
print(f"  • Recipient: +91{mobile_number}")
print(f"  • Sent From: {TWILIO_PHONE_NUMBER}")
print(f"  • Message SID: {message.sid}")
print(f"  • Expiry: 2 minutes (120 seconds)")

print("\n🔗 API Endpoint for Frontend:")
print(f"""
  POST http://localhost:8000/api/auth/send-otp
  Content-Type: application/json
  
  {{
    "login_id": "TN001",
    "mobile_number": "9677151810"
  }}
  
  Response:
  {{
    "status": "success",
    "message": "OTP sent to +919677151810"
  }}
""")

print("✅ Everything is working! Check your phone for the SMS.")
print("=" * 70)
