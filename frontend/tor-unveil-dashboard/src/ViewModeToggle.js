// src/ViewModeToggle.js
// Toggle between Officer View (simplified) and Technical View (detailed)
import React from "react";
import { Eye, Settings } from "lucide-react";
import { useAppContext } from "./AppContext";

export default function ViewModeToggle() {
  const { viewMode, setViewMode } = useAppContext();

  const toggleMode = () => {
    setViewMode(viewMode === "officer" ? "technical" : "officer");
  };

  return (
    <div style={styles.container}>
      <button
        style={{
          ...styles.btn,
          ...(viewMode === "officer" ? styles.btnActive : {}),
        }}
        onClick={() => setViewMode("officer")}
        title="Simplified view for law enforcement officers"
      >
        <Eye size={16} stroke="currentColor" />
        Officer View
      </button>

      <button
        style={{
          ...styles.btn,
          ...(viewMode === "technical" ? styles.btnActive : {}),
        }}
        onClick={() => setViewMode("technical")}
        title="Detailed technical metrics and analysis"
      >
        <Settings size={16} stroke="currentColor" />
        Technical View
      </button>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    gap: "4px",
    padding: "8px",
    backgroundColor: "#1e293b",
    borderRadius: "6px",
    alignItems: "center",
  },
  btn: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "6px 12px",
    backgroundColor: "transparent",
    border: "1px solid #2d3e4f",
    color: "#94a3b8",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: "500",
    cursor: "pointer",
    transition: "all 0.2s",
  },
  btnActive: {
    backgroundColor: "#0ea5e9",
    color: "#0f172a",
    border: "1px solid #0ea5e9",
  },
};
