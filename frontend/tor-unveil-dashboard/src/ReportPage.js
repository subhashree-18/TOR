import React from "react";
import { useAppContext } from "./AppContext";
import ScoreExplainer from "./ScoreExplainer";
import "./ReportPage.css";

export default function ReportPage() {
  const { selectedRelay, selectedPath } = useAppContext();

  const generateTextReport = () => {
    let content = "TOR UNVEIL - FORENSIC INVESTIGATION REPORT\n";
    content += "=========================================\n\n";
    content += `Generated: ${new Date().toISOString()}\n\n`;

    if (selectedRelay) {
      content += "RELAY INFORMATION\n";
      content += "-----------------\n";
      content += `Fingerprint: ${selectedRelay.fingerprint}\n`;
      content += `Nickname: ${selectedRelay.nickname || "Unknown"}\n`;
      content += `IP: ${selectedRelay.ip || "Unknown"}\n`;
      content += `Country: ${selectedRelay.country || "Unknown"}\n`;
      content += `Role: ${selectedRelay.role || "Unknown"}\n\n`;
    }

    if (selectedPath) {
      content += "CORRELATED PATH\n";
      content += "---------------\n";
      content += `Entry: ${selectedPath.entry.nickname} (${selectedPath.entry.fingerprint})\n`;
      content += `Middle: ${selectedPath.middle.nickname} (${selectedPath.middle.fingerprint})\n`;
      content += `Exit: ${selectedPath.exit.nickname} (${selectedPath.exit.fingerprint})\n`;
      content += `Score: ${(selectedPath.score * 100).toFixed(1)}%\n`;
      content += `Confidence: ${selectedPath.score >= 0.8 ? "HIGH" : selectedPath.score >= 0.5 ? "MEDIUM" : "LOW"}\n\n`;

      if (selectedPath.components) {
        content += "SCORE COMPONENTS\n";
        content += "----------------\n";
        content += `Uptime: ${(selectedPath.components.uptime_score * 100).toFixed(1)}%\n`;
        content += `Bandwidth: ${(selectedPath.components.bandwidth_score * 100).toFixed(1)}%\n`;
        content += `Role: ${(selectedPath.components.role_score * 100).toFixed(1)}%\n`;
        content += `AS Penalty: ${(selectedPath.components.as_penalty * 100).toFixed(1)}%\n`;
        content += `Country Penalty: ${(selectedPath.components.country_penalty * 100).toFixed(1)}%\n\n`;
      }
    }

    content += "SCORING METHODOLOGY\n";
    content += "-------------------\n";
    content += "Uptime Window: 7 days\n";
    content += "AS Penalty: 0.70x (same AS)\n";
    content += "Country Penalty: 0.60x (same country)\n";
    content += "Max Score: 85%\n";
    content += "Weights: 50% Uptime | 25% Bandwidth | 25% Role\n\n";

    content += "LEGAL DISCLAIMER\n";
    content += "----------------\n";
    content += "CRITICAL: Results are PLAUSIBILITY only, NOT proof.\n";
    content += "Use as investigative support only.\n";
    content += "Independent validation required.\n";
    content += "No TOR anonymity is broken.\n";
    content += "Authorized Law Enforcement Use Only.\n";

    const blob = new Blob([content], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tor-unveil-report-${Date.now()}.txt`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const generateJSONReport = () => {
    const data = {
      timestamp: new Date().toISOString(),
      tool: "TOR Unveil",
      version: "1.0",
      relay: selectedRelay || null,
      path: selectedPath || null,
      methodology: {
        uptime_window_days: 7,
        as_penalty: 0.70,
        country_penalty: 0.60,
        max_score_cap: 0.85,
        weights: { uptime: 0.50, bandwidth: 0.25, role: 0.25 }
      },
      disclaimer: "Results are probabilistic. Use for investigative support only."
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tor-unveil-report-${Date.now()}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const generateCSVReport = () => {
    let csv = "Field,Value\n";
    csv += `Timestamp,"${new Date().toISOString()}"\n`;

    if (selectedRelay) {
      csv += `Relay.Fingerprint,"${selectedRelay.fingerprint}"\n`;
      csv += `Relay.Nickname,"${selectedRelay.nickname || "Unknown"}"\n`;
      csv += `Relay.IP,"${selectedRelay.ip || "Unknown"}"\n`;
      csv += `Relay.Country,"${selectedRelay.country || "Unknown"}"\n`;
    }

    if (selectedPath) {
      csv += `Path.Entry,"${selectedPath.entry.nickname}"\n`;
      csv += `Path.Middle,"${selectedPath.middle.nickname}"\n`;
      csv += `Path.Exit,"${selectedPath.exit.nickname}"\n`;
      csv += `Path.Score,"${(selectedPath.score * 100).toFixed(1)}%"\n`;
      csv += `Path.Confidence,"${selectedPath.score >= 0.8 ? "HIGH" : selectedPath.score >= 0.5 ? "MEDIUM" : "LOW"}"\n`;
    }

    csv += `Disclaimer,"Probabilistic results only. Not proof."\n`;

    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tor-unveil-report-${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (!selectedRelay && !selectedPath) {
    return (
      <div style={styles.page}>
        <div style={styles.banner}>Forensic Report Export</div>
        <div style={styles.emptyState}>
          <h2>No Investigation Data</h2>
          <p>Please complete an investigation (select relay or path) before generating a report.</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      <div style={styles.banner}>
        Forensic Report Export
        <p>Generate exportable forensic summary for your investigation</p>
      </div>

      <div style={styles.container}>
        <div style={styles.section}>
          <h3>Investigation Summary</h3>
          {selectedRelay && (
            <div style={styles.data}>
              <div style={styles.field}>
                <label>Selected Relay:</label>
                <code>{selectedRelay.fingerprint}</code>
              </div>
              <div style={styles.field}>
                <label>Nickname:</label>
                <span>{selectedRelay.nickname}</span>
              </div>
              <div style={styles.field}>
                <label>Location:</label>
                <span>{selectedRelay.country}</span>
              </div>
              <div style={styles.field}>
                <label>IP Address:</label>
                <code>{selectedRelay.ip}</code>
              </div>
            </div>
          )}

          {selectedPath && (
            <div style={styles.data}>
              <div style={styles.field}>
                <label>Correlated Path:</label>
              </div>
              <div style={styles.pathFlow}>
                <div style={styles.node}>
                  <strong>{selectedPath.entry.nickname}</strong>
                  <br />
                  <code style={{ fontSize: "11px" }}>{selectedPath.entry.fingerprint.substring(0, 8)}</code>
                  <br />
                  <small>{selectedPath.entry.country}</small>
                </div>
                <div style={styles.arrow}>→</div>
                <div style={styles.node}>
                  <strong>{selectedPath.middle.nickname}</strong>
                  <br />
                  <code style={{ fontSize: "11px" }}>{selectedPath.middle.fingerprint.substring(0, 8)}</code>
                  <br />
                  <small>{selectedPath.middle.country}</small>
                </div>
                <div style={styles.arrow}>→</div>
                <div style={styles.node}>
                  <strong>{selectedPath.exit.nickname}</strong>
                  <br />
                  <code style={{ fontSize: "11px" }}>{selectedPath.exit.fingerprint.substring(0, 8)}</code>
                  <br />
                  <small>{selectedPath.exit.country}</small>
                </div>
              </div>
              <div style={styles.field}>
                <label>Plausibility Score:</label>
                <span style={{ color: selectedPath.score > 0.8 ? "#10b981" : "#f59e0b" }}>
                  {(selectedPath.score * 100).toFixed(1)}%
                </span>
              </div>
              
              {/* Score Explanation with full audit trail */}
              <div style={styles.scoreExplainerContainer}>
                <ScoreExplainer path={selectedPath} expanded={true} />
              </div>
            </div>
          )}
        </div>

        <div style={styles.section}>
          <h3>Legal & Ethical Notes</h3>
          <div style={styles.notes}>
            <p>• <strong>Probabilistic Results:</strong> These findings express plausibility, not proof.</p>
            <p>• <strong>Investigative Support:</strong> Use as one data point in a larger investigation.</p>
            <p>• <strong>Court Consideration:</strong> Present with forensic metadata and chain-of-custody.</p>
            <p>• <strong>No Deanonymization:</strong> This tool does not break TOR anonymity.</p>
            <p>• <strong>Metadata Only:</strong> Analysis based on observed relay metadata and timing.</p>
          </div>
        </div>

        <div style={styles.section}>
          <h3>Export Formats</h3>
          <div style={styles.exportButtons}>
            <button style={styles.exportBtn} onClick={generateTextReport}>
              Text Report
            </button>
            <button style={styles.exportBtn} onClick={generateJSONReport}>
              JSON Report
            </button>
            <button style={styles.exportBtn} onClick={generateCSVReport}>
              CSV Report
            </button>
          </div>
          <p style={{ marginTop: "16px", fontSize: "12px", color: "#94a3b8" }}>
            Reports include investigation metadata and forensic timestamps for reproducibility.
          </p>
        </div>

        <div style={styles.disclaimer}>
          <strong>Disclaimer:</strong>
          <br />
          This tool is designed for investigative support by law enforcement. Results must be validated through
          independent means. TOR Unveil does not perform deanonymization and operates within legal and ethical
          boundaries.
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: {
    padding: "20px",
    maxWidth: "1000px",
    margin: "0 auto",
  },
  banner: {
    background: "#1e293b",
    border: "2px solid #38bdf8",
    borderRadius: "8px",
    padding: "20px",
    marginBottom: "20px",
    fontSize: "18px",
    fontWeight: "bold",
    color: "#38bdf8",
  },
  container: {
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },
  section: {
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: "8px",
    padding: "20px",
  },
  data: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    marginTop: "12px",
  },
  field: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  pathFlow: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginTop: "12px",
    padding: "12px",
    background: "#0f172a",
    borderRadius: "6px",
    overflowX: "auto",
  },
  node: {
    background: "#334155",
    border: "2px solid #38bdf8",
    borderRadius: "6px",
    padding: "8px 12px",
    textAlign: "center",
    minWidth: "120px",
    flex: "0 0 auto",
  },
  arrow: {
    fontSize: "20px",
    color: "#38bdf8",
    flex: "0 0 auto",
  },
  scoreExplainerContainer: {
    marginTop: "16px",
    marginBottom: "12px",
  },
  notes: {
    marginTop: "12px",
  },
  exportButtons: {
    display: "flex",
    gap: "12px",
    marginTop: "12px",
  },
  exportBtn: {
    background: "#0ea5e9",
    color: "#000",
    border: "none",
    padding: "10px 20px",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: "bold",
    flex: 1,
  },
  disclaimer: {
    background: "#7f1d1d",
    border: "2px solid #fca5a5",
    borderRadius: "8px",
    padding: "16px",
    marginTop: "20px",
    fontSize: "13px",
    color: "#fef2f2",
  },
  emptyState: {
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: "8px",
    padding: "40px 20px",
    textAlign: "center",
    color: "#cbd5e1",
  },
};
