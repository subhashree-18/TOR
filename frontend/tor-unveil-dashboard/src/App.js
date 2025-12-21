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
import { BrowserRouter, Routes, Route, useNavigate, useLocation, useParams } from "react-router-dom";
import { AppProvider, useAppContext } from "./AppContext";
import Dashboard from "./Dashboard";
import AnalysisPage from "./AnalysisPage";
import ReportPage from "./ReportPage";
import InvestigationPage from "./InvestigationPage";
import ForensicAnalysis from "./ForensicAnalysis";
import ForensicUpload from "./ForensicUpload";
import CasesDashboard from "./CasesDashboard";
import PoliceLogin from "./PoliceLogin";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// ============================================================================
// LEGACY ROUTE REDIRECT COMPONENT
// Handles old URLs gracefully by redirecting to new query parameter format
// ============================================================================

function LegacyRouteRedirect() {
  const navigate = useNavigate();
  const { caseId } = useParams();
  const location = useLocation();

  useEffect(() => {
    if (caseId) {
      // Extract the base path and redirect with query parameters
      let newPath = "/";
      const pathname = location.pathname;
      
      if (pathname.includes("/forensic-upload") || pathname.includes("/evidence")) {
        newPath = `/evidence?caseId=${encodeURIComponent(caseId)}`;
      } else if (pathname.includes("/analysis")) {
        newPath = `/analysis?caseId=${encodeURIComponent(caseId)}`;
      } else if (pathname.includes("/forensic-analysis")) {
        newPath = `/forensic-analysis?caseId=${encodeURIComponent(caseId)}`;
      } else if (pathname.includes("/report")) {
        newPath = `/report?caseId=${encodeURIComponent(caseId)}`;
      }
      
      navigate(newPath, { replace: true });
    } else {
      // No case ID, redirect to dashboard
      navigate("/", { replace: true });
    }
  }, [navigate, caseId, location.pathname]);

  return <div>Redirecting...</div>;
}

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
// CHANGE 9: PROTECTED ROUTE WRAPPER
// Enforces investigation workflow: Dashboard → Investigation → Analysis → Report
// Only allows access to investigation pages if case_id is provided and valid
// ============================================================================

function ProtectedRoute({ element, requiresCaseId = false, requiredAnalysisState = null }) {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get case ID from query params or location state
  const searchParams = new URLSearchParams(location.search);
  const caseIdFromParams = searchParams.get('caseId');
  const caseIdFromState = location.state?.caseId;
  const caseId = caseIdFromParams || caseIdFromState;
  
  // If case ID is required but not provided, redirect to dashboard
  if (requiresCaseId && !caseId) {
    return (
      <div className="route-protection-notice">
        <h2>Access Denied</h2>
        <p>This page requires a valid case ID. Please select a case from the Dashboard.</p>
        <button onClick={() => navigate("/dashboard")}>Return to Dashboard</button>
      </div>
    );
  }
  
  // Return the protected element
  return element;
}

// ============================================================================
// INVESTIGATION WORKFLOW ROUTER
// Ensures proper flow: Dashboard → Investigation → Evidence/Analysis → Report
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
// LEGAL & ETHICAL GUARDRAILS NOTICE
// Global notice about system limitations and ethical usage
// ============================================================================

function LegalNotice() {
  return (
    <div className="legal-notice-banner">
      <div className="legal-notice-content">
        <div className="legal-warning-icon">⚖️</div>
        <div className="legal-text">
          <strong>IMPORTANT LEGAL NOTICE:</strong> This system provides correlation analysis only. 
          <span className="legal-emphasis">TOR-Unveil does not deanonymize TOR users</span> and cannot identify individual persons. 
          All findings are probabilistic assessments for investigative guidance only, not conclusive evidence.
        </div>
      </div>
    </div>
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
      const response = await fetch(`${API_URL}/api/investigations/${caseId}/status`);
      if (response.ok) {
        // Check if response is actually JSON before parsing
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json();
          setCaseStatus({
            hasInvestigation: true,
            hasEvidence: data.evidence_uploaded || false,
            hasAnalysis: data.analysis_complete || false,
            isComplete: data.report_generated || false
          });
        } else {
          console.warn("Backend returned non-JSON response for case status");
          // Assume case exists but is new
          setCaseStatus({
            hasInvestigation: true,
            hasEvidence: false,
            hasAnalysis: false,
            isComplete: false
          });
        }
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
      <LegalNotice />
      
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
              
              {/* Cases Dashboard - View all submitted cases */}
              <Route path="/cases" element={<CasesDashboard />} />
              
              {/* Investigation Hub - Single Source of Truth */}
              {/* Requires valid case_id to function */}
              <Route path="/investigation" element={<InvestigationPage />} />
              <Route path="/investigation/:caseId" element={<InvestigationPage />} />
              
              {/* CHANGE 9: Protected routes - require case_id */}
              {/* Only accessible after selecting case in Investigation page */}
              <Route 
                path="/evidence" 
                element={
                  <ProtectedRoute 
                    element={<ForensicUpload />} 
                    requiresCaseId={true} 
                  />
                } 
              />
              <Route 
                path="/analysis" 
                element={
                  <ProtectedRoute 
                    element={<AnalysisPage />} 
                    requiresCaseId={true} 
                  />
                } 
              />
              <Route 
                path="/forensic-analysis" 
                element={
                  <ProtectedRoute 
                    element={<ForensicAnalysis />} 
                    requiresCaseId={true} 
                  />
                } 
              />
              <Route 
                path="/report" 
                element={
                  <ProtectedRoute 
                    element={<ReportPage />} 
                    requiresCaseId={true} 
                  />
                } 
              />
              
              {/* Legacy route redirects for old URLs */}
              <Route path="/forensic-upload/:caseId" element={<LegacyRouteRedirect />} />
              <Route path="/evidence/:caseId" element={<LegacyRouteRedirect />} />
              <Route path="/analysis/:caseId" element={<LegacyRouteRedirect />} />
              <Route path="/forensic-analysis/:caseId" element={<LegacyRouteRedirect />} />
              <Route path="/report/:caseId" element={<LegacyRouteRedirect />} />
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
