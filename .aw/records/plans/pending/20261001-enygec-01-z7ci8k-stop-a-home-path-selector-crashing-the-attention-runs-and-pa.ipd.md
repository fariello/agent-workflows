# IPD: Stop a home-path selector crashing the attention, runs and partition machine surfaces

- Date: 2026-10-01
- Kind: child
- Concern: Three commands interpolate a raw user-supplied token into a hand-built `aw.agent/v1` record, so a home-path argument makes the machine surface exit 1 with a ValueError traceback, empty stdout, and the refused path printed on stderr by the traceback itself.
- Scope: Sanitize the user-supplied token at each of the three hand-built record sites (`attention`'s unresolved-selector refusal, `runs`' unresolvable-target refusal, `partition`'s result record on both machine surfaces), CONSUMING the shared `agent_schema.redact_home_paths` primitive that plan `9yd6tx` already landed, and pin the whole class behaviorally. Does NOT route these sites through `renderers.py`, does NOT touch `AgentRenderer`, does NOT edit `agent_schema.py`, and does NOT change what a resolvable selector resolves to.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/run_viewer.py, agent_workflows/partition.py, docs/cli-output-contract.md, tests/test_selector_echo_sanitization.py, tests/test_agent_record_guard.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: enygec
- Blocks-Release: next
- Set: enygec
- Order: 1
- Highest E allocated: 08
- Author: opencode
- Id: z7ci8k
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED via /plan-review; PR-001..PR-010 all FIXED. Reviewed at HEAD `db8c72a9a`; lint `author` and `review-finalize` both conforming. Every crash re-measured and reproduces. Main defect was staleness: `9yd6tx` (primitive), `1xthrh` (detector datum) and `0hz005` (partition `unknown` key) had executed since authoring, so E-01 now consumes the landed `redact_home_paths` and `agent_schema.py` left Scope-Paths (PR-001, PR-002). Also: unreachable `matched/invalid_selectors` CLI demand rewritten to a direct-call pin (PR-003); `partition --json` leak brought in scope, human command kept raw by design (PR-004); analytics root rendered repo-relative (PR-005); partition exit 0 not 2 (PR-006); `git stash` replaced by a throwaway worktree (PR-007); execution contract completed (PR-008); `aw sanitize` no longer cited as surface evidence, multi-token case added (PR-009); E-06 de-duplicated (PR-010). Findings and five decisions in `.aw/records/reviews/20261001-enygec-01-z7ci8k-stop-a-home-path-selector-crashing-the-attention-runs-and-pa.review.md`.

- 2026-10-01 draft (opencode): created.
- 2026-10-01 to-review (opencode): authored from backlog `enygec`. Re-measured every site the carrier named, CORRECTED three of its claims (see F-02, F-03, F-08), found two echo sites and one whole surface the carrier missed (F-04, F-05), and resolved the "what is a selector SHOWN AS" product question from the repository's own shipped precedent rather than deferring it (OQ-01).

## Goal

Make a path-shaped argument produce the refusal the command already knows how to emit, instead of a crash. Today `aw attention <home path> --agent`, the same with `--json`, and `aw runs <home path> --agent`/`--json` all exit 1 with an empty stdout and a Python traceback, because each builds an `aw.agent/v1` record by hand with the user's token interpolated verbatim and then calls the validator, whose home-path rule refuses the record the command is trying to print. The refusal is correct about the record; the bug is that nobody sanitized the token on the way in. This plan sanitizes at each site with the shared `agent_schema.redact_home_paths` primitive (already landed by `9yd6tx`, F-11), and pins the class with tests so the next hand-built record cannot reintroduce it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the one primitive these sites need

- [x] E-01 CONSUME the already-landed `agent_schema.redact_home_paths` (added by plan `9yd6tx`, commit `125d585e5`, now `executed`); do NOT write a second definition and do NOT edit `agent_schema.py`, which is no longer in Scope-Paths. Before touching any call site, confirm the landed function still has the contract the sites below rely on, by calling it (not by reading its source): it rewrites an embedded home prefix to `~` in place inside free text, covers all three classes (POSIX, macOS, Windows, the last keeping its drive prefix as `<drive>:\Users\~`), is idempotent, and returns non-string input unchanged. It is the right primitive and `normalize_repo_path` is not, for the two reasons F-06 and F-07 record. If the landed function is ABSENT or has changed shape, that is a prerequisite failure: STOP and report rather than re-adding it here.
  - Depends on: none
  - Expected outcome: a pasted probe showing `redact_home_paths` applied to a POSIX, a macOS and a Windows home path, to an embedded mid-string form, to a `repr()`-quoted form and a `shlex.quote`d form (the two quoting styles the call sites below actually produce), and to `None`, each result carrying no username and matching neither detector.
  - Execution state: performed

- [x] E-02 Pin the CALL-SITE outputs against the repository's OWN detectors, both of them, in the new test module from E-08: for each sanitized record E-03 to E-05 produce, walk every string in the parsed record and assert neither `agent_schema._HOME_PATH_RE` nor any of `leak_sanitizer._FAIL_PATTERNS['home-path']`, `['users-path']`, `['windows-home']` matches. Do NOT re-test the primitive's per-class behavior or the detectors' mutual agreement: the former is already pinned by `tests/test_json_surface_leak_posture.py::HomePathRedactionAgreementTests` and the latter by `tests/test_home_path_pattern_source.py::test_derivation_identity` and `test_cross_module_agreement_corpus` (both landed, F-09). Duplicating them would add a third copy of the same assertion with no new behavior pinned.
  - Depends on: E-01
  - Expected outcome: a shared record-walk helper in the new module, used by every E-08 machine-surface case, that fails if any string anywhere in a parsed record matches either detector.
  - Execution state: performed

### Task group 2: sanitize the three hand-built records

- [x] E-03 In `attention.unresolved_selector_agent_record`, apply `redact_home_paths` to every token list and to the `error` string: `unresolved_selectors`, `unresolved_targets`, the interpolated `quoted` tokens inside `error`, and the two conditional lists `matched_selectors` and `invalid_selectors`. All five are echo sites and the carrier named only three (F-04). Apply it to the whole field, not only the first element: a multi-token invocation such as `aw attention <home path> bogus99 --agent` crashes today on `unresolved_selectors[0]` while `[1]` is innocuous, and a fix that sanitized only a single-token record would still crash there. Leave the field names, the record shape, the `exit`/`verified`/`complete` values and the `assert_valid_agent_record` call EXACTLY as they are: this item changes what goes INTO the record, never the record's contract, and the validator call must stay so the site keeps failing closed on anything this sanitization does not cover.
  - Depends on: E-01
  - Expected outcome: `aw attention <home path> --agent` and `--json`, and the multi-token `aw attention <home path> bogus99 --agent`, exit 2 with a parseable record on stdout whose every field is home-path-free, instead of exiting 1 with a traceback. Note on reachability: `aw attention z7ci8k <home path> --agent` DOES populate `matched_selectors` (with the innocuous `z7ci8k`), but no probed CLI invocation puts a HOME-PATH token into `matched_selectors` or populates `invalid_selectors` at all (see F-04's measured correction), so the redaction of those two branches is pinned by calling `unresolved_selector_agent_record` directly with a constructed `SelectorMatchFacts`, the same construction `tests/test_attention.py::test_selector_match_facts_refusable` already uses.
  - Execution state: performed

- [x] E-04 In `run_viewer`, apply `redact_home_paths` to the token list and to the message in `_unresolvable_target_refusal`, and inside `format_unresolvable_target_message` sanitize BOTH the interpolated tokens and the `analytics_root(repo_root)` value it prints in its reserved-analytics-tree note. That second value is an independent absolute-path leak the carrier did not name: measured, a target under the analytics tree makes the message carry the repo's own absolute root, so the record refuses even when the user's token is innocuous (F-05). Because that value is a WHOLE PATH the command itself computed relative to a known `repo_root`, render it with `agent_schema.normalize_repo_path(analytics_root(repo_root), repo_root)` (measured at review: returns `.aw/records/runs/analytics` for both `Path('.')` and the absolute repo root), and apply `redact_home_paths` to that result only as a backstop for a records backend resolving outside the repo. Home redaction ALONE is not sufficient for this value: on a checkout that is not under a home directory the absolute root would pass the validator yet still violate the cli-output-contract repo-relative rule and spec F8a's no-absolute-path principle (F-10). The F-07 caveat against `normalize_repo_path` applies to USER tokens of unknown provenance, not to a path the command derived from `repo_root`. Note the function is `run_viewer._unresolvable_target_refusal`, NOT the `emit_unresolvable_target_refusal` the carrier and three `attention` docstrings name; that symbol does not exist (F-02).
  - Depends on: E-01
  - Expected outcome: `aw runs <home path> --agent`/`--json` exit 2 with a home-path-free record; `aw runs <a path under the analytics tree> --agent` likewise, where it crashes today, with the note naming the analytics tree as a repo-relative path (`.aw/records/runs/analytics` on a repository-backed checkout) rather than as `~/...` or an absolute path.
  - Execution state: performed

- [x] E-05 In `partition.run_partition`, apply `redact_home_paths` to each `commands` entry for the two MACHINE surfaces only, i.e. build one redacted list and use it in BOTH the `is_agent` record and the `is_json` payload, leaving the HUMAN branch (`for cmd in commands: print(cmd)`) emitting the unredacted command. This is the ACTUAL partition defect and it is not the one the carrier described: the carrier's `unknown` field was unreachable dead weight (F-03) and has since been REMOVED from both machine surfaces by plan `0hz005` (commit `3595e1796`), so there is nothing left to say about it. What really crashes is `commands`, built by `format_shard` from `--model`, `--variant` and `--as`, any of which may legitimately be a path. WHY THE HUMAN BRANCH STAYS RAW: it is the only surface whose output is meant to be piped straight into a shell, and `~` inside a `shlex.quote`d argument (`'~/x'`) is NOT tilde-expanded, so a redacted command would silently point the runner at a nonexistent model path; the machine records are descriptive and are where the validator and the cli-output-contract apply. WHY `is_json` IS INCLUDED (reversing the authored Deferred entry, see PR-004): `--json` shares the exact same `commands` list, `9yd6tx` has since landed and declared the `--json` posture as home-path-redacted for free-text fields (`docs/cli-output-contract.md` "Path Sanitization and Leak Posture"), so there is no longer a pending decision to pre-empt, and leaving it raw would keep a silent leak at exit 0 on a surface this plan already edits.
  - Depends on: E-01
  - Expected outcome: `aw partition -t plans -s to-review --model <a home path> --agent` emits its result record with the model path redacted inside every `commands[i]` instead of exiting 1 with a traceback; the same with `--variant` and `--as`; `--json` emits the same redacted `commands`; the human surface prints the command with the real path unchanged.
  - Execution state: performed

- [x] E-06 Apply `redact_home_paths` to the human-surface counterparts of the two REFUSAL sites, so the human and machine surfaces say the same thing about the same token. For `attention` that is `format_unresolved_selector_message`: its `summary` and EVERY `filters` value (`unmatched`, `matched selectors`, `not a valid selector`), since each echoes tokens. For `runs` the human stderr path prints the SAME `format_unresolvable_target_message` string E-04 already sanitizes, so E-04 covers it and this item only verifies it; do not add a second redaction there. `partition`'s human surface is deliberately NOT redacted (E-05 states why: it is a shell-ready command line). This is not cosmetic parity: these messages print the operator's own argument back to a terminal that is routinely pasted into a shared context, which is the exact reason spec `attention-registry-and-cross-tree-status` F8a gives for forbidding an absolute path on any surface (F-10). The human path does not crash today, so this item is a leak fix and not a crash fix, and it must be reported as such.
  - Depends on: E-01
  - Expected outcome: the human refusal for a home-path token, on both `aw attention` and `aw runs`, names the token in redacted form on stderr, still identifying which argument failed, still exits 2, and no line of that stderr matches either home detector.
  - Execution state: performed

### Task group 3: declare it and pin it

- [x] E-07 Amend `docs/cli-output-contract.md` so its "Path Sanitization and Leak Posture" invariant (as rewritten by `9yd6tx`) covers an INBOUND user-supplied token and a command-specific field of a HAND-BUILT record, not only the named envelope fields. The invariant today enumerates `target`, `location`, `path`, `detail`, `fix`, `summary`, `next`, all fields `CommandResult` emits, so a record a command builds by hand (`unresolved_selectors`, `unresolved_targets`, `error`, `commands`) is not visibly covered, which is why three hand-built records could echo an argument verbatim while every author believed they were conforming. State that any record field carrying a user-supplied token or a command-composed path is sanitized by the producer before the record is built, and that the validator is a backstop rather than the mechanism. Keep the existing wording (repo-relative normalization, the `data` exemption, the composed-path sentence) intact: this adds a clause, it does not rewrite the invariant.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: a reader can answer "may I interpolate the user's argument into a record I build by hand?" from the contract, without reading the validator.
  - Execution state: performed

- [x] E-08 Add `tests/test_selector_echo_sanitization.py` driving the commands as SUBPROCESSES (against a temp repository fixture holding at least one `to-review` plan, so `partition` has a non-empty shard to format a command for and the outcome does not depend on the live corpus' plan population) with a home-path-shaped token, asserting per invocation: the EXPECTED exit code (`2` for the `attention` and `runs` refusals; `0` for `partition`, whose record is a result and not a refusal), stdout parses as JSON on the machine surfaces, every string in the parsed record passes the E-02 walk helper, stderr carries no `Traceback`, and the token is still IDENTIFIABLE in redacted form (its non-home tail is present) so the refusal remains actionable. Cases: `attention` single-token and multi-token (`<home path> bogus99`) on `--agent`, `--json` and human; `runs` on `--agent`, `--json` and human; the analytics-tree target from E-04 on `--agent` and human, asserting the note names a repo-relative tree; `partition` with `--model`, `--variant` and `--as` on `--agent` and `--json`, plus one human-surface case asserting the printed command still carries the UNREDACTED path (E-05's deliberate exception). Pin the `matched_selectors`/`invalid_selectors` branches of E-03 by a direct call to `attention.unresolved_selector_agent_record` with a constructed `SelectorMatchFacts` carrying a home path in `matched` and `invalid`. Build every path literal by concatenation with a `# split: leak guard` comment, the technique `tests/test_agent_schema_paths.py` already uses, so the test file does not itself trip the repository's leak sanitizer.
  - Depends on: E-02, E-03, E-04, E-05, E-06
  - Expected outcome: a module whose machine-surface cases fail on pre-change code (`attention`/`runs`/`partition --agent`: exit 1, empty stdout, traceback; `partition --json`: exit 0 with a home path in `commands`, i.e. a leak and not a crash) and all pass after task group 2.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `agent_schema` imports only the stdlib plus the stdlib-only leaf `agent_workflows.home_path_patterns` (landed by `1xthrh`), so its `redact_home_paths` is reachable from `attention`, `run_viewer` and `partition` with no new dependency and no import cycle, and all three already import the module (`attention` lazily inside the record builder as `_agent_schema`, `run_viewer` as `_agent_schema`, `partition` at module level as `agent_schema`).
- The repository holds distinct postures toward a home path and this plan adds none: `assert_valid_agent_record` REFUSES, `normalize_repo_path` relativizes to the repo, `config._preserve_home` rewrites a whole path value to `~`, `leak_sanitizer._rewrite_line` rewrites the two POSIX classes to `~` inside a line of text, and `agent_schema.redact_home_paths` (landed by `9yd6tx`) rewrites all three classes inside free text. The last is exactly what the echo sites need and E-01 consumes it.
- `aw sanitize --agent` is the repository's own authority for judging leak posture rather than eyeballing (AGENTS.md), and `docs/cli-output-contract.md` already cites it in the Path Sanitization invariant: "All records pass `aw sanitize --agent` with zero findings." That sentence describes the RECORD, which these three commands currently fail to emit at all; and `aw sanitize` cannot check it, because it scans files and never another command's stdout (`9yd6tx` F-13), which is why E-02/E-08 assert on emitted records directly. E-07 reconciles the contract wording.
- Test literals naming a home path are built by concatenation with a `# split: leak guard` comment so the test source does not trip the sanitizer; `tests/test_agent_schema_paths.py` establishes the convention.

## Findings

| # | Finding |
|---|---|
| F-01 | THE CARRIER'S CRASH REPRODUCES AT HEAD, AND IS WORSE THAN REPORTED. Measured on this lane: `attention <home path> --agent`, `attention <same> --json`, `runs <same> --agent` and `runs <same> --json` each exit **1** with EMPTY stdout and a 23-line Python traceback on stderr. Two consequences the carrier did not record. First, the exit code is WRONG as well as the output: `docs/cli-output-contract.md` Section 3 classifies `2` as cannot-run and the record both sites build carries `"exit": 2`, so an automated caller sees `1` ("domain findings") for an invocation that produced no finding at all, and `aw attention --agent` on a typo is indistinguishable from `aw attention --agent` reporting one real finding. Second, THE TRACEBACK PRINTS THE PATH THE RECORD REFUSED TO PRINT: the validator's message interpolates the offending value (`Unsanitized absolute home path in field 'unresolved_selectors[0]': '<the path>'`), so the leak-prevention mechanism leaks, on stderr, in full. |
| F-02 | THE CARRIER NAMES A SYMBOL THAT DOES NOT EXIST, and so do three docstrings. `run_viewer.emit_unresolvable_target_refusal` is nowhere in the package; the real function is `run_viewer._unresolvable_target_refusal` (leading underscore, no `emit_`). The stale name survives in `attention.py` in three places, including inside `unresolved_selector_agent_record`'s own docstring, where it is cited as the shipped precedent this record was shaped on. An executor following the carrier's name finds nothing. Noted so E-04 names the real symbol, and so the three stale citations are not mistaken for a fourth site. |
| F-03 | THE CARRIER'S PARTITION DIAGNOSIS IS WRONG, AND THE REAL ONE IS A DIFFERENT FIELD. It says `partition`'s agent branch "does the same with user-supplied ids in `unknown`". Measured: `partition.collect` has exactly ONE return statement, `return candidates, []`, so `unknown_ids` is ALWAYS the empty list and can echo nothing; an unknown selector does not flow into it but raises `ValueError` from one of 11 raise sites, which `run_partition` catches and prints to stderr, exiting 2 cleanly with no record built. Confirmed end-to-end: `partition -t plans <home path> --agent` exits 2 with a clean one-line stderr and no traceback. The real crash is `commands`: `aw partition -t plans -s to-review --model <home path> --agent` exits **1** with `Unsanitized absolute home path in field 'commands[0]'`, and `--variant` and `--as` crash identically, because `format_shard` interpolates each into the command line it formats. So the partition fix is E-05's `commands`, not the carrier's `unknown`. REVIEW UPDATE (2026-10-07, PR-002): the `unknown` half of this finding is now HISTORY, because plan `0hz005` (commit `3595e1796`) removed the key from both machine surfaces and `collect` now returns `candidates` alone; re-measured at review HEAD `db8c72a9a`, the `commands` crash reproduces for `--model`, `--variant` and `--as` exactly as stated, and `partition -t plans <home path> --agent` still exits 2 with one clean stderr line. |
| F-04 | THE ATTENTION SITE HAS FIVE ECHO FIELDS, NOT THE THREE THE CARRIER COUNTED. `unresolved_selector_agent_record` interpolates `facts.refusable` into `unresolved_selectors`, into `unresolved_targets` (the same list under the `aw runs` precedent's name, a deliberate D2 decision), and into `error` via its `quoted` tokens. It ALSO conditionally sets `matched_selectors` from `facts.matched` and `invalid_selectors` from `facts.invalid`, both raw. REVIEW CORRECTION (2026-10-07, PR-003): the authored claim that a multi-token invocation puts the HOME PATH into these two fields does not reproduce. Measured: `aw attention z7ci8k <home path> --agent` populates `matched_selectors` with `z7ci8k` (innocuous) and crashes on `unresolved_selectors[0]`, not on `matched_selectors`; a home-path token is never MATCHED because nothing in the tracked trees contains it (an absolute path to a REAL plan file is also reported unmatched, measured); and `invalid_selectors` was empty for every probed token (`:`, `set:`, `[`, `*`, `x:y:z`, `\\`, and a home path) because `selectors.resolve` raises nowhere, so `selector_match_facts`' `raised_everywhere` is never true from the CLI. The fields remain echo sites that a future resolver change could make reachable, so E-03 still redacts them, but their behavior is pinned by a direct call with constructed facts rather than by an invocation that cannot reach them. The validator walks the record RECURSIVELY (`_check_string_values` descends into lists and dicts), so a leak in either conditional field refuses the whole record exactly as a leak in the primary one does. E-03 covers all five. |
| F-05 | THE RUNS SITE LEAKS WITHOUT ANY HELP FROM THE USER, which makes it the more serious of the two refusals. `format_unresolvable_target_message` prints `analytics_root(repo_root)` verbatim in its note for a target inside the reserved analytics tree, and that value is an ABSOLUTE path. Measured on an existing, non-home repo path: `runs .aw/records/runs/analytics/nonexistent-run --agent` exits **1** with a traceback naming the repository's absolute analytics root, and the human surface exits 2 printing it. So this site crashes on a token containing no home path at all, purely from a value the command supplied itself, and no amount of input sanitization alone fixes it. E-04 renders the root repo-relative as well as redacting the token (PR-005). |
| F-06 | `normalize_repo_path` CANNOT BE USED FOR THE `error` STRINGS, which is decisive for the primitive choice. It is a whole-path-VALUE function: measured, `normalize_repo_path('aw foo /home/<user>/x.md')` returns the input UNCHANGED and `_HOME_PATH_RE` still matches it. Both refusal sites build an `error` (and `run_viewer` a multi-line `message`) with tokens embedded in prose, so the carrier's suggested `normalize_repo_path` is inert on exactly the field that is hardest to fix. Independently measured and recorded in plan `9yd6tx` F-06 (now executed). |
| F-07 | `normalize_repo_path` IS ALSO UNSAFE FOR THE TOKEN LISTS, by a mechanism neither the carrier nor `9yd6tx` records, and this finding is why E-01 does not simply reuse it. It satisfies the VALIDATOR while PRESERVING THE USERNAME: measured, `normalize_repo_path('/home/<user>/x.md')` returns `'<user>/x.md'`, for which `_HOME_PATH_RE.search` is `None`, so the record validates and ships with the username as its leading path component. Measured against the repository's own identity rule on a real home path of the form `/home/<user>/<one file>`: the output still matches `leak_sanitizer._FAIL_PATTERNS['handle']`. So using `normalize_repo_path` here would convert a loud crash into a SILENT leak that passes the validator and fails `aw sanitize`, which is strictly worse than the present defect. (It also silently falsifies an out-of-repo path into a repo-relative one that does not exist here, `9yd6tx` F-06.) |
| F-08 | THE CARRIER OVERCOUNTS `run_analytics_cli` AND THE SURFACE IT NAMES IS NOT DEFECTIVE. It claims "two further direct `render_jsonl_record` callers". There is exactly ONE (`run_analytics_cli`, the `runs query` refusal branch); the second path reaches the serializer through `AgentRenderer`, so it is renderer-mediated and belongs to `wqiofa`. More to the point, the one direct caller does NOT have this defect, and the reason is instructive: its `reason` and `verdict` come from the statistics engine, not from the user, and its one user-facing refusal path builds its message through `run_analytics_query._refuse_field`, which DELIBERATELY does not interpolate the caller's token ("reflecting arbitrary input into an error that is printed, logged and possibly parsed is a needless injection surface for zero diagnostic gain"). Measured: `runs query metrics --filter bogus=<home path> --agent`, `--group-by <home path>`, `--metric <home path>` and a bare `<home path>` view all exit 2 with a clean valid record. That site is the CORRECT PRECEDENT for the three this plan fixes, and it is excluded from scope because it has no bug. |
| F-09 | REVIEW UPDATE (2026-10-07, PR-001): RESOLVED UPSTREAM SINCE AUTHORING. Plan `1xthrh` (commit `76bd31421`, carrier `ddhpcb` now `done`) made `agent_workflows/home_path_patterns.HOME_PATH_RULES` the single datum both detectors derive from, pinned by `tests/test_home_path_pattern_source.py::test_derivation_identity` and `test_cross_module_agreement_corpus`, so the duplication below no longer exists and E-02 no longer pins detector agreement. The authored text is kept as the record of what was true on 2026-10-01: THE TWO HOME-PATH DETECTORS ARE DUPLICATED WITH NO AGREEMENT TEST, which is why E-02 pins against both. `agent_schema._HOME_PATH_RE` is one fused alternation; `leak_sanitizer._FAIL_PATTERNS` holds the same three forms as the separate rules `home-path`, `users-path` and `windows-home`, character-for-character identical in their path parts. There is no shared constant and no test asserting they agree. F-07's measurement shows the gap is live rather than theoretical: a value can satisfy one and fail the other. This plan does NOT unify them (recorded in Deferred, carrier `ddhpcb` per `9yd6tx` F-07); E-02 merely ensures the new primitive satisfies both and so adds no third independent definition. |
| F-10 | AN IMPLEMENTED SPEC ALREADY FORBIDS THIS, so the posture is settled and not an open design question. Spec `attention-registry-and-cross-tree-status` F8a: "No output surface (human board, `--agent`, `--json`) may contain an ABSOLUTE filesystem path ... these surfaces are pasted into shared contexts, so printing it verbatim is forbidden." It names the human surface explicitly and in the same breath as the two machine ones, which is the authority for E-06 covering the human path rather than leaving it. The spec is about a LANE path and this plan is about a selector token, so this plan does not implement F8a; it stops three commands violating the principle F8a states, which is why no spec amendment is owed (see Spec sync). |
| F-11 | REVIEW UPDATE (2026-10-07, PR-001): THE BRANCH THIS FINDING ANTICIPATED HAS HAPPENED. `9yd6tx` executed (commit `125d585e5`) and `agent_schema.redact_home_paths` is on HEAD with the contract described below (measured at review: POSIX and macOS rewrite to `~`, Windows to `<drive>:\Users\~`, embedded, `repr()`-quoted and `shlex.quote`d forms all redact in place, `None` passes through). So E-01 now CONSUMES it unconditionally and `agent_schema.py` left Scope-Paths. Authored text: THIS PLAN OVERLAPS `9yd6tx` ON ONE FUNCTION AND MUST NOT RACE IT. Pending plan `9yd6tx` (Set `7tixnq`, `Status: to-review`) declares `agent_workflows/agent_schema.py` in Scope-Paths and its E-01 adds `redact_home_paths` to that module, for `--json`'s `CommandResult.to_dict` fields. That is the same primitive E-01 needs, specified compatibly (all three classes, `~`, idempotent, non-string passthrough). Neither plan depends on the other and their APPLICATION sites are disjoint (`9yd6tx` touches `result_types`; this touches three hand-built records), so they are order-independent, but whichever executes second must CONSUME the landed function rather than write a second one. E-01 states that branch explicitly. No `Item-Dependencies` edge is declared, because an edge would serialize two independent plans and park this release-gating bug behind a chore. |
| F-12 | REVIEW UPDATE (2026-10-07, PR-001): MOOT for E-01, which no longer writes a primitive; kept because it still explains why `_rewrite_line` is not the function to call. `leak_sanitizer._rewrite_line` CANNOT BE DELEGATED TO, which bounded E-01's original "reproduce, do not reuse". Its rewrite covers only the two POSIX forms (`_HOME_ANY_RE`, `_USERS_ANY_RE`); the Windows class is absent, and `_FAIL_PATTERNS['windows-home']` still matches its output. The omission is deliberate and self-documented at the definition ("Only home/Users paths are auto-rewritten (safe, generic) ... no safe generic replacement"), since a bare `~` would lose the drive letter. `agent_schema` also must not import `leak_sanitizer` (it is stdlib-only, and `leak_sanitizer` imports `renderers`/`result_types` lazily inside `main` precisely to avoid that cycle). That three-class version now exists (`9yd6tx`). |
| F-13 | THE DEFECT CLASS HAS NO TEST COVERAGE AT ALL, so E-08 regresses nothing. No test anywhere passes a path-shaped token to any of these sites. The nearest existing assertions use innocuous tokens: `tests/test_attention.py::SelectorNoMatchIsReportedTests::test_selector_no_match_is_reported` drives `zzzzzz` and covers `--format json` but NOT `--agent`; `tests/test_run_viewer.py::test_unresolvable_target_refusal` drives `totalgibberish` on both machine surfaces; `tests/test_partition.py::test_cli_partition_agent_mode` validates a record built with no path-bearing flag. `attention.unresolved_selector_agent_record` and `format_unresolved_selector_message` have zero direct test references (re-measured at review; `SelectorMatchFacts.refusable` has since gained one, `tests/test_attention.py::test_selector_match_facts_refusable`, which is also the construction E-08 reuses). So every assertion E-08 adds is new, and the three existing tests above must keep passing unchanged. |
| F-14 | THE `--json` SURFACE CRASHES HERE TOO, WHICH IS A DIFFERENT SHAPE FROM `9yd6tx`'s FINDING. `9yd6tx` F-01 measured `--json` as the surface that LEAKS while `--agent` REFUSES. That holds for renderer-mediated output, but not for these sites: `attention` and `run_viewer` route `--json` through the SAME hand-built record and the same `assert_valid_agent_record`, so `--json` crashes identically (measured, F-01). `partition` is the exception and shows the asymmetry inside one command: its `is_agent` branch calls `render_jsonl_record` and crashes, while its `is_json` branch calls `json.dumps` directly and emits the home path cleanly with exit 0. So this plan fixes a crash on five invocations and a silent leak on one, and must not describe `--json` uniformly as either. REVIEW UPDATE (2026-10-07, PR-004): the silent `partition --json` leak re-measures at HEAD (exit 0, the home path verbatim in both `commands` entries) and is now IN scope (E-05), since `9yd6tx` has landed the `--json` posture the authored Deferred entry was waiting for. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/agent_schema.py`** is NOT edited. Its `redact_home_paths`, landed by `9yd6tx`, is consumed as-is after a behavioral probe confirms its contract (E-01, F-11). No new primitive is added.
2. **`agent_workflows/attention.py`** applies it in `unresolved_selector_agent_record` to all five echo fields (E-03) and in `format_unresolved_selector_message` for the human surface (E-06). The record shape, field names, exit code and the `assert_valid_agent_record` backstop are untouched.
3. **`agent_workflows/run_viewer.py`** applies it in `_unresolvable_target_refusal` to the token list and the message, and in `format_unresolvable_target_message` to the interpolated tokens, rendering the `analytics_root(repo_root)` value repo-relative via `normalize_repo_path` with `redact_home_paths` as backstop (E-04). Its human stderr path prints the same string, so E-06 only verifies it.
4. **`agent_workflows/partition.py`** applies it to `commands` for BOTH machine surfaces (`is_agent` and `is_json`), leaving the shell-ready human output raw (E-05). The `unknown` key is already gone (`0hz005`).
5. **`docs/cli-output-contract.md`** extends the "Path Sanitization and Leak Posture" invariant to cover an inbound user-supplied token and a hand-built record's command-specific fields, stating the validator is a backstop and not the mechanism (E-07).
6. **`tests/test_selector_echo_sanitization.py`** pins the class behaviorally across three commands and three surfaces by subprocess against a temp repository fixture, asserting the expected exit code, parseable stdout, no home path in any field, no traceback, and a still-identifiable redacted token (E-02, E-08).

## Deferred / out of scope (with reason)

- **Removing `partition`'s dead `unknown` key.** No longer deferred work: DONE upstream by plan `0hz005` (commit `3595e1796`, carrier `vf3mw2` now `done`). Recorded so a reader of F-03 knows why E-05 no longer mentions it.
  - Carrier-Declined: Nothing is owed. The key was removed by `0hz005` before this plan executed.
- **Unifying `agent_schema._HOME_PATH_RE` with `leak_sanitizer._FAIL_PATTERNS`' three home rules** (F-09). No longer deferred work: DONE upstream by plan `1xthrh` (commit `76bd31421`, carrier `ddhpcb` now `done`).
  - Carrier-Declined: Nothing is owed. Both detectors already derive from `home_path_patterns.HOME_PATH_RULES`.
- **Redacting `partition`'s HUMAN output** (E-05). Deliberately not done: it is a shell-ready command line and a `~` inside a `shlex.quote`d argument is not tilde-expanded, so redacting it would break the command a user pipes into a shell. A human who pastes that output is pasting a command naming their own model path by choice.
  - Carrier-Declined: Nothing is owed. This is a deliberate behavior decision (review D-2), not deferred work.
- **`run_analytics_cli`'s `render_jsonl_record` caller**, which the carrier listed. Excluded because F-08 measures it as NOT defective: its fields come from the statistics engine, and its user-facing refusal path deliberately declines to interpolate the caller's token. Including it would be a change with no defect behind it.
  - Carrier-Declined: Nothing is owed. This is a measurement, not deferred work: four probe invocations with home-path arguments all produced clean valid records at exit 2.
- **`renderers.py`'s guarded serializer and `AgentRenderer`'s unguarded raise.** That is `wqiofa`'s scope, and the carrier is explicit that routing these hand-built sites through it would MASK this defect behind a generic refusal rather than fix it. This plan deliberately keeps each site's `assert_valid_agent_record` call as a fail-closed backstop.
  - Carrier: un6ppd
- **Teaching `leak_sanitizer._rewrite_line` the Windows class** (F-12). Self-documented as deliberate, with the drive-letter reason. Nothing here depends on it.
  - Carrier: 9cff1j

## Scope check

- Over-scope: none. Eight E-items touch zero new helpers (E-01 consumes the landed one), three record-building sites, one human message builder (plus a verification of the second), one doc invariant and one new test module. No record field is renamed or removed, no exit code contract is redefined (the fix RESTORES the documented `2`), no renderer class is touched, and no selector resolution behavior changes.
- Under-scope: `partition`'s human output keeps the unredacted command by design (E-05). `run_analytics_cli` is untouched by measurement, not omission (F-08). The three stale `emit_unresolvable_target_refusal` docstring citations in `attention.py` (F-02) are NOT corrected here: they are a comment accuracy question in a file this plan edits, and folding a docstring sweep into a release-gating bug fix broadens the diff for no behavioral gain.

## Required tests / validation

- `python3 -m pytest tests/test_selector_echo_sanitization.py` passes, with per-test counts captured via `-o addopts=""` where a count is needed.
- The three existing tests F-13 names pass UNCHANGED, together with the two modules pinning the consumed primitive and the shared detector datum: `python3 -m pytest tests/test_attention.py tests/test_run_viewer.py tests/test_partition.py tests/test_agent_schema_paths.py tests/test_json_surface_leak_posture.py tests/test_home_path_pattern_source.py`.
- The full suite passes BARE: `python3 -m pytest` (configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`). Paste the actual `N passed` summary line.
- Every crashing invocation from F-01, F-03 and F-05 exits with its DOCUMENTED code, a parseable record and no traceback: exit **2** for `attention <home path> --agent`, `attention <home path> --json`, `attention <home path> bogus99 --agent`, `runs <home path> --agent`, `runs <home path> --json` and `runs <analytics-tree path> --agent`; exit **0** for `partition -t plans -s to-review --model <home path> --agent` (and `--variant`, `--as`), whose record is a RESULT and not a refusal. `partition ... --json` emits the same redacted `commands`.
- `aw sanitize --agent` reports no new finding on the tree (including on the new test module, which must use the `# split: leak guard` concatenation convention). Note its limit, recorded by `9yd6tx` F-13: it scans files and history, never another command's stdout, so it proves the TEST SOURCE is clean and says nothing about the emitted records; the record-walk assertions in E-02/E-08 are what prove the surfaces clean.
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

- [x] V-01 validates E-01
  - Required evidence: paste the `git log --oneline -1 125d585e5` line proving `9yd6tx` landed the primitive, and the output of `git diff <base>..HEAD -- agent_workflows/agent_schema.py` being EMPTY, proving no second definition was added. Then paste a Python session calling `agent_schema.redact_home_paths` on one input per home class (POSIX, macOS, Windows), on an embedded mid-string form, on a `repr()`-quoted and a `shlex.quote`d form, and on `None`. For each paste the returned value AND the boolean `agent_schema._HOME_PATH_RE.search(result) is None`. Every boolean must be `True`, `None` must return `None`, and the embedded case must show the surrounding text preserved (a redaction, not a drop). If the function is absent or behaves otherwise, the item FAILS and the executor stops per E-01.
  - Observed evidence:
    `git log --oneline -1 125d585e5`:
    ```
    125d585e5 work(9yd6tx): Give the --json surface one declared leak posture and sanitize the fields that carry a home path
    ```
    `git diff de3edd0cc75c383ff804a0cddfd9863bbd7d9caa..HEAD -- agent_workflows/agent_schema.py`: (empty)
    Python session probe:
    ```
    POSIX: inp='/home/alice/foo.txt' -> res='~/foo.txt', _HOME_PATH_RE search is None: True
    macOS: inp='/Users/<user>/bar.txt' -> res='~/bar.txt', _HOME_PATH_RE search is None: True
    Windows: inp='C:\\Users\\<user>\\baz.txt' -> res='C:\\Users\\~\\baz.txt', _HOME_PATH_RE search is None: True
    embedded: inp='error in /home/alice/nested/file.txt during test' -> res='error in ~/nested/file.txt during test', _HOME_PATH_RE search is None: True
    repr-quoted: inp="'/home/alice/quoted.txt'" -> res="'~/quoted.txt'", _HOME_PATH_RE search is None: True
    shlex-quoted: inp='/home/alice/quoted.txt' -> res='~/quoted.txt', _HOME_PATH_RE search is None: True
    None: inp=None -> res=None, _HOME_PATH_RE search is None: True
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the record-walk helper's source from the new module (a test FILE, not production code, so P16 is not engaged) and a run of the E-08 module with `-o addopts=""` showing every machine-surface case calls it. Prove the helper is FALSIFIABLE without touching production code: in a scratch Python session, feed it a hand-constructed record carrying a home path in a nested list element and paste the assertion failure naming that element; feed it the same record with the value redacted and paste it passing. Paste one failing case per detector, so the walk is shown to consult `_HOME_PATH_RE` AND each of the three `leak_sanitizer._FAIL_PATTERNS` home rules by name.
  - Observed evidence:
    Record-walk helper source in `tests/test_selector_echo_sanitization.py`:
    ```python
    def walk_and_assert_no_home_paths(record: Any, path: str = "root") -> None:
        """Recursively assert that no string value in `record` matches any home-path detector.

        Checks both `agent_schema._HOME_PATH_RE` and `leak_sanitizer._FAIL_PATTERNS` home rules
        ('home-path', 'users-path', 'windows-home').
        """
        if isinstance(record, str):
            match_schema = agent_schema._HOME_PATH_RE.search(record)
            ls_matches = [
                p
                for p in ("home-path", "users-path", "windows-home")
                if leak_sanitizer._FAIL_PATTERNS[p].search(record)
            ]
            if match_schema or ls_matches:
                reasons = []
                if match_schema:
                    reasons.append("agent_schema._HOME_PATH_RE")
                if ls_matches:
                    reasons.append(f"leak_sanitizer._FAIL_PATTERNS[{ls_matches}]")
                raise AssertionError(
                    f"Home path detected by {' and '.join(reasons)} at {path}: {record!r}"
                )
        elif isinstance(record, dict):
            for k, v in record.items():
                walk_and_assert_no_home_paths(v, f"{path}[{k!r}]")
        elif isinstance(record, (list, tuple, set)):
            for idx, item in enumerate(record):
                walk_and_assert_no_home_paths(item, f"{path}[{idx}]")
    ```
    Falsifiability demonstration across all detectors:
    ```
    POSIX: Home path detected by agent_schema._HOME_PATH_RE and leak_sanitizer._FAIL_PATTERNS[['home-path']] at root['data']['nested'][1]: '/home/<user>/secret.txt'
    Redacted POSIX: passed
    macOS: Home path detected by agent_schema._HOME_PATH_RE and leak_sanitizer._FAIL_PATTERNS[['users-path']] at root['items'][0]: '/Users/<user>/secret.txt'
    Windows: Home path detected by agent_schema._HOME_PATH_RE and leak_sanitizer._FAIL_PATTERNS[['windows-home']] at root['commands'][0]: 'C:\\Users\\<user>\\secret.txt'
    ```
    Run of E-08 module with `-o addopts=""` showing all 20 cases passed:
    `20 passed in 69.32s (0:01:09)`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste, for `aw attention <home path> --agent`, `--json`, and the multi-token `aw attention <home path> bogus99 --agent`, the exit code (must be `2`; each is `1` today, the F-01 regression) and the full stdout record. Paste the record walk over each reporting zero matches for both detectors. Paste `aw attention z7ci8k <home path> --agent` (or another real id6) showing `matched_selectors` present and the record valid. For the two branches no CLI invocation reaches with a home path (F-04 correction), paste the direct-call test from E-08 passing, with the constructed `SelectorMatchFacts` putting a home path in `matched` and `invalid`, and the resulting `matched_selectors`/`invalid_selectors` values in `~` form. Finally paste the `error` field in full, showing the token present in `~` form so the message is still actionable.
  - Observed evidence:
    `aw attention <home path> --agent`:
    ```
    exit: 2
    stdout:
    {"schema": "aw.agent/v1", "kind": "error", "cmd": "attention", "outcome": "cannot-run", "exit": 2, "verified": false, "complete": false, "findings": 1, "unresolved_selectors": ["~/sample_target.ipd.md"], "unresolved_targets": ["~/sample_target.ipd.md"], "error": "no artifact matched selector '~/sample_target.ipd.md'; searched the tracked record trees backlog, plans, prompts, releases, research, specs", "next": "aw next"}
    walk_and_assert_no_home_paths: PASS
    ```
    `aw attention <home path> --json`:
    ```
    exit: 2
    stdout:
    {
      "schema": "aw.agent/v1",
      "kind": "error",
      "cmd": "attention",
      "outcome": "cannot-run",
      "exit": 2,
      "verified": false,
      "complete": false,
      "findings": 1,
      "unresolved_selectors": [
        "~/sample_target.ipd.md"
      ],
      "unresolved_targets": [
        "~/sample_target.ipd.md"
      ],
      "error": "no artifact matched selector '~/sample_target.ipd.md'; searched the tracked record trees backlog, plans, prompts, releases, research, specs",
      "next": "aw next"
    }
    walk_and_assert_no_home_paths: PASS
    ```
    `aw attention <home path> bogus99 --agent`:
    ```
    exit: 2
    stdout:
    {"schema": "aw.agent/v1", "kind": "error", "cmd": "attention", "outcome": "cannot-run", "exit": 2, "verified": false, "complete": false, "findings": 2, "unresolved_selectors": ["~/sample_target.ipd.md", "bogus99"], "unresolved_targets": ["~/sample_target.ipd.md", "bogus99"], "error": "no artifact matched selectors '~/sample_target.ipd.md', 'bogus99'; searched the tracked record trees backlog, plans, prompts, releases, research, specs", "next": "aw next"}
    walk_and_assert_no_home_paths: PASS
    ```
    `aw attention z7ci8k <home path> --agent`:
    ```
    exit: 2
    stdout:
    {"schema": "aw.agent/v1", "kind": "error", "cmd": "attention", "outcome": "cannot-run", "exit": 2, "verified": false, "complete": false, "findings": 1, "unresolved_selectors": ["~/sample_target.ipd.md"], "unresolved_targets": ["~/sample_target.ipd.md"], "error": "no artifact matched selector '~/sample_target.ipd.md'; searched the tracked record trees backlog, plans, prompts, releases, research, specs", "next": "aw next", "matched_selectors": ["z7ci8k"]}
    walk_and_assert_no_home_paths: PASS
    ```
    Direct-call test from E-08 (`test_attention_direct_call_matched_and_invalid_redacted`): PASSED.
    Full `error` field:
    `"no artifact matched selector '~/sample_target.ipd.md'; searched the tracked record trees backlog, plans, prompts, releases, research, specs"`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `aw runs <home path> --agent` and `--json` with exit code `2` and their full records, plus the record walk. SEPARATELY paste the F-05 case, `aw runs .aw/records/runs/analytics/<a nonexistent run> --agent`, showing exit `2` and a record whose reserved-analytics-tree note names the tree REPO-RELATIVE (`.aw/records/runs/analytics` on this repository-backed checkout) and contains no absolute path of any kind (not only no home path); this case exits 1 with a traceback today and is the one a token-only fix would miss. Paste the human-surface stderr for the same target showing the same repo-relative note.
  - Observed evidence:
    `aw runs <home path> --agent`:
    ```
    exit: 2
    stdout:
    {"schema": "aw.agent/v1", "kind": "error", "cmd": "runs", "outcome": "cannot-run", "exit": 2, "verified": false, "complete": false, "findings": 1, "unresolved_targets": ["~/sample_target.ipd.md"], "error": "error: no run matched target '~/sample_target.ipd.md'\n  leaves: decisions evidence list next questions resume show status verify-ledger\n  a TARGET is a run id, a run directory path, or a Set id; force viewer interpretation of a leaf-like name with `aw runs -- <target>`", "next": null}
    walk_and_assert_no_home_paths: PASS
    ```
    `aw runs <home path> --json`:
    ```
    exit: 2
    stdout:
    {
      "schema": "aw.agent/v1",
      "kind": "error",
      "cmd": "runs",
      "outcome": "cannot-run",
      "exit": 2,
      "verified": false,
      "complete": false,
      "findings": 1,
      "unresolved_targets": [
        "~/sample_target.ipd.md"
      ],
      "error": "error: no run matched target '~/sample_target.ipd.md'\n  leaves: decisions evidence list next questions resume show status verify-ledger\n  a TARGET is a run id, a run directory path, or a Set id; force viewer interpretation of a leaf-like name with `aw runs -- <target>`",
      "next": null
    }
    walk_and_assert_no_home_paths: PASS
    ```
    `aw runs .aw/records/runs/analytics/nonexistent-run --agent` (F-05 case):
    ```
    exit: 2
    stdout:
    {"schema": "aw.agent/v1", "kind": "error", "cmd": "runs", "outcome": "cannot-run", "exit": 2, "verified": false, "complete": false, "findings": 1, "unresolved_targets": [".aw/records/runs/analytics/nonexistent-run"], "error": "error: no run matched target '.aw/records/runs/analytics/nonexistent-run'\n  note: '.aw/records/runs/analytics/nonexistent-run' is within the reserved analytics tree (.aw/records/runs/analytics); analytics artifacts cannot be targeted as execution runs\n  leaves: decisions evidence list next questions resume show status verify-ledger\n  a TARGET is a run id, a run directory path, or a Set id; force viewer interpretation of a leaf-like name with `aw runs -- <target>`", "next": null}
    walk_and_assert_no_home_paths: PASS
    ```
    Human-surface stderr for the same target:
    ```
    error: no run matched target '.aw/records/runs/analytics/nonexistent-run'
      note: '.aw/records/runs/analytics/nonexistent-run' is within the reserved analytics tree (.aw/records/runs/analytics); analytics artifacts cannot be targeted as execution runs
      leaves: decisions evidence list next questions resume show status verify-ledger
      a TARGET is a run id, a run directory path, or a Set id; force viewer interpretation of a leaf-like name with `aw runs -- <target>`
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste, against a fixture or the live tree with at least one `to-review` plan, `aw partition -t plans -s to-review --max 2 --model <home path> --agent` before (exit 1, traceback naming `commands[0]`) and after (exit 0, valid record with every `commands[i]` carrying the model path in `~` form). Repeat for `--variant` and `--as`. Paste the `--json` form with `--model <home path>` before (exit 0, home path verbatim in `commands`, the F-14 leak) and after (exit 0, `~` form). Paste the HUMAN form after, showing the printed command still carries the REAL path, so the deliberate exception is observed and not assumed.
  - Observed evidence:
    Before:
    `aw partition -t plans -s to-review --model <home>/model --agent` exited 1 with traceback: `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'commands[0]': '... --model <home>/model'`
    After:
    `aw partition -t plans -s to-review --max 2 --model <home>/model --agent`:
    ```
    exit: 0
    stdout:
    {"schema":"aw.agent/v1","kind":"result","cmd":"partition","exit":0,"outcome":"ok","verified":true,"complete":true,"shards":[["2j4pd0"],["62sdwr"]],"commands":["aw oc run --action review 2j4pd0 --model ~/model","aw oc run --action review 62sdwr --model ~/model"],"split_components":[],"cycles":[]}
    walk_and_assert_no_home_paths: PASS
    ```
    `aw partition -t plans -s to-review --max 2 --variant <home>/variant --agent`:
    ```
    exit: 0
    stdout:
    {"schema":"aw.agent/v1","kind":"result","cmd":"partition","exit":0,"outcome":"ok","verified":true,"complete":true,"shards":[["2j4pd0"],["62sdwr"]],"commands":["aw oc run --action review 2j4pd0 --variant ~/variant","aw oc run --action review 62sdwr --variant ~/variant"],"split_components":[],"cycles":[]}
    walk_and_assert_no_home_paths: PASS
    ```
    `aw partition -t plans -s to-review --max 2 --as <home>/profile --agent`:
    ```
    exit: 0
    stdout:
    {"schema":"aw.agent/v1","kind":"result","cmd":"partition","exit":0,"outcome":"ok","verified":true,"complete":true,"shards":[["2j4pd0"],["62sdwr"]],"commands":["aw run as ~/profile --action review 2j4pd0","aw run as ~/profile --action review 62sdwr"],"split_components":[],"cycles":[]}
    walk_and_assert_no_home_paths: PASS
    ```
    `aw partition -t plans -s to-review --max 2 --model <home>/model --json`:
    Before: exited 0 with `<home>/model` verbatim in `commands`.
    After:
    ```
    exit: 0
    stdout:
    {
      "shards": [
        [
          "2j4pd0"
        ],
        [
          "62sdwr"
        ]
      ],
      "commands": [
        "aw oc run --action review 2j4pd0 --model ~/model",
        "aw oc run --action review 62sdwr --model ~/model"
      ],
      "split_components": [],
      "cycles": []
    }
    walk_and_assert_no_home_paths: PASS
    ```
    HUMAN form after:
    ```
    exit: 0
    stdout:
    aw oc run --action review 2j4pd0 --model <home>/model
    aw oc run --action review 62sdwr --model <home>/model
    ```
    The printed command in human mode carries the unredacted path verbatim for shell execution.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the human-surface stderr for `aw attention <home path>` and `aw runs <home path>` (both exit 2), showing the token in `~` form in the summary line AND in every `Active filters:` value, and the message otherwise unchanged. State explicitly that the human path did not crash before this change, so this item is validated as a leak fix and not as a crash fix. Paste the E-08 human-surface test cases passing. (`aw sanitize --agent` is NOT evidence for this item: it never reads command stdout or stderr.)
  - Observed evidence:
    The human paths did not crash prior to this change (they exited 2 but printed the unredacted home path on stderr); this item is validated as a leak fix.
    Human stderr for `aw attention <home>/sample_target.ipd.md`:
    ```
    ✗ FAIL  no artifact matched selector '~/sample_target.ipd.md'

    Active filters:
      unmatched selector: ~/sample_target.ipd.md
      searched trees: backlog, plans, prompts, releases, research, specs

    Next  aw next (show the whole board, then copy an id6 from it)
    ```
    Human stderr for `aw runs <home>/sample_target.ipd.md`:
    ```
    error: no run matched target '~/sample_target.ipd.md'
      leaves: decisions evidence list next questions resume show status verify-ledger
      a TARGET is a run id, a run directory path, or a Set id; force viewer interpretation of a leaf-like name with `aw runs -- <target>`
    ```
    E-08 human-surface test cases (`test_attention_single_token_human`, `test_attention_multi_token_human`, `test_runs_unresolvable_target_human`, `test_runs_analytics_tree_target_human`, `test_partition_human_command_unredacted`): all PASSED.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the `git diff` of `docs/cli-output-contract.md`. It must show the "Path Sanitization and Leak Posture" invariant extended to an inbound user-supplied token and to a hand-built record's command-specific fields, state that the validator is a backstop rather than the mechanism, and leave the existing repo-relative normalization, `data` exemption and composed-path wording intact. Confirm the added prose contains no em or en dashes (user-facing doc, per the execution contract) by pasting a search over the added lines returning nothing.
  - Observed evidence:
    `git diff docs/cli-output-contract.md`:
    ```diff
    diff --git a/docs/cli-output-contract.md b/docs/cli-output-contract.md
    index 761ef6b49..2cc735e5a 100644
    --- a/docs/cli-output-contract.md
    +++ b/docs/cli-output-contract.md
    @@ -267,7 +267,7 @@ Agents (GPT, Gemini, Opus, GLM, etc.) and CI runners must **consume structured r
       - If `complete=False` (and not a non-destructive preview), the outcome is `partial` or `skipped`.
       - If `exit=2`, kind is `error` and outcome is `cannot-run` or `error`.
     - **Exit Code Parity**: The embedded `exit` field in every record MUST equal the process exit code (`0`, `1`, `2`).
    -- **Path Sanitization and Leak Posture**: On both machine surfaces (`--agent` and `--json`), all path-valued and free-text envelope fields (`target`, `location`, `path`, `detail`, `fix`, `summary`, `next`) MUST be repo-relative, normalized (forward slashes, no leading `./`), or home-path-redacted to `~` (POSIX `/home/<user>`, macOS `/Users/<user>`, Windows `<drive>:\Users\<user>`). All records pass `aw sanitize --agent` with zero findings. The `data` dictionary on `--json` is explicitly exempt: it is an unredacted passthrough of command-specific facts where an approved spec (such as spec `kw5y2s` Section 2.4 for `data.logical_roots`) requires absolute paths. The `data` exemption is an exemption from downstream redaction and not a licence for a producer to put an absolute path there: a command-specific payload must itself carry repo-relative text unless an approved spec requires otherwise (as spec `kw5y2s` Section 2.4 does for `data.logical_roots`). Similarly, a field that a producer composes from multiple paths is not reached by `normalize_repo_path`, which takes a whole path value, so relativizing every path component during composition is the producer's responsibility.
    +- **Path Sanitization and Leak Posture**: On both machine surfaces (`--agent` and `--json`), all path-valued and free-text envelope fields (`target`, `location`, `path`, `detail`, `fix`, `summary`, `next`), as well as command-specific fields of hand-built records and any field carrying an inbound user-supplied token (such as `unresolved_selectors`, `unresolved_targets`, `error`, or `commands`), MUST be repo-relative, normalized (forward slashes, no leading `./`), or home-path-redacted to `~` (POSIX `/home/<user>`, macOS `/Users/<user>`, Windows `<drive>:\Users\<user>`). Any record field carrying a user-supplied token or a command-composed path is sanitized by the producer before the record is built, with the validator acting as a backstop rather than the mechanism. All records pass `aw sanitize --agent` with zero findings. The `data` dictionary on `--json` is explicitly exempt: it is an unredacted passthrough of command-specific facts where an approved spec (such as spec `kw5y2s` Section 2.4 for `data.logical_roots`) requires absolute paths. The `data` exemption is an exemption from downstream redaction and not a licence for a producer to put an absolute path there: a command-specific payload must itself carry repo-relative text unless an approved spec requires otherwise (as spec `kw5y2s` Section 2.4 does for `data.logical_roots`). Similarly, a field that a producer composes from multiple paths is not reached by `normalize_repo_path`, which takes a whole path value, so relativizing every path component during composition is the producer's responsibility.
     - **ANSI-Free**: Agent records never contain ANSI escape codes or terminal control characters.
    ```
    Search for em or en dashes:
    ```
    $ git diff docs/cli-output-contract.md | grep '^[+]' | grep -P '[\x{2013}\x{2014}]'
    (empty)
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the bare full-suite run `python3 -m pytest` with its actual `N passed` summary line, and `python3 -m pytest tests/test_selector_echo_sanitization.py -o addopts=""` with per-test counts. Paste the Required-tests regression command proving the F-13 tests and the two primitive/datum modules still pass unmodified. Demonstrate the new module is a real regression test by running it against PRE-CHANGE source WITHOUT `git stash` or `git checkout` in this shared checkout (a restore after a long run can silently discard a co-worker's concurrent edit): use a throwaway `git worktree add` at the pre-change commit with the new test file copied in, run it there, paste the failures (machine-surface cases exiting 1 with empty stdout; `partition --json` showing the leak), and remove the worktree. Finally paste `aw sanitize --agent` clean and `aw ipd lint --phase pre-transition` conforming.
  - Observed evidence:
    Bare full-suite run (`python3 -m pytest`):
    ```
    6702 passed, 2 skipped, 3 warnings in 400.07s (0:06:40)
    ```
    Per-test count run of `tests/test_selector_echo_sanitization.py`:
    ```
    tests/test_selector_echo_sanitization.py ....................            [100%]
    20 passed in 69.32s (0:01:09)
    ```
    Required-tests regression command (`python3 -m pytest tests/test_attention.py tests/test_run_viewer.py tests/test_partition.py tests/test_agent_schema_paths.py tests/test_json_surface_leak_posture.py tests/test_home_path_pattern_source.py`):
    ```
    176 passed in 59.39s
    ```
    Pre-change test run failure demonstration:
    Running `tests/test_selector_echo_sanitization.py` on the pre-change commit produced 19 failures and 1 pass (the deliberate human raw exception):
    ```
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_attention_single_token_agent - AssertionError: 1 != 2
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_attention_single_token_json - AssertionError: 1 != 2
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_attention_multi_token_agent - AssertionError: 1 != 2
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_attention_multi_token_json - AssertionError: 1 != 2
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_runs_unresolvable_target_agent - AssertionError: 1 != 2
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_runs_unresolvable_target_json - AssertionError: 1 != 2
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_partition_model_agent - AssertionError: 1 != 0
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_partition_variant_agent - AssertionError: 1 != 0
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_partition_as_agent - AssertionError: 1 != 0
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_partition_model_json - AssertionError: Home path detected by agent_schema._HOME_PATH_RE and leak_sanitizer._FAIL_PATTERNS[['home-path']]
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_partition_variant_json - AssertionError: Home path detected by agent_schema._HOME_PATH_RE and leak_sanitizer._FAIL_PATTERNS[['home-path']]
    FAILED tests/test_selector_echo_sanitization.py::SelectorEchoSanitizationTests::test_partition_as_json - AssertionError: Home path detected by agent_schema._HOME_PATH_RE and leak_sanitizer._FAIL_PATTERNS[['home-path']]
    ...
    19 failed, 1 passed in 56.58s
    ```
    `aw sanitize --agent`:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
    `aw ipd lint --phase pre-transition`:
    conforming.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan's `- Readiness:` field is written ONLY by `/plan-review` (the 2026-10-07 review wrote it); an author or executor must never hand-write it. Execution requires explicit human approval recorded with `aw ipd set approved z7ci8k --by-human`.

Resolved open questions: OQ-01 and OQ-02 are both `resolved` and non-blocking; there is nothing to ask before executing.

Scope fence (a DECLARATION, not a stop directive): the executor edits only the paths in `- Scope-Paths:`. If the work genuinely requires an edit outside that set, MAKE it and JUSTIFY it: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. STOP and report only for a genuinely unsafe condition: a concurrent edit to one of these files that cannot be safely combined, or a prerequisite symbol (`agent_schema.redact_home_paths`, `agent_schema.normalize_repo_path`, `run_viewer._unresolvable_target_refusal`, `attention.unresolved_selector_agent_record`) that is absent or has changed shape.

Execution contract: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE (`python3 -m pytest`) and PASTE THE ACTUAL RUNNER OUTPUT; a claim of passing tests without pasted output is a contract violation. Do not mark any `V-*` item complete from the matching `E-*` checkmark; inspect the evidence in a separate pass. Write no em or en dashes in `docs/cli-output-contract.md`, which is user-facing prose. Do not use `git stash` or `git checkout` to obtain a before-state in this shared checkout (V-08 names the safe alternative).

Post-gate lifecycle: when every `E-*` item is performed and every `V-*` item carries pasted evidence, run `aw ipd lint --phase pre-transition` and confirm it reports conforming. The terminal transition to `.aw/records/plans/executed/` then happens through the tooled lifecycle and NOT through a hand-rolled `git mv`: if a runner (`aw oc run` / `aw agy run`) is driving this plan the runner OWNS the finalize and the executor must not call it; if the plan is being executed by hand, the executor runs `aw ipd finalize z7ci8k --actor <agent/model> --message <summary> --apply` itself. Backlog item `enygec` is set to `graduated` (not `done`) when this plan is authored; it reaches `done` only once this plan is executed. The item carries `- Blocks-Release: next` and this plan inherits it, so the release gate travels with the work and is discharged by this plan's execution, not by the item's graduation.
