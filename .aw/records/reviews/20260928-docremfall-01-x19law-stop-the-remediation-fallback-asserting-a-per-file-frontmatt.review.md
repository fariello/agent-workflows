# Review findings: plan x19law

- Subject-Id: x19law
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `f3f0d52c` in a lane worktree. No pre-review snapshot was needed: the plan was
committed and unmodified, and the lane-input copy is byte-identical to the tracked file (`diff`
reported no output). Structural preflight `aw ipd lint --phase author --agent` reported `clean` /
exit 0 with no advisories; `--phase review-finalize` still conforms after every revision below.

EVERY AUTHORED FINDING REPRODUCED AND NONE NEEDED CORRECTION. That is rare enough to state plainly,
and it changes what this review is: the plan's diagnosis is sound, so my contribution is four
CALIBRATIONS rather than repairs. I re-derived each load-bearing measurement independently, and
where I could use a different method than the plan did, I did.

F-01, exact on all four fields:

```text
title         = 'cross-tree collisions NOT checked by a per-type run'
summary_fix   = 'inspect artifact frontmatter and schema conformity.'
detailed_fix  = 'inspect <collisions> frontmatter and schema conformity.'
command       = None
file_path     = '<collisions>'
```

F-02 re-derived by AST WALK rather than the plan's bracket-matching regex, which matters because my
first regex pass found only 10 sites and missed the multi-line calls; the AST agrees with the plan
exactly:

```text
AST census: sentinel-located Drift( sites = 12
distinct sentinels = 10 -> ['<artifacts>', '<attention>', '<collisions>', '<git>', '<layout>',
                            '<push>', '<pypi>', '<sanitizer>', '<setup>', '<version>']
sites on the generic fallback: 7
```

and only `<collisions>` passes a `recovery=` kwarg, confirming F-04's account of the five
`doctor.probe-failed` producers.

F-03 IS THE FINDING THE WHOLE PLAN TURNS ON AND IT REPRODUCES EXACTLY. Staging `iyilwm` E-01's
preference and re-running all 7 sentinel sites:

```text
  <collisions>  check.collisions-not-checked   CURED
  <push>        check.push-unauthorized        STILL BROKEN
  <git>         doctor.probe-failed            STILL BROKEN
  <version>     doctor.probe-failed            STILL BROKEN
  <attention>   doctor.probe-failed            STILL BROKEN
  <artifacts>   doctor.probe-failed            STILL BROKEN
  <sanitizer>   doctor.probe-failed            STILL BROKEN

iyilwm alone: CURED 1, STILL BROKEN 6 of 7
```

So the sibling's claim to "substantially satisfy" this item IS an overstatement, the two plans are
genuinely orthogonal, and the plan is right not to be superseded by it.

F-05 and F-06 both hold, the second by construction as claimed:

```text
CLAIM2 rglob calls: 0
returned tuple: ('cross-tree collisions NOT checked by a per-type run', '<collisions>',
                 '<collisions>', '', 'inspect <collisions> frontmatter and schema conformity.')

member         caught_by_first_branch  would_reach_else
  <git>          True                   False        (all 7 identical)
```

F-10's differential re-run with my own corpus: `cases compared: 54   behavioral differences: 0`.
Authoring measured 57 pairs; both are zero-difference, which is why PR-704 makes the pair count
explicitly not the bar.

PR-701 IS THE CALIBRATION MOST WORTH A HUMAN'S TIME. The plan's Goal says the report "currently
tells the reader to inspect the frontmatter of `<collisions>`, `<sanitizer>` or `<git>`", and its
approval paragraph says "6 sentinel-located findings ... stop printing a false instruction". Both
are true. But a human reading them will reasonably expect their terminal to get quieter, and
measured on a real surface it barely does:

```text
aw check plans --json : 26 findings
  sentinel-located    : 1   (<collisions>)
  real-path           : 25  (ipd-uncarried-obligation 18, ipd-lint-diagnostic 3,
                             lifecycle-transition-invalid 2, review-decision-unescalated 1,
                             ipd-carrier-finished-unverified 1)
all 6 of those rule ids reach the terminal fallback
```

So that surface goes from 26 frontmatter sentences to 25. This is NOT an argument against the plan
and I did not treat it as one: a false claim about a non-file is a worse defect than a vague claim
about a real file, and the five crash-path probes are exactly the findings a human reads under
pressure. But the plan should not be approved on a misunderstanding of its size, so the Goal, the
approval paragraph, the scope check and a new V-01(g) now state it, and V-01(g) explicitly forbids
writing a report claiming the sentence was eliminated.

PR-702 corrects a deferral row in the direction of MORE work for the carrier, not less. The row says
`cli._run_check` "writes the human fix string back into each finding's structured `recovery` field
... for those rules". Measured, it is unconditional and total: `_run_check` computes the categorized
`fix` then calls `enrich_drift(d, recovery=fix or "")`, and `enrich_drift` resolves
`recovery or drift.recovery`, so the categorized string WINS over any producer-authored recovery.
All 26 findings report a non-empty `recovery` and every one is the rendered human line, meaning the
agent surface currently has no independent recovery field at all for these rules. That makes
`2cnvh1` a bigger item than implied and confirms it must stay outside this fence.

PR-703 calibrates OQ-01 without changing its decision. I tested order-independence rather than
accepting the argument, composing both fixes in both source orders:

```text
  <collisions>   rec=True   same=False   ('aw check all' vs the sentinel sentence)
  <sanitizer>    rec=False  same=True
  <push>         rec=False  same=True
  real path      rec=True   same=True
  real path      rec=False  same=True
```

Order-independent for 6 of 7 sites and for real paths; different on the one shared site, where both
outcomes are honest and neither mentions frontmatter. The no-edge decision stands, and V-01(d)
already anticipated exactly this. I recorded it so nobody later tests byte-equality across merge
orders and reads a designed difference as a regression.

TWO THINGS I CHECKED AND FOUND CORRECT, recorded so the silence is not read as an oversight. The
Step 0 claim that `tests/test_doctor.py::DoctorRemediationTests::test_remediation_family_guard`
asserts no `<`/`>` in any non-None `command` is accurate, which genuinely does constrain E-01 to put
sentinel text in the fix strings and keep `command=None`. And the `title` workaround is real:
`check_engine.check_collisions` keeps its detail under 60 characters to exploit
`title = detail if len(detail) < 60 else rule`, so the scope fence's prohibition on touching that
expression is load-bearing and V-02(c) is right to pin it mechanically.

RIGHT-SIZING: four E-items over two files, each one concern, with E-04 a comment-only item that is
justified because it carries the cross-plan pointer OQ-01's no-edge decision depends on. No
`IPD-Z602` fired. P16 is satisfied: every prescribed test drives real functions and asserts on
returned values. The plan's own "two ways this can fail silently" paragraph (a vacuous test against
a branch-owning rule, and accepting E-03 on argument rather than differential) is the best such
section I have reviewed in this repository and I added nothing to it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | MEDIUM | IN-SCOPE | F. KISS/UX; G. Plan executability | plan Goal (quoted "tells the reader to inspect the frontmatter of `<collisions>`, `<sanitizer>` or `<git>`"); approval paragraph (quoted "6 sentinel-located findings ... stop printing a false instruction"); `aw check plans --json` at review | The plan's framing invites a reader to expect the frontmatter sentence to disappear, and measured it barely moves: of 26 findings on `aw check plans` exactly 1 is sentinel-located, so that surface goes 26 -> 25, not to 0. The other 25 are real-path findings over 5 rules that all reach the same fallback and that neither this plan nor `iyilwm` touches unless their producers gain a recovery. Approving on the wrong size is the risk. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13 with the measurement and the argument for why the plan is still worth doing (false versus vague; the five crash-path probes). Added a "what this Goal does not claim" paragraph, a calibration sentence to the approval paragraph, and a sizing note to the scope check's under-scope row. Added V-01(g) requiring the executor to report before/after frontmatter counts and the sentinel share, and FORBIDDING a report that claims the sentence was eliminated. |
| PR-702 | MEDIUM | IN-SCOPE | A. Correctness; C. Architecture | plan's `2cnvh1` deferral row (quoted "will also appear in the machine record for those rules"); `cli._run_check`'s `enrich_drift(d, recovery=fix or "")`; `check_engine.enrich_drift`'s `recovery=recovery or drift.recovery` | The deferral row understates the overwrite: it is unconditional and total, not scoped to fallback rules. The categorized fix WINS over any producer-authored recovery, and all 26 findings on the measured surface report a `recovery` equal to the rendered human line, so the agent surface has no independent recovery field for these rules at all. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14 with the two quoted resolution lines and the 26-of-26 measurement, and amended the deferral row to state the true scope. This makes carrier `2cnvh1` larger and better justified rather than smaller, and confirms the deferral (the fix needs `cli.py`, outside this fence) is correctly placed. |
| PR-703 | LOW | IN-SCOPE | C. Architecture and operability | plan OQ-01 (quoted "composable in either order"); compose-both probe over 5 cases | OQ-01's order-independence claim is true of the OUTCOME SET and of the output for 6 of the 7 sentinel sites, but NOT of the output on `<collisions>`, the single site both plans touch, where the two source orders yield `aw check all` versus the sentinel sentence. Both are honest, so the no-edge decision is unaffected, but the unqualified phrasing invites a later reader to test byte-equality across merge orders and read a designed difference as a regression. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-15 with the per-case `same=` table, and calibrated OQ-01 in place to say the claim is exactly true of the outcome set and of 6 of 7 sites, naming the one divergence and why it is not a correctness problem. Cross-referenced V-01(d), which already required the executor to account for both orderings. |
| PR-704 | LOW | IN-SCOPE | E. Testing (evidence bar) | plan validation item 4 and F-10 (quoted "Authoring measured 57 pairs with 0 differences") | The differential proof's pair COUNT reads like part of the bar. Review reproduced the same proof with a differently-sized corpus (54 pairs, 0 differences), so a count is an artifact of corpus construction and an executor matching 57 would be chasing a number rather than the property. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Validation item 4 now records both the authoring and the review counts and states explicitly that only ZERO DIFFERENCES is the bar and neither number may be transcribed. Also recorded review's own re-measured suite baseline (`3246 passed, 2 skipped`, plus `35 passed` for `tests/test_doctor.py`) with a note that its coincidental stability across two heads is not a licence to transcribe it. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------------|-------------------------|-------|------------|
| D-1 | The plan's approval paragraph itself asks the reviewer to decide whether this and `iyilwm` should be ONE change, in which case this plan should be superseded. Supersede, merge, or keep both? | KEEP BOTH, executing independently with no dependency edge. | (a) Supersede this plan in favor of `iyilwm`: rejected on measurement, not on preference. `iyilwm` cures 1 of the 7 sentinel sites and leaves 6, including every `doctor.probe-failed` producer, so superseding would drop the majority of the defect `cciw6g` reports. (b) Merge them into one plan: rejected, `iyilwm` is already `reviewed` with `Readiness: go-pending-approval`, so merging would discard a completed review and re-open an approved-pending change for no correctness gain; the two edits are additive in the same function and the runners isolate each item in its own worktree with a merge-and-revalidate gate. (c) Add an `Item-Dependencies` edge: rejected, see OQ-01 and D-2; an edge asserts a required ordering that does not exist and would make this plan `dependency-blocked` behind a plan awaiting human approval. | Measured 1-cured / 6-still-broken with `iyilwm` staged; its frontmatter (`Status: reviewed`, `Readiness: go-pending-approval`, identical `Scope-Paths`); the AST census showing only `<collisions>` carries a `recovery=`. | yes |
| D-2 | OQ-01 claims both fixes are composable in either order. Accept the argument, or test it? | TEST IT, and calibrate the claim on the result rather than either accepting or rejecting it wholesale. | (a) Accept the plan's reasoning: rejected, the workflow requires a HOW resolution to cite a demonstration, and "composable" is a mechanism claim; F-10 demonstrated the two composing but the ORDER question was argued rather than measured. (b) Mark OQ-01 unresolved and raise it blocking: rejected once measured, because the divergence is confined to one site and both outcomes are honest, so nothing is blocked. (c) Require the plan to pick an order (e.g. mandate the sentinel test first): rejected as over-specification that would create a real dependency between two plans that currently have none, which is the thing OQ-01 correctly avoids. | Compose-both probe: `same=True` for `<sanitizer>`, `<push>` and real paths with and without a recovery; `same=False` only for `<collisions>`, yielding `aw check all` or the sentinel sentence; neither output contains `frontmatter`. | yes |
| D-3 | The plan's population claim (6 sentinel findings fixed) is true but small against a real surface. Raise this as a finding, or leave it since every stated fact is accurate? | RAISE IT as PR-701 and fix the FRAMING, while changing no E-item. | (a) Say nothing because no statement is false: rejected. Every sentence is accurate and the aggregate impression is still misleading, and a human approving a `Blocks-Release: next` bug deserves its true size; the repository's own guidance is that honest documentation beats technically-true documentation. (b) Recommend widening scope to fix the real-path population too: rejected, that is `iyilwm`'s territory for recovery-bearing rules and would require `check_engine.py` edits for the rest, both outside this fence, and it would convert a reviewable two-function fix into a broad one. (c) Recommend lowering the priority: rejected, priority is the maintainer's call and the crash-path probes justify the `bug` classification regardless of count. | `aw check plans --json`: 26 findings, 1 sentinel-located; all 6 involved rule ids measured reaching the terminal fallback; the five `doctor.probe-failed` producers from the AST census. | yes |
| D-4 | Should the review re-verify E-03's behavior-preservation itself, or accept F-10's differential? | RE-VERIFY with an independently constructed corpus. | (a) Accept F-10: rejected, the plan's own gate paragraph says a green suite is insufficient and that the differential IS the evidence, so a reviewer taking the differential on trust applies a weaker standard than the plan sets for its executor. (b) Re-verify only the reachability argument (F-06): rejected, that is the static argument the plan itself says is convincing but insufficient. (c) Demand a larger corpus than the plan specifies: rejected, the specified corpus already includes the only inputs that can distinguish the predicate from the membership test (`<half`, `half>`, `<>`), which is the property that matters. | Independent differential over 54 pairs including all 7 former tuple members, 4 non-tuple sentinels, real nested and bare paths, the empty string and all three malformed inputs: 0 behavioral differences. | yes |

### Deferred and open

- (none). All four findings were FIXED in place. No finding reached the repository's gate threshold
  (`review_findings_gate.block_at`, default `HIGH`) at any severity, so no escalation to a
  `- Blocking: yes` open question was required, and none was warranted.
- All three pre-existing open questions (OQ-01, OQ-02, OQ-03) remain `Blocking: no` /
  `Status: resolved`. OQ-01's resolution was CALIBRATED under PR-703 and D-2 without changing its
  decision; OQ-02 and OQ-03 were re-checked and stand as written (the `file_path` inertness claim
  verified: `_categorize_drift`'s `loc = rem.file_path or d.location` is the single read site, and
  the returned tuple is identical either way; the no-constant decision verified against the four
  shipped inline-predicate sites).
- No `Reversible: no` decision was taken. No backlog item was created: all three carriers the plan
  names (`iyilwm`, `2cnvh1`, `cciw6g`) were verified to exist and to say what the plan claims.
