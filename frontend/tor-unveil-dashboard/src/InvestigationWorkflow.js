/**
 * InvestigationWorkflow.js - Police Investigation Workflow
 * 
 * Implements a 5-step investigation workflow suitable for police cyber crime units:
 * 1. Case Created - Initial case setup with ID and officer info
 * 2. TOR Data Collected - Automated collection from Onionoo/CollecTor
 * 3. Correlation Performed - Time-based path analysis
 * 4. High-Confidence Paths - Results ranked by score
 * 5. Evidence Exported - Ready for court presentation
 * 
 * Each step shows:
 * - Current status (Pending / In Progress / Completed)
 * - Plain-language explanation
 * - Relevant data or actions
 * - Timestamp of completion
 */

import React, { useState, useEffect } from "react";
import {
  CheckCircle2,
  Check,
  Clock,
  AlertCircle,
  FileText,
  Database,
  GitBranch,
  Download,
  User,
  Calendar,
  Scale,
} from "lucide-react";
import "./InvestigationWorkflow.css";

export default function InvestigationWorkflow({
  caseId = "CASE-2025-001",
  officerName = "Officer",
  startedAt = new Date(),
  torDataCount = 0,
  pathsFound = 0,
  highConfidencePaths = 0,
}) {
  const [completedSteps, setCompletedSteps] = useState({
    step1: true, // Case created
    step2: false, // TOR data
    step3: false, // Correlation
    step4: false, // High-confidence paths
    step5: false, // Evidence export
  });

  const [currentStep, setCurrentStep] = useState(1);
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState("");

  // Simulate step progression
  useEffect(() => {
    if (torDataCount > 0 && !completedSteps.step2) {
      const timer = setTimeout(() => {
        setCompletedSteps((prev) => ({ ...prev, step2: true }));
        addNote(
          `TOR Data Collected: ${torDataCount} relays indexed from Onionoo`
        );
        setCurrentStep(2);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [torDataCount, completedSteps.step2]);

  useEffect(() => {
    if (pathsFound > 0 && !completedSteps.step3) {
      const timer = setTimeout(() => {
        setCompletedSteps((prev) => ({ ...prev, step3: true }));
        addNote(`Correlation Performed: ${pathsFound} potential paths analyzed`);
        setCurrentStep(3);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [pathsFound, completedSteps.step3]);

  useEffect(() => {
    if (highConfidencePaths > 0 && !completedSteps.step4) {
      const timer = setTimeout(() => {
        setCompletedSteps((prev) => ({ ...prev, step4: true }));
        addNote(
          `High-Confidence Paths: ${highConfidencePaths} paths with strong evidence`
        );
        setCurrentStep(4);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [highConfidencePaths, completedSteps.step4]);

  const addNote = (note) => {
    const timestamp = new Date().toLocaleTimeString();
    setNotes((prev) => [
      ...prev,
      {
        id: Date.now(),
        text: note,
        timestamp,
        isSystem: true,
      },
    ]);
  };

  const handleAddNote = () => {
    if (newNote.trim()) {
      const timestamp = new Date().toLocaleTimeString();
      setNotes((prev) => [
        ...prev,
        {
          id: Date.now(),
          text: newNote,
          timestamp,
          isSystem: false,
          officer: officerName,
        },
      ]);
      setNewNote("");
    }
  };

  const handleExport = () => {
    setCompletedSteps((prev) => ({ ...prev, step5: true }));
    addNote("Evidence exported - Ready for forensic analysis and court");
    setCurrentStep(5);
  };

  const getStepStatus = (stepNumber) => {
    const stepKey = `step${stepNumber}`;
    if (completedSteps[stepKey]) return "completed";
    if (currentStep === stepNumber) return "active";
    if (currentStep > stepNumber) return "completed";
    return "pending";
  };

  const getStatusIcon = (status) => {
    if (status === "completed") return <CheckCircle2 size={20} />;
    if (status === "active") return <Clock size={20} className="spinning" />;
    if (status === "pending") return <AlertCircle size={20} />;
  };

  const formatTime = (date) => {
    return new Date(date).toLocaleString();
  };

  return (
    <div className="investigation-workflow">
      {/* Header */}
      <div className="workflow-header">
        <div className="workflow-case-info">
          <h2><GitBranch size={28} style={{marginRight: "10px", verticalAlign: "middle"}} />Investigation Workflow</h2>
          <p className="case-id">Case ID: {caseId}</p>
          <p className="officer-info">Officer: {officerName}</p>
          <p className="started-at">Started: {formatTime(startedAt)}</p>
        </div>
        <div className="workflow-legend">
          <div className="legend-item">
            <CheckCircle2 size={16} className="status-completed" />
            <span>Completed</span>
          </div>
          <div className="legend-item">
            <Clock size={16} className="status-active spinning" />
            <span>In Progress</span>
          </div>
          <div className="legend-item">
            <AlertCircle size={16} className="status-pending" />
            <span>Pending</span>
          </div>
        </div>
      </div>

      {/* Workflow Steps */}
      <div className="workflow-steps">
        {/* Step 1: Case Created */}
        <div className={`workflow-step step-${getStepStatus(1)}`}>
          <div className="step-marker">
            <div className="step-number">1</div>
            {getStatusIcon(getStepStatus(1))}
          </div>
          <div className="step-content">
            <h3>Case Created</h3>
            <p className="step-description">
              Initial case setup with officer information and timestamp. This creates an audit trail for all subsequent actions in this investigation.
            </p>
            <div className="step-details">
              <div className="detail-item">
                <User size={14} />
                <span>Officer: {officerName}</span>
              </div>
              <div className="detail-item">
                <Calendar size={14} />
                <span>Created: {formatTime(startedAt)}</span>
              </div>
              <div className="detail-item">
                <FileText size={14} />
                <span>Case ID: {caseId}</span>
              </div>
            </div>
            <p className="step-status completed"><Check size={16} style={{marginRight: "6px", verticalAlign: "middle"}} />Completed</p>
          </div>
        </div>

        {/* Step 2: TOR Data Collected */}
        <div className={`workflow-step step-${getStepStatus(2)}`}>
          <div className="step-marker">
            <div className="step-number">2</div>
            {getStatusIcon(getStepStatus(2))}
          </div>
          <div className="step-content">
            <h3>TOR Data Collected</h3>
            <p className="step-description">
              Automated collection of TOR relay metadata from Onionoo (live relays) and CollecTor (historical data). Data includes fingerprints, flags, bandwidth, uptime intervals, and geographic information.
            </p>
            <div className="step-details">
              <div className="detail-item">
                <Database size={14} />
                <span>Relays Indexed: {torDataCount}</span>
              </div>
              <div className="detail-item">
                <FileText size={14} />
                <span>Data Source: Onionoo + CollecTor</span>
              </div>
              <div className="detail-item">
                <Clock size={14} />
                <span>Collection Timestamps: Included</span>
              </div>
            </div>
            {torDataCount > 0 ? (
              <p className="step-status completed"><Check size={16} style={{marginRight: "6px", verticalAlign: "middle"}} />Completed</p>
            ) : (
              <p className="step-status pending">Waiting for data collection...</p>
            )}
          </div>
        </div>

        {/* Step 3: Correlation Performed */}
        <div className={`workflow-step step-${getStepStatus(3)}`}>
          <div className="step-marker">
            <div className="step-number">3</div>
            {getStatusIcon(getStepStatus(3))}
          </div>
          <div className="step-content">
            <h3>Correlation Performed</h3>
            <p className="step-description">
              Time-based correlation analysis: identifies plausible Entry-Middle-Exit paths using metadata-only analysis. Scores paths based on uptime overlap, bandwidth characteristics, relay stability, and diversity penalties (AS/country).
            </p>
            <div className="step-details">
              <div className="detail-item">
                <GitBranch size={14} />
                <span>Paths Analyzed: {pathsFound}</span>
              </div>
              <div className="detail-item">
                <AlertCircle size={14} />
                <span>Method: Time-based, metadata-only</span>
              </div>
              <div className="detail-item">
                <FileText size={14} />
                <span>No packet inspection</span>
              </div>
            </div>
            {pathsFound > 0 ? (
              <p className="step-status completed"><Check size={16} style={{marginRight: "6px", verticalAlign: "middle"}} />Completed</p>
            ) : (
              <p className="step-status pending">Waiting for correlation analysis...</p>
            )}
          </div>
        </div>

        {/* Step 4: High-Confidence Paths */}
        <div className={`workflow-step step-${getStepStatus(4)}`}>
          <div className="step-marker">
            <div className="step-number">4</div>
            {getStatusIcon(getStepStatus(4))}
          </div>
          <div className="step-content">
            <h3>High-Confidence Paths Identified</h3>
            <p className="step-description">
              Paths ranked by confidence score (30-95% range). Each path shows component breakdown and penalties applied, enabling auditable decision-making suitable for law enforcement and court presentation.
            </p>
            <div className="step-details">
              <div className="detail-item">
                <CheckCircle2 size={14} />
                <span>High-Confidence Paths: {highConfidencePaths}</span>
              </div>
              <div className="detail-item">
                <AlertCircle size={14} />
                <span>Score Range: 30% - 95% (no unrealistic claims)</span>
              </div>
              <div className="detail-item">
                <FileText size={14} />
                <span>Each path includes explainable breakdown</span>
              </div>
            </div>
            {highConfidencePaths > 0 ? (
              <p className="step-status completed"><Check size={16} style={{marginRight: "6px", verticalAlign: "middle"}} />Completed</p>
            ) : (
              <p className="step-status pending">
                Waiting for path identification...
              </p>
            )}
          </div>
        </div>

        {/* Step 5: Evidence Exported */}
        <div className={`workflow-step step-${getStepStatus(5)}`}>
          <div className="step-marker">
            <div className="step-number">5</div>
            {getStatusIcon(getStepStatus(5))}
          </div>
          <div className="step-content">
            <h3>Evidence Exported</h3>
            <p className="step-description">
              Export results in multiple formats: Professional forensic reports (TXT), machine-readable data (JSON), or spreadsheet format (CSV). All exports include legal disclaimers, limitations, and methodology.
            </p>
            <div className="step-details">
              <div className="detail-item">
                <Download size={14} />
                <span>Export Formats: TXT, JSON, CSV</span>
              </div>
              <div className="detail-item">
                <FileText size={14} />
                <span>Includes: Executive summary, technical findings, limitations</span>
              </div>
              <div className="detail-item">
                <AlertCircle size={14} />
                <span>Legal disclaimer: Metadata analysis only</span>
              </div>
            </div>
            {completedSteps.step5 ? (
              <p className="step-status completed"><Check size={16} style={{marginRight: "6px", verticalAlign: "middle"}} />Completed</p>
            ) : (
              <button className="export-btn" onClick={handleExport}>
                <Download size={14} />
                Export Evidence
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Notes Section - Audit Trail */}
      <div className="workflow-notes">
        <h3><FileText size={20} style={{marginRight: "8px", verticalAlign: "middle"}} />Investigation Notes & Audit Trail</h3>
        <p className="notes-explanation">
          Append-only investigation log. All entries timestamped for audit safety.
        </p>

        {/* Notes List */}
        <div className="notes-list">
          {notes.length === 0 ? (
            <p className="no-notes">No notes yet. Add your first note below.</p>
          ) : (
            notes.map((note) => (
              <div key={note.id} className={`note-item ${note.isSystem ? "system" : "user"}`}>
                <div className="note-header">
                  <span className="note-timestamp">[{note.timestamp}]</span>
                  {!note.isSystem && (
                    <span className="note-officer">{note.officer}:</span>
                  )}
                  {note.isSystem && <span className="note-system">SYSTEM:</span>}
                </div>
                <p className="note-text">{note.text}</p>
              </div>
            ))
          )}
        </div>

        {/* Add Note Input */}
        <div className="notes-input">
          <textarea
            className="note-textarea"
            placeholder="Add investigation notes (e.g., 'Suspicious pattern observed', 'Awaiting additional logs')..."
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && e.ctrlKey) handleAddNote();
            }}
            rows="3"
          />
          <button
            className="add-note-btn"
            onClick={handleAddNote}
            disabled={!newNote.trim()}
          >
            Add Note (Ctrl+Enter)
          </button>
        </div>
      </div>

      {/* Methodology Footer */}
      <div className="workflow-methodology">
        <h4><Scale size={18} style={{marginRight: "8px", verticalAlign: "middle"}} />Methodology & Legal Notes</h4>
        <ul>
          <li>
            <strong>Data Source:</strong> Onionoo (public TOR directory) + CollecTor (historical archives)
          </li>
          <li>
            <strong>Analysis Method:</strong> Time-based correlation using metadata only (no packet inspection)
          </li>
          <li>
            <strong>What This Shows:</strong> Plausible relay combinations based on activity timing and characteristics
          </li>
          <li>
            <strong>What This Does NOT Show:</strong> Actual TOR user identity or traffic content
          </li>
          <li>
            <strong>Use Case:</strong> Supporting investigation of TOR-based anonymous threats (financial fraud, cyber harassment, etc.)
          </li>
          <li>
            <strong>Important Limitation:</strong> Multiple paths may be equally plausible. High score indicates better technical evidence, not certainty.
          </li>
        </ul>
      </div>
    </div>
  );
}
