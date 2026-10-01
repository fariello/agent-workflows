# IPD: Give the --json surface one declared leak posture and sanitize the fields that carry a home path

- Date: 2026-09-30
- Kind: child
- Concern: The `--json` machine surface has no declared leak posture: it sanitizes two fields, leaks seven, and no document says which it promises.
- Scope: Declare `--json`'s leak posture in the output contract, add ONE home-path redaction primitive to `agent_schema` shared by both machine surfaces, apply it to the `CommandResult.to_dict` free-text fields that measurably leak, and pin the whole matrix with behavioral tests. Does NOT touch `data`, does NOT make `--json` validate against `aw.agent/v1`, and does NOT touch `AgentRenderer` or `HumanRenderer`.
- Scope-Paths: agent_workflows/agent_schema.py, agent_workflows/result_types.py, docs/cli-output-contract.md, docs/cli-agent-protocol.md, tests/test_json_surface_leak_posture.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: 7tixnq
- Set: 7tixnq
- Order: 1
- Highest E allocated: 06
- Author: opencode
- Id: 9yd6tx

## Workflow history

- 2026-09-30 draft (opencode): created.
- 2026-09-30 to-review (opencode): authored from backlog `7tixnq`. Measured the leak matrix on both machine surfaces, resolved the posture question the carrier raised from in-repo spec and docs evidence (see OQ-01), and settled scope on the three fields that leak through a free-text channel.

## Goal

Make `--json` carry ONE stated leak posture instead of an accidental one. Today `CommandResult.to_dict` normalizes `diagnostics[].location` and `changes[].path` but passes `diagnostics[].fix`, `diagnostics[].detail`, `changes[].detail`, `evidence[].value`, `evidence[].detail`, `next_actions[].command`, and `summary` through verbatim, so the surface is neither "sanitized" nor "raw" and no document says which it promises. This plan redacts the home-path prefix out of the free-text fields that measurably leak, leaves `data` deliberately raw under a stated exemption, and writes the resulting posture into the output contract so the next reader does not have to re-measure it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one shared redaction primitive

- [ ] E-01 Add a `redact_home_paths(text)` function to `agent_workflows/agent_schema.py` that rewrites every home-style absolute path prefix inside a string to `~`, preserving the tail, and returns non-string input unchanged. Cover all three classes `_HOME_PATH_RE` detects (POSIX `/home/<user>`, macOS `/Users/<user>`, and the Windows `<drive>:\Users\<user>` form), using prefix patterns WITHOUT the placeholder negative lookaheads so a already-placeholder value is left alone by virtue of not matching a real username. Place it beside `normalize_repo_path` and state in the docstring that it REDACTS (a lossy, idempotent rewrite) rather than relativizing, and that it is the counterpart `normalize_repo_path` cannot serve because it operates on a whole path value and not on a path embedded in free text.
  - Depends on: none
  - Expected outcome: `agent_schema.redact_home_paths('aw foo /home/<user>/x.md')` returns `'aw foo ~/x.md'`; `redact_home_paths('C:\\Users\\<user>\\x')` returns `'C:\\Users\\~\\x'` or another form carrying no username, and in every case `_HOME_PATH_RE.search(result)` is `None`; non-string input is returned unchanged.
  - Execution state: pending

- [ ] E-02 Pin the new primitive's agreement with the existing detector by asserting, for a table of inputs covering all three home classes plus the already-redacted and the no-path cases, that `_HOME_PATH_RE.search(redact_home_paths(s))` is always `None` and that `redact_home_paths` is idempotent. Put these in the new test module from E-06. This is the property that makes the primitive trustworthy: it is defined as "whatever makes the repository's own home-path detector stop matching", so the two cannot drift.
  - Depends on: E-01
  - Expected outcome: a test that fails if a fourth home class is ever added to `_HOME_PATH_RE` without teaching `redact_home_paths` about it.
  - Execution state: pending

### Task group 2: apply it to the fields that leak

- [ ] E-03 In `agent_workflows/result_types.py`, apply `redact_home_paths` to the free-text fields that measurably leak through `to_dict`: `Diagnostic.to_dict`'s `detail` and `fix`, `Change.to_dict`'s `detail`, and `Evidence.to_dict`'s `value` (string values only) and `detail`. Leave each field's `location`/`path` handling exactly as it is, since `normalize_repo_path` already covers those and changing them is out of scope.
  - Depends on: E-01
  - Expected outcome: the six-row leak matrix measured in F-02 reports `clean` for `diagnostics.detail`, `diagnostics.fix`, `changes.detail`, `evidence.value`, and `evidence.detail`.
  - Execution state: pending

- [ ] E-04 Apply `redact_home_paths` to `NextAction.to_dict`'s `command` and `description`, and to `CommandResult.to_dict`'s `summary`. These are the two remaining leaking channels and they are the ones the carrier's own measurement names: `next_actions[].command` is the field the backlog item measured, and `summary` leaks because it is operator-authored prose that commands interpolate paths into.
  - Depends on: E-01
  - Expected outcome: the leak matrix reports `clean` for `next_actions.command` and `summary`; `aw check --json` emits no `/home/<user>` in any `diagnostics[].fix`.
  - Execution state: pending

### Task group 3: declare the posture

- [ ] E-05 Amend `docs/cli-output-contract.md` and `docs/cli-agent-protocol.md` to state `--json`'s leak posture explicitly: path-valued and free-text fields are home-path-redacted on BOTH machine surfaces, `data` is an UNREDACTED passthrough of command-specific payload and is the one place a caller may still see an absolute path, and the existing "Path Sanitization" invariant is re-scoped so it reads as a property of both machine surfaces rather than of agent records alone. State the reason `data` is exempt (F-05: an approved spec depends on absolute paths there) so the exemption reads as a decision and not an oversight. Correct the "Both renderers expose identical facts ... with zero domain drift" sentence, which says "both" while naming three renderers and which this plan makes true for the leak dimension only.
  - Depends on: E-03, E-04
  - Expected outcome: a reader of either doc can answer "may `aw <cmd> --json` print my home directory?" with "only inside `data`" without reading the code.
  - Execution state: pending

- [ ] E-06 Add `tests/test_json_surface_leak_posture.py` holding the behavioral matrix: for every `CommandResult` channel (`summary`, `diagnostics[].location|detail|fix`, `changes[].path|detail`, `evidence[].value|detail`, `next_actions[].command|description`, `data`), drive `JsonRenderer().render` on a result carrying a planted home path and assert the rendered payload is home-path-free for every channel EXCEPT `data`, which is asserted to still carry it so the exemption is pinned rather than merely documented. Add one end-to-end case driving a real CLI command through `--json` as a subprocess and asserting the parsed payload has no home path outside `data`. Assert the payload still parses as JSON and that the non-path content of each field survives (the redaction is a prefix rewrite, not a drop).
  - Depends on: E-03, E-04
  - Expected outcome: a test module that fails on today's code for seven channels and passes after E-03/E-04, and that would fail if a future change started redacting `data` (which would break spec `kw5y2s`) or stopped redacting a field.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `agent_schema` is STDLIB ONLY and imports nothing from the package (`agent_schema.py` imports `json`, `os`, `re`, `pathlib`, `typing`). `result_types` imports it as `_schema`. So a primitive added to `agent_schema` is reachable from `result_types` with no new import and no cycle, which is why E-01 puts it there rather than in `leak_sanitizer` (which `result_types` does not import, and which imports `renderers`/`result_types` LAZILY inside `leak_sanitizer.main` precisely to avoid that cycle).
- The repository already distinguishes three postures toward a home path, and this plan adds a fourth deliberately rather than reusing one: `assert_valid_agent_record` REFUSES, `normalize_repo_path` RELATIVIZES to the repo, `config._preserve_home` rewrites to `~` for a whole path value, and `leak_sanitizer._rewrite_line` rewrites to `~` inside a LINE OF TEXT. The last is the behavior this plan needs, and the quoted rationale beside it ("Only home/Users paths are auto-rewritten (safe, generic)") is the same reasoning E-01 applies.
- The renderer boundary is uniform: roughly 98 sites call `get_renderer(ctx).emit(res, ctx)`, `emit` is defined ONCE on `BaseRenderer` and overridden by no subclass, and `JsonRenderer` overrides only `render`. So a change made inside `CommandResult.to_dict` reaches every `--json` caller without touching a single call site, which is why this plan changes `to_dict` and not `JsonRenderer`.
- `aw sanitize --agent` is the repository's own authority for judging leak posture (AGENTS.md: run it rather than eyeballing), and `docs/cli-output-contract.md` already cites it in the Path Sanitization invariant: "All records pass `aw sanitize --agent` with zero findings."

## Findings

| # | Finding |
|---|---|
| F-01 | THE CARRIER'S MEASUREMENT REPRODUCES. A `CommandResult` carrying `/home/<user>/secret/x.md` in `next_actions[0].command` renders through `JsonRenderer().render` with the path verbatim in the payload, while `AgentRenderer().render` on the SAME result raises `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next': ...`. Two machine surfaces, identical input, opposite postures. |
| F-02 | `--json` IS NOT SIMPLY UNSANITIZED; IT IS INCONSISTENTLY SANITIZED, which reframes the backlog item. Measured across nine channels, `to_dict` is clean for exactly two: `diagnostics[].location` and `changes[].path` (both call `_schema.normalize_repo_path`). It LEAKS for `summary`, `diagnostics[].detail`, `diagnostics[].fix`, `changes[].detail`, `evidence[].value`, `evidence[].detail`, `next_actions[].command`, and `data`. So the fix is not "add sanitization to `--json`" but "finish the sanitization `--json` already started", which is a materially smaller and less contract-breaking change than the carrier assumed. |
| F-03 | THE LEAK IS LIVE IN SHIPPED COMMANDS, not only in a synthetic result. `aw check --json` emits 22 strings matching the home-path pattern, every one of them in a `diagnostics[].fix` of the form `aw ipd lint <absolute path>`; `aw doctor --json` emits 3, in `diagnostics[].fix`, `data.report.repo_root`, and `data.human_rendered`; `aw status --json` emits 35, all under `data`. `Diagnostic.to_dict` normalizes `location` and passes `fix` through untouched, which is exactly the inconsistency F-02 names and is why `fix` is in E-03's list. |
| F-04 | TWO IMPLEMENTED/APPROVED SPECS ALREADY FORBID AN ABSOLUTE HOME PATH IN `--json`, so the posture is not an open design question for the fields they cover. Spec `attention-registry-and-cross-tree-status` F8a: "No output surface (human board, `--agent`, `--json`) may contain an ABSOLUTE filesystem path for a lane ... these surfaces are pasted into shared contexts, so printing it verbatim is forbidden." Spec `uonrjg` A14 constrains `--json` similarly for ANSI. `aw attention --json` and `aw attention --agent` both measure 0 home-path hits today, so F8a is being honored by the attention command specifically rather than by the surface generally. |
| F-05 | ONE APPROVED SPEC DEPENDS ON ABSOLUTE PATHS IN `--json`, and it is the reason `data` must stay exempt. Spec `kw5y2s` Section 2.4: "`aw context --json` ALREADY emits `data.logical_roots` (all four roots, resolved to absolute paths) ... A non-Python tool willing to shell out to Python is therefore already served for ROOTS." Measured: `aw context --json` emits absolute paths under `data.logical_roots`, `data.target_repo`, `data.effective_aw_home`, and `data.permitted_commit_destinations`. Redacting `data` would break that approved contract, which settles the carrier's question in the SPLIT form E-05 documents: envelope redacted, `data` raw. |
| F-06 | `normalize_repo_path` CANNOT BE REUSED FOR THESE FIELDS, for two independent measured reasons. First, it operates on a whole path VALUE: given `'aw foo /home/<user>/secret/x.md'` it returns the string unchanged and `_HOME_PATH_RE` still matches, so it is useless for the free-text fields that carry a command line. Second, where it does fire on an out-of-repo path it SILENTLY FALSIFIES: `'/home/<user>/code/other/.aw/records/a.md'` returns `'.aw/records/a.md'`, a repo-relative path that does not exist in this repo, because the marker scan strips everything before a known marker. That makes it actively wrong for `detail`/`fix`/`value`, which routinely name paths outside the repo. `leak_sanitizer._rewrite_line`'s substring rewrite handles both cases correctly (`'aw foo ~/secret/x.md'`, `'~/code/other/.aw/records/a.md'`), which is the behavior E-01 reproduces. |
| F-07 | THE THREE HOME-PATH REGEXES ARE DUPLICATED CHARACTER-FOR-CHARACTER between `agent_schema._HOME_PATH_RE` (one fused alternation) and `leak_sanitizer._FAIL_PATTERNS` (three named rules `home-path`, `users-path`, `windows-home`), with NO shared constant and no test asserting they agree. This plan does NOT unify them (that is a separate concern with its own blast radius, recorded in "Deferred"), but E-02 pins the new primitive against `_HOME_PATH_RE` specifically so this plan adds no THIRD independent definition. |
| F-08 | `leak_sanitizer._rewrite_line` DOES NOT HANDLE THE WINDOWS CLASS, WHICH CONSTRAINS E-01 BUT IS NOT ITSELF A DEFECT. Measured, `'C:\Users\<user>\x'` passes through `_rewrite_line` unchanged and both `_FAIL_PATTERNS['windows-home']` and `_HOME_PATH_RE` still match it, because `_HOME_ANY_RE`/`_USERS_ANY_RE` cover only the two POSIX forms. So E-01 must NOT be a copy of `_rewrite_line`; it must cover all three classes, and E-02 is what proves it does. The omission in the sanitizer is DELIBERATE and self-documented at the definition site ("Only home/Users paths are auto-rewritten (safe, generic) ... because there is no safe generic replacement"), and a bare `~` would indeed lose the drive letter. Measured end-to-end in a throwaway repo: `aw sanitize <dir> --fix --yes` rewrites the POSIX path, leaves the Windows path, then prints "Needs manual edit (no safe auto-fix): note.md:1: windows-home: ..." and EXITS 1, because `fix_working_tree` re-scans its own output and collects what the rewrite did not resolve. So `--fix` does not silently leave a leak; it names it and fails. This matters to the plan only as the reason E-01 cannot delegate. |
| F-09 | THE `--agent` SURFACE IS CLEAN MOSTLY BY OMISSION, NOT BY SANITIZATION, which is why "make `--json` match `--agent`" is the wrong framing. In default (non-verbose) mode, `to_agent_record` drops `detail`, `fix`, and evidence values entirely, so a planted home path in those fields never reaches the validator and the record renders clean. Under `--verbose` the same inputs REFUSE with a `ValueError` for `evidence[].value`, `evidence[].detail`, `diagnostics[].detail`, `diagnostics[].fix`, and `changes[].detail`. So `--agent`'s posture is "omit, else crash", and this plan's redaction makes those same fields SAFE rather than fatal, which is a strict improvement for `--agent` too. |
| F-10 | THAT `--verbose` CRASH IS NOT REACHABLE FROM THE COMMAND LINE TODAY, which bounds this plan's claim. `--verbose` is declared on exactly one subcommand (`cli.py`, the `common_upgrade` group near the `upgrade-test` parser); `aw check --agent --verbose` and `aw check -v --agent` both exit 2 with "unrecognized arguments". So F-09's refusal is reachable only through the library API, and this plan must NOT claim to fix a live CLI crash. The live, operator-visible defect is the `--json` leak in F-03. |
| F-11 | NO SPEC GOVERNS THE `--json` PAYLOAD SHAPE, so there is no spec to amend and E-05 amends docs only. `assert_valid_agent_record` appears in zero specs. The closest governing record, spec `command-surface-redesign`, is `implemented` and its G6 was explicitly SUPERSEDED by a history note redirecting to `docs/cli-output-contract.md`, which makes that doc the operative contract for this surface and the right place for E-05's declaration. |
| F-12 | THE DOCS CURRENTLY DISAGREE WITH THEMSELVES on whether `--json` is a machine contract. `docs/cli-agent-protocol.md` calls it "pretty-printed full `CommandResult` JSON (a debugging view, more verbose)" and `docs/cli-output-contract.md` says it is "for human debugging", which argues for raw paths; but the same contract file says "Renderers (`HumanRenderer`, `AgentRenderer`, `JsonRenderer`) consume the same `CommandResult`. Both renderers expose identical facts ... with zero domain drift" (note: says "both" while naming three), and its Path Sanitization invariant is written as a property of records generally. E-05 resolves the contradiction in text rather than leaving the next reader to re-derive it. |
| F-13 | `aw sanitize` CANNOT SEE THIS CLASS OF LEAK, so no existing check would have caught F-03, and this is why E-06 must assert on rendered payloads directly rather than delegating to the sanitizer. It scans files, staged blobs, history, and wheels (it takes a `dir` positional), never the stdout of another command. Separately and incidentally, `aw sanitize --json` emits NOTHING on stdout (exit 0) while the human line "No local leaks found." goes to stderr, because the dispatcher `cli._run_check_local_leaks` forwards `--history`, `--max-commits`, `--wheel`, `--staged`, `--warn`, `--agent`, `--fix`, `--yes`, and `--dry-run` into its hand-built passthrough argv but never forwards `--json`; `leak_sanitizer.main`'s own machine branch tests `ctx.is_agent or ctx.is_json` and would honor it. Carrier `xym8g8`. Not this plan's concern (a dropped flag, not a payload-content question) and not relied upon by any item here. |
| F-14 | THERE IS NO TEST COVERAGE TO REGRESS. No `tests/test_renderers.py` exists and `JsonRenderer` appears in ZERO test files. The nearest existing assertion is `tests/test_attention.py::test_no_project_agent_envelope`, which checks the `--json` shape via `status`/`exit_code` keys and asserts `assertNotIn(td, out)` for a tempdir path, i.e. it already pins a weak form of "no absolute path in `--json`" for one command. E-06 is therefore additive, and `tests/conformance_matrix.py` declares a `"json"` scenario whose driver `test_cli_conformance_matrix.py` does not exist. |
| F-15 | THIS PLAN DOES NOT COLLIDE WITH `wqiofa`, the sibling plan from the same carrier. `wqiofa` (Set `un6ppd`, `Status: reviewed`, `Readiness: no-go`, blocked on its own OQ-05) changes `agent_schema`'s serializer seam and `AgentRenderer`'s four emission points; it explicitly excludes this concern, stating "THE HUMAN AND `--json` RENDERERS ARE NOT TOUCHED ... That `JsonRenderer` consequently emits an unsanitized home path is a REAL and different concern about `--json`'s leak posture, not a crash, and it is not this plan's. `- Carrier: 7tixnq`". Both plans name `agent_workflows/agent_schema.py` in Scope-Paths, but in disjoint regions (it adds a guarded serializer; this adds a redaction helper) and neither depends on the other, so they are order-independent. `wqiofa` is also not executable until its blocking OQ is answered, so sequencing this plan behind it would park it indefinitely for no benefit. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/agent_schema.py`** gains `redact_home_paths(text)` beside `normalize_repo_path`: a lossy, idempotent prefix rewrite covering all three home classes `_HOME_PATH_RE` detects, returning non-string input unchanged (E-01). This is the only new primitive; everything downstream is an application of it.
2. **`agent_workflows/result_types.py`** applies it in `Diagnostic.to_dict` (`detail`, `fix`), `Change.to_dict` (`detail`), and `Evidence.to_dict` (`value` when a string, `detail`) (E-03), then in `NextAction.to_dict` (`command`, `description`) and `CommandResult.to_dict` (`summary`) (E-04). No existing `normalize_repo_path` call is altered. Because the change lands in `to_dict`, it reaches every `--json` caller without touching the ~98 `get_renderer(...).emit(...)` sites, and it also hardens `--agent` under `--verbose` (F-09).
3. **`docs/cli-output-contract.md`** and **`docs/cli-agent-protocol.md`** state the resulting posture: envelope fields redacted on both machine surfaces, `data` an explicitly exempt raw passthrough with F-05's reason, the Path Sanitization invariant re-scoped to both machine surfaces, and the "both renderers" sentence corrected (E-05).
4. **`tests/test_json_surface_leak_posture.py`** pins the full channel matrix behaviorally, including a subprocess end-to-end case and the `data`-still-leaks assertion that keeps spec `kw5y2s` from being broken by a later over-correction (E-02, E-06).

## Deferred / out of scope (with reason)

- **Making `--json` validate against `aw.agent/v1`.** Out of scope and arguably impossible without a schema decision: `to_dict` emits `command`/`exit_code`/`status` where the validator requires `cmd`/`exit`/`outcome`, so `validate_agent_record` can never accept a `--json` payload by construction. Independently measured twice in-repo (pending plan `y0t9u7` F-17 records the actual errors `Invalid kind: 'None'` and `Field 'cmd' must be a non-empty string`; pending plan `5poaqh` records the same asymmetry and explicitly defers the conversion). This plan fixes the LEAK posture without touching the SHAPE question.
  - Carrier: 5poaqh
- **Redacting `data`.** Deliberately exempt, per F-05: approved spec `kw5y2s` Section 2.4 relies on `aw context --json` emitting absolute `data.logical_roots`. E-06 pins the exemption with a test so it stays a decision. Note the consequence honestly: `aw status --json` (35 hits) and `aw doctor --json` (`data.report.repo_root`, `data.human_rendered`) keep emitting home paths under `data` after this plan. Narrowing specific `data` payloads is per-command work.
  - Carrier-Declined: Nothing is owed by this plan. This is a decision resolved from evidence in OQ-01 and F-05, not deferred work: an approved spec DEPENDS on absolute paths under `data`, so redacting it is rejected rather than postponed, and E-06 pins the exemption so the decision cannot rot into an accident. A per-command narrowing of a specific `data` payload would be a new product decision about that command's contract, not an obligation this plan creates.
- **Unifying the duplicated home-path regexes** between `agent_schema` and `leak_sanitizer` (F-07). A real duplication hazard, but it touches the sanitizer's config-gated per-rule severity model and its allowlists, which have nothing to do with `--json`. E-02 ensures this plan adds no third definition.
  - Carrier: ddhpcb
- **Teaching `leak_sanitizer`'s `--fix` a drive-preserving Windows rewrite** (F-08). Explicitly NOT a defect: measured, `--fix` names the unrewritten `windows-home` finding and exits 1, and the omission is self-documented as deliberate because no safe generic replacement exists. Nothing in this plan depends on it.
  - Carrier: 9cff1j
- **`aw sanitize --json` producing no stdout** (F-13), caused by the dispatcher never forwarding `--json` into `leak_sanitizer.main`. Worth auditing the same hand-maintained passthrough pattern on other forwarded leaves, which is that carrier's scope and not this plan's.
  - Carrier: xym8g8
- **`AgentRenderer`'s unguarded `ValueError`** (F-09, F-10). This plan reduces the number of inputs that can trigger it but does not guard the raise.
  - Carrier: un6ppd
- **The missing `tests/test_cli_conformance_matrix.py`** driver referenced by `tests/conformance_matrix.py` (F-14). Pre-existing gap, not created or worsened here.
  - Carrier: h0tiaw

## Scope check

- Over-scope: none. The change is confined to one new helper, six `to_dict` field applications, two doc files, and one new test module. No renderer class, no call site, no `data` payload, and no schema shape is touched.
- Under-scope: `data` stays unredacted by design (F-05), so `aw status --json` and `aw doctor --json` still emit home paths there after this plan; the "Deferred" section records this explicitly rather than leaving it implied. The duplicated regexes (F-07, carrier `ddhpcb`) and the dropped `--json` flag on `aw sanitize` (F-13, carrier `xym8g8`) are left in place. `--agent`'s unguarded raise is `wqiofa`'s.

## Required tests / validation

- `python3 -m pytest tests/test_json_surface_leak_posture.py` passes, with the per-test counts captured via `-o addopts=""` where a count is needed.
- The full suite passes BARE: `python3 -m pytest` (configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`). Paste the actual `N passed` summary line.
- `python3 -m pytest tests/test_attention.py tests/test_agent_field_projection.py tests/test_agent_schema_paths.py tests/test_leak_sanitizer.py tests/test_local_leaks.py` passes, covering the nearest existing assertions on both machine surfaces and both home-path rule sets.
- `aw check --json` and `aw doctor --json` emit zero home-path matches OUTSIDE `data`, measured with the same recursive walk used to establish F-03 (before: 22 and 3 hits respectively; after: 0 outside `data`).
- `aw context --json` STILL emits absolute paths under `data.logical_roots`, confirming spec `kw5y2s` Section 2.4 is unbroken.
- `aw sanitize --agent` reports no new finding on the tree.
- `aw ipd lint --phase pre-transition` reports conforming.

## Spec / documentation sync

- **No spec amendment.** Per F-11 no spec governs the `--json` payload shape, and the one spec that did (`command-surface-redesign` G6) was superseded by a history note redirecting to `docs/cli-output-contract.md`. No `.spec.md` file appears in `Scope-Paths`, so this plan declares no spec edit.
- Specs `attention-registry-and-cross-tree-status` (F8a) and `uonrjg` (A14) are SATISFIED MORE STRONGLY by this change, not amended: both already forbid absolute home paths on `--json`, and this plan moves the guarantee from per-command discipline to the shared `to_dict` boundary.
- Spec `kw5y2s` Section 2.4 is PRESERVED by the `data` exemption, and E-06 adds the test that keeps it preserved.
- `docs/cli-output-contract.md` and `docs/cli-agent-protocol.md` are amended by E-05, which is the operative contract for this surface.

## Open questions

### OQ-01: Should `--json` adopt home-path sanitization, given it is documented as a "full structured JSON representation" whose caller may legitimately want absolute paths?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE; the carrier asked for "a maintainer's view on the intended posture", and the repository already states that posture in two approved/implemented specs, so asking again would be asking the maintainer to re-decide something already decided. Spec `attention-registry-and-cross-tree-status` F8a names `--json` explicitly among the surfaces that may NOT contain an absolute filesystem path, with the reason "these surfaces are pasted into shared contexts"; spec `uonrjg` A14 constrains `--json` in the same breath as `--agent`. That answers "yes, sanitize" for the envelope. The countervailing evidence is equally concrete and bounds the answer rather than contradicting it: approved spec `kw5y2s` Section 2.4 relies on `aw context --json` emitting absolute `data.logical_roots`, so blanket redaction WOULD break a live approved contract. The decision is therefore the SPLIT this plan implements: redact the envelope (where the specs forbid absolute paths), leave `data` raw (where a spec depends on them), and say so in the contract. Two further measurements make this low-risk rather than a judgement call. First, `--json` is not currently a clean "raw" surface a consumer could be relying on: it ALREADY normalizes `diagnostics[].location` and `changes[].path` (F-02), so a caller parsing it cannot already depend on absolute paths in the envelope, and the change finishes an existing behavior instead of reversing a promise. Second, the fields E-03/E-04 touch are free-text human-facing strings (`detail`, `fix`, `summary`, `description`) plus a suggested command line, none of which is a documented machine-consumable path field. If the maintainer disagrees with the split, the correction is confined to E-05's wording and the E-06 expectations, not to the primitive.

### OQ-02: Should the redaction target `~` specifically, or a neutral placeholder such as `<home>`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `~` is chosen, for consistency with the two existing home-rewriting mechanisms rather than on aesthetics: `leak_sanitizer._rewrite_line` rewrites to `~` ("home-style absolute paths rewritten to a portable `~` form") and `config._preserve_home` rewrites to `~/...` with the docstring rationale "`/home/u/src` -> `~/src` (portable)". `~` also keeps a `fix` field's suggested command line PASTEABLE, which `<home>` would not, and that matters because F-03 shows `diagnostics[].fix` is the single highest-volume leaking field and its whole purpose is to be copied into a shell. Note the honest limit: `~` resolves to the READER's home, not the author's, so a redacted `fix` is pasteable but only correct when the path was under the reader's own home. That is strictly better than today, where the string is correct for exactly one machine and leaks on every other.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python session calling `agent_schema.redact_home_paths` on one input per home class (POSIX `/home/<user>/...`, macOS `/Users/<user>/...`, Windows `<drive>:\Users\<user>\...`), on a path embedded mid-string (`'aw foo /home/<user>/x.md'`), on an already-`~` value, on a string with no path, and on a non-string (e.g. `None`, `42`). For each, paste the returned value AND the boolean `_HOME_PATH_RE.search(result) is None`. Every boolean must be `True` and the non-string inputs must come back identical.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `pytest` output for the agreement/idempotence tests run with `-o addopts=""` so the per-test count is visible. Then paste a demonstration that the test is FALSIFIABLE: temporarily add a fourth alternation to a local copy of `_HOME_PATH_RE` (or monkeypatch it) that `redact_home_paths` does not handle, show the test FAILING, revert, and show it passing again.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the before/after leak matrix for the five E-03 channels (`diagnostics[].detail`, `diagnostics[].fix`, `changes[].detail`, `evidence[].value`, `evidence[].detail`), produced by rendering a `CommandResult` carrying a planted home path through `JsonRenderer().render` and reporting `LEAKS`/`clean` per channel. The BEFORE column must match F-02 (all five `LEAKS`) and the AFTER column must be `clean` for all five. Also paste one full rendered field value showing the non-path content survived (e.g. `aw ipd lint ~/r/a.py`, not a dropped field).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the before/after leak matrix rows for `next_actions[].command`, `next_actions[].description`, and `summary` (before: `LEAKS`; after: `clean`). Separately paste the recursive-walk hit count for `aw check --json` before and after (before must be 22 per F-03; after must be 0), and confirm by inspection that the remaining payload still contains the `aw ipd lint` fix strings in redacted form rather than having lost them.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `git diff` of `docs/cli-output-contract.md` and `docs/cli-agent-protocol.md`. The diff must show (a) an explicit statement of `--json`'s leak posture, (b) the `data` exemption WITH its reason naming spec `kw5y2s`, (c) the Path Sanitization invariant re-scoped to both machine surfaces, and (d) the corrected "both renderers" sentence. Confirm the prose contains no em or en dashes (user-facing docs, per the execution contract).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare full-suite run `python3 -m pytest` with its actual `N passed` summary line, plus `python3 -m pytest tests/test_json_surface_leak_posture.py -o addopts=""` showing the per-test counts. Paste the `data`-exemption test asserting a home path is STILL present under `data`, and paste `aw context --json` output showing `data.logical_roots` still absolute (spec `kw5y2s` unbroken). Paste the subprocess end-to-end assertion's output. Finally paste `aw sanitize --agent` showing no new finding, and `aw ipd lint --phase pre-transition` reporting conforming.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `- Status: to-review` and carries NO `- Readiness:` field: that field is an output of `/plan-review` and writing it here would forge a review that has not happened. Execution requires explicit human approval recorded with `aw ipd set approved <id6> --by-human`.

Execution contract: commit only the files named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Run the suite BARE (`python3 -m pytest`) and paste the actual runner output; a claim of passing tests without pasted output is a contract violation. Do not mark any `V-*` item complete from the matching `E-*` checkmark; inspect the evidence in a separate pass.

Post-gate lifecycle: when every `E-*` item is performed and every `V-*` item carries pasted evidence, run `aw ipd lint --phase pre-transition`, confirm it reports conforming, and only then move this plan to `.aw/records/plans/executed/` through the tooled transition. Backlog item `7tixnq` is set to `graduated` (not `done`) when this plan is authored and reviewed; it reaches `done` only once this plan is executed.
