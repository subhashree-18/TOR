// src/ForensicIntegrityBadge.js
// Display forensic integrity metadata and report hash for audit trail
import React, { useMemo } from "react";
import { Shield, Copy, Check } from "lucide-react";

export default function ForensicIntegrityBadge({ report }) {
  const [copied, setCopied] = React.useState(false);

  const integrityData = useMemo(() => {
    if (!report || !report.integrity) {
      return null;
    }

    return {
      generatedAt: new Date(report.integrity.generated_at),
      systemVersion: report.integrity.system_version,
      reportHash: report.integrity.report_hash,
      hashAlgorithm: report.integrity.hash_algorithm,
      metadataOnly: report.integrity.metadata_only,
      noTrafficInspection: report.integrity.no_traffic_inspection,
      noDecryption: report.integrity.no_decryption_performed,
    };
  }, [report]);

  if (!integrityData) {
    return null;
  }

  const copyHashToClipboard = () => {
    navigator.clipboard.writeText(integrityData.reportHash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatDateTime = (date) => {
    return date.toLocaleString();
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <Shield size={18} stroke="currentColor" style={{ color: "#10b981" }} />
        <h4 style={styles.title}>Forensic Integrity Verification</h4>
      </div>

      <div style={styles.content}>
        <div style={styles.row}>
          <span style={styles.label}>Report Hash:</span>
          <div style={styles.hashDisplay}>
            <code style={styles.hash}>{integrityData.reportHash}</code>
            <button
              onClick={copyHashToClipboard}
              style={styles.copyBtn}
              title="Copy hash to clipboard"
            >
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>

        <div style={styles.row}>
          <span style={styles.label}>Algorithm:</span>
          <span style={styles.value}>{integrityData.hashAlgorithm}</span>
        </div>

        <div style={styles.row}>
          <span style={styles.label}>Generated:</span>
          <span style={styles.value}>{formatDateTime(integrityData.generatedAt)}</span>
        </div>

        <div style={styles.row}>
          <span style={styles.label}>System Version:</span>
          <span style={styles.value}>{integrityData.systemVersion}</span>
        </div>

        <div style={styles.divider} />

        <div style={styles.guardsSection}>
          <h5 style={styles.guardsTitle}>Analysis Safeguards</h5>
          <div style={styles.guardsList}>
            <div style={styles.guard}>
              <span style={styles.guardCheck}>✓</span>
              <span>Metadata-only analysis</span>
            </div>
            <div style={styles.guard}>
              <span style={styles.guardCheck}>✓</span>
              <span>No traffic packet inspection</span>
            </div>
            <div style={styles.guard}>
              <span style={styles.guardCheck}>✓</span>
              <span>No encryption decryption attempted</span>
            </div>
            <div style={styles.guard}>
              <span style={styles.guardCheck}>✓</span>
              <span>No user identification performed</span>
            </div>
          </div>
        </div>

        <div style={styles.auditNote}>
          <strong>Audit Trail:</strong> This report contains a deterministic hash of all
          analysis contents. Hash mismatch on re-verification indicates content modification
          post-generation.
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    backgroundColor: "#0f172a",
    border: "1px solid #10b981",
    borderRadius: "8px",
    padding: "16px",
    marginBottom: "16px",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginBottom: "12px",
  },
  title: {
    margin: 0,
    fontSize: "14px",
    fontWeight: "700",
    color: "#10b981",
    letterSpacing: "0.3px",
  },
  content: {
    fontSize: "12px",
  },
  row: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "8px 0",
    borderBottom: "1px solid #1e293b",
  },
  label: {
    color: "#94a3b8",
    fontWeight: "600",
    minWidth: "120px",
  },
  value: {
    color: "#cbd5e1",
  },
  hashDisplay: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  hash: {
    backgroundColor: "#1e293b",
    padding: "4px 8px",
    borderRadius: "3px",
    color: "#0ea5e9",
    fontFamily: "monospace",
    fontSize: "11px",
  },
  copyBtn: {
    background: "none",
    border: "none",
    color: "#0ea5e9",
    cursor: "pointer",
    padding: "4px",
    display: "flex",
    alignItems: "center",
  },
  divider: {
    height: "1px",
    backgroundColor: "#2d3e4f",
    margin: "12px 0",
  },
  guardsSection: {
    marginTop: "12px",
  },
  guardsTitle: {
    margin: "0 0 8px 0",
    fontSize: "11px",
    fontWeight: "700",
    color: "#94a3b8",
    textTransform: "uppercase",
  },
  guardsList: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  guard: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    color: "#cbd5e1",
    fontSize: "12px",
  },
  guardCheck: {
    color: "#10b981",
    fontWeight: "700",
  },
  auditNote: {
    marginTop: "12px",
    fontSize: "11px",
    color: "#94a3b8",
    fontStyle: "italic",
    padding: "8px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    borderLeft: "3px solid #10b981",
  },
};
