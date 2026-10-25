---
id: yibf7z
created: 20261024
set: specflow
order: 16
topic: [specflow, spec-synthesis]
model: opus55high
kind: assessment
status: active
outcome: none-yet
summary: Refinement iteration 1 (self-review, prompt khjc70) of candidate spec yfz5u9; not a /spec-review
consumed-by: []
---

# Refinement record for candidate spec `yfz5u9` (self-review iterations)

## Iteration 1

This is a design-improvement record, not a `/spec-review`. It is filed in the research tree on purpose: a
parseable record under `.aw/records/reviews/` naming `yfz5u9` would satisfy
`review_findings.review_attestation_missing` and could let the spec move to `reviewed` with no real review. That
is the same hazard the candidate's R-62 forbids for the proposed tool.

| Field | Value |
| --- | --- |
| Subject | spec `yfz5u9`, `.aw/records/specs/draft/20261024-specflow-03-yfz5u9-spec-research-synthesis.spec.md` |
| Prompt | `khjc70` (`.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md`) |
| Reviewer | OpenCode, host-reported model `uri/its_direct/pt3-claude-opus-5.5-1m-us`; reasoning setting not observable from inside the session |
| Independence | Self-review. The same model, in the same conversation, wrote the candidate. This iteration is not independent evidence. |
| Iteration | 1 of an operator-run loop. No cap or prior iteration history was supplied. |
| Baseline | repository HEAD `47bd8f9e94ac369121fdd93a51596f629a841ae6`; spec sha256 `5b758a66fc5bd245427783fd6bcaf9f1ea3d6d79a1bcfb263a6b747ede9f7ee6`, 1652 lines, 99 requirement ids, 76 acceptance ids |
| Code citations | unchanged pin `6f430cefd`; `git diff 6f430cefd..47bd8f9e9 -- agent_workflows docs` is empty, so the pin is current |
| Result | 7 ids added (`R-69`, `R-95`, `R-117`, `AC-38b`, `AC-44b`, `AC-48b`, `AC-51b`, `AC-56b`), 0 removed |

## Findings

Severity uses `review_findings.SEVERITIES` (`low|medium|high|blocker`). "Blocks handoff" means the candidate
should not be merged or reviewed with the defect present. All findings are new (first iteration) and all are
resolved in the candidate unless marked otherwise.

| ID | Severity | Area | Defect and evidence | Correction | Blocks handoff |
| --- | --- | --- | --- | --- | --- |
| RF-01 | high | Config, FND-2, R-11, 5.2 | The preferred Gemini participant cannot be configured. `MODEL_RE` requires `provider/model`; `parse_profile('g', {'runner':'agy','model':'gemini-3.8-flash-high'})` raised `ProfileSchemaError` (run 2026-10-25), while `agy models` prints bare ids. The candidate also missed that `aw agy run` ignores a profile's `model` (`agy_runipd.initialize_run`; `docs/runner-profiles.md`). | R-11 now has two relaxations: (a) `variant` on `agy`, (b) single-segment `agy` model ids. FND-2 states all three gaps and that synth builds its own `agy` argv, so the driver gap does not affect synth. Profile table and discrepancy list updated. | yes |
| RF-02 | high | Execution, R-83 | Antigravity takes the prompt as one `-p` argv element. Linux refuses one argument over 128 KiB: measured 120000 bytes spawns, 140000 bytes fails `E2BIG`. Synthesis prompts carrying three candidates inline would exceed it. | R-83: `agy` prompts hold instructions plus input file paths only, refused over 96 KiB (`prompt-too-large`) before spawn; data blocks go in the referenced files. | yes |
| RF-03 | high | Isolation, R-80, R-81, 7.2 | OpenCode participants were left with no out-of-worktree denial, although isolated driver turns already pass `lane_containment.LANE_PERMISSION_POLICY` (`external_directory: deny`) via `OPENCODE_CONFIG_CONTENT`. Also the outbox was placed outside the worktree, which that denial would block. | R-80 requires the existing policy for OpenCode and states Antigravity has none. R-81 puts inputs and outbox inside the worktree under gitignored `.aw/state/` (`LANE_SUBMISSION_SUBDIR`), copied to the run dir after the dispatch. Worktrees go under `worktree_lease.worktrees_root`, not inside the records runs root. AC-44b added. | yes |
| RF-04 | high | Protocol, R-101, 12.3.5 | The candidate streamed `item` records then a final `result` on stdout. `docs/cli-agent-protocol.md` defines a stream as items terminated by exactly one `summary`, and a summary has no run-state slot. | stdout carries exactly one `result`; progress goes to stderr, as `item` records only with `--progress jsonl`. Transcript and AC-53 updated; both record shapes rechecked with `validate_agent_record` (0 errors). | yes |
| RF-05 | medium | Workflow, R-40, R-60 | Contradiction: R-40 counts an incumbent toward synthesis, so N = 1 with `--from-spec` synthesizes, but R-60 said N = 1 creates the spec at generate. | R-40 defines sources; with an incumbent the single candidate is a `source-draft` and synthesize creates the spec. R-60 keyed on whether synthesis runs. Flow diagram node relabelled. | no |
| RF-06 | medium | Workflow, R-61 | R-61 created a single survivor's spec record at finalize, but synth-refine (R-47) must run on the working spec before finalize. | Spec record now created where synthesis would have run; AC-68 updated. | no |
| RF-07 | medium | Recovery, 6.3 | A run capped during generation or candidate refinement (N >= 2) has no spec record, yet the state diagram allowed `capped -> finalized-with-limitations`. | Added to hard blocks with the two permitted next actions. | no |
| RF-08 | medium | Recovery, R-86 | Resume after a runner-profile edit was undefined (the brief explicitly asks for "resume after an input or profile change"). | R-86: resume uses the frozen `ResolvedLaunch`, warns `profile-changed-since-freeze`, stops on `catalog-missing`. AC-48b added. | no |
| RF-09 | medium | Naming, 6.6.4 to 6.6.7 | The brief NN was shown as `01`, but `research_cmd._next_order_for_set` gives a research-prompt opening a new set order `00`. Inventories were therefore not what the owner verb would produce. | Brief NN `00` in the matrix and all three inventories; resumed-run NNs renumbered. | no |
| RF-10 | medium | Naming, location | Intermediates were said to be `active` at creation; `plan_new` writes `todo`. | Location rule now: created `todo`, promoted to `active` on publish via `aw research promote`; brief stays statusless. | no |
| RF-11 | medium | Research, R-66 | A research run setting candidates `adopted` with empty `consumed-by` fails `adopted-without-consumer` (`research_index.check_drift`). | Research runs use `informational` plus `synth-consumed-into`. | no |
| RF-12 | medium | Research, missing finalize rule | Research finalize had no clean-versus-limited rule (R-64 is spec-only). | New R-117 and AC-56b; `--accept-limitations` refused for research. | no |
| RF-13 | medium | Caps, 3.4 | The Q formula omitted research citation-check dispatches, the incumbent-only synthesis, and did not say whether verify reopening or rejections can escape the bound. | Formula updated; research example added (Q = 31, W = 93); R-48 limits verify to once per run; rejections stated to run inside the counter. | no |
| RF-14 | medium | Naming, concurrency | `set-busy` existed only in prose. | New R-95 and AC-51b. | no |
| RF-15 | medium | Context, R-55 | Discovery used `limit.context` although the catalog also reports `limit.input` (measured 922000 input of 1050000 context for `openai/gpt-6.1-sol`). | R-55 prefers `limit.input`, else context minus output; preferences may only lower it. | no |
| RF-16 | low | CLI, 3.3 | Selector rule 4 `last` came after setid matching, so a setid named `last` would shadow it. | `last` is rule 3 and reserved; setid matching requires one non-terminal run. | no |
| RF-17 | low | CLI, 3.2 | `--keep-draft` was in the grammar with no definition. | New R-69 and AC-38b. | no |
| RF-18 | low | CLI, `--with` | "Explicit form consults no preference file" conflicted with a token "required unless the preferences map" it. | Reworded: the explicit form always spells the token. | no |
| RF-19 | low | Research, R-112, R-114 | Quick-mode citation checks key on "high impact", which the claims schema did not define. | `impact: high|normal` added to the claims schema. | no |
| RF-20 | low | R-64 (b) | "Distinct requested model ids" did not say how variants and unknown imports count. | Variants of one id count once; unknown identity does not count; AC-37b extended. | no |
| RF-21 | medium | Diagram, 7.7 | The spec flow did not render: `mmdc` 12.0.0 failed with "Lexical error on line 11" because edge labels contained `--`. | Rewritten with quoted labels; all four diagrams now render with `mmdc`. | no |
| RF-22 | low | R-02 | Preview validation listed R-10 to R-16 and R-93, omitting policy (R-18), preferences (R-17, R-19), and `set-busy`. | R-02 now lists R-10 to R-19, R-93, R-95. | no |

No finding was a D177 violation: every attributed name already used `[.<ace>][.<model>].<type>.md` with dot-free
tokens, and the candidate already states the `_CLUSTERED_RE` / `parse_name` / `check.name-nonconformant` gap
(FND-8, R-90, R-94).

## Original-obligation classification

All obligations of generation prompt `443ltw` and refinement brief `khjc70` Section 2 are `satisfied` after this
iteration, with these qualifications:

- Codex for the Sol slot: `intentionally changed with authority of evidence` (no driver exists; deferred, DL-6). The maintainer has not ruled on it.
- Model-written prompts ("generates a synthesis prompt"): `intentionally changed` to deterministic engine templates (R-23, DL-11). This meets the outcome (task-specific rendered prompts exist and are stored) but not a literal reading in which a model writes them. Flagged as nonblocking OQ-9 below.
- Multiple synthesizers: deferred with a fixed shape (R-45).

## Open questions raised by this iteration

- OQ-9 (nonblocking): Should a model, rather than a template, write the task-specific generation and refinement prompts? Recommendation: keep deterministic templates in release 1, because a rendered template can be validated and replayed and a model-written prompt cannot be checked mechanically for the independence and data-block rules; revisit once a run corpus exists.

## Walkthroughs performed against the revised text

| Scenario | Expected gates and result |
| --- | --- |
| One participant, quick | preview Q = 3; generate creates spec record (no incumbent); one synth-refine iteration; ready-to-finalize; finalize exit 0, `auto_advance: not-multi-model`, spec stays `draft`, Next `aw specs set to-review` |
| Three models, thorough | Q = 29, ceiling 40; barrier; cross-review loops; synthesize creates spec; decision-needed stop; decide; synth-refine; one verify; finalize to `to-review`; Next `/spec-review` |
| Research with conflicting sources | Q = 31; citation checks before and after reconcile; contradiction kept; confidence capped; finalize exit 0 or 1 per R-117; findings record `reference`, outcome `informational` |
| Participant failure | barrier stops at `reduced-participation`; `--continue-reduced` with 2 survivors synthesizes (multi-model if 2 model ids); with 1 survivor creates spec before synth-refine, finalize leaves `draft` |
| Cap with open material findings | `capped-open` banner, result `partial`, exit 1; finalize leaves `draft` unless `--accept-limitations --by-human` on a multi-model synthesis; capped before synthesis is a hard block |
| Interrupted resume after brief edit | `resume` exits 2 `brief-changed`; new run with `--from-run --reuse generate` |
| Interrupted resume after profile edit | warning `profile-changed-since-freeze`; frozen launch used |

## Validation actually performed

- `aw specs check <spec>`: conforms.
- Requirement and acceptance ids parsed with `production_checks.parse_spec_requirement_ids`: 0 removed, 7 added; every `R-` and `AC-` reference resolves; every requirement is covered by at least one acceptance criterion.
- All four Mermaid diagrams rendered to SVG with `@mermaid-js/mermaid-cli` 12.0.0 (`mmdc`), after the RF-21 fix.
- Both machine-output records in Section 12.3.5 validated with `agent_schema.validate_agent_record` (0 errors).
- Unattributed and model-only example filenames round-trip through `research_contract.parse_name` / `format_name`; the two-facet ACE names cannot be checked until R-90 exists.
- `aw sanitize --agent` and gitleaks over the changed files: see the commit for this iteration.
- `aw research index --check` reports 4 `dangling-citation` advisories for fictional example id6s in the spec (`k2m9qa`, `f6nb1x`, `q3rw8e`, `n4bt7c`), present at baseline, among 329 such advisories repository-wide. Left unchanged (residual, low): the examples are labelled fictional; changing them to non-id6 shapes would make the inventories stop obeying the grammar they illustrate.
- No implementation tests apply: the feature is unimplemented.

## Stopping result

Material changes made; rerun warranted. The four `high` findings changed requirements that downstream sections
depend on (configuration, launch argv, isolation, protocol), so another iteration, preferably by a different
model, should check the revised sections.

## Iteration 2

| Field | Value |
| --- | --- |
| Prompt | `khjc70`, run again by the operator |
| Reviewer | OpenCode, same model and conversation as the author and iteration 1 (self-review; not independent evidence) |
| Baseline | HEAD `766875058`; spec sha256 `87b5bb7ec2dfcdc4...`, 1676 lines, 102 requirement ids, 81 acceptance ids |
| Code drift since pin `6f430cefd` | `runner_shared`, `lane_containment`, both drivers: fix-it lane handling and an interrupt `save_state`. No symbol cited by the spec changed behaviour. |
| Result | 6 ids added (`R-96`, `AC-20b`, `AC-22b`, `AC-24b`, `AC-29b`, `AC-56c`), 0 removed |

Iteration-1 findings `RF-01` to `RF-22`: rechecked, none reopened.

| ID | Severity | Area | Defect and evidence | Correction | Blocks handoff |
| --- | --- | --- | --- | --- | --- |
| RF-23 | high | Convergence, R-34 | R-34 required "the deterministic checks for the document (R-63)" to pass, and R-63 starts with `aw specs check`. Candidates are research `source-draft` records, not specs, so a candidate loop could never reach `converged`. | R-34 now names the checks per document type; candidates are never run through `aw specs check`. AC-22b. | yes |
| RF-24 | high | Naming, D177, R-74 | A one-participant research run named its final `findings` record `.reconciliation.`, which D177 reserves for multi-contributor documents, so the file would misstate authorship. | Single-author research finals carry the author's facets. Matrix row and AC-56c updated. | yes |
| RF-25 | high | Lifecycle, `accept` | `accept` set a loop to `accepted`, but R-64 (d) did not list `accepted`, so accepting a `capped-open` loop could have produced an automatic `to-review` with open material findings, that is, a clean label on known defects. | New R-96: acceptance with open findings is a limitation for R-64 (d) and R-117, requires `--by-human --message`, and the findings are listed under `## Known limitations`. AC-24b. | yes |
| RF-26 | medium | CLI, 3.2 | 13 flags or verbs used in requirements, diagrams, or transcripts had no grammar entry: `--from-stage`, `--defer-decisions`, `--allow-reduced`, `--allow-uncataloged`, `--from-run`/`--reuse`, `--finalize`, `--freeze-worktree`, `--progress`, `--review`, `--participant`, `--default`, `aw synth prune`. Found by extracting every `--flag` and diffing against Section 3.2. | All added to the grammar or the run-option table with defaults. | no |
| RF-27 | medium | Reject, R-44 vs R-76 | R-44 said a rejected synthesis is "redone"; R-76 said a rejected working document is revised in place. The two disagreed on whether refinement history survives. | R-44: reject before synth-refine starts redoes the synthesis in place (new revision, new matrix); after it starts, `reject` exits 2 `use-from-run`. AC-29b. | no |
| RF-28 | medium | Naming, inventory 6.6.5/6.6.6 | Iteration 1 moved the brief to NN `00` but left the other records numbered from `02`, leaving a gap at `01` that `plan_new` would never produce; the dispatch range `d001..d031` disagreed with the transcript's 23 dispatches. | Renumbered every example record (inventories, transcripts, finalize paths) and stated the 23-dispatch breakdown. | no |
| RF-29 | medium | Attribution, assessments | One "synthesis assessment" held synth-refine and verify findings even when two different participants wrote them, giving one author facet to another participant's work. | One assessment per (document, reviewer) pair; NN worst case recomputed to `4N + 7`; AC-51 arithmetic redone. | no |
| RF-30 | medium | Review assignment, R-31 | Cross review assigned candidate i to participant i+1 even when that participant had failed and the run continued reduced. | Fallback to the next available participant, else self-review with the label. AC-20b. | no |
| RF-31 | medium | Status exit codes, 3.6 | `status` exited 1 for any run "not clean", so a polling script saw exit 1 for every running run. | Exit 0 and exit 1 states listed explicitly. | no |
| RF-32 | medium | Baseline, Section 0 | Section 0 still described only the authoring HEAD. | Records the re-inspected HEAD and the code drift since the pin. | no |
| RF-33 | low | Prose consistency | Section 1.1 said "read-only view" (contradicts R-81); FND-13 named a nonexistent `aw synth start`; FND-17 said rendered prompts are research-prompt records (contradicts 6.6.3); 1.6 placed research citation checks inside synthesize; the 2.2 table omitted R-11 (b); stage table verify skip rule disagreed with the role table. | Each corrected. | no |
| RF-34 | low | Diagram | State diagram allowed `capped -> finalized-with-limitations` even with no working document, contradicting the hard-block list. | Edge label qualified. | no |

### Iteration 2 validation actually performed

- `aw specs check <spec>`: conforms.
- Requirement and acceptance ids: 0 removed, 6 added; every `R-` and `AC-` reference resolves; every requirement has at least one acceptance criterion.
- All four Mermaid diagrams rendered to SVG with `mmdc` 12.0.0.
- Every `aw.agent/v1` example record in the spec validated with `agent_schema.validate_agent_record` (0 errors).
- Every example research filename in the spec: 5 round-trip through `research_contract.parse_name`/`format_name`; 9 carry an ACE facet and cannot be checked until R-90 exists (expected, stated in the spec).
- Flag inventory: every `--flag` in the spec is now defined in Section 3.2 or is an existing house or host flag.
- Walkthroughs re-run against the revised text: one-participant quick (finalize leaves `draft`, Next `aw specs set to-review`); three-model thorough (23 dispatches, `to-review`); research with conflicting sources (single author: author facets; multiple: `.reconciliation.`); participant failure (review fallback, reduced participation); cap with open findings then `accept` (still a limitation, stays `draft` unless `--accept-limitations`); resume after brief edit (exit 2) and after profile edit (frozen launch, warning).

### Iteration 2 stopping result

Material changes made; rerun warranted. Three `high` findings (RF-23 to RF-25) were found that iteration 1 missed,
so this self-review loop is still finding defects; a review by a different model is the more useful next step.

## Iteration 3

| Field | Value |
| --- | --- |
| Prompt | `khjc70`, run again by the operator |
| Reviewer | OpenCode, same model and conversation as the author and iterations 1 and 2 (self-review; not independent evidence) |
| Baseline | HEAD `e19492246`; spec sha256 `7f1b94dca3e313d5...`, 1694 lines, 103 requirement ids, 86 acceptance ids |
| Code drift since `766875058` | none in `agent_workflows/` or `docs/` |
| Result | 4 ids added (`R-97`, `AC-44c`, `AC-47b`, `AC-51c`), 0 removed |

Iteration 1 and 2 findings (`RF-01` to `RF-34`): rechecked, none reopened.

| ID | Severity | Area | Defect and evidence | Correction | Blocks handoff |
| --- | --- | --- | --- | --- | --- |
| RF-35 | high | Attention, pipeline position | The brief is a statusless research prompt, which attention classifies by set pipeline position. `research_index.derive_pipeline_positions` marks a set `synthesized` (attention `done`) as soon as a `reconciliation-report` member has a body. Verified by calling it: with the matrix body present it returned `synthesized`, with front matter only `partial`. So a run waiting on a maintainer decision would have shown as done in `aw attention`. | New R-97 and Section 6.6.2b: the matrix and research working `findings` records are published front matter only; live bodies stay in the brief companion until finalize (or cancel). Matrix table, decide row, and matrix description updated. AC-51c. | yes |
| RF-36 | high | Concurrency vs cancel, R-85 vs R-07 | R-85 refused every second process on a live run with `run-locked`, so `aw synth cancel` from another terminal could never reach a running run; and nothing said a run releases its lock at `waiting-for-human`, which `accept` and `decide` need. | R-85: read verbs take no lock; `cancel` writes a request file and signals the holder; `accept`, `reject`, `decide` act on stopped runs. R-03: every stopping state ends the process and releases the lock. AC-47b. | yes |
| RF-37 | medium | Worktree cleanup, R-81 | Nothing removed synth worktrees, and `aw lanes prune` will not: `aw lanes list` classifies non-lane directories under the worktree root as `other: not a lane` (four such directories exist today). | R-81 requires `git worktree remove` after each stage, on cancel, finalize, prune, and stale cleanup on resume. AC-44c. | no |
| RF-38 | medium | Timeouts | `--dispatch-timeout` defaulted to 60 min with no link to Antigravity's `--print-timeout` (a Go duration needing a unit, `runner_shared.probe_argv` comment) or to the 8 h ceiling; 60 min is short for a three-candidate synthesis. | Per-stage defaults (90 min generate and synthesize, 45 min otherwise), passed as `--print-timeout` with a unit for `agy`, capped at `MAX_TURN_TIMEOUT`, labelled as estimates. `--stall-timeout` added to the grammar. | no |
| RF-39 | medium | Import parsing, R-06 | `--candidate <label>=<file>@<ace>/<token>` had no split rule for paths containing `=` or `@`, and no validation of the ACE or token. | Split at first `=` and last `@`; ACE from the closed list; token from the vocabulary; `@<token>` alone allowed. | no |
| RF-40 | low | Usability, 8.3 | The one TTY confirmation was described without its prompt text or the flag that skips it, and `--yes` was not in the grammar. | Prompt text and `--yes`/`--no-interactive` behaviour stated; `--yes` defined as never consent for `--by-human`. | no |
| RF-41 | low | Baseline, Section 0 | Section 0 did not record iteration 3. | Updated. | no |

Checked and found sound this iteration (no change): companion files are excluded from id6 scans
(`check_engine._iter_type_files` skips companion directories, and `artifact_adopt.repository_id6s` uses it), so
revision copies holding `id:` or `- Id:` lines cannot create id6 collisions; `From-Spec` on a spec record is a
supported field checked by `check.from-spec-dangling` on both plans and specs.

### Iteration 3 validation actually performed

- `aw specs check <spec>`: conforms.
- Ids: 0 removed, 4 added; every `R-` and `AC-` reference resolves; every requirement has an acceptance criterion.
- All four Mermaid diagrams rendered with `mmdc` 12.0.0.
- Every `aw.agent/v1` example validated with `agent_schema.validate_agent_record` (0 errors).
- `research_index.derive_pipeline_positions` called with constructed entries to confirm the RF-35 mechanism and its fix.
- Every flag newly mentioned is declared in Section 3.2 or is an existing host flag (`--print-timeout`, `--force` on `git worktree remove`).

### Iteration 3 stopping result

Material changes made; rerun warranted. Two `high` findings were still found on the third self-review, in areas
(attention integration, process and lock lifetime) the earlier iterations did not walk. The finding rate is falling
(22, 12, 7), but it has not reached zero, and further self-review by the same model has diminishing value
compared with an independent review.
