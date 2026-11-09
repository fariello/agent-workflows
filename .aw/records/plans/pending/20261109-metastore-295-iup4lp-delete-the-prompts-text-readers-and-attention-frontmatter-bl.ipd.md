# IPD: Delete the prompts text readers and attention frontmatter block reader

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 allows exactly one metadata reader (`artifact_meta`). Part 16 of the round-3 split of `k6jd6l` (Order 43, research `nj8zdp` guidance): delete `prompts.read_metadata_id6`, `prompts.read_metadata_status` and `prompts._METADATA_STATUS_RE` (the staged-prompt `aw-prompt` comment readers) and `attention._frontmatter_block` (a raw YAML block reader). Measured callers at `f83159217`: `artifact_rename._read_existing_id6` (1), `attention._prompts_record` (2), `cli._find_prompt_id6` (2), `prompts.update_metadata_status` (internal), `status_set.read_artifact_record` and `status_set._prepare_status_change` (2), `attention._extract_detail` (1, `_frontmatter_block`); test `tests/test_prompts_new.py` (1).
- Scope: The `prompts` and `attention` reader part of `k6jd6l` E-11 subset 1. EXCLUDES `artifact_rename`'s own regex literals (Order 245, `qttoyc`) and `attention`'s inline literals (Order 248, `tdhav3`).
- Scope-Paths: agent_workflows/prompts.py, agent_workflows/artifact_rename.py, agent_workflows/attention.py, agent_workflows/cli.py, agent_workflows/status_set.py, tests/test_prompts_new.py, .aw/records/plans/pending/20261109-metastore-295-iup4lp-delete-the-prompts-text-readers-and-attention-frontmatter-bl.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:8ysz6b, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 295
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: iup4lp

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from k6jd6l (round 3, research nj8zdp guidance).

## Goal

No module defines or calls `read_metadata_id6`, `read_metadata_status`, `_METADATA_STATUS_RE` or `attention._frontmatter_block`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Carried from `k6jd6l` E-11: "`prompts._METADATA_STATUS_RE`, `read_metadata_id6` and `read_metadata_status`; `attention._frontmatter_block`". Save the before-list of `tests/test_prompts_new.py`, `tests/test_attention.py`, `tests/test_artifact_rename.py` and `tests/test_status_set.py` to `.aw/state/9o83cr/E-11c-before.txt`.

PIN RULE (carried from `9o83cr`): before an edit that deletes or retargets, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > <before-file>`); after it, run the same command into the matching after-file. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: callers first, then delete

- [ ] E-01 Change `artifact_rename._read_existing_id6` and `cli._find_prompt_id6` to read the prompt id through `artifact_meta.read_text(text, record_type="prompts")`.
  - Depends on: none
  - Expected outcome: neither calls `read_metadata_id6`.
  - Execution state: pending

- [ ] E-02 Change `attention._prompts_record`, `status_set.read_artifact_record` and `status_set._prepare_status_change` to read the prompt id and status through `artifact_meta.read_text`; change `prompts.update_metadata_status` to read the current status the same way.
  - Depends on: E-01
  - Expected outcome: no caller outside the definitions remains.
  - Execution state: pending

- [ ] E-03 Delete `prompts.read_metadata_id6`, `prompts.read_metadata_status` and `prompts._METADATA_STATUS_RE`; retarget `tests/test_prompts_new.py` to `artifact_meta.read_text`.
  - Depends on: E-02
  - Expected outcome: the three symbols are gone.
  - Execution state: pending

- [ ] E-04 Replace `attention._frontmatter_block` in `attention._extract_detail` with the research fields from `artifact_meta.read_text`, keeping the bulleted-form-wins cascade order, and delete `attention._frontmatter_block`; save the after-list; commit through `aw commit iup4lp -- <paths>`.
  - Depends on: E-03
  - Expected outcome: `attention` defines no `_frontmatter_block`; `aw attention --format json` is unchanged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `attention._extract_detail` reads Summary, Scope, Concern, Question, Title and the H1 in that order, bulleted form first, then the unbulleted YAML form; the YAML half is what `_frontmatter_block` fed.
- The `artifact_meta` interface (names from `tve77h`, `ffceq0`, `xexn45`): `read(id6) -> State`, `history(id6)`, `read_at(id6, rev)`, `read_text(text, *, record_type=None) -> State`, `append(id6, events, *, expect_seq)` with `dry_run`, the phase-B legacy writer (`append_legacy`, `render_legacy`), and the legacy loader (`load_legacy_artifact`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `f83159217` with `rg -n "read_metadata_(id6|status)|_METADATA_STATUS_RE|_frontmatter_block" agent_workflows tests`: see the Concern.

## Proposed changes (ordered, validatable)

1. Retarget the id readers (E-01).
2. Retarget the status readers (E-02).
3. Delete the `prompts` readers (E-03).
4. Delete `_frontmatter_block` and commit (E-04).

## Deferred / out of scope (with reason)

- `artifact_rename` regex literals.
  - Carrier: qttoyc
- `attention` inline literals.
  - Carrier: tdhav3

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 4 E-items, 6 work Scope-Paths.

## Required tests / validation

The four PIN modules above and `aw attention --format json`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3 and section 7 step 7. CONTRIBUTES to AC-1 (owned by `9o83cr`).

## Open questions

### OQ-01: `artifact_adopt._yaml_frontmatter_block` has a similar name; is it in scope?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No: `k6jd6l` E-11 names only `attention._frontmatter_block`, and `artifact_adopt._yaml_frontmatter_block` frames an inbox file before adoption (not a record); no plan in this family owns it, so if Order 280's F-24 grammar search lists it, it is recorded there as `delete (follow-on)`. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `rg -n "read_metadata_id6" agent_workflows/artifact_rename.py agent_workflows/cli.py` printing nothing and the before/after per-test lines of `tests/test_artifact_rename.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "read_metadata_(id6|status)" agent_workflows` listing only the two `prompts.py` definitions, and the before/after per-test lines of `tests/test_status_set.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "read_metadata_(id6|status)|_METADATA_STATUS_RE" agent_workflows tests` printing nothing and the before/after per-test lines of `tests/test_prompts_new.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `rg -n "_frontmatter_block" agent_workflows/attention.py` printing nothing, the `diff` of `aw attention --format json` against the Order 280 baseline `.aw/state/k6jd6l/before/` file (empty), `diff .aw/state/9o83cr/E-11c-before.txt .aw/state/9o83cr/E-11c-after.txt` with no FAILED or ERROR line, and `git show --stat` of the `aw commit iup4lp` commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Pin-first where an item deletes or retargets. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL output; never claim a result you did not run. Commits: only through `aw commit iup4lp -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
