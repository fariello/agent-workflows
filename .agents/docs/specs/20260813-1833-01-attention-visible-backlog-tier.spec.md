# Spec: an attention-visible backlog tier (`.agents/backlog/` + `aw backlog`)

- Date: 2026-08-13
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: `aw attention` (D125) is the deterministic, on-demand answer to "what needs attention across the repo?" and feeds `/whatnext`, but it scans ONLY status-bearing trees (plans, specs, research, actions). Committed work captured in the free-prose `TODO.md` is therefore SILENTLY omitted from the view. A tool that looks comprehensive but omits a whole class of pending work creates false confidence: relying on `aw attention` misses `TODO.md`; relying on `TODO.md` misses the attention view. The maintainer flagged this as a real risk.
- Relation to prior work: EXTENDS D125 (adds a new attention adopter). Mirrors the already-shipped `actions` tree mechanism (a tracked, lightweight, status-by-directory tree mapped into `aw attention` via `attention_contract.CLASS_MAPS`). Reuses `agent_workflows/artifact_core.py` (id6, atomic write, the `Drift`/`--check` convention) and the `aw specs`/`aw research` verb pattern.

## 1. One-line summary

Add a lightweight, tracked BACKLOG artifact type at `.agents/backlog/{open,parked,done}/` (one small frontmatter+prose file per item) and make it an `aw attention` adopter, so COMMITTED backlog items ("we must / we should do this") surface as `ready` in `aw attention` + `/whatnext`, while explicitly-uncommitted "maybes" are tracked-but-quiet and pure "notes" stay out entirely. This closes the false-comprehensiveness gap without imposing IPD ceremony on backlog capture.

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

- G1 `[Must]` Add a tracked backlog artifact type at `.agents/backlog/{open,parked,done}/`, one file per item, each carrying a machine-readable frontmatter status.
- G2 `[Must]` Make `backlog` an `aw attention` adopter via a `_BACKLOG_MAP` fragment in `attention_contract.CLASS_MAPS`: `open -> ready`, `parked -> parked`, `done -> done`. Committed (`open`) items thus appear in the view + `/whatnext`; `parked` items are in JSON but out of the hot glance (exactly like `archive` research).
- G3 `[Must]` Provide `aw backlog` verbs mirroring `aw research`/`aw specs`: at least `new` (create a conformant item, dry-run by default), `set` (transition open/parked/done + append history), `check` (validate the tree against the contract, fail closed), and `index`/`find` if a manifest is warranted (OQ5).
- G4 `[Must]` Keep capture cheap: creating a backlog item is one `aw backlog new --summary ... --priority ... --kind ...` command (or dropping a conformant file), with NO id6-in-filename ceremony, NO E/V bijection, NO lint-phase gates.
- G5 `[Must]` Migrate the existing `TODO.md`: committed sections (Known bugs, Security follow-ups, Planned next) -> `.agents/backlog/open/`; "Consider / may be declined" -> `.agents/backlog/parked/`; "Notes" stays prose. `TODO.md` is then either retired or reduced to a pointer at the backlog tree + the Notes section.
- G6 `[Should]` `/whatnext` consumes the backlog `ready` items (it already consumes `aw attention --format json`, so this is automatic once G2 lands) and a CI `aw backlog check` fail-closed gate exists (like `aw specs check`).
- G7 `[Must]` Stdlib only; zero runtime deps; Python 3.9; ships in the importable package as `aw backlog` and `python -m agent_workflows backlog`.

## 5. Non-goals

- NOT replacing plans/specs/research. A backlog item that becomes real execution work is PROMOTED to a plan (a backlog item may cite the plan and move to `done`); the backlog is the pre-plan capture tier, not a competing plan lifecycle.
- NOT a priority/urgency SCHEDULER; `priority` is a sort hint only.
- NOT importing in-code `TODO`/`FIXME` comments (that remains a `release-review` concern, D39).
- NOT adding a new attention CLASS; backlog reuses the existing five (`ready`/`active`/`blocked`/`done`/`parked`).

## 6. Functional design

### 6.1 On-disk layout and item format

```
.agents/backlog/
  open/        Tier-1 committed items            (attention: ready)
  parked/      Tier-2 uncommitted "maybes"        (attention: parked)
  done/        completed/closed items             (attention: done)
  README.md
```

Status is encoded BOTH by directory (disposition, like `plans/`) and by a bare-enum frontmatter `status` (the machine-readable source of truth mapped by `class_of`), and the two MUST agree (a `check` rule, mirroring "Status mirrors dir" for plans/specs). One item is one file:

```markdown
---
id: <id6>                 # stable base36 handle, never changes (artifact_core)
created: <YYYYMMDD>
status: open              # open | parked | done   (bare enum; owned by `aw backlog set`)
priority: high            # high | medium | low     (sort hint within a class; not a class)
kind: bug                 # bug | feature | chore | security | followup
summary: <one line>       # the glanceable line aw attention/whatnext show
---
Free-form prose body: description, links to DECISIONS/commits/specs, acceptance notes.
```

Filename grammar (clustering, consistent with plans/research): `YYYYMMDD-<id6>-<slug>.md` (singletons; a `- Set:` grouping MAY be added later if cohorts emerge, OQ6). `aw backlog new` owns the name + frontmatter (no hand-naming, per the plans/research rule).

### 6.2 Attention mapping (the D125 extension)

Add to `agent_workflows/attention_contract.py`:

```python
_BACKLOG_MAP = {"open": READY, "parked": PARKED, "done": DONE}
CLASS_MAPS["backlog"] = _BACKLOG_MAP
```

The mapping is PURE and TOTAL over the backlog status enum (D125 Section 6 invariant): `class_of("backlog", status)` depends only on `(tree, status)`; an unknown status is the `attention.unknown-status` violation, never a default. `aw attention` discovers `.agents/backlog/**/*.md`, reads each item's frontmatter `status`, maps it, and includes it in the board/JSON like any other tree. `priority` is carried into the JSON and used to order the `ready` list (high first); it is NOT a class.

### 6.3 CLI

`aw backlog new|set|check` (+ optional `index`/`find`), wired at the two `cli.py` edit points, mirroring `aw research`/`aw specs`. `set` moves the file between `open/parked/done`, updates the frontmatter `status`, and appends a `## Workflow history` line (append-only provenance, D52 style). `check` validates: frontmatter present + valid enums, status-mirrors-directory, id6 present/unique, `summary` nonempty; fail closed with the `Drift`/`--agent`/exit convention.

## 7. Convention / docs change

- AGENTS.md: add a short pointer that COMMITTED backlog lives in `.agents/backlog/` (surfaced by `aw attention`), and that `TODO.md` (if kept) holds only uncommitted notes.
- `.agents/docs/specs/README.md` / the attention docs: note `backlog` as an attention adopter (extends D125).
- A new `.agents/backlog/README.md` documenting the tiers, format, and `aw backlog` verbs.
- DECISIONS: a new entry recording the three-tier model + backlog-as-attention-adopter (revising D125's adopter set), created when this ships.

## 8. Requirements

- F1 `.agents/backlog/{open,parked,done}/` tree with the item format of Section 6.1.
- F2 `_BACKLOG_MAP` (`open->ready`, `parked->parked`, `done->done`) registered in `CLASS_MAPS`; `aw attention` includes backlog items; `ready` items appear in the hot glance and `/whatnext`, `parked` only in JSON.
- F3 `aw backlog new|set|check` implementing capture, status transitions + history, and fail-closed validation, stdlib-only, `--agent` + exit convention on `check`.
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

- Depends on `artifact_core` and `attention_contract` (D125). The attention-contract change is the load-bearing edit; the rest is a conventional new tree + verbs. Establishes the `aw backlog` namespace (none today). The migration (G5) must not lose any committed item.

## 11. Risks and open questions

- OQ1 Tier assignment of the current `TODO.md` sections: confirm "Known bugs" + "Security follow-ups" + "Planned next (designed, deferred)" are ALL Tier-1 `open`, "Consider / may be declined" is Tier-2 `parked`, and "Notes" is Tier-3 prose. Is "Planned next: designed, deferred" truly committed (`open`), or a distinct "designed-but-not-committed" that should be `parked`? (Leaning: `open` - it is the maintainer's committed-next queue.)
- OQ2 Should `parked` items be TOTALLY excluded from the human `aw attention` board, or shown in a collapsed/secondary "backlog (parked)" section? (Leaning: excluded from the hot glance, in JSON, matching `archive` research; a `--all`/`--include-parked` flag could reveal them.)
- OQ3 Does `backlog` need a `blocked` status (a committed item waiting on a named gate, mapping to the attention `blocked` class + a typed `Gate-Kind`/`Gate-Ref` like specs), or is open/parked/done enough for v1? (Leaning: add `blocked` - committed-but-gated is common and the attention class already exists.)
- OQ4 Promotion path: when a backlog item becomes a plan, does it move to `done` with a cite to the plan, or gain a `promoted`/`superseded` status? (Leaning: `done` + a history line citing the plan id6; avoid a new status.)
- OQ5 Does backlog need its own manifest (`INDEX.json` + `--check`) like plans/research, or is directory + `aw attention` enough at this scale (~dozens of items)? (Leaning: start without a manifest; add `index`/`find` only if the corpus grows.)
- OQ6 `priority` enum: high/medium/low, or must/should/meh, or a small integer? And is a `- Set:` grouping worth carrying from day one for cohorts? (Leaning: high/medium/low; no Set until cohorts appear.)
- OQ7 Location: `.agents/backlog/` (proposed, tracked, sits beside plans/specs/prompts) vs `.aw/state/` (operational, alongside `actions`). Backlog is human-curated project intent, not AW operational state, so `.agents/backlog/` fits the ownership boundary (D126) better than `state`. Confirm.

## 12. Out-of-scope / future

- Auto-triage or auto-classification of backlog items (kept human-curated).
- Importing in-code `TODO`/`FIXME` (stays release-review's job, D39).
- A backlog manifest/index unless OQ5 says otherwise.

## 13. Next step

Drafted to `Status: to-review` and paused. Next: review (internal `/plan-review` or external, maintainer's call) and resolve OQ1-OQ7, then HUMAN APPROVAL before authoring the IPD/Set. Do NOT begin implementation until approved. The cheap interim safety mitigation (an `aw attention`/`/whatnext` "backlog not covered" notice) MAY be done first if the maintainer wants the false-comprehensiveness risk closed before this ships.

## Workflow history
- 2026-08-13 /spec (opencode its_direct/pt3-claude-opus-4.8-1m-us): drafted the attention-visible-backlog-tier spec to Status: to-review, prompted by the maintainer's finding that aw attention (which feeds /whatnext) silently omits committed work living in TODO.md. Proposes a lightweight tracked .agents/backlog/{open,parked,done}/ type mapped into aw attention (open->ready, parked->parked, done->done), mirroring the actions tree, with a three-tier commitment model so committed work surfaces while uncommitted maybes stay quiet. Extends D125.
