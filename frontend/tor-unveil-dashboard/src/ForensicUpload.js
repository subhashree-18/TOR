import React, { useState } from "react";
import axios from "axios";
import {
  Upload,
  AlertCircle,
  CheckCircle,
  FileText,
  Loader,
  X,
  Info,
  BarChart3,
  Search,
  AlertTriangle,
  Zap,
} from "lucide-react";
import "./ForensicUpload.css";

const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

const ForensicUpload = ({ onAnalysisComplete, caseId = null }) => {
  const [files, setFiles] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);

  const SUPPORTED_FORMATS = {
    pcap: {
      name: "PCAP (Packet Capture)",
      accept: ".pcap,.pcapng",
      size: 100, // MB
      description: "Network capture files from tcpdump, Wireshark, etc.",
    },
    log: {
      name: "Network Logs",
      accept: ".log,.txt",
      size: 50, // MB
      description: "Firewall logs, proxy logs, ISP traffic logs",
    },
    csv: {
      name: "Structured Data (CSV)",
      accept: ".csv",
      size: 50, // MB
      description: "Pre-parsed logs in CSV format (timestamp, IP, port)",
    },
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const validateFile = (file) => {
    // Check file size
    const maxSizeMB =
      file.name.endsWith(".pcap") || file.name.endsWith(".pcapng") ? 100 : 50;
    const fileSizeMB = file.size / (1024 * 1024);

    if (fileSizeMB > maxSizeMB) {
      return `File too large (${fileSizeMB.toFixed(2)}MB > ${maxSizeMB}MB)`;
    }

    // Check file type
    const ext = file.name.split(".").pop().toLowerCase();
    const validExts = ["pcap", "pcapng", "log", "txt", "csv"];
    if (!validExts.includes(ext)) {
      return `Unsupported file type (.${ext})`;
    }

    return null;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    processFiles(droppedFiles);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    processFiles(selectedFiles);
  };

  const processFiles = (fileList) => {
    setErrorMessage("");
    const validFiles = [];

    fileList.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        setErrorMessage(`Error - ${file.name}: ${error}`);
      } else {
        validFiles.push({
          file,
          name: file.name,
          size: (file.size / 1024).toFixed(2), // KB
          type: file.name.split(".").pop().toUpperCase(),
          status: "ready",
        });
      }
    });

    if (validFiles.length > 0) {
      setFiles([...files, ...validFiles]);
      setSuccessMessage(`Added ${validFiles.length} file(s) for analysis`);
      setTimeout(() => setSuccessMessage(""), 3000);
    }
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
    setErrorMessage("");
  };

  const analyzeFiles = async () => {
    if (files.length === 0) {
      setErrorMessage("Error - Please select at least one file");
      return;
    }

    setIsAnalyzing(true);
    setErrorMessage("");
    setSuccessMessage("");
    setUploadProgress(0);

    try {
      // Process each file through the forensic upload API endpoint
      // FEATURE 12: FILE UPLOAD FOR FORENSIC CORRELATION
      // Real API call to backend /forensic/upload endpoint
      
      let combinedResults = null;
      let processedCount = 0;

      for (let fileObj of files) {
        try {
          const formData = new FormData();
          formData.append("file", fileObj.file);

          // Upload to real backend endpoint
          console.log(`Uploading forensic file: ${fileObj.name}`);
          
          const response = await axios.post(`${API_URL}/forensic/upload`, formData, {
            headers: {
              "Content-Type": "multipart/form-data",
            },
            timeout: 30000, // 30 second timeout
          });

          processedCount++;
          setUploadProgress(Math.round((processedCount / files.length) * 100));

          if (response.data && response.data.status === "success") {
            console.log(`✓ File processed: ${fileObj.name}`, response.data);

            // Merge results from this file
            if (!combinedResults) {
              combinedResults = response.data;
            } else {
              // Combine results from multiple files
              combinedResults.events.found += response.data.events.found;
              combinedResults.correlation.overlapping_tor_paths += 
                response.data.correlation.overlapping_tor_paths;
              combinedResults.sample_events = [
                ...combinedResults.sample_events,
                ...response.data.sample_events,
              ].slice(0, 20);
            }
          } else {
            setErrorMessage(`Error - File ${fileObj.name}: Invalid response from server`);
            return;
          }
        } catch (error) {
          const errorDetail = error.response?.data?.detail || error.message;
          setErrorMessage(`Error processing ${fileObj.name}: ${errorDetail}`);
          console.error(`Upload error for ${fileObj.name}:`, error);
          return;
        }
      }

      // Transform API response to match component's expected format
      if (combinedResults) {
        const transformedResults = {
          fileCount: files.length,
          totalTimestamps: combinedResults.events.found,
          dateRange: {
            earliest: combinedResults.events.timestamp_range.earliest,
            latest: combinedResults.events.timestamp_range.latest,
          },
          correlatedPaths: combinedResults.correlation.overlapping_tor_paths,
          correlationStrength: (
            (combinedResults.correlation.overlapping_tor_paths / 
            Math.max(1, combinedResults.correlation.total_paths_checked)) * 100
          ).toFixed(1),
          filesProcessed: combinedResults.message,
          processingTime: combinedResults.processing_time_seconds,
          // Extract metadata from paths
          torPaths: combinedResults.correlation.paths || [],
          sampleEvents: combinedResults.sample_events || [],
        };

        setAnalysisResults(transformedResults);
        setSuccessMessage("✓ Forensic analysis complete!");

        if (onAnalysisComplete) {
          onAnalysisComplete(transformedResults);
        }
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message || "Unknown error";
      setErrorMessage(`Error - Forensic analysis failed: ${errorMsg}`);
      console.error("Forensic upload error:", error);
    } finally {
      setIsAnalyzing(false);
      setUploadProgress(0);
    }
  };

  const clearResults = () => {
    setAnalysisResults(null);
    setFiles([]);
    setErrorMessage("");
    setSuccessMessage("");
  };

  if (analysisResults) {
    return (
      <div className="forensic-upload-container results-view">
        <div className="results-header">
          <div className="results-title">
            <CheckCircle className="icon success" size={24} />
            <h2>Forensic Analysis Complete</h2>
          </div>
          <button
            className="clear-button"
            onClick={clearResults}
            title="Clear results and start new analysis"
          >
            <X size={20} />
          </button>
        </div>

        <div className="results-grid">
          <div className="result-card">
            <div className="result-label">Files Analyzed</div>
            <div className="result-value">{analysisResults.fileCount}</div>
            <div className="result-detail">
              {files.map((f) => f.name).join(", ")}
            </div>
          </div>

          <div className="result-card">
            <div className="result-label">Timestamps Extracted</div>
            <div className="result-value">{analysisResults.totalTimestamps}</div>
            <div className="result-detail">
              {new Date(analysisResults.dateRange.earliest).toLocaleDateString()}{" "}
              →{" "}
              {new Date(analysisResults.dateRange.latest).toLocaleDateString()}
            </div>
          </div>

          <div className="result-card">
            <div className="result-label">Correlated TOR Paths</div>
            <div className="result-value">{analysisResults.correlatedPaths}</div>
            <div className="result-detail">
              Correlation strength: {analysisResults.correlationStrength * 100}%
            </div>
          </div>

          <div className="result-card">
            <div className="result-label">IPs Detected</div>
            <div className="result-value">{analysisResults.ipAddresses.length}</div>
            <div className="result-detail">
              {analysisResults.ipAddresses.join(", ")}
            </div>
          </div>
        </div>

        <div className="results-section">
          <h3><FileText size={18} style={{marginRight: "8px", verticalAlign: "middle"}} />Protocols Detected</h3>
          <div className="protocol-list">
            {analysisResults.protocols.map((proto, idx) => (
              <span key={idx} className="protocol-badge">
                {proto}
              </span>
            ))}
          </div>
        </div>

        <div className="results-section">
          <h3><AlertTriangle size={18} style={{marginRight: "8px", verticalAlign: "middle"}} />Suspicious Patterns</h3>
          <div className="patterns-list">
            {analysisResults.suspiciousPatterns.map((pattern, idx) => (
              <div key={idx} className="pattern-item">
                <AlertCircle size={18} className="pattern-icon" />
                <span>{pattern}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="results-section">
          <h3><BarChart3 size={18} style={{marginRight: "8px", verticalAlign: "middle"}} />Correlated Timeline</h3>
          <div className="timeline-list">
            {analysisResults.timeline.map((event, idx) => (
              <div key={idx} className="timeline-item">
                <div className="timeline-time">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </div>
                <div className="timeline-event">
                  <div className="timeline-text">{event.event}</div>
                  <div className="timeline-confidence">
                    Confidence: {event.confidence}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="legal-notice">
          <Info size={18} />
          <div>
            <strong>Metadata-Only Correlation:</strong> This analysis uses only
            timestamps and connection metadata from your logs. No packet payload
            inspection was performed. Results indicate timing correlations with
            TOR relay activity and should be corroborated with other evidence
            before use in investigation.
          </div>
        </div>

        <button className="analyze-button new-analysis" onClick={clearResults}>
          <Zap size={16} style={{marginRight: "6px", display: "inline"}} />New Analysis
        </button>
      </div>
    );
  }

  return (
    <div className="forensic-upload-container">
      <div className="upload-header">
        <h2><Search size={24} style={{marginRight: "10px", verticalAlign: "middle"}} />Forensic Evidence Correlation</h2>
        <p>Upload network logs or PCAP files for timestamp correlation with TOR activity</p>
      </div>

      <div className="legal-disclaimer">
        <AlertCircle size={20} />
        <div>
          <strong>Important:</strong> This tool performs metadata-only analysis.
          No packet content inspection. Timestamps are correlated with TOR relay
          activity to assist investigation.
        </div>
      </div>

      <div className="format-info">
        <h3>📁 Supported Formats</h3>
        <div className="format-grid">
          {Object.entries(SUPPORTED_FORMATS).map(([key, format]) => (
            <div key={key} className="format-card">
              <FileText size={20} />
              <div className="format-name">{format.name}</div>
              <div className="format-detail">{format.description}</div>
              <div className="format-size">Max: {format.size}MB</div>
            </div>
          ))}
        </div>
      </div>

      <div
        className={`drop-zone ${dragActive ? "active" : ""}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <Upload size={48} className="upload-icon" />
        <h3>Drop files here or click to browse</h3>
        <p>PCAP, network logs, firewall logs, ISP traffic logs</p>
        <input
          type="file"
          multiple
          accept=".pcap,.pcapng,.log,.txt,.csv"
          onChange={handleFileSelect}
          className="file-input"
          id="forensic-file-input"
        />
      </div>

      {errorMessage && (
        <div className="error-banner">
          <AlertCircle size={18} />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="success-banner">
          <CheckCircle size={18} />
          <span>{successMessage}</span>
        </div>
      )}

      {files.length > 0 && (
        <div className="files-section">
          <h3>📄 Selected Files ({files.length})</h3>
          <div className="files-list">
            {files.map((fileObj, idx) => (
              <div key={idx} className="file-item">
                <div className="file-info">
                  <FileText size={18} />
                  <div className="file-details">
                    <div className="file-name">{fileObj.name}</div>
                    <div className="file-meta">
                      {fileObj.type} • {fileObj.size}KB
                    </div>
                  </div>
                </div>
                <button
                  className="remove-button"
                  onClick={() => removeFile(idx)}
                  title="Remove file"
                >
                  <X size={18} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {files.length > 0 && (
        <button
          className={`analyze-button ${isAnalyzing ? "analyzing" : ""}`}
          onClick={analyzeFiles}
          disabled={isAnalyzing}
        >
          {isAnalyzing ? (
            <>
              <Loader size={20} className="spinner" />
              Analyzing Files...
            </>
          ) : (
            <>
              <AlertCircle size={20} />
              Start Correlation Analysis
            </>
          )}
        </button>
      )}

      <div className="methodology-footer">
        <h3>🔬 Methodology</h3>
        <ul>
          <li>
            <strong>File Parsing:</strong> Extract timestamps from PCAP/log files
          </li>
          <li>
            <strong>Metadata Extraction:</strong> IP addresses, ports, protocols
            (no packet content)
          </li>
          <li>
            <strong>TOR Correlation:</strong> Match timestamps with relay activity
            windows
          </li>
          <li>
            <strong>Confidence Scoring:</strong> Strength of temporal correlation
          </li>
          <li>
            <strong>Pattern Detection:</strong> Identify suspicious timing patterns
          </li>
        </ul>
      </div>
    </div>
  );
};

export default ForensicUpload;
