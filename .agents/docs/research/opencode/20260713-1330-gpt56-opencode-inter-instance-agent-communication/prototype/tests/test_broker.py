import json
import tempfile
from pathlib import Path
import importlib.util

SPEC = importlib.util.spec_from_file_location(
    "broker", Path(__file__).parents[1] / "broker" / "broker.py"
)
broker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(broker)


def test_submit_claim_complete():
    with tempfile.TemporaryDirectory() as td:
        db = broker.connect(Path(td) / "q.sqlite3")
        env = {
            "task_id": "tsk_test",
            "idempotency_key": "idem-test",
            "target": {"principal_id": "agent:builder"},
        }
        assert broker.submit(db, env) == "tsk_test"
        assert broker.submit(db, env) == "tsk_test"
        claimed = broker.claim(db, "agent:builder", "worker-1")
        assert claimed["task_id"] == "tsk_test"
        broker.complete(db, "tsk_test", "worker-1", {"ok": True}, True)
        row = db.execute(
            "SELECT state,result_json FROM tasks WHERE id='tsk_test'"
        ).fetchone()
        assert row["state"] == "succeeded"
        assert json.loads(row["result_json"])["ok"] is True
