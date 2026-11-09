# IPD: Move the attention and ipd_lint reads onto artifact_meta

- Date: 2026-11-07
- Kind: child
- Concern: Split from `ffceq0` (Task groups 2 and 4) under the maintainer's step-complexity rule. `attention` holds 10 `^-` metadata regular expressions and 6 history-block reads across its six per-tree record builders, and `ipd_lint` parses plan metadata and history itself (5 `^-` literals and `ipd_schema.parse_metadata_block`); spec `4sd62s` C5 requires both to answer from `artifact_meta`. Both are status-and-history consumers of the same cached fields, which is why they share a part.
- Scope: FINISHING PART after the round-3 split (2026-11-09, research `nj8zdp` guidance): the `ipd_lint` item E-03 moved to `1suzlp` (Order 151). Pin then move the `attention` reads (`scan`, every per-tree `_*_record`, `_plans_id`, `_frontmatter_block`, `_ITEM_DEPS_RE`, `read_readiness` callers and the `attention_contract.history_block`/`last_history_at` calls) onto `artifact_meta.query` and `artifact_meta.history`, applying D-3 (`ffceq0` E-04, E-05 carried unchanged). EXCLUDES: `ipd_lint` (`1suzlp`), `selectors` and `aw find` (Order 27 `r81uvz`), `check_engine` (Orders 29 to 32), and everything `ffceq0` keeps.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/attention_contract.py, tests/test_readers_attention.py, .aw/records/plans/pending/20261107-metastore-28-dqutt8-move-the-attention-and-ipd-lint-reads-onto-artifact-meta.ipd.md
- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45, executed:r81uvz, executed:w1cs3p, executed:na188y, executed:i3b5zu, executed:ebrc4t, executed:1suzlp
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 28
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: dqutt8

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-03 moved to 1suzlp.
- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from ffceq0 per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every `aw attention` item is built from one `artifact_meta.query` over the in-scope types, with the same items, drift and history dates as before the move, and an `incomplete` record is reported as a violation rather than dropped. (`ipd_lint` is moved by `1suzlp`.)

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Every E-item that moves a reader follows one rule, so a reviewer can check each the same way: (1) BEFORE the edit, add or extend a behavioral test in the named module that pins the reader's CURRENT observable behavior on a `tmp_path` fixture repository (the "prior behavior" column of the reader ledger in `## Findings`), and run it green against the unmodified code; (2) change the reader to call `artifact_meta`; (3) run the same test unchanged. A test that has to change in step 3 is a behavior change and must be one of the decisions listed in the ledger (D-1 to D-5), never a silent one. For every existing module named as a baseline, save the per-test outcome list under the gitignored `.aw/state/ffceq0/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/ffceq0/<E>-before.txt`) before the move and the same command into `<E>-after.txt` after it; `diff` of the two prints nothing except lines a named decision explains. Every saved baseline (command output, JSON, rule counts) also goes under `.aw/state/ffceq0/`, never `/tmp`, so it survives a lane integration. A count measured at authoring (for example the 1,635 executed plans of F-03) is context, never the bar: each expected outcome compares a before and after value re-derived on the same tree. New test modules set `pytestmark = pytest.mark.core`, call real functions or the real `aw` CLI, and never read production source.

The baseline directory stays `.aw/state/ffceq0/`, not this plan's own id6, because the split parent `ffceq0` keeps the final cache-parity, residual-audit and finishing items that compare against these saved files. Commit through `aw commit dqutt8 -- <each changed path>`, one commit per task group allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push.

### Task group 1: attention

- [ ] E-01 Pin the current `aw attention` behavior in `tests/test_readers_attention.py`: per-tree status mapping (`attention.missing-status`, `attention.unknown-status`, disposition mismatch), `id`, `priority`, `blocks_release`, `readiness`, `last_history_at` (newest record by `attention_contract.newest_history_record`), gate fields, open-question counts and `detail_kind`/`detail_text` for one fixture of each tree (plans, specs, backlog, research, releases, prompts), and the `aw attention --check --agent` exit code with one violation. If `.aw/state/ffceq0/att-before.json` (saved by Order 142 `cdglt1` E-02, which `r81uvz` depends on) is absent from this checkout, save `aw attention --all --format json` to it now, before any attention edit. Run `tests/test_attention.py`, `tests/test_attention_contract.py`, `tests/test_history_consumers_shared_reader.py`, `tests/test_history_date_clock_readers.py` and `tests/test_prompts_attention.py` green as the baseline.
  - Depends on: none
  - Expected outcome: the new module passes on the unmodified code; the five existing modules' summary lines are recorded.
  - Execution state: pending

- [ ] E-02 Move `attention` reads onto `artifact_meta.query`: `scan` builds `Item`s from one `query()` over the in-scope types instead of reading each file; `_plans_record`, `_spec_record`, `_backlog_record`, `_research_record`, `_release_record`, `_prompts_record`, `_plans_id`, `_frontmatter_block`, `_ITEM_DEPS_RE` and `read_readiness` callers read cached fields; `last_history_at` comes from `artifact_meta.history` through the unchanged `attention_contract.last_history_at` rule (phase B: same lines, same answer; the post-cutover `last_history_precision` key is Order 13's, see Deferred). Body-derived columns (open-question counts, E/V counts) still read the body (N3). `_extract_detail` stays as the fallback when `short_description` is absent (D-3). A cross-artifact `query()` `incomplete` list becomes an `attention.missing-status` violation for each named record, so an invalid record is reported, never silently dropped.
  - Depends on: E-01
  - Expected outcome: E-04 and its five baseline modules pass unchanged; `aw attention --all --format json` on this checkout yields the same item count and violation count as `.aw/state/ffceq0/att-before.json` (F-07 records 3,096 and 1 at authoring; the bar is equality with the saved baseline, not those numbers), and the diff of sorted `id`/`tree`/`native_status`/`last_history_at`/`detail_text` tuples is empty.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

Carried verbatim from `ffceq0` Step 0; where a line says "this plan" it means the split parent `ffceq0`.

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `artifact_meta.history(id6)`, `artifact_meta.query(...)` with typed filters (type, status, Set, order, `depends_on`, `latest_gate_review_of`, `path`) and an `incomplete` list, `artifact_meta.resolve(path_or_id6)`, `artifact_meta.read_at(id6, rev)` (Order 09 only), `artifact_meta.repair(id6, *, confirm=None)`, and the `artifacts.short_description` column. The legacy loader stores a multi-word `- Status:` raw value in a legacy-only column and sets `artifacts.status` only for a single token (tve77h OQ-03, which names this plan as the carrier of the reader decision).
- One status normalizer already exists: `plans.normalize_status` maps `EXECUTED`/`DONE` to `executed` and any other unrecognized token to `plans.LEGACY_GROUP` (`legacy/unknown`); `plans.read_status` applies it to the FIRST token of the whole-file `- Status:` line. `attention._plans_record` and `ipd_lint.lint_text` (M105) already use it.
- `selectors.metadata_region` is the shared region bound (the bullet block before the first `##`, or the YAML fence). The PARITY CONSTRAINT comment above `selectors._STATUS_RE` records the 24-plan disagreement and forbids changing it without "owning that contract change", which D-1 does here.
- Shared history rules: `attention_contract.history_block`, `attention_contract.newest_history_record`, `attention_contract.last_history_at`.
- `aw find` for plans uses `plans_index.plan_entry` and `plans_index.query` for display rows and `selectors.resolve` (through `cli._resolve_selectors_with_kinds`) for selector hits; `aw ipd board` is `cli._run_plans` over `plans.scan`.
- New CLI leaves are declared in `command_surface` (`CommandDeclaration`) and covered by `tests/conformance_matrix.py`. Order 03 (`1ajqaa`) creates `agent_workflows/meta_cli.py` for `aw show --history`, so this plan adds `check meta` and `meta repair` to that module.
- Traversal exclusions live in `layout.TRAVERSAL_EXCLUSIONS` (consumed by `selectors`); `_SKIP_NAMES` is defined separately in `check_engine`, `selectors` and `artifact_refs`.
- Core tier: modules set `pytestmark = pytest.mark.core`; the bare gate is `python3 -m pytest` (30 s budget).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).


## Findings

Carried from `ffceq0` `## Findings` (measured 2026-11-02 at `0cbfcc706`), the rows this part relies on:

| Id | Evidence | Finding |
|---|---|---|
| F-07 | `aw attention --all --format json`: 3,096 items (plans 1,719, backlog 1,133, research 165, specs 48, prompts 30, releases 1), 1 violation, `valid: true` | Baseline for E-05. |
| F-08 | `history_block(` call sites: `attention` 6, `check_engine` 3; `last_history_at(` and `history_block(` together 10 sites in `attention` and `check_engine` | All history reads in this plan's modules go through `artifact_meta.history`. |

Step-complexity measurement for this part (2026-11-07, at the worktree HEAD of the split; the rule is that no E-item hides more than about 25 units of work):

- E-01 (pin, `ffceq0` E-04): 1 new module with one fixture per tree (6 trees) plus the `--check` exit code; 5 baseline modules (`test_attention` 76 tests, `test_attention_contract` 27, `test_history_consumers_shared_reader` 5, `test_history_date_clock_readers` 3, `test_prompts_attention` 5). About 13 units.
- E-02 (move, `ffceq0` E-05): measured with an `ast` walk of `agent_workflows/attention.py` for `history_block(`, `last_history_at(`, `read_readiness(`, `_ITEM_DEPS_RE`, `_plans_id(`, `_extract_detail(`/`_frontmatter_block(` and `^-` literals outside comments: 31 site lines in 15 functions (`_plans_record` 6, `_spec_record` 4, `_release_record` 4, `_research_record` 3, `_backlog_record` 3, `_prompts_record` 2, `read_readiness` 2, and one each in `count_question_stats`, `_extract_detail`, `_extract_item_dependencies`, `_plans_id`, `scan`, `item_for_path`, `format_plan_detail_line`); `count_question_stats` (open-question body prose, N3) and `_extract_detail` (D-3 fallback) stay, so about 24 sites move. About 25 units.

READER LEDGER rows this part moves (copied from `ffceq0`; the full ledger stays in `ffceq0`):

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `attention._plans_record` and siblings | per-tree reads, drift on missing/unknown status | E-04 module, `tests/test_attention.py`, `tests/test_attention_degraded_item.py` | same Items and drift |
| `attention._extract_detail` | Summary, Scope, Concern, Question, Title, H1 cascade | `tests/test_attention.py`, `tests/test_specs_releases_unsafe_field.py` | D-3 |
| `attention_contract.last_history_at` callers | newest history record date | `tests/test_history_consumers_shared_reader.py`, `tests/test_history_date_clock_readers.py` | same rule over `artifact_meta.history` |

DECISIONS that govern this part's reader moves (copied verbatim from `ffceq0`, which keeps the full D-1..D-6 table; a test that changes after a move must be one of these, never a silent change):

- D-1 (status of the 24 multi-word plans; F-03, F-04). KEPT: the canonical normalized status that `aw attention`, `aw ipd board` and `ipd_lint` already report (`executed` for `EXECUTED ...` and `DONE ...`, `legacy/unknown` for any other unrecognized token). For PLAN records only, both `aw find` paths match `plans.normalize_status` of the FIRST token of the cached raw value (the `plans.read_status` rule). Every other type keeps today's exact single-token match on the raw value, because `plans.normalize_status` knows only the plan vocabulary and maps `open`, `implemented`, `active` and `planned` to `legacy/unknown` (measured at review: `aw find backlog open` lists 27 rows and `aw find specs implemented` 22 today, and both must stay unchanged). The rule lives in `selectors`' `MATCH_STATUS` branch, so every `selectors.resolve` caller that allows `MATCH_STATUS` sees it; E-01 pins one non-find caller (`tests/test_selector_resolver_matrix.py`) so the change to those callers is observed, not assumed. WHAT EACH CONSUMER LOSES OR GAINS: `aw find plans executed` (selector path) GAINS the 24 plans plus `vfa1tl` and agrees with `--status executed` (1,635 rows at authoring); `aw find plans EXECUTED` stops matching `vfa1tl` by exact case (its only match today); the `aw find` JSON `status` of those 24 changes from the prose line to `executed` (the prose stays in the raw legacy column and in the file); the test edits are the expected value in `tests/test_find_single_read.py::test_d_status_disagreement_record_matches_and_preserves_plans_index_status` (only if its `plans_index` assertion reads through the moved path; Order 09 owns `plans_index`) and the `_read_status(multi)` assertion in `tests/test_front_matter_loose_whitespace.py::test_single_token_status_contract_survives`, whose `read_front_matter_status(multi)` and `parse_plan_file` assertions stay unchanged (D-2; the runner is Order 09's). Reason: one reader, one answer (4.3), and it is the answer three surfaces already give. The migration (Order 04) normalizes these terminal records at the cutover.
- D-3 (detail text). KEPT: the `_extract_detail` cascade as the fallback; `short_description` wins when present (4.4 first bullet). In phase B no record has one, so output is unchanged until Order 13.
- D-4 (status bullet outside the metadata region; F-06). KEPT: region-bounded reading. The 4 records are 3 reviews and 1 walkthrough, which have no lifecycle status, so no plan-status consumer changes.

## Proposed changes (ordered, validatable)

1. Pin then move `attention` and its history reads (E-01, E-02; `ffceq0` E-04, E-05).

## Deferred / out of scope (with reason)

- E-03 (`ipd_lint`, `ffceq0` E-09). Moved to 1suzlp (round-3 split 2026-11-09 per research nj8zdp guidance).
  - Carrier: 1suzlp
- The post-cutover `last_history_at` from the newest event `at` with `last_history_precision`.
  - Carrier: cxxmyv
- `selectors` and `aw find` (`ffceq0` E-01 to E-03). Moved to r81uvz (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: r81uvz
- The event-owned readiness/approval/coverage rules (AC-15).
  - Carrier: 2xwb9b
- Cache parity, offline proof and the residual audit over `attention` and `ipd_lint`: kept in the split parent.
  - Carrier: ffceq0

## Scope check

- Over-scope: none. `attention_contract.py` changes only if a history reader must accept `artifact_meta.history` records.
- Under-scope: none known. This part carries E-04 and E-05 of `ffceq0` unchanged; E-09 (this plan's E-03) moved to `1suzlp`.

## Required tests / validation

New core module `tests/test_readers_attention.py`. The existing modules named in E-01 run before and after each move with an empty outcome-list diff.

Commands: the named modules, the bare core gate `python3 -m pytest`, `aw check`, `aw sanitize --agent`. The thorough tier `make test-all` runs once, in `ffceq0`'s final item.

## Spec / documentation sync

N/A: no spec text changes; this part implements `4sd62s` 4.4 (the `_extract_detail` fallback, D-3, and the bullet "Gate IPD-S405" through `history`) and section 7 step 5 for `attention`. It uses `artifact_meta.read_text`, which Order 27 adds and amends into spec 4.3.

## Open questions

### OQ-01: Does this part fit the step-complexity limits?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Round 3 (2026-11-09): 2 E-items, 3 work Scope-Paths; E-03 moved to `1suzlp`, which carries the original's E-09 -> E-07 edge on the check_engine parts. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --stat agent_workflows/attention.py agent_workflows/attention_contract.py` empty, then `python3 -m pytest -o addopts="" -v tests/test_readers_attention.py` all PASSED with one test per tree, and the saved outcome list (`.aw/state/ffceq0/E-04-before.txt`, `wc -l`) of `python3 -m pytest -o addopts="" tests/test_attention.py tests/test_attention_contract.py tests/test_history_consumers_shared_reader.py tests/test_history_date_clock_readers.py tests/test_prompts_attention.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `diff .aw/state/ffceq0/E-04-before.txt .aw/state/ffceq0/E-05-after.txt (file names keep the `ffceq0` item numbers so the parent's final items find them)` printing nothing, and the output of a `python3 -c` snippet that loads `.aw/state/ffceq0/att-before.json` (saved in E-01) and a fresh `aw attention --all --format json`, sorts `(id, tree, native_status, last_history_at, detail_text)` tuples, and prints `items N -> N, violations M -> M, diff 0` with equal before and after values; plus the test in `tests/test_readers_attention.py` asserting that an `incomplete` record becomes an `attention.missing-status` violation, PASSED.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every `- Item-Dependencies:` edge is executed. Every reader move is pin-first: the baseline runs green on the unmodified code before the matching move, and a test edited after a move must be one that the copied decisions name.

Honesty rule: run the named modules and `python3 -m pytest` (core gate) and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit dqutt8 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
