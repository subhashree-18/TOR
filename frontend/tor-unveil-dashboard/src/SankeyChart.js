import React from "react";
import { Sankey, Tooltip } from "recharts";

export default function SankeyChart({ paths = [] }) {
  if (!paths.length) {
    return (
      <div style={styles.emptyBox}>
        No path data to visualize.
      </div>
    );
  }

  const nodes = [];
  const links = [];

  const addNode = (fp) => {
    let idx = nodes.findIndex((n) => n.name === fp);
    if (idx === -1) {
      nodes.push({ name: fp });
      return nodes.length - 1;
    }
    return idx;
  };

  paths.slice(0, 20).forEach((p) => {
    if (!p.entry || !p.middle || !p.exit) return;

    const e = addNode(p.entry.fingerprint);
    const m = addNode(p.middle.fingerprint);
    const x = addNode(p.exit.fingerprint);

    links.push({ source: e, target: m, value: 1 });
    links.push({ source: m, target: x, value: 1 });
  });

  if (nodes.length === 0 || links.length === 0) {
    return (
      <div style={styles.emptyBox}>
        No valid Sankey data.
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <Sankey
        width={600}
        height={300}
        data={{ nodes, links }}
        nodePadding={40}
        link={{ stroke: "#38bdf8", strokeWidth: 2 }}
        node={{ fill: "#0ea5e9", stroke: "#38bdf8" }}
        label={{ fill: "#f8fafc", fontSize: 12 }}
      >
        <Tooltip
          contentStyle={styles.tooltip}
        />
      </Sankey>
    </div>
  );
}

const styles = {
  container: {
    width: "100%",
    height: 300,
    background: "#1e293b",
    padding: 10,
    borderRadius: 8,
    border: "1px solid #334155"
  },
  emptyBox: {
    padding: 20,
    background: "#1e293b",
    color: "#94a3b8",
    textAlign: "center",
    borderRadius: 8,
    border: "1px solid #334155"
  },
  tooltip: {
    background: "#0f172a",
    border: "1px solid #38bdf8",
    color: "#f8fafc"
  }
};
