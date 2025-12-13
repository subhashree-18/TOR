import React from "react";
import { Sankey, Tooltip, ResponsiveContainer } from "recharts";

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
  const nodeTypeMap = {}; // Track node types for coloring

  const addNode = (fp, nodeType) => {
    let idx = nodes.findIndex((n) => n.name === fp);
    if (idx === -1) {
      nodes.push({ 
        name: fp.substring(0, 8), 
        fullName: fp,
        type: nodeType
      });
      nodeTypeMap[fp] = nodeType;
      return nodes.length - 1;
    }
    return idx;
  };

  // Get node color based on type
  const getNodeColor = (nodeType) => {
    switch (nodeType) {
      case "entry":
        return "#3b82f6"; // Blue
      case "middle":
        return "#f59e0b"; // Amber
      case "exit":
        return "#ef4444"; // Red
      default:
        return "#0ea5e9"; // Cyan
    }
  };

  paths.slice(0, 20).forEach((p) => {
    if (!p.entry || !p.middle || !p.exit) return;

    const e = addNode(p.entry.fingerprint, "entry");
    const m = addNode(p.middle.fingerprint, "middle");
    const x = addNode(p.exit.fingerprint, "exit");

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

  // Custom node rendering for colors with improved readability
  const NodeShape = (props) => {
    const { x, y, width, height, index } = props;
    const node = nodes[index];
    const color = getNodeColor(node.type);
    
    return (
      <g>
        <rect 
          x={x} 
          y={y} 
          width={width} 
          height={height} 
          fill={color}
          stroke={color}
          strokeWidth={2}
          rx={6}
          opacity={0.9}
        />
        <text 
          x={x + width / 2} 
          y={y + height / 2 - 6}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={13}
          fill="#ffffff"
          fontWeight="700"
          fontFamily="'Courier New', monospace"
        >
          {node.name}
        </text>
        <text 
          x={x + width / 2} 
          y={y + height / 2 + 8}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={10}
          fill="rgba(255, 255, 255, 0.8)"
          fontFamily="'Segoe UI', sans-serif"
        >
          {node.type.toUpperCase()}
        </text>
      </g>
    );
  };

  return (
    <div style={styles.container}>
      <ResponsiveContainer width="100%" height={350}>
        <Sankey
          data={{ nodes, links }}
          node={<NodeShape />}
          nodePadding={100}
          margin={{ top: 30, right: 60, bottom: 30, left: 60 }}
          link={{ stroke: "rgba(14, 165, 233, 0.4)", strokeOpacity: 0.6, strokeWidth: 2.5 }}
          label={{ fill: "#f8fafc", fontSize: 12, fontWeight: 600 }}
        >
          <Tooltip
            contentStyle={styles.tooltip}
            formatter={(value) => `Confidence: ${value}`}
          />
        </Sankey>
      </ResponsiveContainer>
      <div style={styles.legend}>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, backgroundColor: "#3b82f6" }}></div>
          <span>Entry Node (Blue)</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, backgroundColor: "#f59e0b" }}></div>
          <span>Middle Relay (Amber)</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{ ...styles.legendDot, backgroundColor: "#ef4444" }}></div>
          <span>Exit Node (Red)</span>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    width: "100%",
    background: "#1e293b",
    padding: 16,
    borderRadius: 8,
    border: "1px solid #334155"
  },
  legend: {
    display: "flex",
    gap: 24,
    marginTop: 12,
    padding: "8px 0",
    justifyContent: "center",
    fontSize: 12,
    color: "#cbd5e1"
  },
  legendItem: {
    display: "flex",
    alignItems: "center",
    gap: 8
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 3,
    flexShrink: 0
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
