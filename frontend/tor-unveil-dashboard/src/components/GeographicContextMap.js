import React from "react";

/**
 * GeographicContextMap - Geographic context visualization for TOR analysis
 * This component displays geographic context for TOR entry/exit nodes
 */
const GeographicContextMap = ({ caseId }) => {
  return (
    <div className="geographic-context-map">
      <div className="map-placeholder">
        <p>Geographic Context Map - Node Location Analysis</p>
        <p style={{ fontSize: "12px", color: "#666" }}>
          Case: {caseId}
        </p>
      </div>
    </div>
  );
};

export default GeographicContextMap;
