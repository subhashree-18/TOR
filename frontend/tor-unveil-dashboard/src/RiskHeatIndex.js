// src/RiskHeatIndex.js
// Simple Low/Medium/High risk index derived from confidence, exit risk, ASN reputation
import React, { useMemo } from "react";
import { AlertTriangle } from "lucide-react";

export default function RiskHeatIndex({ path }) {
  const riskAnalysis = useMemo(() => {
    if (!path) return null;

    // Calculate risk index from multiple factors
    const confidence = path.score || 0.5; // 0-1
    const exitRiskFactor = path.exitRisk || 0.3; // Assume from path data
    const asnReputation = path.asnReputation || 0.5; // Assume from path data

    // Weighted calculation
    const riskScore = (confidence * 0.5) + (exitRiskFactor * 0.3) + (asnReputation * 0.2);

    let level, color, icon, description;
    if (riskScore >= 0.7) {
      level = "HIGH";
      color = "#ef4444";
      description = "High plausibility with increased infrastructure risk indicators";
    } else if (riskScore >= 0.4) {
      level = "MEDIUM";
      color = "#f59e0b";
      description = "Moderate plausibility with mixed infrastructure indicators";
    } else {
      level = "LOW";
      color = "#10b981";
      description = "Lower plausibility with less concerning infrastructure patterns";
    }

    return {
      level,
      color,
      riskScore: (riskScore * 100).toFixed(1),
      description,
      factors: {
        confidence: confidence.toFixed(3),
        exitRisk: exitRiskFactor.toFixed(3),
        asnReputation: asnReputation.toFixed(3),
      }
    };
  }, [path]);

  if (!riskAnalysis) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyState}>Select a path to view risk assessment</div>
      </div>
    );
  }

  const getProgressColor = (level) => {
    if (level === "HIGH") return "#ef4444";
    if (level === "MEDIUM") return "#f59e0b";
    return "#10b981";
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <AlertTriangle size={20} stroke="currentColor" style={{ color: riskAnalysis.color }} />
        <h3 style={styles.title}>Risk Heat Index</h3>
      </div>

      <div style={styles.riskDisplay}>
        <div style={styles.levelBox}>
          <div style={{
            ...styles.levelBadge,
            backgroundColor: riskAnalysis.color,
          }}>
            {riskAnalysis.level}
          </div>
          <div style={styles.riskScore}>{riskAnalysis.riskScore}%</div>
        </div>

        <div style={styles.description}>
          {riskAnalysis.description}
        </div>
      </div>

      <div style={styles.progressBar}>
        <div
          style={{
            ...styles.progressFill,
            width: `${riskAnalysis.riskScore}%`,
            backgroundColor: riskAnalysis.color,
          }}
        />
      </div>

      <div style={styles.factorsBreakdown}>
        <h4 style={styles.factorsTitle}>Risk Components</h4>
        <table style={styles.factorsTable}>
          <tbody>
            <tr>
              <td style={styles.factorLabel}>Path Confidence</td>
              <td style={styles.factorValue}>{(riskAnalysis.factors.confidence * 100).toFixed(1)}%</td>
              <td style={styles.factorWeight}>(50% weight)</td>
            </tr>
            <tr>
              <td style={styles.factorLabel}>Exit Risk Factor</td>
              <td style={styles.factorValue}>{(riskAnalysis.factors.exitRisk * 100).toFixed(1)}%</td>
              <td style={styles.factorWeight}>(30% weight)</td>
            </tr>
            <tr>
              <td style={styles.factorLabel}>ASN Reputation</td>
              <td style={styles.factorValue}>{(riskAnalysis.factors.asnReputation * 100).toFixed(1)}%</td>
              <td style={styles.factorWeight}>(20% weight)</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style={styles.disclaimer}>
        <strong>Investigation Context:</strong> This index combines multiple heuristics
        to indicate plausibility. Higher index = stronger correlation indicators, not proof.
        Independent corroboration required.
      </div>
    </div>
  );
}

const styles = {
  container: {
    backgroundColor: "#0f172a",
    border: "1px solid #2d3e4f",
    borderRadius: "8px",
    padding: "20px",
    marginBottom: "20px",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "16px",
  },
  title: {
    margin: 0,
    fontSize: "18px",
    fontWeight: "600",
    color: "#0ea5e9",
    letterSpacing: "0.5px",
  },
  riskDisplay: {
    marginBottom: "20px",
  },
  levelBox: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    marginBottom: "12px",
  },
  levelBadge: {
    padding: "8px 16px",
    borderRadius: "4px",
    color: "#0f172a",
    fontWeight: "700",
    fontSize: "14px",
  },
  riskScore: {
    fontSize: "32px",
    fontWeight: "700",
    color: "#0ea5e9",
  },
  description: {
    fontSize: "13px",
    color: "#cbd5e1",
    lineHeight: "1.5",
  },
  progressBar: {
    height: "8px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    overflow: "hidden",
    marginBottom: "20px",
  },
  progressFill: {
    height: "100%",
    transition: "width 0.3s ease",
  },
  factorsBreakdown: {
    marginBottom: "16px",
  },
  factorsTitle: {
    margin: "0 0 12px 0",
    fontSize: "12px",
    fontWeight: "700",
    color: "#94a3b8",
    textTransform: "uppercase",
  },
  factorsTable: {
    width: "100%",
    fontSize: "12px",
    borderCollapse: "collapse",
  },
  factorLabel: {
    padding: "6px 0",
    color: "#cbd5e1",
    textAlign: "left",
  },
  factorValue: {
    padding: "6px 12px",
    color: "#0ea5e9",
    fontWeight: "600",
    textAlign: "right",
  },
  factorWeight: {
    padding: "6px 0",
    color: "#64748b",
    fontSize: "11px",
    textAlign: "right",
  },
  disclaimer: {
    fontSize: "12px",
    color: "#94a3b8",
    fontStyle: "italic",
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    borderLeft: "3px solid #f59e0b",
  },
  emptyState: {
    textAlign: "center",
    color: "#64748b",
    padding: "40px 20px",
  },
};
