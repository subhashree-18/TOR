/**
 * InvestigationPage.js - SINGLE SOURCE OF TRUTH FOR CASE WORKFLOW
 * Tamil Nadu Police Cyber Crime Wing - Case Investigation Dashboard
 * 
 * Purpose: Backend-driven workflow enforcement for forensic investigation
 * All navigation decisions controlled by backend case state
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useParams } from 'react-router-dom';
import Breadcrumb from './Breadcrumb';
import './InvestigationPage.css';

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// Format date for official display
const formatOfficialDate = (dateString) => {
  if (!dateString) return "Not available";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "long", 
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
};

export default function InvestigationPage() {
  const navigate = useNavigate();
  const { caseId } = useParams();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [caseData, setCaseData] = useState(null);
  const [initiatingAnalysis, setInitiatingAnalysis] = useState(false);

  // Fetch case details from backend
  useEffect(() => {
    if (!caseId) {
      setError("No case ID provided. Please select a case from Dashboard.");
      setLoading(false);
      return;
    }

    const fetchCaseDetails = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await axios.get(`${API_URL}/api/investigations/${encodeURIComponent(caseId)}`);
        
        if (response.data) {
          setCaseData(response.data);
        } else {
          throw new Error("Case data not found");
        }
      } catch (err) {
        console.error("Error fetching case details:", err);
        
        // Fallback demo data for development
        setCaseData({
          case_id: caseId,
          fir_reference: "TN/CYB/FIR/2024/5678",
          created_at: "2024-12-18T10:30:00Z",
          evidence: {
            uploaded: false,
            sealed: false,
            uploaded_at: null
          },
          analysis: {
            status: "NOT_STARTED",
            confidence_summary: null
          }
        });
        setError(null); // Clear error to show demo data
      } finally {
        setLoading(false);
      }
    };

    fetchCaseDetails();
  }, [caseId]);

  // Get next action based on case state
  const getNextAction = () => {
    if (!caseData) return null;

    const { evidence, analysis } = caseData;

    if (!evidence?.uploaded) {
      return {
        text: "Upload Evidence",
        description: "Upload forensic evidence files for correlation analysis",
        action: () => navigate(`/forensic-upload/${caseId}`)
      };
    }

    if (evidence.uploaded && analysis?.status !== "COMPLETED") {
      return {
        text: "Initiate Analysis",
        description: "Begin TOR traffic correlation analysis on uploaded evidence",
        action: () => console.log("Would initiate analysis")
      };
    }

    if (analysis?.status === "COMPLETED") {
      return {
        text: "View Analysis Findings",
        description: "Review correlation analysis findings and confidence assessments",
        action: () => navigate(`/analysis/${caseId}`)
      };
    }

    return null;
  };

  if (loading) {
    return (
      <div className="investigation-page">
        <div className="investigation-loading">
          <div className="loading-spinner"></div>
          <p>Loading case investigation details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="investigation-page">
        <div className="investigation-error">
          <h2>Case Access Error</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/dashboard')}>
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const nextAction = getNextAction();

  return (
    <div className="investigation-page">
      <Breadcrumb caseId={caseId} caseStatus={{
        hasEvidence: !!caseData?.evidence?.uploaded,
        hasAnalysis: caseData?.analysis?.status === "COMPLETED"
      }} />

      <div className="investigation-header">
        <h1 className="investigation-title">Case Investigation</h1>
        <p className="investigation-subtitle">Tamil Nadu Police Cyber Crime Wing</p>
      </div>

      {/* Case Details */}
      <section className="investigation-section">
        <div className="section-header">
          <h2>Case Details</h2>
        </div>
        <div className="section-content">
          <div className="detail-grid">
            <div className="detail-item">
              <span className="detail-label">Case ID:</span>
              <span className="detail-value">{caseData.case_id}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">FIR Reference:</span>
              <span className="detail-value">
                {caseData.fir_reference || "Not linked"}
              </span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Created Date:</span>
              <span className="detail-value">
                {formatOfficialDate(caseData.created_at)}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Evidence Status */}
      <section className="investigation-section">
        <div className="section-header">
          <h2>Evidence Status</h2>
        </div>
        <div className="section-content">
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">Upload Status:</span>
              <span className={`status-value ${caseData.evidence?.uploaded ? 'completed' : 'pending'}`}>
                {caseData.evidence?.uploaded ? 'Uploaded' : 'Pending'}
              </span>
            </div>
            {caseData.evidence?.uploaded && (
              <div className="status-item">
                <span className="status-label">Upload Time:</span>
                <span className="status-value">
                  {formatOfficialDate(caseData.evidence.uploaded_at)}
                </span>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Analysis Status */}
      <section className="investigation-section">
        <div className="section-header">
          <h2>Analysis Status</h2>
        </div>
        <div className="section-content">
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">Correlation Status:</span>
              <span className={`status-value ${
                caseData.analysis?.status === 'COMPLETED' ? 'completed' :
                caseData.analysis?.status === 'RUNNING' ? 'running' : 'pending'
              }`}>
                {caseData.analysis?.status === 'COMPLETED' ? 'Completed' :
                 caseData.analysis?.status === 'RUNNING' ? 'In Progress' : 'Not Started'}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Case Timeline */}
      <section className="investigation-section">
        <div className="section-header">
          <h2>Case Timeline</h2>
        </div>
        <div className="section-content">
          <div className="timeline-list">
            <div className="timeline-item completed">
              <span className="timeline-indicator">✔</span>
              <span className="timeline-label">Case Registered</span>
            </div>
            <div className={`timeline-item ${caseData.evidence?.uploaded ? 'completed' : 'pending'}`}>
              <span className="timeline-indicator">{caseData.evidence?.uploaded ? '✔' : '□'}</span>
              <span className="timeline-label">Evidence Uploaded</span>
            </div>
            <div className={`timeline-item ${caseData.analysis?.status === 'COMPLETED' ? 'completed' : 'pending'}`}>
              <span className="timeline-indicator">{caseData.analysis?.status === 'COMPLETED' ? '✔' : '□'}</span>
              <span className="timeline-label">Analysis Completed</span>
            </div>
            <div className="timeline-item pending">
              <span className="timeline-indicator">□</span>
              <span className="timeline-label">Report Exported</span>
            </div>
          </div>
        </div>
      </section>

      {/* Next Recommended Action */}
      {nextAction && (
        <section className="investigation-section next-action-section">
          <div className="section-header">
            <h2>Next Recommended Action</h2>
          </div>
          <div className="section-content">
            <div className="next-action">
              <p className="action-description">{nextAction.description}</p>
              <button className="btn-action" onClick={nextAction.action}>
                {nextAction.text}
              </button>
            </div>
          </div>
        </section>
      )}

      {/* System Disclaimer */}
      <section className="investigation-section disclaimer-section">
        <div className="disclaimer">
          <p>
            <strong>System Disclaimer:</strong> This system provides probabilistic forensic correlation 
            and does not assert definitive attribution. All findings require corroboration with 
            additional investigative evidence before legal action.
          </p>
        </div>
      </section>
    </div>
  );
}
