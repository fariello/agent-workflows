# IPD: 256-color pretty output across all aw verbs by default on TTY

- Date: 2026-08-18
- Kind: child
- Concern: awcolor Order 01 (TODO items 21 + 34). `aw` output is inconsistently colored. The `Term` class (`term.py`) already makes the correct color DECISION centrally (`should_color`, term.py:56-80: honors NO_COLOR / FORCE_COLOR / TERM / `isatty()`) and already supports 256-color escapes (`color256`, term.py:100). But roughly a dozen backend modules BYPASS `Term` entirely, writing with raw `print`/`sys.stdout.write` and taking no `term` argument (backlog.py, specs.py, ipd_lint.py, plans_index.py, plans_refs.py, plans_archive.py, research_cmd.py, research_refs.py, research_index.py, research_archive.py, ipd_authoring.py, leak_sanitizer.py), so their human-readable output never colorizes. This Order routes the THREE HIGHEST-VALUE surfaces (specs.py, backlog.py, ipd_lint.py) through `Term` so they colorize by default on a TTY and stay plain when piped / NO_COLOR / `--no-color`, applies a consistent 256-color style vocabulary to them, and proves the on/off policy with a test. The remaining nine raw-print modules are listed in Deferred for follow-up Orders.
- Scope: THREE existing modules edited (`agent_workflows/specs.py`, `agent_workflows/backlog.py`, `agent_workflows/ipd_lint.py`) + ONE new test file (`tests/test_color_output.py`). IN: build a `Term` inside each of these modules' `run_*` entrypoints from the already-parsed `--no-color` flag (`args.no_color`), replace their raw `print`/`sys.stdout.write` HUMAN-readable writes with `Term`-mediated colorized output, and apply a small 256-color style vocabulary (status/severity words, headings, ids, paths) via `Term.color256`. OUT: no change to `should_color` policy (term.py:56-80) or to the `--no-color` flag on the shared `common` parent (cli.py:371); the shared `Term` at cli.py:4033 is unchanged; the machine-readable `--agent`/`--json` branches (`core.render_agent_drift`, the tab-separated lint records) STAY uncolored; the other nine raw-print modules are NOT touched here (Deferred).
- Status: reviewed
- Set: awcolor
- Order: 1
- Highest E allocated: 03
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: u88tb7

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from TODO items 21,34 (Set awcolor).
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against term.py:56-100, specs.py:296-326, backlog.py:464-472, and ipd_lint.py:761-826; styling and accessibility invariants sound; structural lint conforming; no findings; no blocking open questions; GO - PENDING HUMAN APPROVAL.

## Goal

Make the three highest-value `aw` verb surfaces (`aw specs`, `aw backlog`, `aw ipd lint`) emit pretty,
256-color output by default on an interactive TTY, and cleanly plain when NO_COLOR / `--no-color` / a
pipe is in effect, by building a `Term` inside each module's `run_*` from the already-parsed `--no-color`
flag and routing their human-readable writes through it instead of bypassing it with raw `print`. The
machine-readable `--agent` branches stay byte-for-byte uncolored. A named test pins the on/off policy and
the accessibility invariant (the status WORD is always present, so color is never the sole signal).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Do EXACTLY the steps below, in order. Edit ONLY the three modules named in Scope and
create ONLY `tests/test_color_output.py`. Do NOT touch `term.py`, `cli.py`, or any of the other nine
raw-print modules (they are Deferred). The `--no-color` flag is ALREADY parsed on the shared `common`
parent (cli.py:371), so every `args` passed to these `run_*` functions has `args.no_color`. Build the
`Term` from it, exactly as `cli.py` does at line 4033: `Term(color=False if getattr(args, "no_color", False) else None)`.
Leave EVERY `--agent` / tab-separated branch UNCOLORED. Use 4-space indentation.

### Task group 1: thread Term into the raw-print run_* functions (specs, backlog, ipd_lint)

- [ ] E-01 Add a `Term` import and build a `Term` from `args.no_color` at the top of each human-readable branch in the three modules, then replace the HUMAN-readable `sys.stdout.write`/`print` calls (NOT the `--agent` branches) with `term`-mediated writes.
  1. In `agent_workflows/specs.py`, add to the import block (after `from agent_workflows import attention_contract as A`, specs.py:24):
     ```python
     from agent_workflows.term import Term
     ```
     Then in `run_check` (specs.py:296), leave the `if getattr(args, "agent", False):` branch (specs.py:316-317, the `core.render_agent_drift` write) UNTOUCHED, and in the `else:` branch (specs.py:318-326) build a term and route the human output through it:
     ```python
     else:
         term = Term(color=False if getattr(args, "no_color", False) else None)
         if drift:
             for d in drift:
                 term.line(f"{term.color256(d.location, _C_PATH)}: {term.color256(d.rule, _C_RULE)}: {d.detail}")
             term.line(
                 "Move pipeline metadata/status into a bare-enum `- Status:` bullet and a conformant history; see the specs contract."
             )
         else:
             term.status("ok", "aw specs check: all specs conform.")
     ```
     Also convert the three success writes in `run_set` (specs.py:418), `run_migrate` (specs.py:546), and `run_note` (specs.py:561) to use a `term` built the same way, e.g. replace specs.py:418 `sys.stdout.write(f"aw specs set: {path} -> {new}\n")` with:
     ```python
     term = Term(color=False if getattr(args, "no_color", False) else None)
     term.status("ok", f"aw specs set: {term.color256(str(path), _C_PATH)} -> {term.color256(new, _C_ID)}")
     ```
     (Apply the same shape to `run_migrate`/`run_note`.) The `_C_*` style constants are defined in E-02.
  2. In `agent_workflows/backlog.py`, add `from agent_workflows.term import Term` to the import block, leave the `--agent` branch in `run_check` (backlog.py:464-465) UNTOUCHED, and in the `else:` branch (backlog.py:466-472) build a `term` and route the human output through it (mirror the specs.py:318 pattern: color the location/rule via `color256`, emit `term.status("ok", ...)` on the clean path and a `term.status("warn", f"...{len(drift)} violation(s).")` on the drift path). Convert the `run_new` success write (backlog.py:334) and the `run_set` success write (backlog.py:388) to `term.status("ok", ...)` the same way. Leave the DRY-RUN writes (backlog.py:330, backlog.py:382) as-is (they are literal file previews, not status lines).
  3. In `agent_workflows/ipd_lint.py`, add `from agent_workflows.term import Term` to the import block, and in `run_lint` (ipd_lint.py:761) build `term = Term(color=False if getattr(args, "no_color", False) else None)` at the top of the function. Leave the `if agent:` branches (ipd_lint.py:783-791 and ipd_lint.py:810-816) UNTOUCHED. In the NON-agent branches, colorize the disposition WORD and diagnostic codes: replace `print("disposition: {0}".format(res.disposition))` (ipd_lint.py:821) with `term.line("disposition: " + term.color256(res.disposition, _disp_color(res.disposition)))` and replace the per-file `print("{0}: {1}".format(res.disposition, f))` (ipd_lint.py:793) similarly. Keep the `_disp_color` helper defined in E-02.
  - Depends on: none
  - Expected outcome: with `FORCE_COLOR=1`, `aw specs check`, `aw backlog check`, and `aw ipd lint <file>` emit ANSI SGR codes; with `NO_COLOR=1` or `--no-color` or a piped stdout they emit none; the `--agent` output of all three is byte-for-byte unchanged (still no ANSI).
  - Execution state: pending

### Task group 2: consistent 256-color style vocabulary

- [ ] E-02 Add a single shared style vocabulary used by all three modules so headings, ids, paths, and severity are colored consistently. Add these module-level constants near the top of EACH of the three modules (after imports), OR (preferred) define them once in a tiny shared spot and import them; if defining locally, use these EXACT xterm-256 palette indices so the three surfaces match:
  ```python
  # awcolor style vocabulary (xterm-256 palette indices; color is always redundant to a WORD/label).
  _C_HEADING = 45   # bright cyan-ish: section headings
  _C_ID = 213       # magenta: id6 / handles / new-status values
  _C_PATH = 244     # gray: file paths / locations (de-emphasis)
  _C_RULE = 178     # amber: rule / diagnostic codes
  ```
  For `ipd_lint.py`, add the disposition-color helper so the disposition WORD is colored by outcome (green conforming, amber quarantined/legacy, red error) while the word itself is always printed:
  ```python
  def _disp_color(disposition: str) -> int:
      return {
          S.DISPOSITION_CONFORMING: 2,    # green
          S.DISPOSITION_QUARANTINED: 178, # amber
          S.DISPOSITION_LEGACY: 244,      # gray
          S.DISPOSITION_ERROR: 1,         # red
      }.get(disposition, 244)
  ```
  Apply these constants at the call sites introduced in E-01 (the `color256(..., _C_PATH)` / `_C_RULE` / `_C_ID` calls and `_disp_color(...)`). Do NOT invent per-call raw escapes; all color goes through `Term.color256` (term.py:100) so `should_color` (term.py:56-80) still fully gates it. The status WORD (OK / WARN / the disposition string) is ALWAYS emitted regardless of color (accessibility: color is never the sole signal).
  - Depends on: E-01
  - Expected outcome: the three surfaces use the same palette for the same semantic role; the disposition word is green/amber/red by outcome under `FORCE_COLOR` and plain under `NO_COLOR`; the literal disposition string is present in both cases.
  - Execution state: pending

### Task group 3: policy + accessibility test

- [ ] E-03 Create `tests/test_color_output.py` with a `unittest.TestCase` subclass `ColorOutputPolicyTests` that runs one of the touched verbs (`aw ipd lint <a conforming fixture plan>`) three ways and asserts the color policy and the accessibility invariant. Save/restore `NO_COLOR`/`FORCE_COLOR`/`TERM` in `setUp`/`tearDown` (mirror tests/test_term.py:26-36). Write EXACTLY these test methods:
  ```python
  """Policy + accessibility test for awcolor: aw verb output colorizes on a forced TTY,
  stays plain under NO_COLOR / --no-color / a pipe, and always prints the status WORD."""

  from __future__ import annotations

  import io
  import os
  import re
  import unittest
  from contextlib import redirect_stdout

  from agent_workflows import ipd_lint

  _ANSI = re.compile(r"\033\[[0-9;]*m")


  class _Args:
      def __init__(self, path, no_color=False, agent=False):
          self.path = path
          self.phase = "author"
          self.all = False
          self.agent = agent
          self.legacy = False
          self.no_color = no_color


  class ColorOutputPolicyTests(unittest.TestCase):
      def setUp(self):
          self._saved = {k: os.environ.get(k) for k in ("NO_COLOR", "FORCE_COLOR", "TERM")}
          # A known-conforming plan already in the repo (the awselect exemplar) as the fixture.
          self.plan = ".aw/records/plans/pending/20260818-awselect-01-axkviw-shared-selector-resolver-module.ipd.md"

      def tearDown(self):
          for k, v in self._saved.items():
              if v is None:
                  os.environ.pop(k, None)
              else:
                  os.environ[k] = v

      def _run(self):
          buf = io.StringIO()
          with redirect_stdout(buf):
              ipd_lint.run_lint(_Args(self.plan))
          return buf.getvalue()

      def test_force_color_emits_ansi(self):
          os.environ.pop("NO_COLOR", None)
          os.environ["FORCE_COLOR"] = "1"
          out = self._run()
          self.assertRegex(out, _ANSI.pattern)      # ANSI SGR present
          self.assertIn("disposition", out)          # the WORD is still present

      def test_no_color_emits_no_ansi(self):
          os.environ.pop("FORCE_COLOR", None)
          os.environ["NO_COLOR"] = "1"
          out = self._run()
          self.assertNotRegex(out, _ANSI.pattern)    # no ANSI
          self.assertIn("disposition", out)          # WORD still present (accessibility)

      def test_no_color_flag_emits_no_ansi(self):
          os.environ.pop("NO_COLOR", None)
          os.environ["FORCE_COLOR"] = "1"             # even with FORCE_COLOR on...
          buf = io.StringIO()
          with redirect_stdout(buf):
              ipd_lint.run_lint(_Args(self.plan, no_color=True))  # ...--no-color wins
          out = buf.getvalue()
          self.assertNotRegex(out, _ANSI.pattern)
          self.assertIn("disposition", out)

      def test_piped_stdout_is_plain(self):
          os.environ.pop("NO_COLOR", None)
          os.environ.pop("FORCE_COLOR", None)
          os.environ["TERM"] = "xterm-256color"
          # redirect_stdout to a StringIO => isatty() False => should_color() False.
          out = self._run()
          self.assertNotRegex(out, _ANSI.pattern)
          self.assertIn("disposition", out)
  ```
  Then run the full serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-01,E-02
  - Expected outcome: all four test methods pass (FORCE_COLOR => ANSI present; NO_COLOR / `--no-color` / piped stdout => no ANSI; the literal `disposition` WORD present in every case); full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `Term.should_color` (term.py:56-80) already implements the full policy: `NO_COLOR` off (unless `FORCE_COLOR`), `FORCE_COLOR` on, `TERM=dumb`/unset off, else color only when stdout `isatty()`. This is the single source of truth; do NOT reimplement it per module.
- `Term.color256(text, code, *, bold=False)` (term.py:100) emits `\033[38;5;Nm...` when color is on and returns plain text when off; `code` is clamped 0-255. All new color goes through it.
- `Term(color=False if args.no_color else None)` is the exact construction pattern used in `cli.py:4033`; the `--no-color` flag lives on the shared `common` parent (cli.py:371) so it is always present on `args`. Each raw-print `run_*` can build its own `Term` from `args.no_color` (they are not passed the shared `term`).
- The three target modules bypass `Term` today: specs.py writes with `sys.stdout.write` (run_check 316-326, run_set 418, run_migrate 546, run_note 561); backlog.py the same (run_new 334, run_set 388, run_check 464-472); ipd_lint.py writes with `print` (run_lint 761-826).
- Machine-readable output MUST stay uncolored: the `--agent` branches call `core.render_agent_drift` (artifact_core.py:255, tab-separated `location\trule\tdetail`) and ipd_lint emits `\t`-separated `FILE\tCODE\tmessage` records (ipd_lint.py:785-791, 811-816). Those branches are left untouched.
- Status WORDS already exist in `Term.status`/`status_label` (term.py:115-132: OK/WARN/FAIL...), so the accessibility invariant (word first, color redundant) is reused, not reinvented.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Color decision + 256-color already exist centrally in `Term` (term.py:56-80, :100). | No new policy code; the work is plumbing + styling, not decision logic. |
| F2 | ~12 backends bypass `Term`; this Order converts only the 3 highest-value (specs, backlog, ipd_lint). | Scope is bounded and mechanical; the other 9 are explicitly Deferred. |
| F3 | `--no-color` is already parsed on the shared parent (cli.py:371) and present on `args`. | Each `run_*` can build its own `Term(color=False if args.no_color else None)` (the cli.py:4033 pattern). |
| F4 | `--agent`/`--json` output must stay machine-clean (artifact_core.py:255; ipd_lint tab records). | The `--agent` branches are left UNTOUCHED so structured output is never colorized. |
| F5 | Status WORDS are always printed by `Term.status` regardless of color (term.py:129-132). | Color is never the sole signal; the accessibility invariant is reused. |

## Proposed changes (ordered, validatable)

1. Thread a `Term` (built from `args.no_color`) into the human-readable branches of specs.py / backlog.py / ipd_lint.py `run_*` functions and replace their raw writes, leaving the `--agent` branches untouched (E-01).
2. Add a shared 256-color style vocabulary (`_C_HEADING`/`_C_ID`/`_C_PATH`/`_C_RULE` + `_disp_color`) on `Term.color256` and apply it at the E-01 call sites (E-02).
3. Add `tests/test_color_output.py` with the four-case policy + accessibility test and run the full serial suite (E-03).

## Deferred / out of scope (with reason)

- The remaining NINE raw-print modules are NOT converted here (follow-up Orders in Set awcolor): `plans_index.py`, `plans_refs.py`, `plans_archive.py`, `research_cmd.py`, `research_refs.py`, `research_index.py`, `research_archive.py`, `ipd_authoring.py`, `leak_sanitizer.py`. This Order deliberately scopes to the three highest-value surfaces to stay small.
- Any change to `should_color` policy (term.py:56-80) or the `--no-color` flag surface (cli.py:371): out of scope; both are already correct.
- A user-configurable theme/palette system or an `AW_COLOR=always|auto|never` override: out of scope (see OQ-01); the goal is a sane default, not configurability.
- Coloring the machine-readable `--agent`/`--json` output: explicitly excluded (must remain parseable).

## Scope check

- Over-scope: none - only 3 existing modules + 1 new test; the central policy and flag are reused, not rebuilt.
- Under-scope: none for THIS Order's stated target - E-01 routes the three surfaces through `Term`, E-02 makes them consistently pretty, E-03 proves the four disable/enable cases and the accessibility invariant. The other nine modules are named in Deferred as explicit follow-up, so nothing is silently dropped.

## Required tests / validation

`tests/test_color_output.py` (E-03, four named methods: FORCE_COLOR emits ANSI; NO_COLOR emits none; `--no-color` overrides FORCE_COLOR; piped stdout is plain; the `disposition` WORD present in every case) plus the full serial suite to confirm no regression in existing output-asserting tests. Each V-item pins one E.

## Spec / documentation sync

No spec transition here (no owning spec for this Set; the default-on-TTY color behavior is already implied by the existing `--no-color` help text at cli.py:375). If the executor finds a verb help string that promises plain-only output, update it; otherwise N/A. AGENTS.md needs no change (internal styling).

## Open questions

### OQ-01: should there be an `AW_COLOR=always|auto|never` override in addition to NO_COLOR/`--no-color`?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Recommendation: rely on the existing NO_COLOR / FORCE_COLOR / `--no-color` triad for this plan and defer a dedicated `AW_COLOR` env var unless a maintainer wants it; adding it later is additive and non-blocking, so it does not gate this Order.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `FORCE_COLOR=1 python3 -m agent_workflows ipd lint --phase author <a conforming plan>` showing ANSI escapes in the disposition line, AND `NO_COLOR=1 python3 -m agent_workflows ipd lint --phase author <same plan>` showing none; plus a grep confirming `from agent_workflows.term import Term` now appears in specs.py, backlog.py, and ipd_lint.py, and that each `--agent` branch is unchanged (paste `python3 -m agent_workflows ipd lint --phase author --agent <plan>` producing tab-separated records with NO ANSI).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `FORCE_COLOR=1 python3 -m agent_workflows ipd lint --phase author <a non-conforming plan>` showing the disposition word colored red/amber and diagnostic codes colored, and the same command under `NO_COLOR=1` showing the identical WORDS with no ANSI (proving color is redundant); confirm the `_C_*` constants and `_disp_color` exist via a grep.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_color_output.py -p no:xdist -q` showing 4 passed, AND the tail of the full serial suite `python3 -m pytest -p no:xdist` showing no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, with opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the three edited
modules + the one new test file path-scoped (never `git add -A`), never pushes, and the plan moves to
`.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item
is `pass`. Order 01 of awcolor; the remaining nine raw-print modules (see Deferred) are follow-up Orders.
