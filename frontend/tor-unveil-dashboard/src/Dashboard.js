import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Dashboard.css";

/**
 * Dashboard.js — PHASE-1 ENTRY SCREEN (POLICE RECORDS STYLE)
 * Tamil Nadu Police Cyber Crime Wing - Case Management System
 * 
 * Design: Government records system - table layout, borders, monochrome with navy accents
 * No cards, no charts - pure tabular data display
 */

// Sample case data - in production, this would come from backend API
const SAMPLE_CASES = [
  {
    caseId: "TN/CYB/2024/001234",
    caseType: "Dark Web",
    evidenceStatus: "Uploaded",
    analysisStatus: "Completed",
    confidenceLevel: "High",
    lastUpdated: "18-12-2024 14:32"
  },
  {
    caseId: "TN/CYB/2024/001235",
    caseType: "Cyber Crime",
    evidenceStatus: "Uploaded",
    analysisStatus: "In Progress",
    confidenceLevel: "Medium",
    lastUpdated: "18-12-2024 11:15"
  },
  {
    caseId: "TN/CYB/2024/001236",
    caseType: "Financial",
    evidenceStatus: "Pending",
    analysisStatus: "Not Started",
    confidenceLevel: "Low",
    lastUpdated: "17-12-2024 16:45"
  },
  {
    caseId: "TN/CYB/2024/001237",
    caseType: "Dark Web",
    evidenceStatus: "Uploaded",
    analysisStatus: "In Progress",
    confidenceLevel: "Medium",
    lastUpdated: "17-12-2024 09:22"
  },
  {
    caseId: "TN/CYB/2024/001238",
    caseType: "Cyber Crime",
    evidenceStatus: "Uploaded",
    analysisStatus: "Completed",
    confidenceLevel: "High",
    lastUpdated: "16-12-2024 18:10"
  },
  {
    caseId: "TN/CYB/2024/001239",
    caseType: "Financial",
    evidenceStatus: "Uploaded",
    analysisStatus: "Completed",
    confidenceLevel: "High",
    lastUpdated: "16-12-2024 14:55"
  },
  {
    caseId: "TN/CYB/2024/001240",
    caseType: "Dark Web",
    evidenceStatus: "Pending",
    analysisStatus: "Not Started",
    confidenceLevel: "Low",
    lastUpdated: "15-12-2024 10:30"
  },
  {
    caseId: "TN/CYB/2024/001241",
    caseType: "Cyber Crime",
    evidenceStatus: "Uploaded",
    analysisStatus: "In Progress",
    confidenceLevel: "Medium",
    lastUpdated: "15-12-2024 08:45"
  }
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [cases] = useState(SAMPLE_CASES);
  const [selectedCase, setSelectedCase] = useState(null);

  const handleRowClick = (caseItem) => {
    setSelectedCase(caseItem.caseId === selectedCase ? null : caseItem.caseId);
  };

  const handleViewCase = (caseItem) => {
    // Navigate to investigation page with case details
    navigate("/investigation", { state: { caseId: caseItem.caseId } });
  };

  const handleRegisterNewCase = () => {
    navigate("/investigation");
  };

  // Status badge styling helper
  const getEvidenceStatusClass = (status) => {
    switch (status) {
      case "Uploaded": return "status-uploaded";
      case "Pending": return "status-pending";
      default: return "";
    }
  };

  const getAnalysisStatusClass = (status) => {
    switch (status) {
      case "Completed": return "status-completed";
      case "In Progress": return "status-in-progress";
      case "Not Started": return "status-not-started";
      default: return "";
    }
  };

  const getConfidenceClass = (level) => {
    switch (level) {
      case "High": return "confidence-high";
      case "Medium": return "confidence-medium";
      case "Low": return "confidence-low";
      default: return "";
    }
  };

  const getCaseTypeClass = (type) => {
    switch (type) {
      case "Dark Web": return "type-darkweb";
      case "Cyber Crime": return "type-cybercrime";
      case "Financial": return "type-financial";
      default: return "";
    }
  };

  return (
    <div className="records-dashboard">
      {/* Page Header */}
      <div className="records-header">
        <div className="header-left">
          <h1 className="page-title">Case Records</h1>
          <p className="page-subtitle">Cyber Crime Investigation Management System</p>
        </div>
        <div className="header-right">
          <button className="btn-register" onClick={handleRegisterNewCase}>
            + Register New Case
          </button>
        </div>
      </div>

      {/* Summary Bar */}
      <div className="summary-bar">
        <div className="summary-item">
          <span className="summary-label">Total Cases:</span>
          <span className="summary-value">{cases.length}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Pending Evidence:</span>
          <span className="summary-value">{cases.filter(c => c.evidenceStatus === "Pending").length}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Analysis In Progress:</span>
          <span className="summary-value">{cases.filter(c => c.analysisStatus === "In Progress").length}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Completed:</span>
          <span className="summary-value">{cases.filter(c => c.analysisStatus === "Completed").length}</span>
        </div>
      </div>

      {/* Case Records Table */}
      <div className="records-table-container">
        <table className="records-table">
          <thead>
            <tr>
              <th className="th-serial">S.No</th>
              <th className="th-caseid">Case ID</th>
              <th className="th-casetype">Case Type</th>
              <th className="th-evidence">Evidence Status</th>
              <th className="th-analysis">Analysis Status</th>
              <th className="th-confidence">Confidence Level</th>
              <th className="th-updated">Last Updated</th>
              <th className="th-action">Action</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((caseItem, index) => (
              <tr 
                key={caseItem.caseId}
                className={`case-row ${selectedCase === caseItem.caseId ? "row-selected" : ""}`}
                onClick={() => handleRowClick(caseItem)}
              >
                <td className="td-serial">{index + 1}</td>
                <td className="td-caseid">
                  <code>{caseItem.caseId}</code>
                </td>
                <td className="td-casetype">
                  <span className={`type-badge ${getCaseTypeClass(caseItem.caseType)}`}>
                    {caseItem.caseType}
                  </span>
                </td>
                <td className="td-evidence">
                  <span className={`status-badge ${getEvidenceStatusClass(caseItem.evidenceStatus)}`}>
                    {caseItem.evidenceStatus}
                  </span>
                </td>
                <td className="td-analysis">
                  <span className={`status-badge ${getAnalysisStatusClass(caseItem.analysisStatus)}`}>
                    {caseItem.analysisStatus}
                  </span>
                </td>
                <td className="td-confidence">
                  <span className={`confidence-badge ${getConfidenceClass(caseItem.confidenceLevel)}`}>
                    {caseItem.confidenceLevel}
                  </span>
                </td>
                <td className="td-updated">{caseItem.lastUpdated}</td>
                <td className="td-action">
                  <button 
                    className="btn-view"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleViewCase(caseItem);
                    }}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Table Footer */}
      <div className="records-footer">
        <div className="footer-info">
          Showing {cases.length} of {cases.length} records
        </div>
        <div className="footer-note">
          * Click on a row to select. Click "View" to open case details.
        </div>
      </div>
    </div>
  );
}
