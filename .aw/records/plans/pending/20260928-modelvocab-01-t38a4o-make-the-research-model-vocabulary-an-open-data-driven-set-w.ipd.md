# IPD: Make the research model vocabulary an open, data-driven set: warn instead of refusing an unknown model, ship an add verb, and stop one new model from blackholing the whole index

- Date: 2026-09-28
- Kind: child
- Concern: `research_contract.MODELS` is a closed frozenset and `normalize_model` is a bare membership test with no escape hatch, so every model the outside world ships next (Gemini 4, GPT-5.5, DeepSeek, any new reasoning tier) is REFUSED until someone edits Python and amends a spec. Measured here, the consequence is worse than the filed item reports: one doc carrying an unknown model makes `aw research index` refuse to write INDEX.json AT ALL, so a single new model blackholes the manifest for all 130 docs.
- Scope: turn `<model>` into an OPEN vocabulary: an unknown token is recorded with a loud warning instead of being rejected, the known list moves into a tracked editable data file with a shipped package default, `aw research add-model` adds a token in one command, and `aw research index --check` gains an advisory drift rule so a typo stays mechanically visible. Amends spec `20260730-2152-01` requirement E3 and section 5.4, which currently make the vocabulary an enumerated `[Must]`. Does NOT touch `<kind>` (a genuinely closed, repo-owned vocabulary), `MODEL_NORMALIZATIONS`' collapsing behavior, the reasoning-effort-in-identity rule, `<status>`, or any existing artifact's name.
- Scope-Paths: agent_workflows/research_contract.py, agent_workflows/model_vocab.py, agent_workflows/data/research-models.toml, agent_workflows/research_cmd.py, agent_workflows/artifact_adopt.py, agent_workflows/research_index.py, agent_workflows/check_engine.py, agent_workflows/cli.py, pyproject.toml, tests/test_model_vocab.py, tests/test_research_cmd_create.py, tests/test_artifact_adopt.py, tests/test_research_index.py, .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md, .aw/records/research/README.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 6b9zd9
- Blocks-Release: next
- Set: modelvocab
- Order: 1
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: t38a4o

## Workflow history

- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `6b9zd9`. The item's four required fixes are adopted as specified; measurement during authoring found the blast radius materially LARGER than filed (F-2: total index outage, not a naming refusal) and found one of the item's premises factually wrong (F-9: package data already ships, so no packaging decision is owed), both recorded in Findings.

## Goal

Make `<model>` behave like the open set it is: a token from a vendor this repo has never heard of RECORDS with a warning that teaches the exact command to bless it, rather than refusing a correct artifact and taking the research manifest down with it. Keep the one thing the closed list legitimately bought, consistent spelling, by leaving `MODEL_NORMALIZATIONS` in charge of drift and by making an unrecognized token visible as advisory drift in `aw research index --check`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the data file and its loader

- [ ] E-01 Add `agent_workflows/data/research-models.toml`, a tracked, commented data file carrying the canonical model tokens and the drift-spelling map, seeded with EXACTLY today's `research_contract.MODELS` (13 tokens) and `MODEL_NORMALIZATIONS` (20 entries) so the migration is behavior-preserving by construction. Emit only shapes the repo's existing minimal TOML reader round-trips: flat string arrays and flat `key = "value"` pairs, following the `.aw/config/local-leaks-allowlist.toml` precedent, whose own header says "It is read by a minimal TOML reader (3.9-safe, no tomllib), so keep entries to flat string arrays and flat booleans". Represent the normalization MAP as a flat `[normalizations]` section of `from = "to"` pairs rather than nested tables. Carry the same commentary the code holds today, specifically the "A NEW MODEL IS NOT A SPELLING VARIANT" rule and the reasoning-effort-in-identity rule, because that is the review guidance a human editing this file needs and it must not be lost in the move.
  - Depends on: none
  - Expected outcome: a new data file whose parsed content equals today's in-code vocabulary exactly; `sorted(parsed_models) == sorted(research_contract.MODELS)` and the parsed normalization map equals `MODEL_NORMALIZATIONS`.
  - Execution state: pending

- [ ] E-02 Add `agent_workflows/model_vocab.py` with the READER only: resolve the effective vocabulary by merging three ADDITIVE layers, lowest precedence first. The layers are the PACKAGE DEFAULT `agent_workflows/data/research-models.toml` (always present, read via `Path(__file__).parent / "data"`, the same `__file__`-relative idiom `run_dashboard._asset` already uses for `run_dashboard_assets`), then the TARGET REPO file `.aw/config/research-models.toml` when present, then the per-user layer beside the repo config, mirroring the allowlist's "never-committed, per-user layer" split. Merging is ADD-ONLY: a later layer contributes tokens and normalizations and can never delete a package token, which is what stops an artifact already named under a shipped token from becoming unparseable through a config edit (see OQ-01). Reuse the repo's existing minimal TOML reader rather than writing a second one, because `leak_sanitizer._parse_simple_toml_lists` is the established 3.9-safe parser and the support floor forbids `tomllib` (3.11+). If that reader cannot express the `from = "to"` normalization pairs, extend it in place with a flat-scalar-pairs reader beside the flat-array one rather than forking a parallel parser, and say which was done in V-02. The WRITER belongs to E-08, not here.
  - Depends on: E-01
  - Expected outcome: `model_vocab.load(repo_root)` returns the merged `(models, normalizations)`; with no repo file present the result equals the package default; with a repo file adding `deepseek4`, that token is present and every package token still is.
  - Execution state: pending

- [ ] E-03 Give the loader a per-repo-root CACHE so the vocabulary is read from disk ONCE per process rather than per token. This is load-bearing, not an optimization flourish: `normalize_model` is called at least twice per document (`parse_name` for the filename facet and `validate_frontmatter` for the `model:` key), which is at least 260 calls for this repo's 130 research docs in a single `aw research index` run (F-8), and a naive loader would turn each into a file stat plus parse. Key the cache on the resolved repo root and expose an explicit invalidation entry point for the add verb and for tests, so a write through E-05 is visible to a subsequent read in the same process. Do NOT cache on a mutable default argument or a module-level dict keyed by a relative path; a test that chdirs between repos must not see another repo's vocabulary.
  - Depends on: E-02
  - Expected outcome: with a counter patched over the file read, a loop of 500 `normalize_model` calls performs exactly one read per repo root; after the invalidation call a subsequent read picks up a newly added token.
  - Execution state: pending

### Task group 2: warn instead of refuse, without breaking the detector

- [ ] E-04 Change `research_contract.normalize_model` to WARN-NOT-REFUSE, and do it WITHOUT breaking the two callers that legitimately depend on a false result. Today the function returns `VocabResult(False, None, sugg, "unknown model ...")` for anything not in `MODELS`, and two call sites read that `ok=False` as a real answer rather than as an error: `artifact_adopt.suggest_metadata` loops over every trailing filename facet and uses `res.ok` to DECIDE WHICH FACET IS THE MODEL (measured F-5: `some-report.gemini31prohigh.agy.md` yields model `gemini31prohigh` precisely because `agy` returns not-ok), and `research_index._doc_entry` turns a not-ok result into blocking drift. So a blanket flip of `ok` to `True` would make `artifact_adopt` label `agy` (or the kind facet) as the model, which is a NEW provenance-corruption bug in the very field this plan exists to protect. Resolve it by distinguishing RECOGNIZED from ACCEPTED: extend `VocabResult` with a `recognized: bool` (defaulting so existing positional construction and every `normalize_kind`/`normalize_status` caller are untouched), have the model path return `ok=True, recognized=False, value=<the normalized token>` with a warning message for an unknown-but-well-formed token, and convert `artifact_adopt`'s facet detector to test `recognized` instead of `ok`. State in V-04 which predicate each of the four `normalize_model` call sites now reads.
  - Depends on: E-03
  - Expected outcome: `normalize_model("deepseek4")` returns ok, `recognized=False`, `value="deepseek4"`, and a message naming the add command; `normalize_model("sonnet5")` returns ok with `recognized=True`; `artifact_adopt.suggest_metadata("x.gemini31prohigh.agy.md", ...)` still proposes `gemini31prohigh` and NOT `agy`.
  - Execution state: pending

- [ ] E-05 Make the warning TEACH THE FIX, which the backlog item requires as its own numbered point and which the current message fails: `unknown model 'gemini4pro'; did you mean 'gemini31pro'?` leaves the user exactly where the defect found them, and its closest-match hint actively misleads, because `gemini31pro` is a DIFFERENT MODEL and accepting the suggestion would file a report under a model that did not write it. The new message must name the exact command (`aw research add-model <token>`) and must keep the proximity hint clearly subordinate to it, marked as a spelling check rather than a recommendation. Also REJECT a malformed token rather than recording it: a canonical model token is `[a-z0-9]+` (verified: all 13 current tokens match, F-7), so a token containing a dot or a hyphen after normalization must still fail hard, since a dot would silently change the filename's facet arity and make the name unparseable. That refusal is a SYNTAX check, not a vocabulary check, and it is the one place a hard refusal stays correct.
  - Depends on: E-04
  - Expected outcome: the unknown-token message contains `aw research add-model`; `normalize_model("gemini 4")` and `normalize_model("a.b")` return `ok=False` (malformed, not merely unknown).
  - Execution state: pending

- [ ] E-06 Stop an unrecognized model from taking the WHOLE INDEX DOWN, which is the most damaging half of this defect and the half the filed item did not know about. Measured (F-2): `research_index.run_index` reads "Refuse to write over invalid input; report and exit nonzero" and returns 1 before writing, so with one unknown-model doc present `INDEX.json` is never created and all 130 docs lose the manifest that `aw research find` and the attention scanner read. After E-04 an unknown model is no longer a `validate_frontmatter` error or a `parse_name` failure, so the doc INDEXES normally; this item's work is to verify that end to end and to add the advisory drift rule below, not to weaken the refuse-on-invalid-input rule, which stays correct for genuinely invalid input.
  - Depends on: E-05
  - Expected outcome: in a scratch repo containing one unknown-model doc plus one known-model doc, `aw research index` exits 0, writes `INDEX.json`, and the unknown-model doc appears in it with its `model` recorded verbatim.
  - Execution state: pending

- [ ] E-07 Add an ADVISORY drift rule reporting an unrecognized model in `aw research index --check`, registered at `info` severity in `check_engine.RULE_REGISTRY`. The severity is load-bearing and is not a style choice: `artifact_core.drift_exit_code` returns `1 if any(getattr(d, "severity", "") != "info" for d in drift) else 0`, so `info` is the UNIQUE severity that does not fail the gate, and registering this as `warning` would make every repo carrying a not-yet-blessed model exit nonzero, which is the same fail-closed behavior this plan is removing. This is what keeps the backlog item's own stated consequence handled: a typo like `sonnet5hgih` is now RECORDED rather than rejected, so it needs a mechanical surface that still notices it.
  - Depends on: E-06
  - Expected outcome: with an unknown-model doc present, `aw research index --check` reports the unrecognized model and still exits 0; with a hand-broken frontmatter field present it still exits 1, proving the advisory rule did not soften real drift.
  - Execution state: pending

### Task group 3: the add verb, packaging, and the contract text

- [ ] E-08 Add the `aw research add-model <token>` CLI verb (with optional `--normalize-from <spelling>` for a drift alias and the repo's standard dry-run-by-default plus `--apply`, matching `research new`'s documented "'new' and 'new-comparison' are dry-run by default; pass --apply to write" convention). It writes the TARGET REPO layer `.aw/config/research-models.toml`, never the packaged default, atomically, creating the file with its explanatory header when absent. Wire it into `cli.py` beside the existing `research` subparsers and add its one-line entry to the command-help table that already carries `research new` / `research mv` / `research promote`. This is the backlog item's point 3, and its whole purpose is that blessing a model becomes one terminal command instead of a Python edit plus a spec amendment.
  - Depends on: E-07
  - Expected outcome: `aw research add-model deepseek4 --apply` exits 0, creates or extends `.aw/config/research-models.toml`, and a subsequent `normalize_model("deepseek4")` in a fresh process returns `recognized=True`; without `--apply` it writes nothing and previews the change.
  - Execution state: pending

- [ ] E-09 Add `tests/test_model_vocab.py` and extend the three affected existing test files, all as OUTCOME tests that drive real functions and CLI commands and assert on real outputs, exit codes, and file bytes (never by reading source text or counting symbols). Cover: the E-01 seed equivalence; three-layer merge including the no-deletion property; the E-03 single-read cache plus invalidation; an unknown token warning that contains `aw research add-model`; malformed-token refusal; the `artifact_adopt` facet-detector regression from F-5 (`gemini31prohigh` chosen over `agy`); a full `aw research index` run over a scratch repo proving the F-2 outage is gone and the doc is in `INDEX.json`; the `info`-severity `--check` exit-0 behavior alongside a real-drift exit-1 control; and the `add-model` round trip. Update `tests/test_research_cmd_create.py::test_unknown_model_rejected`, which asserts `assertIn("unknown model", err)` on a refusal this plan deliberately removes: REPLACE it with a test that an unknown model is now ACCEPTED and recorded while a MALFORMED one is still refused, and say so explicitly in V-09 rather than silently deleting coverage.
  - Depends on: E-08
  - Expected outcome: new and updated tests pass; the bare full suite passes with its `N passed` line pasted; no test inspects production source text.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- `info` IS THE ONLY ADVISORY SEVERITY. `artifact_core.drift_exit_code` exempts `info` alone, and `check_engine` repeats the reasoning on many registrations ("`artifact_core.drift_exit_code` exempts ONLY `info`, so `warning` would still exit 1"). E-07 therefore cannot use `warning` without recreating the fail-closed behavior this plan removes.
- A VOCABULARY IS DERIVED, NEVER RE-LISTED. `status_set.TYPE_STATUSES` carries this as an explicit comment on its research row ("DERIVED from `research_contract.HOT_STATUSES`"). This plan preserves the property by moving the SOURCE of `MODELS` to a data file and keeping `research_contract` the single module that publishes it; no consumer gains its own copy.
- 3.9 SUPPORT FLOOR, NO NEW DEPENDENCIES. `research_contract` is documented "stdlib-only (zero runtime dependencies, D46) and Python 3.9 compatible", and the leak-sanitizer allowlist exists as a hand-rolled minimal TOML reader specifically because `tomllib` is 3.11+. E-02 reuses that reader rather than adding a TOML dependency.
- THE TRACKED-PLUS-USER CONFIG SPLIT IS AN ESTABLISHED SHAPE. `.aw/config/local-leaks-allowlist.toml` is the tracked CI-deterministic layer and `local-leaks-hints.json` the gitignored per-user layer, "Neither file is required; both are additive". E-02 copies that shape rather than inventing a config idiom.
- `research_contract`'s "no side effects" docstring is ALREADY not literally true: `resolve_research_root` calls `Path.is_dir()` and imports `record_producers`. That matters because this plan makes the module's vocabulary depend on a file read, so the docstring must be amended to state what remains true (pure PARSE/FORMAT helpers; the vocabulary is loaded through `model_vocab`) instead of claiming a purity the module does not have.
- A REFUSAL MESSAGE SHOULD NAME THE VERB THAT CAN DO THE JOB, the convention the research status refusal already follows ("use 'aw research promote <id> --to <s>' instead"). E-05 applies the same shape to the model warning.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The defect reproduces EXACTLY as filed. Four representative next-generation tokens are all refused, and the closest-match hint points at a DIFFERENT MODEL, which is the misleading half. | `normalize_model` over four tokens: `gemini4pro` -> not ok, "did you mean 'gemini31pro'?"; `gpt55high` -> not ok, "did you mean 'gpt56'?"; `deepseek4` -> not ok, no hint; `sonnet5hgih` (typo) -> not ok, "did you mean 'sonnet5'?". |
| F-2 | THE BLAST RADIUS IS LARGER THAN THE ITEM REPORTS, and this reframes the bug from "cannot name a doc" to "manifest outage". One unknown-model doc makes `aw research index` write NOTHING, so all 130 docs lose the index. Both the frontmatter key and the filename facet trigger it, by two different routes. | Scratch repo, three docs (unknown model in frontmatter; unknown model in the filename facet; one known-model control): `aw research index` -> exit 1, `frontmatter-invalid: model: unknown model 'gemini4pro'` and `name-invalid: unknown model 'gemini4pro'`, and `INDEX.json exists: False`. Deleting only the two unknown-model docs -> exit 0, "wrote ... INDEX.json, INDEX.md (1 docs)". Root cause is `research_index.run_index`: "Refuse to write over invalid input; report and exit nonzero". |
| F-3 | The gate does not buy what its own comment claims, confirming the item's reasoning. `normalize_model` only tests LIST MEMBERSHIP, never authorship, so it refuses an unknown-but-TRUE model while permitting a known-but-FALSE one. | `normalize_model("gpt56")` returns ok for any document regardless of who wrote it; nothing in `research_contract` or `research_index` compares `model:` against provenance. The only real property it buys is consistent spelling via `MODEL_NORMALIZATIONS`. |
| F-4 | The interim unblock the item describes HAS landed, so the named blocked artifact is already fixed and must not be re-fixed here. `gemini31prodeepthink` now resolves and the doc carries it. | `normalize_model("gemini31prodeepthink")` -> ok. `.aw/records/research/reference/202609/20260905-hostskill-03-i5gj61-...gemini31prodeepthink.research-report.md` carries `model: gemini31prodeepthink` in frontmatter. |
| F-5 | A BLANKET WARN-NOT-REFUSE WOULD INTRODUCE A NEW BUG, which is the single most important design constraint here. `artifact_adopt.suggest_metadata` uses `normalize_model(...).ok` as a DETECTOR to pick which trailing filename facet is the model; if every token became ok, the FIRST facet always wins and a non-model facet gets recorded as the author. | `suggest_metadata("some-report.gemini31prohigh.agy.md", ...)` -> `model='gemini31prohigh'` (correct today only because `agy` returns not-ok). `suggest_metadata("some-report.agy.md", ...)` -> `model=None`. `suggest_metadata("some-report.research-report.md", ...)` -> `model=None`. Hence E-04's `recognized` flag rather than flipping `ok`. |
| F-6 | `warning` severity WOULD NOT BE ADVISORY, so the new drift rule must be `info`. | `artifact_core.drift_exit_code`: "return 1 if any(getattr(d, 'severity', '') != 'info' for d in drift) else 0", documented as "only error/warning-class findings drive the nonzero exit". `check_engine` states the same constraint repeatedly, e.g. "`drift_exit_code` exempts ONLY `info`, so a `warning` grandfather tier would exit 1 on every clean tree". |
| F-7 | A canonical model token is `[a-z0-9]+` with no exceptions, so a syntax gate is both safe and necessary once the vocabulary gate is relaxed. A dot in a token would change the filename's facet arity and make the name unparseable. | All 13 members of `MODELS` match `[a-z0-9]+` (`all(...) -> True`), with zero non-alphanumeric canonical tokens, while `KINDS` DOES contain hyphens (`reconciliation-report`), so the two vocabularies have genuinely different token shapes. `parse_name` splits the stem on `.` and refuses more than three dotted segments. |
| F-8 | The loader MUST cache, because `normalize_model` sits in a hot scan loop: it runs at least twice per doc (`parse_name` plus `validate_frontmatter`), so at least 260 times per index run over this repo's 130 research files, and a full `aw research index --check` already takes about 2.7s. | `find .aw/records/research -name '*.md'` -> 130 files; `parse_name` calls `normalize_model` for the facet and `validate_frontmatter` calls it for the `model:` key; measured `time aw research index --check` -> `real 0m2.754s`. |
| F-9 | ONE OF THE ITEM'S PREMISES IS FACTUALLY WRONG and drops a whole packaging decision from this plan. The item says there is "NO package data in `pyproject.toml` (packages = only `agent_workflows`)" so "shipping a package-default data file needs a packaging decision". Measured: hatchling already ships non-`.py` files inside the package automatically, with no `force-include` entry. | Built the wheel from this worktree: the wheel contains `agent_workflows/run_dashboard_assets/dashboard.css`, `.../dashboard.js`, `agent_workflows/run_analytics_assets/app.css`, `.../app.js`, none of which appear in the `force-include` block (which maps only `.aw/system`). So `agent_workflows/data/research-models.toml` will ship as-is; `pyproject.toml` is kept in `- Scope-Paths:` only to add the sdist/`include` entry if the sdist proves to need one, and V-08 must state which. |
| F-10 | The `__file__`-relative package-data read idiom already exists in this codebase, so E-02 copies it rather than inventing one. | `run_dashboard._asset` reads `(Path(__file__).parent / ASSETS_DIRNAME / name).read_text(encoding="utf-8")`; `run_analytics_spa` uses the same shape with `Path(__file__).resolve().parent`. |
| F-11 | THE SPEC ALREADY RECORDS THIS EXACT FIX AS ACCEPTED, so the amendment is executing a decision rather than proposing one, and E3's "enumerated" wording is the specific text that must change. | Spec `20260730-2152-01` section 5.4, amendment dated 2026-09-20, names backlog `6b9zd9` and says "The accepted fix is to WARN rather than REFUSE, move the known list out of code into an editable data file (the `.aw/config/local-leaks-allowlist.toml` precedent), and ship a CLI verb that adds a model, at which point requirement E3's 'enumerated' obligation must change too. This amendment is therefore an INTERIM unblock under the existing rule, not an endorsement of it." Requirement E3 currently reads "`<model>` and `<kind>` suffixes are REAL, enumerated vocabularies derived from the corpus". |
| F-12 | This is the SECOND recurrence of one defect, and the first one's own rationale records the same symptom, which is what justifies a structural fix over a third list edit. | Spec section 5.4's 2026-09-08 amendment: as first written the vocabulary "COULD NOT BE NAMED" a high-effort Sonnet or Gemini report and "the contract blocked ingesting real artifacts". The 2026-09-20 amendment then repeats it for `gemini31prodeepthink`. |
| F-13 | Existing test coverage of this vocabulary is nearly absent, and the spec's claim about it is wrong, so E-09 is building coverage rather than extending it. The spec's 2026-09-08 note says "Tests added to tests/test_research_contract.py"; that file does not exist. | `ls tests/ | rg -i research` -> `test_research_archive.py`, `test_research_cmd_create.py`, `test_research_index.py` only. `rg 'gpt56solhigh|gemini38flashhigh|sonnet5high' tests/` -> no matches. The only model-vocabulary assertion in the suite is `tests/test_research_cmd_create.py::test_unknown_model_rejected` (`assertIn("unknown model", err)`), which E-09 must rewrite because this plan deliberately removes that refusal. |
| F-14 | The baseline suite is green before any change, so a later failure is attributable to this work. | Bare `python3 -m pytest` on this worktree at authoring: `3217 passed, 2 skipped, 3 warnings in 70.71s`. |
| F-15 | `research_contract`'s documented purity is already inexact, so making the vocabulary file-backed changes the docstring's accuracy rather than breaking a true invariant. | Module docstring: "This module has no side effects: it does not read the filesystem". `resolve_research_root` in the same module calls `Path(repo_root)`, `res_root.is_dir()`, and imports `record_producers.resolve_record_path`. |

## Proposed changes (ordered, validatable)

1. E-01: add `agent_workflows/data/research-models.toml` seeded to exactly today's vocabulary. Validated by V-01.
2. E-02: add `agent_workflows/model_vocab.py` with the three-layer additive loader reusing the minimal TOML reader. Closes the item's point 4. Validated by V-02.
3. E-03: cache the load per repo root with explicit invalidation. Addresses F-8. Validated by V-03.
4. E-04: warn-not-refuse via a new `recognized` flag, converting `artifact_adopt`'s detector to read it. Closes the item's point 1 without the F-5 regression. Validated by V-04.
5. E-05: make the message teach `aw research add-model` and add a token-syntax refusal. Closes the item's point 2 and F-7. Validated by V-05.
6. E-06: confirm the F-2 index outage is gone end to end. Validated by V-06.
7. E-07: add the `info`-severity unrecognized-model drift rule. Handles the item's stated typo consequence; constrained by F-6. Validated by V-07.
8. E-08: add `aw research add-model`. Closes the item's point 3. Validated by V-08.
9. E-09: new `tests/test_model_vocab.py` plus the three updated test files, including rewriting the one test whose premise this plan removes. Addresses F-13. Validated by V-09.
10. Spec + docs: amend `20260730-2152-01` requirement E3 and section 5.4, and `.aw/records/research/README.md`'s "drawn from the enumerated vocabulary" line. See Spec / documentation sync; validated within V-05 and V-08.

## Deferred / out of scope (with reason)

- `<kind>` REMAINS A CLOSED VOCABULARY and is deliberately not given the same treatment. The backlog item makes this distinction its central argument and it is correct: `<kind>` categories (`research-report`, `findings`, `reconciliation-report`) are defined BY THIS REPO and change only when the repo changes, while `<model>` is extended by the outside world without asking. Opening `<kind>` would let a typo silently create a new category.
  - Carrier-Declined: Nothing is owed. This row records a PROHIBITION on this plan, not outstanding work: closed is the CORRECT shape for a repo-owned vocabulary, so there is no defect to carry and filing an item would misrepresent a settled design decision as debt.
- NO BACKFILL OR RENAME of any existing artifact. The migration is behavior-preserving by construction (E-01 seeds the data file from the current in-code values), every currently valid name stays valid, and F-4 shows the one artifact the item lists as blocked was already fixed by the interim unblock.
  - Carrier-Declined: No future work is owed. The item's "Blocked work" section asks that `i5gj61`'s empty `model:` be fixed "when this lands"; measured (F-4) it is ALREADY `model: gemini31prodeepthink`, so the obligation is discharged and naming a carrier would assert an outstanding task that does not exist.
- NO CHANGE to `MODEL_NORMALIZATIONS`' existing entries or to the reasoning-effort-in-identity rule. The item explicitly requires that decision to survive ("two efforts of one model must not collide on one name"), and the drift map is the part of the old design that genuinely works, so it keeps doing the spelling-consistency job after the membership gate relaxes.
  - Carrier-Declined: Nothing is owed; this is a preservation requirement inherited from the item, already satisfied by E-01 seeding the map verbatim.
- NO PROVENANCE VERIFICATION. F-3 shows the closed list never checked that a named model actually wrote the document, and this plan does not add that check either; it is a genuinely different problem (it would need attested provenance, not a vocabulary) and pretending otherwise would overstate what this fix delivers. The honest claim is that this plan stops refusing TRUE unknown models; it does not start catching FALSE known ones.
  - Carrier-Declined: No future work is owed, so no item is filed. What is absent here is a FEATURE nobody has requested, not a measured defect, and the repository convention is that an unmeasured hunch is not a bug and must not be filed as one. The row exists so a reviewer reads the limitation as a deliberate, stated boundary on what this fix claims rather than as an overlooked gap; a reviewer who wants provenance attestation tracked should say so and it will be filed then.
- NO `aw check` RULE OUTSIDE the research index checker, and no attention-view surfacing of an unrecognized model. E-07 puts the advisory surface exactly where the item asks for it (`aw research index --check`); widening it to the cross-tree view is scope this item does not ask for and would need its own severity argument.
  - Carrier-Declined: Nothing is owed. The item's stated requirement is that "`aw research index --check` should report an unrecognized model as drift", which E-07 satisfies in full; a wider surface was never requested, so there is no gap to carry.

## Scope check

- Over-scope: two files in `- Scope-Paths:` are conditional and must be justified or dropped at execution rather than edited by default. `pyproject.toml` is listed only for a possible sdist `include` entry, and F-9 shows the wheel already ships package data without it, so V-08 must state explicitly whether it was touched and why. `check_engine.py` is listed solely to register one `info`-severity rule id (E-07). Nothing else in this plan touches packaging or the check registry.
- Under-scope: this plan does not make the model facet TRUSTWORTHY, only RECORDABLE (F-3); a doc can still be labelled with a model that did not write it, exactly as today. It also leaves `aw research index`'s refuse-to-write-on-invalid-input behavior intact, so a genuinely malformed doc still blocks the manifest for the whole tree; only the unknown-MODEL cause of that outage is removed, and the broader "one bad doc blocks all 130" design question is not reopened here.

## Required tests / validation

Focused first: `python3 -m pytest tests/test_model_vocab.py tests/test_research_cmd_create.py tests/test_artifact_adopt.py tests/test_research_index.py`. Then the BARE full suite (`python3 -m pytest`, no added flags; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`) with the actual `N passed` summary pasted and compared against the F-14 baseline of `3217 passed, 2 skipped`. The F-1 and F-2 reproductions must be re-run BEFORE implementing and pasted, and the F-2 scratch-repo scenario must be re-run after to show the index writes. Live-corpus read-only checks: `aw research index --check` on this repo before and after, which must not gain any new non-`info` finding, and `aw sanitize --agent` clean given a new tracked data file is added. The `artifact_adopt` facet-detector cases from F-5 must be pasted verbatim post-change as the regression guard.

## Spec / documentation sync

Spec `.aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md` IS AMENDED and is declared in `- Scope-Paths:`. This is required, not optional: requirement E3 currently reads "`<model>` and `<kind>` suffixes are REAL, enumerated vocabularies derived from the corpus (Section 5.4)", and this plan makes `<model>` an OPEN, data-driven vocabulary while leaving `<kind>` enumerated, so E3 must be split to carry the two different shapes. Section 5.4 must record the new mechanism (data file layers, the add verb, warn-not-refuse, the `info` drift rule) and must state that its own 2026-09-20 amendment's "accepted fix ... at which point requirement E3's 'enumerated' obligation must change too" is now DISCHARGED (F-11). The spec's `- Status: implemented` is NOT changed: this amends the BODY only and claims no new implementation of the spec itself, matching the precedent set by the existing `2026-09-23 note (aw specs)` entry on that file. Record the amendment through `aw specs note` rather than hand-editing the history block.

`.aw/records/research/README.md` is also amended: its bullet "`<kind>`: MANDATORY, drawn from the enumerated vocabulary" is fine, but the `[.<model>]` bullet must say the model facet is an OPEN vocabulary, that an unknown model is recorded with a warning, and that `aw research add-model` blesses one. Leaving it unchanged would leave the human-facing README describing the closed-list behavior this plan removes.

No change to spec `5tapom` (research lifecycle reliability): it governs status and shard layout, and this plan touches neither.

## Open questions

### OQ-01: Should a repo-layer config file be able to REMOVE a model token shipped in the package default?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE at authoring: layers are ADDITIVE ONLY, and E-02 states it as a property. The precedent this design is told to copy is explicitly additive ("Neither file is required; both are additive" in `.aw/config/local-leaks-allowlist.toml`), and a removal power would be actively dangerous here in a way it is not for an allowlist: an artifact's model token is embedded in its FILENAME, so deleting a shipped token could make an existing, correctly-named document fail `parse_name` and disappear from the index (the F-2 failure mode, reintroduced by config). Since the whole point of this plan is that the vocabulary must never refuse a real artifact, a config file that can cause exactly that refusal is out.

### OQ-02: Should an unknown model be recorded verbatim, or normalized onto its closest match?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM AN EXISTING RECORDED DECISION: record VERBATIM, never auto-collapse. `research_contract`'s own comment already settles it ("A NEW MODEL IS NOT A SPELLING VARIANT ... the closest-match hint ... is string proximity, not a claim about model identity, and collapsing them would file a report under a model that did not write it"), and spec section 5.4's 2026-09-08 amendment records that the maintainer was OFFERED the cheaper collapsing option and rejected it. F-1 shows why this matters concretely: the current hint maps `gemini4pro` onto `gemini31pro`, a different model. Hence E-05 keeps the proximity hint strictly subordinate and marked as a spelling check.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the full content of the new `agent_workflows/data/research-models.toml`, then paste the output of a command that parses it and compares against the PRE-CHANGE vocabulary, showing set equality for both the 13 model tokens and the 20 normalization entries (for example a printed `sorted(parsed) == sorted(expected) -> True` for each, with the expected values taken from git HEAD's `research_contract`, not from the new loader, so the comparison cannot be circular). State the exact counts found.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a transcript showing, in a scratch repo, (a) `model_vocab.load(root)` with NO repo file returning exactly the package default; (b) after writing `.aw/config/research-models.toml` adding `deepseek4`, that token present AND every package token still present (paste the set-difference proving no package token was lost); (c) a normalization added by the repo layer taking effect. State explicitly WHICH TOML reader was used and, if `leak_sanitizer`'s minimal reader was extended for scalar pairs, paste the diff of that extension and confirm no `tomllib` import and no new dependency was added (`rg -n "tomllib" agent_workflows/` output pasted).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a test transcript proving the file is read ONCE per repo root across many `normalize_model` calls (patch a counter over the read and paste the asserted count for 500 calls), and that the explicit invalidation makes a newly added token visible in the SAME process. Also paste a two-repo case showing repo A's added token is NOT visible from repo B, proving the cache is keyed on the resolved root. Paste `time aw research index --check` on this repo before and after the change and state the delta against the F-8 baseline of about 2.7s.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the output of `normalize_model` over at least `sonnet5`, `deepseek4`, `gemini4pro`, `gpt55high`, showing `ok` and `recognized` for each (known -> recognized True; unknown-but-well-formed -> ok True, recognized False, value equal to the input token). Then paste the F-5 regression cases verbatim: `suggest_metadata` for `some-report.gemini31prohigh.agy.md` (must still be `gemini31prohigh`, NOT `agy`), `some-report.agy.md` (must still be `None`), `some-report.research-report.md` (must still be `None`), and `some-report.gemini4pro.agy.md` (state what it now proposes and why that is correct). Enumerate ALL FOUR `normalize_model` call sites (`research_cmd.plan_new`, `research_cmd.plan_new_comparison`, `research_refs`, `artifact_adopt.suggest_metadata`, plus the two in-module callers `parse_name` and `validate_frontmatter`) and state for each which predicate it now reads and why.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the exact new warning string for an unknown token, showing it contains `aw research add-model` and that any proximity hint is clearly subordinate. Paste refusals for malformed tokens (`"gemini 4"`, `"a.b"`, and one uppercase/underscore case) showing `ok=False` and a message that says MALFORMED rather than merely unknown. Paste the amended requirement E3 text and the new section 5.4 paragraph from the spec (the `git diff` of the spec file), and confirm `- Status: implemented` is unchanged on that spec.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the BEFORE reproduction (re-run at execution time against HEAD: a scratch repo with an unknown-model doc in frontmatter, a second with the unknown model in the filename facet, and a known-model control, showing `aw research index` exit 1 and `INDEX.json` absent) and then the AFTER run showing exit 0, `INDEX.json` written, and the unknown-model doc present in it with `model` recorded verbatim (paste the relevant INDEX.json entry). Confirm the control doc is still indexed correctly.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `aw research index --check` in a scratch repo with an unknown-model doc showing the unrecognized-model finding AND exit 0, then paste the same command in a repo with a genuinely broken frontmatter field showing exit 1, proving real drift still fails. Paste the `check_engine` registration showing the severity is `info`, and paste `aw research index --check` on THIS repo before and after the change showing no new non-`info` finding appeared.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the full round trip: `aw research add-model deepseek4` with no `--apply` (showing a preview and that the file is unchanged or absent), then `--apply` (exit 0), then the resulting `.aw/config/research-models.toml` content, then a FRESH process showing `normalize_model("deepseek4").recognized` is True. Paste a `--normalize-from` case adding a drift spelling and show it resolving. Confirm the packaged default file was NOT modified (`git diff --stat agent_workflows/data/research-models.toml` empty after the add). State explicitly whether `pyproject.toml` was modified: if yes paste the diff and the reason; if no, say so and cite the F-9 wheel measurement, re-run at execution time, showing `agent_workflows/data/research-models.toml` present in the built wheel. Paste `aw sanitize --agent` exit status for the new tracked file.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the new tests FAILING against HEAD first (assertion text, not a summary claim), then the focused `python3 -m pytest tests/test_model_vocab.py tests/test_research_cmd_create.py tests/test_artifact_adopt.py tests/test_research_index.py` output with its `N passed` line, then the BARE `python3 -m pytest` summary line compared against the F-14 baseline `3217 passed, 2 skipped`. Paste the `git diff` for `tests/test_research_cmd_create.py` showing how `test_unknown_model_rejected` was REPLACED (not deleted) and state what the replacement asserts. Confirm explicitly that no new test reads production source text via `inspect`, `ast`, regex over source, or substring search, and that none asserts on caller counts or module line counts (paste `rg -n "inspect|read_text\(.*\.py" tests/test_model_vocab.py` output as the check).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Nine E-items across three task groups is inside both version-1 thresholds (5 task groups, 18 `E-*` leaves), and the work is one cohesive change: a single vocabulary becomes data-driven, and the loader, the validator, the add verb, and the contract text are not independently shippable (warn-not-refuse without the add verb leaves the user unable to bless a model; the data file without the loader changes nothing).

Commit only the `- Scope-Paths:` files through `aw commit t38a4o -- <paths>`, never `git add -A`, and never push. This plan carries `- Blocks-Release: next`, inherited from backlog `6b9zd9`.

BEFORE IMPLEMENTING, re-run the F-1 and F-2 reproductions: if an unknown model no longer refuses, or no longer blocks the index write, STOP and report rather than building a fix for a defect that has moved. F-4 is the precedent for this instruction, since the interim unblock for `gemini31prodeepthink` landed after the item was filed and the item's "Blocked work" is already discharged.

THIS PLAN AMENDS AN APPROVED-AND-IMPLEMENTED SPEC (`20260730-2152-01`), declared in `- Scope-Paths:` so both runners announce it before the run and reconcile it after. The amendment is executing a decision that spec already records as accepted (F-11), not proposing a new contract.

Backlog `6b9zd9` goes to `graduated`, not `done`, at authoring time; it closes only when this plan is executed and the release gate is provably carried. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is unconditionally owed, but under `aw oc run`/`aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-09 carry pasted evidence.
