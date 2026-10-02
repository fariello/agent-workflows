# IPD: Split the Section 8.8 descriptive length bound into a one-line class and a prose class, and enforce it at the write path

- Date: 2026-10-02
- Kind: child
- Concern: Spec `attention-registry-and-cross-tree-status` Section 8.8 declares that "Every descriptive field is a single logical line with a defined maximum length" and that "Over-length values are a contract violation", and F10 makes such a violation a stable named `--check` failure. `attention_contract.MAX_DESCRIPTIVE_LEN` sets that maximum at 300 for EVERY descriptive field, and backlog `tapqf2` reports the bound is corpus-violating. Measured in this lane it is worse than reported: the bound is violated by 1976 of the 2561 live `- Scope:`/`- Concern:`/`- Question:` values (77.2 percent), and the violation is already LIVE rather than latent, because plan `ynhst5` shipped the bound into `specs.validate_spec` for `- Scope:` and a conforming-at-the-time corpus has since drifted. `main` is RED today on two fail-closed CI steps (`aw specs check` and `aw attention --check`, both exit 1) and on one default-suite test, all three from a single committed spec whose `- Scope:` is 343 chars. The same bound also DEADLOCKS the lifecycle: `specs.run_set` re-validates prospective text and refuses a nonconforming result, so an over-length spec cannot be transitioned even to fix itself.
- Scope: Split the one bound into two measured classes in `attention_contract` (a 300-char ONE-LINE class for `Summary`/`Gate-Summary`/`Title`/evidence fields, unchanged; a new prose class for the multi-sentence `- Scope:`/`- Concern:`/`- Question:` fields), repoint the two `specs.validate_spec` prose judgements at the prose bound, close the write-path hole in `specs.run_new` that let the red spec be authored, and add the hostile-string tests. EXCLUDES a grandfather cutover tier (route (a), refused with reasons below), EXCLUDES raising the single bound for all fields (route (b)), EXCLUDES touching the plans tree's `- Concern:`/`- Scope:` which no checker judges today, and EXCLUDES the renderer escaping that plan `qpw45x` owns.
- Scope-Paths: agent_workflows/attention_contract.py, agent_workflows/specs.py, tests/test_descriptive_length_classes.py, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: tapqf2
- Set: tapqf2
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: pl1lbb

## Workflow history

- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `tapqf2`. The item left the route open among (a) a grandfather cutover tier, (b) raising the bound, and (c) write-path-only enforcement; all three are RESOLVED from repository evidence rather than deferred, and the chosen design is none of them verbatim (see OQ-01). Authoring also corrected the item's own measurement and found a defect STRICTLY WORSE than the one it reports: the item says enforcing the bound "would fail `aw check` on a clean checkout", describing a hypothetical, but the bound is ALREADY enforced for spec `- Scope:` by plan `ynhst5` and `main` is ALREADY red on two fail-closed CI steps plus one default-suite test (F-03). That makes this a live breakage rather than the latent-debt `chore` the item assumed; the Work-Kind question is raised for the reviewer at OQ-02 rather than decided here.
- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give Section 8.8's length bound a value that the corpus it governs can actually satisfy, by recognizing that `- Summary:` and `- Scope:` are different KINDS of field with measurably different shapes, so the contract becomes enforceable at `error` for every tree instead of being quietly corpus-violating for one. Restore `main` to green on the two fail-closed CI steps it fails today, and close the `specs new` write path that let the violating artifact in.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: give the contract two measured classes

- [ ] E-01 In `agent_workflows/attention_contract.py`, beside the existing `MAX_DESCRIPTIVE_LEN = 300`, add `MAX_PROSE_DESCRIPTIVE_LEN = 4300` and a `PROSE_DESCRIPTIVE_FIELDS = frozenset({"Scope", "Concern", "Question"})` naming the fields that carry the prose class. Keep `MAX_DESCRIPTIVE_LEN` at 300 and keep its name, because 918 `- Summary:` values, 3 `- Gate-Summary:` values and the `_evidence_resolvable` caller all conform to it today and must keep the tighter bound. Write the derivation of 4300 in a comment citing the measurement in F-05 (live max 4216, so 4300 is the smallest round value clearing the corpus with headroom), and state that the number is a MEASURED CEILING on existing prose, not a licence to write a 4000-char field.
  - Depends on: none
  - Expected outcome: `attention_contract` exports both bounds and the field-name set; `MAX_DESCRIPTIVE_LEN` is byte-unchanged at 300.
  - Execution state: pending

- [ ] E-02 In the same module, add `is_safe_prose_descriptive(value)` applying the IDENTICAL newline and control-character predicate as `is_safe_descriptive` but bounding length at `MAX_PROSE_DESCRIPTIVE_LEN`. Implement it by factoring the shared body into one private helper taking the bound, so the two public predicates cannot drift in their control-character or newline handling (the safety half of Section 8.8 is unchanged for both classes; only the length ceiling differs).
  - Depends on: E-01
  - Expected outcome: one shared implementation, two public predicates differing only in bound; a newline, a BEL, an ANSI escape and a C1 character are unsafe under BOTH.
  - Execution state: pending

### Task group 2: repoint the live checker and close the write path

- [ ] E-03 In `agent_workflows/specs.py`, change the two PROSE judgements in `validate_spec` to call `A.is_safe_prose_descriptive`: the `- Scope:` check and nothing else in that function. Leave the `- Summary:` check, the `Gate-Summary` check and `_evidence_resolvable` on `is_safe_descriptive` unchanged. Keep the emitted rule id `attention.unsafe-field` and keep the detail string value-free (it must not echo the untrusted value, per the `ynhst5` OQ-03 constraint its tests pin). This is the item that turns `aw specs check` and `aw attention --check` green.
  - Depends on: E-02
  - Expected outcome: the committed spec `89xjll` (343-char `- Scope:`) no longer drifts; a 4301-char `- Scope:` still drifts as `attention.unsafe-field`; `- Summary:` at 301 still drifts.
  - Execution state: pending

- [ ] E-04 In `agent_workflows/specs.py` `run_new`, add the missing guard on the value that becomes the spec's `- Scope:`. `_render_new_spec` writes `--summary` into the `- Scope:` field, but `run_new` validates that flag with `_refuse_unsafe_descriptive(..., "--summary", ...)` at the 300-char ONE-LINE bound, which is the wrong class for the field it lands in: it is simultaneously too strict (a legitimate 400-char scope is refused) and not the field actually being written. Validate the rendered `- Scope:` value against the prose bound so the write path and the checker agree on one bound for one field. Keep the `--title` guard on the one-line bound.
  - Depends on: E-02
  - Expected outcome: `aw specs new --summary <4301 chars>` is refused with an actionable message naming the prose bound and the actual length; `--summary <400 chars>` is ACCEPTED and the resulting spec passes `validate_spec` (it is refused today).
  - Execution state: pending

### Task group 3: prove it, and record the contract change

- [ ] E-05 Add `tests/test_descriptive_length_classes.py` covering, with no reliance on the live corpus: (a) the two bounds are distinct and `MAX_DESCRIPTIVE_LEN` is still 300; (b) the four hostile shapes (newline, BEL, ANSI, C1) are unsafe under BOTH predicates, so widening the length bound did not widen the safety predicate; (c) exact-boundary pairs for both classes (300/301 one-line, 4300/4301 prose); (d) a spec with a 400-char `- Scope:` and a 250-char `- Summary:` validates clean, while 301-char `- Summary:` and 4301-char `- Scope:` each drift as exactly `attention.unsafe-field`; (e) the `run_new` write-path round trip from E-04, asserting the authored file passes `validate_spec` (the write-path/checker agreement that was broken); (f) a regression asserting the drift detail still does not echo the untrusted value.
  - Depends on: E-03, E-04
  - Expected outcome: a new test module failing before E-01..E-04 and passing after, exercising real functions and real CLI exit codes rather than source structure.
  - Execution state: pending

- [ ] E-06 Amend spec `attention-registry-and-cross-tree-status` Section 8.8 and F10 to state the TWO classes explicitly ("a defined maximum length" becomes a per-class maximum, naming the prose fields and both numbers), and record the change in `CHANGELOG.md`. This is a deliberate spec amendment in the same change as the behavior, per the repository's plan-may-amend-a-spec rule, and the declared spec path is in `- Scope-Paths:` for that reason. Say WHY in the spec-sync section: the single bound asserted a uniformity the corpus never had.
  - Depends on: E-03
  - Expected outcome: Section 8.8 and F10 describe the enforced behavior; a reader cannot conclude a 300-char ceiling applies to `- Scope:`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The closed rule catalog is deliberate: `attention_contract.RULE_IDS` is documented as "The CLOSED catalog of stable `--check`/`--agent` rule identifiers" and already contains `attention.unsafe-field`, so this plan reuses that id and mints none. `check_engine.RULE_REGISTRY` already registers it at `error`, pinned by `tests/test_specs_releases_unsafe_field.py::test_rule_registry_entry`.
- Severity is declared in CODE, not configuration: `check_engine.RULE_SPEC`/`RULE_REGISTRY` carry the severity and there is no generic per-rule severity override key in `.aw/config/project.json`. Only `info` is exempt from a nonzero exit (`artifact_core.drift_exit_code` returns 1 "if any ... severity != info"), which is why demoting this rule to `warning` would NOT quiet CI and is not an option.
- A drift detail must never echo the untrusted value; `specs.validate_spec` wraps every message in `A.escape_detail` and the `ynhst5` tests assert `assertNotIn(val, d.detail)`. Any message this plan writes keeps that property and reports only the LENGTH.
- The cutover/grandfather machinery exists and is well-factored (`config.resolve_cutover_date`, `config.KNOWN_FEATURE_CUTOVERS`, the `SetidPolicy.tier_for`/`applies_to_artifact_date` split, `check_engine.CARRIER_CUTOVER_DATE`), so route (a) was cheap to adopt and was still refused on the merits (F-07).
- `aw check` severity composition is centralized in `check_engine.enrich_drift`, which stamps `drift.severity or spec.severity`, so a per-finding override at the emitter beats the registry. This plan uses no override: the finding stays `error`.
- The default suite runs bare (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. A whole-corpus assertion belongs behind `@pytest.mark.livecorpus`, which is why E-05 is written against synthetic fixtures.

## Findings

| Id | Finding |
|---|---|
| F-01 | `attention_contract.MAX_DESCRIPTIVE_LEN = 300` is the single bound for every descriptive field, and `is_safe_descriptive` applies it uniformly alongside the newline and control-character checks. |
| F-02 | The corpus splits into two cleanly separated classes, measured over `.aw/records/**/*.md` in this lane. ONE-LINE fields: `Summary` n=918 max=297, `Gate-Summary` n=3 max=69, `Title` n=1 max=70, `Close-Evidence` n=1 max=95 - all conform to 300. PROSE fields: `Scope` n=1293 max=3455, `Concern` n=1263 max=4216, `Question` n=5 max=1798 - of 2561 values, 1976 (77.2 percent) exceed 300. The two classes do not overlap: the one-line max is 297 and the prose p50 is 632. |
| F-03 | THE VIOLATION IS LIVE, NOT LATENT, which corrects the item's framing. Plan `ynhst5` E-02 shipped the bound into `specs.validate_spec` for `- Scope:`, and spec `89xjll` (343-char `- Scope:`, committed 2026-10-01) now violates it. Measured at this lane's HEAD: `python3 -m agent_workflows specs check` exits 1, `python3 -m agent_workflows attention --check --agent` exits 1 reporting `attention.unsafe-field` on that path, and `python3 -m agent_workflows check specs` exits 1. Both of the first two are fail-closed steps in `.github/workflows/tests.yml`, so `main` is red. |
| F-04 | A default-suite test is red for the same reason: `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` fails naming `89xjll: ['attention.unsafe-field']`. It is NOT marked `livecorpus` despite asserting a whole-corpus property, so it blocks every concurrent lane's integration, which is precisely the cost `pyproject.toml`'s `livecorpus` marker comment documents. |
| F-05 | 4300 is the smallest round bound clearing the live prose corpus: violations by bound are 1000->675, 1500->225, 2000->71, 2500->28, 3000->9, 3500->3, 4000->1, 4096->1, 4300->0. The single longest prose value is a 4216-char `- Concern:`. 4300 therefore clears the corpus with about 1.02x headroom over the observed maximum. |
| F-06 | THE LIFECYCLE DEADLOCK IS REAL AND REPRODUCED, not merely argued. `specs.run_set` re-validates prospective text and refuses nonconforming output ("the resulting spec would not conform; refused (file unchanged)"). Probed in a throwaway repo with a 400-char `- Scope:`: `aw specs set --status to-review` exits 1 with exactly `attention.unsafe-field: Scope is over-length`, so the artifact cannot be transitioned even to repair itself. There is no `--force` or repair flag on `aw specs set`. |
| F-07 | ROUTE (a), A GRANDFATHER CUTOVER TIER, IS REFUSED. The precedent exists and would work mechanically, but it gets the direction of the problem wrong: 77.2 percent of the governed population violates the bound, which is evidence the BOUND is wrong rather than evidence the corpus is in debt. A tier would also permanently split prose fields into two populations judged by different rules, and every future `- Scope:` would still be held to 300 chars - a limit the repository's own authoring conventions (which ask for measured, citation-bearing scope statements) make unreachable, as the p50 of 632 shows. |
| F-08 | ROUTE (b), RAISING THE SINGLE BOUND, IS REFUSED. Raising `MAX_DESCRIPTIVE_LEN` to 4300 for all fields would relax the 918 `- Summary:` values from a bound they all satisfy (max 297) to one 14x looser, losing a real constraint on the field that most needs it: `- Summary:` is the field the attention board and `/whatnext` render as the artifact's one-line identity. |
| F-09 | ROUTE (c), WRITE-PATH-ONLY, IS INSUFFICIENT ALONE but is adopted as HALF the fix. It cannot clear F-03, because the red artifact is already committed and a write-path guard is not retroactive; and it cannot be the whole answer while the checker still fails. It IS needed, because the checker alone would leave the hole that admitted `89xjll`. |
| F-10 | THE WRITE PATH IS INCOHERENT WITH THE CHECKER TODAY, which is the mechanism behind F-03. `specs._render_new_spec` writes the `--summary` flag into the `- Scope:` FIELD, while `run_new` validates that flag at the one-line bound. So `aw specs new` refuses a legitimate 400-char scope, yet the field it writes is judged by `validate_spec` under the same 300 bound - and `89xjll` still got in, because it was not authored through `run_new` at all. The guard and the field must name one bound. |
| F-11 | THE SAFETY HALF OF SECTION 8.8 IS ALREADY CLEAN, so widening a length bound costs nothing in safety: ZERO of the 3481 descriptive field instances in the live corpus contain a control character, and zero contain a newline (the bulleted-field regex captures a single line by construction). The bound is doing readability and determinism work here, not injection prevention - exactly as backlog `tapqf2` anticipates once `qpw45x` lands. |
| F-12 | THE PLANS TREE IS UNJUDGED and is deliberately left that way. `python3 -m agent_workflows check plans --agent` reports zero `unsafe-field` findings, and `ipd_lint` imports neither `is_safe_descriptive` nor `MAX_DESCRIPTIVE_LEN`, so the 1005 over-length plan `- Scope:` values drift against no rule today. Extending the rule to plans is a separate decision with a separate population and is out of scope (see Deferred). |
| F-13 | AN IMMUTABILITY WALL MAKES ANY REPAIR-FIRST ROUTE UNAVAILABLE AT THIS SCALE, independently of the deadlock. 1637 of the over-length prose values live in terminal or immutable trees (`plans/executed/`, `plans/superseded/`, `plans/not-executed/`, `specs/implemented/`, `research/archive/`), and AGENTS.md forbids changing what an executed plan records. Plan `ynhst5` E-01 could hand-shorten 2 specs; it cannot be generalized. |
| F-14 | `aw ipd scaffold` writes `- Concern: TODO.` and `- Scope: TODO.` and applies no descriptive guard, so even if the plans tree were judged, the plan write path would need its own guard. Recorded as the reason F-12's extension is a real piece of work rather than a one-line change. |
| F-15 | THREE OTHER DEFAULT-SUITE TESTS FAIL AT THIS LANE'S HEAD AND ARE UNRELATED TO THIS PLAN: `test_run_finding_reachability.py::test_unreachable_binding_refusal_fires_under_perturbation`, `test_typecheck_gate.py::test_typecheck_gate_clean_exit` (which PASSES in isolation, so it is order-dependent), and `test_selector_type_containment.py::test_must_not_refuse_matrix` (asserting a plan path selector is refused, where it now succeeds). Baseline is therefore `4 failed, 4623 passed`; this plan must reduce that to 3 failed and must not be credited with fixing the other three. |

## Proposed changes (ordered, validatable)

1. `attention_contract`: add `MAX_PROSE_DESCRIPTIVE_LEN = 4300` and `PROSE_DESCRIPTIVE_FIELDS`, keeping `MAX_DESCRIPTIVE_LEN = 300` byte-unchanged (E-01).
2. `attention_contract`: add `is_safe_prose_descriptive`, sharing one private body with `is_safe_descriptive` so the safety predicate cannot drift between classes (E-02).
3. `specs.validate_spec`: judge `- Scope:` at the prose bound, leaving `- Summary:`, `Gate-Summary` and `_evidence_resolvable` at 300 (E-03). This clears F-03 and F-04.
4. `specs.run_new`: guard the rendered `- Scope:` value at the prose bound, so the write path and the checker agree on one bound per field (E-04). This clears F-10.
5. `tests/test_descriptive_length_classes.py`: hostile shapes, both boundaries, the clean-spec case, the write-path round trip, and the no-echo regression (E-05).
6. Spec Section 8.8 + F10 amendment and CHANGELOG entry (E-06).

## Deferred / out of scope (with reason)

- EXTENDING THE RULE TO THE PLANS TREE (F-12, F-14): 1005 over-length plan `- Scope:` values and 961 over-length `- Concern:` values are judged by no rule today. Turning the rule on there is a distinct decision (which bound for `- Concern:`, whether `ipd_lint` or `check plans` owns it, and a write-path guard in `ipd_authoring` that does not exist), with its own population and its own risk of reddening CI. Deliberately NOT bundled: this plan's job is to make the bound correct where it is already enforced.
  - Carrier-Declined: NOTHING IS OWED YET, because extending the rule is a POLICY CHOICE the reviewer may legitimately decline outright, not repair work this plan leaves half-done. Filing a carrier would assert that judging the plans tree is agreed and merely unscheduled, which no evidence here supports: the plans tree has never been judged by this rule, so nothing regresses by leaving it unjudged, and this plan neither introduces nor worsens that gap. F-12 and F-14 record the population (1966 values) and the missing `ipd_authoring` guard so the next author inherits the measurement rather than having to re-derive it; if the maintainer wants the extension, that decision is the evidence that justifies an item, and `aw backlog new` files it in one command.
- MARKING THE WHOLE-CORPUS SPEC TEST `livecorpus` (F-04): `test_every_real_spec_in_this_repository_still_conforms` asserts a property over every artifact in `.aw/records/`, which `pyproject.toml`'s own marker documentation says should be marked so one agent's artifact cannot block every concurrent lane. E-03 makes it green, so this plan does not need the marker; the marker question is a correctness-of-test-classification issue that outlives this fix.
  - Carrier: wc5c5e
- THE THREE UNRELATED SUITE FAILURES (F-15): out of scope by the one-concern rule, and fixing them here would hide which failure this plan actually resolved. Each already has an open carrier, which is why F-15 exists: it pins the 4-failure baseline so this plan is credited with fixing exactly one.
  - Carrier: 8jeh4x
  - Carrier-Evidence: .aw/records/backlog/open/20261001-bxnhdj-01-bxnhdj-reconcile-test-must-not-refuse-matrix-in-test-sele.backlog.md
- RENDERER ESCAPING: owned by pending plan `qpw45x` (Set `llnvwj`), which escapes Markdown metacharacters and neutralizes control characters at the board's detail line. Disjoint surface; no file overlap in `- Scope-Paths:` beyond `attention_contract.py`, where that plan ADDS functions and this plan ADDS constants.
  - Carrier: qpw45x

## Scope check

- Over-scope: none. The spec file in `- Scope-Paths:` is a declared amendment (E-06) required by the repository's plan-may-amend-a-spec rule, not scope creep.
- Under-scope: the plans tree keeps 1966 unjudged over-length prose values (F-12), so this plan makes the bound CORRECT where enforced rather than enforced EVERYWHERE. That is the deliberate boundary stated in `- Concern:`, and the Deferred section names what is left.

## Required tests / validation

- `python3 -m pytest tests/test_descriptive_length_classes.py` (new module, E-05) passes.
- `python3 -m pytest tests/test_specs_releases_unsafe_field.py tests/test_specs_releases_descriptive_safety.py tests/test_attention_contract.py tests/test_spec_review_attestation.py` passes: these pin the existing one-line bound, the 300/301 boundary, the closed rule catalog and the whole-corpus spec property, and must not regress.
- `python3 -m agent_workflows specs check`, `python3 -m agent_workflows attention --check --agent` and `python3 -m agent_workflows check specs` each exit 0 (they exit 1 today, F-03).
- The bare default suite `python3 -m pytest` ends at 3 failures, all three named in F-15, down from the 4 measured at this lane's HEAD.
- `python3 -m agent_workflows ipd lint --phase pre-transition <this plan>` conforms.

## Spec / documentation sync

- `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` Section 8.8 and F10 are AMENDED by E-06, and the path is declared in `- Scope-Paths:` so both runners announce the spec edit before the run starts and reconcile it at the end.
- WHY the amendment is necessary rather than optional: Section 8.8's "a defined maximum length" and F10's "length-bounded" read today as ONE bound for all descriptive fields, and that reading is what `MAX_DESCRIPTIVE_LEN` implements. Leaving the spec untouched while shipping two bounds would leave the contract asserting a uniformity the code no longer has, and would leave the next reader to conclude that the 1976 over-length prose values are violations. The spec is `Status: implemented`, so the amendment keeps it true of the shipped code.
- The spec carries NO `- Id:` (it is a pre-cutover `YYYYMMDD-HHMM-NN-<slug>.spec.md` legacy name, grandfathered). This plan does NOT rename or id6-convert it: that is an unrelated change to a path it must edit, and bundling it would obscure the amendment.

## Open questions

### OQ-01: Which of the item's three routes should the fix take?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence, and the answer is none of the three verbatim. Route (a) grandfathering is refused by F-07 (77.2 percent of the governed population violating a bound is evidence against the bound, not evidence of debt, and it would hold every future `- Scope:` to an unreachable 300). Route (b) raising the one bound is refused by F-08 (it would relax 918 conforming `- Summary:` values 14x). Route (c) write-path-only is adopted as HALF the fix (E-04) but is insufficient alone by F-09, because the red artifact is already committed. The chosen design is the SPLIT the item did not enumerate: two measured classes, which F-02 shows the corpus already separates cleanly (one-line max 297 versus prose p50 632), enforced at `error` for both, with no grandfathering and no tier. The item's own closing note anticipates this, observing that the bound's safety justification weakens once `qpw45x` lands and that this "argues for (b) or (c) over a hard fail"; F-11 confirms the premise empirically (zero control characters and zero newlines across 3481 field instances).

### OQ-02: Is `chore` still the right Work-Kind, given the breakage is live?

- Blocking: no
- Status: open
- Owner: human
- Carrier: tapqf2
- Resolution or deferral rationale: INHERITED from backlog item `tapqf2` (`- Work-Kind: chore`, `- Priority: low`) and deliberately NOT changed by this plan, because reclassifying the work I am authoring would be marking my own homework on the one field that carries a release gate. The reviewer should decide, and the evidence is F-03/F-04: this is not latent debt but a LIVE red `main`, failing two fail-closed CI steps and one default-suite test. Under this repository's rule that every live bug gates the next release, `bug` would oblige `- Blocks-Release:`, and AGENTS.md's perceptibility test plausibly applies: a maintainer or lane hitting a red fail-closed CI step is a user-perceptible impact, not an invisible inefficiency. Against `bug`: nothing is WRONG in any output a user reads; a contract is merely stricter than its corpus, which is closer to policy debt. I have deliberately NOT written a `- Blocks-Release:` field, since inventing a gate the item does not carry is exactly the kind of unattested field the authoring rules forbid. If the reviewer rules `bug`, the remedy is `aw ipd set to-review <plan> --work-kind bug --blocks-release next` plus the same change on item `tapqf2`.

### OQ-03: Should 4300 be the prose bound, or should the prose class be unbounded?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as 4300, bounded. Unbounded was considered and refused because Section 8.8's requirement is a BOUND ("a defined maximum length"), and F-11 shows the bound's remaining purpose is determinism and readability rather than injection prevention - both of which still need a ceiling, since the renderer interpolates the value into a terminal line and a JSON record with no truncation anywhere (no `truncat`/`textwrap`/`shorten` call exists in `attention.py` on this path). 4300 is chosen by F-05 as the smallest round value clearing the live maximum of 4216; 4096 was rejected because it still leaves 1 violation, which would red CI on day one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the output of `python3 -c "from agent_workflows import attention_contract as A; print(A.MAX_DESCRIPTIVE_LEN, A.MAX_PROSE_DESCRIPTIVE_LEN, sorted(A.PROSE_DESCRIPTIVE_FIELDS))"` showing `300 4300 ['Concern', 'Question', 'Scope']`. Paste `git diff` for the hunk showing the comment records the 4216 measurement and the derivation of 4300.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a transcript asserting that each of `"x"*4301`, `"a\nb"`, `"a\x07b"`, `"a\x1b[31mb"` and `"a\x85b"` returns False from `is_safe_prose_descriptive`, while `"x"*4300` returns True and `"x"*301` returns True (prose) but False from `is_safe_descriptive` (one-line). This is the proof that widening the LENGTH did not widen the SAFETY predicate.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the exit codes of `python3 -m agent_workflows specs check`, `python3 -m agent_workflows attention --check --agent` and `python3 -m agent_workflows check specs`, each 0, alongside the pre-change exit codes of 1 recorded in F-03. Paste `python3 -m pytest tests/test_spec_review_attestation.py -o addopts="" -k conforms` passing (it fails today, F-04). Paste a transcript showing a synthetic 4301-char `- Scope:` still yields exactly `['attention.unsafe-field']` from `specs.validate_spec`, proving the rule was repointed and not removed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a transcript in a throwaway repo showing `aw specs new --summary <400 chars> --apply` exits 0 AND the resulting file yields `[]` from `specs.validate_spec` (today it exits 2), and `aw specs new --summary <4301 chars> --apply` exits 2 with a message naming both the prose bound and the actual length. Paste the refusal message verbatim and confirm it does not echo the untrusted value.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the full output of `python3 -m pytest tests/test_descriptive_length_classes.py -o addopts=""` showing every test passing with per-test counts, plus the output of `python3 -m pytest tests/test_specs_releases_unsafe_field.py tests/test_specs_releases_descriptive_safety.py tests/test_attention_contract.py -o addopts=""` showing no regression. Also paste the bare `python3 -m pytest` summary line showing 3 failures, all three named in F-15, down from 4.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `git diff` of the spec's Section 8.8 bullet and F10 line showing both now name the per-class maxima and the prose field set, plus the CHANGELOG hunk. Confirm by quoting the amended text that a reader cannot conclude a 300-char ceiling applies to `- Scope:`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries no `- Readiness:` field, which is an output of `/plan-review` and not of authoring. It requires explicit human approval before execution.

Execution contract: commit only the paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never push. Paste actual runner output for every `V-*` item rather than asserting success. The declared spec edit (E-06) is announced by both runners before the run starts and reconciled at the end, so it must be performed in the same change as the behavior it describes.

Post-gate lifecycle: after every `E-*` is `performed` and every `V-*` is `pass` with pasted evidence, run `aw ipd lint --phase pre-transition` and move the plan to `.aw/records/plans/executed/` through the tooled transition. Do NOT mark it executed while any CI step named in V-03 still exits nonzero.
