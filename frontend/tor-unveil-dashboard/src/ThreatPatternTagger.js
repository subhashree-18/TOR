// src/ThreatPatternTagger.js
// Heuristic-based threat pattern tagging with probabilistic language
import React, { useMemo } from "react";
import { AlertCircle, Tag } from "lucide-react";

// Threat pattern heuristics (metadata-only, non-assertive)
const THREAT_PATTERNS = {
  FRAUD: {
    name: "Likely Fraud Infrastructure",
    color: "#ef4444",
    icon: "🚨",
    indicators: [
      "Exit to financial hub countries (US, UK, CN)",
      "High bandwidth consumption pattern",
      "Multiple paths through same ASN",
    ],
  },
  ANON_THREAT: {
    name: "Anonymous Threat Pattern",
    color: "#f59e0b",
    icon: "⚠️",
    indicators: [
      "Frequent country changes",
      "Low ASN reputation score",
      "Entry/exit in different continents",
    ],
  },
  DATA_EXFIL: {
    name: "Possible Data Exfiltration",
    color: "#8b5cf6",
    icon: "📤",
    indicators: [
      "Exit to non-allied jurisdictions",
      "Consistent uptime patterns",
      "High-capacity relay usage",
    ],
  },
};

function analyzePathForPatterns(path) {
  if (!path) return [];

  const patterns = [];
  const score = path.score || 0;
  const exitCountry = path.exit?.country || "";
  const bandwidth = path.components?.bandwidth || 0;
  const asReputation = path.penalties?.as || 0.5;

  // FRAUD detection
  if (
    score > 0.75 &&
    ["US", "UK", "CN", "HK", "SG"].includes(exitCountry) &&
    bandwidth > 0.7
  ) {
    patterns.push({ type: "FRAUD", confidence: Math.min(0.9, score + 0.1) });
  }

  // ANON_THREAT detection
  if (
    score > 0.6 &&
    asReputation < 0.6 &&
    path.entry?.country !== path.exit?.country
  ) {
    patterns.push({ type: "ANON_THREAT", confidence: Math.min(0.85, score) });
  }

  // DATA_EXFIL detection
  if (
    score > 0.7 &&
    !["US", "CA", "UK", "DE", "FR", "AU"].includes(exitCountry) &&
    path.components?.uptime > 0.8
  ) {
    patterns.push({ type: "DATA_EXFIL", confidence: score * 0.8 });
  }

  return patterns;
}

export default function ThreatPatternTagger({ path }) {
  const detectedPatterns = useMemo(() => {
    return analyzePathForPatterns(path);
  }, [path]);

  if (!detectedPatterns || detectedPatterns.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.emptyState}>
          No threat pattern indicators detected for this path.
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <AlertCircle size={18} stroke="currentColor" style={{ color: "#f59e0b" }} />
        <h4 style={styles.title}>Threat Pattern Indicators</h4>
      </div>

      <div style={styles.disclaimer}>
        <strong>Probabilistic Assessment:</strong> The following tags indicate heuristic-based
        pattern matches, not forensic certainties. Each tag requires independent investigative
        corroboration and is presented for analytical support only.
      </div>

      <div style={styles.tagsContainer}>
        {detectedPatterns.map((pattern, idx) => {
          const patternDef = THREAT_PATTERNS[pattern.type];
          if (!patternDef) return null;

          return (
            <div
              key={idx}
              style={{
                ...styles.tag,
                borderColor: patternDef.color,
              }}
            >
              <div style={styles.tagHeader}>
                <span style={styles.tagIcon}>{patternDef.icon}</span>
                <span style={{
                  ...styles.tagName,
                  color: patternDef.color,
                }}>
                  {patternDef.name}
                </span>
              </div>

              <div style={styles.tagConfidence}>
                Heuristic Confidence: <strong>{(pattern.confidence * 100).toFixed(0)}%</strong>
              </div>

              <div style={styles.tagIndicators}>
                <div style={styles.indicatorsLabel}>Pattern Indicators:</div>
                {patternDef.indicators.map((indicator, i) => (
                  <div key={i} style={styles.indicator}>
                    • {indicator}
                  </div>
                ))}
              </div>

              <div style={styles.tagWarning}>
                ⚠️ Requires independent corroboration before use in enforcement action.
              </div>
            </div>
          );
        })}
      </div>

      <div style={styles.footer}>
        <strong>Investigation Notes:</strong>
        <ul style={styles.investigationList}>
          <li>Tags are based on metadata patterns only</li>
          <li>No user behavior or traffic content is analyzed</li>
          <li>Multiple tags may coexist for complex paths</li>
          <li>Use alongside traditional investigative techniques</li>
        </ul>
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
    gap: "10px",
    marginBottom: "12px",
    paddingBottom: "12px",
    borderBottom: "1px solid #2d3e4f",
  },
  title: {
    margin: 0,
    fontSize: "16px",
    fontWeight: "700",
    color: "#cbd5e1",
    letterSpacing: "0.3px",
  },
  disclaimer: {
    fontSize: "12px",
    color: "#94a3b8",
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    borderLeft: "3px solid #f59e0b",
    marginBottom: "16px",
    lineHeight: "1.5",
  },
  tagsContainer: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    marginBottom: "16px",
  },
  tag: {
    padding: "12px",
    backgroundColor: "#1e293b",
    border: "2px solid",
    borderRadius: "6px",
  },
  tagHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "8px",
  },
  tagIcon: {
    fontSize: "18px",
  },
  tagName: {
    fontWeight: "700",
    fontSize: "13px",
  },
  tagConfidence: {
    fontSize: "12px",
    color: "#cbd5e1",
    marginBottom: "8px",
  },
  tagIndicators: {
    fontSize: "12px",
    color: "#94a3b8",
    marginBottom: "8px",
  },
  indicatorsLabel: {
    fontWeight: "600",
    color: "#cbd5e1",
    marginBottom: "4px",
  },
  indicator: {
    paddingLeft: "12px",
    marginBottom: "4px",
  },
  tagWarning: {
    fontSize: "11px",
    color: "#f59e0b",
    fontStyle: "italic",
    paddingTop: "8px",
    borderTop: "1px solid #2d3e4f",
  },
  footer: {
    fontSize: "12px",
    color: "#94a3b8",
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    borderLeft: "3px solid #0ea5e9",
  },
  investigationList: {
    margin: "8px 0 0 0",
    paddingLeft: "20px",
  },
  emptyState: {
    textAlign: "center",
    color: "#64748b",
    padding: "30px 20px",
  },
};

export { analyzePathForPatterns };
