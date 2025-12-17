# 🚀 FREE TIER OTP SETUP GUIDE

## Step 1: Sign Up for Twilio Free Tier (5 minutes)

### What you get FREE:
- **$15 trial credit** (enough for ~750 SMS)
- Unlimited API calls
- Full access to all Twilio features
- No credit card needed initially (for trial)

### How to Sign Up:

1. **Visit**: https://www.twilio.com/try-twilio

2. **Complete Registration**:
   - Email address
   - Create password
   - Verify phone number (you'll receive code via SMS)

3. **Get Your Credentials**:
   After login, go to: https://console.twilio.com/
   
   You'll see:
   ```
   Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Auth Token: (click to reveal)
   ```

4. **Get a Phone Number**:
   - Click "Get a Trial Number"
   - Accept the suggested number or search for one
   - You get ONE free number
   - Example: +1 (415) 555-0132

---

## Step 2: Setup Django/FastAPI Backend (10 minutes)

### Option A: Using MongoDB (Recommended for Free Tier)

MongoDB has a generous free tier:
- 512 MB storage
- Shared cluster
- 3 nodes
- Suitable for testing and small deployments

**Already included in our `auth.py`!**

### Option B: Using SQLite (Simplest)

Already configured for local development.

---

## Step 3: Configure Your Backend

### 1. Copy .env.example to .env

```bash
cd /home/subha/Downloads/tor-unveil/backend
cp .env.example .env
```

### 2. Edit .env with Your Credentials

```bash
nano .env
# or
vim .env
```

### 3. Fill in Twilio Details

```env
# Get from https://console.twilio.com/
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+14155550132  # Your Twilio number

# For testing (use your own verified phone)
TWILIO_TEST_MOBILE_NUMBER=+919876543210
```

### 4. Keep Other Settings

```env
MONGODB_URL=mongodb://localhost:27017/tor_unveil
JWT_SECRET_KEY=your-secret-key-change-this-in-production
ENVIRONMENT=development
```

---

## Step 4: Install Dependencies

```bash
cd /home/subha/Downloads/tor-unveil/backend
pip install -r requirements.txt
```

**Packages added:**
- `twilio==8.10.0` - SMS API
- `python-dotenv==1.0.0` - Environment variables
- `PyJWT==2.8.1` - JWT tokens
- `python-multipart==0.0.6` - Form data handling

---

## Step 5: Test SMS Delivery (5 minutes)

### Test Script: Send SMS via Twilio

```python
# Create file: backend/test_twilio.py

from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Twilio
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
test_phone = os.getenv('TWILIO_TEST_MOBILE_NUMBER')

client = Client(account_sid, auth_token)

# Send test SMS
message = client.messages.create(
    body="Test message from TOR UNVEIL OTP System",
    from_=twilio_phone,
    to=test_phone
)

print(f"SMS sent! Message SID: {message.sid}")
print(f"Status: {message.status}")
```

### Run Test:

```bash
cd backend
python test_twilio.py
```

**Expected Output:**
```
SMS sent! Message SID: SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Status: queued
```

**You should receive SMS on your phone!**

---

## Step 6: Deploy Backend with OTP

### 1. Rebuild Docker Containers

```bash
cd /home/subha/Downloads/tor-unveil/infra
sudo docker compose down
sudo docker compose up --build -d
```

### 2. Verify Services Running

```bash
sudo docker compose ps
```

**Expected:**
```
NAME                IMAGE               STATUS
torunveil-backend   infra-backend       Up (should see no errors)
torunveil-frontend  infra-frontend      Up
torunveil-mongo     mongo:7.0           Up
```

### 3. Check Backend Logs

```bash
sudo docker compose logs backend
```

**Look for:**
```
Uvicorn running on http://0.0.0.0:8000
Application startup complete
```

---

## Step 7: Test Full Login Flow

### 1. Update Frontend API (Already Done! ✓)

The frontend already calls:
- `POST /api/auth/send-otp`
- `POST /api/auth/verify-otp`

### 2. Open Application

```
http://localhost:3000
```

### 3. Test Login

```
Login ID: demo_officer
Mobile: 919876543210  (Your verified phone number)
Click "Send OTP"
```

### 4. Check Your Phone

**You should receive:**
```
Tamil Nadu Police - TOR UNVEIL
Your OTP: 123456
Valid for 2 minutes
Do not share with anyone.
```

### 5. Enter OTP and Login

```
Enter OTP: 123456
Click "Verify OTP"
✅ Success → Dashboard Access
```

---

## Troubleshooting Guide

### Issue 1: "Twilio credentials not found"

**Solution:**
```bash
# Check .env file exists
cat backend/.env

# Verify credentials:
echo $TWILIO_ACCOUNT_SID
echo $TWILIO_AUTH_TOKEN
echo $TWILIO_PHONE_NUMBER
```

### Issue 2: "Failed to send SMS"

**Check:**
1. ✅ Twilio credentials correct
2. ✅ Phone number verified in Twilio console
3. ✅ Trial credit not expired
4. ✅ Phone number format: +919876543210 (with +91)

### Issue 3: "OTP not received"

**Check:**
1. ✅ Your phone number is verified in Twilio
2. ✅ Correct phone number in .env
3. ✅ Check SMS logs in Twilio console
4. ✅ Check backend logs: `docker compose logs backend`

### Issue 4: MongoDB Connection Error

**Solution:**
```bash
# Make sure MongoDB is running
sudo docker compose ps | grep mongo

# If not running:
sudo docker compose up -d mongo

# Test connection:
mongo mongodb://localhost:27017
```

---

## API Endpoints Available

### 1. Send OTP

```bash
curl -X POST http://localhost:8000/api/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "loginId": "officer_001",
    "mobileNumber": "9876543210"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "OTP sent to +919876543210",
  "expiresIn": 120
}
```

### 2. Verify OTP

```bash
curl -X POST http://localhost:8000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "loginId": "officer_001",
    "mobileNumber": "9876543210",
    "otp": "123456"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "loginId": "officer_001",
    "mobileNumber": "9876543210",
    "loginTime": "2024-12-16T10:30:45"
  }
}
```

### 3. Health Check

```bash
curl http://localhost:8000/api/auth/health
```

---

## Free Tier Limitations & Solutions

| Limitation | Free Tier | Solution |
|-----------|----------|----------|
| **SMS Credits** | $15 (~750 SMS) | Enough for development/testing |
| **Numbers** | 1 Twilio number | Get more by upgrading |
| **API Calls** | Unlimited | No limits on trial |
| **Storage** | No limit | MongoDB free tier: 512 MB |
| **Support** | Community | Paid support available |

---

## Cost Breakdown (Free Tier)

### Twilio
- **Initial**: $0 (sign up free)
- **Trial Credit**: $15
- **After Trial**: $0.0075 per SMS (can pay as you go)
- **1000 SMS/month would cost**: $7.50

### MongoDB Free Tier
- **Initial**: $0
- **Ongoing**: $0 (free tier)
- **Storage**: 512 MB (enough for millions of OTP records)
- **Upgrade**: $57/month for 2GB

### Total Monthly Cost (Free)
- **Development**: $0
- **Small Production**: $7.50 (Twilio only)
- **Large Production**: $65+ (with upgrades)

---

## Next Steps

1. ✅ Sign up for Twilio free tier
2. ✅ Get credentials and phone number
3. ✅ Create .env file with credentials
4. ✅ Install Python dependencies
5. ✅ Rebuild Docker containers
6. ✅ Test SMS delivery
7. ✅ Test full login flow
8. ✅ Deploy to production

---

## Production Deployment Checklist

- [ ] Upgrade Twilio account (add payment method)
- [ ] Get more Twilio phone numbers (if needed)
- [ ] Setup MongoDB production cluster
- [ ] Configure HTTPS/SSL
- [ ] Setup monitoring & alerts
- [ ] Add rate limiting
- [ ] Setup audit logging
- [ ] Backup database regularly
- [ ] Monitor SMS costs
- [ ] Security audit

---

## Support & Resources

### Twilio Documentation
- https://www.twilio.com/docs/sms
- https://www.twilio.com/docs/libraries/python

### Our Backend Code
- `backend/app/auth.py` - All OTP logic
- `backend/.env.example` - Configuration template
- `backend/requirements.txt` - All dependencies

### GitHub Repository
- `subhashree-18/TOR`
- All code and documentation included

---

**✅ Ready to Send Real SMS OTP! 🚀**
