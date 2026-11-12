"""Outcome tests: OpenCode v2 tool events render and parse like their v1 equivalents.

The v2 event fixtures below copy the field layout of real `opencode v2.2.7` session logs
(2026-11-12). Before the normalization, every v2 tool line rendered as a bare `tool: shell`,
`tool: edit`, ... with no command or path. The v1 fixtures pin that the v1 output is unchanged.
"""

from __future__ import annotations

import json
import unittest

from agent_workflows import opencode_cli
from agent_workflows import render_stream as rs
from agent_workflows import verifier_corroboration as vc

REPO = "/repo"


def _v2(
    tool: str, inp: dict, inner_meta: dict, output: str = "", status: str = "completed"
) -> dict:
    return {
        "type": "tool_use",
        "timestamp": 1,
        "sessionID": "ses_x",
        "part": {
            "type": "tool",
            "tool": tool,
            "state": {
                "status": status,
                "input": inp,
                "output": output,
                "title": tool,
                "metadata": {
                    "metadata": inner_meta,
                    "content": [{"type": "text", "text": output}],
                    "rawInput": json.dumps(inp),
                    "providerCall": {},
                    "providerResult": {},
                },
                "time": {"start": 1000, "end": 3000},
            },
        },
    }


def _v1(tool: str, inp: dict, meta: dict, title: str) -> dict:
    return {
        "type": "tool_use",
        "part": {
            "tool": tool,
            "state": {
                "status": "completed",
                "input": inp,
                "title": title,
                "metadata": meta,
                "time": {"start": 1000, "end": 3000},
            },
        },
    }


V2_SHELL = _v2(
    "shell",
    {"command": "git status --short", "workdir": REPO},
    {"exit": 0, "truncated": False},
    "M a.py\n",
)
V2_EDIT = _v2(
    "edit",
    {"path": f"{REPO}/a.py", "oldString": "x", "newString": "y"},
    {
        "files": [
            {
                "file": "a.py",
                "patch": "@@ -1 +1 @@\n-x\n+y",
                "status": "modified",
                "additions": 2,
                "deletions": 1,
            }
        ],
        "truncated": False,
    },
    "Edited a.py (1 replacement)",
)
V2_WRITE_NEW = _v2(
    "write",
    {"path": f"{REPO}/n.md", "content": "a\nb\nc\n"},
    {"truncated": False},
    "Created file successfully: n.md",
)
V2_WRITE_OVER = _v2(
    "write",
    {"path": f"{REPO}/n.md", "content": "a\n"},
    {"truncated": False},
    "Wrote file successfully: n.md",
)
V2_READ = _v2(
    "read",
    {"path": f"{REPO}/r.md", "offset": 10, "limit": 5},
    {"truncated": True},
    f"Read file {REPO}/r.md, lines 10-14\n10: x",
)
V2_EXECUTE = _v2(
    "execute", {"code": "return 1"}, {"toolCalls": [], "truncated": False}, "1"
)


def _render(event: dict, verbosity: int = 1) -> str:
    out = rs.render_event(
        json.dumps(event),
        rs.Palette(False),
        rs.StreamTracker(),
        verbosity=verbosity,
        repo_root=REPO,
    )
    assert out is not None
    return out


class RenderV2Tests(unittest.TestCase):
    def test_shell_shows_command_under_bash_prefix(self) -> None:
        line = _render(V2_SHELL, verbosity=0)
        self.assertIn("bash:", line)
        self.assertIn("git status --short", line)
        self.assertNotIn("tool:", line)

    def test_edit_shows_path_and_stats(self) -> None:
        line = _render(V2_EDIT, verbosity=0)
        self.assertIn("edit:", line)
        self.assertIn("a.py (+2, -1)", line)

    def test_edit_marks_file_modified(self) -> None:
        tracker = rs.StreamTracker()
        rs.render_event(json.dumps(V2_EDIT), rs.Palette(False), tracker, repo_root=REPO)
        self.assertIn("a.py", tracker.modified_files)

    def test_write_new_and_overwrite(self) -> None:
        self.assertIn("n.md (new file, 3 lines)", _render(V2_WRITE_NEW, verbosity=0))
        self.assertIn("n.md (overwrote, 1 lines)", _render(V2_WRITE_OVER, verbosity=0))

    def test_read_shows_range_at_verbose_and_is_hidden_by_default(self) -> None:
        self.assertIn("r.md (lines 10-14)", _render(V2_READ, verbosity=1))
        self.assertIsNone(
            rs.render_event(
                json.dumps(V2_READ),
                rs.Palette(False),
                rs.StreamTracker(),
                verbosity=0,
                repo_root=REPO,
            )
        )

    def test_unknown_tool_shows_input_not_its_own_name_twice(self) -> None:
        line = _render(V2_EXECUTE, verbosity=0)
        self.assertIn("execute:", line)
        self.assertIn("return 1", line)
        self.assertNotIn("execute: execute", line)


class RenderV1UnchangedTests(unittest.TestCase):
    def test_v1_bash_and_edit_render_as_before(self) -> None:
        bash = _v1("bash", {"command": "ls"}, {"output": "x", "exit": 0}, "ls")
        self.assertIn("bash:", _render(bash, verbosity=0))
        self.assertIn("ls", _render(bash, verbosity=0))
        edit = _v1(
            "edit",
            {"filePath": f"{REPO}/a.py", "oldString": "x", "newString": "y"},
            {
                "filediff": {
                    "file": f"{REPO}/a.py",
                    "patch": "p",
                    "additions": 1,
                    "deletions": 1,
                }
            },
            "a.py",
        )
        self.assertIn("a.py (+1, -1)", _render(edit, verbosity=0))

    def test_v1_part_passes_through_normalizer_unchanged(self) -> None:
        bash = _v1("bash", {"command": "ls"}, {"output": "x"}, "ls")
        self.assertIs(opencode_cli.normalize_tool_part(bash["part"]), bash["part"])
        self.assertIs(opencode_cli.normalize_event(bash), bash)


class ToolCallV2Tests(unittest.TestCase):
    def test_v2_shell_is_a_bash_call_with_its_command(self) -> None:
        tc = vc.tool_call_from_event(V2_SHELL)
        assert tc is not None
        self.assertEqual(tc.tool, "bash")
        self.assertEqual(tc.command, "git status --short")
        self.assertFalse(tc.command_missing)
        self.assertAlmostEqual(tc.seconds, 2.0)

    def test_v2_file_tools_carry_their_path(self) -> None:
        for event in (V2_EDIT, V2_WRITE_NEW, V2_READ):
            tc = vc.tool_call_from_event(event)
            assert tc is not None
            self.assertTrue(tc.path and tc.path.startswith(REPO), tc)

    def test_normalizer_does_not_mutate_input(self) -> None:
        before = json.dumps(V2_EDIT, sort_keys=True)
        opencode_cli.normalize_event(V2_EDIT)
        self.assertEqual(json.dumps(V2_EDIT, sort_keys=True), before)


if __name__ == "__main__":
    unittest.main()
