# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""End-to-end tests for Set fixfirst promises (IPD iksylm, Order 08).

Validates E-01 through E-05 and V-01 through V-05:
1. Matrix: One scripted run per fix-it failure kind on both hosts (oc and agy)
   via the queue entrypoint mod.run_queue(run_dir, retry_incomplete=False),
   proving that every agent-caused failure reaches a fix-it turn and ends executed
   with exactly one correction spent on that kind's own counter (E-01, V-01).
2. Shared prompt rules and kind-specific evidence: Fix-it prompts delivered across
   all kinds contain prompt.count(FIX_IT_RULE_TEXT) == 1, 'attempt 1 of N', and the
   kind's own evidence (E-02, V-02).
3. Proposal continuation: Three-item run with proposal stopping item A, cascading
   dependent item B, and allowing independent item C to execute (E-03, V-03).
4. Abort set: Driver behavior on corrupt state.json (exit 2), non-abort of hook
   bypass with item 2 executing, and tool-identity mismatch item failure (E-04, V-04).
5. Spec cross-check: Spec 25kzda 5.5 table audit, ABORT_CLASSES agreement, and gap
   carriers filed (E-05, V-05).
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from agent_workflows import (
    agy_runipd,
    artifact_core,
    oc_runipd,
    render_stream,
    run_evidence,
    runner_shared,
    selectors,
)
from tests import support
from tests.support import coordinator_role
from tests.test_lane_rule_break_detection import (
    _PRE_COMMIT_SHIM_SOURCE,
    _SYSTEM_PRE_COMMIT_CONFIG,
)
from tests.test_turn_fix_it import (
    _make_test_repo,
    _passing_suite_check,
    _patch_host_launcher,
    _write_outcome_file,
    _write_plan,
)

_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))

ALL_CORRECTION_COUNTERS = (
    runner_shared.TURN_RETRY_COUNT_KEY,
    runner_shared.HOOK_FINALIZE_RETRY_COUNT_KEY,
    runner_shared.HOOK_INTEGRATION_RETRY_COUNT_KEY,
    runner_shared.COMBINED_RED_RETRY_COUNT_KEY,
    runner_shared.FINALIZE_RETRY_COUNT_KEY,
    runner_shared.UNTOOLED_STATUS_RETRY_COUNT_KEY,
    runner_shared.HOOK_BYPASS_RETRY_COUNT_KEY,
    runner_shared.VERIFICATION_RETRY_COUNT_KEY,
)


def _make_script(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def _setup_matrix_run(
    root: Path,
    mod: Any,
    id6: str,
    *,
    budget: int = 2,
    isolate: bool = True,
    pre_commit_cfg: str | None = None,
) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    repo = _make_test_repo(root / f"repo_{mod.__name__}_{id6}")
    if pre_commit_cfg:
        (repo / ".pre-commit-config.yaml").write_text(pre_commit_cfg, encoding="utf-8")
        subprocess.run(["git", "add", ".pre-commit-config.yaml"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "add pre-commit config"], cwd=repo, check=True
        )
    plan_file = _write_plan(repo, id6=id6)
    subprocess.run(["git", "add", ".aw"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "add plan"], cwd=repo, check=True)

    run_dir = root / f"run_{mod.__name__}_{id6}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(exist_ok=True)
    (run_dir / "prompts").mkdir(exist_ok=True)
    (run_dir / "logs").mkdir(exist_ok=True)

    item = {
        "id6": id6,
        "action": "execute",
        "setid": "fixfirst",
        "position": 1,
        "status": "queued",
        "attempts": [],
        "configured_file": str(plan_file.relative_to(repo)),
    }
    state = {
        "run_id": f"run_{id6}",
        "repo": str(repo),
        "options": {
            "auto": True,
            "no_audit": True,
            "no_verify": True,
            "retry_budget": budget,
            "isolate_worktree": isolate,
        },
        "queue": [item],
    }
    mod.save_state(run_dir, state)
    return repo, run_dir, state, item


def _locate_spec_25kzda(repo_root: Path) -> Path:
    """Locate spec 25kzda recursively under .aw/records/specs/ across any status subdirectory."""
    specs_dir = repo_root / ".aw" / "records" / "specs"
    matches = sorted(specs_dir.rglob("*-25kzda-*.spec.md"))
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly 1 spec matching *-25kzda-*.spec.md under {specs_dir}, "
            f"found {len(matches)}: {matches}"
        )
    return matches[0]


def _spec_5_5_owner_problems(spec_text: str, repo_root: Path) -> list[str]:
    """Check spec 25kzda Section 5.5 retry policy table for owner citations and resolution."""
    problems: list[str] = []
    start_idx = spec_text.find("### 5.5 Retry policy")
    if start_idx == -1:
        return ["Section '### 5.5 Retry policy' not found in spec text"]
    end_idx = spec_text.find("### 5.6", start_idx)
    if end_idx == -1:
        return ["Section '### 5.6' not found in spec text after '### 5.5'"]
    slice_text = spec_text[start_idx:end_idx]

    # (a) any of k8n97m, 120bhh, b8w5o6, 5j73i6 appears anywhere in the slice
    for stale_id in ("k8n97m", "120bhh", "b8w5o6", "5j73i6"):
        if stale_id in slice_text:
            problems.append(f"Stale owner ID `{stale_id}` found in §5.5 slice")

    # Extract retry-policy table rows (lines starting '| ' after header, excluding separator)
    in_table = False
    table_rows: list[str] = []
    for line in slice_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("| Spec Class | Disposition(s) |"):
            in_table = True
            continue
        if in_table:
            if not stripped.startswith("|"):
                break
            if re.match(r"^\|(\s*:?-+:?\s*\|)+$", stripped):
                continue
            table_rows.append(stripped)

    # (b), (c), (d)
    for row_line in table_rows:
        cells = [c.strip() for c in row_line.split("|")[1:-1]]
        if len(cells) < 5:
            continue
        spec_class = cells[0]
        notes_cell = cells[-1]

        # (b) backticked token matching artifact_core.ID6_RE in LAST cell
        # does not resolve via selectors.resolve to exactly one path for plans or backlog
        backticked_tokens = re.findall(r"`([^`]+)`", notes_cell)
        for token in backticked_tokens:
            if artifact_core.ID6_RE.match(token):
                p_res = selectors.resolve(
                    repo_root, "plans", token, allow=frozenset({selectors.MATCH_ID6})
                )
                b_res = selectors.resolve(
                    repo_root, "backlog", token, allow=frozenset({selectors.MATCH_ID6})
                )
                if len(p_res.paths) != 1 and len(b_res.paths) != 1:
                    problems.append(
                        f"Row '{spec_class}': token `{token}` does not resolve to exactly one path "
                        f"for plans or backlog (plans={len(p_res.paths)}, backlog={len(b_res.paths)})"
                    )

        # (c) for every Notes cell matching Order (\d\d), `(<id6>)`
        for m in re.finditer(r"Order\s+(\d\d),\s*`([0-9a-z]{6})`", notes_cell):
            order_num_str = m.group(1)
            cited_id = m.group(2)
            p_res = selectors.resolve(
                repo_root, "plans", cited_id, allow=frozenset({selectors.MATCH_ID6})
            )
            if len(p_res.paths) != 1:
                problems.append(
                    f"Row '{spec_class}': cited plan `{cited_id}` for Order {order_num_str} does not resolve to exactly 1 plan"
                )
                continue
            plan_path = p_res.paths[0]
            plan_text = plan_path.read_text(encoding="utf-8")
            m_order = re.search(r"^- Order:\s*(\S+)", plan_text, re.MULTILINE)
            if not m_order or int(m_order.group(1)) != int(order_num_str):
                actual_order = m_order.group(1) if m_order else "missing"
                problems.append(
                    f"Row '{spec_class}': Order mismatch for plan `{cited_id}`: table has {order_num_str}, plan has {actual_order}"
                )
            m_set = re.search(r"^- Set:\s*(\S+)", plan_text, re.MULTILINE)
            set_first_token = m_set.group(1).lstrip("`").rstrip("`") if m_set else ""
            if set_first_token != "fixfirst":
                problems.append(
                    f"Row '{spec_class}': plan `{cited_id}` has set '{set_first_token}', expected 'fixfirst'"
                )
            plan_status = selectors.read_front_matter_status(plan_text)
            if plan_status != "executed":
                problems.append(
                    f"Row '{spec_class}': plan `{cited_id}` has status '{plan_status}', expected 'executed'"
                )
            status_match = re.search(
                r"(Shipped|Implementing)\b[^\n`]*?Order\s+"
                + order_num_str
                + r",\s*`"
                + cited_id
                + r"`",
                notes_cell,
            )
            if status_match:
                if status_match.group(1) != "Shipped":
                    problems.append(
                        f"Row '{spec_class}': status phrase for Order {order_num_str}, `{cited_id}` starts with '{status_match.group(1)}', expected 'Shipped'"
                    )
            else:
                problems.append(
                    f"Row '{spec_class}': could not find status phrase 'Shipped' for Order {order_num_str}, `{cited_id}`"
                )

        # (d) the verifier transport failure row's Notes cell contains yd4tqw and jodcz3 and not ytas91
        if spec_class == "verifier transport failure":
            if "yd4tqw" not in notes_cell:
                problems.append(
                    "Row 'verifier transport failure': Notes cell missing 'yd4tqw'"
                )
            if "jodcz3" not in notes_cell:
                problems.append(
                    "Row 'verifier transport failure': Notes cell missing 'jodcz3'"
                )
            if "ytas91" in notes_cell:
                problems.append(
                    "Row 'verifier transport failure': Notes cell contains 'ytas91'"
                )

    return problems


class TestFixFirstEndToEnd(unittest.TestCase):
    """End-to-end matrix, continuation, and abort tests for Set fixfirst."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        if shutil.which("pre-commit") is None:
            bin_tmp = tempfile.TemporaryDirectory()
            self.addCleanup(bin_tmp.cleanup)
            bin_dir = Path(bin_tmp.name)
            shim_py = bin_dir / "_pre_commit_shim.py"
            shim_py.write_text(_PRE_COMMIT_SHIM_SOURCE, encoding="utf-8")
            posix_bin = bin_dir / "pre-commit"
            posix_bin.write_text(
                f"#!{sys.executable}\n" + _PRE_COMMIT_SHIM_SOURCE,
                encoding="utf-8",
            )
            posix_bin.chmod(posix_bin.stat().st_mode | stat.S_IEXEC)
            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"

            def _restore_path() -> None:
                os.environ["PATH"] = old_path

            self.addCleanup(_restore_path)

        self.suite_patchers = [
            mock.patch.object(runner_shared, "run_suite_check", _passing_suite_check),
            mock.patch.object(oc_runipd, "run_suite_check", _passing_suite_check),
            mock.patch.object(agy_runipd, "run_suite_check", _passing_suite_check),
        ]
        for p in self.suite_patchers:
            p.start()

    def tearDown(self) -> None:
        for p in reversed(self.suite_patchers):
            p.stop()
        self.temp_dir.cleanup()

    def _assert_counters_isolated(
        self, item: dict[str, Any], expected_key: str
    ) -> None:
        """Assert expected_key is 1 and all other correction counters are absent or 0."""
        self.assertEqual(
            item.get(expected_key),
            1,
            f"Expected counter {expected_key} == 1; got {item.get(expected_key)}",
        )
        for other_key in ALL_CORRECTION_COUNTERS:
            if other_key != expected_key:
                val = item.get(other_key, 0)
                self.assertTrue(
                    val is None or val == 0,
                    f"Counter {other_key} must be absent or 0, got {val}",
                )

    def _assert_v02_prompt(
        self,
        prompt: str,
        kind: str,
        host: str,
        evidence_substr: str,
    ) -> str:
        """Assert rule count, attempt marker, and kind evidence; print V-02 record."""
        rule_count = prompt.count(runner_shared.FIX_IT_RULE_TEXT)
        self.assertEqual(
            rule_count,
            1,
            f"FIX_IT_RULE_TEXT must appear exactly once in fix-it prompt (got {rule_count})",
        )
        self.assertIn(
            "attempt 1 of",
            prompt,
            "Fix-it prompt must carry 'attempt 1 of N'",
        )
        self.assertIn(
            evidence_substr,
            prompt,
            f"Prompt must contain evidence substring {evidence_substr!r}",
        )
        # Extract kind header line for evidence recording
        kind_line = ""
        for line in prompt.splitlines():
            if kind in line or "attempt 1 of" in line:
                kind_line = line.strip()
                break
        evidence_excerpt = evidence_substr[:80]
        print(
            f"[V-02] kind={kind} host={host} rule_count={rule_count} kind_line={kind_line!r} evidence={evidence_excerpt!r}"
        )
        return prompt

    # -------------------------------------------------------------------------
    # E-01 / E-02: Fix-It Matrix (9 kinds x 2 hosts = 18 tests)
    # -------------------------------------------------------------------------

    def _run_matrix_nonzero_exit(self, host_label: str, mod: Any) -> None:
        id6 = f"nze{host_label}"
        repo, run_dir, state, item = _setup_matrix_run(
            self.root, mod, id6, isolate=False
        )
        log_file = run_dir / "logs" / "attempt.log"
        log_file.write_text("crash log\n", encoding="utf-8")

        calls = [0]
        prompts_delivered: list[str] = []

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            calls[0] += 1
            if prompt_p and Path(prompt_p).is_file():
                prompts_delivered.append(Path(prompt_p).read_text(encoding="utf-8"))
            if calls[0] == 1:
                return 1, "ses1", log_file, ["cmd"]
            _write_outcome_file(rd, itm, disposition="executed")
            return 0, "ses1", log_file, ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(
            mod, "driver_finalize", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "assert_child_tool_identity", lambda *a, **k: None):
            rc = mod.run_queue(run_dir, retry_incomplete=False)

        self.assertEqual(rc, 0)
        final_item = mod.load_state(run_dir)["queue"][0]
        self.assertEqual(final_item["status"], "executed")
        self._assert_counters_isolated(final_item, runner_shared.TURN_RETRY_COUNT_KEY)
        self.assertGreaterEqual(len(prompts_delivered), 2)
        self._assert_v02_prompt(
            prompts_delivered[1],
            "nonzero_exit",
            host_label,
            "Exit code: 1",
        )
        print(
            f"[V-01] kind=nonzero_exit host={host_label} status={final_item['status']} "
            f"turn_retry_attempts={final_item.get(runner_shared.TURN_RETRY_COUNT_KEY)}"
        )

    def test_matrix_nonzero_exit_oc(self) -> None:
        self._run_matrix_nonzero_exit("oc", oc_runipd)

    def test_matrix_nonzero_exit_agy(self) -> None:
        self._run_matrix_nonzero_exit("agy", agy_runipd)

    def _run_matrix_stall(self, host_label: str, mod: Any) -> None:
        id6 = f"stl{host_label}"
        repo, run_dir, state, item = _setup_matrix_run(
            self.root, mod, id6, isolate=False
        )
        log_file = run_dir / "logs" / "attempt.log"
        log_file.write_text("stall log\n", encoding="utf-8")

        calls = [0]
        prompts_delivered: list[str] = []

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            calls[0] += 1
            if prompt_p and Path(prompt_p).is_file():
                prompts_delivered.append(Path(prompt_p).read_text(encoding="utf-8"))
            if calls[0] == 1:
                raise runner_shared.StallTimeout("host watchdog stall timeout")
            _write_outcome_file(rd, itm, disposition="executed")
            return 0, "ses1", log_file, ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(
            mod, "driver_finalize", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "assert_child_tool_identity", lambda *a, **k: None):
            rc = mod.run_queue(run_dir, retry_incomplete=False)

        self.assertEqual(rc, 0)
        final_item = mod.load_state(run_dir)["queue"][0]
        self.assertEqual(final_item["status"], "executed")
        self._assert_counters_isolated(final_item, runner_shared.TURN_RETRY_COUNT_KEY)
        self.assertGreaterEqual(len(prompts_delivered), 2)
        self._assert_v02_prompt(
            prompts_delivered[1],
            "stall",
            host_label,
            "Failure kind: stall",
        )
        print(
            f"[V-01] kind=stall host={host_label} status={final_item['status']} "
            f"turn_retry_attempts={final_item.get(runner_shared.TURN_RETRY_COUNT_KEY)}"
        )

    def test_matrix_stall_oc(self) -> None:
        self._run_matrix_stall("oc", oc_runipd)

    def test_matrix_stall_agy(self) -> None:
        self._run_matrix_stall("agy", agy_runipd)

    def _run_matrix_spawn_failure(self, host_label: str, mod: Any) -> None:
        id6 = f"spn{host_label}"
        repo, run_dir, state, item = _setup_matrix_run(
            self.root, mod, id6, isolate=False
        )
        log_file = run_dir / "logs" / "attempt.log"
        log_file.write_text("spawn log\n", encoding="utf-8")

        calls = [0]
        prompts_delivered: list[str] = []

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            calls[0] += 1
            if prompt_p and Path(prompt_p).is_file():
                prompts_delivered.append(Path(prompt_p).read_text(encoding="utf-8"))
            if calls[0] == 1:
                raise runner_shared.HostSpawnError(
                    "cannot spawn host binary: /usr/bin/missing_binary"
                )
            _write_outcome_file(rd, itm, disposition="executed")
            return 0, "ses1", log_file, ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(
            mod, "driver_finalize", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "assert_child_tool_identity", lambda *a, **k: None):
            rc = mod.run_queue(run_dir, retry_incomplete=False)

        self.assertEqual(rc, 0)
        final_item = mod.load_state(run_dir)["queue"][0]
        self.assertEqual(final_item["status"], "executed")
        self._assert_counters_isolated(final_item, runner_shared.TURN_RETRY_COUNT_KEY)
        self.assertGreaterEqual(len(prompts_delivered), 2)
        self._assert_v02_prompt(
            prompts_delivered[1],
            "spawn_failure",
            host_label,
            "cannot spawn host binary",
        )
        print(
            f"[V-01] kind=spawn_failure host={host_label} status={final_item['status']} "
            f"turn_retry_attempts={final_item.get(runner_shared.TURN_RETRY_COUNT_KEY)}"
        )

    def test_matrix_spawn_failure_oc(self) -> None:
        self._run_matrix_spawn_failure("oc", oc_runipd)

    def test_matrix_spawn_failure_agy(self) -> None:
        self._run_matrix_spawn_failure("agy", agy_runipd)

    def _run_matrix_hook_refusal_finalize(self, host_label: str, mod: Any) -> None:
        id6 = f"hkf{host_label}"
        repo, run_dir, state, item = _setup_matrix_run(
            self.root, mod, id6, isolate=False
        )
        log_file = run_dir / "logs" / "attempt.log"
        log_file.write_text("hook finalize log\n", encoding="utf-8")

        fin_calls = [0]
        prompts_delivered: list[str] = []

        def fake_finalize(*a: Any, **k: Any) -> tuple[int, str]:
            fin_calls[0] += 1
            if fin_calls[0] == 1:
                return (
                    1,
                    "error: lifecycle commit did not happen (git rc=1: the lifecycle commit was rejected "
                    "in the coordinator worktree (hooks ran): HOOK_ERROR: trailing whitespace in plan.ipd.md); "
                    "rolled back to pre-finalize state.",
                )
            return 0, "ok"

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            if prompt_p and Path(prompt_p).is_file():
                prompts_delivered.append(Path(prompt_p).read_text(encoding="utf-8"))
            _write_outcome_file(rd, itm, disposition="executed")
            return 0, "ses1", log_file, ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "driver_finalize", fake_finalize), mock.patch.object(
            mod, "assert_child_tool_identity", lambda *a, **k: None
        ):
            rc = mod.run_queue(run_dir, retry_incomplete=False)

        self.assertEqual(rc, 0)
        final_item = mod.load_state(run_dir)["queue"][0]
        self.assertEqual(final_item["status"], "executed")
        self._assert_counters_isolated(
            final_item, runner_shared.HOOK_FINALIZE_RETRY_COUNT_KEY
        )
        self.assertGreaterEqual(len(prompts_delivered), 2)
        self._assert_v02_prompt(
            prompts_delivered[1],
            "hook_refusal_finalize",
            host_label,
            "HOOK_ERROR: trailing whitespace in plan.ipd.md",
        )
        print(
            f"[V-01] kind=hook_refusal_finalize host={host_label} status={final_item['status']} "
            f"hook_finalize_retry_attempts={final_item.get(runner_shared.HOOK_FINALIZE_RETRY_COUNT_KEY)}"
        )

    def test_matrix_hook_refusal_finalize_oc(self) -> None:
        self._run_matrix_hook_refusal_finalize("oc", oc_runipd)

    def test_matrix_hook_refusal_finalize_agy(self) -> None:
        self._run_matrix_hook_refusal_finalize("agy", agy_runipd)

    def _run_matrix_hook_refusal_integration(self, host_label: str, mod: Any) -> None:
        id6 = f"hki{host_label}"
        repo, run_dir, state, item = _setup_matrix_run(
            self.root, mod, id6, isolate=True
        )
        hooks_dir = repo / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        count_file = self.root / f"merge_cnt_{id6}.txt"
        count_file.write_text("0", encoding="utf-8")

        hook_sh = (
            "#!/usr/bin/env bash\n"
            f'cnt=$(cat "{count_file.as_posix()}" 2>/dev/null || echo 0)\n'
            'if [ "$cnt" -lt 1 ]; then\n'
            f'    echo $((cnt + 1)) > "{count_file.as_posix()}"\n'
            '    echo "HOOK_MERGE_FAIL: integration hook rejected commit" >&2\n'
            "    exit 1\n"
            "fi\n"
            "exit 0\n"
        )
        _make_script(hooks_dir / "pre-merge-commit", hook_sh)

        prompts_delivered: list[str] = []
        turn_calls = [0]

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            turn_calls[0] += 1
            if prompt_p and Path(prompt_p).is_file():
                prompts_delivered.append(Path(prompt_p).read_text(encoding="utf-8"))
            work_dir = Path(kw.get("work_dir") or st["repo"])
            (work_dir / "touch.txt").write_text(
                f"touched attempt {turn_calls[0]}\n", encoding="utf-8"
            )
            subprocess.run(["git", "add", "touch.txt"], cwd=work_dir, check=True)
            subprocess.run(
                ["git", "commit", "-qm", f"touch commit {turn_calls[0]}"],
                cwd=work_dir,
                check=True,
            )

            if turn_calls[0] == 1:
                # Advance main non-conflictingly so fast-forward is impossible and merge commit runs pre-merge-commit
                (repo / "main_advance.txt").write_text("advance\n", encoding="utf-8")
                subprocess.run(["git", "add", "main_advance.txt"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "main advance"], cwd=repo, check=True
                )

            _write_outcome_file(rd, itm, disposition="executed")
            return 0, "ses1", rd / "log", ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(
            mod, "driver_finalize", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "assert_child_tool_identity", lambda *a, **k: None):
            rc = mod.run_queue(run_dir, retry_incomplete=False)

        self.assertEqual(rc, 0)
        final_item = mod.load_state(run_dir)["queue"][0]
        self.assertEqual(final_item["status"], "executed")
        self._assert_counters_isolated(
            final_item, runner_shared.HOOK_INTEGRATION_RETRY_COUNT_KEY
        )
        self.assertGreaterEqual(len(prompts_delivered), 2)
        self._assert_v02_prompt(
            prompts_delivered[1],
            "hook_refusal_integration",
            host_label,
            "HOOK_MERGE_FAIL: integration hook rejected commit",
        )
        print(
            f"[V-01] kind=hook_refusal_integration host={host_label} status={final_item['status']} "
            f"hook_integration_retry_attempts={final_item.get(runner_shared.HOOK_INTEGRATION_RETRY_COUNT_KEY)}"
        )

    def test_matrix_hook_refusal_integration_oc(self) -> None:
        self._run_matrix_hook_refusal_integration("oc", oc_runipd)

    def test_matrix_hook_refusal_integration_agy(self) -> None:
        self._run_matrix_hook_refusal_integration("agy", agy_runipd)

    def _run_matrix_red_merged_suite(self, host_label: str, mod: Any) -> None:
        id6 = f"rms{host_label}"
        repo, run_dir, state, item = _setup_matrix_run(
            self.root, mod, id6, isolate=True
        )

        reval_calls = [0]

        def fake_reval_factory(
            st: Any, rd: Any, item_arg: Any, suite_check: Any = None
        ) -> Any:
            def runner_fn(lane_dir: Any, candidate_files: Any) -> bool:
                reval_calls[0] += 1
                if reval_calls[0] == 1:
                    runner_shared._record_revalidation(
                        item_arg,
                        tree_id="tree_red",
                        passed=False,
                        reason="1 new failure",
                        failures=["tests/test_demo.py::test_case_failed"],
                        merged_files=["touch.txt"],
                        measured=True,
                    )
                    return False
                runner_shared._record_revalidation(
                    item_arg,
                    tree_id="tree_green",
                    passed=True,
                    reason="green",
                    failures=[],
                    merged_files=["touch.txt"],
                    measured=True,
                )
                return True

            return runner_fn

        prompts_delivered: list[str] = []
        turn_calls = [0]

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            turn_calls[0] += 1
            if prompt_p and Path(prompt_p).is_file():
                prompts_delivered.append(Path(prompt_p).read_text(encoding="utf-8"))
            work_dir = Path(kw.get("work_dir") or st["repo"])
            (work_dir / "touch.txt").write_text(
                f"touched attempt {turn_calls[0]}\n", encoding="utf-8"
            )
            subprocess.run(["git", "add", "touch.txt"], cwd=work_dir, check=True)
            subprocess.run(
                ["git", "commit", "-qm", f"touch commit {turn_calls[0]}"],
                cwd=work_dir,
                check=True,
            )
            _write_outcome_file(rd, itm, disposition="executed")
            return 0, "ses1", rd / "log", ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "make_integration_validation_runner", fake_reval_factory
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(
            mod, "driver_finalize", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "assert_child_tool_identity", lambda *a, **k: None):
            rc = mod.run_queue(run_dir, retry_incomplete=False)

        self.assertEqual(rc, 0)
        final_item = mod.load_state(run_dir)["queue"][0]
        self.assertEqual(final_item["status"], "executed")
        self._assert_counters_isolated(
            final_item, runner_shared.COMBINED_RED_RETRY_COUNT_KEY
        )
        self.assertGreaterEqual(len(prompts_delivered), 2)
        self._assert_v02_prompt(
            prompts_delivered[1],
            "red_merged_suite",
            host_label,
            "tests/test_demo.py::test_case_failed",
        )
        print(
            f"[V-01] kind=red_merged_suite host={host_label} status={final_item['status']} "
            f"combined_red_retry_attempts={final_item.get(runner_shared.COMBINED_RED_RETRY_COUNT_KEY)}"
        )

    def test_matrix_red_merged_suite_oc(self) -> None:
        self._run_matrix_red_merged_suite("oc", oc_runipd)

    def test_matrix_red_merged_suite_agy(self) -> None:
        self._run_matrix_red_merged_suite("agy", agy_runipd)

    def _run_matrix_out_of_scope_edit(self, host_label: str, mod: Any) -> None:
        id6 = f"oos{host_label}"
        repo, run_dir, state, item = _setup_matrix_run(
            self.root, mod, id6, isolate=True
        )

        fin_calls = [0]

        def fake_finalize(*a: Any, **k: Any) -> tuple[int, str]:
            fin_calls[0] += 1
            if fin_calls[0] == 1:
                return (
                    1,
                    "refused: finalize needs scope reconciliation answers (plan left unmoved).\n"
                    "  IPD-FINALIZE out-of-scope path needs a --scope-reason: src/demo_extra.py",
                )
            return 0, "ok"

        prompts_delivered: list[str] = []

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            if prompt_p and Path(prompt_p).is_file():
                prompts_delivered.append(Path(prompt_p).read_text(encoding="utf-8"))
            work_dir = Path(kw.get("work_dir") or st["repo"])
            (work_dir / "src").mkdir(parents=True, exist_ok=True)
            (work_dir / "src" / "demo.txt").write_text("in-scope\n", encoding="utf-8")
            subprocess.run(["git", "add", "src/demo.txt"], cwd=work_dir, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "scope edit"], cwd=work_dir, check=True
            )
            _write_outcome_file(rd, itm, disposition="executed")
            return 0, "ses1", rd / "log", ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "driver_finalize", fake_finalize), mock.patch.object(
            mod, "assert_child_tool_identity", lambda *a, **k: None
        ):
            rc = mod.run_queue(run_dir, retry_incomplete=False)

        self.assertEqual(rc, 0)
        final_item = mod.load_state(run_dir)["queue"][0]
        self.assertEqual(final_item["status"], "executed")
        self._assert_counters_isolated(
            final_item, runner_shared.FINALIZE_RETRY_COUNT_KEY
        )
        self.assertGreaterEqual(len(prompts_delivered), 2)
        self._assert_v02_prompt(
            prompts_delivered[1],
            "out_of_scope_edit",
            host_label,
            "src/demo_extra.py",
        )
        print(
            f"[V-01] kind=out_of_scope_edit host={host_label} status={final_item['status']} "
            f"finalize_retry_attempts={final_item.get(runner_shared.FINALIZE_RETRY_COUNT_KEY)}"
        )

    def test_matrix_out_of_scope_edit_oc(self) -> None:
        self._run_matrix_out_of_scope_edit("oc", oc_runipd)

    def test_matrix_out_of_scope_edit_agy(self) -> None:
        self._run_matrix_out_of_scope_edit("agy", agy_runipd)

    def _run_matrix_untooled_status_change(self, host_label: str, mod: Any) -> None:
        id6 = f"uts{host_label}"
        repo, run_dir, state, item = _setup_matrix_run(
            self.root, mod, id6, isolate=True
        )

        calls = [0]
        prompts_delivered: list[str] = []

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            calls[0] += 1
            if prompt_p and Path(prompt_p).is_file():
                prompts_delivered.append(Path(prompt_p).read_text(encoding="utf-8"))
            work_dir = Path(kw.get("work_dir") or st["repo"])
            plan_file = next(
                (work_dir / ".aw" / "records" / "plans" / "pending").glob(f"*{id6}*")
            )
            if calls[0] == 1:
                # Hand-edit status without history line
                text = plan_file.read_text(encoding="utf-8").replace(
                    "- Status: approved", "- Status: to-review"
                )
                plan_file.write_text(text, encoding="utf-8")
                subprocess.run(
                    ["git", "commit", "-qam", "hand-edit status"],
                    cwd=work_dir,
                    check=True,
                )
            else:
                # Revert hand edit
                text = plan_file.read_text(encoding="utf-8").replace(
                    "- Status: to-review", "- Status: approved"
                )
                plan_file.write_text(text, encoding="utf-8")
                (work_dir / "src").mkdir(parents=True, exist_ok=True)
                (work_dir / "src" / "demo.txt").write_text("clean\n", encoding="utf-8")
                subprocess.run(["git", "add", "."], cwd=work_dir, check=True)
                subprocess.run(
                    ["git", "commit", "-qam", "revert hand-edit"],
                    cwd=work_dir,
                    check=True,
                )

            _write_outcome_file(rd, itm, disposition="executed")
            return 0, "ses1", rd / "log", ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(
            mod, "driver_finalize", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "assert_child_tool_identity", lambda *a, **k: None):
            rc = mod.run_queue(run_dir, retry_incomplete=False)

        self.assertEqual(rc, 0)
        final_item = mod.load_state(run_dir)["queue"][0]
        self.assertEqual(final_item["status"], "executed")
        self._assert_counters_isolated(
            final_item, runner_shared.UNTOOLED_STATUS_RETRY_COUNT_KEY
        )
        self.assertGreaterEqual(len(prompts_delivered), 2)
        self._assert_v02_prompt(
            prompts_delivered[1],
            "untooled_status_change",
            host_label,
            id6,
        )
        print(
            f"[V-01] kind=untooled_status_change host={host_label} status={final_item['status']} "
            f"untooled_status_retry_attempts={final_item.get(runner_shared.UNTOOLED_STATUS_RETRY_COUNT_KEY)}"
        )

    def test_matrix_untooled_status_change_oc(self) -> None:
        self._run_matrix_untooled_status_change("oc", oc_runipd)

    def test_matrix_untooled_status_change_agy(self) -> None:
        self._run_matrix_untooled_status_change("agy", agy_runipd)

    def _run_matrix_hook_skipping_commit(self, host_label: str, mod: Any) -> None:
        id6 = f"hsk{host_label}"
        repo, run_dir, state, item = _setup_matrix_run(
            self.root, mod, id6, isolate=True, pre_commit_cfg=_SYSTEM_PRE_COMMIT_CONFIG
        )

        calls = [0]
        prompts_delivered: list[str] = []

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            calls[0] += 1
            if prompt_p and Path(prompt_p).is_file():
                prompts_delivered.append(Path(prompt_p).read_text(encoding="utf-8"))
            work_dir = Path(kw.get("work_dir") or st["repo"])
            if calls[0] == 1:
                # Bypass commit past failing hook
                (work_dir / "bad.txt").write_text("REFUSE_HOOK\n", encoding="utf-8")
                subprocess.run(["git", "add", "bad.txt"], cwd=work_dir, check=True)
                subprocess.run(
                    ["git", "commit", "--no-verify", "-qm", "bypass commit"],
                    cwd=work_dir,
                    check=True,
                )
            else:
                # Clean commit passing hook
                if (work_dir / "bad.txt").exists():
                    subprocess.run(
                        ["git", "rm", "-f", "bad.txt"], cwd=work_dir, check=True
                    )
                (work_dir / "clean.txt").write_text("ALL_GOOD\n", encoding="utf-8")
                subprocess.run(["git", "add", "clean.txt"], cwd=work_dir, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "clean commit"], cwd=work_dir, check=True
                )

            _write_outcome_file(rd, itm, disposition="executed")
            return 0, "ses1", rd / "log", ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(
            mod, "driver_finalize", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "assert_child_tool_identity", lambda *a, **k: None):
            rc = mod.run_queue(run_dir, retry_incomplete=False)

        self.assertEqual(rc, 0)
        final_item = mod.load_state(run_dir)["queue"][0]
        self.assertEqual(final_item["status"], "executed")
        self._assert_counters_isolated(
            final_item, runner_shared.HOOK_BYPASS_RETRY_COUNT_KEY
        )
        self.assertGreaterEqual(len(prompts_delivered), 2)
        self._assert_v02_prompt(
            prompts_delivered[1],
            "hook_skipping_commit",
            host_label,
            "refuse-content",
        )
        print(
            f"[V-01] kind=hook_skipping_commit host={host_label} status={final_item['status']} "
            f"hook_bypass_retry_attempts={final_item.get(runner_shared.HOOK_BYPASS_RETRY_COUNT_KEY)}"
        )

    def test_matrix_hook_skipping_commit_oc(self) -> None:
        self._run_matrix_hook_skipping_commit("oc", oc_runipd)

    def test_matrix_hook_skipping_commit_agy(self) -> None:
        self._run_matrix_hook_skipping_commit("agy", agy_runipd)

    def _run_matrix_verifier_transport_error(self, host_label: str, mod: Any) -> None:
        id6 = f"vte{host_label}"
        repo, run_dir, state, item = _setup_matrix_run(
            self.root, mod, id6, isolate=False
        )
        state["options"]["no_verify"] = False
        state["options"]["validate"] = True
        mod.save_state(run_dir, state)

        log_file = run_dir / "logs" / "attempt.log"
        log_file.write_text("verifier transport log\n", encoding="utf-8")

        verify_calls = [0]
        executor_prompts: list[str] = []

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            is_verify = bool(
                kw.get("fresh_session") or kw.get("log_suffix") == "verify"
            )
            if not is_verify and prompt_p and Path(prompt_p).is_file():
                executor_prompts.append(Path(prompt_p).read_text(encoding="utf-8"))

            if is_verify:
                verify_calls[0] += 1
                if verify_calls[0] == 1:
                    raise runner_shared.HostSpawnError(
                        "cannot spawn verifier binary: /usr/bin/missing_binary"
                    )
                v_outcome = {
                    "verdict": "VERIFIED",
                    "tests_run": ["python3 -m pytest tests/test_demo.py"],
                }
                v_file = (
                    rd
                    / "outcomes"
                    / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                )
                v_file.write_text(json.dumps(v_outcome), encoding="utf-8")
                return 0, "vses2", log_file, ["cmd"]

            _write_outcome_file(rd, itm, disposition="executed")
            return 0, "ses1", log_file, ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(
            mod, "driver_finalize", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "assert_child_tool_identity", lambda *a, **k: None):
            rc = mod.run_queue(run_dir, retry_incomplete=False)

        self.assertEqual(rc, 0)
        final_item = mod.load_state(run_dir)["queue"][0]
        self.assertEqual(final_item["status"], "executed")
        self._assert_counters_isolated(
            final_item, runner_shared.VERIFICATION_RETRY_COUNT_KEY
        )
        self.assertGreaterEqual(len(executor_prompts), 2)
        self._assert_v02_prompt(
            executor_prompts[1],
            "verifier_transport_error",
            host_label,
            "verifier-transport-error",
        )
        print(
            f"[V-01] kind=verifier_transport_error host={host_label} status={final_item['status']} "
            f"verification_retry_attempts={final_item.get(runner_shared.VERIFICATION_RETRY_COUNT_KEY)}"
        )

    def test_matrix_verifier_transport_error_oc(self) -> None:
        self._run_matrix_verifier_transport_error("oc", oc_runipd)

    def test_matrix_verifier_transport_error_agy(self) -> None:
        self._run_matrix_verifier_transport_error("agy", agy_runipd)

    # -------------------------------------------------------------------------
    # E-03: Proposal Continuation (2 tests: oc and agy)
    # -------------------------------------------------------------------------

    def _run_proposal_continuation(self, host_label: str, mod: Any) -> None:
        repo = _make_test_repo(self.root / f"repo_prop_{host_label}")
        planA = _write_plan(repo, id6=f"prp1{host_label}", order=1)
        planB = _write_plan(repo, id6=f"prp2{host_label}", order=2)
        # B depends on A
        b_text = planB.read_text(encoding="utf-8").replace(
            "Item-Dependencies: none", f"Item-Dependencies: executed:prp1{host_label}"
        )
        planB.write_text(b_text, encoding="utf-8")
        planC = _write_plan(repo, id6=f"prp3{host_label}", order=3)
        subprocess.run(["git", "add", ".aw"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

        run_dir = self.root / f"run_prop_{host_label}"
        run_dir.mkdir(parents=True)

        idA = f"prp1{host_label}"
        idB = f"prp2{host_label}"
        idC = f"prp3{host_label}"

        itemA = {
            "id6": idA,
            "action": "execute",
            "setid": "fixfirst",
            "position": 1,
            "status": "queued",
            "attempts": [],
            "configured_file": str(planA.relative_to(repo)),
        }
        itemB = {
            "id6": idB,
            "action": "execute",
            "setid": "fixfirst",
            "position": 2,
            "status": "queued",
            "attempts": [],
            "configured_file": str(planB.relative_to(repo)),
            "dependencies": [f"executed:{idA}"],
        }
        itemC = {
            "id6": idC,
            "action": "execute",
            "setid": "fixfirst",
            "position": 3,
            "status": "queued",
            "attempts": [],
            "configured_file": str(planC.relative_to(repo)),
        }

        state = {
            "run_id": f"run_prop_{host_label}",
            "repo": str(repo),
            "options": {
                "auto": True,
                "no_audit": True,
                "no_verify": True,
                "retry_budget": 2,
                "isolate_worktree": True,
            },
            "queue": [itemA, itemB, itemC],
        }
        mod.save_state(run_dir, state)

        dispatched = []

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            dispatched.append(itm["id6"])
            if itm["id6"] == idA:
                rec_p = rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                rec_p.parent.mkdir(parents=True, exist_ok=True)
                rec_p.write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "run_id": f"run_prop_{host_label}",
                            "position": 1,
                            "id6": idA,
                            "setid": "fixfirst",
                            "disposition": "failed-safely",
                            "summary": "proposal demo",
                            "starting_head": "0" * 40,
                            "ending_head": "0" * 40,
                            "commits": [],
                            "files_changed": [],
                            "tests": [],
                            "decision_ids": [],
                            "deferred_question_ids": [],
                            "incomplete_requirements": [],
                            "defect_report": {"state": "none-found", "findings": []},
                            "proposal": {
                                "kind": "tool-defect",
                                "blocked_by": "tool gate defect",
                                "why": "cannot fix in scope",
                                "proposed_change": "update tool",
                                "paths": ["src/tool.py"],
                                "size": "material",
                            },
                            "partial_work_location": None,
                            "recommended_next_action": "review proposal",
                            "pushed": False,
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "s1", rd / "log", ["cmd"]
            elif itm["id6"] == idC:
                _write_outcome_file(rd, itm, disposition="executed")
                return 0, "s3", rd / "log", ["cmd"]
            return 0, "sX", rd / "log", ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(
            mod, "driver_finalize", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "assert_child_tool_identity", lambda *a, **k: None):
            exit_code = mod.run_queue(run_dir, retry_incomplete=False)

        # 1. Exit code is 3 (needs-input / gate answer needs human)
        self.assertEqual(exit_code, 3, f"Run exit code must be 3, got {exit_code}")

        final_state = mod.load_state(run_dir)
        items_by_id = {it["id6"]: it for it in final_state["queue"]}
        finalA = items_by_id[idA]
        finalB = items_by_id[idB]
        finalC = items_by_id[idC]

        # 2. Statuses and refusal codes
        self.assertEqual(finalA["status"], "fail-gate")
        self.assertEqual(
            finalA.get("refusal", {}).get("code"),
            render_stream.GATE_ANSWER_NEEDS_HUMAN_CODE,
        )
        self.assertTrue(finalA.get(runner_shared.NEEDS_INPUT_KEY))

        self.assertIn(finalB["status"], ("fail-depend", "dependency-blocked"))
        self.assertEqual(len(finalB.get("attempts", [])), 0)
        self.assertNotIn(idB, dispatched)

        self.assertEqual(finalC["status"], "executed")

        # 3. Main branch contains exactly one proposal record; lane tip branch does not contain main
        log_out = subprocess.check_output(
            ["git", "log", "-1", "--name-status", "main"], cwd=repo, text=True
        )
        self.assertIn(".agents/backlog/open", log_out)

        lane_tip_branch = f"aw/lane/{idA}"
        contains_out = subprocess.run(
            ["git", "branch", "--contains", lane_tip_branch],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        self.assertNotIn("main", contains_out.stdout)

        # 4. Rendered summary block for A begins with proposal:
        rendered_text = render_stream.render_run_summary_table(final_state)
        self.assertIn("proposal:", rendered_text)
        self.assertIn(idA, rendered_text)

        print(
            f"[V-03] host={host_label} exit_code={exit_code} statusA={finalA['status']} "
            f"refusalA={finalA.get('refusal', {}).get('code')} statusB={finalB['status']} "
            f"statusC={finalC['status']}"
        )

    def test_proposal_continuation_oc(self) -> None:
        self._run_proposal_continuation("oc", oc_runipd)

    def test_proposal_continuation_agy(self) -> None:
        self._run_proposal_continuation("agy", agy_runipd)

    # -------------------------------------------------------------------------
    # E-04: Abort Set Tests (6 tests: corrupt state, non-abort, tool identity)
    # -------------------------------------------------------------------------

    def _run_corrupt_state(self, host_label: str, mod: Any) -> None:
        repo = self.root / f"repo_crp_{host_label}"
        repo.mkdir()
        run_dir = self.root / f"run_crp_{host_label}"
        run_dir.mkdir()
        (run_dir / "state.json").write_text("{corrupt json", encoding="utf-8")

        stderr_io = io.StringIO()
        with coordinator_role(), mock.patch("sys.stderr", stderr_io):
            rc = mod.main(["resume", str(run_dir), "--repo", str(repo)])

        # Measured: exits 2 with DriverError naming state.json, not exit 4
        self.assertEqual(rc, 2)
        err_msg = stderr_io.getvalue().strip()
        self.assertIn("state.json", err_msg)
        self.assertIn("Invalid JSON", err_msg)
        print(f"[V-04-a] host={host_label} corrupt_state rc={rc} stderr={err_msg!r}")

    def test_corrupt_state_oc(self) -> None:
        self._run_corrupt_state("oc", oc_runipd)

    def test_corrupt_state_agy(self) -> None:
        self._run_corrupt_state("agy", agy_runipd)

    def _run_non_abort_hook_bypass(self, host_label: str, mod: Any) -> None:
        repo = _make_test_repo(self.root / f"repo_nab_{host_label}")
        (repo / ".pre-commit-config.yaml").write_text(
            _SYSTEM_PRE_COMMIT_CONFIG, encoding="utf-8"
        )
        id1 = f"nb1{host_label}"
        id2 = f"nb2{host_label}"
        plan1 = _write_plan(repo, id6=id1, order=1)
        plan2 = _write_plan(repo, id6=id2, order=2)
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

        run_dir = self.root / f"run_nab_{host_label}"
        run_dir.mkdir(parents=True)
        item1 = {
            "id6": id1,
            "action": "execute",
            "setid": "fixfirst",
            "position": 1,
            "status": "queued",
            "attempts": [],
            "configured_file": str(plan1.relative_to(repo)),
        }
        item2 = {
            "id6": id2,
            "action": "execute",
            "setid": "fixfirst",
            "position": 2,
            "status": "queued",
            "attempts": [],
            "configured_file": str(plan2.relative_to(repo)),
        }
        state = {
            "run_id": f"run_nab_{host_label}",
            "repo": str(repo),
            "options": {
                "auto": True,
                "no_audit": True,
                "no_verify": True,
                "retry_budget": 0,
                "isolate_worktree": True,
            },
            "queue": [item1, item2],
        }
        mod.save_state(run_dir, state)

        def fake_turn(
            st: Any, rd: Any, itm: Any, plan_p: Any, prompt_p: Any, att: Any, **kw: Any
        ) -> Any:
            target_dir = Path(kw.get("work_dir") or st["repo"])
            if itm["id6"] == id1:
                (target_dir / "bad.txt").write_text("REFUSE_HOOK\n", encoding="utf-8")
                subprocess.run(["git", "add", "bad.txt"], cwd=target_dir, check=True)
                subprocess.run(
                    ["git", "commit", "--no-verify", "-qm", "bypass"],
                    cwd=target_dir,
                    check=True,
                )
                _write_outcome_file(rd, itm, disposition="executed")
                return 0, "s1", rd / "log", ["cmd"]
            else:
                (target_dir / "good.txt").write_text("OK\n", encoding="utf-8")
                subprocess.run(["git", "add", "good.txt"], cwd=target_dir, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "clean"], cwd=target_dir, check=True
                )
                _write_outcome_file(rd, itm, disposition="executed")
                return 0, "s2", rd / "log", ["cmd"]

        with coordinator_role(), _patch_host_launcher(
            mod, fake_turn
        ), mock.patch.object(
            mod, "driver_begin", lambda *a, **k: (0, "ok")
        ), mock.patch.object(
            mod, "driver_finalize", lambda *a, **k: (0, "ok")
        ), mock.patch.object(mod, "assert_child_tool_identity", lambda *a, **k: None):
            rc = mod.run_queue(run_dir, retry_incomplete=False)

        final_state = mod.load_state(run_dir)
        items = {it["id6"]: it for it in final_state["queue"]}
        self.assertEqual(items[id1]["status"], "failed-safely")
        self.assertEqual(items[id2]["status"], "executed")
        print(
            f"[V-04-b] host={host_label} non_abort rc={rc} "
            f"item1_status={items[id1]['status']} item2_status={items[id2]['status']}"
        )

    def test_non_abort_hook_bypass_oc(self) -> None:
        self._run_non_abort_hook_bypass("oc", oc_runipd)

    def test_non_abort_hook_bypass_agy(self) -> None:
        self._run_non_abort_hook_bypass("agy", agy_runipd)

    def _run_tool_identity_item_failure(self, host_label: str, mod: Any) -> None:
        repo = _make_test_repo(self.root / f"repo_tid_{host_label}")
        id1 = f"tid1{host_label}"
        id2 = f"tid2{host_label}"
        plan1 = _write_plan(repo, id6=id1, order=1)
        plan2 = _write_plan(repo, id6=id2, order=2)
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)

        run_dir = self.root / f"run_tid_{host_label}"
        run_dir.mkdir(parents=True)
        item1 = {
            "id6": id1,
            "action": "execute",
            "setid": "fixfirst",
            "position": 1,
            "status": "queued",
            "attempts": [],
            "configured_file": str(plan1.relative_to(repo)),
        }
        item2 = {
            "id6": id2,
            "action": "execute",
            "setid": "fixfirst",
            "position": 2,
            "status": "queued",
            "attempts": [],
            "configured_file": str(plan2.relative_to(repo)),
        }
        state = {
            "run_id": f"run_tid_{host_label}",
            "repo": str(repo),
            "options": {
                "auto": True,
                "no_audit": True,
                "no_verify": True,
                "retry_budget": 2,
                "isolate_worktree": True,
            },
            "queue": [item1, item2],
        }
        mod.save_state(run_dir, state)

        def fake_execute(rd: Any, st: Any, it: Any, *args: Any, **kwargs: Any) -> None:
            if it["id6"] == id1:
                it.setdefault("attempts", []).append(
                    {"number": 1, "started_at": runner_shared.utc_now()}
                )
                it["status"] = "running"
                mod.save_state(rd, st)
                raise runner_shared.ToolIdentityError(
                    "nested aw tool-identity mismatch"
                )
            else:
                it["status"] = "executed"
                mod.save_state(rd, st)

        with coordinator_role(), mock.patch.object(
            mod, "execute_item", side_effect=fake_execute
        ):
            mod.run_queue(run_dir, retry_incomplete=False)

        final_state = mod.load_state(run_dir)
        items = {it["id6"]: it for it in final_state["queue"]}
        # Shipped behavior (IPD s2tn4q / closed backlog 03y5g6): ToolIdentityError fails only the item
        self.assertEqual(items[id1]["status"], "fail-gate")
        self.assertEqual(
            items[id1].get("refusal", {}).get("code"),
            "tool-identity-mismatch",
        )
        self.assertEqual(items[id2]["status"], "executed")
        print(
            f"[V-04-c] host={host_label} tool_identity_divergence (resolved by s2tn4q/03y5g6) "
            f"item1_status={items[id1]['status']} refusal={items[id1].get('refusal', {}).get('code')} "
            f"item2_status={items[id2]['status']}"
        )

    def test_tool_identity_item_failure_oc(self) -> None:
        self._run_tool_identity_item_failure("oc", oc_runipd)

    def test_tool_identity_item_failure_agy(self) -> None:
        self._run_tool_identity_item_failure("agy", agy_runipd)

    # -------------------------------------------------------------------------
    # E-05: Spec Cross-Check & Abort Set Agreement
    # -------------------------------------------------------------------------

    def test_e05_spec_abort_classes_match(self) -> None:
        """E-05 / V-05: Confirm run_evidence.ABORT_CLASSES matches spec 4.1 abort table."""
        self.assertEqual(
            run_evidence.ABORT_CLASSES,
            ("Corrupt run ledger",),
            "run_evidence.ABORT_CLASSES must exactly match spec 4.1 'Corrupt run ledger'",
        )
        print(f"[V-05] ABORT_CLASSES={run_evidence.ABORT_CLASSES} matches spec 4.1")

    def test_e05_spec_5_5_table_owner_ids_resolve(self) -> None:
        """E-05 / V-03: Verify all owner citations in spec 25kzda Section 5.5 resolve cleanly."""
        repo_root = Path(__file__).resolve().parents[1]
        spec_path = _locate_spec_25kzda(repo_root)
        spec_text = spec_path.read_text(encoding="utf-8")
        problems = _spec_5_5_owner_problems(spec_text, repo_root)
        self.assertEqual(
            problems,
            [],
            f"Expected zero problems in spec 25kzda §5.5 owner citations, found: {problems}",
        )

    def test_e05_spec_5_5_checker_rejects_stale_owner(self) -> None:
        """E-05 / V-03: Verify _spec_5_5_owner_problems rejects stale or mismatched owner citations."""
        repo_root = Path(__file__).resolve().parents[1]
        spec_path = _locate_spec_25kzda(repo_root)
        spec_text = spec_path.read_text(encoding="utf-8")

        # Mutation 1: one row's Notes reverted to Implementing: Order 05 (`k8n97m`).
        mut1 = spec_text.replace(
            "Shipped (Order 05, `w9nvq4`).",
            "Implementing: Order 05 (`k8n97m`).",
            1,
        )
        self.assertNotEqual(mut1, spec_text, "Mutation 1 replacement target not found")
        p1 = _spec_5_5_owner_problems(mut1, repo_root)
        self.assertTrue(
            len(p1) > 0,
            "Expected checker to report problems on mutation 1 (stale k8n97m), got empty",
        )

        # Mutation 2: the a red combined suite after merge row's Order 05 changed to Order 06
        target2 = (
            "| a red combined suite after merge | `integration-test-failed` | integration gate | Yes | "
            "Verification suite failed after merge in lane or integration worktree. Shipped (Order 05, `w9nvq4`). |"
        )
        replacement2 = (
            "| a red combined suite after merge | `integration-test-failed` | integration gate | Yes | "
            "Verification suite failed after merge in lane or integration worktree. Shipped (Order 06, `w9nvq4`). |"
        )
        mut2 = spec_text.replace(target2, replacement2, 1)
        self.assertNotEqual(mut2, spec_text, "Mutation 2 replacement target not found")
        p2 = _spec_5_5_owner_problems(mut2, repo_root)
        self.assertTrue(
            len(p2) > 0,
            "Expected checker to report problems on mutation 2 (Order 06 for w9nvq4), got empty",
        )

        # Mutation 3: the verifier transport failure row reverted to Implementing: Order 04 (`ytas91`).
        target3_shipped = (
            "| verifier transport failure | `verifier-transport-error` | `verification_retry_decision` | Yes | "
            "Skeptical verifier session crash or transport failure. Shipped (`yd4tqw`, from backlog `jodcz3`). |"
        )
        target3_impl = (
            "| verifier transport failure | `verifier-transport-error` | `verification_retry_decision` | Yes | "
            "Skeptical verifier session crash or transport failure. Implementing: `yd4tqw` (from backlog `jodcz3`). |"
        )
        target3 = target3_shipped if target3_shipped in spec_text else target3_impl
        replacement3 = (
            "| verifier transport failure | `verifier-transport-error` | `verification_retry_decision` | Yes | "
            "Skeptical verifier session crash or transport failure. Implementing: Order 04 (`ytas91`). |"
        )
        mut3 = spec_text.replace(target3, replacement3, 1)
        self.assertNotEqual(mut3, spec_text, "Mutation 3 replacement target not found")
        p3 = _spec_5_5_owner_problems(mut3, repo_root)
        self.assertTrue(
            len(p3) > 0,
            "Expected checker to report problems on mutation 3 (ytas91 on verifier transport failure), got empty",
        )


if __name__ == "__main__":
    unittest.main()
