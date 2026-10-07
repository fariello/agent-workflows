# Review findings: plan zye6k4

- Subject-Id: zye6k4
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `24891c7c0` in an isolated review-sweep lane. Child plan. Plan committed and byte-identical to
the lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent` clean before semantic review;
`--phase review-finalize` clean after revisions; `check.ipd-uncarried-obligation` fired on the unrevised plan and is
clear after.

Verified:
- `research_cmd._next_order_for_set` docstring and `return (max(orders) + 1) if orders else 0`; `plan_new` calls it
  after `normalize_kind`; `artifact_adopt.plan_adoption` calls `_rc.plan_new` (F-01, conventions hold).
- Spec `20260730-2152-01`: naming list "`00` is the originating prompt (Section 4.6)", Section 4.6 "the prompt is
  `NN=00` of its research set", Section 5.1 "or create a new set at `NN=00`" (F-03 holds).
- Installer writes research README from `templates/agents-docs-{bucket}-README.md` (`engine.py`).
- Scratch `private-target` install: new-set report, prompt, singleton findings and `aw adopt --set` all `-00-`;
  second doc in a set `-01-`; no `--order` on either verb (F-05).
- Throwaway-copy mutation of the proposed rule, research + adopt test files: "5 failed, 182 passed" (F-06).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | D Anti-regression / E | `tests/test_research_cmd_create.py:75` `assertEqual(p1.order, "00")`, `:91`; `tests/test_artifact_adopt.py:545` `["00", "01"]`; `tests/test_research_date_containment.py` `20260929-conf1-00-`, `20260929-dry-conf-00-` | Five existing tests pin the old rule; the plan neither named nor scoped them, so E-02 would turn the suite red with no authorized fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 names all five (re-derived at execution), changes expectations without weakening; three test files added to Scope-Paths; F-06 records the measurement. |
| PR-002 | MEDIUM | IN-SCOPE | E Testing | E-01 three probes; `plan_new` "Omitted set -> singleton" | The singleton path (no `--set`), the most common `research new` call, was untested and unprobed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to E-01, V-01/V-02 and E-05 (g). |
| PR-003 | MEDIUM | IN-SCOPE | A / G | E-03 "refuses with a clear message" | `--order` threading, exit code, range handling, preview behavior and write-nothing guarantee were unstated; no way to put a prompt at `00` in an existing set was tested. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 names the thread path, exit 2, 0-99 range, refusal before mint/write; E-05 (f) asserts no file, (h) `--order 00`; V-03 covers both verbs. |
| PR-004 | LOW | IN-SCOPE | G Spec sync | spec Section 5.1 "Inputs (explicit or tool-derived): `--set`, `--kind`, ..." | E-04 amended the 5.1 sentence but not its Inputs list, leaving `--order` undocumented in the spec; no WHY for amending an implemented spec. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 adds `--order` to Inputs and runs `aw specs check`; spec-sync section states why. |
| PR-005 | HIGH | UNDER-SCOPE | Project rule | `check.ipd-uncarried-obligation` on `Carrier: none (ruled out)`; AGENTS.md live-bug rule | Malformed carrier failed `aw check` at error; live bug lacked `Blocks-Release`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `Carrier-Declined:` with reason; `- Blocks-Release: next`. |
| PR-006 | MEDIUM | UNDER-SCOPE | G contract | gate "move the plan to `executed/` with `aw ipd set executed zye6k4`" | Gate lacked resolved-OQ statement, honesty rule, scope fence as declaration, spec-edit declaration, temp HOME and conditional finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewritten to the Set's standard contract with `aw ipd finalize`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should a `research-prompt` added to an existing set be auto-placed at `00`? | No; max+1, with `--order 00` as the explicit path | Auto-place at `00` when free | OQ-01 ruling scopes the change to the opening document; auto-placement would reorder reading silently | yes |
| D-2 | Update the five pinned tests or keep them? | Update expectations to `01`-first | Leave them and special-case | they encode the old contradicting rule the maintainer ruled against (OQ-01) | yes |
