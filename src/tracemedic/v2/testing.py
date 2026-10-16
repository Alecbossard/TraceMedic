"""Explicit test double for case-01 only. Never a fallback for real inference."""

from tracemedic.models import ModelAction


class ScriptedProvider:
    async def decide(self, role, system, context, tools):
        names = {s["function"]["name"] for s in tools}
        if "delegate" in names:
            target = "verifier" if context["hypotheses"] else "investigator"
            return ModelAction(
                name="delegate",
                arguments={
                    "target": target,
                    "task": "Review captured port values and source; distinguish the mechanism from the symptom.",
                    "hypothesis_ids": [h["id"] for h in context["hypotheses"]],
                },
            )
        if "read_bundle" in names and not context["sources"]:
            return ModelAction(
                name="read_bundle",
                arguments={
                    "paths": [
                        "runtime.log",
                        "service.py",
                        "settings.json",
                        "input.json",
                        "report.json",
                    ]
                },
            )
        if "submit_findings" in names:
            sources = {s["path"]: s for s in context["sources"]}

            def citation(path, text):
                source = sources[path]
                for line in source["untrusted_numbered_text"].splitlines():
                    line_ref, _, content = line.partition(": ")
                    if text in content:
                        return {"line_ref": line_ref}
                raise AssertionError("Expected case-01 source")

            return ModelAction(
                name="submit_findings",
                arguments={
                    "hypotheses": [
                        {
                            "trigger": "The configured port is 6433 while the captured listener uses 5432.",
                            "mechanism": "The source requires the configured port to equal the listening_port, so the port mismatch raises ConnectionRefused.",
                            "effect": "The fixture does not return connected.",
                            "citations": [
                                citation("service.py", 'c["port"] == d["listening_port"]'),
                                citation("settings.json", '"port": 6433'),
                                citation("input.json", '"listening_port": 5432'),
                            ],
                            "next_check": "Run unchanged fixture, then test the listener port.",
                        }
                    ],
                    "unknowns": [],
                },
            )
        if "run_check" in names:
            return ModelAction(name="run_check", arguments={})
        if "run_experiment" in names and len(context["checks"]) == 1:
            return ModelAction(
                name="run_experiment",
                arguments={"changes": [{"path": "/settings/port", "value": 5432}]},
            )
        if "submit_review" in names:
            return ModelAction(
                name="submit_review",
                arguments={
                    "verdicts": [
                        {
                            "hypothesis_id": h["id"],
                            "status": "confirmed",
                            "reason": "Source port equality and captured values explain reproduced failure; isolated port intervention passes.",
                            "check_ids": [c["id"] for c in context["checks"]],
                        }
                        for h in context["hypotheses"]
                    ],
                    "needs_more": False,
                    "request": "",
                },
            )
        return ModelAction(
            name="finish",
            arguments={
                "outcome": "supported",
                "hypothesis_ids": [
                    h["id"] for h in context["hypotheses"] if h["status"] == "confirmed"
                ],
                "next_actions": [
                    "Align the configured port with the actual listener after verifying the deployment."
                ],
            },
        )
