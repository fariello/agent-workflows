# Review: Publish the excluded-tree selector answer as the third zero-match class in Section 11.1

- Subject-Id: y6gsqw
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `0ffb1e798`. `aw ipd lint --phase author --agent` reported `clean` before any edit,
so every finding is semantic. Re-measured: `uxb0tz` is still in `pending/` at `Status: approved`;
`aw attention 7ny1bg` exits 2 ("no artifact matched selector '7ny1bg'") while `aw find 7ny1bg --paths`
exits 0; `grep -c excluded docs/cli-output-contract.md` is 0; `attention_contract.TREE_POLICY` holds
5 `tracked=False` entries (walkthroughs, roadmaps, comms, docs-prompts, reviews) each with a populated
`reason`; no test under `tests/` mentions "Empty Result Convention" or "Discriminator". F-01 to F-04,
F-06 and F-07 reproduce. `aw attention --check` exits 1 here (F-04's premise holds), though
`aw attention reusable` exits 0 at this HEAD; the NOT REFUSED wording remains correct because the
drift path can still produce exit 1.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A. Correctness / G. Sequencing | `.aw/records/plans/pending/20260929-selquiet-01-zyj8io-...ipd.md` OQ-02 "RESOLVED 2026-10-02 by maintainer", `- Status: approved`, E-07 "Section 11.1 survives, scoped" | F-05/OQ-01 rejected a `zyj8io` edge on two premises that are false: its OQ-02 is resolved and the plan approved, and its E-07 edits Section 11.1 itself, so the two plans are not section-disjoint. Unordered, one can silently contradict the other's count sentence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `executed:zyj8io` to `- Item-Dependencies:`, new F-08, revised OQ-01 and F-05, E-02 told to edit the section as it reads at base and preserve `zyj8io`'s clauses, Deferred entry corrected. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing | E-03 "drive the CLI or the public functions"; E-04 "in-memory patching"; `tests/test_attention.py::_attsel_run` | E-04's in-memory breaks cannot reach a subprocess, so a subprocess-driven E-03 would pass under every break and V-04 would be unsatisfiable honestly. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires in-process `attention.run` driving (F-09); V-03 demands the pasted call site. |
| PR-003 | MEDIUM | UNDER-SCOPE | E. Testing / D. Invariants | E-01 "two tokens from two DIFFERENT excluded trees"; E-02 "covers every tree the policy inventory marks excluded"; `selectors.resolve_selectors(root, "docs-prompts"/"prompt-library", ["fix-bar"])` | E-01/V-01 observed only walkthroughs and roadmaps, the two trees `uxb0tz` was scoped to before its PR-004 widened it, while E-02 publishes all five. Measured candidates outside those two: `fix-bar` (prompt-library -> `docs-prompts` policy) and `ocman` (comms), both exit 2 from `aw attention` today. Review-record id6s are unsuitable because a review filename carries its subject plan's id6. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01, its Expected outcome, and V-01 now require three trees including one outside walkthroughs/roadmaps, with the review-filename caveat. |
| PR-004 | LOW | IN-SCOPE | E. Testing | `attention._classify_tree` maps `.aw/records/prompt-library/x` to `docs-prompts`, `.aw/records/docs-prompts/x` to None; `TreePolicy.root` is the legacy `.agents/` path | Deriving the tree from `TREE_POLICY` without the layout mapping can place the fixture where it classifies as nothing, silently turning the excluded-tree case into a bogus-token case. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 requires asserting `_classify_tree` returns the chosen `tracked=False` policy for the fixture path; V-03 demands it pasted. |
| PR-005 | LOW | UNDER-SCOPE | F. UX / E. Testing | E-02 "STATE THE PER-SURFACE CHANNEL RULE"; E-03 had no channel assertion | E-02 publishes a stdout/stderr split that E-03 never pinned, so that part of the published contract stayed undefended. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 covers the human board, `--agent`, and `--paths` with stdout free of explanation; V-03 demands it. |
| PR-006 | LOW | IN-SCOPE | G. Execution contract | Gate: "The terminal transition is the tooled one (`aw ipd finalize`)" | Unconditional finalize instruction; the contract requires runner/executor-conditional ownership. Also the gate's Readiness paragraph described the field as absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: runner finalizes under `aw oc run`/`aw agy run`; a hand executor runs `aw ipd finalize` with `--scope-reason`/`--scope-ack`. Readiness paragraph updated. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the plan carry `executed:zyj8io`? | Yes, add the edge | Keep no edge and rely on merge conflict detection (rejected: a clean textual merge can still leave contradictory prose); add a prose-only coordination note (rejected: not enforced by the runner) | `zyj8io` OQ-02 "RESOLVED 2026-10-02 by maintainer"; `zyj8io` E-07 and V-07 both name Section 11.1 | yes |
| D-2 | Must the test run in-process? | Yes, via `attention.run` | Subprocess with env-injected break hooks (rejected: requires production changes outside scope) | `tests/test_attention.py::_attsel_run`; E-04 in-memory patching requirement | yes |
| D-3 | How many excluded trees must E-01 observe? | Three, at least one outside walkthroughs/roadmaps | All five (rejected: `reviews` has no clean token since review filenames carry tracked plan id6s; `comms` and `docs-prompts` suffice to test the widened claim) | `resolve_selectors` probes for `fix-bar`, `ocman`, `mjx7ne` at HEAD `0ffb1e798` | yes |

### Round 1 close

All six findings FIXED in place; none OPEN or DEFERRED, so no escalation is owed. Both open questions
are `Blocking: no` and `resolved`. `aw ipd lint --phase review-finalize` conforming after edits. The
advisory `check.plan-spec-link-missing` (info) on this plan is intentional, as the plan's own
conventions section records.
