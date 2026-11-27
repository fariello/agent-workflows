"""Behavioral tests for `aw oc prompt`, `aw agy prompt`, and shared session continuation (`z4kwzd`)."""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from agent_workflows import (
    agy_models,
    agy_runipd,
    cli,
    lane_containment,
    oc_runipd,
    render_stream,
    run_viewer,
    runner_profiles,
    runner_shared,
)


def _init_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / ".aw" / "records" / "runs").mkdir(parents=True, exist_ok=True)
    (repo / "README.md").write_text("# test repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)
    return repo


class _FakeStream(io.StringIO):
    def __init__(self, text: str, *, tty: bool) -> None:
        super().__init__(text)
        self._tty = tty
        self.read_called = False

    def isatty(self) -> bool:
        return self._tty

    def read(self, size: int | None = -1) -> str:
        self.read_called = True
        return super().read(size)


class TestResolveAdhocPromptText:
    def test_inline_text(self) -> None:
        assert (
            runner_shared.resolve_adhoc_prompt_text("Summarize the diff.", None)
            == "Summarize the diff."
        )

    def test_file_strips_bom_and_anchored_metadata_preserves_body_comments(
        self, tmp_path: Path
    ) -> None:
        p1 = tmp_path / "p1.md"
        p1.write_text(
            "\ufeff<!-- aw-prompt: id=abc123 kind=research -->\n\n"
            "First line\n<!-- keep this body comment -->\nSecond line\n",
            encoding="utf-8",
        )
        resolved1 = runner_shared.resolve_adhoc_prompt_text(None, str(p1))
        assert resolved1 == "First line\n<!-- keep this body comment -->\nSecond line\n"

        p2 = tmp_path / "p2.md"
        p2.write_text(
            "<!-- aw-managed-prompt: v1\nmultiline: true\n-->\nBody text\n<!-- body -->\n",
            encoding="utf-8",
        )
        resolved2 = runner_shared.resolve_adhoc_prompt_text(None, str(p2))
        assert resolved2 == "Body text\n<!-- body -->\n"

        p3 = tmp_path / "p3.md"
        p3.write_text(
            "<!-- regular user comment -->\nBody stays intact.\n",
            encoding="utf-8",
        )
        resolved3 = runner_shared.resolve_adhoc_prompt_text(None, str(p3))
        assert resolved3 == "<!-- regular user comment -->\nBody stays intact.\n"

    def test_stdin_dash_and_piped(self) -> None:
        dash_stream = _FakeStream("From dash stdin\n", tty=False)
        assert (
            runner_shared.resolve_adhoc_prompt_text("-", None, stdin_stream=dash_stream)
            == "From dash stdin\n"
        )

        piped_stream = _FakeStream("From piped stdin\n", tty=False)
        assert (
            runner_shared.resolve_adhoc_prompt_text(
                None, None, stdin_stream=piped_stream
            )
            == "From piped stdin\n"
        )

    def test_refusals(self, tmp_path: Path) -> None:
        existing = tmp_path / "prompt.md"
        existing.write_text("hello", encoding="utf-8")

        # Conflicting inline + --file
        with pytest.raises(runner_shared.DriverError, match="Conflicting"):
            runner_shared.resolve_adhoc_prompt_text("inline", str(existing))

        # Conflicting '-' + --file
        with pytest.raises(runner_shared.DriverError, match="Conflicting"):
            runner_shared.resolve_adhoc_prompt_text("-", str(existing))

        # Missing file
        with pytest.raises(runner_shared.DriverError, match="Unable to read"):
            runner_shared.resolve_adhoc_prompt_text(None, str(tmp_path / "nope.md"))

        # Interactive TTY with no prompt or file refuses without reading
        tty_stream = _FakeStream("should not be read", tty=True)
        with pytest.raises(runner_shared.DriverError, match="No prompt provided"):
            runner_shared.resolve_adhoc_prompt_text(None, None, stdin_stream=tty_stream)
        assert tty_stream.read_called is False

        # Empty / whitespace-only prompts
        with pytest.raises(runner_shared.DriverError, match="empty"):
            runner_shared.resolve_adhoc_prompt_text("   \n\t  ", None)

        only_header = tmp_path / "only_header.md"
        only_header.write_text("<!-- aw-prompt: id=abc -->\n   \n", encoding="utf-8")
        with pytest.raises(runner_shared.DriverError, match="empty"):
            runner_shared.resolve_adhoc_prompt_text(None, str(only_header))


class TestSharedEngineAndSessionContinuation:
    def test_initialize_continue_and_run_viewer_compatibility(
        self, tmp_path: Path
    ) -> None:
        repo = _init_git_repo(tmp_path)
        run_dir, state, item, prompt_path = runner_shared.initialize_adhoc_prompt_run(
            repo,
            host_labels=runner_shared.OC_HOST_LABELS,
            options={"model": "test/model", "output_mode": "clean"},
            prompt_text="Explain module boundaries.",
        )

        assert run_dir.is_dir()
        assert prompt_path == run_dir / "prompts" / "01-adhoc0-attempt-1.md"
        assert prompt_path.read_text(encoding="utf-8") == "Explain module boundaries."
        assert state["run_kind"] == "adhoc-prompt"
        assert state["driver"] == runner_shared.OC_HOST_LABELS.id
        assert state["selectors"] == ["prompt"]
        assert state["set_sessions"] == {}
        assert item["position"] == 1
        assert item["id6"] == "adhoc0"
        assert item["setid"] == "adhoc"
        assert item["artifact_type"] == "adhoc-prompt"
        assert item["action"] == "prompt"
        assert item["status"] == "queued"

        in_flight_attempts_seen: list[dict[str, Any]] = []

        def fake_spawn(
            *,
            prompt_path: Path,
            attempt_no: int,
            session_id: str | None,
            use_continue: bool,
            work_dir: str | None,
            tracker: Any,
            suffix: str = "",
        ) -> tuple[int, str | None, Path, list[str]]:
            assert len(item["attempts"]) == 1
            in_flight_attempts_seen.append(dict(item["attempts"][-1]))
            log_path = runner_shared.attempt_log_path(
                run_dir, item, attempt_no, suffix=suffix
            )
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(
                json.dumps({"sessionID": "ses_adhoc_001"}) + "\n", encoding="utf-8"
            )
            return 0, "ses_adhoc_001", log_path, ["opencode", "run"]

        rc, sid, log_path, _argv = runner_shared.continue_session_turn(
            run_dir=run_dir,
            state=state,
            item=item,
            prompt_text="Explain module boundaries.",
            session_id=None,
            use_continue=False,
            work_dir=None,
            tracker=render_stream.StreamTracker(),
            spawn_turn_fn=fake_spawn,
        )
        assert rc == 0
        assert sid == "ses_adhoc_001"
        assert log_path.is_file()
        assert len(in_flight_attempts_seen) == 1
        assert in_flight_attempts_seen[0]["attempt"] == 1
        assert "started_at" in in_flight_attempts_seen[0]

        reloaded = runner_shared.load_state(run_dir)
        assert reloaded["session_id"] == "ses_adhoc_001"
        assert reloaded["queue"][0]["attempts"][0]["returncode"] == 0
        assert reloaded["queue"][0]["attempts"][0]["session_id"] == "ses_adhoc_001"
        assert reloaded["queue"][0]["attempts"][0]["ended_at"]

        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        event_names = [ev["event"] for ev in events]
        assert "run-initialized" in event_names
        assert "prompt-turn-started" in event_names
        assert "prompt-turn-finished" in event_names

        # run_viewer compatibility
        summary = run_viewer.load_run_summary(run_dir)
        assert summary.run_id == state["run_id"]
        assert len(summary.steps) == 1
        assert summary.steps[0].id6 == "adhoc0"
        assert summary.steps[0].session_id == "ses_adhoc_001"

    def test_continue_session_turn_record_attempt_false_for_9ici96(
        self, tmp_path: Path
    ) -> None:
        repo = _init_git_repo(tmp_path)
        run_dir, state, item, _ = runner_shared.initialize_adhoc_prompt_run(
            repo,
            host_labels=runner_shared.AGY_HOST_LABELS,
            options={},
            prompt_text="Initial turn",
        )
        item["attempts"].append(
            {
                "attempt": 1,
                "started_at": runner_shared.utc_now(),
                "ended_at": runner_shared.utc_now(),
                "returncode": 0,
                "session_id": "conv_existing",
            }
        )

        captured: dict[str, Any] = {}

        def fake_inject(
            *,
            prompt_path: Path,
            attempt_no: int,
            session_id: str | None,
            use_continue: bool,
            work_dir: str | None,
            tracker: Any,
            suffix: str = "",
        ) -> tuple[int, str | None, Path, list[str]]:
            captured["prompt_path"] = prompt_path
            captured["attempt_no"] = attempt_no
            captured["session_id"] = session_id
            captured["suffix"] = suffix
            log_path = runner_shared.attempt_log_path(
                run_dir, item, attempt_no, suffix=suffix
            )
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            return 0, "conv_existing", log_path, ["agy"]

        rc, sid, _log, _argv = runner_shared.continue_session_turn(
            run_dir=run_dir,
            state=state,
            item=item,
            prompt_text="Operator injected guidance",
            session_id="conv_existing",
            use_continue=False,
            work_dir=None,
            tracker=render_stream.StreamTracker(),
            spawn_turn_fn=fake_inject,
            suffix="inject",
            attempt_no=1,
            record_attempt=False,
            event_prefix="inject-turn",
        )
        assert rc == 0
        assert sid == "conv_existing"
        assert len(item["attempts"]) == 1  # did NOT burn a retry slot
        assert captured["attempt_no"] == 1
        assert captured["suffix"] == "inject"
        assert captured["prompt_path"].name == "01-adhoc0-inject-attempt-1.md"

        events = [
            json.loads(line)["event"]
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        assert "inject-turn-started" in events
        assert "inject-turn-finished" in events

    def test_flag_conflict_refusals_create_no_run_or_worktree(
        self, tmp_path: Path
    ) -> None:
        repo = _init_git_repo(tmp_path)
        runs_root = runner_shared.state_root(repo)

        # Direct validator raises DriverError
        with pytest.raises(runner_shared.DriverError, match="Conflicting session"):
            runner_shared.validate_adhoc_prompt_options(
                session_id="ses_1", use_continue=True, isolate_worktree=False
            )
        with pytest.raises(runner_shared.DriverError, match="Conflicting isolation"):
            runner_shared.validate_adhoc_prompt_options(
                session_id="ses_1", use_continue=False, isolate_worktree=True
            )
        with pytest.raises(runner_shared.DriverError, match="Conflicting isolation"):
            runner_shared.validate_adhoc_prompt_options(
                session_id=None, use_continue=True, isolate_worktree=True
            )

        for kwargs in (
            {"session_id": "ses_1", "use_continue": True, "isolate_worktree": False},
            {"session_id": "ses_1", "use_continue": False, "isolate_worktree": True},
            {"session_id": None, "use_continue": True, "isolate_worktree": True},
        ):
            err = io.StringIO()
            rc = runner_shared.run_adhoc_prompt_turn(
                repo=repo,
                host_labels=runner_shared.OC_HOST_LABELS,
                options={},
                prompt_text="hello",
                spawn_turn_fn=lambda **_: pytest.fail("should not spawn"),
                stderr=err,
                **kwargs,
            )
            assert rc == 2
            assert "Conflicting" in err.getvalue()
        assert list(runs_root.iterdir()) == []
        assert not (repo / ".aw" / "worktrees").exists()

    def test_isolate_worktree_tears_down_empty_lane(self, tmp_path: Path) -> None:
        repo = _init_git_repo(tmp_path)
        seen_work_dir: list[Path] = []

        def fake_spawn(
            *,
            state: dict[str, Any],
            run_dir: Path,
            item: dict[str, Any],
            prompt_path: Path,
            attempt_no: int,
            session_id: str | None,
            use_continue: bool,
            work_dir: str | None,
            tracker: Any,
            suffix: str = "",
        ) -> tuple[int, str | None, Path, list[str]]:
            assert work_dir is not None
            wt = Path(work_dir)
            assert wt.is_dir()
            seen_work_dir.append(wt)
            log_path = runner_shared.attempt_log_path(run_dir, item, attempt_no)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            return 0, "ses_clean", log_path, ["opencode", "run"]

        out = io.StringIO()
        rc = runner_shared.run_adhoc_prompt_turn(
            repo=repo,
            host_labels=runner_shared.OC_HOST_LABELS,
            options={},
            prompt_text="Read-only check",
            spawn_turn_fn=fake_spawn,
            isolate_worktree=True,
            stdout=out,
        )
        assert rc == 0
        assert len(seen_work_dir) == 1
        assert not seen_work_dir[0].exists()
        output = out.getvalue()
        assert "Preserved isolated worktree" not in output
        assert "Session ID: ses_clean" in output
        assert "Run dir: .aw/records/runs/" in output
        assert str(Path.home()) not in output

    def test_isolate_worktree_preserves_dirty_lane(self, tmp_path: Path) -> None:
        repo = _init_git_repo(tmp_path)
        seen_work_dir: list[Path] = []

        def fake_spawn(
            *,
            state: dict[str, Any],
            run_dir: Path,
            item: dict[str, Any],
            prompt_path: Path,
            attempt_no: int,
            session_id: str | None,
            use_continue: bool,
            work_dir: str | None,
            tracker: Any,
            suffix: str = "",
        ) -> tuple[int, str | None, Path, list[str]]:
            assert work_dir is not None
            wt = Path(work_dir)
            seen_work_dir.append(wt)
            (wt / "dirty.txt").write_text("unsaved agent edit\n", encoding="utf-8")
            log_path = runner_shared.attempt_log_path(run_dir, item, attempt_no)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            return 0, "ses_dirty", log_path, ["opencode", "run"]

        out = io.StringIO()
        rc = runner_shared.run_adhoc_prompt_turn(
            repo=repo,
            host_labels=runner_shared.OC_HOST_LABELS,
            options={},
            prompt_text="Make a draft file",
            spawn_turn_fn=fake_spawn,
            isolate_worktree=True,
            stdout=out,
        )
        assert rc == 0
        assert len(seen_work_dir) == 1
        assert (seen_work_dir[0] / "dirty.txt").read_text(
            encoding="utf-8"
        ) == "unsaved agent edit\n"
        output = out.getvalue()
        assert (
            "Preserved isolated worktree with changes: .aw/worktrees/adhoc-" in output
        )
        assert "(branch: aw/lane/adhoc-" in output
        assert str(repo) not in output
        assert str(Path.home()) not in output

    def test_isolate_worktree_preserves_ahead_lane(self, tmp_path: Path) -> None:
        repo = _init_git_repo(tmp_path)
        seen_work_dir: list[Path] = []

        def fake_spawn(
            *,
            state: dict[str, Any],
            run_dir: Path,
            item: dict[str, Any],
            prompt_path: Path,
            attempt_no: int,
            session_id: str | None,
            use_continue: bool,
            work_dir: str | None,
            tracker: Any,
            suffix: str = "",
        ) -> tuple[int, str | None, Path, list[str]]:
            assert work_dir is not None
            wt = Path(work_dir)
            seen_work_dir.append(wt)
            (wt / "committed.txt").write_text("committed change\n", encoding="utf-8")
            subprocess.run(["git", "add", "committed.txt"], cwd=wt, check=True)
            subprocess.run(
                ["git", "commit", "-q", "-m", "agent commit"], cwd=wt, check=True
            )
            log_path = runner_shared.attempt_log_path(run_dir, item, attempt_no)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            return 0, "ses_ahead", log_path, ["opencode", "run"]

        out = io.StringIO()
        rc = runner_shared.run_adhoc_prompt_turn(
            repo=repo,
            host_labels=runner_shared.AGY_HOST_LABELS,
            options={},
            prompt_text="Commit a change",
            spawn_turn_fn=fake_spawn,
            isolate_worktree=True,
            stdout=out,
        )
        assert rc == 0
        assert seen_work_dir[0].is_dir()
        assert (seen_work_dir[0] / "committed.txt").is_file()
        output = out.getvalue()
        assert (
            "Preserved isolated worktree with changes: .aw/worktrees/adhoc-" in output
        )
        assert "(branch: aw/lane/adhoc-" in output

    def test_keyboard_interrupt_and_driver_error_exit_codes(
        self, tmp_path: Path
    ) -> None:
        repo = _init_git_repo(tmp_path)
        runs_root = runner_shared.state_root(repo)

        rc_int = runner_shared.run_adhoc_prompt_turn(
            repo=repo,
            host_labels=runner_shared.OC_HOST_LABELS,
            options={},
            prompt_text="Interrupt me",
            spawn_turn_fn=lambda **_: (_ for _ in ()).throw(KeyboardInterrupt()),
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )
        assert rc_int == 130
        run_dirs = sorted(runs_root.iterdir())
        assert len(run_dirs) == 1
        assert (
            runner_shared.load_state(run_dirs[0])["queue"][0]["status"] == "interrupted"
        )

        err = io.StringIO()
        rc_err = runner_shared.run_adhoc_prompt_turn(
            repo=repo,
            host_labels=runner_shared.AGY_HOST_LABELS,
            options={},
            prompt_text="Fail me",
            spawn_turn_fn=lambda **_: (_ for _ in ()).throw(
                runner_shared.DriverError("binary missing")
            ),
            stdout=io.StringIO(),
            stderr=err,
        )
        assert rc_err == 2
        assert "binary missing" in err.getvalue()
        run_dirs_after = sorted(runs_root.iterdir())
        assert len(run_dirs_after) == 2
        new_dir = [d for d in run_dirs_after if d != run_dirs[0]][0]
        assert runner_shared.load_state(new_dir)["queue"][0]["status"] == "failed"


class TestHostDriversAndCliParity:
    def _write_profiles(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        store = tmp_path / "runner-profiles.json"
        store.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "defaults": {},
                    "profiles": {
                        "ocfast": {
                            "runner": "oc",
                            "model": "google/gemini-3-flash",
                            "variant": "high",
                            "agent": "build",
                        },
                        "agyfast": {
                            "runner": "agy",
                            "model": "google/gemini-4-carbon",
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(runner_profiles, "store_path", lambda: store)
        return store

    @pytest.mark.parametrize("host_token", ["oc", "opencode"])
    def test_oc_prompt_cli_forwarding_profile_session_flags_and_exit_code(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        host_token: str,
    ) -> None:
        repo = _init_git_repo(tmp_path)
        self._write_profiles(tmp_path, monkeypatch)
        calls: list[dict[str, Any]] = []

        def fake_run_opencode(
            state: dict[str, Any],
            run_dir: Path,
            item: dict[str, Any],
            plan_path: Path | None = None,
            prompt_path: Path | None = None,
            attempt_no: int = 1,
            **kwargs: Any,
        ) -> tuple[int, str | None, Path, list[str]]:
            assert prompt_path is not None
            calls.append(
                {
                    "state": state,
                    "item": item,
                    "plan_path": plan_path,
                    "prompt_text": prompt_path.read_text(encoding="utf-8"),
                    "attempt_no": attempt_no,
                    **kwargs,
                }
            )
            log_path = runner_shared.attempt_log_path(run_dir, item, attempt_no)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            return 0, "ses_oc_cli_1", log_path, ["opencode", "run"]

        monkeypatch.setattr(oc_runipd, "run_opencode", fake_run_opencode)

        rc = cli.main(
            [
                host_token,
                "prompt",
                "--repo",
                str(repo),
                "--as",
                "ocfast",
                "--session",
                "ses_test_existing",
                "--timeout",
                "120s",
                "--raw",
                "-vv",
                "--title-style",
                "short",
                "Check status",
            ]
        )
        assert rc == 0
        assert len(calls) == 1
        call = calls[0]
        assert call["plan_path"] is None
        assert call["prompt_text"] == "Check status"
        assert call["resume_session"] == "ses_test_existing"
        assert call["use_continue"] is False
        assert isinstance(call["tracker"], render_stream.StreamTracker)
        opts = call["state"]["options"]
        assert opts["model"] == "google/gemini-3-flash"
        assert opts["variant"] == "high"
        assert opts["agent"] == "build"
        assert opts["timeout"] == "120s"
        assert opts["output_mode"] == "raw"
        assert opts["verbosity"] == 2
        assert opts["title_style"] == "short"

        out = capsys.readouterr().out
        assert "Session ID: ses_oc_cli_1" in out
        assert "Run dir: .aw/records/runs/" in out

    @pytest.mark.parametrize("host_token", ["agy", "antigravity"])
    def test_agy_prompt_cli_forwarding_profile_file_continue_and_exit_code(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        host_token: str,
    ) -> None:
        repo = _init_git_repo(tmp_path)
        self._write_profiles(tmp_path, monkeypatch)
        prompt_file = tmp_path / "task.md"
        prompt_file.write_text(
            "<!-- aw-prompt: id=test -->\nRun quick check\n<!-- note -->\n",
            encoding="utf-8",
        )
        calls: list[dict[str, Any]] = []

        def fake_run_agy_turn(
            state: dict[str, Any],
            run_dir: Path,
            item: dict[str, Any],
            prompt_path: Path,
            attempt_no: int,
            session_id: str | None,
            use_continue: bool,
            **kwargs: Any,
        ) -> tuple[int, str | None, Path, list[str]]:
            calls.append(
                {
                    "state": state,
                    "item": item,
                    "prompt_text": prompt_path.read_text(encoding="utf-8"),
                    "attempt_no": attempt_no,
                    "session_id": session_id,
                    "use_continue": use_continue,
                    **kwargs,
                }
            )
            log_path = runner_shared.attempt_log_path(run_dir, item, attempt_no)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            return 7, "conv_agy_7", log_path, ["agy", "-p", "..."]

        monkeypatch.setattr(agy_runipd, "run_agy_turn", fake_run_agy_turn)

        rc = cli.main(
            [
                host_token,
                "prompt",
                "--repo",
                str(repo),
                "--as",
                "agyfast",
                "-c",
                "--quiet",
                "-v",
                "--effort",
                "high",
                "-f",
                str(prompt_file),
            ]
        )
        assert rc == 7
        assert len(calls) == 1
        call = calls[0]
        assert call["prompt_text"] == "Run quick check\n<!-- note -->\n"
        assert call["session_id"] is None
        assert call["use_continue"] is True
        assert isinstance(call["tracker"], render_stream.StreamTracker)
        opts = call["state"]["options"]
        assert opts["model"] == "google/gemini-4-carbon"
        assert opts["explicit_model"] == "google/gemini-4-carbon"
        assert opts["effort"] == "high"
        assert opts["output_mode"] == "quiet"
        assert opts["verbosity"] == 1

        out = capsys.readouterr().out
        assert "Session ID: conv_agy_7" in out
        assert "Run dir: .aw/records/runs/" in out

    def test_agy_prompt_falls_back_to_default_model_when_no_profile(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        repo = _init_git_repo(tmp_path)
        monkeypatch.setattr(
            runner_profiles, "store_path", lambda: tmp_path / "missing-profiles.json"
        )
        monkeypatch.setattr(
            agy_models,
            "resolve_agy_default_model",
            lambda: ("google/fallback-default", "settings.json"),
        )
        seen_opts: list[dict[str, Any]] = []

        def fake_run_agy_turn(
            state: dict[str, Any],
            run_dir: Path,
            item: dict[str, Any],
            prompt_path: Path,
            attempt_no: int,
            session_id: str | None,
            use_continue: bool,
            **kwargs: Any,
        ) -> tuple[int, str | None, Path, list[str]]:
            seen_opts.append(dict(state["options"]))
            log_path = runner_shared.attempt_log_path(run_dir, item, attempt_no)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            return 0, "conv_def", log_path, ["agy"]

        monkeypatch.setattr(agy_runipd, "run_agy_turn", fake_run_agy_turn)

        rc = agy_runipd.main_prompt(
            ["--repo", str(repo), "--session", "conv_1", "Hello"]
        )
        assert rc == 0
        assert seen_opts[0]["model"] == "google/fallback-default"
        assert seen_opts[0]["explicit_model"] is None

    def test_oc_and_agy_prompt_propagate_nonzero_and_unknown_profile(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        repo = _init_git_repo(tmp_path)
        self._write_profiles(tmp_path, monkeypatch)

        rc_oc = oc_runipd.main_prompt(
            ["--repo", str(repo), "--as", "does-not-exist", "Hi"]
        )
        assert rc_oc == 2
        assert "runner profile" in capsys.readouterr().err

        rc_agy = agy_runipd.main_prompt(
            ["--repo", str(repo), "--as", "does-not-exist", "Hi"]
        )
        assert rc_agy == 2
        assert "runner profile" in capsys.readouterr().err

        # Non-zero child exit propagation on oc
        def fake_oc_fail(
            state: dict[str, Any],
            run_dir: Path,
            item: dict[str, Any],
            plan_path: Path | None = None,
            prompt_path: Path | None = None,
            attempt_no: int = 1,
            **kwargs: Any,
        ) -> tuple[int, str | None, Path, list[str]]:
            log_path = runner_shared.attempt_log_path(run_dir, item, attempt_no)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            return 5, "ses_fail", log_path, ["opencode", "run"]

        monkeypatch.setattr(oc_runipd, "run_opencode", fake_oc_fail)
        rc_fail = oc_runipd.main_prompt(["--repo", str(repo), "Fail please"])
        assert rc_fail == 5

    def test_run_opencode_adhoc_argv_continue_omits_files_and_wires_timeout(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        repo = _init_git_repo(tmp_path)
        runbook = repo / "runbook.md"
        runbook.write_text("# runbook\n", encoding="utf-8")

        run_dir, state, item, prompt_path = runner_shared.initialize_adhoc_prompt_run(
            repo,
            host_labels=runner_shared.OC_HOST_LABELS,
            options={
                "opencode": "opencode",
                "model": "google/gemini-3-flash",
                "timeout": "120s",
                "output_mode": "quiet",
                "verbosity": 0,
                "auto": True,
            },
            prompt_text="Ad-hoc prompt body",
        )
        # Even if a runbook key exists in state, ad-hoc prompts must NOT attach it.
        state["runbook"] = str(runbook)

        captured_argv: list[list[str]] = []
        captured_timeout: list[float] = []

        class _FakeProc:
            pid = 999999
            stdout = iter([json.dumps({"sessionID": "ses_real_oc"}) + "\n"])

            def poll(self) -> int:
                return 0

            def wait(self) -> int:
                return 0

        class _FakeTurnBoundWatch:
            def __init__(
                self, *, reap: Any, is_alive: Any, max_turn_timeout: float
            ) -> None:
                captured_timeout.append(max_turn_timeout)

            def __enter__(self) -> _FakeTurnBoundWatch:
                return self

            def __exit__(self, *args: Any) -> None:
                return None

        monkeypatch.setattr(
            oc_runipd,
            "observe_opencode_policy",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            lane_containment,
            "record_host_posture",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            lane_containment,
            "TurnBoundWatch",
            _FakeTurnBoundWatch,
        )
        real_popen = subprocess.Popen

        def _fake_popen(argv: Any, *args: Any, **kwargs: Any) -> Any:
            argv_list = list(argv)
            if argv_list and argv_list[0] == "opencode":
                captured_argv.append(argv_list)
                return _FakeProc()
            return real_popen(argv, *args, **kwargs)

        monkeypatch.setattr(subprocess, "Popen", _fake_popen)

        rc, sid, _log_path, returned_argv = oc_runipd.run_opencode(
            state,
            run_dir,
            item,
            plan_path=None,
            prompt_path=prompt_path,
            attempt_no=1,
            use_continue=True,
            tracker=render_stream.StreamTracker(),
        )

        assert rc == 0
        assert sid == "ses_real_oc"
        assert len(captured_argv) == 1
        argv = captured_argv[0]
        assert argv == returned_argv
        assert "--continue" in argv
        assert "--session" not in argv
        assert "--file" not in argv
        assert str(runbook) not in argv
        assert argv[-2:] == ["--", "Ad-hoc prompt body"]
        assert captured_timeout == [lane_containment.driver_bound_for_host(120.0)]

    def test_run_agy_turn_emits_continue_and_session(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        repo = _init_git_repo(tmp_path)
        run_dir, state, item, prompt_path = runner_shared.initialize_adhoc_prompt_run(
            repo,
            host_labels=runner_shared.AGY_HOST_LABELS,
            options={
                "agy_executable": "/bin/true",
                "model": "google/gemini-4-carbon",
                "explicit_model": "google/gemini-4-carbon",
                "timeout": "120s",
                "output_mode": "quiet",
                "dangerously_skip_permissions": True,
            },
            prompt_text="Ad-hoc agy prompt",
        )
        captured_argv: list[list[str]] = []

        class _FakeProc:
            pid = 999998
            stdout = iter([json.dumps({"conversation_id": "conv_real_agy"}) + "\n"])

            def poll(self) -> int:
                return 0

            def wait(self) -> int:
                return 0

        monkeypatch.setattr(agy_runipd, "resolve_agy", lambda _: "agy")
        real_popen = subprocess.Popen

        def _fake_popen(argv: Any, *args: Any, **kwargs: Any) -> Any:
            argv_list = list(argv)
            if argv_list and argv_list[0] == "agy":
                captured_argv.append(argv_list)
                return _FakeProc()
            return real_popen(argv, *args, **kwargs)

        monkeypatch.setattr(subprocess, "Popen", _fake_popen)

        rc, sid, _log_path, returned_argv = agy_runipd.run_agy_turn(
            state,
            run_dir,
            item,
            prompt_path=prompt_path,
            attempt_no=1,
            session_id=None,
            use_continue=True,
            tracker=render_stream.StreamTracker(),
        )
        assert rc == 0
        assert sid == "conv_real_agy"
        assert returned_argv == captured_argv[0]
        assert "--continue" in returned_argv
        assert "--conversation" not in returned_argv
        assert "--model" in returned_argv
        assert "google/gemini-4-carbon" in returned_argv

    def test_help_forwarding_both_hosts(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc_oc:
            cli.main(["oc", "prompt", "--help"])
        assert exc_oc.value.code == 0
        oc_help = capsys.readouterr().out
        assert "usage: aw oc prompt" in oc_help
        assert "--isolate-worktree" in oc_help
        assert "--continue" in oc_help
        assert "--variant" in oc_help

        with pytest.raises(SystemExit) as exc_agy:
            cli.main(["agy", "prompt", "--help"])
        assert exc_agy.value.code == 0
        agy_help = capsys.readouterr().out
        assert "usage: aw agy prompt" in agy_help
        assert "--isolate-worktree" in agy_help
        assert "--continue" in agy_help
        assert "--effort" in agy_help
