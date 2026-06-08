"""
healtheval — Clinical failure mode evaluation library for healthcare AI agents.

Quick start:
    from healtheval import run_eval

    result = run_eval(
        "SCRIBE-001",
        run_llm=False,
        context="Metformin was discontinued on 2024-11-14.",
        agent_output="Patient is currently on metformin 500mg twice daily.",
    )
    print(result.final_verdict)  # FAIL
    print(result.failed)         # True
"""

from .loader import load_failure_mode, load_all_failure_modes, load_by_category, list_failure_modes
from .models import EvalResult, EvalVerdict, Severity, AgentCategory, FailureMode, DeterministicResult, LLMEvalResult
from .deterministic import run_deterministic_check
from .runner import run_llm_eval, run_eval

__version__ = "0.1.0"
__author__ = "Anurag Chatterjee"
__email__ = "anurag@versionone.health"
__license__ = "Apache-2.0"
__url__ = "https://github.com/versionone-health/healtheval"

__all__ = [
    "load_failure_mode",
    "load_all_failure_modes",
    "load_by_category",
    "list_failure_modes",
    "run_deterministic_check",
    "run_llm_eval",
    "run_eval",
    "EvalResult",
    "EvalVerdict",
    "Severity",
    "AgentCategory",
    "FailureMode",
    "DeterministicResult",
    "LLMEvalResult",
]
