# Review findings: plan jm27py

- Subject-Id: jm27py
- Subject-Type: ipd
- Reviewed-At: 2026-10-04
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261004T134544Z-4052083` at HEAD `8fc6c3b0c`. The plan was
committed and byte-identical to the sealed lane input (rev-14); no snapshot needed. `- Kind: child`, so `IPD-S407`
does not apply. `aw ipd lint --phase author` clean before review; `review-finalize` clean after revision.

Re-measured: `check_engine.check_plan_spec_link_missing` skips only when `not source_link_is_absent(target)`;
`SOURCE_LINK_ABSENT_SENTINELS = {"-", "none", "unresolved"}`; `_ITEM_FROM_SPEC_RE` reads a single `\S+` token;
`test_plan_carrying_absent_sentinel` asserts one finding for `from_spec="-"`; `releases.set_from_spec_line` strips the
line for `-`; no plan outside `gradcover` writes `- From-Spec: none|-` (rg); live run returns 24 findings, 10 on
`gradcover`; `ipd_authoring._AUTHORING_PLACEHOLDERS` holds `unresolved` placeholders. The only test module touching the
rule is `tests/test_check_engine_from_spec_missing.py`, and `check.plan-spec-link-missing` is `info` in `RULE_REGISTRY`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness (false negatives) | jm27py E-02 "a directory or glob entry that covers the spec file counts only if it resolves to that file through the same matcher `aw ipd finalize`'s scope check uses"; `ipd_lifecycle._scope_match` trailing-slash branch (`.aw/records/specs/approved/` matches every approved spec, verified) | Read literally, a broad directory entry DOES "resolve" through `_scope_match`, so it would silence every spec beneath it: the exact false negative the maintainer asked to avoid. The clause was ambiguous between the two readings. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now exempts a literal file entry only (exact repo-relative equality) and says why; a directory-entry case that still fires was added to E-02's outcome and E-03's tests. |
| PR-002 | MEDIUM | UNDER-SCOPE | F UX / silent failure | `check_plan_spec_link_missing` recovery `aw ipd set {id6} --from-spec {cited[0]}`; `status_set.py` "unresolvable spec id" refuses `--from-spec none`; `releases.set_from_spec_line` removes the line on `-` | After the change the finding still offers only "link it", and no tool can write the new `none` answer (setter refuses it; `-` deletes the line). An author following the remedy would write a false `From-Spec`, which Order 08 then counts as handoff output. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now rewrites `required`/`recovery` to name all three answers including the hand edit; F-05 records the setter limit; E-03 asserts the text. Changing the setter is left OUT (scope unchanged). |
| PR-003 | MEDIUM | IN-SCOPE | Goal reachability | live finding on `hm1h3l` "cites spec 25kzda, 77tr3o, r07vma, 2vev8j"; `hm1h3l` Scope-Paths lists four of those spec files but not `2vev8j`, and carried no `- From-Spec:` | The maintainer's driver (silence the nudge on this Set) would not be met: `hm1h3l` would still fire on `2vev8j` after this plan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- From-Spec: none` to `hm1h3l` (metadata only, re-scope history line) and a superseding note on `1f4faf`; E-03 now states the expected real-tree outcome as context and requires re-derivation. |
| PR-004 | LOW | IN-SCOPE | E testing | E-01 "stripped and lowercased" vs `source_link_is_absent` which also strips quotes | Normalization differed from the shared helper (`"none"` would fire). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 normalizes exactly as `source_link_is_absent`; quoted/uppercase cases added to E-03. |
| PR-005 | LOW | IN-SCOPE | G execution contract; live-artifact criteria | gate paragraph; F-03 counts | Gate lacked the paste-actual-output rule; F-03's count drifted (24/10 at review). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Honesty rule added; F-03 updated as context only, V-03 re-derives. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a directory Scope-Paths entry covering a spec count as declaring an edit of it? | No; literal file only | use `_scope_match` (broad entries silence every spec) | maintainer's "no false positives or false negatives" (jm27py history); `_scope_match` trailing-slash branch | yes |
| D-2 | Fix the unwritable `none` by changing `aw ipd set --from-spec`, or by documenting the hand edit? | Document in the finding's recovery; leave setter unchanged | accept `none` in the setter (widens scope to `status_set.py`, a separate surface) | `status_set.py` validator; jm27py OUT list | yes |
| D-3 | Silence `hm1h3l`'s `2vev8j` citation how? | `- From-Spec: none` on `hm1h3l` | add `2vev8j` to its Scope-Paths (false: it does not edit it) | `hm1h3l` Scope-Paths; 1f4faf history line explaining `none` | yes |
