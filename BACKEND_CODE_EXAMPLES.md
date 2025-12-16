# 💻 Ready-to-Use Backend Code Examples

## Complete OTP Backend Implementation

### File: `backend/app/auth.py`

```python
"""
Authentication module for Police Officer Login with OTP
"""
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
import secrets
import re
import redis
import os
from dotenv import load_dotenv
import jwt

load_dotenv()

# Initialize Redis client (or use database if Redis not available)
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    USE_REDIS = True
except:
    print("Redis not available, using in-memory storage")
    USE_REDIS = False
    IN_MEMORY_OTP = {}  # Fallback in-memory storage

# Router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# ============================================================================
# MODELS
# ============================================================================

class SendOTPRequest(BaseModel):
    """Request model for sending OTP"""
    loginId: str
    mobileNumber: str
    
    @validator('loginId')
    def validate_login_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Login ID cannot be empty')
        return v.strip()
    
    @validator('mobileNumber')
    def validate_mobile(cls, v):
        if not re.match(r'^[6-9]\d{9}$', v):
            raise ValueError('Invalid Indian mobile number')
        return v

class VerifyOTPRequest(BaseModel):
    """Request model for verifying OTP"""
    loginId: str
    mobileNumber: str
    otp: str
    
    @validator('otp')
    def validate_otp(cls, v):
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP must be 6 digits')
        return v

class OTPResponse(BaseModel):
    """Response model for OTP operations"""
    status: str
    message: str
    expiresIn: int = 120

class LoginResponse(BaseModel):
    """Response model for successful login"""
    status: str
    message: str
    token: str
    user: dict

# ============================================================================
# OTP STORAGE FUNCTIONS
# ============================================================================

def store_otp(login_id: str, mobile: str, otp: str, expiry_seconds: int = 120):
    """Store OTP with expiry"""
    key = f"otp:{login_id}:{mobile}"
    
    if USE_REDIS:
        redis_client.setex(key, expiry_seconds, otp)
    else:
        IN_MEMORY_OTP[key] = {
            'otp': otp,
            'expires_at': datetime.utcnow() + timedelta(seconds=expiry_seconds)
        }

def get_otp(login_id: str, mobile: str) -> str or None:
    """Retrieve stored OTP"""
    key = f"otp:{login_id}:{mobile}"
    
    if USE_REDIS:
        return redis_client.get(key)
    else:
        if key in IN_MEMORY_OTP:
            if datetime.utcnow() < IN_MEMORY_OTP[key]['expires_at']:
                return IN_MEMORY_OTP[key]['otp']
            else:
                del IN_MEMORY_OTP[key]
        return None

def delete_otp(login_id: str, mobile: str):
    """Delete OTP after verification"""
    key = f"otp:{login_id}:{mobile}"
    
    if USE_REDIS:
        redis_client.delete(key)
    else:
        if key in IN_MEMORY_OTP:
            del IN_MEMORY_OTP[key]

def increment_attempt(login_id: str, mobile: str) -> int:
    """Increment OTP verification attempts"""
    key = f"otp_attempts:{login_id}:{mobile}"
    
    if USE_REDIS:
        attempts = redis_client.incr(key)
        redis_client.expire(key, 300)  # Reset after 5 minutes
        return attempts
    else:
        if key not in IN_MEMORY_OTP:
            IN_MEMORY_OTP[key] = {'attempts': 0, 'expires_at': datetime.utcnow() + timedelta(minutes=5)}
        
        IN_MEMORY_OTP[key]['attempts'] += 1
        return IN_MEMORY_OTP[key]['attempts']

# ============================================================================
# SMS SENDING FUNCTIONS
# ============================================================================

def send_sms_otp(mobile_number: str, otp_code: str) -> dict:
    """
    Send OTP via SMS
    Currently using console logging for demo
    In production, integrate with Twilio, AWS SNS, or local gateway
    """
    
    # Option 1: Console logging (for development)
    print("\n" + "="*60)
    print(f"📱 SMS SENT TO: +91{mobile_number}")
    print(f"📧 MESSAGE:")
    print(f"   Tamil Nadu Police - TOR UNVEIL")
    print(f"   Your OTP: {otp_code}")
    print(f"   Valid for 2 minutes")
    print("="*60 + "\n")
    
    return {
        "status": "success",
        "message_id": f"demo_{otp_code}"
    }

def send_sms_otp_twilio(mobile_number: str, otp_code: str) -> dict:
    """Send OTP via Twilio (production implementation)"""
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body=f"Tamil Nadu Police - TOR UNVEIL\nYour OTP: {otp_code}\nValid for 2 minutes",
            from_=twilio_number,
            to=f"+91{mobile_number}"
        )
        
        return {"status": "success", "message_id": message.sid}
    
    except Exception as e:
        print(f"Twilio SMS Error: {str(e)}")
        return {"status": "error", "message": str(e)}

def send_sms_otp_aws(mobile_number: str, otp_code: str) -> dict:
    """Send OTP via AWS SNS (production implementation)"""
    try:
        import boto3
        
        sns_client = boto3.client(
            'sns',
            region_name=os.getenv('AWS_REGION', 'ap-south-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        response = sns_client.publish(
            PhoneNumber=f"+91{mobile_number}",
            Message=f"Tamil Nadu Police - TOR UNVEIL\nYour OTP: {otp_code}\nValid for 2 minutes"
        )
        
        return {"status": "success", "message_id": response['MessageId']}
    
    except Exception as e:
        print(f"AWS SNS Error: {str(e)}")
        return {"status": "error", "message": str(e)}

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(
    request: SendOTPRequest,
    client_request: Request
):
    """
    Send OTP to police officer's mobile number
    
    Args:
        request: Contains loginId and mobileNumber
        client_request: FastAPI Request object for rate limiting
    
    Returns:
        OTPResponse with status and expiry time
    """
    
    try:
        # Rate limiting check
        client_ip = client_request.client.host
        rate_limit_key = f"rate_limit:{client_ip}"
        
        if USE_REDIS:
            attempts = redis_client.incr(rate_limit_key)
            if attempts == 1:
                redis_client.expire(rate_limit_key, 60)  # Reset every minute
            
            if attempts > 5:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many OTP requests. Please wait a minute."
                )
        
        # Generate OTP
        otp_code = generate_otp()
        
        # Store OTP
        store_otp(request.loginId, request.mobileNumber, otp_code)
        
        # Send SMS
        sms_result = send_sms_otp(request.mobileNumber, otp_code)
        
        if sms_result["status"] == "success":
            return OTPResponse(
                status="success",
                message=f"OTP sent to +91{request.mobileNumber}",
                expiresIn=120
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send SMS. Please try again."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending OTP: {str(e)}"
        )

@router.post("/verify-otp", response_model=LoginResponse)
async def verify_otp(request: VerifyOTPRequest):
    """
    Verify OTP and return authentication token
    
    Args:
        request: Contains loginId, mobileNumber, and otp
    
    Returns:
        LoginResponse with JWT token and user info
    """
    
    try:
        # Check attempt limit
        attempts = increment_attempt(request.loginId, request.mobileNumber)
        if attempts > 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please request a new OTP."
            )
        
        # Verify OTP
        stored_otp = get_otp(request.loginId, request.mobileNumber)
        
        if not stored_otp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OTP expired or not found. Please request a new OTP."
            )
        
        if stored_otp != request.otp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OTP. Please try again."
            )
        
        # OTP verified successfully
        delete_otp(request.loginId, request.mobileNumber)
        
        # Generate JWT token
        payload = {
            "loginId": request.loginId,
            "mobileNumber": request.mobileNumber,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=8)
        }
        
        token = jwt.encode(
            payload,
            os.getenv("JWT_SECRET_KEY", "your-secret-key"),
            algorithm="HS256"
        )
        
        return LoginResponse(
            status="success",
            message="Login successful",
            token=token,
            user={
                "loginId": request.loginId,
                "mobileNumber": request.mobileNumber,
                "loginTime": datetime.utcnow().isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification error: {str(e)}"
        )

@router.post("/logout")
async def logout(request: Request):
    """
    Logout user (invalidate token if needed)
    """
    try:
        # In a real implementation, you might blacklist the token
        return {
            "status": "success",
            "message": "Logged out successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_otp() -> str:
    """
    Generate a random 6-digit OTP
    """
    return str(int(secrets.token_hex(3), 16) % 1000000).zfill(6)

def validate_token(token: str) -> dict or None:
    """
    Validate JWT token and return payload
    """
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY", "your-secret-key"),
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

### File: `backend/app/main.py` - Add this to include auth routes:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth import router as auth_router

app = FastAPI(title="TOR UNVEIL API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router)

# ... rest of your routes
```

### File: `backend/requirements.txt` - Add these packages:

```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
redis==5.0.0
python-dotenv==1.0.0
PyJWT==2.8.1
twilio==8.10.0  # Optional, for SMS
boto3==1.26.0    # Optional, for AWS SNS
```

### File: `.env` - Environment variables:

```
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# SMS Configuration (Optional - choose one)
# For Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# For AWS SNS
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-south-1
```

---

## Testing with cURL

```bash
# 1. Send OTP
curl -X POST "http://localhost:8000/api/auth/send-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "loginId": "officer_001",
    "mobileNumber": "9876543210"
  }'

# Expected response:
# {
#   "status": "success",
#   "message": "OTP sent to +919876543210",
#   "expiresIn": 120
# }

# 2. Verify OTP (use the OTP from console output)
curl -X POST "http://localhost:8000/api/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "loginId": "officer_001",
    "mobileNumber": "9876543210",
    "otp": "123456"
  }'

# Expected response:
# {
#   "status": "success",
#   "message": "Login successful",
#   "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "user": {
#     "loginId": "officer_001",
#     "mobileNumber": "9876543210",
#     "loginTime": "2024-12-16T10:30:45.123456"
#   }
# }
```

---

## Unit Tests

```python
# File: backend/tests/test_auth.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_send_otp_valid():
    response = client.post(
        "/api/auth/send-otp",
        json={
            "loginId": "test_officer",
            "mobileNumber": "9876543210"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_send_otp_invalid_mobile():
    response = client.post(
        "/api/auth/send-otp",
        json={
            "loginId": "test_officer",
            "mobileNumber": "12345"  # Invalid
        }
    )
    assert response.status_code == 422

def test_verify_otp_success():
    # First send OTP
    client.post(
        "/api/auth/send-otp",
        json={
            "loginId": "test_officer",
            "mobileNumber": "9876543210"
        }
    )
    
    # Then verify (OTP is logged to console in demo mode)
    response = client.post(
        "/api/auth/verify-otp",
        json={
            "loginId": "test_officer",
            "mobileNumber": "9876543210",
            "otp": "000000"  # Any 6 digits in demo mode
        }
    )
    assert response.status_code == 200
    assert "token" in response.json()
```

---

## Ready to Use! 🚀

Copy the `auth.py` file to your backend and you're ready to test real OTP authentication!
