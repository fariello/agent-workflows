"""TEMPORARY Windows CI probe (removed before merge): surface the exception telemetry swallows."""

import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent_workflows import run_analytics_config, run_analytics_privacy, runner_shared
from agent_workflows import run_analytics_telemetry as T

with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    repo = root / "repo"
    repo.mkdir()
    run_dir = root / "run"
    run_dir.mkdir()
    try:
        cfg = run_analytics_config.read_telemetry_config(repo)
        print("enabled", cfg.enabled)
        stream = runner_shared.telemetry_stream_path(run_dir, "x1")
        stream.parent.mkdir(parents=True, exist_ok=True)
        salt = run_analytics_privacy.load_or_create_salt(
            runner_shared.analytics_cache_dir(repo)
        )
        print("salt ok")
        adapter = runner_shared._launch_safe_probe_adapter(T, cfg)
        print("adapter", adapter)
        kw = dict(
            execution_id="x1", salt=salt, config=cfg, context={}, disk_path=run_dir
        )
        if adapter is not None:
            kw["adapter"] = adapter
        c = T.TelemetryCollector(stream, **kw)
        c.start()
        print("collector ok")
        s = T.ResourceSampler(c)
        s.start()
        s.stop()
        c.close()
        print("sampler ok", list(stream.parent.glob("*")))
    except Exception:
        traceback.print_exc()

# round 2: validate each emitted payload directly to expose the swallowed SchemaRefusal
import json

with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    repo = root / "repo"
    repo.mkdir()
    run_dir = root / "run"
    run_dir.mkdir()
    cfg = run_analytics_config.read_telemetry_config(repo)
    adapter = (
        runner_shared._launch_safe_probe_adapter(T, cfg)
        or T.SystemResourceProbeAdapter()
    )
    try:
        r = adapter.resources(disk_path=run_dir)
        print("resources", json.dumps(r, default=str)[:1500])
    except Exception:
        traceback.print_exc()
    try:
        a = adapter.accelerators()
        print("accel", a.ok, a.reason, str(a.value)[:300])
        tv = adapter.tool_versions()
        print("tools", tv.ok, str(tv.value)[:300])
    except Exception:
        traceback.print_exc()
    stream = runner_shared.telemetry_stream_path(run_dir, "x2")
    stream.parent.mkdir(parents=True, exist_ok=True)
    c = T.TelemetryCollector(
        stream,
        execution_id="x2",
        salt="s" * 32,
        config=cfg,
        context={},
        disk_path=run_dir,
        adapter=adapter,
    )
    orig = T.validate_event

    def v(p):
        try:
            return orig(p)
        except Exception as e:
            print("REFUSED:", type(e).__name__, e, json.dumps(p, default=str)[:1500])
            raise

    T.validate_event = v
    c.start()
    c.close()
    print("notes", c.counters.warnings, list(stream.parent.glob("*")))
