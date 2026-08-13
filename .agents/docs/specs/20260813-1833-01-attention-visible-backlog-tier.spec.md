# Spec: an attention-visible backlog tier (`records/backlog/` + `aw backlog`)

- Date: 2026-08-13
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: `aw attention` (D125) is the deterministic, on-demand answer to "what needs attention across the repo?" and feeds `/whatnext`, but it scans ONLY status-bearing trees (plans, specs, research, actions). Committed work captured in the free-prose `TODO.md` is therefore SILENTLY omitted from the view. A tool that looks comprehensive but omits a whole class of pending work creates false confidence: relying on `aw attention` misses `TODO.md`; relying on `TODO.md` misses the attention view. The maintainer flagged this as a real risk.
- Relation to prior work: EXTENDS D125 (adds a new attention adopter). Mirrors the already-shipped `actions` tree mechanism (a tracked, lightweight, status-by-directory tree mapped into `aw attention` via `attention_contract.CLASS_MAPS`). Reuses `agent_workflows/artifact_core.py` (id6, atomic write, the `Drift`/`--check` convention) and the `aw specs`/`aw research` verb pattern.

## 1. One-line summary

Add a lightweight, tracked BACKLOG artifact type as a `records`-class sub-tree `records/backlog/{open,blocked,parked,done}/` (one small frontmatter+prose file per item) and make it an `aw attention` adopter, so COMMITTED backlog items ("we must / we should do this") surface as `ready` in `aw attention` + `/whatnext`, while explicitly-uncommitted "maybes" are tracked-but-quiet and pure "notes" stay out entirely. This closes the false-comprehensiveness gap without imposing IPD ceremony on backlog capture. LOCATION (resolved OQ7, review PR-004): the backlog is a `records` artifact (project work created by humans/workflows, physical spec 20260810-1447-01 line 71 places plans/specs/research/prompts/comms/runs under `records/`), NOT `.agents/` (which the awphysical migration retires, D130) and NOT `state/` (AW-operational only, D126). So it materializes at `.agents/backlog/` PRE-migration and `.aw/records/backlog/` POST-migration, exactly like `plans` (`.agents/plans` -> `.aw/records/plans`); `attention._classify_tree` already normalizes `.aw/records/` -> `.agents/`, so one TreePolicy rooted at the records `backlog/` path covers both.

## 2. Problem / motivation

- `aw attention` tracks plans/specs/research/actions (D125; `attention_contract.CLASS_MAPS`). `TODO.md` is a free-prose file with no per-item machine-readable status, so it is invisible to the view and to `/whatnext`.
- `TODO.md` today mixes THREE commitment levels that must not be treated alike: committed work ("Known bugs to fix", "Security follow-ups", "Planned next: designed, deferred"), explicitly-uncommitted ideas ("Consider and possibly implement (may be declined)"), and pure "Notes". Roughly half is committed, half is maybe.
- The two failure modes to avoid are SYMMETRIC: (a) omitting committed work from `aw attention` (today's bug: false confidence, an eternally growing `TODO.md` nobody reads); (b) flooding `aw attention` with every "meh, maybe someday" idea (would make the view noise and destroy its meaning). The fix must distinguish COMMITMENT LEVEL and surface only the committed tier.
- IPD stubs are the WRONG home for most backlog: a draft plan carries id6-in-filename, an E/V bijection, lint gates, and a full lifecycle - far too much ceremony for "we should fix this bug" and it would flood the plan tree. D52's "born to-review, draft is opt-in" line and the D39 distinction between "concrete units of work" and "open-ended backlog" already establish that not everything belongs in the plan lifecycle.

## 3. The three-tier model

- Tier 1 - COMMITTED ("we must / we should"): needs attention -> MUST surface in `aw attention` (class `ready`).
- Tier 2 - UNCOMMITTED ("consider; may be declined"): tracked but MUST NOT clutter the actionable view -> present in the full `aw attention --format json` but excluded from the human hot glance (class `parked`).
- Tier 3 - NOTES (context, not work): NOT a backlog item at all; stays prose (e.g. a `## Notes` section of `TODO.md` or a doc). Never in the view.

Commitment level is orthogonal to urgency: a `priority` axis (high/medium/low = "must/should/meh-but-committed") orders items WITHIN Tier 1; it is a sort hint, not an attention class.

## 4. Goals

- G1 `[Must]` Add a tracked backlog artifact type as the `records`-class sub-tree `backlog/{open,blocked,parked,done}/` (materializing at `.agents/backlog/` pre-migration, `.aw/records/backlog/` post-migration, like plans), one file per item, each carrying a machine-readable frontmatter status.
- G2 `[Must]` Make `backlog` an `aw attention` adopter via a `_BACKLOG_MAP` fragment in `attention_contract.CLASS_MAPS`: `open -> ready`, `parked -> parked`, `done -> done`. Committed (`open`) items thus appear in the view + `/whatnext`; `parked` items are in JSON but out of the hot glance (exactly like `archive` research).
- G3 `[Must]` Provide `aw backlog` verbs mirroring `aw research`/`aw specs`: at least `new` (create a conformant item, dry-run by default), `set` (transition open/parked/done + append history), `check` (validate the tree against the contract, fail closed), and `index`/`find` if a manifest is warranted (OQ5).
- G4 `[Must]` Keep capture cheap: creating a backlog item is one `aw backlog new --summary ... --priority ... --kind ...` command (or dropping a conformant file), with NO id6-in-filename ceremony, NO E/V bijection, NO lint-phase gates.
- G5 `[Must]` Migrate the existing `TODO.md` (resolved OQ1): committed sections (Known bugs to fix, Security follow-ups, AND "Planned next: designed, deferred" - the committed-next queue) -> `backlog/open/` (or `backlog/blocked/` if an item names a gate); "Consider and possibly implement (may be declined)" -> `backlog/parked/`; "Notes" stays prose. `TODO.md` is then either retired or reduced to a pointer at the backlog tree + the Notes section.
- G6 `[Should]` `/whatnext` consumes the backlog `ready` items (it already consumes `aw attention --format json`, so this is automatic once G2 lands) and a CI `aw backlog check` fail-closed gate exists (like `aw specs check`).
- G7 `[Must]` Stdlib only; zero runtime deps; Python 3.9; ships in the importable package as `aw backlog` and `python -m agent_workflows backlog`.

## 5. Non-goals

- NOT replacing plans/specs/research. A backlog item that becomes real execution work is PROMOTED to a plan (a backlog item may cite the plan and move to `done`); the backlog is the pre-plan capture tier, not a competing plan lifecycle.
- NOT a priority/urgency SCHEDULER; `priority` is a sort hint only.
- NOT importing in-code `TODO`/`FIXME` comments (that remains a `release-review` concern, D39).
- NOT adding a new attention CLASS; backlog reuses the existing five (`ready`/`active`/`blocked`/`done`/`parked`).

## 6. Functional design

### 6.1 On-disk layout and item format

The tree is the `records`-class `backlog/` sub-tree (dual path like plans: `.agents/backlog/`
pre-migration, `.aw/records/backlog/` post-migration):
```
<records-root>/backlog/
  open/        Tier-1 committed, actionable now   (attention: ready)
  blocked/     Tier-1 committed but gated          (attention: blocked; + Gate-Kind/Gate-Ref)
  parked/      Tier-2 uncommitted "maybes"         (attention: parked)
  done/        completed/closed items              (attention: done)
  README.md
```

Status is encoded BOTH by directory (disposition, like `plans/`) and by a bare-enum frontmatter `status` (the machine-readable source of truth mapped by `class_of`), and the two MUST agree (a `check` rule, mirroring "Status mirrors dir" for plans/specs). One item is one file:

```markdown
---
id: <id6>                 # stable base36 handle, never changes (artifact_core)
created: <YYYYMMDD>
status: open              # open | blocked | parked | done  (bare enum; owned by `aw backlog set`)
set: <terse-id>           # grouping key from v1 (a singleton is a set of one); clustering filename
priority: high            # high | medium | low     (sort hint within a class; not a class)
kind: bug                 # bug | feature | chore | security | followup
summary: <one line>       # the glanceable line aw attention/whatnext show
# gate-kind / gate-ref REQUIRED together iff status == blocked (typed gate, like specs):
gate-kind: <spec|plan|external|date>   # only when blocked
gate-ref: <id6|path|iso-date>          # only when blocked
---
Free-form prose body: description, links to DECISIONS/commits/specs, acceptance notes.
```

Status enum (resolved OQ3): `open | blocked | parked | done`. `blocked` = a Tier-1 COMMITTED item waiting on a NAMED gate; it REQUIRES a typed `gate-kind`/`gate-ref` pair (mirroring the specs `Gate-Kind`/`Gate-Ref` contract) and maps to the attention `blocked` class, so a committed-but-gated item is neither mislabeled `open` (falsely actionable-now) nor hidden in `parked` (falsely uncommitted).

Filename grammar (clustering, consistent with plans/research; resolved OQ6): `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md`, and the item carries a `set:` frontmatter field FROM v1 (a singleton is a set of one, never special-cased). `aw backlog new` owns the name + frontmatter (no hand-naming, per the plans/research rule).

### 6.2 Attention integration (the D125 extension) - FOUR touch-points, not one

Making `backlog` an `aw attention` adopter is MORE than a single contract line. Verified against
the code (review PR-001): `aw attention` discovery is NOT generic - `attention.scan()` dispatches
per-tree with bespoke logic and `attention._classify_tree` matches a file to a `TreePolicy` root, so
a `CLASS_MAPS` fragment alone would leave backlog files UNCLASSIFIED and unscanned. The executor MUST
edit all four:

1. `agent_workflows/attention_contract.py`: add the mapping fragment and register it -
   ```python
   _BACKLOG_MAP = {"open": READY, "blocked": BLOCKED, "parked": PARKED, "done": DONE}
   CLASS_MAPS["backlog"] = _BACKLOG_MAP
   ```
   AND add a `TreePolicy("backlog", ".agents/backlog", <owner-managed?>, "aw backlog", "...")` to
   `TREE_POLICY` so `_classify_tree` recognizes the root and its native-status enum. Root the policy
   at the records `backlog/` path; since `_classify_tree` normalizes `.aw/records/` -> `.agents/`, a
   single `.agents/backlog` policy root matches BOTH the pre-migration `.agents/backlog/` and the
   post-migration `.aw/records/backlog/` (identical to how `plans` is handled today).
2. `agent_workflows/artifact_core.py`: add the backlog root(s) to `SCAN_ROOTS` (both `.agents/backlog`
   and `.aw/records/backlog`, mirroring how plans lists `.agents/plans` AND `.aw/records/plans`) so
   `iter_scan_files` discovers the items on either layout. (NOTE: `SCAN_ROOTS` already lists `TODO.md`,
   but `_classify_tree` returns None for it - it has no `TreePolicy` root - which is exactly why TODO.md
   is read-but-ignored today; PR-003.)
3. `agent_workflows/attention.py`: add a `backlog` branch in `_record_for` + a `_backlog_record`
   builder (mirroring `_plans_record`/`_research_record`) that reads the frontmatter `status`,
   `priority`, `summary`, and id; and ensure `scan()` routes backlog files to it.
4. Docs/tests per Sections 7-9.

The mapping is PURE and TOTAL over the backlog status enum (D125 Section 6 invariant):
`class_of("backlog", status)` depends only on `(tree, status)`; an unknown status is the
`attention.unknown-status` violation, never a default. `priority` is carried into the JSON and used
to order the `ready` list (high first); it is NOT a class. (The `actions` tree uses a SEPARATE bespoke
scan path in `attention.py`; backlog should instead go through the standard `iter_scan_files` +
`_classify_tree` + `_record_for` path since it is a `records`-class tracked tree like plans, not
`state` operational state - see OQ7.)

### 6.3 CLI

`aw backlog new|set|check`, wired at the two `cli.py` edit points, mirroring `aw research`/`aw specs`. `new` creates a conformant item (dry-run by default), owning the clustering name + frontmatter (id6, set, status, priority, kind, summary). `set` moves the file between `open/blocked/parked/done`, updates the frontmatter `status` (and requires `gate-kind`/`gate-ref` when moving to `blocked`), and appends a `## Workflow history` line (append-only provenance, D52 style). `check` validates: frontmatter present + valid enums, status-mirrors-directory, `gate-kind`/`gate-ref` present iff `blocked`, id6 present/unique, `summary` nonempty; fail closed with the `Drift`/`--agent`/exit convention. (No `index`/`find` in v1 per OQ5.)

Additionally on the attention surface (resolved OQ2): add `aw attention all` (reveals `parked`/archived-tier items that the default board hides) and an `aw att` alias for `aw attention`. Both are small `cli.py` edits bundled with this work.

## 7. Convention / docs change

- AGENTS.md: add a short pointer that COMMITTED backlog lives in the `records` `backlog/` tree (surfaced by `aw attention`), and that `TODO.md` (if kept) holds only uncommitted notes.
- `.agents/docs/specs/README.md` / the attention docs: note `backlog` as an attention adopter (extends D125).
- A new `backlog/README.md` (in the records backlog tree) documenting the tiers, format, and `aw backlog` verbs.
- DECISIONS: a new entry recording the three-tier model + backlog-as-attention-adopter (revising D125's adopter set), created when this ships.

## 8. Requirements

- F1 The `records`-class `backlog/{open,blocked,parked,done}/` tree (dual path `.agents/backlog/` pre-migration, `.aw/records/backlog/` post-migration) with the item format of Section 6.1; `blocked` items carry a typed `gate-kind`/`gate-ref`.
- F2 The FOUR attention touch-points of Section 6.2 are all implemented (mapping + `TreePolicy` in `attention_contract.py`; `SCAN_ROOTS` in `artifact_core.py`; `_backlog_record` + `scan` routing in `attention.py`; docs/tests), so `aw attention` classifies and includes backlog items; `ready` (open) items appear in the hot glance and `/whatnext`, `parked` only in JSON. A `CLASS_MAPS` edit ALONE is insufficient and MUST NOT be treated as the whole change.
- F3 `aw backlog new|set|check` implementing capture (owning the clustering name + `set`/`priority`/`kind` frontmatter), status transitions + history (incl. the `blocked` typed-gate rule), and fail-closed validation, stdlib-only, `--agent` + exit convention on `check`. PLUS `aw attention all` (reveal parked) and the `aw att` alias (OQ2).
- F4 `TODO.md` migration per G5; `TODO.md` retired or reduced to a pointer + Notes.
- F5 status-mirrors-directory + pure/total mapping enforced (a `check` rule + a contract test).
- N1 stdlib only, zero deps, Python 3.9. N2 ships as `aw backlog`. N3 reuses `artifact_core` + the attention contract; no fork. N4 no em/en dashes in authored user-facing output.

## 9. Acceptance criteria

- A1 An `open/` backlog item appears in `aw attention` (and `aw attention --format json`) with class `ready`; the same item after `aw backlog set --status parked` appears with class `parked` and drops OUT of the human hot glance while remaining in JSON.
- A2 A `done/` item maps to `done`.
- A3 `aw attention --check` stays clean with backlog items present; an item with an invalid/missing `status` produces `attention.unknown-status` (fail closed), never a silent default.
- A4 `/whatnext` surfaces `open` backlog items (via the existing JSON consumption) - i.e. the tool is no longer silently incomplete.
- A5 `aw backlog check` fails closed on a malformed item (missing frontmatter, bad enum, status-vs-directory mismatch, missing/duplicate id6, empty summary) and exits 0 on a clean tree; `--agent` emits tab-separated records.
- A6 After the `TODO.md` migration, every previously-committed TODO item is an `open`/`parked` backlog file, `aw attention` shows the committed ones, and `TODO.md` no longer holds committed work.
- A7 Full unittest suite green with new tests: the `_BACKLOG_MAP` purity/totality, the attention inclusion + hot-glance/JSON split, and the `aw backlog` verbs incl. `check` fail-closed cases.

## 10. Constraints and dependencies

- Depends on `artifact_core` (SCAN_ROOTS, iter_scan_files), `attention_contract` (TREE_POLICY + CLASS_MAPS, D125), and `attention.py` (scan/_classify_tree/_record_for) - the attention integration spans all three modules (Section 6.2), not one line. The rest is a conventional new tree + `aw backlog` verbs (none today). The migration (G5) must not lose any committed item. Verified review evidence: `attention_contract.py:83 TREE_POLICY`, `attention_contract.py:232 CLASS_MAPS` + `:224 _ACTIONS_MAP`, `attention.py:86 scan` + `:47 _classify_tree` + `:208 _record_for`, `artifact_core.py:157 SCAN_ROOTS` (already lists TODO.md, unclassified).

## 11. Risks and open questions

Review findings (2026-08-13 /plan-review), all FIXED in place: PR-001 (HIGH) the attention
integration is FOUR touch-points (attention_contract TREE_POLICY + CLASS_MAPS, artifact_core
SCAN_ROOTS, attention.py scan/_record_for), not a single `CLASS_MAPS` line - Section 6.2 rewritten.
PR-002 (LOW) location interacts with `_classify_tree` normalization - folded into OQ7. PR-003 (LOW)
`SCAN_ROOTS` already lists `TODO.md` but it is unclassified (evidence the gap is real) - noted in 6.2.
PR-004 (HIGH) the original draft rooted the tree at `.agents/backlog/`, contradicting the awphysical
migration (D130) that RETIRES `.agents/`; corrected to the `records`-class `backlog/` sub-tree
(records = human/workflow project artifacts, physical spec line 71), dual-path like plans. OQ1/OQ3/OQ7
resolved with the maintainer during review (below).

- OQ1 RESOLVED (2026-08-13 /plan-review, human maintainer): "Known bugs" + "Security follow-ups" + "Planned next (designed, deferred)" are ALL Tier-1 `open` (the committed-next queue); "Consider / may be declined" is Tier-2 `parked`; "Notes" is Tier-3 prose. (An `open` item that names a gate goes to `blocked` instead.)
- OQ2 RESOLVED (2026-08-13 /plan-review, human maintainer): `parked` items are EXCLUDED from the human `aw attention` hot glance, PRESENT in `aw attention --format json`, and revealed on demand by a new `aw attention all` sub-invocation (reveals parked/archived-tier items). Matches the `archive` research precedent. ALSO (maintainer add): alias `aw att` -> `aw attention` (the tool is invoked constantly; a short alias reduces friction). Both the `all` reveal and the `att` alias are in scope for the implementing IPD.
- OQ3 RESOLVED (2026-08-13 /plan-review, human maintainer): ADD `blocked` in v1. A committed-but-gated item uses `status: blocked` with a REQUIRED typed `gate-kind`/`gate-ref` pair (mirroring the specs gate contract), mapping to the attention `blocked` class. Statuses are `open | blocked | parked | done`.
- OQ4 RESOLVED (2026-08-13 /plan-review, human maintainer): when a backlog item becomes a plan, `aw backlog set --status done` and append a workflow-history line citing the plan's id6 (e.g. "promoted to plan <id6>"). No new status; the backlog captured the intent, the plan now owns execution.
- OQ5 RESOLVED (2026-08-13 /plan-review, human maintainer): NO manifest in v1. Ship the directory tree + frontmatter + `aw attention` integration + `aw backlog new/set/check` only. Add `aw backlog index/find` + an `INDEX.json`/`--check` in a later phase ONLY if backlog items start being cited by id6 or the corpus grows large.
- OQ6 RESOLVED (2026-08-13 /plan-review, human maintainer): `priority` = `high|medium|low`. AND carry a `- Set:` grouping FROM v1 (maintainer chose to include Set from the start, over the leaning to defer it): a backlog item has a `set` field + the clustering filename grammar `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md` (a singleton is a set of one, never special-cased), mirroring plans/research so related backlog items cluster in a name-sorted tree and can be regrouped citation-safely. `aw backlog new` owns the name/frontmatter (no hand-naming), and (if/when a manifest lands, OQ5) `set-assign`/`mv` regroup.
- OQ7 RESOLVED (2026-08-13 /plan-review, human maintainer flagged that `.agents/` is being retired by the awphysical migration - review PR-004): the backlog is a `records`-class sub-tree `backlog/`, NOT `.agents/backlog/` (retired by D130) and NOT `state/` (AW-operational only, D126). The physical spec 20260810-1447-01 (line 71) places plans/specs/research/prompts/comms/runs under `records/`; a backlog is the same kind of human/workflow-produced project artifact, so it belongs in `records/`. It materializes at `.agents/backlog/` pre-migration and `.aw/records/backlog/` post-migration (dual path like plans), and `attention._classify_tree`'s `.aw/records/` -> `.agents/` normalization means one TreePolicy root covers both.

## 12. Out-of-scope / future

- Auto-triage or auto-classification of backlog items (kept human-curated).
- Importing in-code `TODO`/`FIXME` (stays release-review's job, D39).
- A backlog manifest/index unless OQ5 says otherwise.

## 13. Next step

Drafted to `Status: to-review` and paused. Next: review (internal `/plan-review` or external, maintainer's call) and resolve OQ1-OQ7, then HUMAN APPROVAL before authoring the IPD/Set. Do NOT begin implementation until approved. The cheap interim safety mitigation (an `aw attention`/`/whatnext` "backlog not covered" notice) MAY be done first if the maintainer wants the false-comprehensiveness risk closed before this ships.

## Workflow history
- 2026-08-13 /spec (opencode its_direct/pt3-claude-opus-4.8-1m-us): drafted the attention-visible-backlog-tier spec to Status: to-review, prompted by the maintainer's finding that aw attention (which feeds /whatnext) silently omits committed work living in TODO.md. Proposes a lightweight tracked .agents/backlog/{open,parked,done}/ type mapped into aw attention (open->ready, parked->parked, done->done), mirroring the actions tree, with a three-tier commitment model so committed work surfaces while uncommitted maybes stay quiet. Extends D125.
- 2026-08-13 note (aw specs): /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS (non-blocking). PR-001 HIGH (attention integration is 4 touch-points not 1) + PR-004 HIGH (draft rooted the tree at .agents/, contradicting the D130 awphysical migration; corrected to the records-class backlog/ sub-tree, dual-path like plans) FIXED in place; PR-002/PR-003 LOW folded in. Resolved OQ1 (Bugs+Security+Planned-next=open; Consider=parked; Notes=prose), OQ3 (add blocked + typed gate; statuses open|blocked|parked|done), OQ7 (records/backlog, not .agents or state). OQ2/OQ4/OQ5/OQ6 left as non-blocking implementation leanings for the IPD. Status stays to-review; human approval + OQ2/4/5/6 remain before an IPD.
- 2026-08-13 note (aw specs): /plan-review question loop completed (opencode Opus 4.8): resolved the remaining OQs interactively with the human maintainer. OQ2: parked excluded from the aw attention hot glance, in JSON, revealed by 'aw attention all'; + add 'aw att' alias. OQ4: promotion = set done + history line citing the plan id6 (no new status). OQ5: no manifest in v1. OQ6: priority high|medium|low AND carry a Set grouping + clustering filename FROM v1. All four folded into the spec. Status stays to-review; human approval remains the gate before an IPD.
