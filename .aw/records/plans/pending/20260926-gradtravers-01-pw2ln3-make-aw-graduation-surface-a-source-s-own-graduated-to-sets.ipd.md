# IPD: Make aw graduation surface a source's own Graduated-To Sets through one shared plan-setid sweep

- Date: 2026-09-26
- Kind: child
- Concern: `aw graduation <source-id6>` answers only from the REVERSE index (`check_engine.build_graduation_reverse_index`, keyed on `From-Backlog`/`From-Spec` bullets), while the FORWARD link a source carries (`- Graduated-To: <setid>`) is read only by `releases.check_graduated_to`, which builds its own plan-setid set with a private `_iter_plan_ipds` + `_parse_setid` sweep. The two traversals of one relationship never meet (orchestrator `y9s4vm` CID-7's obligation, missed by `bwgyum`). It is now user-visible: 102 records declare `- Graduated-To:`, and 40 of the 97 graduated backlog items get "nothing yet: no plan or spec links to source ... Proceed." Measured at HEAD `f46b6775`: `aw graduation cfgj8s` says Proceed, though `cfgj8s` carries `- Graduated-To: envhermet` and `envhermet` is a real plan Set. The verb exists to prevent duplicate graduation, so "Proceed" on an already-graduated source is the wrong answer in the one place it costs most.
- Scope: IN: (a) factor the plan-setid sweep out of `releases.check_graduated_to` into ONE `check_engine` helper returning `setid -> [plan artifacts]`, and reroute `check_graduated_to` to consume it (its live findings must stay 0 and its resolution semantics, "ANY setid carried by at least one plan file in ANY lifecycle directory", unchanged); (b) make `check_engine.graduation_cluster` also read the SOURCE's own `Graduated-To` (via `releases.parse_graduated_to`) and return those Sets and their plans as FORWARD links, labelled distinctly from the reverse `From-*` links; (c) make `cli._run_graduation`'s human, `--json` and `--agent` outputs report forward links, so a source with only a forward link no longer gets "Proceed"; (d) make `runner_shared.summarize_graduation_cluster` stop saying "nothing yet links" for such a source; (e) behavioral tests. OUT: substituting the reverse index for the setid sweep (measured wrong, see F-4); unifying the two relationships into one store (spec `4sd62s` does that by construction); any new `aw check` rule; changing `GRADUATION_VIEW_LIMITS` verdicts.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/releases.py, agent_workflows/cli.py, agent_workflows/runner_shared.py, tests/test_graduation_forward_links.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: knvpiv
- Blocks-Release: next
- Set: gradtravers
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: pw2ln3

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog knvpiv (reclassified bug + Blocks-Release next on 2026-09-26). Re-measured at HEAD f46b6775: 102 records declare Graduated-To; 40 of 97 graduated backlog items have a forward link and an empty reverse cluster; aw graduation cfgj8s prints Proceed; check_graduated_to returns 0 findings; the plan-setid sweep sees 401 setids and includes envhermet.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`aw graduation` reports what a source already graduated to whichever direction the link was written in, and the forward check and the view read the plan-Set universe from one shared sweep, so the two cannot drift again before spec `4sd62s` replaces both.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline

- [ ] E-01 RE-MEASURE at the executing HEAD and save to `/tmp/opencode/gradtravers-baseline/`: (a) `aw graduation cfgj8s` output and exit code; (b) the count of records carrying `- Graduated-To:` and the count of graduated backlog items whose `releases.parse_graduated_to` is non-empty while `check_engine.graduation_cluster(...).artifact_count == 0` (build the reverse index once and pass `index=`); (c) `len(releases.check_graduated_to(repo))` and the sorted list of its findings; (d) the size of the plan-setid set `check_graduated_to` builds; (e) `aw graduation <id6> --json` for one source WITH reverse links (for example `25kzda`), saved for E-06's byte comparison of the reverse fields.
  - Depends on: none
  - Expected outcome: (a) prints "nothing yet ... Proceed."; (b) about 102 and about 40; (c) 0; (d) about 401. Record the numbers observed.
  - Execution state: pending

### Task group 2: one sweep

- [ ] E-02 ADD `check_engine.build_plan_setid_index(repo_root) -> Dict[str, List[GraduationArtifact]]`: one pass over `_iter_plan_ipds`, reading each plan's `_parse_setid`, `_read_declared_id`, `_PLAN_STATUS_RE` status and repo-relative path exactly as `build_graduation_reverse_index` does for its records, keyed by terse setid, with every plan in every lifecycle directory included. Reuse `GraduationArtifact` (artifact_type `"plan"`). Document that this is the plan-Set UNIVERSE (every setid on any plan) and is deliberately NOT the reverse index, which indexes only artifacts carrying a `From-*` bullet (F-4).
  - Depends on: E-01
  - Expected outcome: `set(build_plan_setid_index(repo))` equals the `known_setids` set E-01 (d) measured.
  - Execution state: pending

- [ ] E-03 REROUTE `releases.check_graduated_to` to take its `known_setids` from `set(check_engine.build_plan_setid_index(repo_root))` (keeping the existing local import to avoid the cycle), deleting its private `_iter_plan_ipds` + `_parse_setid` loop. Keep every other line: the empty-corpus fail-safe, the three rules, the `rglob` over `backlog`/`specs`/`plans`, the skip list, and the docstring's resolution semantics (update only the sentence naming how the setid set is built). Add an optional keyword `plan_setids: Optional[Dict[str, ...]] = None` so a caller that already built the index can inject it, mirroring `graduation_cluster`'s `index=` parameter.
  - Depends on: E-02
  - Expected outcome: `check_graduated_to(repo)` on the live tree returns the same findings as E-01 (c) (0 today).
  - Execution state: pending

### Task group 3: forward links in the view

- [ ] E-04 EXTEND `check_engine.graduation_cluster` with the forward direction. Add fields to `GraduationCluster`: `forward_setids: Tuple[str, ...]` (the source's `Graduated-To` entries, in written order, via `releases.parse_graduated_to`) and `forward_artifacts: Tuple[GraduationArtifact, ...]` (the plans of those Sets from `build_plan_setid_index`, path-sorted), plus a property `forward_unresolved` (entries naming no plan Set). Locate the source by id6 with `selectors.resolve(repo_root, t, source_id6)` for `t` in `backlog`, `specs` (restricted to the kinds `source_kind` allows; kind `id6` matches only), reading its text once. Add optional `plan_setids=` injection like `index=`. Keep `artifacts`/`setids`/`artifact_count`/`terminal_artifacts` MEANING UNCHANGED (reverse links only), so existing consumers do not silently change; add `forward_count` and `has_any_link` (`artifact_count or forward_setids`). Deduplicate nothing across the two directions in the data: a plan reached both ways appears in both tuples, which is the agreement signal E-06 tests.
  - Depends on: E-02
  - Expected outcome: for `cfgj8s`, `forward_setids == ("envhermet",)`, `forward_artifacts` lists the `envhermet` plans, `artifact_count == 0`, `has_any_link` True.
  - Execution state: pending

- [ ] E-05 RENDER THE FORWARD LINKS. In `cli._run_graduation`: (1) take the "nothing yet ... Proceed." branch only when `not cluster.has_any_link`; (2) when forward links exist, print a second table headed `Forward links (this source's Graduated-To)` with the same columns, list any `forward_unresolved` entries as `names no plan Set`, and list the forward terminal members in the ALREADY LANDED line; (3) change the summary to count both directions; (4) add `forward_setids`, `forward_artifacts`, `forward_unresolved` to `data`, and a `graduation-forward` `Evidence` item (count and setids) so `--agent`, which drops `data`, still carries it; (5) extend `GRADUATION_VIEW_COVERAGE` to say the view now also reads the source's own `- Graduated-To:` field. In `runner_shared.summarize_graduation_cluster`, use `has_any_link` for the "nothing yet" branch and name forward Sets in the non-empty line. Keep the reverse-link output byte-identical for a source with no `Graduated-To`.
  - Depends on: E-04
  - Expected outcome: `aw graduation cfgj8s` no longer says Proceed and names `envhermet` with its plans; `aw graduation 25kzda --json` reverse fields equal E-01 (e).
  - Execution state: pending

### Task group 4: prove it

- [ ] E-06 ADD `tests/test_graduation_forward_links.py` on a temp repo (`.aw/records/{backlog,plans,specs}`), driving real functions and the real CLI (`cli.main([...,"--dir",tmp])`, capturing stdout, and `--json`): (1) FORWARD-ONLY FIXTURE: a graduated backlog item `- Graduated-To: fwdset` and two plans in Set `fwdset` with no `From-Backlog`; assert `graduation_cluster` reports both plans as forward artifacts, and the human output does NOT contain "Proceed" and does name `fwdset`; (2) REVERSE-ONLY: a plan with `From-Backlog: <item>` and no `Graduated-To` on the item: reverse artifacts as before, forward empty, output unchanged in shape; (3) AGREEMENT BOTH DIRECTIONS: a source with `Graduated-To: bothset` and a plan in `bothset` carrying `From-Backlog: <source>`: the plan appears in BOTH `artifacts` and `forward_artifacts`, and `set(cluster.setids) == set(cluster.forward_setids)`; (4) DISAGREEMENT VISIBLE: `Graduated-To: nosuchset` -> listed in `forward_unresolved` and printed as naming no plan Set, and `check_graduated_to` on the same fixture reports `check.graduated-to-dangling` (the view and the check agree); (5) SWEEP IDENTITY: `set(build_plan_setid_index(tmp))` equals every setid on the fixture's plans, including one in `executed/`, and `check_graduated_to` does NOT flag a link to a Set whose only plan is executed; (6) no source at all: "nothing yet ... Proceed." still printed (the affirmative zero answer is kept); (7) `--agent` output contains the `graduation-forward` evidence key for case (1). No test reads source text.
  - Depends on: E-03, E-05
  - Expected outcome: all pass after; (1), (3)'s forward half, (4)'s view half and (7) FAIL against the pre-change code; (2), (5) and (6) pass before and after.
  - Execution state: pending

- [ ] E-07 RE-RUN E-01 (a)-(e) and the bare suite `python3 -m pytest` before and after, comparing failing node IDs.
  - Depends on: E-06
  - Expected outcome: (a) names `envhermet` and no Proceed; (b) the forward-only-and-reverse-empty count is unchanged in the data but none of those sources now prints Proceed (re-count with `has_any_link`, expect 0 of them unlinked); (c) findings identical; (d) identical; (e) reverse fields identical; after-minus-before failing node set empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The reverse index is `check_engine.build_graduation_reverse_index` (graduate `jxxec8`), consumed by `graduation_cluster`, `cli._run_graduation`, and `runner_shared.summarize_graduation_cluster`; those three are the only consumers (grep of `graduation_cluster` across `agent_workflows/`).
- The forward check is `releases.check_graduated_to` (setidhard `bwgyum`), run once per full sweep from `check_engine`'s `collisions` seam; its docstring pins "ANY setid carried by at least one plan file in ANY lifecycle directory" and "THE RESOLUTION IS PLANS-ONLY AND MUST STAY THAT WAY (spec `2lcqno` N3)". E-02's helper is plans-only for that reason.
- `releases` imports `check_engine` LAZILY inside `check_graduated_to` to avoid an import cycle; E-03 keeps that shape, and E-04 imports `releases.parse_graduated_to` lazily inside `graduation_cluster` for the same reason.
- `graduation_cluster` already accepts an injected `index=`; E-03/E-04's `plan_setids=` follows that precedent.
- The view "DECIDES NOTHING" and applies no `count > 1` judgement (`cli._run_graduation` docstring); forward links are reported the same way.
- `--agent` drops `data` by design (`CommandResult.to_agent_record`), which is why E-05 adds an `Evidence` item.
- Test policy (maintainer ruling 2026-09-26): behavioral tests only; no source-text or AST pins (the backlog item's "introspection" evidence is not a test to write). Bare `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `f46b6775`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `cli._run_graduation` | Says "Proceed" for a source that already graduated via a forward link. | `aw graduation cfgj8s` -> "nothing yet: no plan or spec links to source cfgj8s. Proceed."; `cfgj8s` item carries `- Graduated-To: envhermet` |
| F-2 | HIGH | population | The wrong answer is common, not an edge case. | 102 files under `.aw/records` carry `^- Graduated-To:`; of 97 graduated backlog items, 40 have a non-empty `parse_graduated_to` and a zero reverse cluster |
| F-3 | MEDIUM | `releases.check_graduated_to` | Builds its own plan-setid set with a private `_iter_plan_ipds` + `_parse_setid` loop; nothing shares it. | the `known_setids` loop in `check_graduated_to`; `graduation_cluster` never reads `Graduated-To` |
| F-4 | HIGH | design constraint | The reverse index is NOT a valid resolution target for the forward check: it indexes only artifacts carrying a `From-*` bullet. | backlog `knvpiv`: 124 setids in the reverse index vs 328 in the sweep at `0823163b`; at `f46b6775` the sweep sees 401 |
| F-5 | INFO | control | The forward check is clean on the live tree, so E-03 has a fixed target. | `len(check_graduated_to(repo))` -> 0; `envhermet` in the sweep's setid set |

## Proposed changes (ordered, validatable)

1. E-01 baseline.
2. E-02 one `build_plan_setid_index` sweep.
3. E-03 `check_graduated_to` consumes it, findings unchanged.
4. E-04 `graduation_cluster` adds forward links.
5. E-05 the CLI and runner advisory render them.
6. E-06 behavioral tests; E-07 re-measure and bare suite.

## Deferred / out of scope (with reason)

- One store answering both directions by construction.
  - Carrier-Declined: owned by spec 4sd62s (graduated-to, from-backlog and from-spec become log fields in one store, unifying both directions by construction); a spec is not an accepted carrier type.
- Reading `Graduated-To` on SPECS as sources: the field is legal there and E-04 resolves spec sources too, but 0 specs carry it today, so no live output changes; nothing further is deferred.
  - Carrier-Declined: covered by E-04's `specs` resolution; no outstanding work.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/command_surface.py` is not declared: the `graduation` leaf's declaration does not change (same read leaf, same shared empty-result renderer).
- Scope-Paths justification: `check_engine.py` (sweep, cluster), `releases.py` (reroute), `cli.py` (render), `runner_shared.py` (advisory line), new test file.

## Required tests / validation

- `tests/test_graduation_forward_links.py` (new), cases (1)-(7) with the stated pre-change failures.
- Live re-measurement and bare `python3 -m pytest` in E-07.

## Spec / documentation sync

- No spec is amended and none is in `- Scope-Paths:`. Spec `2lcqno` N3 (plans-only resolution) is preserved by E-02 being plans-only. Spec `4sd62s` will subsume both traversals; `tests/test_graduation_forward_links.py` states the agreement behavior that rewrite must keep.
- `GRADUATION_VIEW_COVERAGE` is user-facing text rendered in the output; E-05 updates it so the view's statement of what it searched stays true.

## Open questions

### OQ-01: Fold forward plans into `artifacts`, or keep them separate?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: SEPARATE, from repository evidence. `GraduationCluster.artifacts` is documented as "every plan and spec citing it" (reverse), and `runner_shared.summarize_graduation_cluster` reports `artifact_count` as "linked artifact(s)"; silently widening those would change two consumers' meaning. Keeping the directions apart also makes the agreement test (E-06 (3)) and a disagreement visible, which is the point of backlog `knvpiv`.

### OQ-02: Should the reverse index itself start reading `Graduated-To`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO. The reverse index is keyed on what ARTIFACTS say about a source; `Graduated-To` is what the SOURCE says about a Set. Mixing them in one index would reintroduce the resolution confusion F-4 measured. The maintainer's brief for this plan (2026-09-26) also says not to substitute the reverse index for the setid sweep.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste E-01 (a)-(d) values and the path of the saved (e) JSON.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `build_plan_setid_index` diff and a one-liner printing `len(set(index))` and whether it equals E-01 (d)'s set (print the symmetric difference, which must be empty).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `check_graduated_to` diff showing the private loop removed; paste `len(check_graduated_to(repo))` and the sorted findings, identical to E-01 (c).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `graduation_cluster` / `GraduationCluster` diff and `graduation_cluster(repo, "cfgj8s")` printing `forward_setids`, `forward_count`, `artifact_count`, `has_any_link`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `aw graduation cfgj8s` (human) showing the forward table and no "Proceed", `aw graduation cfgj8s --agent` showing the `graduation-forward` evidence, and a diff of `aw graduation 25kzda --json`'s reverse fields against E-01 (e) (must be empty).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_graduation_forward_links.py -o addopts="" -q` passing; then with E-04/E-05 hunks reverted, showing (1), (3)'s forward half, (4)'s view half and (7) FAILING and (2), (5), (6) passing; then passing again.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste E-01 (a)-(e) re-run and the bare `python3 -m pytest` summary BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. `aw graduation` (and the runner's pre-graduation advisory line) start reporting a source's own `- Graduated-To:` Sets and their plans as forward links, so an already-graduated source no longer gets "Proceed". The forward check `aw check all` runs keeps identical findings but reads its plan-Set universe from one shared sweep. The existing reverse-link fields keep their meaning; forward links are added beside them. This is an interim fix; spec `4sd62s` later unifies both directions by construction. Graduates backlog `knvpiv` and inherits its `- Blocks-Release: next`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `check_engine.py` (`build_plan_setid_index`, `GraduationCluster`, `graduation_cluster`, `GRADUATION_VIEW_COVERAGE`), `releases.py` (`check_graduated_to` only), `cli.py` (`_run_graduation` only), `runner_shared.py` (`summarize_graduation_cluster` only), and the new test file. If an edit outside those paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-06 must show the forward-link tests FAILING before the change, and V-03 must show the live forward-check findings unchanged.

Commit ONLY through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize`. Then close backlog `knvpiv` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
