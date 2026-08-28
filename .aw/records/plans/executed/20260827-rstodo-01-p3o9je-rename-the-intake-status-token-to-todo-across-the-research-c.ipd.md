# IPD: Rename the intake status token to todo across the research contract, classification, and CLI modules

- Date: 2026-08-27
- Kind: child
- Concern: The `intake` status token is opaque and must become `todo`. It is referenced in code at: `research_contract.py` STATUSES/HOT_STATUSES (:148-149) + docstring (:18); `research_cmd.py` creation defaults (:189, :244); `attention_contract.py` classification map (:231 `"intake": READY`); `attention.py` stale-reclass logic + color band (:176-228, :485); `research_index.py` hot-glance band + the `## Needs addressing (intake)` header (:185-195); `research_archive.py` docstrings/hot-state logic; `cli.py` (:5994); `term.py`. This child renames the TOKEN in code (behavior-preserving); on-disk doc migration is child 02.
- Scope: Rename `intake` -> `todo` everywhere the token appears in code, keeping behavior identical (a `todo` research doc classifies READY/needs-attention exactly as `intake` did; stale-reclass to PARKED unchanged; color band preserved). Add a BACKWARD-COMPATIBLE READ: the contract accepts a legacy `intake` value as an alias of `todo` (so a not-yet-migrated on-disk doc, and child 02's migration window, do not break). Update the `research_index` `## Needs addressing` header wording to reflect `todo`. Update `cli.py` status choices/help and `term.py` label/color keys. Do NOT migrate on-disk docs here (child 02). Update the module tests that assert `intake` to assert `todo` + add a compat test that a legacy `intake` value still classifies as READY.
- Scope-Paths: agent_workflows/research_contract.py, agent_workflows/research_cmd.py, agent_workflows/research_index.py, agent_workflows/research_archive.py, agent_workflows/attention.py, agent_workflows/attention_contract.py, agent_workflows/cli.py, agent_workflows/term.py, tests/
- Status: executed
- Set: rstodo
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: p3o9je

## Workflow history
- 2026-08-28 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Rename research status intake -> todo across contract/classification/index/CLI/color with a single STATUS_NORMALIZATIONS alias + normalize_status (strategy A: normalize-at-read-site); behavior-preserving, legacy intake reads as todo; creation emits todo. 96 research/attention tests green [Scope reconciliation - in-scope-unmodified agent_workflows/attention.py: committed 00d2bdf before begin base; in-scope-unmodified agent_workflows/attention_contract.py: committed 00d2bdf before begin base; in-scope-unmodified agent_workflows/cli.py: committed 00d2bdf before begin base; in-scope-unmodified agent_workflows/research_archive.py: committed 00d2bdf before begin base; in-scope-unmodified agent_workflows/research_cmd.py: committed 00d2bdf before begin base; in-scope-unmodified agent_workflows/research_contract.py: committed 00d2bdf before begin base; in-scope-unmodified agent_workflows/research_index.py: committed in 3df018c (co-committed by a concurrent agent via a staging race; see DECISION 11-p3o9je-D2), before begin base; in-scope-unmodified agent_workflows/term.py: committed 00d2bdf before begin base; in-scope-unmodified tests/: committed 00d2bdf before begin base]
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): plan-review APPROVE WITH REVISIONS APPLIED: PR-101 raw-frontmatter read-site composition (index/attention/class_of) made explicit in E-02/E-03; PR-102 concrete STATUS_NORMALIZATIONS/normalize_status mechanism in E-01; PR-103 research_archive.py covered (new E-04); PR-104 enumerated test files + load-bearing compat test; PR-105 concrete V-01..V-05 evidence; PR-106 execution contract; PR-107 in-code prose sync. Split research_cmd defaults to E-05 for right-sizing.

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Rename the research `intake` status token to `todo` across the contract, classification, CLI, index, and color modules, behavior-preserving, with a backward-compatible read accepting legacy `intake` as an alias.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: canonical token + creation

- [x] E-01 In `research_contract.py` make `todo` the canonical hot token with a concrete backward-compat normalization modeled on the existing `KIND_NORMALIZATIONS`/`normalize_kind` idiom. `todo` becomes a member of `STATUSES`/`HOT_STATUSES` (:148-149), a new `STATUS_NORMALIZATIONS = {"intake": "todo"}` feeds a `normalize_status(token) -> VocabResult` that maps legacy `intake` to canonical `todo`, and `validate_frontmatter` (:443-447) accepts any value that is in `STATUSES` OR normalizes through `STATUS_NORMALIZATIONS` (a legacy `intake` doc is accepted, not rejected). Record in the plan whether `intake` also stays in `STATUSES` for the window or is accepted purely through normalization. The module docstring (:18 hot-state note) is updated to name `todo`. This is one cohesive concern (the contract vocabulary + its accept-both read) verified by V-01.
  - Depends on: none
  - Expected outcome: `validate_frontmatter` accepts both `todo` and legacy `intake`, `normalize_status("intake") == "todo"`, and nothing that validates a legacy doc raises.
  - Execution state: performed
- [x] E-05 In `research_cmd.py` change the two creation defaults (:189, :244) to emit `status="todo"` so newly created research docs are born `todo`.
  - Depends on: E-01
  - Expected outcome: a newly created research doc has `status: todo`.
  - Execution state: performed

### Task group 2: classification, index, cli, term

- [x] E-02 Update the classification/stale/color path so `todo` behaves exactly as `intake` did AND a legacy (unmigrated) `intake` doc keeps classifying correctly during the child-01-done/child-02-pending window. CRITICAL: these read sites consume the RAW frontmatter status, not a normalized contract value - `research_index._scan_docs` sets `status=str(fm.get("status",""))` (research_index.py:134), `attention` compares `it.native_status == "intake"` (attention.py:209,227), and `attention_contract.class_of` is a PURE, TOTAL map that RAISES `UnknownStatus` (attention_contract.py:273-284) for any status not in `_RESEARCH_MAP`. So simply rekeying to `todo` would (a) drop unmigrated `intake` docs from the `todo` band, (b) skip them in stale-reclass, and (c) raise `attention.unknown-status` on them. Choose and implement ONE coherent strategy and record it: EITHER (A) normalize the raw status to canonical (`normalize_status`) at each read site BEFORE the map/compare/band selection; OR (B) keep `intake` as an accepted ALIAS entry in every total/pure map for the window (`_RESEARCH_MAP` retains `"intake": READY` alongside `"todo": READY`; the color map retains both keys; `attention.py` matches both `todo` and `intake`) while `todo` is the canonical created/primary value. Update `attention_contract.py:231` (add `"todo": READY`), `attention.py` stale-reclass (:176-228) and color band (:485), so behavior is identical (READY, stale->PARKED, color preserved) for `todo` and legacy `intake`. Update the pinned attention status-enum coverage test accordingly.
  - Depends on: E-01
  - Expected outcome: a `todo` research doc classifies READY and stale-reclasses to PARKED exactly as `intake` did (color unchanged); a legacy `intake` doc STILL classifies READY, stale-reclasses, and keeps its color (no `unknown-status`) throughout the migration window.
  - Execution state: performed
- [x] E-03 Update `research_index.py` hot band selector (`intake = [e for e in entries if e.status == "intake"]`, :185), the `## Needs addressing (intake)` header text (:193), the `find` status filter exact-match (:229), and the module docstring's `intake`-band prose (:4-6) to use `todo` - applying the E-02 strategy so an unmigrated `intake` doc still lands in the band (either normalize `e.status` or match both tokens for the window). Update `cli.py` status choices/help (:5994) and `term.py` label/color keys (:104 `"intake": 44`), keeping `intake` as an alias key for the window if strategy (B) was chosen.
  - Depends on: E-01
  - Expected outcome: index renders the band (containing both `todo` and any unmigrated legacy `intake` docs) under a `## Needs addressing` header worded for `todo`; `aw` status choices show `todo`; `find --status todo` returns migrated docs.
  - Execution state: performed
- [x] E-04 Update `research_archive.py` (in Scope-Paths, uncovered by E-01..E-03): change the four-state-lifecycle docstring (:3, :8) and the `suggest_triage` STALE-hot-doc docstring (:373) from `intake` to `todo`, and audit its hot-state logic - it keys off `HOT_STATUSES` membership (updated in E-01), so confirm no literal `"intake"` comparison remains except an intentional alias. Re-word the `attention.py` explanatory comments/docstrings that name the historical token (the IPD h40usm reclass notes :176-228 and the doctext :198-203, plus :599) to `todo` so the code reads consistently and the orchestrator's `grep`-based E-01 verification passes.
  - Depends on: E-01
  - Expected outcome: no stray `intake` docstring/comment describing CURRENT behavior remains in `research_archive.py` or `attention.py`; only the intentional backward-compat alias references `intake`.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Canonical vocab lives in `research_contract.STATUSES`/`HOT_STATUSES` (:148-149); everything else keys off it.
- `attention_contract.py:231` maps status->attention class; `attention.py:485` holds the color band; `research_index.py:185-195` already renders a `## Needs addressing (intake)` header (rename to `todo`).
- Pre-release: no external repos depend on `intake`, so a permanent alias is optional (see orchestrator OQ-01); a transitional alias is still needed so child 02's migration window and any unmigrated doc do not break.

## Findings

Behavior-preserving token rename. The real subtlety is NOT just "accept `intake` as `todo`" in the contract: several consumers read the RAW frontmatter status rather than a normalized value - `research_index._scan_docs` (`status=fm.get("status")`, :134) feeds the band selector `e.status == "intake"` (:185) and `find` filter (:229); `attention` compares `native_status == "intake"` (:209,227); and `attention_contract.class_of` is PURE+TOTAL and RAISES `UnknownStatus` on any unmapped status (:273-284). So the compat read must be enforced at each read site (strategy A) OR `intake` kept as an alias in every total/pure map for the window (strategy B). Getting this wrong silently breaks classification of unmigrated docs during the child-01-done/child-02-pending window - hence the load-bearing compat test.

## Proposed changes (ordered, validatable)

1. `research_contract.py`: canonical token `todo` + concrete `STATUS_NORMALIZATIONS`/`normalize_status` + accept-both in `validate_frontmatter`.
2. `research_cmd.py`: creation emits `todo`.
3. `attention_contract.py`/`attention.py`: classify/color for `todo` AND legacy `intake` (behavior identical; chosen strategy A or B recorded).
4. `research_index.py`/`cli.py`/`term.py`: `todo` band/header/find-filter/choices/labels (raw-status read sites handled per E-02 strategy).
5. `research_archive.py` + `attention.py` comments/docstrings: `todo` (E-04).
6. `tests/`: update the enumerated files' assertions to `todo` + the load-bearing legacy-`intake`-still-behaves compat test.

## Deferred / out of scope (with reason)

- On-disk doc migration + INDEX regeneration: child 02.
- The intake overload fix: spec 5tapom.

## Scope check

- Over-scope: none.
- Under-scope: covered after revision - `research_archive.py` (now E-04), the raw-frontmatter read sites in `research_index`/`attention` (now explicit in E-02/E-03), the concrete `normalize_status` mechanism (E-01), and the enumerated test files (Required tests). The load-bearing risk is behavior parity for legacy `intake` during the migration window, addressed by the E-02 strategy + the compat test.

## Required tests / validation

Concrete test files that hardcode `intake` today and must be updated to `todo` (plus the compat test): `tests/test_research_cmd_create.py:49` (asserts created `status == "intake"` -> `"todo"`); `tests/test_research_index.py:62,90-96` (fixture `status="intake"` and the `"Needs addressing (intake)"` header assertion -> `todo`); `tests/test_research_archive.py` (numerous `status="intake"` fixtures -> `todo`, or keep one as an explicit legacy-`intake` fixture to prove the alias); `tests/test_attention.py` (research `intake`->READY expectations -> `todo`); `tests/test_research_contract.py` (STATUSES/normalization).

- New research doc creation emits `status: todo` (test_research_cmd_create).
- A `todo` research doc classifies READY; stale-reclass to PARKED works; color band unchanged.
- BACKWARD-COMPAT (the load-bearing new test): a doc whose raw frontmatter is `status: intake` (a) passes `validate_frontmatter` (accepted, not rejected), (b) classifies READY (no `attention.unknown-status`), (c) appears in the index `## Needs addressing` band, and (d) keeps its color band - i.e. behavior is identical to a `todo` doc throughout the window.
- `research_index` renders the band under `## Needs addressing` (worded for `todo`); `find --status todo` returns migrated docs; `aw` status choices include `todo`.
- The pinned attention status-enum coverage test reflects the updated research map.

## Spec / documentation sync

- Update research docs/README + AGENTS.md research state vocab (`todo -> active -> reference/archive`); cross-ref spec 5tapom.
- In-code prose to keep honest: the `research_index.py` module docstring (:4-6, "intake band"), the `## Needs addressing (intake)` rendered header (:193), and the `research_contract.py`/`research_archive.py` lifecycle docstrings all name `intake` and must read `todo` (covered by E-03/E-04).

## Open questions

### OQ-01: none beyond the orchestrator's alias-lifetime question.

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Alias lifetime is decided at the orchestrator (OQ-01); this child implements the alias regardless.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste (1) the `research_contract.py` diff showing `todo` in `STATUSES`/`HOT_STATUSES`, the new `STATUS_NORMALIZATIONS`/`normalize_status`, and the `validate_frontmatter` accept-both change; (2) a REPL/test line proving `normalize_status("intake") == "todo"` and `validate_frontmatter({"status":"intake", ...})` returns no error; (3) the `research_cmd` test output showing a newly created doc has `status: todo`. Verified in a separate pass, not from the E-01 checkmark.
  - Observed evidence: (1) research_contract.py now has `STATUSES = frozenset(("todo","active","reference","archive"))` + `HOT_STATUSES = frozenset(("todo","active"))` (`intake` removed), `STATUS_NORMALIZATIONS = {"intake": "todo"}`, and `normalize_status(token) -> VocabResult` (mirrors normalize_kind); `validate_frontmatter` accepts `status` when `normalize_status(val).ok`. (2) Smoke: `R.normalize_status('intake').value == 'todo'`; `[e for e in R.validate_frontmatter({'status':'intake'}) if e.field=='status'] == []` (no status error); `'todo' in R.STATUSES == True`, `'intake' in R.STATUSES == False`. `tests/test_research_contract.py::SchemaConstantsTests::test_statuses`/`test_hot_vs_sharded`/`test_legacy_intake_normalizes_to_todo` pass. (3) `tests/test_research_cmd_create.py::NewPlanTests::test_new_well_formed_and_full_frontmatter` asserts a created doc has `data["status"] == "todo"`. Runner: `python3 -m pytest tests/test_research_contract.py tests/test_research_cmd_create.py tests/test_research_index.py tests/test_research_archive.py tests/test_attention.py -m ''` -> `96 passed in 5.09s`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: state which strategy (A normalize-at-read-site / B alias-in-maps) was implemented; paste passing test output for BOTH a `todo` doc AND a raw `intake` doc showing each classifies READY, stale-reclasses to PARKED, and keeps its color; paste evidence that `class_of("research", "intake")` does NOT raise `UnknownStatus`; paste the updated pinned attention status-enum coverage test passing.
  - Observed evidence: STRATEGY A (normalize-at-read-site; DECISION 11-p3o9je-D1) - `STATUS_NORMALIZATIONS`+`normalize_status` are the single alias table, and the attention scanner (attention.py:_research_record) normalizes the RAW status to canonical BEFORE the STATUSES check / native_status storage / `class_of`, so a legacy `intake` doc gets native_status `todo`. `_RESEARCH_MAP` is keyed on canonical `todo` only; `class_of("research","todo") == "ready"` (smoke). `tests/test_attention.py::StaleResearchReclassifyTests::test_todo_and_legacy_intake_classify_identically` (NEW load-bearing compat test) asserts BOTH a `todo` doc and a legacy `intake` doc classify READY, raise NO `attention.unknown-status`, and both surface with native_status normalized to `todo` (so color + stale-reclass are identical); `test_run_set_intake_not_ready_...` (legacy `intake` fixtures) still asserts stale RUN-set -> PARKED and unrun -> READY. `test_class_of_unchanged_and_total` updated to key on canonical `todo` (a legacy `intake` is normalized at the scanner, not in the pure/total `class_of`). All in the `14 passed` attention run.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `aw research index` output (or the index test) showing a `## Needs addressing` band that contains both a `todo` and an unmigrated `intake` fixture doc; paste `find --status todo` returning the migrated doc; paste `aw <cmd> --help`/choices output listing `todo`.
  - Observed evidence: `research_index.build_index_md` band selector normalizes the raw status (`normalize_status(e.status).value == "todo"`), so a legacy `intake` fixture lands in the band; the header is renamed `## Needs addressing (todo)`. `tests/test_research_index.py::IndexBuildTests::test_index_md_archive_excluded_reference_included_intake_shown` (fixture has raw `status: intake`) asserts the doc `aaaaaa` appears AND the header reads `Needs addressing (todo)` - proving an unmigrated `intake` doc renders in the `todo` band. The `find` filter normalizes both sides so `--status todo` matches a legacy `intake` doc (and vice versa). The stale-state drift tests (`test_trigger_a`/`test_trigger_b`) - which write raw `intake` fixtures - pass because the stale-hot selector also normalizes (`normalize_status(e.status).value in HOT_STATUSES`). cli.py status-bucket list now includes `todo` (kept `intake` as a legacy path-bucket alias). Part of the `96 passed` run.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the scoped grep `grep -rn "intake" agent_workflows/research_archive.py agent_workflows/attention.py | grep -vE "compat|alias|legacy"` showing every remaining hit is an intentional alias reference (no docstring/comment describing CURRENT behavior still says `intake`).
  - Observed evidence: `grep -rn "intake" agent_workflows/research_archive.py agent_workflows/attention.py | grep -vE "compat|alias|legacy"` returns only three attention.py hits, all `rstodo p3o9je`-tagged migration comments/color-key trailing comment that NAME the historical token in describing the rename (attention.py:184,388 migration comments; :494 the `"todo": 44` color key whose comment says "renamed from `intake`"). research_archive.py has ZERO remaining `intake` (its four-state-lifecycle + suggest_triage docstrings now say `todo`; its hot-state logic keys off the E-01 `HOT_STATUSES` via `normalize_status`). No docstring/comment describing CURRENT behavior still says `intake`. The whole-file scoped grep for a live status VALUE (`grep -rn "intake" agent_workflows/ | grep -vE "#|\"\"\"|compat|alias|legacy"`) surfaces only `STATUS_NORMALIZATIONS = {"intake": "todo"}` (the single intentional alias-table entry) + one normalize_status docstring continuation line.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: a newly created research doc has `status: todo` (research_cmd creation defaults).
  - Observed evidence: `research_cmd.py` both creation defaults (the two `status="intake"` call sites) now emit `status="todo"` (grep: 0 `intake`, 2 `status="todo"`). `tests/test_research_cmd_create.py::NewPlanTests::test_new_well_formed_and_full_frontmatter` asserts a created doc has `data["status"] == "todo"` (passes, part of the `96 passed` run).
  - Result: pass



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

### Execution contract

- Human approval required before execution. This is child 01 of Set `rstodo` (order 01, depended on by child 02 `lpqy64`); execute it before child 02.
- Resolved open questions: OQ-01 (alias lifetime) is decided at the orchestrator `dh5gnl` (non-blocking; alias kept through migration + one release). This child implements the transitional alias regardless.
- Scope fence: touch ONLY the Scope-Paths. This child renames the CODE token and adds the backward-compat read; it does NOT migrate on-disk docs (child 02) and does NOT fix the `intake` OVERLOAD (spec `5tapom`). Do not rekey the total/pure attention map in a way that breaks a legacy `intake` doc during the migration window (see E-02).
- Honesty (hard MUST): when reporting the suite or any command as passing, paste the ACTUAL runner output. Never claim a validation passed that was not run. Each V-item is verified from pasted output in a separate pass from its E checkmark.
- Commit discipline: commit ONLY the files this child changed, path-scoped (`git commit -m <msg> -- <path> ...`); never `git add -A`/`-a`/bare add; never push; never create tags or releases.
- Post-gate lifecycle move (NOT a checklist item; performed by the ipd-lifecycle gate after all E/V items complete and validated): append a `## Workflow history` line, set terminal `Status: executed`, and `git mv` from `pending/` to `.aw/records/plans/executed/` in a single path-scoped lifecycle commit - but note the orchestrator moves the whole Set together, so coordinate the terminal move with `dh5gnl`/`lpqy64`. Do not move until `aw ipd lint --phase pre-transition` conforms and every V-item is verified with pasted evidence; otherwise STOP and report.
