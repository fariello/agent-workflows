# Review findings: plan 3fat1n

- Subject-Id: 3fat1n
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `561c9a7f` in a lane worktree; the plan was authored against `e203df44`. Structural
preflight `aw ipd lint --phase author --agent` CONFORMED before revision (exit 0, `findings: 0`) and
`--phase review-finalize --agent` conforms after revision with zero findings and zero advisories. No
pre-review snapshot was owed: the plan was committed and unmodified with `git status --porcelain` empty
at review start. The plan carries `- Kind: child`, so the `IPD-S407` orchestrator row check does not
apply. Every behavioral claim was re-driven through the REAL pinned hooks (`pre-commit-hooks` v4.6.0,
`ruff-pre-commit` v0.4.4) rather than read; the config and one tracked research `.py` were temporarily
modified and restored with path-scoped `git checkout --`, all probe files deleted, and
`git status --short` verified empty afterwards.

EVERY MEASUREMENT IN THIS PLAN REPRODUCES, AND THE BEHAVIORAL ONES REPRODUCE EXACTLY. F-1: the counts
are `0` tracked files under `.aw/records/docs/research`, `0` under `.agents`, `139` under
`.aw/records/research`, `160` under `.aw/system`, and `2` research `.py` files. F-2: identical probe
files in the live and the dead tree, both fixers reporting `Fixing
.aw/records/research/_probe_rev4.md`, md5 `10d4d198...` -> `9f5911cc...` for the live copy while the
dead copy stayed `10d4d198...`. F-3: appending `x   =   1` to the tracked research `broker.py` and
running `ruff-format` reported `1 file reformatted` and the line came back `x = 1`. F-10: under the
four-occurrence substitution both fixers report `Skipped` with md5 unchanged and `ruff-format` reports
`Skipped` leaving `x   =   1` in place. F-7's spec citations, F-8's writer tuple and its config-deferring
comment, F-9's legacy fallback, F-11's template contents, F-12's absent coverage, F-13's four-and-only-four
`exclude` keys, and F-14's `.aw/system/` all verify by reading. The diagnosis, the direction, and the fix
are right.

THE DOMINANT FINDING IS A CONTRADICTION BETWEEN E-01 AND E-03(a) THAT WOULD MAKE THE CORRECTED CONFIG
FAIL ITS OWN NEW TEST. E-03(a) says to build the parity probe paths FROM
`_VERBATIM_PRESERVED_SEGMENTS` "rather than hardcoding them" and assert each is excluded by all four
mutating hooks. That tuple has THREE entries, and the third is `(".aw", "records", "docs", "research")`,
which is precisely the alternative E-01 DELETES. Driven at review against a simulated post-E-01 config:
the two live trees report `excluded=True` on all four hooks and `.aw/records/docs/research/x.py` reports
`excluded=False` on all four, so a literal derivation is RED on the fix. The plan's own prose names only
the two live trees, so the intent is right and only the derivation is under-specified. What makes this a
BLOCKER rather than a nit is the repair an executor would most plausibly reach for: restoring
`\.aw/records/docs/research/` to the regex to go green, which re-adds the exact misleading dead path this
plan exists to remove and would leave a passing test certifying it. The second plausible repair, editing
the writer tuple, touches a file outside `- Scope-Paths:` that is correct as written (the writer's job is
to pass a file through byte-for-byte wherever it finds one, including a path no new install creates).

THE SECOND FINDING IS THAT ONE OF THE PLAN'S OWN STOP CONDITIONS IS WRONG, AND IT WOULD HAVE STOPPED A
CORRECT EXECUTION. The gate tells the executor to STOP if E-03(b) "cannot distinguish the
intentionally-retained `.agents/docs/research/` from a genuinely dead path without an allowlist that
would also hide a future stale entry". That is not a hypothetical to discover, it is the design as
specified: the allowlist necessarily hides exactly one future case, a later flattening of
`.agents/docs/research` (the same rewrite `_RECORDS_SUBPATH_REWRITES` already performed on its `.aw/`
twin). Measured at review, (b) passes for the right reasons and its blind spot is inherent, because the
path is legitimately absent HERE and live in a legacy target, so nothing on disk can check it. So the
honest action is to RECORD the limit, not to stop; leaving the stop condition as written invites an
executor to halt on a resolved question, and deleting case (b) instead would remove the one check that
would have caught the original bug.

THE THIRD IS SMALLER BUT IS AN ATTRIBUTION DEFECT. Both resolved open questions carried
`- Owner: none`. The linter only verifies the field is non-empty and not `none`, and these were resolved
on the author's own authority from repository evidence, which the workflow requires be recorded as a
decision with an owner. `none` asserts that nobody owns a judgement somebody made.

WHAT THIS REVIEW DID NOT CHANGE, AND WHAT IT PRAISES. The plan is honest in the places these reviews
usually find inflation. F-5 is exemplary: it catches its own naive measurement (invoking `ruff` on
explicit filenames bypasses `pre-commit`'s type filter and reports a much larger exposure) and reports
the honest number as 2 rather than 139. F-4 states that nothing is currently dirty, so the fix is
preventive. The severity paragraph argues both directions and lands on MED with reasons. V-01 already
demands md5 pairs rather than accepting a `Skipped` line, which is exactly the right standard and is the
distinction three sibling plans in this sweep needed pointing out. And ALONE IN THIS SWEEP, E-04 pins no
stale failing baseline: it asks for green and requires any failure be named pre-existing or admitted as
new, which is the correct posture. I re-measured and the suite is green at `3087 passed, 2 skipped`; I
added that figure with an explicit instruction to re-derive rather than compare, because the count moved
3069 -> 3075 -> 3081 -> 3087 across four reviews in this one sweep.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-B01 | BLOCKER | IN-SCOPE | E. Testing / A. Correctness | `artifact_core._VERBATIM_PRESERVED_SEGMENTS`'s three entries including `(".aw","records","docs","research")`; plan E-01 (delete that alternative) against E-03(a) (derive probes FROM the tuple); review probe over a simulated post-E-01 config printing `excluded=False` on all four mutating hooks for `.aw/records/docs/research/x.py` | **E-03(a) TAKEN LITERALLY IS RED AFTER E-01**, because the writer tuple still carries the path E-01 deletes. The danger is the repair: an executor facing a red test on the corrected config would most plausibly restore `\.aw/records/docs/research/` to the regex, re-adding the misleading dead path this plan exists to remove and shipping a passing test that certifies it. The alternative wrong repair edits `artifact_core.py`, which is outside `- Scope-Paths:` and correct as written. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (filter one tuple entry; demonstrated) | FIXED | E-03(a) now states the filter explicitly with the measurement, names the reason the `docs/research` entry is excluded from the HOOK probe set but retained in the writer tuple, and FORBIDS both wrong repairs. Its Expected outcome states that a red (a) on the corrected config means the derivation was taken literally. V-03 requires the derived probe set pasted and `artifact_core.py` shown unmodified. New F-15. |
| PR-B02 | HIGH | IN-SCOPE | G. Plan executability (stop conditions) | The gate's stop condition on E-03(b)'s allowlist; review probe printing `.agents/docs/research/ exists=False allowlisted=True`, `.aw/records/research/ exists=True`, `.aw/system/ exists=True`; `layout_inventory._RECORDS_SUBPATH_REWRITES` carrying `("docs/research/", "research/")` | **A STOP CONDITION WOULD HALT A CORRECT EXECUTION.** The gate says to stop if (b)'s allowlist "would also hide a future stale entry", but that is the design as specified rather than a defect to discover: the allowlist necessarily hides exactly one case, a later flattening of `.agents/docs/research`. The limit is inherent (the path is legitimately absent here and live in a legacy target, so nothing on disk can check it), so the correct act is to record it. As written, an executor either halts on a resolved question or deletes the one case that would have caught the original bug. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The stop condition rewritten: the allowlist tension is declared already resolved with the measurement, stopping is narrowed to "(b) cannot be made to fail on the pre-change regex at all", and E-03(b) now requires the blind spot recorded in the test docstring with the note that a legacy-layout change needs a hand re-check. New F-16. |
| PR-B03 | MEDIUM | IN-SCOPE | G. Plan executability (attestation) | Both open questions carrying `- Owner: none`; `ipd_lint`'s `has_owner` passed to `ipd_schema.open_question_error` as a bare boolean that never inspects the value | BOTH RESOLVED QUESTIONS DISCLAIM THEIR OWNER. Each was resolved on the author's own authority from repository evidence, which the workflow requires be recorded as a decision naming whose judgement it was; `none` asserts nobody owns a judgement somebody made, and no mechanical check catches it because the linter only tests non-emptiness. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both set to `- Owner: plan author`, and OQ-01 records the correction with its reason so the change is auditable rather than silent. |
| PR-B04 | LOW | IN-SCOPE | D. Anti-regression | Bare `python3 -m pytest` at review printing `3087 passed, 2 skipped, 3 warnings in 146.30s`; the sweep's own progression 3069 -> 3075 -> 3081 -> 3087 | E-04 STATES NO BASELINE AT ALL. This is the RIGHT posture (uniquely in this sweep it pins no stale failing count), but it leaves the executor without a reference and without the instruction that makes a reference safe. Recorded as LOW and fixed by adding the measurement together with an explicit re-derive instruction, rather than by pinning the number. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now carries the review-measured green baseline, states the bar as ZERO failures, and requires the count RE-DERIVED at lane start rather than compared, citing the four-value drift inside a single sweep as the reason. The existing correct posture is explicitly endorsed so a later editor does not "helpfully" pin a figure. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | E-03(a)'s tuple-derived probe set includes the path E-01 deletes. Filter the probe set, keep the dead alternative in the regex, or edit the writer tuple? | FILTER THE PROBE SET to the trees the hooks must exclude, and say why in the test. | (a) Keep `\.aw/records/docs/research/` in the regex so a literal derivation passes - REJECTED: that is the misleading dead text the whole plan exists to remove, and F-7 establishes (spec `20260817-2124-01` G4 plus Non-goals) that no supported layout can populate it, so the alternative would be permanently false. (b) Remove the entry from `_VERBATIM_PRESERVED_SEGMENTS` - REJECTED twice over: `artifact_core.py` is not in `- Scope-Paths:`, and the tuple is CORRECT for the writer, whose contract is to pass a file through byte-for-byte wherever it finds one, including in a partially-migrated checkout the hooks will never see. The two lists are legitimately allowed to differ on a dead path. | Review probe over a simulated post-E-01 config printing `excluded=False` on all four hooks for the `docs/research` probe; the three-element tuple; spec G4 and Non-goals; the plan's own prose naming only two trees | yes |
| D-2 | (b)'s allowlist hides one future stale case. Stop as the gate says, delete case (b), or record the limit? | RECORD THE LIMIT in the test docstring and narrow the stop condition. | (a) Stop and report as the gate instructs - REJECTED: the tension is the specified design rather than a discovered fault, and halting on it burns a run over a question already answered. (b) Delete case (b) - REJECTED: it is the single case that would have caught the original bug, and the plan's own gate rightly says a check that cannot fail is worse than none; the remedy for a known blind spot is documentation, not deletion. (c) Replace the allowlist with a live-layout probe - REJECTED as impossible here: this repo has no `.agents/` tree, so there is nothing on disk against which to distinguish "absent because legacy" from "absent because stale". | Review probe showing (b) passing for the right reasons; `_RECORDS_SUBPATH_REWRITES`'s `docs/research -> research` rewrite as the migration shape that would trigger it; `research_contract.resolve_research_root`'s legacy fallback | yes |

### Deferred and open

None. Every finding is FIXED, including the BLOCKER (PR-B01). No finding was left OPEN or DEFERRED, so
no escalation to a `- Blocking: yes` open question is owed under the repository's `HIGH` gate threshold.
Both of the plan's open questions were already `resolved` and remain so, with their direction
INDEPENDENTLY RE-DRIVEN at review rather than accepted: OQ-01's "keep the intent, fix the regex" is
supported by all three probes reproducing (F-17), and OQ-02's asymmetry (drop `.aw/records/docs/research`,
keep `.agents/docs/research`) is supported by the spec's design-level unreachability of the first against
the live legacy fallback for the second. Their `- Owner:` fields were corrected from `none` to
`plan author` (PR-B03). All five Carrier-Declined dispositions are correct: each records a rejected
direction or a measured non-defect rather than outstanding work, and F-13's measurement genuinely retires
the general-config-audit idea rather than deferring it. No decision above carries `Reversible: no`.

THE RELEASE GATE IS CORRECTLY INHERITED. Backlog `nmg89m` carries `- Blocks-Release: next` and
`- Work-Kind: bug`; the plan declares both and its gate paragraph states the handoff preserves the gate
via `- From-Backlog: nmg89m`, which matches the repository's close-legitimacy rule. The `bug`
classification is supported by measurement rather than asserted: the mutating hooks really do rewrite an
as-delivered artifact at commit time, silently, which is user-perceptible in the sense the perceptibility
ruling describes.

FINAL GATES: `aw ipd lint --phase author --agent` exit 0 `findings: 0` before revision;
`--phase review-finalize --agent` exit 0 `findings: 0` after, with zero advisories; bare
`python3 -m pytest` -> `3087 passed, 2 skipped, 3 warnings in 146.30s`; `aw check` unchanged at its
pre-existing findings with none on this plan; `aw sanitize --agent` clean; the config and the tracked
research `.py` restored with path-scoped `git checkout --`, every probe file deleted, and
`git status --short` showing exactly the plan (modified) and this record (new).
