# IPD: Make aw graduation surface a source's own Graduated-To Sets through one shared plan-setid sweep

- Date: 2026-09-26
- Kind: child
- Concern: `aw graduation <source-id6>` answers only from the REVERSE index (`check_engine.build_graduation_reverse_index`, keyed on `From-Backlog`/`From-Spec` bullets), while the FORWARD link a source carries (`- Graduated-To: <setid>`) is read only by `releases.check_graduated_to`, which builds its own plan-setid set with a private `_iter_plan_ipds` + `_parse_setid` sweep. The two traversals of one relationship never meet (orchestrator `y9s4vm` CID-7's obligation, missed by `bwgyum`). It is now user-visible: 102 records declare `- Graduated-To:`, and 40 of the 97 graduated backlog items get "nothing yet: no plan or spec links to source ... Proceed." Measured at HEAD `f46b6775`: `aw graduation cfgj8s` says Proceed, though `cfgj8s` carries `- Graduated-To: envhermet` and `envhermet` is a real plan Set. The verb exists to prevent duplicate graduation, so "Proceed" on an already-graduated source is the wrong answer in the one place it costs most.
- Scope: IN: (a) factor the plan-setid sweep out of `releases.check_graduated_to` into ONE `check_engine` helper returning `setid -> [plan artifacts]`, and reroute `check_graduated_to` to consume it (its live findings must stay 0 and its resolution semantics, "ANY setid carried by at least one plan file in ANY lifecycle directory", unchanged); (b) make `check_engine.graduation_cluster` also read the SOURCE's own `Graduated-To` (via `releases.parse_graduated_to`) and return those Sets and their plans as FORWARD links, labelled distinctly from the reverse `From-*` links; (c) make `cli._run_graduation`'s human, `--json` and `--agent` outputs report forward links, so a source with only a forward link no longer gets "Proceed"; (d) make `runner_shared.summarize_graduation_cluster` stop saying "nothing yet links" for such a source; (e) behavioral tests. OUT: substituting the reverse index for the setid sweep (measured wrong, see F-4); unifying the two relationships into one store (spec `4sd62s` does that by construction); any new `aw check` rule; changing `GRADUATION_VIEW_LIMITS` verdicts.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/releases.py, agent_workflows/cli.py, agent_workflows/runner_shared.py, tests/test_graduation_forward_links.py
- Item-Dependencies: none
- Status: to-review
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: knvpiv
- Blocks-Release: next
- Set: gradtravers
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: pw2ln3

## Workflow history

- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-701..PR-709. Reviewed in an isolated lane worktree at HEAD 7cba3a3f. F-1/F-3/F-4/F-5 confirmed by re-measurement; every COUNT had drifted and is now restated as re-derive-at-execution (152 not 102 records, 422 not 401 setids, 111 not 97 graduated items; the 40 held). Three defects fixed: E-04 passes `spec` to `selectors.resolve`, which silently returns EMPTY (the type is `specs`), so spec sources would never resolve; E-05's dict-valued `Evidence` compacts to its KEY ALONE, dropping the count and setids it exists to carry, and E-06 case (7) asserted only the key so it could not detect that; and the plan claimed 0 specs carry `Graduated-To` when `z7nbn1` does, which is a live agreement case the two bugs together would have masked. E-04 also split per IPD-Z602.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog knvpiv (reclassified bug + Blocks-Release next on 2026-09-26). Re-measured at HEAD f46b6775: 102 records declare Graduated-To; 40 of 97 graduated backlog items have a forward link and an empty reverse cluster; aw graduation cfgj8s prints Proceed; check_graduated_to returns 0 findings; the plan-setid sweep sees 401 setids and includes envhermet.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`aw graduation` reports what a source already graduated to whichever direction the link was written in, and the forward check and the view read the plan-Set universe from one shared sweep, so the two cannot drift again before spec `4sd62s` replaces both.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline

- [ ] E-01 RE-MEASURE at the executing HEAD and save to `/tmp/opencode/gradtravers-baseline/`: (a) `aw graduation cfgj8s` output and exit code; (b) the count of records carrying `- Graduated-To:` and the count of graduated backlog items whose `releases.parse_graduated_to` is non-empty while `check_engine.graduation_cluster(...).artifact_count == 0` (build the reverse index once and pass `index=`); (c) `len(releases.check_graduated_to(repo))` and the sorted list of its findings; (d) the size of the plan-setid set `check_graduated_to` builds; (e) `aw graduation <id6> --json` for one source WITH reverse links (for example `25kzda`), saved for E-06's byte comparison of the reverse fields.
  - Depends on: none
  - Expected outcome: (a) prints "nothing yet ... Proceed."; (c) 0. THE COUNTS IN (b) AND (d) ARE LIVE-ARTIFACT POPULATIONS AND MUST BE RE-DERIVED, NEVER ASSERTED: they drift with every merge. Measured at authoring `f46b6775`: 102 records / ~40 / 401 setids. RE-MEASURED IN REVIEW at `7cba3a3f` days later: 152 records carrying `- Graduated-To:` (149 backlog + 1 spec + 0 plans, plus 2 outside `.aw/records`), 111 graduated backlog items of which 40 have a forward link and an empty reverse cluster, and 422 setids over 825 plans. So the required property is (b) a NON-ZERO forward-only-and-reverse-empty population and (d) a setid set CONTAINING `envhermet`, with the observed numbers recorded as context. Do not fail E-01 because a count moved; fail it only if the forward-only population is zero (the defect would then not reproduce) or `envhermet` is absent.
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

- [ ] E-04 LOCATE THE SOURCE AND READ ITS FORWARD FIELD. Add to `check_engine` a helper that, given `repo_root` and `source_id6`, finds the source record and returns its `releases.parse_graduated_to` entries in written order (lazy-import `releases` inside the function, per Step 0's cycle note). Resolve with `selectors.resolve(repo_root, t, source_id6)` for `t` in `("backlog", "specs")`, accepting only `Resolution.kind == "id6"`, and read the resolved text ONCE.
  USE THE RECORD-TYPE SPELLING, NOT THE GRADUATION KIND SPELLING. `GRADUATION_SOURCE_KINDS` is `("backlog", "spec")` (SINGULAR `spec`) while `selectors.KNOWN_PRIMARY_TYPES` uses `specs` (PLURAL). Measured in review: `selectors.resolve(repo, "spec", "<a real spec id6>")` returns an EMPTY `Resolution` with NO error, so passing the graduation kind straight through would make every spec source silently forward-linkless and the bug would look like the feature working. When `source_kind` is given, MAP it (`spec` -> `specs`) rather than forwarding it; assert the mapping in E-07.
  - Depends on: E-02
  - Expected outcome: the helper returns `["envhermet"]` for `cfgj8s` (a backlog source) and `["artdispatch"]` for `z7nbn1` (a SPEC source that really carries the field; see F-8), and `[]` for an id6 that resolves to neither.
  - Execution state: pending

- [ ] E-05 ADD THE FORWARD FIELDS TO THE CLUSTER. Extend `GraduationCluster` with `forward_setids: Tuple[str, ...]` (E-04's entries, written order) and `forward_artifacts: Tuple[GraduationArtifact, ...]` (the plans of those Sets from `build_plan_setid_index`, path-sorted), plus properties `forward_unresolved` (entries naming no plan Set), `forward_count`, and `has_any_link` (`artifact_count or forward_setids`). Wire them in `graduation_cluster` and add optional `plan_setids=` injection mirroring `index=`. Keep `artifacts`/`setids`/`artifact_count`/`terminal_artifacts` MEANING UNCHANGED (reverse links only), so the three existing consumers do not silently change. Deduplicate nothing across the two directions: a plan reached both ways appears in BOTH tuples, which is the agreement signal E-08 tests. NOTE `GraduationCluster` is a `NamedTuple`, so new FIELDS must carry defaults (`()`) to keep positional construction working, and a property named `count` is already forbidden for the reason its docstring gives; `forward_count` follows that precedent.
  - Depends on: E-04
  - Expected outcome: for `cfgj8s`, `forward_setids == ("envhermet",)`, `forward_artifacts` lists the 3 `envhermet` plans, `artifact_count == 0`, `has_any_link` True. For `z7nbn1`, BOTH directions are non-empty and `set(setids) == set(forward_setids) == {"artdispatch"}` (the live agreement case).
  - Execution state: pending

- [ ] E-06 RENDER THE FORWARD LINKS IN THE CLI. In `cli._run_graduation`: (1) take the "nothing yet ... Proceed." branch only when `not cluster.has_any_link`; (2) when forward links exist, print a second table headed `Forward links (this source's Graduated-To)` with the same columns, list any `forward_unresolved` entries as `names no plan Set`, and list the forward terminal members in the ALREADY LANDED line; (3) change the summary to count both directions; (4) add `forward_setids`, `forward_artifacts`, `forward_unresolved` to `data`, and a `graduation-forward` `Evidence` item so `--agent`, which drops `data`, still carries it; (5) extend `GRADUATION_VIEW_COVERAGE` to say the view now also reads the source's own `- Graduated-To:` field.
  THE EVIDENCE VALUE MUST BE A STRING (OR A SCALAR), NOT A DICT, and this is the one line most likely to be got wrong because the existing `graduation-cluster` item beside it uses a dict. Measured in review against `agent_schema.sanitize_evidence_item`: a dict-valued `Evidence` compacts to its KEY ALONE (`'graduation-forward'`), silently dropping the count and setids, which is exactly the data the item exists to carry past `--agent`'s `data` drop; only `int`/`float`/`bool` and a clean `str` survive as `key:value`. So emit something like `value=f"{n} Set(s): {', '.join(setids)}"`, which compacts to `graduation-forward:1 Set(s): envhermet`. (The pre-existing `graduation-cluster` item has the same latent flaw; it is NOT in this plan's scope to change, and no claim is made here that it is correct.)
  Keep the reverse-link output byte-identical for a source with no `Graduated-To`.
  - Depends on: E-05
  - Expected outcome: `aw graduation cfgj8s` no longer says Proceed and names `envhermet` with its plans; `aw graduation cfgj8s --agent` carries a `graduation-forward:<...>` evidence string whose VALUE names `envhermet`; `aw graduation 25kzda --json` reverse fields equal E-01 (e).
  - Execution state: pending

- [ ] E-07 UPDATE THE RUNNER ADVISORY. In `runner_shared.summarize_graduation_cluster`, use `has_any_link` for the "nothing yet links" branch and name the forward Sets in the non-empty line. Keep the function's contract intact: it returns TEXT, raises nothing, decides nothing, applies no `count > 1` judgement, and returns `''` on any exception or an unrecognizable root (its docstring states each, and the broad `except Exception: return ""` must keep covering the new read so a forward-link failure cannot turn into a failed run).
  - Depends on: E-05
  - Expected outcome: for a forward-only source the returned line no longer says "nothing yet links" and names the Set; for a source with neither direction it is unchanged; for an unreadable root it is still `''`.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-08 ADD `tests/test_graduation_forward_links.py` on a temp repo (`.aw/records/{backlog,plans,specs}`), driving real functions and the real CLI (`cli.main([...,"--dir",tmp])`, capturing stdout, and `--json`): (1) FORWARD-ONLY FIXTURE: a graduated backlog item `- Graduated-To: fwdset` and two plans in Set `fwdset` with no `From-Backlog`; assert `graduation_cluster` reports both plans as forward artifacts, and the human output does NOT contain "Proceed" and does name `fwdset`; (2) REVERSE-ONLY: a plan with `From-Backlog: <item>` and no `Graduated-To` on the item: reverse artifacts as before, forward empty, output unchanged in shape; (3) AGREEMENT BOTH DIRECTIONS: a source with `Graduated-To: bothset` and a plan in `bothset` carrying `From-Backlog: <source>`: the plan appears in BOTH `artifacts` and `forward_artifacts`, and `set(cluster.setids) == set(cluster.forward_setids)`; (4) DISAGREEMENT VISIBLE: `Graduated-To: nosuchset` -> listed in `forward_unresolved` and printed as naming no plan Set, and `check_graduated_to` on the same fixture reports `check.graduated-to-dangling` (the view and the check agree); (5) SWEEP IDENTITY: `set(build_plan_setid_index(tmp))` equals every setid on the fixture's plans, including one in `executed/`, and `check_graduated_to` does NOT flag a link to a Set whose only plan is executed; (6) no source at all: "nothing yet ... Proceed." still printed (the affirmative zero answer is kept); (7) `--agent` output contains the `graduation-forward` evidence key for case (1). No test reads source text.
  Two cases are REVISED because as authored they could not fail. CASE (7) MUST ASSERT THE EVIDENCE VALUE, NOT THE KEY: measured in review, a dict-valued `Evidence` compacts to the bare string `'graduation-forward'`, so an assertion that the `--agent` output "contains the `graduation-forward` evidence key" PASSES while the count and setids are gone; assert the compacted item equals/startswith `graduation-forward:` AND contains the setid. ADD CASE (8), THE SPEC SOURCE: a spec record declaring `- Id:` and `- Graduated-To: specset` plus a plan in `specset`, asserting its forward links resolve; this is the case E-04's `spec`-vs-`specs` mapping breaks, it FAILS if the graduation kind is forwarded unmapped, and it is not hypothetical (F-8: `z7nbn1` carries the field live). Drive it BOTH with `source_kind=None` and with `source_kind="spec"`, since only the second exercises the mapping.
  - Depends on: E-03, E-06, E-07
  - Expected outcome: all pass after; (1), (3)'s forward half, (4)'s view half, (7) and (8) FAIL against the pre-change code; (2), (5) and (6) pass before and after. Case (7) must also FAIL against a dict-valued Evidence implementation, and case (8)'s `source_kind="spec"` half must FAIL against an unmapped `selectors.resolve` call: those two counter-runs are what make the pair real rather than decorative.
  - Execution state: pending

- [ ] E-09 RE-RUN E-01 (a)-(e) and the bare suite `python3 -m pytest` before and after, comparing failing node IDs.
  - Depends on: E-08
  - Expected outcome: (a) names `envhermet` and no Proceed; (b) the forward-only population is unchanged in the DATA but none of those sources now prints Proceed (re-count with `has_any_link`, expect 0 of them unlinked); (c) findings identical; (d) the setid set identical; (e) reverse fields identical; `aw graduation z7nbn1` shows the same Set in BOTH directions (the live agreement case, F-8); the mapped-kind assertion from E-04 holds; after-minus-before failing node set empty against the review-measured baseline `2590 passed, 2 skipped`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The reverse index is `check_engine.build_graduation_reverse_index` (graduate `jxxec8`), consumed by `graduation_cluster`, `cli._run_graduation`, and `runner_shared.summarize_graduation_cluster`; those three are the only consumers (grep of `graduation_cluster` across `agent_workflows/`).
- The forward check is `releases.check_graduated_to` (setidhard `bwgyum`), run once per full sweep from `check_engine`'s `collisions` seam; its docstring pins "ANY setid carried by at least one plan file in ANY lifecycle directory" and "THE RESOLUTION IS PLANS-ONLY AND MUST STAY THAT WAY (spec `2lcqno` N3)". E-02's helper is plans-only for that reason.
- `releases` imports `check_engine` LAZILY inside `check_graduated_to` to avoid an import cycle; E-03 keeps that shape, and E-04 imports `releases.parse_graduated_to` lazily inside its source-lookup helper for the same reason.
- `graduation_cluster` already accepts an injected `index=`; E-03/E-05's `plan_setids=` follows that precedent.
- `selectors.resolve`'s record types are PLURAL (`specs`), while `GRADUATION_SOURCE_KINDS` is SINGULAR (`spec`), and an unknown type returns an empty `Resolution` rather than raising (F-6). Any new source lookup must map the kind, and no test that only exercises a BACKLOG source can detect the difference.
- `agent_schema.sanitize_evidence_item` preserves an `Evidence` value only when it is `int`/`float`/`bool` or a clean `str` (rendered `key:value`); ANY other value, including a dict, compacts to the bare `key` (F-7). So an `Evidence` item added to survive `--agent`'s `data` drop must carry a scalar or string value, and a test asserting only the key cannot tell the two apart.
- The view "DECIDES NOTHING" and applies no `count > 1` judgement (`cli._run_graduation` docstring); forward links are reported the same way.
- `--agent` drops `data` by design (`CommandResult.to_agent_record`), which is why E-06 adds an `Evidence` item.
- Test policy (maintainer ruling 2026-09-26): behavioral tests only; no source-text or AST pins (the backlog item's "introspection" evidence is not a test to write). Bare `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1..F-5 authored at HEAD `f46b6775` and re-measured in review at `7cba3a3f`. F-6..F-9 found in review at `7cba3a3f`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `cli._run_graduation` | Says "Proceed" for a source that already graduated via a forward link. CONFIRMED verbatim in review. | `aw graduation cfgj8s` -> "nothing yet: no plan or spec links to source cfgj8s. Proceed." (exit 0); `cfgj8s` item carries `- Graduated-To: envhermet` and `parse_graduated_to` returns `['envhermet']` |
| F-2 | HIGH | population | The wrong answer is common, not an edge case. THE COUNTS DRIFTED between authoring and review; the PROPERTY held. | Authored `f46b6775`: 102 records, 97 graduated items, 40 affected. Re-measured `7cba3a3f`: 152 records carry `^- Graduated-To:` (149 backlog, 1 spec, 0 plans), 111 graduated backlog items, and 40 of those have a non-empty `parse_graduated_to` with a zero reverse cluster. Treat as a live population to re-derive (E-01), never as a fixed bar |
| F-3 | MEDIUM | `releases.check_graduated_to` | Builds its own plan-setid set with a private `_iter_plan_ipds` + `_parse_setid` loop; nothing shares it. | the `known_setids` loop in `check_graduated_to`; `graduation_cluster` never reads `Graduated-To` |
| F-4 | HIGH | design constraint | The reverse index is NOT a valid resolution target for the forward check: it indexes only artifacts carrying a `From-*` bullet. CONFIRMED with a stronger measurement than the authored one: the reverse-index setid set is a STRICT SUBSET of the sweep's. | Re-measured `7cba3a3f`: 215 reverse-index setids vs 422 sweep setids; `sweep - reverse` = 207 entries, `reverse - sweep` = 0. Substituting the reverse index would make 207 real Sets unresolvable, i.e. mass false `check.graduated-to-dangling` |
| F-5 | INFO | control | The forward check is clean on the live tree, so E-03 has a fixed target. | `len(check_graduated_to(repo))` -> 0 (re-confirmed); `envhermet` in the sweep's setid set |
| F-6 | HIGH | E-04's source resolution | **THE GRADUATION KIND AND THE RECORD TYPE ARE SPELLED DIFFERENTLY, AND THE MISMATCH FAILS SILENTLY.** `GRADUATION_SOURCE_KINDS` is `("backlog", "spec")` (singular) while `selectors` uses `specs` (plural). `selectors.resolve(repo, "spec", <real spec id6>)` returns an EMPTY `Resolution` with no error, so forwarding the kind unmapped would make every spec source forward-linkless while looking like it worked. | `selectors.resolve(tmp,'specs','aa11bb').paths` -> non-empty; `selectors.resolve(tmp,'spec','aa11bb').paths` -> `[]`, no exception; `selectors.KNOWN_PRIMARY_TYPES` contains `specs`, not `spec` |
| F-7 | HIGH | the `--agent` Evidence item (now E-06) | **A DICT-VALUED `Evidence` COMPACTS TO ITS KEY ALONE, DROPPING THE VALUE,** so the item added specifically to survive `--agent`'s `data` drop would carry no count and no setids. `sanitize_evidence_item` returns `f"{key}:{val}"` only for `int`/`float`/`bool` or a clean `str`, and bare `key` otherwise. The authored test case (7) asserted only that the output "contains the key", which PASSES in exactly that broken state. | `sanitize_evidence_item(Evidence(key='graduation-forward', value={'count':1,'setids':['envhermet']}))` -> `'graduation-forward'`; with `value="1 Set(s): envhermet"` -> `'graduation-forward:1 Set(s): envhermet'`; live `aw graduation z7nbn1 --agent` evidence list is `['graduation-cluster', 'limit:...', ...]`, the first already value-less |
| F-8 | MEDIUM | the deferred row's premise | **A SPEC DOES CARRY `Graduated-To` TODAY, so the claim "0 specs carry it, so no live output changes" is false,** and it matters twice: it is the live proof that E-04's spec path is exercised, and combined with F-6 it would have MASKED the bug (spec sources silently unresolved, with the plan asserting no spec output was expected anyway). | `git grep -l "^- Graduated-To:" -- .aw/records/specs` -> `.aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md`, `- Graduated-To: artdispatch`, `- Status: implementing`; `artdispatch` IS in the plan-setid sweep; `graduation_cluster(repo,'z7nbn1')` already has 6 reverse artifacts in Set `artdispatch`, so it is a live BOTH-DIRECTIONS AGREEMENT case |
| F-9 | INFO | existing coverage | There is NO existing test for `graduation_cluster`, `check_graduated_to`, `summarize_graduation_cluster` or the `graduation` verb, so E-08 is the first coverage and a regression in the reverse path would be caught by nothing else. `tests/test_runner_shared.py` also cites a `tests/test_graduation_dispatch.py` that does not exist (noted, NOT in this plan's scope). | `grep -rln "graduation_cluster\|check_graduated_to\|summarize_graduation_cluster" tests/` -> no matches; `ls tests/test_graduation_dispatch.py` -> No such file |

## Proposed changes (ordered, validatable)

1. E-01 baseline (counts re-derived, not asserted).
2. E-02 one `build_plan_setid_index` sweep.
3. E-03 `check_graduated_to` consumes it, findings unchanged.
4. E-04 locate the source and read its `Graduated-To`, with the `spec` -> `specs` kind mapping.
5. E-05 `GraduationCluster` gains the forward fields.
6. E-06 the CLI renders them, with a STRING-valued `--agent` Evidence.
7. E-07 the runner advisory line.
8. E-08 behavioral tests (8 cases, two with counter-runs); E-09 re-measure and bare suite.

## Deferred / out of scope (with reason)

- One store answering both directions by construction.
  - Carrier-Declined: owned by spec 4sd62s (graduated-to, from-backlog and from-spec become log fields in one store, unifying both directions by construction); a spec is not an accepted carrier type.
- Reading `Graduated-To` on SPECS as sources: the field is legal there, E-04 resolves spec sources too, and CORRECTED IN REVIEW, one spec carries it TODAY (`z7nbn1` -> `artdispatch`, F-8), so there IS a live output change and it is a both-directions agreement case. Nothing further is deferred.
  - Carrier-Declined: covered by E-04's `specs` resolution (with the kind mapping F-6 requires) and asserted by E-08 case (8); no outstanding work.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/command_surface.py` is not declared: the `graduation` leaf's declaration does not change (same read leaf, same shared empty-result renderer). Verified in review: the leaf's only properties there are `command="graduation"` and the read/empty-renderer declaration, neither of which this plan touches.
- Scope-Paths justification: `check_engine.py` (sweep, cluster, source lookup), `releases.py` (reroute), `cli.py` (render), `runner_shared.py` (advisory line), new test file.
- `agent_workflows/agent_schema.py` and `result_types.py` are NOT declared and must NOT be edited. F-7 is a property of `sanitize_evidence_item`'s existing contract; this plan complies with it by emitting a STRING value, and does not change the compaction rule. The pre-existing `graduation-cluster` Evidence item has the same latent value-loss and is deliberately left alone: changing it would alter a shipped `--agent` record outside this plan's concern.
- `selectors.py` is NOT declared. F-6's silent-empty behavior is consumed as-is and worked around by mapping the kind at the call site; no claim is made here that returning an empty `Resolution` for an unknown record type is the right design.
- `GRADUATION_SOURCE_KINDS`' spelling is NOT changed. Renaming `spec` -> `specs` there would touch `build_graduation_reverse_index`'s keys and every reverse consumer, which is a far larger change than this plan's concern; the mapping lives at the one new call site instead.

## Required tests / validation

- `tests/test_graduation_forward_links.py` (new), cases (1)-(8) with the stated pre-change failures, plus the two counter-runs in V-08.
- Live re-measurement and bare `python3 -m pytest` in E-09 (review baseline `2590 passed, 2 skipped`).
- THIS IS THE FIRST TEST COVERAGE THESE FUNCTIONS HAVE EVER HAD (F-9): no existing test names `graduation_cluster`, `check_graduated_to`, `summarize_graduation_cluster` or the `graduation` verb. So a regression in the REVERSE path would be caught by nothing but case (2), which makes case (2) load-bearing despite passing both before and after, and makes V-03's unchanged-findings check the only guard on `check_graduated_to`'s behavior.

## Spec / documentation sync

- No spec is amended and none is in `- Scope-Paths:`. Spec `2lcqno` N3 (plans-only resolution) is preserved by E-02 being plans-only. Spec `4sd62s` will subsume both traversals; `tests/test_graduation_forward_links.py` states the agreement behavior that rewrite must keep.
- `GRADUATION_VIEW_COVERAGE` is user-facing text rendered in the output; E-06 updates it so the view's statement of what it searched stays true.

## Open questions

### OQ-01: Fold forward plans into `artifacts`, or keep them separate?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: SEPARATE, from repository evidence. `GraduationCluster.artifacts` is documented as "every plan and spec citing it" (reverse), and `runner_shared.summarize_graduation_cluster` reports `artifact_count` as "linked artifact(s)"; silently widening those would change two consumers' meaning. Keeping the directions apart also makes the agreement test (E-08 case (3)) and a disagreement visible, which is the point of backlog `knvpiv`.

### OQ-02: Should the reverse index itself start reading `Graduated-To`?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO. The reverse index is keyed on what ARTIFACTS say about a source; `Graduated-To` is what the SOURCE says about a Set. Mixing them in one index would reintroduce the resolution confusion F-4 measured. The maintainer's brief for this plan (2026-09-26) also says not to substitute the reverse index for the setid sweep.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste E-01 (a)-(d) values and the path of the saved (e) JSON. State the observed counts as OBSERVED, and confirm the two required PROPERTIES rather than the authored numbers: the forward-only-and-reverse-empty population is non-zero, and `envhermet` is in the setid set. If a count differs from both the authored (`f46b6775`) and review (`7cba3a3f`) figures, that is expected drift, not a failure.
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
  - Required evidence: paste the source-lookup helper's diff and its return value for THREE inputs: `cfgj8s` (backlog) -> `["envhermet"]`, `z7nbn1` (SPEC) -> `["artdispatch"]`, and an id6 resolving to neither -> `[]`. Paste the resolved record PATH for `z7nbn1` proving the specs tree was actually read, and paste the kind-mapping evidence: the value passed to `selectors.resolve` when `source_kind="spec"` must be `"specs"`. A V-04 that shows only the backlog case does NOT satisfy this item, because the spec case is the one F-6 breaks.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `GraduationCluster` / `graduation_cluster` diff and `graduation_cluster(repo, "cfgj8s")` printing `forward_setids`, `forward_count`, `artifact_count`, `has_any_link`; plus `graduation_cluster(repo, "z7nbn1")` showing BOTH directions non-empty with `set(setids) == set(forward_setids)`. Also paste a positional construction of `GraduationCluster` with the old four arguments still working (the defaults requirement).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw graduation cfgj8s` (human) showing the forward table and no "Proceed"; paste the `aw graduation cfgj8s --agent` RECORD's full `evidence` list showing an item of the form `graduation-forward:<...>` whose text CONTAINS `envhermet` (a bare `graduation-forward` with no colon is a FAILED validation, per F-7); and a diff of `aw graduation 25kzda --json`'s reverse fields against E-01 (e) (must be empty).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `summarize_graduation_cluster` diff and its returned line for (a) a forward-only source (no "nothing yet links", names the Set), (b) a source with neither direction (unchanged wording), (c) a `repo` with no `.aw`/`.agents` (still `''`).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `python3 -m pytest tests/test_graduation_forward_links.py -o addopts="" -q` passing with its count; then with the E-05/E-06 hunks reverted, showing (1), (3)'s forward half, (4)'s view half, (7) and (8) FAILING and (2), (5), (6) passing; then passing again. PLUS the two targeted counter-runs that make the new assertions real: (i) case (7) FAILING against a dict-valued `Evidence`, and (ii) case (8)'s `source_kind="spec"` half FAILING against an unmapped `selectors.resolve` call. Without those two, the items F-6 and F-7 exist to close are unproven.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste E-01 (a)-(e) re-run, `aw graduation z7nbn1` showing the same Set in both directions, and the bare `python3 -m pytest` summary BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty; review-measured baseline `2590 passed, 2 skipped`).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. `aw graduation` (and the runner's pre-graduation advisory line) start reporting a source's own `- Graduated-To:` Sets and their plans as forward links, so an already-graduated source no longer gets "Proceed". The forward check `aw check all` runs keeps identical findings but reads its plan-Set universe from one shared sweep. The existing reverse-link fields keep their meaning; forward links are added beside them. This is an interim fix; spec `4sd62s` later unifies both directions by construction. Graduates backlog `knvpiv` and inherits its `- Blocks-Release: next`.

WHAT REVIEW CHANGED. Three defects, each measured, two of which would have shipped silently. (1) E-04 passed the graduation kind `spec` to `selectors.resolve`, whose record type is `specs`; the mismatch returns an EMPTY resolution with NO error, so every spec source would have been forward-linkless while the code looked correct. (2) E-05's `--agent` Evidence used a dict value, and `sanitize_evidence_item` compacts a dict-valued item to its KEY ALONE, dropping the count and setids that item exists to carry past `--agent`'s `data` drop; the authored test asserted only the key, so it PASSED in exactly that broken state. (3) The plan claimed 0 specs carry `Graduated-To`; `z7nbn1` does, and it is a live both-directions agreement case, so defects (1) and (2) together would have masked each other. All authored COUNTS had also drifted (152 records not 102, 422 setids not 401, 111 graduated items not 97; the 40 held) and are now re-derive-at-execution properties.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `check_engine.py` (`build_plan_setid_index`, the source-lookup helper, `GraduationCluster`, `graduation_cluster`, `GRADUATION_VIEW_COVERAGE`), `releases.py` (`check_graduated_to` only), `cli.py` (`_run_graduation` only), `runner_shared.py` (`summarize_graduation_cluster` only), and the new test file. If an edit outside those paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-08 must show the forward-link tests FAILING before the change, INCLUDING the two counter-runs (a dict-valued Evidence, and an unmapped `selectors.resolve`) that prove the F-6/F-7 fixes are load-bearing; V-03 must show the live forward-check findings unchanged. A green suite is weak evidence here: these functions had NO prior test coverage (F-9), so nothing but this plan's own new cases guards the reverse path.

GENUINE STOP CONDITIONS: (1) if E-01's forward-only population is ZERO, the defect does not reproduce at the executing HEAD; stop and report rather than building a fix for a state you cannot observe. (2) If closing F-6 appears to require renaming `GRADUATION_SOURCE_KINDS`' `spec` member, stop and report: that key is read by `build_graduation_reverse_index` and every reverse consumer, and it is a larger contract change than this plan's concern.

Commit ONLY through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize`. Then close backlog `knvpiv` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
