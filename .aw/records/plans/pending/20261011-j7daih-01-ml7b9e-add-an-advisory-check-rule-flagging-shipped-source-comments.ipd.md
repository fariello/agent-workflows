# IPD: Add an advisory check rule flagging shipped-source comments that cite nonexistent test files

- Date: 2026-10-11
- Kind: child
- Concern: Comments and docstrings in shipped source (`agent_workflows/`, `tools/`, non-test `.py`) cite `tests/test_*.py` paths as live guards, and many of those files no longer exist (the `19313eed` and `80db6750c` suite trims removed hundreds). Nothing detects a NEW dangling citation, so the rot regrows as fast as sibling cleanup plans remove it. The existing `check.test-citation-dangling` rule (`check_engine.check_spec_test_citations_for_text`, IPD `h65phz`) covers spec bodies only, and `tests/test_docs_test_citations.py` (plan `1jg2m2`) covers `docs/` plus five root prose files only. Shipped source has no equivalent.
- Scope: IN: (a) a new `check_engine` rule `check.source-test-citation-dangling` registered in `RULE_REGISTRY` at severity `info` (advisory, exit code unaffected), evaluated on the `aw check all` full-sweep seam in `check_engine.check_types`; (b) a keyed exemption for retirement statements (a citation whose sentence names it deleted/retired/removed together with a commit hash) and for an explicit placeholder set of illustrative names; (c) a behavioral test over synthesized fixture trees; (d) a CHANGELOG entry. OUT: fixing any existing dangling citation (owned by `iosmvn`, `3tov52`/`65d5zf`, `9vfxhn`/`l4lc6p` and siblings); promoting the rule to `error` (needs the baseline at zero first); `.aw/records/`, `docs/`, `CHANGELOG.md`/`DECISIONS.md` citation scanning (owned elsewhere or append-only history); test files themselves (fixture literals).
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_source_test_citation.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: low
- From-Backlog: j7daih
- Set: j7daih
- Order: 1
- Highest E allocated: 07
- Author: opencode
- Id: ml7b9e
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008

- 2026-10-12 /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 fixed (review record 20261011-j7daih-01-ml7b9e)
- 2026-10-12 draft (opencode): created.
- 2026-10-11 to-review (opencode): authored from backlog `j7daih`; baseline measured at HEAD `0d67a8b70`.

## Goal

Make every NEW shipped-source comment that cites a nonexistent `tests/test_*.py` file visible in `aw check all`, without turning the check red while the existing baseline (about 110 live dangling citations) is still being cleaned up by sibling plans, so the cleanup cannot be silently undone and the rule can later be promoted to `error` by a one-line severity change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [ ] E-01 Re-measure the baseline at execution HEAD and record the suite baseline. Run (a) `git rev-parse --short HEAD`; (b) a throwaway measurement script (not committed) that walks non-test `*.py` under `agent_workflows/` and `tools/`, matches `tests/test_[A-Za-z0-9_]+\.py`, and prints counts of citations whose target is missing, partitioned into `placeholder`, `retired` and `live` using exactly the exemption rules E-03 will implement, plus the count of distinct live (file, cited path) pairs (the figure E-03's deduplicated finding count must equal); (c) a BARE `python3 -m pytest` (no `-n0`, no extra `-q`, no `-p no:randomly`), recording the summary line AND the set of FAILED node ids; (d) `aw check all --agent`, recording its exit code and the per-rule count of its diagnostics; (e) `time aw check all >/dev/null` for end-to-end wall-clock context.
  - Depends on: none
  - Expected outcome: five pasted outputs. The partition and pair count are re-derived at execution HEAD and are the bar for V-03; the authoring measurement is context only (placeholder 11, retired 21, live 110, 79 live pairs at `0d67a8b70`, reproduced identically at review HEAD `bd8b8e993`), and any drift is stated and attributed to sibling cleanup plans landing.
  - Execution state: pending

### Task group 2: the rule

- [ ] E-02 Register `"check.source-test-citation-dangling": RuleSpec("info", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")` in `check_engine.RULE_REGISTRY`, directly after the existing `"check.test-citation-dangling"` entry, with a comment stating: the scope (shipped non-test source), WHY `info` (the measured live baseline would start the rule red, which the backlog item explicitly sequences after cleanup, and `artifact_core.drift_exit_code` ignores `info` so no caller's exit contract changes), and that promotion to `error` is a one-line change once the live count reaches zero.
  - Depends on: E-01
  - Expected outcome: `python3 -c "from agent_workflows import check_engine as c; print(c.RULE_REGISTRY['check.source-test-citation-dangling'].severity)"` prints `info`.
  - Execution state: pending

- [ ] E-03 Add `check_engine.check_source_test_citations(repo_root, scan_roots=("agent_workflows", "tools"))` beside `check_spec_test_citations`. It walks `*.py` under each scan root, skips files named `test_*.py` or `*_test.py` (fixture literals) and paths for which `artifact_core.is_ignored_path` is True (using `artifact_core.get_ignored_dirs`), skips any file not containing the substring `tests/test_` before regex work (cheap prefilter), reuses the existing `_TEST_PATH_RE`, and for each match whose `repo_root / <match>` is not a file emits one `enrich_drift(_core.Drift(<repo-relative POSIX path>:<line>, "check.source-test-citation-dangling", <constant detail>), observed=..., required=..., recovery=...)` with `severity="info"`. Exemptions, each a named module constant so a reviewer can read them: (i) `_SOURCE_TEST_CITATION_PLACEHOLDERS`, a frozenset of illustrative names measured in the live tree at authoring (`tests/test_x.py`, `tests/test_foo.py`, `tests/test_extra.py`, `tests/test_secret.py`); (ii) a RETIREMENT STATEMENT, a compiled module regex `_SOURCE_TEST_CITATION_RETIRED_RE` applied to the WINDOW formed by the match's own line joined (with one space) to the next line: a whole word `deleted`, `retired` or `removed` (case-insensitive) followed within 80 characters by a whole-word hex token of 7 to 40 characters CONTAINING AT LEAST ONE DIGIT (so an English hex-letter word such as `defaced` is not a hash). No sentence parsing is attempted; the window is the only boundary. This is the established retirement wording (`was deleted in \`19313eed\``) used by sibling plans `65d5zf` and `dtelfb`; review reproduced the digit-requiring form exempting the same 21 citations as the authoring form. Exemptions are applied PER OCCURRENCE, BEFORE deduplication: deduplicate the remaining non-exempt occurrences per (file, cited path) and report the line of the FIRST non-exempt occurrence, so a pair whose first mention is a retirement statement but whose later mention is a live claim still reports (review measured 4 such mixed pairs). The `detail` is a CONSTANT string under 60 characters (for example `comment cites a test file that does not exist`), because `doctor.build_remediation`'s generic fallback uses a short detail as the title and `aw doctor` summaries group on (title, summary_fix), so interpolating the path would fragment the summary; the cited path goes in `observed`, and `recovery` names both remedies (repoint the citation, or rewrite it as a retirement statement naming the deleting commit).
  - Depends on: E-02
  - Expected outcome: calling the function on the live repo returns only findings of the new rule, each with severity `info` and a `path:line` location; on a fixture tree it returns exactly the defects planted there.
  - Execution state: pending

- [ ] E-04 Wire the evaluator into the `collisions` full-sweep branch of `check_engine.check_types`, beside `check_scope_path_target_stale`, inside its OWN `try/except Exception: pass` matching its neighbours (a failure must not suppress another scan), with a comment noting that it therefore fires on `aw check all` and not on a type-scoped run, exactly like its siblings on that seam.
  - Depends on: E-03
  - Expected outcome: `aw check all --agent` emits `check.source-test-citation-dangling` findings at `info`; its per-rule diagnostic counts differ from E-01's ONLY in the new rule id (every other rule's count unchanged, modulo drift explained by a commit landing between the two runs); and its exit code equals E-01's. Because the live tree already exits 1 at review (`bd8b8e993`), exit parity alone cannot show the rule is advisory; the discriminating proof is E-05 cases (9) and (9b).
  - Execution state: pending

### Task group 3: tests and docs

- [ ] E-05 Create `tests/test_check_engine_source_test_citation.py` exercising the rule ONLY through behavior (P16: no reading of `check_engine.py` source). Each test builds a synthesized repo under `tempfile.TemporaryDirectory` with `agent_workflows/`, `tools/` and `tests/` dirs and calls `check_engine.check_source_test_citations`, then `check_engine.check_types(repo, ["all"])` for integration. Cases: (1) a comment citing a missing `tests/test_gone.py` FIRES once with rule id and severity `info` and a location naming the file and line; (2) a citation of an existing `tests/test_here.py` is SILENT; (3) a retirement statement ("`tests/test_gone.py` was deleted in `19313eed`") is SILENT; (4) the word "deleted" WITHOUT a commit hash still FIRES, and so does "deleted in `defaced`" (a hex-letter word with no digit) (discriminating negatives for the exemption); (5) a placeholder `tests/test_x.py` is SILENT; (6) the same missing path cited twice in one file reports ONCE, and cited in two files reports twice; (6b) a file whose FIRST mention of a missing path is a retirement statement and whose LATER mention is a bare live claim reports ONCE, at the later line; (7) a missing citation inside a file named `test_fixture.py` under `tools/` is SILENT; (8) a citation under a `__pycache__` directory is SILENT (default ignore set, no git needed), and a citation under a directory listed in `.gitignore` of a fixture on which `git init` was run is SILENT (skip only that half with a stated reason if `git` is unavailable); (9) `check_engine.rule_spec("check.source-test-citation-dangling").severity == "info"` and `artifact_core.drift_exit_code` over the case (1) finding list returns 0; (9b) the same list with each finding `._replace(severity="warning")` returns 1, the contrastive pair that localizes the exit code to the severity; (10) the `check_types(repo, ["all"])` result contains the case (1) finding.
  - Depends on: E-04
  - Expected outcome: `python3 -m pytest tests/test_check_engine_source_test_citation.py -o addopts=""` passes every case above; temporarily neutering the retirement exemption (local edit, reverted, not committed) makes case (3) fail, and temporarily moving deduplication before the exemption makes case (6b) fail, proving both discriminate.
  - Execution state: pending

- [ ] E-06 Add one `- Added:` bullet under the pending `2.0.0` section of `CHANGELOG.md` describing the advisory `check.source-test-citation-dangling` rule in plain user-facing language (what it reports, that it is advisory and does not change the exit code, how to silence a deliberate historical mention by naming the deleting commit). No em or en dashes.
  - Depends on: E-05
  - Expected outcome: `git diff CHANGELOG.md` shows exactly one added bullet, and `grep -nP '[\x{2013}\x{2014}]'` over the added line prints nothing.
  - Execution state: pending

- [ ] E-07 Run the full regression: BARE `python3 -m pytest`, `aw check all --agent` (exit code and per-rule counts compared against E-01), a timing one-liner calling `check_engine.check_source_test_citations` on the live repo with `time.perf_counter`, `time aw check all >/dev/null` (context), and `aw sanitize --agent`.
  - Depends on: E-06
  - Expected outcome: the set of FAILED node ids is a subset of E-01's (a node failing only after is re-run once alone and, if it still fails, is a STOP condition when attributable to this change); `aw check all` exit code unchanged; the new scan's own wall clock is under 1 second (review measured an equivalent scan at 0.23s over 47 candidate files), with the end-to-end `aw check all` times pasted as context only, since a 28s run's run-to-run noise exceeds the scan's cost; sanitizer result `pass`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `check_engine.RULE_REGISTRY` maps rule id to `RuleSpec(severity, assurance, determinism, invariant)`; `tests/test_severity_tier_contract.py::test_rule_registry_severities_conform_to_canonical_enum` requires a canonical severity (`error`/`warning`/`info`).
- `artifact_core.drift_exit_code` returns 0 when every finding is `info` ("an `info`-severity finding is ADVISORY ... and does NOT fail the gate"). Precedent for advisory-first rules: `check.collisions-not-checked` and `check.plan-spec-link-missing`.
- Cross-tree scans ride the `if collisions:` seam of `check_engine.check_types`, each in its own `try/except` (see the `check_scope_path_target_stale` and `check_from_spec_dangling` calls and their comments).
- The sibling rule `check.test-citation-dangling` (`check_spec_test_citations_for_text`, IPD `h65phz`) defines `_TEST_PATH_RE = _re.compile(r"tests/test_[a-zA-Z0-9_]+\.py")` and the `enrich_drift(observed/required/recovery)` shape; this plan reuses both.
- `artifact_refs.check_source_citations` already walks `agent_workflows/` and `tools/` non-test `.py` for dangling RECORD filename citations (IPD `68hdic`), skipping test files and ignored paths via `artifact_core.get_ignored_dirs`/`is_ignored_path`; this plan follows the same file-selection rule so the two source scans agree on what "shipped source" means.
- Retirement wording precedent: plan `65d5zf` and plan `dtelfb` rewrite dead citations as "deleted in `<commit>`; no live guard currently enforces this".
- `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE" / `GUIDING_PRINCIPLES` P16: the test calls functions over fixture trees; it never reads production source. The RULE itself reads source comments, which is its product behavior, not a test pinning code.
- Suite runs BARE (`python3 -m pytest`); narrowed runs clear defaults with `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | MEDIUM | Throwaway scan at `0d67a8b70` over non-test `*.py`: `agent_workflows 136 dangling in 27 files`, `tools 6 in 1 file` | Shipped source carries 142 citations of missing `tests/test_*.py` files, and nothing reports a new one. |
| F-02 | MEDIUM | Same scan partitioned: `Counter({'live': 110, 'retired': 21, 'placeholder': 11})`, 0.12s | 21 already read as retirement statements naming a commit, 11 are illustrative placeholders (`tests/test_x.py`, `tests/test_extra.py`, `tests/test_foo.py`, `tests/test_secret.py`). An `error` rule would start red on 110; the backlog item says the rule lands "once the baseline cleanup is complete", which is why it is born `info`. |
| F-03 | INFO | `check_engine.check_spec_test_citations_for_text` docstring and `RULE_REGISTRY["check.test-citation-dangling"]` comment | The existing rule is scoped to spec normative bodies only and is `error` because that tree measured clean; no source equivalent exists. |
| F-04 | INFO | `tests/test_docs_test_citations.py` module docstring: bounded to `docs/**/*.md` plus five root prose docs | The docs guard (plan `1jg2m2`) does not reach shipped source, as the backlog item states. |
| F-05 | LOW | `time aw check all` -> `real 0m28.041s` | The full sweep is already slow; the new scan must be cheap. The substring prefilter limits regex work to the 46 files that mention `tests/test_` at all. |
| F-06 | INFO | `grep -rln check.test-citation-dangling` over specs/docs -> only `check_engine.py` and its test | No spec or doc enumerates check rules by id, so no spec amendment is owed. |
| F-07 | LOW | Review re-scan at `bd8b8e993`: 82 missing (file, path) pairs, 79 with a live occurrence, 4 mixed (`agy_runipd.py`/`oc_runipd.py` x `tests/test_runner_backlog_close.py`, `runner_shared.py` x `tests/test_orchestrator_probe_cache.py` and `tests/test_runner_refork_guard.py`) | Exemption-vs-dedup order decides whether a mixed pair reports; E-03 now fixes it (exempt per occurrence, then dedup) and V-03's bar is the live-pair count. |
| F-08 | LOW | `aw check all --agent` at `bd8b8e993`: `exit 1` (79 `check.lifecycle-transition-unvalidated`, 30 `check.ipd-uncarried-obligation`, others) | The live tree already exits 1, so exit-code parity cannot prove the rule advisory; the proof is the registry assertion plus the `drift_exit_code` contrastive pair (E-05 9/9b) and the per-rule count delta (V-04). |

## Proposed changes (ordered, validatable)

1. E-01: measure baseline partition, suite, `aw check all` exit code and wall clock.
2. E-02: register the `info` rule with its rationale comment.
3. E-03: implement `check_source_test_citations` with the placeholder and retirement-statement exemptions.
4. E-04: wire it onto the `aw check all` full-sweep seam.
5. E-05: behavioral test with a discriminating negative.
6. E-06: CHANGELOG entry.
7. E-07: full regression, exit-code parity, timing, sanitizer.

## Deferred / out of scope (with reason)

- Repairing or retiring the roughly 110 live dangling citations: cleanup work already tracked per cluster; doing it here would collide with reviewed sibling plans.
  - Carrier: iosmvn
- Promoting `check.source-test-citation-dangling` from `info` to `error` (fail closed) once the live count is zero: a policy change with repo-wide blast radius that cannot be decided until the sibling cleanups land.
  - Carrier-Declined: Declined here rather than owed: it is a one-line severity edit whose precondition (live count zero) is printed by this rule itself in every `aw check all`, so it cannot be forgotten silently, and the decision belongs to the maintainer at that time.
- Scanning `docs/`, root prose, `.aw/records/`, `CHANGELOG.md`/`DECISIONS.md`: `docs/` and root prose are owned by `1jg2m2`; records and the two history files are immutable or append-only history whose citations were true when written.
  - Carrier-Evidence: .aw/records/plans/executed/20260930-ikxtkj-01-1jg2m2-repoint-or-retire-the-dangling-test-file-citations-in-publis.ipd.md
- Citations in test files (`tests/**`, `tools/**/test_*.py`): these are fixture literals that must not resolve on disk (same exclusion `artifact_refs.check_source_citations` makes).
  - Carrier-Declined: genuine won't-fix; flagging fixture literals would be a false positive by construction.
- `pytest` node-id suffixes (`tests/test_x.py::Class::test`) for files that exist but whose class or function was deleted: the item asks for nonexistent test FILES; node-level resolution needs importing tests and is a different, costlier check.
  - Carrier-Declined: outside the backlog item's stated subject (nonexistent test files); no tracked demand for node-level resolution exists.

## Scope check

- Over-scope: none. `CHANGELOG.md` is touched only because a new user-visible check finding is a user-facing change.
- Under-scope: none. The rule, its registration, wiring, test and release note are all in scope; cleanup and promotion are carried or declined above.

## Required tests / validation

New `tests/test_check_engine_source_test_citation.py` (behavioral cases enumerated in E-05) including the discriminating negatives for the retirement exemption (cases 4 and 3-neutered), the exempt-before-dedup ordering (6b), and the advisory proof (registry severity plus the `drift_exit_code` contrastive pair, 9/9b); `tests/test_severity_tier_contract.py` continues to pass with the new registry entry; bare full suite with no new failed node ids; `aw check all` exit code unchanged and only the new rule's count moved; the new scan itself under one second; `aw sanitize --agent` passes.

## Spec / documentation sync

N/A for specs, with reason: F-06 measured that the sibling `check.test-citation-dangling` appears only in `check_engine.py` and its test; the specs that DO name rule ids (for example the attention-registry spec) name their own domain's rules and enumerate no catalog this rule must join, and `docs/cli-output-contract.md` describes the severity tiers generically (its `info` worked example is `check.plan-date-filename-mismatch`) without listing every rule. So `- Scope-Paths:` declares no `.spec.md` and no doc. Documentation: one CHANGELOG bullet (E-06).

## Open questions

### OQ-01: Severity at birth: `info`, `warning`, or `error`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `info`. The backlog item sequences the rule after baseline cleanup, and F-02 measured 110 live dangling citations, so `error` or `warning` (both drive a nonzero exit per `artifact_core.drift_exit_code`) would break `aw check all` for every user today. `info` makes regressions visible now and becomes `error` by a one-line change later.

### OQ-02: How is a deliberate historical mention exempted?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: By content, not by a hand-maintained allowlist: a citation inside a sentence saying it was deleted/retired/removed together with a commit hash. This is the wording sibling cleanup plans (`65d5zf`, `dtelfb`) already write, so their output is silent by construction, and requiring the hash keeps a bare "removed" from laundering a live pointer (E-05 case 4). A tiny placeholder frozenset covers illustrative names measured in the tree.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git rev-parse --short HEAD`, the measurement script and its printed partition and live-pair count, the bare `python3 -m pytest` summary line and FAILED node-id set with a statement that no flags were added, the `aw check all --agent` exit code and per-rule diagnostic counts, and the `time aw check all` output; any drift from F-02 stated and attributed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the registry entry and comment quoted from `git diff agent_workflows/check_engine.py`, and the pasted `python3 -c ...` output printing `info`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the new function and exemption constants quoted from the diff; pasted output of a one-liner calling `check_engine.check_source_test_citations` on the live repo printing the finding count, the set of rule ids (exactly one), the set of severities (exactly `{'info'}`), and three sample locations; the count EQUALS E-01's live-pair count (both re-derived at execution HEAD); any inequality is explained per pair or treated as a defect in E-03.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the `check_types` hunk quoted from the diff showing its own `try/except`; pasted `aw check all --agent` lines containing `check.source-test-citation-dangling`; pasted per-rule diagnostic counts before (E-01) and after showing the new rule id as the only id whose count moved (or the movement of any other id explained by a named intervening commit); pasted exit codes before and after, which are equal. Observation produced by `check_engine.check_types` via the `aw check all` CLI path created in E-04.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -m pytest tests/test_check_engine_source_test_citation.py -o addopts="" -v` output showing every E-05 case passing, including (6b), (9) and (9b); pasted output of the same run with the retirement exemption locally neutered showing case (3) FAILING, and with deduplication moved before the exemption showing case (6b) FAILING, followed by `git diff --stat agent_workflows/check_engine.py` proving the neutering was reverted; and a statement, checkable in the diff, that the test file contains no `inspect`, `ast`, or read of `check_engine.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `git diff CHANGELOG.md` showing exactly one added bullet, and the pasted empty output of the dash grep over it.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted bare `python3 -m pytest` summary line and FAILED node-id set compared with V-01's (no new failure, or a re-run-alone result for any post-only failure); pasted `aw check all` exit code compared with V-01's; pasted `perf_counter` timing of `check_source_test_citations` on the live repo under 1s, with the end-to-end `time aw check all` output as context; pasted `aw sanitize --agent` result record showing `pass`; `git diff --cached --name-only` before commit listing only the three Scope-Paths plus this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

The plan must not execute before explicit human approval recorded through `aw ipd set approved`.

EXECUTION CONTRACT. Commit only the declared paths through `aw commit <plan> -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push. Verify the staged set with `git diff --cached --name-only` before committing. Paste actual command output for every measurement and suite claim. STOP conditions: E-04 changes the `aw check all` exit code or E-05 case (9) shows a nonzero `drift_exit_code` (the rule must be advisory), or E-07 shows a new suite failure attributable to this change. Scope fence: `- Scope-Paths:` is a declaration, not a stop rule; an edit outside it is made and then justified to `aw ipd finalize` with `--scope-reason`.

POST-GATE LIFECYCLE MOVE. After every `V-*` passes with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition is tooled: under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan or hand-edit `- Status:`. Backlog `j7daih` moves to `done` only after this plan is executed.
