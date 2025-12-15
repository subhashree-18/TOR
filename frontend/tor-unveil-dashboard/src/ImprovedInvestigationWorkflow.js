/**
 * ImprovedInvestigationWorkflow.js - Police-Grade Investigation Workflow
 * 
 * 5-Step Procedural Flow:
 * 1. Case Initialized - Case ID assigned, officer identified
 * 2. TOR Data Collected - Relay indexing from Onionoo completed
 * 3. Correlation Performed - Path analysis from metadata correlation
 * 4. High-Priority Paths Identified - Results sorted by confidence
 * 5. Evidence Prepared - Report ready for forensic review
 * 
 * Each step shows: status, timestamp, count of items, brief explanation
 */

import React, { useState, useEffect } from "react";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Database,
  GitBranch,
  FileText,
  User,
  Calendar,
} from "lucide-react";
import "./ImprovedInvestigationWorkflow.css";

export default function ImprovedInvestigationWorkflow({
  caseId = "CASE-2025-001",
  officerName = "Officer",
  startedAt = new Date(),
  torDataCount = 0,
  pathsFound = 0,
  highConfidencePaths = 0,
}) {
  const [steps, setSteps] = useState([
    {
      id: 1,
      title: "Case Initialized",
      status: "completed",
      timestamp: new Date(startedAt),
      icon: User,
      explanation: "Case created and assigned to investigator",
      details: {
        label: "Case ID",
        value: caseId,
      },
      color: "#0ea5e9",
    },
    {
      id: 2,
      title: "TOR Data Collected",
      status: "pending",
      timestamp: null,
      icon: Database,
      explanation: "Relay indexing from Onionoo and CollecTor",
      details: {
        label: "Relays Indexed",
        value: torDataCount || "—",
      },
      color: "#f59e0b",
    },
    {
      id: 3,
      title: "Correlation Performed",
      status: "pending",
      timestamp: null,
      icon: GitBranch,
      explanation: "Time-based metadata analysis and path construction",
      details: {
        label: "Paths Found",
        value: pathsFound || "—",
      },
      color: "#8b5cf6",
    },
    {
      id: 4,
      title: "High-Priority Paths Identified",
      status: "pending",
      timestamp: null,
      icon: AlertCircle,
      explanation: "Results ranked by correlation confidence score",
      details: {
        label: "High-Confidence",
        value: highConfidencePaths || "—",
      },
      color: "#ef4444",
    },
    {
      id: 5,
      title: "Evidence Prepared",
      status: "pending",
      timestamp: null,
      icon: FileText,
      explanation: "Report formatted for forensic analysis and court",
      details: {
        label: "Status",
        value: "Ready",
      },
      color: "#10b981",
    },
  ]);

  // Update step status based on data availability
  useEffect(() => {
    setSteps((prev) => {
      const updated = [...prev];

      // Update step 2 when torDataCount > 0
      if (torDataCount > 0 && updated[1].status !== "completed") {
        updated[1].status = "completed";
        updated[1].timestamp = new Date();
        // Advance to next step
        if (updated[2].status === "pending") updated[2].status = "active";
      }

      // Update step 3 when pathsFound > 0
      if (pathsFound > 0 && updated[2].status !== "completed") {
        updated[2].status = "completed";
        updated[2].timestamp = new Date();
        if (updated[3].status === "pending") updated[3].status = "active";
      }

      // Update step 4 when highConfidencePaths > 0
      if (highConfidencePaths > 0 && updated[3].status !== "completed") {
        updated[3].status = "completed";
        updated[3].timestamp = new Date();
        if (updated[4].status === "pending") updated[4].status = "active";
      }

      return updated;
    });
  }, [torDataCount, pathsFound, highConfidencePaths]);

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case "completed":
        return "status-completed";
      case "active":
        return "status-active";
      default:
        return "status-pending";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 size={24} />;
      case "active":
        return <Clock size={24} className="spinning" />;
      default:
        return <AlertCircle size={24} />;
    }
  };

  const formatTimestamp = (date) => {
    if (!date) return "—";
    return new Date(date).toLocaleTimeString();
  };

  return (
    <div className="improved-workflow">
      <div className="workflow-container">
        {/* Timeline visualization */}
        <div className="workflow-timeline">
          {steps.map((step, idx) => (
            <div key={step.id} className="timeline-item">
              {/* Step box */}
              <div className={`step-box ${getStatusBadgeClass(step.status)}`}>
                <div className="step-icon" style={{ color: step.color }}>
                  <step.icon size={28} />
                </div>
                <div className="step-status-indicator">
                  {getStatusIcon(step.status)}
                </div>
              </div>

              {/* Connector line (if not last step) */}
              {idx < steps.length - 1 && (
                <div
                  className={`timeline-connector ${
                    step.status === "completed" ? "completed" : ""
                  }`}
                ></div>
              )}
            </div>
          ))}
        </div>

        {/* Step details */}
        <div className="steps-details">
          {steps.map((step) => (
            <div
              key={step.id}
              className={`step-card ${getStatusBadgeClass(step.status)}`}
            >
              <div className="card-header">
                <div className="step-number">Step {step.id}</div>
                <div className={`step-status ${getStatusBadgeClass(step.status)}`}>
                  {step.status === "completed"
                    ? "✓ Completed"
                    : step.status === "active"
                    ? "⟳ In Progress"
                    : "◯ Pending"}
                </div>
              </div>

              <h3 className="step-title">{step.title}</h3>

              <p className="step-explanation">{step.explanation}</p>

              {step.timestamp && (
                <div className="step-timestamp">
                  <Calendar size={14} />
                  <span>{formatTimestamp(step.timestamp)}</span>
                </div>
              )}

              {step.details && (
                <div className="step-details-box">
                  <span className="details-label">{step.details.label}</span>
                  <span className="details-value">{step.details.value}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Summary info */}
      <div className="workflow-summary">
        <div className="summary-card">
          <div className="summary-item">
            <span className="summary-label">Investigation Case</span>
            <code className="summary-value">{caseId}</code>
          </div>
          <div className="summary-item">
            <span className="summary-label">Investigator</span>
            <span className="summary-value">{officerName}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Started</span>
            <span className="summary-value">{new Date(startedAt).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
