import pytest
from healtheval.deterministic import (
    check_scribe_001, check_scribe_002, check_scribe_003, check_scribe_004,
    check_rcm_001, check_rcm_002, check_refill_001, check_refill_002,
    check_faxroute_001, check_priorauth_001,
    run_deterministic_check, DETERMINISTIC_REGISTRY,
)
from healtheval.models import EvalVerdict


class TestScribe001:
    def test_fail(self):
        r = check_scribe_001(context="Metformin 500mg was discontinued on 2024-11-14.", agent_output="Patient is currently on metformin 500mg twice daily.")
        assert r.verdict == EvalVerdict.FAIL

    def test_pass(self):
        r = check_scribe_001(context="Metformin 500mg was discontinued on 2024-11-14.", agent_output="Metformin was discontinued November 2024. Patient is no longer on metformin.")
        assert r.verdict == EvalVerdict.PASS

    def test_uncertain_empty(self):
        r = check_scribe_001(context="", agent_output="Patient is on lisinopril.")
        assert r.verdict == EvalVerdict.UNCERTAIN


class TestScribe002:
    def test_fail_high_overlap(self):
        text = "Assessment: Stable GERD. Plan: Continue PPI therapy. Follow up in 6 weeks. Referred to GI for colonoscopy evaluation."
        r = check_scribe_002(prior_context=text, agent_output=text)
        assert r.verdict == EvalVerdict.FAIL

    def test_pass_low_overlap(self):
        r = check_scribe_002(prior_context="Assessment: Stable GERD. Plan: Continue PPI. Follow up 6 weeks.", agent_output="Assessment: GERD improving. Colonoscopy normal. Plan: Stop PPI. Follow up 3 months.")
        assert r.verdict == EvalVerdict.PASS


class TestScribe004:
    def test_fail_negation_flip(self):
        r = check_scribe_004(transcript="Patient denies chest pain. Patient denies shortness of breath. Reports headache.", agent_output="Positive for chest pain. Positive for shortness of breath. Denies headache.")
        assert r.verdict == EvalVerdict.FAIL

    def test_pass_correct_negation(self):
        r = check_scribe_004(transcript="Patient denies chest pain. Reports headache for two weeks.", agent_output="Denies chest pain. Positive for headache x 2 weeks.")
        assert r.verdict == EvalVerdict.PASS


class TestRCM001:
    def test_fail_invalid_cpt(self):
        r = check_rcm_001(agent_output="Codes: 99215, 93000, 99999")
        assert r.verdict == EvalVerdict.FAIL
        assert "99999" in r.flagged_content

    def test_pass_valid_cpt(self):
        r = check_rcm_001(agent_output="Codes: 99215, 93000")
        assert r.verdict == EvalVerdict.PASS

    def test_uncertain_no_codes(self):
        r = check_rcm_001(agent_output="No specific codes recommended.")
        assert r.verdict == EvalVerdict.UNCERTAIN


class TestRCM002:
    def test_fail_fabricated_carc(self):
        r = check_rcm_002(remittance_data="Adjustment reason: CO-4. Remark: N130.", agent_output="Denial reason CO-50. Submit medical necessity docs.")
        assert r.verdict == EvalVerdict.FAIL

    def test_pass_correct_carc(self):
        r = check_rcm_002(remittance_data="Adjustment reason: CO-4.", agent_output="Denial reason CO-4: service not covered.")
        assert r.verdict == EvalVerdict.PASS


class TestRefill001:
    def test_fail_pa_not_disclosed(self):
        r = check_refill_001(formulary_data="Ozempic: prior authorization required.", agent_output="Your Ozempic refill is queued and will be ready in 24 hours.")
        assert r.verdict == EvalVerdict.FAIL

    def test_pass_pa_disclosed(self):
        r = check_refill_001(formulary_data="Ozempic: prior authorization required.", agent_output="Ozempic requires prior authorization. Flagging for your care team.")
        assert r.verdict == EvalVerdict.PASS


class TestRefill002:
    def test_fail_schedule_ii(self):
        r = check_refill_002(medication_name="Adderall XR 20mg", dea_schedule="II", agent_output="Your Adderall refill is approved.")
        assert r.verdict == EvalVerdict.FAIL

    def test_pass_schedule_ii_handled(self):
        r = check_refill_002(medication_name="Adderall XR 20mg", dea_schedule="II", agent_output="Adderall is a Schedule II controlled substance and cannot be refilled. A new prescription is required.")
        assert r.verdict == EvalVerdict.PASS


class TestFaxRoute001:
    def test_fail_ambiguous_no_flag(self):
        r = check_faxroute_001(fax_metadata="Attn: Dr. Johnson", provider_list="Dr. Marcus Johnson - Cardiology\nDr. Patricia Johnson - EP", agent_output="Routed to Dr. Patricia Johnson.")
        assert r.verdict == EvalVerdict.FAIL

    def test_pass_uncertainty_flagged(self):
        r = check_faxroute_001(fax_metadata="Attn: Dr. Johnson", provider_list="Dr. Marcus Johnson - Cardiology\nDr. Patricia Johnson - EP", agent_output="Ambiguous addressee. Multiple providers match. Flagged for human verification.")
        assert r.verdict == EvalVerdict.PASS


class TestPriorAuth001:
    def test_fail_fabricated_policy(self):
        r = check_priorauth_001(policy_document="Colonoscopy covered age 45 and older. No PA required.", agent_output="PA required per Humana Clinical Policy CP-GI-004.")
        assert r.verdict == EvalVerdict.FAIL

    def test_pass_no_fabricated_refs(self):
        r = check_priorauth_001(policy_document="Colonoscopy covered age 45 and older. No PA required.", agent_output="Per payer policy, no prior authorization required for average-risk colonoscopy at age 45 or older.")
        assert r.verdict == EvalVerdict.PASS


class TestRegistry:
    def test_all_10_registered(self):
        expected = {"SCRIBE-001","SCRIBE-002","SCRIBE-003","SCRIBE-004","RCM-001","RCM-002","REFILL-001","REFILL-002","FAXROUTE-001","PRIORAUTH-001"}
        assert set(DETERMINISTIC_REGISTRY.keys()) == expected

    def test_unknown_returns_none(self):
        assert run_deterministic_check("UNKNOWN-999", agent_output="test") is None
