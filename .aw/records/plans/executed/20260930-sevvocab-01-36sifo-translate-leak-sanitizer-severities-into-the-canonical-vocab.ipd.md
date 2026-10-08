# IPD: Translate leak_sanitizer severities into the canonical vocabulary at one doctor boundary

- Date: 2026-09-30
- Kind: child
- Concern: Backlog `11pjkd` reports that `leak_sanitizer` declares its own closed `fail`/`warn` severity vocabulary and translates it correctly at the `CommandResult` boundary, but `doctor` renders that raw value into user-facing strings and into a machine payload whose sibling diagnostics use the canonical `error`/`warning`/`info` vocabulary, so ONE payload carries TWO vocabularies for the same field name. REPRODUCED END-TO-END at authoring against a fixture repository outside this checkout (F-01): `aw doctor --json` emits `data.report.sanitizer.findings[0].severity == "fail"` while the SIBLING diagnostic for the same finding emits `severity == "error"`, and that diagnostic's own `detail` string begins with the raw token (`fail: P = "<a home-style path>"`, truncated at 120 characters). The human renderer shows the same raw token (`- leak.py:1: home-path (fail: ...)`). Three sites, one defect: `doctor.SanitizerProbeResult.to_dict` passes the sanitizer value straight through, and `doctor.probe_sanitizer` plus `doctor.render_human_report` interpolate it into prose.
- Scope: IN: (a) introducing ONE canonical translation point so no raw `fail`/`warn` token leaves `doctor` in a severity field or a rendered string, covering the three measured sites (`probe_sanitizer`'s drift detail, `SanitizerProbeResult.to_dict`'s `severity` key, and `render_human_report`'s per-finding line); (b) a behavior test pinning that property, because F-06 measured that NO test anywhere asserts on any of the three. OUT: `leak_sanitizer`'s OWN `fail`/`warn` vocabulary, which is correct and stays (F-03 explains why renaming it is the wrong fix); the `check-local-leaks` CLI's own `--agent`/human output, whose `fail`/`warn` wording is its documented contract (F-04); the two internal consumers that compare against `"fail"` as a CONTROL-FLOW predicate rather than rendering it (`security_hardening.check_evidence_redaction`, documented in `host_runner`), which are correct and must not be touched (F-05); and any change to `artifact_core.drift_exit_code` or to the exit code `aw doctor` returns (F-07 measures why this is a REPORTING fix that must stay exit-neutral).
- Scope-Paths: agent_workflows/doctor.py, tests/test_sanitizer_severity_vocabulary.py
- Item-Dependencies: executed:nwcf8j
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 11pjkd
- Blocks-Release: next
- Set: sevvocab
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 36sifo

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 36sifo verified (set sevvocab, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261008-wxpytg-01-wxpytg-doctor-machine-diagnostic-construction-hardcodes-s.backlog.md: changed by the plan's approved execution (auto-reconciled by aw agy run)]
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review complete: PR-101..PR-105 all fixed, zero deferred, zero open

- 2026-10-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101..PR-105 all FIXED, zero deferred, zero open. Reviewed at HEAD `37b80807c`. `aw ipd lint --phase author` conformed before review and `--phase review-finalize` conforms after. EVERY DEFECT THIS PLAN CLAIMS REPRODUCES AND ITS APPROACH IS CORRECT. Re-derived independently against a git fixture built OUTSIDE this checkout: F-01 verbatim (`sanitizer.findings[0].severity == "fail"` beside the same document's `doctor.leak-home-path` diagnostic at `"error"`, the raw `fail:` prefix in both that diagnostic's `detail` and the drift's, the human line `- leak.py:1: home-path (fail: ...)`, both runs exit 1); the three-site census is exactly complete (exactly three sites in `doctor.py` forward or interpolate a sanitizer severity); F-07 directly (`error -> 1`, `warning -> 1`, `"" -> 1`, `info -> 0`, and `drift_exit_code(report.all_drift)` really is what sets doctor's exit code, so the `warn -> info` trap is live); F-03/F-04/F-05, F-06 (`severity` appears ZERO times in `tests/test_doctor.py`), F-08 (`ROLE_COLOR_256` maps `fail`/`error` both to 196 and `warn`/`warning` both to 226, so the wrong token renders in the right color), and F-09 (`nwcf8j` is `approved` in `pending/`, declares `doctor.py`, and does extract a shared classifier in `render_human_report`). FIVE FINDINGS, NONE ABOUT THE APPROACH. PR-101 (HIGH) is that E-03's rationale was false: no consumer reads `Drift.severity` on this path, because `to_dict`'s drift serializer emits only `location`/`rule`/`detail` and doctor's machine `Diagnostic` hardcodes `severity="error"`; applying E-03 alone left `--json` byte-unchanged (probe reverted, `git diff --stat` empty). E-03 is kept as hygiene with a corrected claim, and doctor's hardcoded literal, a live defect of the same class that `nwcf8j` fixes only in `attention.py`, is now F-10 with a REQUIRED carrier rather than review prose. PR-104 is that `core.Drift` is an immutable NamedTuple whose `severity` is the NINTH field, so E-03 must pass a keyword; I hit the fourth-positional near-miss myself and briefly measured `info -> 1`, which would have falsified F-07, so F-11 records it. PR-102 corrects F-02: the ZERO warn rules under the default is structural and load-bearing, but the cited "29 warn" is environment-DERIVED (`derive_warn_tokens`), measured as 3 here, so E-04 now forbids asserting any warn count. PR-105 removes a `git stash` instruction from V-04: stashing is repository-wide in a shared checkout, and this lane's own stash list contains an entry labelled "pre-existing WIP popped in error by plan-review". PR-103 fixes a stale citation in V-01. Nothing weakened: the translate-at-the-consumer approach, the `warn -> warning` mandate, the honest-limits candour (extended with a fourth limit) and OQ-01 all stand. Bare suite at review HEAD: `3565 passed, 2 skipped, 3 warnings in 188.65s`. No production file was left modified by this review.
- 2026-09-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `11pjkd`, which plan `nwcf8j` (Set `sevtruth`) deferred as its finding F-08 and named this item as the carrier. Every claim re-derived independently rather than inherited: the three raw-render sites were located by symbol, the two-vocabularies-in-one-payload defect was reproduced end-to-end through the real `aw doctor --json` CLI over a fixture repository built outside this checkout, and the `warn`-side reachability question the backlog does not raise was measured and is recorded as F-02 because it changes what a test may honestly assert.

## Goal

Make `doctor` speak ONE severity vocabulary. After this plan, every severity `doctor` renders or serializes for a sanitizer finding is one of the canonical `error`/`warning`/`info` values that its sibling diagnostics already use, the translation happens at exactly one place rather than being repeated at three, and a behavior test fails if a raw `fail` or `warn` token ever reaches a rendered or serialized severity field again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Confirm the premise at the execution base

- [x] E-01 Re-measure the defect at the execution base, so this plan does not build on a stale premise. Build a throwaway git repository OUTSIDE this checkout (pytest's `tmp_path` or `tempfile.mkdtemp()` with no `dir=` argument), commit one file containing a home-style path that trips the `home-path` rule, then run `python3 -m agent_workflows doctor --dir <fixture> --json` and report three things side by side: `data.report.sanitizer.findings[*].severity`, the `severity` of the sibling `doctor.leak-*` entry in the top-level `diagnostics` list, and that diagnostic's `detail` prefix. Then run the same command WITHOUT `--json` under `NO_COLOR=1` and report the `Sanitizer:` block's per-finding line. Finally record the exit code of both runs.
  DO NOT BUILD THE FIXTURE INSIDE THIS CHECKOUT. Measured at authoring: a fixture created under this worktree works for the sanitizer probe specifically, but it leaves an untracked directory inside a SHARED checkout, and the sibling plan `nwcf8j` measured a worse version of the same trap where a fixture under `.aw/` caused `attention` to report the REAL repository's lanes because `_resolve_runs_repo_root` walks parents. Build outside the tree and the question does not arise.
  - Depends on: none
  - Expected outcome: the two vocabularies are shown COEXISTING in one payload (`sanitizer.findings[].severity == "fail"` beside the sibling diagnostic's `"error"`), the diagnostic `detail` and the human line are both shown carrying the raw `fail:` prefix, and both runs exit 1. STOP AND REPORT if the sanitizer payload already reports a canonical value, because the defect would then be fixed and this plan is moot.
  - Execution state: performed

### Task group 2: Translate at one boundary

- [x] E-02 Add ONE translation helper in `doctor` mapping the sanitizer vocabulary to the canonical one, and route all three measured sites through it so the mapping exists exactly once (GUIDING_PRINCIPLES P8, one definition). The three sites, by symbol: `doctor.probe_sanitizer` (builds the drift `detail` as `f"{f.severity}: {f.snippet[:120]}"`), `doctor.SanitizerProbeResult.to_dict` (emits `"severity": getattr(f, "severity", "error")`), and `doctor.render_human_report` (emits the per-finding line `f"    - {f.location}: {f.rule} ({f.severity}: {f.snippet})"` under the `Security & Local Leak Sanitizer` heading). Map `fail` -> `error` and `warn` -> `warning`, which is NOT a free choice but the mapping `leak_sanitizer` ITSELF already uses at its `CommandResult` boundary (`severity="error" if f.severity == "fail" else "warning"`); adopting it keeps the two surfaces consistent rather than inventing a second answer. Give an UNRECOGNIZED value the conservative `error`, matching the established `X or "error"` idiom this repository uses for unknown severities, so a future sanitizer vocabulary addition lands in the alarming bucket and never in silence.
  DO NOT MAP `warn` TO `info`, WHICH WOULD SILENTLY MOVE AN EXIT CODE. Measured at authoring (F-07): `artifact_core.drift_exit_code` returns 0 only when EVERY drift is `info`, so `error`, `warning` and the legacy empty string all fail the gate identically. `warning` is therefore exit-neutral while `info` would convert a leak finding into an advisory that no longer fails `aw doctor`. That is a GATING change masquerading as a reporting fix, and it is out of scope.
  - Depends on: E-01
  - Expected outcome: one helper, three callers, no remaining site in `doctor` that interpolates or forwards a sanitizer `severity` without translating it. `aw doctor --json` reports `error` for a `fail` finding in BOTH the sanitizer payload and the sibling diagnostic, the human line reads `(error: ...)`, and the exit code is unchanged at 1.
  - Execution state: performed

- [x] E-03 Set the `Drift.severity` field on the sanitizer drift that `probe_sanitizer` constructs, using the same helper, and verify the exit code does not move. Measured at authoring: `probe_sanitizer` builds `core.Drift(location, rule, detail)` POSITIONALLY with three fields, so `severity` defaults to the empty string; `Drift`'s own docstring documents the trailing fields as optional and the empty value as the legacy shape. This is exit-neutral BY CONSTRUCTION and must be shown to be: an empty severity already fails `drift_exit_code`, and so does `error`, so a `fail`-severity leak keeps exiting 1. Add a brief comment recording that neutrality so a later reader does not "simplify" the mapping toward `info`.

  PASS `severity=` AS A KEYWORD ON CONSTRUCTION; DO NOT ASSIGN TO THE FIELD AFTERWARDS. `core.Drift` is a `NamedTuple` and is therefore IMMUTABLE: `setattr(d, "severity", "error")` raises `AttributeError: can't set attribute` (measured at review). `severity` is also the NINTH positional field (`location`, `rule`, `detail`, `observed`, `required`, `recovery`, `assurance`, `determinism`, `severity`), so it must be named rather than appended positionally, or the value lands in `observed`. A reviewer made exactly that mistake and measured `info -> 1`, which would have falsified F-07; named correctly, `info -> 0` as F-07 states.
  THIS ITEM CHANGES NO OBSERVABLE OUTPUT TODAY, WHICH IS WHY ITS JUSTIFICATION IS CORRECTED (PR-101). The original rationale claimed populating the field was "the difference between a payload that merely LOOKS right and a drift object that CARRIES its severity for any consumer that reads the field". Measured at review: NO consumer reads it on this path. `SanitizerProbeResult.to_dict`'s drift serializer emits exactly `{"location", "rule", "detail"}` and omits `severity` entirely; and the emitted machine `Diagnostic` for a leak carries a HARDCODED `severity="error"` literal rather than a read of the drift. I applied E-03 alone and confirmed the `--json` payload was byte-unchanged: the sibling diagnostic still read `error` (from the literal), the sanitizer finding still read `fail`, and the serialized drift still carried three keys. So E-03 is correct FORWARD-LOOKING hygiene (it stops the drift asserting the legacy empty severity, and it is what makes the `drift_exit_code` contribution honest rather than accidental), and it is NOT a user-visible fix. Keep it, and do not claim it fixes a symptom.
  DOCTOR'S OWN HARDCODED `severity="error"` IS OUT OF SCOPE AND IS NOT FIXED BY THE DEPENDENCY. `nwcf8j` replaces the hardcoded literal in `attention.py`, not the one in `doctor.py`'s diagnostic construction, so doctor's literal survives BOTH plans. That is recorded as F-10 with a carrier rather than silently absorbed, because fixing it would change which severity doctor reports for every drift rule, not just the sanitizer's.
  - Depends on: E-02
  - Expected outcome: the sanitizer drift carries a canonical `severity` instead of the empty legacy default, constructed with a `severity=` KEYWORD. `aw doctor`'s exit code over the E-01 fixture is byte-identical before and after, and so is the rest of the payload, since no consumer reads this field yet (measured at review).
  - Execution state: performed

### Task group 3: Pin the property

- [x] E-04 Add `tests/test_sanitizer_severity_vocabulary.py` asserting that NO raw `fail`/`warn` token reaches a rendered or serialized severity field. Drive the real CLI over a fixture repository built under pytest's `tmp_path` (outside this checkout, per E-01) and assert on command output, the structured payload, and the exit code only. Assert the PROPERTY, not the fixture's incidental numbers: every `severity` value in the sanitizer payload and in the sibling `doctor.leak-*` diagnostics is a member of the canonical three-value set, the rendered human line for the planted finding does not contain the raw token, and the exit code matches the pre-fix exit code for the same fixture. Follow the existing fixture idiom in `tests/test_doctor.py` plus `tests.support.init_repo` / `tests.support.run_cli`.
  DO NOT READ PRODUCTION SOURCE. No `inspect`, `ast`, regex, or substring search over `doctor.py`, no caller counts, no symbol censuses, no assertion that the helper exists or is named anything in particular (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). The test must pass against ANY correct implementation of E-02, including one that inlines the mapping differently.
  COVER THE `warn` SIDE THROUGH A SEAM, AND SAY SO IN THE DOCSTRING. Measured at authoring (F-02): `doctor.probe_sanitizer` calls `scan_working_tree_counted(repo_root)` with the default `include_warn=False`, and `build_ruleset(..., include_warn=False)` compiles ZERO warn rules, so a CLI-only fixture CANNOT currently produce a `warn` finding and a test that merely drives the CLI would leave half the mapping unproven. Cover `fail` end-to-end through the CLI, and cover `warn` by driving the rendering and serialization path with a `leak_sanitizer.Finding(..., severity="warn")` supplied through the production call seam. State in the docstring WHICH half is end-to-end and WHICH is seam-driven, and why that is faithful rather than a convenience.
  THE SEAM IS CONFIRMED WORKABLE AND ITS SHAPE IS MEASURED (PR-104), so do not invent one. `leak_sanitizer.Finding`'s signature is `(location, rule, severity, snippet)` with NO defaults, so all four must be supplied. Patching `leak_sanitizer.scan_working_tree_counted` to return `([Finding(location="x.py:1", rule="derived:host", severity="warn", snippet="tok")], 1)` and calling the real `doctor.probe_sanitizer` produced drift detail `'warn: tok'` and a `to_dict` severity of `'warn'` at review, i.e. it reproduces the raw token on BOTH surfaces the fix must clean. Patch the name in the module UNDER TEST's namespace (`doctor`'s imported reference), not a copy.
  DO NOT ASSERT ANY WARN-RULE COUNT (PR-102). The warn rules are DERIVED PER REPOSITORY AND PER MACHINE by `derive_warn_tokens(repo_root)`, measured as 3 in this lane against the authoring row's claim of 29, so any warn count is environment-dependent and would make this module flaky across checkouts. The only stable fact is that the default compiles ZERO warn rules, and even that belongs in the docstring as the REASON for the seam rather than as an assertion.
  - Depends on: E-03
  - Expected outcome: a test that FAILS against the base (where `"fail"` appears in the payload and the rendered line) and PASSES after E-02 and E-03, covering both vocabulary values and pinning exit-code neutrality. This is the durable guard F-06 shows is absent today.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL or by a quoted content string; a bare line number expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation below names a symbol or quotes the code.
- THE CANONICAL SEVERITY VOCABULARY IS THREE VALUES AND IS DECLARED IN TWO PLACES THAT AGREE: `result_types.Diagnostic.severity` carries the inline comment `# "error", "warning", "info"`, and `artifact_core.Drift`'s docstring documents its own `severity` as "``error`` / ``warning`` / ``info``". The sanitizer's `fail`/`warn` is a FOURTH and FIFTH token entering those fields, which is exactly the mismatch this plan removes.
- THE MAPPING ALREADY EXISTS IN-REPO AND MUST BE REUSED, NOT REDESIGNED: `leak_sanitizer`'s own `CommandResult` branch writes `severity="error" if f.severity == "fail" else "warning"`. That is the authority for E-02's choice, which is why this plan does not treat `warn` -> `warning` versus `warn` -> `info` as an open design question.
- `artifact_core.drift_exit_code` returns `1 if any(getattr(d, "severity", "") != "info" for d in drift) else 0`, so `error`, `warning` and `""` are all gate-failing and ONLY `info` is advisory. This single line is why E-02 and E-03 are exit-neutral and why mapping `warn` to `info` would not be.
- A legacy three-field `Drift(location, rule, detail)` carries `severity=""`. `probe_sanitizer` constructs exactly that shape today, which is why E-03 exists as a distinct item from E-02.
- Tests must exercise behavior and assert on real outputs; tests that read production source text or count symbols are forbidden (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). This is why E-04 drives the CLI.
- Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md "HOW TO RUN THE SUITE").
- Commit through `aw commit 36sifo -- <paths>`; never `git add -A`, never `-a`, never push.

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `aw doctor --json` over a fixture repo; `doctor.SanitizerProbeResult.to_dict`, `doctor.probe_sanitizer`, `doctor.render_human_report` | THE DEFECT REPRODUCES END-TO-END, AND IT IS THREE SITES RATHER THAN THE TWO THE ITEM NAMES. Measured against a git repo built outside this checkout containing one home-style path: `data.report.sanitizer.findings[0].severity` is `"fail"` while the sibling `doctor.leak-home-path` entry in the SAME payload's `diagnostics` list is `"error"`, so one document answers "how serious is this finding?" twice in two vocabularies. The same raw token also leaks into PROSE at two more places: the diagnostic `detail` reads `fail: P = "<a home-style path>"` truncated at 120 characters (built by `probe_sanitizer` as `f"{f.severity}: {f.snippet[:120]}"`) and the human renderer prints `- leak.py:1: home-path (fail: ...)`. The item's fix sketch anticipates one ingest boundary; there are three call sites to route through it. |
| F-02 | `leak_sanitizer.build_ruleset`, `leak_sanitizer.scan_working_tree_counted` signature, `doctor.probe_sanitizer`'s call | ONLY THE `fail` HALF IS REACHABLE THROUGH THE CLI TODAY, WHICH CONSTRAINS WHAT A TEST MAY HONESTLY CLAIM. `probe_sanitizer` calls `scan_working_tree_counted(repo_root)` without `include_warn`, whose default is `False`, and `build_ruleset(..., include_warn=False)` compiles ZERO warn rules. So no CLI-driven fixture can currently produce a `warn` finding in doctor. THE ZERO IS THE LOAD-BEARING FACT AND IT IS STRUCTURAL: the `if include_warn or hostname_fail:` block is the ONLY writer of `rs.warn`, so with both false the dict stays empty regardless of repository. CONSEQUENCE: this is NOT an argument that the `warn` mapping is dead code (the field is typed `"fail" \| "warn"`, the value is forwarded unconditionally, and one `include_warn=True` call would reach it), but it IS the reason E-04 covers `warn` through a production seam and says so, instead of pretending an end-to-end fixture proved it. CORRECTED AT REVIEW (PR-102): the authoring row cited "8 fail / 29 warn when `include_warn=True`". The warn side is NOT a fixed code fact: those rules are DERIVED PER REPOSITORY from the environment by `derive_warn_tokens(repo_root)` (hostname, git identity, account handles), so the count varies by checkout and by machine. Measured at review in this lane: `include_warn=False` -> `fail=8 warn=0`; `include_warn=True` -> `fail=8 warn=3`, the three being `derived:` tokens for this environment. Do NOT re-derive 29 and do NOT treat any warn count as a regression signal; only the ZERO under the default is a stable fact to rely on. |
| F-10 | ADDED AT REVIEW (PR-101). `doctor.py`'s diagnostic construction (`severity="error"` literal beside `location=d.location, rule=d.rule, detail=d.detail`); `nwcf8j`'s E-03 and its `- Scope-Paths:` | **DOCTOR'S MACHINE DIAGNOSTIC HARDCODES `severity="error"` FOR EVERY DRIFT, AND NEITHER THIS PLAN NOR ITS DEPENDENCY FIXES IT.** `nwcf8j` E-03 replaces the hardcoded literal at the two sites in `attention.py`; doctor's own literal is not in its scope and is not in this plan's either. TWO CONSEQUENCES. (1) It explains why E-03 is invisible: the sibling diagnostic's `error` comes from this literal, not from the drift, so populating `Drift.severity` cannot change it (measured: applying E-03 alone left the `--json` payload byte-unchanged). (2) It means the canonical value a reader sees in `diagnostics[].severity` is currently a CONSTANT rather than a translation, so this plan's fix is genuinely about the sanitizer payload and the human line, which ARE reads. Filed rather than absorbed because changing it would alter the reported severity of EVERY doctor drift rule, which is a larger behavior change than a vocabulary translation and needs its own evidence. |
| F-11 | ADDED AT REVIEW (PR-101). `artifact_core.Drift` field order and mutability | `core.Drift` IS AN IMMUTABLE `NamedTuple` AND `severity` IS ITS NINTH FIELD, so E-03 must pass `severity=` as a KEYWORD at construction. Measured: `setattr(d, "severity", "error")` raises `AttributeError: can't set attribute`, and the field order is `location, rule, detail, observed, required, recovery, assurance, determinism, severity`, so a fourth positional argument silently populates `observed` instead. Recorded because I made that exact error while verifying F-07 and briefly measured `info -> 1`, which would have falsified the plan's central safety claim; passing the keyword correctly gives `info -> 0` as F-07 states. |
| F-03 | `leak_sanitizer.Finding.severity` (`severity: str  # "fail" \| "warn"`), module docstring ("``fail`` patterns fail the non-interactive gate", "``warn`` patterns are ADVISORY only") | THE SANITIZER'S OWN VOCABULARY IS CORRECT AND MUST NOT BE RENAMED. `fail`/`warn` are meaningful THERE: they name gate behavior, the module docstring builds its contract on them, `Ruleset` splits its pattern dicts into `fail=` and `warn=` fields, the CLI exposes a `--warn` flag, and the documented `--agent` line format is `path:line\trule\tseverity`. Renaming them to `error`/`warning` would churn a public contract to fix a rendering bug. THIS IS WHY THE FIX IS A TRANSLATION AT THE CONSUMER, which is what the item's own fix sketch proposes and what this plan does. |
| F-04 | `leak_sanitizer.main`'s `--agent` help text and its human branch | THE SANITIZER CLI'S OWN OUTPUT IS OUT OF SCOPE AND IS NOT THE DEFECT. Its `--agent` help documents emitting `severity` in its own vocabulary, and its human branch prints `[warn]`-prefixed advisory lines; AGENTS.md itself documents `aw sanitize --agent` as printing `location\trule\tseverity`. Those are deliberate and self-consistent: a reader of that command is in the sanitizer's own vocabulary. The defect is specifically that DOCTOR mixes it with a different one in a single payload. Changing the sanitizer CLI would break a documented contract to no benefit. |
| F-05 | `security_hardening.check_evidence_redaction` (`fail_findings = [f for f in findings if getattr(f, "severity", "fail") == "fail"]`), `host_runner`'s docstring ("a hard leak (severity 'fail')") | THE OTHER TWO IN-TREE CONSUMERS ARE CORRECT AND MUST NOT BE SWEPT IN. Both use `fail` as a CONTROL-FLOW predicate inside the sanitizer's own vocabulary (deciding whether a redaction boundary fails closed), never as a value rendered to a human or serialized beside canonical diagnostics. They are the CORRECT way to consume the vocabulary and are evidence that the vocabulary itself is fine. Named explicitly because an executor told to "unify two severity vocabularies" could reasonably reach for them, which would be scope creep into a security boundary. |
| F-06 | `tests/test_doctor.py`; searched the suite for any assertion on a sanitizer severity | NO TEST PINS ANY OF THE THREE SITES, WHICH IS HOW THIS SURVIVED. `tests/test_doctor.py` is the only module touching `probe_sanitizer`/`SanitizerProbeResult`, and it asserts on drift RULES (`doctor.leak-home-path`), remediation commands, and scanned-file counts; the string `severity` does not appear in it at all. So nothing fails today when the raw token is emitted, and nothing would fail tomorrow if it regressed. This is why E-04 is a required deliverable rather than a nicety. It also means the fix carries LOW regression risk: no existing assertion pins the `fail`/`warn` text. |
| F-07 | `artifact_core.drift_exit_code`; measured each severity | THE FIX MUST BE EXIT-NEUTRAL, AND ONE PLAUSIBLE MAPPING IS NOT. Measured directly: `error` -> 1, `warning` -> 1, `""` (today's value) -> 1, `info` -> 0. So `fail` -> `error` and `warn` -> `warning` leave every gate decision untouched, while the superficially reasonable `warn` -> `info` would convert an advisory leak finding into one that NO LONGER FAILS `aw doctor`. Recorded as a finding rather than left to an executor's judgement because the two mappings are indistinguishable in a rendered payload and differ in whether CI still catches a leak. |
| F-08 | `term.ROLE_COLOR_256`; `renderers` human diagnostics branch (`badge = term.badge(sev.upper(), sev)`) | WHY NOBODY NOTICED: THE RENDERER TOLERATES THE WRONG TOKEN BY COINCIDENCE. The human diagnostics renderer colors each badge by looking the severity up in `ROLE_COLOR_256`, and that table happens to contain BOTH `fail` -> 196 and `warn` -> 226, the same codes as `error` -> 196 and `warning` -> 226. So a raw `fail` renders in exactly the red a correct `error` would, and the mismatch is invisible to the eye while remaining wrong in every machine payload. An unrecognized token would instead fall back to grey 244, which is the visible failure mode this plan's conservative default avoids. |
| F-09 | `.aw/records/plans/pending/20260929-sevtruth-01-nwcf8j-...ipd.md` (its F-08 row, "Deferred / out of scope", and `- Scope-Paths:`) | THIS PLAN IS THE CARRIER PLAN `nwcf8j` NAMED, AND THE TWO OVERLAP IN ONE FILE. `nwcf8j` recorded this exact defect as its F-08, deferred it as "a vocabulary-unification change rather than a read-the-severity-you-have change", and named "Carrier: 11pjkd". Its `- Scope-Paths:` are `agent_workflows/doctor.py, agent_workflows/attention.py, tests/test_severity_truth_surfaces.py`, so it and this plan BOTH edit `doctor.py`. The regions differ (it edits the summary-line bucket expressions in `render_human_report`/`inspect_repo`; this plan edits the sanitizer sections and `to_dict`), but one of its items extracts a SHARED CLASSIFIER in `render_human_report`, the same function this plan's third site lives in. CONSEQUENCE: this plan declares `Item-Dependencies: executed:nwcf8j` so the ordering is enforced rather than hoped for, and an executor rebases onto its result instead of racing it. |

## Proposed changes (ordered, validatable)

1. Re-measure the defect at the execution base through the real CLI over an out-of-tree fixture, and stop if it no longer reproduces (E-01 / V-01).
2. Introduce one translation helper in `doctor` and route the three measured render/serialize sites through it, reusing the sanitizer's own `fail` -> `error` / `warn` -> `warning` mapping and defaulting an unknown value conservatively to `error` (E-02 / V-02).
3. Populate the `Drift.severity` field that `probe_sanitizer` currently leaves at its legacy empty default, passing it as a KEYWORD on construction (F-11), and demonstrate the exit code does not move. This is forward-looking hygiene with NO observable output change today, because no consumer reads the field on this path (F-10); the plan says so rather than claiming a symptom fix (E-03 / V-03).
4. Add the behavior test pinning the property for both vocabulary values and for exit-code neutrality (E-04 / V-04).

## Deferred / out of scope (with reason)

- `leak_sanitizer`'s own `fail`/`warn` vocabulary (F-03). Correct where it lives, load-bearing in the module docstring, the `Ruleset` field names, the `--warn` flag, and the documented `--agent` line format. Translating at the consumer is both the item's own fix sketch and the smaller change.
  - Carrier-Declined: NOTHING IS OUTSTANDING. This is a decision that the sanitizer's vocabulary is CORRECT and stays, not work postponed: F-03 measures that the tokens are load-bearing in the module docstring, the `Ruleset.fail`/`Ruleset.warn` field names, the `--warn` flag, and the documented `--agent` line format. A carrier would assert a future renaming this plan deliberately rejects.
- The `check-local-leaks` CLI's own human and `--agent` output (F-04). Self-consistent inside the sanitizer's vocabulary and documented in AGENTS.md; changing it would break a published contract without fixing the mixed-vocabulary payload.
  - Carrier-Declined: NOTHING IS OUTSTANDING. The sanitizer CLI's own output is self-consistent inside its own vocabulary and its `location\trule\tseverity` shape is documented in AGENTS.md, so there is no defect here to carry. The mixed-vocabulary payload this plan fixes is doctor's, not this command's.
- `security_hardening.check_evidence_redaction` and the `host_runner` path that documents it (F-05). These compare against `"fail"` as control flow, not as a rendered value, and they sit on a security boundary. Correct as written.
  - Carrier-Declined: NOTHING IS OUTSTANDING. Both consume `fail` as a control-flow predicate inside the sanitizer's own vocabulary and render it nowhere, which F-05 establishes is the CORRECT way to consume it. They are named here to prevent scope creep into a security boundary, not to defer work.
- Any change to `artifact_core.drift_exit_code` or to what `aw doctor` exits (F-07). This is a reporting fix; moving a gate decision would be a different, larger change needing its own approval.
  - Carrier-Declined: NOTHING IS OUTSTANDING, AND THIS IS A CONSTRAINT RATHER THAN A DEFERRAL. `drift_exit_code` is measured CORRECT as written (F-07), and exit-code neutrality is an acceptance criterion of this plan, verified by V-02 and V-03. There is no follow-on work for a carrier to hold.
- Making `warn`-severity findings REACHABLE from doctor by passing `include_warn=True` (F-02). That would change WHICH findings doctor reports, i.e. its scanning policy, not how it names their severity. A legitimate question, but a separate one; this plan makes the mapping correct for whichever findings arrive.
  - Carrier-Declined: NO CARRIER IS FILED BECAUSE NO DEFECT IS ESTABLISHED. `include_warn=False` is a deliberate, documented default ("`--agent` stays fail-focused by default (deterministic, low-noise)"), so whether doctor SHOULD surface advisory findings is an open product question, not a known bug. Filing a backlog item would assert a defect this plan has not demonstrated. A reviewer who judges otherwise should say so and an item can be filed.
- The `aw doctor` summary-line bucket exhaustiveness and the `attention` hardcoded-severity defects (F-09). Those are plan `nwcf8j`'s, already approved, and this plan declares a dependency edge on it rather than absorbing them.
  - Carrier: nwcf8j
  - Carrier-Evidence: .aw/records/plans/executed/20260929-sevtruth-01-nwcf8j-report-each-finding-s-real-severity-in-the-doctor-and-attent.ipd.md
- DOCTOR'S OWN HARDCODED `severity="error"` IN ITS MACHINE DIAGNOSTIC CONSTRUCTION (F-10, added at review). Every doctor drift is reported to a machine consumer as `error` regardless of its real severity, which is the same defect CLASS `nwcf8j` fixes in `attention.py` but at a site neither plan's `- Scope-Paths:` covers.
  - Carrier: wxpytg
  - Carrier-Evidence: .aw/records/backlog/open/20261008-wxpytg-01-wxpytg-doctor-machine-diagnostic-construction-hardcodes-s.backlog.md
  - Carrier-Required: a backlog item MUST be filed for this before this plan finalizes, because it is a live defect this review DISCOVERED and neither this plan nor its dependency closes it, so leaving it in prose would lose it the moment this plan reaches `executed` and classes `done`. It is deliberately NOT absorbed here: fixing it changes the reported severity of EVERY doctor drift rule (not just the sanitizer's), it interacts with `nwcf8j`'s shared-classifier extraction in the same file, and `nwcf8j` F-10 already measured that the correct read is `check_engine.enrich_drift(d).severity or "error"` rather than a bare `d.severity or "error"`, so the fix needs that plan's groundwork. File it with `aw backlog new` as `- Work-Kind: bug` inheriting `- Blocks-Release: next` (it is a live correctness defect on a machine surface, and the repository gates every live bug), cite the new id6 in V-02's evidence, and note that `.aw/records/backlog/` is an expected out-of-fence write to be justified at finalize with `--scope-reason`.

## Scope check

- Over-scope: none in the declared paths: they are the one module holding all three measured sites and one new test module. ONE EXPECTED OUT-OF-FENCE WRITE IS DECLARED (added at review): the F-10 carrier item under `.aw/records/backlog/`, which is required before finalize and is to be justified with `--scope-reason` rather than declared in `- Scope-Paths:` (declaring it would demand a `--scope-ack` on the path in every other respect, and the repository's route for a foreseeable conditional write is make-then-justify).
- Also in scope but worth naming: E-03 is a NO-OP for every observable surface today (F-10), kept as hygiene. A reviewer or approver who would rather drop it should say so; the plan does not claim it fixes a symptom.
- Under-scope: this plan does NOT unify the two vocabularies in the sense of making them one set of tokens; it establishes a single TRANSLATION so each surface speaks the vocabulary its own readers expect (F-03, F-04). It also does not touch the sanitizer's control-flow consumers (F-05), does not alter exit codes (F-07), and does not make `warn` findings reachable from doctor (F-02), which means the `warn` half of the mapping is proven through a production seam rather than end-to-end and the plan says so plainly in E-04 and in the honest-limits note below.

## Required tests / validation

Run the suite BARE as `python3 -m pytest` and paste the actual summary line. Compare FAILURE SETS BY NODE ID against a freshly re-derived baseline taken on the unmodified tree, not against a total written here: for reference the suite read `3565 passed, 2 skipped, 3 warnings` at review HEAD `37b80807c`, and that number is live context rather than an acceptance bar. Re-run the E-01 measurements and show the raw tokens gone from all three surfaces with the exit code unchanged. Run `python3 -m agent_workflows check all` to confirm no new findings, and `aw sanitize --agent; echo rc=$?`.

HONEST LIMITS ON WHAT THIS PROVES. First, it proves no raw `fail`/`warn` token leaves doctor in a severity field or rendered line; it does NOT prove the canonical value is the RIGHT seriousness for a given leak rule, which is a question about the sanitizer's rule severities and is untouched here. Second, the `fail` half is proven end-to-end through the CLI while the `warn` half is proven through a production call seam, because F-02 measured that doctor cannot currently produce a `warn` finding at all; a validator must not claim an end-to-end fixture exercised the `warn` mapping. Third, exit-code neutrality is demonstrated over the E-01 fixture rather than over every possible finding mix; the argument that it holds generally rests on `drift_exit_code` treating `error`, `warning` and `""` identically (F-07), which is read from that function and was re-measured directly at review (`error -> 1`, `warning -> 1`, `"" -> 1`, `info -> 0`) rather than exhaustively tested over finding mixes. Fourth, and added at review: this plan does NOT make the canonical severity a machine consumer reads actually DEPEND on the finding, because doctor's diagnostic construction hardcodes `severity="error"` for every drift (F-10). So after this plan the `diagnostics[].severity` a reader sees is still a constant; what becomes correct is the sanitizer payload's own `findings[].severity`, the drift `detail` prefix, and the human line, all three of which ARE reads of the sanitizer value. A validator must not claim this plan made the machine diagnostic severity truthful.

## Spec / documentation sync

No `.spec.md` is amended and no user-facing doc is edited, so `- Scope-Paths:` declares neither. Checked at authoring: no spec pins the sanitizer severity vocabulary or doctor's sanitizer rendering. The two places that DO document the canonical three-value vocabulary, `result_types.Diagnostic`'s inline comment and `artifact_core.Drift`'s docstring, already say `error`/`warning`/`info`; this plan makes the code match what they already document, so neither needs changing. AGENTS.md documents `aw sanitize --agent` as printing `location\trule\tseverity` in the sanitizer's own vocabulary, which F-04 keeps out of scope, so that text stays true. If an executor finds a doc or spec that DOES pin doctor's sanitizer line format, that is a scope finding to report at finalize with `--scope-reason`, not a silent edit.

## Open questions

### OQ-01: Should the canonical translation live in `doctor` or at the `leak_sanitizer` boundary?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED IN FAVOUR OF `doctor`, on the item's own reasoning and on measured evidence. The item's fix sketch says to translate "most likely where doctor ingests sanitizer findings", and three findings support that over the alternative. (1) `leak_sanitizer` ALREADY translates at its own `CommandResult` boundary and is correct there (F-03), so the sanitizer is not the broken party; adding a second translation inside it would mean the module exporting canonical values from one path and native ones from another. (2) The native vocabulary is load-bearing for the sanitizer's real consumers: `security_hardening` branches on `"fail"` (F-05), and the documented `--agent` format emits it (F-04), so changing what `scan_working_tree_counted` returns would ripple into a security boundary and a published contract. (3) The defect is doctor-local by construction: it is the only consumer that puts a sanitizer severity next to canonical diagnostics in one payload. So translation belongs at the consumer that needs canonical values. A HUMAN MAY OVERRULE: if the maintainer would rather `leak_sanitizer` grow a canonical accessor (for example a `canonical_severity()` on `Finding`) so future consumers cannot repeat this mistake, that is a defensible and slightly larger design, and this plan's helper would move there with no change to its callers. Marked resolved-not-blocking so it does not gate review.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `--json` run's three values side by side (the sanitizer finding `severity`, the sibling `doctor.leak-*` diagnostic `severity`, and that diagnostic's `detail` prefix), the `NO_COLOR=1` human `Sanitizer:` per-finding line, and both exit codes. The evidence must show `"fail"` in the sanitizer payload beside `"error"` in the sibling diagnostic, i.e. the two vocabularies coexisting. FAIL this item if the fixture was created inside this checkout (the path must not contain `.aw/` or the worktree root), since E-01's recorded sibling trap (plan `nwcf8j` measured a fixture under `.aw/` making `attention` report the REAL repository's lanes, because `_resolve_runs_repo_root` walks parents) shows an in-tree fixture can answer about the live repository. CONFIRMED REACHABLE AT REVIEW: an out-of-tree fixture built with `tempfile.mkdtemp()` and one committed home-style path reproduces every value this item demands, so the stop condition is satisfiable rather than aspirational.
  - Observed evidence:
    Fixture path: `/tmp/tmpx2sp51ro` (outside checkout, does not contain `.aw/` or workspace root).
    Pre-fix side-by-side values:
    - `data.report.sanitizer.findings[*].severity`: `['fail']`
    - Sibling `doctor.leak-*` diagnostic `severity`: `['error']`
    - Sibling diagnostic `detail` prefix: `['fail: P = "~/test.txt"']`
    - Exit code (`rc_json`): 1
    Human run under `NO_COLOR=1`:
    - Per-finding line: `    - leak.py:1: home-path (fail: P = "/home/" + "someuser/test.txt")`
    - Exit code (`rc_human`): 1
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the post-change `--json` sanitizer payload severities and sibling diagnostic severities (every value must be one of `error`/`warning`/`info`), plus the post-change human per-finding line showing no `fail:`/`warn:` prefix. Paste a `git diff` of `doctor.py` showing the mapping defined ONCE and all three call sites routed through it. FAIL this item if the diff shows the mapping written out more than once, if any of the three sites still interpolates `f.severity` untranslated, or if the diff maps `warn` to `info` rather than `warning` (F-07: that silently stops a leak finding failing the gate). ALSO REQUIRED (PR-101): paste the id6 of the backlog item filed for F-10 (doctor's hardcoded `severity="error"`), confirming it carries `- Work-Kind: bug` and `- Blocks-Release: next`. FAIL this item if no such item exists, since F-10 is a live defect this plan deliberately does not fix and prose in a plan that is about to reach `executed` is not a carrier.
  - Observed evidence:
    Post-change probe over out-of-tree fixture `/tmp/tmpjqu24_rl`:
    - `data.report.sanitizer.findings[*].severity`: `['error']`
    - Sibling `doctor.leak-*` diagnostic `severity`: `['error']`
    - Sibling diagnostic `detail` prefix: `['error: P = "~/test.txt"']`
    - Exit code (`rc_json`): 1
    Post-change human per-finding line (`NO_COLOR=1`):
    - `    - leak.py:1: home-path (error: P = "/home/" + "someuser/test.txt")`
    - Exit code (`rc_human`): 1
    Git diff of `doctor.py` showing one mapping helper and three call sites routed through it:
    ```diff
    @@ -164,6 +164,22 @@ class ArtifactsProbeResult:
             }


    +def _canonical_sanitizer_severity(severity: Optional[str]) -> str:
    +    """Map leak_sanitizer severity ('fail' / 'warn') to canonical ('error' / 'warning').
    +
    +    Matches the mapping leak_sanitizer uses at its CommandResult boundary:
    +    'fail' -> 'error', 'warn' -> 'warning'. Unrecognized or empty values fall
    +    back conservatively to 'error'.
    +
    +    DO NOT MAP 'warn' TO 'info': core.drift_exit_code returns 0 only when every
    +    drift is 'info', so 'warning' is exit-neutral while 'info' would silently stop
    +    a leak finding from failing aw doctor (F-07).
    +    """
    +    if severity == "warn":
    +        return "warning"
    +    return "error"
    +
    +
     @dataclass
     class SanitizerProbeResult:
         scanned_files: int = 0
    @@ -178,7 +194,9 @@ class SanitizerProbeResult:
                         "location": f.location,
                         "line_number": getattr(f, "line_number", None),
                         "rule": f.rule,
    -                    "severity": getattr(f, "severity", "error"),
    +                    "severity": _canonical_sanitizer_severity(
    +                        getattr(f, "severity", "error")
    +                    ),
                         "snippet": f.snippet,
                     }
                     for f in self.findings
    @@ -705,9 +723,15 @@ def probe_sanitizer(repo_root: Path) -> SanitizerProbeResult:
             )
             return res
         for f in findings:
    +        # Exit-neutral: Drift.severity defaults to "" which fails drift_exit_code;
    +        # setting canonical 'error' or 'warning' keeps exit code at 1 (never map to 'info').
    +        sev = _canonical_sanitizer_severity(getattr(f, "severity", "error"))
             res.drift.append(
                 core.Drift(
    -                f.location, f"doctor.leak-{f.rule}", f"{f.severity}: {f.snippet[:120]}"
    +                f.location,
    +                f"doctor.leak-{f.rule}",
    +                f"{sev}: {f.snippet[:120]}",
    +                severity=sev,
                 )
             )
         return res
    @@ -1862,7 +1886,10 @@ def render_human_report(report: DoctorReport, term: T.Term) -> str:
                 )
             )
             for f in san.findings:
    -            lines.append(f"    - {f.location}: {f.rule} ({f.severity}: {f.snippet})")
    +            sev = _canonical_sanitizer_severity(
    +                getattr(f, "severity", "error")
    +            )
    +            lines.append(f"    - {f.location}: {f.rule} ({sev}: {f.snippet})")
         else:
             lines.append("  Sanitizer:   Clean (0 maintainer/local leak findings)")
         lines.append("")
    ```
    F-10 carrier backlog item: `wxpytg` in `.aw/records/backlog/open/20261008-wxpytg-01-wxpytg-doctor-machine-diagnostic-construction-hardcodes-s.backlog.md`, carrying `- Work-Kind: bug` and `- Blocks-Release: next`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: show the sanitizer drift now carrying a canonical non-empty `severity` (for example by printing `[(d.rule, d.severity) for d in probe_sanitizer(<fixture>).drift]`, which read `[('doctor.leak-home-path', "''")]` at review before the change), and paste the `aw doctor` exit code over the E-01 fixture from BOTH before and after the change, which must be identical. Quote the constructed `core.Drift(...)` showing `severity=` passed as a KEYWORD (F-11: it is the ninth positional field, and the tuple is immutable so it cannot be assigned afterwards). ALSO STATE EXPLICITLY (PR-101) that this item changes NO other observable output, which is the expected result and not a failure: the serialized drift carries only `location`/`rule`/`detail`, and the sibling diagnostic's `error` comes from doctor's own hardcoded literal (F-10), so a byte-unchanged `--json` payload apart from the exit code is the CORRECT outcome. FAIL this item if the exit code moved, if the drift still carries the empty legacy severity, if the before/after exit codes were not actually both captured, or if the executor claims this item fixed a user-visible symptom.
  - Observed evidence:
    Drift severity before vs after:
    - Before change: `[('doctor.leak-home-path', "''")]`
    - After change: `[('doctor.leak-home-path', "'error'")]`
    Doctor exit code over fixture:
    - Before change: 1
    - After change: 1 (byte-identical, exit-neutral)
    Constructed `core.Drift` showing keyword `severity=sev`:
    ```python
            sev = _canonical_sanitizer_severity(getattr(f, "severity", "error"))
            res.drift.append(
                core.Drift(
                    f.location,
                    f"doctor.leak-{f.rule}",
                    f"{sev}: {f.snippet[:120]}",
                    severity=sev,
                )
            )
    ```
    Explicit confirmation (PR-101): This item changes NO other observable output today. The serialized drift in `to_dict` emits only `location`/`rule`/`detail` (omits severity), and the sibling diagnostic's `error` comes from doctor's hardcoded literal (`severity="error"`, F-10), so the `--json` payload remains byte-identical apart from the exit code and finding/detail translations owned by E-02.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new test FAILING against the pre-fix code and PASSING after, then paste the BARE `python3 -m pytest` summary line showing the whole suite green. TAKE THE RED STATE BEFORE APPLYING E-02, NOT BY STASHING (PR-105): write the test module first, run it against the untouched `doctor.py`, capture the failure naming the raw `fail` token, and only then apply E-02/E-03. `git stash` is UNSAFE here because this checkout is shared and stashing is repository-wide, not path-scoped: it would sweep a co-worker's unrelated uncommitted work into the stash stack and a mistaken `pop` would then restore it into your tree. That is not hypothetical, and the dependency plan `nwcf8j` states the same preference for the same reason. If the red state must be taken after the fact, use `git stash push -- agent_workflows/doctor.py` (path-scoped) or `git diff > patch; git checkout -- agent_workflows/doctor.py`, and confirm with `git diff --stat` that nothing else moved; NEVER a bare `git stash`. Also paste the test's docstring sentence stating which half is end-to-end and which is seam-driven (E-04, F-02). FAIL this item if the test passes against the pre-fix code (it would be pinning nothing, the exact failure mode F-06 records), if it asserts on fixture-specific finding counts rather than the vocabulary property, if it reads `doctor.py` source with `inspect`/`ast`/regex/substring search or asserts on symbol names (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"), or if it covers only the `fail` value.
  - Observed evidence:
    RED state against untouched `doctor.py`:
    ```
    FFF                                                                      [100%]
    =================================== FAILURES ===================================
    ___ test_doctor_translates_unrecognized_sanitizer_severity_to_error_via_seam ___
    E           AssertionError: assert 'novel_future_token' == 'error'
    ___________ test_doctor_translates_warn_sanitizer_severity_via_seam ____________
    E           AssertionError: assert 'warn' in {'error', 'info', 'warning'}
    __________ test_doctor_translates_fail_sanitizer_severity_end_to_end ___________
    E           AssertionError: Raw/non-canonical severity 'fail' in sanitizer finding: {'location': 'leaking_file.py:1', 'line_number': None, 'rule': 'home-path', 'severity': 'fail', 'snippet': 'P = "/home/" + "someuser/secret.txt"'}
    E           assert 'fail' in {'error', 'info', 'warning'}
    =========================== short test summary info ============================
    FAILED tests/test_sanitizer_severity_vocabulary.py::test_doctor_translates_unrecognized_sanitizer_severity_to_error_via_seam
    FAILED tests/test_sanitizer_severity_vocabulary.py::test_doctor_translates_warn_sanitizer_severity_via_seam
    FAILED tests/test_sanitizer_severity_vocabulary.py::test_doctor_translates_fail_sanitizer_severity_end_to_end
    3 failed in 11.12s
    ```
    GREEN state after applying E-02 and E-03:
    ```
    ...                                                                      [100%]
    3 passed in 6.57s
    ```
    Full bare suite pytest summary line:
    `6709 passed, 2 skipped, 3 warnings in 393.56s (0:06:33)`
    Test docstring sentence stating which half is end-to-end and which is seam-driven:
    "The 'fail' severity mapping is covered end-to-end through the real CLI over a fixture repository. The 'warn' severity mapping is covered through a production seam by patching leak_sanitizer.scan_working_tree_counted in doctor's namespace, because doctor calls the scanner with include_warn=False by default (compiling zero warn rules), making a CLI-only warn finding unreachable without altering doctor's scanning policy."
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN HAS NOW BEEN REVIEWED (2026-10-01, `APPROVE WITH REVISIONS APPLIED`), and `- Readiness: go-pending-approval` is recorded by that review as its attestation. `reviewed` is NOT approval: explicit human sign-off (`- Status: approved`) is still required before execution.

WHAT AN APPROVER MOST NEEDS TO KNOW. The defect is real and reproduces end-to-end: one `aw doctor --json` document reports the same leak finding as `"fail"` in the sanitizer payload and `"error"` in the sibling diagnostic (F-01). It is THREE sites, not the two the item describes, and one of them leaks the raw token into human prose. The fix is deliberately narrow: translate at the consumer, reusing the mapping `leak_sanitizer` already applies at its own `CommandResult` boundary, and leave the sanitizer's native vocabulary alone because it is correct where it lives and two other consumers depend on it (F-03, F-04, F-05). TWO THINGS REVIEW CHANGED THAT AN APPROVER SHOULD READ. FIRST, E-03 is a NO-OP for every observable surface: the sibling diagnostic's `error` comes from a HARDCODED literal in doctor, not from the drift, and the serialized drift omits `severity` entirely, so populating the field changes nothing a user sees (measured). It is kept as hygiene and its claim is corrected rather than removed. SECOND, that hardcoded literal is itself a live defect of the same class, it is fixed by NEITHER this plan nor its dependency (which fixes the twin in `attention.py`), and it is now a REQUIRED carrier item (F-10) rather than a sentence in this plan's prose.

THE ONE TRAP WORTH THE APPROVER'S ATTENTION IS THE `warn` MAPPING. Mapping `warn` to `info` looks right (the sanitizer calls warn findings "ADVISORY") and would SILENTLY STOP A LEAK FINDING FAILING `aw doctor`, because `drift_exit_code` treats `info` as the only non-failing severity (F-07). This plan mandates `warn` -> `warning`, which is exit-neutral and matches the sanitizer's own boundary. Two honest limits follow from F-02: doctor cannot currently produce a `warn` finding at all (it scans with `include_warn=False`, which compiles zero warn rules), so the `warn` half is pinned through a production seam rather than end-to-end, and this plan does not change that scanning policy.

ORDERING IS DECLARED, NOT HOPED FOR. Plan `nwcf8j` recorded this defect as its own F-08, deferred it, and named backlog `11pjkd` as the carrier, so this plan is the intended continuation. Both edit `doctor.py`, and `nwcf8j` extracts a shared classifier inside `render_human_report`, the same function holding this plan's third site. Hence `- Item-Dependencies: executed:nwcf8j`: this plan cannot land first and collide. VERIFIED AT REVIEW: `nwcf8j` is in `pending/` with `- Status: approved` and `- Readiness: go-pending-approval`, so the edge is SATISFIABLE and not dangling; the runner re-checks `executed:` edges at dispatch and marks this item `dependency-blocked` (continuing the run) rather than failing if the edge is still unmet, so no human step is needed to sequence them. STOP AND REPORT if `nwcf8j` has instead been retired unexecuted, since a `superseded`/`not-executed` plan does NOT satisfy an `executed:` edge and a human must then decide whether this plan proceeds alone.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the two paths in `- Scope-Paths:`. If the work genuinely requires a file outside it, make the edit and JUSTIFY it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). In particular do NOT edit `agent_workflows/leak_sanitizer.py`, `agent_workflows/security_hardening.py`, or `agent_workflows/host_runner.py`: F-03 through F-05 establish that all three are correct as written, and editing them is the specific scope creep this plan is shaped to avoid.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit 36sifo -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize 36sifo --actor <agent/model> --message <summary> --apply` (the runner owns it when it executes this plan in a lane). This plan inherits `- Blocks-Release: next` from backlog `11pjkd` and is its `From-Backlog` carrier, so the HANDOFF route legitimizes closing that item; AFTER EXECUTION, and not before, set it `done` citing this executed plan. The ORDER is load-bearing: while this plan sits in `pending/`, closing `11pjkd` fails closed because the gate is handed to a carrier that has not shipped.
