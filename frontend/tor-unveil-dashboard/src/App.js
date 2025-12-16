// src/App.js - SOC-Style Sidebar + Top Bar Layout
import React, { useState } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { LayoutDashboard, GitBranch, Activity, FileText, RefreshCw, Menu, X, Eye, Briefcase, Search } from "lucide-react";
import { AppProvider, useAppContext } from "./AppContext";
import Dashboard from "./Dashboard";
import PathsDashboard from "./PathsDashboard";
import AnalysisPage from "./AnalysisPage";
import ReportPage from "./ReportPage";
import InvestigationPage from "./InvestigationPage";
import ForensicPage from "./ForensicPage";
import IndiaAnalytics from "./IndiaAnalytics";
import Breadcrumb from "./Breadcrumb";
import TamilNaduBrand from "./TamilNaduBrand";

// ============================================================================
// SIDEBAR NAVIGATION COMPONENT
// ============================================================================

function SideNavigation() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const isActive = (path) => location.pathname === path;

  const navSections = [
    {
      title: "INVESTIGATION",
      items: [
        { path: "/investigation", label: "Workflow", Icon: Briefcase },
        { path: "/dashboard", label: "Dashboard", Icon: LayoutDashboard },
        { path: "/paths", label: "Paths", Icon: GitBranch },
        { path: "/analysis", label: "Analysis", Icon: Activity },
      ],
    },
    {
      title: "REGIONAL ANALYTICS",
      items: [
        { path: "/india", label: "India Focus", Icon: Search },
      ],
    },
    {
      title: "FORENSICS",
      items: [
        { path: "/forensic", label: "Evidence Correlation", Icon: Search },
      ],
    },
    {
      title: "REPORTING",
      items: [
        { path: "/report", label: "Reports", Icon: FileText },
      ],
    },
  ];

  return (
    <aside style={styles.sidebar(isCollapsed)}>
      <div style={styles.sidebarHeader}>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          style={styles.collapseBtn}
          title={isCollapsed ? "Expand" : "Collapse"}
        >
          {isCollapsed ? (
            <Menu size={20} stroke="currentColor" fill="none" />
          ) : (
            <X size={20} stroke="currentColor" fill="none" />
          )}
        </button>
        {!isCollapsed && <h1 style={styles.brandTitle}>TOR UNVEIL</h1>}
      </div>

      {navSections.map((section) => (
        <div key={section.title} style={styles.sidebarSection}>
          {!isCollapsed && <div style={styles.sectionTitle}>{section.title}</div>}
          {section.items.map((item) => (
            <button
              key={item.path}
              style={{
                ...styles.sidebarBtn,
                ...(isActive(item.path) ? styles.sidebarbtnActive : {}),
              }}
              onClick={() => navigate(item.path)}
              title={item.label}
            >
              <item.Icon 
                size={20} 
                strokeWidth={1.5} 
                stroke="currentColor"
                fill="none"
                style={{ flexShrink: 0 }}
              />
              {!isCollapsed && <span style={{ marginLeft: "12px" }}>{item.label}</span>}
            </button>
          ))}
        </div>
      ))}
    </aside>
  );
}

// ============================================================================
// TOP BAR COMPONENT
// ============================================================================

function TopBar() {
  const { selectedRelay, selectedPath } = useAppContext();
  const [caseId, setCaseId] = useState("CASE-2025-001");
  const [isEditingCase, setIsEditingCase] = useState(false);

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <header style={styles.topbar}>
      <div style={styles.topbarLeft}>
        <div style={styles.caseSection}>
          <span style={styles.caseLabel}>Case ID:</span>
          {isEditingCase ? (
            <input
              style={styles.caseInput}
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              onBlur={() => setIsEditingCase(false)}
              onKeyDown={(e) => e.key === "Enter" && setIsEditingCase(false)}
              autoFocus
            />
          ) : (
            <span
              style={styles.caseId}
              onClick={() => setIsEditingCase(true)}
              title="Click to edit"
            >
              {caseId}
            </span>
          )}
        </div>
        {selectedRelay && (
          <div style={styles.selectedTag}>
            <Eye size={14} strokeWidth={2} stroke="currentColor" fill="none" />
            <span style={{fontFamily: "'Courier New', monospace", fontSize: "11px"}}>
              {selectedRelay.nickname || selectedRelay.fingerprint.substring(0, 8)}
            </span>
          </div>
        )}
        {selectedPath && (
          <div style={styles.selectedTag}>
            <Eye size={14} strokeWidth={2} stroke="currentColor" fill="none" />
            <span style={{fontSize: "11px"}}>
              {selectedPath.entry.nickname} → {selectedPath.exit.nickname}
            </span>
          </div>
        )}
      </div>

      <div style={styles.topbarRight}>
        <span style={styles.timestamp}>
          {new Date().toLocaleString()}
        </span>
        <button
          style={styles.toolbarBtn}
          onClick={handleRefresh}
          title="Refresh data"
        >
          <RefreshCw size={18} strokeWidth={1.5} stroke="currentColor" fill="none" />
        </button>
      </div>
    </header>
  );
}

// ============================================================================
// MAIN APP CONTENT
// ============================================================================

function AppContent() {
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", width: "100vw" }}>
      <TamilNaduBrand />
      <div style={styles.appContainer}>
        <SideNavigation />
        <div style={styles.mainContent}>
          <TopBar />
          <Breadcrumb />
          <div style={styles.pageContainer}>
            <Routes>
              <Route path="/investigation" element={<InvestigationPage />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/paths" element={<PathsDashboard />} />
              <Route path="/analysis" element={<AnalysisPage />} />
              <Route path="/forensic" element={<ForensicPage />} />
              <Route path="/india" element={<IndiaAnalytics />} />
              <Route path="/report" element={<ReportPage />} />
              <Route path="/" element={<InvestigationPage />} />
            </Routes>
          </div>
        </div>
      </div>
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

// ============================================================================
// STYLING OBJECT - SOC CONSOLE COLORS & LAYOUT
// ============================================================================

const styles = {
  appContainer: {
    flex: 1,
    height: "auto",
    background: "#0a0e27",
    color: "#e2e8f0",
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    display: "flex",
    overflow: "hidden",
    margin: 0,
    padding: 0,
  },

  // ========== SIDEBAR ==========
  sidebar: (isCollapsed) => ({
    width: isCollapsed ? "70px" : "240px",
    height: "100vh",
    background: "linear-gradient(180deg, #1a3d5c 0%, #0f172a 50%, #1a2332 100%)",
    borderRight: "3px solid #ff6b35",
    padding: "12px 0",
    display: "flex",
    flexDirection: "column",
    transition: "width 0.3s ease",
    boxShadow: "2px 0 12px rgba(255, 107, 53, 0.2)",
    zIndex: 100,
    overflowY: "auto",
  }),

  sidebarHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 12px",
    borderBottom: "1px solid #1e3a5f",
    marginBottom: "8px",
  },

  collapseBtn: {
    background: "none",
    border: "none",
    color: "#0ea5e9",
    cursor: "pointer",
    padding: "6px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "color 0.2s ease",
  },

  brandTitle: {
    fontSize: "13px",
    fontWeight: "700",
    background: "linear-gradient(135deg, #ff6b35 0%, #ffa500 100%)",
    backgroundClip: "text",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    margin: "0",
    letterSpacing: "1px",
    flex: 1,
    textAlign: "center",
  },

  sidebarSection: {
    padding: "8px 0",
    marginBottom: "12px",
    borderBottom: "1px solid #1e3a5f",
  },

  sectionTitle: {
    fontSize: "10px",
    fontWeight: "700",
    color: "#64748b",
    padding: "8px 16px",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },

  sidebarBtn: {
    background: "none",
    border: "none",
    color: "#cbd5e1",
    padding: "12px 12px",
    margin: "0 6px",
    borderRadius: "6px",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: "500",
    display: "flex",
    alignItems: "center",
    justifyContent: "flex-start",
    transition: "all 0.25s ease",
    textAlign: "left",
  },

  sidebarbtnActive: {
    background: "rgba(14, 165, 233, 0.15)",
    color: "#0ea5e9",
    borderLeft: "3px solid #0ea5e9",
    paddingLeft: "9px",
  },

  // ========== MAIN CONTENT ==========
  mainContent: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },

  // ========== TOP BAR ==========
  topbar: {
    background: "linear-gradient(90deg, #1a3d5c 0%, #111c3a 50%, #1a2332 100%)",
    borderBottom: "2px solid #ff6b35",
    padding: "12px 20px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    boxShadow: "0 4px 12px rgba(255, 107, 53, 0.2)",
    flexShrink: 0,
  },

  topbarLeft: {
    display: "flex",
    alignItems: "center",
    gap: "20px",
  },

  caseSection: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },

  caseLabel: {
    fontSize: "11px",
    fontWeight: "700",
    color: "#64748b",
    textTransform: "uppercase",
  },

  caseId: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#0ea5e9",
    cursor: "pointer",
    padding: "4px 8px",
    borderRadius: "4px",
    transition: "background 0.2s ease",
  },

  caseInput: {
    background: "#1e3a5f",
    border: "1px solid #0ea5e9",
    color: "#0ea5e9",
    padding: "4px 8px",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: "600",
    outline: "none",
  },

  selectedTag: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "11px",
    color: "#94a3b8",
    background: "#1e3a5f",
    padding: "4px 10px",
    borderRadius: "4px",
    border: "1px solid #0ea5e9",
  },

  topbarRight: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },

  timestamp: {
    fontSize: "11px",
    color: "#64748b",
    whiteSpace: "nowrap",
  },

  toolbarBtn: {
    background: "#1e3a5f",
    border: "1px solid #0ea5e9",
    color: "#0ea5e9",
    width: "36px",
    height: "36px",
    borderRadius: "6px",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "all 0.2s ease",
  },

  // ========== PAGE CONTAINER ==========
  pageContainer: {
    flex: 1,
    overflow: "auto",
    padding: "12px",
    background: "#0a0e27",
    margin: 0,
    height: "calc(100vh - 64px)",
  },
};
