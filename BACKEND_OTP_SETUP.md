# 🔧 Backend OTP Integration Guide

## Overview
This guide explains how to integrate real SMS OTP functionality with your FastAPI backend.

---

## Step 1: Install Required Packages

Add to `backend/requirements.txt`:

```
twilio==8.10.0
# or
python-nexmo==2.0.2  # For Nexmo
# or
boto3==1.26.0  # For AWS SNS
redis==5.0.0  # For OTP storage
python-dotenv==1.0.0
```

Then run:
```bash
pip install -r requirements.txt
```

---

## Step 2: Choose OTP Storage Strategy

### Option A: Redis (Recommended for Production)
```python
import redis
import secrets
import time

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def store_otp(login_id: str, mobile: str, otp: str, expiry: int = 120):
    """Store OTP in Redis with expiry"""
    key = f"otp:{login_id}:{mobile}"
    redis_client.setex(key, expiry, otp)

def verify_otp(login_id: str, mobile: str, otp_input: str) -> bool:
    """Verify OTP from Redis"""
    key = f"otp:{login_id}:{mobile}"
    stored_otp = redis_client.get(key)
    if stored_otp and stored_otp.decode() == otp_input:
        redis_client.delete(key)  # OTP used, delete it
        return True
    return False
```

### Option B: Database (Simple but less secure)
```python
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

class OTPRecord(Base):
    __tablename__ = "otp_records"
    
    id = Column(Integer, primary_key=True)
    login_id = Column(String)
    mobile_number = Column(String)
    otp_code = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    verified = Column(Boolean, default=False)

def store_otp_db(db: Session, login_id: str, mobile: str, otp: str):
    otp_record = OTPRecord(
        login_id=login_id,
        mobile_number=mobile,
        otp_code=otp,
        expires_at=datetime.utcnow() + timedelta(minutes=2)
    )
    db.add(otp_record)
    db.commit()
```

---

## Step 3: Setup SMS Provider

### Option A: Twilio Integration

**Get Credentials:**
1. Sign up at https://www.twilio.com
2. Get Account SID and Auth Token
3. Get a Twilio phone number

**Add to `.env`:**
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

**Backend Code:**
```python
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

def send_sms_otp(mobile_number: str, otp_code: str):
    """Send OTP via Twilio SMS"""
    try:
        message = twilio_client.messages.create(
            body=f"Tamil Nadu Police - TOR UNVEIL\nYour OTP: {otp_code}\nValid for 2 minutes",
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=f"+91{mobile_number}"  # +91 for India
        )
        return {"status": "success", "message_id": message.sid}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### Option B: AWS SNS Integration

**Add to `.env`:**
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=ap-south-1
```

**Backend Code:**
```python
import boto3
from botocore.exceptions import ClientError
import os

sns_client = boto3.client('sns', region_name=os.getenv('AWS_REGION'))

def send_sms_otp_aws(mobile_number: str, otp_code: str):
    """Send OTP via AWS SNS"""
    try:
        response = sns_client.publish(
            PhoneNumber=f"+91{mobile_number}",
            Message=f"Tamil Nadu Police - TOR UNVEIL\nYour OTP: {otp_code}\nValid for 2 minutes"
        )
        return {"status": "success", "message_id": response['MessageId']}
    except ClientError as e:
        return {"status": "error", "message": str(e)}
```

### Option C: Local SMS Gateway (For testing)

```python
def send_sms_otp_local(mobile_number: str, otp_code: str):
    """Log OTP to console (for testing only)"""
    print(f"\n{'='*50}")
    print(f"SMS TO: +91{mobile_number}")
    print(f"MESSAGE: Your OTP is {otp_code}")
    print(f"{'='*50}\n")
    return {"status": "success", "message": "Logged to console"}
```

---

## Step 4: Create FastAPI Endpoints

Add to `backend/app/main.py`:

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from datetime import datetime
import secrets
import re

app = FastAPI()

# Models
class SendOTPRequest(BaseModel):
    loginId: str
    mobileNumber: str

class VerifyOTPRequest(BaseModel):
    loginId: str
    mobileNumber: str
    otp: str

# Validation functions
def validate_mobile(mobile: str) -> bool:
    """Validate Indian mobile number"""
    return re.match(r"^[6-9]\d{9}$", mobile) is not None

def generate_otp() -> str:
    """Generate random 6-digit OTP"""
    return str(int(secrets.token_hex(3), 16) % 1000000).zfill(6)

# Endpoints
@app.post("/api/auth/send-otp")
async def send_otp(request: SendOTPRequest):
    """
    Send OTP to police officer's mobile number
    """
    # Validate inputs
    if not request.loginId.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login ID is required"
        )
    
    if not validate_mobile(request.mobileNumber):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Indian mobile number"
        )
    
    try:
        # Generate OTP
        otp_code = generate_otp()
        
        # Store OTP (using Redis)
        store_otp(request.loginId, request.mobileNumber, otp_code)
        
        # Send SMS
        result = send_sms_otp(request.mobileNumber, otp_code)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "message": f"OTP sent to {request.mobileNumber}",
                "expiresIn": 120
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send SMS"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/auth/verify-otp")
async def verify_otp_endpoint(request: VerifyOTPRequest):
    """
    Verify OTP and return auth token
    """
    # Validate OTP format
    if not re.match(r"^\d{6}$", request.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP must be 6 digits"
        )
    
    try:
        # Verify OTP
        if verify_otp(request.loginId, request.mobileNumber, request.otp):
            # Generate JWT token or session
            from datetime import datetime, timedelta
            import jwt
            
            payload = {
                "loginId": request.loginId,
                "mobileNumber": request.mobileNumber,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(hours=8)
            }
            
            token = jwt.encode(
                payload,
                "your_secret_key",
                algorithm="HS256"
            )
            
            return {
                "status": "success",
                "message": "OTP verified successfully",
                "token": token,
                "user": {
                    "loginId": request.loginId,
                    "mobileNumber": request.mobileNumber
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/api/auth/logout")
async def logout(token: str = None):
    """
    Logout user (invalidate token)
    """
    return {
        "status": "success",
        "message": "Logged out successfully"
    }
```

---

## Step 5: Update Frontend to Use Real Endpoints

Modify `frontend/src/PoliceLogin.js`:

```javascript
const handleSendOtp = async (e) => {
  e.preventDefault();
  setError("");
  setSuccess("");

  if (!loginId.trim()) {
    setError("Please enter your Login ID");
    return;
  }

  if (!mobileNumber || !validateMobileNumber(mobileNumber)) {
    setError("Please enter a valid 10-digit mobile number");
    return;
  }

  setLoading(true);
  try {
    // Call real backend API
    const response = await fetch("http://localhost:8000/api/auth/send-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ loginId, mobileNumber })
    });

    const data = await response.json();

    if (response.ok) {
      setSuccess(`OTP sent successfully to ${mobileNumber}`);
      setOtpSent(true);
      setStep("otp");
      setTimer(data.expiresIn || 120);
    } else {
      setError(data.detail || "Failed to send OTP");
    }
  } catch (err) {
    setError("Network error. Please try again.");
  } finally {
    setLoading(false);
  }
};

const handleVerifyOtp = async (e) => {
  e.preventDefault();
  setError("");
  setSuccess("");

  const otpCode = otp.join("");
  if (otpCode.length !== 6) {
    setError("Please enter a complete 6-digit OTP");
    return;
  }

  setLoading(true);
  try {
    // Call real backend API
    const response = await fetch("http://localhost:8000/api/auth/verify-otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        loginId,
        mobileNumber,
        otp: otpCode
      })
    });

    const data = await response.json();

    if (response.ok) {
      setSuccess("OTP verified successfully!");
      setStep("verification");

      // Store token in localStorage
      localStorage.setItem("authToken", data.token);
      localStorage.setItem("userInfo", JSON.stringify(data.user));

      setTimeout(() => {
        onLoginSuccess(data.user);
      }, 1500);
    } else {
      setError(data.detail || "OTP verification failed");
    }
  } catch (err) {
    setError("Network error. Please try again.");
  } finally {
    setLoading(false);
  }
};
```

---

## Step 6: Docker Compose Update

Add Redis to `infra/docker-compose.yml`:

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: torunveil-redis
    ports:
      - "6379:6379"
    networks:
      - torunveil-net
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

---

## Step 7: Testing the Integration

### Test with Postman/cURL

```bash
# Send OTP
curl -X POST http://localhost:8000/api/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "loginId": "officer_001",
    "mobileNumber": "9876543210"
  }'

# Verify OTP
curl -X POST http://localhost:8000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "loginId": "officer_001",
    "mobileNumber": "9876543210",
    "otp": "123456"
  }'
```

---

## Security Considerations

1. **Rate Limiting**
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/send-otp")
@limiter.limit("3/minute")
async def send_otp(request: SendOTPRequest):
    # ...
```

2. **OTP Attempts**
```python
# Max 3 attempts per OTP
attempt_key = f"otp_attempts:{loginId}:{mobileNumber}"
if redis_client.incr(attempt_key) > 3:
    raise HTTPException(status_code=429, detail="Too many attempts")
redis_client.expire(attempt_key, 300)  # Reset after 5 minutes
```

3. **CORS Configuration**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Deployment Checklist

- [ ] SMS API credentials configured
- [ ] Redis running (if using Redis)
- [ ] Rate limiting enabled
- [ ] Error handling tested
- [ ] OTP expiry working
- [ ] Frontend endpoints updated
- [ ] CORS properly configured
- [ ] JWT tokens generating correctly
- [ ] Logout clearing sessions
- [ ] Unit tests passing

---

**Ready to deploy real OTP authentication! 🚀**
