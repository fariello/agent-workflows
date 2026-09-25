# IPD: Split research pipeline position from shelf status so a prompt carries no hot status

- Date: 2026-09-24
- Kind: child
- Concern: ONE STATUS ENUM IS APPLIED TO EVERY RESEARCH KIND AND ONLY FITS ANSWER DOCUMENTS. `research_contract.STATUSES` (`todo`/`active`/`reference`/`archive`) is not keyed by kind, and `research_cmd.plan_new` / `research_cmd.plan_new_comparison` write `status="todo"` for every kind including the `NN=00` `research-prompt`. On a report `todo` means "not yet ingested"; on a prompt it means "never dispatched", and no state says a prompt WAS run. The structural stand-in (`research_index.derive_unrun_prompts` / `run_prompt_set_ids`) keys on "an `NN>=01` sibling EXISTS", which is wrong in both directions (measured, Findings F-2/F-3): it calls the never-run `awclia` set RUN because `new-comparison` pre-scaffolds empty report stubs, and it calls the provenance prompt `3nlmug` (`outcome: adopted`, `consumed-by: [25kzda]`) UNRUN. A second consumer has forked the vocabulary outright: `status_set.TYPE_STATUSES["research"]` is `{open, active, done, parked}`, and `aw set done <research-id6> --yes` WRITES `status: done`, which `research_contract.validate_frontmatter` then rejects (F-4).
- Scope: IN: (a) amend spec `5tapom` sections 3.1/3.2 to define two axes; (b) a DERIVED, set-level pipeline position `unrun`/`partial`/`synthesized` computed from set shape plus whether members carry a body, absent for a set with no prompt; (c) a `research-prompt` carries no hot status (`todo`/`active` refused), may carry a cold shelf status (`reference`/`archive`), and is created without one; (d) move every consumer: `research_contract`, `research_cmd`, `research_index`, `research_archive`, `attention`, `attention_contract`, `lifecycle_style`, `status_set`; (e) strip `status: todo` from the 7 hot prompts; (f) docs. OUT: retiring the `.aw/records/prompts/` research kind (OQ-01), and the stale-row data cleanup the item itself disowns.
- Scope-Paths: .aw/records/specs/approved/20260824-2000-01-research-lifecycle-reliability.spec.md, agent_workflows/research_contract.py, agent_workflows/research_cmd.py, agent_workflows/research_index.py, agent_workflows/research_archive.py, agent_workflows/attention.py, agent_workflows/attention_contract.py, agent_workflows/lifecycle_style.py, agent_workflows/status_set.py, tests/test_research_index.py, tests/test_research_cmd_create.py, tests/test_research_archive.py, tests/test_attention.py, tests/test_status_set.py, .aw/records/research/README.md, docs/artifact-lifecycles.md, .aw/records/research/20260823-actorenv-00-8it88r-deriving-actor-identity-host-and-model-from-coding-agent-environments.research-prompt.md, .aw/records/research/20260826-awclia-00-f79ve1-aw-cli-naming-ia.research-prompt.md, .aw/records/research/20260826-awrunverify-00-3nlmug-aw-run-and-verify-design-prompts.research-prompt.md, .aw/records/research/20260830-humanchk-00-5ek188-human-owned-task-tracking.research-prompt.md, .aw/records/research/20260830-privrecs-00-nilw5h-private-records-repo-trackedness.research-prompt.md, .aw/records/research/20260831-cross-platform-agent-write-confinement-00-q65sz3-cross-platform-agent-write-confinement.research-prompt.md, .aw/records/research/20260905-skill-authoring-best-practice-00-ti73qs-skill-authoring-best-practice.research-prompt.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Set: resstatus
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 5e3nj2
- From-Backlog: imntrh
- Blocks-Release: next

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog imntrh; re-measured the prompt-set corpus (19 prompt sets, 7 hot prompts), found `awclia` mis-derived RUN from empty scaffold stubs and `aw set` writing an invalid `status: done`, and found only `chkplace` genuinely double-homed.

## Goal

Give research two axes instead of one conflated field: a derived set-level PIPELINE POSITION that answers "was this prompt run, and how far did the fan-out get", and the existing per-document SHELF STATUS that answers "has this answer been ingested, and is it cold". A prompt stops carrying a hot status it cannot substantiate, and every consumer reads the axis that fits it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: contract

- [ ] E-01 Amend spec `5tapom`: replace the 3.2 bullet "`status` stays the four-state vocabulary (`intake`/`active`/`reference`/`archive`); NO new state" with the two-axis rule (shelf status `todo`/`active`/`reference`/`archive` for answer docs; a `research-prompt` carries no hot status; derived pipeline position `unrun`/`partial`/`synthesized` per set, absent for a set with no prompt), and rewrite 3.1's "has NO `NN>=01` sibling" definition to "no non-prompt member carries a body", with the provenance and cold guards from E-04. Append a `## Workflow history` note citing this plan. Status stays `approved`.
  - Depends on: none
  - Expected outcome: the spec no longer contains "NO new state"; 3.1 names the three positions and the body rule.
  - Execution state: pending

- [ ] E-02 In `research_contract`: add `PIPELINE_POSITIONS = frozenset(("unrun", "partial", "synthesized"))` and `SYNTHESIS_KINDS = frozenset(("reconciliation-report", "findings"))`; in `validate_frontmatter`, when `kind` is `research-prompt`, make `status` optional and REFUSE a hot value (`HOT_STATUSES`) with `FrontmatterError("status", "a research-prompt carries no hot status; its pipeline position is derived")`. Answer kinds keep `status` required. `STATUSES` is unchanged.
  - Depends on: E-01
  - Expected outcome: a prompt dict without `status` validates; one with `status: todo` yields exactly that error; a report without `status` still fails.
  - Execution state: pending

- [ ] E-03 In `research_cmd.build_frontmatter`, accept `status: Optional[str]` and emit no `status:` line when it is None; `plan_new` and `plan_new_comparison._mk` pass `None` when `kind == "research-prompt"`. Add a test in `tests/test_research_cmd_create.py` asserting the `new-comparison` `00` file has no `status:` line and every other member still reads `status: todo`.
  - Depends on: E-02
  - Expected outcome: a fresh comparison set's prompt carries no status; reports unchanged.
  - Execution state: pending

### Task group 2: derivation and its consumers

- [ ] E-04 In `research_index`: add `has_body: bool = False` to `DocEntry` (set in `_scan_docs` from non-whitespace text after the closing `---`), and add `derive_pipeline_positions(entries) -> Dict[str, str]`. A set has a position only if some member is `kind: research-prompt` (any order, which also catches a prompt filed outside `NN=00`). Let LANDED be non-prompt members with `has_body`. `synthesized` if a LANDED member's kind is in `SYNTHESIS_KINDS`; `partial` if LANDED is non-empty otherwise; `unrun` if LANDED is empty AND every prompt in the set has `outcome: none-yet` AND no cold status; otherwise the set is absent (a provenance or shelved prompt, not pipeline work). Reimplement `derive_unrun_prompts` (prompts of `unrun` sets) and `run_prompt_set_ids` (sets at `partial` or `synthesized`) on it, and key the `check_drift` `STALE_STATE_RULE` "doc in RUN set" branch on `synthesized` only, since a landed `todo` report in a `partial` set is legitimately awaiting ingestion. Add `tests/test_research_index.py` cases: an all-stub comparison set is `unrun`; one bodied report of two is `partial`; a bodied reconciliation is `synthesized`; an adopted lone prompt and an `archive` lone prompt are absent and not in `derive_unrun_prompts`; a set with no prompt is absent.
  - Depends on: E-02
  - Expected outcome: `aw research pending` lists `f79ve1` (awclia) and no longer lists `3nlmug`, `jd8qhs`, `g5vhpz`, `2838rp`, `q48a20`.
  - Execution state: pending

- [ ] E-05 In `research_index.build_index_md`, add pipeline position to the "Needs addressing" band: list `unrun` and `partial` prompts with their position, alongside the existing `todo` answer docs (a statusless prompt would otherwise vanish from the band). In `research_archive`: `suggest_triage` keeps calling `research_index.run_prompt_set_ids` (now body-aware); `plan_transition` refuses a hot `new_status` for a `research-prompt` with the E-02 message. Add a `tests/test_research_archive.py` case for the refusal.
  - Depends on: E-04
  - Expected outcome: `aw research promote <prompt-id6> --to todo` exits nonzero; `--to reference` still moves it into the shard.
  - Execution state: pending

- [ ] E-06 Classify research prompts in `aw attention` by derived pipeline position. Mapping `unrun`->READY, `partial`->ACTIVE, `synthesized`->DONE lives in a new `attention_contract._PROMPT_PIPELINE_MAP`, mirrored as `_RESEARCH_PAIRS` entries in `lifecycle_style` so `test_all_owner_enums_are_covered_by_native_maps` holds. `attention._research_record` accepts a statusless `research-prompt` (no `attention.missing-status`), and `attention._reclassify_stale_research` sets each prompt Item's class from `research_index.derive_pipeline_positions` (absent position: `reference` or no status -> DONE, `archive` -> PARKED), leaving the answer-doc stale reclass as is; `attention.item_for_path` uses the same derivation. Add `tests/test_attention.py` cases for an unrun statusless prompt (READY) and a partial one (ACTIVE).
  - Depends on: E-04
  - Expected outcome: `aw attention --type research` shows `f79ve1` READY, `3nlmug` not READY.
  - Execution state: pending

- [ ] E-07 In `status_set`, replace the forked `TYPE_STATUSES["research"] = {"open", "active", "done", "parked"}` with `set(research_contract.HOT_STATUSES)` (the backlog-entry precedent: derived, never re-listed). A cold target (`reference`/`archive`) is refused with a message naming `aw research promote <id6> --to <status>`, because only that verb moves the file into its shard (`record_placement.resolve_transition_path` has no research placement). A hot target on a `research-prompt` is refused with the E-02 message. Add `tests/test_status_set.py` cases using `create_research`.
  - Depends on: E-02
  - Expected outcome: `aw set done <research-id6> --yes` refuses and leaves the file byte-identical; `aw set active <report-id6> --yes` still writes `status: active`.
  - Execution state: pending

### Task group 3: data, docs, suite

- [ ] E-08 Remove the `status: todo` line from the 7 hot prompts named in `- Scope-Paths:` (the files matching `^kind: research-prompt` that carry `^status: (todo|active|intake)`). Do not touch the 15 cold-shelved prompts. Regenerate with `python3 -m agent_workflows research index`.
  - Depends on: E-02, E-04
  - Expected outcome: no research prompt carries a hot status; `index --check` reports no `frontmatter-invalid` for any prompt.
  - Execution state: pending

- [ ] E-09 Update `.aw/records/research/README.md` "States and layout" (it still says `intake`) and `docs/artifact-lifecycles.md` "Statuses" with a short second table for pipeline position and one sentence that a research prompt carries no hot status. No em or en dashes in `docs/artifact-lifecycles.md`.
  - Depends on: E-01
  - Expected outcome: both docs name `unrun`/`partial`/`synthesized` and neither lists `todo` as a prompt state.
  - Execution state: pending

- [ ] E-10 Run the bare suite `python3 -m pytest`.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07, E-08, E-09
  - Expected outcome: the summary line reports 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The backlog entry of `status_set.TYPE_STATUSES` states the rule this plan applies to research: a status copy must be DERIVED from the owning module, because a re-listed copy desyncs (GUIDING_PRINCIPLES P8).
- Research front matter is plain YAML, rewritten via `research_archive._rewrite_status_in_text`; cold statuses move files into `reference/YYYYMM/` or `archive/YYYYMM/` via `research_archive._shard_subpath`.
- `INDEX.json`/`INDEX.md` are generated and untracked (`git ls-files .aw/records/research | grep -c INDEX` prints `0`), so adding `DocEntry.has_body` changes no tracked file.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone.

## Findings

- F-1 CONFIRMED: `research_cmd.plan_new_comparison._mk` passes `status="todo"` for the `research-prompt` it scaffolds at order `00`. Probe in a scratch repo: `research new-comparison --models gpt56,gemini36flash --apply` wrote a 4-file set, then `research pending` printed "no unrun research prompts".
- F-2 NEW, THE CORE FALSE NEGATIVE: that probe shows the sibling-exists rule cannot see an unrun comparison set, because the scaffold creates the siblings. Live instance `awclia`: all four non-prompt members are 224 to 257 bytes, front matter only, yet `aw attention` classes prompt `f79ve1` as `parked` (stale-reclassed as RUN). Body presence, not member existence, is the signal, and the stubs themselves declare the fan-out width, so no new "expected width" field is needed.
- F-3 CONFIRMED: `aw research pending` lists `3nlmug` (`outcome: adopted`, `consumed-by: [25kzda]`) and `q48a20` (adopted, 11 consumers), plus cold-shelved `jd8qhs`, `g5vhpz` (`reference`) and `2838rp` (`archive`). Hence the provenance and cold guards in E-04.
- F-4 NEW: `status_set.TYPE_STATUSES["research"]` is `{"open", "active", "done", "parked"}`. Scratch probe: `aw set done <id6> --yes` committed `status: done`; `research_contract.validate_frontmatter` on that value returns `status must be one of ['active', 'archive', 'reference', 'todo']`. `aw set reference` is refused outright.
- F-5 PARTLY FALSE in the backlog item: "FOUR sets exist in BOTH trees". Measured, `hostprobe`, `awdeliv` and `wtiso` have NO `research-prompt` in the research tree (their `00` members are `research-report`s); only `chkplace` (`rzfaon`) is truly double-homed. The other three follow the documented prompts/ convention. This lowers the urgency of OQ-01.
- F-6 Corpus: 19 of 50 sets carry a `research-prompt`; 7 prompts are hot (`todo`), 15 are cold. The 7 are the E-08 migration set.

## Proposed changes (ordered, validatable)

1. Contract (E-01..E-03): spec amendment, kind-conditional status validation, prompts created without status.
2. Derivation (E-04): one body-aware `derive_pipeline_positions`; existing helpers become thin views over it.
3. Consumers (E-05..E-07): index band, promote refusal, attention classes, `aw set` de-forked.
4. Data and docs (E-08, E-09), then the suite (E-10).

## Deferred / out of scope (with reason)

- Retiring the `research` kind from `.aw/records/prompts/` and re-pointing the `research-prompt` workflow at the research set (maintainer decision of 2026-09-11 recorded in `imntrh`). It changes a shipped workflow's output location, `prompts.PROMPT_KINDS`, and the prompts README, none of which the status misfit needs; see OQ-01.
  - Carrier-Declined: pending OQ-01; if the default holds it is authored as `resstatus` Order 02, and `imntrh` stays `graduated` (not `done`) until that plan exists.
- Promoting the stale finished rows and adopting `sx0cqv`'s delivered reports from `.aw/inbox/`: data cleanup the backlog item explicitly disowns.
  - Carrier-Declined: operator data cleanup via existing verbs (`aw research promote`, `aw research set-outcome`, `aw adopt`), no code change to plan.
- Empty report stubs (no body) still appear as `todo` answer rows in `aw attention`. They roll up under their set's position and hiding them is a board-noise change, not this misfit.
  - Carrier-Declined: not a defect in the vocabulary; revisit only if measured as board noise after this lands.

## Scope check

- Over-scope: none; each consumer listed is one that reads or writes research status or the run/unrun signal (grep for `run_prompt_set_ids`, `derive_unrun_prompts`, `HOT_STATUSES`, `normalize_status`, `TYPE_STATUSES`).
- Under-scope: `oc_runipd`/`runner_shared` do not read research status (grep found only an unrelated docstring mention in `runner_shared`), so they are not moved.

## Required tests / validation

New tests in `tests/test_research_index.py`, `tests/test_research_cmd_create.py`, `tests/test_research_archive.py`, `tests/test_attention.py`, `tests/test_status_set.py`; the E-04 and E-07 tests are shown failing against HEAD first. Live-corpus checks via `aw research pending` and `aw attention --type research`. Bare suite last.

## Spec / documentation sync

Spec `5tapom` (`.aw/records/specs/approved/20260824-2000-01-research-lifecycle-reliability.spec.md`) is amended in E-01 and listed in `- Scope-Paths:`. WHY: its 3.2 "NO new state" is the exact clause that forced runnedness into a sibling-existence heuristic, and its 3.1 definition is the rule F-2 and F-3 falsify; leaving it would make the spec contradict the code this plan ships. Docs: E-09.

## Open questions

### OQ-01: Does retiring the prompts/ research kind ride in this Set now, or wait?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: The maintainer decided (2026-09-11) that the research set owns the prompt, but executing it re-points the shipped `research-prompt` workflow and `aw prompts new --kind research` (its default kind). F-5 shows only one set is actually double-homed. DEFAULT: author it as `resstatus` Order 02 after this plan lands, keeping this plan to the status misfit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n "NO new state\|unrun\|partial\|synthesized" .aw/records/specs/approved/20260824-2000-01-research-lifecycle-reliability.spec.md`; expect no "NO new state" hit and at least one hit each for the three positions, plus the new workflow-history line citing `5e3nj2`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the output of a `python3 -c` calling `research_contract.validate_frontmatter` on three dicts (prompt without status, prompt with `status: todo`, report without status); expect `[]`, one `status` error with the E-02 message, and one "missing required field 'status'" error.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -q tests/test_research_cmd_create.py` showing the new test passing, and the new test's name.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new `tests/test_research_index.py` cases FAILING against HEAD's `research_index` (stash-free: run them against a checkout of HEAD in a scratch worktree) and PASSING after; then paste `python3 -m agent_workflows research pending --agent | cut -f1` showing `f79ve1` present and none of `3nlmug`, `jd8qhs`, `g5vhpz`, `2838rp`, `q48a20`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `tests/test_research_archive.py` refusal test passing, and the "Needs addressing" section of a regenerated `INDEX.md` listing `f79ve1` with position `unrun`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new `tests/test_attention.py` cases and `tests/test_lifecycle_style.py` passing, and `python3 -m agent_workflows attention --type research --format json` filtered to `f79ve1` and `3nlmug` showing `f79ve1` ready and `3nlmug` not ready.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the new `tests/test_status_set.py` cases FAILING against HEAD (the `done` case writes `status: done`) and PASSING after; paste the refusal message for `aw set reference <id6>` naming `aw research promote`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `rg -l '^kind: research-prompt' .aw/records/research | xargs rg -l '^status: (todo|active|intake)' | wc -l` printing `0`, and `python3 -m agent_workflows research index --check` output containing no `frontmatter-invalid` line for a `.research-prompt.md` path.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste `grep -n "unrun\|partial\|synthesized" .aw/records/research/README.md docs/artifact-lifecycles.md` with hits in both files, and `grep -nP "[\x{2013}\x{2014}]" docs/artifact-lifecycles.md` printing nothing for the edited section.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste the final summary line of the bare `python3 -m pytest` run; expect `N passed` with 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`- Status: approved`). Commit only the `- Scope-Paths:` files through `aw commit 5e3nj2 -- <paths>`; never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. `imntrh` goes to `graduated`, not `done`, while OQ-01's follow-on is unauthored.
