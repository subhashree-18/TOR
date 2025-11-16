import React, { useState } from "react";
import Timeline from "./Timeline";

export default function TimelinePage() {
  const [fp, setFp] = useState("");

  return (
    <div style={{ padding: 20 }}>
      <h2>Timeline Viewer</h2>

      <input
        type="text"
        value={fp}
        placeholder="Enter fingerprint"
        onChange={(e) => setFp(e.target.value)}
        style={{ width: 300, padding: 8 }}
      />

      {fp && (
        <div style={{ marginTop: 20 }}>
          <Timeline fingerprint={fp} />
        </div>
      )}
    </div>
  );
}
