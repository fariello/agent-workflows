# IPD: Stop a home-path selector crashing the attention, runs and partition machine surfaces

- Date: 2026-10-01
- Kind: child
- Concern: Three commands interpolate a raw user-supplied token into a hand-built `aw.agent/v1` record, so a home-path argument makes the machine surface exit 1 with a ValueError traceback, empty stdout, and the refused path printed on stderr by the traceback itself.
- Scope: Sanitize the user-supplied token at each of the three hand-built record sites (`attention`'s unresolved-selector refusal, `runs`' unresolvable-target refusal, `partition`'s result record), add the one shared primitive those sites need, and pin the whole class behaviorally. Does NOT route these sites through `renderers.py`, does NOT touch `AgentRenderer`, and does NOT change what a resolvable selector resolves to.
- Scope-Paths: agent_workflows/agent_schema.py, agent_workflows/attention.py, agent_workflows/run_viewer.py, agent_workflows/partition.py, docs/cli-output-contract.md, tests/test_selector_echo_sanitization.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: enygec
- Blocks-Release: next
- Set: enygec
- Order: 1
- Highest E allocated: 08
- Author: opencode
- Id: z7ci8k

## Workflow history

- 2026-10-01 draft (opencode): created.
- 2026-10-01 to-review (opencode): authored from backlog `enygec`. Re-measured every site the carrier named, CORRECTED three of its claims (see F-02, F-03, F-08), found two echo sites and one whole surface the carrier missed (F-04, F-05), and resolved the "what is a selector SHOWN AS" product question from the repository's own shipped precedent rather than deferring it (OQ-01).

## Goal

Make a path-shaped argument produce the refusal the command already knows how to emit, instead of a crash. Today `aw attention <home path> --agent`, the same with `--json`, and `aw runs <home path> --agent`/`--json` all exit 1 with an empty stdout and a Python traceback, because each builds an `aw.agent/v1` record by hand with the user's token interpolated verbatim and then calls the validator, whose home-path rule refuses the record the command is trying to print. The refusal is correct about the record; the bug is that nobody sanitized the token on the way in. This plan sanitizes at each site, adds the one primitive they share, and pins the class with tests so the next hand-built record cannot reintroduce it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the one primitive these sites need

- [ ] E-01 Add a `redact_home_paths(text)` function to `agent_workflows/agent_schema.py`, beside `normalize_repo_path`, that rewrites every home-style absolute path prefix inside a string to `~` and returns non-string input unchanged. Cover all three classes `_HOME_PATH_RE` detects (POSIX `/home/<user>`, macOS `/Users/<user>`, Windows `<drive>:\Users\<user>`), matching the real-username forms only so an already-placeholder value is left alone by not matching. State in the docstring that it REDACTS (lossy, idempotent) rather than relativizing, and that it exists because `normalize_repo_path` cannot serve: it is a whole-path-value function that leaves an embedded path untouched (F-06) and, where it does fire, PRESERVES THE USERNAME as the leading component (F-07). IF `9yd6tx` HAS ALREADY LANDED THIS FUNCTION, do not write a second one: consume the existing one and mark this item complete citing the landed definition (F-11).
  - Depends on: none
  - Expected outcome: `agent_schema.redact_home_paths('/home/<user>/x.md')` returns a string carrying no username for which `_HOME_PATH_RE.search(...)` is `None`; the embedded form `'aw foo /home/<user>/x.md'` is redacted in place; `redact_home_paths(None)` returns `None`.
  - Execution state: pending

- [ ] E-02 Pin the primitive against the repository's OWN detectors, both of them, in the new test module from E-08: for a table of inputs covering all three home classes plus the already-redacted and no-path cases, assert `agent_schema._HOME_PATH_RE.search(redact_home_paths(s))` is `None` AND that no `leak_sanitizer._FAIL_PATTERNS` home rule (`home-path`, `users-path`, `windows-home`) matches the result, and assert idempotence. Pinning both is the point: F-09 records that the two definitions are duplicated character-for-character with no shared constant and no agreement test, so a primitive pinned against only one of them can satisfy the validator while still failing `aw sanitize`.
  - Depends on: E-01
  - Expected outcome: a test that fails if a fourth home class is added to either detector without teaching `redact_home_paths` about it.
  - Execution state: pending

### Task group 2: sanitize the three hand-built records

- [ ] E-03 In `attention.unresolved_selector_agent_record`, apply `redact_home_paths` to every token list and to the `error` string: `unresolved_selectors`, `unresolved_targets`, the interpolated `quoted` tokens inside `error`, and the two conditional lists `matched_selectors` and `invalid_selectors`. All five are echo sites and the carrier named only three (F-04). Leave the field names, the record shape, the `exit`/`verified`/`complete` values and the `assert_valid_agent_record` call EXACTLY as they are: this item changes what goes INTO the record, never the record's contract, and the validator call must stay so the site keeps failing closed on anything this sanitization does not cover.
  - Depends on: E-01
  - Expected outcome: `aw attention <home path> --agent` and `--json` exit 2 with a parseable record on stdout whose every field is home-path-free, instead of exiting 1 with a traceback.
  - Execution state: pending

- [ ] E-04 In `run_viewer`, apply `redact_home_paths` to the token list and to the message in `_unresolvable_target_refusal`, and inside `format_unresolvable_target_message` redact BOTH the interpolated tokens and the `analytics_root(repo_root)` value it prints in its reserved-analytics-tree note. That second value is an independent absolute-path leak the carrier did not name: measured, a target under the analytics tree makes the message carry the repo's own absolute root, so the record refuses even when the user's token is innocuous (F-05). Note the function is `run_viewer._unresolvable_target_refusal`, NOT the `emit_unresolvable_target_refusal` the carrier and three `attention` docstrings name; that symbol does not exist (F-02).
  - Depends on: E-01
  - Expected outcome: `aw runs <home path> --agent`/`--json` exit 2 with a home-path-free record; `aw runs <a path under the analytics tree> --agent` likewise, where it crashes today.
  - Execution state: pending

- [ ] E-05 In `partition.run_partition`'s `is_agent` branch, apply `redact_home_paths` to the `commands` list before the record is built. This is the ACTUAL partition defect and it is not the one the carrier described: `unknown` is unreachable dead weight, because `collect` has exactly one return statement and it returns `[]` for the unknown list unconditionally, raising `ValueError` on an unknown selector instead (F-03). What really crashes is `commands`, built by `format_shard` from `--model`, `--variant` and `--as`, any of which may legitimately be a path. Do NOT delete the `unknown` key: its removal is a surface-contract change, not a sanitization fix, and it is recorded in Deferred.
  - Depends on: E-01
  - Expected outcome: `aw partition -t plans --model <a home path> --agent` emits its result record with the model path redacted inside `commands[0]`, instead of exiting 1 with a traceback.
  - Execution state: pending

- [ ] E-06 Apply `redact_home_paths` to the human-surface counterparts of the three sites, specifically `attention.format_unresolved_selector_message` and `run_viewer.format_unresolvable_target_message`'s stderr path, so the human and machine surfaces say the same thing about the same token. This is not cosmetic parity: these messages print the operator's own argument back to a terminal that is routinely pasted into a shared context, which is the exact reason spec `attention-registry-and-cross-tree-status` F8a gives for forbidding an absolute path on any surface (F-10). The human path does not crash today, so this item is a leak fix and not a crash fix, and it must be reported as such.
  - Depends on: E-01
  - Expected outcome: the human refusal for a home-path token names the token in redacted form on stderr, still identifying which argument failed, and `aw sanitize --agent` finds nothing new.
  - Execution state: pending

### Task group 3: declare it and pin it

- [ ] E-07 Amend `docs/cli-output-contract.md` so its Path Sanitization invariant covers an INBOUND user-supplied token, not only an outbound path-valued field. The invariant currently reads as a property of `target`/`location`/`path`, which is why four hand-built records could echo an argument verbatim while every author believed they were conforming. State that a record field carrying a user-supplied token is sanitized before the record is built, and that the validator is a backstop rather than the mechanism. Keep the existing wording about repo-relative normalization intact: this adds a clause, it does not rewrite the invariant.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: a reader can answer "may I interpolate the user's argument into a record I build by hand?" from the contract, without reading the validator.
  - Execution state: pending

- [ ] E-08 Add `tests/test_selector_echo_sanitization.py` driving all three commands as SUBPROCESSES with a home-path-shaped token on `--agent`, `--json` and the human surface, asserting per invocation: exit 2 (not 1), stdout parses as JSON on the machine surfaces, no field anywhere in the parsed record matches either home detector, stderr carries no traceback, and the token is still IDENTIFIABLE in redacted form so the refusal remains actionable. Cover the analytics-tree target from E-04 and the `--model` path from E-05 as their own cases. Build every path literal by concatenation with a `# split: leak guard` comment, the technique `tests/test_agent_schema_paths.py` already uses, so the test file does not itself trip the repository's leak sanitizer.
  - Depends on: E-03, E-04, E-05, E-06
  - Expected outcome: a module that fails on today's code for every machine-surface case (exit 1, empty stdout) and passes after task group 2.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `agent_schema` is STDLIB ONLY: it imports `json`, `os`, `re`, `pathlib` and `typing` and nothing from the package. So a primitive added there is reachable from `attention`, `run_viewer` and `partition` with no new dependency and no import cycle, and all three already import it (`attention` lazily inside the record builder, `partition` at module level as `agent_schema`).
- The repository holds FOUR distinct postures toward a home path and this plan adds none: `assert_valid_agent_record` REFUSES, `normalize_repo_path` relativizes to the repo, `config._preserve_home` rewrites a whole path value to `~`, and `leak_sanitizer._rewrite_line` rewrites to `~` inside a line of text. The last is the behavior E-01 needs, and E-01 reproduces it rather than delegating only because `_rewrite_line` omits the Windows class (F-12).
- `aw sanitize --agent` is the repository's own authority for judging leak posture rather than eyeballing (AGENTS.md), and `docs/cli-output-contract.md` already cites it in the Path Sanitization invariant: "All records pass `aw sanitize --agent` with zero findings." That sentence is currently FALSE for these three commands, which is what E-07 reconciles.
- Test literals naming a home path are built by concatenation with a `# split: leak guard` comment so the test source does not trip the sanitizer; `tests/test_agent_schema_paths.py` establishes the convention.

## Findings

| # | Finding |
|---|---|
| F-01 | THE CARRIER'S CRASH REPRODUCES AT HEAD, AND IS WORSE THAN REPORTED. Measured on this lane: `attention <home path> --agent`, `attention <same> --json`, `runs <same> --agent` and `runs <same> --json` each exit **1** with EMPTY stdout and a 23-line Python traceback on stderr. Two consequences the carrier did not record. First, the exit code is WRONG as well as the output: `docs/cli-output-contract.md` Section 3 classifies `2` as cannot-run and the record both sites build carries `"exit": 2`, so an automated caller sees `1` ("domain findings") for an invocation that produced no finding at all, and `aw attention --agent` on a typo is indistinguishable from `aw attention --agent` reporting one real finding. Second, THE TRACEBACK PRINTS THE PATH THE RECORD REFUSED TO PRINT: the validator's message interpolates the offending value (`Unsanitized absolute home path in field 'unresolved_selectors[0]': '<the path>'`), so the leak-prevention mechanism leaks, on stderr, in full. |
| F-02 | THE CARRIER NAMES A SYMBOL THAT DOES NOT EXIST, and so do three docstrings. `run_viewer.emit_unresolvable_target_refusal` is nowhere in the package; the real function is `run_viewer._unresolvable_target_refusal` (leading underscore, no `emit_`). The stale name survives in `attention.py` in three places, including inside `unresolved_selector_agent_record`'s own docstring, where it is cited as the shipped precedent this record was shaped on. An executor following the carrier's name finds nothing. Noted so E-04 names the real symbol, and so the three stale citations are not mistaken for a fourth site. |
| F-03 | THE CARRIER'S PARTITION DIAGNOSIS IS WRONG, AND THE REAL ONE IS A DIFFERENT FIELD. It says `partition`'s agent branch "does the same with user-supplied ids in `unknown`". Measured: `partition.collect` has exactly ONE return statement, `return candidates, []`, so `unknown_ids` is ALWAYS the empty list and can echo nothing; an unknown selector does not flow into it but raises `ValueError` from one of 11 raise sites, which `run_partition` catches and prints to stderr, exiting 2 cleanly with no record built. Confirmed end-to-end: `partition -t plans <home path> --agent` exits 2 with a clean one-line stderr and no traceback. The real crash is `commands`: `aw partition -t plans -s to-review --model <home path> --agent` exits **1** with `Unsanitized absolute home path in field 'commands[0]'`, and `--variant` and `--as` crash identically, because `format_shard` interpolates each into the command line it formats. So the partition fix is E-05's `commands`, not the carrier's `unknown`. |
| F-04 | THE ATTENTION SITE HAS FIVE ECHO FIELDS, NOT THE THREE THE CARRIER COUNTED. `unresolved_selector_agent_record` interpolates `facts.refusable` into `unresolved_selectors`, into `unresolved_targets` (the same list under the `aw runs` precedent's name, a deliberate D2 decision), and into `error` via its `quoted` tokens. It ALSO conditionally sets `matched_selectors` from `facts.matched` and `invalid_selectors` from `facts.invalid`, both raw. Those two are the ones a multi-token invocation hits: a home path alongside a valid id6 populates `matched_selectors`, and a token the resolver rejects for every record type populates `invalid_selectors`. The validator walks the record RECURSIVELY (`_check_string_values` descends into lists and dicts), so a leak in either conditional field refuses the whole record exactly as a leak in the primary one does. E-03 covers all five. |
| F-05 | THE RUNS SITE LEAKS WITHOUT ANY HELP FROM THE USER, which makes it the more serious of the two refusals. `format_unresolvable_target_message` prints `analytics_root(repo_root)` verbatim in its note for a target inside the reserved analytics tree, and that value is an ABSOLUTE path. Measured on an existing, non-home repo path: `runs .aw/records/runs/analytics/nonexistent-run --agent` exits **1** with a traceback naming the repository's absolute analytics root, and the human surface exits 2 printing it. So this site crashes on a token containing no home path at all, purely from a value the command supplied itself, and no amount of input sanitization alone fixes it. E-04 redacts the root as well as the token. |
| F-06 | `normalize_repo_path` CANNOT BE USED FOR THE `error` STRINGS, which is decisive for the primitive choice. It is a whole-path-VALUE function: measured, `normalize_repo_path('aw foo /home/<user>/x.md')` returns the input UNCHANGED and `_HOME_PATH_RE` still matches it. Both refusal sites build an `error` (and `run_viewer` a multi-line `message`) with tokens embedded in prose, so the carrier's suggested `normalize_repo_path` is inert on exactly the field that is hardest to fix. Independently measured and recorded in pending plan `9yd6tx` F-06. |
| F-07 | `normalize_repo_path` IS ALSO UNSAFE FOR THE TOKEN LISTS, by a mechanism neither the carrier nor `9yd6tx` records, and this finding is why E-01 does not simply reuse it. It satisfies the VALIDATOR while PRESERVING THE USERNAME: measured, `normalize_repo_path('/home/<user>/x.md')` returns `'<user>/x.md'`, for which `_HOME_PATH_RE.search` is `None`, so the record validates and ships with the username as its leading path component. Measured against the repository's own identity rule on a real home path of the form `/home/<user>/<one file>`: the output still matches `leak_sanitizer._FAIL_PATTERNS['handle']`. So using `normalize_repo_path` here would convert a loud crash into a SILENT leak that passes the validator and fails `aw sanitize`, which is strictly worse than the present defect. (It also silently falsifies an out-of-repo path into a repo-relative one that does not exist here, `9yd6tx` F-06.) |
| F-08 | THE CARRIER OVERCOUNTS `run_analytics_cli` AND THE SURFACE IT NAMES IS NOT DEFECTIVE. It claims "two further direct `render_jsonl_record` callers". There is exactly ONE (`run_analytics_cli`, the `runs query` refusal branch); the second path reaches the serializer through `AgentRenderer`, so it is renderer-mediated and belongs to `wqiofa`. More to the point, the one direct caller does NOT have this defect, and the reason is instructive: its `reason` and `verdict` come from the statistics engine, not from the user, and its one user-facing refusal path builds its message through `run_analytics_query._refuse_field`, which DELIBERATELY does not interpolate the caller's token ("reflecting arbitrary input into an error that is printed, logged and possibly parsed is a needless injection surface for zero diagnostic gain"). Measured: `runs query metrics --filter bogus=<home path> --agent`, `--group-by <home path>`, `--metric <home path>` and a bare `<home path>` view all exit 2 with a clean valid record. That site is the CORRECT PRECEDENT for the three this plan fixes, and it is excluded from scope because it has no bug. |
| F-09 | THE TWO HOME-PATH DETECTORS ARE DUPLICATED WITH NO AGREEMENT TEST, which is why E-02 pins against both. `agent_schema._HOME_PATH_RE` is one fused alternation; `leak_sanitizer._FAIL_PATTERNS` holds the same three forms as the separate rules `home-path`, `users-path` and `windows-home`, character-for-character identical in their path parts. There is no shared constant and no test asserting they agree. F-07's measurement shows the gap is live rather than theoretical: a value can satisfy one and fail the other. This plan does NOT unify them (recorded in Deferred, carrier `ddhpcb` per `9yd6tx` F-07); E-02 merely ensures the new primitive satisfies both and so adds no third independent definition. |
| F-10 | AN IMPLEMENTED SPEC ALREADY FORBIDS THIS, so the posture is settled and not an open design question. Spec `attention-registry-and-cross-tree-status` F8a: "No output surface (human board, `--agent`, `--json`) may contain an ABSOLUTE filesystem path ... these surfaces are pasted into shared contexts, so printing it verbatim is forbidden." It names the human surface explicitly and in the same breath as the two machine ones, which is the authority for E-06 covering the human path rather than leaving it. The spec is about a LANE path and this plan is about a selector token, so this plan does not implement F8a; it stops three commands violating the principle F8a states, which is why no spec amendment is owed (see Spec sync). |
| F-11 | THIS PLAN OVERLAPS `9yd6tx` ON ONE FUNCTION AND MUST NOT RACE IT. Pending plan `9yd6tx` (Set `7tixnq`, `Status: to-review`) declares `agent_workflows/agent_schema.py` in Scope-Paths and its E-01 adds `redact_home_paths` to that module, for `--json`'s `CommandResult.to_dict` fields. That is the same primitive E-01 needs, specified compatibly (all three classes, `~`, idempotent, non-string passthrough). Neither plan depends on the other and their APPLICATION sites are disjoint (`9yd6tx` touches `result_types`; this touches three hand-built records), so they are order-independent, but whichever executes second must CONSUME the landed function rather than write a second one. E-01 states that branch explicitly. No `Item-Dependencies` edge is declared, because an edge would serialize two independent plans and park this release-gating bug behind a chore. |
| F-12 | `leak_sanitizer._rewrite_line` CANNOT BE DELEGATED TO, which bounds E-01's "reproduce, do not reuse". Its rewrite covers only the two POSIX forms (`_HOME_ANY_RE`, `_USERS_ANY_RE`); the Windows class is absent, and `_FAIL_PATTERNS['windows-home']` still matches its output. The omission is deliberate and self-documented at the definition ("Only home/Users paths are auto-rewritten (safe, generic) ... no safe generic replacement"), since a bare `~` would lose the drive letter. `agent_schema` also must not import `leak_sanitizer` (it is stdlib-only, and `leak_sanitizer` imports `renderers`/`result_types` lazily inside `main` precisely to avoid that cycle). So E-01 writes the three-class version in `agent_schema` and E-02 proves it agrees with both detectors. |
| F-13 | THE DEFECT CLASS HAS NO TEST COVERAGE AT ALL, so E-08 regresses nothing. No test anywhere passes a path-shaped token to any of these sites. The nearest existing assertions use innocuous tokens: `tests/test_attention.py::SelectorNoMatchIsReportedTests::test_selector_no_match_is_reported` drives `zzzzzz` and covers `--format json` but NOT `--agent`; `tests/test_run_viewer.py::test_unresolvable_target_refusal` drives `totalgibberish` on both machine surfaces; `tests/test_partition.py::test_cli_partition_agent_mode` validates a record built with no path-bearing flag. `attention.unresolved_selector_agent_record`, `format_unresolved_selector_message` and `SelectorMatchFacts.refusable` have zero direct test references (independently recorded in plan `o6ksmw` F-04). So every assertion E-08 adds is new, and the three existing tests above must keep passing unchanged. |
| F-14 | THE `--json` SURFACE CRASHES HERE TOO, WHICH IS A DIFFERENT SHAPE FROM `9yd6tx`'s FINDING. `9yd6tx` F-01 measured `--json` as the surface that LEAKS while `--agent` REFUSES. That holds for renderer-mediated output, but not for these sites: `attention` and `run_viewer` route `--json` through the SAME hand-built record and the same `assert_valid_agent_record`, so `--json` crashes identically (measured, F-01). `partition` is the exception and shows the asymmetry inside one command: its `is_agent` branch calls `render_jsonl_record` and crashes, while its `is_json` branch calls `json.dumps` directly and emits the home path cleanly with exit 0. So this plan fixes a crash on five invocations and a silent leak on one, and must not describe `--json` uniformly as either. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/agent_schema.py`** gains `redact_home_paths(text)` beside `normalize_repo_path`: a lossy, idempotent, three-class rewrite to `~`, non-string input returned unchanged (E-01), consumed from `9yd6tx` instead if that plan landed first (F-11). This is the only new primitive.
2. **`agent_workflows/attention.py`** applies it in `unresolved_selector_agent_record` to all five echo fields (E-03) and in `format_unresolved_selector_message` for the human surface (E-06). The record shape, field names, exit code and the `assert_valid_agent_record` backstop are untouched.
3. **`agent_workflows/run_viewer.py`** applies it in `_unresolvable_target_refusal` to the token list and the message, and in `format_unresolvable_target_message` to both the interpolated tokens and the `analytics_root(repo_root)` value (E-04, E-06).
4. **`agent_workflows/partition.py`** applies it to `commands` in `run_partition`'s `is_agent` branch (E-05). `unknown` is left alone as the unreachable dead field it is (F-03, Deferred).
5. **`docs/cli-output-contract.md`** extends the Path Sanitization invariant to cover an inbound user-supplied token, stating the validator is a backstop and not the mechanism (E-07).
6. **`tests/test_selector_echo_sanitization.py`** pins the class behaviorally across three commands and three surfaces by subprocess, asserting exit 2, parseable stdout, no home path in any field, no traceback, and a still-identifiable redacted token (E-02, E-08).

## Deferred / out of scope (with reason)

- **Removing `partition`'s dead `unknown` key.** F-03 proves it is unconditionally `[]` on both machine surfaces, so it is a field no caller can ever learn anything from. Removing it is a surface-contract change needing its own decision (a consumer may be reading the key's presence), and it is not a sanitization fix. Left in place deliberately so this plan's diff stays reviewable as a leak fix.
  - Carrier: vf3mw2
- **`partition --json` emitting a home path in `commands` with exit 0** (F-14). This plan's E-05 sanitizes `commands` before the `is_agent` branch builds its record; whether the `is_json` branch shares that sanitization is the same question `9yd6tx` is answering for `--json` generally, and settling it here would pre-empt that plan's declared posture.
  - Carrier: 7tixnq
- **Unifying `agent_schema._HOME_PATH_RE` with `leak_sanitizer._FAIL_PATTERNS`' three home rules** (F-09). A real duplication hazard, but it touches the sanitizer's config-gated per-rule severity model and its allowlists, which have nothing to do with a selector echo. E-02 ensures this plan adds no third definition.
  - Carrier: ddhpcb
- **`run_analytics_cli`'s `render_jsonl_record` caller**, which the carrier listed. Excluded because F-08 measures it as NOT defective: its fields come from the statistics engine, and its user-facing refusal path deliberately declines to interpolate the caller's token. Including it would be a change with no defect behind it.
  - Carrier-Declined: Nothing is owed. This is a measurement, not deferred work: four probe invocations with home-path arguments all produced clean valid records at exit 2.
- **`renderers.py`'s guarded serializer and `AgentRenderer`'s unguarded raise.** That is `wqiofa`'s scope, and the carrier is explicit that routing these hand-built sites through it would MASK this defect behind a generic refusal rather than fix it. This plan deliberately keeps each site's `assert_valid_agent_record` call as a fail-closed backstop.
  - Carrier: un6ppd
- **Teaching `leak_sanitizer._rewrite_line` the Windows class** (F-12). Self-documented as deliberate, with the drive-letter reason. Nothing here depends on it.
  - Carrier: 9cff1j

## Scope check

- Over-scope: none. Six E-items touch one new helper, three record-building sites, two human message builders, one doc invariant and one new test module. No record field is renamed or removed, no exit code contract is redefined (the fix RESTORES the documented `2`), no renderer class is touched, and no selector resolution behavior changes.
- Under-scope: `partition`'s `is_json` branch keeps emitting an unredacted `commands` at exit 0 (F-14, deferred to `7tixnq`), and the dead `unknown` key stays. The duplicated detectors stay duplicated. `run_analytics_cli` is untouched by measurement, not omission (F-08). The three stale `emit_unresolvable_target_refusal` docstring citations in `attention.py` (F-02) are NOT corrected here: they are a comment accuracy question in a file this plan edits, and folding a docstring sweep into a release-gating bug fix broadens the diff for no behavioral gain.

## Required tests / validation

- `python3 -m pytest tests/test_selector_echo_sanitization.py` passes, with per-test counts captured via `-o addopts=""` where a count is needed.
- The three existing tests F-13 names pass UNCHANGED: `python3 -m pytest tests/test_attention.py tests/test_run_viewer.py tests/test_partition.py tests/test_agent_schema_paths.py`.
- The full suite passes BARE: `python3 -m pytest` (configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`). Paste the actual `N passed` summary line.
- All six crashing invocations from F-01, F-03 and F-05 exit **2** with a parseable record and no traceback: `attention <home path> --agent`, `attention <home path> --json`, `runs <home path> --agent`, `runs <home path> --json`, `runs <analytics-tree path> --agent`, `partition -t plans -s to-review --model <home path> --agent`.
- `aw sanitize --agent` reports no new finding on the tree (including on the new test module, which must use the `# split: leak guard` concatenation convention).
- `aw ipd lint --phase pre-transition` reports conforming.

## Spec / documentation sync

- **No spec amendment, and no `.spec.md` file appears in `Scope-Paths`.** Spec `attention-registry-and-cross-tree-status` F8a states the principle these three commands violate (F-10), but it is scoped to a LANE's absolute path and this plan neither widens nor narrows it: the commands are brought into line with a rule the spec already states, which is conformance and not amendment. No spec governs the selector-echo path or `partition`'s record shape.
- `docs/cli-output-contract.md` is amended by E-07 (inbound-token clause on the Path Sanitization invariant). It is the operative contract for this surface: spec `command-surface-redesign` G6 was superseded by a history note redirecting to that file (recorded in `9yd6tx` F-11).
- `docs/cli-agent-protocol.md` is deliberately NOT in Scope-Paths. Its Section on exit pairing (`exit: 2` pairs with `error` or `cannot-run`) is already correct and is what F-01 shows the code violating; the fix makes the code match the existing doc, so there is nothing to change there.

## Open questions

### OQ-01: Once sanitized, what should each surface SHOW the selector as? The carrier calls this "a per-verb product decision".

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM SHIPPED IN-REPO PRECEDENT, so it needs no maintainer round trip. The answer is ONE form across all three verbs, the token with its home prefix rewritten to `~`, for three reasons that are measurements rather than preferences. FIRST, the repository has already made this choice twice for exactly this purpose: `leak_sanitizer._rewrite_line` rewrites to `~` ("a portable `~` form") and `config._preserve_home` rewrites to `~/...` with the rationale "portable". Choosing a third form here would make the same path print three ways. SECOND, the refusal's whole job is to tell the operator WHICH argument failed, so dropping or opaquely placeholdering the token would defeat the message: `no artifact matched selector '~/x.md'` is actionable, `no artifact matched selector '<redacted>'` is not, and in a multi-token invocation it is useless. THIRD, per-verb divergence is affirmatively WRONG here, because `attention`'s record deliberately emits `unresolved_targets` under `aw runs`' own field name so one consumer can read both verbs unchanged (its D2 decision, stated in `unresolved_selector_agent_record`'s docstring); two verbs sharing a field name must not disagree about that field's format. The honest limit, stated as `9yd6tx` OQ-02 states it: `~` resolves to the READER's home, not the author's, so a redacted token is portable but only literally correct when the path was under the reader's own home. That is strictly better than today, where the value is correct on exactly one machine and crashes the surface on every one.

### OQ-02: Should the three sites keep calling `assert_valid_agent_record` after sanitization, or is the call now redundant?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP IT, at all three sites, unchanged. The call is not redundant and treating it as such would be the same mistake in a new form. Three reasons. First, it is the only thing that caught this defect at all: the validator is why the carrier could measure the bug instead of discovering a leaked path in a shared paste months later, and `attention`'s own comment at the call site says so ("Fail closed on our OWN record rather than trusting it by eye"). Second, this plan's sanitization covers the HOME classes those detectors know about, and the validator enforces more than that (ANSI escapes, `kind`/`exit`/`outcome` coherence, the `exit: 2` pairing); removing it to celebrate the home fix would drop the unrelated rules. Third, F-05 is the case that settles it: that leak came from a value the COMMAND supplied, not the user, so no input-sanitization discipline can be assumed sufficient, and the backstop must survive. The validator's behavior on failure (an unguarded `ValueError`) is `wqiofa`'s concern and stays out of scope.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python session calling `agent_schema.redact_home_paths` on one input per home class (POSIX, macOS, Windows), on an embedded mid-string form (`'aw foo /home/<user>/x.md'`), on an already-`~` value, on a no-path string, and on two non-strings (`None`, `42`). For each paste the returned value AND the boolean `agent_schema._HOME_PATH_RE.search(result) is None`. Every boolean must be `True`, the non-strings must return identical, and the embedded case must show the surrounding text preserved (a redaction, not a drop). If E-01 consumed an already-landed `9yd6tx` definition instead of writing one, paste the `git log` line proving it landed and state that no second definition was added.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_selector_echo_sanitization.py -k "agreement or idempotence" -o addopts=""` showing the per-test counts. Then prove the test is FALSIFIABLE: monkeypatch a fourth alternation into `_HOME_PATH_RE` that `redact_home_paths` does not handle, paste the FAILING run, revert, and paste it passing. Separately paste the assertion output showing the result is clean against all three `leak_sanitizer._FAIL_PATTERNS` home rules by name, not only against `_HOME_PATH_RE`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste, for both `aw attention <home path> --agent` and `--json`, the exit code (must be `2`, which is also the F-01 regression: it is `1` today) and the full stdout record. Then paste a recursive walk over each parsed record reporting zero matches for both detectors. Cover the two conditional fields F-04 names with a dedicated invocation combining a home-path token with a real id6 (populating `matched_selectors`) and one with a resolver-invalid token (populating `invalid_selectors`), pasting those records too. Finally paste the `error` field in full, showing the token present in `~` form so the message is still actionable.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw runs <home path> --agent` and `--json` with exit code `2` and their full records, plus the recursive no-match walk. SEPARATELY paste the F-05 case, `aw runs .aw/records/runs/analytics/<a nonexistent run> --agent`, showing exit `2` and a record whose reserved-analytics-tree note contains NO absolute path; this case exits 1 with a traceback today and is the one a token-only fix would miss. Paste the human-surface stderr for the same target showing the same redaction.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw partition -t plans -s to-review --max 2 --model <home path> --agent` before (exit 1, traceback naming `commands[0]`) and after (exit 0, valid record with `commands[0]` carrying the model path in `~` form). Repeat for `--variant` and `--as`. Also paste the F-03 disproof so the record shows WHY `unknown` was not touched: `aw partition -t plans <home path> --agent` exiting 2 with a clean one-line stderr and no traceback, on BOTH today's code and after.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the human-surface stderr for all three commands with a home-path token, showing the token in `~` form and the message otherwise unchanged. Paste `aw sanitize --agent` on the tree showing no new finding. State explicitly that the human path did not crash before this change, so this item is validated as a leak fix and not as a crash fix.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `git diff` of `docs/cli-output-contract.md`. It must show the Path Sanitization invariant extended to an inbound user-supplied token, state that the validator is a backstop rather than the mechanism, and leave the existing repo-relative normalization wording intact. Confirm the added prose contains no em or en dashes (user-facing doc, per the execution contract).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the bare full-suite run `python3 -m pytest` with its actual `N passed` summary line, and `python3 -m pytest tests/test_selector_echo_sanitization.py -o addopts=""` with per-test counts. Paste `python3 -m pytest tests/test_attention.py tests/test_run_viewer.py tests/test_partition.py tests/test_agent_schema_paths.py` proving the three F-13 tests still pass unmodified. Demonstrate the new module is a real regression test by pasting it FAILING against pre-change code (`git stash` the source edits, keep the test, run it, paste the failures showing exit 1 and empty stdout, restore). Finally paste `aw sanitize --agent` clean and `aw ipd lint --phase pre-transition` conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `- Status: to-review` and carries NO `- Readiness:` field: that field is an output of `/plan-review` and writing it here would forge a review that has not happened. Execution requires explicit human approval recorded with `aw ipd set approved z7ci8k --by-human`.

Execution contract: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE (`python3 -m pytest`) and paste the actual runner output; a claim of passing tests without pasted output is a contract violation. Do not mark any `V-*` item complete from the matching `E-*` checkmark; inspect the evidence in a separate pass.

Post-gate lifecycle: when every `E-*` item is performed and every `V-*` item carries pasted evidence, run `aw ipd lint --phase pre-transition`, confirm it reports conforming, and only then move this plan to `.aw/records/plans/executed/` through the tooled transition. Backlog item `enygec` is set to `graduated` (not `done`) when this plan is authored; it reaches `done` only once this plan is executed. The item carries `- Blocks-Release: next` and this plan inherits it, so the release gate travels with the work and is discharged by this plan's execution, not by the item's graduation.
