/**
 * Breadcrumb.js ??? PHASE-2 GOVERNMENT NAVIGATION
 * Tamil Nadu Police Cyber Crime Wing - Investigation Progress Indicator
 * 
 * Purpose: Show investigation progress clearly to officers
 * Format: Dashboard > Investigation > Evidence > Analysis > Report
 * Style: Text-only, no icons, highlight current step, disable based on backend status
 */

import React from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import './Breadcrumb.css';

// Navigation steps in investigation workflow
const WORKFLOW_STEPS = [
  { id: 'dashboard', label: 'Dashboard', path: '/' },
  { id: 'investigation', label: 'Investigation', path: '/investigation' },
  { id: 'evidence', label: 'Evidence', path: '/evidence' },
  { id: 'analysis', label: 'Analysis', path: '/analysis' },
  { id: 'report', label: 'Report', path: '/report' }
];

/**
 * Breadcrumb Component
 * Props:
 *   - caseStatus: Object from backend with status fields
 *     { hasEvidence: bool, hasAnalysis: bool, isComplete: bool }
 *   - caseId: Current case identifier (optional)
 */
function Breadcrumb({ caseStatus = {}, caseId = null }) {
  const navigate = useNavigate();
  const location = useLocation();
  const params = useParams();
  
  // Use params caseId if not passed as prop
  const activeCaseId = caseId || params.caseId;
  
  // Determine current step from URL path
  const getCurrentStep = () => {
    const path = location.pathname;
    if (path === '/') return 'dashboard';
    if (path.includes('/investigation')) return 'investigation';
    if (path.includes('/forensic-upload') || path.includes('/evidence')) return 'evidence';
    if (path.includes('/forensic-analysis') || path.includes('/analysis')) return 'analysis';
    if (path.includes('/report')) return 'report';
    return 'dashboard';
  };
  
  const currentStep = getCurrentStep();
  
  // Determine which steps are enabled based on backend case status
  const isStepEnabled = (stepId) => {
    switch (stepId) {
      case 'dashboard':
        // Dashboard always accessible
        return true;
      case 'investigation':
        // Investigation requires a case to be selected
        return !!activeCaseId;
      case 'evidence':
        // Evidence requires a case
        return !!activeCaseId;
      case 'analysis':
        // Analysis requires evidence uploaded
        return cat > /home/subha/Downloads/tor-unveil/frontend/tor-unveil-dashboard/src/ReportPage.css << 'EOF'
/* ReportPage.css ??? PHASE-2 FINAL FORENSIC REPORT
 * Tamil Nadu Police Cyber Crime Wing - Official Government Report
 * Design: White background, black text, document-style, print-friendly
 */

/* ========== MAIN CONTAINER ========== */
.report-page {
  padding: 20px 24px;
  background: #f5f7fa;
  min-height: 100%;
}

/* ========== SCREEN-ONLY CONTROLS ========== */
.report-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.report-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-family: "Segoe UI", Arial, sans-serif;
}

.report-breadcrumb .crumb {
  color: #0b3c5d;
  cursor: pointer;
  text-decoration: underline;
}

.report-breadcrumb .crumb:hover {
  color: #094056;
}

.report-breadcrumb .crumb.active {
  color: #333;
  text-decoration: none;
  cursor: default;
  font-weight: 600;
}

.report-breadcrumb .separator {
  color: #999;
}

.export-buttons {
  display: flex;
  gap: 12px;
}

.btn-export {
  background: #0b3c5d;
  color: #fff;
  border: 1px solid #0b3c5d;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: "Segoe UI", Arial, sans-serif;
}

.btn-export:hover {
  background: #094056;
}

.btn-export-secondary {
  background: #fff;
  color: #0b3c5d;
  border: 1px solid #0b3c5d;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: "Segoe UI", Arial, sans-serif;
}

.btn-export-secondary:hover {
  background: #e8f4fc;
}

/* ========== LOADING/ERROR STATES ========== */
.report-loading,
.report-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: #fff;
  border: 1px solid #d0d5dd;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #d0d5dd;
  border-top-color: #0b3c5d;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.report-loading p {
  font-size: 14px;
  color: #555;
  margin: 0;
}

.report-error p {
  color: #dc3545;
  margin: 0 0 16px 0;
}

.report-error button {
  background: #0b3c5d;
  color: #fff;
  border: none;
  padding: 8px 20px;
  cursor: pointer;
}

/* ========== REPORT DOCUMENT ========== */
.report-document {
  background: #fff;
  border: 1px solid #d0d5dd;
  padding: 40px 50px;
  max-width: 850px;
  margin: 0 auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  font-family: "Times New Roman", Times, serif;
  font-size: 12pt;
  line-height: 1.6;
  color: #000;
}

/* ========== REPORT HEADER ========== */
.report-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #000;
}

.header-emblem {
  margin-bottom: 16px;
}

.emblem-placeholder {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border: 2px solid #000;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 700;
  font-family: "Segoe UI", Arial, sans-serif;
}

.header-title h1 {
  font-size: 18pt;
  font-weight: 700;
  margin: 0 0 4px 0;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.header-title h2 {
  font-size: 14pt;
  font-weight: 400;
  margin: 0 0 8px 0;
}

.header-subtitle {
  font-size: 11pt;
  font-style: italic;
  margin: 0;
  color: #333;
}

.header-meta {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}

.meta-item {
  text-align: left;
}

.meta-label {
  font-weight: 700;
  font-size: 10pt;
}

.meta-value {
  font-size: 10pt;
  margin-left: 8px;
}

/* ========== REPORT SECTIONS ========== */
.report-section {
  margin-bottom: 28px;
  page-break-inside: avoid;
}

.section-number {
  display: inline;
  font-size: 12pt;
  font-weight: 700;
  margin: 0 8px 0 0;
}

.section-title {
  display: inline;
  font-size: 12pt;
  font-weight: 700;
  text-transform: uppercase;
  text-decoration: underline;
  margin: 0 0 12px 0;
}

.section-content {
  margin-top: 12px;
  text-align: justify;
}

.section-content p {
  margin: 0 0 12px 0;
  text-indent: 2em;
}

.section-content p:first-child {
  text-indent: 0;
}

/* ========== DISCLAIMER SECTION ========== */
.disclaimer-section {
  border: 1px solid #000;
  padding: 16px;
  background: #fafafa;
}

.disclaimer-content {
  font-size: 10pt;
}

.disclaimer-content p {
  text-indent: 0;
}

/* ========== REPORT FOOTER ========== */
.report-footer {
  margin-top: 40px;
  padding-top: 20px;
}

.footer-line {
  border-top: 1px solid #000;
  margin-bottom: 12px;
}

.footer-content {
  text-align: center;
  font-size: 9pt;
  color: #333;
}

.footer-content p {
  margin: 0 0 4px 0;
}

.footer-page {
  margin-top: 8px !important;
  font-style: italic;
}

/* ========== BACK BUTTON ========== */
.report-actions {
  max-width: 850px;
  margin: 20px auto 0;
  text-align: left;
}

.btn-back {
  background: #fff;
  color: #0b3c5d;
  border: 1px solid #0b3c5d;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: "Segoe UI", Arial, sans-serif;
}

.btn-back:hover {
  background: #e8f4fc;
}

/* ========== RESPONSIVE ========== */
@media (max-width: 900px) {
  .report-document {
    padding: 24px;
    margin: 0;
  }
  
  .header-meta {
    flex-direction: column;
    gap: 8px;
    align-items: center;
  }
  
  .report-controls {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* ========== PRINT STYLES ========== */
.no-print {
  /* Will be hidden in print */
}

@media print {
  @page {
    size: A4;
    margin: 20mm;
  }
  
  body {
    background: #fff !important;
  }
  
  .report-page {
    background: #fff;
    padding: 0;
  }
  
  .no-print {
    display: none !important;
  }
  
  .report-document {
    border: none;
    box-shadow: none;
    padding: 0;
    max-width: none;
  }
  
  .report-section {
    page-break-inside: avoid;
  }
  
  .disclaimer-section {
    background: #fff;
  }
  
  .report-header {
    border-bottom: 2px solid #000;
  }
  
  .footer-line {
    border-top: 1px solid #000;
  }
}
EOFactiveCaseId && caseStatus.hasEvidence;
      case 'report':
        // Report requires analysis complete
        return cat > /home/subha/Downloads/tor-unveil/frontend/tor-unveil-dashboard/src/ReportPage.css << 'EOF'
/* ReportPage.css ??? PHASE-2 FINAL FORENSIC REPORT
 * Tamil Nadu Police Cyber Crime Wing - Official Government Report
 * Design: White background, black text, document-style, print-friendly
 */

/* ========== MAIN CONTAINER ========== */
.report-page {
  padding: 20px 24px;
  background: #f5f7fa;
  min-height: 100%;
}

/* ========== SCREEN-ONLY CONTROLS ========== */
.report-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.report-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-family: "Segoe UI", Arial, sans-serif;
}

.report-breadcrumb .crumb {
  color: #0b3c5d;
  cursor: pointer;
  text-decoration: underline;
}

.report-breadcrumb .crumb:hover {
  color: #094056;
}

.report-breadcrumb .crumb.active {
  color: #333;
  text-decoration: none;
  cursor: default;
  font-weight: 600;
}

.report-breadcrumb .separator {
  color: #999;
}

.export-buttons {
  display: flex;
  gap: 12px;
}

.btn-export {
  background: #0b3c5d;
  color: #fff;
  border: 1px solid #0b3c5d;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: "Segoe UI", Arial, sans-serif;
}

.btn-export:hover {
  background: #094056;
}

.btn-export-secondary {
  background: #fff;
  color: #0b3c5d;
  border: 1px solid #0b3c5d;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: "Segoe UI", Arial, sans-serif;
}

.btn-export-secondary:hover {
  background: #e8f4fc;
}

/* ========== LOADING/ERROR STATES ========== */
.report-loading,
.report-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: #fff;
  border: 1px solid #d0d5dd;
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid #d0d5dd;
  border-top-color: #0b3c5d;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.report-loading p {
  font-size: 14px;
  color: #555;
  margin: 0;
}

.report-error p {
  color: #dc3545;
  margin: 0 0 16px 0;
}

.report-error button {
  background: #0b3c5d;
  color: #fff;
  border: none;
  padding: 8px 20px;
  cursor: pointer;
}

/* ========== REPORT DOCUMENT ========== */
.report-document {
  background: #fff;
  border: 1px solid #d0d5dd;
  padding: 40px 50px;
  max-width: 850px;
  margin: 0 auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  font-family: "Times New Roman", Times, serif;
  font-size: 12pt;
  line-height: 1.6;
  color: #000;
}

/* ========== REPORT HEADER ========== */
.report-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #000;
}

.header-emblem {
  margin-bottom: 16px;
}

.emblem-placeholder {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border: 2px solid #000;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 700;
  font-family: "Segoe UI", Arial, sans-serif;
}

.header-title h1 {
  font-size: 18pt;
  font-weight: 700;
  margin: 0 0 4px 0;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.header-title h2 {
  font-size: 14pt;
  font-weight: 400;
  margin: 0 0 8px 0;
}

.header-subtitle {
  font-size: 11pt;
  font-style: italic;
  margin: 0;
  color: #333;
}

.header-meta {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}

.meta-item {
  text-align: left;
}

.meta-label {
  font-weight: 700;
  font-size: 10pt;
}

.meta-value {
  font-size: 10pt;
  margin-left: 8px;
}

/* ========== REPORT SECTIONS ========== */
.report-section {
  margin-bottom: 28px;
  page-break-inside: avoid;
}

.section-number {
  display: inline;
  font-size: 12pt;
  font-weight: 700;
  margin: 0 8px 0 0;
}

.section-title {
  display: inline;
  font-size: 12pt;
  font-weight: 700;
  text-transform: uppercase;
  text-decoration: underline;
  margin: 0 0 12px 0;
}

.section-content {
  margin-top: 12px;
  text-align: justify;
}

.section-content p {
  margin: 0 0 12px 0;
  text-indent: 2em;
}

.section-content p:first-child {
  text-indent: 0;
}

/* ========== DISCLAIMER SECTION ========== */
.disclaimer-section {
  border: 1px solid #000;
  padding: 16px;
  background: #fafafa;
}

.disclaimer-content {
  font-size: 10pt;
}

.disclaimer-content p {
  text-indent: 0;
}

/* ========== REPORT FOOTER ========== */
.report-footer {
  margin-top: 40px;
  padding-top: 20px;
}

.footer-line {
  border-top: 1px solid #000;
  margin-bottom: 12px;
}

.footer-content {
  text-align: center;
  font-size: 9pt;
  color: #333;
}

.footer-content p {
  margin: 0 0 4px 0;
}

.footer-page {
  margin-top: 8px !important;
  font-style: italic;
}

/* ========== BACK BUTTON ========== */
.report-actions {
  max-width: 850px;
  margin: 20px auto 0;
  text-align: left;
}

.btn-back {
  background: #fff;
  color: #0b3c5d;
  border: 1px solid #0b3c5d;
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: "Segoe UI", Arial, sans-serif;
}

.btn-back:hover {
  background: #e8f4fc;
}

/* ========== RESPONSIVE ========== */
@media (max-width: 900px) {
  .report-document {
    padding: 24px;
    margin: 0;
  }
  
  .header-meta {
    flex-direction: column;
    gap: 8px;
    align-items: center;
  }
  
  .report-controls {
    flex-direction: column;
    align-items: flex-start;
  }
}

/* ========== PRINT STYLES ========== */
.no-print {
  /* Will be hidden in print */
}

@media print {
  @page {
    size: A4;
    margin: 20mm;
  }
  
  body {
    background: #fff !important;
  }
  
  .report-page {
    background: #fff;
    padding: 0;
  }
  
  .no-print {
    display: none !important;
  }
  
  .report-document {
    border: none;
    box-shadow: none;
    padding: 0;
    max-width: none;
  }
  
  .report-section {
    page-break-inside: avoid;
  }
  
  .disclaimer-section {
    background: #fff;
  }
  
  .report-header {
    border-bottom: 2px solid #000;
  }
  
  .footer-line {
    border-top: 1px solid #000;
  }
}
EOFactiveCaseId && caseStatus.hasAnalysis;
      default:
        return false;
    }
  };
  
  // Get step path with caseId if needed
  const getStepPath = (step) => {
    if (step.id === 'dashboard') return '/';
    if (!activeCaseId) return step.path;
    
    // Map to actual routes in the app
    switch (step.id) {
      case 'investigation':
        return `/investigation/${activeCaseId}`;
      case 'evidence':
        return `/forensic-upload/${activeCaseId}`;
      case 'analysis':
        return `/analysis/${activeCaseId}`;
      case 'report':
        return `/report/${activeCaseId}`;
      default:
        return step.path;
    }
  };
  
  // Handle step click
  const handleStepClick = (step) => {
    if (!isStepEnabled(step.id)) return;
    if (step.id === currentStep) return;
    
    navigate(getStepPath(step));
  };
  
  // Determine step state for styling
  const getStepState = (stepId, stepIndex) => {
    const currentIndex = WORKFLOW_STEPS.findIndex(s => s.id === currentStep);
    
    if (stepId === currentStep) return 'current';
    if (stepIndex < currentIndex) return 'completed';
    if (!isStepEnabled(stepId)) return 'disabled';
    return 'available';
  };

  return (
    <nav className="breadcrumb-nav" aria-label="Investigation Progress">
      <ol className="breadcrumb-list">
        {WORKFLOW_STEPS.map((step, index) => {
          const state = getStepState(step.id, index);
          const enabled = isStepEnabled(step.id);
          
          return (
            <li key={step.id} className="breadcrumb-item">
              <span
                className={`breadcrumb-step ${state}`}
                onClick={() => handleStepClick(step)}
                role="button"
                tabIndex={enabled ? 0 : -1}
                aria-current={state === 'current' ? 'step' : undefined}
                aria-disabled={!enabled}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleStepClick(step);
                  }
                }}
              >
                {step.label}
              </span>
              {index < WORKFLOW_STEPS.length - 1 && (
                <span className="breadcrumb-separator" aria-hidden="true">???</span>
              )}
            </li>
          );
        })}
      </ol>
      
      {/* Case ID indicator if a case is active */}
      {activeCaseId && (
        <span className="breadcrumb-case-id">
          Case: {activeCaseId}
        </span>
      )}
    </nav>
  );
}

export default Breadcrumb;
