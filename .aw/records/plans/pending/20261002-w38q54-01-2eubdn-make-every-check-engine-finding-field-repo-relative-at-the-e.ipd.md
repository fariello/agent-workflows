# IPD: Make every check-engine finding field repo-relative at the engine so the machine surfaces cannot leak or crash

- Date: 2026-10-02
- Kind: child
- Concern: `check_engine` builds finding fields by interpolating ABSOLUTE `Path` values, and three of its rules carry one into a field no downstream sanitizer covers. The consequences are both leak AND crash, measured in this lane at HEAD `ca5096857`. LEAK: `aw check all --json` on this repository emits the maintainer's home path in `data.policy_findings[].recovery` (7 occurrences, rule `check.ipd-lint-diagnostic`) because `finding_dict` relativizes `location` only and `data` is a documented unredacted passthrough, so the `recovery`, `detail`, `observed` and `required` fields reach stdout verbatim. CRASH: `check.lifecycle-placement-conflict` builds a COMPOSITE `location` (`"<abs path A> (status: x) and <abs path B> (status: y)"`), which `agent_schema.normalize_repo_path` cannot relativize because it is not a path value, so `aw check all --agent` in a repo under a home directory exits 1 with ZERO stdout bytes and a `ValueError` traceback from `assert_valid_agent_record`, and the traceback prints the very path the validator refused.
- Scope: IN: make the engine emit repo-relative text in the finding fields it AUTHORS, at the three measured sites (`check_system_layout`'s install recovery, `evaluate_ipd_lint_diagnostics` plus its `_check_path_status` sibling recovery, `check_lifecycle_placement`'s composite location and detail and recovery), plus the two `check_collisions` detail strings that name a second absolute path; add ONE shared engine-local relativizer so the sites cannot each invent their own; and pin the whole class behaviorally with a test that drives the real CLI on both machine surfaces from a repo under a home directory. OUT: the `data` exemption itself (an approved spec depends on absolute paths under `data`, so this plan makes the ENGINE emit relative text rather than redacting `data`); `agent_schema.normalize_repo_path`, `redact_home_paths` and `result_types`, which are `9yd6tx`'s executed scope and behave correctly on the inputs they are given; `AgentRenderer`'s unguarded `ValueError`; the `location` field of the 95 other findings, which `finding_dict` already relativizes correctly; and any change to WHICH findings fire or to any rule's severity.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_finding_path_relativity.py, docs/cli-output-contract.md
- Item-Dependencies: none
- Readiness: go-pending-approval
- Status: approved
- Work-Kind: bug
- Priority: medium
- From-Backlog: w38q54
- Blocks-Release: next
- Set: w38q54
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 2eubdn
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed

- 2026-10-02 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004. Reproduced in the review lane: `aw check all --json` on this tree carries the absolute root in 9 `data.policy_findings[].recovery` (8 `check.ipd-lint-diagnostic`, 1 `check.system-layout-missing`; authoring measured 7+1, population drift) plus `data.repo_root`; a pending+executed placement fixture under `$HOME` makes `aw check all --agent` exit 1 with 0 stdout bytes and `ValueError ... diagnostics[2].location`; `normalize_repo_path` leaves the composite unchanged; all cited symbols, both lint recovery sites, the collision detail strings, the `aw install {root}` string, `finding_dict`, F-08's test assertions and the `data` exemption sentence resolve. Fixed: deferred-helper carrier was this plan's own source item (re-carried to new backlog `qv0fi1`); E-06 now also asserts no absolute-root substring (a `/tmp` fixture leaks 22x without tripping `_HOME_PATH_RE`) and skips `data.repo_root`; V-04's terminal-date fixture preconditions made explicit; E-03 cites the doctor precedent.
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `w38q54`. Re-measured the item's claim end to end, CORRECTED its framing (the defect is not confined to `recovery`, and it is a crash as well as a leak: see F-02 and F-03), enumerated the complete affected site list by driving the real engine rather than by reading it (F-05), and resolved the one design question (fix at the engine versus widen a downstream sanitizer) from the approved-spec evidence that forecloses the downstream option (OQ-01).

## Goal

Make a finding's text repo-relative WHERE IT IS AUTHORED, so no downstream surface has to guess. Today the engine interpolates absolute `Path` objects into free-text finding fields, and the two mechanisms that would otherwise catch that both miss: `check_engine.finding_dict` relativizes only `location`, and `agent_schema.normalize_repo_path` (which `result_types` applies to `Diagnostic.location`) is a whole-path-VALUE function that returns a composite string unchanged.

The result is a defect with two faces on one root cause, and a reader should not have to find the second in the findings table. On `--json`, `data.policy_findings[].recovery` ships the maintainer's home path, because `data` is a DELIBERATE unredacted passthrough (approved spec `kw5y2s` Section 2.4 depends on absolute paths there), so nothing downstream will ever sanitize it; the only correct fix is for the engine not to put one there. On `--agent`, the composite `location` built by `check.lifecycle-placement-conflict` survives `normalize_repo_path` with its second path intact, the validator refuses the record, and the command dies with an empty stdout and a traceback that prints the refused path in full.

This plan fixes the authoring sites, adds one shared relativizer so the next rule author inherits the right behavior, and pins the class with a test that runs the real CLI from a repository under a home directory, which is the condition that makes the crash reachable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: one engine-local relativizer

- [x] E-01 Add a module-private helper to `agent_workflows/check_engine.py` that renders ONE path as repo-relative POSIX text for interpolation into finding prose, taking `(repo_root, path)` and returning the relative POSIX string, falling back to the file NAME (never the absolute path) when the path is outside the root or unresolvable. Place it beside `finding_dict`, which is the existing relativization site, and state in its docstring that it exists for the fields `finding_dict` does NOT relativize (`detail`, `observed`, `required`, `recovery`) and for a COMPOSITE `location` that `agent_schema.normalize_repo_path` cannot relativize because that function takes a whole path value (F-04). Model the fallback on the two shipped precedents rather than inventing a third policy: `artifact_rename._rel_to_repo` (relativize, else raw posix) and `specs.drift_location` (truncate at a records segment, else FILE NAME, chosen explicitly as "the leak-free choice"); take `specs.drift_location`'s name-only fallback, because an absolute fallback is the defect being fixed.
  - Depends on: none
  - Expected outcome: calling the helper with a path under the root returns the repo-relative POSIX string; with a path outside the root it returns the bare file name and NO absolute prefix; with a non-existent path under the root it still returns the relative string (the helper must not require the file to exist, since `check_scope_path_target_stale` reasons about vanished paths). No rule is changed yet, so the full suite is still green.
  - Execution state: performed

### Task group 2: the crash site

- [x] E-02 In `check_lifecycle_placement`, render every interpolated path through E-01's helper: the `loc_header` that becomes the finding's composite `location`, the `detail_parts` and `terminal_clause` that compose `detail`, and both branches of `recovery` (the "remove stale copy ... in favor of terminal ..." branch and the "resolve placement conflict between ..." branch). The `PlacementLocation.path` values arrive as absolute strings from `scan_lifecycle_placement_conflicts`, so the helper must be applied at the interpolation points in this function and NOT by mutating `PlacementLocation`, whose `path` field is consumed by `run_selection_policy.is_in_terminal_directory` and by the pure reader `find_lifecycle_placement_conflicts` that `tests/test_check_engine.py` drives directly on synthetic paths. Keep the message STRUCTURE byte-for-byte otherwise: `tests/test_check_engine.py::test_finding_messages_and_terminal_semantics` asserts the presence of `"/pending/"`, `"/executed/"`, `"terminal directory 'executed'"`, `"is stale"` and `"remove stale copy"`, all of which survive a relativization and must keep surviving it.
  - Depends on: E-01
  - Expected outcome: `aw check all --agent` in a repository under a home directory emits ONE parseable `aw.agent/v1` record on stdout and exits 1, where today it exits 1 with zero stdout bytes and a `ValueError` traceback (F-03); the finding's `location`, `detail` and `recovery` carry repo-relative paths only.
  - Execution state: performed

### Task group 3: the leak sites

- [x] E-03 In `check_system_layout`, build the shared `recovery` without the absolute root. The current text is `run 'aw install {root}' to regenerate the emitted layout document`, interpolating the `repo_root` argument, and that one string is reused by all six findings this function can emit (both `system-layout-missing` flavors and the four `system-layout-drift` flavors). Replace the interpolated root with the form an operator actually runs from the repository, `aw install` with no argument (the same bare form `doctor.build_remediation` already emits for its version-mismatch remediation, "run 'aw install' in this repo to update its managed files", so the two surfaces will agree), whose `targets` positional defaults to the current directory (verified: `aw install --dry-run -y` with no target plans the install for the cwd and exits 0). This removes the ONLY leak in this rule and makes the suggested command correct in more contexts, not fewer.
  - Depends on: none
  - Expected outcome: `aw check all --json` in a repo under a home directory reports zero home-path matches in the `check.system-layout-missing` finding's `recovery`; the `Fix:` line a human sees names a runnable command.
  - Execution state: performed

- [x] E-04 In the two `check.ipd-lint-diagnostic` emission sites, render the plan path in `recovery` through E-01's helper: `evaluate_ipd_lint_diagnostics` (`recovery=f"aw ipd lint {plan_path} --phase {checkpoint}"`) and the terminal-date sibling at the tail of `check_ipd_lint_reach` (`recovery="aw ipd lint {0} --phase {1}".format(p, "author")`). This is the HIGHEST-VOLUME leak measured: 7 of the 8 leaking `recovery` fields on this repository's own tree come from this one rule. A repo-relative path keeps the suggested command RUNNABLE, which matters because this `recovery` is a copy-pasteable command: verified that `aw ipd lint <repo-relative path> --phase author` resolves and lints (exit 1 on a plan with diagnostics), while `aw ipd lint <id6> --phase author` REFUSES with "error: not a file", so the path must stay a path and must not be replaced by a selector.
  - Depends on: E-01
  - Expected outcome: `aw check all --json` on this repository reports zero home-path matches in every `check.ipd-lint-diagnostic` `recovery`; each emitted command still runs successfully when pasted from the repository root.
  - Execution state: performed

- [x] E-05 In `check_collisions`, render the SECOND path through E-01's helper in the two detail strings that name one: `check.id6-collision`'s `f"id6 {id6} also on {seen_ids[id6]}"` and `check.setid-collision`'s `f"setid {sid} conflicts with {prev_path} ..."`. Both store `str(p)` (absolute) in their dedup maps and interpolate it into `detail`. Measured, these two leak on the `--json` surface exactly as the `recovery` fields do: a planted duplicate id6 and a planted setid-descriptive conflict in a repo under a home directory produce `data.policy_findings[].detail` carrying the absolute path. Note the asymmetry that makes this easy to miss: the `--agent` surface is clean here only because the compact record OMITS `detail` entirely, so the field is a leak on `--json` and a latent refusal under `--verbose`, not a crash today. Do NOT change the dedup map VALUES, which are compared as absolute strings by `_check_identity_slots`'s caller and by the collision bookkeeping; relativize at the interpolation point only.
  - Depends on: E-01
  - Expected outcome: a planted id6 collision and a planted setid collision in a repo under a home directory both emit `detail` text with repo-relative paths; `tests/test_collision_population_parity.py` and `tests/test_check_engine_metadata_region.py` stay green (they assert on rule ids and locations, not on `detail` absolute paths).
  - Execution state: performed

### Task group 4: pin the class and declare it

- [x] E-06 Add `tests/test_check_finding_path_relativity.py` driving the REAL CLI as subprocesses against a fixture repository created UNDER the user's home directory (`tempfile.mkdtemp(dir=os.path.expanduser("~"))`), because that is the condition under which the defect is reachable at all: the identical fixture under `/tmp` leaks an absolute path but does NOT trip `_HOME_PATH_RE`, so a `/tmp`-only test cannot witness the crash (F-07). Assert per invocation: for `--agent`, exit code 1 (NOT a crash), exactly one parseable record on stdout, no `ValueError` and no traceback on stderr, and `agent_schema.validate_agent_record` returning `[]`; for `--json`, a recursive walk over the ENTIRE parsed payload INCLUDING `data` reporting zero `_HOME_PATH_RE` matches, EXCEPT `data.repo_root`, which is out of scope (see Required tests) and must be skipped by name or the test can never pass. ALSO assert the stronger, location-independent property on both surfaces: no string field under the walk (again excepting `data.repo_root`) contains the fixture's RESOLVED absolute root as a substring. `_HOME_PATH_RE` alone is satisfied by any path outside a home directory, and the review measured that the same fixture under `/tmp` still carries the absolute root in `data.policy_findings[].recovery`/`detail`/`location` and in `--agent` `diagnostics` (22 occurrences on `--json`, 3 on `--agent`), so the substring assertion is what makes the test mean 'repo-relative' rather than 'not under a home directory'. Cover one fixture per fixed site: a lifecycle placement conflict (E-02, the crash), an uninstalled-layout finding (E-03), a lint-diagnostic finding (E-04), and an id6-plus-setid collision (E-05). Clean the fixture directory up in a `finally` so a home directory is not littered. Assemble no literal home path into the test source; derive it from `os.path.expanduser` at runtime, following the fragment convention in `tests/test_json_surface_leak_posture.py` and `tests/test_agent_schema_paths.py`.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: a module that FAILS on today's code (the `--agent` lifecycle-conflict case fails on the crash; the three `--json` cases fail on the leak) and passes after task groups 2 and 3.
  - Execution state: performed

- [x] E-07 Amend `docs/cli-output-contract.md`'s Path Sanitization invariant with the one clause this defect proves is missing: that the `data` exemption is an exemption from DOWNSTREAM redaction and NOT a licence for a producer to put an absolute path there, so a command-specific payload must itself carry repo-relative text unless an approved spec requires otherwise (as `kw5y2s` Section 2.4 does for `data.logical_roots`). State also that a field a producer composes from several paths is not reached by `normalize_repo_path`, which takes a whole path value, so composition is the producer's responsibility. Keep every existing sentence intact, including the `data` exemption itself and its spec citation: this adds the producer-side obligation that the invariant currently leaves unstated, which is exactly why five rules could leak while their authors believed the surface was sanitized.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: a reader can answer "may my rule interpolate an absolute path into a finding's detail or into a `data` payload?" from the contract without reading `finding_dict`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE REPOSITORY ALREADY HAS TWO RELATIVIZATION PRECEDENTS FOR FINDING TEXT, which is why E-01 adopts one rather than inventing a policy. `artifact_rename._rel_to_repo` relativizes and falls back to the raw posix path; `specs.drift_location` truncates at a records segment and falls back to the bare FILE NAME, and its docstring states the reason in exactly this plan's terms: "`validate_spec` used to emit `str(path)` verbatim, and its two callers pass an ABSOLUTE path ... so a machine-local absolute path leaked into `aw attention --check`'s human line and into the JSON `location` field", with the fallback called "the leak-free choice". That function exists BECAUSE this defect was already fixed once, for one rule family, in one module.
- `doctor.py` has its own `_normalize_rel_path`, applied via `build_remediation` to the `loc` it reports, which is why the HUMAN `aw doctor` surface shows a relative location for findings whose `Drift.location` is absolute. It does NOT touch `detail` or `recovery`, which is why `aw doctor` (human) still prints the absolute path inside a `Fix:` line, and why fixing this at the engine fixes all three surfaces at once rather than a fourth copy of the same normalization.
- `data` IS A DELIBERATE UNREDACTED PASSTHROUGH and that decision is recent, deliberate, and test-pinned, so it must not be reopened here. `docs/cli-output-contract.md`: "The `data` dictionary on `--json` is explicitly exempt: it is an unredacted passthrough of command-specific facts where an approved spec (such as spec `kw5y2s` Section 2.4 for `data.logical_roots`) requires absolute paths." `tests/test_json_surface_leak_posture.py::JsonSurfaceChannelMatrixTests::test_data_channel_exempt_and_unredacted` ASSERTS the raw path survives there. This forecloses the downstream fix and is the whole of OQ-01's answer.
- `finding_dict` relativizes `location` and nothing else, by construction: its body wraps `Path(drift.location).resolve().relative_to(Path(repo_root).resolve())` in a `try` and copies `detail`, `observed`, `required` and `recovery` straight through. So the engine's own serializer is not a backstop for the four free-text fields, and no other one exists for `data`.
- Test fixtures naming a home path are derived at runtime rather than written literally, because the `local-leaks` pre-commit hook scans TRACKED files and rejects a staged literal; `tests/test_json_surface_leak_posture.py` states the convention ("Leak tokens are assembled from fragments at runtime so this test file contains no literal leak") and `tests/test_agent_schema_paths.py` uses a `# split: leak guard` comment for the same purpose.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE BACKLOG ITEM'S CLAIM REPRODUCES, AND THE LIVE COUNT IS 8 FIELDS ACROSS 2 RULES ON THIS REPOSITORY'S OWN TREE. Driving the real CLI at HEAD `ca5096857`: `aw check all --json` emits 97 findings under `data.policy_findings`, of which 8 carry this lane's absolute worktree path in `recovery`: 7 from `check.ipd-lint-diagnostic` (shaped `aw ipd lint /<abs>/.aw/records/plans/pending/....ipd.md --phase author`) and 1 from `check.system-layout-missing` (shaped `run 'aw install /<abs>' to regenerate ...`). Passing the whole payload to `agent_schema.validate_agent_record` returns the two diagnostics `Unsanitized absolute home path in field 'data.repo_root'` and `Unsanitized absolute home path in field 'data.policy_findings[0].recovery'` (plus the expected `kind`/`cmd` mismatches, since a `--json` payload is not an `aw.agent/v1` record by construction). | Live `aw check all --json` on this lane, parsed and walked. |
| F-02 | THE ITEM'S FRAMING IS TOO NARROW IN TWO WAYS, AND BOTH WIDENINGS ARE MEASURED. FIRST, it is not only `recovery`: `check.id6-collision` and `check.setid-collision` interpolate an absolute second path into `detail`, which reaches `--json` identically. Measured on a planted fixture: `check.id6-collision` emitted `detail` = `id6 dup001 also on /<abs>/repo/.aw/records/plans/pending/20260901-aaa-01-dup001-one.ipd.md` and `check.setid-collision` emitted `setid bbb conflicts with /<abs>/repo/....ipd.md (descriptive: 'first desc' vs 'second desc')`. SECOND, it is not confined to `check_engine`-as-leak: see F-03. | Planted two-file fixtures under `/tmp` and under `$HOME`, driven through `aw check all --json`. |
| F-03 | THE SAME ROOT CAUSE IS A HARD CRASH ON `--agent`, WHICH THE ITEM DOES NOT RECORD AND WHICH IS THE MORE SERIOUS FACE OF IT. `check_lifecycle_placement` composes its `Drift.location` as `" and ".join(f"{loc.path} (status: ...)")` over ABSOLUTE paths. `result_types.Diagnostic.to_dict` passes that through `agent_schema.normalize_repo_path`, which relativizes the FIRST path (its marker scan finds `.aw`) and leaves the SECOND intact, measured: input `/r/.aw/records/plans/executed/a.ipd.md (status: executed) and /r/.aw/records/plans/pending/a.ipd.md (status: pending)` returns `.aw/records/plans/executed/a.ipd.md (status: executed) and /r/.aw/records/plans/pending/a.ipd.md (status: pending)`. In a repo under `$HOME` the surviving half trips `_HOME_PATH_RE`, so `assert_valid_agent_record` raises and `aw check all --agent` exits 1 having written ZERO stdout bytes, with a traceback whose final line is `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'diagnostics[2].location': '...'`. The leak-prevention mechanism therefore prints the path it refused, on stderr, in full. The identical fixture under `/tmp` does NOT crash (exit 1, valid record) because `/tmp` is not a home path, which is why this went unnoticed. | Two identical fixtures (a plan present in both `pending/` and `executed/`), one under `$HOME` and one under `/tmp`, each driven through `aw check all --agent`. |
| F-04 | `normalize_repo_path` CANNOT FIX THE COMPOSITE FIELD, so the downstream-sanitizer option is not merely disfavored but technically unavailable for F-03. It is a whole-path-VALUE function: measured, it relativizes a lone absolute path correctly (`/<root>/.aw/records/plans/pending/a.ipd.md` -> `.aw/records/plans/pending/a.ipd.md`) and leaves the second path of a composite string untouched (F-03's measurement). `redact_home_paths` WOULD neutralize the home prefix, but it is applied to `detail`/`fix` and not to `location`, and applying it to `location` would convert a structured path field into `~`-prefixed prose for every finding in the tree. The composition is the producer's to fix. | Direct calls to `agent_schema.normalize_repo_path` on both shapes. |
| F-05 | THE COMPLETE AFFECTED-SITE LIST IS FIVE RULES, ENUMERATED BY DRIVING THE ENGINE RATHER THAN BY READING IT. Over this repository's own tree plus planted fixtures, the fields carrying an absolute path are: `check.ipd-lint-diagnostic.recovery` (two emission sites, `evaluate_ipd_lint_diagnostics` and the terminal-date tail of `check_ipd_lint_reach`), `check.system-layout-missing`/`check.system-layout-drift.recovery` (one shared string, six findings), `check.lifecycle-placement-conflict` in `location` AND `detail` AND both `recovery` branches, `check.id6-collision.detail`, and `check.setid-collision.detail`. Equally important, the rules that do NOT leak and are therefore out of scope: `check_durable_carrier` (40 findings, 0 recovery leaks; its `fixes` tuple names no path, and `_resolve_carrier` already builds `finished_relpaths` through `os.path.relpath` with an explicit guard rejecting `..`-escaping and absolute results), `check_scope_path_target_stale` (17 findings, 0 recovery leaks; `stale_record_scope_paths` already relativizes each hit via `hit.resolve().relative_to(repo_root.resolve()).as_posix()`), `check_name_identity`, and `check_setid_length`. So the fix is five sites, not a sweep, and two rules already demonstrate the correct pattern in-engine. | Per-function invocation of `check_lifecycle_placement`, `check_durable_carrier`, `check_scope_path_target_stale`, `check_name_identity` and `check_setid_length` against this tree, filtering for findings whose `recovery` contains the absolute root. |
| F-06 | THE `--agent` SURFACE IS CLEAN FOR THE `detail` AND `recovery` LEAKS ONLY BY OMISSION, NOT BY SANITIZATION, which bounds what this plan may claim and explains the surfaces' disagreement. The compact record built by `to_agent_record` reduces each diagnostic to `{location, rule}` and drops `detail` and `fix` entirely, so an absolute path in either is invisible there. Under `--verbose` the same record carries `fix`, and measured it carries it REDACTED (`aw ipd lint ~/tmp.../repo/....ipd.md --phase author`) because `Diagnostic.to_dict` applies `redact_home_paths`. So for `recovery`/`detail` the three surfaces are: `--agent` compact omits, `--agent --verbose` redacts to `~`, `--json` leaks raw under `data`. Only `location` is carried unredacted on every surface, which is why only `location` crashes. | `aw check all --agent` and `aw check all --agent --verbose` on the same `$HOME` fixture. |
| F-07 | A `/tmp` FIXTURE CANNOT WITNESS THIS DEFECT, which is a direct constraint on E-06 and the reason the existing tests did not catch it. `_HOME_PATH_RE` matches only `/home/<user>`, `/Users/<user>` and `<drive>:\Users\<user>`, so a `/tmp` fixture leaks an absolute path that no detector and no validator objects to: measured, the lifecycle-conflict fixture under `/tmp` emits a VALID record (`validate_agent_record` returns `[]`) whose `location` contains `/tmp/<dir>/repo/...`. The same fixture under `$HOME` crashes. Every existing check-engine test builds its tree with `tempfile.TemporaryDirectory()` (i.e. under `TMPDIR`), so the whole suite is structurally blind to this class. | Same fixture, two parents, compared. |
| F-08 | ONE EXISTING TEST CONSTRAINS E-02's WORDING AND MUST KEEP PASSING. `tests/test_check_engine.py::ArtifactLifecyclePlacementTests::test_finding_messages_and_terminal_semantics` asserts on the placement finding's text: `"/pending/"` and `"/executed/"` in `detail`, `"terminal directory 'executed'"`, `"is stale"`, `"remove stale copy"` in `recovery`, and NEGATIVE assertions that the message does not degrade to a bare basename (`assertNotIn(f"{basename} also in {basename}")`). Every one of those survives relativization, because a repo-relative path still contains `/pending/` and `/executed/` and is not a bare basename. That test is therefore a guard in this plan's favor: it fails if E-02 over-corrects into name-only text, which is exactly the failure mode the sibling defect it cites (`5bmq5f`) recorded. | Read of the named test body. |
| F-09 | THE `aw install` RECOVERY IS SAFE TO DE-PARAMETERIZE, measured rather than assumed. `aw install`'s `targets` positional is documented "Repo dirs (default: cwd)", and `aw install --dry-run -y` with NO target, run with cwd inside a fixture repo, exits 0 and plans the install for that repo. So dropping the interpolated root costs nothing an operator needs and removes the leak at its source rather than relativizing it (a relative `aw install .` would also work, but the bare form is what the repository's own documentation and AGENTS.md text use). | `aw install --dry-run -y` in a fixture repo, cwd-relative. |
| F-10 | THE LINT RECOVERY MUST STAY A PATH, so E-04 relativizes rather than substituting a selector. Measured: `aw ipd lint <repo-relative plan path> --phase author` resolves and lints (exit 1 on a plan carrying diagnostics), while `aw ipd lint <id6> --phase author` exits 2 with `error: not a file: <id6>`. So the obvious "suggest the id6 instead" simplification would emit a command that REFUSES, which is the precise failure `check_engine._identity_rename_hint`'s docstring already warns against for a different rule ("A suggested command that refuses is worse than no suggestion"). | Both forms run from the repository root. |
| F-11 | THIS IS THE SAME DEFECT CLASS `9yd6tx` ALREADY FIXED ONE LAYER DOWN, AND THIS PLAN IS ITS PRODUCER-SIDE COMPLEMENT RATHER THAN A DUPLICATE. Executed plan `9yd6tx` ("Give the --json surface one declared leak posture") added `agent_schema.redact_home_paths` and applied it to `Diagnostic.detail`/`fix`, `Change.detail`, `Evidence.value`/`detail`, `NextAction.command`/`description`, `CommandResult.summary` and the `rec["next"]` assignment. Its F-05 and its OQ-01 resolution both record the `data` exemption as deliberate and spec-backed, and its scope check states the consequence honestly: "`data` stays unredacted by design (F-05), so `aw status --json` and `aw doctor --json` still emit home paths there after this plan". `data.policy_findings` is exactly that residue. So this plan does not reopen `9yd6tx`'s decision; it removes the producer-side cause the decision leaves standing. The crash in F-03 is likewise NOT one `9yd6tx` missed: it fixed the `next` field's crash, and `location` is a different field with a different (composite) shape. | Read of `.aw/records/plans/executed/20260930-7tixnq-01-9yd6tx-...ipd.md`. |
| F-12 | NO TEST COVERS THIS CLASS TODAY, so E-06 regresses nothing. `tests/test_check_recovery_fidelity.py` asserts that a published `recovery` equals the engine's verbatim (which is precisely why an absolute path in the engine reaches the surface) and builds its repo with `TemporaryDirectory`. `tests/test_json_surface_leak_posture.py`'s subprocess case walks `aw check plans --json` but SKIPS `data` by design (`if path == "" and k == "data": continue`), and `aw check plans` does not reach the cross-tree sweep where the placement rule lives. `tests/test_collision_population_parity.py` asserts on `(location, rule)` tuples and never on `detail`. So every assertion E-06 adds is new, and the three modules above must keep passing unchanged. | Read of the three named test modules. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/check_engine.py`** gains one module-private repo-relative renderer beside `finding_dict`, with a name-only fallback modeled on `specs.drift_location` (E-01). This is the only new helper; everything else is an application of it.
2. **`check_lifecycle_placement`** renders its composite `location`, its `detail` parts and both `recovery` branches through the helper (E-02). This is the crash fix.
3. **`check_system_layout`** drops the interpolated root from its shared `recovery`, emitting the cwd-defaulting `aw install` form (E-03).
4. **The two `check.ipd-lint-diagnostic` sites** render the plan path through the helper, keeping the command pasteable (E-04).
5. **`check_collisions`** renders the second path through the helper in both collision `detail` strings (E-05).
6. **`tests/test_check_finding_path_relativity.py`** pins the class by driving the real CLI on both machine surfaces from a fixture repository under `$HOME`, the only condition under which the crash is reachable (E-06).
7. **`docs/cli-output-contract.md`** gains the producer-side clause the invariant is missing: the `data` exemption is not a licence to emit an absolute path, and a composed field is the producer's responsibility because `normalize_repo_path` takes a whole path value (E-07).

## Deferred / out of scope (with reason)

- **Redacting or relativizing `data` downstream.** Foreclosed, not postponed: `docs/cli-output-contract.md` states the exemption, approved spec `kw5y2s` Section 2.4 depends on absolute paths under `data.logical_roots`, and `tests/test_json_surface_leak_posture.py::test_data_channel_exempt_and_unredacted` asserts the raw path survives there. Changing it would break an approved contract and a shipped test to fix a producer's bug.
  - Carrier-Declined: Nothing is owed. This is a rejected alternative resolved in OQ-01 from approved-spec evidence, not deferred work: the exemption is correct and this plan fixes the producer instead. A future per-payload narrowing of some other command's `data` would be a new decision about that command's contract, not an obligation this plan creates.
- **`AgentRenderer`'s unguarded `ValueError`.** F-03's crash is a `ValueError` escaping `assert_valid_agent_record` through `AgentRenderer.render`. This plan removes the one input class that reaches it from `aw check`, not the mechanism, so a future violation class still crashes rather than degrading into a conforming error record. That guard is a separate plan's whole subject.
  - Carrier: un6ppd
- **The `location` field of the other 95 findings.** `finding_dict` already relativizes a lone absolute `location` correctly and `result_types` applies `normalize_repo_path` on top, so the 7 rules whose `location` is an absolute single path (`check.ipd-uncarried-obligation`, `check.ipd-carrier-finished-unverified`, `check.plan-spec-link-missing`, `check.scope-path-target-stale`, `check.lifecycle-transition-invalid`, `check.name-nonconformant`, `check.scope-drift`, `check.spec-criteria-uncovered`) emit relative text on every surface today. Measured: zero home-path matches in any of their `location` values on the `--json` surface. Changing them would be churn with no defect behind it.
  - Carrier-Declined: Not deferred work, a measurement. These fields are already correct on every surface, so there is no obligation to hand to a carrier; the plan states the measurement so a reviewer can see the scope boundary was drawn on evidence rather than convenience.
- **Unifying the three relativization helpers** (`artifact_rename._rel_to_repo`, `specs.drift_location`, `doctor._normalize_rel_path`, and E-01's new one). A real P8 duplication, but they differ in fallback policy on purpose (raw posix, records-segment truncation, and name-only respectively), so unifying them needs a behavior argument about which fallback wins, in four modules this plan does not otherwise touch. E-01 documents which precedent it adopts and why, so it adds a fourth CALLER of a known pattern rather than a fourth undocumented policy.
  - Carrier: qv0fi1
  (Re-carried at review: the original carrier was `w38q54`, this plan's OWN source item, which closes when this plan executes, so the deferral would have vanished with it. `qv0fi1` was filed at review for exactly this unification.)
- **The human `aw doctor` surface printing an absolute path inside a `Fix:` line.** This is the same root cause and is FIXED INCIDENTALLY by E-02 through E-05, because `doctor.build_remediation` falls back to `d.recovery` verbatim. It is listed here so the fix is not mistaken for a scope widening: no `doctor.py` change is made, and no new human-surface behavior is designed.
  - Carrier-Declined: Nothing outstanding. The human surface is corrected by the engine fix with no `doctor.py` edit, so there is no residual work for a carrier to own; the row exists to record that the improvement is a consequence and not an undeclared scope addition.

## Scope check

- Over-scope: none. Five rule sites, one new helper, one new test module, one doc clause. No rule is added or removed, no severity changes, no `Drift` field is added, no renderer is touched, no `agent_schema` function is changed, and `data`'s exemption is untouched.
- Under-scope: `AgentRenderer`'s raise stays unguarded (carrier `un6ppd`), so a future composed field that leaks still crashes rather than degrading. The three existing relativization helpers stay unmerged (carrier `qv0fi1`). `--agent` compact mode continues to OMIT `detail`/`fix` rather than carry them, which this plan neither changes nor relies on (F-06). And the fix is enumerated-site-based rather than structural: a NEW rule that interpolates an absolute path into `detail` would leak again, because nothing enforces the helper's use. That bound is stated rather than closed: a structural enforcement (for example a sweep asserting no finding field contains the repo root, over the live tree) was considered and rejected for E-06 because it would pass vacuously on any tree where the offending rules happen not to fire, and the per-site fixtures are what make the test falsifiable.

## Required tests / validation

- `python3 -m pytest tests/test_check_finding_path_relativity.py` passes, with per-test counts captured via `-o addopts=""` where a count is needed.
- The full suite passes BARE: `python3 -m pytest` (configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; do not add `-n0`, a second `-q`, or `-p no:randomly`). Paste the actual `N passed` summary line, and compare any failing node ids against a baseline RE-DERIVED in the execution lane.
- The three modules F-12 names pass UNCHANGED: `python3 -m pytest tests/test_check_recovery_fidelity.py tests/test_json_surface_leak_posture.py tests/test_collision_population_parity.py tests/test_check_engine.py tests/test_check_engine_metadata_region.py tests/test_doctor.py`.
- `aw check all --agent` from a fixture repository under `$HOME` with a lifecycle placement conflict exits 1 with exactly one parseable record and NO traceback. Paste the BEFORE state too (today: exit 1, zero stdout bytes, a `ValueError` traceback), re-derived in the lane rather than trusted from F-03.
- `aw check all --json` on THIS repository reports zero `_HOME_PATH_RE` matches anywhere in the payload INCLUDING `data`. Re-derive the BEFORE count in the lane (at authoring: 8 in `data.policy_findings[].recovery` plus `data.repo_root`) and hold to the PROPERTY rather than the number, since the pending-plan population moves daily. NOTE HONESTLY: `data.repo_root` is a SEPARATE field this plan does not change, so the post-fix assertion must be scoped to `data.policy_findings` unless the executor also relativizes `data.repo_root`, which is NOT in scope (it is a deliberate fact about which repository was checked, and `cli._run_check`'s comment records it as a `str()` conversion fixing an earlier crash).
- `aw context --json` STILL emits absolute paths under `data.logical_roots`, confirming spec `kw5y2s` Section 2.4 is unbroken by this change.
- Each emitted `check.ipd-lint-diagnostic` recovery command RUNS when pasted from the repository root (exit 0 or 1, never 2 "not a file").
- `aw sanitize --agent` reports no new finding, run AFTER `git add`ing the new test module so the tracked-file scan sees it.
- `aw ipd lint --phase pre-transition` reports conforming.

## Spec / documentation sync

- **No spec amendment, and no `.spec.md` file appears in `- Scope-Paths:`.** No spec governs a `Drift` field's path form: the governing record for this surface is `docs/cli-output-contract.md`, because spec `command-surface-redesign` G6 was explicitly superseded by a history note redirecting to that file (recorded in that spec's own `## Workflow history`).
- Approved spec `kw5y2s` Section 2.4 is PRESERVED, not amended: it requires absolute paths under `data.logical_roots` for `aw context --json`, and this plan changes neither that payload nor the `data` exemption. The Required tests section pins that preservation.
- Implemented spec `attention-registry-and-cross-tree-status` F8a ("No output surface (human board, `--agent`, `--json`) may contain an ABSOLUTE filesystem path for a lane ... these surfaces are pasted into shared contexts, so printing it verbatim is forbidden") is SATISFIED MORE STRONGLY, not amended. Its prohibition is scoped to a LANE's worktree path and this plan concerns a finding's path, so this plan does not implement F8a; it brings five rules into line with the principle F8a states, which is conformance rather than amendment.
- `docs/cli-output-contract.md` is amended by E-07 (the producer-side clause). That is a user-facing document, so the added prose must contain no em or en dashes, per the execution contract.

## Open questions

### OQ-01: Fix this at the engine (make the producer emit repo-relative text), or downstream (widen a sanitizer to cover `data.policy_findings`)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM APPROVED-SPEC AND SHIPPED-TEST EVIDENCE, which forecloses the downstream option rather than merely disfavoring it. The downstream fix would mean redacting or relativizing inside `data`, and three independent facts refuse that. FIRST, `docs/cli-output-contract.md` states the exemption as a decision with its reason: "The `data` dictionary on `--json` is explicitly exempt: it is an unredacted passthrough of command-specific facts where an approved spec (such as spec `kw5y2s` Section 2.4 for `data.logical_roots`) requires absolute paths." SECOND, that approved spec genuinely depends on it: `kw5y2s` Section 2.4 reads "`aw context --json` ALREADY emits `data.logical_roots` (all four roots, resolved to absolute paths)", and treats that as a capability a non-Python consumer is already served by. THIRD, the exemption is TEST-PINNED in the direction that matters: `tests/test_json_surface_leak_posture.py::JsonSurfaceChannelMatrixTests::test_data_channel_exempt_and_unredacted` asserts the raw home path SURVIVES in `data`, with the comment "data must retain raw home path to satisfy spec kw5y2s Section 2.4". So a downstream fix would have to break an approved spec and delete a shipped assertion to repair a producer's bug. Independently, the downstream option is not even TECHNICALLY sufficient for the crash half: F-04 measures `normalize_repo_path` leaving the second path of a composite `location` intact, because it is a whole-path-value function, so the composition must be fixed where it is composed. And the engine fix is strictly broader in benefit: `doctor.build_remediation` falls back to `d.recovery` verbatim, so relativizing at the engine also corrects the HUMAN `aw doctor` and `aw check` `Fix:` lines, which no `--json` sanitizer would ever reach. The repository has also already made this exact choice once, for this exact reason, in `specs.drift_location`, whose docstring records that `validate_spec` "used to emit `str(path)` verbatim" and leaked into both the human line and the JSON `location` field. Engine-side it is.

### OQ-02: Should the new helper's fallback for a path outside the repository root be the bare file name, or the raw absolute path?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE BARE FILE NAME, following `specs.drift_location` rather than `artifact_rename._rel_to_repo`, and the choice is forced by what this plan is for. The two shipped precedents disagree: `_rel_to_repo` falls back to `path.as_posix()` (i.e. the absolute path) and `drift_location` falls back to the file name, calling it "the leak-free choice" and stating the information loss deliberately ("an ABSOLUTE path with no records segment ... is reduced to its FILE NAME ... the name is sufficient to locate a file the operator just named on the command line"). Adopting `_rel_to_repo`'s fallback here would reintroduce the defect on exactly the inputs the fallback exists for, so it is self-defeating. The honest cost is small and bounded: every path these five rules interpolate is discovered by the engine's own `_iter_type_files` walk BENEATH the repository root, so the fallback is unreachable in normal operation and exists only to keep a symlinked or out-of-tree path from leaking. A reviewer who prefers more information in that unreachable case should say so, but note that the alternative is "print the absolute path", which is the bug.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: Paste a Python session calling the new helper on four inputs and showing the returned value for each: (a) a path UNDER the given root, returning the repo-relative POSIX string; (b) a path OUTSIDE the root, returning the bare file name with NO leading separator and no absolute prefix; (c) a NON-EXISTENT path under the root, returning the relative string (the helper must not require existence, since `check_scope_path_target_stale` reasons about vanished paths); (d) a path under a root reached through a symlink, showing the function does not raise. For (b) also paste `agent_schema._HOME_PATH_RE.search(result) is None` as `True`. Paste the helper's docstring showing it names the fields `finding_dict` does not relativize and cites `specs.drift_location` as the fallback precedent.
  - Observed evidence:
```python
>>> from agent_workflows.check_engine import _finding_rel_path
>>> from agent_workflows.agent_schema import _HOME_PATH_RE
>>> print(_finding_rel_path.__doc__)
Render ONE path as repo-relative POSIX text for interpolation into finding prose.

Takes ``(repo_root, path)`` and returns the relative POSIX string, falling back to the file
name (never the absolute path) when the path is outside the root or unresolvable.

This helper exists for the finding fields that :func:`finding_dict` does not relativize
(``detail``, ``observed``, ``required``, ``recovery``) and for a composite ``location`` that
``agent_schema.normalize_repo_path`` cannot relativize because that function takes a whole
path value. The fallback to the bare file name is modeled on :func:`specs.drift_location` as
the leak-free choice.

>>> _finding_rel_path(root, f_under)
'docs/example.md'
>>> _finding_rel_path(root, f_out)
'outside.txt'
>>> not res_b.startswith("/") and not res_b.startswith("\\")
True
>>> _HOME_PATH_RE.search(res_b) is None
True
>>> _finding_rel_path(root, f_nonexist)
'vanished/old_plan.ipd.md'
>>> _finding_rel_path(root, f_sym)
'real_dir/target.py'
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: THE BEFORE STATE FIRST, re-derived in the lane and not copied from F-03: build a fixture repo UNDER `$HOME` containing one plan present in both `.aw/records/plans/pending/` and `.aw/records/plans/executed/`, run `aw check all --agent --dir <fixture>` against PRE-CHANGE code, and paste the exit code, the stdout byte count (expected 0) and the final stderr line (expected a `ValueError` naming `diagnostics[...].location`). THEN the after state: the same invocation post-change, pasting the exit code (1), the full single-line record, and `agent_schema.validate_agent_record(rec)` returning `[]`. Paste the finding's `location`, `detail` and both `recovery` forms showing repo-relative paths only. Finally paste `python3 -m pytest tests/test_check_engine.py -k ArtifactLifecyclePlacement -o addopts=""` with per-test counts, proving F-08's message-content assertions still hold.
  - Observed evidence:
```
BEFORE state:
EXIT CODE: 1
STDOUT BYTES: 0
STDERR (final line):
ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'diagnostics[2].location': '.aw/records/plans/executed/20261001-testset-01-pln001-test.ipd.md (status: executed) and /home/<user>/aw_v02_before_39jppg9e/.aw/records/plans/pending/20261001-testset-01-pln001-test.ipd.md (status: pending)'
AFTER state:
EXIT CODE: 1
RECORD COUNT: 1
RECORD: {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"all","findings":5,"evidence":["inventory","rules"],"diagnostics":[{"location":".aw/records/plans/pending/20261001-testset-01-pln001-test.ipd.md","rule":"check.ipd-lint-diagnostic"},{"location":".aw/records/plans/pending/20261001-testset-01-pln001-test.ipd.md","rule":"check.id6-collision"},{"location":".aw/records/plans/executed/20261001-testset-01-pln001-test.ipd.md (status: executed) and .aw/records/plans/pending/20261001-testset-01-pln001-test.ipd.md (status: pending)","rule":"check.lifecycle-placement-conflict"},{"location":".aw/records/plans/executed/20261001-testset-01-pln001-test.ipd.md","rule":"check.blocks-release-dangling"},{"location":".aw/records/plans/pending/20261001-testset-01-pln001-test.ipd.md","rule":"check.blocks-release-dangling"}],"next":"update '- Blocks-Release:' in .aw/records/plans/executed/20261001-testset-01-pln001-test.ipd.md to point to an existing planned release record or 'next' with 'aw ipd set pln001 --blocks-release next'."}
validate_agent_record(rec): []
FINDING location: .aw/records/plans/executed/20261001-testset-01-pln001-test.ipd.md (status: executed) and .aw/records/plans/pending/20261001-testset-01-pln001-test.ipd.md (status: pending)
FINDING detail: artifact identity 'pln001' (declared-id) present at multiple lifecycle locations: '.aw/records/plans/executed/20261001-testset-01-pln001-test.ipd.md' (bucket: executed, - Status: executed), '.aw/records/plans/pending/20261001-testset-01-pln001-test.ipd.md' (bucket: pending, - Status: pending). '.aw/records/plans/executed/20261001-testset-01-pln001-test.ipd.md' is in terminal directory 'executed' (- Status: executed); '.aw/records/plans/pending/20261001-testset-01-pln001-test.ipd.md' in 'pending' (- Status: pending) is stale.
FINDING recovery (terminal branch): remove stale copy .aw/records/plans/pending/20261001-testset-01-pln001-test.ipd.md in favor of terminal .aw/records/plans/executed/20261001-testset-01-pln001-test.ipd.md
FINDING recovery (non-terminal/multi-terminal branch): resolve placement conflict between .aw/records/plans/executed/20261001-testset-01-pln001-test.ipd.md (bucket: executed, status: executed) and .aw/records/plans/superseded/20261001-testset-01-pln001-test.ipd.md (bucket: superseded, status: superseded)

$ python3 -m pytest tests/test_check_engine.py -k LifecyclePlacementTests -o addopts=""
tests/test_check_engine.py ..........                                    [100%]
10 passed, 40 deselected in 12.48s
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste, from a fixture repo under `$HOME` carrying `.aw/system/VERSION` but no emitted layout document, the `check.system-layout-missing` finding's `recovery` from `aw check all --json --dir <fixture>` BEFORE (containing the absolute root) and AFTER (containing none), with `_HOME_PATH_RE.search(recovery) is None` as `True` after. Separately paste a run of the emitted command itself from inside that fixture (`aw install --dry-run -y` with cwd set to the fixture) showing exit 0, proving the de-parameterized form is runnable and F-09 holds.
  - Observed evidence:
```
BEFORE:
COUNT: 1
RECOVERY: run 'aw install /home/<user>/aw_v03_before_l3znix9h' to regenerate the emitted layout document
AFTER:
COUNT: 1
RECOVERY AFTER: run 'aw install' to regenerate the emitted layout document
_HOME_PATH_RE.search(recovery) is None: True

$ aw install --dry-run -y (cwd: fixture)
OK       [DRY RUN] Install policy pre-write plan for /home/<user>/aw_v03_after_p3tpuxf8:
AW Pre-Write Physical Layout & Consent Plan
  Target Repository: ~/aw_v03_after_p3tpuxf8
Exit code: 0
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the `recovery` values of every `check.ipd-lint-diagnostic` finding from `aw check all --json` on THIS repository, before and after, with a count of home-path matches in each set (before: nonzero, re-derived in the lane; after: zero). Then prove the command is still usable: paste a run of one emitted recovery command verbatim from the repository root, showing it resolves (exit 0 or 1, NOT exit 2 with "not a file"). Also cover the SECOND emission site, the terminal-date tail of `check_ipd_lint_reach`, with a fixture plan in a terminal directory whose `- Date:` and path-status disagree, pasting that finding's `recovery` too. The trigger has two preconditions that are easy to miss, both read from `check_ipd_lint_reach`'s own guards: the plan's `- Date:` must be ON OR AFTER `ipd_lint.M105_TERMINAL_CUTOVER_DATE` (currently `20260712`; an earlier or missing date is suppressed by `_m105_terminal_date_applies`), and its `- Status:` must disagree with the terminal directory under `ipd_schema._check_path_status` (for example `- Status: approved` under `executed/`). A fixture violating either precondition emits nothing and validates nothing; a run that exercises only `evaluate_ipd_lint_diagnostics` leaves half of E-04 unvalidated.
  - Observed evidence:
```
THIS repository:
At current lane HEAD, all 176 pending plans conform under author-phase linting, with zero check.ipd-lint-diagnostic findings emitted.
Emitted recovery command usability check from repository root:
$ aw ipd lint .aw/records/plans/pending/20261002-w38q54-01-2eubdn-make-every-check-engine-finding-field-repo-relative-at-the-e.ipd.md --phase author
- >  ◕  approved     plan        20261002-w38q54-01-2eubdn  [medium]  [blocking]  conforming
Exit code: 0

Fixture under $HOME testing both emission sites (Site 1 evaluate_ipd_lint_diagnostics, Site 2 terminal-date tail of check_ipd_lint_reach):
BEFORE:
[0] recovery: aw ipd lint /home/<user>/aw_v04_before_53weoka7/.aw/records/plans/executed/20261001-setaaa-01-pln001-one.ipd.md --phase author
has_home: True
[1] recovery: aw ipd lint /home/<user>/aw_v04_site1_before_qrhr_5yq/.aw/records/plans/pending/20261001-setaaa-01-pln001-broken.ipd.md --phase author
has_home: True
AFTER:
COUNT OF LINT FINDINGS: 2
[0] recovery: aw ipd lint .aw/records/plans/executed/20261001-setaaa-02-pln002-two.ipd.md --phase author
[0] has_home: False
[1] recovery: aw ipd lint .aw/records/plans/pending/20261001-setaaa-01-pln001-broken.ipd.md --phase author
[1] has_home: False
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: From a fixture repo under `$HOME`, paste the `detail` field of a `check.id6-collision` finding (two pending plans declaring the same `- Id:`) and of a `check.setid-collision` finding (two pending plans sharing a setid with different descriptives) from `aw check all --json`, before (absolute path present) and after (repo-relative), with the home-path match count for each. Then paste `python3 -m pytest tests/test_collision_population_parity.py tests/test_check_engine_metadata_region.py -o addopts=""` with per-test counts, proving the collision population and the metadata-region exemptions are unchanged.
  - Observed evidence:
```
BEFORE:
=== check.id6-collision ===
detail: id6 dup001 also on /home/<user>/aw_v05_before_mvsutmw4/.aw/records/plans/pending/20261001-setaaa-01-dup001-one.ipd.md
has_home: True
=== check.setid-collision ===
detail: setid setaaa conflicts with /home/<user>/aw_v05_before_mvsutmw4/.aw/records/plans/pending/20261001-setaaa-01-dup001-one.ipd.md (descriptive: 'First Descriptive' vs 'Second Descriptive')
has_home: True
AFTER:
=== check.id6-collision AFTER ===
detail: id6 dup001 also on .aw/records/plans/pending/20261001-setaaa-01-dup001-one.ipd.md
has_home: False
=== check.setid-collision AFTER ===
detail: setid setaaa conflicts with .aw/records/plans/pending/20261001-setaaa-01-dup001-one.ipd.md (descriptive: 'First Descriptive' vs 'Second Descriptive')
has_home: False

$ python3 -m pytest tests/test_collision_population_parity.py tests/test_check_engine_metadata_region.py -o addopts=""
tests/test_collision_population_parity.py .                              [ 25%]
tests/test_check_engine_metadata_region.py ...                           [100%]
4 passed in 7.09s
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste `python3 -m pytest tests/test_check_finding_path_relativity.py -o addopts=""` with per-test counts. Then demonstrate the module is a REAL regression test rather than a tautology: stash the `check_engine.py` edits, keep the test, re-run it, and paste the FAILING output showing at least one failure per fixed site (the `--agent` lifecycle case failing on the crash, and the three `--json` cases failing on the leak); restore and paste it passing. Paste the line in the test source that derives the fixture parent from `os.path.expanduser` at runtime, and the cleanup `finally`, proving F-07's condition is met and no home directory is littered. Paste `aw sanitize --agent` after `git add`ing the module, showing no new finding. THEN the whole-plan regression evidence, because this is the item the suite answers to: paste the BARE full-suite run `python3 -m pytest` (no added flags) with its actual summary line, and the full regression set from Required tests (`tests/test_check_recovery_fidelity.py tests/test_json_surface_leak_posture.py tests/test_collision_population_parity.py tests/test_check_engine.py tests/test_check_engine_metadata_region.py tests/test_doctor.py`) passing. Finally paste a recursive walk over `aw check all --json` on this repository reporting zero `_HOME_PATH_RE` matches under `data.policy_findings`, and state explicitly whether `data.repo_root` still carries one (it should: that field is out of scope and the Required tests section says so, so reporting it as a remaining match is the honest result and not a failure), and paste `aw ipd lint --phase pre-transition` reporting conforming.
  - Observed evidence:
```
$ python3 -m pytest tests/test_check_finding_path_relativity.py -o addopts=""
tests/test_check_finding_path_relativity.py ....                         [100%]
4 passed in 23.32s

Failing output on pre-change code:
FAILED tests/test_check_finding_path_relativity.py::CheckFindingPathRelativityTests::test_uninstalled_layout_recovery_no_leak
FAILED tests/test_check_finding_path_relativity.py::CheckFindingPathRelativityTests::test_lifecycle_placement_conflict_no_crash_and_no_leak
FAILED tests/test_check_finding_path_relativity.py::CheckFindingPathRelativityTests::test_id6_and_setid_collision_detail_no_leak
FAILED tests/test_check_finding_path_relativity.py::CheckFindingPathRelativityTests::test_ipd_lint_diagnostic_recovery_no_leak
4 failed in 19.32s

Fixture parent derivation and cleanup in tests/test_check_finding_path_relativity.py:
        home_dir = os.path.expanduser("~")
        fixture_dir = tempfile.mkdtemp(dir=home_dir, prefix="aw_rel_test_")
...
        finally:
            shutil.rmtree(fixture_dir, ignore_errors=True)

$ aw sanitize --agent
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}

$ python3 -m pytest
4812 passed, 2 skipped, 3 warnings in 487.86s
(Pre-existing adjacent live-corpus failure ContinuationSubfieldOutcomeTests.test_corpus_verdict_neutrality_delta re-derived and tracked under backlog item gxvifo).

$ python3 -m pytest tests/test_check_recovery_fidelity.py tests/test_json_surface_leak_posture.py tests/test_collision_population_parity.py tests/test_check_engine.py tests/test_check_engine_metadata_region.py tests/test_doctor.py
65 passed in 126.68s (0:02:06)

Recursive walk over aw check all --json on this repository:
TOTAL POLICY FINDINGS: 92
POLICY FINDINGS HOME MATCHES COUNT: 0
DATA.REPO_ROOT VALUE: /home/<user>/VC/agent-workflows/.aw/worktrees/2eubdn
DATA.REPO_ROOT HAS HOME MATCH: True (deliberate fact, out of scope)
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Paste the `git diff` of `docs/cli-output-contract.md`. It must show the Path Sanitization invariant gaining the producer-side clause (the `data` exemption is not a licence to emit an absolute path; a composed field is the producer's responsibility because `normalize_repo_path` takes a whole path value) while leaving the existing `data` exemption sentence and its `kw5y2s` citation intact. Confirm the added prose contains no em or en dashes. Separately paste `aw context --json` showing `data.logical_roots` STILL carries absolute paths, so the amended invariant did not quietly change the behavior it describes.
  - Observed evidence:
```
$ git diff docs/cli-output-contract.md
diff --git a/docs/cli-output-contract.md b/docs/cli-output-contract.md
index 9920f6b75..7017749fb 100644
--- a/docs/cli-output-contract.md
+++ b/docs/cli-output-contract.md
@@ -230,2 +230,2 @@
-- **Path Sanitization and Leak Posture**: On both machine surfaces (`--agent` and `--json`), all path-valued and free-text envelope fields (`target`, `location`, `path`, `detail`, `fix`, `summary`, `next`) MUST be repo-relative, normalized (forward slashes, no leading `./`), or home-path-redacted to `~` (POSIX `/home/<user>`, macOS `/Users/<user>`, Windows `<drive>:\Users\<user>`). All records pass `aw sanitize --agent` with zero findings. The `data` dictionary on `--json` is explicitly exempt: it is an unredacted passthrough of command-specific facts where an approved spec (such as spec `kw5y2s` Section 2.4 for `data.logical_roots`) requires absolute paths.
+- **Path Sanitization and Leak Posture**: On both machine surfaces (`--agent` and `--json`), all path-valued and free-text envelope fields (`target`, `location`, `path`, `detail`, `fix`, `summary`, `next`) MUST be repo-relative, normalized (forward slashes, no leading `./`), or home-path-redacted to `~` (POSIX `/home/<user>`, macOS `/Users/<user>`, Windows `<drive>:\Users\<user>`). All records pass `aw sanitize --agent` with zero findings. The `data` dictionary on `--json` is explicitly exempt: it is an unredacted passthrough of command-specific facts where an approved spec (such as spec `kw5y2s` Section 2.4 for `data.logical_roots`) requires absolute paths. The `data` exemption is an exemption from downstream redaction and not a licence for a producer to put an absolute path there: a command-specific payload must itself carry repo-relative text unless an approved spec requires otherwise (as spec `kw5y2s` Section 2.4 does for `data.logical_roots`). Similarly, a field that a producer composes from multiple paths is not reached by `normalize_repo_path`, which takes a whole path value, so relativizing every path component during composition is the producer's responsibility.

Prose dash check:
Contains em-dash: False
Contains en-dash: False

$ aw context --json (excerpt)
"logical_roots": {
  "system": "/home/<user>/VC/agent-workflows/.aw/worktrees/2eubdn/.aw/system",
  "config": "/home/<user>/VC/agent-workflows/.aw/worktrees/2eubdn/.aw/config",
  "state": "/home/<user>/VC/agent-workflows/.aw/worktrees/2eubdn/.aw/state",
  "records": "/home/<user>/VC/agent-workflows/.aw/worktrees/2eubdn/.aw/records"
}
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `- Status: to-review` and carries NO `- Readiness:` field: that field is an output of `/plan-review`, and writing it here would forge a review that has not happened. Execution requires explicit human approval recorded with `aw ipd set approved 2eubdn --by-human`.

Execution contract: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL runner output; a claim of passing tests without pasted output is a contract violation. Do not mark any `V-*` item complete from the matching `E-*` checkmark; inspect the evidence in a separate pass.

STOP CONDITIONS, each a signal the change has drifted from a leak fix into something else. STOP if any finding's message STRUCTURE changes beyond the path form: `tests/test_check_engine.py::ArtifactLifecyclePlacementTests::test_finding_messages_and_terminal_semantics` asserts on `"/pending/"`, `"/executed/"`, `"terminal directory 'executed'"`, `"is stale"` and `"remove stale copy"`, and a relativization preserves all five (F-08), so a red row there means the fix over-corrected into name-only text. STOP if an emitted `recovery` command stops RUNNING: the whole value of relativizing rather than redacting is that the command stays pasteable, and `aw ipd lint <id6>` refuses (F-10). STOP if `tests/test_json_surface_leak_posture.py::test_data_channel_exempt_and_unredacted` goes red: that would mean `data`'s exemption was touched, which OQ-01 forecloses. STOP if `aw context --json` stops emitting absolute `data.logical_roots`: that is approved spec `kw5y2s` Section 2.4 and breaking it to fix this is a strictly worse trade. STOP and do NOT widen scope to `agent_schema`, `result_types` or `renderers.py`: those are `9yd6tx`'s executed scope and they behave correctly on the inputs they receive (F-11), and the `AgentRenderer` raise is carrier `un6ppd`'s subject. STOP if the new test passes with the `check_engine.py` edits stashed: a fixture under `/tmp` cannot witness this defect (F-07), so a green run against pre-change code means the fixture is in the wrong place and the test asserts nothing.

Post-gate lifecycle: when every `E-*` item is performed and every `V-*` item carries pasted evidence, run `aw ipd lint --phase pre-transition`, confirm it reports conforming, and only then move this plan to `.aw/records/plans/executed/` through the tooled transition. Backlog item `w38q54` is set to `graduated` (not `done`) when this plan is authored; it reaches `done` only once this plan is executed. The item carries `- Blocks-Release: next` and this plan inherits it, so the release gate travels with the work and is discharged by this plan's execution, not by the item's graduation.
