Forensic Notes — TOR Unveil

This document describes what data the system collects, how we produce correlation results, why outputs are probabilistic, and the legal/ethical boundaries for investigators.

1) What data is collected

- Relay metadata from Onionoo: fingerprint, nickname, OR addresses, advertised bandwidth, flags (Exit/Guard/etc.), first_seen, last_seen, hostnames, and AS/hosting provider names.
- Geolocation lookups (when possible) to provide latitude/longitude and country. These are best-effort and may be absent.
- Timestamps of when the system fetched the data (fetched_at) so each record has an acquisition time for reproducibility.
- Derived fields: a deterministic risk score and a short human-readable explanation of the score.
- Generated candidate paths (entry → middle → exit) with a plausibility score and a timestamp when the path was generated.

All data items include simple fields suitable for review by non-technical personnel.

2) How correlation works (plain language)

- We first reduce the full set of relays to a smaller, sensible group to keep the analysis manageable. This selection is deterministic and based on simple rules (for example: only relays marked running, and sorted by advertised bandwidth).
- From this smaller set we form candidate paths: one relay chosen as entry, one as middle, and one as exit.
- Each candidate path receives a plausibility score. The score is a weighted, explainable combination of:
  - How long each relay was active (overlap in observation times)
  - Advertised bandwidth of the relays
  - Relay roles and flags (exit/guard/running)
  - Small penalties/boosts for AS (network) or country similarity/diversity
- We keep the scoring deterministic and intentionally avoid machine learning. This makes it possible to reproduce and explain why a path received a given score.

3) Why outputs are probabilistic

- The system works with observational data, which is incomplete and noisy. For example:
  - A relay may appear under different IPs or hostnames over time.
  - Time delays and sampling frequency can make exact overlap uncertain.
- The plausibility score expresses the degree of confidence in a path, not a statement of guilt. Higher score means the path looks more plausible given the available evidence.

4) Legal and ethical boundaries

- This tool is an investigative aid only. It does not provide proof that a person used Tor for a specific action.
- Operators must follow applicable laws and court orders before acting on the results.
- Minimize data sharing; provide only necessary evidence artifacts when requested by law enforcement.
- Maintain a chain-of-custody: preserve original fetched data and note the `fetched_at` timestamp so any later review can see what data was available at the time of analysis.

5) Reproducibility and audit

- Each relay record includes `fetched_at` and the raw Onionoo fields we used for normalization.
- Candidate generation and scoring are deterministic with documented heuristics; rerunning with the same data should produce the same results.

6) Contact / notes

If in doubt about any interpretation, consult the development team. This document is intended for investigators and judges and avoids technical jargon where possible.
