"""
Authentication module for Police Officer Login with OTP
Uses Twilio Free Tier for SMS and MongoDB for storage
"""

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
import secrets
import re
import os
from dotenv import load_dotenv
import jwt
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import logging

load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# MONGODB CONNECTION
# ============================================================================

# Global variables for lazy loading
_mongo_client = None
_db = None
_otp_collection = None
_user_collection = None

def get_mongodb_client():
    """Initialize MongoDB connection (lazy loaded)"""
    global _mongo_client, _db, _otp_collection, _user_collection
    
    if _mongo_client is not None:
        return _mongo_client
    
    try:
        mongodb_url = os.getenv('MONGODB_URL', 'mongodb://torunveil-mongo:27017/tor_unveil')
        _mongo_client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        _mongo_client.admin.command('ping')
        
        _db = _mongo_client.get_database()
        _otp_collection = _db.get_collection('otp_records')
        _user_collection = _db.get_collection('users')
        
        # Create indexes for better performance
        _otp_collection.create_index([("expires_at", 1)], expireAfterSeconds=0)
        _otp_collection.create_index([("login_id", 1), ("mobile_number", 1)])
        
        logger.info("MongoDB connected successfully")
        return _mongo_client
    except ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise

def get_db():
    """Get database instance (lazy loaded)"""
    if _db is None:
        get_mongodb_client()
    return _db

def get_otp_collection():
    """Get OTP collection (lazy loaded)"""
    if _otp_collection is None:
        get_mongodb_client()
    return _otp_collection

def get_user_collection():
    """Get user collection (lazy loaded)"""
    if _user_collection is None:
        get_mongodb_client()
    return _user_collection

# ============================================================================
# TWILIO CONFIGURATION (FREE TIER)
# ============================================================================

def get_twilio_client():
    """Initialize Twilio client with free tier credentials"""
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            logger.warning("Twilio credentials not configured. SMS will be logged to console.")
            return None
        
        return Client(account_sid, auth_token)
    except ImportError:
        logger.error("Twilio not installed. Install with: pip install twilio")
        return None

twilio_client = get_twilio_client()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SendOTPRequest(BaseModel):
    """Request model for sending OTP"""
    loginId: str
    mobileNumber: str
    
    @validator('loginId')
    def validate_login_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Login ID cannot be empty')
        if len(v) < 3:
            raise ValueError('Login ID must be at least 3 characters')
        return v.strip()
    
    @validator('mobileNumber')
    def validate_mobile(cls, v):
        # Support both Indian numbers (10 digits) and international format
        if len(v) == 10:
            if not re.match(r'^[6-9]\d{9}$', v):
                raise ValueError('Invalid Indian mobile number')
        elif len(v) == 12 and v.startswith('91'):
            # International format like 919876543210
            if not re.match(r'^91[6-9]\d{9}$', v):
                raise ValueError('Invalid Indian mobile number')
        else:
            raise ValueError('Mobile must be 10 digits or +91 format')
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
# OTP FUNCTIONS
# ============================================================================

def generate_otp() -> str:
    """Generate a random 6-digit OTP"""
    otp_length = int(os.getenv('OTP_LENGTH', 6))
    return str(int(secrets.token_hex(3), 16) % (10 ** otp_length)).zfill(otp_length)

def store_otp(login_id: str, mobile: str, otp: str) -> bool:
    """Store OTP in MongoDB with expiry"""
    try:
        expiry_seconds = int(os.getenv('OTP_EXPIRY_SECONDS', 120))
        
        otp_record = {
            'login_id': login_id,
            'mobile_number': mobile,
            'otp_code': otp,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(seconds=expiry_seconds),
            'attempts': 0,
            'verified': False
        }
        
        # Delete old OTP for this user first
        get_otp_collection().delete_many({
            'login_id': login_id,
            'mobile_number': mobile
        })
        
        # Insert new OTP
        result = get_otp_collection().insert_one(otp_record)
        logger.info(f"OTP stored for {login_id}: {otp}")
        return result.inserted_id is not None
    
    except Exception as e:
        logger.error(f"Error storing OTP: {str(e)}")
        return False

def get_otp_record(login_id: str, mobile: str):
    """Retrieve OTP record from MongoDB"""
    try:
        record = get_otp_collection().find_one({
            'login_id': login_id,
            'mobile_number': mobile,
            'expires_at': {'$gt': datetime.utcnow()}  # Not expired
        })
        return record
    except Exception as e:
        logger.error(f"Error retrieving OTP: {str(e)}")
        return None

def delete_otp(login_id: str, mobile: str):
    """Delete OTP after successful verification"""
    try:
        get_otp_collection().delete_one({
            'login_id': login_id,
            'mobile_number': mobile
        })
    except Exception as e:
        logger.error(f"Error deleting OTP: {str(e)}")

def increment_attempts(login_id: str, mobile: str):
    """Increment verification attempts"""
    try:
        get_otp_collection().update_one(
            {
                'login_id': login_id,
                'mobile_number': mobile
            },
            {'$inc': {'attempts': 1}}
        )
    except Exception as e:
        logger.error(f"Error incrementing attempts: {str(e)}")

# ============================================================================
# SMS FUNCTIONS
# ============================================================================

def send_sms_otp(mobile_number: str, otp_code: str) -> dict:
    """
    Send OTP via SMS using Twilio Free Tier
    Free tier includes:
    - 1000 free SMS credits per month
    - Use Twilio sandbox for unlimited testing
    """
    
    # Format phone number for Twilio
    if len(mobile_number) == 10:
        phone = f"+91{mobile_number}"
    else:
        phone = f"+{mobile_number}" if not mobile_number.startswith('+') else mobile_number
    
    try:
        # Check if we have Twilio configured
        if not twilio_client:
            logger.info(f"SMS would be sent to {phone} with OTP: {otp_code}")
            return {
                "status": "success",
                "message": "OTP logged (Twilio not configured)",
                "phone": phone
            }
        
        # Send via Twilio
        twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        message = twilio_client.messages.create(
            body=f"Tamil Nadu Police - TOR UNVEIL\nYour OTP: {otp_code}\nValid for 2 minutes\nDo not share with anyone.",
            from_=twilio_phone,
            to=phone
        )
        
        logger.info(f"SMS sent successfully to {phone}. Message SID: {message.sid}")
        return {
            "status": "success",
            "message_id": message.sid,
            "phone": phone
        }
    
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone}: {str(e)}")
        # In demo mode, still allow login
        if os.getenv('ENVIRONMENT') == 'development':
            logger.info(f"Development mode: OTP {otp_code} would be sent to {phone}")
            return {
                "status": "success",
                "message": "OTP logged to console (development mode)",
                "phone": phone
            }
        return {
            "status": "error",
            "message": str(e)
        }

# ============================================================================
# API ROUTER
# ============================================================================

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(request: SendOTPRequest, client_request: Request):
    """
    Send OTP to police officer's mobile number via SMS
    
    Free Tier Benefits:
    - 1000 SMS credits/month (Twilio)
    - Unlimited sandbox testing
    - Works with Indian numbers (+91)
    
    Args:
        request: Contains loginId and mobileNumber
        client_request: FastAPI Request object
    
    Returns:
        OTPResponse with status and expiry time
    """
    
    try:
        # Rate limiting check
        client_ip = client_request.client.host
        rate_limit_key = f"rate_limit:{client_ip}"
        
        # Check if user has exceeded rate limit
        rate_limit_doc = get_otp_collection().find_one(
            {'_id': rate_limit_key}
        )
        
        if rate_limit_doc:
            if rate_limit_doc.get('count', 0) >= int(os.getenv('OTP_RATE_LIMIT_COUNT', 5)):
                if datetime.utcnow() < rate_limit_doc.get('expires_at', datetime.utcnow()):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many OTP requests. Please wait a minute."
                    )
        
        # Validate input
        if not request.loginId.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Login ID is required"
            )
        
        # Generate OTP
        otp_code = generate_otp()
        logger.info(f"Generated OTP for {request.loginId}: {otp_code}")
        
        # Store OTP in MongoDB
        if not store_otp(request.loginId, request.mobileNumber, otp_code):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store OTP"
            )
        
        # Send SMS
        sms_result = send_sms_otp(request.mobileNumber, otp_code)
        
        if sms_result.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP. Please try again."
            )
        
        return OTPResponse(
            status="success",
            message=f"OTP sent to +91{request.mobileNumber}",
            expiresIn=int(os.getenv('OTP_EXPIRY_SECONDS', 120))
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.post("/verify-otp", response_model=LoginResponse)
async def verify_otp(request: VerifyOTPRequest):
    """
    Verify OTP and return JWT authentication token
    
    Args:
        request: Contains loginId, mobileNumber, and otp
    
    Returns:
        LoginResponse with JWT token and user info
    """
    
    try:
        # Get OTP record
        otp_record = get_otp_record(request.loginId, request.mobileNumber)
        
        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OTP expired or not found. Please request a new OTP."
            )
        
        # Check attempt limit
        max_attempts = int(os.getenv('OTP_MAX_ATTEMPTS', 3))
        if otp_record.get('attempts', 0) >= max_attempts:
            delete_otp(request.loginId, request.mobileNumber)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed attempts. Please request a new OTP."
            )
        
        # Verify OTP
        if otp_record.get('otp_code') != request.otp:
            increment_attempts(request.loginId, request.mobileNumber)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OTP. Please try again."
            )
        
        # OTP verified successfully
        delete_otp(request.loginId, request.mobileNumber)
        
        # Generate JWT token
        jwt_secret = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
        jwt_expire_hours = int(os.getenv('JWT_EXPIRE_HOURS', 8))
        
        payload = {
            "loginId": request.loginId,
            "mobileNumber": request.mobileNumber,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=jwt_expire_hours)
        }
        
        token = jwt.encode(
            payload,
            jwt_secret,
            algorithm=os.getenv('JWT_ALGORITHM', 'HS256')
        )
        
        # Log successful login
        logger.info(f"Successful login for {request.loginId}")
        
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
        logger.error(f"Error verifying OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification error: {str(e)}"
        )

@router.post("/logout")
async def logout():
    """Logout user"""
    try:
        return {
            "status": "success",
            "message": "Logged out successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check MongoDB connection
        get_db().command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
