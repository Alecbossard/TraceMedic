import os
import subprocess
import sys
import time

from tracemedic.store import Store


def test_hard_process_kill_then_resume_preserves_proof_and_single_execution(settings):
    data = settings.data_dir
    run_id = "crash-test"
    cmd = [
        sys.executable,
        "-m",
        "tracemedic.cli",
        "--provider",
        "scripted",
        "--data-dir",
        str(data),
        "run",
        "case-01",
        "--run-id",
        run_id,
        "--step-delay",
        "0.35",
    ]
    with (data / "worker-output.txt").open("w") as output:
        worker = subprocess.Popen(
            cmd,
            stdout=output,
            stderr=output,
            **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
        )
        store = Store(settings.audit_db)
        try:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                if any(
                    e["kind"] == "tool_result" and e["data"].get("tool") == "run_check"
                    for e in store.events(run_id)
                ):
                    break
                if worker.poll() is not None:
                    raise AssertionError((data / "worker-output.txt").read_text())
                time.sleep(0.03)
            else:
                raise AssertionError("Worker did not reach fixture operation")
            before = store.evidence(run_id)
            worker.kill()  # abrupt death, not a graceful in-memory pause
            worker.wait(timeout=10)
        finally:
            if worker.poll() is None:
                worker.kill()
                worker.wait(timeout=10)
    resumed = subprocess.run(
        [
            sys.executable,
            "-m",
            "tracemedic.cli",
            "--provider",
            "scripted",
            "--data-dir",
            str(data),
            "resume",
            run_id,
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert store.run(run_id)["status"] == "completed"
    assert {e["id"] for e in before} <= {e["id"] for e in store.evidence(run_id)}
    for item in before:
        assert item in store.evidence(run_id)
    with store.connect() as db:
        assert (
            db.execute(
                "SELECT count(*) FROM operations WHERE run_id=? AND key LIKE 'fixture:%'", (run_id,)
            ).fetchone()[0]
            == 1
        )
    assert (
        len(
            [
                e
                for e in store.events(run_id)
                if e["kind"] == "tool_result" and e["data"].get("tool") == "run_check"
            ]
        )
        == 1
    )
    assert any(e["kind"] == "resumed" for e in store.events(run_id))
