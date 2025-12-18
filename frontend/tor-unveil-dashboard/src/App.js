// src/App.js - Tamil Nadu Police Cyber Crime Wing Portal
// Government-style layout matching tn.gov.in / tnpolice.gov.in
import React, { useState } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { AppProvider, useAppContext } from "./AppContext";
import Dashboard from "./Dashboard";
import PathsDashboard from "./PathsDashboard";
import AnalysisPage from "./AnalysisPage";
import ReportPage from "./ReportPage";
import InvestigationPage from "./InvestigationPage";
import ForensicAnalysis from "./ForensicAnalysis";
import ForensicUpload from "./ForensicUpload";
import PoliceLogin from "./PoliceLogin";
import "./App.css";

// ============================================================================
// GOVERNMENT HEADER COMPONENT
// Tamil Nadu Police official header with emblem and title
// ============================================================================

function GovernmentHeader({ userInfo, onLogout }) {
  return (
    <header className="govt-header">
      <div className="govt-header-content">
        {/* Left: Emblem and Title */}
        <div className="govt-header-left">
          <div className="govt-emblem">
            {/* Tamil Nadu Police Emblem Placeholder */}
            <div className="emblem-circle">
              <span className="emblem-text">TN</span>
              <span className="emblem-subtext">POLICE</span>
            </div>
          </div>
          <div className="govt-title-block">
            <h1 className="govt-title">TOR???Unveil</h1>
            <p className="govt-subtitle">Cyber Crime Wing, Tamil Nadu Police</p>
            <p className="govt-dept">??????????????? ????????????????????? ??????????????????, ??????????????????????????? ???????????????????????????</p>
          </div>
        </div>

        {/* Right: User info and logout */}
        <div className="govt-header-right">
          {userInfo && (
            <div className="govt-user-info">
              <span className="user-label">Officer ID:</span>
              <span className="user-id">{userInfo.loginId}</span>
              <button className="govt-logout-btn" onClick={onLogout}>
                Logout
              </button>
            </div>
          )}
          <div className="govt-date">
            {new Date().toLocaleDateString('en-IN', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </div>
        </div>
      </div>
    </header>
  );
}

// ============================================================================
// LEFT NAVIGATION SIDEBAR
// Government-style vertical navigation - always visible
// ============================================================================

function LeftNavigation() {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  const navItems = [
    { path: "/", label: "Dashboard", icon: "???" },
    { path: "/investigation", label: "Investigations", icon: "???" },
    { path: "/forensic", label: "Evidence Upload", icon: "???" },
    { path: "/analysis", label: "Analysis", icon: "???" },
    { path: "/report", label: "Forensic Report", icon: "???" },
    { path: "/paths", label: "Path Analysis", icon: "???" },
  ];

  return (
    <nav className="govt-sidebar">
      <div className="sidebar-title">MAIN MENU</div>
      <ul className="sidebar-nav-list">
        {navItems.map((item) => (
          <li key={item.path}>
            <button
              className={`sidebar-nav-item ${isActive(item.path) ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          </li>
        ))}
      </ul>
      
      <div className="sidebar-section">
        <div className="sidebar-section-title">QUICK LINKS</div>
        <ul className="sidebar-links">
          <li><a href="https://tnpolice.gov.in" target="_blank" rel="noopener noreferrer">TN Police Portal</a></li>
          <li><a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer">National Cyber Crime</a></li>
          <li><a href="https://tn.gov.in" target="_blank" rel="noopener noreferrer">TN Government</a></li>
        </ul>
      </div>
    </nav>
  );
}

// ============================================================================
// GOVERNMENT FOOTER
// Official footer with disclaimers
// ============================================================================

function GovernmentFooter() {
  return (
    <footer className="govt-footer">
      <div className="footer-content">
        <div className="footer-main">
          <div className="footer-org">
            <strong>Government of Tamil Nadu</strong>
            <span>Cyber Crime Wing, Chennai</span>
          </div>
          <div className="footer-contact">
            <span>Cyber Crime Helpline: 1930</span>
            <span>Email: cybercrime@tnpolice.gov.in</span>
          </div>
        </div>
        <div className="footer-disclaimer">
          <strong>DISCLAIMER:</strong> This system is for authorized Tamil Nadu Police personnel only. 
          Unauthorized access is prohibited and punishable under the Information Technology Act, 2000. 
          All activities are logged and monitored. Analysis results are probabilistic and must not be 
          used as sole evidence for legal proceedings.
        </div>
        <div className="footer-copyright">
          ?? {new Date().getFullYear()} Tamil Nadu Police. All Rights Reserved.
        </div>
      </div>
    </footer>
  );
}

// ============================================================================
// CASE ID BAR
// Secondary toolbar for case management
// ============================================================================

function CaseIdBar() {
  const { selectedRelay } = useAppContext();
  const [caseId, setCaseId] = useState("CASE-2025-001");
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div className="case-bar">
      <div className="case-bar-left">
        <label className="case-label">Case Reference:</label>
        {isEditing ? (
          <input
            type="text"
            className="case-input"
            value={caseId}
            onChange={(e) => setCaseId(e.target.value)}
            onBlur={() => setIsEditing(false)}
            onKeyDown={(e) => e.key === 'Enter' && setIsEditing(false)}
            autoFocus
          />
        ) : (
          <span className="case-id" onClick={() => setIsEditing(true)}>
            {caseId}
          </span>
        )}
        {selectedRelay && (
          <span className="selected-relay">
            Selected Relay: {selectedRelay.nickname || selectedRelay.fingerprint?.substring(0, 8)}
          </span>
        )}
      </div>
      <div className="case-bar-right">
        <span className="timestamp">
          Last Updated: {new Date().toLocaleTimeString('en-IN')}
        </span>
      </div>
    </div>
  );
}

// ============================================================================
// MAIN APP CONTENT
// ============================================================================

function AppContent() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    const saved = localStorage.getItem("tor-unveil-logged-in");
    return saved === "true";
  });
  const [userInfo, setUserInfo] = useState(() => {
    const saved = localStorage.getItem("tor-unveil-user-info");
    return saved ? JSON.parse(saved) : null;
  });

  const handleLoginSuccess = (loginData) => {
    setUserInfo(loginData);
    setIsLoggedIn(true);
    localStorage.setItem("tor-unveil-logged-in", "true");
    localStorage.setItem("tor-unveil-user-info", JSON.stringify(loginData));
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserInfo(null);
    localStorage.removeItem("tor-unveil-logged-in");
    localStorage.removeItem("tor-unveil-user-info");
  };

  if (!isLoggedIn) {
    return <PoliceLogin onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="govt-app-container">
      <GovernmentHeader userInfo={userInfo} onLogout={handleLogout} />
      
      <div className="govt-main-layout">
        <LeftNavigation />
        
        <main className="govt-main-content">
          <CaseIdBar />
          <div className="page-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/investigation" element={<InvestigationPage />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/paths" element={<PathsDashboard />} />
              <Route path="/analysis" element={<AnalysisPage />} />
              <Route path="/forensic" element={<ForensicAnalysis />} />
              <Route path="/upload" element={<ForensicUpload />} />
              <Route path="/report" element={<ReportPage />} />
            </Routes>
          </div>
        </main>
      </div>
      
      <GovernmentFooter />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </BrowserRouter>
  );
}
