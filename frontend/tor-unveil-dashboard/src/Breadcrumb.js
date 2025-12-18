/**
 * Breadcrumb.js — PHASE-2 GOVERNMENT NAVIGATION
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
        // Analysis requires evidence to be uploaded
        return !!activeCaseId && !!caseStatus.hasEvidence;
      case 'report':
        // Report requires analysis to be completed
        return !!activeCaseId && !!caseStatus.hasEvidence && !!caseStatus.hasAnalysis;
      default:
        return false;
    }
  };
  
  // Get disabled hint message for a step
  const getDisabledHint = (stepId) => {
    if (isStepEnabled(stepId)) return '';
    
    switch (stepId) {
      case 'investigation':
        return 'Select a case from Dashboard to proceed.';
      case 'evidence':
        return 'Complete previous stage to proceed.';
      case 'analysis':
        return 'Complete evidence upload to proceed.';
      case 'report':
        return 'Complete analysis to proceed.';
      default:
        return 'Complete previous stage to proceed.';
    }
  };
  
  // Handle step click
  const handleStepClick = (step) => {
    if (!isStepEnabled(step.id)) return;
    
    if (step.id === 'dashboard') {
      navigate('/');
    } else {
      navigate(step.path, { state: { caseId: activeCaseId } });
    }
  };
  
  // Get CSS class for step
  const getStepClass = (stepId) => {
    if (stepId === currentStep) return 'breadcrumb-step active';
    if (!isStepEnabled(stepId)) return 'breadcrumb-step disabled';
    return 'breadcrumb-step enabled';
  };

  return (
    <nav className="breadcrumb-navigation" aria-label="Investigation progress">
      <ol className="breadcrumb-list">
        {WORKFLOW_STEPS.map((step, index) => {
          const enabled = isStepEnabled(step.id);
          const hint = getDisabledHint(step.id);
          
          return (
            <li key={step.id} className="breadcrumb-item">
              <span
                className={getStepClass(step.id)}
                onClick={() => {
                  if (enabled) {
                    handleStepClick(step);
                  }
                }}
                title={hint}
                aria-disabled={!enabled}
                role={enabled ? "button" : "text"}
                tabIndex={enabled ? 0 : -1}
              >
                {step.label}
                {!enabled && hint && (
                  <span className="disabled-hint">{hint}</span>
                )}
              </span>
              {index < WORKFLOW_STEPS.length - 1 && (
                <span className="breadcrumb-separator" aria-hidden="true">›</span>
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