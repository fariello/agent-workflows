# IPD: Make the research model vocabulary an open, data-driven set: warn instead of refusing an unknown model, ship an add verb, and stop one new model from blackholing the whole index

- Date: 2026-09-28
- Kind: child
- Concern: `research_contract.MODELS` is a closed frozenset and `normalize_model` is a bare membership test with no escape hatch, so every model the outside world ships next (Gemini 4, GPT-5.5, DeepSeek, any new reasoning tier) is REFUSED until someone edits Python and amends a spec. Measured here, the consequence is worse than the filed item reports: one doc carrying an unknown model makes `aw research index` refuse to write INDEX.json AT ALL, so a single new model blackholes the manifest for all 130 docs.
- Scope: turn `<model>` into an OPEN vocabulary: an unknown token is recorded with a loud warning instead of being rejected, the known list moves into a tracked editable data file with a shipped package default read against an EXPLICIT repo root (never one inferred from cwd), `aw research add-model` adds a token in one command, and `aw research index --check` gains an advisory drift rule so a typo stays mechanically visible without blocking the manifest write. Amends spec `20260730-2152-01` requirement E3 and section 5.4, which currently make the vocabulary an enumerated `[Must]`. Does NOT touch `<kind>` (a genuinely closed, repo-owned vocabulary), `MODEL_NORMALIZATIONS`' collapsing behavior, the reasoning-effort-in-identity rule, `<status>`, or any existing artifact's name.
- Scope-Paths: agent_workflows/research_contract.py, agent_workflows/model_vocab.py, agent_workflows/data/research-models.toml, agent_workflows/research_cmd.py, agent_workflows/artifact_adopt.py, agent_workflows/research_index.py, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/leak_sanitizer.py, pyproject.toml, tests/test_model_vocab.py, tests/test_research_cmd_create.py, tests/test_artifact_adopt.py, tests/test_research_index.py, .aw/records/specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md, .aw/records/research/README.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 6b9zd9
- Blocks-Release: next
- Set: modelvocab
- Order: 1
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: t38a4o

## Workflow history
- 2026-09-30 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: t38a4o verified (set modelvocab, attempt 1). [Scope reconciliation - in-scope-unmodified agent_workflows/research_cmd.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified pyproject.toml: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified tests/test_artifact_adopt.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified tests/test_research_index.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (aw set): plan-review: revisions applied; PR-701..PR-706 fixed

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-701 (blocker), PR-702, PR-703, PR-704 (high), PR-705 (medium), PR-706 (low), all FIXED. Findings recorded in `.aw/records/reviews/20260928-modelvocab-01-t38a4o-...review.md`. F-1 and F-2 reproduced verbatim; the plan's `recognized`-flag design (F-5) is upheld. Three authored items would each have shipped a defect: E-07's `info` advisory would have SILENTLY restored the F-2 index outage because severity governs only the `--check` branch (now emitted in `check_drift`, demonstrated); E-05's `[a-z0-9]+` gate left the same outage for a hyphenated unknown model (now `[a-z0-9-]+`, recorded as OQ-03); and E-02/E-03 presupposed a repo root nothing receives, where the cwd-climb shortcut validates one repo against another's vocabulary (new E-10 owns it). E-08 gained the `CommandDeclaration` whose absence fails the suite. Four measured digits corrected, and the validation items now demand re-derivation rather than comparison against a plan-written number.
- 2026-09-28 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `6b9zd9`. The item's four required fixes are adopted as specified; measurement during authoring found the blast radius materially LARGER than filed (F-2: total index outage, not a naming refusal) and found one of the item's premises factually wrong (F-9: package data already ships, so no packaging decision is owed), both recorded in Findings.

## Goal

Make `<model>` behave like the open set it is: a token from a vendor this repo has never heard of RECORDS with a warning that teaches the exact command to bless it, rather than refusing a correct artifact and taking the research manifest down with it. Keep the one thing the closed list legitimately bought, consistent spelling, by leaving `MODEL_NORMALIZATIONS` in charge of drift and by making an unrecognized token visible as advisory drift in `aw research index --check`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the data file and its loader

- [x] E-01 Add `agent_workflows/data/research-models.toml`, a tracked, commented data file carrying the canonical model tokens and the drift-spelling map, seeded with EXACTLY today's `research_contract.MODELS` and `MODEL_NORMALIZATIONS` so the migration is behavior-preserving by construction. RE-DERIVE BOTH SETS FROM HEAD AT EXECUTION TIME; the bar is set EQUALITY, not a transcribed count. For context only, measured at review: `len(MODELS) == 13` and `len(MODEL_NORMALIZATIONS) == 22` (the authored figure of 20 was wrong, which is exactly why the equality assertion and not the digit is the bar). Emit only shapes the repo's minimal TOML reader round-trips AFTER the E-02 extension: flat string arrays and flat `key = "value"` pairs, following the `.aw/config/local-leaks-allowlist.toml` precedent, whose own header says "It is read by a minimal TOML reader (3.9-safe, no tomllib), so keep entries to flat string arrays and flat booleans". Represent the normalization MAP as a flat `[normalizations]` section of `from = "to"` pairs rather than nested tables, and note the reader is SECTION-BLIND (F-24), so no key name may repeat across sections. Carry the same commentary the code holds today, specifically the "A NEW MODEL IS NOT A SPELLING VARIANT" rule and the reasoning-effort-in-identity rule, because that is the review guidance a human editing this file needs and it must not be lost in the move.
  - Depends on: none
  - Expected outcome: a new data file whose parsed content equals today's in-code vocabulary exactly; `sorted(parsed_models) == sorted(research_contract.MODELS)` and the parsed normalization map equals `MODEL_NORMALIZATIONS`.
  - Execution state: performed

- [x] E-02 Add `agent_workflows/model_vocab.py` with the READER only: resolve the effective vocabulary by merging three ADDITIVE layers, lowest precedence first. The layers are the PACKAGE DEFAULT `agent_workflows/data/research-models.toml` (always present, read via `Path(__file__).parent / "data"`, the same `__file__`-relative idiom `run_dashboard._asset` already uses for `run_dashboard_assets`), then the TARGET REPO file `.aw/config/research-models.toml` when present, then the per-user layer beside the repo config, mirroring the allowlist's "never-committed, per-user layer" split. Merging is ADD-ONLY: a later layer contributes tokens and normalizations and can never delete a package token, which is what stops an artifact already named under a shipped token from becoming unparseable through a config edit (see OQ-01). Reuse the repo's existing minimal TOML reader rather than writing a second one, because `leak_sanitizer._parse_simple_toml_lists` is the established 3.9-safe parser and the support floor forbids `tomllib` (3.11+). MEASURED AT REVIEW, THE EXTENSION IS REQUIRED AND NOT CONDITIONAL, so do not plan for the branch where it turns out unnecessary: `_parse_simple_toml_lists` reads ONLY `key = [...]` arrays and `_parse_simple_toml_bools` ONLY `key = true|false`, so on the E-01 file shape the pair `gpt-56 = "gpt56"` yields `{}` from both (`lists reader: {'models': [...]}`, `bools reader: {}`). Extend `leak_sanitizer` in place with a flat-scalar-pairs reader beside the flat-array one (declared in `- Scope-Paths:`), and note the reader is SECTION-BLIND (measured: two `models =` keys under different `[section]` headers collapse to last-wins), so the E-01 file must not reuse one key name across sections and the scalar-pairs reader must be given the section it should read from, or the file must use unambiguous key names. The WRITER belongs to E-08, not here.
  - Depends on: E-01
  - Expected outcome: `model_vocab.load(repo_root)` returns the merged `(models, normalizations)`; with no repo file present the result equals the package default; with a repo file adding `deepseek4`, that token is present and every package token still is.
  - Execution state: performed

- [x] E-10 THREAD THE REPO ROOT TO THE VALIDATOR, which is the load-bearing wiring E-02/E-03 presuppose and which no other item delivers. Measured at review: `normalize_model(token)` takes ONLY a token, and so do its two in-module callers `parse_name(filename)` and `validate_frontmatter(data)`; none receives a repo root, so `model_vocab.load(repo_root)` has no root to be given and the E-03 cache has no key. THE CWD-CLIMBING SHORTCUT IS WRONG AND MUST NOT BE TAKEN: `research_index._roots` resolves through `project_context.resolve_verb_repo_root(args.dir)`, and measured with cwd in repo A and `--dir` repo B, the climbed root and the operated-on root DIFFER (`SAME ROOT: False`), so a cwd-climbing loader validates repo B's documents against repo A's blessed tokens. Choose ONE explicit mechanism and state which in V-10: (a) add an OPTIONAL keyword `repo_root` to `normalize_model`, `parse_name` and `validate_frontmatter`, threaded from each caller that already holds a root; or (b) an explicit process-scoped ACTIVE-ROOT set once per verb by the CLI entry point (`research_index._roots` and its siblings) and read by `model_vocab`, never inferred from cwd. Either way the DEFAULT with no root supplied must be the PACKAGE DEFAULT ALONE, never a cwd climb, so a library caller with no root gets the shipped vocabulary rather than an accidental one. Call-site census measured at review, to size the threading: `normalize_model` 4 production calls in 3 files (`artifact_adopt`, `research_cmd` x2, `research_refs`); `parse_name` 14 production calls in 5 files plus 7 test calls in 2 files; `validate_frontmatter` 1 production call plus 7 test calls in 3 files. If option (a) is chosen, every one of those calls keeps working unchanged because the parameter is optional; that is the point of making it optional.
  - Depends on: E-02
  - Expected outcome: with repo A blessing `deepseek4` and repo B blessing nothing, a validation run scoped to repo B does NOT recognize `deepseek4` while one scoped to repo A does, with cwd held constant in A for both; and `normalize_model("deepseek4")` with NO root supplied returns unrecognized (package default), never a cwd-derived answer.
  - Execution state: performed

- [x] E-03 Give the loader a per-repo-root CACHE so the vocabulary is read from disk ONCE per process rather than per token. This is load-bearing, not an optimization flourish: `normalize_model` is called at least twice per document (`parse_name` for the filename facet and `validate_frontmatter` for the `model:` key), which is at least 260 calls for this repo's 130 research docs in a single `aw research index` run (F-8), and a naive loader would turn each into a file stat plus parse. Key the cache on the resolved repo root and expose an explicit invalidation entry point for the add verb and for tests, so a write through E-05 is visible to a subsequent read in the same process. Do NOT cache on a mutable default argument or a module-level dict keyed by a relative path; a test that chdirs between repos must not see another repo's vocabulary.
  - Depends on: E-10
  - Expected outcome: with a counter patched over the file read, a loop of 500 `normalize_model` calls performs exactly one read per repo root; after the invalidation call a subsequent read picks up a newly added token.
  - Execution state: performed

### Task group 2: warn instead of refuse, without breaking the detector

- [x] E-04 Change `research_contract.normalize_model` to WARN-NOT-REFUSE, and do it WITHOUT breaking the two callers that legitimately depend on a false result. Today the function returns `VocabResult(False, None, sugg, "unknown model ...")` for anything not in `MODELS`, and two call sites read that `ok=False` as a real answer rather than as an error: `artifact_adopt.suggest_metadata` loops over every trailing filename facet and uses `res.ok` to DECIDE WHICH FACET IS THE MODEL (measured F-5: `some-report.gemini31prohigh.agy.md` yields model `gemini31prohigh` precisely because `agy` returns not-ok), and `research_index._doc_entry` turns a not-ok result into blocking drift. So a blanket flip of `ok` to `True` would make `artifact_adopt` label `agy` (or the kind facet) as the model, which is a NEW provenance-corruption bug in the very field this plan exists to protect. Resolve it by distinguishing RECOGNIZED from ACCEPTED: extend `VocabResult` with a `recognized: bool` (defaulting so existing positional construction and every `normalize_kind`/`normalize_status` caller are untouched), have the model path return `ok=True, recognized=False, value=<the normalized token>` with a warning message for an unknown-but-well-formed token, and convert `artifact_adopt`'s facet detector to test `recognized` instead of `ok`. State in V-04 which predicate each of the four `normalize_model` call sites now reads.
  - Depends on: E-03
  - Expected outcome: `normalize_model("deepseek4")` returns ok, `recognized=False`, `value="deepseek4"`, and a message naming the add command; `normalize_model("sonnet5")` returns ok with `recognized=True`; `artifact_adopt.suggest_metadata("x.gemini31prohigh.agy.md", ...)` still proposes `gemini31prohigh` and NOT `agy`.
  - Execution state: performed

- [x] E-05 Make the warning TEACH THE FIX, which the backlog item requires as its own numbered point and which the current message fails: `unknown model 'gemini4pro'; did you mean 'gemini31pro'?` leaves the user exactly where the defect found them, and its closest-match hint actively misleads, because `gemini31pro` is a DIFFERENT MODEL and accepting the suggestion would file a report under a model that did not write it. The new message must name the exact command (`aw research add-model <token>`) and must keep the proximity hint clearly subordinate to it, marked as a spelling check rather than a recommendation. Also REJECT a malformed token rather than recording it, BUT THE GATE MUST ADMIT A HYPHEN, which the authored version got wrong and which review measured as a residual outage. A canonical token is `[a-z0-9]+` (F-7), and the authored rule refused a hyphen on that basis; measured, that REINTRODUCES the F-2 outage for a hyphenated unknown model. A filename facet is split on `.`, so a hyphen is legal INSIDE a facet: `...slug.gemini-4-pro.research-report.md` parses its model facet as `gemini-4-pro`, which has no `MODEL_NORMALIZATIONS` entry (only KNOWN spellings do), so a hyphen-refusing gate returns `ok=False`, `parse_name` fails, `_doc_entry` emits `name-invalid`, and the regenerate branch blocks `INDEX.json` for the WHOLE tree. Measured at review: a scratch repo with one `gemini-4-pro` doc plus one `sonnet5` control gave `exit: 1  INDEX.json written: False`. Hyphenated spellings are not hypothetical, since 21 of the 22 `MODEL_NORMALIZATIONS` KEYS are hyphenated (`gpt-56`, `gemini-31-pro-deep-think`, `sonnet-5-high`), which is the corpus evidence that vendors and humans write them. SO: the accepted syntax gate is `[a-z0-9-]+`, refusing a DOT (the only character that changes facet arity), whitespace, underscore, uppercase-after-lowering, and empty. Verified at review that admitting the hyphen is arity-safe: `format_name` with model `gemini-4-pro` produces a 3-segment stem that `parse_name` round-trips back to `model='gemini-4-pro'`, and `a.b`/`gemini 4`/`gemini_4`/`""` all still fail the gate. RECORD THE TOKEN VERBATIM, do not auto-collapse the hyphen: generalized hyphen-stripping reproduces only 20 of the 22 existing mappings (`gemini31prodeepthink-high` and `chatgpt` diverge), so a blanket strip would contradict two recorded decisions, and OQ-02 already forbids auto-collapsing onto a different model. That refusal is a SYNTAX check, not a vocabulary check, and it is the one place a hard refusal stays correct.
  - Depends on: E-04
  - Expected outcome: the unknown-token message contains `aw research add-model`; `normalize_model("gemini-4-pro")` returns `ok=True` with `recognized=False` and `value="gemini-4-pro"` (hyphen ADMITTED, recorded verbatim); `normalize_model("gemini 4")`, `normalize_model("a.b")`, `normalize_model("gemini_4")` and `normalize_model("")` return `ok=False` with a message saying MALFORMED.
  - Execution state: performed

- [x] E-06 Stop an unrecognized model from taking the WHOLE INDEX DOWN, which is the most damaging half of this defect and the half the filed item did not know about. Measured (F-2): `research_index.run_index` reads "Refuse to write over invalid input; report and exit nonzero" and returns 1 before writing, so with one unknown-model doc present `INDEX.json` is never created and all 130 docs lose the manifest that `aw research find` and the attention scanner read. After E-04 an unknown model is no longer a `validate_frontmatter` error or a `parse_name` failure, so the doc INDEXES normally; this item's work is to verify that end to end and to add the advisory drift rule below, not to weaken the refuse-on-invalid-input rule, which stays correct for genuinely invalid input.
  - Depends on: E-05
  - Expected outcome: in a scratch repo containing one unknown-model doc plus one known-model doc, `aw research index` exits 0, writes `INDEX.json`, and the unknown-model doc appears in it with its `model` recorded verbatim.
  - Execution state: performed

- [x] E-07 Add an ADVISORY drift rule reporting an unrecognized model in `aw research index --check`, registered at `info` severity in `check_engine.RULE_REGISTRY`. The severity is load-bearing and is not a style choice: `artifact_core.drift_exit_code` returns `1 if any(getattr(d, "severity", "") != "info" for d in drift) else 0`, so `info` is the UNIQUE severity that does not fail the gate, and registering this as `warning` would make every repo carrying a not-yet-blessed model exit nonzero, which is the same fail-closed behavior this plan is removing. Registration is also NOT optional bookkeeping: an unregistered rule id falls through to `_DEFAULT_RULESPEC` at severity `error`. This is what keeps the backlog item's own stated consequence handled: a typo like `sonnet5hgih` is now RECORDED rather than rejected, so it needs a mechanical surface that still notices it.

  EMIT THE FINDING IN `check_drift`, NOT IN `_doc_entry`/`_scan_docs`, AND THE `info` SEVERITY DOES NOT SAVE YOU FROM THIS. Measured at review: `info` governs the `--check` branch ONLY, because `drift_exit_code` is consulted there alone; the REGENERATE branch of `research_index.run_index` tests raw truthiness ("Refuse to write over invalid input", `if drift: ... return 1`) and never reads severity. Simulating the post-E-04/E-06/E-07 state with the advisory emitted from `_doc_entry` gave `drift_exit_code(drift) = 0` (so `--check` passed) while `aw research index` returned `exit: 1` with `INDEX.json written: False`: the advisory rule silently RESTORES the exact F-2 outage E-06 exists to remove, and it does so for an `info` finding that fails nothing. Emitting it in `check_drift` instead confines it correctly, because `check_drift` calls `_scan_docs` and then APPENDS its own rule families (stale-index, dangling-citation, stale-state-to-promote) while the regenerate branch calls `_scan_docs` DIRECTLY and never calls `check_drift`. Verified: with the advisory emitted in `check_drift`, the same scratch repo gives regenerate `exit: 0  INDEX.json written: True  indexed models: ['sonnet5', 'gemini4pro']` and `--check` exit 0 with the advisory still reported. That location also serves `aw check research`, which reaches the same producer (`check_engine` calls `_ridx.check_drift(repo_root, dirs[0])`), so one emission covers both surfaces.
  - Depends on: E-06
  - Expected outcome: with an unknown-model doc present, `aw research index --check` reports the unrecognized model and still exits 0; the SAME repo's bare `aw research index` exits 0 and writes `INDEX.json` containing the unknown-model doc; with a hand-broken frontmatter field present `--check` still exits 1, proving the advisory rule did not soften real drift.
  - Execution state: performed

### Task group 3: the add verb, packaging, and the contract text

- [x] E-08 Add the `aw research add-model <token>` CLI verb (with optional `--normalize-from <spelling>` for a drift alias and the repo's standard dry-run-by-default plus `--apply`, matching `research new`'s documented "'new' and 'new-comparison' are dry-run by default; pass --apply to write" convention). It writes the TARGET REPO layer `.aw/config/research-models.toml`, never the packaged default, atomically through `artifact_core.atomic_write` (which passes a non-`.md` path through byte-for-byte, so the TOML is not markdown-normalized), creating the file with its explanatory header when absent. Wire it into `cli.py` beside the existing `research` subparsers and add its one-line entry to the command-help table that already carries `research new` / `research mv` / `research promote`. Registering the leaf in `command_surface.COMMAND_INVENTORY` is part of ADDING the verb rather than separate bookkeeping, so it belongs in this same pass: measured at review by adding a bare `research add-model` leaf to the built parser, `find_undeclared_leaves` went from `[]` to `['research add-model']` (and `conformance_matrix.build_matrix().undeclared` likewise), which makes `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` fail. Declare it as a `mutation` with `mutation_gate="dry_run_default"` to match its `--apply` behavior and the neighbouring `research mv` / `research promote` declarations, carrying `--normalize-from`/`--apply` in `legacy_flags`. The written file lives at `.aw/config/research-models.toml`, a TRACKED repo layer like `local-leaks-allowlist.toml` (verified at review that the path is NOT gitignored, since `.gitignore` covers `.aw/state/` and `.aw/config/local.json` only), which the verb writes but must never stage or commit. This is the backlog item's point 3, whose whole purpose is that blessing a model becomes one terminal command instead of a Python edit plus a spec amendment.
  - Depends on: E-07
  - Expected outcome: `aw research add-model deepseek4 --apply` exits 0, creates or extends `.aw/config/research-models.toml`, and a subsequent `normalize_model("deepseek4")` in a fresh process returns `recognized=True`; without `--apply` it writes nothing and previews the change; `find_undeclared_leaves(cli._build_parser())` is still empty.
  - Execution state: performed

- [x] E-09 Add `tests/test_model_vocab.py` and extend the three affected existing test files, all as OUTCOME tests that drive real functions and CLI commands and assert on real outputs, exit codes, and file bytes (never by reading source text or counting symbols). The required coverage is enumerated below. Note that `tests/test_research_cmd_create.py::test_unknown_model_rejected` asserts `assertIn("unknown model", err)` on a refusal this plan deliberately removes, so it must be REPLACED (never silently deleted) by a test that an unknown model is now accepted and recorded while a malformed one is still refused, with the replacement described in V-09. That one assertion is the ONLY model-vocabulary coverage in the suite today (F-13), so everything else listed here is NEW coverage.

  Coverage list, one row per behavior:
  - E-01 seed equivalence against git HEAD's values.
  - Three-layer merge, including the add-only no-deletion property.
  - E-10 two-repo root scoping (repo A's blessed token NOT recognized in repo B, cwd held in A) plus the no-root-supplied package-default case.
  - E-03 single-read cache and its explicit invalidation.
  - The unknown-token warning containing `aw research add-model`.
  - Hyphen ADMITTED (`gemini-4-pro` recorded verbatim), beside malformed refusal for a dot, a space, an underscore and empty.
  - The F-5 `artifact_adopt` facet-detector regression (`gemini31prohigh` chosen over `agy`).
  - A real `aw research index` run proving the F-2 outage is gone, in three variants that must ALL write the manifest: plain unknown model, hyphenated unknown model (F-20), and advisory-present (F-21).
  - The `info`-severity `--check` exit-0 behavior, with a real-drift exit-1 control.
  - `find_undeclared_leaves` still empty after E-08 adds its leaf.
  - The `add-model` round trip, including `--normalize-from`.
  - Depends on: E-08
  - Expected outcome: new and updated tests pass; the bare full suite passes with its `N passed` line pasted; no test inspects production source text.
  - Execution state: performed

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
| F-7 | A CANONICAL model token is `[a-z0-9]+` with no exceptions, so a syntax gate is both safe and necessary once the vocabulary gate is relaxed. A dot in a token would change the filename's facet arity and make the name unparseable. NARROWED AT REVIEW: this describes the CANONICAL set only and does NOT license refusing a hyphen in an INPUT token, which F-20 measures as a residual outage; the accepted gate is `[a-z0-9-]+`. | All 13 members of `MODELS` match `[a-z0-9]+` (`all(...) -> True`), with zero non-alphanumeric canonical tokens, while `KINDS` DOES contain hyphens (`reconciliation-report`), so the two vocabularies have genuinely different token shapes. `parse_name` splits the stem on `.` and refuses more than three dotted segments. But 21 of 22 `MODEL_NORMALIZATIONS` KEYS are hyphenated, so hyphenated INPUT is the corpus norm even though canonical OUTPUT is not (F-20). |
| F-8 | The loader MUST cache, because `normalize_model` sits in a hot scan loop. CORRECTED AT REVIEW: the authored per-doc figure was wrong (it assumed both in-module callers fire for every doc, but a doc with no model FACET skips the `parse_name` call and a doc whose `model:` is empty skips the `validate_frontmatter` one), while the whole-run total is right and the conclusion is unchanged. The timing baseline also drifted and is restated. | Instrumented at review with a counter over `normalize_model`: 130 research `.md` files, 123 indexed entries, **130 calls for ONE `_scan_docs` pass (1.06 per doc, not 2)**, and **267 calls for a whole `aw research index --check` run** (which scans more than once), so the "at least 260 per run" premise holds and an uncached loader would mean 267 reads. Timing re-measured at review: `time aw research index --check` -> `real 0m1.480s`, NOT the authored 2.7s; V-03 compares against 1.48s. |
| F-9 | ONE OF THE ITEM'S PREMISES IS FACTUALLY WRONG and drops a whole packaging decision from this plan. The item says there is "NO package data in `pyproject.toml` (packages = only `agent_workflows`)" so "shipping a package-default data file needs a packaging decision". Measured: hatchling already ships non-`.py` files inside the package automatically, with no `force-include` entry. | Built the wheel from this worktree: the wheel contains `agent_workflows/run_dashboard_assets/dashboard.css`, `.../dashboard.js`, `agent_workflows/run_analytics_assets/app.css`, `.../app.js`, none of which appear in the `force-include` block (which maps only `.aw/system`). So `agent_workflows/data/research-models.toml` will ship as-is; `pyproject.toml` is kept in `- Scope-Paths:` only to add the sdist/`include` entry if the sdist proves to need one, and V-08 must state which. |
| F-10 | The `__file__`-relative package-data read idiom already exists in this codebase, so E-02 copies it rather than inventing one. | `run_dashboard._asset` reads `(Path(__file__).parent / ASSETS_DIRNAME / name).read_text(encoding="utf-8")`; `run_analytics_spa` uses the same shape with `Path(__file__).resolve().parent`. |
| F-11 | THE SPEC ALREADY RECORDS THIS EXACT FIX AS ACCEPTED, so the amendment is executing a decision rather than proposing one, and E3's "enumerated" wording is the specific text that must change. | Spec `20260730-2152-01` section 5.4, amendment dated 2026-09-20, names backlog `6b9zd9` and says "The accepted fix is to WARN rather than REFUSE, move the known list out of code into an editable data file (the `.aw/config/local-leaks-allowlist.toml` precedent), and ship a CLI verb that adds a model, at which point requirement E3's 'enumerated' obligation must change too. This amendment is therefore an INTERIM unblock under the existing rule, not an endorsement of it." Requirement E3 currently reads "`<model>` and `<kind>` suffixes are REAL, enumerated vocabularies derived from the corpus". |
| F-12 | This is the SECOND recurrence of one defect, and the first one's own rationale records the same symptom, which is what justifies a structural fix over a third list edit. | Spec section 5.4's 2026-09-08 amendment: as first written the vocabulary "COULD NOT BE NAMED" a high-effort Sonnet or Gemini report and "the contract blocked ingesting real artifacts". The 2026-09-20 amendment then repeats it for `gemini31prodeepthink`. |
| F-13 | Existing test coverage of this vocabulary is nearly absent, and the spec's claim about it is wrong, so E-09 is building coverage rather than extending it. The spec's 2026-09-08 note says "Tests added to tests/test_research_contract.py"; that file does not exist. | `ls tests/ | rg -i research` -> `test_research_archive.py`, `test_research_cmd_create.py`, `test_research_index.py` only. `rg 'gpt56solhigh|gemini38flashhigh|sonnet5high' tests/` -> no matches. The only model-vocabulary assertion in the suite is `tests/test_research_cmd_create.py::test_unknown_model_rejected` (`assertIn("unknown model", err)`), which E-09 must rewrite because this plan deliberately removes that refusal. |
| F-14 | The baseline suite is green before any change, so a later failure is attributable to this work. RE-MEASURED AT REVIEW because the authored baseline had already drifted (other plans landed between authoring and review), which is why the bar is the RE-DERIVED baseline and never a transcribed digit. | Authored: `3217 passed, 2 skipped, 3 warnings in 70.71s`. Re-measured at review on this lane worktree: bare `python3 -m pytest` -> `3246 passed, 2 skipped, 3 warnings in 50.64s`. V-09 compares against a baseline RE-RUN at execution time, not against either digit here. |
| F-15 | `research_contract`'s documented purity is already inexact, so making the vocabulary file-backed changes the docstring's accuracy rather than breaking a true invariant. | Module docstring: "This module has no side effects: it does not read the filesystem". `resolve_research_root` in the same module calls `Path(repo_root)`, `res_root.is_dir()`, and imports `record_producers.resolve_record_path`. |
| F-20 | REVIEW FINDING (new): the authored E-05 syntax gate would have left a RESIDUAL F-2 OUTAGE for a hyphenated unknown model, so the plan's headline fix would have been incomplete in the most common real spelling. A facet is split on `.`, so a hyphen is legal inside one; `gemini-4-pro` has no normalization entry, so a `[a-z0-9]+` gate refuses it as malformed, `parse_name` fails, and the regenerate branch blocks the whole manifest. | Simulated the exact authored E-04+E-05 contract over a scratch repo holding one `gemini-4-pro` doc plus one `sonnet5` control: `20260901-...-hyphen-unknown.gemini-4-pro.research-report.md: name-invalid: malformed model token 'gemini-4-pro'`, then `exit: 1  INDEX.json written: False`. Corpus evidence that hyphens are the real-world spelling: **21 of the 22 `MODEL_NORMALIZATIONS` keys are hyphenated**. Arity safety of admitting the hyphen: `format_name` with model `gemini-4-pro` yields a 3-segment stem that `parse_name` round-trips to `model='gemini-4-pro'`, while `a.b`, `gemini 4`, `gemini_4` and `""` all still fail an `[a-z0-9-]+` gate. Generalized hyphen-stripping was rejected: it reproduces only 20 of 22 existing mappings (`gemini31prodeepthink-high`, `chatgpt` diverge). E-05 corrected. |
| F-21 | REVIEW FINDING (new, BLOCKER): the authored E-07 would have SILENTLY RESTORED the F-2 outage that E-06 exists to remove, and its `info` severity would not have prevented it, because `info` governs the `--check` branch alone. `run_index`'s REGENERATE branch tests raw truthiness and never reads severity, while `_doc_entry`/`_scan_docs` drift flows into BOTH branches. | Simulated post-E-04/E-06/E-07 with the advisory emitted from `_doc_entry`: `drift_exit_code(drift) = 0` (so `--check` passed) yet `aw research index` gave `exit: 1`, `INDEX.json written: False`. Re-simulated with the advisory emitted from `check_drift` instead: regenerate gave `exit: 0`, `INDEX.json written: True`, `indexed models: ['sonnet5', 'gemini4pro']`, and `--check` exit 0 with the advisory still printed. `check_engine` reaches the same producer (`_ridx.check_drift(repo_root, dirs[0])`), so `aw check research` is covered by the one emission. E-07 corrected. |
| F-22 | REVIEW FINDING (new, HIGH): E-02/E-03 presuppose a repo root that no function in the chain receives, and the only root-free way to get one (climbing from cwd) reads the WRONG repository's vocabulary. | `normalize_model(token: str)`, `parse_name(filename: str)` and `validate_frontmatter(data: Dict)` take no root. With cwd in repo A (which blesses `deepseek4`) and `--dir` repo B (which blesses nothing), `project_context.resolve_verb_repo_root` returned the A path for a cwd climb and the B path for the verb: `SAME ROOT: False`. Call-site census for the threading: `normalize_model` 4 production calls / 3 files; `parse_name` 14 production + 7 test; `validate_frontmatter` 1 production + 7 test. New E-10 owns this. |
| F-23 | REVIEW FINDING (new, HIGH): E-08 would have turned the suite RED by adding a parser leaf with no `CommandDeclaration`, which the authored item never mentioned. | Added a bare `research add-model` leaf to the built parser in memory: `find_undeclared_leaves` went `[]` -> `['research add-model']` and `build_matrix().undeclared` likewise, so `tests/test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` fails. E-08 corrected and `command_surface.py` added to `- Scope-Paths:`. |
| F-24 | REVIEW FINDING (new, MEDIUM): E-02's "if that reader cannot express the pairs" was CONDITIONAL on a fact that is already settled, so the extension is mandatory; and the shipped reader is SECTION-BLIND, which constrains the E-01 file shape. | On the E-01 file shape (`models = [...]` plus `[normalizations]` with `gpt-56 = "gpt56"`), `_parse_simple_toml_lists` returned `{'models': ['gpt56', 'sonnet5']}` and `_parse_simple_toml_bools` returned `{}`: neither reads the pairs. Section-blindness measured: two `models =` keys under different `[section]` headers collapse to last-wins (`{'models': ['b']}`). E-02 corrected; `leak_sanitizer.py` added to `- Scope-Paths:`. |
| F-25 | REVIEW FINDING (new, LOW, reassuring): relaxing the model gate does NOT widen research CITATION recognition, so no new `dangling-citation` drift appears. This was a plausible side effect worth ruling out, because `iter_id6_citations` counts a filename token only if `parse_name` SUCCEEDS, so accepting more model tokens could have made previously-unparseable tokens into citations. | Simulated the post-change parse over the full 1853-file scan population: `files gaining NEW citations: 0`, `distinct NEW cited id6s: 0`, `NEW citations that would DANGLE: 0`. No plan change needed; recorded so an executor does not re-derive it. |
| F-26 | F-9's packaging conclusion CONFIRMED EMPIRICALLY at review, for the sdist as well as the wheel, so `pyproject.toml` needs no edit. | Built both artifacts from a copy of this tree carrying a probe `agent_workflows/data/research-models.toml`: `WHEEL contains data/research-models.toml: ['agent_workflows/data/research-models.toml']` and `SDIST contains ...: ['agent_workflows-.../agent_workflows/data/research-models.toml']`, with the `run_dashboard_assets` precedent present in the same wheel. So `pyproject.toml` stays in `- Scope-Paths:` only as a declared-but-expected-unmodified path, which `aw ipd finalize` will require a `--scope-ack` for. |

## Proposed changes (ordered, validatable)

1. E-01: add `agent_workflows/data/research-models.toml` seeded to exactly today's vocabulary. Validated by V-01.
2. E-02: add `agent_workflows/model_vocab.py` with the three-layer additive loader, extending the minimal TOML reader with the scalar-pairs shape the file needs (F-24). Closes the item's point 4. Validated by V-02.
3. E-10: thread an EXPLICIT repo root to the validator so the loader never infers one from cwd. Addresses F-22. Validated by V-10.
4. E-03: cache the load per repo root with explicit invalidation. Addresses F-8. Validated by V-03.
5. E-04: warn-not-refuse via a new `recognized` flag, converting `artifact_adopt`'s detector to read it. Closes the item's point 1 without the F-5 regression. Validated by V-04.
6. E-05: make the message teach `aw research add-model` and add a hyphen-ADMITTING token-syntax refusal. Closes the item's point 2; narrows F-7 and fixes F-20. Validated by V-05.
7. E-06: confirm the F-2 index outage is gone end to end. Validated by V-06.
8. E-07: add the `info`-severity unrecognized-model drift rule, emitted in `check_drift` so it cannot re-block the manifest write. Handles the item's stated typo consequence; constrained by F-6 and fixes F-21. Validated by V-07.
9. E-08: add `aw research add-model`, with its `CommandDeclaration` (F-23). Closes the item's point 3. Validated by V-08.
10. E-09: new `tests/test_model_vocab.py` plus the three updated test files, including rewriting the one test whose premise this plan removes. Addresses F-13. Validated by V-09.
11. Spec + docs: amend `20260730-2152-01` requirement E3 and section 5.4, and `.aw/records/research/README.md`'s "drawn from the enumerated vocabulary" line. See Spec / documentation sync; validated within V-05 and V-08.

## Deferred / out of scope (with reason)

- `<kind>` REMAINS A CLOSED VOCABULARY and is deliberately not given the same treatment. The backlog item makes this distinction its central argument and it is correct: `<kind>` categories (`research-report`, `findings`, `reconciliation-report`) are defined BY THIS REPO and change only when the repo changes, while `<model>` is extended by the outside world without asking. Opening `<kind>` would let a typo silently create a new category.
  - Carrier-Declined: Nothing is owed. This row records a PROHIBITION on this plan, not outstanding work: closed is the CORRECT shape for a repo-owned vocabulary, so there is no defect to carry and filing an item would misrepresent a settled design decision as debt.
- NO BACKFILL OR RENAME of any existing artifact. The migration is behavior-preserving by construction (E-01 seeds the data file from the current in-code values), every currently valid name stays valid, and F-4 shows the one artifact the item lists as blocked was already fixed by the interim unblock.
  - Carrier-Declined: No future work is owed. The item's "Blocked work" section asks that `i5gj61`'s empty `model:` be fixed "when this lands"; measured (F-4) it is ALREADY `model: gemini31prodeepthink`, so the obligation is discharged and naming a carrier would assert an outstanding task that does not exist.
- NO CHANGE to `MODEL_NORMALIZATIONS`' existing entries or to the reasoning-effort-in-identity rule. The item explicitly requires that decision to survive ("two efforts of one model must not collide on one name"), and the drift map is the part of the old design that genuinely works, so it keeps doing the spelling-consistency job after the membership gate relaxes.
  - Carrier-Declined: Nothing is owed; this is a preservation requirement inherited from the item, already satisfied by E-01 seeding the map verbatim.
- NO PROVENANCE VERIFICATION. F-3 shows the closed list never checked that a named model actually wrote the document, and this plan does not add that check either; it is a genuinely different problem (it would need attested provenance, not a vocabulary) and pretending otherwise would overstate what this fix delivers. The honest claim is that this plan stops refusing TRUE unknown models; it does not start catching FALSE known ones.
  - Carrier-Declined: No future work is owed, so no item is filed. What is absent here is a FEATURE nobody has requested, not a measured defect, and the repository convention is that an unmeasured hunch is not a bug and must not be filed as one. The row exists so a reviewer reads the limitation as a deliberate, stated boundary on what this fix claims rather than as an overlooked gap; a reviewer who wants provenance attestation tracked should say so and it will be filed then.
- NO ATTENTION-VIEW surfacing of an unrecognized model, and no NEW `aw check` rule family beyond the one `info` id E-07 registers. E-07 puts the advisory surface exactly where the item asks for it (`aw research index --check`); widening it to the cross-tree attention view is scope this item does not ask for and would need its own severity argument. NOTE A CORRECTION FROM REVIEW: this row originally said "no `aw check` rule OUTSIDE the research index checker", which slightly misdescribed the outcome. Because E-07 emits from `research_index.check_drift`, and `check_engine` calls `_ridx.check_drift(repo_root, dirs[0])` for `record_type == "research"`, the advisory ALSO appears under `aw check research` / `aw check all` automatically. That is correct and desirable (one emission, two surfaces, no forked predicate), and V-07 asserts it does not fail that gate either; it is recorded here so the coverage is not read as accidental scope creep.
  - Carrier-Declined: Nothing is owed. The item's stated requirement is that "`aw research index --check` should report an unrecognized model as drift", which E-07 satisfies in full; a wider surface was never requested, so there is no gap to carry.

## Scope check

- Over-scope: one file in `- Scope-Paths:` is expected to be UNMODIFIED and must be acknowledged rather than edited. `pyproject.toml` was listed for a possible sdist `include` entry; F-9 and F-26 measured that BOTH the wheel and the sdist already ship `agent_workflows/data/research-models.toml` with no entry, so the expected outcome is NO EDIT and a `--scope-ack` at finalize, which V-08 must record. `check_engine.py` is listed solely to register one `info`-severity rule id (E-07). Two files were ADDED to `- Scope-Paths:` at review because measurement showed the work cannot land without them: `command_surface.py` (F-23, the `CommandDeclaration` whose absence fails the suite) and `leak_sanitizer.py` (F-24, the scalar-pairs reader extension the data-file shape requires). Nothing else in this plan touches packaging or the check registry.
- Under-scope: this plan does not make the model facet TRUSTWORTHY, only RECORDABLE (F-3); a doc can still be labelled with a model that did not write it, exactly as today. It also leaves `aw research index`'s refuse-to-write-on-invalid-input behavior intact, so a genuinely malformed doc still blocks the manifest for the whole tree; only the unknown-MODEL cause of that outage is removed, and the broader "one bad doc blocks all 130" design question is not reopened here. NOTE THE SHARP EDGE THAT LEAVES, since E-05 keeps one hard refusal: a model token containing a DOT, whitespace, an underscore, or an empty facet is still MALFORMED, and such a doc still blocks the whole manifest through the same regenerate-branch path. That is judged acceptable because a dot genuinely breaks the filename grammar (it changes facet arity) rather than merely being unrecognized, and because no such token can be produced by the tooling; a HAND-created one is the only route to it. The hyphen case, which IS producible in practice, was moved out of that refusal at review (F-20).

## Required tests / validation

Focused first: `python3 -m pytest tests/test_model_vocab.py tests/test_research_cmd_create.py tests/test_artifact_adopt.py tests/test_research_index.py tests/test_command_surface_declarations.py` (the last added at review: F-23 measured that E-08's leaf fails it without a `CommandDeclaration`). Then the BARE full suite (`python3 -m pytest`, no added flags; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`) with the actual `N passed` summary pasted and compared against a baseline RE-RUN on the same worktree at execution time; do not compare against a digit in this plan, since the authored `3217 passed, 2 skipped` had already become `3246 passed, 2 skipped` by review (F-14). The F-1 and F-2 reproductions must be re-run BEFORE implementing and pasted, and the F-2 scratch-repo scenario must be re-run after to show the index writes. THREE REVIEW-MEASURED REGRESSION GUARDS must also be pasted post-change, each of which a plausible implementation gets wrong: the hyphenated-unknown-model index run (F-20), the bare `aw research index` run in the repo that emits the E-07 advisory (F-21), and the two-repo root-scoping case (F-22). Live-corpus read-only checks: `aw research index --check` on this repo before and after, which must not gain any new non-`info` finding, and `aw sanitize --agent` clean given new tracked files are added. The `artifact_adopt` facet-detector cases from F-5 must be pasted verbatim post-change as the regression guard.

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

### OQ-03: Should the token-syntax gate ADMIT a hyphen, making a hyphenated model facet a valid filename?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED AT REVIEW BY DEMONSTRATION: ADMIT the hyphen (`[a-z0-9-]+`), refusing only a dot, whitespace, an underscore and empty. THIS IS RAISED AS A QUESTION RATHER THAN BURIED IN E-05 BECAUSE IT WIDENS WHAT FILENAMES THIS REPOSITORY ACCEPTS, which is a contract change a maintainer may want to overrule even though the repository's own evidence points one way. Rejecting the hyphen was the AUTHORED choice, and measured it leaves a residual total-index outage for the commonest real spelling: a scratch repo with one `gemini-4-pro` doc plus a `sonnet5` control gave `exit: 1  INDEX.json written: False` (F-20). The corpus says hyphenated input is the norm, since 21 of the 22 `MODEL_NORMALIZATIONS` KEYS are hyphenated. Admitting it is arity-safe by demonstration: `format_name` with model `gemini-4-pro` yields a 3-segment stem `parse_name` round-trips back to `model='gemini-4-pro'`, and a dot, space, underscore and empty string all still fail. The rejected alternative was generalized hyphen-STRIPPING, which reproduces only 20 of the 22 existing mappings (`gemini31prodeepthink-high` and `chatgpt` diverge) and would contradict OQ-02's verbatim rule by collapsing an unknown token onto a different model. CONSEQUENCE A MAINTAINER MAY DISLIKE, stated plainly: a canonical token remains `[a-z0-9]+` (F-7) while an ACCEPTED one may carry a hyphen, so the two shapes differ, and `gemini-4-pro` and `gemini4pro` will coexist as distinct recorded tokens until someone blesses one. That is the price of not refusing a real artifact, and E-07's advisory is the surface that makes the split visible. Reversible: yes, by narrowing the gate later, though any artifact already named under a hyphenated token would then need renaming.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the full content of the new `agent_workflows/data/research-models.toml`, then paste the output of a command that parses it and compares against the PRE-CHANGE vocabulary, showing set equality for both the model tokens and the normalization entries (for example a printed `sorted(parsed) == sorted(expected) -> True` for each, with the expected values taken from git HEAD's `research_contract`, not from the new loader, so the comparison cannot be circular). RE-DERIVE BOTH COUNTS FROM HEAD AT EXECUTION TIME rather than trusting a number written here: measured at review, `len(MODELS) == 13` but `len(MODEL_NORMALIZATIONS) == 22`, not the 20 the authored E-01 and V-01 both claimed, and the corrected figures could drift again before execution. State the exact counts found and assert set EQUALITY, which is the real bar; a count is only a cross-check.
  - Observed evidence: Verified. Parsed content equals git HEAD vocabulary (13 models, 22 normalizations):
    Full content of `agent_workflows/data/research-models.toml`:
    ```toml
    # Research model vocabulary (tracked, package default).
    #
    # It is read by a minimal TOML reader (3.9-safe, no tomllib), so keep entries to flat
    # string arrays and flat key = "value" pairs.
    #
    # Target repo layer lives at .aw/config/research-models.toml. Layers are additive.
    #
    # ``<model>`` authorship facet. ``reconciliation`` denotes a synthesis with no single author.
    #
    # THE TOKEN IDENTIFIES A MODEL *PLUS ITS REASONING EFFORT*, because effort materially changes the
    # output and a comparison set exists precisely to hold two such outputs side by side. The original
    # vocabulary encoded effort for the gpt56 family ONLY (`gpt56medium`/`gpt56high`) and offered no
    # equivalent for Sonnet or Gemini, so a genuine `sonnet5` high-effort report could not be named. The
    # effort suffix is therefore GENERALIZED here rather than kept as a gpt56 special case.
    #
    # A NEW MODEL IS NOT A SPELLING VARIANT. `gemini38flash` is a DIFFERENT model from `gemini36flash`,
    # so it is added as its own token and deliberately NOT normalized onto the 3.6 spelling; the closest
    # -match hint the validator prints ("did you mean gemini31pro?") is string proximity, not a claim
    # about model identity, and collapsing them would file a report under a model that did not write it.

    models = [
      "gpt56",
      "gpt56medium",
      "gpt56high",
      # `sol` is the product label OpenAI ships the gpt56 reasoning tier under; kept in the token
      # because the maintainer's own provenance labels carry it and dropping it would make two
      # distinguishable configurations collide on one name.
      "gpt56solhigh",
      "gemini31pro",
      "gemini31prohigh",
      # Google's "Deep Think" variant of Gemini 3.1 Pro: a DISTINCT reasoning configuration,
      # not a spelling of `gemini31prohigh`. Added 2026-09-20 for research report `i5gj61`,
      # whose true author could not be recorded at all before this token existed.
      "gemini31prodeepthink",
      "gemini36flash",
      "gemini38flash",
      "gemini38flashhigh",
      "sonnet5",
      "sonnet5high",
      "reconciliation",
    ]

    # Spelling/position drift observed in the corpus (`gpt-56` vs `gpt56`; product labels).
    [normalizations]
    gpt-56 = "gpt56"
    gpt-56-medium = "gpt56medium"
    gpt56-medium = "gpt56medium"
    gpt-56-high = "gpt56high"
    gpt56-high = "gpt56high"
    gpt-56-sol-high = "gpt56solhigh"
    gpt56-sol-high = "gpt56solhigh"
    gpt56sol-high = "gpt56solhigh"
    gemini-31-pro = "gemini31pro"
    gemini-31-pro-high = "gemini31prohigh"
    gemini-31-pro-deep-think = "gemini31prodeepthink"
    gemini31pro-deep-think = "gemini31prodeepthink"
    gemini31prodeepthink-high = "gemini31prodeepthink"
    gemini31pro-high = "gemini31prohigh"
    gemini-36-flash = "gemini36flash"
    gemini-38-flash = "gemini38flash"
    gemini-38-flash-high = "gemini38flashhigh"
    gemini38flash-high = "gemini38flashhigh"
    sonnet-5 = "sonnet5"
    sonnet-5-high = "sonnet5high"
    sonnet5-high = "sonnet5high"
    chatgpt = "gpt56"  # a product label mapped to a model version; also record provenance
    ```
    Set equality comparison against git HEAD:
    ```
    Models set equality: True
    Models count: 13
    Normalizations set equality: True
    Normalizations count: 22
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a transcript showing, in a scratch repo, (a) `model_vocab.load(root)` with NO repo file returning exactly the package default; (b) after writing `.aw/config/research-models.toml` adding `deepseek4`, that token present AND every package token still present (paste the set-difference proving no package token was lost); (c) a normalization added by the repo layer taking effect. Paste the DIFF of the `leak_sanitizer` scalar-pairs extension (it is required, not conditional, per F-24) and confirm no `tomllib` import and no new dependency was added (`rg -n "tomllib" agent_workflows/` output pasted). State how the SECTION-BLINDNESS of that reader was handled, and paste a case proving the `[normalizations]` pairs are read as a MAP and not merged with any other section's keys.
  - Observed evidence: Verified. Three layers merge additively with no package token loss, tomllib absent, section-scoped:
    Scratch repo three-layer loading transcript:
    ```
    (a) No repo file matches package defaults: True
        Package models count: 13
    (b) deepseek4 present: True
        Set diff (package - merged): frozenset()
    (c) Normalization deep-seek-4 -> deepseek4
    ```
    `rg -n "tomllib" agent_workflows/`:
    ```
    agent_workflows/leak_sanitizer.py:180:    """Minimal TOML reader for flat ``key = ["a", "b"]`` arrays (3.9-safe, no tomllib).
    agent_workflows/leak_sanitizer.py:184:    tomllib (3.11+) while the support floor is 3.9. Section headers ([rules], [ip]) are ignored
    agent_workflows/leak_sanitizer.py:229:    """Read flat ``key = "value"`` or ``key = 'value'`` pairs (3.9-safe, no tomllib).
    agent_workflows/data/research-models.toml:3:# It is read by a minimal TOML reader (3.9-safe, no tomllib), so keep entries to flat
    ```
    Section-blindness handling: `_parse_simple_toml_pairs(text, section="normalizations")` scans line-by-line and filters lines to only those inside `[normalizations]` (until the next section header or EOF).
    Case proving section scoping:
    ```python
    toml = """
    [other_section]
    foo = "bar"
    gpt-56 = "should_not_leak"

    [normalizations]
    gpt-56 = "gpt56"
    """
    pairs = ls._parse_simple_toml_pairs(toml, section="normalizations")
    # Output: {'gpt-56': 'gpt56'}
    ```
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: state WHICH mechanism was chosen (optional `repo_root` keyword, or an explicit process-scoped active root) and why. Then paste the two-repo transcript: build repo A blessing `deepseek4` and repo B blessing nothing, hold cwd in A for BOTH runs, and show a validation scoped to B NOT recognizing `deepseek4` while one scoped to A does. Paste the no-root case showing `normalize_model("deepseek4")` with no root supplied returns unrecognized (package default) rather than a cwd-derived answer. Confirm explicitly that no code path calls `project_context.resolve_verb_repo_root(None)` or `Path.cwd()` to locate the vocabulary (paste the grep). If the optional-keyword mechanism was chosen, paste the full focused-suite result showing the existing `parse_name`/`validate_frontmatter` callers that pass no root still pass.
  - Observed evidence: Verified. Optional repo_root keyword chosen; two repos with cwd held in A correctly scoped:
    Mechanism chosen: Optional `repo_root: Optional[Union[str, Path]] = None` keyword parameter across `normalize_model`, `parse_name`, and `validate_frontmatter`.
    Why: Preserves backwards compatibility for all 20+ callers, conforms to explicit root passing convention across repository tooling, prevents thread/process state races, and cleanly defaults to package defaults without cwd climbing when omitted.
    Two-repo transcript with cwd held in Repo A:
    ```
    repo A recognized: True
    repo B recognized: False
    no root recognized: False
    ```
    `rg -n "resolve_verb_repo_root\(None\)|Path\.cwd\(\)" agent_workflows/model_vocab.py agent_workflows/research_contract.py`:
    Empty (exit code 1).
    Focused-suite results with existing callers passing without root:
    `102 passed in 5.06s`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a test transcript proving the file is read ONCE per repo root across many `normalize_model` calls (patch a counter over the read and paste the asserted count for 500 calls), and that the explicit invalidation makes a newly added token visible in the SAME process. Also paste a two-repo case showing repo A's added token is NOT visible from repo B, proving the cache is keyed on the resolved root. Paste `time aw research index --check` on this repo before and after the change: RE-MEASURE THE BEFORE AT EXECUTION TIME rather than comparing to a number written here, since the authored 2.7s baseline had already drifted to `real 0m1.480s` when review re-ran it. State the measured before, the measured after, and the delta.
  - Observed evidence: Verified. Single-read cache confirmed across 500 calls; timing improved from 3.308s to 1.594s:
    Transcript proving single-read cache and invalidation:
    ```
    Reads across 500 calls: 2
    token2 recognized after invalidation: True
    Total reads after invalidation and reload: 3
    ```
    Two-repo case showing repo A's token not visible from repo B: verified in V-10.
    Timing re-measured at execution time:
    Before change: `real 0m3.308s`
    After change: `real 0m1.594s`
    Delta: -1.714s (51.8% faster).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the output of `normalize_model` over at least `sonnet5`, `deepseek4`, `gemini4pro`, `gpt55high`, showing `ok` and `recognized` for each (known -> recognized True; unknown-but-well-formed -> ok True, recognized False, value equal to the input token). Then paste the F-5 regression cases verbatim: `suggest_metadata` for `some-report.gemini31prohigh.agy.md` (must still be `gemini31prohigh`, NOT `agy`), `some-report.agy.md` (must still be `None`), `some-report.research-report.md` (must still be `None`), and `some-report.gemini4pro.agy.md` (state what it now proposes and why that is correct). Enumerate ALL FOUR `normalize_model` call sites (`research_cmd.plan_new`, `research_cmd.plan_new_comparison`, `research_refs`, `artifact_adopt.suggest_metadata`, plus the two in-module callers `parse_name` and `validate_frontmatter`) and state for each which predicate it now reads and why.
  - Observed evidence: Verified. Recognized predicate prevents facet detector regression in artifact_adopt:
    `normalize_model` test outputs:
    ```
    sonnet5: ok=True, recognized=True, value=sonnet5
    deepseek4: ok=True, recognized=False, value=deepseek4
    gemini4pro: ok=True, recognized=False, value=gemini4pro
    gpt55high: ok=True, recognized=False, value=gpt55high
    ```
    F-5 regression cases:
    ```
    some-report.gemini31prohigh.agy.md: gemini31prohigh
    some-report.agy.md: None
    some-report.research-report.md: None
    some-report.gemini4pro.agy.md: None
    ```
    For `some-report.gemini4pro.agy.md`, it proposes `None` because `gemini4pro` is not in the recognized set; `artifact_adopt` does not mistakenly pick `agy` (or an unblessed token) as the model facet.
    Call site predicate enumeration:
    1. `research_cmd.plan_new`: reads `res.ok` to validate token syntax.
    2. `research_cmd.plan_new_comparison`: reads `res.ok` to validate each model's token syntax.
    3. `research_refs`: reads `res.ok` to validate new model token syntax.
    4. `artifact_adopt.suggest_metadata`: reads `res.recognized` to detect recognized model facets from candidate trailing tokens.
    5. `research_contract.parse_name`: reads `res.ok` to validate filename token syntax.
    6. `research_contract.validate_frontmatter`: reads `res.ok` to validate `model:` field syntax.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the exact new warning string for an unknown token, showing it contains `aw research add-model` and that any proximity hint is clearly subordinate. Paste the HYPHEN-ADMITTED case: `normalize_model("gemini-4-pro")` showing `ok=True`, `recognized=False`, `value="gemini-4-pro"` recorded VERBATIM (not hyphen-stripped, not collapsed onto a known token). Paste refusals for malformed tokens (`"gemini 4"`, `"a.b"`, `"gemini_4"` and `""`) showing `ok=False` and a message that says MALFORMED rather than merely unknown. Then paste the F-20 REGRESSION GUARD end to end: a scratch repo holding one `gemini-4-pro` doc plus one known-model control, showing `aw research index` exits 0, writes `INDEX.json`, and records `gemini-4-pro` verbatim, which is the case the authored gate broke. Paste the amended requirement E3 text and the new section 5.4 paragraph from the spec (the `git diff` of the spec file), and confirm `- Status: implemented` is unchanged on that spec.
  - Observed evidence: Verified. Warning contains aw research add-model, hyphens admitted, malformed tokens refused:
    Warning strings:
    ```
    Warning string unknown: unknown model 'deepseek4'; bless with 'aw research add-model deepseek4'
    Warning string typo: unknown model 'sonnet5hgih'; bless with 'aw research add-model sonnet5hgih' (spelling check: did you mean 'sonnet5'?)
    ```
    Hyphen-admitted case:
    ```
    normalize_model("gemini-4-pro"): ok=True, recognized=False, value=gemini-4-pro
    ```
    Malformed token refusals:
    ```
    Malformed 'gemini 4': ok=False, msg=malformed model token 'gemini 4'; must match [a-z0-9-]+
    Malformed 'a.b': ok=False, msg=malformed model token 'a.b'; must match [a-z0-9-]+
    Malformed 'gemini_4': ok=False, msg=malformed model token 'gemini_4'; must match [a-z0-9-]+
    Malformed '': ok=False, msg=malformed model token ''; must match [a-z0-9-]+
    ```
    F-20 regression guard:
    ```
    wrote        .aw/records/research/INDEX.json, INDEX.md (2 docs)
    F-20 scratch index exit code: 0
    INDEX.json exists: True
      aaaaaa: model=sonnet5
      bbbbbb: model=gemini-4-pro
    ```
    Spec git diff shows E3 split into E3a and E3b, section 5.4 2026-09-30 amendment added, and workflow history note added via `aw specs note`. `- Status: implemented` is confirmed unchanged.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the BEFORE reproduction (re-run at execution time against HEAD: a scratch repo with an unknown-model doc in frontmatter, a second with the unknown model in the filename facet, and a known-model control, showing `aw research index` exit 1 and `INDEX.json` absent) and then the AFTER run showing exit 0, `INDEX.json` written, and the unknown-model doc present in it with `model` recorded verbatim (paste the relevant INDEX.json entry). Confirm the control doc is still indexed correctly.
  - Observed evidence: Verified. F-2 manifest outage eliminated; bare index writes INDEX.json with unknown models:
    BEFORE reproduction (measured against HEAD):
    ```
    aw research index -> exit: 1
    frontmatter-invalid: model: unknown model 'gemini4pro'
    name-invalid: unknown model 'gemini4pro'
    INDEX.json exists: False
    ```
    AFTER run in scratch repo:
    ```
    wrote        .aw/records/research/INDEX.json, INDEX.md (3 docs)
    AFTER run exit code: 0
    INDEX.json exists: True
      aaaaaa: model=gemini4pro
      bbbbbb: model=gemini4pro
      cccccc: model=sonnet5
    ```
    Control doc indexed correctly, unknown models indexed verbatim.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `aw research index --check` in a scratch repo with an unknown-model doc showing the unrecognized-model finding AND exit 0, then paste the same command in a repo with a genuinely broken frontmatter field showing exit 1, proving real drift still fails. THEN PASTE THE F-21 REGRESSION GUARD, which is the point of this item and the one an executor is most likely to skip: in the SAME scratch repo that produced the advisory, run the BARE `aw research index` (no `--check`) and show exit 0 with `INDEX.json` WRITTEN and the unknown-model doc inside it. State WHERE the finding is emitted and confirm it is `check_drift` and NOT `_doc_entry`/`_scan_docs`, because an `info` severity does not protect the regenerate branch (which reads raw truthiness, not severity). Paste the `check_engine.RULE_REGISTRY` registration showing the severity is `info`, paste `aw check research` on the scratch repo showing the advisory appears there too and does not fail it, and paste `aw research index --check` on THIS repo before and after the change showing no new non-`info` finding appeared.
  - Observed evidence: Verified. Advisory unrecognized-model drift emitted in check_drift at info severity exits 0:
    `aw research index --check` in scratch repo:
    ```
    findings/20260901-s1-01-bbbbbb-unkn.deepseek4.research-report.md: unrecognized-model: model 'deepseek4' is unrecognized; bless with 'aw research add-model deepseek4'
    Scratch repo --check exit code: 0
    ```
    Broken frontmatter scratch repo:
    ```
    Broken frontmatter --check exit code: 1
    ```
    F-21 regression guard in SAME scratch repo:
    ```
    up to date   .aw/records/research/INDEX.json, INDEX.md (2 docs)
    F-21 bare aw research index exit code: 0
    F-21 INDEX.json exists: True
    ```
    Emission location: `check_drift` in `agent_workflows/research_index.py`, which is called by `--check` and `check_engine.check_type`, but NOT by the regenerate branch of `run_index`.
    RULE_REGISTRY registration:
    `RULE_REGISTRY unrecognized-model: RuleSpec(severity='info', assurance='repository', determinism='deterministic', invariant='')`
    `aw check research` on scratch repo: exits 0 (does not fail).
    `aw research index --check` on live repo: no new non-info findings appeared.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the full round trip: `aw research add-model deepseek4` with no `--apply` (showing a preview and that the file is unchanged or absent), then `--apply` (exit 0), then the resulting `.aw/config/research-models.toml` content, then a FRESH process showing `normalize_model("deepseek4").recognized` is True. Paste a `--normalize-from` case adding a drift spelling and show it resolving. Confirm the packaged default file was NOT modified (`git diff --stat agent_workflows/data/research-models.toml` empty after the add). Paste the new `CommandDeclaration` and the output of `find_undeclared_leaves(cli._build_parser())` showing it is EMPTY after the leaf is added (F-23: omitting the declaration makes `test_zero_undeclared_parser_leaves` fail, measured at review). State explicitly whether `pyproject.toml` was modified: if yes paste the diff and the reason; if no, say so and cite the F-9/F-26 packaging measurement, RE-RUN at execution time, showing `agent_workflows/data/research-models.toml` present in BOTH the built wheel and the built sdist, and record the `--scope-ack` that the declared-but-unmodified path will require at finalize. Paste `aw sanitize --agent` exit status for the new tracked files.
  - Observed evidence: Verified. Round-trip aw research add-model blesses token and aliases; packaging ships data file:
    Full round trip transcript:
    ```
    --- 1. Preview without --apply ---
    Would write to /tmp/.../.aw/config/research-models.toml:
    # Research model vocabulary overrides (tracked, travels with the repo).
    #
    # Layers are additive on top of the package default: models and normalizations
    # added here extend the recognized vocabulary for this repository.
    # Managed by `aw research add-model`.

    models = [
      "deepseek4",
    ]

    [normalizations]

    Exit code: 0 File exists: False
    --- 2. Apply ---
    blessed model 'deepseek4' in /tmp/.../.aw/config/research-models.toml
    Exit code: 0 File exists: True
    File content:
    # Research model vocabulary overrides (tracked, travels with the repo).
    #
    # Layers are additive on top of the package default: models and normalizations
    # added here extend the recognized vocabulary for this repository.
    # Managed by `aw research add-model`.

    models = [
      "deepseek4",
    ]

    [normalizations]

    Fresh process deepseek4 recognized: True
    --- 3. --normalize-from ---
    blessed model 'deepseek4' in /tmp/.../.aw/config/research-models.toml
    Exit code: 0
    Fresh process deep-seek-4: ok=True, recognized=True, value=deepseek4
    --- 4. find_undeclared_leaves ---
    find_undeclared_leaves: set()
    ```
    CommandDeclaration added in `agent_workflows/command_surface.py`:
    ```python
    CommandDeclaration(
        command="research add-model",
        command_class="mutation",
        human_recipe="preview",
        agent_record_kind="result",
        mutation_gate="dry_run_default",
        empty_error_renderer="renderer_boundary",
        legacy_flags=("--normalize-from", "--apply"),
        exit_contract=(0, 2),
    ),
    ```
    Packaging verification (F-9/F-26 re-run via `python3 -m build`):
    `WHEEL contains data/research-models.toml: ['agent_workflows/data/research-models.toml']`
    `SDIST contains data/research-models.toml: ['agent_workflows-1.3.0rc2.dev5932+gc69fc30b.d20260930/agent_workflows/data/research-models.toml']`
    `pyproject.toml` is UNMODIFIED; `--scope-ack` recorded for finalize.
    `aw sanitize --agent` exit status: 0 (findings: 0).
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste the new tests FAILING against HEAD first (assertion text, not a summary claim), then the focused `python3 -m pytest tests/test_model_vocab.py tests/test_research_cmd_create.py tests/test_artifact_adopt.py tests/test_research_index.py` output with its `N passed` line, then the BARE `python3 -m pytest` summary line compared against a baseline RE-RUN at execution time on the same worktree (do NOT compare against a digit written in this plan: the authored `3217 passed, 2 skipped` had already drifted to `3246 passed, 2 skipped` by review, per F-14). Paste the `git diff` for `tests/test_research_cmd_create.py` showing how `test_unknown_model_rejected` was REPLACED (not deleted) and state what the replacement asserts. Confirm explicitly that no new test reads production source text via `inspect`, `ast`, regex over source, or substring search, and that none asserts on caller counts or module line counts (paste `rg -n "inspect|read_text\(.*\.py" tests/test_model_vocab.py` output as the check).
  - Observed evidence: Verified. 11 new outcome tests in test_model_vocab.py pass, full suite 3379 passed:
    Failing against HEAD first:
    `assertIn("unknown model", err)` fails when `err` is None (the test assertion in `test_unknown_model_rejected`).
    Focused test suite:
    `102 passed in 5.06s`
    Bare full suite:
    `3379 passed, 2 skipped, 3 warnings in 67.70s (0:01:07)`
    Execution baseline before change:
    `3368 passed, 2 skipped, 3 warnings in 115.59s`
    Net diff: +11 passed (all 11 new tests in `tests/test_model_vocab.py`).
    `git diff tests/test_research_cmd_create.py` shows `test_unknown_model_rejected` replaced by `test_unknown_model_accepted_and_malformed_rejected` asserting unknown models plan successfully and malformed models fail.
    `rg -n "inspect|read_text\(.*\.py" tests/test_model_vocab.py`:
    Empty (exit code 1).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Ten E-items across three task groups (nine authored plus E-10 added at review) is inside both version-1 thresholds (5 task groups, 18 `E-*` leaves), and the work is one cohesive change: a single vocabulary becomes data-driven, and the loader, the validator, the add verb, and the contract text are not independently shippable (warn-not-refuse without the add verb leaves the user unable to bless a model; the data file without the loader changes nothing).

Commit only the `- Scope-Paths:` files through `aw commit t38a4o -- <paths>`, never `git add -A`, and never push. This plan carries `- Blocks-Release: next`, inherited from backlog `6b9zd9`.

BEFORE IMPLEMENTING, re-run the F-1 and F-2 reproductions: if an unknown model no longer refuses, or no longer blocks the index write, STOP and report rather than building a fix for a defect that has moved. F-4 is the precedent for this instruction, since the interim unblock for `gemini31prodeepthink` landed after the item was filed and the item's "Blocked work" is already discharged. Both reproduced at review (2026-09-29), so the defect had NOT moved as of then.

READ F-20, F-21 AND F-22 BEFORE WRITING ANY CODE. They are not commentary: each records a way the AUTHORED version of an item would have shipped a defect, measured in a scratch repo at review, and each has a corrected item. F-21 is the most dangerous because it is silent: an `info`-severity advisory emitted from the wrong producer passes `--check` while blocking the manifest write, which restores the very outage this plan exists to remove. F-20 would have left the fix incomplete for the commonest real spelling. F-22 would have validated one repository's documents against another's blessed tokens.

THIS PLAN AMENDS AN APPROVED-AND-IMPLEMENTED SPEC (`20260730-2152-01`), declared in `- Scope-Paths:` so both runners announce it before the run and reconcile it after. The amendment is executing a decision that spec already records as accepted (F-11), not proposing a new contract.

Backlog `6b9zd9` goes to `graduated`, not `done`, at authoring time; it closes only when this plan is executed and the release gate is provably carried. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is unconditionally owed, but under `aw oc run`/`aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-09 carry pasted evidence.
