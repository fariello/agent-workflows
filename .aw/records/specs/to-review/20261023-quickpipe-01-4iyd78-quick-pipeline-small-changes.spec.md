# Spec: Quick pipeline for small changes

- Date: 2026-10-23
- Status: to-review
- Id: 4iyd78
- Author: aw specs new
- From-Backlog: rsisop
- Work-Kind: feature
- Priority: medium
- Set: quickpipe
- Scope: One shortened pipeline for small changes from plan straight to review and execution. Specification only; authorizes no code change.
- Constrained-by: `.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`
  (`k3yx72`, `approved`), which defines the `simple` review tier and its runner signals, and excludes
  the rest of the pipeline as non-goal N4.
- Constrained-by: `.aw/records/specs/approved/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md`
  (`llbr2b`, `approved`), which owns the configurable per-(type, transition) permission surface.

## Workflow history
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
1. A backlog item is created in `draft/`, moved to `open/`, and picked up by a runner turn.
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

At the execution HEAD, the script yields:
- Total small executed non-orchestrator plans: 151
- Plans carrying `- From-Backlog:`: 21
- Median plan `## Workflow history` records: 4
- Median plan distinct lifecycle statuses: 2
- Median backlog `## Workflow history` records (for plans linked to a backlog item): 3

### 1.2 Per-plan records for small changes carrying a backlog item

The 21 small executed plans carrying `- From-Backlog:` demonstrate the cumulative history records
written across both artifacts for a 1 or 2 item execution:

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
| 438gkf | liybkg | 2 | 5 | 5 | 3 |
| 8bhcd3 | yqpb7q | 2 | 5 | 5 | 3 |
| 78g6ic | q86fxm | 2 | 5 | 5 | 48 |
| ej30u4 | w4eswb | 2 | 5 | 5 | 3 |

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

Measured at the execution HEAD: 92 of 1,117 executed non-orchestrator plans dated 2026-09/10 carried
neither `- From-Backlog:` nor `- From-Spec:` (across all plan statuses in that date range, 100 of 1,178).
This confirms that scaffolding a plan directly without a prior backlog item is already supported by
`ipd_authoring.run_scaffold` when `--priority` and `--work-kind` are supplied.

Furthermore, running `aw ipd scaffold --kind child --title "Test Scaffold" --set quickpipe --order 2 --priority low --work-kind chore --author test` confirms that `ipd_authoring.build_skeleton` unconditionally initializes plans to `draft` (`- Status: draft`).

### 2.2 Inventory of pipeline stages, enforcing symbols, and skipping consequences

| Stage | Enforcing Symbol | Skippable Today? | Loss if Skipped (Ceremony vs Safety Gate) |
|---|---|---|---|
| 1. Backlog item creation | `ipd_authoring.run_scaffold` | Yes | Ceremony. Requires `--priority`/`--work-kind` when `--from-backlog` is absent. Drops initial idea tracking, but creates no safety hazard if the plan defines scope and tests. |
| 2. Initial status assignment | `ipd_authoring.build_skeleton` | No | Ceremony. Always writes `- Status: draft`. Forces an authoring-to-review status transition. |
| 3. Status progression skips | `ipd_lifecycle.validate_transition` | Partial | Safety gate. Forward skips (e.g. `draft -> to-review`) are permitted, but moving to `executed` strictly requires at least `reviewed`. Bypassing this would risk unreviewed execution. |
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

Section 5.2 of `k3yx72` establishes runner signals that raise the tier away from `simple`:
- Modifying a spec file (`.spec.md` in `- Scope-Paths:`).
- Touching sensitive modules in `review.sensitive_paths` (security, leak sanitation, git commit helpers, worktree isolation, sandbox profiles).
- Exceeding size limits (`ipd_schema.MAX_E_LEAVES`, `ipd_schema.MAX_TASK_GROUPS`).
- Grandfathered scope (plans omitting `- Scope-Paths:`).

### 3.2 Stricter mechanical bounds for the quick pipeline

The quick pipeline adopts all disqualifiers from `k3yx72` Section 5.2 and imposes stricter limits
grounded in Section 1's empirical findings:

1. **Orchestrator exclusion** (`- Kind: orchestrator`): Disqualified mechanically. Orchestrators
   coordinate child plans, manage rollup retirement, and never execute small self-contained edits.
2. **Open blocking questions** (`Blocking: yes`): Disqualified mechanically via
   `plan_readiness.has_unresolved_blocking_question`. A plan cannot execute unattended with unresolved
   design questions.
3. **Attended execution required** (`- Attended: required`): Disqualified mechanically via
   `ipd_schema.META_ATTENDED`. Unattended quick execution cannot run interactive turns.
4. **Spec modification** (`.spec.md` in `- Scope-Paths:`): Disqualified mechanically. Changing
   specifications alters system invariants and requires standard or complex review.
5. **Sensitive paths** (`review.sensitive_paths`): Disqualified mechanically. Touching security,
   credentials, leak sanitizer, sandbox, or worktree isolation modules requires full scrutiny.
6. **Grandfathered scope** (missing `- Scope-Paths:`): Disqualified mechanically. Scope must be
   explicitly bounded.
7. **Strict item count**: At most 2 `E-*` items and at most 1 task group. While `k3yx72` permits up to
   18 `E-*` items for standard plans, the quick path strictly requires `<= 2` `E-*` items.
8. **Strict path count**: At most 3 distinct files declared in `- Scope-Paths:`. Prevents wide or
   cross-cutting edits.
9. **Reviewer risk judgement**: Step T review questions in `/plan-review`. If the review agent answers
   "yes" to any question regarding interface breakage, data loss risk, or subtle regressions, the tier
   is raised.

| Criterion | Type | Source / Enforcement |
|---|---|---|
| Kind is child | Mechanical | Plan front matter (`- Kind: child`) |
| No open blocking questions | Mechanical | `plan_readiness.has_unresolved_blocking_question` |
| Attended not required | Mechanical | `ipd_schema.META_ATTENDED` != "required" |
| No spec files modified | Mechanical | `- Scope-Paths:` contains no `.spec.md` |
| No sensitive paths touched | Mechanical | `- Scope-Paths:` matches no `review.sensitive_paths` |
| Explicit scope paths | Mechanical | `- Scope-Paths:` is non-empty |
| Small execution size | Mechanical | Count of `E-*` items <= 2, Task Groups <= 1 |
| Small path footprint | Mechanical | Count of declared paths in `- Scope-Paths:` <= 3 |
| Review risk assessment | Judgement | Review agent Step T questions (spec `k3yx72` 5.2) |

## 4. Deciding role and disagreement fallback

### 4.1 Consistency with `k3yx72` MD-1

Spec `k3yx72` MD-1 dictates:
> "The review agent rates the tier; the runner only raises it."

The quick pipeline respects this invariant. An author cannot unilaterally force quick execution,
and the runner never lowers a tier assigned by review.

### 4.2 Deciding options considered

1. **Option A (Author proposal with Review confirmation)**: The author indicates quick pipeline intent
   via front matter (`- Pipeline: quick`). The review agent evaluates Check T. If Check T confirms
   `simple` tier and all runner mechanical signals pass, the quick pipeline proceeds.
2. **Option B (Implicit tier derivation)**: No front-matter field. The quick path is entered purely if
   the review agent assigns `simple` and runner signals pass.
3. **Option C (CLI creation flag only)**: A human flag on creation dictates the pipeline.

**Recommendation**: Option A (Recommendation strength: Strong).
Recording authorial intent in front matter allows authoring tools (`aw ipd quick`) to validate size
bounds upfront, makes the expectation obvious to reviewers, and prevents unexpected fast-tracking
of plans not written for the quick pipeline.

The proposed field is `- Pipeline:` with the closed value set `{"standard", "quick"}` (defaulting to
`standard` when absent). The implementing Set must register `Pipeline` in `ipd_schema.META_RECOGNIZED`.

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
`status_set.validate_transition_allowed` for specs only; for plans, human approval is enforced by
convention and the setter gate `plan_readiness.approval_refusals`. The implementing Set should add
an explicit check in `status_set.validate_transition_allowed` requiring `--by-human` when transitioning
a plan to `approved`, firmly distinguishing human `approved` from runner `auto-approved`.

### 5.2 Composition with lifecycle automation policy (spec `llbr2b`)

Spec `llbr2b` establishes a unified permission matrix for automated transitions. The quick pipeline
does not create a parallel or conflicting switch.
- Under `llbr2b`, the transition `("plans", "->auto-approved")` is governed by policy.
- When `llbr2b` policy permits `("plans", "->auto-approved")` (or runner `--full-auto` is active),
  and a plan qualifies for the quick pipeline with an approving review readiness, the runner sets
  `auto-approved`.
- If `llbr2b` policy denies the transition or `--full-auto` is disabled, the plan stops at `reviewed`,
  requiring explicit human approval (`aw ipd set approved <id6> --by-human`).

### 5.3 Host session and turn separation

Authoring, review, and execution MUST NOT share a single host session or agent turn.
- **Attestation independence**: A review agent must examine the plan in a fresh context, free from
  authoring biases, to independently evaluate risk and produce an authentic `- Readiness:` record.
- **Executor isolation**: Execution must take place in an isolated worktree lane (`isolate_worktree`)
  with a clean git status, baseline checks, and merge-and-revalidate gating.
- **Contiguous execution**: While turns are distinct and isolated, the runner may execute authoring,
  review, and execution sequentially in a single unattended batch run when auto-approval is permitted.

## 6. Tracked records and release gate preservation

### 6.1 Records lifecycle table

| Record | Disposition | Justification |
|---|---|---|
| Backlog item and history | Dropped | Dropped to eliminate draft/open/graduate friction for small changes. |
| Plan file (`.ipd.md`) | Kept | Primary unit of work and historical truth. |
| Plan `## Workflow history` | Kept | Retains audit trail of status progression (`draft -> to-review -> reviewed -> auto-approved -> executed`). |
| `E-*` and `V-*` evidence | Kept | Pasted execution and validation evidence is a mandatory repository invariant. |
| Review record (`.review.md`) | Kept | Written by `/plan-review` under `.aw/records/reviews/` to document tier answers and checks. |
| `- Readiness:` field | Kept | Attested by review; required by `ipd_lint.check_readiness_required` (`IPD-M113`). |
| `aw ipd begin` receipt | Kept | Written by runner to prevent concurrent execution conflicts. |
| Finalize commit | Kept | Atomic commit moving plan to `executed/` under integration gate. |
| Walkthrough document | Dropped | 1 to 4 line fixes do not warrant separate walkthroughs; the git diff and execution report suffice. |

### 6.2 Preserving the release gate for bug fixes

In the standard pipeline, bug tracking and release gating operate through backlog items:
`check_engine.check_live_bug_gate` scans live backlog items and fails if any bug item lacks
`- Blocks-Release:`.
Currently, `aw ipd scaffold --work-kind bug` without `--from-backlog` writes no `- Blocks-Release:`
bullet. If a bug plan were scaffolded directly without a backlog item, it would escape release gating.

The quick pipeline closes this loophole with two mandatory mechanisms:
1. **Scaffold-time gate assignment**: The quick creation command (`aw ipd quick`) evaluates
   `backlog.decide_gate_default(repo_root, work_kind="bug", priority=priority)` and writes
   `- Blocks-Release: next` directly into the plan's front matter whenever `work-kind` is `bug`.
2. **Plan-side release gate check**: The implementing Set must update `check_engine.py` (adding
   `check_live_plan_bug_gate` or extending `check_live_bug_gate`) to verify that any active plan in
   `pending/` with `- Work-Kind: bug` carries a valid `- Blocks-Release:` field.

### 6.3 Cross-tree visibility in `aw attention` and the runner queue

- `aw attention`: The cross-tree attention view scans `.aw/records/plans/` directly. A quick plan is
  tracked from inception (`draft` -> `active`, `to-review` -> `ready`, `auto-approved` -> `ready`).
  It requires no backlog entry to be visible.
- Runner Queue: `run_selection_policy.py` constructs the execution DAG from plan dependencies. A quick
  plan with no prerequisites enters the queue as an Order-1 leaf, runnable immediately.

## 7. Entry point, work breakdown, and open questions

### 7.1 User-facing entry point

The primary user entry point is `aw ipd quick`:
```sh
aw ipd quick --title "Fix typo in CLI help" --slug fix-cli-help --work-kind bug --priority low --author opencode --scope "agent_workflows/cli.py" --apply
```
This command:
- Calls `ipd_authoring.run_scaffold` with `--quick`.
- Writes `- Pipeline: quick` into front matter.
- Sets `- Work-Kind:` and `- Priority:`.
- Automatically assigns `- Blocks-Release: next` if `work-kind` is `bug`.
- Validates that declared scope paths do not touch `review.sensitive_paths` or `.spec.md`.

Code surfaces extended by the implementing Set:
- `agent_workflows/cli.py`: Register `quick` subparser in `ipd_sub`.
- `agent_workflows/command_surface.py`: Add `aw ipd quick` to `COMMAND_INVENTORY`.
- `agent_workflows/ipd_authoring.py`: Implement `run_quick` / extend `run_scaffold`.
- `agent_workflows/ipd_schema.py`: Register `Pipeline` in `META_RECOGNIZED`.
- `agent_workflows/check_engine.py`: Add plan-side bug release gate.
- `agent_workflows/runner_shared.py`: Wire `simple` tier review auto-approval to contiguous execution.

### 7.2 Implementing work breakdown (Set `quickpipe`)

| Order | Work | Depends on | Documentation to Amend |
|---|---|---|---|
| 00 | Orchestrator: Child tracking and rollup. | All children | None |
| 01 | Plan schema and authoring entry point: Register `Pipeline` in `ipd_schema.META_RECOGNIZED`, implement `aw ipd quick`, and apply `backlog.decide_gate_default`. | Spec approval | `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`, `.aw/records/plans/README.md` |
| 02 | Release gate integrity: Implement plan-side bug gate in `check_engine.py` ensuring active bug plans require `- Blocks-Release:`. | Order 01 | `docs/artifact-lifecycles.md` |
| 03 | Runner integration: Connect `k3yx72` Order 02 `Review-Depth` signals to `auto-approved` transition under `llbr2b` policy; support contiguous turn dispatch. | Order 01, `k3yx72` Order 02, `llbr2b` | `docs/artifact-lifecycles.md` |
| 04 | Verification and regression tests: CLI tests, qualification rejection tests, and runner simulation. | Orders 02, 03 | None |

### 7.3 Open questions for the maintainer

#### OQ-01: Entry point syntax: dedicated verb vs scaffold flag

- Blocking: no
- Status: open
- Owner: maintainer
- Question: Should the quick pipeline entry point be a dedicated CLI verb (`aw ipd quick`) or a flag on the existing scaffold command (`aw ipd scaffold --quick`)?
- Recommendation: Dedicated verb `aw ipd quick`, aliasing `aw ipd scaffold --quick`.
- Recommendation strength: Strong. A distinct verb emphasizes the streamlined workflow while preserving discoverability.

#### OQ-02: Front-matter marker: explicit field vs implicit derivation

- Blocking: no
- Status: open
- Owner: maintainer
- Question: Should plans declare `- Pipeline: quick` in front matter, or should the runner infer quick handling solely from `simple` review tier and runner signals?
- Recommendation: Explicit `- Pipeline: quick` field.
- Recommendation strength: Moderate. Explicit declaration makes author intent unambiguous and allows upfront linting.

#### OQ-03: Plan approval mechanical enforcement

- Blocking: no
- Status: open
- Owner: maintainer
- Question: Should `aw ipd set approved` enforce `--by-human` mechanically in `status_set.validate_transition_allowed` (mirroring specs), rather than relying on convention?
- Recommendation: Add mechanical `--by-human` requirement to `status_set.validate_transition_allowed` for plans entering `approved`.
- Recommendation strength: Strong. Prevents inadvertent automated sets of `approved`, preserving `auto-approved` as the sole automated status.

#### OQ-04: Contiguous runner dispatch

- Blocking: no
- Status: open
- Owner: maintainer
- Question: Should the runner execute review and execution in separate turns within the same unattended batch run, or require separate runner invocations?
- Recommendation: Contiguous execution across distinct turns in the same batch run when `auto-approved` succeeds.
- Recommendation strength: Strong. Minimizes human turnaround while strictly preserving turn-level isolation.

## 8. Requirements index (canonical declaration site)

This table is the single canonical declaration of this spec's requirements; the cited sections
elaborate them.

| ID | Requirement | Detail |
|---|---|---|
| R-01 | The quick pipeline authorizes no code change until an approved implementing plan executes. | 0, 7.2 |
| R-02 | Quick plans are created directly without requiring a backlog item or backlog graduation turn. | 1.1, 2.2, 6.1 |
| R-03 | A plan must satisfy all mechanical disqualifiers (no orchestrators, no open blocking questions, no attended requirement, no spec edits, no sensitive paths, bounded size <= 2 E items and <= 3 paths) to qualify. | 3.2 |
| R-04 | Review agent Step T questions govern review tier assignment; the runner may raise the tier but never lowers it. | 3.2, 4.1 |
| R-05 | A plan failing any qualification criterion or rated above `simple` falls back cleanly to the standard pipeline. | 4.3 |
| R-06 | Author intent is recorded via `- Pipeline: quick` in front matter, registered in `ipd_schema.META_RECOGNIZED`. | 4.2, 7.1 |
| R-07 | Human approval `->approved` remains an attested human act; automated clearance sets `auto-approved` exclusively. | 5.1 |
| R-08 | Automated clearance to `auto-approved` requires an approving review readiness verdict (`is_plan_review_approved`) and compliance with `llbr2b` policy. | 5.1, 5.2 |
| R-09 | Authoring, review, and execution operate in separate turns and isolated worktree sessions. | 5.3 |
| R-10 | Plan files, history records, and E/V evidence are preserved; walkthroughs are dropped for quick changes. | 6.1 |
| R-11 | Bug fixes created via the quick pipeline automatically inherit release gating (`- Blocks-Release: next`) and are policed by plan-side release checks. | 6.2 |
| R-12 | The CLI provides `aw ipd quick` as the primary authoring entry point. | 7.1 |

## 9. Acceptance criteria for the implementing Set

| ID | Covers | Criterion | Evidence |
|---|---|---|---|
| AC-01 | R-02, R-06, R-12 | `aw ipd quick` scaffolds an IPD with `- Pipeline: quick`, valid `- Status: draft`, and no backlog dependency. | CLI execution output and generated plan file. |
| AC-02 | R-03, R-06 | Scaffolding or linting a quick plan exceeding 2 `E-*` items, exceeding 3 paths, or touching sensitive paths fails validation. | Lint refusal diagnostics and test assertions. |
| AC-03 | R-04, R-05 | A quick plan rated `standard` by `/plan-review` rejoins the standard pipeline without error or record loss. | Runner execution ledger and plan workflow history. |
| AC-04 | R-07, R-08 | Runner advances a passing `simple` plan to `auto-approved` under `--full-auto`, while rejecting unreviewed auto-approval. | Transition event logs and status checks. |
| AC-05 | R-07 | Transitioning a plan to `approved` without `--by-human` is refused by `aw ipd set`. | Command error output and exit code. |
| AC-06 | R-09 | Authoring, review, and execution run in separate isolated turns within the runner. | Run trace demonstrating distinct turn sessions. |
| AC-07 | R-10 | Executed quick plans retain full `E-*`/`V-*` evidence and workflow history in `executed/` without a walkthrough file. | File presence check in `.aw/records/plans/executed/`. |
| AC-08 | R-11 | An active quick bug plan lacking `- Blocks-Release:` is flagged by `check_engine` release checks. | `aw check` diagnostic output. |

## 10. Deliberately out of scope

- Implementing the quick pipeline CLI verbs, runner changes, or lint rules (owned by follow-on Set `quickpipe`).
- Modifying `/plan-review` prompt steps or rubrics (owned by spec `k3yx72`).
- Re-specifying the lifecycle automation policy (owned by spec `llbr2b`).
- Retrofitting existing executed plans.
