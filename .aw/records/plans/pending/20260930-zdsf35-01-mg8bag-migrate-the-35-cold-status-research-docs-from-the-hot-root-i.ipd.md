# IPD: Migrate the 35 cold-status research docs from the hot root into their monthly shards

- Date: 2026-09-30
- Kind: child
- Concern: 35 research docs carry `status: reference` while living at the research tree's hot root, so the physical tier contradicts the frontmatter status the README declares authoritative.
- Scope: Move those 35 docs into their computed `reference/YYYYMM/` shards with `aw research promote --apply`, and repair the three LIVE path citations the moves would strand. No source change, no checker rule (that is sibling `ucwlwt`), no frontmatter change beyond what the tool writes.
- Scope-Paths: .aw/records/research, agent_workflows/comms.py, .aw/records/plans/pending/20260929-zftbta-01-68hdic-report-a-dangling-record-citation-in-packaged-source-as-a-ch.ipd.md, .aw/records/plans/pending/20260929-sklbrt-01-h8e3sm-mint-an-id6-for-the-two-live-legacy-specs-so-they-are-reacha.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: zdsf35
- Set: zdsf35
- Order: 1
- Highest E allocated: 07
- Author: opencode Opus 5, its_direct/pt3-claude-opus-5-1m-us
- Id: mg8bag

## Workflow history

- 2026-09-30 to-review (opencode Opus 5, its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `zdsf35`. `- Work-Kind: chore` and `- Priority: low` are INHERITED and both survive scrutiny: the readers key on frontmatter `status`, not on path, so no answer is wrong and the standing live-bug release gate does not attach (the item carries no `- Blocks-Release:` and this plan invents none). THE ITEM'S CENTRAL MEASUREMENT REPRODUCES EXACTLY at authoring HEAD `7000df73`: 35 root-dwelling docs carry a cold status, 0 docs carry a hot status inside a cold shard, and 0 sharded docs sit in the wrong month. THE ITEM'S REMEDY SHAPE IS ADOPTED, including its ordering argument (migrate first, then detect), which is why this is Order 01 of a two-child Set and sibling `ucwlwt` declares a hard `executed:mg8bag` edge. THREE CORRECTIONS THE ITEM DOES NOT CONTAIN, each measured rather than reasoned. FIRST, the item says all 35 are `reference` OR `archive`; measured, ALL 35 ARE `reference` and NONE is `archive`, so no `archive/` shard is created by this plan at all. SECOND, AND THIS IS THE REASON THE PLAN IS NOT A ONE-LINE SWEEP: 14 of the 35 docs are cited BY FULL PATH from elsewhere in the repository, and `aw research promote` DOES NOT REWRITE A PATH CITATION (verified in a scratch repo: after a move the citing file still named the old root path and `find_dangling_citations` returned `[]` both before and after, so nothing would have told us). 11 of those citing files are immutable executed plans or review records whose citations were correct when written and MUST NOT be rewritten; the other 3 are live and are repaired here. THIRD, the item's premise that a drift rule "would turn the tree red" needs one qualification that strengthens rather than weakens it: `aw research index --check` ALREADY exits 1 today on 61 pre-existing `dangling-citation` and 35 `adopted-without-consumer` findings, so the honest statement is that a tier rule would add 35 MORE findings to an already-failing gate, not that it would redden a green one. ONE ORDERING HAZARD IS REAL AND IS NOT DEFERRED: APPROVED plan `68hdic` (`- Blocks-Release: next`) instructs its executor to re-point `comms.py` at `j2000q`'s path, and `j2000q` is one of the 35. Whichever of the two runs second must use the post-move path, so E-06 repairs `68hdic`'s three occurrences in place and OQ-01 states the conflict for the maintainer rather than silently assuming an order.

## Goal

Make the research tree's physical layout agree with the status its own README declares authoritative, by moving the 35 cold-status docs out of the hot root into their monthly shards without stranding a single live citation. The payoff is that the hot root then means what it says (`todo`/`active` work awaiting attention) instead of being 59 files of which 35 are finished, and that sibling `ucwlwt` can ship a tier-drift rule that starts from zero findings instead of 35.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before moving anything

- [ ] E-01 RE-DERIVE the stranded cohort at execution HEAD rather than trusting this plan's list, and write the census into the execution record. For each conformant doc at the research root (one path component under the root, excluding `README.md` and `INDEX.md`), read frontmatter `status` through `research_contract.normalize_status` and select those whose normalized value is `reference` or `archive`. For each selected doc compute its target with `research_archive.plan_transition(root, <id6>, <status>)` and record `(id6, status, target shard)`. Also re-check the two directions the item measured clean: zero docs with a normalized hot status inside a `reference/` or `archive/` subtree, and zero sharded docs whose shard month differs from their frontmatter `created` month. REPORT the counts; do not reconcile them to this plan's numbers by adjusting the query. The authoring measurement, for comparison only: 35 docs, all `reference`, targeting `reference/202607` (18), `reference/202608` (14), `reference/202609` (3), with zero `plan_transition` errors; ids `0jl8pv 36rfym 524dw1 5zczmo 72n26s 74bchk 80eqy0 8i9py4 cnkyvn dkxesq e4k1m0 ebh1ap en5c8i fpt0dg g5vhpz ibl5kt itntmu j2000q jd8qhs kdr9kv ktlhfx lc6898 le9q02 mqqk8e qcxc6c rzfaon uec14r uxq2tt vdz4ui wusyd6 x41kw0 x9whzs ypmm6z z0wxwa za72ko`.
  - Depends on: none
  - Expected outcome: a recorded census of the cohort with each doc's computed target shard, the two clean-direction re-checks restated with their actual numbers, and any divergence from the authoring numbers named explicitly rather than smoothed over.
  - Execution state: pending

- [ ] E-02 CENSUS THE PATH CITATIONS the moves would strand, and CLASSIFY each citing file as LIVE (repairable) or IMMUTABLE (must not be touched), because `aw research promote` does not rewrite them. For every doc in E-01's cohort, search the tracked tree outside `.aw/records/research/` for the string `.aw/records/research/<filename>`; a basename-only mention is NOT affected by a move and is out of scope. Classify by location: a file under `plans/executed/`, `plans/superseded/`, `plans/not-executed/`, `reviews/`, or `backlog/done/` is IMMUTABLE under the execution contract's rule that an executed plan's record must not be rewritten and a citation correct when written must not be falsified; a file under `plans/pending/`, `backlog/open/`, `specs/`, or in source is LIVE. The authoring measurement, to be re-derived: 11 citing files, 8 of them executed plans plus 1 review (IMMUTABLE, 16 occurrences) and 2 pending plans (LIVE); separately `agent_workflows/comms.py` line 20 cites `j2000q` through its RETIRED `.agents/docs/research/` path, which is already dangling and is handled at E-05.
  - Depends on: E-01
  - Expected outcome: a per-file classification table naming every citing file, its occurrence count, and its LIVE/IMMUTABLE disposition with the reason, so the subsequent repairs are bounded by evidence rather than by a sweep.
  - Execution state: pending

### Task group 2: perform the migration

- [ ] E-03 PREVIEW the whole cohort with `aw research promote <id6> --to <status>` (no `--apply`) for every doc E-01 selected, and confirm each preview line names the shard E-01 computed. A promote whose preview errors or names a different target is a STOP for that doc: record it and exclude it rather than forcing it, because a mismatch means the doc's `created` disagrees with what this plan measured. Note that the shard follows frontmatter `created`, NOT the filename date (`research_archive._shard_subpath` passes `created` to `research_contract.shard_for_date`); 11 of the 35 have a `created` month that differs from their filename month, so a target like `reference/202608` for a `20260731-` file is CORRECT and must not be "fixed".
  - Depends on: E-01
  - Expected outcome: a preview line per doc, each matching E-01's computed target, with any erroring or diverging doc named and excluded rather than forced.
  - Execution state: pending

- [ ] E-04 APPLY the moves with `aw research promote <id6> --to <status> --apply` for each doc E-03 previewed clean. The verb rewrites frontmatter `status` in place, performs the move as a tracked `git mv`, and refreshes the local manifest; the manifest is GITIGNORED and must NOT be committed (`research_archive.apply_moves` deliberately omits `INDEX.json`/`INDEX.md` from its returned touched list for exactly this reason). Do NOT hand-move a file with `git mv` and do NOT hand-edit a `status:` line: the tool owns both halves of the transition and splitting them is what produces the mirror-image drift this Set exists to remove. Commit the moves with `aw commit` on the research paths. Confirm the hot root afterwards contains no doc with a cold normalized status.
  - Depends on: E-03
  - Expected outcome: every previewed doc lives in its shard with frontmatter `status` unchanged in value (it was already cold) and a tracked rename in `git status`, the hot root holds zero cold-status docs, and no `INDEX.json`/`INDEX.md` is staged.
  - Execution state: pending

### Task group 3: repair only the live citations the moves strand

- [ ] E-05 RE-POINT `agent_workflows/comms.py`'s module docstring citation at `j2000q`'s POST-MOVE path. The line reads ``.agents/docs/research/20260714-2300-01-same-box-agent-wakeup-mechanisms.md`` and is ALREADY dangling before this plan runs (the `.agents/` tree is retired); `j2000q` is in the cohort, so its correct target after E-04 is the shard path, not the current root path. Write the path E-01/E-04 actually produced, re-read from disk rather than copied from this plan. THIS EDIT OVERLAPS APPROVED PLAN `68hdic` E-05, which owns the same line and names the PRE-MOVE root path; that is the conflict OQ-01 records. If `68hdic` has already executed at this point, this item becomes a one-line correction of the root path it wrote; if it has not, E-06 is what keeps it from writing a stale path later. Either way state which case applied. This is a docstring; change no code path.
  - Depends on: E-04
  - Expected outcome: `comms.py` names a path that resolves on disk, verified by an existence check on the exact string now in the file, with the pre-existing dangling `.agents/` form gone and no executable line altered.
  - Execution state: pending

- [ ] E-06 CORRECT the stale root paths in the two LIVE PENDING plans so a later executor does not act on a path this plan invalidated, and leave every IMMUTABLE citation E-02 classified untouched. In `68hdic` (3 occurrences of `j2000q`'s root path, in its workflow history, its E-05 body, and its F-15 row) and in `h8e3sm` (1 occurrence of `en5c8i`'s root path in its F-15 row), replace the root path with the post-move shard path. Both are APPROVED plans, so this is the minimum edit that keeps an approved instruction executable; do not restructure either plan, do not touch their `- Status:`, and append nothing to their workflow history beyond what the lifecycle tooling writes. Note `h8e3sm`'s F-15 concerns a COMMIT-PINNED GitHub permalink that must survive untouched; only the in-repo path on that row is edited. DO NOT rewrite the 16 occurrences in the 8 executed plans and 1 review: those citations were correct when written and the execution contract forbids changing what an executed plan records.
  - Depends on: E-04
  - Expected outcome: both pending plans cite paths that resolve, the pinned permalink is byte-identical, and a diff restricted to the immutable set shows zero changes.
  - Execution state: pending

### Task group 4: prove the tree is no worse than it was

- [ ] E-07 ESTABLISH the before/after comparison that shows this migration introduced no new finding, since the gate is ALREADY failing and so a bare exit code proves nothing. Before E-04, capture `aw research index --check` findings grouped by rule; after E-04 and the repairs, capture them again and diff the GROUPED COUNTS. The authoring baseline, to be re-derived at execution HEAD: exit 1 with 61 `dangling-citation`, 35 `adopted-without-consumer`, 17 `stale-state-to-promote`, and 2 `check.stale-index-missing` (the last at `info`, which `artifact_core.drift_exit_code` exempts). Expect the counts to be UNCHANGED by the migration: the moves alter neither citation resolution (resolution is by `<id6>`, not by path) nor `consumed-by`. A changed count is a STOP to investigate, not a number to accept. Also run the bare suite (`python3 -m pytest`) and paste its actual summary line.
  - Depends on: E-06
  - Expected outcome: grouped finding counts before and after with an explicit statement that the delta is zero (or the investigated reason it is not), plus the pasted bare-suite summary.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE TOOL OWNS BOTH HALVES OF A TIER TRANSITION. `research_archive.apply_moves` rewrites frontmatter `status`, performs a tracked `git mv`, and refreshes the manifest in one pass; `plan_transition` computes the target via `_target_path` / `_shard_subpath`. Hand-moving a file or hand-editing a `status:` line performs half a transition and is precisely how the drift this Set removes was created. `.aw/records/research/README.md` states the rule directly: "Do NOT hand-name or hand-maintain research files or the index."
- THE SHARD FOLLOWS FRONTMATTER `created`, NOT THE FILENAME DATE. `_shard_subpath` passes `created` to `shard_for_date`. Measured: all 64 already-sharded docs match their `created` month and 63 match their filename month, so the one divergence proves which field governs. In the cohort, 11 of 35 have diverging months, so a target shard that disagrees with the filename prefix is correct.
- THE GENERATED MANIFESTS ARE GITIGNORED AND MUST NOT BE COMMITTED. `apply_moves` deliberately excludes `INDEX.json`/`INDEX.md` from its returned touched list, citing IPD `4r0qp1`; the README records that a tracked auto-regenerated manifest conflicts on any concurrent branch by construction, and that one such conflict stranded 2477 lines of correct code.
- `aw research index --check` IS ALREADY FAILING, so exit code alone cannot validate this work. `run_index` returns `artifact_core.drift_exit_code(drift)`, which fails on anything not at `info` severity; three non-`info` rule families are already firing. Validation therefore compares GROUPED COUNTS before and after.
- A RESEARCH CITATION RESOLVES BY `<id6>`, NOT BY PATH, which is why a move is safe for the checker and unsafe for a human reader. `research_refs.find_dangling_citations` resolves the `RSCH-<id6>` handle and the full parseable filename; the BASENAME is unchanged by a tier move, so the detector is silent either way. Verified in a scratch repo: a plan citing a doc's root path still named the root path after the doc moved, and the detector returned `[]` both before and after.
- AN EXECUTED PLAN AND A REVIEW RECORD ARE IMMUTABLE. The execution contract forbids changing what a plan in `plans/executed/` records. Approved plan `68hdic`'s own deferral table states the positive form of this for citations: they "were CORRECT WHEN WRITTEN ... so fixing them is forbidden, not pending."

## Findings

| Id | Severity | Finding | Consequence |
|---|---|---|---|
| F-01 | n/a | THE ITEM'S CENSUS REPRODUCES EXACTLY. At HEAD `7000df73`: 126 docs under the research tree, 35 carrying a cold normalized status at the hot root, 0 carrying a hot status inside a cold shard, 0 sharded docs in the wrong month. | The premise needs no correction; the plan can proceed to remedy rather than re-litigate. |
| F-02 | LOW | ALL 35 ARE `reference`; NONE IS `archive`, where the item says "reference/archive". Targets: `reference/202607` (18), `reference/202608` (14), `reference/202609` (3). | No `archive/` shard is created. A plan written for both tiers would carry an unexercised branch. |
| F-03 | **HIGH** | **`aw research promote` DOES NOT REWRITE A PATH CITATION, AND NOTHING REPORTS THE BREAKAGE.** Measured in a scratch repo: after promoting a doc cited by full path from an executed plan, the plan still named the old root path, and `find_dangling_citations` returned `[]` BEFORE and AFTER. `apply_moves`' own comment concedes the gap ("if a full-path cite exists it is caught by the dangling detector"), and that claim is FALSE for a tier move, because the basename is unchanged so id6 resolution still succeeds. | A bare sweep silently strands every path citation. E-02 must census them and E-05/E-06 repair the live ones; a validation resting on `--check` exiting the same way would have passed over the damage. |
| F-04 | **HIGH** | **14 OF THE 35 ARE CITED BY FULL PATH, ACROSS 11 FILES, AND 9 OF THOSE FILES ARE IMMUTABLE.** 8 executed plans plus 1 review hold 16 occurrences; 2 pending plans hold the rest. | The repair set is 3 live citations, not 11 files. Rewriting the immutable 9 would falsify history and violate the execution contract. |
| F-05 | **HIGH** | **AN APPROVED, RELEASE-GATING PLAN WILL WRITE A PATH THIS MIGRATION INVALIDATES.** `68hdic` (`- Status: approved`, `- Blocks-Release: next`) E-05 instructs its executor to re-point `comms.py` at `j2000q`'s CURRENT ROOT PATH, and names that path 3 times. `j2000q` is in the cohort. | Whichever plan runs second must use the post-move path. E-06 repairs `68hdic` in place; OQ-01 surfaces the ordering to the maintainer rather than assuming it. |
| F-06 | MEDIUM | THE "WOULD TURN THE TREE RED" ARGUMENT IS DIRECTIONALLY RIGHT AND FACTUALLY IMPRECISE. `aw research index --check` already exits 1 at HEAD: 61 `dangling-citation`, 35 `adopted-without-consumer`, 17 `stale-state-to-promote`, 2 `check.stale-index-missing` (`info`, exempted by `drift_exit_code`). | A tier rule would add 35 findings to an ALREADY-failing gate. The ordering argument survives, but this plan's validation cannot use exit code as its signal (E-07 uses grouped counts). |
| F-07 | MEDIUM | THE 35 `adopted-without-consumer` FINDINGS ARE NOT THE SAME 35 DOCS, despite the coincident count. Overlap is 17; 18 of them sit on docs already in shards. | A validation that matched on count alone could mistake one rule's findings for another's. E-07 groups by rule and compares per-rule counts. |
| F-08 | MEDIUM | THE SHARD IS COMPUTED FROM `created`, NOT THE FILENAME DATE, and 11 of the 35 diverge (four `20260726-skills-*` and seven `20260731-chkplace-*` all carry `created: 20260802`, so they target `reference/202608`). | An executor who "corrects" a target to match the filename prefix would mis-shard 11 docs and contradict all 64 existing sharded docs, every one of which matches its `created` month. |
| F-09 | LOW | `h8e3sm`'s stale citation sits on a row about a COMMIT-PINNED GitHub permalink (`blob/<sha>/...`) that the repository's own tooling deliberately preserves via `_PINNED_PERMALINK_RE`. | E-06 edits only the in-repo path on that row and must leave the permalink byte-identical. |
| F-10 | LOW | ALREADY-STALE ROOT-PATH CITATIONS EXIST TODAY from the previous sharding pass (for example `bu9yij`, `27rjro` and `i5gj61` are cited at root paths while living in `reference/` shards), and no checker reports them. | Confirms F-03 as a STANDING gap rather than a hazard this plan invents, and bounds this plan: it must not strand more, and it is not chartered to fix the pre-existing ones (see the deferral table). |
| F-11 | LOW | NO PENDING OR REUSABLE PLAN DECLARES ANY COHORT DOC IN `- Scope-Paths:`, so the moves cannot collide with another plan's declared scope. | No cross-plan scope coordination is needed beyond the citation repairs. |

## Proposed changes (ordered, validatable)

1. Re-derive the stranded cohort and both clean-direction re-checks at execution HEAD (E-01; F-01, F-02, F-08).
2. Census the path citations the moves would strand and classify each citing file LIVE or IMMUTABLE (E-02; F-03, F-04, F-10).
3. Preview every promotion and confirm each target matches the computed shard (E-03; F-02, F-08).
4. Apply the promotions through the tool, committing the renames and not the manifests (E-04; F-01).
5. Re-point `comms.py` at the post-move path (E-05; F-05).
6. Correct the stale root paths in the two live pending plans, leaving the immutable nine untouched (E-06; F-04, F-05, F-09).
7. Compare grouped `--check` findings before and after and run the bare suite (E-07; F-06, F-07).

## Deferred / out of scope (with reason)

- THE STATUS-VERSUS-TIER DRIFT RULE. Deferred BY DESIGN to sibling plan `ucwlwt` (Order 02 of this Set), which declares `Item-Dependencies: executed:mg8bag`. The item's own ordering argument is adopted: a rule shipped before this migration would report all 35 docs immediately.
  - Carrier: ucwlwt
- THE PRE-EXISTING STALE ROOT-PATH CITATIONS TO ALREADY-SHARDED DOCS (F-10). Out of scope: they were created by an earlier sharding pass, this plan neither creates nor worsens them, and fixing them means editing immutable executed plans and review records in most cases. Fixing them is a separate judgement about which are live pointers.
  - Carrier-Declined: Nothing is owed by this plan, and the larger class is one a carrier would misrepresent as uniformly actionable when most members are immutable records whose citations were correct when written. The GENERAL defect (no checker reports a stale record path citation) already has an owner in approved plan `68hdic`, which builds exactly that detector for source trees; filing a second record would duplicate it.
- REWRITING THE 16 PATH CITATIONS IN THE 8 EXECUTED PLANS AND 1 REVIEW (F-04). Forbidden, not deferred: the execution contract prohibits changing what a plan in `plans/executed/` records, and those citations were correct when written.
  - Carrier-Declined: Nothing is owed; this is a POSITIVE contract rather than an absence. A carrier would name an obligation the execution contract explicitly prohibits discharging.
- TEACHING `apply_moves` TO REWRITE PATH CITATIONS ON A TIER MOVE (the root cause behind F-03). Out of scope here: this plan's charter is the corpus, and a rewriter change is a source change with its own blast radius (it would have to distinguish a live pointer from a historical record and from a pinned permalink, exactly the classification `68hdic` measured as mechanically delicate).
  - Carrier: zdsf35
  - Carrier-Note: Backlog item `zdsf35` remains the Set's parent record and is the natural home for the follow-up; this plan records the measured gap at F-03 and the scratch-repo evidence so the follow-up starts from data rather than from suspicion.
- `- Work-Kind: chore` IS INHERITED AND IS CORRECT. The item's own reasoning holds and was re-verified: readers key on frontmatter `status`, so no user-visible answer is wrong, and the perceptibility test for `bug` is not met. No release gate attaches.
  - Carrier-Declined: Nothing is owed. This row records an inherited classification that measurement confirms, not deferred work.

## Scope check

- Over-scope: none. The three citation repairs (E-05, E-06) are not opportunistic widening: each is a citation THIS PLAN'S MOVES INVALIDATE, so leaving them would ship a known regression. The immutable nine are deliberately excluded.
- Under-scope: the pre-existing stale root paths of F-10 and the `apply_moves` rewriter gap of F-03 are both left unfixed, each with a reason and a disposition in the deferral table above.

## Required tests / validation

No new automated test is added, and that is a deliberate judgement rather than an omission: this plan changes DATA (file locations in this repository's own records tree), not behavior. The behavior it relies on is already covered - `tests/test_research_archive.py::test_promote_to_reference_moves_to_weekly_shard_keeps_id` asserts the shard move preserves the id6 and rewrites the status, and `test_shard_for_date` pins the month derivation. A test asserting "this repository's corpus currently has zero stranded docs" would be a corpus-census test, which is the code-pinning shape the contract forbids; the DURABLE guard is sibling `ucwlwt`'s checker rule, which is tested against a fixture.

Validation is therefore evidential: the re-derived census (E-01), the per-file citation classification (E-02), the per-doc previews (E-03), `git status` showing tracked renames with an empty cold-status hot root (E-04), existence checks on each repaired citation string (E-05, E-06), a zero diff over the immutable set (E-06), grouped `--check` finding counts before and after (E-07), and the pasted bare `python3 -m pytest` summary (E-07).

## Spec / documentation sync

N/A with reason. No spec or README amendment is required, because this plan brings the CORPUS into line with a layout the documentation ALREADY mandates rather than changing the contract. `.aw/records/research/README.md` states the invariant this plan enforces ("Hot states (`todo`/`active`) stay flat at this directory's root ... Cold states live in monthly `YYYYMM` shards"), and spec `5tapom` Section 4 explicitly preserves "the shard layout" as a non-goal. No `.spec.md` file appears in `- Scope-Paths:` and none is edited.

## Open questions

### OQ-01: Should this plan execute before or after approved plan `68hdic`, which edits the same `comms.py` line and names a path this migration invalidates?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED as EITHER ORDER, which is why no `Item-Dependencies` edge is declared on `68hdic` and why nothing is owed to a later turn. The two plans are in different Sets with no edge between them, so the runner's dependency-depth sort leaves the order genuinely undetermined; rather than assume one, E-05 and E-06 together make BOTH correct. If `68hdic` runs first it writes `j2000q`'s root path and E-05 then corrects it to the shard path; if this plan runs first, E-06 has already corrected `68hdic`'s instruction so its executor writes the shard path directly. V-05 requires the executor to STATE which case applied, so the record says which happened rather than leaving it inferable. The only residual difference is cosmetic (running `68hdic` first costs this plan no amendment of an approved release-gating plan, but costs one extra correction here), and a maintainer who prefers that order can simply run it first; no instruction here depends on the choice. The plans do not conflict over any other file: `68hdic`'s `- Scope-Paths:` covers source and tests, and the only overlap is the `comms.py` docstring line plus `68hdic`'s own plan text.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted census output listing every selected doc with its id6, normalized status, and computed target shard, plus the two clean-direction counts stated as actual numbers (hot-status-in-cold-shard, and sharded-doc-month-mismatch). State whether the cohort size matches 35 and whether all are `reference`; if either differs from the authoring measurement, name the difference and the reason rather than restating this plan's numbers.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted classification table: every citing file, its occurrence count, and LIVE or IMMUTABLE with the reason. Confirm the LIVE set is exactly the files this plan will edit at E-05/E-06, and that every file under `plans/executed/`, `reviews/`, `plans/superseded/`, `plans/not-executed/`, or `backlog/done/` is classified IMMUTABLE.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the pasted preview lines (`would set <id6> status=... and move to <shard>/...`), one per doc, with a statement that each matches V-01's computed target. Name any doc whose preview errored or diverged and confirm it was EXCLUDED rather than forced. Explicitly confirm that the docs whose `created` month differs from their filename month (expected: 11) previewed to the `created`-derived shard and were NOT adjusted.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git status --porcelain` (or `git log --stat` for the commit) showing the moves as tracked renames `R`, a re-run of V-01's query proving the hot root now holds ZERO cold-status docs, and `git diff --cached --name-only` for the commit proving no `INDEX.json` or `INDEX.md` was staged. Also paste one moved file's frontmatter `status:` line to show it is intact.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the one-line diff of `agent_workflows/comms.py`, plus a test that the path string now in the file EXISTS on disk (for example an `ls` of that exact path succeeding). Confirm the old `.agents/docs/research/...` form returns no grep hit, and state which `68hdic` ordering case applied. Confirm no executable line changed (the diff touches the module docstring only).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the diffs for both pending plans showing root path replaced by shard path (expected 3 occurrences in `68hdic`, 1 in `h8e3sm`), an existence check on each new path, and a grep proving the `blob/<sha>/` permalink on `h8e3sm`'s F-15 row is byte-identical. Also paste `git diff --name-only` restricted to the IMMUTABLE set from V-02 showing EMPTY output, and confirm neither plan's `- Status:` line changed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the before and after `aw research index --check` findings GROUPED BY RULE with counts side by side, and an explicit statement that the per-rule delta is zero (or, if not, the investigated cause). Note the exit code remains 1 both times and say so, so a reader does not mistake a failing gate for a regression this plan caused. Plus the actual bare `python3 -m pytest` summary line pasted verbatim.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution and must not be executed by the agent that authored it in the same turn. On execution: commit ONLY the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. The generated `INDEX.json`/`INDEX.md` are gitignored and must not be staged even though `aw research promote` refreshes them on disk.

Keep the migration commit (E-04) separate from the citation repairs (E-05, E-06): the first touches only the research tree, the second touches source and two other plans' records, and mixing them makes the rename set unreadable in review.

Do not mark this plan executed until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries pasted evidence. Then move it to `.aw/records/plans/executed/` through the lifecycle tooling. Sibling plan `ucwlwt` declares `Item-Dependencies: executed:mg8bag` and cannot execute until that terminal transition has happened.
