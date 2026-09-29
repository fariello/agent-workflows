# IPD: Report a dangling record citation in packaged source as a check finding instead of extending the rename rewriter into the shipped package

- Date: 2026-09-29
- Kind: child
- Concern: `aw rename` never rewrites a record citation that lives in the shipped package, because the rewriter's scan list `artifact_core.REFERENCE_SCAN_ROOTS` covers records, three repo-root docs, `.aw/records/reviews` and `tests`, and does NOT cover `agent_workflows/` or `tools/`. So a rename leaves citations in the package dangling and a maintainer discovers them by hand, which has already cost hand-fixes at least once (`d6b2fa00`).
- Scope: Give the packaged source a DETECTOR rather than a rewriter. Add a `suffixes` parameter to `artifact_refs.dead_filename_citations` (which today cannot reach a `.py` file at all), add a `--source-citations` scan verb that reports a dangling record-filename citation under `agent_workflows/` and `tools/` with its file, line and cited name, and fix the 5 measured danglers the new detector finds. EXCLUDES extending `REFERENCE_SCAN_ROOTS` to rewrite the shipped package (rejected on measured evidence, see F-6 and F-7), EXCLUDES wiring the detector as an always-on `aw check` rule (the false-positive reason recorded at `plans_index.check_drift` is unretired, see F-8 and OQ-01), and EXCLUDES the two live-source spec-path citations already owned by pending plan `2wmwf7`.
- Scope-Paths: agent_workflows/artifact_refs.py, agent_workflows/cli.py, agent_workflows/comms.py, agent_workflows/agy_run.py, agent_workflows/oc_runipd.py, tests/test_source_citation_scan.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: zftbta
- Blocks-Release: next
- Set: zftbta
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 68hdic

## Workflow history

- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `zftbta`. `- Blocks-Release: next` and `- Work-Kind: bug` are INHERITED from the item and both are correct. THE ITEM'S PREMISE VERIFIES BUT ITS NUMBER AND ITS PREFERRED FIX DO NOT SURVIVE MEASUREMENT, and both corrections are the substance of this plan. The premise is confirmed by an actual dry-run, not by reading code: `aw rename specs .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md --to-id6` prints 74 `would rewrite` lines, 5 of them in `tests/`, and ZERO in `agent_workflows/`, while `agent_workflows/ipd_schema.py` line 4 cites that exact spec filename and is left untouched. The item's "44 citations" is NOT reproducible and is superseded here: measured with the repo's own `artifact_refs._FILENAME_TOKEN_RE` plus the boundaried legacy-prefix form, `agent_workflows/**/*.py` holds 61 citation tokens on 61 lines (20 full filenames, 41 legacy prefixes), and `tools/**/*.py` holds a further 22 that the item does not mention at all. MORE IMPORTANTLY, only 5 of those 83 are actually DANGLING; the rest cite records that still exist, so the item's framing ("leaves 44 citations dangling") overstates the live damage by an order of magnitude while UNDERSTATING the population at risk. THE ITEM'S PRIMARY FIX DIRECTION IS REJECTED ON EVIDENCE. It proposes "a third scan list (agent_workflows/, .py only) applied to reference rewriting". Measurement shows that rewriting the shipped package is both riskier and less valuable than the item assumes: 6 of the citation-bearing lines are NON-DOCSTRING STRING LITERALS, one of which (`runner_shared.py`, the `default_rb` branch selecting `tools/ipdrunner/20260823-pending-ipds-overnight-execution-runbook.md`) is a RUNTIME PATH CONSTRUCTION whose rewrite would break the runner's default runbook lookup, and another (`oc_runipd.py`'s `--help` epilog) is user-facing help text. Meanwhile the item's own cheaper alternative ("a CHECK that reports a dangling record citation in source rather than rewriting it") is the one that matches the measured need, since the actual cost is 5 stale strings a human cannot see, not a rewrite backlog. This plan therefore ADOPTS the alternative and records the rejection with its measurement rather than silently choosing. THE ITEM'S OPEN QUESTION IS ANSWERED, NOT DEFERRED: it asks "whether it should ask for confirmation as 5xzld0 does for tests/". With no rewrite there is nothing to confirm, so the question dissolves; that is recorded at F-7 rather than carried as an OQ. ONE ADJACENT PENDING PLAN OVERLAPS AND IS DELIBERATELY NOT DUPLICATED: `2wmwf7` (Set `ajomj3`, `to-review`) fixes 2 of the 5 danglers (`agy_run.py`'s `--spec` example and `check_engine.py`'s I-07 comment) and adds `tests/test_spec_path_citations.py`. This plan owns the OTHER 3 and a GENERAL detector; the file-level disjointness is stated at F-9 and the ordering consequence at OQ-02.

## Goal

Make a dangling record citation in the shipped package MACHINE-DISCOVERABLE instead of hand-discoverable, and fix the five that exist today. A maintainer who renames a record can then run one command to learn whether the package still cites the old name, rather than finding out months later by reading a comment. The rewriter is deliberately left alone, because measurement shows the package contains runtime path constructions that must not be rewritten.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before changing anything

- [ ] E-01 RE-MEASURE the dangling-citation census in packaged source at execution HEAD rather than trusting this plan's authoring numbers, because every one of them is a function of where records currently live and a concurrent lane may have renamed, archived or transitioned a record since authoring (which is the whole root cause here). Build the existence set exactly as `artifact_refs.dead_filename_citations` does (every `*.md` name and stem under `selectors.record_dirs` for all eight types, minus `artifact_refs._SKIP_NAMES`), then scan `agent_workflows/**/*.py` and `tools/**/*.py` for `artifact_refs._FILENAME_TOKEN_RE` matches and report, per token, whether it resolves. Record the total token count, the resolving count and the DANGLING count for each of the two trees. Confirm or correct the five danglers this plan names at F-2. If the set has drifted, use the measured set and say so at finalize; do NOT silently fix a different list than the one validated.
  - Depends on: none
  - Expected outcome: a pasted census giving, per tree, total citation tokens, resolving tokens and dangling tokens, plus the explicit dangling list, with any drift from this plan's F-1/F-2 numbers named rather than absorbed.
  - Execution state: pending

### Task group 2: make the existing detector able to reach a source file

- [ ] E-02 ADD a `suffixes` keyword parameter to `artifact_refs.dead_filename_citations`, defaulting to `artifact_core._TEXT_SUFFIXES` so EVERY existing caller keeps its present behavior byte for byte, and pass it through to the `artifact_core.iter_scan_files` call in that function's body (which today calls `iter_scan_files(repo_root, scan_roots)` and therefore silently falls back to the `(".md", ".txt")` default). This is the load-bearing defect behind the item's complaint that no check covers source: the function ALREADY accepts `scan_roots`, so a caller can aim it at `agent_workflows`, but with no `suffixes` parameter it can never open a `.py` file, so it returns an empty list and reads as "no danglers" when it means "nothing was examined". Verify the claim before and after by calling it with `scan_roots=("agent_workflows",)` and observing 0 findings before the change (a false negative) and a non-empty list after.
  - Depends on: E-01
  - Expected outcome: `dead_filename_citations` accepts `suffixes`, defaults it so no existing caller changes behavior, and returns a non-empty result for `scan_roots=("agent_workflows",), suffixes=(".py",)` where it returned `[]` before.
  - Execution state: pending

- [ ] E-03 MAKE the detector's type filter reach a citation whose facet is not the scanned type, by giving `dead_filename_citations` a way to answer "is this token a citation of ANY record type" rather than only of one. Today `_type_appropriate` returns False for a `.spec.md` token when `record_type="specs"` because the token is not clustered (it is a legacy `YYYYMMDD-HHMM-NN` name and the legacy branch is gated on `record_type == "plans"`), so the two most valuable danglers are only reachable via `record_type="plans"`, which is a misleading way to ask the question. Add a sentinel record type (or an explicit `any_type=True` flag; choose one and justify it in the docstring) under which a token is a candidate if it parses under ANY type's facet. Do NOT widen the existing per-type behavior: the per-type call must keep returning exactly what it returns today, because `plans_index.check_drift` and `research_index.check_drift` consume the per-type semantics.
  - Depends on: E-02
  - Expected outcome: a single call can enumerate dangling citations of every record type in a given tree, while every existing per-type call returns an unchanged result.
  - Execution state: pending

### Task group 3: give a maintainer one command to run after a rename

- [ ] E-04 ADD a read-only `--source-citations` scan mode that reports every dangling record-filename citation under `agent_workflows/` and `tools/` (`.py` only), one finding per line carrying the repo-relative file, the line number and the cited name, and exits nonzero when any finding exists so it is usable in a script. Wire it onto the existing `check` verb surface in `agent_workflows/cli.py` (locate the noun-verb registration by the content string `"Check a TYPE for drift/consistency"` and follow the flag-adding pattern its siblings use) rather than minting a new top-level verb, and honor the repository's `--agent` JSONL convention so an agent can consume it. It must be PURE READ: no rewrite, no prompt, no commit. State in its help text that it reports and does not fix, and why (a citation in packaged source may be a runtime path, see F-4).
  - Depends on: E-03
  - Expected outcome: a documented read-only mode that prints the measured danglers with file, line and cited name, exits nonzero when findings exist and zero when clean, writes nothing, and is reachable from `aw check`'s help.
  - Execution state: pending

### Task group 4: fix the danglers this plan owns

- [ ] E-05 CORRECT the three dangling citations that are NOT owned by pending plan `2wmwf7`, each to the record's real current name, located by content string rather than by line number: in `agent_workflows/comms.py` the module docstring's `.agents/docs/research/20260714-2300-01-same-box-agent-wakeup-mechanisms.md` (a path whose directory no longer exists either; re-point it at the real record or, if no successor exists, state that in the comment instead of naming a phantom file); in `agent_workflows/oc_runipd.py` the `--help` epilog line `runipd 20260824-ipdrunner-01-pr2nd0-harden.ipd.md` (the real record is `20260824-ipdrunner-01-pr2nd0-harden-ipdrunner-process-lifecycle-dependency-validation-and.ipd.md`, so the epilog shows a name that cannot be resolved; prefer the id6 form `runipd pr2nd0` if that is what the tool actually accepts, and VERIFY which forms it accepts before choosing); and in `agent_workflows/agy_run.py` the `--ipd` example citing `20260821-awoptimize-01-nmwy3m.ipd.md` (the real record is `20260821-awoptimize-01-nmwy3m-canonical-workflow-schema-and-compiler.ipd.md`). Do NOT touch `agy_run.py`'s `--spec` example or `check_engine.py`'s I-07 comment: those two belong to `2wmwf7` and editing them here would create the overlapping edit OQ-02 exists to avoid. These are comment and help text only; change no code path.
  - Depends on: E-01
  - Expected outcome: the three citations name records that exist on disk (or, where no successor exists, say so rather than naming a phantom), verified by an existence check on the exact strings now in the files, with `2wmwf7`'s two citations demonstrably unmodified.
  - Execution state: pending

- [ ] E-06 LEAVE the five legacy-prefix citations of retired `.agents/`-era plans alone and RECORD why in this plan, rather than "fixing" them. Measured: `20260715-1033-01`, `20260721-1353-01`, `20260723-1100-01`, `20260723-1100-02` and `20260723-1100-03` each resolve to no current record, so a naive sweep would flag them; but git shows each was RENAMED onto the id6 grammar (for example `.agents/plans/executed/20260723-1100-03-untracked-safety-convention-and-tracking-warning.md` -> `20260723-instsafe-03-2jovaz-untracked-safety-convention-and-tracking-warning.md`), and each citation appears in a comment describing WHAT THAT PLAN DID at the time, which was true when written. Re-point them only if E-01 confirms the successor record exists AND the surrounding comment reads as a live pointer rather than as history; otherwise leave them. This E-item's deliverable is the recorded decision plus whatever subset of the five the executor judges to be live pointers, with the judgement stated per citation.
  - Depends on: E-01
  - Expected outcome: a per-citation decision recorded for all five legacy prefixes, with the git rename evidence cited, and no citation rewritten on the basis of non-resolution alone.
  - Execution state: pending

### Task group 5: keep it from regressing

- [ ] E-07 ADD a behavioral regression test at `tests/test_source_citation_scan.py` that drives the new scan mode and asserts on its real output, and that proves the E-02 false negative cannot return. It MUST include a CONSTRUCTED case built in `tmp_path` (a fake repo with one record file and two source files, one citing the record's real name and one citing a name that does not exist) asserting the scan reports exactly the second, so the test does not depend on the live tree's current dangler set. It MUST also include the discriminating negative for E-02: assert that a scan restricted to `.md`/`.txt` suffixes finds nothing in a `.py`-only tree while the `.py` scan finds the planted dangler, which is precisely the bug E-02 fixes. Do NOT assert a count against the live repository tree: that number changes on every rename and would make this test the same kind of path-coupled trap that backlog `p0a5kr` exists to remove. Test OUTCOMES: drive the CLI or the public function and assert on findings, exit code and stderr, never on how any function is written (GUIDING_PRINCIPLES P16).
  - Depends on: E-04
  - Expected outcome: a new test that passes, that fails if `dead_filename_citations` loses its `suffixes` pass-through, and that contains no assertion keyed to the live repository's current dangler count.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The scan lists are a deliberate two-tier design, not an oversight. `artifact_core.SCAN_ROOTS` is the narrow tier consumed by the DETECTORS (`find_dangling_citations`, `dead_filename_citations`), and `REFERENCE_SCAN_ROOTS = SCAN_ROOTS + (".aw/records/reviews", "tests")` is the wider tier consumed by the REWRITER. Plan `5xzld0` created that split deliberately and recorded the reason it did not widen the narrow tier: `attention_contract`'s `reviews` TreePolicy decision refuses a reviews scan root and `tests/test_attention_contract.py` asserts no `SCAN_ROOTS` entry covers `reviews`. This plan adds a THIRD consumer (a source detector) and must not collapse the tiers.
- `artifact_core.iter_scan_files` already takes `suffixes`; `5xzld0` added it. `dead_filename_citations` was simply never updated to pass it through, which is why the detector cannot see a `.py` file. E-02 is therefore a one-line completion of an existing seam, not a new mechanism.
- `check_engine.check_refs` is a documented STUB returning `[]` and "remains the documented SEAM for future per-type ref checks". It is tempting to wire this plan's detector there. Do NOT, without retiring the false-positive reason recorded at `plans_index.check_drift`; see OQ-01.
- `_SKIP_NAMES` (`README.md`, `INDEX.md`, `STATUS.md`) exists because those are GENERATED manifests; any new scan must honor it, and the existence set the detector builds already does.
- A citation may be a pinned permalink (`/blob/<sha>/`), which names a file as it was at that commit and is correct forever. `artifact_refs._mask_permalinks` and `artifact_rename._PINNED_PERMALINK_RE` both exist for this. A source scan must not flag one.
- This repository treats an executed plan and a review record as IMMUTABLE. That is why a detector aimed at SOURCE is safe while a sweep aimed at records is not: source is editable, and a stale comment in it is a defect rather than a historical fact.

## Findings

| Id | Severity | Finding | Consequence |
|---|---|---|---|
| F-1 | HIGH | The premise verifies by DRY RUN, not by code reading. `aw rename specs .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md --to-id6` emits 74 `would rewrite` lines, 5 in `tests/` and **0** in `agent_workflows/`, while `agent_workflows/ipd_schema.py`'s module docstring cites that exact filename. The cause is that `REFERENCE_SCAN_ROOTS` covers records, `DECISIONS.md`, `README.md`, `ARCHITECTURE.md`, `.aw/records/reviews` and `tests`, and not the package. | The bug is real and reproducible on demand. Every claim below is measured against this same rename. |
| F-2 | HIGH | The live damage is **5** danglers, not 44: `agy_run.py` (`20260821-awoptimize-01-nmwy3m.ipd.md`), `agy_run.py` (`20260809-2211-01-aw-project-layout.spec.md`), `comms.py` (`20260714-2300-01-same-box-agent-wakeup-mechanisms.md`), `oc_runipd.py` (`20260824-ipdrunner-01-pr2nd0-harden.ipd.md`), `runner_shared.py` (`20260823-pending-ipds-overnight-execution-runbook.md`). Of 20 full-filename tokens in `agent_workflows/**/*.py`, 15 RESOLVE. | The item's number is wrong in both directions and both matter: the fix is small (5 strings), so a rewrite engine is disproportionate, while the exposure is larger than stated (F-3), so a detector is warranted. |
| F-3 | MEDIUM | The population at risk is **83 tokens on 83 lines**, not 44, and it spans a tree the item never mentions: `agent_workflows/**/*.py` holds 61 (20 full filenames + 41 boundaried legacy prefixes across 15 distinct prefixes) and `tools/**/*.py` holds 22 (21 full filenames + 1 legacy prefix). | Any scan this plan adds must cover `tools/` as well as `agent_workflows/`, or it under-reports by a quarter. E-01 and E-04 both name both trees. |
| F-4 | HIGH | Rewriting the package is UNSAFE, proven by classifying every citation-bearing line by AST + tokenizer: 28 are comments, 27 are docstrings, and **6 are non-docstring string literals**. The worst is `runner_shared.py`'s `default_rb` branch, `/ "20260823-pending-ipds-overnight-execution-runbook.md"`, a RUNTIME PATH CONSTRUCTION selecting the runner's default runbook, guarded by `if default_rb.is_file()`. A rewrite there silently changes which file the runner loads, or silently disables the default. `oc_runipd.py`'s dangler is `--help` epilog text and `cli.py`'s is a user-facing message string. | This is the decisive argument for detect-over-rewrite and the reason this plan rejects the item's primary fix direction. A "bad substitution changes runtime behavior" risk the item raised in the abstract is CONCRETE and locatable. |
| F-5 | MEDIUM | `artifact_refs.dead_filename_citations` CANNOT SEE A SOURCE FILE. It accepts `scan_roots` but not `suffixes`, and its body calls `iter_scan_files(repo_root, scan_roots)`, taking the `(".md", ".txt")` default. Verified: `dead_filename_citations(root, "plans", scan_roots=("agent_workflows",))` returns **0** findings, and so does the `"specs"` call, even though 5 danglers are present. | The existing "cheap alternative" the item hopes for is already 90 percent built and silently broken. Its failure mode is the worst kind: it reports zero and means "I opened nothing". E-02 owns this. |
| F-6 | MEDIUM | Extending `REFERENCE_SCAN_ROOTS` by `("agent_workflows", "tools")` introduces **zero** new `--to-id6` refusals, measured exhaustively over all 37 legacy-timestamp-named records: 18 already refuse today on baseline roots, 19 stay clean, 0 newly refuse. But it also pulls in 10 NON-`.py` files (`tools/README.md`, seven `tools/awphysical/*.md` prompt files, `tools/awphysical/migration-followup-review.md`, and the runbook itself), and it raises the rewriter's corpus from 2578 files / 63.0MB to 2789 files / 73.3MB (walk 248ms -> 332ms, read 67ms -> 172ms). | The extension is not blocked by the refusal gate, which is worth knowing because that was the plausible blocker. It is rejected on F-4's runtime-literal risk instead, and this row records that the cheaper objection does not apply, so a reviewer can dispute the real reason rather than a guessed one. |
| F-7 | MEDIUM | The item's open question ("whether it should ask for confirmation as `5xzld0` does for `tests/`") DISSOLVES under the chosen direction: a detector writes nothing, so there is nothing to confirm. For the record, the `tests/` prompt it refers to (`artifact_refs.filter_test_edits_interactive`) is TTY-gated and a non-interactive run rewrites WITHOUT asking, so a confirmation prompt would have given an unattended run no protection at all. | The question is answered, not deferred, and the answer also removes the safety story a rewrite-based fix would have relied on. |
| F-8 | MEDIUM | A filename-dangling rule is DELIBERATELY UNWIRED, with the reason in-tree at `plans_index.check_drift`: the primitive "is NOT wired as an always-on drift rule here: on real prose it flags legitimate historical/example filenames (false positives) ... enabling it awaits a durable 'known real names' source (run decision 05-3cmnfc-D3)". `check_engine.check_refs` is the documented seam and returns `[]`. | The recorded objection is about PROSE. Source comments are a narrower, editable corpus, so an opt-in scan is defensible where an always-on prose rule was not; but promoting it to gating is a separate decision and is OQ-01, not a step here. |
| F-9 | MEDIUM | Pending plan `2wmwf7` (Set `ajomj3`, `Status: to-review`, `Work-Kind: chore`) already owns 2 of the 5 danglers and declares `Scope-Paths: agent_workflows/agy_run.py, agent_workflows/check_engine.py, tests/test_spec_path_citations.py`. It independently measured "470 dangling full-path spec citations across 151 files" and correctly bounds its own test to package source. `tests/test_spec_path_citations.py` does not exist yet. | The two plans OVERLAP on `agent_workflows/agy_run.py` and are otherwise disjoint. E-05 partitions the edits by content string; OQ-02 records the ordering. The overlap is a coordination cost, not a duplication: `2wmwf7` fixes two strings, this plan builds the detector that would have found them. |
| F-10 | LOW | Two of the five danglers are near-misses that a careless fix would get wrong: the real records are `20260824-ipdrunner-01-pr2nd0-harden-ipdrunner-process-lifecycle-dependency-validation-and.ipd.md` and `20260821-awoptimize-01-nmwy3m-canonical-workflow-schema-and-compiler.ipd.md`, i.e. the cited names are TRUNCATIONS carrying the right id6 and the wrong slug. The `comms.py` one has no successor under the cited `.agents/docs/research/` directory at all. | A mechanical prefix fix would still dangle. E-05 requires an existence check on the exact final string, and allows "say there is no successor" for the `comms.py` case. |
| F-11 | LOW | The detector's per-type filter would hide the two most valuable danglers if asked the obvious way. `_type_appropriate` accepts `20260809-2211-01-aw-project-layout.spec.md` under `record_type="plans"` (via the legacy branch) and REJECTS it under `record_type="specs"` (it is not clustered, and the legacy branch is gated on plans). | Asking "are there dangling spec citations" returns nothing while asking "dangling plan citations" returns the spec ones. E-03 owns making the question askable honestly. |

## Proposed changes (ordered, validatable)

1. Re-measure the census in both source trees at execution HEAD before editing anything (E-01; F-1, F-2, F-3).
2. Complete the `suffixes` seam in `dead_filename_citations` so the detector can open a `.py` file at all, with every existing caller unchanged (E-02; F-5).
3. Make an any-type query expressible so a spec citation is not invisible to a spec-typed scan (E-03; F-11).
4. Add a read-only `--source-citations` scan over `agent_workflows/` and `tools/` reporting file, line and cited name, nonzero on findings (E-04; F-3, F-8).
5. Fix the three danglers this plan owns, located by content string, leaving `2wmwf7`'s two untouched (E-05; F-2, F-9, F-10).
6. Record a per-citation decision for the five retired-plan legacy prefixes instead of sweeping them (E-06; F-3).
7. Add a constructed regression test that drives the scan and pins the E-02 false negative, with no assertion keyed to the live dangler count (E-07; F-5).

## Deferred / out of scope (with reason)

- EXTENDING `REFERENCE_SCAN_ROOTS` TO REWRITE THE SHIPPED PACKAGE. Rejected, not deferred, on F-4: the package contains a runtime path construction (`runner_shared.py`'s `default_rb`) and user-facing help strings among its citations, so a substitution can change behavior rather than a document. F-6 records that the refusal gate does NOT block the extension, so the rejection rests on the runtime-literal risk alone. If a future maintainer wants it anyway, the honest precondition is a way to distinguish a comment or docstring citation from a live string literal, which the AST classification in F-4 shows is mechanically possible but is a separate piece of work.
- WIRING THE DETECTOR AS AN ALWAYS-ON `aw check` RULE. Deferred to OQ-01. The recorded objection (F-8) is a false-positive rate measured on prose; this plan neither inherits nor refutes it for source, and promoting a rule to gating without that measurement would redden the suite on historical comments.
- THE 470 DANGLING FULL-PATH SPEC CITATIONS IN RECORD TREES that `2wmwf7` measured. Out of scope and correctly unfixed: 404 are in `plans/executed/` and `reviews/`, which are immutable, and rewriting a citation that was correct when written falsifies history. This plan's detector is bounded to SOURCE for exactly that reason.
- `tools/**/*.py` CITATION FIXES. The scan covers `tools/` (F-3), but this plan fixes only the `agent_workflows/` danglers. The 22 `tools/` tokens include `tools/ipdrunner/runipd.py`'s compatibility shim and the `awphysical` harnesses; whether a stale citation there is a defect or a historical note needs the same per-citation judgement E-06 applies, and bundling it would make this plan two plans. If E-01 finds a DANGLING citation in `tools/`, file it rather than fixing it here.
- `- Work-Kind: bug` IS INHERITED AND IS ARGUABLE. The user-perceptible cost is a maintainer reading a comment that names a file which no longer exists, plus the hand-fixes already spent (`d6b2fa00`, "two spec handles in runner_shared.py comments"). That is a correctness defect in shipped text rather than a latency one, so it is not measured in milliseconds. The item's maintainer set this gate; this plan carries it rather than re-litigating it.

## Scope check

- Over-scope: none. Every declared path is touched by a named E-item: `artifact_refs.py` (E-02, E-03), `cli.py` (E-04), `comms.py`/`agy_run.py`/`oc_runipd.py` (E-05), `tests/test_source_citation_scan.py` (E-07), `CHANGELOG.md` (user-visible new scan mode). `runner_shared.py` is deliberately NOT in `Scope-Paths`: F-4 identifies its citation as a runtime path that must not change.
- Under-scope: the detector reports `tools/` but this plan fixes no `tools/` citation (recorded above). Two of the five danglers are fixed by `2wmwf7`, not here (F-9). The five legacy prefixes may end the plan unchanged by E-06's own design.

## Required tests / validation

- The bare suite, `python3 -m pytest`, with the actual `N passed` summary pasted. Configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`; do not add flags.
- `tests/test_source_citation_scan.py` specifically, including its constructed `tmp_path` case and the suffix-restriction negative.
- A before/after call of `dead_filename_citations(root, ..., scan_roots=("agent_workflows",))` proving the 0-findings false negative and its repair (E-02, V-02).
- An existence check on every citation string E-05 writes, run against the real tree.
- `aw check` (or `aw check all`) before and after, proving no new finding is introduced, since the plan adds a scan mode that is deliberately NOT wired into the gating set.
- A repeat of the F-1 dry-run (`aw rename specs ... --to-id6`, no `--apply`) confirming the rewriter's behavior is UNCHANGED by this plan, which is the point of choosing a detector.

## Spec / documentation sync

No `.spec.md` file is amended, and none is in `Scope-Paths`. The two specs adjacent to this change do not constrain it: `ipd-structure-and-linting` governs plan structure rather than scan roots, and the physical-layout spec governs where records live rather than who may cite them. The scan lists are code-level constants with their rationale in comments, not a spec-declared contract, and plan `5xzld0` established them the same way. `CHANGELOG.md` IS updated, because a new read-only scan mode is user-visible surface; write that entry without em or en dashes per the execution contract.

## Open questions

### OQ-01: Should the source-citation scan become a gating `aw check` rule, and on what measured false-positive rate?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because the plan ships the scan opt-in and an opt-in scan needs no false-positive budget. The decision needs a number this plan can supply but should not act on alone: F-8 records that the always-on version was refused for prose on measured false positives, awaiting "a durable 'known real names' source". Source comments are a narrower corpus, and F-2's measured 5-of-20 dangling ratio in `agent_workflows/` is the starting datum. Promotion is a risk-appetite call (it can redden the suite on a historical comment), so it belongs to the maintainer. Backlog `hesb87` is the adjacent precedent: it asks the same promote-an-advisory question about `IPD-C801` using its measured false-positive rate.

### OQ-02: If `2wmwf7` and this plan execute in either order, which one writes `agent_workflows/agy_run.py`?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, and deliberately NOT expressed as an `Item-Dependencies` edge. Both plans touch `agy_run.py` but DIFFERENT strings: `2wmwf7` owns the `--spec` example (`20260809-2211-01-aw-project-layout.spec.md`) and this plan's E-05 owns the `--ipd` example (`20260821-awoptimize-01-nmwy3m.ipd.md`), so either order converges and no edit is lost. Each runner item executes in an isolated worktree whose changes return through the merge-and-revalidate gate, so a shared file is not a runtime hazard. A dependency edge would be actively worse: it would serialize two independent low-priority plans and, if `2wmwf7` were retired, would leave this plan blocked on something that will never execute. The residual risk is a textual merge conflict in one file, which the gate hands back to the agent. Recorded so a reviewer does not read the missing edge as an oversight.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted census for BOTH trees, giving total citation tokens, resolving tokens and dangling tokens per tree, plus the explicit dangling list with file and cited name. It must state whether the five danglers at F-2 and the token totals at F-3 (61 in `agent_workflows`, 22 in `tools`) still hold at execution HEAD, and name any drift explicitly. A census that reports only a total without the resolving/dangling split does NOT satisfy this item, because the whole correction this plan makes to the backlog item is that those three numbers differ.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: two pasted calls of `artifact_refs.dead_filename_citations` with `scan_roots=("agent_workflows",)`, one at the pre-change commit showing `0` findings (the false negative) and one after showing a non-empty list; PLUS proof that no existing caller changed, as the pasted result of the tests that exercise the per-type path (`tests/test_artifact_refs_rewrite.py` and whatever test covers `plans_index.check_drift`) passing unchanged, and a pasted `aw check` run showing no new finding. The default-preserving claim is the risky half of this item, so evidence that only shows the new capability is insufficient.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: a pasted demonstration that the any-type query returns the `.spec.md` dangler that the `record_type="specs"` query does NOT (F-11), showing both calls and both results side by side; PLUS a pasted before/after for at least two existing per-type calls (`"plans"` and `"research"`) over the default scan roots proving their results are byte-identical, since E-03 explicitly forbids widening them.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the actual terminal output of the new scan mode showing findings with repo-relative file, line number and cited name, its exit code on a dirty tree (nonzero) AND on a clean one (zero), the `--agent` JSONL form, and the relevant `--help` excerpt showing the mode is documented and states that it reports without fixing. Also paste evidence that it wrote nothing: a `git status --porcelain` before and after the scan showing an identical result.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: a `git diff` of the three edited files, plus for EACH new citation string a pasted existence check (an `ls` or equivalent on the exact path/name now in the file) proving it resolves, or for the `comms.py` case the pasted evidence that no successor exists together with the wording chosen instead. Plus a pasted `git diff` of `agent_workflows/check_engine.py` showing NO change, and a diff of `agy_run.py` showing the `--spec` line untouched, proving `2wmwf7`'s two citations were not absorbed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the recorded per-citation decision for all five legacy prefixes, each with the git rename evidence (the `git log --diff-filter=R` line showing the old and new name) and the judgement "live pointer, re-pointed" or "historical, left". If any was re-pointed, a diff and an existence check for it. A blanket "left all five" with no per-citation reasoning does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the pasted bare `python3 -m pytest` summary line with its `N passed` count, plus a targeted run of `tests/test_source_citation_scan.py` showing its individual tests pass. It must ALSO paste a deliberate-break demonstration: revert the `suffixes` pass-through from E-02 in the working tree, run the new test, paste the FAILURE, then restore and paste the pass. Without that, the test is unproven as a regression guard. Finally, paste a grep of the new test file showing it contains no assertion comparing against a hard-coded live-tree dangler count.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, whose absence is the correct unattested state; `/plan-review` owns that field and writing it here would forge a review that did not happen. Explicit human approval is required before execution, and the runner's queue action for this plan must not become `execute` until a human sets `approved`.

On execution: commit only the files named in `- Scope-Paths:` and only through `aw commit <plan> -- <paths>`, never `git add -A` and never with `--no-verify`; do not push; do not create a tag or release. Report the bare `python3 -m pytest` output verbatim rather than a claim about it. If E-01's re-measurement contradicts F-2 or F-3, say so at finalize and state which list was actually fixed, rather than reshaping the evidence to match this plan.

If any `V-*` item cannot be satisfied with the concrete evidence it demands, leave the plan in `pending/` and report the gap. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. The terminal transition is the tooled one (`aw ipd finalize`), not a hand `git mv`.
