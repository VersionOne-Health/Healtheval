import pytest
from healtheval import load_failure_mode, load_all_failure_modes, load_by_category, list_failure_modes
from healtheval.models import AgentCategory, Severity


def test_load_all_returns_10_modes():
    modes = load_all_failure_modes()
    assert len(modes) == 10, f"Expected 10 failure modes, got {len(modes)}: {[m.id for m in modes]}"

def test_all_mode_ids_unique():
    modes = load_all_failure_modes()
    ids = [m.id for m in modes]
    assert len(ids) == len(set(ids)), f"Duplicate IDs: {ids}"

def test_load_failure_mode_scribe_001():
    fm = load_failure_mode("SCRIBE-001")
    assert fm.id == "SCRIBE-001"
    assert fm.category == AgentCategory.SCRIBE
    assert fm.severity == Severity.CRITICAL
    assert len(fm.eval_prompt) > 50

def test_load_failure_mode_not_found():
    with pytest.raises(ValueError, match="not found"):
        load_failure_mode("INVALID-999")

def test_load_by_category_scribe():
    modes = load_by_category("scribe")
    assert len(modes) == 4
    assert all(m.category == AgentCategory.SCRIBE for m in modes)

def test_load_by_category_rcm():
    modes = load_by_category("rcm")
    assert len(modes) == 2

def test_load_by_category_refill():
    modes = load_by_category("refill")
    assert len(modes) == 2

def test_load_by_category_fax_routing():
    modes = load_by_category("fax_routing")
    assert len(modes) == 1
    assert modes[0].id == "FAXROUTE-001"

def test_load_by_category_prior_auth():
    modes = load_by_category("prior_auth")
    assert len(modes) == 1
    assert modes[0].id == "PRIORAUTH-001"

def test_list_failure_modes():
    listing = list_failure_modes()
    assert len(listing) == 10
    for item in listing:
        assert "id" in item and "name" in item and "category" in item and "severity" in item

def test_all_failure_modes_have_required_fields():
    for mode in load_all_failure_modes():
        assert mode.id
        assert mode.name
        assert mode.description
        assert mode.eval_prompt
        assert mode.severity in Severity
        assert mode.category in AgentCategory
        assert isinstance(mode.specialties, list)
        assert len(mode.specialties) > 0
