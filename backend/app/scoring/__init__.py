"""
TOR Unveil Evidence Scoring Module

This package provides independent evidence metrics for analyzing TOR relay paths.
Each metric is independently testable and returns normalized values (0.0-1.0).

Available Functions:
- time_overlap_score: Temporal alignment of relay uptime windows
- traffic_similarity_score: Traffic pattern analysis across path
- relay_stability_score: Infrastructure stability assessment
- path_consistency_score: Path architecture plausibility
- geo_plausibility_score: Geographic distribution analysis
- pcap_evidence_score: PCAP forensic evidence analysis
- compute_evidence_summary: Aggregate evidence report

Example Usage:
    from backend.app.scoring.evidence import (
        time_overlap_score,
        relay_stability_score,
        pcap_evidence_score,
        compute_evidence_summary
    )
    
    # Compute individual metrics
    temporal = time_overlap_score(
        entry_uptime=(datetime(2024,1,1), datetime(2024,1,10)),
        middle_uptime=(datetime(2024,1,2), datetime(2024,1,12)),
        exit_uptime=(datetime(2024,1,3), datetime(2024,1,8)),
    )
    
    stability = relay_stability_score(
        entry_uptime_days=9.0,
        middle_uptime_days=10.0,
        exit_uptime_days=5.0,
        entry_tor_flags=["Running", "Valid", "Stable"],
    )
    
    # Compute PCAP evidence (if available)
    pcap = pcap_evidence_score(pcap_evidence=flow_evidence)
    
    # Aggregate into report
    report = compute_evidence_summary(
        time_overlap=temporal,
        traffic_similarity=...,
        relay_stability=stability,
        path_consistency=...,
        geo_plausibility=...,
        pcap_evidence=pcap,
    )
"""

from .evidence import (
    time_overlap_score,
    traffic_similarity_score,
    relay_stability_score,
    path_consistency_score,
    geo_plausibility_score,
    pcap_evidence_score,
    compute_evidence_summary,
)

from .bayes_inference import (
    BayesianEntryInference,
    RelayInfo,
    EvidenceObservation,
    create_relay_info,
    posterior_probability_given_evidence,
)

from .confidence_calculator import (
    ConfidenceCalculator,
    EvidenceMetrics,
)

from .confidence_evolution import (
    ConfidenceSnapshot,
    ConfidenceTimeline,
    ConfidenceEvolutionTracker,
    InvestigationConfidenceManager,
    ConfidenceChangeReason,
    ConfidenceTrend,
)

__all__ = [
    # Evidence metrics
    "time_overlap_score",
    "traffic_similarity_score",
    "relay_stability_score",
    "path_consistency_score",
    "geo_plausibility_score",
    "pcap_evidence_score",
    "compute_evidence_summary",
    # Bayesian inference
    "BayesianEntryInference",
    "RelayInfo",
    "EvidenceObservation",
    "create_relay_info",
    "posterior_probability_given_evidence",
    # Confidence calculation
    "ConfidenceCalculator",
    "EvidenceMetrics",
    # Confidence evolution
    "ConfidenceSnapshot",
    "ConfidenceTimeline",
    "ConfidenceEvolutionTracker",
    "InvestigationConfidenceManager",
    "ConfidenceChangeReason",
    "ConfidenceTrend",
]

__version__ = "1.2.0"
__description__ = "Independent evidence metrics for TOR relay correlation analysis"
