# IPD: Delete the research INDEX writers and the research archive refresh

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 4.5 says the SQLite cache replaces the `INDEX.{json,md}` files. After the `q6epwc` family nothing calls the research INDEX write path, yet `research_index.build_index_json`, `research_index.build_index_md`, `research_index._set_last_touched`, `research_index.DEFAULT_INDEX_LIMIT`, the write path of `research_index.run_index`, and the post-move refresh in `research_archive.apply_moves` remain. This is part 5 of the round-3 split of `snin8q` (Order 42), carrying the research subset of `snin8q` E-03.
- Scope: delete those research symbols, the post-move refresh, and the `research_index` entry of `record_producers`; keep `research_index._scan_docs`, `query`, `run_find` and the non-INDEX rules of `research_index.check_drift`; retarget the INDEX-byte cases of `tests/test_research_index.py`. EXCLUDES the plans and prompts writers (Orders 233 and 235), the shared `artifact_core.emit_index_*` helpers (`snin8q`), and the `research_archive` skip of `INDEX.md` during scans (cutover, `cxxmyv`).
- Scope-Paths: agent_workflows/research_index.py, agent_workflows/research_archive.py, agent_workflows/record_producers.py, tests/test_research_index.py, .aw/records/plans/pending/20261109-metastore-234-s6k01k-delete-the-research-index-writers-and-the-research-archive-r.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:54a80m, executed:59aiyh, executed:6966zq, executed:dcerjg, executed:f6y2yy, executed:ffceq0, executed:g5hpbb, executed:q6epwc, executed:t4gl15, executed:uopi8z
- Status: approved
- Review-Depth: standard
- Readiness: go-pending-approval
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 234
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: s6k01k
- Approval: 2026-11-16, recorded via aw ipd set: status set to approved

> Reviewed and proofread per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md`, including requirement 12 (diagrams).

## Workflow history
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): /plan-review (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004.
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from snin8q (round 3, research nj8zdp guidance).

## Goal

After this plan, no research code can write an INDEX file, while `aw find research` and `aw check research --all` behave as in the `54a80m` baseline.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

`snin8q` E-03's site list is split across Orders 231 to 235 and `snin8q`; this plan takes the research members: `build_index_json`, `build_index_md`, `_set_last_touched`, the write path of `run_index` and `DEFAULT_INDEX_LIMIT` in `research_index`; "the post-move refresh in `research_archive`"; the `research_index` entry in `record_producers`; and `tests/test_research_index.py`. Keep the non-INDEX drift classes of `research_index.check_drift` (`q6epwc` F-04).

PIN RULE (carried from `9o83cr`): before the edit, create directory `mkdir -p .aw/state/s6k01k/` and save the module's per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA tests/test_research_index.py | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/s6k01k/<E>-before.txt`); after it, the same into `<E>-after.txt`. A retargeted test keeps every input case; a test whose only subject is a deleted INDEX writer is deleted and named "INDEX-byte-only" in the mapping.

### Task group 1: pin, delete, retarget

- [ ] E-01 Ensure `.aw/state/s6k01k/` exists (`mkdir -p .aw/state/s6k01k/`) and pin `tests/test_research_index.py` (PIN RULE, `E-01-before.txt`).
  - Depends on: none
  - Expected outcome: `.aw/state/s6k01k/E-01-before.txt` exists.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/research_index.py`, delete `research_index.build_index_json`, `research_index.build_index_md`, `research_index._set_last_touched` and `research_index.DEFAULT_INDEX_LIMIT`; drop the `limit` parameter and INDEX-comparison block of `research_index.check_drift`; delete `research_index.run_index` (replaced by `meta_cli.index_alias`). Keep `INDEX_MD` only while `research_archive` still names it in its scan skip.
  - Depends on: E-01
  - Expected outcome: `rg -n "build_index_(json|md)|_set_last_touched|DEFAULT_INDEX_LIMIT|def run_index" agent_workflows/research_index.py` prints nothing.
  - Execution state: pending

- [ ] E-03 In `research_archive.apply_moves`, delete the "Refresh the index after the moves" block that writes `RI.INDEX_JSON` and `RI.INDEX_MD`, and rewrite the module docstring bullet "an INDEX refresh after any archival move" and the two comments that describe the regenerated INDEX.
  - Depends on: E-02
  - Expected outcome: `rg -n "build_index|INDEX_JSON|INDEX refresh" agent_workflows/research_archive.py` prints nothing.
  - Execution state: pending

- [ ] E-04 In `agent_workflows/record_producers.py`, delete the `RecordProducerEntry` named `research_index` (anchor `run_index`).
  - Depends on: E-02
  - Expected outcome: `rg -n "name=\"research_index\"" agent_workflows/record_producers.py` prints nothing; `tests/test_record_producers.py` passes.
  - Execution state: pending

- [ ] E-05 In `tests/test_research_index.py`, delete the INDEX-byte-only cases (`test_index_md_archive_excluded_reference_included_intake_shown`, `test_n_honored`, `test_determinism`, `test_clean_after_regen`, `test_run_index_change_detection_and_output`, `test_default_is_40`, and the `run_index` render cases), retarget `test_json_contains_every_doc` and `test_docentry_and_json_carry_consumed_by` to the scan entries, and remove the INDEX-writing fixture from the drift cases (`test_invalid_frontmatter_detected`, `test_dangling_citation_detected`, `test_manifest_regeneration_not_blocked_by_tier_mismatch`). Save `E-05-after.txt`, run `tests/test_research_index.py` and `tests/test_record_producers.py`, and commit through `aw commit s6k01k -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-03, E-04
  - Expected outcome: both modules pass; the mapping names every removed case.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `check_engine.check_content` calls `research_index.check_drift` on the `--all` path.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `3d0ddb845`: `rg -n "build_index_(json|md)|_set_last_touched|DEFAULT_INDEX_LIMIT|def run_index" agent_workflows/research_index.py` prints 12 lines; `research_archive.apply_moves` writes `RI.INDEX_JSON`/`RI.INDEX_MD` after the moves; `tests/test_research_index.py` calls `build_index_*` 17 times, `run_index` 4 times, `DEFAULT_INDEX_LIMIT` once.

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["1. Pin baseline test outcomes (E-01)<br/>tests/test_research_index.py"]
    E02["2. Delete research INDEX writers (E-02)<br/>agent_workflows/research_index.py"]
    E03["3. Delete archive refresh (E-03)<br/>agent_workflows/research_archive.py"]
    E04["4. Delete producer entry (E-04)<br/>agent_workflows/record_producers.py"]
    E05["5. Retarget tests, verify & commit (E-05)<br/>tests/, aw commit"]

    E01 --> E02
    E02 --> E03
    E02 --> E04
    E03 --> E05
    E04 --> E05
```

1. Pin (E-01).
2. Delete the research writers (E-02), the archive refresh (E-03), the producer entry (E-04).
3. Retarget and commit (E-05).

## Deferred / out of scope (with reason)

- `artifact_core.emit_index_*`: deleted by `snin8q` once all three `run_index` functions are gone.
  - Carrier: snin8q
- The `research_archive` scan skip of `INDEX.md`: protects unmigrated repositories until `m0001` deletes the files.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 5 E-items, 4 work Scope-Paths.

## Required tests / validation

`tests/test_research_index.py` (pinned, retargeted) and `tests/test_record_producers.py`, then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.5.

## Open questions

### OQ-01: Does `aw archive research` still report its moves without the refresh?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. The regenerated INDEX was deliberately never appended to `touched` (comment citing idxuntrack `4r0qp1` E-07), so the reported move list is unchanged. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `wc -l .aw/state/s6k01k/E-01-before.txt` and its first three lines.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "build_index_(json|md)|_set_last_touched|DEFAULT_INDEX_LIMIT|def run_index" agent_workflows/research_index.py` printing nothing, and `aw check research --all --agent` rule-id multiset beside the `54a80m` F-29 research multiset, equal.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "build_index|INDEX_JSON|INDEX refresh" agent_workflows/research_archive.py` printing nothing, and a fixture `aw archive research --apply` followed by `ls .aw/records/research/INDEX.*` showing no such file. Code path: `research_archive.apply_moves` (E-03).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `rg -n "name=\"research_index\"" agent_workflows/record_producers.py` printing nothing and `python3 -m pytest -o addopts="" tests/test_record_producers.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `diff .aw/state/s6k01k/E-01-before.txt .aw/state/s6k01k/E-05-after.txt` with each removed name mapped or named "INDEX-byte-only", `python3 -m pytest -o addopts="" -v tests/test_research_index.py` showing the three named drift cases PASSED, and `git show --stat` of the `aw commit s6k01k` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed (Order 233 first, because both edit `agent_workflows/record_producers.py`; serial order keeps each diff small). Pin-first. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Safety stop: if a prerequisite plan in `- Item-Dependencies:` is not executed or required metastore symbols from `f6y2yy`, `6966zq`, or `uopi8z` are absent, stop and report rather than proceeding. Honesty rule: paste the ACTUAL summary lines. Commits: only through `aw commit s6k01k -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize s6k01k` itself.
