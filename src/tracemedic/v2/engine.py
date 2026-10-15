"""Evidence-constrained V2. The original V1 runner/prompts remain untouched."""

import asyncio
import json
import time
import uuid

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph

from tracemedic.engine import Engine as V1Engine
from tracemedic.engine import InvestigationState
from tracemedic.mcp_client import connect_tools
from tracemedic.models import Delegation, ModelAction
from tracemedic.provider import ProviderUnavailable
from tracemedic.store import stable_id
from tracemedic.v2 import prompts
from tracemedic.v2.contracts import Findings, Finish, Review
from tracemedic.v2.provider import Provider


class V2State(InvestigationState, total=False):
    engine_version: str
    evidence_aliases: dict[str, str]
    findings_turn: int
    review_turn: int
    round: int
    round_tools: int


class Engine(V1Engine):
    def __init__(self, settings, provider=None):
        super().__init__(settings, provider or Provider(settings))

    def create(self, incident_id, mode="multi", run_id=None):
        if mode not in ("multi", "single"):
            raise ValueError("Unknown orchestration mode")
        path = self.settings.root / "corpus" / "v2_catalog.json"
        if not path.exists():
            path = self.settings.root / "corpus" / "catalog.json"
        incident = next((c for c in json.loads(path.read_text()) if c["id"] == incident_id), None)
        if not incident:
            raise ValueError("Unknown incident")
        run_id = run_id or str(uuid.uuid4())
        self.store.create(run_id, incident_id, mode, self.settings.provider, self.settings.model)
        state: V2State = {
            "run_id": run_id,
            "incident": incident,
            "mode": mode,
            "role": "coordinator" if mode == "multi" else "single",
            "turn": 0,
            "status": "running",
            "engine_version": "v2",
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
            "evidence_aliases": {},
            "findings_turn": -1,
            "review_turn": -1,
            "round": 0,
            "round_tools": 0,
        }
        self.store.update(run_id, state=state)
        return run_id

    def context(self, state, role):
        evidence = {e["id"]: e for e in self.store.evidence(state["run_id"])}
        reverse = {v: k for k, v in state["evidence_aliases"].items()}
        check_aliases = {c["check_id"]: f"C{i + 1}" for i, c in enumerate(state["checks"])}
        hypotheses = [
            {
                "id": h["alias"],
                "trigger": h["trigger"],
                "mechanism": h["mechanism"],
                "effect": h["effect"],
                "status": h["status"],
                "reason": h["reason"],
                "citations": [
                    {"line_ref": f"{reverse[q['evidence_id']]}:L{q['line']}"}
                    for q in h["citations"]
                ],
                "check_ids": [check_aliases[c] for c in h["check_ids"]],
            }
            for h in state["hypotheses"]
        ]
        sources = [
            {
                "id": alias,
                "path": evidence[key]["path"],
                "lines": f"{evidence[key]['start_line']}-{evidence[key]['end_line']}",
                **(
                    {
                        "untrusted_numbered_text": "\n".join(
                            f"{alias}:L{i}: {line}"
                            for i, line in enumerate(
                                evidence[key]["excerpt"].splitlines(), evidence[key]["start_line"]
                            )
                        )
                    }
                    if role != "coordinator"
                    else {}
                ),
            }
            for alias, key in state["evidence_aliases"].items()
            if key in evidence
        ]
        metrics = self.store.metrics(state["run_id"])
        return {
            "incident": state["incident"],
            "task": state.get("delegation")
            if role != "coordinator"
            else "Choose a justified specialist task or finish from the reviewed records.",
            "hypotheses": hypotheses,
            "checks": [
                {
                    **{k: v for k, v in c.items() if k != "check_id"},
                    "id": check_aliases[c["check_id"]],
                }
                for c in state["checks"]
            ],
            "sources": sources,
            "unknowns": state.get("findings", {}).get("unknowns", []),
            "review": state.get("review"),
            "feedback": state["feedback"],
            "recent_actions": state["observations"][-5:] if role != "coordinator" else [],
            "budget": {
                "model_calls_remaining": self.settings.max_calls - metrics["model_calls"],
                "tool_calls_remaining": self.settings.max_tools - metrics["tool_calls"],
            },
            "visited": state["visited"],
            "round": state["round"],
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
                "Reused completed decision after restart",
            )
            return ModelAction.model_validate(json.loads(cached["result"]))
        context = self.context(state, role)
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
                {
                    "attempt": attempt + 1,
                    "context_chars": len(json.dumps(context)),
                    "decoding": "json_schema_control"
                    if isinstance(self.provider, Provider)
                    and self.provider.structured_control(schemas)
                    else "native_function",
                },
            )
            try:
                action = await self.provider.decide(role, prompts.PROMPTS[role], context, schemas)
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

    def citations(self, state, citations):
        captured = {e["id"]: e for e in self.store.evidence(state["run_id"])}
        result = []
        for citation in citations:
            alias, _, number = citation.line_ref.partition(":L")
            line_number = int(number)
            evidence_id = state["evidence_aliases"].get(alias)
            source = captured.get(evidence_id)
            if not source:
                raise ValueError("Unknown source alias; use captured E aliases")
            if not source["start_line"] <= line_number <= source["end_line"]:
                raise ValueError("Citation line outside captured source range")
            line = source["excerpt"].splitlines()[line_number - source["start_line"]]
            result.append(
                {
                    "evidence_id": evidence_id,
                    "line": line_number,
                    "quote": line[:240],
                    "quote_truncated": len(line) > 240,
                }
            )
        return result

    def control(self, state, role, action):
        run, args = state["run_id"], action.arguments
        known = {h["alias"]: h for h in state["hypotheses"]}
        if action.name == "delegate":
            d = Delegation.model_validate(args)
            if not set(d.hypothesis_ids) <= known.keys():
                raise ValueError("Unknown hypothesis alias")
            if d.target == "verifier" and state["findings_turn"] < 0:
                raise ValueError("Investigator must submit findings first")
            if d.target == "investigator":
                if state["round"] >= 2:
                    raise ValueError("At most two investigation rounds")
                state["round"] += 1
            state.update(
                role=d.target,
                delegation=d.model_dump(),
                round_tools=0,
                delegations=[*state["delegations"], d.model_dump()],
            )
            self.store.event(
                run, f"delegate:{state['turn']}", role, "delegation", d.task, d.model_dump()
            )
        elif action.name == "submit_findings":
            findings = Findings.model_validate(args)
            additions = []
            for cause in findings.hypotheses:
                cited = self.citations(state, cause.citations)
                captured = {e["id"]: e for e in self.store.evidence(run)}
                paths = {captured[q["evidence_id"]]["path"] for q in cited}
                if "service.py" not in paths or len(paths) < 2:
                    raise ValueError(
                        "A causal proposal needs an exact service.py quote AND an exact quote from another file showing its captured condition or effect; two code quotes alone are insufficient. Use [] if unavailable."
                    )
                claim = f"{cause.trigger} {cause.mechanism} {cause.effect}"
                key = "h-" + stable_id(claim)
                if any(h["id"] == key for h in [*state["hypotheses"], *additions]):
                    continue
                additions.append(
                    {
                        **cause.model_dump(exclude={"citations"}),
                        "claim": claim,
                        "id": key,
                        "alias": f"H{len(known) + len(additions) + 1}",
                        "citations": cited,
                        "evidence_ids": list(dict.fromkeys(q["evidence_id"] for q in cited)),
                        "status": "proposed",
                        "reason": "",
                        "check_ids": [],
                        "support_level": "unverified",
                    }
                )
            state.update(
                findings=findings.model_dump(),
                hypotheses=[*state["hypotheses"], *additions],
                findings_turn=state["turn"],
                round_tools=0,
                role="single" if role == "single" else "coordinator",
            )
            self.store.event(
                run,
                f"findings:{state['turn']}",
                role,
                "findings",
                f"{len(additions)} causal proposal(s); {len(findings.unknowns)} unknown(s)",
                {"hypotheses": additions, "unknowns": findings.unknowns},
            )
        elif action.name == "submit_review":
            review = Review.model_validate(args)
            checks = {f"C{i + 1}": c for i, c in enumerate(state["checks"])}
            updates = []
            seen = set()
            evidence = {e["id"]: e for e in self.store.evidence(run)}
            for verdict in review.verdicts:
                if verdict.hypothesis_id not in known or verdict.hypothesis_id in seen:
                    raise ValueError("Unknown or duplicate hypothesis alias in review")
                seen.add(verdict.hypothesis_id)
                if not set(verdict.check_ids) <= checks.keys():
                    raise ValueError("Unknown check alias in review")
                h = dict(known[verdict.hypothesis_id])
                status, reason = verdict.status, verdict.reason
                selected = [checks[c] for c in verdict.check_ids]
                reproduced = any(
                    c.get("kind") != "intervention" and c.get("status") == "reproduced"
                    for c in selected
                )
                paths = {evidence[c]["path"] for c in h["evidence_ids"]}
                sufficient = reproduced and "service.py" in paths and len(paths) >= 2
                if status == "confirmed" and not sufficient:
                    status = "unresolved"
                    reason = (
                        "Confirmation blocked: need a reproduced baseline plus cited source and a second file. "
                        + reason
                    )
                    self.store.event(
                        run,
                        f"blocked:{state['turn']}:{h['id']}",
                        role,
                        "confirmation_blocked",
                        reason,
                        {"hypothesis_id": h["id"]},
                    )
                intervention = any(
                    c.get("kind") == "intervention"
                    and c.get("baseline", {}).get("status") == "reproduced"
                    and c.get("trial", {}).get("status") == "passed"
                    for c in selected
                )
                h.update(
                    status=status,
                    reason=reason,
                    check_ids=[c["check_id"] for c in selected],
                    support_level=("controlled_intervention" if intervention else "reproduction")
                    if status == "confirmed"
                    else "unresolved",
                )
                updates.append(h)
            replacements = {h["id"]: h for h in updates}
            applied_review = review.model_dump()
            for verdict, h in zip(applied_review["verdicts"], updates, strict=True):
                verdict.update(status=h["status"], reason=h["reason"])
            state.update(
                review=applied_review,
                review_turn=state["turn"],
                round_tools=0,
                hypotheses=[replacements.get(h["id"], h) for h in state["hypotheses"]],
                role="single" if role == "single" else "coordinator",
            )
            self.store.event(
                run,
                f"review:{state['turn']}",
                role,
                "review",
                "Causal records reviewed against executed checks",
                {"verdicts": updates, "needs_more": review.needs_more, "request": review.request},
            )
        elif action.name == "finish":
            finish = Finish.model_validate(args)
            if not set(finish.hypothesis_ids) <= known.keys():
                raise ValueError("Unknown hypothesis alias")
            if (
                state["review_turn"] < 0
                or state["review_turn"] < state["findings_turn"]
                or (
                    state["mode"] == "multi"
                    and not {"investigator", "verifier"} <= set(state["visited"])
                )
            ):
                raise ValueError("Review must precede final selection")
            selected = [known[key] for key in dict.fromkeys(finish.hypothesis_ids)]
            if finish.outcome == "supported" and (
                not selected or any(h["status"] != "confirmed" for h in selected)
            ):
                raise ValueError("Supported finish must select only confirmed records")
            if finish.outcome == "insufficient" and selected:
                raise ValueError("Insufficient finish selects no causal record; use []")
            diagnostic = {
                "outcome": finish.outcome,
                "summary": "\n\n".join(h["claim"] for h in selected)
                if selected
                else "The captured evidence and executed checks do not establish a causal mechanism for this incident.",
                "hypothesis_ids": [h["id"] for h in selected],
                "evidence_ids": list(
                    dict.fromkeys(key for h in selected for key in h["evidence_ids"])
                ),
                "next_actions": finish.next_actions,
                "limitations": [
                    "Scope: captured synthetic execution; deployment history and production cause are not established.",
                    "Source references and executed checks do not guarantee that the proposed mechanism is complete or semantically correct.",
                    *(
                        ["No executable baseline reproduction was available."]
                        if any(c.get("status") == "unavailable" for c in state["checks"])
                        else []
                    ),
                    *(
                        [
                            "The captured baseline passed; it does not reproduce the reported incident."
                        ]
                        if any(
                            c.get("kind") != "intervention" and c.get("status") == "passed"
                            for c in state["checks"]
                        )
                        else []
                    ),
                ],
                "support_level": "controlled_intervention"
                if selected
                and all(h["support_level"] == "controlled_intervention" for h in selected)
                else "reproduction"
                if selected
                else "insufficient",
                "rendered_from_reviewed_records": True,
            }
            state.update(diagnostic=diagnostic, status="completed", role="end")
            self.store.event(
                run,
                f"diagnostic:{state['turn']}",
                role,
                "diagnostic",
                diagnostic["summary"],
                diagnostic,
            )
        else:
            raise ValueError(f"Unavailable control: {action.name}")

    def schemas(self, state, role, tools):
        remaining = self.settings.max_calls - self.store.metrics(state["run_id"])["model_calls"]
        if role == "coordinator":
            if state["findings_turn"] < 0:
                allowed, target = [prompts.DELEGATE], "investigator"
            elif state["review_turn"] < state["findings_turn"]:
                allowed, target = [prompts.DELEGATE], "verifier"
            else:
                allowed, target = [prompts.FINISH], "investigator"
                if (
                    state.get("review", {}).get("needs_more")
                    and state["round"] < 2
                    and remaining >= 8
                ):
                    allowed.append(prompts.DELEGATE)
        else:
            collection = [
                s
                for s in tools.schemas
                if s["function"]["name"] not in {"run_check", "run_experiment"}
            ]
            checking = [
                s
                for s in tools.schemas
                if s["function"]["name"]
                in {"read_bundle", "read_file", "run_check", "run_experiment"}
            ]
            if role == "investigator" or (role == "single" and state["findings_turn"] < 0):
                allowed = [prompts.FINDINGS]
                if state["round_tools"] < 3 and remaining > (5 if role == "investigator" else 3):
                    allowed += collection
            elif role == "single" and state["review_turn"] >= state["findings_turn"]:
                allowed = [prompts.FINISH]
            elif not state["checks"]:
                allowed = [s for s in checking if s["function"]["name"] == "run_check"]
            else:
                allowed = [prompts.REVIEW]
                if state["hypotheses"] and state["round_tools"] < 3 and remaining > 2:
                    allowed += checking
        schemas = json.loads(json.dumps(allowed))
        captured = self.store.evidence(state["run_id"])
        known_paths = {e["path"] for e in captured}
        unavailable = {
            path for o in state["observations"] for path in o.get("data", {}).get("file_errors", {})
        }
        truncated = {
            path
            for o in state["observations"]
            for path in o.get("data", {}).get("truncated_paths", [])
        }
        unread = [
            p
            for p in ("runtime.log", "service.py", "settings.json", "input.json", "report.json")
            if p not in known_paths | unavailable
        ]
        readable = unread + sorted(truncated)
        remove = set()
        if not captured:
            remove |= {"list_files", "read_file", "search_trace", "get_test_report"}
        else:
            remove.add("list_files")
        if not unread:
            remove.add("read_bundle")
        if not readable:
            remove |= {"read_file", "search_trace"}
        if "report.json" in known_paths | unavailable:
            remove.add("get_test_report")
        schemas = [s for s in schemas if s["function"]["name"] not in remove]
        completed = {stable_id(o["tool"], o["arguments"]) for o in state["observations"] if o["ok"]}
        if (
            stable_id(
                "read_bundle",
                {
                    "paths": [
                        "runtime.log",
                        "service.py",
                        "settings.json",
                        "input.json",
                        "report.json",
                    ]
                },
            )
            in completed
        ):
            schemas = [
                s
                for s in schemas
                if s["function"]["name"] not in {"list_files", "get_test_report", "read_bundle"}
            ]
        if state["checks"]:
            schemas = [s for s in schemas if s["function"]["name"] != "run_check"]
        h_ids = [h["alias"] for h in state["hypotheses"]]
        c_ids = [f"C{i + 1}" for i in range(len(state["checks"]))]

        def constrain(value):
            if isinstance(value, dict):
                properties = value.get("properties", {})
                for field, ids in {"hypothesis_ids": h_ids, "check_ids": c_ids}.items():
                    if field in properties:
                        if ids:
                            properties[field]["items"]["enum"] = ids
                        else:
                            properties[field]["maxItems"] = 0
                for field, ids in {
                    "hypothesis_id": h_ids,
                    "line_ref": [
                        f"{alias}:L{i}"
                        for alias, key in state["evidence_aliases"].items()
                        for e in captured
                        if e["id"] == key
                        for i in range(e["start_line"], e["end_line"] + 1)
                    ],
                }.items():
                    if field in properties and ids:
                        properties[field]["enum"] = ids
                for child in value.values():
                    constrain(child)
            elif isinstance(value, list):
                for child in value:
                    constrain(child)

        constrain(schemas)
        for schema in schemas:
            function = schema["function"]
            if function["name"] == "submit_findings" and "service.py" not in known_paths:
                function["parameters"]["properties"]["hypotheses"]["maxItems"] = 0
            if function["name"] == "submit_review":
                function["parameters"]["properties"]["verdicts"].update(
                    maxItems=len(h_ids), uniqueItems=True
                )
            if function["name"] == "finish":
                confirmed = [h["alias"] for h in state["hypotheses"] if h["status"] == "confirmed"]
                properties = function["parameters"]["properties"]
                if confirmed:
                    properties["hypothesis_ids"]["items"]["enum"] = confirmed
                else:
                    properties["outcome"]["enum"] = ["insufficient"]
                    properties["hypothesis_ids"]["maxItems"] = 0
            if function["name"] == "delegate":
                function["parameters"]["properties"]["target"]["enum"] = [target]
            if function["name"] == "read_bundle":
                function["parameters"]["properties"]["paths"].update(
                    minItems=1,
                    maxItems=len(unread),
                    uniqueItems=True,
                    items={
                        "type": "string",
                        "enum": unread,
                    },
                )
            if function["name"] == "read_file":
                function["parameters"]["properties"]["path"]["enum"] = readable
        return schemas

    async def node(self, incoming, role, tools):
        state = json.loads(json.dumps(incoming))
        state["status"] = "running"
        run = state["run_id"]
        if (
            self.store.metrics(run)["model_calls"] >= self.settings.max_calls
            or state["turn"] >= self.settings.max_steps
        ):
            return self.stopped(
                state,
                "budget_exhausted",
                "Investigation reached configured budget; cause is not established.",
            )
        if state["agent_turns"].get(role, 0) >= (
            self.settings.max_calls if role == "single" else self.settings.max_agent_turns
        ):
            return self.stopped(
                state, "budget_exhausted", f"{role} reached configured turn budget."
            )
        state["visited"] = list(dict.fromkeys([*state["visited"], role]))
        try:
            schemas = self.schemas(state, role, tools)
            action = await self.model_action(state, role, schemas)
            if action.name not in {s["function"]["name"] for s in schemas}:
                raise ValueError(f"Unavailable action: {action.name}")
            if action.name in {s["function"]["name"] for s in tools.schemas}:
                result = await tools.call(action.name, action.arguments, role, state["turn"])
                state["observations"].append(
                    {
                        "role": role,
                        "tool": action.name,
                        "arguments": action.arguments,
                        "ok": result.ok,
                        "data": result.data,
                        "error": result.error,
                    }
                )
                state["round_tools"] += 1
                for e in result.evidence:
                    if e.id not in state["evidence_aliases"].values():
                        state["evidence_aliases"][f"E{len(state['evidence_aliases']) + 1}"] = e.id
                if (
                    result.ok
                    and "check_id" in result.data
                    and result.data["check_id"] not in {c["check_id"] for c in state["checks"]}
                ):
                    state["checks"].append(result.data)
            else:
                self.control(state, role, action)
            state.update(feedback="", errors=0)
        except ProviderUnavailable as exc:
            state.update(status="error", feedback=str(exc))
            self.store.event(
                run, f"provider-error:{state['turn']}", role, "error", str(exc), {"resumable": True}
            )
        except Exception as exc:
            state["errors"] += 1
            state["feedback"] = f"Action rejected: {str(exc)[:800]}"
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
                    state, "failed", "Three consecutive invalid actions; inspect audit events."
                )
        state["turn"] += 1
        state["agent_turns"][role] = state["agent_turns"].get(role, 0) + 1
        return state

    def graph(self, saver, tools):
        graph = StateGraph(V2State)
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

    async def _run(self, run_id, pause_after, step_delay):
        record = self.store.run(run_id)
        if record["state"].get("engine_version") != "v2":
            raise ValueError("Use the V1 runner for this saved investigation")
        if record["status"] in ("completed", "budget_exhausted", "failed"):
            return record
        self.settings = self.settings.model_copy(update=record["state"]["config"])
        if type(self.provider) is Provider:
            self.provider = Provider(self.settings)
        self.store.update(run_id, status="running", cancel=False)
        if record["status"] != "queued":
            self.store.event(
                run_id,
                f"resume:{len(self.store.events(run_id))}",
                "system",
                "resumed",
                "Resumed saved V2 graph, aliases and operation keys",
            )
        started, steps = time.perf_counter(), 0
        try:
            async with connect_tools(
                self.settings, self.store, run_id, record["incident_id"], version=2
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
                                "Cancelled at a durable action boundary",
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
