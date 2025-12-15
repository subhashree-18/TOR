/**
 * InvestigationPage.js - Main Investigation Workflow Dashboard
 * 
 * Shows the complete police investigation workflow with case management
 */

import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { BarChart2, FileText, Download, Upload, Zap, Briefcase } from "lucide-react";
import ImprovedInvestigationWorkflow from "./ImprovedInvestigationWorkflow";
import MandatoryDisclaimer from "./MandatoryDisclaimer";
import "./InvestigationPage.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function InvestigationPage() {
  const navigate = useNavigate();
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(() => {
    // Check localStorage for persisted acceptance
    const stored = localStorage.getItem("disclaimerAccepted");
    return stored === "true";
  });
  const [caseData, setCaseData] = useState({
    caseId: "CASE-2025-001",
    officerName: "Officer",
    startedAt: new Date(),
  });
  const [torDataCount, setTorDataCount] = useState(0);
  const [pathsFound, setPathsFound] = useState(0);
  const [highConfidencePaths, setHighConfidencePaths] = useState(0);
  const [loading, setLoading] = useState(true);
  const [editingOfficer, setEditingOfficer] = useState(false);
  const [tempOfficerName, setTempOfficerName] = useState(caseData.officerName);

  // Simulate data loading
  useEffect(() => {
    const loadData = async () => {
      try {
        // Get relay count
        const relaysRes = await axios.get(`${API_URL}/relays?limit=1`);
        const totalRelays = (relaysRes.data?.total || relaysRes.data?.count || 0);
        setTorDataCount(totalRelays);

        // Get top paths to show evidence count
        const pathsRes = await axios.get(`${API_URL}/paths/top?limit=200`);
        // Handle both direct array and nested response structure
        const paths = Array.isArray(pathsRes.data) ? pathsRes.data : (pathsRes.data?.results || []);
        setPathsFound(paths.length);

        // Count high-confidence paths (>80%)
        const highConf = Array.isArray(paths) ? paths.filter((p) => (p.score || 0) > 0.80).length : 0;
        setHighConfidencePaths(highConf);

        setLoading(false);
      } catch (err) {
        console.error("Error loading investigation data:", err);
        setLoading(false);
      }
    };

    const timer = setTimeout(loadData, 500);
    return () => clearTimeout(timer);
  }, []);

  const handleUpdateOfficer = () => {
    setCaseData((prev) => ({
      ...prev,
      officerName: tempOfficerName,
    }));
    setEditingOfficer(false);
  };

  // Quick Actions Handlers
  const handleViewPaths = () => {
    navigate("/paths");
  };

  const handleGenerateReport = () => {
    // Generate and download report as JSON
    const reportData = {
      case: caseData,
      investigation: {
        torDataCount,
        pathsFound,
        highConfidencePaths,
        timestamp: new Date().toISOString(),
      },
      generatedAt: new Date().toLocaleString(),
    };
    
    const dataStr = JSON.stringify(reportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${caseData.caseId}_report_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleExportEvidence = () => {
    // Export evidence data as JSON
    const evidenceData = {
      caseId: caseData.caseId,
      officer: caseData.officerName,
      investigationStarted: caseData.startedAt,
      evidenceCount: {
        relays: torDataCount,
        paths: pathsFound,
        highConfidencePaths: highConfidencePaths,
      },
      exportedAt: new Date().toISOString(),
      status: "Ready for forensic analysis",
    };
    
    const dataStr = JSON.stringify(evidenceData, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${caseData.caseId}_evidence_${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleAddPcapLog = () => {
    navigate("/forensic");
  };

  return (
    <div className="investigation-page">
      {/* Mandatory Disclaimer Modal - MUST be accepted before proceeding */}
      {!disclaimerAccepted && (
        <MandatoryDisclaimer
          isModal={true}
          onAcknowledge={() => {
            setDisclaimerAccepted(true);
            localStorage.setItem("disclaimerAccepted", "true"); // Persist acceptance
          }}
        />
      )}

      {/* Page Header */}
      <div className="page-header">
        <h1><Briefcase size={32} style={{marginRight: "10px", verticalAlign: "middle"}} />Active Investigation</h1>
        <p className="page-subtitle">
          Tamil Nadu Police Cybercrime Investigation Unit - TOR Network Forensics
        </p>
      </div>

      {/* Case Information Card */}
      <div className="case-info-card">
        <div className="case-info-left">
          <div className="case-field">
            <label>Case ID:</label>
            <code className="case-id">{caseData.caseId}</code>
          </div>
          <div className="case-field">
            <label>Assigned Officer:</label>
            {editingOfficer ? (
              <div className="officer-edit">
                <input
                  type="text"
                  value={tempOfficerName}
                  onChange={(e) => setTempOfficerName(e.target.value)}
                  className="officer-input"
                  placeholder="Enter officer name"
                />
                <button
                  className="save-btn"
                  onClick={handleUpdateOfficer}
                  disabled={!tempOfficerName.trim()}
                >
                  Save
                </button>
                <button
                  className="cancel-btn"
                  onClick={() => setEditingOfficer(false)}
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div className="officer-display">
                <span>{caseData.officerName}</span>
                <button
                  className="edit-btn"
                  onClick={() => {
                    setTempOfficerName(caseData.officerName);
                    setEditingOfficer(true);
                  }}
                >
                  Edit
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="case-info-right">
          <div className="info-stat">
            <div className="stat-value">{torDataCount}</div>
            <div className="stat-label">TOR Relays Indexed</div>
          </div>
          <div className="info-stat">
            <div className="stat-value">{pathsFound}</div>
            <div className="stat-label">Paths Analyzed</div>
          </div>
          <div className="info-stat">
            <div className="stat-value">{highConfidencePaths}</div>
            <div className="stat-label">High-Confidence Paths</div>
          </div>
        </div>
      </div>

      {/* Main Workflow Component */}
      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading investigation data...</p>
        </div>
      ) : (
        <ImprovedInvestigationWorkflow
          caseId={caseData.caseId}
          officerName={caseData.officerName}
          startedAt={caseData.startedAt}
          torDataCount={torDataCount}
          pathsFound={pathsFound}
          highConfidencePaths={highConfidencePaths}
        />
      )}

      {/* Quick Actions */}
      <div className="quick-actions">
        <h3><Zap size={20} style={{marginRight: "8px", verticalAlign: "middle"}} />Quick Actions</h3>
        <div className="action-buttons">
          <button className="action-btn primary" onClick={handleViewPaths}>
            <BarChart2 size={16} style={{marginRight: "8px"}} />View Paths
          </button>
          <button className="action-btn secondary" onClick={handleGenerateReport}>
            <FileText size={16} style={{marginRight: "8px"}} />Generate Report
          </button>
          <button className="action-btn secondary" onClick={handleExportEvidence}>
            <Download size={16} style={{marginRight: "8px"}} />Export Evidence
          </button>
          <button className="action-btn secondary" onClick={handleAddPcapLog}>
            <Upload size={16} style={{marginRight: "8px"}} />Add PCAP Log
          </button>
        </div>
      </div>
    </div>
  );
}
