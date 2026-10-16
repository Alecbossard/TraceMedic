from typing import Annotated, Literal

from pydantic import Field

from tracemedic.models import Contract


class Citation(Contract):
    line_ref: str = Field(
        pattern=r"^E[1-9][0-9]*:L[1-9][0-9]*$",
        description="Copy an existing source line handle, e.g. E2:L3. The host attaches its exact text; do not supply a quote yourself.",
    )


class Cause(Contract):
    trigger: str = Field(
        min_length=8,
        max_length=300,
        description="Concrete captured condition/input, no assumed deployment history",
    )
    mechanism: str = Field(
        min_length=12,
        max_length=500,
        description="Explain how the source transforms the condition into failure, beyond repeating the error",
    )
    effect: str = Field(
        min_length=8, max_length=300, description="Observed failure or incorrect result"
    )
    citations: list[Citation] = Field(
        min_length=2,
        max_length=4,
        description="At least one service.py line AND one line from a different captured file showing condition or effect",
    )
    next_check: str = Field(max_length=240)


class Findings(Contract):
    hypotheses: list[Cause] = Field(
        max_length=1,
        description="One focused causal record, or [] when no defensible mechanism can be proposed",
    )
    unknowns: list[str] = Field(max_length=4)


class Verdict(Contract):
    hypothesis_id: str = Field(description="Existing short hypothesis alias, e.g. H1")
    status: Literal["confirmed", "rejected", "unresolved"]
    reason: str = Field(min_length=8, max_length=500)
    check_ids: list[str] = Field(
        max_length=3, description="Existing short executed check aliases, e.g. C1"
    )


class Review(Contract):
    verdicts: list[Verdict] = Field(max_length=4)
    needs_more: bool
    request: str = Field(max_length=300)


class Finish(Contract):
    outcome: Literal["supported", "insufficient"]
    hypothesis_ids: list[str] = Field(max_length=2)
    next_actions: list[Annotated[str, Field(min_length=12, max_length=400)]] = Field(
        min_length=1,
        max_length=4,
        description="Proposed actions, not assertions of a fix or additional causes",
    )
