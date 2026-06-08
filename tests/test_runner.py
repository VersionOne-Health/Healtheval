import pytest
from unittest.mock import patch, MagicMock
from healtheval.runner import run_eval, _parse_verdict
from healtheval.models import EvalVerdict


class TestParseVerdict:
    def test_fail_at_start(self):
        assert _parse_verdict("FAIL — hallucinated a CPT code.") == EvalVerdict.FAIL

    def test_pass_at_start(self):
        assert _parse_verdict("PASS — all codes valid.") == EvalVerdict.PASS

    def test_uncertain(self):
        assert _parse_verdict("UNCERTAIN — insufficient context.") == EvalVerdict.UNCERTAIN

    def test_default_uncertain(self):
        assert _parse_verdict("This is ambiguous.") == EvalVerdict.UNCERTAIN


class TestRunEvalDeterministicOnly:
    def test_scribe_001_fail(self):
        result = run_eval("SCRIBE-001", run_llm=False, context="Metformin was discontinued on 2024-11-14.", agent_output="Patient is currently on metformin 500mg twice daily.")
        assert result.failed
        assert result.final_verdict == EvalVerdict.FAIL
        assert result.llm_result is None

    def test_rcm_invalid_cpt(self):
        result = run_eval("RCM-001", run_llm=False, agent_output="Codes: 99215, 99999")
        assert result.failed

    def test_refill_schedule_ii(self):
        result = run_eval("REFILL-002", run_llm=False, medication_name="Adderall XR 20mg", dea_schedule="II", agent_output="Your refill is approved.")
        assert result.failed

    def test_result_has_metadata(self):
        result = run_eval("FAXROUTE-001", run_llm=False, fax_metadata="Attn: Dr. Johnson", provider_list="Dr. Marcus Johnson\nDr. Patricia Johnson", agent_output="Routed to Dr. Patricia Johnson.")
        assert result.failure_mode_id == "FAXROUTE-001"
        assert result.failure_mode_name == "Provider Identity Mismatch"
        d = result.to_dict()
        assert d["failure_mode_id"] == "FAXROUTE-001"
        assert isinstance(d["passed"], bool)

    def test_no_api_key_skips_llm(self):
        import os
        backup = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            result = run_eval("RCM-001", run_llm=True, agent_output="Codes: 99215, 93000")
            assert result is not None
        finally:
            if backup:
                os.environ["ANTHROPIC_API_KEY"] = backup
