#!/usr/bin/env python3
"""The versioned ACTIVITY TAXONOMY: a MULTI-LABEL classifier over structured tool signals.

WHY MULTI-LABEL AND NOT PRECEDENCE, WHICH IS THE WHOLE SHAPE OF THIS MODULE. The authoring plan
specified "precedence, overlap, uncertainty, and unclassified accounting", which reads as one winning
class per event plus a note. That was measured and refuted. Over all 22787 real ``bash`` tool calls
in this repository's own run corpus at review, 84.7 percent contained MORE THAN ONE shell segment
(45.3 percent carried a leading ``cd X &&``); classifying each segment independently, 41.9 percent of
commands matched TWO OR MORE classes, 49.4 percent matched exactly one and 8.7 percent matched none.
So OVERLAP IS THE NORM, not an exception a tiebreak handles. A precedence chain keeps one label and
discards the rest in two of every five commands, and WHICH it discards is an artifact of the ordering
rather than of the data. :func:`classify` therefore returns a SET of labels with per-label evidence,
and precedence survives only to choose a DISPLAY label (:meth:`Classification.display_label`), which
is a presentation concern and is documented as such.

THE ONLY CLASSIFIABLE SIGNAL FOR A SHELL ACTION IS THE COMMAND STRING, AND THAT IS A PRIVACY
BOUNDARY. Measured: the corpus holds 32333 ``tool_use`` parts across 462 session files with exactly
10 distinct tool names (``bash`` 22757, ``edit`` 5512, ``read`` 2332, ``todowrite`` 1074, ``write``
575, ``grep`` 49, ``glob`` 21, ``task`` 11, ``invalid`` 1, ``skill`` 1). ``edit``/``read``/``write``
carry a ``filePath`` (8420 of 8421 do), which is a clean STRUCTURED signal. ``bash`` carries only
free command text. So classifying a shell action REQUIRES reading command text, while the fact schema
forbids PERSISTING it. This module resolves that by classifying AT INGEST and emitting only derived
labels: :class:`LabelEvidence` names the matched RULE and the matched SEGMENT KIND and deliberately
carries no command text, and :meth:`Classification.to_dict` (the persistable form) has no field that
could hold one. :func:`assert_no_command_text` exists so a test can prove it rather than trust it.

THE UNCLASSIFIED AND AMBIGUOUS SHARES ARE DIFFERENT FACTS, KEPT APART DELIBERATELY. ``other-unknown``
means NO rule matched, which is a taxonomy COVERAGE GAP and is what the regression floor measures.
An AMBIGUOUS command matched a rule that cannot resolve a class from the head alone (the measured
exemplar is a bare ``python3``, 3807 segments, which runs both test suites and ad-hoc analysis), which
is a property of the DATA and not a gap. Mixing them into one catch-all would make a rising number
unattributable to either cause, so :class:`ClassAccounting` publishes both shares side by side.

``echo`` IS ITS OWN CLASS FOR A MEASURED REASON. It is the single largest unclassified head at 14895
segments, an eighth of all segments, and is almost entirely progress narration. Leaving it in
``other-unknown`` would put a known, describable behavior into the bucket reserved for "we do not know",
which is what the accounting exists to keep small.

Stdlib only. No prompt, response or command content is persisted by any function here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "TAXONOMY_VERSION",
    "ActivityClass",
    "ACTIVITY_CLASSES",
    "Confidence",
    "SegmentKind",
    "LabelEvidence",
    "Classification",
    "ClassAccounting",
    "CORPUS_BASELINE",
    "DISPLAY_PRECEDENCE",
    "TaxonomyError",
    "split_command_segments",
    "classify_segment",
    "classify_command",
    "classify_tool_call",
    "classify",
    "accumulate",
    "assert_no_command_text",
]


#: The taxonomy's own version. Orders 07, 08 and 10 render and query these labels, so the label SET
#: and a label's MEANING are a contract: changing either bumps this. Adding a rule that widens an
#: existing class's coverage does not.
TAXONOMY_VERSION = 1


class TaxonomyError(ValueError):
    """A classification input was malformed, or a persisted record carried command text."""


class ActivityClass(str, Enum):
    """The activity classes. A ``str`` enum so a persisted label is the bare token.

    Deliberately COARSE and CLOSED. A finer taxonomy would drift with whatever commands an agent
    happened to run and would become free text in practice, which the privacy projector's
    closed-vocabulary check would then refuse.
    """

    #: Reading, searching, listing, diffing-to-look. The measured largest class (30540 segments).
    INSPECTION = "inspection-search"
    #: Editing, writing, patching, moving, creating. Measured 5909 segments.
    IMPLEMENTATION = "implementation-editing"
    #: Any git invocation that is not itself an inspection (commit, merge, branch, stash).
    GIT = "git"
    #: Running a test suite or a single test. Measured 3975 segments.
    TESTS = "tests"
    #: This toolkit's own CLI (`aw ...`). Measured 3598 segments.
    AW_TOOLING = "aw-tooling"
    #: Linters and formatters. Measured 93 segments, so genuinely rare rather than absent.
    LINT_FORMAT = "lint-format"
    #: Dependency resolution and installation. Measured 17 segments.
    DEPENDENCY = "dependency-install"
    #: Sleeping, waiting, polling. Measured 12 segments.
    IDLE_WAIT = "idle-wait"
    #: Progress narration (`echo`). ITS OWN CLASS because it is the largest single unclassified head
    #: at 14895 segments; see the module docstring.
    NARRATION = "narration"
    #: NO rule matched. This is the taxonomy's COVERAGE GAP and the regression floor measures it.
    #: It is NOT the bucket for an ambiguous head; see :class:`Confidence` and ``is_ambiguous``.
    OTHER_UNKNOWN = "other-unknown"


ACTIVITY_CLASSES: tuple[ActivityClass, ...] = tuple(ActivityClass)


class Confidence(str, Enum):
    """How sure the classifier is of ONE label.

    ``LOW`` is the AMBIGUITY marker and is load-bearing: a bare ``python3`` head (measured 3807
    segments) genuinely runs both tests and ad-hoc analysis, and recording that as a confident label
    would be a guess while recording it as ``other-unknown`` would hide it in the coverage gap.
    """

    #: An unambiguous head or a structured signal (a `filePath`, a tool name).
    HIGH = "high"
    #: A head that usually means this class but has known other uses.
    MEDIUM = "medium"
    #: The head matched but cannot resolve the class from the head alone. AMBIGUOUS.
    LOW = "low"


class SegmentKind(str, Enum):
    """WHAT KIND of thing the matched segment was, which is the evidence a label may carry.

    A kind, never the text. This is the field that lets a consumer see WHY a label was assigned
    without the record holding the command that caused it.
    """

    #: A simple command head (the first word of a shell segment).
    COMMAND_HEAD = "command-head"
    #: A command head plus its first subcommand (`git commit`, `aw ipd lint`).
    COMMAND_SUBCOMMAND = "command-subcommand"
    #: A module invocation (`python3 -m pytest`).
    MODULE_INVOCATION = "module-invocation"
    #: A redirection or pipeline element that implies a write.
    REDIRECTION = "redirection"
    #: The tool's own name (`edit`, `read`, `write`), which needs no text at all.
    TOOL_NAME = "tool-name"
    #: A structured file path's CATEGORY (never the path).
    FILE_CATEGORY = "file-category"


#: DISPLAY-ONLY precedence, and the docstring says so because the plan's central correction is that
#: precedence is not the classification. Used by :meth:`Classification.display_label` to pick ONE
#: label for a table cell or a chart legend. It NEVER removes a label from
#: :attr:`Classification.labels` and no analysis consumes it.
#:
#: Ordered most-specific-first: a command that both runs tests and invokes git is more usefully
#: DISPLAYED as a test run, because that is the rarer and more informative fact about it.
DISPLAY_PRECEDENCE: tuple[ActivityClass, ...] = (
    ActivityClass.TESTS,
    ActivityClass.LINT_FORMAT,
    ActivityClass.DEPENDENCY,
    ActivityClass.AW_TOOLING,
    ActivityClass.IMPLEMENTATION,
    ActivityClass.GIT,
    ActivityClass.IDLE_WAIT,
    ActivityClass.INSPECTION,
    ActivityClass.NARRATION,
    ActivityClass.OTHER_UNKNOWN,
)


# --- The review-time baseline -------------------------------------------------------------------
#: THE REVIEW-TIME CORPUS SNAPSHOT. NOT A CURRENT MEASUREMENT.
#:
#: Every number here was measured on 2026-09-08 over the corpus as it stood, and the corpus GROWS
#: WITH EVERY RUN. It is retained for exactly two purposes: as the comparison baseline
#: :func:`ClassAccounting.compare_to_baseline` reports against, and as the regression floor
#: :meth:`ClassAccounting.unclassified_regressed` enforces. NOTHING here is used as an input to a
#: classification decision, so a stale baseline cannot change how a command is classified; it can
#: only change what a comparison REPORTS, which is the honest failure mode.
CORPUS_BASELINE: dict[str, Any] = {
    "provenance": "review-time-snapshot",
    "measured_at": "2026-09-08",
    "is_current": False,
    "note": (
        "measured at plan review over the then-current corpus; the corpus grows with every run, "
        "so re-measure with accumulate() over a live corpus before citing any figure as current"
    ),
    "bash_command_count": 22787,
    "segment_count": 104116,
    "multi_segment_command_share": 0.847,
    "leading_cd_command_share": 0.453,
    "multi_class_command_share": 0.419,
    "single_class_command_share": 0.494,
    "unclassified_command_share": 0.087,
    "four_or_more_class_command_share": 0.016,
    "tool_call_count": 32333,
    "tool_name_counts": {
        "bash": 22757,
        "edit": 5512,
        "read": 2332,
        "todowrite": 1074,
        "write": 575,
        "grep": 49,
        "glob": 21,
        "task": 11,
        "invalid": 1,
        "skill": 1,
    },
    "segment_class_counts": {
        ActivityClass.INSPECTION.value: 30540,
        ActivityClass.GIT.value: 9158,
        ActivityClass.IMPLEMENTATION.value: 5909,
        ActivityClass.TESTS.value: 3975,
        ActivityClass.AW_TOOLING.value: 3598,
        ActivityClass.LINT_FORMAT.value: 93,
        ActivityClass.DEPENDENCY.value: 17,
        ActivityClass.IDLE_WAIT.value: 12,
    },
    "top_unclassified_heads": {
        "echo": 14895,
        "": 3834,
        "python3": 3807,
        "def": 1432,
        "cd": 1257,
    },
    "file_category_shares": {
        "source-code": 0.380,
        "plan-or-ipd": 0.375,
        "test-code": 0.130,
    },
    "file_touching_call_count": 8421,
}

#: The DECLARED MARGIN on the unclassified-command-share regression floor. A floor with no margin
#: would fire on any corpus whose command mix differs at all, which trains a reader to ignore it; a
#: wide one detects nothing. 2 absolute percentage points over the measured 8.7 percent.
UNCLASSIFIED_SHARE_MARGIN = 0.02


# --- Segment splitting ---------------------------------------------------------------------------
#: Shell separators a segment split respects. Deliberately a SEPARATOR LIST and not a shell parser:
#: the goal is to find the command HEADS in a compound command, which is what classification needs,
#: and a full parser would be a large dependency-free reimplementation whose failure modes are worse
#: than an over-split. Measured: 84.7 percent of real bash commands are compound, so splitting is
#: the common path rather than an edge case.
_SEGMENT_SPLIT_RE = re.compile(r"(?:\|\||&&|\||;|\n)")

#: A leading `cd <somewhere> &&`, measured on 45.3 percent of real commands. STRIPPED before
#: classification because it is navigation, not activity: leaving it in would put `cd` (1257
#: segments) at the head of nearly half the corpus and classify those commands by their prologue.
_LEADING_CD_RE = re.compile(r"^\s*cd\s+[^&;|]+(?:&&|;)\s*")

#: An environment-variable prefix (`FOO=bar cmd`), stripped so the real head is found.
_ENV_PREFIX_RE = re.compile(
    r"^(?:[A-Za-z_][A-Za-z0-9_]*=(?:\"[^\"]*\"|'[^']*'|[^\s]*)\s+)+"
)

#: A shell-builtin prefix that WRAPS another command rather than being one (`sudo`, `time`, `env`,
#: `nohup`, `xargs`). The head after it is the real head.
_WRAPPER_HEADS: frozenset[str] = frozenset(
    {"sudo", "time", "env", "nohup", "xargs", "command", "exec", "nice", "timeout"}
)


def split_command_segments(command: str) -> tuple[list[str], bool]:
    """Split a compound command into its segments; report whether a leading ``cd`` was stripped.

    Returns ``(segments, had_leading_cd)``. A segment is a best-effort shell fragment, NOT a parsed
    AST; see :data:`_SEGMENT_SPLIT_RE` for why a parser is deliberately not used. An empty command
    yields ``([], False)`` rather than ``([""], False)``, so a blank input contributes no segment
    instead of one meaningless one (the measured corpus holds 3834 empty segments, which is exactly
    the artifact this avoids double-counting).

    Never raises for hostile input, and never returns any part of ``command`` to a persisted record:
    the caller uses these segments to derive labels and then discards them.
    """

    text = str(command or "")
    if not text.strip():
        return [], False

    had_cd = bool(_LEADING_CD_RE.match(text))
    if had_cd:
        text = _LEADING_CD_RE.sub("", text, count=1)

    segments = [s.strip() for s in _SEGMENT_SPLIT_RE.split(text)]
    return [s for s in segments if s], had_cd


def _segment_head(segment: str) -> tuple[str, str]:
    """``(head, first_argument)`` for one segment, with wrappers and env prefixes stripped.

    Both are lowercased bare tokens. A quoted or path-shaped head is reduced to its BASENAME
    (``/usr/bin/git`` -> ``git``), because the same tool legitimately lives at different absolute
    paths and because an absolute path is exactly what must not influence a persisted label.
    """

    parts = segment.strip().split()
    # STRIPPING LOOPS UNTIL STABLE, and it must: an env prefix can precede a wrapper
    # (`FOO=1 sudo cmd`) and a wrapper can precede an env prefix (`env FOO=1 cmd`), so a single pass
    # in either order leaves the real head unfound for one of the two. Measured defect: `env FOO=1 git
    # commit` classified as unclassified because `env` was stripped as a wrapper and `FOO=1` was then
    # read as the head.
    changed = True
    while changed and parts:
        changed = False
        stripped = _ENV_PREFIX_RE.sub("", " ".join(parts))
        candidate = stripped.split()
        if candidate != parts:
            parts = candidate
            changed = True
        if parts and parts[0].lower().strip("\"'") in _WRAPPER_HEADS:
            parts = parts[1:]
            changed = True
            # A wrapper's own flags (`timeout 30s`, `xargs -0`) are skipped too.
            while parts and parts[0].startswith("-"):
                parts = parts[1:]
            if parts and re.fullmatch(r"[0-9]+[smhd]?", parts[0]):
                parts = parts[1:]
    if not parts:
        return "", ""
    head = parts[0].strip("\"'")
    if "/" in head or "\\" in head:
        head = re.split(r"[\\/]", head)[-1]
    rest = [p for p in parts[1:] if not p.startswith("-")]
    return head.lower(), (rest[0].strip("\"'").lower() if rest else "")


# --- The rules -----------------------------------------------------------------------------------
@dataclass(frozen=True)
class _Rule:
    """ONE classification rule. Its ``name`` is the evidence a label carries.

    A rule NAME is a stable identifier, so it may be persisted; a rule's PATTERN is never persisted
    and neither is anything it matched.
    """

    name: str
    activity: ActivityClass
    kind: SegmentKind
    confidence: Confidence = Confidence.HIGH


#: Command heads that ALWAYS mean inspection. `git` is deliberately absent: a git invocation's class
#: depends on its subcommand and is resolved by :data:`_GIT_SUBCOMMANDS`.
_INSPECTION_HEADS: dict[str, str] = {
    "cat": "cat",
    "head": "head",
    "tail": "tail",
    "less": "pager",
    "more": "pager",
    "ls": "ls",
    "find": "find",
    "grep": "grep",
    "rg": "ripgrep",
    "ack": "ack",
    "ag": "silversearcher",
    "tree": "tree",
    "wc": "wc",
    "stat": "stat",
    "file": "file",
    "du": "du",
    "df": "df",
    "which": "which",
    "whereis": "whereis",
    "type": "type",
    "pwd": "pwd",
    "readlink": "readlink",
    "basename": "basename",
    "dirname": "dirname",
    "diff": "diff",
    "cmp": "cmp",
    "od": "od",
    "xxd": "xxd",
    "strings": "strings",
    "jq": "jq",
    "yq": "yq",
    "sort": "sort",
    "uniq": "uniq",
    "cut": "cut",
    "column": "column",
    "nl": "nl",
    "sha256sum": "checksum",
    "md5sum": "checksum",
    "date": "date",
    "ps": "ps",
    "top": "top",
    "env": "env",
    "printenv": "printenv",
    "uname": "uname",
    "hostname": "hostname",
    "id": "id",
    "whoami": "whoami",
    "man": "man",
    "help": "help",
}

#: Heads that ALWAYS mean implementation/editing.
_IMPLEMENTATION_HEADS: dict[str, str] = {
    "sed": "sed",
    "awk": "awk",
    "tee": "tee",
    "patch": "patch",
    "cp": "cp",
    "mv": "mv",
    "rm": "rm",
    "mkdir": "mkdir",
    "rmdir": "rmdir",
    "touch": "touch",
    "ln": "ln",
    "chmod": "chmod",
    "chown": "chown",
    "truncate": "truncate",
    "install": "install",
    "vim": "editor",
    "vi": "editor",
    "nano": "editor",
    "emacs": "editor",
    "ed": "editor",
    "tar": "archive",
    "unzip": "archive",
    "zip": "archive",
    "gzip": "archive",
}

#: Heads that mean a test run.
_TEST_HEADS: dict[str, str] = {
    "pytest": "pytest",
    "py.test": "pytest",
    "tox": "tox",
    "nox": "nox",
    "unittest": "unittest",
    "jest": "jest",
    "vitest": "vitest",
    "mocha": "mocha",
    "rspec": "rspec",
    "phpunit": "phpunit",
    "ctest": "ctest",
}

#: Heads that mean a lint/format run.
_LINT_HEADS: dict[str, str] = {
    "ruff": "ruff",
    "flake8": "flake8",
    "pylint": "pylint",
    "mypy": "mypy",
    "black": "black",
    "isort": "isort",
    "prettier": "prettier",
    "eslint": "eslint",
    "shellcheck": "shellcheck",
    "clang-format": "clang-format",
    "gofmt": "gofmt",
    "rustfmt": "rustfmt",
    "yamllint": "yamllint",
    "markdownlint": "markdownlint",
    "pre-commit": "pre-commit",
}

#: Heads that mean dependency resolution/installation.
_DEPENDENCY_HEADS: dict[str, str] = {
    "pip": "pip",
    "pip3": "pip",
    "pipx": "pipx",
    "poetry": "poetry",
    "uv": "uv",
    "npm": "npm",
    "pnpm": "pnpm",
    "yarn": "yarn",
    "bundle": "bundler",
    "apt": "apt",
    "apt-get": "apt",
    "brew": "brew",
    "conda": "conda",
}

#: Heads that mean idling/waiting.
_IDLE_HEADS: dict[str, str] = {"sleep": "sleep", "wait": "wait", "watch": "watch"}

#: Heads that mean progress narration. `echo` is the measured largest unclassified head (14895).
_NARRATION_HEADS: dict[str, str] = {
    "echo": "echo",
    "printf": "printf",
    "true": "noop",
    ":": "noop",
}

#: git subcommand -> the class it means. THE REASON THIS TABLE EXISTS: `git` is 9158 segments and its
#: class genuinely depends on the subcommand. `git status`/`git diff`/`git log` are INSPECTION, not
#: repository mutation, and filing them under GIT alone would make the git class unreadable as a
#: measure of version-control WORK. Such a subcommand gets BOTH labels, which is precisely what
#: multi-label exists to express.
_GIT_SUBCOMMANDS: dict[str, tuple[ActivityClass, ...]] = {
    "status": (ActivityClass.GIT, ActivityClass.INSPECTION),
    "diff": (ActivityClass.GIT, ActivityClass.INSPECTION),
    "log": (ActivityClass.GIT, ActivityClass.INSPECTION),
    "show": (ActivityClass.GIT, ActivityClass.INSPECTION),
    "blame": (ActivityClass.GIT, ActivityClass.INSPECTION),
    "ls-files": (ActivityClass.GIT, ActivityClass.INSPECTION),
    "rev-parse": (ActivityClass.GIT, ActivityClass.INSPECTION),
    "branch": (ActivityClass.GIT, ActivityClass.INSPECTION),
    "remote": (ActivityClass.GIT, ActivityClass.INSPECTION),
    "add": (ActivityClass.GIT,),
    "commit": (ActivityClass.GIT,),
    "merge": (ActivityClass.GIT,),
    "rebase": (ActivityClass.GIT,),
    "checkout": (ActivityClass.GIT,),
    "switch": (ActivityClass.GIT,),
    "restore": (ActivityClass.GIT,),
    "reset": (ActivityClass.GIT,),
    "stash": (ActivityClass.GIT,),
    "cherry-pick": (ActivityClass.GIT,),
    "worktree": (ActivityClass.GIT,),
    "push": (ActivityClass.GIT,),
    "fetch": (ActivityClass.GIT,),
    "pull": (ActivityClass.GIT,),
    "clone": (ActivityClass.GIT,),
    "tag": (ActivityClass.GIT,),
    "mv": (ActivityClass.GIT, ActivityClass.IMPLEMENTATION),
    "rm": (ActivityClass.GIT, ActivityClass.IMPLEMENTATION),
    "apply": (ActivityClass.GIT, ActivityClass.IMPLEMENTATION),
}

#: `aw` subcommands recognized in a rule identifier. A CLOSED VOCABULARY, and that is the point: a
#: rule identifier is PERSISTED, so interpolating an arbitrary next token into it would carry command
#: text into a fact. An unrecognized subcommand yields the bare `aw` rule, which loses a little
#: granularity and leaks nothing. Any string here is safe because it is written in this file rather
#: than read from input.
_AW_SUBCOMMANDS: frozenset[str] = frozenset(
    {
        "ipd",
        "specs",
        "spec",
        "backlog",
        "check",
        "attention",
        "index",
        "find",
        "research",
        "archive",
        "group",
        "rename",
        "commit",
        "sanitize",
        "oc",
        "agy",
        "opencode",
        "host",
        "runs",
        "show",
        "set",
        "install",
        "review",
        "release",
        "help",
        "version",
        "doctor",
    }
)

#: A `python3 -m <module>` module name -> its class. THIS IS WHY THE AMBIGUITY RULE EXISTS: a bare
#: `python3` (measured 3807 segments) resolves to nothing, while `python3 -m pytest` resolves
#: exactly. The module form is checked BEFORE the bare head so the resolvable case never falls
#: through to the ambiguous one.
_PY_MODULES: dict[str, ActivityClass] = {
    "pytest": ActivityClass.TESTS,
    "unittest": ActivityClass.TESTS,
    "tox": ActivityClass.TESTS,
    "nox": ActivityClass.TESTS,
    "ruff": ActivityClass.LINT_FORMAT,
    "black": ActivityClass.LINT_FORMAT,
    "flake8": ActivityClass.LINT_FORMAT,
    "mypy": ActivityClass.LINT_FORMAT,
    "isort": ActivityClass.LINT_FORMAT,
    "pylint": ActivityClass.LINT_FORMAT,
    "pip": ActivityClass.DEPENDENCY,
    "venv": ActivityClass.DEPENDENCY,
    "agent_workflows": ActivityClass.AW_TOOLING,
    "json.tool": ActivityClass.INSPECTION,
    "http.server": ActivityClass.INSPECTION,
}

#: Interpreter heads that are AMBIGUOUS on their own. Measured: a bare `python3` runs both test
#: suites and ad-hoc analysis, so a confident label would be a guess and `other-unknown` would hide
#: a known behavior in the coverage gap. They get a LOW-confidence label instead; see D-4.
_AMBIGUOUS_INTERPRETERS: frozenset[str] = frozenset(
    {"python", "python3", "python2", "node", "ruby", "perl", "sh", "bash", "zsh"}
)

#: `python3 -m <module>` / `python -m <module>`.
_PY_MODULE_RE = re.compile(
    r"\b(?:python[0-9.]*)\s+(?:-[A-Za-z]+\s+)*-m\s+([A-Za-z_][A-Za-z0-9_.]*)"
)

#: A `make <target>` whose target names a known activity.
_MAKE_TARGETS: dict[str, ActivityClass] = {
    "test": ActivityClass.TESTS,
    "tests": ActivityClass.TESTS,
    "check": ActivityClass.TESTS,
    "lint": ActivityClass.LINT_FORMAT,
    "fmt": ActivityClass.LINT_FORMAT,
    "format": ActivityClass.LINT_FORMAT,
    "install": ActivityClass.DEPENDENCY,
    "install-dev": ActivityClass.DEPENDENCY,
}

#: A redirection implying a WRITE. `>>`/`>` to a file is an edit even when the head is not.
#: Deliberately excludes `2>&1` and `>/dev/null`, which write nothing durable: counting those as
#: edits would classify most diagnostic commands as implementation.
_WRITE_REDIRECT_RE = re.compile(r"(?<![0-9])>>?\s*(?!&|/dev/null|/dev/stderr)[^\s|;&]+")

#: Tool names that carry a structured signal and need no text. Measured tool census: 10 names.
_TOOL_NAME_CLASSES: dict[str, tuple[ActivityClass, ...]] = {
    "read": (ActivityClass.INSPECTION,),
    "grep": (ActivityClass.INSPECTION,),
    "glob": (ActivityClass.INSPECTION,),
    "edit": (ActivityClass.IMPLEMENTATION,),
    "write": (ActivityClass.IMPLEMENTATION,),
    "todowrite": (ActivityClass.NARRATION,),
    "task": (ActivityClass.INSPECTION,),
    "skill": (ActivityClass.INSPECTION,),
}


# --- Results -------------------------------------------------------------------------------------
@dataclass(frozen=True)
class LabelEvidence:
    """WHY one label was assigned: the rule name and the segment KIND. NEVER the command text.

    THIS TYPE IS THE PRIVACY BOUNDARY OF THE TAXONOMY, and its shape is the enforcement. There is no
    field here that can hold free text: ``rule`` is a fixed identifier from a table in this module and
    ``kind`` is an enum. :func:`assert_no_command_text` checks a persisted record against a candidate
    command so a test can prove the absence rather than assert it.
    """

    rule: str
    kind: SegmentKind
    confidence: Confidence = Confidence.HIGH
    #: How many segments of the command matched this rule. A COUNT, which carries no content.
    segment_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "segment_kind": self.kind.value,
            "confidence": self.confidence.value,
            "segment_count": self.segment_count,
        }


@dataclass(frozen=True)
class Classification:
    """The LABEL SET for one tool call, with per-label evidence and per-label share.

    ``labels`` is a SET, which is the plan's central correction: 41.9 percent of real commands carry
    two or more and a single-label result would discard one arbitrarily. ``shares`` apportions the
    command's segments across its labels so a per-class total is computable without double counting
    the command itself.
    """

    labels: tuple[ActivityClass, ...]
    evidence: dict[ActivityClass, LabelEvidence] = field(default_factory=dict)
    #: label -> fraction of this command's classified segments carrying it. Sums to 1.0 over labels
    #: when anything was classified, so summing shares over a corpus yields per-class segment mass
    #: rather than a count inflated by multi-label commands.
    shares: dict[ActivityClass, float] = field(default_factory=dict)
    segment_count: int = 0
    had_leading_cd: bool = False
    #: The taxonomy version that produced this record, so a stored classification is interpretable.
    taxonomy_version: int = TAXONOMY_VERSION

    @property
    def is_multi_class(self) -> bool:
        return len(self.labels) >= 2

    @property
    def is_unclassified(self) -> bool:
        """True when NO rule matched at all. The COVERAGE GAP, and what the floor measures.

        NOTE THE ``not self.evidence`` TERM, WHICH IS THE WHOLE OF D-4 IN ONE LINE. An AMBIGUOUS
        command also carries the ``other-unknown`` LABEL (there is no honest class to give it), so a
        test on the label alone would count it in the coverage gap and make a rising gap
        unattributable to either a taxonomy defect or a shift in the command mix. An ambiguous
        command HAS evidence (a rule matched and recorded that it could not resolve), so requiring an
        EMPTY evidence map is what separates "we have no rule for this" from "our rule says this
        cannot be resolved".
        """

        return self.labels == (ActivityClass.OTHER_UNKNOWN,) and not self.evidence

    @property
    def is_ambiguous(self) -> bool:
        """True when a rule matched but no label reached better than LOW confidence.

        The measured exemplar is a bare ``python3``. This is a fact about the DATA, not a gap in the
        taxonomy, which is why it is counted separately from :attr:`is_unclassified`.
        """

        if not self.evidence:
            return False
        return all(e.confidence is Confidence.LOW for e in self.evidence.values())

    def display_label(self) -> ActivityClass:
        """ONE label for a table cell or a chart legend. PRESENTATION ONLY.

        Uses :data:`DISPLAY_PRECEDENCE`. This is the ONLY surviving use of precedence in this module
        and it removes nothing: :attr:`labels` still carries every label. No analysis calls this.
        """

        for candidate in DISPLAY_PRECEDENCE:
            if candidate in self.labels:
                return candidate
        return ActivityClass.OTHER_UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        """The PERSISTABLE form: labels, evidence, shares and counts. NO command text anywhere.

        Every value here is an enum token, a rule identifier, a count or a float. A reader can see
        that no field could hold a command string, and :func:`assert_no_command_text` proves it for a
        given input.
        """

        return {
            "taxonomy_version": self.taxonomy_version,
            "labels": [c.value for c in self.labels],
            "display_label": self.display_label().value,
            "evidence": {
                c.value: e.to_dict()
                for c, e in sorted(self.evidence.items(), key=lambda kv: kv[0].value)
            },
            "shares": {
                c.value: round(s, 6)
                for c, s in sorted(self.shares.items(), key=lambda kv: kv[0].value)
            },
            "segment_count": self.segment_count,
            "had_leading_cd": self.had_leading_cd,
            "is_multi_class": self.is_multi_class,
            "is_unclassified": self.is_unclassified,
            "is_ambiguous": self.is_ambiguous,
        }


# --- Classification ------------------------------------------------------------------------------
def classify_segment(segment: str) -> dict[ActivityClass, LabelEvidence]:
    """Classify ONE shell segment into zero or more classes with evidence.

    Zero classes (an empty result) means no rule matched THIS segment; the caller decides whether the
    whole command is unclassified. Returns evidence keyed by class, so a segment matching two rules
    for the same class contributes one label rather than two.
    """

    found: dict[ActivityClass, LabelEvidence] = {}

    def note(
        activity: ActivityClass,
        rule: str,
        kind: SegmentKind,
        confidence: Confidence = Confidence.HIGH,
    ) -> None:
        existing = found.get(activity)
        # A HIGHER confidence wins for the same class: a `python3 -m pytest` segment must not be
        # recorded as LOW merely because the bare-interpreter rule also looked at it.
        order = {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}
        if existing is None or order[confidence] > order[existing.confidence]:
            found[activity] = LabelEvidence(rule=rule, kind=kind, confidence=confidence)

    text = str(segment or "")
    if not text.strip():
        return found

    head, first_arg = _segment_head(text)

    # A `python -m <module>` is checked FIRST so the resolvable form never falls through to the
    # ambiguous bare-interpreter rule below.
    module_match = _PY_MODULE_RE.search(text)
    if module_match:
        module = module_match.group(1)
        # RESOLVED TO A TABLE KEY BEFORE INTERPOLATION, so the rule identifier is provably closed.
        # `module` itself comes from the input; naming it in the rule would carry input text into a
        # persisted record (the same defect the `aw:` rule had). `resolved` is a KEY OF `_PY_MODULES`,
        # i.e. a string written in this file, so interpolating it leaks nothing.
        resolved = module if module in _PY_MODULES else module.split(".")[0]
        activity = _PY_MODULES.get(resolved)
        if activity is not None:
            note(
                activity,
                f"python-module:{resolved.split('.')[0]}",
                SegmentKind.MODULE_INVOCATION,
            )
        else:
            note(
                ActivityClass.OTHER_UNKNOWN,
                "python-module:unrecognized",
                SegmentKind.MODULE_INVOCATION,
                Confidence.LOW,
            )

    if head == "git":
        classes = _GIT_SUBCOMMANDS.get(first_arg)
        if classes:
            for activity in classes:
                note(activity, f"git:{first_arg}", SegmentKind.COMMAND_SUBCOMMAND)
        else:
            # An unrecognized git subcommand is still git. MEDIUM because the subcommand is unknown.
            note(
                ActivityClass.GIT,
                "git:other",
                SegmentKind.COMMAND_HEAD,
                Confidence.MEDIUM,
            )
    elif head == "aw":
        # THE SUBCOMMAND IS LOOKED UP IN A FIXED TABLE, NEVER INTERPOLATED. An earlier revision built
        # the rule as f"aw:{first_arg}", which put UNBOUNDED COMMAND TEXT into a persisted rule
        # identifier: `aw <anything>` would have carried `<anything>` into a fact. That is exactly the
        # leak this module exists to prevent, and it was caught by the privacy test rather than by
        # inspection, which is why every rule identifier now comes from a closed vocabulary.
        known = first_arg if first_arg in _AW_SUBCOMMANDS else ""
        note(
            ActivityClass.AW_TOOLING,
            f"aw:{known}" if known else "aw",
            SegmentKind.COMMAND_SUBCOMMAND if known else SegmentKind.COMMAND_HEAD,
        )
    elif head == "make":
        activity = _MAKE_TARGETS.get(first_arg)
        if activity is not None:
            note(activity, f"make:{first_arg}", SegmentKind.COMMAND_SUBCOMMAND)
        else:
            note(
                ActivityClass.IMPLEMENTATION,
                "make:other",
                SegmentKind.COMMAND_HEAD,
                Confidence.MEDIUM,
            )
    elif head in _TEST_HEADS:
        note(ActivityClass.TESTS, f"test:{_TEST_HEADS[head]}", SegmentKind.COMMAND_HEAD)
    elif head in _LINT_HEADS:
        note(
            ActivityClass.LINT_FORMAT,
            f"lint:{_LINT_HEADS[head]}",
            SegmentKind.COMMAND_HEAD,
        )
    elif head in _DEPENDENCY_HEADS:
        note(
            ActivityClass.DEPENDENCY,
            f"dep:{_DEPENDENCY_HEADS[head]}",
            SegmentKind.COMMAND_HEAD,
        )
    elif head in _IDLE_HEADS:
        note(
            ActivityClass.IDLE_WAIT,
            f"idle:{_IDLE_HEADS[head]}",
            SegmentKind.COMMAND_HEAD,
        )
    elif head in _NARRATION_HEADS:
        note(
            ActivityClass.NARRATION,
            f"narration:{_NARRATION_HEADS[head]}",
            SegmentKind.COMMAND_HEAD,
        )
    elif head in _IMPLEMENTATION_HEADS:
        note(
            ActivityClass.IMPLEMENTATION,
            f"impl:{_IMPLEMENTATION_HEADS[head]}",
            SegmentKind.COMMAND_HEAD,
        )
    elif head in _INSPECTION_HEADS:
        note(
            ActivityClass.INSPECTION,
            f"inspect:{_INSPECTION_HEADS[head]}",
            SegmentKind.COMMAND_HEAD,
        )
    elif head in _AMBIGUOUS_INTERPRETERS and not module_match:
        # THE AMBIGUITY CASE, measured at 3807 bare-`python3` segments. A rule DID match (we know it
        # is an interpreter), but the class cannot be resolved from the head, so this is neither a
        # confident label nor a coverage gap. LOW confidence records exactly that.
        note(
            ActivityClass.OTHER_UNKNOWN,
            f"ambiguous-interpreter:{head}",
            SegmentKind.COMMAND_HEAD,
            Confidence.LOW,
        )

    # A write redirection is an EDIT regardless of the head, and it is ADDITIVE: a
    # `grep ... > out.txt` is simultaneously inspection and implementation, which is the overlap a
    # single-label taxonomy would have to discard.
    if _WRITE_REDIRECT_RE.search(text):
        note(
            ActivityClass.IMPLEMENTATION,
            "redirect:write",
            SegmentKind.REDIRECTION,
            Confidence.MEDIUM,
        )

    return found


def classify_command(command: str) -> Classification:
    """Classify one shell command (possibly compound) into a LABEL SET.

    The measured shape of the input drives this: 84.7 percent of real commands are compound, so the
    command is SPLIT and each segment classified independently, then the per-segment results are
    unioned. That union is what produces two or more labels for 41.9 percent of commands.

    Consumes ``command`` and returns NO part of it. This function is the ingest-time boundary the
    module docstring describes.
    """

    segments, had_cd = split_command_segments(command)
    if not segments:
        return Classification(
            labels=(ActivityClass.OTHER_UNKNOWN,),
            evidence={},
            shares={ActivityClass.OTHER_UNKNOWN: 1.0},
            segment_count=0,
            had_leading_cd=had_cd,
        )

    per_class: dict[ActivityClass, LabelEvidence] = {}
    counts: dict[ActivityClass, int] = {}
    order = {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}

    for segment in segments:
        for activity, evidence in classify_segment(segment).items():
            counts[activity] = counts.get(activity, 0) + 1
            existing = per_class.get(activity)
            if (
                existing is None
                or order[evidence.confidence] > order[existing.confidence]
            ):
                per_class[activity] = evidence

    if not per_class:
        return Classification(
            labels=(ActivityClass.OTHER_UNKNOWN,),
            evidence={},
            shares={ActivityClass.OTHER_UNKNOWN: 1.0},
            segment_count=len(segments),
            had_leading_cd=had_cd,
        )

    evidence = {
        activity: LabelEvidence(
            rule=item.rule,
            kind=item.kind,
            confidence=item.confidence,
            segment_count=counts[activity],
        )
        for activity, item in per_class.items()
    }
    total = sum(counts.values())
    shares = {activity: counts[activity] / total for activity in counts}
    labels = tuple(sorted(per_class, key=lambda c: c.value))
    return Classification(
        labels=labels,
        evidence=evidence,
        shares=shares,
        segment_count=len(segments),
        had_leading_cd=had_cd,
    )


#: File-path CATEGORY rules. Ordered, first match wins, and the CATEGORY is all that is kept: a path
#: itself never reaches a label. Measured over the 8421 file-touching calls: source-code 38.0 percent,
#: plan-or-ipd 37.5 percent, test-code 13.0 percent.
_FILE_CATEGORY_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("test-code", re.compile(r"(?:^|/)tests?/|(?:^|/)test_[^/]*\.py$|_test\.py$")),
    ("plan-or-ipd", re.compile(r"\.ipd\.md$|/records/plans/")),
    ("spec", re.compile(r"\.spec\.md$|/records/specs/")),
    ("documentation", re.compile(r"\.(?:md|rst|txt)$")),
    ("configuration", re.compile(r"\.(?:toml|cfg|ini|ya?ml|json)$|(?:^|/)Makefile$")),
    ("source-code", re.compile(r"\.(?:py|js|ts|tsx|jsx|go|rs|rb|sh|c|h|cpp|java)$")),
)


def _file_category(file_path: str) -> str:
    """The CATEGORY of a file path, never the path. ``other`` when no rule matches.

    Matched against the path with separators normalized, and the return value is one of a small
    closed set, which is what makes it safe to persist as a label.
    """

    text = str(file_path or "").replace("\\", "/")
    if not text.strip():
        return "other"
    for name, pattern in _FILE_CATEGORY_RULES:
        if pattern.search(text):
            return name
    return "other"


def classify_tool_call(
    tool: str,
    *,
    command: str | None = None,
    file_path: str | None = None,
) -> Classification:
    """Classify ONE tool call from its tool name plus whichever signal that tool carries.

    THE SIGNAL AVAILABLE DEPENDS ON THE TOOL, which is the measured asymmetry the module docstring
    records. ``edit``/``read``/``write`` carry a structured ``filePath`` (8420 of 8421 do) and are
    classified from the TOOL NAME with the file CATEGORY as corroborating evidence, needing no free
    text at all. ``bash`` (22757 of 32333 calls) carries only the command string, so it goes through
    :func:`classify_command`, and that is the one path where command text is read.
    """

    name = str(tool or "").strip().lower()

    if name == "bash":
        if command is None:
            # A bash call with no command recorded is a MISSING signal, not an unclassifiable one.
            # It is filed as unclassified with no evidence, so it counts in the coverage gap rather
            # than silently vanishing from the accounting.
            return Classification(
                labels=(ActivityClass.OTHER_UNKNOWN,),
                evidence={},
                shares={ActivityClass.OTHER_UNKNOWN: 1.0},
            )
        return classify_command(command)

    classes = _TOOL_NAME_CLASSES.get(name)
    if not classes:
        return Classification(
            labels=(ActivityClass.OTHER_UNKNOWN,),
            evidence={},
            shares={ActivityClass.OTHER_UNKNOWN: 1.0},
            segment_count=1,
        )

    category = _file_category(file_path) if file_path else ""
    kind = SegmentKind.FILE_CATEGORY if category else SegmentKind.TOOL_NAME
    rule = f"tool:{name}" + (f"+category:{category}" if category else "")
    evidence = {
        activity: LabelEvidence(rule=rule, kind=kind, confidence=Confidence.HIGH)
        for activity in classes
    }
    share = 1.0 / len(classes)
    return Classification(
        labels=tuple(sorted(classes, key=lambda c: c.value)),
        evidence=evidence,
        shares={activity: share for activity in classes},
        segment_count=1,
    )


def classify(call: Mapping[str, Any]) -> Classification:
    """Classify one tool call given as a mapping, which is the shape a session log yields.

    Accepts ``{"tool": ..., "command": ..., "file_path"/"filePath": ...}``. Tolerant by design: a
    mapping missing every signal yields an unclassified record rather than raising, because one
    malformed event must not abort a corpus sweep.
    """

    if not isinstance(call, Mapping):
        raise TaxonomyError(f"a tool call must be a mapping, got {type(call).__name__}")
    return classify_tool_call(
        str(call.get("tool") or ""),
        command=call.get("command") if call.get("command") is not None else None,
        file_path=str(call.get("file_path") or call.get("filePath") or "") or None,
    )


# --- Accounting ----------------------------------------------------------------------------------
@dataclass(frozen=True)
class ClassAccounting:
    """The MEASURED per-class, unclassified and overlap accounting over a set of classified calls.

    E-02's requirement is that these be first-class MEASURED OUTPUTS rather than a promise, so every
    field here is computed from the input and none is copied from :data:`CORPUS_BASELINE`. The
    baseline is used only by :meth:`compare_to_baseline` and by the regression floor.

    UNCLASSIFIED AND AMBIGUOUS ARE SEPARATE FIELDS, which is D-4's resolution: the first is a
    taxonomy coverage gap, the second a property of the data, and a single catch-all would make a
    rising number unattributable to either.
    """

    command_count: int = 0
    segment_count: int = 0
    multi_segment_command_count: int = 0
    leading_cd_command_count: int = 0
    multi_class_command_count: int = 0
    single_class_command_count: int = 0
    unclassified_command_count: int = 0
    ambiguous_command_count: int = 0
    four_or_more_class_command_count: int = 0
    #: class -> how many COMMANDS carried this label. A multi-label command counts in EVERY label,
    #: which is why these sum to more than ``command_count`` and why ``class_segment_mass`` exists.
    class_command_counts: dict[str, int] = field(default_factory=dict)
    #: class -> summed per-command SHARE. Sums to the classified command count, so this is the
    #: figure to use for a per-class proportion without double counting.
    class_segment_mass: dict[str, float] = field(default_factory=dict)
    taxonomy_version: int = TAXONOMY_VERSION

    def _share(self, count: int) -> float:
        return (count / self.command_count) if self.command_count else 0.0

    @property
    def multi_class_command_share(self) -> float:
        """The measure that refuted single-label precedence. 0.419 at review; RE-MEASURE."""

        return self._share(self.multi_class_command_count)

    @property
    def single_class_command_share(self) -> float:
        return self._share(self.single_class_command_count)

    @property
    def unclassified_command_share(self) -> float:
        """The COVERAGE GAP share the regression floor is declared over. 0.087 at review."""

        return self._share(self.unclassified_command_count)

    @property
    def ambiguous_command_share(self) -> float:
        """The AMBIGUITY share, reported ALONGSIDE the gap and never folded into it (D-4)."""

        return self._share(self.ambiguous_command_count)

    @property
    def multi_segment_command_share(self) -> float:
        return self._share(self.multi_segment_command_count)

    @property
    def leading_cd_command_share(self) -> float:
        return self._share(self.leading_cd_command_count)

    def unclassified_regressed(
        self, *, margin: float = UNCLASSIFIED_SHARE_MARGIN
    ) -> tuple[bool, str]:
        """Has the unclassified share risen above the measured floor plus a DECLARED margin?

        Returns ``(regressed, reason)``. The floor is
        :data:`CORPUS_BASELINE`'s ``unclassified_command_share`` (0.087, measured 2026-09-08) and the
        margin defaults to :data:`UNCLASSIFIED_SHARE_MARGIN`. A zero-command input does NOT regress:
        no data is not a regression, and reporting one would fire on every empty fixture.

        This is the mechanism preventing ``other-unknown`` from silently absorbing a growing share,
        which is E-02's explicit requirement.
        """

        if not self.command_count:
            return False, "no-commands-classified"
        floor = float(CORPUS_BASELINE["unclassified_command_share"]) + float(margin)
        observed = self.unclassified_command_share
        if observed > floor:
            return True, (
                f"unclassified command share {observed:.4f} exceeds the measured baseline "
                f"{CORPUS_BASELINE['unclassified_command_share']:.4f} plus margin {margin:.4f} "
                f"(= {floor:.4f}) over {self.command_count} commands"
            )
        return False, (
            f"unclassified command share {observed:.4f} is within the baseline "
            f"{CORPUS_BASELINE['unclassified_command_share']:.4f} plus margin {margin:.4f}"
        )

    def compare_to_baseline(self) -> dict[str, Any]:
        """This accounting against the REVIEW-TIME baseline, with the baseline labeled as such.

        Every row carries ``observed``, ``baseline`` and ``baseline_is_current: False``, so a reader
        cannot mistake the snapshot for a current measurement. That labeling is the whole point: the
        plan's gate requires re-measurement, and an unlabeled comparison would look like one.
        """

        rows: dict[str, Any] = {
            "baseline_provenance": CORPUS_BASELINE["provenance"],
            "baseline_measured_at": CORPUS_BASELINE["measured_at"],
            "baseline_is_current": False,
            "observed_command_count": self.command_count,
            "baseline_command_count": CORPUS_BASELINE["bash_command_count"],
        }
        for key, observed in (
            ("multi_class_command_share", self.multi_class_command_share),
            ("single_class_command_share", self.single_class_command_share),
            ("unclassified_command_share", self.unclassified_command_share),
            ("multi_segment_command_share", self.multi_segment_command_share),
            ("leading_cd_command_share", self.leading_cd_command_share),
        ):
            rows[key] = {
                "observed": round(observed, 6),
                "baseline": CORPUS_BASELINE[key],
                "baseline_is_current": False,
            }
        return rows

    def to_dict(self) -> dict[str, Any]:
        return {
            "taxonomy_version": self.taxonomy_version,
            "command_count": self.command_count,
            "segment_count": self.segment_count,
            "multi_class_command_count": self.multi_class_command_count,
            "single_class_command_count": self.single_class_command_count,
            "unclassified_command_count": self.unclassified_command_count,
            "ambiguous_command_count": self.ambiguous_command_count,
            "four_or_more_class_command_count": self.four_or_more_class_command_count,
            "multi_class_command_share": round(self.multi_class_command_share, 6),
            "single_class_command_share": round(self.single_class_command_share, 6),
            "unclassified_command_share": round(self.unclassified_command_share, 6),
            "ambiguous_command_share": round(self.ambiguous_command_share, 6),
            "multi_segment_command_share": round(self.multi_segment_command_share, 6),
            "leading_cd_command_share": round(self.leading_cd_command_share, 6),
            "class_command_counts": dict(sorted(self.class_command_counts.items())),
            "class_segment_mass": {
                k: round(v, 6) for k, v in sorted(self.class_segment_mass.items())
            },
        }

    def format_report(self) -> str:
        """A pasteable accounting report. Emits no command text and no path."""

        lines = [
            f"taxonomy_version={self.taxonomy_version}  commands={self.command_count}  "
            f"segments={self.segment_count}",
            f"multi-class share   {self.multi_class_command_share:.4f} "
            f"({self.multi_class_command_count} commands at 2+ classes)",
            f"single-class share  {self.single_class_command_share:.4f} "
            f"({self.single_class_command_count})",
            f"UNCLASSIFIED share  {self.unclassified_command_share:.4f} "
            f"({self.unclassified_command_count})  [coverage gap; the regression floor]",
            f"AMBIGUOUS share     {self.ambiguous_command_share:.4f} "
            f"({self.ambiguous_command_count})  [data property, NOT a gap]",
            f"multi-segment share {self.multi_segment_command_share:.4f} "
            f"({self.multi_segment_command_count})",
            f"leading-cd share    {self.leading_cd_command_share:.4f} "
            f"({self.leading_cd_command_count})",
            "per-class command counts (a multi-label command counts in EVERY label):",
        ]
        for name, count in sorted(
            self.class_command_counts.items(), key=lambda kv: (-kv[1], kv[0])
        ):
            mass = self.class_segment_mass.get(name, 0.0)
            lines.append(f"  {name:<24} commands={count:<8} segment_mass={mass:.2f}")
        regressed, reason = self.unclassified_regressed()
        lines.append(
            f"regression floor: {'REGRESSED' if regressed else 'ok'} - {reason}"
        )
        return "\n".join(lines)


def accumulate(classifications: Iterable[Classification]) -> ClassAccounting:
    """Roll classified calls up into one :class:`ClassAccounting`.

    THE FUNCTION TO RUN OVER A LIVE CORPUS to re-measure every figure in
    :data:`CORPUS_BASELINE`. It computes each share from the input, so a baseline that has gone stale
    changes only what :meth:`ClassAccounting.compare_to_baseline` prints, never what is measured.
    """

    command_count = 0
    segment_count = 0
    multi_segment = 0
    leading_cd = 0
    multi_class = 0
    single_class = 0
    unclassified = 0
    ambiguous = 0
    four_plus = 0
    class_counts: dict[str, int] = {}
    class_mass: dict[str, float] = {}

    for item in classifications:
        command_count += 1
        segment_count += item.segment_count
        if item.segment_count > 1:
            multi_segment += 1
        if item.had_leading_cd:
            leading_cd += 1
        if item.is_unclassified:
            unclassified += 1
        if item.is_ambiguous:
            ambiguous += 1
        real = [c for c in item.labels if c is not ActivityClass.OTHER_UNKNOWN]
        if len(real) >= 2:
            multi_class += 1
        elif len(real) == 1:
            single_class += 1
        if len(real) >= 4:
            four_plus += 1
        for activity in item.labels:
            class_counts[activity.value] = class_counts.get(activity.value, 0) + 1
            class_mass[activity.value] = class_mass.get(
                activity.value, 0.0
            ) + item.shares.get(activity, 0.0)

    return ClassAccounting(
        command_count=command_count,
        segment_count=segment_count,
        multi_segment_command_count=multi_segment,
        leading_cd_command_count=leading_cd,
        multi_class_command_count=multi_class,
        single_class_command_count=single_class,
        unclassified_command_count=unclassified,
        ambiguous_command_count=ambiguous,
        four_or_more_class_command_count=four_plus,
        class_command_counts=class_counts,
        class_segment_mass=class_mass,
    )


def _closed_vocabulary() -> frozenset[str]:
    """Every token that may legitimately appear in a persisted record, DERIVED from the tables.

    WHY THIS IS DERIVED RATHER THAN LISTED. A token like ``commit`` appears in the rule identifier
    ``git:commit``, which is a KEY OF :data:`_GIT_SUBCOMMANDS`, i.e. a string written in this file
    rather than an echo of the input. A leak check that flagged it would be unusable; one that
    hard-coded an exception list would silently stop covering a table that later grew. Deriving the
    allowed set from the tables themselves means adding a rule automatically keeps the check correct,
    and a token NOT in any table can only have come from the input.
    """

    allowed: set[str] = {
        "other",
        "unknown",
        "high",
        "medium",
        "low",
        "true",
        "false",
        "null",
    }
    for table in (
        _INSPECTION_HEADS,
        _IMPLEMENTATION_HEADS,
        _TEST_HEADS,
        _LINT_HEADS,
        _DEPENDENCY_HEADS,
        _IDLE_HEADS,
        _NARRATION_HEADS,
    ):
        allowed.update(table.keys())
        allowed.update(str(v) for v in table.values())
    allowed.update(_GIT_SUBCOMMANDS.keys())
    allowed.update(_PY_MODULES.keys())
    allowed.update(_MAKE_TARGETS.keys())
    allowed.update(_AW_SUBCOMMANDS)
    allowed.update(_AMBIGUOUS_INTERPRETERS)
    allowed.update(_WRAPPER_HEADS)
    allowed.update(c.value for c in ActivityClass)
    allowed.update(k.value for k in SegmentKind)
    allowed.update(c.value for c in Confidence)
    allowed.update(name for name, _pattern in _FILE_CATEGORY_RULES)
    # Field names and structural tokens of the serialized form.
    allowed.update(
        {
            "taxonomy_version",
            "labels",
            "display_label",
            "evidence",
            "shares",
            "segment_count",
            "segment_kind",
            "confidence",
            "rule",
            "had_leading_cd",
            "is_multi_class",
            "is_unclassified",
            "is_ambiguous",
            "category",
            "tool",
            "ambiguous",
            "interpreter",
            "redirect",
            "write",
            "impl",
            "inspect",
            "dep",
            "narration",
            "idle",
            "lint",
            "test",
            "git",
            "make",
            "python",
            "module",
            "unrecognized",
            "command",
            "head",
            "subcommand",
            "invocation",
            "file",
            "name",
        }
    )
    # Split multi-part identifiers (`clang-format`, `pre-commit`, `ls-files`) into their parts too,
    # since the token splitter below will encounter them separately.
    for token in list(allowed):
        allowed.update(re.split(r"[^A-Za-z0-9_]+", token))
    return frozenset(t for t in allowed if t)


def assert_no_command_text(record: Any, command: str) -> None:
    """REFUSE if a persisted classification record contains any distinctive part of ``command``.

    THE POINT IS PROOF, NOT POLITENESS. E-01 creates the one place in this Set where the privacy
    boundary and the core algorithm touch: classifying bash REQUIRES reading command text while the
    fact schema forbids persisting it. A reader can inspect :meth:`Classification.to_dict` and see no
    field could hold a command, but a test needs a mechanical check, and this is it. THIS CHECK HAS
    ALREADY EARNED ITS KEEP: it caught a real leak during implementation, where the ``aw`` rule was
    built as ``f"aw:{first_arg}"`` and would have carried an arbitrary next token into a persisted
    record.

    Checks every token of ``command`` at least 4 characters long, EXCLUDING tokens that belong to this
    module's own closed vocabulary (see :func:`_closed_vocabulary`). A token in a table is a string
    written in this file and is not an echo of the input; a token outside every table can only have
    come from the input, which is precisely what must not appear.

    Raises :class:`TaxonomyError` naming the leaked token.
    """

    import json as _json

    allowed = _closed_vocabulary()
    serialized = _json.dumps(
        record if not hasattr(record, "to_dict") else record.to_dict()
    )
    for token in re.split(r"[^A-Za-z0-9_./-]+", str(command or "")):
        if len(token) < 4 or token.lower() in allowed:
            continue
        if token in serialized:
            raise TaxonomyError(
                f"a persisted classification record contains the command token {token!r}; "
                "classification must consume command text at ingest and persist only labels"
            )


def classify_corpus_calls(
    calls: Sequence[Mapping[str, Any]],
) -> tuple[list[Classification], ClassAccounting]:
    """Classify many calls and accumulate them in one pass.

    The convenience entry point for a corpus sweep: returns the per-call classifications (for
    per-event facts) alongside the accounting (for the measured shares). A malformed call is
    classified as unclassified rather than raising, so one bad event costs its own label and nothing
    else.
    """

    results: list[Classification] = []
    for call in calls:
        try:
            results.append(classify(call))
        except TaxonomyError:
            results.append(
                Classification(
                    labels=(ActivityClass.OTHER_UNKNOWN,),
                    evidence={},
                    shares={ActivityClass.OTHER_UNKNOWN: 1.0},
                )
            )
    return results, accumulate(results)
