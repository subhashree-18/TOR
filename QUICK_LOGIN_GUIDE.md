# 🎯 Quick Login Reference - Visual Guide

## Current Status: DEMO MODE ✅

OTP is **simulated** for testing. Use any 6 digits to login.

---

## 📱 STEP-BY-STEP LOGIN FLOW

```
┌─────────────────────────────────────────────────────────────┐
│                     STEP 1: LOGIN PAGE                      │
│                   http://localhost:3000                     │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ENTER LOGIN ID        ENTER MOBILE
         (e.g., "demo_01")      (e.g., "9876543210")
                    │                   │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼──────────┐
                    │   CLICK "SEND OTP" │
                    └────────┬───────────┘
                             │
                ┌────────────▼────────────┐
                │ OTP "SENT" (simulated)  │
                │ Success message shown   │
                └────────────┬────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│              STEP 2: OTP VERIFICATION PAGE                  │
└─────────────────────────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ ENTER 6 DIGITS  │
                    │ [_][_][_][_][_][_]  │
                    └────────┬────────┘
                             │
              ┌──────────────▼──────────────┐
              │   ⏱️ TIMER: 120 seconds    │
              │   (OTP expires after this)  │
              └──────────────┬──────────────┘
                             │
                   ┌─────────▼─────────┐
                   │ CLICK "VERIFY OTP"│
                   └────────┬──────────┘
                            │
         ┌──────────────────▼──────────────────┐
         │   ✅ VERIFICATION SUCCESSFUL        │
         │   "Redirecting to dashboard..."     │
         └──────────────────┬──────────────────┘
                            │
┌───────────────────────────────────────────────────────────┐
│             STEP 3: DASHBOARD - LOGGED IN                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 🔐 Tamil Nadu TOR UNVEIL                Logout ➤    │ │
│  │ Logged in as: demo_01                                │ │
│  └──────────────────────────────────────────────────────┘ │
│  │                                                        │ │
│  │ ☰ SIDEBAR          MAIN CONTENT AREA                 │ │
│  │ • Dashboard        [Investigation Cases]              │ │
│  │ • Analysis         [Active Cases]                      │ │
│  │ • Reports          [Recent Activity]                   │ │
│  │                                                        │ │
└───────────────────────────────────────────────────────────┘
```

---

## 🔑 TEST CREDENTIALS

**Copy and paste these values:**

| Field | Value | Notes |
|-------|-------|-------|
| **Login ID** | `demo_officer` | Any text works |
| **Mobile** | `9876543210` | Must be 10 digits |
| **OTP** | `123456` | Any 6 digits work |

---

## 📋 What Each Screen Shows

### **SCREEN 1: Login Credentials**
```
┌──────────────────────────────────────────┐
│  🔐 Police Officer Login                │
│  Secure Authentication with OTP          │
│                                          │
│  LOGIN ID *                             │
│  ┌────────────────────────────────────┐ │
│  │ demo_officer                       │ │
│  └────────────────────────────────────┘ │
│                                          │
│  MOBILE NUMBER *                        │
│  ┌──────┬──────────────────────────────┐ │
│  │ +91  │ 9876543210                   │ │
│  └──────┴──────────────────────────────┘ │
│                                          │
│      ┌──────────────────────────┐       │
│      │  ▶ SEND OTP              │       │
│      └──────────────────────────┘       │
│                                          │
│  For support: cybercrime@tnpolice...    │
└──────────────────────────────────────────┘
```

### **SCREEN 2: OTP Entry**
```
┌──────────────────────────────────────────┐
│  Enter the 6-digit OTP sent to          │
│  9876543210                              │
│                                          │
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐         │
│  │1 │ │2 │ │3 │ │4 │ │5 │ │6 │         │
│  └──┘ └──┘ └──┘ └──┘ └──┘ └──┘         │
│                                          │
│  OTP expires in 120s ⏱️                  │
│                                          │
│      ┌──────────────────────────┐       │
│      │  ▶ VERIFY OTP            │       │
│      └──────────────────────────┘       │
│      ┌──────────────────────────┐       │
│      │   BACK TO LOGIN ID       │       │
│      └──────────────────────────┘       │
│      ┌──────────────────────────┐       │
│      │   RESEND OTP             │       │
│      └──────────────────────────┘       │
└──────────────────────────────────────────┘
```

### **SCREEN 3: Success**
```
┌──────────────────────────────────────────┐
│                                          │
│            ✅ ✅ ✅                     │
│                                          │
│       Login Successful                  │
│   Redirecting to dashboard...           │
│                                          │
│          ⟳ Loading...                  │
│                                          │
└──────────────────────────────────────────┘
```

---

## ⚙️ INPUT VALIDATION RULES

### Login ID Field
```
✅ VALID                  ❌ INVALID
- demo_officer           - (empty/blank)
- PO12345               - Only spaces
- officer_001           
- test_123              
- ANY_TEXT              
```

### Mobile Number Field
```
✅ VALID                  ❌ INVALID
- 9876543210            - 987654321 (9 digits)
- 9123456789            - 98765432101 (11 digits)
- 8765432109            - 9876543abc (letters)
- 7654321098            - 987-654-3210 (dashes)
                        - +919876543210 (with +91)
```

### OTP Field
```
✅ VALID                  ❌ INVALID
- 000000                - 12345 (5 digits)
- 123456                - 1234567 (7 digits)
- 999999                - abcdef (letters)
- 777777                - 123 45 (spaces)
```

---

## ⏱️ TIMING INFORMATION

| Event | Duration |
|-------|----------|
| **OTP Validity** | 120 seconds (2 minutes) |
| **Redirect to Dashboard** | 1.5 seconds after verification |
| **Session Duration** | Indefinite (will add timeout in production) |
| **Loading Animation** | 1.5 seconds per step |

---

## 🎯 COMMON ISSUES & SOLUTIONS

### Issue 1: "Please enter your Login ID"
```
❌ Problem: Left Login ID empty
✅ Solution: Type any username (e.g., "officer_001")
```

### Issue 2: "Please enter a valid 10-digit mobile number"
```
❌ Problem: Entered wrong number of digits
✅ Solution: Must be exactly 10 digits (e.g., "9876543210")
```

### Issue 3: "OTP expired"
```
❌ Problem: Took more than 120 seconds to enter OTP
✅ Solution: Click "Resend OTP" for a new 120-second window
```

### Issue 4: Page won't load
```
❌ Problem: Docker containers not running
✅ Solution: Run these commands:
   cd /home/subha/Downloads/tor-unveil/infra
   sudo docker compose up -d
```

### Issue 5: Can't enter numbers in OTP
```
❌ Problem: Might be a browser issue
✅ Solution: Try different browser or clear cache
```

---

## 🔄 RESET & RE-LOGIN

To login again as a different user:

1. **Click "Logout"** button (top-right of dashboard)
2. **You return to login page**
3. **Enter new Login ID and Mobile**
4. **Get new OTP (any 6 digits)**
5. **Verify and login**

---

## 🌐 LIVE DEMO TEST SCRIPT

**Copy-paste this sequence:**

```
1. Open: http://localhost:3000

2. Wait for page to load (2-3 seconds)

3. Enter Login ID:
   demo_officer

4. Enter Mobile Number:
   9876543210

5. Click "Send OTP"

6. See success message ✅

7. Enter OTP (any 6 digits):
   123456

8. Click "Verify OTP"

9. See success animation ✅

10. Auto-redirect to dashboard 🎉

11. See logged-in status: "Logged in as: demo_officer"

12. Click "Logout" to test again
```

---

## 📊 CURRENT vs PRODUCTION FLOW

### CURRENT (DEMO MODE) ✅
```
Step 1: Enter credentials
Step 2: Click "Send OTP" → Success message (no SMS sent)
Step 3: Enter any 6 digits
Step 4: Click "Verify" → Auto-login
Step 5: Dashboard access granted
```

### PRODUCTION (WITH SMS) 🚀
```
Step 1: Enter credentials
Step 2: Click "Send OTP" → SMS sent to real phone
Step 3: Officer receives SMS with real OTP code
Step 4: Officer enters OTP from SMS
Step 5: Backend validates OTP against SMS
Step 6: Login succeeds with authentication token
```

---

## 💡 TESTING DIFFERENT SCENARIOS

### Scenario 1: Normal Login ✅
```
Login ID: officer_001
Mobile: 9876543210
OTP: 000000
Result: Login successful
```

### Scenario 2: Empty Login ID ❌
```
Login ID: (empty)
Mobile: 9876543210
Result: Error message shown
```

### Scenario 3: Invalid Mobile ❌
```
Login ID: officer_001
Mobile: 98765 (only 5 digits)
Result: Error message shown
```

### Scenario 4: OTP Timeout ❌
```
Login ID: officer_001
Mobile: 9876543210
(Wait 121 seconds)
OTP: 123456
Result: "OTP expired" message
Action: Click "Resend OTP"
```

---

## 🔗 QUICK LINKS

| Resource | Link |
|----------|------|
| **Application** | http://localhost:3000 |
| **API Server** | http://localhost:8000 |
| **Database** | localhost:27017 (MongoDB) |
| **Full Login Guide** | See `LOGIN_GUIDE.md` |
| **Backend Setup** | See `BACKEND_OTP_SETUP.md` |

---

## 🎓 KEY CONCEPTS

**OTP** = One-Time Password
- 6-digit code sent to phone
- Valid for only 120 seconds
- Can be resent for new code

**MFA** = Multi-Factor Authentication
- Login ID = something you know
- OTP = something you have (phone)
- Two factors = more secure

**Demo Mode** = Simulated without real SMS
- Useful for testing UI/UX
- No phone number needed
- Any OTP code works

**Production Mode** = Real SMS integration
- Real phone numbers required
- Real OTP sent via SMS
- Backend validates code

---

**Ready? Go to http://localhost:3000 and login! 🚀**
