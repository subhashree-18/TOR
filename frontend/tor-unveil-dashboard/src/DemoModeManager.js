// src/DemoModeManager.js
// Manages demo mode with pre-generated realistic datasets
import React, { useCallback } from "react";
import { Play, Pause } from "lucide-react";
import { useAppContext } from "./AppContext";

// Pre-generated realistic demo datasets
const DEMO_DATASET = {
  paths: [
    {
      id: "demo-path-1",
      score: 0.89,
      entry: { country: "US", city: "New York", fingerprint: "d2e7f8a1b9c3e4f5" },
      middle: { country: "NL", city: "Amsterdam", fingerprint: "a1b2c3d4e5f6g7h8" },
      exit: { country: "CN", city: "Beijing", fingerprint: "m9n8o7p6q5r4s3t2" },
      components: { uptime: 0.92, bandwidth: 0.85, role: 0.90 },
      penalties: { as: 0.75, country: 0.60 },
      timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
    },
    {
      id: "demo-path-2",
      score: 0.76,
      entry: { country: "GB", city: "London", fingerprint: "e5d4c3b2a1f9e8d7" },
      middle: { country: "DE", city: "Frankfurt", fingerprint: "b3c4d5e6f7g8h9i0" },
      exit: { country: "IR", city: "Tehran", fingerprint: "t2s3r4q5p6o7n8m9" },
      components: { uptime: 0.88, bandwidth: 0.72, role: 0.68 },
      penalties: { as: 0.80, country: 0.50 },
      timestamp: new Date(Date.now() - 10 * 60000).toISOString(),
    },
    {
      id: "demo-path-3",
      score: 0.62,
      entry: { country: "CA", city: "Toronto", fingerprint: "f7e6d5c4b3a2f1e0" },
      middle: { country: "SG", city: "Singapore", fingerprint: "d9e8f7g6h5i4j3k2" },
      exit: { country: "RU", city: "Moscow", fingerprint: "n7m8l9k0j1i2h3g4" },
      components: { uptime: 0.75, bandwidth: 0.60, role: 0.55 },
      penalties: { as: 0.70, country: 0.65 },
      timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
    },
  ],
  relays: [
    { country: "US", city: "New York", fingerprint: "d2e7f8a1", asn: "AS1234" },
    { country: "NL", city: "Amsterdam", fingerprint: "a1b2c3d4", asn: "AS5678" },
    { country: "CN", city: "Beijing", fingerprint: "m9n8o7p6", asn: "AS9012" },
  ],
};

export default function DemoModeManager() {
  const { viewMode } = useAppContext();
  const [demoActive, setDemoActive] = React.useState(false);

  const activateDemoMode = useCallback(() => {
    // Store demo data in localStorage
    localStorage.setItem("tor-unveil-demo-mode", JSON.stringify({
      active: true,
      data: DEMO_DATASET,
      activatedAt: new Date().toISOString(),
    }));

    setDemoActive(true);
    window.dispatchEvent(new Event("demo-mode-activated"));
  }, []);

  const deactivateDemoMode = useCallback(() => {
    localStorage.removeItem("tor-unveil-demo-mode");
    setDemoActive(false);
    window.dispatchEvent(new Event("demo-mode-deactivated"));
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.content}>
        <div style={styles.badge}>
          🎬 DEMO MODE
        </div>

        {demoActive ? (
          <>
            <p style={styles.activeText}>
              Demo mode is <strong>ACTIVE</strong>. Pre-generated realistic datasets are loaded.
              Live TOR network fetches are disabled.
            </p>

            <div style={styles.demoInfo}>
              <div style={styles.infoItem}>
                ✓ 3 realistic paths loaded
              </div>
              <div style={styles.infoItem}>
                ✓ Multiple countries represented
              </div>
              <div style={styles.infoItem}>
                ✓ Plausible score distributions
              </div>
              <div style={styles.infoItem}>
                ✓ Suitable for presentations
              </div>
            </div>

            <button
              onClick={deactivateDemoMode}
              style={styles.deactivateBtn}
            >
              <Pause size={16} stroke="currentColor" />
              Exit Demo Mode
            </button>
          </>
        ) : (
          <>
            <p style={styles.inactiveText}>
              Demo mode is currently OFF. System will use live TOR network data.
            </p>

            <button
              onClick={activateDemoMode}
              style={styles.activateBtn}
            >
              <Play size={16} stroke="currentColor" />
              Enter Demo Mode
            </button>

            <div style={styles.demoNote}>
              <strong>Demo Mode includes:</strong>
              <ul style={styles.list}>
                <li>Pre-generated realistic path correlations</li>
                <li>Plausible geographic distributions</li>
                <li>Representative ASN and uptime data</li>
                <li>Failure-free presentations (no API errors)</li>
              </ul>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// Export demo dataset for use in other components
export function getDemoData() {
  const stored = localStorage.getItem("tor-unveil-demo-mode");
  if (stored) {
    try {
      const { data } = JSON.parse(stored);
      return data;
    } catch (e) {
      return null;
    }
  }
  return null;
}

const styles = {
  container: {
    backgroundColor: "#0f172a",
    border: "2px dashed #0ea5e9",
    borderRadius: "8px",
    padding: "20px",
    marginBottom: "20px",
  },
  content: {
    maxWidth: "600px",
  },
  badge: {
    display: "inline-block",
    padding: "6px 12px",
    backgroundColor: "#0ea5e9",
    color: "#0f172a",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: "700",
    marginBottom: "12px",
  },
  activeText: {
    color: "#10b981",
    fontSize: "13px",
    lineHeight: "1.5",
    marginBottom: "12px",
  },
  inactiveText: {
    color: "#94a3b8",
    fontSize: "13px",
    lineHeight: "1.5",
    marginBottom: "12px",
  },
  demoInfo: {
    marginBottom: "16px",
  },
  infoItem: {
    fontSize: "12px",
    color: "#cbd5e1",
    padding: "4px 0",
  },
  activateBtn: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "10px 16px",
    backgroundColor: "#0ea5e9",
    color: "#0f172a",
    border: "none",
    borderRadius: "4px",
    fontWeight: "600",
    fontSize: "13px",
    cursor: "pointer",
    transition: "background 0.2s",
    marginBottom: "12px",
  },
  deactivateBtn: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "10px 16px",
    backgroundColor: "#f59e0b",
    color: "#0f172a",
    border: "none",
    borderRadius: "4px",
    fontWeight: "600",
    fontSize: "13px",
    cursor: "pointer",
    transition: "background 0.2s",
    marginBottom: "12px",
  },
  demoNote: {
    fontSize: "12px",
    color: "#cbd5e1",
    padding: "12px",
    backgroundColor: "#1e293b",
    borderRadius: "4px",
    borderLeft: "3px solid #0ea5e9",
  },
  list: {
    marginTop: "8px",
    paddingLeft: "20px",
    margin: "8px 0 0 0",
  },
};
