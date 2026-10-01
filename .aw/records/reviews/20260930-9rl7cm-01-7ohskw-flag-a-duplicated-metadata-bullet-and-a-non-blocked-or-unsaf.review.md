# Review: Flag a duplicated metadata bullet and a non-blocked or unsafe Gate-Summary in backlog validate_item

- Subject-Id: 7ohskw
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims re-measured at HEAD `cd5df51c` by importing the shipped modules and driving the real
validators against temporary fixtures, not transcribed. The target plan was committed and unchanged
with a clean tree, so the pre-review snapshot was correctly skipped per Step 1. Structural preflight
`aw ipd lint --phase author` reported `conforming` before review and `--phase review-finalize`
reported `conforming` after the revisions.

EVERY ONE OF THE PLAN'S ELEVEN FINDINGS REPRODUCES, AND THE CENTRAL ASYMMETRY IS REAL. F-01: all
five duplicate shapes return `[]` from `validate_item`, and the doubled-`Status` fixture parses to
`open` while its second bullet reads `done`, so the silent-contradiction framing is accurate. F-02:
a `done` item carrying `- Gate-Summary:` returns `[]`, while the same shape on a non-`deferred` spec
returns `attention.gate-forbidden`; the two `has_gate` expressions differ by exactly the summary
term, as quoted. F-03: an ANSI-bearing value returns `[]` on the backlog tree while the spec tree
reports `attention.unsafe-field`. F-04 is the strongest finding and reproduces end to end:
`set_blocks_release_line`'s `\S+` value group cannot match an empty value, so seeding a bare
`- Blocks-Release:` line and setting `next` yields TWO lines at `validate_item` -> `[]`. F-05: zero
`backlog.*` keys in `RULE_REGISTRY` against seventeen emitted ids. F-06: inserting a `-duplicate`
id does break the shipped naming guard. F-07, F-08, F-09, F-10, F-11 all confirmed. The defect is
real and the fix shape is right.

THE DOMINANT FINDING IS THAT THE PLAN'S OWN PROPOSED RULE NAME IS CONDEMNED BY THE PLAN'S OWN
REASONING. OQ-02 argues for distinct rule ids precisely because `doctor.build_remediation`
dispatches on SUBSTRINGS of the id. That same mechanism makes `backlog.gate-summary-unsafe` wrong:
it CONTAINS `summary-unsafe`, so the existing arm captures it. Driven at review,
`build_remediation` on that id returns the title "Summary is not a single bounded control-char-free
line" and the fix "edit frontmatter `- Summary:` ...", which would ship a finding about
`- Gate-Summary:` that tells a human to edit a different field. The plan had already done the hard
analytical work (it identified substring dispatch as the governing mechanism) and then did not apply
it to its own name. `tests/test_doctor.py::test_remediation_family_guard` would not have caught it:
it asserts command shape over a fixed list and never that an id reaches its own arm. Renamed to
`backlog.gate-descriptive-unsafe`, which collides with no arm, with the `doctor.py` alternative
documented and deliberately not taken so the plan stays a validator-plus-registry change.

THREE SMALLER DEFECTS, EACH WORTH AN EXECUTION PASS. E-04's expected outcome is not provable by
outcome: with `invariant=""` the registered `RuleSpec` is field-identical to `_DEFAULT_RULESPEC`, so
`rule_spec` and `finding_dict` return indistinguishable values before and after registration, and
the item's own phrase "visible in the registry source" concedes it by appealing to source, which the
outcome-testing rule forbids a test from reading; the fix is to assert registry MEMBERSHIP, which is
a value read off the shipped mapping (PR-304, F-15). E-01's census would report a false positive if
it scans whole files: a third specs `- Gate-Summary:` hit exists but is a documentation EXAMPLE in a
spec BODY, so a naive grep would stop a landable plan on a corpus problem that does not exist
(PR-302, F-13). And a pre-existing UTC date-rollover failure sits in `tests/test_backlog.py`, first
in this plan's own targeted regression set, so the executor will meet it and could read it as a
regression they caused (PR-305, F-16).

ONE CORRECTION OF FACT THAT DOES NOT CHANGE AN INSTRUCTION. The plan says `parse_item` is
first-occurrence-wins, which is true PER SPELLING and which I confirmed in both directions. But the
legacy/canonical pair is resolved by spelling PREFERENCE rather than order
(`item.kind = work_kind if work_kind is not None else legacy_kind`), so in the `Kind`-plus-`Work-Kind`
shape the later bullet can win. E-02's canonicalization instruction is correct as written; the
precedence prose around it was imprecise (PR-306, F-14).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-301 | HIGH | IN-SCOPE | A. Correctness; F. UX | Driven: `doctor.build_remediation(Drift(rule="backlog.gate-summary-unsafe", ...))` -> `title="Summary is not a single bounded control-char-free line"`, `summary_fix="edit frontmatter '- Summary:' ..."`; `if "summary-unsafe" in rule:` arm in `agent_workflows/doctor.py` | The proposed id `backlog.gate-summary-unsafe` CONTAINS `summary-unsafe` and is captured by that arm, so a finding about `- Gate-Summary:` emits a remediation telling a human to edit `- Summary:`. The plan's own OQ-02 names substring dispatch as the governing mechanism and then fails to apply it to its own name. `test_remediation_family_guard` cannot catch it (command shape only, fixed list, never own-arm routing). | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | Added F-12 with the driven misroute. E-03(b) now forbids the name, explains the mechanism, and prescribes `backlog.gate-descriptive-unsafe` (verified to collide with no arm) with the `doctor.py`-arm alternative documented and dispreferred. Renamed at every dependent site (E-03, E-04, V-03, V-04, proposed changes). V-03 must paste the routing proof for the chosen name AND for the rejected one. E-05 gains a routing test case. OQ-02 amended to record that the mechanism cuts both ways. |
| PR-302 | MEDIUM | IN-SCOPE | E. Testing; G. Plan executability | Front-matter-restricted census: specs carry exactly 2 `- Gate-Summary:` lines, both `deferred`, both safe; whole-file grep finds 3, the third being `- Gate-Summary: <optional human context; never machine state>` in the BODY of `implemented/...attention-registry-and-cross-tree-status.spec.md` | E-01's census is specified without a front-matter restriction. A whole-file scan finds a documentation EXAMPLE and would report a corpus problem that does not exist, stopping a landable plan at its own precondition gate. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-13. E-01 now mandates front-matter-only scanning using the same boundary the duplicate rule uses, names the example hit so it is recognized, records both authoring and review totals, and states that only a NONZERO duplicated-key or backlog-`Gate-Summary` count is a divergence (the totals moving is expected). |
| PR-303 | MEDIUM | IN-SCOPE | Step 1 evidence accuracy | Re-driven census: 776 backlog items (plan says 759), 1095 plans (plan says 1054), all zeros unchanged | Two of F-09's figures have expired. The landability PRECONDITION holds, which is what the plan depends on, but an executor re-measuring per E-01 sees a mismatch with no statement of whether it invalidates anything. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-13 records both measurements and E-01 states explicitly that a moved TOTAL is expected and not a divergence, while a nonzero duplicate or backlog-`Gate-Summary` count is. |
| PR-304 | MEDIUM | IN-SCOPE | E. Testing | Driven: `finding_dict(Drift(rule="backlog.gate-unexpected"))` -> `severity='error', invariant=''`, field-identical to a would-be `invariant=""` registration; registered control `check.name-nonconformant` -> `invariant='I-09'` | E-04's expected outcome ("each return the registered spec rather than `_DEFAULT_RULESPEC`") is unobservable: with `invariant=""` the two are field-identical through both `rule_spec` and `finding_dict`. The item's own phrase "visible in the registry source" concedes this by appealing to SOURCE, which `AGENTS.md`'s outcome-testing rule forbids a test from reading, so as written it invites a banned code-pinning test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15. E-04's outcome now asserts `id in check_engine.RULE_REGISTRY`, a value read off the shipped mapping, and explicitly forbids grepping `check_engine.py`. V-04 requires the membership booleans as the evidence plus a statement that the printed specs are field-identical by design. F-15 also records that registration remains load-bearing because `enrich_drift`/`finding_dict` consult `rule_spec`. |
| PR-305 | LOW | IN-SCOPE | E. Testing | `python3 -m pytest tests/test_backlog.py -o addopts=""` -> `1 failed, 43 passed`; `test_release_exempt_setter_roundtrip_and_parity` asserts `- 2026-09-30` against a stamped `2026-10-01`; `date -u` confirms the rollover | A pre-existing UTC date-rollover failure sits in `tests/test_backlog.py`, which is FIRST in this plan's own targeted regression set, so the executor will meet it. Unflagged it reads as a regression they caused or gets fixed as an unrelated widening. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-16. Required tests now names the failure, its cause, that it touches no declared path, and instructs reproducing it at the lane baseline and leaving it alone without letting it mask a real regression in the same file. |
| PR-306 | LOW | IN-SCOPE | Step 1 evidence accuracy | Driven both orders: `Kind: chore` then `Work-Kind: bug` -> `bug`; `Work-Kind: bug` then `Kind: chore` -> `bug`; same-spelling doubles confirmed first-wins in both directions | The plan's first-occurrence-wins framing is true per spelling but the `Kind`/`Work-Kind` pair is resolved by spelling PREFERENCE, not order, so the LATER bullet can win in the F-7 shape. The E-02 instruction built on it is correct; the surrounding prose was imprecise about why. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14 stating the precedence precisely in both directions and noting E-02's instruction is unchanged. |
| PR-307 | LOW | IN-SCOPE | G. Plan executability (scope fence) | plan Scope check, Over-scope clause; `tests/test_doctor.py::test_remediation_family_guard` read in full | Two gaps: the Over-scope clause recorded no candidate checked-and-excluded and no make-and-justify instruction; and the targeted regression set implies a green `tests/test_doctor.py` covers remediation behavior, which it does not. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Over-scope now records `agent_workflows/doctor.py` as the one path a PR-301 alternative would require, with the rename preferred, plus the make-and-justify instruction. Required tests and V-04 both state what the family guard does NOT prove so a green run is not over-read. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should the `gate-summary-unsafe` misrouting be closed: rename the rule, or add a `doctor.py` arm? | Rename to `backlog.gate-descriptive-unsafe`, with the arm documented as an acceptable alternative requiring a declared scope path. | Adding a `doctor.py` arm ordered before `summary-unsafe`, not rejected but dispreferred: it is correct and would also serve a future human-facing fix, but it widens `- Scope-Paths:` to a fifth production file for a problem one token solves. Leaving the name and accepting the misroute, rejected: it ships a finding that names the wrong field. Reusing `backlog.summary-unsafe`, rejected: it is a different field with a different fix. | Driven `build_remediation` misroute; substring membership checked for all three proposed ids (only this one collides); the in-tree `check.graduated-to-repeated` precedent for renaming rather than disturbing another plan's surface. | yes |
| D-2 | Should E-04's registration item be dropped, given the registered spec is field-identical to the default? | Keep it; fix the assertion to registry MEMBERSHIP. | Dropping E-04 as a no-op, rejected: `enrich_drift` and `finding_dict` both consult `rule_spec`, so the entry becomes load-bearing the moment any field diverges from the default, and an unregistered id silently carries an unclassified severity. Inventing an `I-*` invariant row to create a visible difference, rejected as out of scope exactly as the plan already says (spec `pqsx96` has no record-metadata-wellformedness invariant). | Driven field-identity of `_DEFAULT_RULESPEC` and a would-be `invariant=""` registration through `finding_dict`; `rule_spec`/`enrich_drift` read from `check_engine.py`; the plan's own refusal to invent a catalog row. | yes |
| D-3 | Is the third rule (unsafe value) scope creep that review should strike, as the plan's D-1 explicitly invites? | Keep it. | Striking E-03(b) and its V-03 cases, which the plan offers as a clean cut, rejected on the author's own evidence: the predicate is already imported by this module for `item.summary`, the `if` block is already being edited, and the specs/backlog asymmetry on this exact field is the plan's stated purpose, so a separate plan would cost a full authoring and review cycle to add one branch. | The plan's D-1 options read in full; `backlog.py` already calling `A.is_safe_descriptive`; F-02 and F-03's driven specs-versus-backlog contrast. | yes |
| D-4 | Does the pre-existing `tests/test_backlog.py` failure block this plan or belong to it? | Neither; flag it as pre-existing and fence it. | Fixing the date flake here, rejected: it touches no declared path and would widen scope for an unrelated defect. Saying nothing, rejected: the file is first in this plan's own regression set, so silence invites misattribution. | `tests/test_backlog.py` failure output showing the `2026-09-30` versus `2026-10-01` diff; `date -u` confirming the rollover; the test's path absent from `- Scope-Paths:`. | yes |
| D-5 | Is the whole-file-versus-front-matter census distinction worth an in-plan correction, or is it obvious? | Worth correcting explicitly in E-01. | Trusting the executor to restrict to front matter, rejected: the plan's E-01 is a STOP gate, so a false positive there halts a landable plan, and the example hit looks exactly like a real field to a grep. | The third specs hit printed with its file and its position after a `## ` heading, reading `<optional human context; never machine state>`; the front-matter-restricted census returning exactly two, both `deferred` and safe. | yes |
| D-6 | The plan's three open questions are all `resolved` with `- Owner: none`. Does that need correcting as it did on a sibling plan? | No. | Rewriting them to `plan author` as I did for plan `2lxcwt`, rejected after re-reading the workflow clause: it requires the resolver recorded as owner where a reviewer resolves a question, and these were resolved AT AUTHORING with the reasoning stated inline and attributed by the plan's own `- Author:` field. The sibling case differed in that its rationales were review-relevant judgement calls left ownerless after the fact. No mechanical check applies either way (`ipd_schema.open_question_error` returns `None` for every non-blocking combination). | plan-review 3.1 item 5; `ipd_schema.open_question_error` driven over the non-blocking matrix; the three rationales read in full, each self-contained and dated to authoring. | yes |

No `Reversible: no` decisions were made, so no escalation was required under the
irreversible-decision rule. No finding was left `OPEN` or `DEFERRED` at or above the `HIGH` gate
threshold, so no `- Blocking: yes` escalation question was added to the plan.
