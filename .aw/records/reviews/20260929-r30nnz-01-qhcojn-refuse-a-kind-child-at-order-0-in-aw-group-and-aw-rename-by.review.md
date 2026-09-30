# Review findings: plan qhcojn

- Subject-Id: qhcojn
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-A01 (MEDIUM, fixed), PR-A02 (MEDIUM, fixed), PR-A03 (MEDIUM, fixed), PR-A04 (LOW, fixed), PR-A05 (LOW, fixed), PR-A06 (LOW, fixed)

## Round 1

Reviewed at HEAD `2da9f43f` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `conforming` after revision. `aw check plans` reported no finding
on this plan before or after.

THIS IS AN UNUSUALLY WELL-EVIDENCED PLAN AND I RE-RAN ITS WHOLE MEASUREMENT SET RATHER THAN READING IT.
Every one of its twelve authored findings reproduced, in a throwaway git repo driving the real CLI with
`PYTHONPATH` pinned to this lane (the plan is right that this pin matters; `ccbe60`'s hazard is real). F-01:
`aw group plans bbb222 --set newset --order 0 --rename --apply` on a seeded `Kind: child` exits 0 with no
warning, writes `- Order: 0` and the `-00-` filename, and the result then lints `IPD-M104: Order: child Order
must be an integer >= 1`. F-02: the metadata-only form wrote `- Order: 0` while the filename kept `-03-`, the
file contradicting its own name, exactly as claimed. F-03: `aw rename plans ccc333 --order 0 --apply` renamed
`-02-` to `-00-` and wrote `- Order: 0`, exit 0, confirming the second write site the backlog item's body
never considers. F-04, the constraint that decides the implementation: the multi-plan
`--order 0` call with the orchestrator named first correctly produced `-00-`/`-01-`/`-02-`, exit 0, so a
refusal keyed on the FLAG would break documented working behavior. F-05: 102 plans carry no `- Kind:` line
(100 `executed/`, 2 `not-executed/`, identical to the plan's split) and a seeded `Kind`-less plan regrouped to
Order 0 emits ZERO `IPD-M104`. F-09: a bare regroup preserved `-04-` and `- Order: 4`. F-10: preview printed
`--- would rename ... -00- ... ---` and exited 0. F-11: the orchestrator mirror wrote `- Order: 5` and lints
`orchestrator Order must be 0`. F-08: `aw ipd scaffold --kind child --set sc --order 0` exits 2. F-06: spec
`4w7d6s` is `Status: superseded` and carries a verbatim "REVERSED BY MAINTAINER DECISION 2026-09-10" banner,
with `2lcqno` keeping "its recovery command for the surviving case". F-12: `19313eed` deleted 797 lines and
`grep -rn '_preserved_order' tests/` is empty.

OQ-02 IS THE BEST THING IN THIS PLAN AND IT SURVIVES SCRUTINY EXACTLY. Its resolution is a HOW question
answered by demonstration, which is what the workflow asks for, and every value it cites is right:
`validate_metadata({'Kind':'child','Set':'x','Order':'0'})` yields exactly one `Order` error, `orchestrator`
at 0 yields none, a map with NO `Kind` key yields none (the silence F-05 needs), and `child` at 1 yields none.
Its warning is the load-bearing part and I confirmed it is not theoretical: the FULL return list is never
empty for a minimal map (6 or 7 unrelated missing-field errors), so an executor testing truthiness instead of
filtering `e.field == "Order"` would refuse every plan. That is precisely the trap an implementer falls into,
and the plan names it in three places.

F-07 DESERVES A SPECIAL NOTE BECAUSE I FIRST MEASURED IT AS FALSE AND IT IS TRUE. My initial probe gave
`errors 5`, exit 1, which contradicts the plan's `✓ CONFORMS` / exit 0 claim. The cause was my own fixture:
a minimal seeded plan carries no `- Item-Dependencies:`, which raises an unrelated ERROR-severity finding.
With that line added, `aw check plans` printed exactly `✓ CONFORMS  2 plans checked`, exited 0, and carried
`IPD-M104 Order: child Order must be an integer >= 1` at `"severity": "info"`. So the plan's most
counter-intuitive claim is correct, and the near-miss became PR-A05, because an executor seeding minimal
fixtures will hit the same false alarm and read it as their own regression.

WHAT REVIEW FOUND. Three MEDIUM findings, none of which undermines the approach; all three are things an
executor would have discovered the hard way.

PR-A01 is the one with real consequences. E-04 tells the executor to register `--allow-invalid-order` in the
shared noun-verb parser loop "one flag, both verbs". That loop iterates SIX verbs, not two. I verified that
`--order` already parses on `aw check plans --order 3` and on `find`, `search` and `index`, where it is inert,
so an unguarded `add_argument` hands four read verbs a flag they cannot honor. Two consequences the plan did
not state: the declaration must cover `rename`/`group` ONLY (the subset assertion is DECLARED minus ACCEPTED,
which I confirmed is `set()` today for both, so a narrow declaration passes while an over-declaration would
claim a read verb honors the flag), and the registration is better gated on `_verb in ("rename", "group")`,
a pattern that same loop already uses for `--status`. I also checked the thing the plan was about to edit
needlessly: both declarations already carry `exit_contract=(0, 2)`, so the new exit-2 refusal needs no
contract change.

PR-A02 is a scope-honesty finding. The backlog item lists exactly THREE acceptance criteria and a new FLAG is
not among them; its phrase "pass a deliberate override" PRESUMES an override rather than commissioning one.
That matters here specifically because OQ-01 refuses the orchestrator mirror ON SCOPE-FIDELITY GROUNDS, so the
plan refuses an undemanded RULE in one breath and adds an undemanded FLAG in the next without acknowledging
the asymmetry. I kept E-04, because the justification is sound and I made it explicit: a flag WIDENS what an
operator may do and cannot make a previously valid call fail, whereas the orchestrator rule would NARROW it
and could. But the plan now says this out loud, and names dropping E-04 whole as the correct fallback if the
maintainer prefers strict fidelity, rather than leaving a half-done flag.

PR-A03 is the live-artifact convention. The plan's "102 of 950" ratio appears seven times. The numerator and
the executed/not-executed split re-measured IDENTICAL (they are legacy files and stable), but the denominator
is already 1033, one day later. The claim never depended on the ratio, so it is now stated without one, and
the zero-plans-need-repair census is marked for re-derivation.

WHAT I DELIBERATELY DID NOT DO. I did not re-open OQ-01. Its refusal of the orchestrator mirror is correct on
the reasoning it gives, and the carrier it names is REAL: `oev4h7` exists at `.aw/records/backlog/open/` with
the measurement in its body, so the deferral is a genuine handoff rather than a gesture. I did not touch any
of the four declared paths, and I mutated no real plan (all probes were throwaway repos under a gitignored
path, removed afterwards; `git status --short` clean). I did not attempt to tighten the `--order`-on-six-verbs
oddity itself: it is pre-existing, harmless, and outside this plan's fence.

Bare suite at review HEAD: `3246 passed, 2 skipped, 3 warnings`. `aw sanitize --agent`: clean. No production
code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-A01 | MEDIUM | IN-SCOPE | C. Architecture / G. Plan executability | `cli.py`'s noun-verb loop iterates `check`, `find`, `search`, `index`, `rename`, `group`; verified `--order 3` parses on ALL SIX; `set(decl.legacy_flags) - accepted` is `set()` today for `rename` and `group`; both carry `exit_contract=(0, 2)` | **E-04 says "one flag on the shared parser, BOTH verbs", but the loop it names covers SIX verbs, so an unguarded registration gives four read verbs a flag they cannot honor.** The plan also did not say which declarations should gain it, and was silent on whether `exit_contract` needed widening | C:Low; U:Medium; S:Low; F:Low; Overall:Low | FIXED | New F-13 with the per-verb parse measurement. E-04 now states the six-verb reach, requires the declaration on `rename`/`group` ONLY (with the declared-minus-accepted direction as the reason a narrow declaration is correct), recommends gating on `_verb in ("rename", "group")` citing the loop's own `if _verb != "search"` precedent, and confirms rather than edits the already-sufficient `exit_contract`. V-04 requires the per-verb parse table and an explicit statement of which spelling was chosen. The doc-sync section's `--order` help-text instruction corrected from "BOTH verbs" to six |
| PR-A02 | MEDIUM | OVER-SCOPE | Scope fidelity | The backlog item's `IF BUILT` criteria read verbatim: refuse on `Kind: child` + resolved Order 0; permit orchestrator at 0 with a test; name plan and rule in the message. No flag is commissioned; "pass a deliberate override" presumes one | **`--allow-invalid-order` is the one thing this plan adds beyond its item's acceptance criteria, and the plan did not acknowledge it** while OQ-01 simultaneously refuses the orchestrator mirror ON SCOPE-FIDELITY GROUNDS. The unexplained asymmetry invites a reviewer to strike the wrong one | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-14. E-04 now states the over-scope plainly, gives the retention argument (a refusal with no escape hatch on a REPAIR path can block a repair, the item's own second hesitation), and resolves the asymmetry on a stated principle: a flag WIDENS and cannot break a valid call, the orchestrator rule would NARROW and could. Scope check gains an explicit over-scope entry naming it, replacing the bare "none". The fallback (drop E-04 whole, never ship it undeclared) is named in both places and in the gate |
| PR-A03 | MEDIUM | IN-SCOPE | G. Live-artifact re-derivation | Re-measured: 102 `Kind`-less plans (100 `executed/`, 2 `not-executed/`) IDENTICAL to the plan; total plans 1033 against the plan's 950; zero plans carry both `Kind: child` and `Order: 0`, confirmed over 1033 | **The "102 of 950" ratio appears seven times and its denominator is a LIVE count that moved 950 to 1033 in one day.** The zero-need-repair census is likewise asserted against the stale total | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-05 rewritten to carry the stable numerator and split, to record the denominator drift explicitly, and to state that the claim (SOME plans legitimately carry no `Kind`) never depended on the ratio. All seven occurrences de-ratio'd. The zero-need-repair deferral now says re-measure rather than trust either count |
| PR-A04 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | The gate's EXECUTION CONTRACT and POST-GATE LIFECYCLE paragraphs as authored | **Missing the scope fence stated as a DECLARATION and the conditional finalize ownership.** No `--scope-reason` route for the `ipd_schema.py` edit OQ-02 itself anticipates, no shared-checkout unstaging guidance, no paste-the-actual-output rule, and the transition instructed without naming the tooled path | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fence added as a declaration with `--scope-reason`/`--scope-ack`, naming `ipd_schema.py` as the anticipated case and the genuinely-unsafe stop cases (concurrent edit to a declared path, an absent cited symbol). Transition made tooled-only with `AW-LIFECYCLE-ROLE-001` ownership conditional. Shared-checkout unstaging, never-tag and paste-the-actual-output added |
| PR-A05 | LOW | UNDER-SCOPE | E. Testing (a false alarm an executor will hit) | A seeded fixture without `- Item-Dependencies:` makes `aw check plans` emit `check.ipd-missing-dependency-statement` at severity ERROR and exit 1; with the line added it printed `✓ CONFORMS  2 plans checked` and exited 0 | **A minimal seeded probe plan fails `aw check` for a reason unrelated to the Order rule**, which review hit while re-measuring F-07 and which an executor asserting on `aw check`'s exit code will read as their own regression | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-15 with the with/without comparison. E-01 now requires either `- Item-Dependencies: none` in every seeded fixture or an explicit statement that no assertion touches `aw check`; V-01 and the validation list carry the same requirement |
| PR-A06 | LOW | IN-SCOPE | E. Testing (an unsatisfiable assertion avoided) | A probe plan's lint emits `IPD-H202` structural codes beside the `IPD-M104`, confirmed at review | **The plan already warns that an exit-0 lint assertion can never pass for a probe file; review confirmed the specific codes**, and V-04 stated the warning without the evidence behind it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 now names `IPD-H202` as the measured companion code, so the reason an exit-0 assertion is unsatisfiable is grounded rather than asserted |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-A02: should `--allow-invalid-order` (E-04) be struck as over-scope, since the backlog item does not commission a flag? | Keep it, with the over-scope named explicitly and the retention argument stated | Striking E-04 and letting the message say "fix the Order"; leaving it unacknowledged as authored | A flag WIDENS what an operator may do and cannot make a previously valid call fail; the orchestrator rule OQ-01 refuses would NARROW and could. That asymmetry is principled rather than convenient, and it is the reason the two undemanded additions are treated differently. The item's own second hesitation is that a new failure mode on a REPAIR path can block a repair, which is exactly what an escape hatch answers, and a public flag is far cheaper to add now than after an operator is stuck. Striking it is a legitimate maintainer preference, so the plan now names that fallback and forbids the middle state (accepted but undeclared), which is the only genuinely bad outcome | yes |
| D-2 | PR-A01: should the new flag be registered loop-wide or gated to `rename`/`group`? | Do not impose one; require the executor to choose and STATE it, with the gated form recommended | Mandating the gated form; mandating loop-wide for symmetry with `--order` | Both are defensible and the choice turns on implementation detail I should not pre-judge: loop-wide matches how `--order` itself is registered today (and `--order` is already inert on four verbs, so the precedent exists), while gating is cleaner and the loop already does it for `--status` (`if _verb != "search"`). What is NOT optional is the DECLARATION, which must cover `rename`/`group` only, because the subset assertion runs declared-minus-accepted and an over-declaration would assert a read verb honors a flag it ignores. Requiring the choice to be stated makes either answer auditable | yes |
| D-3 | PR-A03: replace the stale `950` denominator with `1033`, or remove the ratio? | Remove the ratio; keep the stable numerator and split, and record the drift as the reason | Updating 950 to 1033; deleting the census entirely | Updating installs a figure that is stale again next week, which is the failure the re-derivation convention exists to prevent. Deleting the census loses the fact the constraint rests on. The numerator (102) and its executed/not-executed split are legacy files and re-measured IDENTICAL, so they are stable facts worth keeping exactly; the total is a live population and was never load-bearing, since the claim is only that SOME plans carry no `Kind` | yes |
| D-4 | OQ-01 refuses the orchestrator mirror and defers it to `oev4h7`. Should review overturn that and widen the predicate? | No; the refusal stands | Widening E-02's predicate by one clause (the fix really is that small); re-opening OQ-01 as a maintainer question | Verified the mirror gap is real (an orchestrator regrouped to `--order 5` writes `- Order: 5` and lints `orchestrator Order must be 0`) and that the fix would be one clause. But the item's acceptance criteria say an orchestrator at 0 must be "permitted unconditionally" and say nothing about policing orchestrators elsewhere, and the item's own third reason warns this conditionality is "easy to get wrong". Decisively, the carrier is REAL rather than gestural: `oev4h7` exists at `.aw/records/backlog/open/` carrying the measurement, so nothing is lost. Adding an unasked second rule to a `low`-priority followup is how a narrow plan becomes unreviewable | yes |
| D-5 | OQ-02 resolves the predicate's home by measurement. Should review accept it, or require the predicate be extracted into `ipd_schema`? | Accept it as resolved; calling `validate_metadata` with a minimal field map is correct | Requiring extraction into `ipd_schema`; requiring a local predicate in `plans_refs` | Re-ran all four cases the resolution cites and every value matched, including the critical negative (a map with no `Kind` key yields no `Order` error, which is the silence the 102 `Kind`-less plans need). This is a HOW question resolved by DEMONSTRATION, which is the standard the workflow sets, and it needs no edit to the file the plan deliberately leaves undeclared. The resolution's own warning is the load-bearing part and is not theoretical: the unfiltered list carries 6 or 7 unrelated errors for a minimal map, so filtering on `e.field == "Order"` is mandatory and the plan says so three times. Extraction remains available as a stated scope change if the executor judges it necessary | yes |
| D-6 | Is `- Work-Kind: followup` at `- Priority: low` with no release gate correct, given the verbs write a schema-invalid state? | Yes, unchanged | Reclassifying as `bug` and gating the next release | The accidental path is already closed by `e3hzyc` (verified: a bare regroup preserved `- Order: 4`), so only an EXPLICIT `--order 0` typed at a child reaches the defect, which is rare rather than user-perceptible in normal use. The written state is also detected (by `aw ipd lint`) and no plan in the tree is currently in it (measured: zero). That combination is latent risk and self-inconsistency rather than measured user harm, which puts it outside the auto-gating `bug` set on the repository's own perceptibility test. The plan reasons this out explicitly instead of inheriting it silently | yes |
