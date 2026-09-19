# Review findings: plan 2xz59a

- Subject-Id: 2xz59a
- Subject-Type: ipd
- Reviewed-At: 2026-09-19
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Readiness: no-go

## Round 1

Reviewed at HEAD `f3da906e`. The plan on disk was byte-identical to the sealed lane input
(`sha256 06be3d2e...`, confirmed by `diff`), and `git status --porcelain` on the plan path was empty, so
no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author --agent` reported
`clean`, 0 findings, exit 0, both before and after the revisions.

THIS IS A GOOD ORCHESTRATOR AND ITS CENTRAL JUDGEMENTS ARE RIGHT. The Set shape is correct, the linear
chain is genuinely load-bearing rather than timid (07 deletes tables that 05 and 06's consumers still
read), the checklist is properly confined to child-completion confirmations so the coverage gate passes
honestly, and the author resisted the standard temptation to park real work on the parent. The four
live palettes it describes are all present exactly where it says (`term.py:117`, `attention.py:1403`,
`render_stream.py:51`, re-exported at `oc_runipd.py:104` / `agy_runipd.py:104` / `runner_shared.py:168`),
and `agent_workflows/lifecycle_style.py` is indeed absent. I verified every structural claim it makes
about the runner against the runner's own code rather than accepting its prose.

WHERE THIS REVIEW SPENT ITS EFFORT: the plan's own safeguard against orphaned criteria is the thing that
failed, and three of its verification commands do not measure what they claim. Each finding below was
measured, not inferred.

**1. The criterion-coverage map asserts coverage that does not exist, and nothing downstream would
catch it.** The plan states the correct rule ("if any of A1 to A21 has no child claiming it at review
time, that is a missing child and a new one must be authored, not a criterion quietly dropped") and then
violates it. Grepping each criterion token across all eight child files:

```text
A1   : (no child)          A12  : n4xq3l (re-reads it), pow5sj (Step 0 note only)
A4   : (no child)          A19  : (no child)
A6   : (no child)          A21  : (no child)
```

`grep -c` for the glyphs those criteria are about returns 0 in every one of the eight files: `✘` 0,
`↻` 0, `◔◑◕` 0. Child `7p3tt8` names no criterion at all. The map claimed `A4/A5/A6 -> udgilu and
bn026f`, `A19 -> udgilu`, and `A21 -> every child's suite run`; A5 is in `udgilu`, and A4, A6, A19 and
A21 are in nothing. Spec `uonrjg` is `approved` with `Blocks-Release: next`, so these six criteria gate
the release, and no tooling cross-checks a spec's criteria against a Set's coverage: each child
validates what it names, the parent validates only child completion. The Set would execute to
completion and report success with six release-gating criteria never verified.

I drafted an `E-09` on the parent to close this and REMOVED it, which is the substantive part of this
finding. A runner retires an Order-0 orchestrator once every child is `executed` on disk and
deliberately SKIPS the pre-transition E/V checkpoint, so an item on this parent would be marked
complete having never been performed or verified: exactly the lost-work failure the orchestrator
coverage gate exists to prevent. Note also that the coverage gate would NOT have caught this, because
it asks whether the parent carries WORK no child covers, and these criteria are unowned rather than
parked on the parent. The honest fix edits six child plans, which are outside this review's ledger, so
it is escalated as OQ-02 with `- Blocking: yes` and `- Finding: PR-001`.

**2. OQ-01 asked the maintainer to trade away wall-clock time that is not being spent.** The question
offered parallelizing children 05 and 06, reasoning that "serializing them costs wall-clock time they
may not want to spend". Neither runner can execute two items concurrently. `run_queue` selects ONE
runnable item per loop iteration and breaks:

```text
oc_runipd.py:6582-6585     satisfied, _ = dependency_status(item, state)
                           if satisfied:
                               runnable = item
                               break
agy_runipd.py:3395-3398    (identical)
```

No thread pool, no `concurrent.futures`, no `--jobs`/`--parallel` flag (`grep -E
"parallel|jobs|workers|concurr"` on `aw oc runipd --help` returns nothing; the only `threading.Thread`
in either runner is the stall watchdog). A concurrency analyzer exists
(`orchestrate_isolation.analyze_concurrency_eligibility`) but neither runner imports it; it is reached
only from `ipd_set_plan`/`ipd_set_executor`, whose CLI surface `aw ipd execute-set --help` states "v1
supports ONLY --plan-only: it never launches a model or worktree". So the choice the question put to the
maintainer does not exist, and asking it would have spent a maintainer turn on a false premise. Resolved
from evidence rather than escalated (D-1).

**3. `git diff --check` does not check what the completion criteria assume.** The bare form diffs the
worktree against the INDEX, so it reports nothing for an untracked file and nothing for a staged one.
Measured with a probe file containing trailing whitespace:

```text
untracked  + `git diff --check`           -> no output, exit 0   (not diffed at all)
add -N     + `git diff --check`           -> trailing whitespace, exit 2
git add    + `git diff --check`           -> no output, exit 0   (worktree now matches index)
git add    + `git diff --cached --check`  -> trailing whitespace, exit 2
```

A21 exists to prove the change introduces no whitespace damage, and a check that a staged error passes
cannot prove it. Fixed by requiring `git diff --check HEAD` or `git diff --cached --check`. The
pre-commit `trailing-whitespace` hook is a backstop but excludes `.aw/system/` and the research trees.

**4. The A17 grep would either license deleting working behavior or report a false pass.**
`term.py`'s `STATUS_COLOR_256` holds 56 keys, of which only 34 appear anywhere in spec `uonrjg`. The
other 22 are generic command-outcome and formatting roles that R10.3 explicitly keeps valid and outside
the spec. Three of the four read sites are generic, not lifecycle: `format_badge` resolves an arbitrary
`role_or_code` (`term.py:469`) and `format_path` looks up `"paths"` (`term.py:477`), and `"paths"`,
`"ok"`, `"info"` each appear ZERO times in the spec. So "delete `STATUS_COLOR_256`" (which child
`qdd5jq` E-04 says literally) would remove path and badge coloring across the CLI. A17 is satisfied when
no second LIFECYCLE table remains, not when the symbol name is absent.

**5. The deletion-ordering rule was both too strict and silent on the real hazard.** It named only
`term.py`, implying `attention.py`'s table is also order-constrained; it is not, being read at exactly
three sites inside its own module (1852, 1997, 2160), so child 05 may delete it immediately. Meanwhile
`_CLASS_COLOR_256` (`attention.py:1396`) keys on the five attention CLASSES (`A.ACTIVE`, `A.READY`,
`A.BLOCKED`, `A.DONE`, `A.PARKED`), which spec Section 3 lists as an explicit NON-GOAL, so the Set-level
A17 assertion must not be read as licensing its removal. Child 05's E-02 already handles this correctly
with a determination step; recorded at Set level so 07 cannot undo it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | UNDER-SCOPE | D. anti-regression / G. executability; the plan's own no-orphaned-criterion rule | plan `104-105` (the map); measured across `.aw/records/plans/pending/20260919-lifeglyph-0[1-8]*.ipd.md`: A1/A4/A6/A19/A21 in no child, A12 only re-read by `n4xq3l`; `grep -c` for `✘`/`↻`/`◔◑◕` = 0 in all eight | Six acceptance criteria of `approved`, release-gating spec `uonrjg` are claimed by the parent's coverage map and demanded by no child's validation section. The Set would execute to completion reporting success with six release-gating criteria never verified. The orchestrator coverage gate does NOT catch this (it asks about uncovered WORK, not uncovered CRITERIA), and an item on the parent could not fix it because retirement skips the E/V checkpoint | C:Medium; U:Low; S:Low; F:Medium-High; Overall:Medium-High | OPEN | Escalated as OQ-02 `- Blocking: yes` / `- Finding: PR-001`. The correct fix edits six CHILD plans, outside this review's ledger, and needs the maintainer's authorization; recommended assignment recorded (A1/A4/A6/A19 -> `udgilu`, A12 -> `pow5sj`, A21 -> `qdd5jq`). A parent-side `E-09` was drafted and deliberately removed, with the reason recorded in the plan |
| PR-002 | MEDIUM | IN-SCOPE | C. architecture; F. KISS (do not ask what the repo answers) | `oc_runipd.py:6582-6585`, `agy_runipd.py:3395-3398`; `aw oc runipd --help` has no parallel/jobs flag; `orchestrate_isolation.analyze_concurrency_eligibility` imported by neither runner; `aw ipd execute-set --help` "v1 supports ONLY --plan-only" | OQ-01 asked the maintainer to weigh parallelizing children 05 and 06 against wall-clock cost, but no runner can dispatch two items concurrently, so the offered trade-off does not exist and the question would have spent a maintainer turn on a false premise | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Resolved in place with the measured evidence; `- Status:` moved `open` -> `resolved`. Also recorded that the linear order is required for correctness regardless of dispatcher capability (D-1) |
| PR-003 | MEDIUM | IN-SCOPE | E. testing; exact validation commands | Probe measured 2026-09-19: staged trailing-whitespace file passes bare `git diff --check` (exit 0) and fails `git diff --cached --check` (exit 2); `.pre-commit-config.yaml:29-32` excludes `.aw/system/` and research trees | Completion criterion A21 specified a bare `git diff --check`, which diffs worktree-vs-index only and therefore passes a whitespace error that is untracked or already staged, so it cannot prove the criterion it is cited for | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Criterion and the required-tests section now specify `git diff --check HEAD` or `git diff --cached --check`, with the measurement and the hook's exclusions recorded |
| PR-004 | HIGH | IN-SCOPE | A. correctness; D. anti-regression | `term.py:117` (56 keys, 34 in spec, 22 generic); read sites `term.py:287,394,469,477`; `"paths"`/`"ok"`/`"info"` appear 0 times in the spec; spec R10.3 "Generic `Term` outcomes... remain valid" | The A17 completion grep treats the name `STATUS_COLOR_256` as equivalent to "lifecycle table". It is not: 22 of 56 keys are generic outcome and formatting roles R10.3 keeps in scope, and `format_badge`/`format_path` read them. Taken literally the criterion licenses deleting path and badge coloring across the CLI | C:Low; U:Medium; S:Low; F:Medium; Overall:Medium | FIXED | A17 restated as "no second LIFECYCLE table", with the 56/34/22 measurement, the generic key list, and an explicit instruction that child `qdd5jq` E-04 must SPLIT the table rather than delete the symbol |
| PR-005 | MEDIUM | IN-SCOPE | A. correctness; C. architecture | `attention.py:1396` (`_CLASS_COLOR_256` keys are `A.ACTIVE/READY/BLOCKED/DONE/PARKED`); `attention.py:1403` read only at 1852/1997/2160; `status_256`/`status_label` callers = cli, run_viewer, research_index, plans_index, status_set, ipd_lint; spec Section 3 non-goal | The deletion-ordering rule named only `term.py`, implying `attention.py`'s table is order-constrained (it is not, so 05 is needlessly blocked) while saying nothing about `_CLASS_COLOR_256`, a non-lifecycle attention-class vocabulary that Section 3 protects and that a Set-level A17 sweep could remove | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Rule rewritten with the measured read sites and caller set, distinguishing the order-constrained `term.py`/`render_stream.py` tables from `attention.py`'s local one, and recording that `_CLASS_COLOR_256` must survive the Set |
| PR-006 | LOW | UNDER-SCOPE | G. executability; honest gate | plan gate `206-208`; retirement is gated on every child `executed` and skips the pre-transition checkpoint | The gate's coverage-gate paragraph could be read as asserting that a clean gate verdict means the Set's criteria are covered. Given PR-001 that reading is false and load-bearing | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added an explicit statement of what the coverage gate does NOT check (criteria, as against work), cross-referencing OQ-02 |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | OQ-01 asks the maintainer whether children 05 and 06 should run in parallel. Leave it open for the human, or resolve it? | RESOLVE from evidence and close it `Status: resolved`. The premise is false: no runner can dispatch two items concurrently, so there is no wall-clock cost to trade, and the linear order is independently required because 07 deletes tables 05 and 06's consumers read. | (a) Leave it open for the maintainer: rejected, the workflow forbids asking the human what the repository answers, and this is answerable by reading the dispatch loop. (b) Rewrite the Set with parallel edges: rejected outright, there is no dispatcher to honor them and the deletion ordering forbids it anyway. (c) Close it silently without recording why: rejected, the false premise is itself worth recording so a later author does not re-raise it. | `oc_runipd.py:6582-6585` and `agy_runipd.py:3395-3398` select one item and `break`; no thread pool or `concurrent.futures` in either runner; `aw oc runipd --help` has no parallel/jobs/workers flag; `analyze_concurrency_eligibility` is imported by `ipd_set_plan`/`ipd_set_executor`/`migration_complex`/`worktree_lease` and by neither runner; `aw ipd execute-set --help` states "v1 supports ONLY --plan-only". | yes |
| D-2 | PR-001's fix requires editing six child plans outside this review's ledger. Add an `E-09` to the parent instead, or escalate as blocking? | ESCALATE as OQ-02 with `- Blocking: yes` and `- Finding: PR-001`, and do NOT add a parent item. Record in the plan why the parent-side fix is wrong. | (a) Add `E-09` to the parent: DRAFTED AND REVERTED. A runner retires an Order-0 orchestrator without running its pre-transition E/V checkpoint, so the item would be marked complete having never been performed, which is the exact lost-work failure measured in production 2026-09-08. (b) Edit the six child plans myself: rejected, they are not in the Step 0 ledger and the review's scope rule forbids expanding it; also the assignment of A4/A6 between `udgilu` and `bn026f` is a genuine authoring judgement the Set's author should make. (c) Report it as advisory and let the Set proceed: rejected, the spec is `approved` with `Blocks-Release: next`, so the six criteria gate the release and nothing downstream checks them. | Measured absence of A1/A4/A6/A19/A21 from all eight child files and of the glyphs they assert (`✘`/`↻`/`◔◑◕` all 0); the runner's retirement path skipping the E/V checkpoint; the coverage gate's question being about uncovered WORK rather than uncovered CRITERIA; `uonrjg` front matter `- Status: approved` / `- Blocks-Release: next`. | yes |
| D-3 | A17's grep is unsound (PR-004). Weaken the criterion, or keep it and add the caveat? | KEEP the grep as a necessary-but-not-sufficient signal and add the measured caveat plus an explicit instruction that `qdd5jq` must SPLIT the table. | (a) Delete the grep: rejected, it is a genuinely useful cheap signal and the Set needs a mechanical A17 check. (b) Restate A17 as a pure judgement call: rejected, that is what allowed the ambiguity in the first place. (c) Enumerate the 34 lifecycle keys in the parent: rejected, it would become a fourth table to drift, which is the problem this Set exists to end. | `term.py:117` 56 keys, 34 matched in the spec text, 22 unmatched and generic; read sites at 287/394/469/477 of which `format_badge` and `format_path` are generic; `"paths"`/`"ok"`/`"info"` 0 occurrences in the spec; spec R10.3's explicit carve-out for generic `Term` outcomes. | yes |
