import argparse
import asyncio
import json
import os
from pathlib import Path

from tracemedic.config import Settings
from tracemedic.engine import Engine
from tracemedic.mcp_client import connect_tools


def build_engine(args):
    changes = {}
    if args.data_dir:
        changes["data_dir"] = Path(args.data_dir).resolve()
    if args.provider:
        changes["provider"] = args.provider
    settings = Settings(**changes)
    provider = None
    if settings.provider == "scripted":
        from tracemedic.testing import ScriptedProvider

        provider = ScriptedProvider()
    return Engine(settings, provider)


async def execute(args):
    engine = build_engine(args)
    if args.command == "run":
        run = engine.create(args.incident, args.mode, args.run_id)
        print(
            json.dumps(
                {
                    "run_id": run,
                    "provider": engine.settings.provider,
                    "warning": "TEST DOUBLE" if engine.settings.provider == "scripted" else None,
                }
            ),
            flush=True,
        )
        result = await engine.run(run, args.pause_after, args.step_delay)
        print(json.dumps({**result, "metrics": engine.store.metrics(run)}, indent=2))
        return 0 if result["status"] in ("completed", "interrupted", "cancelled") else 2
    if args.command == "resume":
        result = await engine.run(args.run_id, args.pause_after)
        print(json.dumps({**result, "metrics": engine.store.metrics(args.run_id)}, indent=2))
        return 0 if result["status"] in ("completed", "interrupted", "cancelled") else 2
    if args.command == "show":
        print(
            json.dumps(
                {
                    **engine.store.run(args.run_id),
                    "events": engine.store.events(args.run_id),
                    "evidence": engine.store.evidence(args.run_id),
                    "metrics": engine.store.metrics(args.run_id),
                },
                indent=2,
            )
        )
    if args.command == "list":
        print(json.dumps(engine.store.runs(), indent=2))
    if args.command == "tools":
        run = engine.create(args.incident)
        async with connect_tools(engine.settings, engine.store, run, args.incident) as tools:
            output = {
                "schemas": tools.schemas,
                "discovery": (await tools.call("list_files", {}, "system", 0)).model_dump(),
                "read": (
                    await tools.call("read_file", {"path": "runtime.log"}, "system", 1)
                ).model_dump(),
                "check": (await tools.call("run_check", {}, "system", 2)).model_dump(),
            }
            print(json.dumps(output, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description="TraceMedic evidence-first incident investigation")
    parser.add_argument("--data-dir")
    parser.add_argument(
        "--provider",
        choices=["ollama", "openai-compatible", "scripted"],
        help="scripted is an explicit test double, not an LLM",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("incident")
    run.add_argument("--mode", choices=["multi", "single"], default="multi")
    run.add_argument("--run-id")
    run.add_argument("--pause-after", type=int)
    run.add_argument(
        "--step-delay",
        type=float,
        default=0,
        help="Diagnostic pause between durable steps, useful for crash tests",
    )
    resume = commands.add_parser("resume")
    resume.add_argument("run_id")
    resume.add_argument("--pause-after", type=int)
    show = commands.add_parser("show")
    show.add_argument("run_id")
    commands.add_parser("list")
    tools = commands.add_parser("tools")
    tools.add_argument("incident", default="case-01", nargs="?")
    serve = commands.add_parser("serve")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.command == "serve":
        if args.data_dir:
            os.environ["TRACEMEDIC_DATA_DIR"] = str(Path(args.data_dir).resolve())
        import uvicorn

        uvicorn.run("tracemedic.api:app", host="127.0.0.1", port=args.port)
    else:
        raise SystemExit(asyncio.run(execute(args)))


if __name__ == "__main__":
    main()
