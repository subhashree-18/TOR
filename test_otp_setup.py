#!/usr/bin/env python3
"""
Test script to verify OTP backend configuration
Run this to check if everything is set up correctly
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

def check_env_file():
    """Check if .env file exists"""
    print("\n📋 Checking .env file...")
    env_path = Path('backend/.env')
    
    if env_path.exists():
        print("✅ .env file found")
        with open(env_path) as f:
            content = f.read()
            if 'TWILIO_ACCOUNT_SID' in content:
                print("✅ Twilio credentials configured")
                return True
            else:
                print("❌ Twilio credentials not found in .env")
                return False
    else:
        print("❌ .env file not found")
        print("   Run: cp backend/.env.example backend/.env")
        return False

def check_python_packages():
    """Check if required packages are installed"""
    print("\n📦 Checking Python packages...")
    
    required_packages = {
        'fastapi': 'FastAPI',
        'pymongo': 'MongoDB driver',
        'twilio': 'Twilio SMS',
        'dotenv': 'Environment variables',
        'jwt': 'JWT tokens',
    }
    
    all_installed = True
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {name} ({package})")
        except ImportError:
            print(f"❌ {name} ({package})")
            all_installed = False
    
    if not all_installed:
        print("\n   Install missing packages:")
        print("   pip install -r backend/requirements.txt")
    
    return all_installed

def check_mongodb():
    """Check MongoDB connection"""
    print("\n🗄️  Checking MongoDB...")
    
    try:
        from pymongo import MongoClient
        
        client = MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ MongoDB is running and accessible")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        print("   Make sure MongoDB is running:")
        print("   docker compose up -d mongo")
        return False

def check_twilio_credentials():
    """Check Twilio credentials"""
    print("\n📱 Checking Twilio credentials...")
    
    from dotenv import load_dotenv
    load_dotenv('backend/.env')
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
    
    if not account_sid:
        print("❌ TWILIO_ACCOUNT_SID not set")
        return False
    
    if not auth_token:
        print("❌ TWILIO_AUTH_TOKEN not set")
        return False
    
    if not twilio_phone:
        print("❌ TWILIO_PHONE_NUMBER not set")
        return False
    
    # Mask sensitive info
    masked_sid = account_sid[:2] + '*' * (len(account_sid) - 4) + account_sid[-2:]
    masked_token = auth_token[:2] + '*' * (len(auth_token) - 4) + auth_token[-2:]
    
    print(f"✅ Account SID: {masked_sid}")
    print(f"✅ Auth Token: {masked_token}")
    print(f"✅ Phone Number: {twilio_phone}")
    
    return True

def test_twilio_connection():
    """Test Twilio SMS sending"""
    print("\n🧪 Testing Twilio Connection...")
    
    try:
        from dotenv import load_dotenv
        from twilio.rest import Client
        
        load_dotenv('backend/.env')
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            print("❌ Twilio credentials not configured")
            return False
        
        client = Client(account_sid, auth_token)
        
        # List recent messages to verify connection
        messages = client.messages.list(limit=1)
        
        print("✅ Successfully connected to Twilio API")
        return True
    
    except Exception as e:
        print(f"❌ Twilio connection failed: {str(e)}")
        return False

def check_api_endpoints():
    """Check if API endpoints are available"""
    print("\n🔌 Checking API endpoints...")
    
    try:
        import requests
        
        endpoints = [
            'http://localhost:8000/api/auth/health',
            'http://localhost:8000/docs',
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=2)
                if response.status_code in [200, 404]:
                    print(f"✅ {endpoint}")
                else:
                    print(f"⚠️  {endpoint} (Status: {response.status_code})")
            except requests.ConnectionError:
                print(f"❌ {endpoint} (Connection refused)")
                print("   Make sure backend is running: docker compose up -d backend")
                return False
        
        return True
    
    except ImportError:
        print("⚠️  requests library not installed (skipping endpoint check)")
        return False

def print_summary(results):
    """Print test summary"""
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_bool in results.items():
        status = "✅ PASS" if passed_bool else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Ready for SMS OTP testing!")
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Fix issues above.")
    
    print("="*50)

def main():
    """Run all checks"""
    print("\n" + "="*50)
    print("OTP BACKEND CONFIGURATION CHECKER")
    print("="*50)
    
    results = {
        ".env file configured": check_env_file(),
        "Python packages installed": check_python_packages(),
        "MongoDB running": check_mongodb(),
        "Twilio credentials": check_twilio_credentials(),
        "Twilio API connection": test_twilio_connection(),
        "API endpoints available": check_api_endpoints(),
    }
    
    print_summary(results)
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
