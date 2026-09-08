# IPD: Suppress synthetic system protocol messages in run streams

- Date: 2026-09-06
- Kind: child
- Concern: Runner stream cleanliness and noise suppression during live unattended runs.
- Scope: Suppress the LLM platform protocol placeholder `[System: Empty ...]` from the LIVE TERMINAL DISPLAY of a run, by filtering it in the shared renderer `agent_workflows/render_stream.py` (used by `aw oc run`) and, for host parity, in `agent_workflows/agy_runipd.py` (used by `aw agy run`). A text part that is NOTHING BUT placeholders renders nothing; a text part carrying a LEADING placeholder renders its real remaining text. This changes DISPLAY ONLY: the durable session log is written before rendering and keeps every byte, and `--output raw` is untouched.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/agy_runipd.py, tests/test_render_stream.py, tests/test_agy_runipd_cli.py, tools/ipdrunner/test_runagy.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: sysproto
- Order: 1
- Highest E allocated: 04
- Author: antigravity/gemini-2.5-pro
- Id: eqzd0h
- Approval: 2026-09-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-08 approved (aw set): status set to approved

- 2026-09-07 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; PR-001..PR-011 all FIXED, no deferrals, no open questions. Reviewed at HEAD `4cbee5fa`; `aw ipd lint --phase author` conformed before review and `--phase review-finalize` after. METHOD: every empirical claim was re-measured against the corpus the plan is about (4,058 placeholder-bearing `text` events across 294 of 426 session logs under `.aw/records/runs/*/sessions/*.jsonl`) rather than trusted. THE PLAN'S OWN CENTRAL COUNT IS CORRECT AND WAS CONFIRMED: the regex it specifies matches exactly 20 distinct variants. Three claims were WRONG and each would have produced a visible defect. FIRST AND WORST, E-01 prescribed the output format `pal("• ", "cyan") + _one_line(text, 400)`, which HEAD REPLACED four commits ago (`4308015c`, `render_stream.py:603`): following the plan literally would have reverted the just-shipped `◈ think:` aligned prefix and broken `tests/test_render_stream.py:43` and the golden transcript at `:238`. SECOND, E-02 instructed edits to `render_agy_event` branches that DO NOT EXIST (that function reads no message/text field anywhere, `agy_runipd.py:510-625`) for a case measured at ZERO occurrences. THIRD, "suite remains green" is false at HEAD (`1 failed, 5613 passed`, the pre-existing `test_orchestrator_retirement::RealRepositorySets`). Two further measurements reshaped the design: the placeholder sits at POSITION 0 in 4,058 of 4,059 occurrences (so the unanchored iterative strip the plan specified bought nothing and risked eating a quotation of the token out of real narration, the exact text this very review round produces), and `tools/ipdrunner/test_runagy.py` pins `render_agy_event` through the `runagy.py` re-export shim but is NOT collected by a bare `python3 -m pytest` (`pyproject.toml:154` `testpaths = ["tests"]`), so an agy render change could break 9 tests invisibly.
- 2026-09-06 to-review (antigravity/gemini-2.5-pro): Completed review-ready IPD suppressing synthetic system protocol messages.
- 2026-09-06 draft (antigravity/gemini-2.5-pro): created.

## Goal

Stop the synthetic placeholder `[System: Empty message content sanitised to satisfy protocol]` from occupying the operator's live terminal during a run, in both `aw oc run` and `aw agy run`, without deleting any information from the durable record and without disturbing the aligned prefix grammar the stream just adopted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared helper and the OpenCode renderer

- [ ] E-01 Add `strip_system_protocol_prefix` to `agent_workflows/render_stream.py` and apply it in `render_event`'s `text` branch.
  THE MATCHER. `_SYSTEM_PROTOCOL_MSG_RE = re.compile(r"\[System:\s*Empty\b[^\]]*\]", re.IGNORECASE)`. `re` is already imported (`render_stream.py:27`); do not add a second import. This exact pattern was validated against the real corpus and matches all 20 observed variants (F-1), including the one CHAINED occurrence (`...satisfy prot[System: Empty ...protocol]`), which it consumes in a single match because `[^\]]*` cannot cross the first `]`.
  ANCHOR AT THE START; DO NOT STRIP MID-TEXT. Remove only a LEADING RUN of placeholders (loop while the text, after `lstrip()`, starts with a match), then `strip()` the remainder. Measured: the placeholder is at POSITION 0 in 4,058 of 4,059 occurrences, and the single non-zero one is the inner half of that chained token, so anchoring loses NOTHING. This is a correctness requirement, not a style preference: an unanchored strip would also delete the token out of REAL agent narration that QUOTES it, which is exactly what an agent working on this very plan emits, and the operator would silently lose that sentence. F-4.
  ORDER OF OPERATIONS: strip FIRST on the raw `part.get("text")`, THEN `_one_line(...)`. Stripping after collapsing would work too, but stripping first keeps the `\n\n` separator case (observed, F-2) obvious rather than incidental.
  THE OUTPUT FORMAT IS `format_event_prefix`, NOT A BULLET. Preserve the CURRENT line exactly: `prefix = format_event_prefix("think", pal, use_unicode, style="cyan")` then `f"{prefix}{text}"` (`render_stream.py:603-604`). The earlier revision of this plan specified `pal("\u2022 ", "cyan") + _one_line(text, 400)`, which is the SUPERSEDED format that commit `4308015c` deliberately replaced with the aligned `◈ think:` prefix; writing it back would revert shipped work and break `tests/test_render_stream.py:43` and `:238`. Change ONLY what feeds `text`; touch neither the prefix nor the pad. PR-001.
  BEHAVIOR: if nothing survives the strip, `return None` (the existing empty-text guard at `:601-602` already does this once `text` is empty, so prefer reusing it over adding a second early return). Otherwise render the surviving text through the unchanged prefix path.
  ALSO SANITIZE THE `JSONDecodeError` FALLBACK (`:594-595`) for defense in depth, returning `None` when a non-JSON line reduces to nothing. STATE THE HONEST BASIS: this case is measured at ZERO (23 non-JSON lines in 101,836, none containing the placeholder), so it is parity insurance, not an observed defect. F-6.
  - Depends on: none
  - Expected outcome: a text part that is only placeholders renders nothing; a text part with a leading placeholder renders its real text behind the unchanged `◈ think:` prefix; a placeholder QUOTED inside real narration is left intact; the aligned format and pad are byte-identical to HEAD.
  - Execution state: pending

### Task group 2: the Antigravity renderer (host parity)

- [ ] E-02 In `agent_workflows/agy_runipd.py`, import `strip_system_protocol_prefix` from `agent_workflows.render_stream` and apply it to the code paths that ACTUALLY EXIST in `render_agy_event`.
  READ THE FUNCTION BEFORE EDITING IT, because the earlier revision of this plan named branches that are not there. `render_agy_event` (`agy_runipd.py:481-625`) handles exactly `init`, `result`, and `step_update` with `step_type` in {`tool`, `agent_response`, `subagent`}, plus the `JSONDecodeError` fallback at `:515-516`. IT READS NO `message` OR `text` FIELD ANYWHERE, and `agent_response` already `return None`s at `:605-606`. So there is NO text branch to sanitize, and inventing one would be adding a renderer for an event shape this host has never been observed to emit. PR-004.
  WHAT TO ACTUALLY CHANGE, therefore: the `JSONDecodeError` fallback only. If `strip_system_protocol_prefix(line)` leaves nothing, `return None` instead of the dim raw line.
  BE HONEST THAT THIS IS UNEVIDENCED PARITY, not a fix for an observed problem. Measured: ZERO agy-shaped session logs exist in `.aw/records/runs/` (all 394 parseable session logs are OpenCode-shaped `type`/`part`), and the placeholder is a platform artifact of the OpenCode/Anthropic path. The justification is that `render_stream.py` exists precisely so a stream behavior added for one host reaches both (`agy_runipd.py:493-495`), so the helper is IMPORTED rather than duplicated. Do not claim a measured agy occurrence.
  IF A FUTURE `message`/`text` FIELD APPEARS in the agy schema, sanitizing it is the same one-line call; note that rather than pre-building the branch.
  - Depends on: E-01
  - Expected outcome: `render_agy_event` imports the shared helper (no second regex, no copied function) and suppresses a placeholder-only unparseable line; no new event branch is invented; every existing agy render path is byte-identical.
  - Execution state: pending

### Task group 3: prove the OpenCode side

- [ ] E-03 Add unit tests to `tests/test_render_stream.py` for the helper and for `render_event`.
  USE INLINE STRING LITERALS FOR THE VARIANTS. Copy the 20 observed variants into the test as literals; do NOT have the test read `.aw/records/runs/`. That tree is GITIGNORED (`.aw/.gitignore:14`, zero tracked files), so a corpus-reading test passes only on this machine and fails in a fresh clone, a bare worktree, and CI. It is legitimate local evidence and cannot be a fixture. PR-005.
  REQUIRED CASES: each of the 20 variants reduces to empty; the CHAINED variant reduces to empty; a leading placeholder plus real text yields the real text ONLY, still behind `EVENT_PREFIXES["think"].ljust(event_prefix_pad(True))`; a placeholder QUOTED MID-SENTENCE inside real narration is PRESERVED VERBATIM (the anchoring guarantee from E-01, and the case that proves the filter cannot eat real narration); a truncated `[System: Empty` with no closing bracket is left visible rather than half-eaten; a placeholder-only `JSONDecodeError` line returns `None`.
  PIN THE FORMAT, NOT JUST THE FILTER. At least one assertion must compare against the prefix built from `render_stream.EVENT_PREFIXES["think"]` and `event_prefix_pad(True)`, so a future attempt to reintroduce the bullet format fails here. The existing `test_text_event_renders_narration` (`:36-44`) is the pattern to follow.
  - Depends on: E-01
  - Expected outcome: the 20 variants, the chained case, the prefixed case, the quoted-mid-sentence preservation case, the truncated case, and the fallback case all pass; the aligned-format assertion is present; no test reads `.aw/records/runs/`.
  - Execution state: pending

### Task group 4: prove the Antigravity side, including the module a bare suite does not collect

- [ ] E-04 Cover the agy change in `tests/test_agy_runipd_cli.py` AND verify the UNCOLLECTED renderer module `tools/ipdrunner/test_runagy.py` did not regress.
  THE TRAP THIS ITEM EXISTS TO CATCH. `tools/ipdrunner/test_runagy.py::AgyEventRenderTests` asserts on `render_agy_event` output through the `runagy.py` re-export shim (`tools/ipdrunner/runagy.py:29-31`), but `pyproject.toml:154` sets `testpaths = ["tests"]`, so a bare `python3 -m pytest` NEVER COLLECTS IT. An agy render change can therefore break those tests while the suite reports green. PR-003.
  MEASURED BASELINES, so a pre-existing failure is not mistaken for a new one: `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k AgyEventRender` is `9 passed, 16 deselected` at HEAD, and the WHOLE module is `10 failed, 15 passed` for reasons unrelated to rendering (`AttributeError: module 'runagy' has no attribute '_read_deps'` and siblings). Fixing those 10 is explicitly OUT of scope; the requirement is that the count stay exactly 10 and that the 9 render tests stay green.
  ADD the agy-side case to `tests/test_agy_runipd_cli.py` (a placeholder-only unparseable line renders nothing) so the behavior is pinned inside the COLLECTED tree too, not only in the module a bare run skips.
  - Depends on: E-02, E-03
  - Expected outcome: `-k AgyEventRender` still `9 passed`; the module's pre-existing failure count is still exactly 10; a collected test in `tests/test_agy_runipd_cli.py` pins the new agy behavior.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/render_stream.py` is the established host-neutral stream-rendering module shared between `oc_runipd.py` and `agy_runipd.py`; `agy_runipd.py` already imports `_one_line`, `Palette`, `Statusline`, `Heartbeat`, and `format_event_prefix` from it. A stream behavior belongs there once and is imported, never copied.
- `render_event` and `render_agy_event` return `None` to mean "render nothing for this event". That is the existing suppression mechanism (`render_stream.py:601-602`, `:630`), so this change needs no new vocabulary.
- THE OUTPUT FORMAT IS THE ALIGNED PREFIX GRAMMAR, NOT A BULLET. `render_event`'s text branch emits `format_event_prefix("think", pal, use_unicode, style="cyan")` (`render_stream.py:603-604`). The bullet form `pal("• ", "cyan")` was REMOVED by commit `4308015c` (2026-09-07) and is pinned against by `tests/test_render_stream.py:43` and the golden transcript at `:238`. Any instruction to emit a bullet here is stale.
- `re` is already imported in `render_stream.py:27`.
- THE DURABLE RECORD IS WRITTEN BEFORE RENDERING, so display filtering deletes nothing. `oc_runipd.py`'s stream loop does `log.write(line)` and `log.flush()` as the FIRST two statements per line, then `watchdog.touch()`, and only later branches on `output_mode` to call `render_event` (`oc_runipd.py:5626-5729`). Consequences worth stating: the session JSONL keeps every placeholder, `--output raw` still prints them, and STALL DETECTION IS UNAFFECTED because `watchdog.touch()` runs before and independently of rendering. F-5.
- `.aw/records/runs/` IS GITIGNORED (`.aw/.gitignore:14`; `git ls-files` returns nothing for it). It is valid local evidence and can never be a test fixture.
- `pyproject.toml:154` `testpaths = ["tests"]` means a bare `python3 -m pytest` does NOT collect `tools/ipdrunner/test_runagy.py`, which nevertheless pins `render_agy_event`.
- `pyproject.toml:169` `addopts = "-q -n auto --dist=worksteal -m 'not slow'"`, so run the suite BARE. Clear the defaults explicitly with `-o addopts=""` only when a narrowed per-test count is genuinely needed.
- THE SUITE IS NOT GREEN AT HEAD: `1 failed, 5613 passed, 3 skipped, 2 xfailed` (`tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`, a status-drift assertion unrelated to stream rendering). Judge on the DELTA.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | THE VARIANT COUNT IS CORRECT AND WAS CONFIRMED, not merely trusted: the regex specified in E-01 matches exactly **20** distinct placeholder strings across the corpus (4,058 matches in `type: "text"` parts, spread over 294 session logs). The dominant form is `[System: Empty message content sanitised to satisfy protocol]` (4,021); the tail is single-occurrence corruptions of it (`portocol`, `polocol`, `propecol`, `propriety`, `parity`, `sandbox to satisfy`, `Empty method content sanitised`, and so on), which is why a broad `Empty\b[^\]]*` body rather than a literal is the right matcher. | measured over `.aw/records/runs/*/sessions/*.jsonl` |
| F-2 | The PREFIXED case is real but RARE: 5 of 4,058 text parts carry real text after the placeholder (three with no separator, two with `\n\n`), and exactly 1 occurrence is a CHAINED double token. So OQ-01's strip-and-show resolution is correct, and the chained case is a single measured instance rather than a common shape. | measured; e.g. `[System: Empty ...protocol]\n\nNow let me look at the key structural question:...` |
| F-3 | THE PLACEHOLDER IS AT POSITION 0 in 4,058 of 4,059 occurrences; the one exception is the inner half of the chained token. Anchoring the strip to the leading run therefore costs nothing and removes the false-positive risk entirely. | measured `re.finditer` start offsets |
| F-4 | **AN UNANCHORED STRIP WOULD EAT REAL NARRATION.** The token is a string agents legitimately QUOTE when discussing this very behavior, and a mid-text strip would silently delete it from a genuine sentence, leaving mangled prose with no indication anything was removed. This is not hypothetical: session `02-eqzd0h-attempt-1.jsonl` contains the literal token inside `tool_use` payloads produced while working on this plan. | `render_stream.py` text branch semantics; observed `tool_use` occurrences in the eqzd0h session log |
| F-5 | **DISPLAY FILTERING DELETES NOTHING FROM THE RECORD, AND CANNOT CAUSE A FALSE STALL.** `log.write(line)` + `log.flush()` are the first statements of the per-line loop and `watchdog.touch()` immediately follows, all BEFORE the `output_mode` branch that calls `render_event`. So the session JSONL is complete, `--output raw` is unaffected, and returning `None` cannot starve the stall watchdog. | `oc_runipd.py:5626-5731` |
| F-6 | THE `JSONDecodeError` PATH IS MEASURED AT ZERO: 23 non-JSON lines in 101,836 total, NONE containing the placeholder. Sanitizing it is defensible parity insurance and must not be described as fixing an observed defect. | measured over all session logs |
| F-7 | **E-01's PRESCRIBED OUTPUT FORMAT WAS STALE AND WOULD HAVE REVERTED SHIPPED WORK.** The plan specified `pal("• ", "cyan") + _one_line(text, 400)`; commit `4308015c` (4 commits before this review) replaced exactly that expression with the aligned `format_event_prefix("think", ...)` prefix. An executor following the plan literally would have undone it and broken two pinning tests. | plan (pre-revision) line 35; `render_stream.py:603-604`; `git show 4308015c~1:agent_workflows/render_stream.py:601`; `tests/test_render_stream.py:43`, `:238` |
| F-8 | **`render_agy_event` HAS NO TEXT OR MESSAGE BRANCH TO SANITIZE.** It handles `init`, `result`, and `step_update`/{`tool`,`agent_response`,`subagent`} plus the `JSONDecodeError` fallback, and reads no `message`/`text` field anywhere; `agent_response` already returns `None`. E-02's original instruction to sanitize "text/message events or step updates containing message/text" named nothing that exists. | `agy_runipd.py:481-625`, `:605-606` |
| F-9 | THE PLACEHOLDER HAS NEVER BEEN OBSERVED ON THE AGY PATH: zero agy-shaped session logs exist in the corpus (all 394 parseable ones are OpenCode `type`/`part` shaped), and the token is an artifact of the OpenCode/Anthropic platform. The agy edit is parity, not a fix. | measured event-shape classification over all session logs |
| F-10 | **`tools/ipdrunner/test_runagy.py` PINS `render_agy_event` BUT IS NOT COLLECTED BY A BARE SUITE RUN.** `testpaths = ["tests"]` excludes `tools/`, so 9 `AgyEventRenderTests` assertions could break invisibly. Baselines: `-k AgyEventRender` is `9 passed, 16 deselected`; the whole module is `10 failed, 15 passed`, all 10 failures pre-existing and unrelated to rendering. | `pyproject.toml:154`; `tools/ipdrunner/runagy.py:29-31`; measured runs |
| F-11 | **"SUITE REMAINS GREEN" IS FALSE AT HEAD:** `1 failed, 5613 passed, 3 skipped, 2 xfailed`. The failure is `test_orchestrator_retirement::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` (expects `{"kgpptv": "reviewed"}`, gets `{"kgpptv": "approved"}`), a plans-status drift unrelated to this work. The acceptance criterion must be an empty AFTER-minus-BEFORE failure delta, not greenness. | measured `python3 -m pytest` at HEAD `4cbee5fa` |
| F-12 | F-1's original claim that all occurrences are in `type: "text"` parts was true for the authoring corpus, but a `tool_use` payload CAN carry the literal token (observed 3 times, from an agent grepping for it). E-01 deliberately does not touch the `tool_use` branch: a tool's own output is the operator's evidence and must not be edited. | measured; `render_stream.py:625` onward |

## Proposed changes (ordered, validatable)

1. Add `strip_system_protocol_prefix` to `render_stream.py` and apply it in `render_event`'s `text` branch, anchored to a LEADING run, preserving the existing `format_event_prefix("think", ...)` output format exactly (E-01).
2. Import the shared helper in `agy_runipd.py` and apply it to the only path that exists there, the `JSONDecodeError` fallback, without inventing a text branch (E-02).
3. Pin the OpenCode behavior with inline-literal tests, including the quoted-mid-sentence preservation case and an assertion on the aligned prefix format (E-03).
4. Pin the agy behavior in the collected tree and prove the uncollected `tools/ipdrunner/test_runagy.py` renderer tests did not regress (E-04).

## Deferred / out of scope (with reason)

- MODIFYING HISTORICAL SESSION RECORDS in `.aw/records/runs/`: those logs are the immutable record of past executions, and this change is display-only by design (F-5). Rewriting them would destroy evidence to improve cosmetics.
- SANITIZING THE `tool_use` BRANCH. A tool's input and output are the operator's primary evidence; a `grep` whose command line or output legitimately contains the token must render verbatim. F-12.
- BUILDING AN AGY `message`/`text` BRANCH. None exists and no agy occurrence has ever been observed (F-8, F-9). Adding a renderer for a hypothetical event shape would be speculative scope; the one-line call is trivial to add when a real event appears.
- FIXING THE 10 PRE-EXISTING FAILURES in `tools/ipdrunner/test_runagy.py` (`_read_deps` and siblings). Unrelated to rendering; this plan only requires the count stay at 10.
- FIXING THE PRE-EXISTING `test_orchestrator_retirement` FAILURE (F-11). A plans-status drift owned elsewhere.
- A GENERAL PLATFORM-PLACEHOLDER FRAMEWORK (a table of vendor artifacts to filter). One pattern is observed; a registry for one entry is speculative generality.

## Scope check

- Over-scope: none remaining. The original E-02 was over-scope (it directed edits to nonexistent branches for an unevidenced case, F-8/F-9); it is now narrowed to the single real code path and labeled honestly as parity.
- Scope-Paths justification: `agent_workflows/render_stream.py` holds the shared helper and `render_event` (E-01); `agent_workflows/agy_runipd.py` holds `render_agy_event` (E-02); `tests/test_render_stream.py` is where the OpenCode renderer is pinned (E-03); `tests/test_agy_runipd_cli.py` is the COLLECTED home for the agy case, and `tools/ipdrunner/test_runagy.py` is the UNCOLLECTED module that pins `render_agy_event` through the shim and must be run explicitly (E-04, F-10).
- Under-scope, stated rather than left as `none`: this child does not touch the `tool_use` branch, does not add an agy text branch, does not alter the prefix table or pad, does not change `output_mode` handling or the stall watchdog, does not rewrite historical logs, and does not fix either pre-existing failure set. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the summary line pasted. The criterion is that the AFTER failure set MINUS the BEFORE set is EMPTY. Measured BEFORE at HEAD `4cbee5fa`: `1 failed, 5613 passed, 3 skipped, 2 xfailed`. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
- Targeted: `python3 -m pytest tests/test_render_stream.py tests/test_agy_runipd_cli.py`.
- THE UNCOLLECTED MODULE, run explicitly because a bare suite skips it: `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k AgyEventRender` (baseline `9 passed, 16 deselected`) and the whole module (baseline `10 failed, 15 passed`, count must be unchanged).
- THE ANTI-REGRESSION ASSERTION for the aligned format: `tests/test_render_stream.py::RenderEventUnitTests::test_text_event_renders_narration` and the golden transcript test must pass UNMODIFIED, proving the `◈ think:` prefix was not reverted.
- THE FALSE-POSITIVE CASE: a text part quoting the placeholder mid-sentence must render that sentence intact.
- `aw sanitize --agent` clean.
- Pre-commit hooks clean.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).

## Spec / documentation sync

No spec change. Stream rendering is presentation, and no spec asserts what a text event displays.

The new helper's DOCSTRING is the authoritative prose for this behavior and must record three things a future reader cannot re-derive: that the strip is ANCHORED to a leading run and WHY (the 4,058-of-4,059 measurement plus the quoted-narration false positive, F-3/F-4), that filtering is DISPLAY ONLY because the durable log is written first (F-5), and that the agy application is unevidenced parity rather than an observed occurrence (F-9). Do not restate the superseded bullet format anywhere.

## Open questions

### OQ-01: How to handle placeholders attached to real agent text?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: STRIP THE LEADING PLACEHOLDER AND DISPLAY THE GENUINE TEXT, rather than suppressing the whole text part. Confirmed correct by measurement: 5 text parts carry real text after the placeholder (F-2), and suppressing them would discard real narration to remove noise.

### OQ-02: Strip placeholders anywhere in the text, or only a leading run?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ONLY A LEADING RUN. The unanchored iterative strip originally specified gains nothing and carries a real cost. Gains nothing: the placeholder is at position 0 in 4,058 of 4,059 occurrences, and the sole exception is the inner half of a chained token that a leading-anchored loop already consumes (F-3). Real cost: the token is a string agents legitimately quote when discussing this feature, and a mid-text strip would silently delete it from genuine prose (F-4). For a filter whose whole purpose is to remove noise, quietly corrupting signal is the one unacceptable failure mode, so the narrower rule wins.

### OQ-03: Should the agy renderer be changed at all, given zero observed occurrences there?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, BUT ONLY THE PATH THAT EXISTS, AND LABELED HONESTLY. `render_stream.py` exists so a stream behavior is written once and reaches both hosts (`agy_runipd.py:493-495`), so importing the shared helper in the agy fallback costs one line and keeps the two renderers from diverging. What is REFUSED is the original instruction to sanitize text/message branches: they do not exist (F-8), and building them for an unobserved event shape (F-9) would be speculative scope dressed as a fix. The plan now says plainly that this is parity insurance rather than a measured defect.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the final `strip_system_protocol_prefix` source and the `render_event` text branch. Confirm BY INSPECTION, in one sentence each, that (a) the emitted prefix is still `format_event_prefix("think", pal, use_unicode, style="cyan")` and no bullet was introduced, and (b) the strip is ANCHORED to a leading run. Paste an interpreter probe showing: a placeholder-only text part -> `None`; a leading placeholder plus real text -> the real text behind the `◈ think:` prefix; a placeholder QUOTED MID-SENTENCE -> rendered VERBATIM; a truncated `[System: Empty` -> left visible.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `render_agy_event` diff and confirm by inspection that it IMPORTS the shared helper (no second regex, no copied function) and that NO new event branch was added. Paste a probe showing a placeholder-only unparseable line returns `None` and that an `init`, a `result`, and a `tool` `step_update` render byte-identically to before the change.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the pytest output for `tests/test_render_stream.py`. Confirm the 20 variants are INLINE LITERALS and that no test reads `.aw/records/runs/` (paste the grep proving it). Paste `test_text_event_renders_narration` and the golden transcript test passing UNMODIFIED, which is what proves the aligned format was not reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -k AgyEventRender` showing `9 passed` and the whole-module run showing the pre-existing failure count STILL EXACTLY 10. Paste the new collected `tests/test_agy_runipd_cli.py` case passing. THEN paste the BARE `python3 -m pytest` summary and show the AFTER-minus-BEFORE failure set is EMPTY against the `1 failed, 5613 passed` baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY the five paths in `Scope-Paths`. Do NOT change the prefix table, `event_prefix_pad`, or `format_event_prefix`. Do NOT alter the `tool_use` branch, the `output_mode` handling, or the stall watchdog. Do NOT rewrite anything under `.aw/records/runs/`. Do NOT add an agy `message`/`text` branch. Do NOT attempt the 10 pre-existing `test_runagy.py` failures or the `test_orchestrator_retirement` failure. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: run `aw runs` before starting, and never revert or commit another party's work.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

WARNING FIRST: DO NOT REINTRODUCE THE BULLET. The single likeliest way to damage the repository with this plan is to follow a stale instruction and emit `pal("• ", "cyan")`, reverting commit `4308015c`'s aligned `◈ think:` prefix. Two tests catch it (`tests/test_render_stream.py:43`, `:238`); if either fails, you reverted shipped work rather than found a broken test.

WARNING SECOND: THE RISK RUNS TOWARD DELETING SIGNAL, not toward leaving noise. This change makes the display show LESS, which is the direction in which a mistake is invisible: an over-broad filter silently removes real agent narration and nothing ever complains. Suppress ONLY a leading run of placeholders. If you find yourself stripping the token out of the middle of a sentence, the rule is wrong.

WARNING THIRD: A BARE SUITE RUN DOES NOT COVER YOUR AGY CHANGE. `testpaths = ["tests"]` skips `tools/ipdrunner/test_runagy.py`, whose 9 `AgyEventRenderTests` assert on the exact function E-02 edits. Run it explicitly (E-04) or you will report green over a broken renderer.

BASELINE HONESTY: the suite is NOT green at HEAD (`1 failed, 5613 passed`) and this plan does not make it green. Judge on the DELTA, and do not report the pre-existing `test_orchestrator_retirement` failure as yours.
