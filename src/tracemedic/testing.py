"""Explicit deterministic test double. NEVER presented as an LLM investigation."""

from tracemedic.models import ModelAction


class ScriptedProvider:
    async def decide(self, role, system, context, tools):
        evidence = context.get("untrusted_evidence", []) or context.get("evidence_index", [])
        ids = [e["id"] for e in evidence]
        h = context["hypotheses"]
        check = context["checks"]

        def action(name, **arguments):
            return ModelAction(
                name=name, arguments=arguments, input_tokens=None, output_tokens=None
            )

        if role == "coordinator":
            if not context.get("findings"):
                return action(
                    "delegate",
                    target="investigator",
                    task="Inspect the incident source and configuration for the connection failure",
                    hypothesis_ids=[],
                )
            if not context.get("review"):
                return action(
                    "delegate",
                    target="verifier",
                    task="Check the proposed port mismatch against an executed fixture",
                    hypothesis_ids=[x["id"] for x in h],
                )
        if role in ("investigator", "single") and not h:
            seen = {e["path"] for e in evidence}
            for path in ("runtime.log", "service.py", "settings.json", "input.json", "report.json"):
                if path not in seen:
                    return action("read_file", path=path)
            return action(
                "submit_findings",
                summary="TEST DOUBLE: configured port differs from listener",
                hypotheses=[
                    {
                        "claim": "Configured port 6433 differs from listening port 5432, causing a connection refusal.",
                        "evidence_ids": ids,
                        "next_check": "Run the immutable fixture",
                    }
                ],
                missing_information=[],
            )
        if role in ("verifier", "single") and not context.get("review"):
            if not check:
                return action("run_check")
            return action(
                "submit_review",
                summary="TEST DOUBLE: fixture reproduces configured port mismatch",
                verdicts=[
                    {
                        "hypothesis_id": h[0]["id"],
                        "status": "confirmed",
                        "reason": "Configured 6433 and observed listener 5432 differ; the fixture independently reproduced the refusal.",
                        "evidence_ids": ids or h[0]["evidence_ids"],
                        "check_ids": [check[0]["check_id"]],
                    }
                ],
                needs_more=False,
                request="",
            )
        return action(
            "finish",
            outcome="supported",
            summary="TEST DOUBLE: configured port 6433 differs from the listening port 5432.",
            hypothesis_ids=[h[0]["id"]],
            evidence_ids=h[0]["evidence_ids"],
            next_actions=[
                "Align the configured port with the intended listener, then rerun the test."
            ],
            limitations=["Deterministic test double; no LLM was called."],
        )
