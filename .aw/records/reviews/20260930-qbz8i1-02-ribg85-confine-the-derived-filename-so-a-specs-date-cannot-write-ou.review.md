# Review findings: plan ribg85

- Subject-Id: ribg85
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-901 (HIGH, fixed), PR-902 (HIGH, fixed), PR-903 (MEDIUM, fixed), PR-904 (MEDIUM, fixed), PR-905 (LOW, fixed), PR-906 (LOW, fixed), PR-907 (LOW, fixed)

## Round 1

Reviewed at HEAD `938935fe` in an isolated review lane. The plan file was already committed and
byte-identical to the lane input, so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review; it still reports `conforming` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply to it; I separately read the Set's Order-00
orchestrator (`xhr0dj`) and it holds a three-row child checklist with no work of its own, which is
the correct shape.

EVERY ONE OF THE PLAN'S TEN FINDINGS REPRODUCED, and this is a security finding so I drove all of
them rather than reading any. F-01: in a fixture at `<tmp>/a/b/repo`,
`specs new --date ../../../../ESCAPED --apply` exits 0, prints
`wrote <repo>/.aw/records/specs/draft/../../../../ESCAPED-qf25hh-01-qf25hh-x.spec.md`, and the file
lands at `a/b/repo/ESCAPED-qf25hh-01-qf25hh-x.spec.md`, i.e. the repo root. F-02: a deeper
traversal writes `a/b/c/OUTSIDE/deep/dir-55ew2h-01-55ew2h-x.spec.md`, having CREATED `OUTSIDE/` and
`deep/` to get there. F-04: `--date 9999-99-99` exits 0, writes
`99999999-fkssn3-01-fkssn3-x.spec.md` carrying `- Date: 9999-99-99` and
`- 9999-99-99 created (aw specs): s`, and `aw specs check --agent` reports
`"outcome":"clean","findings":0`. F-05: after the escape, `aw specs check --agent` reports
`"checked":0,"findings":0` on a repository that just wrote a spec; and for `notadate` the two
checkers disagree exactly as claimed (`aw specs check` 1 finding `attention.history-missing`;
`aw check specs` 3 including `check.name-nonconformant`). F-06, F-07, F-08, F-09 and F-10 all
reproduced. The diagnosis is correct, the two-guard shape is the right shape, and the decision to
separate this from Order 01 is correct on the measured ground that `is_safe_descriptive` returns
True for a traversal.

WHAT REVIEW FOUND WERE TWO DEFECTS IN THE PLAN ITSELF, one in the fix and one in the method.

THE FIX WAS SITED WHERE IT CANNOT SEE HALF THE DEFECT (PR-901). E-02 says to place the containment
assertion "after `resolve_creation_path` returns `dest` and before `dest.parent.mkdir(...)`". In
`specs.run_new` the dry-run branch (`if not getattr(args, "apply", False):`) sits BETWEEN those two
points and RETURNS, so a guard placed as instructed lives inside the apply arm only. Measured: a
traversing dry run exits 0 and prints `--- would write <...>/draft/../../../../ESCAPED-... ---`
with the rendered body, and `--agent` emits `"outcome":"clean","exit":0,"applied":false` carrying a
`changes` entry whose `kind` is `create` and whose `path` is the escaping path. That is not a
cosmetic gap: a dry run is the one tool an operator has for checking a command before running it,
and here it affirmatively reports an out-of-tree write as clean. E-02 is re-sited above the branch,
its expected outcome and V-02 now require the dry arm to refuse, and the `- Scope:` and `- Concern:`
fields say so.

THE PLAN'S OWN REPRODUCTION METHOD IS UNSAFE, AND I PROVED IT THE EXPENSIVE WAY (PR-902). F-03 says
a shallow fixture makes the escape test pass before the fix via `[Errno 13] Permission denied`, and
concludes that the fixture must be nested. The conclusion is right and the stated mechanism did not
reproduce: from a shallow fixture with ten `../` segments the command SUCCEEDED at exit 0 and wrote
a real 204-byte `.spec.md` into a real directory above my scratch area, whose path I confirmed with
`ls -la` and which my sandbox's path policy then refused to let me delete. It is untracked, outside
any records tree, and `git status --short` stayed clean throughout, so no tracked file and no other
agent's work was affected; I am reporting it rather than quietly leaving it. The generalisable point
is the one the plan was missing: because the verb CREATES INTERMEDIATE DIRECTORIES (its own F-02), a
traversal deeper than its fixture does not fail, it succeeds somewhere unintended. So the hazard is
environment-dependent in both directions, a FALSE GREEN where the escape lands somewhere unwritable
and COLLATERAL DAMAGE where it lands somewhere writable. E-03 now requires the traversal depth be
BOUNDED to the fixture depth and asserted before each probe, V-03 requires that bound be pasted, the
required-tests section carries the warning, and the gate carries it as a plan-specific safety
obligation. This matters more than usual because `AGENTS.md` states this checkout is SHARED.

THREE SMALLER FINDINGS. The deferral section named `aw research new` as the only remaining hole, and
a symbol census found two more verbs reading the same unvalidated flag into a derived name
(`aw adopt`, `aw group research`); I did NOT drive either to an escape, so they are recorded as a
scope-accuracy note for the `m5csyi` sweep to probe rather than as defect claims, and I confirmed
`aw backlog new` is NOT in the set because it derives its filename from an internal `today`. E-04's
group (d) instructs the executor to drive `run_set`/`run_note` with a malformed date, which through
the CLI refuses earlier for an unrelated argparse reason and so measures nothing; driven at the
function, `run_note` returns 0, writes `- ../../../ESCAPED note (aw specs): m`, and creates no file,
which is the behavior worth pinning and which confirms the plan's `Carrier-Declined` reasoning. And
the gate prescribed `aw ipd set executed` as the terminal transition where the contract is
`aw ipd finalize` with conditional runner/executor ownership.

BOTH OPEN QUESTIONS CARRIED `- Owner: none` while being substantive self-resolutions, so I
attributed them to the plan author and marked them as upheld at review rather than as maintainer
rulings. OQ-01's resolution (validate format AND calendar, diverging from the sibling) is correct
and I strengthened its basis by driving the sibling: `aw prompts new --date 9999-99-99 --apply`
really does exit 0 and write, so the divergence it accepts is a measured fact rather than a
prediction. OQ-02 (do not sanitize inside `build_clustered_name`) is correct on all three of its
stated grounds, the first of which is decisive and which I verified: the unvalidated value also
reaches the `- Date:` bullet and the history record, neither of which passes through the builder.

WHAT I DID NOT CHANGE. The port-the-sibling-guard shape, the `relative_to`/`ValueError` containment
idiom, the derive-the-boundary-from-`resolve_type_dir` requirement (which I confirmed is load-bearing
for legacy `.agents/` layouts by reading that function's fallback), the exit-2 convention, the
pre-fix falsification requirement, and the refusal to widen into `research` are all correct and well
argued. The plan's F-09 narrowing argument is right and I re-derived it (`kebab` flattens a traversal
in the slug to `etc-passwd`).

Bare suite at review HEAD before any probe: `3387 passed, 2 skipped, 3 warnings in 63.48s`, 207
deselected. The plan's named regression set: `86 passed in 6.41s`. Repository tree:
`aw specs check --agent` `"checked":38,"findings":0`, `aw check specs --agent` `"outcome":"conforms"`.
No production file was modified by this review.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-901 | HIGH | IN-SCOPE | B. Security / A. Correctness (a guard sited where it cannot see half the defect) | Source order in `specs.run_new`: `dest = _placement.resolve_creation_path(...)`, then `if not getattr(args, "apply", False):` with its returns, then `dest.parent.mkdir(parents=True, exist_ok=True)`. Driven at HEAD in a fixture at `<tmp>/a/b/repo`: `specs new --date ../../../../ESCAPED` with NO `--apply` exits `0` and prints `--- would write <repo>/.aw/records/specs/draft/../../../../ESCAPED-tysgh9-01-tysgh9-x.spec.md ---` plus the body carrying `- Date: ../../../../ESCAPED`; with `--agent` it emits `"outcome":"clean","exit":0,"applied":false` and a `changes` entry `{"kind":"create","path":"...draft/../../../../ESCAPED-bxep0j-01-bxep0j-x.spec.md"}` | **E-02 instructs the guard be placed "before `dest.parent.mkdir(...)`", which is INSIDE the apply branch, so the dry-run arm returns first and keeps reporting an out-of-tree write as clean.** A dry run is the one tool an operator has for checking a command before running it, and this one affirmatively blesses the escape, including in the machine envelope another tool would consume. A guard that only fires on `--apply` leaves the preview lying | C:Low; U:Medium; S:Medium; F:Medium; Overall:Medium | FIXED | New F-11 records the source order and both dry-run transcripts. E-02 re-sited to run immediately after `resolve_creation_path` and BEFORE the apply branch, with the reason stated in the item. Its expected outcome now requires the bypassed dry run to exit 2. V-02 requires the dry arm's refusal AND its `--agent` form pasted, and requires the guard's source be quoted showing it sits above the `if not getattr(args, "apply", False):` line; a run where the dry arm still previews the escape explicitly fails the item. E-03 adds a traversing dry-run case. `- Concern:`, `- Scope:`, proposed-changes item 2 and the scope check updated |
| PR-902 | HIGH | IN-SCOPE | E. Testing / B. Security (a reproduction method that damages the tree it runs in) | Driven at review HEAD from a fixture directly under the scratch base with ten `../` segments: `rc=0`, printing `wrote <tmp>/repo/.aw/records/specs/draft/../../../../../../../../../../ESCAPED-8ry6rb-01-8ry6rb-x.spec.md`. Resolving `repo/.aw/records/specs/draft` up ten parents lands ABOVE the scratch base; `ls -la` confirmed a 204-byte `ESCAPED-8ry6rb-01-8ry6rb-x.spec.md` present there. F-03's claimed `[Errno 13] Permission denied` did NOT occur. The mechanism is the plan's own F-02: `dest.parent.mkdir(parents=True, exist_ok=True)` | **F-03's stated mechanism did not reproduce and what happened instead is worse: an over-deep traversal from a shallow fixture SUCCEEDS and writes outside the intended scratch area.** The plan requires the fixture be nested but never bounds the TRAVERSAL to the fixture depth, so an executor following E-03 can write a file outside their workspace, as review did (and could not then delete it from its sandbox). The hazard is environment-dependent in both directions: a false green where the escape lands somewhere unwritable, collateral damage where it lands somewhere writable. Neither is a guard, and `AGENTS.md` states this checkout is SHARED | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | New F-12 records the measurement, the confirmed file, that it is untracked and no tracked file or co-worker's work was touched, and that the sandbox refused its deletion. E-03 gains a MATCH-THE-DEPTH requirement: compute the `../` count from the fixture depth, assert each probe's resolved target is inside the temp base before running it, skip otherwise. Its nesting comment must state the environment-dependent hazard rather than asserting the permission error. V-03 requires the traversal depth be stated beside the fixture depth and the bounding assertion pasted, and states that an escape outside the temp base is evidence the test is DANGEROUS. Required-tests and the gate both carry the warning; `- Concern:` names it |
| PR-903 | MEDIUM | UNDER-SCOPE | G. Plan executability (an understated residue) | `grep -n 'getattr(args, "date"' agent_workflows/*.py` returns ten sites. Beyond `specs.py:1183` (this plan) and `prompts.py:437` (guarded): `research_cmd.py:738`/`:795`, `research_refs.py:413` (`date_str = getattr(args, "date", None) or date.today().strftime("%Y%m%d")` feeding `plan_set_assign`), and `artifact_adopt.py:1051` (`date_str=getattr(args, "date", None)`). `backlog.py:1718` is history-only and backlog's creating path uses `filename = f"{today}-{item.set}-01-{item.id}-{slug}.backlog.md"` | **The deferral names `aw research new` as the only remaining hole, and two further verbs read the same unvalidated flag into a derived name** (`aw adopt`, `aw group research`). A reader of the deferral would believe the residue is one verb, and whoever picks up `m5csyi` would rediscover these later. I did NOT drive either to an escape, so this is a scope-accuracy defect, not a claim of two more measured vulnerabilities | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-13 records the census with each site's role. A new deferral row names both verbs, states explicitly that neither was driven to an escape and why they are listed anyway, and carries `- Carrier: m5csyi`. The scope check gains under-scope item (a2) with the same honesty qualifier, and records that `aw backlog new` was checked and excluded on measured grounds |
| PR-904 | MEDIUM | IN-SCOPE | E. Testing (a required measurement the prescribed method cannot take) | Driven at review HEAD: `cli.main(['specs','note',...,'--date','../../../ESCAPED'])` exits 2 with an argparse `unrecognized arguments` usage error, measuring nothing about the date path. Driven at the FUNCTION, `specs.run_note` returns `0`, the spec gains `- ../../../ESCAPED note (aw specs): m`, and a `*ESCAPED*` glob under the fixture base returns nothing | **E-04's group (d) asks the executor to drive `run_set`/`run_note` with a malformed date to document the scope boundary, and the CLI spelling refuses earlier for an unrelated argparse reason.** A CLI-only attempt would produce an exit 2 that looks like a guard which is not there, recording the opposite of the intended evidence and leaving the `Carrier-Declined` reasoning unverified | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New F-15 records both spellings and the measured function behavior. E-04 group (d) now requires the probe be driven at the FUNCTION, states why the CLI spelling measures nothing, and names the exact behavior to pin. V-04 requires the history line and the no-file glob pasted |
| PR-905 | LOW | IN-SCOPE | G. Plan executability (an incomplete non-regression set) | E-02's re-siting adds a guard to the dry-run arm, which E-04's non-regression groups (a) through (d) do not cover | **With E-02 re-sited, the dry-run path gains a guard and no non-regression pins that a CONFORMING preview still works.** Every non-escaping input must still preview the same path at exit 0, and after PR-901 that arm is newly guarded, so it is exactly where a regression would land | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 gains non-regression group (e), a conforming dry run previewing the same path at exit 0. Its expected outcome updated from four groups to five. V-02 additionally requires a conforming dry run in both layout fixtures; V-04 requires group (e) |
| PR-906 | LOW | IN-SCOPE | G. Plan executability (a terminal-transition instruction that is not the contract) | Plan gate: "move the plan to `.aw/records/plans/executed/` through the tooled transition (`aw ipd set executed`), never by hand" | **The gate names `aw ipd set executed` as the terminal transition where the contract is `aw ipd finalize` with conditional runner/executor ownership.** The plan is right that it must not be done by hand; it names the wrong tooled verb, and in a managed lane the runner owns the transition rather than the executor | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to `aw ipd finalize` with conditional runner/executor ownership, and to record that this plan's `- Readiness:` is the review's output and approval is recorded through `aw ipd set approved --by-human` |
| PR-907 | LOW | IN-SCOPE | G. Plan executability (unattributed self-resolutions and stale live counts) | Both OQ blocks carried `- Owner: none`. `ipd_lint`'s `has_owner` only tests non-emptiness, so the field is unchecked for a resolved question. Plan F-10 cites `checked:38` and its required-tests bullet already asks for re-derivation; no suite baseline was recorded at all | **Two substantive self-resolutions carry no owner, so a reader cannot tell a self-resolved question from an answered one; and the plan records no suite baseline against which an execution failure could be attributed.** Writing `Owner: maintainer` would be worse (a forged attestation that passes every mechanical check), so the fix is honest attribution | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both questions now read `- Owner: plan author`, explicitly marked as upheld at review and NOT a maintainer ruling. OQ-01's basis strengthened with F-14, the driven sibling measurement. New F-16 records the bare suite (`3387 passed, 2 skipped`) and the regression set (`86 passed`); F-10 gains its re-measurement and the standing `check.collisions-not-checked` advisory; required-tests and V-04 now demand before/after runs rather than comparison against any recorded number |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-901: where should the containment assertion sit, given the dry-run branch returns between the plan's two named landmarks? | IMMEDIATELY after `resolve_creation_path`, ABOVE the `--apply` branch, so both arms refuse | (a) Keep it before `mkdir` as authored and accept that a preview blesses the escape, on the ground that no file is written; (b) place it before `mkdir` AND add a second copy in the dry-run branch; (c) place it inside `resolve_creation_path` so every record type gets it | Option (a) fails on what a dry run is FOR: it is the one way to check a command without mutating anything, and an operator who previews this invocation is told `outcome: clean` with a `create` change naming an out-of-tree path, which is worse than no preview because it is read as a clearance. Option (b) is two guards for one property, which is how they drift; the single site above the branch dominates it with strictly less code. Option (c) is tempting and is the same mistake OQ-02 already rejected one layer down: `resolve_creation_path` is a shared placement helper used by every record type, and putting a refusal in it would change behavior for callers this plan has not measured, while still leaving the unvalidated value flowing into the `- Date:` bullet and the history record. The verb that accepts the input is the right boundary, which is where `prompts.run_new` already puts it | yes |
| D-2 | PR-902: F-03's permission-error mechanism did not reproduce and the probe escaped my scratch area. Weaken the nesting requirement, or strengthen it? | STRENGTHEN it into a two-part rule: nest the fixture AND bound the traversal to the fixture depth, asserting the resolved target before each probe | (a) Keep the nesting requirement as authored and correct only F-03's stated mechanism; (b) drop the nesting rationale as unreproducible; (c) forbid destructive traversal probes entirely and test only the exit code | Option (b) is exactly backwards: the measurement did not weaken the requirement, it revealed a second and more serious failure mode, since an unbounded probe from a shallow fixture writes outside its own tmpdir rather than refusing. Option (a) leaves the live hazard, because the plan's text nowhere bounds the `../` count and an executor reading "nest it several deep" may still pass ten segments, which is what I did. Option (c) would gut the plan's strongest property: V-03 rightly demands the pre-fix failure show a FILE PRESENT rather than an exit code, and an exit-code-only test is precisely the false green F-03 warns about. Bounding the probe keeps the strong assertion and removes the hazard, and the arithmetic is trivial (fixture depth is known to the test that created it) | yes |
| D-3 | PR-903: two further verbs read the same unvalidated flag. Widen this plan, drive them to an escape, or record them? | RECORD them as a scope-accuracy note with the honesty qualifier that neither was driven, carrying the existing `m5csyi` carrier | (a) Widen this plan to cover `aw adopt` and `aw group research`; (b) drive both to a full escape and file them as measured vulnerabilities; (c) leave the deferral as authored, naming only `research new` | Option (a) contradicts the plan's own correct reasoning for excluding `research new`: a different module, a different call path, its own test surface, and one commit mixing several modules' behavior changes. Option (b) was the tempting thorough choice and I declined it deliberately: each probe is a deliberate out-of-tree write, PR-902 is the record of what that costs when it goes wrong, and driving two more escapes to strengthen a deferral row is a poor trade when the symbol evidence already tells the `m5csyi` sweep exactly where to look. That is also why the row says plainly that neither was driven, so nobody reads it as a measured claim. Option (c) is the finding | yes |
| D-4 | PR-907: both open questions were `resolved` with `Owner: none`. Attribute, forge, or reopen? | Attribute both to `plan author`, explicitly NOT a maintainer ruling, and strengthen OQ-01's basis by driving the sibling | (a) Leave `Owner: none`, which the linter accepts; (b) write `Owner: maintainer` since both answers are plainly right; (c) reopen OQ-01 for the human, since it deliberately diverges from a sibling verb's contract | Option (b) is a forgery of exactly the kind the workflow names: `ipd_lint`'s `has_owner` only tests non-emptiness, so a false `Owner: maintainer` passes every mechanical check while asserting a ruling that never happened. Option (c) would ask the human what the repository already answers: the divergence is justified by a realized harm recorded in this repository's own backlog (`tf4jz5`), and I confirmed the sibling really does admit `9999-99-99` (F-14), so the evidence is complete. Option (a) is legal but erases the difference between a self-resolved question and an answered one, which is the whole reason a reader checks the field. Attribution with an explicit non-ruling marker is the honest state, and it leaves the maintainer free to overturn either at approval | yes |
