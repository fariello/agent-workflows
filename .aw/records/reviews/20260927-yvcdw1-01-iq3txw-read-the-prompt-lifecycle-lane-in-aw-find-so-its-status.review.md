# Review findings: plan iq3txw

- Subject-Id: iq3txw
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `b86cfd87` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`) and `--phase review-finalize --agent`
conforms after revision with `findings: 0`. No pre-review snapshot was owed: the plan was committed
and unmodified (`git status --short` clean) and the lane-input copy at `.aw/state/lane-inputs/rev-13/`
is byte-identical to the tracked file (`diff` reported no difference). `aw sanitize --agent` clean.

FIFTEEN OF FIFTEEN AUTHORED FINDINGS REPRODUCE EXACTLY, which is the highest hit rate in this sweep.
The diagnosis is correct and precise: one line in one branch, with a sharp explanation of the 16-versus-1
split (only one prompt carries a `- Status:` bullet inside its metadata region that `selectors._read_status`
can see, while all 17 carry the comment form it cannot). The plan's Step 0 analysis is better than the
backlog item it graduated from: it identifies that `ipd_lint._dir_of`, which the item recommended, reads
`LIFECYCLE_SUBDIRS["plans"]` rather than `["prompts"]` and uses an anywhere-in-path `anchor in parts`
test, and it picks the sharding-safe `attention._prompt_disposition_from_rel` instead. I verified every
one of those claims, including the sharding case.

WHAT REVIEW FOUND IS THAT THE PLAN COULD NOT HAVE BEEN FINALIZED AS AUTHORED, AND THAT ITS THIRD STEP
COULD NOT HAVE BEEN IMPLEMENTED AS SEQUENCED.

**ALL FOUR DEFERRED ROWS NAMED NO CARRIER (PR-401, BLOCKER).** `aw check` already reported
`check.ipd-uncarried-obligation` against this plan at ERROR severity before review touched it, and the
shared predicate `check_engine.evaluate_durable_carrier` returns the reason in full: "4 obligation(s)
name no durable carrier: deferred row 1 ... row 2 ... row 3 ... row 4 ... once this plan reaches
`executed` it classes `done` in `aw attention` and this vanishes with no record". That same rule is
merged into `aw ipd lint --phase pre-transition`, which the plan's own gate requires to report
conforming before the lifecycle move, so the plan as authored was structurally unable to satisfy its own
gate. This is a BLOCKER rather than a HIGH because it is not a matter of taste or completeness: a
mechanical gate the plan itself invokes refuses it. Three rows now carry reasoned `Carrier-Declined:`
lines and the id6 row carries a real carrier. The plan was RIGHT that the id6 column is a genuine
outstanding obligation and right not to file while authoring ("filing is not authoring"), so review
filed it: backlog `y0t9u7`, measured (all 17 id6 cells are `-`; `prompts.read_metadata_id6` returns
`sloz20` where `selectors._read_id` returns `None`) and carrying `Blocks-Release: next` because it is a
`bug` under the every-live-bug-gates policy, the same treatment its sibling `yvcdw1` received. Verified
fixed: the predicate now returns zero drifts.

**E-03 IS NOT IMPLEMENTABLE IN THE ORDER GIVEN (PR-402, HIGH).** E-01 describes the helper's input as
"the already-computed repo-relative path string", but in the generic branch the source order is
`raw_status = sel_mod._read_status(text)`, then `if explicit_status: ... continue`, then
`status = raw_status or "-"`, then the `try: rel = ...` block. So `rel` does not exist at the filter
site where E-03 must compare the effective status. An executor following the plan literally would
either compute a SECOND path string beside the existing one, which is precisely the two-spellings
divergence E-03 exists to prevent, or move `rel` without the plan authorizing it. E-01 and E-02 now
specify the relocation (up to just after `text` is read, before the `explicit_id` filter), argue why it
is behavior-preserving, and forbid a second path string; V-01 requires the moved block pasted so a
reviewer can see the move rather than infer it.

**APPENDING THE REVIEW RECORD EXPOSED A LATENT DEFECT IN THE PLAN'S OWN HISTORY (PR-407, MEDIUM).** The
two authored records were written OLDEST-FIRST within one date, contrary to the newest-first convention,
so the recorded event stream reads `to-review` -> `draft`. That was silent only because a same-date
group with a mixed status set is treated as unordered and skipped; the instant a newer-dated record
existed the group became ordered and `check.lifecycle-transition-invalid` fired with "backwards
transition 'to-review' -> 'draft'". I reordered the two lines and the rule is clear. This is worth
recording beyond this plan: any plan whose first two history records share a date and are written
oldest-first carries the same trap, invisible until someone appends to it.

Two smaller items. E-03 changes the filter code path for EVERY generic type, not only prompts, while
E-04(e)'s non-leakage case pinned only the rendered cell; E-04 gained a filter-non-leakage case and a
case-variant `--status` case (PR-403). And every baseline was unnumbered (PR-405), now measured at
`2935 passed, 2 skipped` bare, `12 passed` for `tests/test_lifecycle_style.py` (which must RISE by one
when E-05 lands) and `42 passed` for the six-file neighbour set (which must NOT change).

OQ-01 was self-resolved and its CONCLUSION IS CORRECT, but its first reason does not hold and I
corrected it rather than accepting it (PR-404). The plan argues that a lane-first display "would hide
the disagreement" that `check.prompt-status-mismatch` reports. Measured: that rule compares the
`<!-- aw-prompt: ... -->` COMMENT status against the bucket, while `aw find`'s generic branch reads the
`- Status:` BULLET through `selectors._read_status`. They are different fields, so the rule fires
regardless of what this column shows and no display choice can hide it. The honest residue is narrower
and still real (a lane-first display could never reveal a BULLET-versus-lane divergence, which no rule
checks at all), and reasons two and three carry the decision unaided: `prompts_index.scan_prompts`
already resolves the identical conflict identically, and no row in the repository diverges today.

Every other claim verified. F-01 (`16 · -`, `1 ↪ superseded`); F-02 (the one line, read in source
order); F-03 (`_read_status` sees 1 of 17); F-04 (the single bullet-carrying `superseded/` prompt is
exactly the row that renders); F-05 (zero divergence across all 17); F-06 (both `--status` forms return
zero rows); F-07 (all five lanes in `_PROMPTS_PAIRS`); F-08 (spec `uonrjg` 6.5's header is literally
"Native status or lane" with the same five mappings, so this implements an approved spec); F-09 (no
`prompts.STATUSES`; `_find_valid_statuses("prompts")` is `None`); F-10 (the `check_engine` precedent
import); F-11 (no test asserts this column; `test_cli_find.py`'s prompts mention is a `record_dirs`
assertion); F-12 (13/2/2, and the `reusable`/`not-executed` lanes hold only READMEs and `.gitkeep`, so
constructed fixtures really are required); F-13 (the comment promises `test_prompts_directory_derived`
and `rg` finds only the comment); F-14 (the JSON carries `'·  -             -  .aw/records/prompts/...'`
byte-for-byte); F-15 (`scan_prompts`' `status = meta.get("Status") or disposition`). The convention
claims hold too: all five lane words resolve natively through `_find_resolve_lifecycle` with no resolver
edit, `PROMPT_LANES` does equal `LIFECYCLE_SUBDIRS["prompts"]` as a set, the two subdir tuples are
incidentally identical as the plan says, and the lazy-import style has four precedents in `cli.py`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-401 | BLOCKER | UNDER-SCOPE | G. Plan executability / D. records integrity | `aw check` names this plan with `check.ipd-uncarried-obligation`; `check_engine.evaluate_durable_carrier(repo, plan_path=..., plan_text=...)` returns one `error` drift: "4 obligation(s) name no durable carrier: deferred row 1 ... row 4 ... once this plan reaches `executed` it classes `done` in `aw attention` and this vanishes with no record"; the same rule appears in `aw ipd lint --phase pre-transition` output; the plan's own gate requires that phase to conform | **THE PLAN COULD NOT HAVE BEEN FINALIZED AS AUTHORED.** None of the four Deferred rows carried a `Carrier:` or `Carrier-Declined:` line, so a mechanical gate the plan itself invokes refuses it, and the one genuinely outstanding obligation (the prompts id6 column) would have vanished from `aw attention` the moment this plan reached `executed`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Three rows gained reasoned `Carrier-Declined:` lines (enum: absence is the correct state; backfill: a prohibition, not owed work; `_STATUS_RE`: would not fix it and relaxes a documented contract). The id6 row gained carrier `y0t9u7`, a backlog item review FILED with the measurement, the ready-made reader, the `--id` filter consequence, and an ordering note to land after this plan. Verified: the predicate now returns ZERO drifts and `aw check` reports nothing against this plan. |
| PR-402 | HIGH | IN-SCOPE | A. Correctness / G. Executability | Source order in `cli._find_type_records`' generic branch: `raw_status = sel_mod._read_status(text)` -> `if explicit_status: ... continue` -> `status = raw_status or "-"` -> `try: rel = str(p.resolve().relative_to(repo_root.resolve()))`; plan E-01 "takes the already-computed repo-relative path string"; plan E-03 "compare against the same fallback-resolved value" | **E-03 CANNOT BE IMPLEMENTED AS SEQUENCED**, because `rel` does not exist at the filter site. An executor would either compute a second path string beside the existing one (the exact divergence class E-03 exists to close) or relocate `rel` without authorization. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-01 now names the trap and E-02 owns the relocation (move the `rel` block above the `explicit_id` filter), with the behavior-preservation argument and an explicit prohibition on a second path string. E-03 states the effective value is computed ONCE above the filter and reused, and to keep the existing `.strip().lower()` normalization. V-01 requires the relocated block pasted. New F-17. |
| PR-403 | MEDIUM | UNDER-SCOPE | D. Anti-regression / E. Testing | E-03 edits the `explicit_status` comparison in a branch shared by `walkthroughs`, `roadmaps`, `comms`, `reviews` and `other` (all measured to return `None` from `_find_valid_statuses`, so all reach it); E-04(e) asserts only that a non-prompts type still RENDERS `-` | The non-leakage case covered the COLUMN but not the FILTER, which is the half E-03 actually changes for every generic type. A prompts-only filter change could have leaked into another type with nothing asserting otherwise. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 gained case (f), asserting `--status <lane>` against a non-prompts generic type still returns nothing, and case (g), a case-variant `--status` argument returning the same rows, pinning the normalization E-03 preserves. Expected outcome updated. New F-18. |
| PR-404 | MEDIUM | IN-SCOPE | F. Honest documentation / A. Correctness | `check_engine`'s prompt checks compare `comment_status` (from the first-line `<!-- aw-prompt: ... -->`) against `disp`; `aw find`'s generic branch reads `selectors._read_status`, the `- Status:` BULLET; measured, only 1 of 17 prompts has a bullet that reader can see | **OQ-01's FIRST REASON IS FALSE AS STATED.** A lane-first display could not "hide" `check.prompt-status-mismatch`, because that rule reads a different field and fires either way. The conclusion (front-matter-first) is nonetheless correct on its other two reasons, so this is a corrected justification rather than a reversed decision. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01's first reason rewritten to state the measurement, demoted to a weak consideration, and replaced with the narrower claim that actually holds (only front-matter-first can ever surface a BULLET-versus-lane divergence, which no rule checks). Reason two promoted as the one carrying the decision. |
| PR-405 | LOW | IN-SCOPE | E. Testing | Required tests named three runs with no expected counts | No baseline meant no comparison; in particular nothing would have caught E-05 silently not adding its test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Measured at review: bare `2935 passed, 2 skipped, 3 warnings` (zero failures); `tests/test_lifecycle_style.py` `12 passed`, which MUST rise by one; the six-file neighbour set `42 passed`, which must NOT change. All six neighbour files confirmed to exist. |
| PR-406 | LOW | IN-SCOPE | G. Plan executability (gate) | Gate as authored: path-scoped commit, staged-set verification, never-push, paste-actual-output, the gate-inheritance paragraph and the `Readiness` abstention all present; no named scope fence, no out-of-scope-edit disposition; lifecycle move stated unconditionally; 2026-09-01 scope-fence ruling | The gate named no forbidden paths, carried no out-of-scope-edit disposition, and stated the lifecycle move without conditional runner/executor ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a SCOPE FENCE (no prompt record, no `.spec.md`, not `attention.py`/`selectors.py`/`prompts_index.py`, no sixth lane derivation, not the id6 column, no prompts enum); make-and-justify wording; conditional finalize ownership; and a note that `pre-transition` also measures the carrier rule, so it must be re-run rather than assumed to be checkbox-only. |
| PR-407 | MEDIUM | IN-SCOPE | D. Records integrity | `ce.check_lifecycle_transitions` returned "recorded lifecycle transition 'to-review' -> 'draft' is invalid: missing predecessor: backwards transition" once the review record was appended; `life._plan_status_event_groups` on the COMMITTED text gives one group with `ordered=False`, on the edited text `('2026-09-27', [draft, to-review], True)` plus the new date | **THE PLAN'S OWN HISTORY WAS ORDERED OLDEST-FIRST AND CARRIED A LATENT BACKWARDS TRANSITION**, silent only while every record shared one date. Appending any newer record makes it fire. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The two 2026-09-27 lines reordered to newest-first; `ce.check_lifecycle_transitions` returns ZERO drifts and `aw check` reports nothing against this plan. New F-19 records the general trap. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | PR-401: the id6 Deferred row names a real outstanding obligation and the plan declined to file it. File it at review, or leave the row uncarried? | FILE IT as backlog `y0t9u7` and point the row at it. | (a) Write `Carrier-Declined:` on it: rejected, and this is the one row where a decline would be a LIE. The obligation is real and measurable (17 of 17 id6 cells are `-`, with a working reader in `prompts.read_metadata_id6`), so declining would assert that nothing is owed when something is. (b) Leave it uncarried and report the blocker: rejected, the fix is one backlog item and the rule is an ERROR that blocks the plan's own gate; reporting a blocker I can correctly clear would waste a round trip. (c) Fold the id6 fix into this plan: rejected, it changes `--id` filter behavior and needs its own tests, exactly as the plan argues. | `aw check` / `evaluate_durable_carrier` naming the four rows; measured id6 dashes and `read_metadata_id6` output; the plan's own reasoning that filing is not authoring, which makes this the reviewer's act rather than the author's omission. | yes |
| D-2 | `y0t9u7` covers a `bug`. Should it carry `Blocks-Release: next`? | YES. | Omit the gate: rejected. The repository policy is that every live bug gates the next release, `find prompts` printing a dash in a column an operator reads is the same user-perceptible class as its sibling `yvcdw1` (which carries the gate), and omitting it would under-file a defect to make a queue look cleaner. | The every-live-bug-gates-the-next-release policy; sibling item `yvcdw1` carrying `- Blocks-Release: next` for the adjacent column; `next` resolving to the single `planned` release. | yes |
| D-3 | PR-404: OQ-01's first reason is false but its conclusion is right. Reverse the decision, or correct the justification? | CORRECT THE JUSTIFICATION, keep the decision. | Reverse to lane-first: rejected. Reasons two and three are independently sufficient and both verified (`scan_prompts` uses the identical order, and no row diverges today), and lane-first would also contradict the in-repo precedent for the same artifact type. Silently leaving the false reason: rejected, a plan whose recorded reasoning is wrong teaches the next reader the wrong thing even when its outcome is right. | Measured field mismatch (rule reads the comment, `aw find` reads the bullet); `prompts_index.scan_prompts`' fallback; F-05's zero-divergence measurement. | yes |
| D-4 | PR-407 arose from my OWN appended record. Fix the ordering, or leave it and report? | FIX IT. | Leave it: rejected. It is a two-line reorder in a section I was already editing, the newest-first convention is explicit, and leaving it would hand the executor a plan that fails `aw check` for a reason review created. Note the underlying defect was PRE-EXISTING (the committed text already read `to-review` -> `draft`); appending merely made it observable. | `ce.check_lifecycle_transitions` before and after; `_plan_status_event_groups` showing the committed group was `ordered=False`; the newest-first convention in the plan-review workflow. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`, including the BLOCKER, so no `- Blocking: yes` escalation under Step 4 is owed
either. OQ-01 remains `resolved` with a corrected first reason (D-3).

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`
  after all edits.
- `aw ipd lint --phase pre-transition --agent <plan>` -> BEFORE: 16 findings, 15 `IPD-S404` plus
  `check.ipd-uncarried-obligation`. AFTER: 15 findings, all `IPD-S404` (the expected unticked
  checkboxes), with the carrier rule ABSENT.
- `aw check --agent` -> BEFORE: this plan flagged `check.ipd-uncarried-obligation`. AFTER: this plan is
  flagged by NOTHING; the two remaining repository findings belong to other artifacts
  (`4er1ev`'s own carrier rule and `.aw/system/layout.json`).
- `check_engine.evaluate_durable_carrier(Path('.'), plan_path=..., plan_text=...)` -> BEFORE: one
  `error` drift, "4 obligation(s) name no durable carrier". AFTER: ZERO drifts.
- `check_engine.check_lifecycle_transitions(Path('.'))` -> AFTER appending the review record and BEFORE
  the reorder: one drift, "recorded lifecycle transition 'to-review' -> 'draft' is invalid". After the
  reorder: ZERO.
- `aw sanitize --agent` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- Lane input identity: `diff` of the `rev-13` lane input against the tracked plan -> no difference;
  `git status --short` clean before editing.
- **F-01 reproduced**: `aw find prompts --no-color | awk 'NF{print $1,$2}' | sort | uniq -c` ->
  `16 · -` and `1 ↪ superseded`.
- **F-02 reproduced** by reading the generic branch: `raw_status = sel_mod._read_status(text)` and
  `status = raw_status or "-"`, with no lane consultation.
- **F-03 / F-04 reproduced**: across all 17 `*.prompt.md`, 17 carry a first-line comment `Status:` and
  exactly 1 is visible to `selectors._read_status`, that one being
  `.aw/records/prompts/superseded/20260717-06nu85-01-06nu85-session-handoff-resume-here.prompt.md`.
- **F-05 / F-12 reproduced**: lane counts `{'executed': 13, 'pending': 2, 'superseded': 2}`, zero
  comment-versus-lane divergence. The `reusable/` and `not-executed/` lanes contain only `README.md`
  and `.gitkeep`, so they hold no prompt and constructed fixtures are genuinely required.
- **F-06 reproduced**: `aw find prompts --status pending` and `--status executed` each return 0 rows and
  print the empty-state block.
- **F-07 reproduced**: `_PROMPTS_PAIRS` maps all five lanes; and every lane word resolves natively,
  measured through `cli._find_resolve_lifecycle('prompts', ...)` -> `ready`, `done`, `reusable`,
  `superseded`, `abandoned`, with `-` and `''` -> `none`, and `walkthroughs` -> `none` for any value.
- **F-08 reproduced**: spec `uonrjg` 6.5's table header is literally "Native status or lane" with the
  five lane words mapped to the five stages, so this plan implements an approved spec.
- **F-09 reproduced**: `prompts.py` defines `PROMPT_KINDS`, `DEFAULT_STATUS`, `PENDING_BUCKET`; no
  `STATUSES`; `_find_valid_statuses('prompts')` is `None` while `plans`/`specs`/`backlog` return sets.
- **F-10 reproduced**: `from agent_workflows.attention import _prompt_disposition_from_rel` inside
  `check_engine`.
- **F-11 reproduced**: no test asserts this column; `tests/test_cli_find.py`'s only prompts mention is
  a `record_dirs` assertion.
- **F-13 reproduced**: `rg -rn "directory_derived" tests/` matches ONE line, the comment itself.
- **F-14 reproduced**: `aw find prompts --json` `data.matches` carries
  `'·  -             -  .aw/records/prompts/executed/...'`, so the dash is in the machine surface.
- **F-15 reproduced**: `prompts_index.scan_prompts` line reading `status = meta.get("Status") or
  disposition`.
- **Helper choice verified sharding-safe**: `_prompt_disposition_from_rel` returns `pending` for a
  plain lane path, `executed` for `.aw/records/prompts/executed/202609/x.prompt.md`, and `''` for both
  a no-lane prompts path and a `walkthroughs` path.
- **The rejected helper verified wrong as the plan says**: `ipd_lint._dir_of` iterates
  `_LD.LIFECYCLE_SUBDIRS["plans"]` and tests `anchor in parts`; `LIFECYCLE_SUBDIRS['prompts']` and
  `['plans']` are independently-owned but currently identical tuples, and `PROMPT_LANES` equals the
  prompts tuple as a set.
- Suite baselines: bare `python3 -m pytest` -> `2935 passed, 2 skipped, 3 warnings`;
  `tests/test_lifecycle_style.py -o addopts=""` -> `12 passed`; the six-file neighbour set -> `42
  passed`. All six neighbour files exist.
- Filed during review: backlog `y0t9u7`
  (`.aw/records/backlog/open/20260928-y0t9u7-01-y0t9u7-find-prompts-id6-always-dash.backlog.md`),
  measured id6 evidence, `Blocks-Release: next`, carrier for this plan's first Deferred row.
