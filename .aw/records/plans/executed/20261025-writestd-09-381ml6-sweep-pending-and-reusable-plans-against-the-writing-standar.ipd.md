# IPD: Sweep pending and reusable plans against the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-08 to R-11 require a one-time proofread of every live plan in `.aw/records/plans/pending/` and `reusable/` against the writing standard, with diagrams where requirement 12 applies (`ecmw83` R-04). Approved plans keep their approval (`ecmw83` MD-4). For a plan in `reviewed`, `approved`, or `auto-approved`, the sweep must not change the inputs of `ipd_lifecycle.frozen_region_digest` (`- Scope-Paths:` and every E-item and V-item action block), because `plan_readiness.review_staleness_index` then reports `substantive-edit` (`ecmw83` R-09). Plans that a live run is executing or has queued are skipped (`ecmw83` R-10). Measured at review (2026-11-07, HEAD `417785106`, context only; E-01 re-derives the set): 23 live plans besides this one, all `reviewed` with `- Readiness: go-pending-approval`, two of them orchestrators (`8fvkmp`, `63ib9r`), about 786 KB; `reusable/` holds only its README.
- Scope: Proofread every live plan in `pending/` and `reusable/` that is not skipped at execution time; add or correct diagrams per requirement 12; append one sweep line to the `## Workflow history` of every swept plan; write the sweep walkthrough; file one backlog carrier for any skipped plan, any defect left inside a protected region, or any `Unresolved` annotation. EXCLUDES this plan's own file; plans in terminal directories (`ecmw83` N3); any change to a plan's title line or metadata fields (every `- Key:` line before the first `## ` heading, which includes `Status`, `Readiness`, `Review-Depth`, `Approval`, `Coverage*`, `Blocks-Release`, `Id`, `From-*`, `Item-Dependencies`, and `Scope-Paths`); any change to an E/V id, a checkbox, a `Depends on`, `Execution state`, `Result`, or `Observed evidence` value, or an open-question or deferral field; for a plan in `reviewed`, `approved`, or `auto-approved`, any change to an E-item or V-item action block or any of its indented sub-fields; for an orchestrator, any change to the text its coverage fingerprint covers; and any change to a heading, a stable ID, an inline code span, a number, a non-diagram fenced block, a `## Workflow history` record, or text that another tracked file quotes.
- Scope-Paths: .aw/records/plans/pending/, .aw/records/plans/reusable/, .aw/records/walkthroughs/, .aw/records/backlog/open/
- Item-Dependencies: executed:g4719s, executed:gzhw9c, executed:k2x0yl, executed:e4n4p3, executed:sfez3e, executed:uog8nc
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: standard
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 9
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 381ml6

## Workflow history
- 2026-11-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 381ml6 verified (set writestd, attempt 1). [Scope reconciliation - in-scope-unmodified .aw/records/plans/reusable/: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): maintainer 2026-11-09 excluded Set metastore from this sweep ("Run all 3 except metastore"); added as a Deferred entry carried by 63ib9r.
- 2026-11-07 approved (aw set): status set to approved
- 2026-11-07 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-012 FIXED
- 2026-11-07 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-012 FIXED; review record .aw/records/reviews/20261025-writestd-09-381ml6-sweep-pending-and-reusable-plans-against-the-writing-standar.review.md
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Bring every live plan up to the writing standard once, without changing what any plan requires, without staling any review, approval, or coverage record, and without disturbing any run, and prove mechanically that no protected element changed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Definitions used by every item below:

- BASE is the commit that E-01 records. Every comparison in this plan is against BASE.
- A frozen plan is a live plan whose `- Status:` at BASE is `reviewed`, `approved`, or `auto-approved`.
- The guard is the first script in `## Required tests / validation`. Save it once as `.aw/state/381ml6/sweep_guard.py` (gitignored, inside the workspace) and run it from the repository root. With no plan arguments it checks every plan that was live at BASE, except this plan; with plan paths it checks only those. A plan that a run moved to a terminal directory after BASE is reported as `MOVED` and not checked.
- A plan unit is the work for ONE plan, done in this order: (1) run `aw runners --once --json` and apply the skip rule below; (2) proofread the plan per the "Proofreading procedure" section of `.aw/system/workflows/technical-writing/technical-writing.md` and its numbered requirements, editing only the editable text defined below; (3) apply requirement 12: add a Mermaid diagram (for a Set, the child dependency flow is the common case) only where its criteria apply and no diagram covers that content, and correct an existing diagram that disagrees with the text; (4) where a passage's meaning cannot be established, keep the original text and add an adjacent block-quote line `> **Unresolved (PW-NN):** <the ambiguity>. Decision needed: <what must be decided>.`, numbering `PW-01` upward across the whole sweep (`ecmw83` R-11); (5) insert the sweep line directly under the `## Workflow history` heading (newest first); (6) run the guard on that plan and fix every reported problem by restoring the original text; (7) commit the plan alone with `aw commit 381ml6 -m "sweep(writestd): proofread plan <id6> (381ml6)" -- <plan path>`.
- Skip rule (`ecmw83` R-10, MD-4): skip the plan when any runner reported by `aw runners --once --json`, other than the run executing this plan, has the plan's id6 as its `id6`, or has `setid` equal to the plan's `- Set:` value (the monitor does not list a run's queue, so a running Set is treated as wholly queued). Record the skip, the runner's `run_id`, and the reason. A plan in Set `writestd` is never skipped for the run executing this plan.
- Editable text: in every live plan, prose outside the protected elements below, including the `## Goal`, `## Findings`, `## Project conventions discovered (Step 0)`, `## Proposed changes (ordered, validatable)`, `## Deferred / out of scope (with reason)` and `## Scope check` prose, the `## Required tests / validation` and `## Spec / documentation sync` prose, the `## Open questions` prose that is not a `- Key:` field, the `## Child IPDs, sequence, and dependencies` prose, and the gate prose. In a plan that is not frozen, an E-item or V-item action block, `- Expected outcome:`, and `- Required evidence:` text are editable too.
- Do not change, in any plan unit: the title line and the metadata fields (every `- Key:` line before the first `## ` heading, with its indented continuation lines); any E or V id or checkbox; any `Depends on`, `Execution state`, `Result`, or `Observed evidence` value; any open-question or deferral field (`Blocking`, `Status`, `Owner`, `Finding`, `Carrier`, `Carrier-Declined`, `Gate-Kind`, `Gate-Ref`, `Resolution or deferral rationale`), or a `Size assessment` or `Cohesion rationale` line; in a frozen plan, any E-item or V-item action block or any of its indented sub-fields (`Expected outcome`, `Required evidence`, and the rest), which the review approved even though `frozen_region_digest` reads only the action blocks; in an orchestrator, any text that `runner_shared.probe_cache_digest` covers (each E-item action block, the child table cells, and the unattached prose of the sections in `runner_shared.PROBE_PROSE_SECTIONS`, which include `## Goal` and `## Scope check`), because a changed fingerprint makes `aw ipd lint --phase review-finalize` report `IPD-S408` until `aw ipd coverage` re-runs a model probe; any heading text; any stable ID such as `R-08`, `AC-06`, `OQ-01`, a decision number such as `D140`, or an id6 such as `25kzda`; any inline code span; any number; any fenced block that is not a Mermaid diagram; any `## Workflow history` record; any text that another tracked file quotes; any `must`, `should`, `may`, `shall`, or `never`, with or without a following `not`. The guard enforces each of these. Where the guard blocks a fix you judge necessary, keep the original and list the case in the walkthrough.
- Sweep line: `- <date> proofread (<agent/model>): per the technical writing standard (spec ecmw83 R-08); meaning unchanged; frozen region untouched`, dropping `; frozen region untouched` for a plan that is not frozen, and appending `; N Unresolved annotations` when step 4 added any. Use the label `proofread` exactly. Do not use `/plan-review`, `reviewed`, or `review` as the label, and do not begin the message with a verdict word, because `plan_readiness.is_review_history_entry` would then read the line as a review record. Placing it newest first is safe for a plan that carries `- Readiness:`, because `plan_readiness.is_plan_review_approved` honors the field when any history record is a review record (`plan_readiness.history_has_review_record`). For a frozen plan with no `- Readiness:` field, the approval fallback reads only the newest record (`plan_readiness.extract_newest_history_entry`), so a sweep line on top would withdraw its review clearance; the guard reports this as `review-approval predicate changed`. Skip such a plan with the reason "no Readiness field" instead of noting it.
- Dashes: the `AGENTS.md` execution contract exempts plans from the dash rule, and the shipped standard adds no dash rule of its own (maintainer ruling, `g4719s` OQ-02). Spec `ecmw83` AC-06 still requires that no swept plan carries an `IPD-C802` advisory outside quotations and recorded evidence. So reword a prose em or en dash that `aw ipd lint` reports as `IPD-C802`, unless the guard protects the text; do not search for dashes otherwise. Measured at review: 14 live plans each hold the two dashes of the scaffold's runtime-demonstration reachability rule sentence, which `ipd_authoring._VALID_INTRO` writes; plan `yz4jdm` edits that module and does not remove them, so new scaffolds keep producing them.

### Task group 1: baseline

- [x] E-01 Confirm the record format first: `.aw/config/project.json` carries no `metadata_schema` key of 2 or more, and every live plan has a `- Status:` line and a `## Workflow history` heading. If either fails, the metadata cutover (plan `cxxmyv`, spec `4sd62s` Section 5.2) has landed, the guard reads a format that no longer exists, and the executor stops and reports that this plan needs revision. Then record the baseline: `git rev-parse HEAD` as BASE; the `aw check all --agent --verbose` list of `error` diagnostics and of `check.ipd-review-may-be-stale` diagnostics (rule and location, sorted); `aw ipd lint --agent` with no path (every pending plan); `aw ipd lint --phase review-finalize --agent` on each live orchestrator; `aw runners --once --json`; the digest table printed by the second script in `## Required tests / validation`, saved as `.aw/state/381ml6/digests-base.tsv`; and one full guard run at BASE, which must report `problems=0`. Save each output under `.aw/state/381ml6/`.
  - Depends on: none
  - Expected outcome: the format check passes; BASE and the outputs are saved; the live set and its statuses are re-derived at execution time rather than taken from this plan; the guard reports zero problems at BASE.
  - Execution state: performed

### Task group 2: sweep

- [x] E-02 (spec `ecmw83` R-08, `ecmw83` R-04, `ecmw83` R-09, `ecmw83` R-10, `ecmw83` R-11) Do one plan unit for each live plan from E-01 except this plan, in path order. If a turn ends before this item finishes, the committed plan units stand; resume at the first live plan with neither a sweep line nor a recorded skip.
  - Depends on: E-01
  - Expected outcome: each live plan is either skipped with a recorded runner and reason, or has its own `aw commit` holding only that plan, exactly one new sweep line, and a guard line with `problems=0`.
  - Execution state: performed

- [x] E-03 (spec `ecmw83` R-08) Run the full guard with `--final`: `python3 .aw/state/381ml6/sweep_guard.py <BASE> --final --skipped=<comma-separated skipped id6s>`. It checks every plan live at BASE for all protected elements, for unchanged `frozen_region_digest`, coverage fingerprint, and review-approval predicate, and for exactly one new sweep line per swept plan and none per skipped plan.
  - Depends on: E-02
  - Expected outcome: the guard exits 0 with `problems=0`.
  - Execution state: performed

- [x] E-04 (spec `ecmw83` R-09, `ecmw83` AC-07) Re-run the digest script to `.aw/state/381ml6/digests-final.tsv` and join it with `digests-base.tsv` on the plan name, adding a match column for each digest. Every frozen plan must match on `frozen_region_digest` and every orchestrator on the coverage fingerprint. Any mismatch: restore that plan's edits inside the protected region, commit the restoration, and repeat E-03 and this item.
  - Depends on: E-03
  - Expected outcome: every row present in both tables reads `match` for both digests; a row only in the base table is a plan that a run moved to a terminal directory and is listed as such.
  - Execution state: performed

- [x] E-05 (spec `ecmw83` AC-06, `ecmw83` AC-07) Run `aw ipd lint --agent` with no path and `aw ipd lint --phase review-finalize --agent` on each live orchestrator, and compare them with E-01. Run `aw check all --agent --verbose` and compare its `check.ipd-review-may-be-stale` list with E-01.
  - Depends on: E-04
  - Expected outcome: no plan's disposition changed; no `check.ipd-review-may-be-stale` diagnostic exists that was absent at BASE; no `IPD-S408` diagnostic exists that was absent at BASE; no `IPD-C802` advisory remains in a swept plan outside quotations and recorded evidence.
  - Execution state: performed

### Task group 3: report

- [x] E-06 (spec `ecmw83` AC-08) Write the walkthrough with `set_records.write_walkthrough(Path("."), set_id="writestd", order=9, target_id6="381ml6", slug="plan-sweep", body=...)`, which mints the walkthrough's own id6 and records `- Target-Id: 381ml6` (`DECISIONS.md` D140). The body holds: a table of the plans swept (id6, status, frozen or not, lines changed, diagrams added or corrected, `Unresolved` count); every skipped plan with its runner and reason; every defect left inside a protected region, with its plan and location; every `Unresolved` annotation with its plan, section heading, and `PW-NN`; and the E-01, E-03, E-04, and E-05 outputs. If any plan was skipped, any defect was left, or any `Unresolved` annotation was added, file one backlog carrier listing them: `aw backlog new --summary "Finish the writestd plan sweep: skipped plans, protected-region defects, Unresolved annotations" --set writestd --priority medium --work-kind followup --body "<list>" --apply`, and add its id6 to the walkthrough. Otherwise write "Nothing skipped, left, or unresolved; no carrier filed." in the walkthrough. Commit the walkthrough and any carrier with `aw commit 381ml6 -m "sweep(writestd): plan sweep walkthrough (381ml6)" -- <walkthrough path> [<item path>]`.
  - Depends on: E-05
  - Expected outcome: one walkthrough named `YYYYMMDD-writestd-09-<own id6>-plan-sweep.walkthrough.md` exists and is committed; `aw check all` reports no `check.id6-identity-slot` finding for it; a tracked open backlog item lists every skip, left defect, and `Unresolved` annotation, or the walkthrough states that there are none.
  - Execution state: performed

- [x] E-07 (spec `ecmw83` AC-06) Run `aw check all --agent --verbose` and compare its `error` list with the E-01 baseline; run the routine gate `python3 -m pytest`; run `aw sanitize --agent`; commit any walkthrough update with `aw commit 381ml6 -- <walkthrough path>`.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: no `error` diagnostic exists that was absent at BASE; the routine gate passes; the sanitizer reports no finding in any file this plan changed; no path outside the swept plans, the walkthrough, and the carrier item was committed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Read `.aw/system/workflows/technical-writing/technical-writing.md` in full before E-02 and apply its "Proofreading procedure" section (added by Order 01 `g4719s` E-03) and requirement 12 (`g4719s` E-02).
- A writing correction does not authorize a change to scope, obligations, approval, status, or recorded evidence (standard section "How it combines with other rules"; spec `ecmw83` R-08).
- Plan status is owned by `aw ipd set`; never hand-edit a status line. A plan has no `note` verb, so the sweep line is a hand-written `## Workflow history` record, which `ecmw83` R-08 permits ("a plan `## Workflow history` line").
- `ipd_lifecycle.frozen_region_digest` covers `Scope-Paths` and each E/V action block via `ipd_lint.leaf_action_blocks`, which stops before indented sub-fields; prose sections and `- Expected outcome:`/`- Required evidence:` text are outside it (measured at review: editing either left the digest unchanged).
- `plan_readiness.review_staleness_index` compares the working tree with the newest `plan-review:` commit of each frozen plan and reports `substantive-edit` when the digest differs or `answered-blocking-question` when a blocking question was resolved; `aw ipd lint` (rule `check.ipd-review-may-be-stale`, `ipd_lint._review_stale_advisory`) and `aw check all` surface it as an `info` advisory.
- `runner_shared.probe_cache_digest` is the orchestrator coverage fingerprint that `coverage_record.is_current` compares with `- Coverage-Fingerprint:`.
- Walkthroughs dated after the `walkthrough_id6` cutover (2026-09-27, `.aw/config/project.json`) use the clustered name with their own id6 and `- Target-Id:` (`.aw/records/walkthroughs/README.md`, D140). A walkthrough is not tracked by `aw attention`, so an open obligation must also live in a tracked carrier (E-06).
- Commit only through `aw commit`; one plan per commit, so a reviewer can read each diff alone and a resumed turn keeps finished units.

## Findings

- This plan runs after the spec and backlog sweeps (`sfez3e`, `uog8nc`), so a plan's citations of spec sections are checked against the proofread specs. Its unit, guard, carrier, and walkthrough design follows those two plans; the `Unresolved` prefix is `PW-` here (`SW-` and `BW-` there), so the three carriers do not collide.
- Measured at review in a scratch worktree of HEAD `417785106`: editing `## Goal` or `## Findings` text of a frozen child left `frozen_region_digest` unchanged and produced no staleness advisory; editing an E-item action line produced `check.ipd-review-may-be-stale` ("review may be stale: substantive-edit") from `aw ipd lint --agent`; editing an E-item's `- Expected outcome:` left the digest unchanged, so V-04 alone cannot show that a reviewed contract is unchanged, which is why the guard protects every indented sub-field of a frozen plan.
- Measured at review: appending one word to the `## Goal` of orchestrator `8fvkmp` left its frozen digest unchanged but turned `aw ipd lint --phase review-finalize` from conforming to `error` with `IPD-S408` ("coverage-record-stale (8fvkmp): plan changed since the check on 2026-11-02 (fingerprint mismatch)"), because `runner_shared.PROBE_PROSE_SECTIONS` includes `Goal` and `Scope check`. Re-running `aw ipd coverage` needs a model probe and writes `- Coverage-*` metadata, which this plan may not do, so the guard refuses any change to that text.
- Measured at review: for a frozen plan with no `- Readiness:` field, `plan_readiness.is_plan_review_approved` returned True with the `/plan-review` record on top and False after a `proofread` line was inserted above it. Every live plan carried `- Readiness:` at review, so this case is guarded and skipped rather than expected.
- Measured at review: the 14 live plans holding em dashes hold them only in the scaffolded runtime-demonstration reachability sentence. That sentence is quoted in many executed plans; the guard treats a dash reworded to a comma as the same quoted passage, so rewording it in a child passes, while rewording it in orchestrator `63ib9r` is refused because its `## Validation and cross-check (verify before reporting the Set complete)` prose is covered by the coverage fingerprint.
- `aw runners --once --json` reports, per live runner, `run_id`, `setid`, `id6`, `action`, and `status`, and does not list the run's queue (`runners_monitor.extract_journey_info` reads `state.json` only to count it). The skip rule therefore treats every plan in a running Set as queued.
- An isolated lane executing another plan would edit that plan's own file; a sweep edit of the same file would conflict in the merge-and-revalidate gate, which is why `ecmw83` R-10 skips it. Spec `ecmw83` Section 7 records that Set `revsteps` was executing when the spec was written.
- Pending plan `cxxmyv` (Set `metastore`) runs migration `m0001`, which deletes every record's bullet block and `## Workflow history` section (spec `4sd62s` Section 5.2 "Delete the legacy bullet block"). After it lands, the guard's metadata and history checks read nothing, so E-01 checks the format before any plan unit starts.

## Proposed changes (ordered, validatable)

1. Baseline, digest table, and guard at BASE (E-01).
2. Sweep each plan as one committed unit with the live-run skip (E-02).
3. Prove every protected element, digest, and readiness unchanged (E-03, E-04, E-05).
4. Report, carry anything skipped or left, check, and commit (E-06, E-07).

## Deferred / out of scope (with reason)

- Every plan of Set `metastore` (`.aw/records/plans/pending/*-metastore-*.ipd.md`): EXCLUDED from this sweep by the maintainer (2026-11-09, "Run all 3 except metastore"), because those plans are being re-split and re-reviewed; a sweep edit now would be overwritten or would conflict. Record each with a skip line naming this reason, exactly as for a plan held by a live run (`ecmw83` R-10), and proofread them in their own review.
  - Carrier: 63ib9r
- Plans skipped because a live run held them, and defects left inside a protected region: proofread when they are next revised; E-06 files a backlog carrier listing them.
  - Carrier: 381ml6
- Terminal plans: out of scope by spec `ecmw83` N3.
  - Carrier-Declined: deliberate non-goal of the spec.
- The em dashes that `ipd_authoring._VALID_INTRO` writes into every new scaffold: changing the generator is outside this plan's scope (plan `yz4jdm` owns that module) and outside the spec; this plan only rewords the copies `IPD-C802` reports where the guard permits.
  - Carrier: 8fvkmp

## Scope check

- Over-scope: none.
- Under-scope: none after review. The review added the guard (meaning-preservation proof), the coverage-fingerprint and approval-predicate protections, a sweep line for every swept plan rather than only changed ones (`ecmw83` R-08), the backlog carrier, the sanitizer run, and the D140 walkthrough name.

## Required tests / validation

`aw ipd lint`, `aw check all` against the E-01 baseline, the guard and the digest table below, the routine gate `python3 -m pytest`, and `aw sanitize --agent`.

The guard (save verbatim as `.aw/state/381ml6/sweep_guard.py`; usage `python3 .aw/state/381ml6/sweep_guard.py <BASE> [--final] [--skipped=<id6>,...] [plan path ...]`; exit 0 means no problem). It reports, per plan, the protected elements that changed between BASE and the working tree. Measured at review in a scratch worktree of HEAD `417785106`: a full run takes about 25 seconds and reports `TOTAL live=23 checked=23 problems=0`. Each of these reported a problem with exit 1: an E-item action edit (`frozen_region_digest changed`), an `- Expected outcome:` edit, a `- Required evidence:` edit, an open question's `Blocking: yes` changed to `no`, a deferral `Carrier:` change, a `- Readiness:` change, `MUST` changed to `MUST NOT` in gate prose, one word added to the `## Goal` of orchestrator `8fvkmp` (`probe_cache_digest (orchestrator coverage) changed`), the dash reworded in orchestrator `63ib9r`, and a sweep line on a frozen plan with no `- Readiness:` (`review-approval predicate changed`). A reworded `## Goal` sentence in a frozen child, the reachability-sentence dash reworded in child `7ehv8l`, and a sweep line with `--final` on a plan carrying `- Readiness:` each reported `problems=0` and exit 0.

```python
"""Sweep guard for plan 381ml6: compares every live plan at BASE with the working tree."""
import collections, pathlib, re, subprocess, sys

sys.path.insert(0, ".")
from agent_workflows.ipd_lifecycle import frozen_region_digest
from agent_workflows.runner_shared import probe_cache_digest
from agent_workflows.plan_readiness import is_plan_review_approved
import tempfile

base, final = sys.argv[1], "--final" in sys.argv
skipped = {s for a in sys.argv[2:] if a.startswith("--skipped=") for s in a[10:].split(",") if s}
only = {a.split("/")[-1] for a in sys.argv[2:] if not a.startswith("--")}
NOTE = "per the technical writing standard (spec ecmw83 R-08)"
TERMINAL = ("executed", "superseded", "not-executed")
def git(*a, inp=None):
    return subprocess.run(["git", *a], input=inp, capture_output=True).stdout
names = git("ls-tree", "-r", "--name-only", base).decode().split()
live = [p for p in names if p.startswith((".aw/records/plans/pending/", ".aw/records/plans/reusable/"))
        and p.endswith(".md") and not p.endswith("/README.md") and "-381ml6-" not in p]
texts = [p for p in names if p.endswith((".md", ".py", ".json", ".toml", ".yml", ".yaml", ".txt"))]
raw, old, i = git("cat-file", "--batch", inp="".join(f"{base}:{p}\n" for p in texts).encode()), {}, 0
for p in texts:
    nl = raw.index(b"\n", i); head = raw[i:nl].split()
    if head[-1] == b"missing": i = nl + 1; continue
    n = int(head[2]); old[p] = raw[nl + 1:nl + 1 + n].decode("utf-8", "replace"); i = nl + 2 + n
quote = re.compile(r'"([^"\n]{20,400})"')
def norm(s):  # a dash reworded to a comma or a space still counts as the same quoted passage
    return " ".join(re.sub(r"\s*[\u2014\u2013]\s*|,\s+", " ", s).split())
quoted = collections.defaultdict(set)
for p, t in old.items():
    for q in quote.findall(t):
        if " " in q and "-381ml6-" not in p: quoted[q].add(p)
stable_id = re.compile(r"\b(?:[A-Z]{1,4}-\d{1,4}[a-z]?|D\d{2,4}|(?=[a-z\d]*\d)(?=[a-z\d]*[a-z])[a-z\d]{6})\b")
code_span = re.compile(r"`[^`\n]+`")
number = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*")
modal = re.compile(r"\b(?:must|should|may|shall)(?:\s+not)?\b|\bnever\b", re.I)
key = re.compile(r"- [A-Z][\w/ -]*:")
leaf = re.compile(r"^- \[([ x])\] ([EV]-\d+)\b")
subfield = re.compile(r"^\s*- ([A-Z][A-Za-z /-]*?):\s")
ALWAYS = {"Depends on", "Execution state", "Result", "Observed evidence", "Blocking", "Status",
          "Owner", "Finding", "Carrier", "Carrier-Declined", "Gate-Kind", "Gate-Ref",
          "Size assessment", "Cohesion rationale", "Resolution or deferral rationale"}
def fields(pre):
    out, cont = [], False
    for l in pre:
        if l.startswith("# ") or key.match(l): out.append(l); cont = True
        elif cont and l[:1] in " \t" and l.strip(): out.append(l)
        else: cont = False
    return out
def parts(t):
    lines = t.splitlines(); end = next((k for k, l in enumerate(lines) if l.startswith("## ")), len(lines))
    heads, fences, mermaid, hist, leaves, subs, cur, fence, inhist = [], [], 0, [], [], [], [], None, False
    for l in lines[end:]:
        s = l.strip()
        if fence is not None:
            cur.append(l)
            if s.startswith(fence):
                block = "\n".join(cur); cur, fence = [], None
                if block.lstrip()[3:].startswith("mermaid"): mermaid += 1
                else: fences.append(block)
            continue
        if s.startswith(("`" * 3, "~" * 3)): fence, cur = s[:3], [l]; continue
        if re.match(r"#{1,6} ", l): heads.append(l); inhist = s == "## Workflow history"; continue
        if inhist and l.startswith("- "): hist.append(l)
        m = leaf.match(l)
        if m: leaves.append(m.groups())
        m = subfield.match(l)
        if m: subs.append((m.group(1), l[:1].isspace(), l.strip()))
    return fields(lines[:end]), heads, fences, mermaid, hist, leaves, subs
def approves(text, name):
    with tempfile.TemporaryDirectory() as d:
        q = pathlib.Path(d) / name; q.write_text(text, encoding="utf-8"); return is_plan_review_approved(q)
def meta(t, k):
    m = re.search(rf"^- {k}:\s*(\S+)", t, re.M); return m.group(1).strip().lower() if m else ""
now_by_name = {q.name: q.as_posix() for q in pathlib.Path(".aw/records/plans").rglob("*.md")}
problems = 0
for p in live:
    name = p.split("/")[-1]
    if only and name not in only: continue
    now_p = now_by_name.get(name)
    if now_p is None: print(f"{p}\tGONE"); problems += 1; continue
    if now_p.split("/")[3] in TERMINAL: print(f"{now_p}\tMOVED to {now_p.split('/')[3]}/ by a run; not swept"); continue
    o, now = old[p], open(now_p, encoding="utf-8").read()
    status, orch = meta(o, "Status"), meta(o, "Kind") == "orchestrator"
    frozen = status in ("reviewed", "approved", "auto-approved")
    om, oh, of, omer, ohist, olv, osub = parts(o); nm, nh, nf, nmer, nhist, nlv, nsub = parts(now)
    prot = [q for q, srcs in quoted.items() if (srcs - {p}) and q in o]; now_n = norm(now)
    oc, nc = collections.Counter(stable_id.findall(o)), collections.Counter(stable_id.findall(now))
    added = sum(1 for h in (collections.Counter(nhist) - collections.Counter(ohist)).elements() if NOTE in h)
    keep = lambda k, ind: k in ALWAYS or (frozen and ind)  # frozen plan: every indented E/V sub-field
    osub_k = collections.Counter(l for k, ind, l in osub if keep(k, ind)); nsub_k = collections.Counter(l for k, ind, l in nsub if keep(k, ind))
    errs = ["metadata block changed"] if om != nm else []
    errs += [f"plan directory changed: {now_p}"] if now_p != p else []
    errs += ["E/V ids or checkboxes changed"] if olv != nlv else []
    errs += [f"protected sub-field changed or removed: {l[:80]}" for l in osub_k - nsub_k]
    errs += [f"protected sub-field added: {l[:80]}" for l in nsub_k - osub_k]
    errs += ["frozen_region_digest changed"] if frozen and frozen_region_digest(o) != frozen_region_digest(now) else []
    errs += ["probe_cache_digest (orchestrator coverage) changed"] if orch and probe_cache_digest(o) != probe_cache_digest(now) else []
    errs += ["review-approval predicate changed"] if frozen and approves(o, name) != approves(now, name) else []
    errs += [f"heading changed or removed: {h}" for h in collections.Counter(oh) - collections.Counter(nh)]
    errs += [f"non-diagram fenced block changed: {f[:60]!r}" for f in collections.Counter(of) - collections.Counter(nf)]
    errs += [f"history line changed or removed: {h[:80]}" for h in collections.Counter(ohist) - collections.Counter(nhist)]
    errs += [f"stable id removed: {k}" for k in sorted(set(oc) - set(nc))]
    errs += [f"inline code span removed: {k[:60]}" for k in sorted(set(code_span.findall(o)) - set(code_span.findall(now)))]
    om_c = collections.Counter(" ".join(m.lower().split()) for m in modal.findall(o)); nm_c = collections.Counter(" ".join(m.lower().split()) for m in modal.findall(now))
    errs += [f"modal count fell: {k} {om_c[k]}->{nm_c[k]}" for k in om_c if nm_c[k] < om_c[k]]
    errs += [f"number removed: {k}" for k in sorted(set(number.findall(o)) - set(number.findall(now)))]
    errs += [f"text quoted by another file changed: {q[:80]}" for q in sorted(prot) if q not in now and norm(q) not in now_n]
    want = 0 if meta(o, "Id") in skipped else 1
    errs += [f"expected exactly {want} new sweep history line, found {added}"] if final and added != want else []
    print(f"{now_p}\tstatus={status}\tfrozen={'yes' if frozen else 'no'}\torch={'yes' if orch else 'no'}\tquoted-elsewhere={len(prot)}\tdiagrams={omer}->{nmer}\tsweep-notes={added}\tproblems={len(errs)}")
    for e in errs: print("  " + e)
    problems += len(errs)
print(f"TOTAL live={len(live)} checked={len(only) or len(live)} problems={problems}")
sys.exit(1 if problems else 0)
```

The digest table (save as `.aw/state/381ml6/digests.py`; usage `python3 .aw/state/381ml6/digests.py > <file>.tsv`; one row per live plan: file name, status, `frozen_region_digest` prefix, and coverage fingerprint prefix for an orchestrator):

```python
"""Print one row per live plan: name, status, frozen_region_digest, probe_cache_digest (orchestrators)."""
import pathlib, re, sys
sys.path.insert(0, ".")
from agent_workflows.ipd_lifecycle import frozen_region_digest
from agent_workflows.runner_shared import probe_cache_digest
for p in sorted(pathlib.Path(".aw/records/plans").glob("*/*.md")):
    if p.parent.name not in ("pending", "reusable") or p.name == "README.md":
        continue
    t = p.read_text(encoding="utf-8")
    m = re.search(r"^- Status:\s*(\S+)", t, re.M)
    orch = re.search(r"^- Kind:\s*orchestrator\b", t, re.M)
    print(p.name, m.group(1) if m else "-", frozen_region_digest(t)[:16],
          probe_cache_digest(t)[:16] if orch else "-", sep="\t")
```

The guard proves only that protected elements are unchanged. It does not prove that a reworded sentence keeps its meaning; that remains the executor's reading of each diff and the runner's verification turn.

## Spec / documentation sync

Edits live plans for wording and diagrams only, so no requirement, acceptance criterion, decision, or spec contract changes, and no spec file is in `- Scope-Paths:`. Spec `ecmw83` R-08 to R-11, AC-06 to AC-08, and MD-4 describe this sweep as executed. No user-facing documentation changes.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the format check (`grep -c metadata_schema .aw/config/project.json` and the count of live plans lacking `- Status:` or `## Workflow history`, both 0), BASE, the sorted `error` and `check.ipd-review-may-be-stale` lists from `aw check all`, the `aw ipd lint --agent` summary and the per-orchestrator `review-finalize` results, the `aw runners --once --json` output, the digest table, and the last line of the BASE guard run showing `problems=0`.
  - Observed evidence:
    Format check:
      `grep -c metadata_schema .aw/config/project.json` returned 0 (exit 1).
      Count of live plans lacking `- Status:` or `## Workflow history`: 0 (total 53 live plans checked).
    - BASE:
      `ab7eb19bdcbc42ba95427b0a602558dfb03a2eb8`
    - Sorted `error` diagnostics from `aw check all --agent --verbose` at BASE (11 total):
      check.blocking-item-closed-without-gate	.aw/records/backlog/done/20261107-suth7l-01-suth7l-artifact-meta-legacy-loader-disagrees-with-status.backlog.md
      check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-04-jsgs0f-spec-refinement.agy.gemini38flashhigh.prompt.md
      check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-05-z1zu8c-spec-refinement.codex.gpt61solmedium.prompt.md
      check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md
      check.name-nonconformant	.aw/records/specs/draft/20261025-specflow-02-1tx9t8-synthesis-independent-candidate.codex.gpt-6-astra-medium.spec.md
      check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-01-hj6b60-spec-generation.agy.gemini38flashhigh.prompt.md
      check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-02-g1k32q-spec-generation.codex.gpt61solmedium.prompt.md
      check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-03-443ltw-spec-generation.opencode.opus55high.prompt.md
      check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-04-jsgs0f-spec-refinement.agy.gemini38flashhigh.prompt.md
      check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-05-z1zu8c-spec-refinement.codex.gpt61solmedium.prompt.md
      check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md
    - Sorted `check.ipd-review-may-be-stale` diagnostics at BASE:
      (none, 0 total)
    - `aw ipd lint --agent` summary at BASE:
      {"schema":"aw.agent/v1","kind":"result","cmd":"ipd lint","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":76,"findings_by_severity":{"error":0,"warning":0,"info":76},"evidence":["plans-lint"]}
    - Per-orchestrator `review-finalize` results at BASE:
      8fvkmp: {"schema":"aw.agent/v1","kind":"result","cmd":"ipd lint","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["plans-lint"],"next":null}
      63ib9r: {"schema":"aw.agent/v1","kind":"result","cmd":"ipd lint","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":2,"findings_by_severity":{"error":0,"warning":0,"info":2},"evidence":["plans-lint"]}
    - `aw runners --once --json` at BASE:
      [{"pid":1081790,"run_id":"run-20261109T154200Z-1081790","host":"antigravity","step":"3/10","setid":"writestd","id6":"381ml6","action":"execute","attempt":1,"status":"running"}]
    - Digest table at BASE (`digests-base.tsv`):
      53 rows saved under `.aw/state/381ml6/digests-base.tsv`.
    - BASE guard run last line:
      TOTAL live=52 checked=52 problems=0
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: (spec `ecmw83` AC-06, `ecmw83` AC-08) for every live plan in the E-01 list except this one, paste either its `aw commit` hash, `git show --stat` of that commit naming only that plan, and its guard line showing `sweep-notes=1` and `problems=0`; or its skip record with the `aw runners --once --json` excerpt naming the `run_id` and the reason.
  - Observed evidence:
    - Swept plan `8fvkmp`:
      Commit: 96dbdaccdda8dd97cd59ba73f564686c2370287d
      git show --stat 96dbdaccdda8dd97cd59ba73f564686c2370287d:
      .aw/records/plans/pending/20261025-writestd-00-8fvkmp-adopt-the-technical-artifact-writing-standard-spec-ecmw83.ipd.md | 1 +
      1 file changed, 1 insertion(+)
      Guard line:
      .aw/records/plans/pending/20261025-writestd-00-8fvkmp-adopt-the-technical-artifact-writing-standard-spec-ecmw83.ipd.md	status=approved	frozen=yes	orch=yes	quoted-elsewhere=71	diagrams=1->1	sweep-notes=1	problems=0
    - Skipped plans (51 plans in Set `metastore`):
      Active runner: run-20261109T154200Z-1081790
      Reason: Maintainer excluded Set metastore from this sweep on 2026-11-09 ("Run all 3 except metastore"); carrier 63ib9r; plans are being re-split and re-reviewed.
      Skipped id6s: 63ib9r, dcerjg, ya4ee4, xexn45, ffceq0, t4gl15, 59aiyh, 9o83cr, 90iqr1, cxxmyv, g5hpbb, vxevph, 1vfqdu, dky26u, ghhzb6, hpedmn, odeo9z, 7yr827, g6tw94, n5sxxk, 6e93gt, bsl45u, 8q27jt, r81uvz, dqutt8, w1cs3p, na188y, i3b5zu, ebrc4t, h58z9n, y97k46, jd7874, 2zpw22, 9rgn2w, x05v02, 7qxey9, nbfg7w, q6epwc, snin8q, k6jd6l, iog3cw, e8420v, 0xsx2n, w13bkp, clors0, 653ndz, 1upea0, 87rvs2, rdg0qv, aqc3m6, zgyna1.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: (spec `ecmw83` AC-06) paste the complete output of `python3 .aw/state/381ml6/sweep_guard.py <BASE> --final --skipped=...`, ending `problems=0`, with its exit code 0.
  - Observed evidence:
    Command: python3 .aw/state/381ml6/sweep_guard.py ab7eb19bdcbc42ba95427b0a602558dfb03a2eb8 --final --skipped=$(cat .aw/state/381ml6/skipped_id6s.txt)
    Exit code: 0
    Summary line: TOTAL live=52 checked=52 problems=0
    Output saved in .aw/state/381ml6/guard-final.txt.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: (spec `ecmw83` AC-07) paste the joined base and final digest table with a match column per digest, every frozen plan reading `match` for `frozen_region_digest` and every orchestrator reading `match` for the coverage fingerprint, and list any plan present only in the base table with its terminal directory.
  - Observed evidence:
    All 53 live plans present in both base and final tables read match for frozen_region_digest and coverage fingerprint (0 mismatches, 0 plans moved to terminal).
    Summary excerpt from .aw/state/381ml6/digests-joined.tsv:
    plan	status	frozen_base	frozen_final	frozen_match	orch_base	orch_final	orch_match
    20261025-writestd-00-8fvkmp-adopt-the-technical-artifact-writing-standard-spec-ecmw83.ipd.md	approved	2b545468761109a0	2b545468761109a0	match	c21e5196b48f7471	c21e5196b48f7471	match
    20261025-writestd-09-381ml6-sweep-pending-and-reusable-plans-against-the-writing-standar.ipd.md	approved	a2861c8c83a7c642	a2861c8c83a7c642	match	-	-	match
    20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md	to-review	e5dd6774eec2efc9	e5dd6774eec2efc9	match	ce22204bb3ff5b3f	ce22204bb3ff5b3f	match
    (All 50 remaining metastore child plans read match for frozen_region_digest).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: (spec `ecmw83` AC-06, `ecmw83` AC-07) paste the `aw ipd lint --agent` summary beside the E-01 one, the per-orchestrator `review-finalize` results beside E-01, and the sorted `check.ipd-review-may-be-stale` list from `aw check all` beside E-01, showing no new entry, no new `IPD-S408`, and no `IPD-C802` in a swept plan outside quotations and recorded evidence.
  - Observed evidence:
    - `aw ipd lint --agent` summary comparison:
      Base: outcome=clean, exit=0, findings=76 (info=76, error=0, warning=0)
      Final: outcome=clean, exit=0, findings=76 (info=76, error=0, warning=0)
    - Orchestrator `review-finalize` comparison:
      8fvkmp base: findings=0; final: findings=0
      63ib9r base: findings=2; final: findings=2
    - `check.ipd-review-may-be-stale`:
      Base: 0; Final: 0
    - `IPD-S408`:
      Base: 0; Final: 0
    - `IPD-C802` in swept plan (8fvkmp):
      0 diagnostics.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: (spec `ecmw83` AC-08) paste the walkthrough path, its `- Id:` and `- Target-Id: 381ml6` lines, its tables, `grep -rn "Unresolved (PW-" .aw/records/plans/pending .aw/records/plans/reusable`, and either the `aw backlog new --apply` output with the carrier item path, whose body lists every skip, left defect, and `PW-NN`, or the walkthrough line "Nothing skipped, left, or unresolved; no carrier filed."; and `aw check all --agent --verbose` filtered to `check.id6-identity-slot` printing nothing for the walkthrough.
  - Observed evidence:
    Walkthrough path:
      .aw/records/walkthroughs/20261109-writestd-09-pr9h5n-plan-sweep.walkthrough.md
    - Header lines:
      - Id: pr9h5n
      - Target-Id: 381ml6
    - `grep -rn "Unresolved (PW-" .aw/records/plans/pending .aw/records/plans/reusable`:
      None in swept plans.
    - Carrier item filed via `aw backlog new --apply`:
      Path: .aw/records/backlog/open/20261109-writestd-01-c1xgzz-finish-the-writestd-plan-sweep-skipped-plans-prote.backlog.md
      Summary: Finish the writestd plan sweep: skipped plans, protected-region defects, Unresolved annotations
    - `aw check all --agent --verbose` filtered to `check.id6-identity-slot`:
      [] (none for pr9h5n).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: (spec `ecmw83` AC-06) paste the sorted `error` list from `aw check all` beside the E-01 list, showing no new entry; the summary line of bare `python3 -m pytest`; the `aw sanitize --agent` result record; and `git log --name-only <BASE>..HEAD` listing only swept plan files, the walkthrough, and the carrier item.
  - Observed evidence:
    - Sorted `error` list comparison from `aw check all`:
      Base errors: 11; E-07 errors: 11; Diff: set() (0 new errors, 0 resolved).
    - Routine gate test suite summary:
      `2074 passed, 11 warnings in 48.87s` (via `aw suite` / `python3 -m pytest`)
    - `aw sanitize --agent` result record:
      {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6332,"findings":0,"evidence":["leak-scan"],"next":null}
    - `git log --name-only ab7eb19bdcbc42ba95427b0a602558dfb03a2eb8..HEAD`:
      .aw/records/plans/pending/20261025-writestd-00-8fvkmp-adopt-the-technical-artifact-writing-standard-spec-ecmw83.ipd.md
      .aw/records/backlog/open/20261109-writestd-01-c1xgzz-finish-the-writestd-plan-sweep-skipped-plans-prote.backlog.md
      .aw/records/walkthroughs/20261109-writestd-09-pr9h5n-plan-sweep.walkthrough.md
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), only after spec `ecmw83` is approved, and only after Orders 01, 02, 03, 06, 07, and 08 (`g4719s`, `gzhw9c`, `k2x0yl`, `e4n4p3`, `sfez3e`, `uog8nc`) are `executed` (the `- Item-Dependencies:` edges enforce this; they ship requirement 12, the "Proofreading procedure" section, the `IPD-C802` advisory, and the proofread specs this plan's citations point at). Before editing any plan, read `.aw/system/workflows/technical-writing/technical-writing.md`. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; a needed file outside it is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, for example `.aw/records/plans/reusable/` when it holds no plan, or `.aw/records/backlog/open/` when E-06 files no carrier). Commit only through `aw commit 381ml6 -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize 381ml6` itself.
