// src/EnhancedFlowVisualization.js
// Highlights dominant paths, fades low-confidence paths for better visual distinction
import React, { useMemo, useState } from "react";
import { Eye, EyeOff } from "lucide-react";

export default function EnhancedFlowVisualization({ paths = [] }) {
  const [hideLoConfidence, setHideLoConfidence] = useState(false);

  const processedPaths = useMemo(() => {
    if (!paths || paths.length === 0) return [];

    // Sort by confidence for emphasis
    const sorted = [...paths].sort((a, b) => (b.score || 0) - (a.score || 0));

    // Calculate quartiles for emphasis
    const scores = sorted.map(p => p.score || 0);
    const q3 = scores[Math.floor(scores.length * 0.25)];

    // Mark dominant vs faded
    return sorted.map((p, idx) => ({
      ...p,
      isDominant: (p.score || 0) >= q3,
      order: idx,
    }));
  }, [paths]);

  const displayPaths = useMemo(() => {
    if (hideLoConfidence) {
      return processedPaths.filter(p => p.isDominant);
    }
    return processedPaths;
  }, [processedPaths, hideLoConfidence]);

  if (displayPaths.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyBox}>
          {hideLoConfidence ? "No high-confidence paths to display" : "No path data to visualize"}
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>Path Flow Emphasis</h3>
        <button
          onClick={() => setHideLoConfidence(!hideLoConfidence)}
          style={styles.toggleBtn}
          title="Toggle to show/hide low-confidence paths"
        >
          {hideLoConfidence ? (
            <>
              <Eye size={16} stroke="currentColor" />
              Show All
            </>
          ) : (
            <>
              <EyeOff size={16} stroke="currentColor" />
              Hide Low Confidence
            </>
          )}
        </button>
      </div>

      <div style={styles.pathsList}>
        {displayPaths.map((path, idx) => (
          <div
            key={idx}
            style={{
              ...styles.pathItem,
              ...(!path.isDominant && styles.pathItemFaded),
            }}
          >
            {/* Entry Node */}
            <div style={styles.nodeGroup}>
              <div style={{ ...styles.nodeBadge, ...styles.entryNode }}>
                {path.entry?.country || "??"}
              </div>
              <div style={styles.nodeLabel}>Entry</div>
            </div>

            {/* Arrow */}
            <div style={styles.flowArrow}>→</div>

            {/* Middle Node */}
            <div style={styles.nodeGroup}>
              <div style={{ ...styles.nodeBadge, ...styles.middleNode }}>
                {path.middle?.country || "??"}
              </div>
              <div style={styles.nodeLabel}>Middle</div>
            </div>

            {/* Arrow */}
            <div style={styles.flowArrow}>→</div>

            {/* Exit Node */}
            <div style={styles.nodeGroup}>
              <div style={{ ...styles.nodeBadge, ...styles.exitNode }}>
                {path.exit?.country || "??"}
              </div>
              <div style={styles.nodeLabel}>Exit</div>
            </div>

            {/* Score & Confidence */}
            <div style={styles.scoreSection}>
              <div style={styles.score}>
                Score: <strong>{(path.score || 0).toFixed(3)}</strong>
              </div>
              <div style={{
                ...styles.confidence,
                color: getConfidenceColor(path.score || 0),
              }}>
                {getConfidenceLabel(path.score || 0)}
              </div>
            </div>

            {/* Emphasis Indicator */}
            {path.isDominant && (
              <div style={styles.dominantBadge}>🔝 HIGH</div>
            )}
          </div>
        ))}
      </div>

      <div style={styles.summary}>
        Showing {displayPaths.length} of {paths.length} paths
        {hideLoConfidence && (
          <span style={styles.hiddenCount}>
            ({paths.length - displayPaths.length} low-confidence hidden)
          </span>
        )}
      </div>

      <div style={styles.disclaimer}>
        <strong>Visual Emphasis Note:</strong> Dominant paths (top quartile) are highlighted.
        Hidden low-confidence paths may still be valid investigative leads.
      </div>
    </div>
  );
}

function getConfidenceColor(score) {
  if (score >= 0.7) return "#10b981";
  if (score >= 0.5) return "#f59e0b";
  return "#ef4444";
}

function getConfidenceLabel(score) {
  if (score >= 0.7) return "HIGH";
  if (score >= 0.5) return "MEDIUM";
  return "LOW";
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
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px",
    paddingBottom: "12px",
    borderBottom: "1px solid #2d3e4f",
  },
  title: {
    margin: 0,
    fontSize: "18px",
    fontWeight: "600",
    color: "#0ea5e9",
    letterSpacing: "0.5px",
  },
  toggleBtn: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "6px 12px",
    backgroundColor: "#1e293b",
    border: "1px solid #2d3e4f",
    borderRadius: "4px",
    color: "#0ea5e9",
    fontSize: "12px",
    fontWeight: "500",
    cursor: "pointer",
    transition: "all 0.2s",
  },
  pathsList: {
    marginBottom: "16px",
  },
  pathItem: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "12px",
    marginBottom: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    border: "1px solid #2d3e4f",
    transition: "opacity 0.2s, filter 0.2s",
  },
  pathItemFaded: {
    opacity: 0.5,
    filter: "grayscale(0.3)",
  },
  nodeGroup: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "4px",
  },
  nodeBadge: {
    padding: "6px 12px",
    borderRadius: "4px",
    fontWeight: "700",
    fontSize: "12px",
    color: "#0f172a",
    minWidth: "40px",
    textAlign: "center",
  },
  entryNode: {
    backgroundColor: "#3b82f6",
  },
  middleNode: {
    backgroundColor: "#f59e0b",
  },
  exitNode: {
    backgroundColor: "#ef4444",
  },
  nodeLabel: {
    fontSize: "10px",
    color: "#94a3b8",
    fontWeight: "500",
  },
  flowArrow: {
    color: "#0ea5e9",
    fontSize: "16px",
    fontWeight: "bold",
  },
  scoreSection: {
    marginLeft: "auto",
    textAlign: "right",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  score: {
    fontSize: "12px",
    color: "#cbd5e1",
  },
  confidence: {
    fontSize: "12px",
    fontWeight: "700",
  },
  dominantBadge: {
    padding: "4px 8px",
    backgroundColor: "#10b981",
    color: "#0f172a",
    borderRadius: "3px",
    fontSize: "11px",
    fontWeight: "700",
  },
  summary: {
    fontSize: "12px",
    color: "#94a3b8",
    textAlign: "center",
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    marginBottom: "12px",
  },
  hiddenCount: {
    color: "#64748b",
    fontSize: "11px",
    marginLeft: "6px",
  },
  disclaimer: {
    fontSize: "12px",
    color: "#94a3b8",
    fontStyle: "italic",
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    borderLeft: "3px solid #0ea5e9",
  },
  emptyBox: {
    padding: "40px 20px",
    background: "#1e293b",
    color: "#94a3b8",
    textAlign: "center",
    borderRadius: "8px",
  },
};
