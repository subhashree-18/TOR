# 🔐 TOR UNVEIL - Police Officer Login Guide

## 📱 How to Login with OTP

### **Step 1: Access the Login Page**
- Open your browser and go to: **http://localhost:3000**
- You will see the **Police Officer Login** page with a professional blue government theme

---

## **Step 2: Enter Your Credentials**

### Screen 1 - Login Credentials
The login page will show:
- 🆔 **Login ID** field
- 📱 **Mobile Number** field (with +91 country code)

**What to enter:**
```
Login ID: Any username (e.g., "PO12345", "officer_name", etc.)
Mobile Number: 10-digit number (e.g., 9876543210)
```

**Validation Rules:**
- ✅ Login ID must not be empty
- ✅ Mobile number must be exactly 10 digits
- ✅ Only numbers in mobile field

**Example Input:**
```
Login ID: officer_tnpd_123
Mobile:   9876543210
```

Click **"Send OTP"** button

---

## **Step 3: OTP Delivery (Current Implementation)**

### ⚠️ IMPORTANT - Current Status:

**In the current demo/development version:**
- OTP is **NOT actually sent to the mobile number**
- This is because backend API for SMS is not configured yet

### What happens currently:
1. You see message: "OTP sent successfully to 9876543210" ✅
2. You proceed to OTP entry screen
3. **Use any 6-digit number** (e.g., `000000` or `123456`)
4. System will accept it and log you in

---

## **Step 4: Enter OTP**

### Screen 2 - OTP Verification
The page shows:
- 6 input boxes for OTP digits
- ⏱️ **120-second countdown timer**
- "OTP expires in 120s" message

**How to enter OTP:**

**In Current Demo Mode:**
```
Type any 6 digits, for example:
[1][2][3][4][5][6]

Or you can use:
[0][0][0][0][0][0]
[9][9][9][9][9][9]
```

**Features:**
- ✅ Auto-focus to next box as you type
- ✅ Backspace moves to previous box
- ✅ Only accepts numbers
- ✅ Can resend OTP if needed (button appears)

Click **"Verify OTP"** button

---

## **Step 5: Successfully Logged In**

### Screen 3 - Verification Success
- ✅ Green checkmark animation
- "Login Successful" message
- "Redirecting to dashboard..." 

**Redirects to Dashboard after 1.5 seconds**

---

## 📋 Complete Login Flow Example

```
1. OPEN: http://localhost:3000
   ↓
2. ENTER:
   - Login ID: "subha_officer"
   - Mobile: "9876543210"
   ↓
3. CLICK: "Send OTP"
   ↓
4. SEE: "OTP sent successfully to 9876543210"
   ↓
5. ENTER OTP (any 6 digits): "123456"
   ↓
6. CLICK: "Verify OTP"
   ↓
7. SUCCESS: Redirects to Dashboard
   ↓
8. YOU SEE: 
   - Top bar with "Logged in as: subha_officer"
   - Logout button
   - Full dashboard access
```

---

## 🔄 How OTP Will Work in Production

When backend SMS API is configured:

1. **Send OTP Request**
   - Backend receives: Login ID + Mobile Number
   - Backend generates random 6-digit OTP
   - Backend calls SMS API (Twilio, AWS SNS, etc.)
   - OTP sent to actual phone number

2. **User receives SMS**
   ```
   Tamil Nadu Police - TOR UNVEIL
   Your OTP: 456789
   Valid for 2 minutes
   ```

3. **User enters OTP**
   - Backend validates OTP matches
   - If correct → Login success
   - If wrong → Show error

---

## 🔐 Security Features

### Current Implementation:
- ✅ OTP expires after 120 seconds (2 minutes)
- ✅ Resend OTP button available
- ✅ Back button to return to login
- ✅ Error messages for invalid input
- ✅ Loading states during processing

### To Add in Production:
- [ ] Rate limiting (max 3 attempts)
- [ ] OTP must be stored in backend database
- [ ] SMS API integration (Twilio/AWS)
- [ ] IP-based fraud detection
- [ ] Session timeout after 30 minutes
- [ ] Device fingerprinting
- [ ] Login activity logging

---

## 🛠️ Backend API Setup Required (Future)

To make real OTP work, you need to create backend endpoints:

### **Endpoint 1: Send OTP**
```
POST /api/auth/send-otp

Request:
{
  "loginId": "officer_name",
  "mobileNumber": "9876543210"
}

Response:
{
  "status": "success",
  "message": "OTP sent successfully",
  "expiresIn": 120
}
```

### **Endpoint 2: Verify OTP**
```
POST /api/auth/verify-otp

Request:
{
  "loginId": "officer_name",
  "mobileNumber": "9876543210",
  "otp": "456789"
}

Response:
{
  "status": "success",
  "token": "jwt_token_here",
  "user": {
    "loginId": "officer_name",
    "mobileNumber": "9876543210"
  }
}
```

---

## 💡 Testing the Login

### Test Cases to Try:

| Test Case | Input | Expected Result |
|-----------|-------|-----------------|
| Valid login | ID: "test", Mobile: "9876543210" | Proceeds to OTP screen |
| Empty Login ID | ID: "", Mobile: "9876543210" | Error: "Please enter your Login ID" |
| Invalid mobile (too short) | ID: "test", Mobile: "98765432" | Error: "Please enter a valid 10-digit..." |
| Invalid mobile (letters) | ID: "test", Mobile: "98abc54321" | Numbers only, auto-filtered |
| Valid OTP entry | OTP: "123456" | Login success, redirects to dashboard |
| OTP expiration | Wait 120+ seconds, then enter OTP | Error: "OTP expired" |
| Resend OTP | Click "Resend OTP" after 30s | New OTP timer starts |

---

## 🎯 Quick Start for Testing

### Option 1: Test with Demo Data
```
Login ID: demo_officer
Mobile: 9999999999
OTP: 000000 (any 6 digits)
```

### Option 2: Test with Your Details
```
Login ID: Your choice (e.g., "officer_001")
Mobile: 10-digit number
OTP: Any 6 digits
```

---

## ⏱️ Timer Information

- **OTP Validity**: 120 seconds (2 minutes)
- **Timer Display**: Shows countdown in red when < 30 seconds
- **After Expiration**: "OTP expired" message appears
- **Resend OTP**: Click button to get new OTP with fresh 120s timer

---

## 🚪 Logout

After successful login:
- Top-right shows: "Logged in as: [your_login_id]"
- Click **"Logout"** button to return to login page
- Session clears, must log in again

---

## ❓ FAQs

**Q: Why isn't OTP being sent to my phone?**
A: Backend SMS API is not configured yet. Use any 6 digits to test.

**Q: Can I use the same Login ID multiple times?**
A: Yes, the system doesn't store or validate Login IDs yet.

**Q: What happens if I close the browser during login?**
A: Session is lost, you must start login again from the beginning.

**Q: How long do I stay logged in?**
A: Currently indefinitely (no timeout). In production, add 30-minute session timeout.

**Q: Can I have multiple devices logged in?**
A: Yes, currently no device limit. In production, limit to 1-2 devices.

---

## 📞 Next Steps

To enable real SMS OTP delivery:

1. **Choose SMS Provider**:
   - Twilio (Recommended)
   - AWS SNS
   - Nexmo
   - Local SMS gateway

2. **Backend Configuration**:
   - Add SMS API credentials
   - Create `/api/auth/send-otp` endpoint
   - Create `/api/auth/verify-otp` endpoint
   - Add OTP storage (Redis/Database)
   - Add rate limiting

3. **Frontend Updates**:
   - Update PoliceLogin.js to call real endpoints
   - Add real error handling
   - Store JWT token from backend
   - Add persistent login state

4. **Testing**:
   - Test with real phone numbers
   - Test with various edge cases
   - Monitor SMS delivery logs

---

**🎉 You're all set! Start by visiting http://localhost:3000**
