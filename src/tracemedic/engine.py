import asyncio
import json
import time
import uuid
from typing import Any, TypedDict

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph

from tracemedic.config import Settings
from tracemedic.locking import run_lock
from tracemedic.mcp_client import connect_tools
from tracemedic.models import Delegation, Diagnostic, Findings, Hypothesis, ModelAction, Review
from tracemedic.prompts import DELEGATE, FINDINGS, FINISH, PROMPTS, REVIEW
from tracemedic.provider import Provider, ProviderUnavailable
from tracemedic.store import Store, stable_id


class InvestigationState(TypedDict, total=False):
    run_id: str
    incident: dict[str, Any]
    mode: str
    role: str
    turn: int
    status: str
    config: dict[str, Any]
    delegation: dict[str, Any]
    delegations: list[dict[str, Any]]
    hypotheses: list[dict[str, Any]]
    observations: list[dict[str, Any]]
    checks: list[dict[str, Any]]
    findings: dict[str, Any]
    review: dict[str, Any]
    visited: list[str]
    agent_turns: dict[str, int]
    feedback: str
    errors: int
    diagnostic: dict[str, Any]


class Engine:
    def __init__(self, settings: Settings, provider=None):
        self.settings = settings
        self.store = Store(settings.audit_db)
        self.provider = provider or Provider(settings)

    def create(self, incident_id, mode="multi", run_id=None):
        if mode not in ("multi", "single"):
            raise ValueError("Unknown orchestration mode")
        catalog = json.loads((self.settings.root / "corpus" / "catalog.json").read_text())
        incident = next((c for c in catalog if c["id"] == incident_id), None)
        if not incident:
            raise ValueError("Unknown incident")
        run_id = run_id or str(uuid.uuid4())
        self.store.create(run_id, incident_id, mode, self.settings.provider, self.settings.model)
        state: InvestigationState = {
            "run_id": run_id,
            "incident": incident,
            "mode": mode,
            "role": "coordinator" if mode == "multi" else "single",
            "turn": 0,
            "status": "running",
            "config": self.settings.model_dump(
                mode="json", exclude={"api_key", "root", "data_dir"}
            ),
            "delegations": [],
            "hypotheses": [],
            "observations": [],
            "checks": [],
            "visited": [],
            "agent_turns": {},
            "feedback": "",
            "errors": 0,
        }
        self.store.update(run_id, state=state)
        return run_id

    def context(self, state, role):
        evidence = self.store.evidence(state["run_id"])
        base = {
            "incident": state["incident"],
            "task": state.get("delegation", {})
            if role != "coordinator"
            else {
                "goal": "Choose the next specialist or final synthesis from the current findings and review. The previous specialist task is complete when findings/review is present."
            },
            "hypotheses": state["hypotheses"],
            "checks": state["checks"],
            "feedback": state["feedback"],
            "role_turns_remaining": (
                self.settings.max_calls if role == "single" else self.settings.max_agent_turns
            )
            - state["agent_turns"].get(role, 0),
            "budget": {
                "model_calls_remaining": self.settings.max_calls
                - self.store.metrics(state["run_id"])["model_calls"],
                "tool_calls_remaining": self.settings.max_tools
                - self.store.metrics(state["run_id"])["tool_calls"],
            },
            "visited": state["visited"],
        }
        if role == "coordinator":
            return {
                **base,
                "findings": state.get("findings"),
                "review": state.get("review"),
                "evidence_index": [
                    {k: v for k, v in e.items() if k != "excerpt"} for e in evidence
                ],
                "past_delegations": state["delegations"],
            }
        return {
            **base,
            "untrusted_evidence": evidence,
            "own_observations": [o for o in state["observations"] if o["role"] == role],
            "review_feedback": state.get("review", {}).get("request", ""),
            "review": state.get("review") if role == "single" else None,
        }

    async def model_action(self, state, role, schemas):
        run, step = state["run_id"], state["turn"]
        key = f"model:{step}:{role}"
        cached = self.store.cached(run, key)
        if cached and cached["status"] == "completed":
            self.store.event(
                run,
                f"model-reuse:{step}",
                role,
                "model_reused",
                "Reused a completed decision after restart",
            )
            return ModelAction.model_validate(json.loads(cached["result"]))
        for attempt in range(3):
            count = self.store.metrics(run)["model_calls"]
            if count >= self.settings.max_calls:
                raise ValueError("Model call budget exhausted")
            attempt_key = f"attempt:{step}:{role}:{count}"
            self.store.event(
                run,
                attempt_key,
                role,
                "model_attempt",
                f"Decision call {count + 1}/{self.settings.max_calls}",
                {"attempt": attempt + 1},
            )
            try:
                action = await self.provider.decide(
                    role, PROMPTS[role], self.context(state, role), schemas
                )
                self.store.event(
                    run,
                    "response:" + attempt_key,
                    role,
                    "model_response",
                    action.name,
                    action.model_dump(),
                )
                self.store.complete(run, key, action.model_dump())
                return action
            except ProviderUnavailable:
                if attempt == 2:
                    raise
                self.store.event(
                    run,
                    "retry:" + attempt_key,
                    role,
                    "retry",
                    "Model unavailable; bounded backoff",
                    {"backoff_seconds": 0.5 * (2**attempt)},
                )
                await asyncio.sleep(0.5 * (2**attempt))
        raise AssertionError("Unreachable")

    def require_evidence(self, run, ids):
        valid = {e["id"] for e in self.store.evidence(run)}
        if not set(ids) <= valid:
            raise ValueError("Unknown evidence ID; cite only captured MCP evidence")

    def control(self, state, role, action):
        name, args, run = action.name, action.arguments, state["run_id"]
        if name == "delegate":
            d = Delegation.model_validate(args)
            if not set(d.hypothesis_ids) <= {h["id"] for h in state["hypotheses"]}:
                raise ValueError("Delegation references unknown hypothesis")
            if d.target == "verifier" and "investigator" not in state["visited"]:
                raise ValueError("Collect evidence with investigator first")
            if state["agent_turns"].get(d.target, 0) >= self.settings.max_agent_turns:
                raise ValueError(
                    "Specialist turn budget exhausted; finish with explicit limitations"
                )
            state.update(
                role=d.target,
                delegation=d.model_dump(),
                delegations=[*state["delegations"], d.model_dump()],
            )
            self.store.event(
                run, f"delegate:{state['turn']}", role, "delegation", d.task, d.model_dump()
            )
        elif name == "submit_findings":
            findings = Findings.model_validate(args)
            hypotheses = []
            for draft in findings.hypotheses:
                self.require_evidence(run, draft.evidence_ids)
                if not draft.evidence_ids:
                    raise ValueError("A hypothesis must cite captured evidence")
                hypotheses.append(
                    Hypothesis(id="h-" + stable_id(draft.claim), **draft.model_dump()).model_dump()
                )
            # Preserve earlier reviewed hypotheses and do not silently upgrade a proposal.
            merged = {h["id"]: h for h in state["hypotheses"]}
            for h in hypotheses:
                merged.setdefault(h["id"], h)
            state.update(
                findings=findings.model_dump(),
                hypotheses=list(merged.values()),
                role="single" if role == "single" else "coordinator",
            )
            self.store.event(
                run,
                f"findings:{state['turn']}",
                role,
                "findings",
                findings.summary,
                {"hypotheses": hypotheses, "missing_information": findings.missing_information},
            )
        elif name == "submit_review":
            review = Review.model_validate(args)
            known = {h["id"]: dict(h) for h in state["hypotheses"]}
            valid_checks = {
                c["check_id"]
                for c in state["checks"]
                if c.get("status") in ("reproduced", "passed")
            }
            for verdict in review.verdicts:
                if verdict.hypothesis_id not in known:
                    raise ValueError("Review references an unknown hypothesis")
                self.require_evidence(run, verdict.evidence_ids)
                if not set(verdict.check_ids) <= {c["check_id"] for c in state["checks"]}:
                    raise ValueError("Unknown check ID")
                if verdict.status == "confirmed" and (
                    not verdict.evidence_ids or not set(verdict.check_ids) & valid_checks
                ):
                    raise ValueError(
                        "Confirmation needs source evidence and an executed independent check"
                    )
                known[verdict.hypothesis_id].update(
                    status=verdict.status,
                    reason=verdict.reason,
                    evidence_ids=verdict.evidence_ids,
                    check_ids=verdict.check_ids,
                )
            state.update(
                review=review.model_dump(),
                hypotheses=list(known.values()),
                role="single" if role == "single" else "coordinator",
            )
            self.store.event(
                run, f"review:{state['turn']}", role, "review", review.summary, review.model_dump()
            )
        elif name == "finish":
            diagnostic = Diagnostic.model_validate(args)
            self.require_evidence(run, diagnostic.evidence_ids)
            selected = [h for h in state["hypotheses"] if h["id"] in diagnostic.hypothesis_ids]
            if len(selected) != len(set(diagnostic.hypothesis_ids)):
                raise ValueError("Diagnostic references unknown hypotheses")
            if state["mode"] == "multi" and not {"investigator", "verifier"} <= set(
                state["visited"]
            ):
                raise ValueError("Consult both specialists before finishing")
            if diagnostic.outcome == "supported" and (
                not any(h["status"] == "confirmed" for h in selected) or not diagnostic.evidence_ids
            ):
                raise ValueError(
                    "Supported diagnostic requires a confirmed hypothesis and evidence"
                )
            if diagnostic.outcome == "insufficient" and any(
                h["status"] == "confirmed" for h in selected
            ):
                raise ValueError("An insufficient diagnostic cannot select a confirmed cause")
            state.update(diagnostic=diagnostic.model_dump(), status="completed", role="end")
            self.store.event(
                run,
                f"diagnostic:{state['turn']}",
                role,
                "diagnostic",
                diagnostic.summary,
                diagnostic.model_dump(),
            )
        else:
            raise ValueError(f"Action not allowed in this role: {name}")

    def stopped(self, state, status, reason):
        state.update(
            status=status,
            role="end",
            diagnostic={
                "outcome": "insufficient",
                "summary": reason,
                "hypothesis_ids": [],
                "evidence_ids": [],
                "next_actions": [
                    "Inspect the audit trail and resolve the reported limit or error before starting a new investigation."
                ],
                "limitations": [
                    reason,
                    "This is a controlled system termination, not a successful LLM diagnosis.",
                ],
            },
        )
        self.store.event(state["run_id"], f"stop:{state['turn']}", "system", status, reason)
        return state

    async def node(self, incoming, role, tools):
        # Copy mutable channels: failed validation must not partially mutate a checkpoint.
        state = json.loads(json.dumps(incoming))
        state["status"] = "running"
        run = state["run_id"]
        metrics = self.store.metrics(run)
        if (
            metrics["model_calls"] >= self.settings.max_calls
            or state["turn"] >= self.settings.max_steps
        ):
            return self.stopped(
                state,
                "budget_exhausted",
                "Investigation reached its configured call/step budget; cause is not established.",
            )
        if state["agent_turns"].get(role, 0) >= (
            self.settings.max_calls if role == "single" else self.settings.max_agent_turns
        ):
            return self.stopped(
                state, "budget_exhausted", f"{role} reached its configured turn budget."
            )
        state["visited"] = list(dict.fromkeys([*state["visited"], role]))
        controls = {
            "coordinator": [DELEGATE, FINISH],
            "investigator": [FINDINGS],
            "verifier": [REVIEW],
            "single": [FINDINGS, REVIEW, FINISH],
        }[role]
        schemas = controls if role == "coordinator" else [*tools.schemas, *controls]
        schemas = json.loads(json.dumps(schemas))
        if role == "investigator":
            schemas = [s for s in schemas if s["function"]["name"] != "run_check"]
        if role == "verifier":
            schemas = [
                s for s in schemas if s["function"]["name"] not in {"list_files", "search_trace"}
            ]
        if role == "single":
            if not state.get("findings") and state["agent_turns"].get(role, 0) >= 6:
                schemas = [s for s in schemas if s["function"]["name"] == "submit_findings"]
            elif state.get("findings"):
                next_action = (
                    "run_check"
                    if not state["checks"]
                    else "submit_review"
                    if not state.get("review")
                    else "finish"
                )
                schemas = [s for s in schemas if s["function"]["name"] == next_action]
        if role == "coordinator" and not state.get("review"):
            for schema in schemas:
                if schema["function"]["name"] == "delegate":
                    target = "verifier" if state.get("findings") else "investigator"
                    schema["function"]["parameters"]["properties"]["target"]["enum"] = [target]
        if (
            role == "coordinator"
            and state.get("review")
            and metrics["model_calls"] >= self.settings.max_calls - 5
        ):
            schemas = [s for s in schemas if s["function"]["name"] == "finish"]
        completed_tools = {o["tool"] for o in state["observations"] if o["result"]["ok"]}
        schemas = [
            s
            for s in schemas
            if s["function"]["name"]
            not in completed_tools & {"list_files", "get_test_report", "run_check"}
        ]
        # Reserve calls for review/synthesis; the model still decides the findings
        # and can request another targeted round through its review.
        if role == "investigator" and (
            state["agent_turns"].get(role, 0) >= 6
            or metrics["model_calls"] >= self.settings.max_calls - 5
        ):
            schemas = [s for s in schemas if s["function"]["name"] == "submit_findings"]
        if role == "verifier" and state["agent_turns"].get(role, 0) >= 3:
            schemas = [s for s in schemas if s["function"]["name"] == "submit_review"]
        read_paths = {e["path"] for e in self.store.evidence(run) if e["start_line"] == 1}
        unread = [
            p
            for p in ("runtime.log", "service.py", "settings.json", "input.json", "report.json")
            if p not in read_paths
        ]
        for schema in schemas:
            if schema["function"]["name"] == "read_file":
                properties = schema["function"]["parameters"]["properties"]
                properties["path"]["enum"] = unread or sorted(read_paths)
                properties["start_line"]["minimum"] = 1
                properties["end_line"]["minimum"] = 1
        valid_ids = {
            "evidence_ids": [e["id"] for e in self.store.evidence(run)],
            "hypothesis_ids": [h["id"] for h in state["hypotheses"]],
            "check_ids": [c["check_id"] for c in state["checks"]],
        }

        def constrain(value):
            if isinstance(value, dict):
                properties = value.get("properties", {})
                for field, ids in valid_ids.items():
                    if field in properties:
                        properties[field]["description"] = (
                            "Copy only these existing IDs: " + repr(ids) + ". Use [] if none."
                        )
                        if ids:
                            properties[field]["items"] = {"type": "string", "enum": ids}
                        else:
                            properties[field]["maxItems"] = 0
                if "hypothesis_id" in properties and valid_ids["hypothesis_ids"]:
                    properties["hypothesis_id"]["enum"] = valid_ids["hypothesis_ids"]
                for child in value.values():
                    constrain(child)
            elif isinstance(value, list):
                for child in value:
                    constrain(child)

        constrain(schemas)
        try:
            action = await self.model_action(state, role, schemas)
            allowed = {t["function"]["name"] for t in schemas}
            if action.name not in allowed:
                raise ValueError(f"Unavailable action: {action.name}")
            if action.name in {t["function"]["name"] for t in tools.schemas}:
                output = await tools.call(action.name, action.arguments, role, state["turn"])
                state["observations"].append(
                    {
                        "role": role,
                        "tool": action.name,
                        "arguments": action.arguments,
                        "result": output.model_dump(),
                    }
                )
                if action.name == "run_check" and output.ok and "check_id" in output.data:
                    if output.data["check_id"] not in {c["check_id"] for c in state["checks"]}:
                        state["checks"].append(output.data)
            else:
                self.control(state, role, action)
            state["feedback"] = ""
            state["errors"] = 0
        except ProviderUnavailable as exc:
            state.update(status="error", feedback=str(exc))
            self.store.event(
                run, f"provider-error:{state['turn']}", role, "error", str(exc), {"resumable": True}
            )
        except Exception as exc:
            state["errors"] += 1
            state["feedback"] = f"Action rejected: {str(exc)[:1000]}"
            self.store.event(
                run,
                f"validation:{state['turn']}",
                role,
                "action_rejected",
                state["feedback"],
                {"type": type(exc).__name__},
            )
            if state["errors"] >= 3:
                self.stopped(
                    state,
                    "failed",
                    "Three consecutive invalid agent/tool actions; inspect audit events.",
                )
        state["turn"] += 1
        state["agent_turns"][role] = state["agent_turns"].get(role, 0) + 1
        return state

    def graph(self, saver, tools):
        graph = StateGraph(InvestigationState)
        routes = {r: r for r in ("coordinator", "investigator", "verifier", "single")}
        routes["end"] = END
        for role in routes:
            if role == "end":
                continue

            async def step(state, current_role=role):
                return await self.node(state, current_role, tools)

            graph.add_node(role, step)
            graph.add_conditional_edges(role, lambda state: state["role"], routes)
        graph.add_conditional_edges(START, lambda state: state["role"], routes)
        return graph.compile(checkpointer=saver)

    async def run(self, run_id, pause_after=None, step_delay=0):
        with run_lock(self.settings.data_dir / "locks" / (run_id + ".lock")):
            return await self._run(run_id, pause_after, step_delay)

    async def _run(self, run_id, pause_after, step_delay):
        record = self.store.run(run_id)
        if record["status"] in ("completed", "budget_exhausted", "failed"):
            return record
        # Limits and provider identity remain those of the original run. Credentials are never checkpointed.
        saved = record["state"]["config"]
        self.settings = self.settings.model_copy(update=saved)
        if type(self.provider) is Provider:
            self.provider = Provider(self.settings)
        self.store.update(run_id, status="running", cancel=False)
        if record["status"] != "queued":
            self.store.event(
                run_id,
                f"resume:{len(self.store.events(run_id))}",
                "system",
                "resumed",
                "Resumed durable checkpoint with saved evidence and operation keys",
            )
        started = time.perf_counter()
        steps = 0
        try:
            async with connect_tools(
                self.settings, self.store, run_id, record["incident_id"]
            ) as tools:
                async with AsyncSqliteSaver.from_conn_string(
                    str(self.settings.checkpoint_db)
                ) as saver:
                    graph = self.graph(saver, tools)
                    config = {
                        "configurable": {"thread_id": run_id},
                        "recursion_limit": self.settings.max_steps + 10,
                    }
                    snapshot = await graph.aget_state(config)
                    argument = None if snapshot.values else record["state"]
                    while True:
                        result = await graph.ainvoke(
                            argument,
                            config,
                            interrupt_after=["coordinator", "investigator", "verifier", "single"],
                            durability="sync",
                        )
                        argument = None
                        steps += 1
                        self.store.update(run_id, status=result["status"], state=result)
                        if result["role"] == "end" or result["status"] == "error":
                            break
                        if self.store.run(run_id)["cancel_requested"]:
                            self.store.update(run_id, status="cancelled")
                            self.store.event(
                                run_id,
                                f"cancelled:{result['turn']}",
                                "system",
                                "cancelled",
                                "Cancelled at a durable action boundary; resume is available",
                            )
                            break
                        if pause_after and steps >= pause_after:
                            self.store.update(run_id, status="interrupted")
                            self.store.event(
                                run_id,
                                f"paused:{result['turn']}",
                                "system",
                                "interrupted",
                                "Paused at a durable action boundary",
                            )
                            break
                        if step_delay:
                            await asyncio.sleep(step_delay)
        except asyncio.CancelledError:
            self.store.update(run_id, status="interrupted")
            raise
        except Exception as exc:
            self.store.update(run_id, status="error")
            self.store.event(
                run_id,
                f"runtime-error:{len(self.store.events(run_id))}",
                "system",
                "error",
                f"{type(exc).__name__}: {str(exc)[:800]}",
                {"resumable": True},
            )
        finally:
            self.store.event(
                run_id,
                f"session:{len(self.store.events(run_id))}",
                "system",
                "session_end",
                "Runner session ended",
                {"elapsed_ms": round((time.perf_counter() - started) * 1000, 1)},
            )
        return self.store.run(run_id)
