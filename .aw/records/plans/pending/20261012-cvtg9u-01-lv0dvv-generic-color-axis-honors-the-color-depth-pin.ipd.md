# IPD: Generic color axis honors the color_depth pin

- Date: 2026-10-12
- Kind: child
- Concern: Backlog `cvtg9u` (finding F-08 of executed plan `y2ge26`): the user-facing `color_depth` config pin is documented in `config.CONFIG_SCHEMA` as "Pin the terminal color depth (256, 16, or none) instead of detecting it", but only the LIFECYCLE axis (`Term.style_lifecycle_text`, `Term.format_lifecycle_marker`, `render_stream.Palette.lifecycle`) consults the resolved tier. The GENERIC axis (`Term.colorize`, `Term.color256`, and everything built on them: `status_256`, `badge`, `format_path`/`path`, `severity_label`, `format_fix`, `format_next_action`, headers, tables) gates only on the boolean `Term.color`. Measured in this lane at HEAD `3ecef6088` with the pin at `none` on a capable TTY (`TERM=xterm-256color`): `Term.status_256("up to date")` returns `'\x1b[1;38;5;46mup to date\x1b[0m'`, `Term.path("a/b")` returns `'\x1b[38;5;33ma/b\x1b[0m'`, `Term.colorize("x","bold")` returns `'\x1b[1mx\x1b[0m'`, while `Term.lifecycle_depth()` returns `none`; at pin `16`, `Term.status_256` still emits `38;5;46` and `Term.badge("x","error")` emits `38;5;196`. Across real CLI commands with `--color` at pin `none`: `aw ipd lint` emits 85 `1;38;5;46` and 48 `1;38;5;244` sequences, `aw check` emits 110 `1;38;5;39` and 48 `1;38;5;196`.
- Scope: IN: make `Term.colorize` and `Term.color256` in `agent_workflows/term.py` consult the ONE existing resolver (`Term.lifecycle_depth`, which delegates to `term.resolve_color_depth`), so the `none` tier emits no escape on the generic axis and the `16` tier emits no `38;5;` sequence; add one behavioral test file. The 256 tier is byte-identical to today. OUT: modules that emit hard-coded SGR literals without going through `Term` (`pwatch.py`, `runners_monitor.py`, `render_stream.py` header/statusline literals, `render_stream.Palette.__call__`), filed as backlog `y11p5u`; the lifecycle axis (already correct, guarded by `tests/test_term.py`); any change to `should_color` or `resolve_color_depth` precedence; a per-role authored 16-color generic palette (see OQ-02).
- Scope-Paths: agent_workflows/term.py, tests/test_generic_color_depth.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Blocks-Release: next
- Priority: medium
- From-Backlog: cvtg9u
- Set: cvtg9u
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: lv0dvv

## Workflow history
- 2026-10-12 same-status (aw set): Maintainer ruling 2026-10-12: pin none must disable all color (reading B); OQ-01 still to be marked resolved + plan approved by maintainer

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `cvtg9u`. Reproduced F-08 in the lane, measured a prototype of the fix against the full bare suite at two `TERM` values (zero new failures) and across seven CLI commands at pins `none` and `16` (zero escapes at `none`, zero `38;5;` at `16`), measured that an unmemoized resolver call costs no end-to-end time, filed the out-of-`Term` raw-literal residue as backlog `y11p5u`, and left the scope ruling the item reserves for the maintainer as OQ-01 (owner maintainer, gated by E-01).

## Goal

Make the `color_depth` pin mean what its user-facing description says on every surface rendered through `Term`, not only on lifecycle tokens: pin `none` yields escape-free output, pin `16` yields no 256-color sequences, pin `256` (and the unpinned default) is unchanged. This is the implementation branch of the scope question backlog `cvtg9u` reserves for the maintainer (OQ-01); it is held behind that question rather than executed on an agent's reading.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: confirm the ruling and capture a baseline

- [ ] E-01 CONFIRM THE MAINTAINER'S SCOPE RULING BEFORE CHANGING ANYTHING. Read this plan's `## Open questions`. Proceed ONLY if OQ-01 reads `- Status: resolved` with a ruling, attributed to the maintainer, that `color_depth` governs the generic axis (reading B), AND this plan's `- Status:` is `approved` with a `- Approval:` line. Also check whether backlog `cvtg9u` was reclassified as the item itself directs on that ruling ("reclassified as `bug` with `- Blocks-Release: next` via `aw backlog set`"). Reclassifying is part of the human's ruling act, not this item's job, so only RECORD whether this plan's `- Work-Kind:`/`- Blocks-Release:` match the item's, and report any mismatch. If OQ-01 is open or resolved to reading A (lifecycle-only), mark this item `blocked`, change no file, and report that the ruling belongs to the maintainer.
  - Depends on: none
  - Expected outcome: the quoted resolved OQ-01 ruling, the `- Status: approved` and `- Approval:` lines, and the recorded Work-Kind/Blocks-Release comparison; or a `blocked` item with no file changed.
  - Execution state: pending

- [ ] E-02 CAPTURE THE BASELINE: run the bare suite `python3 -m pytest` BEFORE the first edit and record its summary line and the failing node ids. (Measured at authoring in this lane: `39 failed, 7180 passed, 2 skipped`, every failure in no-project / outside-project tests such as `tests/test_no_project_exit_is_cannot_run.py` and `tests/test_validator_nonsurveyable_dir.py`, which fail identically with this plan's change reverted, i.e. they are lane-environment failures unrelated to color.) The post-change bar is "no node id fails that did not fail here".
  - Depends on: E-01
  - Expected outcome: a recorded baseline summary line and failing-node-id list.
  - Execution state: pending

### Task group 2: the fix

- [ ] E-03 In `agent_workflows/term.py`, make the two generic emitters consult the resolved tier. In `Term.colorize`, after the existing `if not self.color or not styles: return text` guard, add `if self.lifecycle_depth() == DEPTH_NONE: return text`. In `Term.color256`, after the existing `if not self.color: return text` guard, resolve `tier = self.lifecycle_depth()`; return `text` unchanged at `DEPTH_NONE`; at `DEPTH_16` return `f"\033[{prefix}{sgr}m{text}{_RESET}"` where `sgr` is produced by a new module-level pure function `color_16_for_index(code: int) -> int` (below); at `DEPTH_256` keep today's exact `38;5;N` output. `color_16_for_index` maps an xterm-256 index to one of the named SGR foreground codes already defined in the module (`_SGR_RED` .. `_SGR_BRIGHT_CYAN`, plus `_SGR_BRIGHT_BLACK` for the grays) by a standard nearest-color reduction over the xterm-256 cube/grayscale ramp, so the generic 196 (failure) becomes red, 46 (success) green, 226/214 (warn/advisory) yellow, 39/33 (info/paths) blue or cyan, and 244/245/250 neutrals bright-black. Its docstring states WHY a derived mapping is acceptable here although R9.3a.3 forbids one for lifecycle stages: the generic role palette carries no ready/done-style separations that a merge could destroy, every generic outcome already prints a WORD (docs/cli-human-guide.md "Color and accessibility"), and the authored-table obligation is scoped by spec `uonrjg` to the twenty lifecycle stages. Update the `color256` docstring (it currently says escapes are gated only by `should_color`) and the `colorize` docstring to name the depth rung. Do NOT change `lifecycle_depth`, `resolve_color_depth`, `should_color`, or any lifecycle method. Do NOT memoize: measured at authoring, an unmemoized `lifecycle_depth()` per call costs about 490us in isolation, yet `aw find backlog --color` (about 5.8k escapes) ran in 0.93/0.88/0.91 s with the prototype versus 1.09/0.96/0.97 s at baseline, i.e. no end-to-end regression a user could perceive, so a cache would add invalidation risk for no measured gain.
  - Depends on: E-02
  - Expected outcome: at pin `none` on a capable TTY, `Term.status_256`, `Term.path`, `Term.badge`, `Term.colorize`, `Term.severity_label` return plain text; at pin `16` they return escapes containing no `38;5;`; at pin `256` and unpinned they are byte-identical to HEAD.
  - Execution state: pending

### Task group 3: tests and changelog

- [ ] E-04 Add `tests/test_generic_color_depth.py`, a behavioral test file (no source reading, per P16). Reuse the isolation pattern of `tests/test_term.py`'s `_DepthTestBase` (point `XDG_CONFIG_HOME` at a temp dir, clear `NO_COLOR`/`FORCE_COLOR`/`COLORTERM`, set `TERM=xterm-256color`, clear the override, pin via `config.set_config_value("color_depth", ...)`). Cells: (a) pin `none`, fake TTY: each of `status_256("up to date")`, `path("a/b")`, `badge("x","error")`, `colorize("x","bold")`, `severity_label("error")`, `format_fix("do it")` contains no `\x1b`, and the WORD is still present; (b) pin `16`: each is styled (contains `\x1b`) and contains no `38;5;`, and `status_256("error")` and `status_256("up to date")` render DIFFERENT SGR codes (failure is not success); (c) pin `256`: `status_256("up to date") == '\x1b[1;38;5;46mup to date\x1b[0m'` and `path("a/b") == '\x1b[38;5;33ma/b\x1b[0m'` (today's bytes); (d) `NO_COLOR=1` with pin `256` still yields plain text (NO_COLOR outranks the pin, R9.3a.2); (e) `Term(stream=<fake pipe>, color=True)` with pin `16` styles at 16 rather than collapsing to none (the `override=True` behavior `lifecycle_depth` already has); (f) `color_16_for_index` returns a code in the named 30-37/90-97 set for every index 0-255; (g) END TO END: in a synthesized `git init` fixture repo with one backlog item and `AW_NO_REEXEC=1`, `PYTHONPATH` at this checkout, run `python -m agent_workflows find backlog --color` and `python -m agent_workflows index plans --color` as subprocesses at each pin and assert: pin `none` stdout contains no `\x1b`; pin `16` contains `\x1b` and no `38;5;`; pin `256` contains `38;5;`. Do NOT edit `tests/test_term.py` (not in Scope-Paths); its two now-stale "generic axis ignores the depth pin per F-08" docstring caveats are carried by backlog `y11p5u` (see Deferred).
  - Depends on: E-03
  - Expected outcome: the new file passes with E-03 applied and its cells (a), (b), (g) FAIL with E-03 reverted (demonstrated once, see V-04).
  - Execution state: pending

- [ ] E-05 Add one `- Fixed:` bullet at the top of the `## 2.0.0 (pending)` change list in `CHANGELOG.md`: the `color_depth` pin now also governs general command styling (outcome words, paths, badges, severity labels), so `none` removes all color from those surfaces and `16` uses basic ANSI colors; no em or en dashes (user-facing prose rule).
  - Depends on: E-03
  - Expected outcome: one new bullet, no other CHANGELOG line changed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- One depth resolver: spec `uonrjg` R9.3a.2 requires the tier to have "exactly one definition"; `term.resolve_color_depth` is it, and `Term.lifecycle_depth` is the `Term`-bound accessor (forwarding `override=True` so an explicit `Term(color=True)` is not re-litigated against a pipe). The fix calls that accessor; it adds no second resolver.
- `NO_COLOR` outranks the pin structurally because `resolve_color_depth` returns `none` via `should_color` before reading the pin; the generic axis inherits this by calling the same function.
- Behavioral tests only (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE", GUIDING_PRINCIPLES P16); `tests/test_term.py` `ColorDepthEndToEndLadderTests` and `LifecycleColorDepthCrossSurfaceCliTests` show the subprocess pattern (`AW_NO_REEXEC=1`, `PYTHONPATH`, isolated `XDG_CONFIG_HOME`).
- Run the suite bare (`python3 -m pytest`), never `-n0` or extra `-q` (AGENTS.md repo-local development contract).
- User-facing prose (CHANGELOG) carries no em/en dashes.
- Commit via `aw commit lv0dvv -- <paths>`.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The pin is ignored on the generic axis at `none` and at `16`. | Lane repro at `3ecef6088` (Concern): pin `none` -> `status_256` emits `1;38;5;46`, `lifecycle_depth()` returns `none`; pin `16` -> `badge("x","error")` emits `1;38;5;196`. |
| F-02 | The two emitters `Term.colorize` and `Term.color256` are the only generic escape sites in `Term`; every other generic helper (`status_256`, `badge`, `format_path`, `severity_label`, `format_fix`, `format_next_action`, headers, tables, `confirm` hints) composes them. | `grep -n 'color256\|colorize' agent_workflows/term.py`: the only `\033[` f-strings in `Term` are in `colorize`, `color256`, and `style_lifecycle_text`. |
| F-03 | Fixing those two sites closes the CLI-observable symptom across the commands the item lists. | Prototype measured: pin `none` -> 0 escapes from `aw index plans`, `aw ipd lint`, `aw check`, `aw find backlog`, `aw attention`, `aw ipd board`, `aw doctor` (each with `--color`); pin `16` -> 0 `38;5;` sequences from all seven. |
| F-04 | The prototype breaks no existing test. | Full bare suite with the prototype at `TERM=xterm-256color` and `TERM=vt100`: `39 failed, 7180 passed, 2 skipped` both times; with the prototype reverted the same 11 files yield `39 failed, 249 passed`, i.e. all 39 are pre-existing no-project-environment failures. |
| F-05 | No perceptible performance cost from calling the resolver per escape. | `aw find backlog --color` 0.93/0.88/0.91 s prototype vs 1.09/0.96/0.97 s baseline; `aw check --color` 16.65/16.78/16.69 s vs 16.96/16.71/16.74 s. |
| F-06 | Raw SGR literals outside `Term` still bypass the pin and are NOT reached by this fix. | `grep -c '38;5;'`: `pwatch.py` 19, `runners_monitor.py` 7, `render_stream.py` 14 (excluding docstrings); `render_stream.Palette.__call__` gates on `enabled` only. Filed as backlog `y11p5u`. |
| F-07 | The scope conflict the item names is real and unresolved in repo text. | Spec `uonrjg` Section 3 non-goal: "Replacing finding-severity icons or generic command outcome icons that are not lifecycle states"; R10.3: "Generic `Term` outcomes such as command-level OK, WARN, and FAIL remain valid and are outside this spec." Versus DECISIONS D42 ("honor `NO_COLOR`/`FORCE_COLOR`/`TERM`/`isatty()` and degrade through 256/16/none", not restricted to lifecycle) and `config.CONFIG_SCHEMA`'s unqualified description. |

## Proposed changes (ordered, validatable)

1. Gate on the maintainer's ruling (E-01) and record a suite baseline (E-02).
2. Route `Term.colorize` and `Term.color256` through `Term.lifecycle_depth()` with a derived 256->16 reduction for generic roles (E-03).
3. Add behavioral unit + subprocess tests (E-04) and a CHANGELOG bullet (E-05).

## Deferred / out of scope (with reason)

- Raw SGR literals in `pwatch.py`, `runners_monitor.py`, `render_stream.py` (header/statusline) and `render_stream.Palette.__call__`: they do not go through `Term`, so they need a different routing change in three modules with their own tests; filed during this authoring.
  - Carrier: y11p5u
- The two now-stale caveats in `tests/test_term.py` (`LifecycleColorDepthSeamSweepTests` and `LifecycleColorDepthCrossSurfaceCliTests` docstrings, "generic axis ... ignores the depth pin entirely per finding F-08, tracked in carrier backlog item cvtg9u"): docstring-only, left out of Scope-Paths to keep this plan minimal; the executor names them in V-04 evidence, and backlog `y11p5u` (same ladder, same test file) records the docstring edit explicitly.
  - Carrier: y11p5u
- An AUTHORED 16-color generic role palette: see OQ-02; the derived reduction is sufficient because generic outcomes always carry a word.
  - Carrier-Declined: resolved by OQ-02 as unnecessary, so there is no outstanding work to carry
- Amending spec `uonrjg`: NOT done. On reading B the spec stays correct as written (its non-goal is about REPLACING generic icons/styles with lifecycle ones, which this plan does not do; it only makes them degrade), and the depth obligation comes from D42 and the config contract. If the maintainer instead wants the spec to state the generic-axis obligation, that is a spec edit for them to direct.
  - Carrier-Declined: no spec change is needed on either reading; any amendment is the maintainer's call at OQ-01

## Scope check

- Over-scope: none. Only the two emitters every generic helper composes are changed; no lifecycle code, resolver, or precedence changes.
- Under-scope: raw-literal modules outside `Term` (F-06) remain on 256 at pins `none`/`16`; explicitly carried by `y11p5u`, so the item's "every CLI command" symptom is closed for every `Term`-rendered command (F-03) but not for `aw pwatch`, `aw runners`, or runner stream headers.

## Required tests / validation

- `python3 -m pytest tests/test_generic_color_depth.py tests/test_term.py -o addopts=""` passes (new file plus the lifecycle ladder guards, so the lifecycle axis is proven unchanged).
- Bare `python3 -m pytest`: no node id fails that was not in the E-02 baseline.
- Negative control: with E-03 temporarily reverted (save it with `git diff agent_workflows/term.py > /tmp/opencode/lv0dvv.patch`, `git checkout -- agent_workflows/term.py`, run the new file, then `git apply /tmp/opencode/lv0dvv.patch`; never `git stash`), cells (a), (b), (g) of the new file fail.
- CLI spot check at pins `none`/`16`/`256` for `aw ipd lint --color`, `aw check --color`, `aw index plans --color` with escape and `38;5;` counts.
- `aw ipd lint` on this plan conforms at `pre-transition` before the terminal move.

## Spec / documentation sync

- Spec `uonrjg`: N/A, not amended (see Deferred: the spec's non-goal does not conflict with reading B, and it is not in Scope-Paths).
- `CHANGELOG.md`: one `- Fixed:` bullet (E-05).
- `docs/cli-human-guide.md` "Color and accessibility" already states "degrading through 16-color ANSI and then no-color monochrome. Users can pin their preferred color depth", which this plan makes TRUE for general styling; no edit needed (measured).
- `config.CONFIG_SCHEMA` description: unchanged; it already describes the post-fix behavior.

## Open questions

### OQ-01: Does the `color_depth` pin govern the generic (non-lifecycle) styling axis?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: cvtg9u
- Resolution or deferral rationale: OPEN FOR THE MAINTAINER. Marked non-blocking ONLY so the plan lints conforming at authoring (a blocking open question is `IPD-Q501`, an error); the stop is E-01, which refuses to edit anything until this question reads resolved to reading B with an `approved` status and a human `- Approval:` line. A reviewer MAY flip this to `- Blocking: yes` (precedent: plan `15db4k` OQ-01, review PR-001) to make the stop mechanical against `--full-auto`. Backlog `cvtg9u` states "Resolving this conflict requires a maintainer decision, as fixing it would change user-visible styling across all non-lifecycle surfaces in the package." READING A (lifecycle-only): spec `uonrjg` Section 3 lists "generic command outcome icons that are not lifecycle states" as a non-goal and R10.3 says generic `Term` outcomes "are outside this spec"; on this reading the pin is lifecycle-scoped, this plan is retired to `not-executed`, and the honest remedy is instead to qualify the `color_depth` description in `config.CONFIG_SCHEMA` (a separate small item). READING B (all styling): DECISIONS D42 states the ladder as a general accessibility obligation and the config description makes no lifecycle qualification; a user who pins `none` reasonably expects no color. Author's recommendation (non-binding): B, because a preference labeled "Pin the terminal color depth" that leaves 85+ 256-color sequences in `aw ipd lint` is surprising, the fix is two call sites with no measured test or performance cost (F-03..F-05), and the 256 tier is byte-identical. TO ANSWER: for B, set `- Status: resolved` here with the date and ruling, reclassify the item as it directs (`aw backlog set cvtg9u --work-kind bug --blocks-release next`), mirror that on this plan (`aw ipd set to-review lv0dvv --work-kind bug --blocks-release next` or at approval), then approve with `aw ipd set approved lv0dvv --by-human --message ...`. For A, retire this plan to `not-executed` with the ruling as its reason.

### OQ-02: Should the 16-color generic tier be an authored per-role table rather than a derived reduction?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to a derived reduction (`color_16_for_index`). R9.3a.3's "authored, not derived" rule is stated for the twenty lifecycle stages because Section 5 has adjacent-index pairs with opposite meanings (ready 45 / done 46); the generic role palette's indices are far apart in hue (46 green, 196 red, 226/214 yellow, 39/33 blue, 24x gray), so a nearest-color reduction preserves success/warn/failure distinctness, which E-04 cell (b) asserts, and every generic outcome prints a word. An authored table would duplicate `ROLE_COLOR_256` keys and still need a fallback for the ~17 literal indices callers pass directly (measured: 33 36 39 40 44 46 196 203 207 208 214 220 226 244 245 250 255).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted OQ-01 block showing `- Status: resolved` with a maintainer-attributed reading-B ruling, plus the plan's `- Status: approved` and `- Approval:` lines, plus the item's and plan's `- Work-Kind:`/`- Blocks-Release:` lines side by side (or, if blocked, the pasted open OQ-01 and `git status --short` showing no change).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted final summary line of the bare `python3 -m pytest` baseline run and its `FAILED` node-id list.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff agent_workflows/term.py` pasted, showing changes confined to `Term.colorize`, `Term.color256`, their docstrings, and the new `color_16_for_index`; plus pasted output of a `python3 -c` probe (fake-TTY stream, isolated `XDG_CONFIG_HOME`, `TERM=xterm-256color`) printing `repr()` of `status_256("up to date")`, `path("a/b")`, `badge("x","error")` at pins `none`, `16`, `256`: no `\x1b` at `none`, no `38;5;` at `16`, and exactly `'\x1b[1;38;5;46mup to date\x1b[0m'` / `'\x1b[38;5;33ma/b\x1b[0m'` at `256`. The code path producing the observation is `Term.color256` -> `Term.lifecycle_depth` -> `term.resolve_color_depth` (E-03).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted pytest output of `python3 -m pytest tests/test_generic_color_depth.py tests/test_term.py -o addopts=""` showing all passed; pasted output of the new file run once with E-03 temporarily reverted showing cells (a), (b), (g) FAILED (then restored, with `git diff --stat agent_workflows/term.py` pasted to show the fix is back); pasted bare `python3 -m pytest` summary line and a statement, backed by the pasted `FAILED` list, that no node id fails that was absent from the V-02 baseline; and the two stale `tests/test_term.py` docstring locations named (quoted strings).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `git diff CHANGELOG.md` pasted showing exactly one added `- Fixed:` line under `## 2.0.0 (pending)`, and `grep -nP '[\x{2013}\x{2014}]'` over that line returning nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THE MAINTAINER'S SCOPE RULING FOR BACKLOG `cvtg9u` IS RECORDED BY RESOLVING OQ-01, then approving.
OQ-01 is `open` and owned by the maintainer: the remaining question is a user-visible styling policy,
not plan quality, so a reviewer should not clear this plan on plan quality alone (E-01 refuses to edit
anything without the resolved ruling, an `approved` status and a human `- Approval:` line). Reading B path: resolve OQ-01 recording the ruling, reclassify `cvtg9u` as the item directs
(`bug`, `- Blocks-Release: next`) and mirror both fields on this plan, then
`aw ipd set approved lv0dvv --by-human --message ...`; E-01 re-checks before any edit. Reading A path:
retire this plan to `.aw/records/plans/not-executed/` with the ruling as the reason; `cvtg9u` then
closes or is re-scoped to qualifying the config description, at the maintainer's direction.

Execution contract once approved: perform E-01..E-05 in order, commit only the Scope-Paths files via
`aw commit lv0dvv -- <paths>`, never push, paste actual runner output into each `V-*`, and move the
plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms.
