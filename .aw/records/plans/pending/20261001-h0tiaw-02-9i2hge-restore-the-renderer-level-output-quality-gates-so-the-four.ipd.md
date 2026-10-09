# IPD: Restore the renderer-level output quality gates so the four reviewed goldens are asserted again

- Date: 2026-10-01
- Kind: child
- Concern: TWELVE REVIEWED GOLDEN FILES ARE COMMITTED AND NO TEST READS ANY OF THEM, AND ONE HAS ALREADY SILENTLY DRIFTED. `tests/fixtures/conformance_goldens/` holds 12 tracked `.golden` files (four fixtures across `agent`, `human` and `json` renders); measured in this lane at HEAD `b6792ad4a`, `rg '\.golden' --glob '!*.golden'` over the whole tree returns ZERO hits, so nothing consumes them. Their reader, `tests/test_cli_quality_gates.py`, was deleted by test-trimming commit `19313eed7`, taking SEVEN gates with it: agent-record schema validity, ANSI stream posture, deterministic byte goldens, ASCII accessibility fallback, stream truncation accounting, human-versus-agent fact parity, and a per-record byte and token budget. Re-rendering the four fixtures today, eleven goldens match byte for byte and `check_findings.human.golden` DOES NOT: it still carries `Fix: run 'aw rename plans a.md' or rename to match ...` where the live renderer now emits `Fix: a.md does not carry a clustered identity prefix; run 'aw rename plans a.md --to-id6 --apply' or rename to match ...`, and likewise lacks the `--rename --apply` the regroup hint now carries. That is a reviewed-bytes artifact that went stale with nothing to catch it, which makes this a LIVE if low-impact defect rather than the purely latent debt backlog `h0tiaw` filed it as. The tree even contains evidence of someone maintaining these files blind: commit `f8ff56ec1` (2026-10-01) hand-edited four `.human.golden` files to track a renderer change, with no test to confirm the edits were right. Separately, `CONTRIBUTING.md` step 6 promises a new-leaf author six live checks ("ANSI-free agent stream, exit-code parity, fact-parity, help, usage error, no-color") of which exactly one, exit-code parity, is executed today.
- Scope: IN: restore the seven renderer-level gates as a DEFAULT-COLLECTED module over the same four reviewed `CommandResult` fixtures, recovered from `git show 19313eed7^:tests/test_cli_quality_gates.py` rather than rewritten; give all twelve `.golden` files a reader; resolve the drifted `check_findings.human.golden` by regenerating it with the full diff quoted as evidence; and reconcile `CONTRIBUTING.md` step 6 against the enforced set this Set actually lands, promise by promise. OUT: the structural matrix gate, the exemption-registry cleanup and the `command_surface.py` comment reconciliation (sibling `dq9bj9`); the expensive live scenario sweep and the vacuous human-banner parity gate over live leaves (carrier `2wowfy`); any change to `agent_workflows/renderers.py`, `agent_workflows/result_types.py`, `agent_workflows/agent_schema.py` or `agent_workflows/term.py`, since every gate here measures GREEN against today's code and a production edit would mean the gate was authored to its own convenience.
- Scope-Paths: tests/test_cli_quality_gates.py, tests/fixtures/conformance_goldens/check_findings.human.golden, CONTRIBUTING.md
- Item-Dependencies: executed:dq9bj9
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: h0tiaw
- Set: h0tiaw
- Order: 2
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 9i2hge
- Approval: 2026-10-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004. Reviewed at HEAD 8fecdffcb. Recovered module re-run in-process with the update variable unset: 14 tests, exactly 1 failure (check_findings human golden), confirming E-01's prediction. E-06(c) reconciled with dq9bj9 F-08 (a third undeclared-leaf assertion is allowed if labelled a precondition); E-06(b) gains the internally-used category dq9bj9 E-03 keeps; E-06(a) scoped to tests/; gate gains honesty, scope-fence and finalize-ownership wording. Review record .aw/records/reviews/20261001-h0tiaw-02-9i2hge-restore-the-renderer-level-output-quality-gates-so-the-four.review.md.
- 2026-10-07 to-review (aw set): returned to review: Set-level checks now owned by 9i2hge E-06 (runs last) and the children's own V-items; coverage pass recorded
- 2026-10-06 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): added E-06/V-06, the three Set-level checks (no orphaned golden, no orphaned symbol, no tripled assertion) the orchestrator `l8wvv3` carried with no owner; this plan runs last, after `dq9bj9`, so it is the only child that can see both changes. Measurement only; no scope change.
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: No orphaned golden and no orphaned symbol, checked across both children together

- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `h0tiaw` as Order 02 of Set `h0tiaw` (orchestrator `l8wvv3`), which carries the Set-wide reasoning. Every claim was MEASURED in this lane at HEAD `b6792ad4a`. THIS CHILD IS WHERE THE ITEM'S FRAMING WAS MEASURED WRONG: it filed the concern as "latent coverage debt, not a live defect", and one golden has in fact already drifted, so a reviewed artifact is stale right now. The item's second open question ("whether the intended contract is still the one the helpers encode") is answered favorably for this half: all seven gates were driven in-process against today's code and ALL SEVEN PASS, in 0.790s total, so unlike sibling `dq9bj9` (which must widen a pin that went false) nothing here asserts an obsolete promise. The ONE exception is the drifted golden, and OQ-01 resolves its direction from evidence rather than defaulting: the live render is the correct one because the golden's suggested commands lack the `--apply` every mutating verb in this repository requires, so the golden is regenerated and not the code. `aw ipd lint --phase author` reports conforming.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give the twelve reviewed golden files a reader again, so a renderer change that alters published bytes fails a
default-collected test instead of being hand-patched by whoever notices, and leave `CONTRIBUTING.md` step 6
promising only the checks that are actually executed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: recover the driver and reproduce the drift

- [ ] E-01 RECOVER THE DELETED QUALITY-GATES MODULE AND RUN IT UNCHANGED, capturing a per-test-method result
  table before writing anything. Extract with `git show 19313eed7^:tests/test_cli_quality_gates.py`. The
  module defines four `CommandResult` fixtures (`read_clean`, `check_findings`, `mutation_preview`,
  `error_cannot_run`) and seven gate classes (`SchemaGateTests`, `AnsiStreamGateTests`,
  `DeterministicByteGoldenTests`, `AccessibilityGateTests`, `TruncationGateTests`, `FactParityGateTests`,
  `BudgetGateTests`).

  THE PREDICTION IS EXACTLY ONE FAILURE: `DeterministicByteGoldenTests::test_human_plain_goldens_stable` on
  the `check_findings` subtest, from the drifted golden. Every other method is predicted to pass. That
  prediction is falsifiable and this item exists to test it rather than to assume it.

  DO NOT RUN IT WITH `AW_CONFORMANCE_UPDATE_GOLDENS=1`. The module's `_read_or_write_golden` helper WRITES
  the golden when that variable is set OR when the file does not exist, so a careless first run silently
  overwrites the very drift this item is here to examine and the evidence is destroyed. Run it with the
  variable UNSET and confirm it is unset before running.

  NOTE THE MODULE HAS NO `slow` MARKER, unlike its sibling driver, which is consistent with the 0.790s
  measurement and means this half needs no marker decision.
  - Depends on: none
  - Expected outcome: a per-method result table with exactly one failure, the `check_findings.human` golden
    assertion, and its diff captured verbatim; plus an explicit statement that
    `AW_CONFORMANCE_UPDATE_GOLDENS` was unset during the run.
  - Execution state: pending

### Task group 2: resolve the one real defect

- [ ] E-02 REGENERATE `check_findings.human.golden` WITH THE FULL DIFF QUOTED, and justify the direction
  rather than defaulting to it. Measured at authoring, the golden differs from today's render on exactly two
  lines: the golden reads `Fix: run 'aw rename plans a.md' or rename to match
  'YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md'.` where the render reads `Fix: a.md does not carry a clustered
  identity prefix; run 'aw rename plans a.md --to-id6 --apply' or rename to match '...'.`, and the golden's
  regroup hint reads `run 'aw group plans b.md --set <new-set-id>' to regroup this record` where the render
  reads `run 'aw group plans b.md --set <new-set-id> --rename --apply' to regroup this record`.

  THE LIVE RENDER IS CORRECT AND THE GOLDEN IS STALE, which is why this is a fixture regeneration and not a
  renderer fix. Both of the render's additions make the suggested command actually DO something: every
  mutating verb in this repository previews by default and requires `--apply` to write (`aw ipd scaffold`,
  `aw backlog new` and `aw rename` all say so in their own `--help`), so the golden's commands would print a
  preview and exit, leaving the finding unfixed. State that reasoning in the evidence; do not regenerate on
  the premise that newer bytes are automatically right.

  REGENERATE BY WRITING THE REVIEWED BYTES, NOT BY SETTING THE ENVIRONMENT VARIABLE BLIND. `AW_CONFORMANCE_UPDATE_GOLDENS=1`
  is the module's documented regeneration path and may be used, but only AFTER the diff is captured and
  quoted, and the resulting `git diff` on the golden must be read line by line and included in the evidence.
  A golden regenerated without a reviewed diff is no longer a reviewed artifact, which would reproduce this
  item's root cause in a new form.

  CHANGE NO OTHER GOLDEN. The other eleven match byte for byte; if any now differs, that is a finding to
  report with its diff before proceeding, because it would mean something moved between authoring and
  execution.
  - Depends on: E-01
  - Expected outcome: `check_findings.human.golden` matching today's render, its two-line diff quoted in the
    evidence with the `--apply` reasoning stated, and `git status --short tests/fixtures/conformance_goldens/`
    showing exactly ONE modified file.
  - Execution state: pending

### Task group 3: land the gates, default-collected

- [ ] E-03 WRITE `tests/test_cli_quality_gates.py` CARRYING ALL SEVEN GATES, default-collected. Port from the
  recovered module. Each gate was driven at authoring and each is GREEN, with the measured value recorded
  here so execution compares against a number rather than a hope.

  THE SEVEN GATES AND THEIR MEASURED STATE. (1) SCHEMA: `validate_agent_record` returns `[]` for all four
  fixtures' agent records, and `AgentRenderer().render_summary("find", total=10, emitted=3, omitted=7, ...)`
  yields a valid record whose `emitted + omitted == total`. (2) ANSI: all four agent renders and all four JSON
  renders are ANSI-free; the human render carries ANSI with `color=True` and none with `color=False`.
  (3) GOLDENS: rendering twice is byte-identical and matches the committed file, for all twelve after E-02.
  (4) ACCESSIBILITY: `term.Term(color=False, unicode=False)` degrades `glyph("fail")`, `glyph("ok")` and
  `glyph("arrow")` to `FAIL`, `OK` and `->`, and the monochrome human render of `check_findings` contains both
  `FINDINGS` and `[ERROR]` so meaning never depends on color. (5) TRUNCATION: `render_stream` over 10 items
  with `limit=3` emits three `item` records plus a `summary` carrying `emitted=3, omitted=7, total=10,
  complete=False` and a `next`; unlimited yields `complete=True, omitted=0`. (6) PARITY: each fixture's agent
  record `findings` equals `len(result.diagnostics)`, its `next` equals the first `next_actions` command and
  that command appears verbatim in the human render, and its `target` round-trips. (7) BUDGET: the largest
  agent record is 341 bytes (`check_findings`) against the module's `BYTE_BUDGET = 1200` and
  `TOKEN_BUDGET = 400`, and `--fields findings` shrinks it from 341 to 130 bytes while retaining all seven
  envelope keys (`schema`, `kind`, `cmd`, `exit`, `outcome`, `verified`, `complete`).

  NOTE WHAT THE PARITY GATE HERE IS AND IS NOT. This is the RENDERER-level parity assertion, comparing a
  `CommandResult`'s agent record against its own human render, and it is NON-VACUOUS: driven on a synthesized
  `check_findings` render, `semantic_facts_from_human` correctly returns `{'outcome_family': 'findings'}`.
  That is categorically different from the LIVE-leaf parity gate carried by `2wowfy`, which is vacuous because
  no curated leaf emits the required banner. Say so in the module docstring so a later reader does not
  conclude the live gate was already restored.

  KEEP THE BUDGET NUMBERS AS CEILINGS, NOT AS PINS. `BYTE_BUDGET = 1200` against a measured 341 is a 3.5x
  ceiling that catches a record-bloat regression without failing on a one-field addition. Do NOT tighten it
  to the measured value: that converts a regression guard into a census pin, which `GUIDING_PRINCIPLES` 16
  prohibits and which would fail on any legitimate field.

  NO CODE-PINNING (`GUIDING_PRINCIPLES` 16). Every assertion renders a real `CommandResult` through a real
  renderer and asserts on the produced string or record. Do not read `agent_workflows/*.py` as text and do not
  assert that any docstring or comment exists. The goldens are the ONE legitimate content comparison here and
  they fall squarely inside P16's narrow exception ("Content verification is permissible only where the text
  or file itself is the artifact under test"): the golden IS the artifact under test, and it is fixture data,
  not production source.
  - Depends on: E-02
  - Expected outcome: a module COLLECTED AND PASSING under a bare `python3 -m pytest` with no `-m ''`, with
    all seven gates present, no `pytestmark = pytest.mark.slow`, and a docstring distinguishing its
    renderer-level parity gate from the deferred live-leaf one.
  - Execution state: pending

- [ ] E-04 PROVE THE GATES ARE SENSITIVE BY BREAKING WHAT THEY GUARD, with THROWAWAY probes reverted before
  any commit. A restored gate that passes proves nothing about whether it can fail
  (`GUIDING_PRINCIPLES` 16: "A test is only valid if breaking the underlying behavior makes the test fail").

  FOUR PROBES, EACH REVERTED, chosen to hit four DIFFERENT gates so a single over-broad assertion cannot pass
  all of them. (1) Alter one byte of a golden file and confirm the golden gate fails naming that fixture and
  render. (2) Inject an ANSI escape into a value that reaches an agent record and confirm either the ANSI gate
  fails or `validate_agent_record` rejects it, reporting WHICH (the schema validator has its own
  `_ANSI_ESCAPE_RE` rule, so the two gates overlap here and the evidence should say so rather than claim
  credit twice). (3) Break the truncation arithmetic (for example by making `render_stream` report `omitted`
  as zero under a limit) and confirm the truncation gate fails on `emitted + omitted == total`. (4) Inflate a
  record past the 1200-byte ceiling and confirm the budget gate fails.

  PASTE EACH FAILURE and then PASTE `git status --short` plus `git diff --stat` for `agent_workflows/` and
  `tests/fixtures/` showing no probe survived. A probe left in a golden is especially dangerous here, because
  it would be a committed wrong byte in a reviewed artifact.
  - Depends on: E-03
  - Expected outcome: four pasted failures each naming the specific broken property, and clean
    `git status`/`git diff --stat` output for both production code and fixtures.
  - Execution state: pending

### Task group 4: make the contributor promise true

- [ ] E-05 RECONCILE `CONTRIBUTING.md` STEP 6 AGAINST WHAT THE SET ACTUALLY ENFORCES, promise by promise. The
  step currently reads: "If the leaf is safe to run read-only in the repo, add it to `LIVE_SAFE_LEAVES` in
  `tests/conformance_matrix.py` so the harness exercises it live (ANSI-free agent stream, exit-code parity,
  fact-parity, help, usage error, no-color)."

  SIX PROMISES, AND AFTER THIS SET THE HONEST ANSWER IS STILL NOT SIX. Walk them individually. EXIT-CODE
  PARITY is executed, by `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership`,
  with the honest caveat that it is `slow` and therefore runs in CI only inside the step carrying
  `continue-on-error: true`. ANSI-FREE AGENT STREAM is executed at the RENDERER level by this plan and over
  42 live read/check leaves by `tests/test_agent_surface_conformance.py`, but NOT per-leaf across the
  `LIVE_SAFE_LEAVES` scenario grid. FACT-PARITY is executed at the renderer level by this plan and is NOT
  executed over live leaves (and would be vacuous if it were, which is why `2wowfy` carries it). HELP,
  USAGE ERROR and NO-COLOR are NOT executed per-leaf at all; the `--help` and usage-error FLOORS are asserted
  tree-wide in-process by `test_exit_contract_conformance.py`'s first two gates, which is a different and
  weaker claim than the per-leaf scenario the step promises.

  REWRITE THE STEP TO SAY WHAT IS TRUE AND NAME THE TEST FOR EACH CLAIM, so a contributor can verify the
  promise instead of trusting it, and point the unexecuted scenarios at carrier `2wowfy` rather than silently
  dropping them. DO NOT simply delete the step: adding a leaf to `LIVE_SAFE_LEAVES` still has real effect
  (it is what `test_exit_contract_conformance.py` iterates), so the instruction is right and only its promise
  is overstated.

  WRITE NO EM OR EN DASHES. `CONTRIBUTING.md` is user-facing prose under the execution contract, so use
  hyphens.
  - Depends on: E-04
  - Expected outcome: step 6 naming, for each check it claims, the test that executes it, with the
    unexecuted per-leaf scenarios attributed to `2wowfy` and the `slow`/CI-advisory caveat stated rather than
    hidden; no em or en dashes added.
  - Execution state: pending

### Task group 5: the Set-level checks this plan runs because it executes last

- [ ] E-06 RUN THE THREE SET-LEVEL CHECKS orchestrator `l8wvv3` assigns to this plan, because this plan executes after `dq9bj9` (its declared dependency) and is the only point at which both children's changes exist together. (a) NO ORPHANED GOLDEN: `rg '\.golden' --glob '!*.golden' tests/` returns at least one hit (scoped to `tests/` at review 2026-10-07, because a tree-wide search is now satisfied trivially by plan and review prose under `.aw/records/`), and every one of the twelve `.golden` files under `tests/fixtures/conformance_goldens/` is READ by a collected test, shown by mapping each file to the fixture name and render suffix the module iterates. (b) NO ORPHANED SYMBOL: for every public name defined in `tests/conformance_matrix.py` after `dq9bj9`'s edits, record exactly one of: imported by a test; used INTERNALLY by a name that is imported (the category `dq9bj9` E-03 deliberately keeps for `RunResult`, `Exemption` and `_pinned_env`, which have zero importers by design); or absent from the module. A name in none of those three is the orphan this check exists to catch. (c) NO SILENTLY TRIPLED ASSERTION: the zero-undeclared-leaves assertion is made by `test_command_surface_declarations.py::test_zero_undeclared_parser_leaves` and `test_model_vocab.py::test_10_zero_undeclared_leaves`. `dq9bj9` F-08 PERMITS `tests/test_conformance_matrix_structure.py` to make it a third time as the matrix's own precondition, provided the module SAYS so rather than presenting it as new coverage. Confirm either that it is absent there, or that it is present AND labelled as a precondition; and confirm each new module states what it adds. (Corrected at review 2026-10-07: the earlier wording required it to be absent, which contradicted the sibling plan's own permitted design.) This plan changes nothing for this item; it only measures. A failure is reported and the Set is not declared complete.
  - Depends on: E-05
  - Expected outcome: (a) at least one reader hit under `tests/` and all twelve goldens mapped to a reading test; (b) a per-name table where every name is imported, internally used by an imported name, or absent; (c) the third undeclared-leaf assertion either absent or explicitly labelled a precondition.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- NO CODE-PINNING TESTS (`GUIDING_PRINCIPLES` 16), with its ONE narrow exception squarely applicable here:
  "Content verification is permissible only where the text or file itself is the artifact under test." A
  golden fixture is exactly that. What remains forbidden is reading `agent_workflows/*.py` as text, pinning a
  docstring, or asserting a census; the budget ceilings are deliberately loose (3.5x the measured value) so
  they guard against regression rather than pinning a count.
- DEFAULT COLLECTION IS THE POINT. `pyproject.toml` `addopts` is
  `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'` and `.github/workflows/tests.yml` runs
  `python -m pytest tests/ -n auto -rfEs` with no `-m ''`, while the `-m slow` step carries
  `continue-on-error: true`. The recovered module has no marker and at 0.790s needs none.
- GOLDEN REGENERATION IS GUARDED BY AN ENVIRONMENT VARIABLE THAT ALSO FIRES ON A MISSING FILE. The recovered
  `_read_or_write_golden` writes when `AW_CONFORMANCE_UPDATE_GOLDENS == "1"` OR when the path does not exist,
  so a renamed or deleted golden is silently recreated from whatever the code currently emits. That is a real
  sharp edge: it means a golden can never go MISSING-red, only silently-regenerated. E-03 should consider
  whether to keep that fallback or require the file to exist, and must state its choice.
- THE BARE SUITE IS THE CONTRACT (`AGENTS.md`): `python3 -m pytest` with no added flags, and specifically not
  `-n0`, not a second `-q`, and not `-p no:randomly`.
- USER-FACING PROSE CARRIES NO EM OR EN DASHES. `CONTRIBUTING.md` is in scope and is user-facing; this plan
  itself is not.

## Findings

| id | finding | evidence |
| --- | --- | --- |
| F-01 | TWELVE GOLDENS ARE COMMITTED AND UNREAD. `git ls-files tests/fixtures/conformance_goldens/` returns 12 files (`check_findings`, `error_cannot_run`, `mutation_preview`, `read_clean`, each with `.agent`, `.human` and `.json` variants). `rg '\.golden' --glob '!*.golden'` across the whole tree returns ZERO hits, so no test, script, or doc references them. Their reader was `tests/test_cli_quality_gates.py`, deleted by `19313eed7`. | `git ls-files`; the `rg` sweep; `git show --stat 19313eed7` confirming the deletion. |
| F-02 | ONE GOLDEN HAS DRIFTED, WHICH IS THE LIVE DEFECT. Re-rendering all four fixtures through `AgentRenderer`, `HumanRenderer` and `JsonRenderer` with the same `OutputContext` values the deleted module used: eleven of twelve match byte for byte; `check_findings.human.golden` differs on two `Fix:` lines. Golden: `Fix: run 'aw rename plans a.md' or rename to match 'YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md'.` and `run 'aw group plans b.md --set <new-set-id>' to regroup this record`. Render: `Fix: a.md does not carry a clustered identity prefix; run 'aw rename plans a.md --to-id6 --apply' or rename to match '...'.` and `run 'aw group plans b.md --set <new-set-id> --rename --apply' to regroup this record`. So the committed bytes advertise two commands that would preview and exit rather than fix. | All twelve re-rendered and diffed in-process at HEAD `b6792ad4a`; the unified diff of the differing file captured. |
| F-03 | ALL SEVEN GATES PASS AGAINST TODAY'S CODE, so nothing here asserts an obsolete promise. Driven in-process: `validate_agent_record` returns `[]` for all four fixtures; all four agent and JSON renders are ANSI-free while the human render carries ANSI only with `color=True`; `FINDINGS` and `[ERROR]` both appear in the monochrome render; `Term(color=False, unicode=False)` yields `FAIL`/`OK`/`->`; `render_stream` with `limit=3` over 10 items reports `{'emitted': 3, 'omitted': 7, 'total': 10, 'complete': False}` plus a `next`; `render_summary` with `total=10, emitted=3, omitted=7` validates and sums correctly; `--fields findings` shrinks `check_findings` from 341 to 130 bytes retaining all seven envelope keys; the largest record is 341 bytes against a 1200-byte and 400-token budget. Total runtime for the whole gate shape: 0.790s. | Each gate driven and its value printed; the shape timed end to end. |
| F-04 | SOMEONE IS ALREADY MAINTAINING THESE FILES BLIND. Commit `f8ff56ec1` (2026-10-01, `work(zosxj4)`) modified four files under `tests/fixtures/conformance_goldens/`, all `.human.golden`, one line each, alongside an edit to `agent_workflows/renderers.py` and a new `tests/test_human_renderer_agent_hint.py`. So a run correctly noticed that a renderer change altered the published human bytes and updated the goldens by hand, with no test to confirm the updates were right. Giving the files a reader is what makes that maintenance verifiable rather than diligent-but-unchecked. | `git log -1 --stat` on the fixture directory; the commit's full stat read. |
| F-05 | THE `CONTRIBUTING.md` PROMISE IS ONE-SIXTH TRUE, AND WILL NOT BE SIX-SIXTHS AFTER THIS SET. Step 6 names six live checks. Executed today: exit-code parity only, via `tests/test_exit_contract_conformance.py::test_live_safe_leaves_exit_contract_membership`, which is itself `@pytest.mark.slow` and so runs in CI only in the step carrying `continue-on-error: true`. Not executed per-leaf: help, usage error, no-color (their tree-wide in-process FLOORS are asserted by the same module's first two gates, a weaker and different claim), and ANSI-free agent stream and fact-parity per-leaf. After this Set, renderer-level ANSI and parity ARE enforced and the per-leaf scenario grid still is not, so E-05's rewrite must be honest rather than triumphant. | `CONTRIBUTING.md` step 6 read; `tests/test_exit_contract_conformance.py` read including its three gates and its markers. |
| F-06 | THE GOLDEN HELPER CANNOT FAIL ON A MISSING FILE, which is a second sharp edge in the same mechanism. `_read_or_write_golden` writes the golden when `AW_CONFORMANCE_UPDATE_GOLDENS == "1"` OR when `not path.exists()`, then returns the value it just wrote, so the subsequent `assertEqual` compares the render against itself. A golden that is deleted, renamed, or never created therefore passes silently and is recreated from current behavior. This is worth a decision rather than a faithful port, which is why E-03 must state whether it keeps the fallback. | `_read_or_write_golden` read in the recovered module. |
| F-07 | THE RENDERER-LEVEL PARITY GATE IS NON-VACUOUS, UNLIKE ITS LIVE-LEAF COUSIN, and the distinction must be documented or it will be misread. `FactParityGateTests` compares a fixture's agent record against its own human render and asserts `findings` count parity, `next` command parity (the command string must appear in the human text) and `target` parity; all three are real comparisons that pass today. The LIVE-leaf gate deferred to `2wowfy` is vacuous because `semantic_facts_from_human` requires an `AW <command>` banner that none of the 16 curated leaves emits. Driven directly on this plan's `check_findings` render, that same helper correctly returns `{'outcome_family': 'findings'}`, which confirms the helper works and only the curated leaf set fails to reach it. | The parity assertions driven per fixture; `semantic_facts_from_human` driven on the synthesized render. |
| F-08 | NO SPEC GOVERNS THIS HARNESS AND NO PRODUCTION EDIT IS NEEDED. `rg` over `.aw/records/specs/` for `conformance_matrix`, `EXEMPTION_REGISTRY`, `LIVE_SAFE_LEAVES` and `conformance_goldens` returns nothing. The contract measured is `docs/cli-output-contract.md`, a normative document and not a spec record, and since every gate passes (F-03), the plan declares no file under `agent_workflows/` in its scope: a gate authored alongside a change to the code it measures is a gate authored to its own convenience. | The specs `rg` sweep; F-03's green measurements. |
| F-09 | THIS CHILD DEPENDS ON `dq9bj9` FOR ONE MECHANICAL REASON. The recovered module imports `ANSI_RE` and `GOLDEN_DIR` from `tests.conformance_matrix`, and sibling `dq9bj9` resolves that module's zero-importer symbols to keep-or-delete. `GOLDEN_DIR` has zero importers TODAY precisely because this module was deleted, so if `dq9bj9` ran second it could delete a symbol this child needs; running it FIRST means its per-symbol verdict is made with this child's requirement already visible, and `dq9bj9`'s own E-03 explicitly names `GOLDEN_DIR` as kept for that reason. | `dq9bj9`'s E-03 text read; the recovered module's import list read. |

## Proposed changes (ordered, validatable)

1. E-01 recovers the deleted quality-gates module from `19313eed7^`, runs it with
   `AW_CONFORMANCE_UPDATE_GOLDENS` unset, and captures a per-method table confirming exactly one failure.
2. E-02 regenerates the drifted `check_findings.human.golden` with its two-line diff quoted and the `--apply`
   reasoning stated, changing no other golden.
3. E-03 writes `tests/test_cli_quality_gates.py` with all seven gates, default-collected, loose budget
   ceilings, a documented distinction between renderer-level and live-leaf parity, and a stated decision on
   the missing-file regeneration fallback.
4. E-04 proves four different gates can fail, with four reverted throwaway probes and their failures pasted.
5. E-05 rewrites `CONTRIBUTING.md` step 6 to name the test behind each promise, attribute the unexecuted
   per-leaf scenarios to `2wowfy`, and state the `slow`/CI-advisory caveat.

## Deferred / out of scope (with reason)

- THE STRUCTURAL MATRIX GATE, the exemption-registry cleanup, and the `agent_workflows/command_surface.py`
  comment reconciliation. Sibling child, and this plan's declared dependency (F-09).
  - Carrier: dq9bj9
  - Carrier-Evidence: .aw/records/plans/executed/20261001-h0tiaw-01-dq9bj9-revive-the-dormant-conformance-matrix-as-a-live-structural-g.ipd.md
- THE PER-LEAF LIVE SCENARIO GRID (`--help`, usage error, `--no-color`, ANSI per leaf) and the LIVE-leaf
  fact-parity gate. The first costs minutes and could only land `slow`, hence CI-advisory; the second is
  vacuous on all 16 curated leaves. E-05 attributes the remaining gaps in `CONTRIBUTING.md` to this carrier
  by name rather than dropping them from the prose.
  - Carrier: 2wowfy
- ANY EDIT TO `agent_workflows/renderers.py`, `result_types.py`, `agent_schema.py` OR `term.py`. All seven
  gates pass against today's code (F-03), so there is nothing to fix, and declaring a production path here
  would permit authoring the gate and the behavior it measures in one unreviewable change.
  - Carrier-Declined: nothing is deferred. This row records production paths the plan deliberately leaves
    alone and whose current behavior V-03 PROVES conformant, so there is no outstanding obligation to hand
    off. If execution finds a gate red against today's code, that is a scope-widening finding to record and
    reconcile at finalize, not a silent production edit.
- AUDITING WHETHER `f8ff56ec1`'s FOUR HAND-EDITED GOLDENS WERE EACH CORRECT (F-04). Giving the files a reader
  subsumes the audit: once E-03 lands, every golden is asserted against the live render on every default
  suite run, so a wrong byte surfaces as a failure instead of as silent fiction.
  - Carrier-Declined: a separate audit would re-derive by hand exactly what E-03's gate derives mechanically
    on every run, and would produce no artifact the test does not. V-01's per-method table is the audit, run
    once, and V-03's passing gate is the audit, run forever.
- THE MISSING-FILE REGENERATION FALLBACK (F-06) IF E-03 CHOOSES TO KEEP IT. If E-03 requires the file to
  exist, the hole is closed and nothing is deferred; if it keeps the fallback, the residual risk is that a
  DELETED golden passes silently.
  - Carrier-Declined: under either branch the decision is recorded in E-03's evidence and is a one-line
    property of a test file this plan owns, so there is no work for a separate item to perform. Filing a
    carrier to re-decide a choice this plan explicitly makes and documents would be records churn.

## Scope check

- Over-scope: none. `tests/test_cli_quality_gates.py` is the new module from E-03.
  `tests/fixtures/conformance_goldens/check_findings.human.golden` is the single drifted file from E-02; the
  other eleven goldens are deliberately NOT in scope because they match byte for byte, and if any turns out
  not to, that is a finding to record and reconcile at finalize rather than a silent addition.
  `CONTRIBUTING.md` carries E-05's step 6 rewrite. Deliberately NOT touched: `tests/conformance_matrix.py`
  (this child only IMPORTS `ANSI_RE` and `GOLDEN_DIR` from it; sibling `dq9bj9` owns its content, which is
  what the dependency edge enforces), every module under `agent_workflows/` (F-03, F-08), and
  `docs/cli-output-contract.md` (normative but satisfied, so unchanged). No `.spec.md` file is declared, so a
  run must announce no declared spec edits and none may be made.
- Under-scope: the risk is that between authoring and execution a renderer change lands in a concurrent lane
  and a SECOND golden drifts, making E-01's single-failure prediction wrong. The response is to report the
  additional diff as a finding, apply the same OQ-01 test to it (does the live render make the suggested
  action actually work, and is it consistent with the documented behavior?), and widen scope to that golden
  explicitly at finalize rather than regenerating it silently as part of E-02. A SECOND, smaller risk: E-05's
  rewrite depends on what sibling `dq9bj9` actually enforced, so if that child took OQ-01 branch A and
  deleted the parity helpers, E-05 must describe the enforced set as it is, not as this plan predicted.

## Required tests / validation

- THE NEW MODULE `tests/test_cli_quality_gates.py`, COLLECTED AND PASSING under a bare `python3 -m pytest`
  with no `-m ''` override, carrying all seven gates: schema validity for every fixture record plus the
  summary-count consistency check; ANSI-free agent and JSON streams with human color opt-in; deterministic
  and golden-matching bytes for all twelve files; ASCII glyph degradation and the color-independent status
  words; truncation arithmetic (`emitted + omitted == total`, `complete=False` under a limit and `True`
  without); renderer-level fact parity on findings count, next command and target; and the byte/token budget
  with the `--fields` projection shrinking the record while retaining every envelope key.
- THE SENSITIVITY PROBES of E-04: four throwaway breakages across four DIFFERENT gates (golden byte, ANSI
  injection, truncation arithmetic, budget inflation), each producing a named failure, each reverted, with
  `git status --short` and `git diff --stat` proving no probe survived in production code OR in a fixture.
- THE REGENERATED GOLDEN: `git diff` on `check_findings.human.golden` read line by line, with the two `Fix:`
  lines quoted, and `git status --short tests/fixtures/conformance_goldens/` showing exactly one modified
  file.
- `tests/test_human_renderer_agent_hint.py` unchanged and passing, since it is the module `f8ff56ec1` added
  alongside the hand-edited goldens and so is the one existing test adjacent to this fixture set.
- THE BARE FULL SUITE: `python3 -m pytest` with no added flags, at the base commit and again at the end, with
  the delta stated as a SET of test ids and required to be EMPTY. An environmental failure present before the
  change is not this plan's to fix; one present only after is a regression and blocks the transition.
- `aw ipd lint` conforming at `--phase author` before review and at `--phase pre-transition` before the
  terminal move, plus `aw check` reporting no new drift.

## Spec / documentation sync

No spec amendment, and no `.spec.md` path is declared in `- Scope-Paths:`, so a run executing this plan must
announce no declared spec edits and none may be made. Checked rather than assumed (F-08): `rg` over
`.aw/records/specs/` for `conformance_matrix`, `EXEMPTION_REGISTRY`, `LIVE_SAFE_LEAVES` and
`conformance_goldens` returns no hits. The contract these gates MEASURE is `docs/cli-output-contract.md`
(Section 4's ANSI rule, Section 10's single-canonical-format ruling, Section 11's state conventions), which is
a normative document rather than a spec record; it is NOT edited, because every gate passes against today's
code (F-03), so the document and the behavior already agree and the only thing missing was the test.

One documentation change is in scope and it is the point of E-05. `CONTRIBUTING.md` step 6 promises six live
checks and delivers one (F-05), which is a false instruction to every future leaf author, and it stays
partly false even after this Set lands, because the per-leaf scenario grid remains with carrier `2wowfy`. The
rewrite therefore names the executing test for each claim it keeps, attributes the rest to `2wowfy`, and
states the honest caveat that the one check already executed lives in a `slow` test that CI runs with
`continue-on-error: true`. It is written with hyphens, since `CONTRIBUTING.md` is user-facing prose under the
execution contract.

## Open questions

### OQ-01: Should the drifted golden be regenerated, or is the renderer's new text the defect

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE: REGENERATE THE GOLDEN, because the render became
  MORE correct and the golden is stale. The two differing lines both add flags that make the suggested
  command actually perform the fix: the golden's `run 'aw rename plans a.md'` and `run 'aw group plans b.md
  --set <new-set-id>'` would each PREVIEW and exit, because every mutating verb in this repository previews
  by default and requires `--apply` (confirmed in the `--help` of `aw ipd scaffold`, `aw backlog new` and
  `aw rename`), whereas the render's `--to-id6 --apply` and `--rename --apply` forms do the work. The render
  additionally explains WHY the name is nonconformant ("a.md does not carry a clustered identity prefix"),
  which is strictly more useful in a `Fix:` line. So the code is right. TWO CONSTRAINTS ON HOW: the diff MUST
  be captured and quoted BEFORE regenerating, because a golden regenerated without a reviewed diff stops
  being a reviewed artifact and reproduces this item's root cause; and only this ONE file may change, since
  the other eleven match byte for byte today.

### OQ-02: Should the golden helper keep silently creating a missing golden file

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS A BOUNDED CHOICE E-03 MAKES AND RECORDS, with a stated
  preference. The recovered `_read_or_write_golden` writes the file when `AW_CONFORMANCE_UPDATE_GOLDENS == "1"`
  OR when it does not exist, then compares the render against what it just wrote, so a deleted or renamed
  golden passes vacuously and is recreated from current behavior (F-06). PREFERRED: require the file to exist
  and FAIL with a message naming the missing path, keeping the environment variable as the one explicit
  regeneration route. That is strictly better for the property this plan exists to protect, since a golden
  that cannot go missing-red is a golden that can be deleted to silence a failure, which is the same
  weakening `GUIDING_PRINCIPLES` 16 forbids ("Never weaken an assertion so it passes everywhere"). ACCEPTABLE:
  keep the fallback, if E-03 records the residual risk explicitly and states why the convenience is worth it
  (for example that a new fixture would otherwise require a two-step dance). What is NOT acceptable is
  porting the fallback without noticing it, which is why this is an open question rather than a silent
  implementation detail.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the per-test-method result table from the recovered module, naming every method
    across its seven gate classes with its outcome. Exactly ONE must fail:
    `DeterministicByteGoldenTests::test_human_plain_goldens_stable` on the `check_findings` subtest. PASTE its
    failure output including the differing text. PASTE the command used and confirm, by showing the
    environment (for example `env | rg AW_CONFORMANCE_UPDATE_GOLDENS` returning nothing), that the
    regeneration variable was UNSET. If any other method failed, describe it with evidence before E-02
    proceeds.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE `git diff tests/fixtures/conformance_goldens/check_findings.human.golden` in
    full, and QUOTE both changed `Fix:` lines before and after. STATE the direction taken and the reasoning,
    which must match OQ-01's `--apply` argument or justify a departure from it. PASTE
    `git status --short tests/fixtures/conformance_goldens/` showing exactly ONE modified file, which is what
    proves the other eleven were not swept along. PASTE a re-render comparison showing all twelve goldens now
    match.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the output of `python3 -m pytest` (bare, no added flags) showing the new module
    COLLECTED AND PASSING; a run requiring `-m ''` does not satisfy this item. PASTE
    `rg -n 'pytest.mark.slow|pytestmark' tests/test_cli_quality_gates.py` returning nothing. ENUMERATE all
    seven gates by test-class name and, for each, paste the measured value its assertion checked (the
    validator result, the ANSI search result, the golden comparison, the glyph values, the truncation
    summary record, the parity triple, and the byte and token figures). STATE the OQ-02 decision on the
    missing-file fallback and quote the code implementing it. QUOTE the module docstring sentence
    distinguishing renderer-level parity from the deferred live-leaf parity.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE all four probe failures verbatim. Probe 1 must name the fixture and render whose
    golden byte was altered. Probe 2 must state WHICH mechanism rejected the ANSI escape (the module's own
    ANSI gate, `agent_schema`'s `_ANSI_ESCAPE_RE` rule, or both), since the two overlap and the evidence must
    not claim credit twice. Probe 3 must fail on the `emitted + omitted == total` arithmetic specifically.
    Probe 4 must fail on the byte ceiling. PASTE `git status --short` and `git diff --stat` for BOTH
    `agent_workflows/` and `tests/fixtures/` showing no probe residue, which matters most for the fixture
    probe because a surviving one would be a committed wrong byte in a reviewed artifact.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: QUOTE the rewritten `CONTRIBUTING.md` step 6 in full. Then produce a six-row table,
    one row per promise the original made (ANSI-free agent stream, exit-code parity, fact-parity, help, usage
    error, no-color), each row naming either the test that executes it or the carrier it is attributed to.
    CONFIRM the `slow`/`continue-on-error` caveat on exit-code parity is stated in the prose. CONFIRM no em or
    en dash was added, for example by pasting a search for those characters over the diff returning nothing.
    Finally PASTE the two bare-suite summary lines (base and final) and state the failure-set delta as a SET
    of test ids, which must be EMPTY.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: PASTE the `rg '\.golden' --glob '!*.golden' tests/` output and, for each of the twelve goldens, the test method and fixture/suffix pair that reads it. PASTE the per-name table for `tests/conformance_matrix.py` (name, and one of: importer, internal user, or `absent`), re-derived at execution rather than copied from `dq9bj9`. PASTE the greps showing the zero-undeclared-leaves assertion in the two named files, and for `tests/test_conformance_matrix_structure.py` either a grep returning nothing or the assertion together with the sentence labelling it a precondition.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires human approval before execution and carries no `- Readiness:` field, because that field is
an OUTPUT of `/plan-review` and writing one at authoring would forge the attestation the auto-approve
predicate reads first. It declares `- Item-Dependencies: executed:dq9bj9` and must not execute before that sibling, for
the mechanical reason in F-09: it imports `GOLDEN_DIR` from a module whose symbol set `dq9bj9` resolves.

The executing agent commits ONLY the paths in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never
`git add -A` and never pushing. Three commit-time hazards are specific to this plan. FIRST, E-01 brings a
recovered file into the tree temporarily and it must be gone before any commit. SECOND, E-04 probes BOTH
production code and a fixture file; the fixture probe is the dangerous one, because an unreverted byte there
is a wrong value inside a reviewed artifact that now has a reader, so re-verify
`git status --short tests/fixtures/` specifically. THIRD, exactly ONE golden may appear in the staged set;
if a second does, stop and determine whether it is this plan's change or a concurrent lane's. Other agents
may be working in this checkout, so leave untracked or modified files this plan does not own alone.

HONESTY RULE (hard MUST): paste the ACTUAL runner output for every claimed pass, probe failure, grep and
summary line; a summary you did not run is not evidence. SCOPE FENCE: `- Scope-Paths:` is a DECLARATION for
reconciliation; an out-of-scope edit (for example a second drifted golden, per Scope check) is made and then
justified at finalize with `--scope-reason`, and a declared-but-unmodified path is acknowledged with
`--scope-ack`.

Do NOT move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports
conforming and every `V-*` above carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run`
the runner performs the terminal transition; executed by hand, the executor runs `aw ipd finalize`. Never
hand-edit `- Status:` and never hand-`git mv` the file into `executed/`. The bar for V-05's suite delta is
an EMPTY SET, not a green run.
