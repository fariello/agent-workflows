# Review findings: plan ahq0mq

- Subject-Id: ahq0mq
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `151a53cc` in a lane worktree. Structural preflight `aw ipd lint --phase author`
CONFORMED (exit 0, `findings: 0`, no advisories) and `--phase review-finalize` conforms after revision.
No pre-review snapshot was needed: the plan was committed and unmodified, and the lane-input copy is
byte-identical to the tracked file.

THE DEFECT IS REAL AND EVERY SOURCE CLAIM IS EXACT. `_STATUS_META_RE = _re.compile(r"(?m)^- Status:\s*(\S+)\s*$")`
is searched over the whole file in both places, verbatim as F-1 says: `_status_meta` does
`m = _STATUS_META_RE.search(text)` and `is_retired` does the same before testing `_RETIRED_STATUSES`.
The four `is_retired` callers in F-4 are all present with the quoted expressions. The dependency
`kecxnb` is genuinely `- Status: executed`. `selectors.metadata_region`'s docstring states the
principle this plan applies, including the F-4 caveat the plan relies on (a headingless record's region
is the whole text). Demonstrated on the motivating shape:

```text
whole-file read      : executed
region-bounded read  : None
```

WHERE THE PLAN GOES WRONG IS ITS EFFECT CLAIM, AND THAT IS THE REVIEW'S MAIN CONTRIBUTION. The plan
predicts ebh1ap "was hidden as retired and now becomes visible to research-type checks and the
attention view". I simulated the change by patching both readers to the region-bounded form and drove
the real commands. Both halves are false:

```text
attention byte-identical: True (len 1385256 vs 1385256)
attention references is_retired: False
live view already contains: {"id": "ebh1ap", "tree": "research",
                             "native_status": "reference", "attention_class": "done"}
BEFORE findings: 4   AFTER findings: 4      (empty symmetric difference)
research files yielded: before=91 after=92  (only addition: ebh1ap)
check_collisions: unchanged (3)   check_content: unchanged (0)
check_id_outside_metadata_region / check_name_identity / check_names /
check_setid_length / check_lifecycle_transitions: all unchanged
```

So `aw attention` cannot change (it never calls `is_retired`) and ebh1ap was never hidden there; it is
classified from its YAML front matter. The only real change is internal and produces no finding. The
plan is still worth executing, but as correctness-by-construction, and E-03's job is to confirm the
ABSENCE of a diff rather than to explain one.

THE TEST DESIGN OVERSTATES ITSELF TOO. Running each of E-02's shapes through both readers, only (a)
discriminates:

```text
DISCRIMINATES  before=executed   after=None        (a) no front-matter status + ## Goal + fenced quote
vacuous        before=approved   after=approved    (b) front matter approved + same fenced quote
vacuous        before=approved   after=approved    (c) HEADINGLESS, first bullet approved, later quote
vacuous        before=executed   after=executed    (e) metadata says executed (real signal)
```

and the end-to-end (d), built in a temp git repo, is also a control: `PRE-FIX check_status_untooled
drift: []`, with `HEAD _status_meta: approved` and `STAGED _status_meta: approved`. The plan's Expected
outcome claimed (a) AND (c) fail pre-change; (c) does not.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. testing (a stated pre-change failure that does not occur) | Measured per shape: `DISCRIMINATES before=executed after=None (a)`; `vacuous before=approved after=approved (b)`; `vacuous before=approved after=approved (c)`; `vacuous before=executed after=executed (e)`. For (d) in a temp git repo: `PRE-FIX check_status_untooled drift: []`, `HEAD _status_meta: approved`, `STAGED _status_meta: approved` | **E-02's EXPECTED OUTCOME CLAIMS (a) AND (c) FAIL PRE-CHANGE; ONLY (a) DOES.** Four of the five cases are controls that pass identically on both sides. An executor following the plan would either paste a V-02 evidence block asserting a failure that never happened, or spend a cycle trying to force (c) red. The mislabelling also overstates the suite: four controls presented as regression tests make coverage look four times stronger than it is. Note (c) is vacuous for an instructive reason and should be KEPT: `metadata_region` returns the whole text for a headingless record, so only `search`'s first-match semantics keep that answer right, which makes it a real guard against a future last-match or findall rewrite. | C:Low; U:Low; S:Low; F:Medium (a V-02 that cannot be satisfied honestly invites a fabricated paste) but the FIX is Low | FIXED | E-02 gains the measured discrimination table and an instruction to label (b), (c), (d), (e) as CONTROLS in their docstrings with the reason (c) is worth keeping. Its Expected outcome now says only (a) fails pre-change. Case (d)'s text records the measured pre-fix `[]` and why. V-02 forbids claiming (c) fails, requires a per-case regression-or-control statement, and bounds the revert (restore in the next command, never `git stash` in a shared checkout, throwaway worktree offered). Added as F-6. |
| PR-002 | MEDIUM | IN-SCOPE | D. anti-regression / F. honest documentation (a predicted benefit that does not exist) | Simulated at review: `aw attention --format json` BYTE-IDENTICAL (1385256 bytes both sides); `'is_retired' in inspect.getsource(attention)` -> False; the live attention view ALREADY contains ebh1ap as `native_status: reference`, `attention_class: done`; `aw check all --agent` -> same 4 findings both sides, empty symmetric difference; seven individual checks consuming `_iter_type_files` all unchanged | **THE PLAN'S CENTRAL EFFECT CLAIM IS FALSE IN BOTH HALVES.** E-03 and the approval gate both state ebh1ap "becomes visible to research-type checks and the attention view". `attention.py` never calls `is_retired`, so this change cannot alter its output, and ebh1ap was never hidden from it. No check emits a finding for the newly-yielded file either. Two concrete harms: a human approves a benefit that is not delivered, and an executor is told to explain diff lines that cannot appear, which in a plan whose real diff is EMPTY is a strong invitation to manufacture something. | C:Low; U:Medium (the approval summary misinforms the approver); S:Low; F:Low; Overall:Medium | FIXED | E-03 rewritten: the expected diff is EMPTY on both surfaces, with the measurements pasted, and its job restated as confirming the absence of change. The Goal gains a "what this buys, stated honestly" paragraph. The approval gate now says there is NO observable effect and explains why attention is untouched. Added as F-5 with the full measurement set. OQ-02 added, asking and answering whether such a change is worth executing at all. |
| PR-003 | LOW | IN-SCOPE | A. correctness / E. testing (an empty diff is indistinguishable from work never done) | Consequence of PR-002: with both diffs expected empty and `aw check all` unchanged, every artifact V-03 asks for looks identical whether or not E-01 was applied. The one measurable signal is internal: `_iter_type_files(repo,'research')` 91 -> 92 | **THE PLAN'S ONLY EVIDENCE OF SUCCESS WAS EVIDENCE THAT AN UNAPPLIED CHANGE WOULD ALSO PRODUCE.** V-03 as written asks for two diffs and an explanation per differing line. Once the diffs are correctly expected to be empty, that evidence is vacuous: an executor who edited nothing would paste the same thing. The stop condition was also keyed to "a new finding not attributable to ebh1ap", implying legitimate ebh1ap diff lines exist, when measured there are none. | C:Low; U:Low; S:Low; F:Medium (a false green on the whole plan) but the FIX is Low (require one count) | FIXED | V-03 now requires the `_iter_type_files(repo, "research")` count before and after, rising by exactly one with ebh1ap shown as the addition, and states plainly that without it an empty diff cannot be distinguished from a change never applied. The stop condition tightened to ANY new finding, with a note that the bar is deliberately stricter than the plan set it. A FALSE-GREEN WARNING paragraph added to the gate. |
| PR-004 | LOW | IN-SCOPE | A. correctness (a count that does not reproduce) | Re-derived over `.aw/records/**/*.md` only: 7 records change their read status (exactly F-2's first seven), not 10. The other three are gitignored run records; `find .aw -maxdepth 3 -name 'run-*' -type d` returns nothing in a fresh lane, and `.aw/workflow-artifacts/runs/` does not exist | **F-2's 10 MIXES TRACKED RECORDS WITH GITIGNORED RUN SCRATCH, SO IT DOES NOT REPRODUCE.** The sweep itself is correct and its per-record values are right; the problem is that E-03 tells the executor to expect "nine further records" changing, a figure that silently depends on which run records happen to exist in the tree they execute in. In a fresh clone or an isolated lane (which is where a runner executes) the number is 7, and an executor comparing against 10 would report a discrepancy that is not one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added as F-4b recording both populations, why they differ, and that neither figure is wrong. E-03's rewritten text no longer quotes a fixed count and instructs re-derivation; the Required tests section states the measured `aw check all` baseline (4 pre-existing findings, named individually) so they are not mistaken for regressions. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan's predicted effect does not exist. REPLAN, retire it, or keep it with corrected framing? | KEEP IT, with the framing corrected to correctness-by-construction and the absence of a diff made the expected outcome. | (a) `REJECT - NEEDS REPLAN`: rejected, the approach (bound both readers to the one shared region helper) is correct and minimal and the defect is real; only the effect PROSE was wrong, which is a bounded edit. (b) Retire the plan as valueless: rejected for two reasons that do not need a visible diff, both recorded in OQ-02: the latent defect is real in a repo whose records routinely quote metadata blocks, and sibling `kecxnb` already applied this rule to the transition hook, so leaving these two unbounded keeps two answers to "what is this record's status?". (c) Widen it to also read YAML `status:` so the change has visible effect: rejected as manufacturing scope to justify a plan, and the plan already declines that deliberately. | `aw attention` byte-identical and `'is_retired' in inspect.getsource(attention)` False; `aw check all` unchanged; `selectors.metadata_region` docstring ("Identity comes from where an artifact declares it"); `kecxnb` `- Status: executed`. | yes |
| D-2 | With the diff expected empty, what proves the change was applied? | REQUIRE the `_iter_type_files(repo,'research')` count (91 -> 92, ebh1ap the addition) as the one positive signal. | (a) Accept the empty diffs as sufficient: rejected, they are exactly what doing nothing produces, and this plan's whole risk profile after PR-002 is a silent no-op that looks like success. (b) Require a unit-level assertion instead: rejected as insufficient on its own, the unit tests can pass while the production readers were left unpatched (E-02 could in principle test a helper nothing calls); the count is measured through the real caller. (c) Manufacture a fixture record in the corpus to create a visible diff: rejected outright, it would write into the shared records tree to satisfy a test. | Measured 91 -> 92 with ebh1ap as the sole addition; `aw check all` 4 findings both sides. | yes |
| D-3 | Only one of E-02's five cases discriminates. Delete the four controls, or keep and relabel? | KEEP all five and LABEL the four as controls, with (c)'s reason spelled out. | (a) Delete the vacuous four: rejected, (c) in particular guards a real future regression (a last-match or findall rewrite of the helper would break the headingless shape and nothing else would catch it), and (d) is the only end-to-end case over the real git-backed path. (b) Leave the labels as-is: rejected, it would require V-02 to paste a failure that cannot happen, which is an invitation to fabricate evidence. (c) Add a new discriminating case for the untooled detector: rejected as impossible in any meaningful form, since it would need a plan with NO front-matter `- Status:`, which is already structurally invalid. | Per-shape before/after table; `PRE-FIX check_status_untooled drift: []` for (d); `metadata_region`'s whole-text return for a headingless record. | yes |

### Deferred and open

- (none). All four findings were FIXED in place. No finding reached the repository's gate threshold
  (`HIGH`), so no escalated `- Blocking: yes` question is owed. The plan's open questions (OQ-01 from
  the author, OQ-02 added at review) are both `resolved` and non-blocking. No `Reversible: no` decision
  was taken. The plan's one `Carrier-Declined` deferral (reading YAML `status:` in `is_retired`) was
  examined and stands: it is a different behavior change with its own corpus impact and no item asks
  for it.

HONEST LIMITS, stated because they bound what this round proves. I verified every source claim, the
dependency's status, the corpus sweep (re-derived), the per-case test discrimination, the end-to-end
(d) pre-fix behavior, and the full before/after effect on `aw attention`, `aw check all`, the
`_iter_type_files` yield, and seven individual checks. My effect measurement SIMULATED the change by
patching `is_retired` and `_status_meta` rather than editing the module, which is the right call in a
shared checkout but means I proved the behavior of the patch shape I wrote, not of the executor's
eventual diff; if E-01 is implemented differently (for example bounding the regex itself, which the
plan explicitly forbids) my numbers do not transfer. I did NOT run the new tests or write any code, so
E-01..E-04 and V-01..V-04 still own that. I ran the bare suite once for the `2501 passed, 2 skipped in
59.95s` baseline and did NOT run the slow set (`make test-all`). My sweep covered `.aw/records/**/*.md`
plus a scan of non-records `.aw/**` (which found nothing); the three gitignored run records F-2 names
were absent here, so I confirmed their ABSENCE rather than their contents. Finally, "no observable
effect" is a statement about THIS tree at THIS commit: the corpus moves, which is why E-03 is now
instructed to re-derive rather than match.
