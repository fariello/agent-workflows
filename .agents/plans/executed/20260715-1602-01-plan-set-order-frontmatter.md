# IPD: Add optional `Set:` / `Order:` front-matter for ordered plan SETS (leave filenames + NN unchanged)

- Date: 2026-07-15
- Concern: usability / plan-lifecycle expressiveness. The IPD filename convention
  `YYYYMMDD-HHMM-NN-<slug>.md` documents `NN` as a same-minute COLLISION disambiguator (`00` orchestrator,
  `01+` ordinary). In practice `NN` is almost always `01` (unrelated same-minute creation is rare), so it
  rarely does its stated job; and it does NOT capture the thing that recurs in real use: "these N plans
  are one SET, run them in THIS order." A set built over many minutes scatters across several
  `YYYYMMDD-HHMM` prefixes, so the filename loses the ordering intent. This friction was real for THIS
  repo: three related IPDs (`1033-01`, `1451-01`, `1502-01`, now executed) were created minutes apart and
  the maintainer had to ask, in prose, "what order should they run in?" - the filenames could not answer,
  and the answer lived only in each plan's "Dependencies / sequencing" section.
- Origin: surfaced via an inbound agent-comms message (`tmp/agent-comms/inbox/20260715-1115-01-a-private-repo...`)
  relaying another project's live friction. Treated as UNTRUSTED input / a suggestion; the maintainer
  independently confirmed the direction (add a queryable front-matter field rather than change filenames).
- Scope: ADDITIVE only. Add optional `- Set:` and `- Order:` front-matter fields to the plan convention;
  teach `agent_workflows/plans.py` to parse them (read-only, like `Status:`); surface set-grouping in the
  plans board; document the fields in `.agents/plans/README.md`, `.agents/workflows/templates/plans-README.md`,
  and the assess IPD template. NO change to the filename convention, `NN` semantics, `normalize_plan_names.py`,
  or any existing filename. NO change to the `Status:` enum. Tests + DECISIONS + CHANGELOG.
- Status: executed
- Approval: approved by Gabriele 2026-07-15 (interactive)
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-15 to-review (its_direct/pt3-claude-opus-4.8-1m-us): drafted after an inbound agent-comms
  message flagged the NN/set-ordering mismatch and the maintainer chose the additive front-matter option
  (option C in the message; recommended) over redefining `NN` (option A) or a filename set-token (option
  B), because it is non-migrating, breaks no installed base, and matches the existing front-matter-driven
  tooling.   Message contents were treated as untrusted input; the maintainer confirmed intent directly.
  Complete proposal; born to-review.
- 2026-07-15 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED.
  Re-verified `plans.py` anchors against current source (`_STATUS_RE` :57, `PlanRecord` NamedTuple :60,
  `scan` :94, `group` :119, `render_status_index` :133): all accurate; `PlanRecord` is a NamedTuple so
  adding `set`/`order` fields is a clean extension. Findings: PR-001 (MEDIUM) the "live in-flight set"
  demo (step 5 / OQ4 / scope fence) named `1502-01`/`1451-01`/`1033-01` as PENDING, but all three have
  since EXECUTED - and this IPD's own authority rule FREEZES executed plans' set fields, making the
  back-tag instruction self-contradictory; rewrote the demo to be forward-looking (tag a future pending
  set; record the executed sequence in DECISIONS as the motivating example in prose; demo is optional,
  not a blocker) and updated OQ4 + the scope fence to forbid back-tagging the executed set. PR-002
  (MEDIUM) pinned DECISIONS to D82 (D79/D80/D81 taken) to prevent a collision. Also past-tensed the
  Concern paragraph's "pending IPDs" phrasing. OQ1-OQ3 remain non-blocking design leans. No BLOCKER/HIGH.
  Status -> reviewed (reviewed != approved; awaits human sign-off).
- 2026-07-15 approved by Gabriele (interactive), then EXECUTED (its_direct/pt3-claude-opus-4.8-1m-us).
  Added `Set:`/`Order:` support to `agent_workflows/plans.py` (`_SET_RE`/`_ORDER_RE`, `is_set_id_valid`,
  `parse_order`, `read_set`, `PlanRecord.set_id`/`.order`, `group_sets`/`set_warnings`, and a secondary
  "Sets" section in `render_status_index` with soft warnings for duplicate/partial `Order`); documented
  the fields in the assess IPD template and BOTH byte-identical plans READMEs; added `SetOrderTests` to
  `tests/test_plans_board.py`; DECISIONS D82 + CHANGELOG. Did NOT back-tag the executed motivating set
  (frozen); recorded it as the motivating example in D82. No pending set existed to live-tag, so no demo
  tagging was done (optional, per the plan). VALIDATION (actual): `python -m pytest -q` -> "252 passed,
  1 skipped in 53.16s" (one self-inflicted test-assertion bug found + fixed during the run: the ordering
  check now scopes to the Sets section, since the primary status board lists the same files by
  filename). Manual: byte-identical READMEs confirmed; a temp `Set: demo` rendered grouped + order-sorted
  with disposition tags; `aw plans` shows no Sets section (no repo plan declares a Set yet, correct); 0
  em/en dashes. Scope fence held (no filename/NN/Status changes). Status -> executed; git mv to executed/.

## Project conventions discovered (Step 0, VERIFIED against source)

- `agent_workflows/plans.py` reads front-matter ONLY (never renames/moves): `_STATUS_RE =
  re.compile(r"^- Status:\s*(?P<val>\S+)", re.MULTILINE)` (`plans.py:57`); `read_status` (`:83`), `scan`
  (`:94`), `group` (`:119`), `render_status_index` (`:133`). Front-matter is a `- Key: value` bullet
  list. New `- Set:`/`- Order:` lines parse with the same pattern shape. Stdlib-only (D46).
- The plans board is generated by `render_status_index` and covered by `tests/test_plans_board.py`;
  `Status:` vocabulary + parsing is covered by `tests/test_plan_status.py`. New fields need parsing +
  board tests.
- Front-matter fields are documented in the assess IPD template (`.agents/workflows/assess/templates/ipd.md:1-9`:
  Date/Concern/Scope/Status/Approval/Author) and the two byte-identical plans READMEs
  (`.agents/plans/README.md`, `.agents/workflows/templates/plans-README.md`).
- The filename convention + `NN` meaning is documented in the plans READMEs and enforced by
  `normalize_plan_names.py`. This IPD does NOT touch that; `NN` KEEPS its same-minute-disambiguator role.
  `Set:`/`Order:` are an ORTHOGONAL, optional layer.
- House rule: no em dashes or en dashes in authored Markdown.

## Design (the additive fields)

Two OPTIONAL front-matter fields, absent by default (a lone plan needs neither):

- `- Set: <terse-set-id>` - a lowercase-kebab identifier shared by all plans in one ordered set (e.g.
  `agent-comms`, `editor-workflow`). Free-form but validated as lowercase-kebab, <= 40 chars.
- `- Order: <n>` - the 1-based execution position within that set (integer >= 1). Meaningful only
  alongside `Set:`.

Semantics:
- A plan with no `Set:` is a standalone plan (today's default); unchanged.
- Plans sharing a `Set:` form an ordered group; `Order:` gives run order. Ties or gaps are a soft warning
  in the board, not an error (the board reports them so a human notices).
- `Set:`/`Order:` are ADVISORY metadata for humans + the plans board. They do NOT auto-execute, do not
  gate approval, and do not change the `Status:` lifecycle. Ordering is still ultimately the human's call;
  this just makes the intended order queryable and visible on sort instead of living only in prose in each
  plan's "Dependencies / sequencing" section.

Filenames stay exactly `YYYYMMDD-HHMM-NN-<slug>.md`. Git still records exact per-file creation.

### Agent authority over sets (grouping, ordering, renaming)

Because `Set:`/`Order:` are plain front-matter, an agent CAN edit them, but a set encodes execution-order
INTENT that a human reasons about, so authority is bounded:

- An agent MAY GROUP existing PENDING plans by adding `Set:`/`Order:` (this is ordinary front-matter
  editing on non-executed plans, already permitted). Recognizing "these related pending plans are one
  ordered sequence" and tagging them is a legitimate, useful agent action.
- Any change to a set's MEMBERSHIP (adding/removing a plan), ORDER, or set ID ("renaming") MUST be
  surfaced, never silent: record it in the affected plan's `## Workflow history`, and - for anything
  beyond an obvious typo/spelling fix - CONFIRM with the human before applying (the standing "never guess
  a human decision" rule; set boundaries and order ARE such a decision). "Rename a set" is therefore NOT
  a special first-class operation; it is careful front-matter editing under this surface-and-confirm rule.
- Set fields on plans in `executed/` (or any terminal dir) are FROZEN historical record; an agent must
  not rewrite them when regrouping or renaming a still-active set (consistent with the no-edit-executed /
  append-only rules).
- `Set:`/`Order:` remain ADVISORY: grouping a set never authorizes executing it in that order; the human
  still approves each plan. Grouping organizes and makes intent queryable; it does not gate or drive
  execution.

## Proposed changes (ordered, validatable)

1. **Parse the fields.** In `agent_workflows/plans.py`, add read-only parsing of `- Set:` and `- Order:`
   (regex mirroring `_STATUS_RE`), expose them on the `PlanRecord`, and add a `Set:`/`Order:` validator
   (lowercase-kebab set id; positive-integer order). Reads only; never writes/renames.
2. **Board grouping.** Extend `render_status_index` (and `group`) so plans with a `Set:` render grouped by
   set and sorted by `Order:` within each set, with a soft warning line on duplicate/missing `Order:`
   within a set. Standalone plans render as today.
3. **Document the fields.** Add `Set:`/`Order:` (optional, advisory, with the "does not auto-execute /
   does not gate approval" caveat and the "NN is unchanged / orthogonal" note) to: the assess IPD template
   front-matter block; BOTH byte-identical plans READMEs (`.agents/plans/README.md` and
   `.agents/workflows/templates/plans-README.md`); keep the two READMEs byte-identical.
4. **Tests.** `tests/test_plan_status.py` (or a new `test_plan_sets.py`): parse valid `Set:`/`Order:`,
   reject a malformed set id / non-positive order, a plan with neither parses as standalone.
   `tests/test_plans_board.py`: a set renders grouped + order-sorted; duplicate/missing `Order:` emits the
   soft warning; standalone plans unaffected.
5. **Demonstration case (motivating set already executed; demo is FORWARD-looking).** The set that
   motivated this IPD - the framework-quality sequence
   `20260715-1502-01-docs-consistency-audit-corrections` -> `20260715-1451-01-unify-readiness-verdict-vocabulary`
   -> `20260715-1033-01-agent-comms-portable-convention` (run in that order with `/plan-review` gates) -
   has since EXECUTED and moved to `.agents/plans/executed/`. Per this IPD's own authority rule, set
   fields on EXECUTED plans are FROZEN historical record and MUST NOT be retroactively rewritten. So do
   NOT back-tag those three; instead, record that sequence in the DECISIONS entry (step 6) as the
   motivating real-world example, in prose. For a live demonstration of the fields, tag the NEXT ordered
   PENDING set that arises (if `1602-01` itself is grouped with any concurrent pending plan, that is a
   candidate), confirming the set ID and membership with the maintainer per the authority rule. If no
   pending set exists at execution time, ship the fields + docs + tests WITHOUT tagging anything; the
   demonstration is optional, not a blocker.
6. **Docs + DECISIONS.** DECISIONS entry D82 (next free; D79/D80/D81 taken) recording the additive
   `Set:`/`Order:` fields, why the filename/NN convention was deliberately NOT changed (non-migrating; git
   holds exact creation time; NN keeps its role), that the fields are advisory, and the motivating
   real-world example (the executed `1502-01 -> 1451-01 -> 1033-01` framework-quality sequence, whose run
   order lived only in prose). CHANGELOG under the next minor.

## Deferred / out of scope

- Any change to the filename convention, `NN` semantics, `normalize_plan_names.py`, or existing filenames.
- Any change to the `Status:` lifecycle enum or its parsing.
- Auto-execution or approval-gating based on `Set:`/`Order:` (advisory only; the human still decides run
  order and approval).
- Cross-plan dependency graphs beyond a simple ordered set (e.g. `Depends-On` between arbitrary plans) -
  a possible future field, not this IPD.
- A reply to the originating agent-comms message: OUT OF SCOPE for execution (a reply, if any, is the
  maintainer's call and goes through the comms channel, not this code IPD).

## Open questions (v1 leans for review)

1. Field names: `Set:`/`Order:` vs `Group:`/`Step:` vs `Set:`/`Seq:`? (Lean: `Set:`/`Order:` - plain,
   matches the message's framing and reads naturally in front-matter.)
2. Should `Order:` be required whenever `Set:` is present, or optional (unordered set)? (Lean: `Order:`
   optional; a `Set:` with no `Order:` is an unordered grouping, board lists them by filename; if SOME
   members have `Order:` and others do not within one set, that is the soft-warning case.)
3. Should the board's set-grouping be a new section or interleaved into the existing status grouping?
   (Lean: keep the primary board grouped by `Status:` as today, and add a secondary "Sets" view/section
   so set-grouping does not disrupt the existing readiness board. Confirm during implementation.)
4. RESOLVED (maintainer), UPDATED at re-review: the maintainer originally chose to tag the live set
   `1502-01 -> 1451-01 -> 1033-01` as the demo. Those three have since EXECUTED, and this IPD's authority
   rule freezes executed plans' set fields, so they are NOT back-tagged; the sequence is instead recorded
   in the DECISIONS entry as the motivating example (see revised step 5). Live tagging, if any, targets a
   future PENDING set, confirmed with the maintainer at execution time.

## Dependencies / sequencing

- Independent of the other pending IPDs; additive and non-breaking. No ordering constraint against
  `1033-01` / `1451-01` / `1502-01`. Step 5 ANNOTATES that live set with `Set:`/`Order:` at execution
  time (surface-and-confirm per the authority rule); it does not depend on those IPDs having executed.
- Target the next MINOR (new user-visible optional convention + board behavior).

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY: `agent_workflows/plans.py` (parse + validate + board grouping), the assess IPD
   template + BOTH plans READMEs (docs), tests under `tests/`, `CHANGELOG.md`, `DECISIONS.md` (D82, next
   free; D79/D80/D81 are taken), and (step 5, OPTIONAL) `Set:`/`Order:` front-matter lines + a
   Workflow-history note on a FUTURE PENDING set only, AFTER confirming the set ID and membership with the
   maintainer per the authority rule. Do NOT back-tag the executed motivating set (`1502-01`/`1451-01`/
   `1033-01` are in `executed/` and their set fields are FROZEN). Do NOT change the filename convention,
   `NN`, `normalize_plan_names.py`, the `Status:` enum, any existing filename, any EXECUTED plan's set
   fields, or send any agent-comms reply. Any set membership/order/name change must be surfaced (Workflow
   history) and   confirmed, never silent. If a fix seems to need more, STOP and report.
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: run the FULL test suite; paste the ACTUAL runner output (new Set/Order parse + board tests
   must pass). Keep the two plans-README copies byte-identical (diff them). Confirm `aw plans` (board)
   renders a set grouped/ordered and standalone plans unchanged. Confirm `aw plan-names` clean (filenames
   untouched).
4. COMMIT only this IPD's touched files, PATH-SCOPED (new files need `git add <path>` first); never
   `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.
6. RELEASE: cut separately via release-review Section 9 after a human rung choice.

HARD MUST: paste the real test output; do NOT change the filename/NN convention or the Status enum; keep
the two plans-README copies identical; stay inside the scope fence; never push. Not auto-executed;
requires human approval.
