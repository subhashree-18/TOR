// src/PoliceLogin.js - Professional Police Login with OTP
import React, { useState, useEffect } from "react";
import { Shield, Phone, Lock, CheckCircle, AlertCircle, Loader, LogOut } from "lucide-react";
import "./PoliceLogin.css";

// Sample Police Officer Database
const VALID_OFFICERS = [
  { loginId: "TN001", name: "Rajesh Kumar", mobile: "9876543210", designation: "Inspector" },
  { loginId: "TN002", name: "Priya Singh", mobile: "9877654321", designation: "Constable" },
  { loginId: "TN003", name: "Amit Verma", mobile: "9878765432", designation: "Sub-Inspector" },
  { loginId: "TN004", name: "Vikram Patel", mobile: "9879876543", designation: "ASI" },
  { loginId: "TN005", name: "Neha Sharma", mobile: "9880987654", designation: "Inspector" },
];

function PoliceLogin({ onLoginSuccess }) {
  const [step, setStep] = useState("mobile"); // mobile, otp, verification
  const [mobileNumber, setMobileNumber] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [loginId, setLoginId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [timer, setTimer] = useState(0);
  const [otpSent, setOtpSent] = useState(false);
  const [officerName, setOfficerName] = useState("");
  const [officerDesignation, setOfficerDesignation] = useState("");

  // Timer for OTP resend
  useEffect(() => {
    let interval;
    if (timer > 0) {
      interval = setInterval(() => setTimer(timer - 1), 1000);
    }
    return () => clearInterval(interval);
  }, [timer]);

  const validateMobileNumber = (number) => {
    return /^[0-9]{10}$/.test(number);
  };

  const validateOfficer = (id, mobile) => {
    const officer = VALID_OFFICERS.find(
      (o) => o.loginId === id && o.mobile === mobile
    );
    return officer;
  };

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

    // Validate officer credentials
    const officer = validateOfficer(loginId, mobileNumber);
    if (!officer) {
      setError("Invalid Login ID or Mobile Number. Check your credentials.");
      return;
    }

    setOfficerName(officer.name);
    setOfficerDesignation(officer.designation);

    setLoading(true);
    try {
      // Simulate API call to send OTP
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // In production, this would call your backend API
      // const response = await fetch('/api/auth/send-otp', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ loginId, mobileNumber })
      // });

      setSuccess(`OTP sent successfully to +91${mobileNumber}`);
      setOtpSent(true);
      setStep("otp");
      setTimer(120); // 2 minutes to enter OTP
    } catch (err) {
      setError("Failed to send OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index, value) => {
    if (!/^[0-9]*$/.test(value)) return;
    
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      document.getElementById(`otp-${index + 1}`).focus();
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
      // Simulate API call to verify OTP
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // In production, this would call your backend API
      // const response = await fetch('/api/auth/verify-otp', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ loginId, mobileNumber, otp: otpCode })
      // });

      setSuccess("OTP verified successfully!");
      setStep("verification");

      // Call onLoginSuccess after a short delay
      setTimeout(() => {
        onLoginSuccess({
          loginId,
          name: officerName,
          designation: officerDesignation,
          mobileNumber,
          timestamp: new Date().toISOString(),
        });
      }, 1500);
    } catch (err) {
      setError("OTP verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = () => {
    setOtp(["", "", "", "", "", ""]);
    setTimer(120);
    handleSendOtp({ preventDefault: () => {} });
  };

  return (
    <div className="police-login-container">
      {/* Header Section */}
      <div className="login-header">
        <div className="header-logo-section">
          <div className="govt-logo-left">
            <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect fill='%23fff' width='100' height='100' rx='12'/%3E%3Ctext x='50' y='55' font-size='40' font-weight='bold' text-anchor='middle' fill='%230d47a1'%3ETN%3C/text%3E%3C/svg%3E" alt="Tamil Nadu Govt" className="logo-img" title="Tamil Nadu Government Logo Placeholder" />
          </div>
          <div className="header-text">
            <h1>National Cyber Crime Reporting Portal</h1>
            <p>Tamil Nadu Police - Cybercrime Investigation Unit</p>
          </div>
          <div className="govt-logo-right">
            <Shield size={48} className="shield-icon" />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="login-content">
        <div className="login-card">
          <div className="login-title">
            <Lock size={32} className="lock-icon" />
            <h2>Police Officer Login</h2>
            <p>Secure Authentication with OTP</p>
          </div>

          {/* Alert Messages */}
          {error && (
            <div className="alert alert-error">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}
          {success && (
            <div className="alert alert-success">
              <CheckCircle size={18} />
              <span>{success}</span>
            </div>
          )}

          {/* Quick Login Help */}
          <div className="quick-help-box">
            <p className="help-title">💡 Test Credentials:</p>
            <div className="credentials-list">
              {VALID_OFFICERS.slice(0, 3).map((officer) => (
                <div key={officer.loginId} className="credential-item">
                  <span className="cred-label">ID: {officer.loginId}</span>
                  <span className="cred-separator">•</span>
                  <span className="cred-value">{officer.mobile}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Step 1: Login ID & Mobile */}
          {step === "mobile" && (
            <form onSubmit={handleSendOtp} className="login-form">
              <div className="form-group">
                <label htmlFor="login-id">Login ID</label>
                <input
                  type="text"
                  id="login-id"
                  value={loginId}
                  onChange={(e) => {
                    setLoginId(e.target.value.toUpperCase());
                    setError("");
                  }}
                  placeholder="e.g., TN001, TN002"
                  disabled={loading}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label htmlFor="mobile">Mobile Number</label>
                <div className="mobile-input-group">
                  <span className="country-code">+91</span>
                  <input
                    type="tel"
                    id="mobile"
                    value={mobileNumber}
                    onChange={(e) => {
                      setMobileNumber(e.target.value.replace(/\D/g, "").slice(0, 10));
                      setError("");
                    }}
                    placeholder="Enter 10-digit mobile number"
                    disabled={loading}
                    maxLength="10"
                    className="form-input"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="submit-btn"
              >
                {loading ? (
                  <>
                    <Loader size={18} className="spin" />
                    Sending OTP...
                  </>
                ) : (
                  "Send OTP"
                )}
              </button>
            </form>
          )}

          {/* Step 2: OTP Verification */}
          {step === "otp" && (
            <form onSubmit={handleVerifyOtp} className="login-form">
              <div className="otp-instruction">
                <p>Enter the 6-digit OTP sent to <strong>+91{mobileNumber}</strong></p>
              </div>

              <div className="otp-inputs">
                {otp.map((digit, index) => (
                  <input
                    key={index}
                    id={`otp-${index}`}
                    type="text"
                    value={digit}
                    onChange={(e) => handleOtpChange(index, e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Backspace" && !digit && index > 0) {
                        document.getElementById(`otp-${index - 1}`).focus();
                      }
                    }}
                    maxLength="1"
                    disabled={loading}
                    className="otp-input"
                    placeholder="0"
                  />
                ))}
              </div>

              {timer > 0 ? (
                <div className="timer-info">
                  OTP expires in <span className="timer">{timer}s</span>
                </div>
              ) : (
                <div className="timer-expired">
                  OTP expired. Please request a new one.
                </div>
              )}

              <button
                type="submit"
                disabled={loading || timer === 0}
                className="submit-btn"
              >
                {loading ? (
                  <>
                    <Loader size={18} className="spin" />
                    Verifying...
                  </>
                ) : (
                  "Verify OTP"
                )}
              </button>

              <button
                type="button"
                onClick={() => {
                  setStep("mobile");
                  setOtp(["", "", "", "", "", ""]);
                  setError("");
                  setSuccess("");
                }}
                className="back-btn"
              >
                Back to Login ID
              </button>

              {timer > 0 && (
                <button
                  type="button"
                  onClick={handleResendOtp}
                  disabled={loading}
                  className="resend-btn"
                >
                  Resend OTP
                </button>
              )}
            </form>
          )}

          {/* Step 3: Verification Success */}
          {step === "verification" && (
            <div className="verification-success">
              <div className="success-icon">
                <CheckCircle size={64} />
              </div>
              <h3>Login Successful</h3>
              <p>Welcome, {officerName}</p>
              <p className="designation-text">{officerDesignation}</p>
              <p className="redirecting">Redirecting to dashboard...</p>
              <Loader size={32} className="spin" />
            </div>
          )}

          {/* Footer */}
          <div className="login-footer">
            <p>
              For technical support, contact: <strong>cybercrime@tnpolice.gov.in</strong>
            </p>
            <p className="security-notice">
              🔒 This is a secure government portal. Your data is encrypted.
            </p>
          </div>
        </div>

        {/* Right Side - Info Panel */}
        <div className="login-info-panel">
          <div className="info-section">
            <div className="info-icon">
              <Shield size={32} />
            </div>
            <h3>Secure Access</h3>
            <p>Multi-factor authentication with OTP for enhanced security</p>
          </div>

          <div className="info-section">
            <div className="info-icon">
              <Phone size={32} />
            </div>
            <h3>SMS OTP Verification</h3>
            <p>Receive one-time password via SMS to your registered mobile number</p>
          </div>

          <div className="info-section">
            <div className="info-icon">
              <Lock size={32} />
            </div>
            <h3>Data Protection</h3>
            <p>All data transmitted is encrypted with industry-standard protocols</p>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="login-page-footer">
        <p>© 2024 Tamil Nadu Police - Cybercrime Investigation Unit</p>
        <p>Government of India | Ministry of Home Affairs</p>
      </div>
    </div>
  );
}

export default PoliceLogin;
