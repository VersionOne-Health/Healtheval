from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvalVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNCERTAIN = "UNCERTAIN"
    ERROR = "ERROR"


class AgentCategory(str, Enum):
    SCRIBE = "scribe"
    RCM = "rcm"
    REFILL = "refill"
    FAX_ROUTING = "fax_routing"
    PRIOR_AUTH = "prior_auth"


@dataclass
class FailureMode:
    id: str
    category: AgentCategory
    name: str
    description: str
    severity: Severity
    specialties: List[str]
    triggers: List[str]
    example_context: str
    example_bad_output: str
    example_good_output: str
    what_went_wrong: str
    eval_prompt: str
    deterministic_check: str
    references: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailureMode":
        return cls(
            id=data["id"],
            category=AgentCategory(data["category"]),
            name=data["name"],
            description=data["description"],
            severity=Severity(data["severity"]),
            specialties=data.get("specialties", ["general"]),
            triggers=data.get("triggers", []),
            example_context=data.get("example_context", ""),
            example_bad_output=data.get("example_bad_output", ""),
            example_good_output=data.get("example_good_output", ""),
            what_went_wrong=data.get("what_went_wrong", ""),
            eval_prompt=data.get("eval_prompt", ""),
            deterministic_check=data.get("deterministic_check", ""),
            references=data.get("references", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "name": self.name,
            "severity": self.severity.value,
            "specialties": self.specialties,
            "description": self.description,
        }


@dataclass
class DeterministicResult:
    verdict: EvalVerdict
    reason: str
    flagged_content: Optional[str] = None


@dataclass
class LLMEvalResult:
    verdict: EvalVerdict
    explanation: str
    model_used: str
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class EvalResult:
    failure_mode_id: str
    failure_mode_name: str
    severity: Severity
    category: AgentCategory
    deterministic_result: Optional[DeterministicResult] = None
    llm_result: Optional[LLMEvalResult] = None
    final_verdict: EvalVerdict = field(init=False)

    def __post_init__(self):
        if self.deterministic_result and self.deterministic_result.verdict == EvalVerdict.FAIL:
            self.final_verdict = EvalVerdict.FAIL
        elif self.llm_result:
            self.final_verdict = self.llm_result.verdict
        elif self.deterministic_result:
            self.final_verdict = self.deterministic_result.verdict
        else:
            self.final_verdict = EvalVerdict.UNCERTAIN

    @property
    def passed(self) -> bool:
        return self.final_verdict == EvalVerdict.PASS

    @property
    def failed(self) -> bool:
        return self.final_verdict == EvalVerdict.FAIL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_mode_id": self.failure_mode_id,
            "failure_mode_name": self.failure_mode_name,
            "severity": self.severity.value,
            "category": self.category.value,
            "final_verdict": self.final_verdict.value,
            "passed": self.passed,
            "deterministic": {
                "verdict": self.deterministic_result.verdict.value,
                "reason": self.deterministic_result.reason,
                "flagged_content": self.deterministic_result.flagged_content,
            } if self.deterministic_result else None,
            "llm": {
                "verdict": self.llm_result.verdict.value,
                "explanation": self.llm_result.explanation,
                "model": self.llm_result.model_used,
                "total_tokens": self.llm_result.total_tokens,
            } if self.llm_result else None,
        }
