from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Evidence(Contract):
    id: str
    incident_id: str
    path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    excerpt: str
    sha256: str

    @model_validator(mode="after")
    def valid_range(self):
        if self.end_line < self.start_line:
            raise ValueError("end_line must not precede start_line")
        return self


class ToolResult(Contract):
    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: list[Evidence] = Field(default_factory=list)
    error: str | None = None


class HypothesisDraft(Contract):
    claim: str = Field(min_length=8, max_length=1200)
    evidence_ids: list[str] = Field(max_length=8)
    next_check: str = Field(max_length=600)


class Findings(Contract):
    summary: str = Field(max_length=1600)
    hypotheses: list[HypothesisDraft] = Field(max_length=4)
    missing_information: list[str] = Field(max_length=6)


class Hypothesis(HypothesisDraft):
    id: str
    status: Literal["proposed", "confirmed", "rejected", "unresolved"] = "proposed"
    reason: str = ""
    check_ids: list[str] = Field(default_factory=list)


class Verdict(Contract):
    hypothesis_id: str
    status: Literal["confirmed", "rejected", "unresolved"]
    reason: str = Field(min_length=8, max_length=1200)
    evidence_ids: list[str] = Field(max_length=8)
    check_ids: list[str] = Field(max_length=6)


class Review(Contract):
    summary: str = Field(max_length=1600)
    verdicts: list[Verdict] = Field(max_length=4)
    needs_more: bool
    request: str = Field(max_length=600)


class Delegation(Contract):
    target: Literal["investigator", "verifier"]
    task: str = Field(min_length=8, max_length=1000)
    hypothesis_ids: list[str] = Field(
        max_length=4,
        description="Copy existing hypothesis IDs from context; use [] when hypotheses is empty. Never invent IDs.",
    )


class Diagnostic(Contract):
    outcome: Literal["supported", "insufficient"]
    summary: str = Field(min_length=10, max_length=2400)
    hypothesis_ids: list[str] = Field(max_length=4)
    evidence_ids: list[str] = Field(max_length=12)
    next_actions: list[str] = Field(min_length=1, max_length=6)
    limitations: list[str] = Field(max_length=8)


class ModelAction(Contract):
    name: str
    arguments: dict[str, Any]
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float = 0
