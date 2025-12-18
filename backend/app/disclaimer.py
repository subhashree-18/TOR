"""
Legal and Ethical Disclaimer Module

Provides consistent legal and ethical disclaimers across all API responses
and forensic reports. This module ensures that users understand the
probabilistic nature of the analysis and the ethical boundaries of the system.

Author: TOR-Unveil Team
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime, timezone


# ============================================================================
# DISCLAIMER TEXT CONSTANTS
# ============================================================================

DISCLAIMER_SHORT = (
    "This system performs probabilistic forensic correlation using metadata "
    "and lawful network evidence. It does not de-anonymize TOR users."
)

DISCLAIMER_MEDIUM = (
    "LEGAL DISCLAIMER: This system performs probabilistic forensic correlation "
    "using publicly available TOR network metadata and lawfully obtained network "
    "evidence. Results represent statistical correlations, not definitive identifications. "
    "This system does not de-anonymize TOR users or compromise TOR network security. "
    "All analysis is conducted within legal and ethical boundaries."
)

DISCLAIMER_FULL = """
================================================================================
                    LEGAL AND ETHICAL DISCLAIMER
================================================================================

PURPOSE AND METHODOLOGY:
This forensic analysis system performs probabilistic correlation using:
- Publicly available TOR relay metadata from the TOR Project's consensus
- Lawfully obtained network evidence (e.g., PCAP captures with proper authorization)
- Statistical inference techniques including Bayesian probability analysis

IMPORTANT LIMITATIONS:
1. PROBABILISTIC NATURE: All results represent statistical correlations and
   probability estimates, NOT definitive identifications. Confidence scores
   indicate correlation strength, not certainty.

2. NO DE-ANONYMIZATION: This system does NOT de-anonymize TOR users. It analyzes
   relay infrastructure patterns and does not compromise TOR's anonymity guarantees
   for end users.

3. LAWFUL USE ONLY: This tool is designed exclusively for lawful forensic
   investigations conducted by authorized personnel with proper legal authority.
   Unauthorized use may violate applicable laws and regulations.

4. METADATA ONLY: Analysis is based on network metadata (timing, bandwidth,
   relay characteristics) - not content inspection or traffic decryption.

5. VERIFICATION REQUIRED: Results should be independently verified and
   corroborated with additional evidence before any legal or investigative action.

ETHICAL GUIDELINES:
- Use only for legitimate law enforcement or authorized security research
- Respect privacy rights and legal constraints in your jurisdiction
- Do not use results to target individuals without proper legal process
- Report any vulnerabilities discovered to the TOR Project responsibly

ACCURACY NOTICE:
Probability scores and confidence levels are derived from statistical models
that may have inherent limitations. False positives and false negatives are
possible. Professional judgment and additional verification are essential.

================================================================================
"""

DISCLAIMER_API = {
    "type": "legal_disclaimer",
    "version": "1.0",
    "summary": DISCLAIMER_SHORT,
    "full_text": DISCLAIMER_MEDIUM,
    "key_points": [
        "Probabilistic correlation using metadata and lawful evidence",
        "Does not de-anonymize TOR users",
        "Results are statistical correlations, not definitive identifications",
        "For authorized forensic use only",
        "Independent verification required before any action",
    ],
    "methodology": {
        "data_sources": [
            "Public TOR relay consensus data",
            "Lawfully obtained network captures",
            "Relay metadata (bandwidth, uptime, flags)",
        ],
        "analysis_type": "Bayesian probabilistic inference",
        "limitations": [
            "Results are probabilistic estimates",
            "Confidence scores indicate correlation strength only",
            "False positives/negatives possible",
            "No content inspection or decryption performed",
        ],
    },
    "legal_notice": (
        "This tool is intended for use by authorized personnel conducting "
        "lawful forensic investigations. Users are responsible for ensuring "
        "compliance with all applicable laws and regulations in their jurisdiction."
    ),
}


# ============================================================================
# DISCLAIMER DATA CLASS
# ============================================================================

@dataclass
class ForensicDisclaimer:
    """
    Structured disclaimer for forensic reports and API responses.
    
    Provides consistent legal and ethical disclaimers with configurable
    detail levels for different use cases.
    """
    
    # Disclaimer detail level
    level: str = "medium"  # "short", "medium", "full"
    
    # Timestamp
    generated_at: Optional[datetime] = None
    
    # Custom additions
    jurisdiction_notice: Optional[str] = None
    case_reference: Optional[str] = None
    
    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now(timezone.utc)
    
    @property
    def text(self) -> str:
        """Get disclaimer text based on level"""
        if self.level == "short":
            return DISCLAIMER_SHORT
        elif self.level == "full":
            return DISCLAIMER_FULL
        else:
            return DISCLAIMER_MEDIUM
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {
            "disclaimer": {
                "text": self.text,
                "level": self.level,
                "generated_at": self.generated_at.isoformat() if self.generated_at else None,
                "key_points": DISCLAIMER_API["key_points"],
                "legal_notice": DISCLAIMER_API["legal_notice"],
            }
        }
        
        if self.jurisdiction_notice:
            result["disclaimer"]["jurisdiction_notice"] = self.jurisdiction_notice
        
        if self.case_reference:
            result["disclaimer"]["case_reference"] = self.case_reference
        
        return result
    
    def to_report_header(self) -> str:
        """Generate disclaimer header for forensic reports"""
        header = DISCLAIMER_FULL
        
        if self.case_reference:
            header += f"\nCase Reference: {self.case_reference}\n"
        
        if self.jurisdiction_notice:
            header += f"\nJurisdiction Notice: {self.jurisdiction_notice}\n"
        
        if self.generated_at:
            header += f"\nGenerated: {self.generated_at.isoformat()}\n"
        
        return header


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_api_disclaimer(level: str = "medium") -> Dict[str, Any]:
    """
    Get disclaimer dictionary for API responses.
    
    Args:
        level: Detail level ("short", "medium", "full")
        
    Returns:
        Dictionary with disclaimer information
    """
    disclaimer = ForensicDisclaimer(level=level)
    return disclaimer.to_dict()


def get_disclaimer_text(level: str = "medium") -> str:
    """
    Get disclaimer text string.
    
    Args:
        level: Detail level ("short", "medium", "full")
        
    Returns:
        Disclaimer text string
    """
    if level == "short":
        return DISCLAIMER_SHORT
    elif level == "full":
        return DISCLAIMER_FULL
    else:
        return DISCLAIMER_MEDIUM


def add_disclaimer_to_response(response: Dict[str, Any], level: str = "short") -> Dict[str, Any]:
    """
    Add disclaimer to an existing API response dictionary.
    
    Args:
        response: Existing response dictionary
        level: Disclaimer detail level
        
    Returns:
        Response with disclaimer added
    """
    disclaimer = ForensicDisclaimer(level=level)
    response["_disclaimer"] = disclaimer.to_dict()["disclaimer"]
    response["_disclaimer"]["notice"] = DISCLAIMER_SHORT
    return response


def create_forensic_report_disclaimer(
    case_reference: Optional[str] = None,
    jurisdiction: Optional[str] = None,
) -> str:
    """
    Create disclaimer for forensic reports.
    
    Args:
        case_reference: Optional case/investigation reference
        jurisdiction: Optional jurisdiction notice
        
    Returns:
        Full disclaimer text for report header
    """
    disclaimer = ForensicDisclaimer(
        level="full",
        case_reference=case_reference,
        jurisdiction_notice=jurisdiction,
    )
    return disclaimer.to_report_header()


def get_methodology_disclosure() -> Dict[str, Any]:
    """
    Get methodology disclosure for transparency.
    
    Returns:
        Dictionary describing analysis methodology
    """
    return {
        "methodology_disclosure": {
            "analysis_type": "Probabilistic Forensic Correlation",
            "techniques": [
                "Bayesian inference for entry node probability estimation",
                "Evidence metric computation (temporal, traffic, stability)",
                "Confidence evolution tracking across observations",
                "Path plausibility assessment",
            ],
            "data_sources": [
                {
                    "name": "TOR Relay Consensus",
                    "type": "Public data",
                    "description": "Publicly available relay metadata from TOR Project",
                },
                {
                    "name": "Network Captures",
                    "type": "Lawful evidence",
                    "description": "PCAP data obtained through proper legal authorization",
                },
            ],
            "limitations": [
                "Results are probability estimates, not certainties",
                "Analysis depends on data quality and completeness",
                "Temporal correlations may have alternative explanations",
                "Network conditions affect measurement accuracy",
            ],
            "verification_requirements": [
                "Independent corroboration recommended",
                "Multiple evidence sources should be considered",
                "Professional forensic judgment required",
                "Legal review before investigative action",
            ],
        }
    }


# ============================================================================
# RESPONSE WRAPPER
# ============================================================================

class DisclaimedResponse:
    """
    Wrapper class for API responses with automatic disclaimer injection.
    
    Usage:
        response = DisclaimedResponse(data={"results": [...]})
        return response.to_dict()  # Includes disclaimer
    """
    
    def __init__(
        self,
        data: Dict[str, Any],
        disclaimer_level: str = "short",
        include_methodology: bool = False,
    ):
        """
        Initialize response wrapper.
        
        Args:
            data: Response data dictionary
            disclaimer_level: Disclaimer detail level
            include_methodology: Whether to include methodology disclosure
        """
        self.data = data
        self.disclaimer_level = disclaimer_level
        self.include_methodology = include_methodology
        self.timestamp = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with disclaimer"""
        result = dict(self.data)
        
        # Add disclaimer
        disclaimer = ForensicDisclaimer(level=self.disclaimer_level)
        result["_meta"] = {
            "disclaimer": DISCLAIMER_SHORT,
            "disclaimer_full": disclaimer.text if self.disclaimer_level != "short" else None,
            "legal_notice": DISCLAIMER_API["legal_notice"],
            "generated_at": self.timestamp.isoformat(),
            "probabilistic_analysis": True,
            "verification_required": True,
        }
        
        # Add methodology if requested
        if self.include_methodology:
            result["_meta"]["methodology"] = get_methodology_disclosure()["methodology_disclosure"]
        
        return result


# ============================================================================
# CONSTANTS FOR EXPORT
# ============================================================================

# Standard disclaimer to append to all API responses
API_RESPONSE_DISCLAIMER = {
    "_disclaimer": DISCLAIMER_SHORT,
    "_legal_notice": DISCLAIMER_API["legal_notice"],
    "_probabilistic_analysis": True,
}

# Disclaimer for inclusion in response headers
RESPONSE_HEADER_DISCLAIMER = (
    "X-Forensic-Disclaimer: Probabilistic correlation analysis. "
    "Does not de-anonymize TOR users. Verification required."
)
