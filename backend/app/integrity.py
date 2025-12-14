# Forensic integrity markers for reports
import hashlib
import json
from datetime import datetime
from typing import Dict, Any

SYSTEM_VERSION = "2.0-Advanced"

def generate_report_hash(report_data: Dict[str, Any]) -> str:
    """Generate deterministic hash of report contents for integrity verification"""
    # Exclude mutable fields
    content = {
        k: v for k, v in report_data.items()
        if k not in ["report_hash", "generated_at", "system_version"]
    }
    
    # Serialize deterministically
    serialized = json.dumps(content, sort_keys=True, default=str)
    
    # Generate SHA-256 hash
    return hashlib.sha256(serialized.encode()).hexdigest()[:16]

def attach_integrity_metadata(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Attach integrity metadata to report"""
    report_data["integrity"] = {
        "generated_at": datetime.utcnow().isoformat(),
        "system_version": SYSTEM_VERSION,
        "report_hash": generate_report_hash(report_data),
        "hash_algorithm": "SHA-256 (truncated to 16 chars)",
        "metadata_only": True,
        "no_traffic_inspection": True,
        "no_decryption_performed": True,
    }
    
    return report_data

def format_integrity_footer() -> str:
    """Generate formatted integrity footer for PDF"""
    return (
        f"Report Generated: {datetime.utcnow().isoformat()} | "
        f"System Version: {SYSTEM_VERSION} | "
        f"Metadata-Only Analysis | No Traffic Inspection | No User Identification"
    )
