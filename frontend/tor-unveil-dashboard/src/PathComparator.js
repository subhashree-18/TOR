// src/PathComparator.js
// Side-by-side comparison of top 2-3 paths with detailed breakdown
import React, { useMemo, useState } from "react";
import { Scale, ChevronDown, ChevronUp } from "lucide-react";

export default function PathComparator({ paths }) {
  const [expanded, setExpanded] = useState(true);

  // Select top 3 by confidence
  const topPaths = useMemo(() => {
    if (!paths || paths.length === 0) return [];
    return [...paths]
      .sort((a, b) => (b.score || 0) - (a.score || 0))
      .slice(0, 3);
  }, [paths]);

  if (topPaths.length < 2) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyState}>
          Need at least 2 paths to compare. Current: {topPaths.length}
        </div>
      </div>
    );
  }

  const getMetricLabel = (value, type) => {
    if (type === "confidence") return (value * 100).toFixed(1) + "%";
    if (type === "penalty") return (value * 100).toFixed(1) + "%";
    if (type === "score") return value.toFixed(3);
    return value;
  };

  const compareMetric = (paths, metric) => {
    return paths.map(p => {
      if (metric === "score") return p.score || 0;
      if (metric === "uptime") return p.components?.uptime || 0;
      if (metric === "bandwidth") return p.components?.bandwidth || 0;
      if (metric === "role") return p.components?.role || 0;
      if (metric === "as_penalty") return p.penalties?.as || 1;
      if (metric === "country_penalty") return p.penalties?.country || 1;
      if (metric === "confidence") {
        if (p.score >= 0.7) return 0.8;
        if (p.score >= 0.5) return 0.5;
        return 0.2;
      }
      return 0;
    });
  };

  const renderMetricRow = (label, metric) => {
    const values = compareMetric(topPaths, metric);
    const maxValue = Math.max(...values);

    return (
      <div key={metric} style={styles.metricRow}>
        <div style={styles.metricLabel}>{label}</div>
        {topPaths.map((path, idx) => {
          const value = values[idx];
          const percentage = (value / maxValue) * 100;
          const isHighest = value === maxValue;
          return (
            <div key={idx} style={styles.metricCell}>
              <div style={styles.metricBar}>
                <div
                  style={{
                    ...styles.metricBarFill,
                    width: `${percentage}%`,
                    backgroundColor: isHighest ? "#10b981" : "#0ea5e9",
                  }}
                />
              </div>
              <div style={styles.metricValue}>
                {getMetricLabel(value, metric)}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <button
          style={styles.toggleBtn}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
        <Scale size={20} stroke="currentColor" style={{ color: "#0ea5e9" }} />
        <h3 style={styles.title}>Path Comparison Analysis</h3>
        <span style={styles.pathCount}>({topPaths.length} paths)</span>
      </div>

      {expanded && (
        <>
          <div style={styles.pathHeaders}>
            <div style={styles.pathLabel}></div>
            {topPaths.map((path, idx) => (
              <div key={idx} style={styles.pathHeader}>
                <div style={styles.pathNumber}>Path {idx + 1}</div>
                <div style={styles.pathId}>{path.id?.substring(0, 8)}</div>
              </div>
            ))}
          </div>

          <div style={styles.metricsContainer}>
            {/* Overall Score */}
            {renderMetricRow("Overall Score", "score")}

            {/* Component Breakdown */}
            <div style={styles.metricSeparator}>Components</div>
            {renderMetricRow("Uptime (30%)", "uptime")}
            {renderMetricRow("Bandwidth (45%)", "bandwidth")}
            {renderMetricRow("Role (25%)", "role")}

            {/* Penalties */}
            <div style={styles.metricSeparator}>Penalties</div>
            {renderMetricRow("AS Diversity", "as_penalty")}
            {renderMetricRow("Country Diversity", "country_penalty")}

            {/* Confidence */}
            <div style={styles.metricSeparator}>Confidence</div>
            {renderMetricRow("Confidence Level", "confidence")}
          </div>

          <div style={styles.topPathIndicator}>
            🏆 Path {topPaths.findIndex(p => p.score === Math.max(...topPaths.map(x => x.score))) + 1} has highest
            plausibility
          </div>

          <div style={styles.disclaimer}>
            <strong>Analyst Note:</strong> This comparison shows relative metric strengths.
            Higher scores in one path do not imply certainty; multiple strong paths
            may exist for the same timestamp window.
          </div>
        </>
      )}
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
  toggleBtn: {
    background: "none",
    border: "none",
    color: "#0ea5e9",
    cursor: "pointer",
    padding: "4px",
    display: "flex",
    alignItems: "center",
  },
  title: {
    margin: 0,
    fontSize: "18px",
    fontWeight: "600",
    color: "#0ea5e9",
    letterSpacing: "0.5px",
  },
  pathCount: {
    marginLeft: "auto",
    fontSize: "13px",
    color: "#64748b",
  },
  pathHeaders: {
    display: "grid",
    gridTemplateColumns: "150px repeat(auto-fit, minmax(120px, 1fr))",
    gap: "12px",
    marginBottom: "20px",
    paddingBottom: "12px",
    borderBottom: "1px solid #2d3e4f",
  },
  pathLabel: {},
  pathHeader: {
    textAlign: "center",
  },
  pathNumber: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#cbd5e1",
  },
  pathId: {
    fontSize: "11px",
    color: "#64748b",
    fontFamily: "monospace",
  },
  metricsContainer: {
    marginBottom: "16px",
  },
  metricRow: {
    display: "grid",
    gridTemplateColumns: "150px repeat(auto-fit, minmax(120px, 1fr))",
    gap: "12px",
    alignItems: "center",
    paddingBottom: "12px",
    borderBottom: "1px solid #1e293b",
  },
  metricLabel: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#94a3b8",
  },
  metricCell: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  metricBar: {
    height: "6px",
    backgroundColor: "#1e293b",
    borderRadius: "3px",
    overflow: "hidden",
  },
  metricBarFill: {
    height: "100%",
    transition: "width 0.3s ease",
  },
  metricValue: {
    fontSize: "11px",
    color: "#cbd5e1",
    textAlign: "center",
  },
  metricSeparator: {
    fontSize: "11px",
    fontWeight: "700",
    color: "#0ea5e9",
    textTransform: "uppercase",
    marginTop: "16px",
    marginBottom: "12px",
    paddingTop: "12px",
    borderTop: "1px solid #2d3e4f",
  },
  topPathIndicator: {
    fontSize: "12px",
    color: "#10b981",
    padding: "12px",
    backgroundColor: "#0f3a2a",
    borderRadius: "4px",
    marginBottom: "12px",
    borderLeft: "3px solid #10b981",
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
