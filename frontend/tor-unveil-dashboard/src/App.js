/**
 * App.js ??? GOVERNMENT PORTAL SHELL
 * Tamil Nadu Police Cyber Crime Wing - TOR???Unveil
 * 
 * GLOBAL CONSTRAINTS:
 * - No mock data, no static placeholders
 * - All UI state must be driven by backend APIs
 * - Conservative government UI (NIC / tnpolice.gov.in style)
 * - No animations, no gradients, no hacker themes
 * - Flat layout, tables over cards
 * - Officers are non-technical users
 * 
 * Color Palette:
 * - Background: #f5f7fa
 * - Primary (nav/header): #0b3c5d
 * - Secondary (warnings): #7a1f1f
 * - Accent (minimal): #d9a441
 * - Text: black / dark grey only
 */

import React, { useState, useEffect, useCallback } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { AppProvider, useAppContext } from "./AppContext";
import Dashboard from "./Dashboard";
import AnalysisPage from "./AnalysisPage";
import ReportPage from "./ReportPage";
import InvestigationPage from "./InvestigationPage";
import ForensicAnalysis from "./ForensicAnalysis";
import ForensicUpload from "./ForensicUpload";
import PoliceLogin from "./PoliceLogin";
import "./App.css";

// ============================================================================
// NAVIGATION WORKFLOW STEPS
// Investigation workflow: Dashboard → Investigation → Evidence → Analysis → Report
// PROTECTED PAGES ACCESSIBLE ONLY VIA INVESTIGATION WORKFLOW
// ============================================================================

const WORKFLOW_STEPS = [
  { 
    id: "dashboard", 
    label: "Case Dashboard", 
    path: "/", 
    requiresCase: false,
    description: "View all cases and create new investigations"
  },
  { 
    id: "investigation", 
    label: "Case Investigation", 
    path: "/investigation", 
    requiresCase: true,
    description: "Single source of truth for case workflow"
  }
  // Evidence, Analysis, Report removed from direct navigation
  // Only accessible via buttons in Investigation page based on case state
];

// ============================================================================
// GOVERNMENT HEADER COMPONENT
// Fixed top header with official branding
// ============================================================================

function GovernmentHeader({ userInfo, onLogout }) {
  return (
    <header className="govt-header">
      <div className="govt-header-content">
        {/* Left: Title and Department */}
        <div className="govt-header-left">
          <div className="govt-emblem">
            <div className="emblem-box">
              <span className="emblem-text">TN</span>
              <span className="emblem-subtext">POLICE</span>
            </div>
          </div>
          <div className="govt-title-block">
            <h1 className="govt-title">TOR???Unveil</h1>
            <p className="govt-subtitle">Cyber Crime Wing, Tamil Nadu Police</p>
          </div>
        </div>

        {/* Right: User info and logout */}
        <div className="govt-header-right">
          {userInfo && (
            <div className="govt-user-info">
              <span className="user-label">Officer:</span>
              <span className="user-id">{userInfo.loginId || userInfo.username || "???"}</span>
              <button className="govt-logout-btn" onClick={onLogout}>
                Logout
              </button>
            </div>
          )}
          <div className="govt-date">
            {new Date().toLocaleDateString("en-IN", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric"
            })}
          </div>
        </div>
      </div>
    </header>
  );
}

// ============================================================================
// LEFT VERTICAL NAVIGATION
// Backend-aware navigation - disables links based on investigation state
// ============================================================================

function LeftNavigation({ caseStatus, activeCaseId }) {
  const navigate = useNavigate();
  const location = useLocation();

  // Determine current active step from URL (only Dashboard and Investigation shown in nav)
  const getCurrentStep = () => {
    const path = location.pathname;
    if (path === "/" || path === "/dashboard") return "dashboard";
    if (path.includes("/investigation")) return "investigation";
    // Protected pages don't show as active in navigation
    return "dashboard"; // Default fallback
  };

  const currentStep = getCurrentStep();

  // Check if a step is enabled based on backend case status
  const isStepEnabled = (step) => {
    // Dashboard always accessible
    if (step.id === "dashboard") return true;
    
    // Check if case is selected
    if (step.requiresCase && !activeCaseId) return false;
    
    // Check investigation status
    if (step.requiresInvestigation && !caseStatus.hasInvestigation) return false;
    
    // Check evidence status
    if (step.requiresEvidence && !caseStatus.hasEvidence) return false;
    
    // Check analysis status
    if (step.requiresAnalysis && !caseStatus.hasAnalysis) return false;
    
    return true;
  };

  // Get navigation path (only Dashboard and Investigation accessible via nav)
  const getNavigationPath = (step) => {
    if (step.id === "dashboard") return "/";
    if (step.id === "investigation") {
      return activeCaseId ? `/investigation/${activeCaseId}` : "/investigation";
    }
    return step.path; // Fallback for unexpected steps
  };

  // Handle navigation click
  const handleNavClick = (step) => {
    if (!isStepEnabled(step)) return;
    navigate(getNavigationPath(step));
  };

  return (
    <nav className="govt-sidebar" aria-label="Main Navigation">
      <div className="sidebar-title">MAIN MENU</div>
      <ul className="sidebar-nav-list">
        {WORKFLOW_STEPS.map((step) => {
          const enabled = isStepEnabled(step);
          const active = currentStep === step.id;
          
          return (
            <li key={step.id}>
              <button
                className={`sidebar-nav-item ${active ? "active" : ""} ${!enabled ? "disabled" : ""}`}
                onClick={() => handleNavClick(step)}
                disabled={!enabled}
                aria-current={active ? "page" : undefined}
                aria-disabled={!enabled}
              >
                <span className="nav-label">{step.label}</span>
                {!enabled && <span className="nav-locked">???</span>}
              </button>
            </li>
          );
        })}
      </ul>

      {/* Case ID indicator */}
      {activeCaseId && (
        <div className="sidebar-case-info">
          <div className="case-info-label">Active Case:</div>
          <div className="case-info-id">{activeCaseId}</div>
        </div>
      )}

      {/* External links */}
      <div className="sidebar-section">
        <div className="sidebar-section-title">EXTERNAL LINKS</div>
        <ul className="sidebar-links">
          <li>
            <a href="https://tnpolice.gov.in" target="_blank" rel="noopener noreferrer">
              TN Police Portal
            </a>
          </li>
          <li>
            <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer">
              National Cyber Crime
            </a>
          </li>
        </ul>
      </div>
    </nav>
  );
}

// ============================================================================
// GOVERNMENT FOOTER
// Official footer with government branding
// ============================================================================

function GovernmentFooter() {
  return (
    <footer className="govt-footer">
      <div className="footer-content">
        <div className="footer-main">
          <span className="footer-org">
            <strong>Government of Tamil Nadu</strong> | Cyber Crime Wing, Chennai
          </span>
          <span className="footer-helpline">
            Cyber Crime Helpline: <strong>1930</strong>
          </span>
        </div>
        <div className="footer-disclaimer">
          This system is for authorized Tamil Nadu Police personnel only. 
          Unauthorized access is prohibited under IT Act, 2000. 
          All analysis results are probabilistic and require corroboration.
        </div>
        <div className="footer-copyright">
          ?? {new Date().getFullYear()} Tamil Nadu Police. All Rights Reserved.
        </div>
      </div>
    </footer>
  );
}

// ============================================================================
// MAIN APP CONTENT
// Handles authentication and case status from backend
// ============================================================================

function AppContent() {
  const { selectedCase } = useAppContext();
  
  // Authentication state - driven by backend
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    const saved = localStorage.getItem("tor-unveil-logged-in");
    return saved === "true";
  });
  
  const [userInfo, setUserInfo] = useState(() => {
    const saved = localStorage.getItem("tor-unveil-user-info");
    return saved ? JSON.parse(saved) : null;
  });

  // Case status from backend - controls navigation availability
  const [caseStatus, setCaseStatus] = useState({
    hasInvestigation: false,
    hasEvidence: false,
    hasAnalysis: false,
    isComplete: false
  });

  // Active case ID from context or URL
  const [activeCaseId, setActiveCaseId] = useState(null);

  // Fetch case status from backend when case changes
  const fetchCaseStatus = useCallback(async (caseId) => {
    if (!caseId) {
      setCaseStatus({
        hasInvestigation: false,
        hasEvidence: false,
        hasAnalysis: false,
        isComplete: false
      });
      return;
    }

    try {
      const response = await fetch(`/api/investigations/${caseId}/status`);
      if (response.ok) {
        const data = await response.json();
        setCaseStatus({
          hasInvestigation: true,
          hasEvidence: data.evidence_uploaded || false,
          hasAnalysis: data.analysis_complete || false,
          isComplete: data.report_generated || false
        });
      } else {
        // Case exists but might be new
        setCaseStatus({
          hasInvestigation: true,
          hasEvidence: false,
          hasAnalysis: false,
          isComplete: false
        });
      }
    } catch (error) {
      // Backend unavailable - allow navigation based on case existence
      console.warn("Could not fetch case status:", error.message);
      setCaseStatus({
        hasInvestigation: !!caseId,
        hasEvidence: false,
        hasAnalysis: false,
        isComplete: false
      });
    }
  }, []);

  // Update case status when selected case changes
  useEffect(() => {
    if (selectedCase?.caseId) {
      setActiveCaseId(selectedCase.caseId);
      fetchCaseStatus(selectedCase.caseId);
    }
  }, [selectedCase, fetchCaseStatus]);

  // Handle login success
  const handleLoginSuccess = (loginData) => {
    setUserInfo(loginData);
    setIsLoggedIn(true);
    localStorage.setItem("tor-unveil-logged-in", "true");
    localStorage.setItem("tor-unveil-user-info", JSON.stringify(loginData));
  };

  // Handle logout
  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserInfo(null);
    setActiveCaseId(null);
    setCaseStatus({
      hasInvestigation: false,
      hasEvidence: false,
      hasAnalysis: false,
      isComplete: false
    });
    localStorage.removeItem("tor-unveil-logged-in");
    localStorage.removeItem("tor-unveil-user-info");
  };

  // Show login if not authenticated
  if (!isLoggedIn) {
    return <PoliceLogin onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="govt-app-container">
      <GovernmentHeader userInfo={userInfo} onLogout={handleLogout} />
      
      <div className="govt-main-layout">
        <LeftNavigation 
          caseStatus={caseStatus} 
          activeCaseId={activeCaseId}
        />
        
        <main className="govt-main-content">
          <div className="page-content">
            <Routes>
              {/* Public access routes only - Workflow enforced via Investigation */}
              
              {/* Dashboard - Case List (Entry Point) */}
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              
              {/* Investigation Hub - Single Source of Truth */}
              <Route path="/investigation" element={<InvestigationPage />} />
              <Route path="/investigation/:caseId" element={<InvestigationPage />} />
              
              {/* Protected routes with backend verification */}
              {/* Only accessible via Investigation workflow buttons */}
              <Route path="/evidence/:caseId" element={<ForensicUpload />} />
              <Route path="/analysis/:caseId" element={<AnalysisPage />} />
              <Route path="/forensic-analysis/:caseId" element={<ForensicAnalysis />} />
              <Route path="/report/:caseId" element={<ReportPage />} />
            </Routes>
          </div>
        </main>
      </div>
      
      <GovernmentFooter />
    </div>
  );
}

// ============================================================================
// ROOT APP COMPONENT
// ============================================================================

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </BrowserRouter>
  );
}
