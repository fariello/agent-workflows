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
summary: Refinement iterations 1-8 (prompt khjc70) of candidate spec yfz5u9; not a /spec-review
consumed-by: []
---

# Refinement record for candidate spec `yfz5u9` (review iterations)

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

## Iteration 4

| Field | Value |
| --- | --- |
| Subject | spec `yfz5u9`, `.aw/records/specs/draft/20261024-specflow-03-yfz5u9-spec-research-synthesis.spec.md` |
| Prompt | `khjc70` (`.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md`) |
| Reviewer | Antigravity, model Gemini 3.8 Flash High |
| Independence | Independent review. Conducted by a distinct host environment (Antigravity) and a different model family (Gemini 3.8 Flash High) from the author and iterations 1-3 (OpenCode / Opus 5.5 High). This provides true multi-model adversarial scrutiny. |
| Iteration | 4 of an operator-run loop. |
| Baseline | HEAD `59f6d3137`; spec sha256 `713b54f8dae059ef1912f7b881491941b3f806fb430789b7eb00eea91820c991`, 1718 lines, 104 requirement ids, 89 acceptance ids |
| Code drift since pin `6f430cefd` | driver fix-it lane handling, interrupt `save_state`, and plan review tooling (`revsteps`); no symbol cited by the candidate changed behaviour. |
| Result | 2 requirement ids added (`R-98`, `R-99`), 2 acceptance ids added (`AC-9b`, `AC-29c`), 0 removed. Current totals: 106 requirements, 91 acceptance criteria. |

Iteration 1 to 3 findings (`RF-01` to `RF-41`): rechecked, none reopened.

| ID | Severity | Area | Defect and evidence | Correction | Blocks handoff |
| --- | --- | --- | --- | --- | --- |
| RF-42 | high | Workflow / Lifecycle, R-44, Table 3.6 | Candidate rejection allowed after synthesis started. Table 3.6 permitted `reject <doc-id6>` for any published record not yet consumed by finalize. However, R-44 only addressed working document rejection before synth-refine. Allowing a candidate to be rejected after synthesis has already merged it would leave the published matrix and working document citing an archived/rejected candidate. Also R-44 specified `<spec-id6>`, omitting research working documents. | Added R-98: `reject` on a candidate after synthesize has started is refused (exit 2 `candidate-already-synthesized`, AC-29c). Generalized R-44 from `<spec-id6>` to `<doc-id6>` to cover research working documents. Updated Table 3.6. | yes |
| RF-43 | high | Concurrency / Lifecycle, R-85 | R-85 restricted `accept`, `reject`, and `decide` to when the run is stopped in `waiting-for-human`. But under R-03, every stopping state ends the process and releases the run lock. `accept` on a document whose loop capped open (R-96, AC-24b) and `decide` on deferred conflicts are specifically valid and required at `ready-to-finalize` or `capped`. | R-85 updated to state that `accept`, `reject`, and `decide` can be used in any non-terminal stopped state (`waiting-for-human`, `ready-to-finalize`, `capped`), where the run lock is released. | yes |
| RF-44 | high | Diagram, Section 6.1 ER diagram | Cardinality `SYNTHESIS ||--o| ASSESSMENT : "reviewed in (0..1)"` contradicts Sections 6.1, 6.6.1, and 6.6.4, which specify that when synth-refine and verify are different participants, the synthesis has two separate assessments. Also `MATRIX ||--|| SYNTHESIS` enforces a 1:1 relationship that breaks on N=1 runs where no matrix exists. | ER diagram updated: `SYNTHESIS ||--o{ ASSESSMENT : "reviewed in (0..2)"` and `MATRIX }o--|| SYNTHESIS : "explains (0..1 to 1)"`. | yes |
| RF-45 | medium | Diagram, Section 7.7 Spec Flow | Spec flow diagram had no branch for `PART` when `--allow-reduced` is active (it showed only `no, and not allow-reduced`), an unlabeled edge from `VER` to `RTF`, and unqualified `DR --> TR` transition. | Added `PART -->|"no, and allow-reduced"| N`, labeled `VER -->|"no material findings, or no cap left"| RTF`, and qualified `DR --> TR` with condition (c) pass requirement. | no |
| RF-46 | medium | Diagram, Section 7.5 Research Flow | Diagram 7.5 unconditionally routed research runs through reconciliation and a second citation check (CC2), with no path for N=1 runs where synthesis and reconciliation are skipped. | Added `Sources >= 2?` decision after CC1; N=1 bypasses reconcile and CC2 directly to CF and synth-refine on findings. | no |
| RF-47 | medium | CLI / Config, Table 3.2, Section 3.6 | Behavior when no user preferences file exists (`defaults.roster` missing) and no `--with` flag is passed was undefined. | New R-99 and AC-9b: start without `--with` when no preferences file exists or `defaults.roster` is unset exits 2 `no-roster-configured` with a hint to run `aw synth config init --apply` or pass `--with`. Table 3.2 and Table 3.6 updated. | no |
| RF-48 | medium | Research / Roles, Section 3.4, Table 5.3 | Section 3.4 line 350 used undefined term "every claim marked important" instead of schema term `every claim with confidence medium or above` (R-114). Table 5.3 listed `verify` role default for N=1 as `(thorough only)`, leaving quick research runs without a designated verify participant for high-impact citation checks. | Section 3.4 updated to match R-114 schema terms. Table 5.3 updated to clarify `the participant (thorough mode for spec runs; thorough and quick for research runs)`. | no |
| RF-49 | medium | Research / Arithmetic, Section 3.4 | Dispatch arithmetic formula `(research ? 2 : 0)` unconditionally added 2 citation checks even when N=1 (where reconciliation is skipped and only 1 citation check runs). | Formula updated to `(research ? (N>=2 ? 2 : 1) : 0)`; N=1 thorough research example updated (Q = 9, W = 27, ceiling 27). | no |
| RF-50 | medium | Owner Verbs, R-66, Section 6.6.1 | R-66 and Section 6.6.1 cited `aw research promote` as setting outcome and `consumed-by`. But `promote` only updates status and moves files into monthly shards. Outcome and consumption provenance are owned by `aw research set-outcome`. | R-66 and Section 6.6.1 updated to explicitly cite `aw research set-outcome` for outcome and consumed-by provenance, followed by `aw research promote` for status transition. | no |
| RF-51 | medium | Naming / Inventory, Section 6.6.5 | Worked inventory companion directory tree omitted `matrix.md` despite R-97 and Section 6.6.2b requiring live bodies in `<C>/matrix.md` during the run. | `matrix.md` added to the companion file listing in Section 6.6.5. | no |
| RF-52 | low | Naming / Inventory, Section 6.6.4, Section 6.6.5 | Table 6.6.4 line 970 listed worktree as `synth-<run>-<did>/`, contradicting R-81 and AC-44c `synth-<run>-<label>-<stage>`. Section 6.6.5 line 1019 parser check had typo `...-02-b3xq8n-...` for `NN '01'`. | Table 6.6.4 corrected to `synth-<run>-<label>-<stage>/`; line 1019 example corrected to `...-01-b3xq8n-...`. | no |
| RF-53 | low | CLI, Table 3.2 | `--slug` derivation from brief's H1 fails when brief has no H1 (e.g. `--brief-text` or plain-text stdin). | Table 3.2 specifies fallback to first non-empty line or `--brief-text` (kebab-cased); if still empty, `--slug` is required (exit 2 `slug-missing`). | no |
| RF-54 | low | Security / Policy, R-18, R-80 | Model ID provider prefix rule assumed `/`, which fails on single-segment Antigravity IDs (`gemini-3.8-flash-high`). | R-18 and R-80 updated: single-segment `agy` model IDs derive provider from runner and model prefix (e.g. `gemini` -> `google`). | no |
| RF-55 | low | Splitting, R-52 | R-52 mandated units receive "the glossary" and "the interface contract section", which are not guaranteed sections in briefs (R-21). | R-52 updated to state units receive shared context from the brief when present (glossary, problem statement, interface definitions). | no |
| RF-56 | low | Provenance / Matrix, Table 7.3 | Matrix row `origin` admitted only `candidate` or `new`, omitting `incumbent` when merging with `--from-spec`. Also quote matching mechanics were unspecified. | Table 7.3 updated with `origin: candidate|incumbent|new`; quote verification specified as normalized substring match. | no |

### Iteration 4 validation actually performed

- `aw specs check <spec>`: conforms (1 specs checked, 0 errors).
- Requirement and acceptance ids parsed with `production_checks.parse_spec_requirement_ids`: 0 removed, 2 requirements added (`R-98`, `R-99`), 2 acceptance criteria added (`AC-9b`, `AC-29c`). Every requirement resolves to at least one acceptance criterion (106 declared `R-`, 91 declared `AC-`, 0 uncovered).
- All four Mermaid diagrams syntax-checked against spec prose, tables, and state transitions. No headless SVG renderer was run.
- Machine-output result record in Section 12.3.5 validated with `agent_schema.validate_agent_record` (0 errors).
- Clean worktree isolation maintained: all reviews, edits, and checks performed in `.aw/worktrees/refine-yfz5u9-iter4`.
- Leak checks passed.

### Iteration 4 stopping result

Material changes made; rerun warranted. The independent cross-model review by Antigravity / Gemini 3.8 Flash High uncovered 3 high-severity issues (candidate rejection lifecycle, stopping state lock release semantics, and ER diagram multi-assessment cardinality) that three prior OpenCode self-review iterations overlooked, as well as 7 medium and 5 low issues across owner-verb precision, diagram branch coverage, arithmetic, and CLI fallbacks. All 15 findings are resolved in the candidate spec.

## Iteration 5

| Field | Value |
| --- | --- |
| Subject | spec `yfz5u9`, `.aw/records/specs/draft/20261024-specflow-03-yfz5u9-spec-research-synthesis.spec.md` |
| Prompt | `khjc70` (`.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md`) |
| Reviewer | Antigravity, model Gemini 3.8 Flash High |
| Independence | Independent review. Conducted by a distinct host environment (Antigravity) and a different model family (Gemini 3.8 Flash High) from the author and iterations 1-3 (OpenCode / Opus 5.5 High). |
| Iteration | 5 of an operator-run loop. |
| Baseline | HEAD `2edf1f3ac`; spec sha256 `9dc2516e7549e9fb5b3c29793f694bd0a822ec656ec5abfb729cabfb8b777f7e`, 1728 lines, 106 requirement ids, 91 acceptance ids |
| Code drift since pin `6f430cefd` | driver fix-it lane handling, interrupt `save_state`, plan review tooling (`revsteps`), and specflow refinement iterations 1-4; no symbol cited by the candidate changed behaviour. |
| Result | 0 requirement ids added (clarified `R-06`, `R-25`, `R-49`, `R-53`, `R-60`, `R-64`, `R-83`), 2 acceptance ids added (`AC-6b`, `AC-16b`), 0 removed. Current totals: 106 requirements, 93 acceptance criteria. |

Iteration 1 to 4 findings (`RF-01` to `RF-56`): rechecked, none reopened.

| ID | Severity | Area | Defect and evidence | Correction | Blocks handoff |
| --- | --- | --- | --- | --- | --- |
| RF-57 | high | Inputs / Replay, R-25 | Source commit inheritance under `--reuse`: When a new run starts via `--from-run <run> --reuse generate|refine`, `R-25` did not define which repository commit is frozen. Freezing current `HEAD` when the repository has advanced causes candidate records generated against `<run>`'s commit to be mixed with refinement/synthesis against the newer commit, breaking codebase consistency across packet manifests and citations. | Clarify in R-25 that a run with `--reuse generate|refine` inherits the frozen source commit of `<run>` by default rather than freezing current `HEAD`. If `--source-commit` is explicitly supplied and differs from `<run>`'s source commit, `--reuse generate|refine` is refused (exit 2 `commit-mismatch-under-reuse`). Added AC-16b. | yes |
| RF-58 | high | Import / Roster, R-06, Table 3.6 | `aw synth import --from-stage refine` participant and roster binding: In refinement, R-31 requires that candidate `i` is revised by its author `i`. But an imported candidate's `<label>` comes from the command line, not necessarily a participant in the resolved roster. If `<label>` is not in the roster, the engine cannot dispatch a reviser because no runner profile is bound to that label. | Clarify in R-06 and Table 3.6 that when `--from-stage refine` is specified, each candidate `<label>` MUST match a participant label in the resolved roster (R-15); if any label does not match, `import` exits 2 `import-roster-mismatch`. When `--from-stage synthesize` (default) is specified, candidate labels do not need to match roster participants and serve only as matrix identifiers. Added AC-6b. | yes |
| RF-59 | high | Owner Verbs, R-60, Section 6.6.1 | Date formatting crash in `aw specs new --date`: `R-60` and Section 6.6.1 specified creating the spec working document with `aw specs new --date <set date>`. Set date prefixes in `agent-workflows` and research `plan_new` are 8 digits (`YYYYMMDD`, e.g. `20261102`). However, `aw specs new --date` strictly requires ISO 8601 format (`YYYY-MM-DD`, e.g. `2026-11-02`); passing `YYYYMMDD` fails with exit 2 `aw specs new: --date must be YYYY-MM-DD (got '20261102')`. | Update R-60 and Section 6.6.1 to state that the engine formats the 8-digit set date as `YYYY-MM-DD` when invoking `aw specs new --date <YYYY-MM-DD>`, while `aw group specs --date <set date>` retains the 8-digit format. | yes |
| RF-60 | medium | Splitting / Failure, R-49, R-53 | Split candidate unit retry exhaustion semantics: R-53 defines assembly of units into a candidate document, but neither R-53 nor R-49 specified what happens when a single unit of a split participant fails all retries during the generate stage. Because the candidate document cannot be assembled (`unit-missing`), candidate generation fails. | Explicitly specify in R-49 and R-53 that if any unit of a split participant exhausts its retry budget, candidate assembly fails, and the participant is treated as failed under R-49 (triggering `reduced-participation` or proceeding if `--allow-reduced` is active). | no |
| RF-61 | medium | Machine Protocol / Examples, Section 12.3.5 | Machine output `next_actions` listed `finalize` when capped before synthesis: In Section 12.3.5 line 1721, the `result` record for a spec run that reached `capped` during candidate refinement (prior to synthesis) listed `"aw synth finalize synth-77c0e1f2a3b4c5d6 --apply"` in `next_actions`. But under Section 6.3.1 (Hard blocks), running `finalize` on a spec run before a working spec record exists exits 2 as a hard block. Listing `finalize` as a valid next action directly contradicted Section 6.3.1, Section 12.3.4, and R-103. | Update Section 12.3.5 line 1721 `next_actions` to list valid actions for a pre-synthesis capped state: `aw synth findings ...`, `aw synth spec ... --from-run ... --reuse refine ...`, and `aw synth cancel ...`. | no |
| RF-62 | medium | ER Diagram, Section 6.1 | ER diagram cardinality contradiction for `new` matrix rows: Section 6.1 ER diagram specified `MATRIX_ROW }|--|{ CANDIDATE : "quotes source revision"`. The `}|--|{` cardinality asserted that every matrix row quotes at least one candidate. But Table 7.3 explicitly defines `origin: new (synthesizer-introduced; sources then empty)` and `origin: incumbent` where no candidate is cited. | Update ER diagram to `MATRIX_ROW }o--o{ CANDIDATE : "quotes (0..n)"`. | no |
| RF-63 | medium | Launches / Safety, R-83 | Antigravity `-p` prompt data paths must be worktree-relative: R-83 specified passing paths of data files in the dispatch's input directory to Antigravity's `-p` prompt. If machine-local absolute paths were passed, they would fail the repository leak sanitizer under `leak_sanitizer.scan_text` and violate repository rules. | Clarify in R-83 that paths in the rendered prompt are strictly relative to the dispatch worktree root (e.g. `.aw/state/synth-inputs/<did>/brief.md`), never machine-local absolute paths. | no |
| RF-64 | low | Lifecycle, R-64 (d), Table 3.6 | Working document loop scope in R-64 (d) vs candidate loops: R-35 states that candidate loop oscillation/capping allows the candidate to proceed into synthesis with a warning, while synthesis loop oscillation/capping blocks clean finalization. R-64 (d) used the unqualified phrasing "no loop outcome is capped-open, oscillating...", which could be misread as applying to candidate loops even when the synthesis merged candidates and resolved all issues. Also Table 3.6 line 429 omitted `oscillating` loops from human `accept` prerequisites. | Clarify R-64 (d) to explicitly specify the working document's loop (`synth-refine`, or the candidate loop when N=1). Update Table 3.6 line 429 to include `oscillating` loops under `accept`. | no |

### Iteration 5 validation actually performed

- `aw specs check <spec>`: conforms (1 specs checked, 0 errors).
- Requirement and acceptance ids parsed with `production_checks.parse_spec_requirement_ids`: 0 removed, 0 requirements added (clarified 7 requirements), 2 acceptance criteria added (`AC-6b`, `AC-16b`). Every requirement resolves to at least one acceptance criterion (106 declared `R-`, 93 declared `AC-`, 0 uncovered).
- All four Mermaid diagrams syntax-checked against spec prose, tables, and state transitions. No headless SVG renderer was run.
- Machine-output result record in Section 12.3.5 validated with `agent_schema.validate_agent_record` (0 errors).
- Clean worktree isolation maintained: all reviews, edits, and checks performed in `.aw/worktrees/refine-yfz5u9-iter5`.
- Leak checks passed via `check-local-leaks --agent` (0 findings).

### Iteration 5 stopping result

Material changes made; rerun warranted. The second independent cross-model review by Antigravity / Gemini 3.8 Flash High uncovered 3 high-severity issues (source commit inheritance under `--reuse`, import roster binding under `--from-stage refine`, and an actual runtime command crash in `aw specs new --date` due to ISO date formatting requirements) as well as 4 medium and 1 low issues across split candidate unit failure semantics, machine output next-action correctness, ER diagram cardinality, and relative data paths for prompt construction. All 8 findings are resolved in the candidate spec.

## Iteration 6

| Field | Value |
| --- | --- |
| Subject | spec `yfz5u9`, `.aw/records/specs/draft/20261024-specflow-03-yfz5u9-spec-research-synthesis.spec.md` |
| Prompt | `khjc70` (`.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md`) |
| Reviewer | Antigravity, model Gemini 3.8 Flash High |
| Independence | Independent review. Conducted by a distinct host environment (Antigravity) and a different model family (Gemini 3.8 Flash High) from the author and iterations 1-3 (OpenCode / Opus 5.5 High). |
| Iteration | 6 of an operator-run loop. |
| Baseline | HEAD `0d75ca5f0`; spec sha256 `acc90c614df7606f1734abacfe70756ff707c2998e669a10f8cb78f7de6baff7`, 1731 lines, 106 requirement ids, 93 acceptance ids |
| Code drift since pin `6f430cefd` | driver fix-it lane handling, interrupt `save_state`, plan review tooling (`revsteps`), and specflow refinement iterations 1-5; no symbol cited by the candidate changed behaviour. |
| Result | 0 requirement ids added (clarified `R-06`, `R-40`, `R-44`, `R-46`, `R-48`, `R-76`, `R-86`, `R-93`), 2 acceptance ids added (`AC-29d`, `AC-48c`), 0 removed. Current totals: 106 requirements, 95 acceptance criteria. |

Iteration 1 to 5 findings (`RF-01` to `RF-64`): rechecked, none reopened.

| ID | Severity | Area | Defect and evidence | Correction | Blocks handoff |
| --- | --- | --- | --- | --- | --- |
| RF-65 | high | Stage Graph / Incumbent, Table 6.2, R-40 | Synthesis skip condition with incumbent: Table 6.2 line 788 specified that `synthesize` is skipped when "fewer than 2 candidates". However, R-40 and Section 3.4 (line 372) explicitly mandate that synthesis runs when two or more *sources* exist, including N=1 with a hidden incumbent (`--from-spec`). In that case, there is only 1 candidate, but synthesis merges it with the incumbent to create the spec record. Table 6.2 also omitted `or N = 1` for skipping the candidate `refine` loop in line 787. | Update Table 6.2 line 788 to specify skipped when "fewer than 2 sources (fewer than 2 candidates and no incumbent under `--incumbent hidden`)". Update line 787 to specify skipped when "cap 0 or N = 1 (candidate refine loop is skipped when N = 1; the working document has only the synth-refine loop)". | yes |
| RF-66 | high | Research Flow / Verification, Section 7.5, Table 6.2, Section 3.4 | Research flowchart omitted thorough verify dispatch branch: In Section 7.5, the research Mermaid flowchart connected `SR` (synth-refine loop on findings) directly to `D{Ready to finalize}` with no branch. But Section 3.4 line 366 (`+ (verify ? 1 : 0)`), line 382 (Q=31 for N=3 thorough research), line 383 (Q=9 for N=1 thorough research), Table 5.3 line 686, Table 6.2 line 791, and Table 7.1 line 1075 all require that thorough research runs perform an independent verify dispatch to check coverage of brief questions, inaccessible sources, and contradictions before finalize. The flowchart completely omitted this verify stage. Furthermore, node `D` in Section 7.5 had an unlabeled arrow to `FIN`. | Update the Section 7.5 Mermaid flowchart to add the `V{Thorough mode?}` decision node after `SR`, branching on `yes` to `VER[Verify dispatch: questions coverage, inaccessible sources, contradictions]` and on `no` to `D{Ready to finalize}` (with `VER --> D`), and label the branch from `D` to `FIN` as `yes: ready`. Clarify Table 6.2 line 791 for research runs. | yes |
| RF-67 | high | Lifecycle / Rejections, Table 3.5, Table 3.6, R-44, R-76 | Rejection mutating effects falsely stated working document is archived: Table 3.5 (line 407) and Table 3.6 (line 431) stated that `aw synth reject <run> <doc-id6>` sets "Record status archive, outcome rejected". While this is true for candidate records and matrix records, R-44 and R-76 explicitly mandate that a rejected working document (the spec record or research findings) MUST NOT be moved to archive or given a new id6; it is revised in place as a new revision under the same id6, because it serves as the stable handle for `/spec-review` and downstream plans. Applying "Record status archive" to the working spec record would archive the spec and break its lifecycle and references. | Update Table 3.5 line 407 and Table 3.6 line 431 to explicitly distinguish candidate/matrix records (which move to `archive` with outcome `rejected`) from working document records (which are revised in place as a new revision under the same id6 in `draft/`, while the superseded matrix is archived). Added AC-29d. | yes |
| RF-68 | medium | State Machine / Cancel, Table 6.3, Diagram 6.3.1, Table 3.6 | Missing `cancelled` exit from `ready-to-finalize`: Table 3.6 line 433 permits `cancel` on any non-terminal run. `ready-to-finalize` is a non-terminal stopping state (Section 6.3). However, Table 6.3 line 800 listed the exits from `ready-to-finalize` only as `finalized-clean, finalized-with-limitations`, and Mermaid Diagram 6.3.1 omitted `ready_to_finalize --> cancelled: cancel` while drawing cancel transitions from every other non-terminal state. | Add `ready_to_finalize --> cancelled: cancel` to Mermaid Diagram 6.3.1 and add `cancelled` to the "Leaves to" column for `ready-to-finalize` in Table 6.3. | no |
| RF-69 | medium | Recovery / Run States, Section 6.3, line 804, line 855 | Missing `stage-failed` reason for `waiting-for-human`: Line 855 defines the dispatch lifecycle as transitioning to a retry or stage failure when retries are exhausted. Line 804 enumerates the reasons for entering `waiting-for-human`: `reduced-participation`, `decision-needed`, `context-overflow`, `artifact-modified`, `leak-detected`, `identity-mismatch`, `stage-rejected-cap`. When a non-generation dispatch (such as synthesize, synth-refine revise, or verify) exhausts its retry budget, the stage fails. Because `failed` is reserved strictly for unrecoverable engine errors (corrupt event log, line 810), a stage dispatch retry exhaustion must pause the run in `waiting-for-human`. But `stage-failed` was omitted from line 804's list of reasons and from Diagram 6.3.1's transition label. | Add `stage-failed` (naming stage, participant/document, and failure class) to the list of `waiting-for-human` reasons in line 804 and update Diagram 6.3.1's `running --> waiting_for_human` transition label. | no |
| RF-70 | medium | CLI Contracts, Table 3.6 | Conflation of `aw synth list` with selector validation: Table 3.6 grouped `status, list, findings` together under `Inputs and validation: Selector resolves` and `Exit 2: Selector resolves to nothing or is ambiguous`. But `aw synth list` has no `<run>` selector (its flags are optional filters `--active` and `--set <setid>`). In standard CLI design across `agent-workflows`, a listing query matching zero records emits an empty list and exits 0; it does not exit 2. Only `status` and `findings` take a positional `<run>` selector that must resolve. | Separate `list` from `status, findings` in Table 3.6, clarifying that `list` validates filter flags (`--set` length/syntax) and exits 0 on matching zero runs, whereas `status` and `findings` require a `<run>` selector and exit 2 if unresolved or ambiguous. | no |
| RF-71 | medium | Recovery / Resume, Table 3.6, R-86 | Undefined resume behavior on unresolved human wait reasons: When a run pauses in `waiting-for-human` due to `reduced-participation` (R-49) or `decision-needed` (R-46), continuing requires an explicit flag (`--continue-reduced` or `--defer-decisions`, or recording decisions via `decide`). Neither Table 3.6 nor R-86 defined what occurs if `aw synth resume <run> --apply` is invoked without these resolution flags while the blocking condition remains open. | Clarify in Table 3.6 and R-86 that invoking `resume` without the required resolution flag (`--continue-reduced` for `reduced-participation`, `--defer-decisions` or prior `decide` for `decision-needed`, or `--by-human` for `artifact-modified`) exits 2 with a specific error (`reduced-participation-unconfirmed`, `decisions-pending`, `artifact-modified-unresolved`) and a hint naming the required flag or command. Added AC-48c. | no |
| RF-72 | medium | Naming / Bounds, Section 6.6.1, line 908 | Omitted N=1 NN bounds with incumbent: Section 6.6.1 line 908 stated "For N = 1: brief, working document, one assessment = 3". This applies only to N=1 without an incumbent. Under R-40, an N=1 run with a hidden incumbent generates a candidate (`source-draft`), synthesizes it with the incumbent, publishes a matrix (`reconciliation-report`), creates the working spec record in the specs tree, and runs synth-refine with an assessment record (5 records, plus up to 2 regenerated matrices = 7 records). | Clarify Section 6.6.1 line 908 to explicitly bound both N=1 cases (without incumbent: 3 records; with incumbent: 5 base records, up to 7 with regenerations). | no |
| RF-73 | low | CLI / Decisions, Table 3.6, R-46, Transcript 12.3.2 | Clarify `--choose recommendation` keyword in `aw synth decide`: Transcript 12.3.2 line 1663 shows the operator running `aw synth decide last X-2 --choose recommendation ...`. However, Table 3.6 line 432 specified `option is one listed in the conflict` and exits 2 on `unknown option`, without explicitly defining `recommendation` as a reserved keyword alias for the synthesizer's recorded recommendation in conflict `X-<n>`. | Clarify in Table 3.6 and R-46 that `--choose <option>` accepts either an explicit option key from the conflict or the literal keyword `recommendation` to adopt the synthesizer's recorded recommendation. | no |
| RF-74 | low | Naming / Placement, Table 6.6.4 | Promoted research records shard path accuracy: In Table 6.6.4, the "After finalize" column listed `reference/` for promoted research records (brief, candidate, assessment, matrix, findings), whereas Section 6.6.1 line 916 and Section 6.6.5 line 1019 specify that `aw research promote` moves promoted records into monthly shard directories (`reference/YYYYMM/`). | Update the "After finalize" column in Table 6.6.4 to `reference/YYYYMM/` for all promoted research records, aligning with Section 6.6.1 and 6.6.5. | no |
| RF-75 | low | Import / Syntax, R-06, Section 3.2 | Clarify slash separator for `@<ace>/<token>` in R-06: Section 3.2 line 245 and line 410 document `--candidate <label>=<file>[@<ace>/<token>]` using a slash `/` between `<ace>` and `<token>`. R-06 described splitting at the first `=` and last `@`, but omitted explicit definition of the `/` separator between `<ace>` and `<token>`. | Update R-06 to explicitly specify that when both ACE and model are supplied, they are formatted as `@<ace>/<token>` (slash-separated). | no |

### Iteration 6 validation actually performed

- `aw specs check <spec>`: conforms (1 specs checked, 0 errors).
- Requirement and acceptance ids parsed with `production_checks.parse_spec_requirement_ids`: 0 removed, 0 requirements added (clarified 8 requirements), 2 acceptance criteria added (`AC-29d`, `AC-48c`). Every requirement resolves to at least one acceptance criterion (106 declared `R-`, 95 declared `AC-`, 0 uncovered).
- All four Mermaid diagrams syntax-checked against spec prose, tables, and state transitions. No headless SVG renderer was run.
- Machine-output result record in Section 12.3.5 validated with `agent_schema.validate_agent_record` (0 errors).
- Clean worktree isolation maintained: all reviews, edits, and checks performed in `.aw/worktrees/refine-yfz5u9-iter6`.
- Leak checks passed via `check-local-leaks --agent` (0 findings).

### Iteration 6 stopping result

Material changes made; rerun warranted. The third independent cross-model review by Antigravity / Gemini 3.8 Flash High uncovered 3 high-severity issues (synthesis skip condition contradicting R-40 for N=1 with incumbent, missing thorough verify dispatch branch in the research flowchart, and a lifecycle contradiction where rejected working documents were stated to be archived) as well as 5 medium and 3 low issues across cancel transitions from ready-to-finalize, stage retry exhaustion wait reasons, list command CLI contract separation, resume resolution gating, N=1 with incumbent NN allocation bounds, decide keyword aliases, and promoted research shard paths. All 11 findings are resolved in the candidate spec.

## Iteration 7

| Field | Value |
| --- | --- |
| Subject | spec `yfz5u9`, `.aw/records/specs/draft/20261024-specflow-03-yfz5u9-spec-research-synthesis.spec.md` |
| Prompt | `khjc70` (`.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md`) |
| Reviewer | Antigravity, model Gemini 3.8 Flash High |
| Independence | Independent review. Conducted by a distinct host environment (Antigravity) and a different model family (Gemini 3.8 Flash High) from the author and iterations 1-3 (OpenCode / Opus 5.5 High). |
| Iteration | 7 of an operator-run loop. |
| Baseline | HEAD `def40d511`; spec sha256 `507863f9a30bc6aee9977abe690643341eac1c408a58494163211581f86b4b46`, 1739 lines, 106 requirement ids, 95 acceptance ids |
| Code drift since pin `6f430cefd` | driver fix-it lane handling, interrupt `save_state`, plan review tooling (`revsteps`), spec 4sd62s diagrams, and specflow refinement iterations 1-6; no symbol cited by the candidate changed behaviour. |
| Result | 1 requirement id added (`R-118`), 3 acceptance ids added (`AC-32b`, `AC-56d`, `AC-76`), 0 removed. Clarified `R-21`, `R-42`, `R-48`, `R-49`, `R-51`. Current totals: 107 requirements, 98 acceptance criteria. |

Iteration 1 to 6 findings (`RF-01` to `RF-75`): rechecked, none reopened.

| ID | Severity | Area | Defect and evidence | Correction | Blocks handoff |
| --- | --- | --- | --- | --- | --- |
| RF-76 | high | Research Lifecycle / Working Doc, Section 4.13, R-60, R-118, AC-56d | Missing normative lifecycle requirement for working document in research runs: R-60 specifies that for a spec run the working document is a spec record in `specs/` from creation. However, research runs have no corresponding requirement defining the working document lifecycle. A research run creates its working document as a `findings` record (with model token `reconciliation` when N>=2, or author facets when N=1 without incumbent), published with front matter only until finalize under R-97. | Added R-118 and AC-56d to Section 4.13 and Section 9, formally defining the research working document lifecycle. | yes |
| RF-77 | high | CLI Contracts / Pruning, Section 3.2, Table 3.6, Section 9 | Missing `aw synth prune` leaf contract in Table 3.6 and acceptance criteria: Section 3.2 line 262 declared `aw synth prune [--older-than <days>] [--apply]`, but Table 3.6 omitted `prune` from the CLI leaf commands table, and Section 9 had no acceptance criteria testing prune semantics. | Added `prune` leaf row to Table 3.6 defining arguments (`--older-than`), state eligibility (terminal states only), preview vs `--apply`, and added AC-76 to Section 9. | yes |
| RF-78 | high | Recovery / Total Participant Failure, Section 4.7, R-49, AC-32b | Unhandled `--allow-reduced` under total participant failure (`k = 0`): R-49 specified that `--allow-reduced` bypasses `waiting-for-human` when a participant fails. However, if all participants fail (or the sole participant of an N=1 run fails), synthesis cannot proceed because 0 candidates exist. The engine must stop and refuse resume. | Updated R-49 to mandate stopping in `waiting-for-human` with reason `reduced-participation` even if `--allow-reduced` was passed when `k = 0` candidates remain, and specified that `resume --continue-reduced` exits 2 `no-candidates-available`. Added AC-32b. | yes |
| RF-79 | medium | Selectors / Resolution, Section 3.3, rule 4 | Setid selector resolution distinction between read and mutation verbs: Section 3.3 rule 4 stated that for a setid selector, "exactly one non-terminal run resolves; several, or only terminal runs, exit 2 listing them." This rule is appropriate for mutating verbs (`resume`, `accept`, `reject`, `decide`, `cancel`, `finalize`), but breaks read verbs (`status`, `findings`) when querying a completed/terminal run or when multiple runs exist for a setid. | Updated Section 3.3 rule 4 to distinguish mutating verbs (which resolve exactly one non-terminal run) from read verbs (which resolve a single run whether active or terminal, preferring an active run or the most recent terminal run when multiple exist). | no |
| RF-80 | medium | Configuration / Mutation, Section 5.2, Table 3.6 | Missing specification of dotted key paths and typing for `config set`: Table 3.6 and Section 5.2 mentioned `config set`, but did not specify whether key paths can be dotted (e.g. `defaults.mode`, `defaults.concurrency`) or shorthand, nor how type coercion behaves for integer/boolean config values. | Updated Table 3.6 and Section 5.2 to explicitly specify dotted path resolution (`defaults.<key>` or shorthand), type coercion (integer, boolean, string), and rejection of invalid keys/types before mutation. | no |
| RF-81 | medium | Assessment Attribution / Verify, Section 4.6, R-48, Table 6.1, Table 6.6.4 | Attribution contradiction for verify findings in R-48: R-48 stated that verify reports dropped items and contradictions "as findings in the synthesis assessment record". However, Table 6.1 line 741 and Table 6.6.4 line 973 explicitly mandate that when `verify` and `synth-refine` are performed by different participants, each participant has its own assessment record to maintain strict single-author attribution. | Updated R-48 to state that verify findings are recorded in the synthesis assessment when `synth-refine` and `verify` are the same participant, or in a separate verify assessment attributed to the verify participant when they differ. | no |
| RF-82 | medium | Heuristic Budgeting / Heuristic Bytes, Section 4.7, R-51, Section 7.6 | R-51 packet token estimate omitted definition of `bytes` and `read_factor`: R-51 specified the token estimate as `ceil(bytes / 4)` without defining what constitutes `bytes`. Section 7.6 line 1223 defines it as rendered prompt bytes + inline document bytes + (`read_factor * repo_files_bytes`). | Updated R-51 to explicitly define `bytes` with prompt bytes, inline documents, and the repository file `read_factor` factor (default 0.25). | no |
| RF-83 | low | Persistence / Revisions, Table 6.6.4, R-75 | Purpose column in Table 6.6.4 for `revisions/` stated "earlier bodies", contradicting R-75: Table 6.6.4 line 969 described the purpose of companion `revisions/` files as "earlier bodies". But R-75 explicitly requires storing all revision bodies, "including revision 0 and the current one". | Updated Table 6.6.4 line 969 to "all revision bodies (r00 through current)". | no |
| RF-84 | low | Freezing / Obligations, Section 4.3, R-21 | Clarify top-level list items for `B-1..B-n` assignment: R-21 stated that brief obligation ids are assigned to "every list item" under designated headings. If an author uses nested sub-bullets for examples or details, a naive parser would assign separate `B-n` ids to each sub-bullet. | Clarified R-21 to state that `B-1..B-n` are assigned to top-level list items, preserving nested sub-bullets within their parent item. | no |
| RF-85 | low | ER Diagram / Research Claims, Section 6.1 | ER diagram omitted synthesis relationship to claims in research runs: Section 6.1 Mermaid ER diagram showed `CANDIDATE ||--o{ CLAIM : "asserts (research)"`, but omitted the consolidated claims ledger produced by synthesis under R-113. | Added `SYNTHESIS ||--o{ CLAIM : "consolidates (research)"` to the Section 6.1 ER diagram. | no |
| RF-86 | low | Deterministic Synthesis Checks, Section 4.6, R-42 | Quote character limit on normalized text: R-42 specifies that row source quotes must be at most 200 characters from the cited revision, but did not specify whether character count is measured before or after whitespace normalization. | Clarified R-42 that the 200-character limit is measured on normalized text with internal whitespace collapsed. | no |

### Iteration 7 validation actually performed

- `aw specs check <spec>`: conforms (1 specs checked, 0 errors).
- Requirement and acceptance ids parsed with `production_checks.parse_spec_requirement_ids`: 0 removed, 1 requirement added (`R-118`), 3 acceptance criteria added (`AC-32b`, `AC-56d`, `AC-76`). Every requirement resolves to at least one acceptance criterion (107 declared `R-`, 98 declared `AC-`, 0 uncovered).
- All four Mermaid diagrams syntax-checked against spec prose, tables, and state transitions. No headless SVG renderer was run.
- Machine-output result record in Section 12.3.5 validated with `agent_schema.validate_agent_record` (0 errors).
- Clean worktree isolation maintained: all reviews, edits, and checks performed in `.aw/worktrees/refine-yfz5u9-iter7`.
- Leak checks passed via `check-local-leaks --agent` (0 findings).

### Iteration 7 stopping result

Material changes made; rerun warranted. The fourth independent cross-model review by Antigravity / Gemini 3.8 Flash High uncovered 3 high-severity issues (missing normative lifecycle requirement for research working documents, omission of the `aw synth prune` leaf command from the CLI table and acceptance criteria, and failure to handle total participant failure under `--allow-reduced`) as well as 4 medium and 4 low issues across setid resolution for read vs mutation verbs, dotted key path and typing rules for `config set`, attribution rules for verify assessments, packet token byte definitions with `read_factor`, companion revision retention definitions, top-level obligation item parsing, claims ledger consolidation in the ER diagram, and whitespace normalization for quote length limits. All 11 findings are resolved in the candidate spec.

## Iteration 8

| Field | Value |
| --- | --- |
| Subject | spec `yfz5u9`, `.aw/records/specs/draft/20261024-specflow-03-yfz5u9-spec-research-synthesis.spec.md` |
| Prompt | `khjc70` |
| Reviewer | OpenCode, host-reported model `uri/its_direct/pt3-claude-opus-5.5-1m-us` (reasoning setting not observable), in a NEW session that did not author iterations 1 to 3 in-context. Same model as the author: a self-review by model, not independent evidence. |
| Iteration | 8 of an operator-run loop. No cap was supplied. |
| Baseline | HEAD `87f0de31ee8bd02e2fa3b77509f6f15d79fe8ac7`; spec sha256 `bbf6ab5c8dec5aa5cca411d7d72ead8205ff71764daaaf6e625ccf274f72d65a`, 1748 lines, 107 requirement ids, 98 acceptance ids |
| Code drift since `def40d511` | none in `agent_workflows/` or `docs/` (two records-only commits). Every cited symbol was re-located in current source (`LANE_PERMISSION_POLICY`, `MAX_TURN_TIMEOUT`, `LANE_SUBMISSION_SUBDIR`, `_PROMPT_PIPELINE_MAP`, `derive_pipeline_positions`, `_next_order_for_set`, `plan_new`, `run_promote`, `run_set_outcome`, `probe_argv`, `MODEL_RE`, `validate_agent_record`, and others). |
| Result | 1 requirement id added (`R-25b`), 6 acceptance ids added (`AC-77` to `AC-82`), 0 removed. Revised: `R-25`, `R-36`, `R-41`, `R-47`/`R-48` (text only in R-48), `R-53`, `R-64`, `R-81`, `R-86`, `R-87`, `R-95`, `R-96`, `R-102`, `R-110`, `R-114`, `R-117`, Section 3.2 grammar, 3.4 formula, 6.3 states, reason table, 6.3.1 diagram and hard/soft lists, 6.6.1, 6.6.4, 6.6.5, 7.5 diagram, transcripts 12.3.1, 12.3.2, 12.3.3. Totals: 108 requirements, 104 acceptance criteria. Final sha256 `f8a6256ff20481783b355459120be2f6260a7b2d0d42568886952ff1d0573b9f`, 1798 lines. |

Iteration 1 to 7 findings (`RF-01` to `RF-86`): rechecked. One is reopened in effect: RF-25 closed the `accepted` route to a false clean label but left the `capped-clean` route (RF-87). No other reopened.

| ID | Status | Severity | Area | Defect and evidence | Correction | Blocks handoff |
| --- | --- | --- | --- | --- | --- | --- |
| RF-87 | new (extends RF-25) | high | Caps, R-33, R-36, R-64 (d), R-117 | `capped-clean` labelled a loop clean on the reviser's own word. R-33 obliges every valid revise to disposition every open material finding, so after any capped final iteration no finding is `open` and the outcome was always `capped-clean`, which R-64 (d) accepted for automatic `to-review`. Counterexample: quick mode (synth-refine cap 1), the one review finds 2 high findings, the revise marks them `fixed`, no review follows, the run finalizes clean. This is the "capped work mislabelled clean" failure the brief forbids, and it contradicts R-39 (a participant's statement is not read by a gate). | `capped-clean` renamed `capped-unverified` and defined as a soft limitation on the working document (R-36, R-64 (d), R-117, 6.3.1); warning `fixes-unverified` names the unchecked findings; cleared by `accept --by-human` (R-96); a clean verify dispatch on the final revision converts it to `converged` (R-48). Transcripts, inventory, quick-mode note, AC-19 updated. Choice recorded as nonblocking OQ-10 with alternatives. | yes |
| RF-88 | new | high | Recovery, R-25, R-95, 6.3 | The documented next action after a cap (`--from-run <run> --reuse refine`, Sections 6.3.3, 12.3.4, 12.3.5) is refused by R-95 `set-busy`: the old run is `capped`, which is non-terminal, and names the same setid. Nothing moved the old run to a terminal state, so its `active` intermediates and draft spec would stay in `aw attention` indefinitely. Also undefined: whether reused outputs are shared records or copies, and whether a reused candidate's open findings follow it. | New R-25b: the new run supersedes the old one (new terminal state `superseded`, intermediates `archive`/`informational`, old working spec `aw specs set superseded`, verified legal from `draft` with `--dry-run`); reused outputs are copied into new records with `reused-from`; open findings carry over with `was:` links. R-95 exempts the named old run. State table, state diagram, prune eligibility, status exit list, R-102 updated. AC-77, DL-19. | yes |
| RF-89 | new | high | Recovery, 6.3, R-86 | `leak-detected`, `identity-mismatch`, `catalog-missing`, `stage-failed`, `context-overflow`, and `stage-rejected-cap` stop the run in `waiting-for-human`, but R-86 defined how `resume` resolves only three reasons. For the other six there was no command that continues the run, so the R-103 `next_actions` could not be computed and the operator could only cancel. | Added a reason table in Section 6.3 (continuation, hard-block flag) and `resume --retry-stage`; R-86 and Table 3.6 list every refusal code (`retry-stage-required`, `use-from-run`). AC-81. | yes |
| RF-90 | new | high | Research evidence, R-114, 7.5 | The merged-claims citation check (CC2) runs before synth-refine, and nothing re-checks claims afterwards. A synth-refine revise could raise a claim to `high` or add a new claim with an unchecked source, and the final report would carry it at that confidence. The cap "not above any candidate's confidence" also cannot apply to a claim no candidate made. | R-114: finalize re-applies the caps to the final ledger; sources new or changed after the last check count `not-checked`; claims introduced in synth-refine carry `introduced-by: synthesis` and are capped `low`. No extra dispatch. Research flow diagram gains the finalize recheck node. AC-80. | yes |
| RF-91 | new | medium | Splitting, R-53, NN bound, ER | The integration review produces findings but had no record (assessments were one per (document, reviewer) pair, and the author is not the cross reviewer), no rule for who fixes them when the refine cap is 0 or N = 1, and the R-93 bound `4N + 7` did not count a second assessment per split candidate, so R-93 could under-reserve NNs. The 6.6.5 inventory showed no integration assessment. | R-53 places integration findings in an author-facet assessment and defines the revise; Q formula counts 2 per split candidate (examples unaffected, none split); bound recomputed to `6N + 7` (N = 12 gives 79); AC-51 rewritten (70 + 31 = 101 refused, 70 + 25 = 95 accepted); ER cardinality 0..2; 6.6.5 renumbered (spec now `09`). AC-82. | no |
| RF-92 | new | medium | Independence, R-41 | Blind labels were undermined by the inputs: candidate filenames carry D177 facets (`.agy.gemini38flashhigh.`) and research front matter carries `model`, `ace`, `participant`; the synthesizer reads input files by path (R-83). | R-41 requires inputs copied without front matter, filenames, or identity fields, assessments relabelled by subject. AC-78. | no |
| RF-93 | new | medium | Recovery, R-87 vs R-96 | `aw synth accept <run> <id6> --by-human` meant both "adopt a hand edit" (R-87) and "end the loop as accepted" (R-96), so adopting an edit could silently close the loop. | `accept --edit` for R-87; plain `accept` at `artifact-modified` exits 2 `accept-edit-required`; a human edit counts as a revise. Grammar, Table 3.6, reason table, AC-49. | no |
| RF-94 | new | medium | Research input, R-110 vs R-21 | R-110 requires `Questions`, but R-21 turns any unstructured brief into `B-1` with only a warning, and no exit code was defined for a research brief without questions. | R-110: exit 2 `research-questions-missing`; `brief-unstructured` fallback is spec-only; `--brief-text` is one question. AC-79. | no |
| RF-95 | new | medium | Protocol, R-102 vs Table 3.6 | R-102 mapped every `ready-to-finalize` to `ok`/exit 0, while Table 3.6 sends a start that stops with warnings to exit 1. `superseded`, `cancelled`, and `failed` had no mapping. | R-102: `ready-to-finalize` with a warning or pending soft limitation is `findings`, exit 1; `cancelled`/`superseded` `partial` exit 1; `failed` `error` exit 2. Three representative records validated with `validate_agent_record` (0 errors). Transcript 12.3.1 banner changed from OK. | no |
| RF-96 | new | medium | Execution, R-81, R-80 | The input directory is inside an ignored path (`.aw/state/`, confirmed with `git check-ignore`), so `git status` cannot see a participant rewriting its inputs, and inputs were not copied to the run directory, so a dispatch's inputs were not reproducible after worktree removal. The preview claimed `write-confinement: detected` without qualification. | R-81: inputs written to the run directory first, digests recorded, re-hashed after the dispatch (`inputs-modified`); writes in other ignored paths and outside the worktree stated as undetected. AC-72 updated. | no |
| RF-97 | new | low | CLI grammar | `--source-commit` (R-25, AC-16b) and `--allow-leaks` (R-06, AC-6) were used but not in Section 3.2. Found by diffing every `--flag` against 3.2. | Both added with defaults and validation. | no |
| RF-98 | new | low | Setid, 6.6.1, transcripts | "First 14 characters trimmed at a hyphen" did not define the result for a short slug; transcript 12.3.1 claimed `retrypol` was derived "from slug retry-policy", which no rule produces; a derived setid could equal the reserved word `last`. | Exact rule with examples; transcripts pass `--set`; `last` suffixed. | no |
| RF-99 | new | low | Naming matrix 6.6.4 | The "Live state" row had 6 cells in a 10-column table. | Row completed. | no |
| RF-100 | new | low | Requirement ids, FND-3 | `R-6`, `R-7`, `R-8` in FND-3 are spec `w15vzb` requirement ids but parse as dangling references to this spec's ids. | Qualified as `w15vzb` R-6 and so on. | no |

Checked and found sound this iteration (no change): D177 conformance of every attributed example name (type last, dot-free tokens, `reconciliation` with no ACE for multi-contributor records, single-author research final with author facets); the R-90/R-94 grammar gap is stated; `research-prompt` refuses hot status (`plan_transition_for_path`), matching the brief's statusless placement; `plan_new` mints repository-wide (`_mint_research_id6`); `set-outcome --consumed-by` is the owner verb for consumption; `aw specs new --date` takes `YYYY-MM-DD` and `aw group specs --date` takes `YYYYMMDD`; `agy --effort` accepts `low|medium|high|xhigh|max`; the four dispatch-arithmetic examples recomputed (29/87, 6/18, 3/9, 31/93, 9/27) and the 23-dispatch inventory adds up.

### Iteration 8 validation actually performed

- `aw specs check <spec> --agent`: `outcome: clean`, 1 checked, 0 findings.
- `production_checks.parse_spec_requirement_ids`: 108 requirement ids, 104 acceptance ids, 0 removed; every requirement is named by at least one acceptance criterion; the only unresolved `R-` tokens (`R-6`, `R-7`, `R-8`) are now explicitly `w15vzb` ids.
- All four Mermaid diagrams rendered to SVG with `@mermaid-js/mermaid-cli` 12.0.0 (`mmdc`, rc 0 each).
- Both `aw.agent/v1` examples in Section 12.3.5, plus three constructed records for the new R-102 mappings, validated with `agent_schema.validate_agent_record` (0 errors each).
- `aw specs set superseded yfz5u9 --dry-run` and `aw specs set parked ... --dry-run`: both transitions legal from `draft` (nothing written).
- `aw sanitize --agent`: `outcome: clean`, 6116 checked, 0 findings.
- Not checked: the D177 two-facet names cannot round-trip until R-90 exists (unchanged, stated in the spec). No implementation tests apply: the feature is unimplemented.

### Iteration 8 stopping result

Material changes made; rerun warranted. Four `high` findings were found in recovery and evidence paths
(cap labelling, `--from-run` hand-off, six unresolvable wait reasons, post-check claim edits) that seven earlier
iterations did not walk end to end. The new R-25b and the `capped-unverified` outcome change behaviour that other
sections depend on, so a further iteration, preferably by a different model family, should check them.
