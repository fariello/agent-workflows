# IPD: Tell agents to run the suite bare; never -n0 or an extra -q

- Date: 2026-08-29
- Kind: child
- Concern: Nothing in the always-loaded agent contract states how to invoke the test suite, so an agent overrode the repo's `-n auto` with `-n0` (measured 4-6x slower) and fought its own duplicated `-q` for ~19 minutes.
- Scope: The installed agent-contract text in `agent_workflows/engine.py` (the generator that owns the `aw:block` region of AGENTS.md), the regenerated AGENTS.md block, and a test asserting the guidance is present. NO change to `pyproject.toml` addopts, to any test's behavior, or to the runner.
- Scope-Paths: agent_workflows/engine.py, AGENTS.md, tests/test_agent_contract_test_invocation.py
- Item-Dependencies: none
- Status: approved
- Set: testinvoke
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: uyd3lw
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved
- Blocks-Release: next

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004. Self-review of a plan I authored, so every claim was re-verified against the repo rather than trusted. PR-001 (FIXED, HIGH): F-2 cited a single timing pair as if stable; remeasured under concurrent-agent load and got 50.65s vs 222.60s (4.4x) against the original 26.75s vs 147.73s (5.5x), so the plan now states the RATIO as the durable claim (4-6x) and explicitly warns against citing one absolute figure; E-01 and the Concern line corrected to match. PR-002 (FIXED, HIGH): OQ-01's reasoning was WRONG - it called -p no:randomly a harmless no-op because pytest-randomly is undeclared in pyproject, but the plugin IS installed in the active venv and randomization is live (pytest -o addopts= prints Using --randomly-seed=154451933), so the flag actually hides order-dependence bugs; OQ-01 resolved to YES, E-01 now forbids it, and V-01 requires all three flags plus the escape hatch to appear in the pasted evidence. Also recorded the secondary undeclared-plugin gap as out of scope. PR-003 (FIXED, HIGH): E-02 said to regenerate AGENTS.md through the normal installer path, but aw install . --dry-run declares a Target Delta of .aw/system/, .aw/config/project.json and .aw/state/durable, far wider than Scope-Paths and unsafe while wtiso holds lanes; E-02 now forbids a full install, names the narrow block-writer alternative, and V-02 demands a git status scope proof that those three paths were NOT written. PR-004 (FIXED, MEDIUM): recorded the validation coupling with i79rgh - Item-Dependencies: none is correct since Scope-Paths are disjoint, but a bare full-suite run here still shows i79rgh's two failures, which must be deselected and attributed, not fixed here. Verified clean: all path:line citations resolve (engine.py:1174, AGENTS.md:3/:60, engine.py:219-220, test_backlog_graduated.py:221), aw ipd lint conforming at author and review-finalize, E/V bijection 4/4, gate carries the full execution contract.

- 2026-08-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review, SECOND independent pass over the already-reviewed plan (requested again by the maintainer); APPROVE WITH REVISIONS APPLIED; PR-011..PR-016. The prior self-review's four fixes were re-verified and all HELD (every path:line resolves: engine.py:1174, AGENTS.md:3/:60, engine.py:219-220, test_backlog_graduated.py:221-236; F-3 reproduced exactly; OQ-01's correction confirmed, pytest-randomly importable but undeclared at pyproject.toml:38/:44 and randomization live with a fresh seed). The material new finding is PR-011 (HIGH): the validation baseline of "2874 passed, excluding the two failures owned by i79rgh" could not be met as written, because the real pre-existing set is 1 failure in the fast subset (2875 passed) and SIX in the full suite, four of them unmentioned CLI-surface failures from concurrent run_cli work, and one of i79rgh's two (test_todo_matches_attention) is FLAKY not deterministic (1 failure in 5 isolated runs). An executor comparing against the old number would have read four unexplained failures as its own regression, or deselected a moving target. Replaced with measured baselines plus a mandatory capture-before-you-change delta rule, recorded as F-7. PR-012 (HIGH): E-02 named no concrete narrow writer and omitted a silent-failure mode; added the verified entry point (merge_aw_block engine.py:1464, agents_managed_block :1405, parse_aw_block :1310, confirmed found/non-ambiguous single `pointer` section) and the manifest drift-preserve hazard that can DISCARD the edit while leaving a clean diff that mimics idempotency, with V-02 now demanding the returned action string. PR-013 (MEDIUM): E-03's no-dash assertion would have been a trap if written naively, since the shipped contract text already contains an ASCII hyphen at engine.py:1176; pinned it to the unicode chars and to a scoped section, per the precedent's actual code. PR-014 (MEDIUM): recorded F-9, the 5-8x vs 4-6x split between CONTRIBUTING.md:111 and this plan, and constrained E-01 to state a range so no future editor reconciles them by invention. PR-015 (LOW): added F-8 confirming `make test` (Makefile:24-25) really is bare-equivalent. PR-016 (LOW): added OQ-02 resolving that forbidding -p no:randomly stays correct on a clean install where the plugin is absent. Also verified the leak the earlier scan reported at :172 is now clean. aw ipd lint conforming at author and review-finalize; E/V bijection 4/4.
- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from an observed live failure during the `0soncw` review run (pid 4178108), measured on this checkout.

## Goal

Give agents one unambiguous instruction for running this repo's suite, in the always-loaded contract
where they will actually see it, so no agent again disables the repo's configured parallelism or
burns minutes fighting a verbosity flag it set itself.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: state the invocation rule where agents read it

- [ ] E-01 Add a test-invocation sentence to the agent execution contract string in
      `agent_workflows/engine.py` (the `"### Agent execution contract"` block; the pasted-output
      clause is at `engine.py:1174`). It must state: run the suite with a BARE `python3 -m pytest`
      (or `make test`), because `pyproject.toml` `addopts` already supplies `-q -n auto
      --dist=worksteal -m 'not slow'`; do NOT pass `-n0` (it disables xdist and is measurably 4-6x
      slower here); do NOT add another `-q` (it compounds with the configured one to `-qq`, which
      suppresses the very `N passed` summary line the contract demands you paste); and do NOT pass
      `-p no:randomly` (per OQ-01 it is NOT a no-op here: the plugin is installed and randomization is
      live, so the flag hides order-dependence bugs). Name the escape hatch for when the counts are
      needed from a narrowed run: `python3 -m pytest -o addopts=""`.

      WORDING CONSTRAINT (per F-9): express the `-n0` penalty as a RANGE or as "several times slower,
      depending on core count and load", not as one authoritative constant. `CONTRIBUTING.md:111`
      already tells humans "roughly 5-8x" for a different scope, and two hard numbers in two contracts
      invite a future editor to "reconcile" them by inventing a figure neither measured. Also keep the
      new text free of em/en dashes, since E-03 asserts that; the ASCII hyphen is fine and is already
      used in the surrounding contract text.
  - Depends on: none
  - Expected outcome: the generator emits the rule; no other contract wording changes; the penalty is
    stated as a range rather than a single constant.
  - Execution state: pending

- [ ] E-02 Regenerate ONLY the managed `aw:block` region of `AGENTS.md` from the generator (NOT by
      hand-editing between the `<!-- aw:block -->` / `<!-- /aw:block -->` markers at `AGENTS.md:3`
      and `AGENTS.md:60`), so the tracked file and the generator stay byte-consistent.
      CONSTRAINT: do NOT run a full `aw install .` to achieve this. Verified by `aw install . --dry-run`,
      that command's declared Target Delta is `.aw/system/, .aw/config/project.json, .aw/state/durable
      created/updated`, which is far wider than this plan's Scope-Paths and would mutate shared state
      while the wtiso Set holds `.aw/worktrees/` lanes and other runs are active. Call the narrow
      block-writing function directly (the `aw:block` writer in `engine.py`), or run the installer
      against a scratch target and transplant only the AGENTS.md block region. If neither is possible
      without a wider write, STOP and report rather than widening scope.

      CONCRETE ENTRY POINT (verified in review, so this is not left as an exercise): the narrow writer
      is `engine.merge_aw_block(existing, sections, ...)` at `engine.py:1464`, which returns
      `(new_text, action)` and preserves foreign text before and after the block; the section list comes
      from `engine.agents_managed_block(...)` at `engine.py:1405`, and `engine.parse_aw_block` at
      `engine.py:1310` reads the current on-disk sections. Confirmed on this tree that
      `parse_aw_block(AGENTS.md)` returns `found=True, ambiguous=False` with exactly one section, slug
      `pointer`, so the well-formed `refreshed` path applies and no legacy conversion or
      append-on-malformed branch is in play.

      MANIFEST HAZARD to check, do not assume: `merge_aw_block` applies per-section consent through
      `_apply_section_consent` (`engine.py`), which PRESERVES the on-disk body instead of writing ours
      when the manifest has a recorded hash for the section that does not match what is on disk (the
      "user drift" rule). If that fires, your edit is silently DISCARDED and AGENTS.md looks
      untouched, which would read as "idempotent" rather than "failed". Verified in review that
      `.aw/system/managed-sections.json` tracks the key `AGENTS.md#aw:pointer` but that
      `recorded_hash` for the parsed section currently returns NONE, so the desired version WOULD be
      written today. Re-confirm this before concluding your regeneration worked, and if the section
      body is unchanged after the call, treat it as a FAILURE to investigate, not a success.
  - Depends on: E-01
  - Expected outcome: AGENTS.md contains the new sentence inside the managed block; `git status` shows
    AGENTS.md as the ONLY changed file from this step; re-running the regeneration is idempotent; and
    the change is confirmed to have actually been written rather than drift-preserved away.
  - Execution state: pending

### Task group 2: prove the guidance is present and honest

- [ ] E-03 Add `tests/test_agent_contract_test_invocation.py` asserting the rule reached AGENTS.md,
      following the established pattern in `tests/test_backlog_graduated.py:221-236`
      (`test_agents_md_documents_the_contract` plus `test_agents_md_contract_has_no_em_or_en_dash`):
      assert the required phrases are present, and assert the section carries no em/en dash, since this
      is authored user-facing prose.

      Two precision notes from review, both taken from the precedent's actual code. First, the dash
      assertion must test for the UNICODE characters `\u2014` (em) and `\u2013` (en) ONLY, exactly as
      the precedent does; it must NOT reject the ASCII hyphen-minus, because the existing contract
      string legitimately uses one as a clause separator (`engine.py:1176`: "end users) - this keeps
      user-facing text..."), and a naive "no dashes" check would fail on shipped, correct text.
      Second, scope the assertion to the contract SECTION (the precedent slices from a heading offset
      with a fixed length) rather than the whole file, so an unrelated dash elsewhere in AGENTS.md
      cannot fail this test. Assert against the phrases as they appear in the RENDERED AGENTS.md, since
      that is what an agent actually loads.
  - Depends on: E-02
  - Expected outcome: the test passes, fails if the guidance is removed from the generator, and does
    NOT fail on the pre-existing ASCII hyphen already present in the contract text.
  - Execution state: pending

- [ ] E-04 Add to the same test a CONSISTENCY assertion that the guidance still matches reality:
      parse the `addopts` value out of `pyproject.toml` and assert it contains `-n auto`, so that if
      someone later changes the repo default (e.g. to serial), this test fails loudly rather than
      leaving AGENTS.md instructing agents to rely on a default that no longer exists.
  - Depends on: E-03
  - Expected outcome: the doc and the config cannot silently diverge.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The AGENTS.md guidance block is MACHINE-MANAGED. `agent_workflows/engine.py` owns the region
  between `<!-- aw:block -->` and `<!-- /aw:block -->` (`AGENTS.md:3`/`AGENTS.md:60`;
  `engine.py:219-220` define the markers). Editing AGENTS.md directly would be overwritten on the
  next install, so the fix MUST land in the generator.
- The existing precedent for "assert generator wording reached AGENTS.md" is
  `tests/test_backlog_graduated.py:221-236`, which also enforces the no-em-dash rule on the authored
  section. This plan mirrors that shape rather than inventing a new one.
- `pyproject.toml:118-121` already documents the parallel-by-default intent and the `make
  test-serial` debugging escape, but those comments sit in a file an agent has no reason to open. The
  gap is placement, not absence of intent.
- `CONTRIBUTING.md:111` documents `make test` / `-n auto` for humans; the always-loaded agent
  contract says nothing, which is why the agent improvised.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The repo configures parallel-by-default. | `pyproject.toml:122`: `addopts = "-q -n auto --dist=worksteal -m 'not slow'"` |
| F-2 | `-n0` is several times slower here. The RATIO is the durable claim; the absolute seconds are NOT, because they move with machine load. Two independent measurement pairs on 12 cores (`nproc`): idle-ish, `-n auto` `26.75 s` vs `-n0` `147.73 s` (5.5x); under concurrent-agent load (`load average: 34.25`), `-n auto` `50.65 s` vs `-n0` `222.60 s` (4.4x). | Both pairs measured on this checkout; do NOT cite a single absolute figure as stable |
| F-3 | A second `-q` suppresses the summary the contract requires. | `pytest -p no:randomly -n0 --tb=no -q -rN tests/test_backlog.py` prints only `......` with no `22 passed` line; the same run with `-o addopts=""` prints `22 passed in 0.23s` |
| F-4 | The observed loop cost real time and money. | `0soncw` review (pid 4178108) ran the serial suite at least 4 times across ~19 minutes of stall gaps, reaching `$15.19` cumulative |
| F-5 | The agent diagnosed the cause and still did not fix its own flag. | Its narration: "The `-q` config suppresses the count line", after which it escalated to `-rN`, then `-v | grep -c`, then a report hook, each at full serial cost |
| F-6 | The contract demands pasted output but never says how to obtain it. | `engine.py:1174` requires "paste the ACTUAL runner output"; no sibling clause names the invocation |
| F-7 | The pre-existing failure set is NOT the "two tests owned by `i79rgh`" this plan assumed, so the stated baseline could not be met as written. Measured: 1 failure in the fast subset (`1 failed, 2875 passed`), 6 in the full suite. Four are CLI-surface failures from concurrent `run_cli` work that the baseline never mentioned, and one of `i79rgh`'s two is FLAKY rather than deterministic. | `python3 -m pytest --no-header --tb=no -rN`; `python3 -m pytest -m "" -n auto`; `test_todo_matches_attention` failed 1 of 5 consecutive isolated runs then passed 3 file-level runs |
| F-8 | `make test` is genuinely equivalent to a bare invocation, so E-01 naming both is safe. | `Makefile:24-25`: `test:` runs `python3 -m pytest tests/`, inheriting `addopts` |
| F-9 | `CONTRIBUTING.md:111` tells HUMANS parallel "cuts wall time roughly 5-8x" while this plan tells AGENTS 4-6x, both about the same suite on the same 12-core machine. Not a defect in either (they measure different scopes and loads), but two different ratios in two contracts invite a future editor to "correct" one to the other. | `CONTRIBUTING.md:111` vs this plan's F-2 |

## Proposed changes (ordered, validatable)

1. Add the invocation rule to the generator's execution-contract string (E-01).
2. Regenerate the managed AGENTS.md block through the installer path (E-02).
3. Assert the guidance landed, with the no-dash rule, per existing precedent (E-03).
4. Assert the guidance cannot drift from `addopts` (E-04).

## Deferred / out of scope (with reason)

- **Changing `addopts` or the parallel default.** Out of scope: the configuration is correct; the
  defect is that agents were not told about it. Touching it would invalidate F-2's measurement.
- **Making the runner reject `-n0` in agent-issued commands.** Deferred: a tool-policy denylist on
  test flags is a runner change in `oc_runipd.py`/`agy_runipd.py`, which the wtiso Set is actively
  rewriting; adding to that surface now would collide. Guidance first, enforcement later if the
  behavior recurs after this lands.
- **The two live-state test failures.** Handled by sibling plan `i79rgh` (Order 02), because they are
  a different defect: those tests are wrong, whereas this plan's subject is agent guidance. They are
  what made the loop terminal (the suite could never come back green), but fixing them does not fix
  the invocation problem and vice versa.
- **A `make test-agent` convenience target.** Deferred: one more spelling to remember is a weaker fix
  than making the bare, obvious command correct.

## Scope check

- Over-scope: none. Three files, one of which is generated and one of which is new.
- Under-scope: this plan is guidance only. It does not PREVENT an agent from passing `-n0`; a
  determined or careless agent can still do it. That enforcement is deliberately deferred above, and
  the honest claim here is "the rule is now stated where agents load it", not "the failure mode is
  impossible".
- Under-scope closed in second review: the plan's VALIDATION baseline was wrong in a way that could
  have produced a false "executed" claim (F-7). It is now a measured range plus a mandatory
  capture-before-you-change rule, rather than a single expected number.
- Deliberately NOT fixed here, though encountered while validating: the four CLI-surface failures
  (`test_command_surface_declarations`, `test_cli` subparser descriptions, `test_cli_conformance_matrix`
  x2) belong to concurrent `run_cli` work, and the two live-state tests belong to `i79rgh`. Six
  pre-existing failures, zero of them this plan's to fix. Touching any of them would be over-scope and
  would also make this plan's own delta unreadable.

## Required tests / validation

1. `python3 -m pytest tests/test_agent_contract_test_invocation.py` green (run BARE, per the very
   rule being added).
2. Full default suite, counts pasted. Do NOT expect a green run and do NOT use a single expected
   number: the pre-existing failure set here is NOT a fixed pair, and an executor that treats it as one
   will either chase a phantom regression or paper over a real one.

   MEASURED BASELINE, re-established in a second review pass on the current tree (paste your own):
   - BARE `python3 -m pytest` (fast subset, `-m 'not slow'`): `1 failed, 2875 passed, 3 skipped, 4
     xfailed in 34.00s`. The one failure is `tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_issues_flag`.
   - `python3 -m pytest -m "" -n auto` (full): `6 failed, 3201 passed, 3 skipped, 4 xfailed`. The six
     are the above, plus `test_awcmdsurf_merge_and_renames.py::MergeAndRenamesTests::test_todo_matches_attention`,
     `test_command_surface_declarations::test_zero_undeclared_parser_leaves`,
     `test_cli::SubcommandDescriptionTests::test_every_subparser_has_fuller_description`, and
     `test_cli_conformance_matrix::UndeclaredLeafGuardTests` x2.
   - The earlier claim of a baseline "`2874 passed`, excluding the two failures owned by `i79rgh`" does
     NOT hold and was corrected here. Two reasons, both measured: (a) the passed count is 2875 in the
     fast subset, and the fast subset shows only ONE of `i79rgh`'s two tests, because
     `test_todo_matches_attention` is FLAKY, not deterministically failing (observed 1 failure in 5
     consecutive isolated runs, then 3 clean file-level runs), so "deselect exactly them" silently
     changes meaning between runs; (b) four MORE pre-existing failures exist in the full suite that the
     baseline never mentioned, so an executor comparing against "2874 + two known" would read four
     unexplained failures as caused by this plan.
   - RULE for the executor: capture the failure set BEFORE making any change, paste it, then compare
     after. Judge by DELTA against your own pre-change capture, never against a number written in this
     plan. Attribute `test_run_viewer_cli_issues_flag` and `test_todo_matches_attention` to `i79rgh`
     and the four CLI-surface failures to concurrent `run_cli` work. Do not fix any of the six here.
     If your pre-change capture disagrees with the numbers above, YOUR measurement wins; say so.
3. Generator idempotency demonstrated: run the install/regeneration twice and show the second run
   produces no diff to AGENTS.md.
4. An adversarial check that the new test actually fires: remove the guidance sentence from
   `engine.py`, regenerate, and show the test FAILS; then restore and show it passes.

## Spec / documentation sync

- `CONTRIBUTING.md:111` already documents `make test` and `-n auto` for humans and needs no change;
  this plan adds the agent-facing equivalent. If E-04 is implemented, `pyproject.toml:118-121`'s
  comment block becomes the tested source of truth for the default and needs no edit either.
- No spec governs the agent contract text; `engine.py` is the source of truth.
- Per F-9, the human-facing `CONTRIBUTING.md:111` says "roughly 5-8x" and this plan's agent-facing text
  says "4-6x". Both are honest for what they measured, and neither is edited here. The E-01 wording
  should therefore avoid implying a single authoritative constant: state that serial is MULTIPLE TIMES
  slower and that the ratio depends on core count and machine load, so the two documents cannot be read
  as contradicting each other and no future editor "reconciles" them by inventing a number.

## Open questions

### OQ-01: Should the rule also forbid `-p no:randomly`, which the observed run also passed?

- Blocking: no
- Status: resolved
- Owner: resolved from repository evidence during /plan-review
- Resolution or deferral rationale: RESOLVED - YES, the rule should cover it, and the reasoning in the
  authored draft was WRONG. That draft claimed `-p no:randomly` was "a no-op" because `pytest-randomly`
  is not a declared test dep (correct: it is absent from `pyproject.toml`). But the flag is not a no-op,
  because the plugin IS installed in the active environment (verify with
  `python3 -c "import pytest_randomly; print(pytest_randomly.__file__)"`, which resolves inside the
  active virtualenv's `site-packages`) and
  randomization is demonstrably live: `python3 -m pytest -o addopts="" tests/test_backlog.py` prints
  `Using --randomly-seed=154451933`. So `-p no:randomly` DISABLES real test-order randomization, which
  is precisely the mechanism that surfaces order-dependence bugs. An agent passing it is silently
  weakening the suite, not making a harmless tidy-up. E-01 must therefore name `-p no:randomly`
  alongside `-n0` as a flag not to pass. Note the secondary finding for the maintainer: the plugin is
  installed but UNDECLARED, so suite behavior differs between this venv and a clean
  `pip install '.[test]'`; that declaration gap is out of scope here and left for a separate item.

### OQ-02: Does forbidding `-p no:randomly` create a contradiction on a clean install, where the plugin is absent?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO CONTRADICTION, and the wording already in E-01 is safe as long as
  it forbids PASSING the flag rather than asserting the plugin is present. Verified in review:
  `pytest-randomly` is importable in the active environment but is NOT declared in `pyproject.toml`
  (`test = ["pytest>=8", "pytest-xdist>=3"]` at `:38`, `dev` likewise at `:44`), and randomization is
  live here (`python3 -m pytest -o addopts="" tests/test_backlog.py` prints `Using
  --randomly-seed=909395090`, a DIFFERENT seed from the one recorded in OQ-01, which independently
  confirms the seed is random per run rather than pinned). On a clean `pip install '.[test]'` the plugin
  is simply absent, `-p no:randomly` would then be a genuine no-op, and an instruction not to pass it
  costs nothing and stays correct. So the rule is environment-independent and needs no conditional
  phrasing. The declaration gap itself (behavior differing between this venv and a clean install) remains
  out of scope per OQ-01 and is the maintainer's to file.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n` of the new sentence in `agent_workflows/engine.py` showing it
    inside the `### Agent execution contract` string, plus a `git diff` of that hunk proving no other
    contract wording changed. The pasted text MUST name all three forbidden flags (`-n0`, a second
    `-q`, `-p no:randomly`) and the `-o addopts=""` escape hatch; a sentence missing any of them does
    not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new sentence as it appears in `AGENTS.md` BETWEEN the `aw:block`
    markers, and paste the output of running the regeneration twice, showing `git diff AGENTS.md` is
    empty on the second run (idempotency). Confirm no hand-edit occurred by showing the generator
    alone produces the file content. SCOPE PROOF (required): paste `git status --short` immediately
    after the regeneration, showing AGENTS.md as the only path this step changed and specifically that
    `.aw/system/`, `.aw/config/project.json` and `.aw/state/durable` were NOT written; if any of those
    appear, the step used a too-wide installer path and must be redone.
    WRITE-ACTUALLY-HAPPENED PROOF (required, because the drift-preserve rule can silently discard the
    edit and leave a clean diff that mimics idempotency): paste the `action` string returned by
    `merge_aw_block` (expect `refreshed`), AND paste the new sentence grepped out of AGENTS.md AFTER the
    call. An empty first-run diff is a FAILURE for this item, not a pass.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_agent_contract_test_invocation.py` green,
    AND the adversarial run: with the sentence deleted from `engine.py` and AGENTS.md regenerated,
    paste the FAILING output; then paste it passing again after restore. A guard never observed
    failing is not accepted as evidence. Additionally paste evidence that the dash assertion is
    correctly scoped: show it PASSING while the pre-existing ASCII hyphen at `engine.py:1176` ("end
    users) - this keeps...") is present in the rendered section, proving the check targets `\u2014`
    and `\u2013` only and does not reject shipped correct text.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the test passing, then paste a run with `addopts` temporarily altered to
    drop `-n auto`, showing the consistency assertion FAILS and names the drift. Restore and show
    green. Also paste the parsed `addopts` value the test read, so the assertion is not vacuous.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` and requires explicit human approval before execution.

Execution contract: commit only the files changed for this plan, path-scoped
(`git commit -m msg -- <path>`), never `git add -A` and never push. Other agents and runs are ACTIVE
in this checkout (the wtiso Set holds `.aw/worktrees/` lanes and other review runs work in the main
tree; at second-review time uncommitted work by other parties was present across
`.aw/records/backlog/`, `.aw/records/plans/pending/`, and the research indexes), so verify the staged
set before every commit and never sweep in their uncommitted work. Run the suite BARE when validating
this plan, which is the rule it installs. When every `V-*` item carries pasted evidence and
`aw ipd lint --phase pre-transition` conforms, move this plan to `.aw/records/plans/executed/` via
`aw ipd finalize`.

FIRST ACTION, before editing anything: capture and paste the pre-change failure set for BOTH the fast
subset and the full suite. Per F-7 that set is neither stable nor limited to `i79rgh`'s two tests (one
of which is flaky), so a baseline written in a plan is not trustworthy and only a delta against your own
pre-change capture is. If you skip this, you cannot honestly attribute any failure you see later.

Honesty rule (hard MUST): paste the ACTUAL runner output including the summary line, obtained by the
BARE invocation this plan installs. Never claim a pass you did not run, and never present a deselected
run as if it were the full suite without saying which tests you deselected and why.
