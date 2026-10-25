# Spec: Quick pipeline for small changes

- Date: 2026-10-23
- Status: approved
- Blocks-Release: next
- Id: 4iyd78
- Author: aw specs new
- From-Backlog: rsisop
- Work-Kind: feature
- Priority: medium
- Set: quickpipe
- Scope: One shortened pipeline for small changes from plan straight to review and execution. Specification only; authorizes no code change.
- Constrained-by: `.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`
  (`k3yx72`, `approved`), which defines the `simple` review tier and the five tier questions the
  review agent answers to choose it, and excludes the rest of the pipeline as non-goal N4. Under its
  MD-20 the `simple` tier is built in Stage 1 and kept only if its pilot (Order 09) passes.
- Constrained-by: `.aw/records/specs/approved/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md`
  (`llbr2b`, `approved`), which owns the configurable per-(type, transition) permission surface.

## Workflow history
- 2026-10-25 approved (aw set, --by-human): Approved by maintainer 2026-10-25 in session: 'Accept both defaults + approve'. OQ-01 (verb aw ipd quick + scaffold --quick alias) and OQ-02 (explicit Pipeline: quick field) resolved to the recommendations. OQ-03 and OQ-05 remain open, non-blocking.

- 2026-10-25 note (aw specs): /spec-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; SR-001..SR-012 FIXED; OQ-05 added (Part 2 scope vs shipped --full-auto); OQ-03 decoupled from Part 1; OQ-04 resolved from evidence
- 2026-10-25 reviewed (aw set): REVIEWED - OPEN QUESTIONS; SR-001..SR-012 FIXED; OQ-01, OQ-02, OQ-03, OQ-05 open (non-blocking); OQ-04 resolved
- 2026-10-24 to-review (aw specs): Blocks release 2.0.0 (f33nrj, the planned release) per maintainer 2026-10-24

- 2026-10-24 note (aw specs): Aligned with k3yx72 as of bbceabeb2: removed references to runner tier signals and review.sensitive_paths (k3yx72 MD-1 revised, OQ-08); the Section 3.2 rules are now this spec's own admission rules, with its own quickpipe.excluded_paths list; tier stays the review agent's choice. Maintainer decision 2026-10-24 (Option A): built in two parts; Part 1 (Orders 01, 02, Part 1 tests) needs no pilot; Part 2 (Order 03 auto-approval and its tests) depends on k3yx72 Order 09 recording BUILD THE REST (MD-20).
- 2026-10-24 to-review (aw set): authored review-ready spec defining quick pipeline for small changes

- 2026-10-24 created (aw specs): Specify the quick pipeline for small changes from plan straight to review and execution

## 0. What this spec authorizes, and what it does not

THIS SPEC AUTHORIZES NO CODE CHANGE. It is a design contract produced by plan `e41qgx` from backlog
item `rsisop`, and nothing in it licenses an implementation. An executor reading this document has
no permission to build from it: implementation belongs to the follow-on Set `quickpipe`, graduated from
this spec once approved by a human maintainer, where concrete code changes, tests, and sequencing
are planned.

Every requirement in this specification is a statement about what an implementation must do when
it is built, not a claim that it already does.

## 1. Problem statement and measured pipeline cost

Backlog item `rsisop` identifies unnecessary friction when delivering small, low-risk changes (such
as a 1 to 4 line bug fix or adding a single CLI flag). Today, such changes travel the full feature
pipeline:
1. A backlog item is created in `open/` (the backlog tree has no `draft` status:
   `lifecycle_dirs.LIFECYCLE_SUBDIRS["backlog"]` is `open, graduated, blocked, parked, done`; the
   maintainer's "backlog draft" in `rsisop` names the authoring step), and picked up by a runner turn.
2. A plan-production turn authors an IPD, moving the backlog item to `graduated/`.
3. The IPD is created in `draft/`, transitioned to `to-review/`, reviewed by `/plan-review` to `reviewed/`.
4. The IPD is approved (`approved` by a human or `auto-approved` under `--full-auto`).
5. An execution turn runs the plan in an isolated worktree lane, validating and finalizing it to `executed/`.

While this multi-turn ceremonial pipeline is essential for large, cross-cutting features or architecture
changes, it imposes substantial lifecycle overhead on trivial fixes. Spec `k3yx72` addressed part of
this problem by defining the lightweight `simple` tier for `/plan-review`, but explicitly left the
rest of the pipeline (backlog, authoring, and queue dispatch) to `rsisop` (its non-goal N4).

### 1.1 Empirical measurement of small plan costs

To quantify the lifecycle cost of small changes under the current pipeline, we measured all executed
non-orchestrator plans dated 2026 having at most 2 `E-*` items.

```python
import glob, re, statistics
from pathlib import Path

# Measuring script: cost of small changes in current pipeline
files = sorted(glob.glob(".aw/records/plans/executed/2026*.ipd.md"))
non_orch = [f for f in files if "- Kind: orchestrator" not in Path(f).read_text(encoding="utf-8", errors="replace")]

small_plans = []
for f in non_orch:
    t = Path(f).read_text(encoding="utf-8", errors="replace")
    e_items = re.findall(r"^[ \t]*- \[[ xX]\][ \t]+E-\d+", t, re.MULTILINE)
    if len(e_items) <= 2:
        small_plans.append((f, t, len(e_items)))

def parse_history(text):
    m = re.search(r"## Workflow history\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if not m:
        return []
    return [l.strip() for l in m.group(1).splitlines() if l.strip().startswith("- ")]

def parse_statuses(lines):
    statuses = set()
    for l in lines:
        m = re.match(r"^-\s+\d{4}-\d{2}-\d{2}\s+([a-zA-Z0-9_\-]+)", l)
        if m:
            statuses.add(m.group(1))
    return statuses

backlog_cache = {}
for p in glob.glob(".aw/records/backlog/**/*.backlog.md", recursive=True):
    txt = Path(p).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^- Id:\s*(\S+)", txt, re.MULTILINE)
    if m:
        backlog_cache[m.group(1)] = (p, txt)

plan_hist = []
plan_stats = []
bk_hist = []
fb_rows = []

for f, t, e_cnt in small_plans:
    id6_m = re.search(r"^- Id:\s*(\S+)", t, re.MULTILINE)
    id6 = id6_m.group(1) if id6_m else Path(f).name[:6]
    fb_m = re.search(r"^- From-Backlog:\s*(\S+)", t, re.MULTILINE)
    fb = fb_m.group(1) if fb_m else None

    h = parse_history(t)
    st = parse_statuses(h)

    plan_hist.append(len(h))
    plan_stats.append(len(st))

    bh_len = None
    if fb and fb in backlog_cache:
        bh = parse_history(backlog_cache[fb][1])
        bh_len = len(bh)
        bk_hist.append(bh_len)
        fb_rows.append((id6, fb, len(h), len(st), bh_len, e_cnt))

print(f"Total small plans: {len(small_plans)}")
print(f"Plans carrying From-Backlog: {len(fb_rows)}")
print(f"Median plan history records: {statistics.median(plan_hist)}")
print(f"Median plan distinct statuses: {statistics.median(plan_stats)}")
print(f"Median backlog history records: {statistics.median(bk_hist)}")
```

Re-measured at spec review (HEAD `182161e5d`, 2026-10-24; the authoring plan `e41qgx` measured 151
and 21 at its own execution HEAD, and the population grows as plans execute), the script yields:
- Total small executed non-orchestrator plans: 153
- Plans carrying `- From-Backlog:`: 23
- Median plan `## Workflow history` records: 4
- Median plan distinct lifecycle statuses: 2
- Median backlog `## Workflow history` records (for plans linked to a backlog item): 3

Of the same 153 small plans, measured at the same HEAD for the admission rules of Section 3.2: 45
carry `- Scope-Paths:` (the field postdates most of them), 38 of those 45 declare at most 3 entries
(median 2), and 121 of 153 have at most one `### Task group` heading.

### 1.2 Per-plan records for small changes carrying a backlog item

The 23 small executed plans carrying `- From-Backlog:` (HEAD `182161e5d`) demonstrate the cumulative
history records written across both artifacts for a 1 or 2 item execution:

| Plan ID | Backlog ID | E-Items | Plan History Records | Distinct Plan Statuses | Backlog History Records |
|---|---|---|---|---|---|
| 3v7wo6 | 5wdoze | 2 | 6 | 5 | 1 |
| yi24m0 | rayd4c | 2 | 6 | 5 | 3 |
| dtcgsz | y2vnr7 | 1 | 5 | 5 | 3 |
| 9g97e5 | 2je7m3 | 1 | 6 | 5 | 3 |
| fdmo2v | 5v4p2l | 1 | 5 | 5 | 3 |
| dmrbqa | tl8qmc | 2 | 6 | 5 | 4 |
| pua92o | rgl2d4 | 2 | 5 | 4 | 4 |
| aoy1uk | rdtme9 | 1 | 5 | 5 | 3 |
| jzeeky | m88gwh | 2 | 5 | 5 | 3 |
| ic6vpg | upkghw | 2 | 5 | 5 | 3 |
| 5apgyn | pyezbc | 2 | 4 | 4 | 3 |
| f0kolj | g3ropl | 2 | 6 | 5 | 3 |
| 8e7xrj | 2n9y3f | 1 | 6 | 5 | 3 |
| 5ne0fo | zgqs4e | 2 | 6 | 5 | 3 |
| jl0bv0 | a48b4m | 1 | 6 | 5 | 3 |
| 3nczai | 6i9viq | 2 | 5 | 5 | 3 |
| rg7rnx | 96lj37 | 2 | 5 | 5 | 3 |
| s56tsu | q2cgcu | 2 | 5 | 5 | 3 |
| 438gkf | liybkg | 2 | 5 | 5 | 3 |
| 8bhcd3 | yqpb7q | 2 | 5 | 5 | 3 |
| 78g6ic | q86fxm | 2 | 5 | 5 | 48 |
| ej30u4 | w4eswb | 2 | 5 | 5 | 3 |
| x8p9ek | qtd3lj | 2 | 5 | 5 | 3 |

Runner turn and cost attribution: Invoking `aw runs --ipd <id6>` (e.g. for `yi24m0`) and `aw runs --last 5`
returns `no matching runs found` in this lane worktree, so runner turns and monetary costs cannot be
attributed from local run ledgers at this HEAD.

## 2. Existing pipeline stages and enforcement inventory

Not all stages of the existing pipeline are equally enforced. Some are mandatory safety gates that
prevent data loss or unvalidated code from reaching the main tree; others are convention or ceremony.

### 2.1 Live census of plans without backlog or spec parents

To evaluate whether the backlog step is already optional in practice, we measured the population of
non-orchestrator plans from 2026-09 and 2026-10 carrying neither `- From-Backlog:` nor `- From-Spec:`.

```python
import glob, re
from pathlib import Path

files = sorted(glob.glob(".aw/records/plans/executed/202609*.ipd.md") + glob.glob(".aw/records/plans/executed/202610*.ipd.md"))
non_orch = [f for f in files if "- Kind: orchestrator" not in Path(f).read_text(encoding="utf-8", errors="replace")]

neither_count = 0
for f in non_orch:
    t = Path(f).read_text(encoding="utf-8", errors="replace")
    has_fb = bool(re.search(r"^- From-Backlog:\s*\S+", t, re.MULTILINE))
    has_fs = bool(re.search(r"^- From-Spec:\s*\S+", t, re.MULTILINE))
    if not has_fb and not has_fs:
        neither_count += 1

print(f"Executed non-orchestrator plans (2026-09/10): {len(non_orch)}")
print(f"Neither From-Backlog nor From-Spec: {neither_count}")
```

Re-measured at spec review (HEAD `182161e5d`): 95 of 1,124 executed non-orchestrator plans dated
2026-09/10 carried neither `- From-Backlog:` nor `- From-Spec:` (across all plan statuses in that date
range, 98 of 1,155; the authoring plan measured 92 of 1,117 and 100 of 1,178 at its own HEAD).
This confirms that scaffolding a plan directly without a prior backlog item is already supported by
`ipd_authoring.run_scaffold` when `--priority` and `--work-kind` are supplied.

Furthermore, running `aw ipd scaffold --kind child --title "Test Scaffold" --set quickpipe --order 2 --priority low --work-kind chore --author test` confirms that `ipd_authoring.build_skeleton` unconditionally initializes plans to `draft` (`- Status: draft`).

### 2.2 Inventory of pipeline stages, enforcing symbols, and skipping consequences

| Stage | Enforcing Symbol | Skippable Today? | Loss if Skipped (Ceremony vs Safety Gate) |
|---|---|---|---|
| 1. Backlog item creation | `ipd_authoring.run_scaffold` | Yes | Ceremony. Requires `--priority`/`--work-kind` when `--from-backlog` is absent. Drops initial idea tracking, but creates no safety hazard if the plan defines scope and tests. |
| 2. Initial status assignment | `ipd_authoring.build_skeleton` | No | Ceremony. Always writes `- Status: draft`. Forces an authoring-to-review status transition. |
| 3. Status progression skips | `ipd_lifecycle.validate_transition` | Partial | Safety gate. Forward skips (e.g. `draft -> reviewed`) are permitted, but moving to `executed` strictly requires at least `reviewed`. Bypassing this would risk unreviewed execution. |
| 4. Readiness attestation | `ipd_lint.check_readiness_required` (`IPD-M113`), `ipd_lint.check_readiness_attestation` (`IPD-M107`) | No | Safety gate. Refuses a `reviewed` or ready-to-execute plan lacking an attested `- Readiness:` field from `/plan-review`. Hand-written readiness is rejected. |
| 5. Human approval authority | `attention_contract.TRANSITION_AUTHORITY["->approved"]`, `status_set.validate_transition_allowed` | Specs: No; Plans: Convention | Safety gate. `TRANSITION_AUTHORITY` enforces `--by-human` mechanically for specs. For plans, `approved` is human by convention plus setter gates; `auto-approved` is the sanctioned automated tier. |
| 6. Setter-side approval gate | `plan_readiness.approval_refusals`, `ipd_schema.READY_TO_EXECUTE` | No | Safety gate. `status_set.validate_transition_allowed` refuses ready-to-execute status if review failed, or if blocking questions/findings remain. |
| 7. Automated approval | `runner_shared.set_plan_approved`, `plan_readiness.is_plan_review_approved`, `runner_shared.initialize_run_core`, `runner_shared.execute_item_core` | Under `--full-auto` | Safety gate. Advances `reviewed -> auto-approved` and rewrites queue action to `execute` only when review readiness is positive. Preserves D65 (executor cannot self-approve). |
| 8. Queue action mapping | `run_selection_policy.runner_action`, `runner_shared.item_needs_approval` | No | Safety gate. Unapproved `reviewed` plans freeze with `needs_input=True` unless `--full-auto` auto-approves them. |
| 9. Backlog graduation | `aw backlog set graduated`, `production_checks.backlog_graduate_set` (`BACKLOG-GRADUATE-SET`) | Yes (if no backlog item) | Ceremony for small plans. When no backlog item exists, no graduation turn is needed; plan-level lint and review gates provide full verification. |

## 3. Qualification criteria: which changes qualify

The quick pipeline is intended exclusively for small, low-risk changes where the friction of the
backlog and multi-turn staging exceeds the risk of the change itself.

### 3.1 Base criteria from spec `k3yx72`

Spec `k3yx72` Section 5.1 defines the `simple` review tier as:
> "Very low risk: typically a few lines of code, such as a small bug fix or one new CLI option."

Spec `k3yx72` Section 5.2 has the review agent choose the tier after answering five recorded
questions: whether the plan changes a spec or other contract; whether it touches code that guards
private data, commits, worktree isolation, merges to main, or the sandbox; whether it is large or
cross-cutting; whether it lists the files it changes; and whether a mistake could lose data, break
dependent behavior, or be hard to undo. Under `k3yx72` MD-1 (revised 2026-10-19) the runner forces no
tier: it records the tier and the answers. `k3yx72` defines no runner signals and no
`review.sensitive_paths` setting (its OQ-08 was resolved as "no such list").

The quick pipeline therefore adds its OWN admission rules (Section 3.2). They decide whether a plan
may use the quick pipeline; they do not change the review tier, which stays the review agent's
choice.

### 3.2 Stricter mechanical bounds for the quick pipeline

The quick pipeline admits a plan only when all of the following hold. These are admission rules of
this spec, checked by the quick-pipeline code (Section 7.1) and the runner (Section 7.2 Order 03, Part 2 only); they
are grounded in Section 1's measurements:

1. **Orchestrator exclusion** (`- Kind: orchestrator`): Disqualified mechanically. Orchestrators
   coordinate child plans, manage rollup retirement, and never execute small self-contained edits.
2. **Open blocking questions** (`Blocking: yes`): Disqualified mechanically via
   `plan_readiness.has_unresolved_blocking_question`. A plan cannot execute unattended with unresolved
   design questions.
3. **Attended execution required** (`- Attended: required`): Disqualified mechanically via
   `ipd_schema.META_ATTENDED`. Unattended quick execution cannot run interactive turns.
4. **Spec modification** (`.spec.md` in `- Scope-Paths:`): Disqualified mechanically. Changing
   specifications alters system invariants and requires standard or complex review.
5. **Guarded code**: Disqualified mechanically when `- Scope-Paths:` names a path on this spec's own
   list `quickpipe.excluded_paths` in `.aw/config/project.json` (package default: empty). This
   repository seeds it with the modules `k3yx72` Section 5.2 question 2 names as examples:
   `agent_workflows/leak_sanitizer.py`, `agent_workflows/local_leaks.py`,
   `agent_workflows/git_commit_helper.py`, `agent_workflows/commit_lock.py`,
   `agent_workflows/lane_containment.py`, `agent_workflows/egress_policy.py`,
   `agent_workflows/host_sandbox_profile.py`. The list limits only the quick pipeline; it does not
   force a review tier. Matching: each `- Scope-Paths:` entry and each list entry is compared as a
   normalized repo-relative POSIX path; a list entry ending in `/` matches every path under that
   directory, any other list entry matches that exact path only.
6. **Grandfathered scope** (missing `- Scope-Paths:`): Disqualified mechanically. Scope must be
   explicitly bounded. The scaffold placeholder (a value beginning `TODO`) counts as missing.
7. **Strict item count**: At most 2 `E-*` items and at most 1 `### Task group` heading. The general
   lint size warning (`ipd_schema.MAX_E_LEAVES`, 18) does not apply; the quick path strictly requires
   `<= 2` `E-*` items.
8. **Strict path count**: At most 3 distinct entries declared in `- Scope-Paths:`, and every entry a
   literal path. An entry containing a glob or pathspec metacharacter (`*`, `?`, `[`, or a leading
   `:`) disqualifies the plan, because one such entry can name an unbounded set of files. Prevents
   wide or cross-cutting edits.
9. **Reviewer judgement**: the review agent rates the plan `simple` after answering the five tier
   questions of `k3yx72` Section 5.2 (check T). Any other tier disqualifies the plan from the quick
   pipeline.

| Criterion | Type | Source / Enforcement |
|---|---|---|
| Kind is child | Mechanical | Plan front matter (`- Kind: child`) |
| No open blocking questions | Mechanical | `plan_readiness.has_unresolved_blocking_question` |
| Attended not required | Mechanical | `ipd_schema.META_ATTENDED` != "required" |
| No spec files modified | Mechanical | `- Scope-Paths:` contains no `.spec.md` |
| No guarded code touched | Mechanical | `- Scope-Paths:` matches no `quickpipe.excluded_paths` entry |
| Explicit scope paths | Mechanical | `- Scope-Paths:` is non-empty and not the `TODO` placeholder |
| Small execution size | Mechanical | Count of `E-*` items <= 2, Task Groups <= 1 |
| Small path footprint | Mechanical | Count of declared entries in `- Scope-Paths:` <= 3, none a glob or pathspec |
| Review tier is `simple` | Judgement | Review agent check T, five tier questions (spec `k3yx72` 5.2) |

## 4. Deciding role and disagreement fallback

### 4.1 Consistency with `k3yx72` MD-1

Spec `k3yx72` MD-1 (revised 2026-10-19) says the review agent rates the tier after answering the five
tier questions, and the runner forces no tier.

The quick pipeline respects this. An author cannot force quick execution, the runner never changes
the tier the review assigned, and the admission rules of Section 3.2 only decide whether a plan the
review rated `simple` may take the quick path.

### 4.2 Deciding options considered

1. **Option A (Author proposal with Review confirmation)**: The author indicates quick pipeline intent
   via front matter (`- Pipeline: quick`). The review agent evaluates Check T. If Check T confirms
   `simple` tier and every admission rule of Section 3.2 passes, the quick pipeline proceeds.
2. **Option B (Implicit tier derivation)**: No front-matter field. The quick path is entered purely if
   the review agent assigns `simple` and every admission rule of Section 3.2 passes.
3. **Option C (CLI creation flag only)**: A human flag on creation dictates the pipeline.

**Recommendation**: Option A (Recommendation strength: Strong).
Recording authorial intent in front matter allows authoring tools (`aw ipd quick`) to validate size
bounds upfront, makes the expectation obvious to reviewers, and prevents unexpected fast-tracking
of plans not written for the quick pipeline.

The proposed field is `- Pipeline:` with the closed value set `{"standard", "quick"}` (defaulting to
`standard` when absent). The implementing Set must register `Pipeline` in `ipd_schema.META_RECOGNIZED`,
and a PRESENT value outside the closed set is a metadata error (the shape `ipd_schema` already uses for
`- Attended:`), never a silent default to `standard`.

`- Pipeline: quick` RECORDS INTENT and confers nothing by itself: under Part 1 it changes no gate, no
status, and no queue action, and under Part 2 it is one input to the Section 5.2 rule. Section 3.2
admission is evaluated against the plan's CURRENT text at each point it is checked, so a plan edited
after authoring (for example by review revisions) is re-judged rather than admitted on its original
shape.

### 4.3 Disagreement and fallback rule

If the review agent rates the tier as `standard` or `complex`, or if any mechanical disqualifier fires:
- The plan immediately falls back to the standard pipeline.
- `- Pipeline: quick` is treated as unfulfilled intent; no history is discarded, no files are deleted,
  and no synthetic human steps are created.
- The plan stops at `reviewed` for normal human approval (or standard `--full-auto` clearance).

## 5. Approval authority and session separation

### 5.1 Human approval vs automated clearance

The repository attestation model requires that:
1. `->approved` remains an attested human act.
2. Automated clearance into execution uses `auto-approved` exclusively, requiring an approving
   `- Readiness:` verdict from `/plan-review` (`plan_readiness.is_plan_review_approved`).
3. D65 holds: `auto-approved` is set only by an automated checker / runner controller, never by an
   executor fast-tracking its own work.

Today, `attention_contract.TRANSITION_AUTHORITY["->approved"]` (`by_human`) is enforced by
`status_set.validate_transition_allowed` for specs only (the check sits inside its
`rec.record_type == "specs"` branch); for plans, human approval is enforced by convention and the
setter gate `plan_readiness.approval_refusals`, and a plan set to `approved` without `--by-human`
records `- Approval: <date>, recorded via aw ipd set: ...` instead of `human ("approved")`
(`status_set.apply_status_change`).

Making `--by-human` mechanically REQUIRED for a plan entering `approved` is a decision this spec does
NOT take: it is OQ-03 below, and AC-05 applies only if the maintainer adopts it. It is a cross-cutting
behavior change to a shipped verb (every existing script, test fixture, and workflow that runs
`aw ipd set approved` without the flag would be refused), it is not needed by either Part of the quick
pipeline (Part 2 uses `auto-approved`, never `approved`), and `llbr2b` Section 6.4 already lists
`ipd:*->approved` as contract-closed to automation, which constrains automated actors rather than
the CLI flag. If adopted, it must ship with that compatibility consequence stated in its plan.

### 5.2 Composition with lifecycle automation policy (spec `llbr2b`)

Spec `llbr2b` establishes a unified permission matrix for automated transitions. The quick pipeline
does not create a parallel or conflicting switch.
- Under `llbr2b`, the transition `("plans", "->auto-approved")` is governed by policy.
- When `llbr2b` policy permits `("plans", "->auto-approved")` (or runner `--full-auto` is active),
  and a plan qualifies for the quick pipeline with an approving review readiness, the runner sets
  `auto-approved`.
- If `llbr2b` policy denies the transition or `--full-auto` is disabled, the plan stops at `reviewed`,
  requiring explicit human approval (`aw ipd set approved <id6> --by-human`).

MEASURED BASELINE THE PART 2 RULE MUST BE STATED AGAINST (HEAD `182161e5d`). Under `--full-auto` the
runner ALREADY sets `auto-approved` for EVERY `reviewed` plan whose readiness is approving, whatever
its size or tier: at queue build (`runner_shared.initialize_run_core`, the
`status == "reviewed" and full_auto` branch) and after a review turn
(`runner_shared.execute_item_core`, which also rewrites the item's action to `execute` and its status
to `queued`, emitting `ipd-auto-approved`). `llbr2b` is approved but not yet implemented: no module
under `agent_workflows/` reads its policy key. So "auto-approve a qualifying `simple` plan under
`--full-auto`" is today's behavior for every plan and adds nothing. What Part 2 changes relative to
this baseline (auto-approval of a qualifying quick plan WITHOUT `--full-auto`, or restricting
`--full-auto` auto-approval, or something else) is the maintainer's decision, OQ-05. No Part 2 plan
may be authored until OQ-05 is answered.

### 5.3 Host session and turn separation

Authoring, review, and execution MUST NOT share a single host session or agent turn.
- **Attestation independence**: A review agent must examine the plan in a fresh context, free from
  authoring biases, to independently evaluate risk and produce an authentic `- Readiness:` record.
- **Executor isolation**: Execution must take place in an isolated worktree lane (`isolate_worktree`)
  with a clean git status, baseline checks, and merge-and-revalidate gating.
- **Contiguous execution**: While turns are distinct and isolated, the runner may run review and
  execution sequentially in a single unattended batch run when auto-approval is permitted. This is
  SHIPPED behavior, not new work: `runner_shared.execute_item_core` re-queues an auto-approved item as
  `execute` in the same run (OQ-04, resolved). Authoring a quick plan is not a runner turn: it is the
  `aw ipd quick` command (Section 7.1), run by a human or an agent before the run.

## 6. Tracked records and release gate preservation

### 6.1 Records lifecycle table

| Record | Disposition | Justification |
|---|---|---|
| Backlog item and history | Dropped | Dropped to eliminate the backlog create/graduate steps for small changes. |
| Plan file (`.ipd.md`) | Kept | Primary unit of work and historical truth. |
| Plan `## Workflow history` | Kept | Retains audit trail of status progression (`draft -> to-review -> reviewed -> auto-approved -> executed`). |
| `E-*` and `V-*` evidence | Kept | Pasted execution and validation evidence is a mandatory repository invariant. |
| Review record (`.review.md`) | Kept | Written by `/plan-review` under `.aw/records/reviews/` to document tier answers and checks. |
| `- Readiness:` field | Kept | Attested by review; required by `ipd_lint.check_readiness_required` (`IPD-M113`). |
| `aw ipd begin` receipt | Kept | Written by runner to prevent concurrent execution conflicts. |
| Finalize commit | Kept | Atomic commit moving plan to `executed/` under integration gate. |
| Walkthrough document | Not required | Not required for any plan today either (27 walkthroughs exist beside 1,628 executed plans at HEAD `182161e5d`), so this is no saving; the quick pipeline adds no walkthrough obligation. |

### 6.2 Preserving the release gate for bug fixes

In the standard pipeline, bug tracking and release gating operate through backlog items:
`check_engine.check_live_bug_gate` scans live backlog items and fails if any bug item lacks
`- Blocks-Release:`.
Currently, `aw ipd scaffold --work-kind bug` without `--from-backlog` writes no `- Blocks-Release:`
bullet. If a bug plan were scaffolded directly without a backlog item, it would escape release gating.

The quick pipeline closes this loophole with two mandatory mechanisms:
1. **Scaffold-time gate assignment**: The quick creation command (`aw ipd quick`) decides the gate
   through the existing single authority `backlog.decide_gate_default` (keyword-only `kind`,
   `status`, `explicit_blocks_release`, ...; it takes no `priority`), so the plan gets exactly the
   behavior a backlog item gets: a work kind in the repository's `release_gate_work_kinds` (default
   `bug` alone) is written `- Blocks-Release: next`; an explicit `--blocks-release` value (including
   `-`) wins; and when `next` resolves to no planned release the plan is written UNGATED with the
   function's notice printed, rather than refused. A second, plan-local copy of that decision is not
   permitted.
2. **Plan-side release gate check**: The implementing Set must add a `check_engine.py` rule (a new
   `check_live_plan_bug_gate`, or an extension of `check_live_bug_gate`, which today reads only
   backlog items) that flags a plan under `.aw/records/plans/pending/` whose `- Work-Kind:` is in
   `config.release_gate_work_kinds` and which carries no `- Blocks-Release:`. The rule covers every
   pending plan, not only quick plans, since the loophole is `aw ipd scaffold` without
   `--from-backlog`, not the quick verb. Measured at HEAD `182161e5d`: 2 pending plans carry
   `- Work-Kind: bug` and both carry `- Blocks-Release:`, so the rule flags nothing on arrival.
   Executed and retired plans are never flagged, matching the backlog rule's treatment of `done`.

### 6.3 Cross-tree visibility in `aw attention` and the runner queue

- `aw attention`: The cross-tree attention view scans `.aw/records/plans/` directly. A quick plan is
  tracked from inception: `draft`, `to-review`, `reviewed`, `approved` and `auto-approved` all map to
  `ready` (`attention_contract._PLANS_MAP`). It requires no backlog entry to be visible.
- Runner Queue: the queue is ordered by `runner_shared.queue_sort_key`, whose first key is
  `runner_shared.dependency_depth`. A quick plan with no in-queue prerequisite has depth 0 and is
  dispatchable as soon as its status permits.

## 7. Entry point, work breakdown, and open questions

### 7.1 User-facing entry point

The primary user entry point is `aw ipd quick`:
```sh
aw ipd quick --title "Fix typo in CLI help" --set clihelp --work-kind bug --priority low --author opencode --scope "agent_workflows/cli.py" --apply
```
This command:
- Calls `ipd_authoring.run_scaffold` with `--quick`.
- Requires `--set`, exactly as `aw ipd scaffold` does, and writes a `- Kind: child` plan. `--order`
  is optional and defaults to the lowest free child Order (>= 1) in that Set, so a quick plan never
  silently duplicates an Order (`plans.set_warnings` reports duplicate Orders in a Set).
- Writes `- Pipeline: quick` into front matter, and `--scope` into `- Scope-Paths:`.
- Sets `- Work-Kind:` and `- Priority:` (both required, as for `aw ipd scaffold` without
  `--from-backlog`).
- Decides `- Blocks-Release:` through `backlog.decide_gate_default` (Section 6.2).
- Checks every admission rule decidable at creation (rules 4, 5, 6 and 8 of Section 3.2, on the
  `--scope` value). A violation REFUSES: the command exits nonzero, names each violated rule and the
  offending path, and writes no file. It never silently falls back to writing a `standard` plan.

Admission after creation. A `- Pipeline: quick` plan that later fails a Section 3.2 rule (for
example review revisions add a third `E-*` item) is NOT a lint error, because R-05 requires a clean
fall back to the standard pipeline: `aw ipd lint` reports it as a WARNING naming the failed rule and
stating the plan will take the standard path, and no gate refuses on it.

Code surfaces extended by the implementing Set:
- `agent_workflows/cli.py`: Register `quick` subparser in `ipd_sub`.
- `agent_workflows/command_surface.py`: Add `aw ipd quick` to `COMMAND_INVENTORY`.
- `agent_workflows/ipd_authoring.py`: Implement `run_quick` / extend `run_scaffold`.
- `agent_workflows/ipd_schema.py`: Register `Pipeline` in `META_RECOGNIZED`.
- `agent_workflows/check_engine.py`: Add plan-side bug release gate.
- `agent_workflows/runner_shared.py`: (Part 2 only, shape set by OQ-05) the quick-pipeline
  auto-approval rule.

### 7.2 Implementing work breakdown (Set `quickpipe`)

| Order | Work | Depends on | Documentation to Amend |
|---|---|---|---|
| 00 | Orchestrator: Child tracking and rollup. | All children | None |
| 01 | Plan schema and authoring entry point: Register `Pipeline` in `ipd_schema.META_RECOGNIZED`, implement `aw ipd quick`, and apply `backlog.decide_gate_default`. | Spec approval | `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`, `.aw/records/plans/README.md` |
| 02 | Release gate integrity: Implement plan-side bug gate in `check_engine.py` ensuring active bug plans require `- Blocks-Release:`. | Order 01 | `docs/artifact-lifecycles.md` |
| 03 | (Part 2) Runner integration: read the `- Review-Depth:` tier that `k3yx72` Order 02 records; when it is `simple`, the plan carries `- Pipeline: quick`, and every Section 3.2 admission rule passes on the current text, apply the auto-approval rule OQ-05 decides, through the `llbr2b` predicate once that exists. Contiguous review-then-execute dispatch is already shipped (Section 5.3) and needs no new work. | Order 01, OQ-05 answered, `k3yx72` Order 09 executed with a BUILD THE REST decision (MD-20), `llbr2b` | `docs/artifact-lifecycles.md` |
| 04 | Verification and regression tests. Part 1: CLI tests and admission-rule rejection tests (with Orders 01 and 02). Part 2: runner simulation (with Order 03). May be two plans. | Orders 01, 02; Part 2 also 03 | None |

Build parts (maintainer decision 2026-10-24, Option A). The quick pipeline is built in two parts so
that nothing waits on the `k3yx72` pilot except what depends on its result:

- **Part 1 (build after this spec is approved):** Orders 01 and 02, and the Part 1 tests of Order 04.
  These give `aw ipd quick`, the `- Pipeline:` field, the admission rules, and the plan-side release
  gate for bug plans, and they let a small plan skip the backlog item. A Part 1 quick plan still goes
  through the normal review and approval path.
- **Part 2 (build only after the `k3yx72` pilot passes):** Order 03 and the Part 2 tests of Order 04,
  the automatic approval of a plan the review rated `simple`, in the form OQ-05 decides. Under `k3yx72` MD-20 the `simple` tier
  is built in its Stage 1 and kept only if the pilot (`k3yx72` Order 09) records a BUILD THE REST
  decision. Each Part 2 plan therefore lists `executed:<k3yx72 Order 09 id6>` in
  `- Item-Dependencies:`, and is authored only after that decision is recorded. If the pilot records
  STOP, Part 2 is not built, and quick plans keep using the normal approval path.

### 7.3 Open questions for the maintainer

#### OQ-01: Entry point syntax: dedicated verb vs scaffold flag

- Blocking: no
- Status: resolved
- Owner: maintainer
- Question: Should the quick pipeline entry point be a dedicated CLI verb (`aw ipd quick`) or a flag on the existing scaffold command (`aw ipd scaffold --quick`)?
- Recommendation: Dedicated verb `aw ipd quick`, aliasing `aw ipd scaffold --quick`.
- Recommendation strength: Strong. A distinct verb emphasizes the streamlined workflow while preserving discoverability.
- Closes when: the maintainer answers, at or before approval of this spec. The default if approved unanswered is the recommendation (both spellings, one implementation).
- Resolution: RESOLVED 2026-10-25 by the user via /askme: accepted the recommendation. Dedicated verb `aw ipd quick`, aliasing `aw ipd scaffold --quick` (both spellings, one implementation). No reason was given.

#### OQ-02: Front-matter marker: explicit field vs implicit derivation

- Blocking: no
- Status: resolved
- Owner: maintainer
- Question: Should plans declare `- Pipeline: quick` in front matter, or should the runner infer quick handling solely from a `simple` review tier and the Section 3.2 admission rules?
- Recommendation: Explicit `- Pipeline: quick` field.
- Recommendation strength: Moderate. Explicit declaration makes author intent unambiguous and allows upfront linting.
- Closes when: the maintainer answers, at or before approval of this spec. Section 4.2 and R-06 already assume the recommendation; choosing implicit derivation instead deletes R-06 and the field from AC-01.
- Resolution: RESOLVED 2026-10-25 by the user via /askme: accepted the recommendation. Explicit `- Pipeline: quick` front-matter field; R-06 and AC-01 stand as written. No reason was given.

#### OQ-03: Plan approval mechanical enforcement

- Blocking: no
- Status: open
- Owner: maintainer
- Question: Should `aw ipd set approved` REFUSE a plan without `--by-human` (mirroring specs), rather than recording `- Approval: ..., recorded via aw ipd set` as it does today? This is independent of the quick pipeline: neither Part needs it. If adopted it is a breaking change to a shipped verb, and its plan must list the callers, tests, and workflow texts that run `aw ipd set approved` without the flag.
- Recommendation: Adopt it, as its own plan in this Set (not folded into Order 01), with the compatibility census above.
- Recommendation strength: Moderate. It closes a mislabelled-approval path, but `llbr2b` 6.4 already forbids automated actors from writing `approved`, so the residual risk is a human or agent typing the bare command.
- Closes when: the maintainer answers. If declined, R-07's mechanical clause and AC-05 are deleted.

#### OQ-04: Contiguous runner dispatch

- Blocking: no
- Status: resolved
- Owner: maintainer
- Question: Should the runner execute review and execution in separate turns within the same unattended batch run, or require separate runner invocations?
- Resolution: Resolved from repository evidence at spec review (2026-10-24): already shipped. `runner_shared.execute_item_core` re-queues an item auto-approved after its review turn as `action: execute`, `status: queued` in the same run, unless the run's action is `review`. Execution remains a separate turn in its own lane. No new behavior is specified.

#### OQ-05: What Part 2 auto-approval adds to today's `--full-auto`

- Blocking: no (it blocks authoring any Part 2 plan, not approval of this spec or Part 1)
- Status: open
- Owner: maintainer
- Question: Today `--full-auto` already auto-approves EVERY `reviewed` plan with an approving readiness, of any size (Section 5.2, measured). So Part 2's "auto-approve a qualifying `simple` quick plan" must mean something else. Which? (a) A qualifying quick plan is auto-approved even in a run WITHOUT `--full-auto` (a new, narrower automatic clearance; the material risk change). (b) `--full-auto` keeps today's behavior, and Part 2 only records that the plan took the quick path (analytics, no behavior change). (c) Under `--full-auto`, only qualifying plans are auto-approved, and other plans stop at `reviewed` (a tightening of shipped behavior). (d) Drop Part 2.
- Recommendation: (a), behind an explicit per-repository opt-in that is off by default, expressed as an `llbr2b` policy entry once that predicate exists.
- Recommendation strength: Moderate. It is the only option that removes a human step for small changes, which is what `rsisop` asked for; off-by-default keeps every existing run unchanged.
- Closes when: the maintainer chooses. AC-04 is then rewritten to that choice before any Part 2 plan is authored.

## 8. Requirements index (canonical declaration site)

This table is the single canonical declaration of this spec's requirements; the cited sections
elaborate them.

| ID | Requirement | Detail |
|---|---|---|
| R-01 | The quick pipeline authorizes no code change until an approved implementing plan executes. | 0, 7.2 |
| R-02 | Quick plans are created directly without requiring a backlog item or backlog graduation turn. | 1.1, 2.2, 6.1 |
| R-03 | A plan must satisfy every admission rule (not an orchestrator, no open blocking questions, no attended requirement, no spec edits, no `quickpipe.excluded_paths` entry, explicit `- Scope-Paths:`, at most 2 E items, 1 task group, and 3 paths) to qualify. | 3.2 |
| R-04 | The review agent assigns the tier from the five tier questions of `k3yx72` Section 5.2; the runner never changes it. The Section 3.2 admission rules decide only whether a `simple` plan may use the quick pipeline. | 3.1, 3.2, 4.1 |
| R-05 | A plan failing any qualification criterion or rated above `simple` falls back cleanly to the standard pipeline. | 4.3 |
| R-06 | Author intent is recorded via `- Pipeline: quick` in front matter, registered in `ipd_schema.META_RECOGNIZED`; a value outside `{standard, quick}` is a metadata error. The field confers nothing by itself. | 4.2, 7.1 |
| R-07 | Human approval `->approved` remains an attested human act; no quick-pipeline code writes `approved`, and automated clearance sets `auto-approved` exclusively. Mechanical refusal of `aw ipd set approved` without `--by-human` applies only if OQ-03 is adopted. | 5.1, OQ-03 |
| R-08 | (Part 2) Any quick-pipeline automated clearance to `auto-approved` requires an approving review readiness verdict (`is_plan_review_approved`), a recorded `simple` tier, `- Pipeline: quick`, and every Section 3.2 rule passing on the current text, and is subject to `llbr2b` policy. Its scope relative to shipped `--full-auto` is set by OQ-05. Built only after the `k3yx72` pilot records BUILD THE REST. | 5.1, 5.2, 7.2 |
| R-09 | Review and execution of a quick plan are separate agent turns, and execution runs in an isolated worktree lane. | 5.3 |
| R-10 | Plan files, history records, review records, and E/V evidence are kept for quick plans exactly as for standard plans. | 6.1 |
| R-11 | A plan created by `aw ipd quick` gets its `- Blocks-Release:` from `backlog.decide_gate_default`, and `aw check` flags any pending plan whose work kind is in `release_gate_work_kinds` and which carries no `- Blocks-Release:`. | 6.2 |
| R-12 | The CLI provides `aw ipd quick` as the primary authoring entry point, and it refuses (nonzero exit, no file written) when a creation-time admission rule fails. | 7.1 |

## 9. Acceptance criteria for the implementing Set

| ID | Covers | Criterion | Evidence |
|---|---|---|---|
| AC-01 | R-02, R-06, R-12 | In a fixture repository with no backlog items, `aw ipd quick ... --scope <one literal path> --apply` exits 0 and writes one `pending/` plan carrying `- Kind: child`, `- Pipeline: quick`, `- Status: draft`, the given `- Scope-Paths:`, and no `- From-Backlog:`; `aw ipd lint --phase author` reports no error on it. | CLI output, exit code, and the generated file's front matter. |
| AC-02 | R-03, R-12 | `aw ipd quick` REFUSES, exiting nonzero with a message naming the rule and path and writing no file, for each of: a `.spec.md` scope entry; a `quickpipe.excluded_paths` entry (exact path, and a path under a `/`-terminated entry); 4 scope entries; a glob entry; an empty `--scope`. | One test per refusal asserting exit code, message, and that no file was created. |
| AC-03 | R-03, R-05, R-06 | A `- Pipeline: quick` plan edited to violate a Section 3.2 rule after creation (3 `E-*` items; 2 task groups; `- Kind: orchestrator`; `- Attended: required`; an open `Blocking: yes` question) gets an `aw ipd lint` WARNING naming the rule, no lint ERROR, and stays eligible for the standard path. A `- Pipeline:` value outside `{standard, quick}` is a lint ERROR. | Lint diagnostics and exit codes per case. |
| AC-04 | R-04, R-05 | A quick plan whose recorded tier is `standard` reaches `reviewed` and stops there for normal approval (or standard `--full-auto` clearance); its `- Review-Depth:`, workflow history, and review record are unchanged by any quick-pipeline code. | Plan file before and after; runner state. |
| AC-05 | R-07 | (Only if OQ-03 is adopted) `aw ipd set approved <plan>` without `--by-human` exits nonzero and leaves the plan unchanged; with `--by-human` it succeeds. Regardless of OQ-03: no quick-pipeline code path writes `approved`. | Command exit codes and plan text; test asserting the quick code path's transitions. |
| AC-06 | R-08 | (Part 2, rewritten to OQ-05's answer before any Part 2 plan is authored) A qualifying `simple` quick plan with an approving readiness is set `auto-approved` under the chosen rule; the same plan with readiness `no-go`, with tier `standard`, without `- Pipeline: quick`, or failing any Section 3.2 rule is NOT; and when `llbr2b` policy denies `ipd:reviewed->auto-approved` it is not. | Runner state, `ipd-auto-approved` events, and plan status per case. |
| AC-07 | R-09 | (Part 2) In a run that auto-approves a quick plan after review, the review and the execution are separate attempts in the run ledger and the execution attempt ran in its own lane worktree. | Run ledger attempts for the item. |
| AC-08 | R-11 | `aw ipd quick --work-kind bug` writes `- Blocks-Release: next` when a planned release exists, and writes no gate plus the `decide_gate_default` notice when none exists; `--blocks-release -` writes none. `aw check` flags a pending plan with `- Work-Kind: bug` and no `- Blocks-Release:` under the plan-side rule id, does not flag one with the gate, and does not flag an executed one. | CLI output and front matter; `aw check` diagnostics per fixture. |

R-01 is covered by the lifecycle itself (no plan of this Set may execute before this spec is
approved) and R-10 by the unchanged finalize gates; neither needs a new test.

## 10. Deliberately out of scope

- Implementing the quick pipeline CLI verbs, runner changes, or lint rules (owned by follow-on Set `quickpipe`).
- Modifying `/plan-review` prompt steps or rubrics (owned by spec `k3yx72`).
- Re-specifying the lifecycle automation policy (owned by spec `llbr2b`).
- Retrofitting existing executed plans. Existing pending plans carry no `- Pipeline:` and therefore
  read as `standard`; nothing is migrated.
- Changing the meaning of `--full-auto` for plans that are not `- Pipeline: quick`, unless the
  maintainer chooses OQ-05 (c).

## 11. Honest limits

- The admission rules measure SIZE and DECLARED REACH, not risk. A two-line change to a file outside
  `quickpipe.excluded_paths` can still be dangerous; the review agent's tier judgement is the only
  risk check, and `k3yx72` MD-1 deliberately adds no runner gate behind it.
- `- Scope-Paths:` is the author's declaration. The finalize scope gate reconciles the files actually
  changed against it, so an undeclared edit is caught at finalize, not at admission.
- Part 1 removes the backlog step only. It does not remove a review or an approval, so its saving is
  the backlog item and its graduation turn (median 3 backlog history records per small plan, Section
  1.1), not a review turn or a human approval.
- Monetary and turn cost per stage could not be attributed from local run ledgers at authoring
  (Section 1.2), so the size of the saving is not measured here.
