"""Configuration and policy resolution for notification channels (spec 6kwd2e R10.2, R10.4).

User config lives at `<AW_HOME>/notify.json` (mode 0600 on POSIX).
Secrets are never read from or written to tracked repository config.
Tracked project policy in `.aw/config/project.json` under `notify_policy`
can act only as a ceiling ('forbid' or 'terse-only'), never as enablement.
"""

from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any
import warnings

from agent_workflows import project_context


def get_notify_config_path() -> Path:
    """Return the absolute path to <AW_HOME>/notify.json."""
    aw_home = Path(project_context.get_default_aw_home())
    return aw_home / "notify.json"


def load_user_config() -> dict[str, Any]:
    """Read <AW_HOME>/notify.json.

    NEVER creates the file if missing.
    On POSIX, if any group/other permission bit is set (st_mode & 0o077),
    tightens the file to 0600 with a warning. If tightening fails, fails closed
    (returns {} without reading).
    Malformed JSON disables every channel with one warning and returns {}.
    """
    path = get_notify_config_path()
    if not path.is_file():
        return {}

    if os.name != "nt":
        try:
            st = path.stat()
            if st.st_mode & 0o077:
                warnings.warn(
                    f"Tightening permissions of {path} to 0600 (was {oct(st.st_mode & 0o777)})",
                    UserWarning,
                    stacklevel=2,
                )
                try:
                    path.chmod(0o600)
                except Exception as exc:
                    warnings.warn(
                        f"Failed to tighten permissions of {path} to 0600 ({exc}); "
                        f"ignoring user notify config (fail closed)",
                        UserWarning,
                        stacklevel=2,
                    )
                    return {}
        except Exception as exc:
            warnings.warn(
                f"Failed to stat {path} ({exc}); ignoring user notify config (fail closed)",
                UserWarning,
                stacklevel=2,
            )
            return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            warnings.warn(
                f"Malformed {path}: expected top-level JSON object; ignoring user notify config",
                UserWarning,
                stacklevel=2,
            )
            return {}
        return data
    except Exception as exc:
        warnings.warn(
            f"Malformed or unreadable {path} ({exc}); disabling all notification channels",
            UserWarning,
            stacklevel=2,
        )
        return {}


def save_user_config(cfg: dict[str, Any]) -> Path:
    """Atomically write <AW_HOME>/notify.json with strict user-only permissions.

    On POSIX, creates the temp file with mode 0600 via os.open(..., O_CREAT|O_EXCL, 0o600).
    On Windows, sets a user-only ACL via icacls and warns on failure.
    """
    target = get_notify_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.parent / f".notify.json.tmp.{os.getpid()}.{time.time_ns()}"

    if os.name != "nt":
        fd = os.open(str(tmp_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(cfg, handle, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(tmp_path), str(target))
        finally:
            if tmp_path.exists():
                with contextlib.suppress(OSError):
                    tmp_path.unlink()
    else:
        try:
            tmp_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
            username = os.environ.get("USERNAME", "")
            if username:
                cmd = [
                    "icacls",
                    str(tmp_path),
                    "/inheritance:r",
                    "/grant:r",
                    f"{username}:(F)",
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if res.returncode != 0:
                    warnings.warn(
                        f"icacls failed to set user-only ACL on {tmp_path}: {res.stderr.strip()}",
                        UserWarning,
                        stacklevel=2,
                    )
            os.replace(str(tmp_path), str(target))
        finally:
            if tmp_path.exists():
                with contextlib.suppress(OSError):
                    tmp_path.unlink()

    return target


def read_notify_policy(repo: Path | str | None = None) -> str | None:
    """Read .aw/config/project.json key notify_policy ('forbid' | 'terse-only').

    Absent or null means no ceiling (returns None).
    Never raises: an unreadable file or unrecognized value is treated as 'forbid'
    with a warning (fail closed, D-2).
    """
    if repo is None:
        repo = Path.cwd()
    repo_path = Path(repo)
    project_cfg = repo_path / ".aw" / "config" / "project.json"
    if not project_cfg.is_file():
        return None

    try:
        data = json.loads(project_cfg.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            warnings.warn(
                f"Malformed {project_cfg}: expected JSON object; treating notify_policy as 'forbid'",
                UserWarning,
                stacklevel=2,
            )
            return "forbid"
    except Exception as exc:
        warnings.warn(
            f"Unreadable {project_cfg} ({exc}); treating notify_policy as 'forbid'",
            UserWarning,
            stacklevel=2,
        )
        return "forbid"

    if "notify_policy" not in data or data["notify_policy"] is None:
        return None

    val = data["notify_policy"]
    if val in ("forbid", "terse-only"):
        return val

    warnings.warn(
        f"Unrecognized notify_policy {val!r} in {project_cfg}; treating as 'forbid'",
        UserWarning,
        stacklevel=2,
    )
    return "forbid"


def tracked_secret_warnings(repo: Path | str | None = None) -> list[str]:
    """Scan tracked .aw/config/*.json files for forbidden notify secret keys.

    Reports, without echoing values, any 'notify' key or any key starting 'notify_'
    other than 'notify_policy'.
    """
    if repo is None:
        repo = Path.cwd()
    repo_path = Path(repo)
    cfg_dir = repo_path / ".aw" / "config"
    if not cfg_dir.is_dir():
        return []

    warnings_list: list[str] = []
    for cfg_file in sorted(cfg_dir.glob("*.json")):
        try:
            data = json.loads(cfg_file.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for k in sorted(data.keys()):
                    if k == "notify" or (
                        k.startswith("notify_") and k != "notify_policy"
                    ):
                        try:
                            rel_path = cfg_file.relative_to(repo_path).as_posix()
                        except ValueError:
                            rel_path = cfg_file.name
                        warnings_list.append(
                            f"Tracked file {rel_path} contains forbidden secret key {k!r}; "
                            f"channel settings must live under AW_HOME or in environment variables"
                        )
        except Exception:
            pass
    return warnings_list


def effective_channels(repo: Path | str | None = None) -> dict[str, dict[str, Any]]:
    """Determine active notification channels and their resolved configuration.

    Applies tracked policy ceiling to user and environment configuration.
    Returns a mapping of channel_name -> channel_config dict.
    """
    user_cfg = load_user_config()
    channels: dict[str, dict[str, Any]] = {}
    for k, v in user_cfg.items():
        if isinstance(v, dict):
            channels[k] = dict(v)

    # Check environment variable overrides
    wh_env = os.environ.get("AW_NOTIFY_WEBHOOK_URL")
    if wh_env is not None:
        wh_val = wh_env.strip()
        if not wh_val or not (
            wh_val.startswith("http://") or wh_val.startswith("https://")
        ):
            warnings.warn(
                f"Malformed or empty AW_NOTIFY_WEBHOOK_URL: {wh_env!r}; ignoring",
                UserWarning,
                stacklevel=2,
            )
        else:
            curr = channels.get("webhook", {})
            mode = curr.get("mode") if curr.get("mode") == "full" else "terse"
            entry = dict(curr)
            entry["enabled"] = True
            entry["mode"] = mode
            entry["url"] = wh_val
            channels["webhook"] = entry

    cmd_env = os.environ.get("AW_NOTIFY_COMMAND")
    if cmd_env is not None:
        cmd_val = cmd_env.strip()
        if not cmd_val:
            warnings.warn(
                "AW_NOTIFY_COMMAND is empty; ignoring",
                UserWarning,
                stacklevel=2,
            )
        else:
            try:
                parsed = json.loads(cmd_val)
                if not isinstance(parsed, list) or not all(
                    isinstance(x, str) and x for x in parsed
                ):
                    warnings.warn(
                        f"AW_NOTIFY_COMMAND must be a JSON array of non-empty strings; got {cmd_val!r}; ignoring",
                        UserWarning,
                        stacklevel=2,
                    )
                else:
                    curr = channels.get("command", {})
                    mode = curr.get("mode") if curr.get("mode") == "full" else "terse"
                    entry = dict(curr)
                    entry["enabled"] = True
                    entry["mode"] = mode
                    entry["command"] = parsed
                    channels["command"] = entry
            except Exception as exc:
                warnings.warn(
                    f"AW_NOTIFY_COMMAND malformed JSON ({exc}); ignoring",
                    UserWarning,
                    stacklevel=2,
                )

    # Filter enabled channels
    active = {k: v for k, v in channels.items() if v.get("enabled") is True}

    # Apply project policy ceiling
    policy = read_notify_policy(repo)
    if policy == "forbid":
        return {}
    if policy == "terse-only":
        for v in active.values():
            v["mode"] = "terse"
    else:
        for v in active.values():
            if v.get("mode") not in ("terse", "full"):
                v["mode"] = "terse"

    return active
