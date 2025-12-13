import React, { useState } from "react";
import {
  BookOpen,
  FileUp,
  BarChart3,
  Archive,
  Network,
  Zap,
  Check,
  AlertCircle as AlertIcon,
  GitBranch,
  Download,
} from "lucide-react";
import ForensicUpload from "./ForensicUpload";
import ForensicAnalysis from "./ForensicAnalysis";
import "./ForensicPage.css";

const ForensicPage = ({ caseId = null }) => {
  const [activeTab, setActiveTab] = useState("upload");
  const [analysisData, setAnalysisData] = useState(null);

  const handleAnalysisComplete = (data) => {
    setAnalysisData(data);
    // Auto-switch to analysis tab after upload completes
    setTimeout(() => setActiveTab("analysis"), 500);
  };

  return (
    <div className="forensic-page-container">
      <div className="page-header">
        <div className="header-content">
          <BookOpen size={32} className="page-icon" />
          <div>
            <h1>Forensic Evidence Correlation</h1>
            <p>
              Upload network logs or PCAP files to correlate with TOR activity metadata
            </p>
          </div>
        </div>
      </div>

      <div className="tabs-container">
        <div className="tabs-header">
          <button
            className={`tab-button ${activeTab === "upload" ? "active" : ""}`}
            onClick={() => setActiveTab("upload")}
          >
            <FileUp size={16} style={{marginRight: "8px"}} />Upload Evidence
            {!analysisData && <span className="tab-badge new">New</span>}
          </button>
          <button
            className={`tab-button ${activeTab === "analysis" ? "active" : ""}`}
            onClick={() => setActiveTab("analysis")}
            disabled={!analysisData}
          >
            <Network size={16} style={{marginRight: "8px"}} />View Correlations
            {analysisData && <span className="tab-badge complete">Ready</span>}
          </button>
        </div>

        <div className="tabs-content">
          {activeTab === "upload" && (
            <div className="tab-pane active">
              <ForensicUpload
                onAnalysisComplete={handleAnalysisComplete}
                caseId={caseId}
              />
            </div>
          )}
          {activeTab === "analysis" && (
            <div className="tab-pane active">
              <ForensicAnalysis forensicData={analysisData} />
            </div>
          )}
        </div>
      </div>

      <div className="methodology-section">
        <h2><Zap size={24} style={{marginRight: "10px"}} />How Forensic Correlation Works</h2>

        <div className="methodology-grid">
          <div className="methodology-card">
            <div className="card-icon"><FileUp size={32} /></div>
            <h3>File Upload & Parsing</h3>
            <p>
              Upload your PCAP files or network logs. System parses timestamps,
              IP addresses, and connection metadata.
            </p>
          </div>

          <div className="methodology-card">
            <div className="card-icon"><Network size={32} /></div>
            <h3>Metadata Extraction</h3>
            <p>
              Extract connection metadata: source/dest IPs, ports, protocols,
              timestamps. <strong>NO packet payload inspection.</strong>
            </p>
          </div>

          <div className="methodology-card">
            <div className="card-icon"><BarChart3 size={32} /></div>
            <h3>Timestamp Alignment</h3>
            <p>
              Compare timestamps from your logs with TOR relay uptime windows
              and activity records from Onionoo.
            </p>
          </div>

          <div className="methodology-card">
            <div className="card-icon"><GitBranch size={32} /></div>
            <h3>Path Correlation</h3>
            <p>
              Identify plausible TOR paths where timing aligns with relay
              activity. Calculate correlation strength scores.
            </p>
          </div>

          <div className="methodology-card">
            <div className="card-icon"><Zap size={32} /></div>
            <h3>Confidence Scoring</h3>
            <p>
              Score plausibility based on temporal overlap, frequency of matches,
              and consistency of evidence.
            </p>
          </div>

          <div className="methodology-card">
            <div className="card-icon"><Download size={32} /></div>
            <h3>Report Generation</h3>
            <p>
              Generate forensic report with all correlated paths, confidence
              scores, and methodology explanation.
            </p>
          </div>
        </div>
      </div>

      <div className="investigation-workflow">
        <h2><GitBranch size={28} style={{marginRight: "10px", verticalAlign: "middle"}} />Forensic Investigation Workflow</h2>

        <div className="workflow-steps">
          <div className="step">
            <div className="step-icon"><Archive size={28} /></div>
            <div className="step-content">
              <h4>Prepare Evidence</h4>
              <p>
                Gather network logs, PCAP captures, firewall logs from your
                investigation. Ensure timestamps are accurate.
              </p>
            </div>
          </div>

          <div className="arrow">↓</div>

          <div className="step">
            <div className="step-icon"><FileUp size={28} /></div>
            <div className="step-content">
              <h4>Upload to TOR UNVEIL</h4>
              <p>
                Click "Upload Evidence" tab. Drag and drop or browse to select
                PCAP/log files.
              </p>
            </div>
          </div>

          <div className="arrow">↓</div>

          <div className="step">
            <div className="step-icon"><BarChart3 size={28} /></div>
            <div className="step-content">
              <h4>Review Correlations</h4>
              <p>
                System analyzes and shows plausible TOR paths with confidence
                scores. Review findings and reasoning for each path.
              </p>
            </div>
          </div>

          <div className="arrow">↓</div>

          <div className="step">
            <div className="step-icon"><Download size={28} /></div>
            <div className="step-content">
              <h4>Export Report</h4>
              <p>
                Generate forensic report showing methodology, correlated paths,
                confidence scores, and court presentation guidelines.
              </p>
            </div>
          </div>

          <div className="arrow">↓</div>

          <div className="step">
            <div className="step-icon"><Check size={28} /></div>
            <div className="step-content">
              <h4>Corroborate Evidence</h4>
              <p>
                Use TOR correlations alongside other evidence (logs, behavior,
                witness testimony) for strongest case.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="critical-notes">
        <h2><AlertIcon size={28} style={{marginRight: "10px", verticalAlign: "middle"}} />Critical Notes for Court Use</h2>

        <div className="notes-grid">
          <div className="note-card">
            <h4><AlertIcon size={18} style={{marginRight: "8px"}} />Metadata-Only Analysis</h4>
            <p>
              This system analyzes timestamps and metadata ONLY. No packet
              content, encryption keys, or payload inspection is performed.
            </p>
          </div>

          <div className="note-card">
            <h4><BarChart3 size={18} style={{marginRight: "8px"}} />Plausibility, Not Proof</h4>
            <p>
              Correlations show plausible paths. Multiple paths may be equally
              plausible. High scores indicate evidence alignment, not certainty.
            </p>
          </div>

          <div className="note-card">
            <h4><Check size={18} style={{marginRight: "8px"}} />Always Corroborate</h4>
            <p>
              Present TOR analysis with corroborating evidence. Behavioral
              patterns, ISP logs, financial transactions strengthen your case.
            </p>
          </div>

          <div className="note-card">
            <h4><AlertIcon size={18} style={{marginRight: "8px"}} />Expert Testimony</h4>
            <p>
              Be prepared to explain methodology to court. State limitations
              clearly. Acknowledge alternative explanations. Answer questions
              about timestamp accuracy.
            </p>
          </div>

          <div className="note-card">
            <h4><AlertIcon size={18} style={{marginRight: "8px"}} />Never Claim Deanonymization</h4>
            <p>
              Do NOT claim the system identifies TOR users or breaks TOR. Do NOT
              claim 100% certainty. This evidence assists investigation, doesn't
              prove identity.
            </p>
          </div>

          <div className="note-card">
            <h4><Check size={18} style={{marginRight: "8px"}} />Best Practices</h4>
            <p>
              Document case ID. Record officer name and timestamps. Maintain
              chain of custody. Save all reports. Keep evidence separate from
              analysis.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForensicPage;
