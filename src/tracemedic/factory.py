"""Choose the saved workflow on resume; old records are unambiguously V1."""

from tracemedic.engine import Engine as V1Engine
from tracemedic.store import Store
from tracemedic.v2.engine import Engine as V2Engine


def build_engine(settings, workflow=None, run_id=None, provider=None):
    if run_id:
        workflow = Store(settings.audit_db).run(run_id)["state"].get("engine_version", "v1")
    workflow = workflow or ("v1" if settings.provider == "scripted" else "v2")
    if workflow not in ("v1", "v2"):
        raise ValueError("Unknown workflow version")
    if provider is None and settings.provider == "scripted":
        if workflow == "v2":
            from tracemedic.v2.testing import ScriptedProvider
        else:
            from tracemedic.testing import ScriptedProvider
        provider = ScriptedProvider()
    return (V2Engine if workflow == "v2" else V1Engine)(settings, provider)
