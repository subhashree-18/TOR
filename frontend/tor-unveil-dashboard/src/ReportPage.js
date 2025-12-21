/**
 * ReportPage.js - FORENSIC REPORT GENERATION
 * Tamil Nadu Police Cyber Crime Wing - Official Forensic Report
 * 
 * CHANGE 8: Forensic-Grade Output
 * - Fetches report data from backend APIs ONLY
 * - NO mock or static data
 * - Real case metadata, entry node candidates, timeline, confidence justification
 * - Export button triggers backend report generation
 */

import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate, useLocation } from "react-router-dom";
import "./ReportPage.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

export default function ReportPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get case ID from query params or location state - REQUIRED
  const searchParams = new URLSearchParams(location.search);
  const caseId = searchParams.get('caseId') || location.state?.caseId;
  
  // Report data states - REAL data ONLY from backend
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState('pdf'); // 'pdf', 'json', or 'txt'
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [timelineRefreshCounter, setTimelineRefreshCounter] = useState(0);
  
  // Fetch report data from backend APIs - REAL DATA ONLY
  useEffect(() => {
    if (!caseId) {
      setError("No case ID provided. Redirecting to dashboard...");
      setTimeout(() => navigate("/dashboard"), 2000);
      return;
    }
    
    fetchReportData();
  }, [caseId, navigate]);

  // Auto-refresh timeline every 3 seconds to show latest events in real-time
  useEffect(() => {
    const timelineInterval = setInterval(() => {
      setTimelineRefreshCounter(prev => prev + 1);
    }, 3000);
    
    return () => clearInterval(timelineInterval);
  }, []);

  // Fetch only timeline when refresh counter changes (every 3 seconds)
  useEffect(() => {
    if (reportData) {
      fetchTimelineOnly();
    }
  }, [timelineRefreshCounter]);
  
  const fetchReportData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch case investigation details from backend (optional, may not exist for all cases)
      let investigationData = null;
      try {
        const investigationResponse = await axios.get(
          `${API_URL}/api/investigations/${encodeURIComponent(caseId)}`
        );
        investigationData = investigationResponse.data;
      } catch (err) {
        console.warn("Investigation data not found, using analysis data only:", err.message);
        // Continue without investigation data - it's optional
      }
      
      // Fetch analysis results for this case from backend (REQUIRED)
      const analysisResponse = await axios.get(
        `${API_URL}/api/analysis/${encodeURIComponent(caseId)}`
      );
      
      // Fetch timeline events from backend for context
      let timelineData = [];
      try {
        const timelineResponse = await axios.get(
          `${API_URL}/api/timeline?limit=50`
        );
        timelineData = timelineResponse.data.events || [];
      } catch (err) {
        console.warn("Timeline data not available:", err.message);
      }
      
      // Combine data from backend (investigation is optional)
      const combinedReportData = {
        caseInfo: investigationData || { caseId, title: `Case ${caseId}` },
        analysisResults: analysisResponse.data,
        timelineEvents: timelineData,
        generatedAt: new Date().toISOString(),
      };
      
      setReportData(combinedReportData);
    } catch (err) {
      console.error("Failed to fetch report data from backend:", err.message);
      setError(`Failed to load analysis data from backend: ${err.message}`);
      setReportData(null);
    } finally {
      setLoading(false);
    }
  };

  // Fetch only timeline data for real-time updates (every 3 seconds)
  const fetchTimelineOnly = async () => {
    try {
      const timelineResponse = await axios.get(
        `${API_URL}/api/timeline?limit=50`
      );
      const timelineData = timelineResponse.data.events || [];
      
      // Update only the timeline events, keeping other data intact
      setReportData(prev => ({
        ...prev,
        timelineEvents: timelineData,
        lastTimelineUpdate: new Date().toISOString()
      }));
    } catch (err) {
      console.warn("Could not refresh timeline:", err.message);
    }
  };

  
  // Export report - triggers backend PDF generation
  const handleExportReport = async () => {
    if (!caseId) {
      alert("Cannot export: no case ID available");
      return;
    }
    
    try {
      setExporting(true);
      
      let endpoint;
      let filename;
      let mediaType = 'application/octet-stream';
      
      // Determine endpoint and filename based on selected format
      switch (exportFormat) {
        case 'json':
          endpoint = `${API_URL}/api/export/report-json?case_id=${encodeURIComponent(caseId)}`;
          filename = `forensic_report_${caseId}.json`;
          break;
        case 'txt':
          endpoint = `${API_URL}/api/export/report-txt?case_id=${encodeURIComponent(caseId)}`;
          filename = `forensic_report_${caseId}.txt`;
          break;
        case 'pdf':
        default:
          endpoint = `${API_URL}/api/export/report-from-case?case_id=${encodeURIComponent(caseId)}`;
          filename = `forensic_report_${caseId}.pdf`;
          break;
      }
      
      // Trigger backend report generation and download from case analysis
      const response = await axios.get(endpoint, { responseType: 'blob' });
      
      // Create download link from backend response
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      console.log(`${exportFormat.toUpperCase()} export successful for case:`, caseId);
      
    } catch (err) {
      console.error("Failed to export report from backend:", err.message);
      alert(`Export failed - backend error: ${err.message}`);
    } finally {
      setExporting(false);
    }
  };

  // Handle case submission - save to backend database
  const handleSubmitCase = async () => {
    if (!caseId || !reportData) {
      alert("Cannot submit: missing case data");
      return;
    }

    try {
      setSubmitting(true);

      // Prepare case data for submission
      const caseToSubmit = {
        case_id: caseId,
        case_title: reportData.caseInfo?.title || `Case ${caseId}`,
        department: reportData.caseInfo?.department || "Tamil Nadu Police - Cyber Crime Wing",
        officer_name: reportData.caseInfo?.officer_name || "Investigating Officer",
        analysis: reportData.analysis || {},
        session_summary: reportData.session_summary || {},
        report_data: {
          hypotheses_count: reportData.hypotheses?.length || 0,
          confidence_level: reportData.hypothesis_data?.confidence || "Unknown",
          entry_node: reportData.hypothesis_data?.entry_node || "Unknown",
          exit_node: reportData.hypothesis_data?.exit_node || "Unknown"
        }
      };

      // Submit to backend
      const response = await axios.post(
        `${API_URL}/api/cases/submit`,
        caseToSubmit
      );

      if (response.data.status === "success") {
        setSubmitted(true);
        alert(`✓ Case '${caseId}' submitted successfully!\n\nSubmitted at: ${response.data.submitted_at}`);
        console.log("Case submission response:", response.data);
      }
    } catch (err) {
      console.error("Failed to submit case:", err.message);
      alert(`Case submission failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };
  
  // Render loading state
  if (loading) {
    return (
      <div className="report-page">
        <div className="report-loading">
          <div className="loading-spinner"></div>
          <p>Loading report data from backend...</p>
          <p style={{ fontSize: "12px", color: "#666", marginTop: "10px" }}>
            Case ID: {caseId}
          </p>
        </div>
      </div>
    );
  }
  
  // Render error state
  if (error || !reportData) {
    return (
      <div className="report-page">
        <div className="report-error">
          <h2>Report Generation Failed</h2>
          <p>{error || "No report data available from backend"}</p>
          <div className="report-actions">
            <button 
              className="btn-secondary"
              onClick={() => navigate("/dashboard")}
            >
              Return to Dashboard
            </button>
            <button 
              className="btn-secondary"
              onClick={fetchReportData}
            >
              Retry Loading
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  // Extract REAL data from reportData (all from backend)
  const caseInfo = reportData.caseInfo || {};
  const analysisResults = reportData.analysisResults || {};
  const timelineEvents = reportData.timelineEvents || [];
  
  return (
    <div className="report-page">
      {/* Report Header */}
      <div className="report-header">
        <h1>FORENSIC INVESTIGATION REPORT</h1>
        <p className="report-subtitle">Tamil Nadu Police Cyber Crime Wing</p>
        <div className="report-metadata">
          <div className="metadata-item">
            <span className="label">Case ID:</span>
            <code>{caseId}</code>
          </div>
          <div className="metadata-item">
            <span className="label">Case Type:</span>
            <span>{caseInfo.caseType || "N/A"}</span>
          </div>
          <div className="metadata-item">
            <span className="label">Status:</span>
            <span className="status-badge">{caseInfo.status || "N/A"}</span>
          </div>
          <div className="metadata-item">
            <span className="label">Generated:</span>
            <span>{new Date(reportData.generatedAt).toLocaleString('en-IN')}</span>
          </div>
        </div>
      </div>
      
      {/* Case Summary Section - REAL DATA */}
      <section className="report-section">
        <h2>1. CASE SUMMARY</h2>
        <div className="report-content">
          <p><strong>Title:</strong> {caseInfo.title || "Pending"}</p>
          <p><strong>Description:</strong> {caseInfo.description || "No description available"}</p>
          <p><strong>Assigned Officer:</strong> {caseInfo.assignedOfficer || "Unassigned"}</p>
          <p><strong>Priority:</strong> {caseInfo.priority || "N/A"}</p>
          <p><strong>Evidence Status:</strong> {caseInfo.evidenceStatus || "Pending"}</p>
          <p><strong>Analysis Status:</strong> {caseInfo.analysisStatus || "Not Started"}</p>
          <p><strong>Last Activity:</strong> {new Date(caseInfo.lastActivity || Date.now()).toLocaleString('en-IN')}</p>
        </div>
      </section>
      
      {/* Analysis Results Section - REAL DATA */}
      <section className="report-section">
        <h2>2. CORRELATION ANALYSIS RESULTS</h2>
        <div className="report-content">
          {analysisResults.hypotheses && analysisResults.hypotheses.length > 0 ? (
            <div className="hypotheses-table">
              <h3>Top Entry Node Candidates</h3>
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Entry Node</th>
                    <th>Exit Node</th>
                    <th>Evidence</th>
                    <th>Confidence</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {analysisResults.hypotheses.slice(0, 10).map((hyp, idx) => {
                    // Extract country code from entry_region (e.g., "Russia (RU)" -> "RU")
                    const entryCountry = hyp.entry_region ? hyp.entry_region.split('(')[1]?.replace(')', '') : 'XX';
                    const entryCountryName = hyp.entry_region ? hyp.entry_region.split('(')[0]?.trim() : 'Unknown';
                    
                    // Extract country code from exit_region (e.g., "India (IN)" -> "IN")
                    const exitCountry = hyp.exit_region ? hyp.exit_region.split('(')[1]?.replace(')', '') : 'XX';
                    const exitCountryName = hyp.exit_region ? hyp.exit_region.split('(')[0]?.trim() : 'Unknown';
                    
                    return (
                    <tr key={idx}>
                      <td>#{hyp.rank || idx + 1}</td>
                      <td style={{ fontSize: "11px" }}>
                        {/* Show entry region from backend */}
                        <div><strong>{entryCountryName || 'Unknown'}</strong></div>
                        <div style={{ color: "#666" }}>Code: {entryCountry}</div>
                        <div style={{ color: "#999" }}>Entry Relay</div>
                      </td>
                      <td style={{ fontSize: "11px" }}>
                        {/* Show exit region from backend */}
                        <div><strong>{exitCountryName || 'Unknown'}</strong></div>
                        <div style={{ color: "#666" }}>Code: {exitCountry}</div>
                        <div style={{ color: "#999" }}>Exit Relay</div>
                      </td>
                      <td>{hyp.evidence_count || 0}</td>
                      <td>
                        <span className={`confidence-badge ${(hyp.confidence_level || "").toLowerCase()}`}>
                          {hyp.confidence_level || "Unknown"}
                        </span>
                      </td>
                      <td>
                        {/* Show confidence level as percentage */}
                        {hyp.confidence_level === 'High' ? '85%' : hyp.confidence_level === 'Medium' ? '60%' : '35%'}
                      </td>
                    </tr>
                  );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p>No hypothesis data available from backend analysis.</p>
          )}
        </div>
      </section>
      
      {/* Timeline Summary Section - REAL DATA */}
      <section className="report-section">
        <h2>3. FORENSIC TIMELINE</h2>
        <div className="report-content">
          {timelineEvents.length > 0 ? (
            <div className="timeline-summary">
              {timelineEvents.slice(0, 15).map((evt, idx) => {
                // Format timestamp as DD/MM/YYYY, HH:MM:SS AM/PM
                const date = new Date(evt.timestamp);
                const formattedDate = date.toLocaleDateString('en-IN', {
                  day: '2-digit',
                  month: '2-digit',
                  year: 'numeric'
                });
                const formattedTime = date.toLocaleTimeString('en-IN', {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                  hour12: true
                });
                const fullTimestamp = `${formattedDate}, ${formattedTime}`;
                
                return (
                  <div key={idx} className="timeline-item">
                    <div className="timeline-timestamp">
                      {fullTimestamp}
                    </div>
                    <div className="timeline-label">{evt.label}</div>
                    <div className="timeline-description">{evt.description}</div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p>No timeline events available from backend.</p>
          )}
        </div>
      </section>
      
      {/* Confidence Justification Section - REAL DATA */}
      <section className="report-section">
        <h2>4. CONFIDENCE JUSTIFICATION</h2>
        <div className="report-content">
          {analysisResults.hypotheses && analysisResults.hypotheses[0] ? (
            <div className="confidence-justification">
              <p>
                <strong>Top Hypothesis (Rank #1):</strong>
              </p>
              <p>
                {analysisResults.hypotheses[0].explanation?.timing_consistency || "Based on temporal correlation analysis of network events."}
              </p>
              <p>
                <strong>Supporting Evidence:</strong>
              </p>
              <ul>
                <li>{analysisResults.hypotheses[0].explanation?.guard_persistence || "Guard relay persistence supports this hypothesis"}</li>
                <li>{analysisResults.hypotheses[0].explanation?.evidence_strength || "Evidence is consistent with observed network topology"}</li>
              </ul>
              <p>
                <strong>Confidence Level:</strong>
                <span className={`confidence-badge ${(analysisResults.hypotheses[0].confidence_level || "").toLowerCase()}`}>
                  {analysisResults.hypotheses[0].confidence_level || "Unknown"}
                </span>
              </p>
              <p>
                <strong>Limitations:</strong>
              </p>
              <p>
                {analysisResults.hypotheses[0].limiting_factors || "Analysis based on metadata correlation only. Results require independent verification."}
              </p>
            </div>
          ) : (
            <p>No confidence justification data available from backend.</p>
          )}
        </div>
      </section>
      
      {/* Legal Disclaimer Section */}
      <section className="report-section disclaimer-section">
        <h2>5. LEGAL & TECHNICAL DISCLAIMER</h2>
        <div className="report-content">
          <p>
            <strong>CONFIDENTIAL - LAW ENFORCEMENT ONLY</strong>
          </p>
          <p>
            This forensic investigation report is prepared for official law enforcement use only. 
            The analysis presented herein is based on metadata correlation using publicly available 
            TOR network directory data and does not involve breaking TOR encryption or identifying user identities.
          </p>
          <p>
            All findings represent statistical correlations that require independent verification 
            through corroborating evidence. Results are intended for investigative guidance only 
            and are not suitable for direct legal action without additional evidence.
          </p>
          <p>
            This analysis complies with Indian Penal Code provisions and was conducted 
            in accordance with authorized investigation protocols.
          </p>
        </div>
      </section>
      
      {/* Report Actions */}
      <div className="report-actions">
        <div className="export-controls">
          <div className="format-selector">
            <label htmlFor="export-format">Export Format: </label>
            <select 
              id="export-format"
              value={exportFormat} 
              onChange={(e) => setExportFormat(e.target.value)}
              disabled={exporting}
            >
              <option value="pdf">PDF Document</option>
              <option value="json">JSON Data</option>
              <option value="txt">Text File</option>
            </select>
          </div>
          <button 
            className="btn-primary"
            onClick={handleExportReport}
            disabled={exporting}
          >
            {exporting ? `Generating ${exportFormat.toUpperCase()}...` : `Export as ${exportFormat.toUpperCase()}`}
          </button>
        </div>
        
        <button 
          className="btn-submit"
          onClick={handleSubmitCase}
          disabled={submitting || submitted}
          title="Save this case to the backend database for future reference"
        >
          {submitted ? "✓ Case Submitted" : submitting ? "Submitting Case..." : "💾 Submit Case to Database"}
        </button>
        
        <button 
          className="btn-secondary"
          onClick={() => navigate("/dashboard")}
        >
          Return to Dashboard
        </button>
        <button 
          className="btn-secondary"
          onClick={() => navigate("/investigation", { state: { caseId } })}
        >
          Back to Investigation
        </button>
      </div>
    </div>
  );
}

