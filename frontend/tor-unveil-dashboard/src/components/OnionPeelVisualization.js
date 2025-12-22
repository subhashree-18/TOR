/**
 * OnionPeelVisualization.js
 * 
 * D3.js-based timeline-driven onion peel visualization for TOR paths.
 * 
 * Shows TOR path evolution with:
 * - Concentric circles for each path layer (Client, Guard, Middle, Exit, Destination)
 * - Timeline slider to scrub through session evolution
 * - Animated node transitions as time progresses
 * - Interactive tooltips with node details
 */

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import './OnionPeelVisualization.css';

const OnionPeelVisualization = ({ caseId, sessionId }) => {
  const svgRef = useRef();
  const [data, setData] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch path evolution data
  useEffect(() => {
    const fetchPathEvolution = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `/api/path/evolution?case_id=${caseId}${sessionId ? `&session_id=${sessionId}` : ''}`
        );
        
        if (!response.ok) {
          throw new Error('Failed to fetch path evolution data');
        }
        
        const result = await response.json();
        
        if (result.status === 'success' && result.evolution) {
          setData(result.evolution);
          setCurrentTime(0);
        } else {
          setError('No path evolution data available');
        }
      } catch (err) {
        setError(err.message);
        console.error('Error fetching path evolution:', err);
      } finally {
        setLoading(false);
      }
    };

    if (caseId) {
      fetchPathEvolution();
    }
  }, [caseId, sessionId]);

  // D3 visualization effect
  useEffect(() => {
    if (!data || !svgRef.current || data.snapshots.length === 0) return;

    const currentSnapshot = data.snapshots[Math.min(currentTime, data.snapshots.length - 1)];
    visualizeOnionPeel(svgRef.current, currentSnapshot, data);
  }, [data, currentTime]);

  const visualizeOnionPeel = (svgElement, snapshot, fullData) => {
    // Clear previous content
    d3.select(svgElement).selectAll('*').remove();

    const width = svgElement.clientWidth || 800;
    const height = svgElement.clientHeight || 600;
    const centerX = width / 2;
    const centerY = height / 2;

    // Create SVG
    const svg = d3.select(svgElement)
      .attr('width', width)
      .attr('height', height)
      .style('background', '#f8f9fa');

    // Define layers
    const layers = [
      { name: 'Client', radius: 60, node: snapshot.client, color: '#4CAF50' },
      { name: 'Guard', radius: 130, node: snapshot.guard, color: '#FF9800' },
      { name: 'Middle', radius: 200, node: snapshot.middle, color: '#2196F3' },
      { name: 'Exit', radius: 270, node: snapshot.exit, color: '#F44336' },
      { name: 'Destination', radius: 340, node: snapshot.destination, color: '#9C27B0' }
    ];

    // Draw concentric circles
    layers.forEach((layer, index) => {
      // Layer ring
      svg.append('circle')
        .attr('cx', centerX)
        .attr('cy', centerY)
        .attr('r', layer.radius)
        .attr('fill', 'none')
        .attr('stroke', layer.color)
        .attr('stroke-width', 2)
        .attr('opacity', 0.3);

      // Layer label
      svg.append('text')
        .attr('x', centerX + layer.radius + 20)
        .attr('y', centerY - 10)
        .attr('font-size', '12px')
        .attr('fill', layer.color)
        .attr('font-weight', 'bold')
        .text(layer.name);

      // Node circle
      if (layer.node) {
        // Node glow effect
        svg.append('circle')
          .attr('cx', centerX)
          .attr('cy', centerY - layer.radius)
          .attr('r', 20)
          .attr('fill', layer.color)
          .attr('opacity', 0.1)
          .attr('class', 'node-glow');

        // Node dot
        svg.append('circle')
          .attr('cx', centerX)
          .attr('cy', centerY - layer.radius)
          .attr('r', 12)
          .attr('fill', layer.color)
          .attr('stroke', 'white')
          .attr('stroke-width', 2)
          .attr('cursor', 'pointer')
          .attr('class', 'node-dot')
          .on('mouseover', (event) => {
            d3.select(event.target)
              .attr('r', 16)
              .attr('stroke-width', 3);
            
            showTooltip(event, layer.node);
          })
          .on('mouseout', (event) => {
            d3.select(event.target)
              .attr('r', 12)
              .attr('stroke-width', 2);
            
            hideTooltip();
          });

        // Node label
        svg.append('text')
          .attr('x', centerX)
          .attr('y', centerY - layer.radius + 30)
          .attr('text-anchor', 'middle')
          .attr('font-size', '11px')
          .attr('fill', '#333')
          .text(layer.node.nickname || layer.node.fingerprint.substring(0, 8));
      }
    });

    // Draw connections between nodes
    let prevRadius = 0;
    layers.forEach((layer, index) => {
      if (index > 0 && layer.node && layers[index - 1].node) {
        svg.append('line')
          .attr('x1', centerX)
          .attr('y1', centerY - prevRadius)
          .attr('x2', centerX)
          .attr('y2', centerY - layer.radius)
          .attr('stroke', '#999')
          .attr('stroke-width', 1)
          .attr('opacity', 0.5)
          .attr('stroke-dasharray', '5,5');
      }
      prevRadius = layer.radius;
    });

    // Add timestamp
    svg.append('text')
      .attr('x', 20)
      .attr('y', height - 20)
      .attr('font-size', '14px')
      .attr('fill', '#666')
      .text(`Time: ${new Date(snapshot.timestamp).toLocaleString()}`);
  };

  const showTooltip = (event, node) => {
    if (!node) return;

    const tooltip = d3.select('body')
      .append('div')
      .attr('class', 'onion-tooltip')
      .style('position', 'absolute')
      .style('background', '#333')
      .style('color', '#fff')
      .style('padding', '10px')
      .style('border-radius', '4px')
      .style('pointer-events', 'none')
      .style('font-size', '12px')
      .style('z-index', '1000')
      .style('left', event.pageX + 10 + 'px')
      .style('top', event.pageY + 10 + 'px');

    tooltip.html(`
      <strong>${node.nickname || 'Unknown'}</strong><br/>
      Fingerprint: ${node.fingerprint.substring(0, 16)}...<br/>
      Country: ${node.country || 'N/A'}<br/>
      ASN: ${node.asn || 'N/A'}<br/>
      Uptime: ${node.uptime_percentage?.toFixed(1) || 'N/A'}%<br/>
      Bandwidth: ${node.bandwidth_mbps ? node.bandwidth_mbps.toFixed(1) + ' Mbps' : 'N/A'}
    `);

    tooltip.attr('class', 'onion-tooltip visible');
  };

  const hideTooltip = () => {
    d3.selectAll('.onion-tooltip').remove();
  };

  const handleTimeSliderChange = (e) => {
    setCurrentTime(parseInt(e.target.value));
  };

  if (loading) {
    return <div className="visualization-container">Loading path evolution...</div>;
  }

  if (error) {
    return <div className="visualization-container error">{error}</div>;
  }

  if (!data || data.snapshots.length === 0) {
    return <div className="visualization-container">No path data available for visualization</div>;
  }

  return (
    <div className="visualization-container onion-peel-container">
      <div className="visualization-header">
        <h3>🧅 TOR Path Evolution - Onion Peel View</h3>
        <p>Case: {caseId} | Duration: {data.duration_seconds?.toFixed(1)}s | Snapshots: {data.snapshots.length}</p>
      </div>

      <div className="visualization-stats">
        <div className="stat-item">
          <span>Guard Changes:</span>
          <strong>{data.guard_changes || 0}</strong>
        </div>
        <div className="stat-item">
          <span>Middle Changes:</span>
          <strong>{data.middle_changes || 0}</strong>
        </div>
        <div className="stat-item">
          <span>Exit Changes:</span>
          <strong>{data.exit_changes || 0}</strong>
        </div>
      </div>

      <svg ref={svgRef} className="onion-peel-svg"></svg>

      <div className="timeline-controls">
        <label htmlFor="timeline-slider">Timeline Slider:</label>
        <input
          id="timeline-slider"
          type="range"
          min="0"
          max={data.snapshots.length - 1}
          value={currentTime}
          onChange={handleTimeSliderChange}
          className="timeline-slider"
        />
        <span className="timeline-label">
          {currentTime + 1} / {data.snapshots.length}
        </span>
      </div>

      {data.transitions.length > 0 && (
        <div className="transitions-panel">
          <h4>🔄 Node Transitions</h4>
          <ul className="transitions-list">
            {data.transitions.slice(0, 10).map((transition, idx) => (
              <li key={idx} className={`transition-item ${transition.type}`}>
                <span className="transition-layer">{transition.layer}</span>
                <span className="transition-type">{transition.type}</span>
                <span className="transition-confidence">Confidence: {(transition.confidence * 100).toFixed(0)}%</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default OnionPeelVisualization;
