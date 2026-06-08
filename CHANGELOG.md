# Changelog

## [0.1.0] — 2026-06-07

### Added

- Initial release with 10 clinical failure modes across 4 agent categories
- Deterministic checks for all 10 failure modes
- LLM-as-judge runner (Sonnet for critical, Haiku for high/medium/low)
- run_eval() with deterministic + LLM, short-circuit on deterministic FAIL
- CLI: list, show, run, test, ui
- 20 synthetic test cases
- GitHub Actions CI (Python 3.9–3.12)
- GitHub Actions PyPI publish workflow
- Streamlit web UI (healtheval ui command)
- GitHub Pages landing page

### Failure Modes
SCRIBE-001 Treatment Status Hallucination (critical)
SCRIBE-002 Prior Visit Note Bleed (high)
SCRIBE-003 Fabricated Vitals (critical)
SCRIBE-004 Symptom Negation Flip (critical)
RCM-001 CPT Code Hallucination (high)
RCM-002 Denial Reason Fabrication (high)
REFILL-001 Formulary Non-Adherence Approval (critical)
REFILL-002 Controlled Substance Misclassification (critical)
FAXROUTE-001 Provider Identity Mismatch (high)
PRIORAUTH-001 Criteria Hallucination (high)
