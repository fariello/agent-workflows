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
