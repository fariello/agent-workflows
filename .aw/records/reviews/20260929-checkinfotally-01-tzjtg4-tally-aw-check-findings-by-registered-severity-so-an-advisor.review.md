# Review findings: plan tzjtg4

- Subject-Id: tzjtg4
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at lane HEAD `c27346dc` in an isolated worktree. Structural preflight `aw ipd lint --phase author`
reported `clean` (`findings: 0`) before any edit; re-run at `--phase review-finalize` after revisions, also
clean. No pre-review snapshot was owed: the plan was committed and unmodified. Bare suite at review HEAD:
`3246 passed, 2 skipped, 3 warnings in 49.09s`. NO PRODUCTION FILE, TEST, OR BACKLOG ITEM WAS MODIFIED by
this review; the only mutating-looking probe I ran was a direct call to the read-only
`check_engine.evaluate_blocking_close` predicate, which computes a verdict and writes nothing.

THE DEFECT AND THE FIX ARE BOTH EXACTLY AS DESCRIBED, and every code-level claim reproduces at review.
`RULE_REGISTRY` holds 52 rules with severities 33 `error` / 12 `warning` / 7 `info` and ZERO ids beginning
with `warn`, so `warn_cnt` is unconditionally 0 and `err_cnt` is unconditionally `len(drift)`; the two
counters are the only `startswith("warn")` callers under `agent_workflows/`; the self-contradiction renders
live (`aw check specs` shows `CONFORMS`, `errors 1   warnings 0`, exit 0, and the same run's
`--json data.policy_findings` shows that single finding is `info`); `enriched.severity` is genuinely already
computed in the loop immediately above and already fed to the adjacent `Diagnostic`; `drift_exit_code` is
exactly the quoted one-liner and correctly exempts `info`; the renderer collects scalar Evidence keys
generically so a third bucket needs no renderer edit; the compact `--agent` record really does project
evidence to `['inventory', 'rules']`; no test anywhere asserts on this row; and neither
`docs/cli-output-contract.md` nor `docs/cli-human-guide.md` mentions `warnings`. F-01 and F-04 through F-07
are all confirmed, and the plan's judgement on OQ-01 (give `info` its own bucket) is right for the reason it
gives: `drift_exit_code` already treats `info` as categorically different from `warning`.

ONE BLOCKER WAS FOUND, AND IT IS NOT IN THE FIX. F-03's premise has expired under the plan: the related
backlog item `xqm16x` is no longer an `open` duplicate that this plan may tidy up. It is `graduated`, carries
`- Graduated-To: sevtruth`, and its `- From-Backlog:` carrier is pending plan `nwcf8j`, authored the same
day, which declares `- Item-Dependencies: executed:tzjtg4` on THIS plan and fixes the same defect CLASS at
two surfaces this plan never touches. E-05's instruction to close it would therefore have discharged another
carrier's inherited release gate for work this plan does not perform. What makes it a BLOCKER rather than a
tidiness finding is that it would have SUCCEEDED rather than failed closed, which I verified by calling the
shipped predicate directly.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | BLOCKER | OVER-SCOPE | A (correctness) / D (release-gate integrity) | plan E-05, F-03, Deferred, Scope check, gate; `.aw/records/backlog/graduated/20260920-xqm16x-...`; `.aw/records/plans/pending/20260929-sevtruth-01-nwcf8j-...`; `check_engine.evaluate_blocking_close` | E-05 instructs the executor to close backlog `xqm16x` on this plan's executed evidence, on F-03's premise that it is an `open` DUPLICATE fixed by the same two lines. BOTH halves are false at review. It is `graduated` with `- Graduated-To: sevtruth`, and its carrier is pending plan `nwcf8j`, which declares `- Item-Dependencies: executed:tzjtg4` on this plan, fixes the same class at `doctor.py` (measured dropping 63 of 87 findings from the rendered summary) and `attention.py` (hardcoded `severity="error"`), and whose gate says "do NOT edit `agent_workflows/cli.py`: that is `tzjtg4`'s fence". So `xqm16x` is the BROADER item, correctly split, not a duplicate. THE CLOSE WOULD NOT FAIL CLOSED: verified at review, `evaluate_blocking_close(root, <xqm16x>, "done", evidence=<this plan>)` returns `legitimate=True, path='SATISFIED'`, because a resolvable in-tree citation satisfies the gate on its own. This plan would therefore silently discharge `nwcf8j`'s `- Blocks-Release: next` for the doctor and attention defects it does not fix, leaving that plan holding a gate against an already-`done` item | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | E-05's close instruction REMOVED and replaced with an explicit prohibition carrying the measurement and the reason; F-03 rewritten to record the real ownership split while keeping its still-accurate content observations; the Deferred row converted from "resolved by E-05" to a `Carrier-Declined` explaining that each item already has its own carrier; Scope check no longer claims the close as justified over-scope; the gate's approver note and lifecycle paragraph both corrected; and V-05 now REQUIRES the negative proof (no `.aw/records/backlog/` file modified, `xqm16x` still `graduated`) |
| PR-702 | MEDIUM | IN-SCOPE | F (honest documentation) | plan F-03 ("Both are `open`"), Deferred, gate ("there is a DUPLICATE open item") | Three separate places state or rely on both items being `open`, and one states this plan "closes `xqm16x`". All three are stale: `aw find backlog` reports `xqm16x`, `zosk0a` AND `ct1n04` all `graduated`. Left as written, an approver weighs a duplicate-cleanup benefit that does not exist, and an executor looks for an `open` item in `.aw/records/backlog/open/` that has moved | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Every statement of `xqm16x`'s status corrected to `graduated` with its `Graduated-To` target named, in F-03, the Deferred section, the Scope check, the gate, and V-05; the file path in F-03's Location column updated from `open/` to `graduated/` |
| PR-703 | MEDIUM | IN-SCOPE | E (testing) / shared-checkout safety | plan V-04 red-state recipe; `AGENTS.md` shared-checkout rule | V-04 prescribes obtaining the required red state with `git stash push agent_workflows/cli.py` then restoring. `cli.py` is a high-traffic shared file (last touched by an unrelated commit), and a path-scoped stash-then-restore round trip in a shared checkout can swallow or reorder a co-worker's concurrent edit to the same path, which is the hazard `AGENTS.md` explicitly forbids. The requirement itself (prove the test fails first) is correct and must stay | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | V-04 now prefers taking the red state BEFORE applying E-02 (no stash needed, and the natural order), offers in-memory staging as the fallback, requires naming the mechanism used, and demands before/after `git status --porcelain` if a stash is used anyway. The `-o addopts=""` narrowing was verified correct at review (`tests/test_agent_checked_count.py` runs `3 passed` that way) and is kept |
| PR-704 | LOW | IN-SCOPE | F / E | plan E-05 and V-05 expected hit list; review `git grep` | V-05 tells the executor to expect `startswith("warn")` hits "ONLY in historical records ... (this plan, backlog `zosk0a`, backlog `xqm16x`, and any review record quoting them)". Measured at review: 25 lines across SIX files, and the quoting records are backlog `xqm16x`, this plan, sibling plan `nwcf8j`, pending plan `xs557y` (the `ct1n04` carrier), and executed plan `sk7ggr` - two of which the list does not anticipate, while `zosk0a` (which it does name) is not among them | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-05 carries the re-measured six-file set with the count, and directs the executor to enumerate what they measure rather than match the list, since more records may quote the string by execution time; the load-bearing assertion is restated as ZERO hits under `agent_workflows/` |

PR-701 is FIXED in place, so no finding is left OPEN or DEFERRED at or above the gate threshold and no
escalation to a `- Blocking: yes` question is owed (`check.review-finding-unescalated` satisfied vacuously).

WHAT I DELIBERATELY DID NOT FLAG. The fix itself is minimal and correctly bounded, and I confirmed each of
its four out-of-scope declarations on the code rather than accepting them: `drift_exit_code` genuinely needs
no change and is genuinely the reason the exit code is right while the display is wrong; the registry is
genuinely the right authority to start trusting; `renderers.py` and `term.py` genuinely need no edit for a
third scalar key; and the compact `--agent` record is genuinely key-only. E-03's insistence that an
out-of-enum severity inflate `errors` rather than vanish is the right conservative direction and matches
both `_DEFAULT_RULESPEC` and `drift_exit_code`. F-02's stale-number discipline is exemplary and is exactly
the right response to a live tree (and it proved itself during review: the figure moved again, from the
item's 428 to authoring's 15 to `1` on `aw check specs` today). The `ct1n04` deferral is correctly carried
rather than declined. E-04's insistence on driving the CLI rather than grepping `cli.py` is required by P16
and correctly reasoned, and `tests/test_agent_checked_count.py` is a real, non-`slow` precedent of the right
shape. The gate's stop conditions are genuine write-something-false conditions rather than scope questions.

ONE FORWARD-LOOKING NOTE FOR THE MAINTAINER, recorded rather than actioned: sibling plan `nwcf8j`'s own F-02
and OQ-01 were authored believing this plan "undertakes to CLOSE `xqm16x`". After PR-701 that sentence is
stale, though `nwcf8j`'s conclusions are unaffected (it already closes the item itself in its E-06, and it
already declines to touch `cli.py`). The correct place to fix that sentence is `nwcf8j`'s own review, not an
edit from here, and a new Deferred row in this plan records that reasoning.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | PR-701: E-05 closes a backlog item owned by another carrier. Remove the close, or keep it and let whichever plan runs first close the item? | Remove it and forbid it explicitly | Keeping it on the authoring argument that "whichever closes it first is harmless", rejected because it is NOT harmless: the item's gate belongs to the work `nwcf8j` performs (doctor and attention), so closing it here marks that work release-clear before it exists. Retiring `nwcf8j` and absorbing all three surfaces into this plan, rejected because that is a maintainer-level restructuring of two already-authored plans and would triple this plan's fence | Measured: `xqm16x` is `graduated` to `sevtruth`; `nwcf8j` carries `- From-Backlog: xqm16x` and `- Item-Dependencies: executed:tzjtg4`; `evaluate_blocking_close` returns `legitimate=True` on a citation of this plan, so the close succeeds rather than refusing | yes |
| D-2 | Should this review edit sibling plan `nwcf8j` to correct its now-stale sentence about this plan closing `xqm16x`? | No. Record it as a Deferred row and surface it in the report | Editing `nwcf8j` directly, rejected because it is a pending plan this review's scope does not own, its conclusions are unaffected by the stale sentence, and its own review will correct it; editing another plan's Findings from here would be an undeclared out-of-fence change to a record with its own lifecycle | The repository's per-plan ownership convention and this review's scope (one plan); `nwcf8j` is `to-review`, so a review of it is still owed and is the natural place | yes |
| D-3 | PR-703: V-04's red-state recipe uses `git stash` on a shared high-traffic file. Drop the fail-first requirement, or change the mechanism? | Change the mechanism; keep the requirement absolutely | Dropping the fail-first proof, rejected outright because a test that passes before and after pins nothing, which is the precise failure this plan exists to prevent (the row shipped unguarded per F-04). Mandating in-memory staging only, rejected because the simplest correct route is to author the test before applying the fix, which needs no staging at all | `AGENTS.md`'s shared-checkout prohibition on disturbing another party's uncommitted work; `git log` confirming `cli.py` is actively touched; review verified `-o addopts=""` works as the plan intends | yes |
| D-4 | The plan has 5 E-items for a two-line fix. Does it breach right-sizing in the other direction (over-decomposed)? | No. Keep as authored | Merging E-01 into E-02 and E-03 into E-02, rejected because E-01 is a premise GUARD with a real stop condition (a `warn`-prefixed rule id would invalidate the whole plan) and E-03 is a distinct correctness edge with its own validation question; collapsing them would bury a stop condition inside an implementation step. The linter raised no density advisory in either direction | The rubric's density diagnostics applied per item; each E-item is one concern with one verification surface; `aw ipd lint` clean at both phases | yes |

No `Reversible: no` decision was taken, so no escalation is owed under the irreversible-decision rule.
