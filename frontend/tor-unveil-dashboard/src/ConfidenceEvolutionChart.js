// src/ConfidenceEvolutionChart.js
// Displays confidence evolution over time as path correlations accumulate
import React, { useMemo } from "react";
import { TrendingUp } from "lucide-react";

export default function ConfidenceEvolutionChart({ path }) {
  if (!path) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyState}>Select a path to view confidence evolution</div>
      </div>
    );
  }

  // Generate synthetic confidence history for demo
  // In production: fetch from backend timeline data
  const confidenceHistory = useMemo(() => {
    if (!path.confidenceHistory) {
      // Generate demo data based on current score
      const baseScore = path.score || 0.5;
      return Array.from({ length: 8 }, (_, i) => ({
        step: i + 1,
        timestamp: new Date(Date.now() - (8 - i) * 300000).toLocaleTimeString(),
        confidence: Math.min(1, baseScore * (0.5 + i * 0.1) + Math.random() * 0.05),
        event: [
          "Initial correlation",
          "Uptime confirmed",
          "Bandwidth matched",
          "ASN verified",
          "Country verified",
          "Role identified",
          "Exit confirmed",
          "Final analysis"
        ][i]
      }));
    }
    return path.confidenceHistory;
  }, [path]);

  // Normalize for chart display (0-100)
  const maxConfidence = Math.max(...confidenceHistory.map(d => d.confidence));
  const minConfidence = Math.min(...confidenceHistory.map(d => d.confidence));

  const renderChart = () => {
    return (
      <svg viewBox="0 0 500 200" style={{ width: "100%", height: "auto" }}>
        {/* Grid background */}
        <defs>
          <pattern id="grid" width="50" height="20" patternUnits="userSpaceOnUse">
            <path d="M 50 0 L 0 0 0 20" fill="none" stroke="#2d3e4f" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="500" height="200" fill="url(#grid)" />

        {/* Y-axis labels */}
        <text x="5" y="10" fontSize="10" fill="#94a3b8">1.0</text>
        <text x="5" y="105" fontSize="10" fill="#94a3b8">0.5</text>
        <text x="5" y="195" fontSize="10" fill="#94a3b8">0.0</text>

        {/* Y-axis line */}
        <line x1="30" y1="0" x2="30" y2="180" stroke="#2d3e4f" strokeWidth="1" />
        
        {/* X-axis line */}
        <line x1="30" y1="180" x2="500" y2="180" stroke="#2d3e4f" strokeWidth="1" />

        {/* Plot points and line */}
        {confidenceHistory.length > 1 && (
          <polyline
            points={confidenceHistory
              .map((d, i) => {
                const x = 30 + (i / (confidenceHistory.length - 1)) * 470;
                const y = 180 - (d.confidence * 180);
                return `${x},${y}`;
              })
              .join(" ")}
            fill="none"
            stroke="#0ea5e9"
            strokeWidth="2"
          />
        )}

        {/* Data points */}
        {confidenceHistory.map((d, i) => {
          const x = 30 + (i / (confidenceHistory.length - 1)) * 470;
          const y = 180 - (d.confidence * 180);
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r="3"
              fill={d.confidence >= 0.7 ? "#10b981" : d.confidence >= 0.5 ? "#f59e0b" : "#ef4444"}
              stroke="#1e293b"
              strokeWidth="1"
            />
          );
        })}

        {/* X-axis labels */}
        {confidenceHistory.map((d, i) => (
          <text
            key={`label-${i}`}
            x={30 + (i / (confidenceHistory.length - 1)) * 470}
            y="200"
            fontSize="9"
            fill="#94a3b8"
            textAnchor="middle"
          >
            {d.step}
          </text>
        ))}
      </svg>
    );
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <TrendingUp size={20} stroke="currentColor" style={{ color: "#0ea5e9" }} />
        <h3 style={styles.title}>Confidence Evolution</h3>
      </div>

      <div style={styles.chartWrapper}>
        {renderChart()}
      </div>

      <div style={styles.legend}>
        <table style={styles.historyTable}>
          <tbody>
            {confidenceHistory.map((d, i) => (
              <tr key={i} style={styles.historyRow}>
                <td style={styles.historyStep}>{d.step}</td>
                <td style={styles.historyEvent}>{d.event}</td>
                <td style={styles.historyTime}>{d.timestamp}</td>
                <td style={styles.historyConfidence}>
                  {(d.confidence * 100).toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={styles.note}>
        <strong>Note:</strong> Confidence evolves as additional correlations are verified.
        Higher values indicate greater plausibility, not certainty.
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
  chartWrapper: {
    marginBottom: "20px",
  },
  legend: {
    marginBottom: "16px",
  },
  historyTable: {
    width: "100%",
    fontSize: "13px",
    borderCollapse: "collapse",
  },
  historyRow: {
    borderBottom: "1px solid #2d3e4f",
  },
  historyStep: {
    padding: "8px",
    color: "#94a3b8",
    fontWeight: "600",
    width: "40px",
  },
  historyEvent: {
    padding: "8px",
    color: "#cbd5e1",
  },
  historyTime: {
    padding: "8px",
    color: "#64748b",
    fontSize: "12px",
  },
  historyConfidence: {
    padding: "8px",
    color: "#0ea5e9",
    fontWeight: "600",
    textAlign: "right",
  },
  note: {
    fontSize: "12px",
    color: "#94a3b8",
    fontStyle: "italic",
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    borderLeft: "3px solid #0ea5e9",
  },
  emptyState: {
    textAlign: "center",
    color: "#64748b",
    padding: "40px 20px",
  },
};
