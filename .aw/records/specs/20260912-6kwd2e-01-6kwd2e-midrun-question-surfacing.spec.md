# Spec: Surfacing a mid-run question to the human without stopping the queue

- Date: 2026-09-12
- Status: to-review
- Id: 6kwd2e
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Work-Kind: feature
- Scope: How a review or execute turn under `aw oc run` / `aw agy run` asks the human a question that did not exist before the turn: park the item, keep the queue moving, ask in bulk at the drain, and resume without discarding work.

## Workflow history

- 2026-09-12 created (aw specs): How a review or execute turn under a runner asks the human a question that did not exist before the turn: park the item, keep the queue moving, and ask in bulk.
- 2026-09-12 revised (author self-review, at the maintainer's request to stress-test the UX for review, execute, and mixed runs): SIX defects found and fixed, four of them found by reading the cited code rather than the prose. (1) R1.3 cited `prompt_for_gate_phrase` as the sweep prompt; that function is an EXACT-PHRASE ADMISSION GATE whose 10s timeout and "silence means refuse" contract (`runner_shared.py:2291-2296`) are both wrong for a free-text question needing thought. R1.3 now forbids reusing it, inherits its four safety constraints explicitly, and R1.3a additionally forbids the interrupt menu's unbounded `readline()`. (2) R1's pre-flight batch applied NO dedup or ordering, so a 74-plan run would have asked 74 serial questions before item 1 dispatched, which is the same wall R4 exists to remove; new R1.6 applies R4 to the sweep, and R1.7 makes a half-finished sitting durable. (3) The mixed review+execute case was unaddressed although the maintainer asked about it: new 0.35 states why the mechanism is uniform (isolation) and where it is NOT (cost of delay: a parked execute lane's base goes stale, a parked review is free), yielding R4.3a. It also records the honest current limit that no invocation can produce a mixed selection until `--type` lands. (4) Nothing bounded runaway escalation, so a broken prompt could park all 74 items and report NON-FAILURE; new R4b makes a high park ratio a diagnosed defect distinct from an ordinary parked run. (5) `fingerprint` was required but undefined: R4.1a makes it driver-computed and deterministic (a worker-supplied key would make dedup depend on 74 model judgements and would break host parity), R4.1b fails collisions toward asking separately. (6) R5.3 permitted unbounded ask-and-re-dispatch regress; R5.3a bounds it. Also: OQ-01 RESOLVED to `ready` rather than deferred, because leaving it open invited the harmful default of `blocked`, which would hide a parked item from the default attention view at exactly the moment a human could clear it. Criteria A16-A26 added for the new requirements; A6 strengthened to assert the preserved BASE, not only the commit.

## 0. Concepts (kept distinct)

Four distinctions carry every requirement below. Conflating any two produces a design that either
deadlocks a queue or silently degrades a review.

- **PRE-EXISTING QUESTION**: an `### OQ-*` block already present in an artifact when a run starts. It is
  visible to a pre-flight sweep and is what `aw attention`'s OQs column counts
  (`attention.py:85`, rendered `:1955-1971`).
- **EMERGENT QUESTION**: a question that does not exist until a turn runs. `/plan-review` Step 3.1
  requires collecting "questions created by findings", "instruction conflicts", and "decisions needed to
  repair or replan" (`plan-review.md:236-240`). None of these can be enumerated before the review that
  discovers them. THIS SPEC EXISTS FOR THIS CLASS.
- **PARKING**: ending a turn non-terminally with its question recorded and its evidence preserved, so the
  queue advances to other items. Distinct from blocking, which holds the queue.
- **ESCALATION**: the worker's judgement that a question is the HUMAN'S to decide rather than its own to
  resolve. Governed entirely by `askme` Step 1 (R2.5). Distinct from parking, which is the mechanical
  consequence: escalation decides WHETHER to ask, parking is HOW the queue survives it.
- **DRAIN**: the point after the queue has no dispatchable item left, where parked questions are asked in
  bulk. Distinct from run end: a drain may be followed by re-dispatch of parked items in the same run.

## 0.1 Actors

- **DRIVER**: `aw oc run` / `aw agy run`. Owns the queue, the run directory, lane lifecycle, and every
  decision about whether a human is present. Trusted.
- **WORKER**: the agent process for one turn. Emits questions; never asks them directly.
- **HUMAN**: answers at a time of their choosing, possibly hours after the run. Never a queue dependency.

## 0.2 The measured defect this spec repairs

`/plan-review` Step 3 (`plan-review.md:232-262`) is the asking step, and `:543` makes NO-GO fire on **any**
open question, not only `Blocking: yes`. Under a runner the worker has `question: deny` injected
(`lane_containment.py:749-752`), which removes the question tool from the model's schema entirely
(opencode `llm/request.ts:209-213` via `permission/index.ts:204-214`). The worker therefore has two moves:
resolve from evidence and record a `D-*` decision row, or leave the question open and return NO-GO.

Consequence, stated plainly: **a review under `aw` is systematically biased toward NO-GO, and the question
never reaches the human.** The same review run interactively asks and can reach GO. Measured 2026-09-12:
nine `to-review` plans (`planprio` x4, `nobugship` x4, `compinert` x1) each carry open questions and are
subject to this bias.

## 0.3 The constraint that rules out the obvious fix

A live blocking ask is the intuitive design and it is WRONG here, for three independent reasons. The
maintainer's operative scenario is a review of 74 IPDs in one run.

1. **HEAD-OF-LINE BLOCKING.** One question at item 6 strands the other 68 until a human returns to the
   console. Hours or days of throughput lost to one prompt.
2. **THE STALL WATCHDOG KILLS IT.** `DEFAULT_STALL_TIMEOUT = 600.0` (`oc_runipd.py:5008`); a child
   producing no output while a human thinks is killed with `StallTimeout` (`:5938-5942`). A live ask must
   fight this. Parking does not, because the child EXITS NORMALLY and writes its outcome JSON.
3. **IT NEEDS A PERMISSION RELAXATION.** A live ask requires undoing `question: deny`
   (`lane_containment.py:749-752`), whose rationale is a measured deadlock (`qyaime`, `v1ex5z`). Parking
   needs no permission change, because the question travels out through the outcome JSON that the worker
   already writes (`oc_runipd.py:4885-4900`).

Parking is therefore cheaper, safer, AND better UX than blocking. That coincidence is the spine of this
design.

## 0.35 Review turns, execute turns, and a mix of both

The design is uniform across both actions, and the two nonetheless differ in one way that changes an
ordering rule. Stated here because a reader who assumes symmetry will get R4.3 wrong.

**WHY THE MECHANISM IS UNIFORM.** A parked execute turn is safe for exactly the reason a parked review
turn is: worktree isolation. Its commits sit in its own lane, `EXECUTION_SUCCESS_STATES`
(`oc_runipd.py:337`) gates the merge so nothing reaches `main`, reclaim already preserves any non-empty
lane as a documented data-safety asymmetry (`:1708`), and `lane_preserved_for_missing_input`
(`:6795-6815`) plus the preserved-lane resolution at `:4414-4440` are a SHIPPED precedent for resuming
that exact work later. So execute needs no separate design, and it may in fact be the cheaper half to
wire, since review needs the dedup and re-review machinery built fresh.

**WHERE THEY DIFFER: THE COST OF DELAY IS NOT SYMMETRIC.**

- A parked REVIEW is nearly free to leave parked. It is read-only and re-runnable, so a late answer costs
  one cheap turn.
- A parked EXECUTE holds a lane with real commits against a FROZEN BASE. The longer it waits, the more
  likely `main` has moved underneath it, which turns a cheap resume into a merge problem. That staleness
  is a live, separately-tracked concern in this repository (pending plans `wmnmei`, "decide what a frozen
  begin base means once main has moved", and `3i0aaz` on ungated dirty-base cases). This spec does not
  solve base staleness; it MUST avoid making it worse.

**CONSEQUENCE (R4.3a).** In a run containing both, execute questions are asked BEFORE review questions at
equal unblock counts, because delay costs more there.

**CURRENT REALITY, stated so a reader does not over-build.** A single invocation cannot today produce a
mixed selection: discovery walks only the two plans trees and NEITHER host registers `--type`, so
`enforce_mixed_type_gate` (`runner_shared.py:2209`, called `oc_runipd.py:2881`) is reached on every run
and correctly does not apply. The gate's own call site records this honest limit
(`oc_runipd.py:2876-2880`). So R4.3a is a rule written NOW for a shape that becomes reachable when
`--type` lands; it costs one comparator and prevents a wrong default being chosen later by accident.

## 0.4 Constraints and dependencies

- Spec `25kzda` (approved) mandates front-loading: "Front-loading every question is the point; a second
  prompt after the first item has run defeats it" (`:278`). THIS SPEC DOES NOT CONTRADICT IT. Front-loading
  governs PRE-EXISTING questions, and R1 strengthens it. An EMERGENT question cannot be front-loaded
  because it does not exist yet; `25kzda` is silent on it, and this spec fills that gap rather than
  overriding it. `25kzda` also already defines `needs_input` (`:589`, `:1041`).
- Spec `7ckptx` (approved) R3.2 forbids prompting on missing input, because an unattended turn has no
  answerer (`lane_containment.py:1853-1856`). THIS SPEC HONORS IT: the worker never prompts. R7 keeps the
  unattended path fail-closed.
- `dependency-blocked` is the precedent for park-and-continue (`oc_runipd.py:324`, propagation `:4227`).
- `lane_preserved_for_missing_input` (`oc_runipd.py:6795-6815`) already preserves and pauses a lane "so its
  evidence is not destroyed", and `:4414-4440` already resolves `preserved_lane_id`/`preserved_base`/
  `preserved_branch` as the MOST authoritative source when a later turn resumes that work.
- Ledger kinds `question_raised`, `human_answer`, `question_disposition` already exist with shapes
  (`run_ledger_schema.py:222-235`), the disposition `answered_by_human` (`:107`), and an enforced rule that
  a `human_answer` MUST carry `actor == "human"` (`:446-451`).
- `set_records.render_open_questions` (`:86-92`) already renders raised-minus-answered.
- `set_state.SET_WAITING_INPUT` (`:29`) exists with a `human_answer_recorded` resume predicate (`:92-107`).
- `run_gates.py` exists entire, with `GATE_STATUS_NEEDS_INPUT` (`:31`) and a headless path returning
  `needs_input` before any side effect (`:154-164`). Unwired to both runners.

Honest statement of novelty: this spec invents almost nothing. It WIRES existing, tested vocabulary that
no runner currently reaches.

## 1. Goals

1. A question a worker discovers reaches the human, instead of being converted into a NO-GO the human
   never sees.
2. A queue of N items with K parked questions still processes the other N-K items in the same run.
3. The human answers asynchronously and is never a queue dependency.
4. A parked item's work is never destroyed and never merged.
5. The number of prompts the human faces is proportional to DISTINCT questions, not to items.
6. A question is discoverable WHILE the run is still going, not only after it ends.
7. Only questions that are genuinely the human's to decide are escalated at all.

## 2. Non-goals

- A live mid-turn interactive prompt. Refused, per 0.3.
- Relaxing `question: deny`. Not required by this design, and left in place.
- Answering a question on the human's behalf under automation. R7 forbids it.
- A remote or web answering surface. The answer carrier is a file in the run directory; a richer surface
  may be built later on the same carrier.
- Changing what `/plan-review` considers a NO-GO. R6 changes only whether the question SURFACED first.

## 3. Requirements

### R1. Pre-flight sweep of pre-existing questions

- **R1.1** Before dispatching any item, the driver MUST collect every unresolved `### OQ-*` block across
  every artifact in the resolved queue and, when a human is present (R7.1), ask them in one batch.
- **R1.2** The default scope MUST be every question that gates progress, not only `Blocking: yes`. Basis:
  `plan-review.md:543` NO-GOs on ANY open question, so a non-blocking OQ also gates progress, and a
  blocking-only sweep would leave the measured nine plans of 0.2 untouched. A `--blocking-only` flag MAY
  narrow it.
- **R1.3** The sweep MUST use a BOUNDED prompt and MUST NOT use an unbounded read.
  **IT MUST NOT REUSE `prompt_for_gate_phrase`** (`runner_shared.py:2269-2325`), and the reason is a
  semantic mismatch that would be silent and wrong. That function is an ADMISSION GATE: it captures a
  line for an EXACT-PHRASE comparison, its timeout is `GATE_PROMPT_TIMEOUT = 10.0` (`:2266`, chosen to
  match the lane prompt), and its contract is that "an unanswered prompt falls through... a timeout can
  only ever produce the same outcome as the unattended path - it can never grant an admission"
  (`:2291-2296`). Both properties are wrong here. Ten seconds is not a human-scale interval for a
  question that requires thought, and "silence means refuse" is meaningless for free text, where the
  correct reading of silence is "not answered yet" (which is PARKING, per R3).
  A new prompt is therefore required, inheriting the four hard constraints of
  `prompt_for_gate_phrase`'s docstring (`:2285-2299`) unchanged: no TTY means no prompt; `select` with a
  bounded timeout and never a plain read; an unanswered prompt falls through; the automatic decision
  remains the authority. It MUST differ in exactly three ways: it captures FREE TEXT rather than an
  exact phrase, its timeout is human-scale and configurable, and falling through means PARK the
  question rather than REFUSE the artifact.
- **R1.3a** The sweep MUST NOT use the unbounded `readline()` of the interrupt menu
  (`runner_stop.py:1876`). That call is safe only because it runs in a signal handler with the human
  demonstrably at the keyboard; its own safety predicate calls the site "STRICTLY MORE DANGEROUS" than
  the measured 1h49m wedge (`runner_stop.py:1798-1807`). A pre-flight sweep has no such guarantee.
- **R1.4** The sweep MUST run at the existing pre-flight gate seam, beside `enforce_draft_admission_gate`
  (`oc_runipd.py:2801-2806`, `agy_runipd.py:1848-1853`), so all front-loaded prompts occur together as
  `25kzda:278` requires.
- **R1.5** An answer recorded by the sweep MUST be written to the artifact durably, per `askme.md:208-224`:
  set `- Status: resolved` with a rationale naming the human and date, leave `- Blocking:` unchanged, and
  never record an answer only under the gitignored run directory.
- **R1.6** The sweep MUST apply R4 (dedup by fingerprint, one answer applied to every raiser, ordering by
  unblock count, and reporting the shape of the sitting) TO ITSELF. Without this, a 74-plan run asks 74
  questions serially before item 1 dispatches, which is precisely the wall R4's rationale calls "moving
  the wall the design exists to remove". The pre-flight ask is where dedup matters MOST, not least: at
  pre-flight EVERY item is still unstarted, so every answer is maximally valuable and the ordering
  decides how quickly the run can begin doing useful work.
- **R1.7** The sweep MUST be interruptible without losing answers already given. Each answer MUST be
  recorded durably (R1.5) BEFORE the next question is asked, which is the same rule `askme` Step 3 already
  imposes so an interrupted session loses nothing (`askme.md:174-181`). A human who answers four of
  fifteen questions and walks away MUST keep those four, and the run MUST proceed with the remaining
  eleven parked rather than discarding the sitting.

### R2. The emergent-question carrier

- **R2.1** A worker that discovers a question it cannot resolve from evidence MUST record it in the outcome
  JSON it already writes (`oc_runipd.py:4885-4900`), in a `questions[]` array, and MUST exit normally.
- **R2.2** Each entry MUST carry: a stable `question_id`, the question text, the artifact `id6`, whether it
  gates the verdict, a `fingerprint` (R4.1), and the evidence the worker already consulted.
- **R2.3** The worker MUST NOT block, MUST NOT prompt, and MUST NOT wait for an answer. This is
  `7ckptx` R3.2 applied unchanged.
- **R2.4** The carrier MUST be the outcome JSON, NOT a new stdout token. Rationale: the outcome JSON is
  already parsed on both hosts and already schema-versioned, whereas a token needs a parser per host. The
  `AW_MISSING_INPUT` token (`lane_containment.py:86-87`) remains the carrier for its own distinct case and
  MUST NOT be overloaded; `MissingInputDecision` is deliberately incapable of granting (`:1482-1489`).
- **R2.5** A worker MUST classify every question with the three-way sort of `askme` Step 1
  (`askme.md:131-162`) BEFORE escalating any of it, and MUST escalate only the "THE HUMAN'S TO DECIDE"
  pile. That sort is the single source for this decision and MUST NOT be restated here or in a prompt,
  so the two cannot drift. Three parts of it are load-bearing and are named because omitting any one
  produces either a prompt storm or a silent guess:
  - **MEASURE, DO NOT ASK.** If the owning artifact states a rule that becomes decidable once a
    measurement is taken, the work is to MEASURE and apply the rule, not to ask. This test is FIRST
    because it is the cheapest way to avoid the worst outcome, and it exists from a measured failure:
    on 2026-09-08 a prompt was composed asking the maintainer to choose between two retry approaches
    when the plan's own open question already stated the rule and the deciding measurement had already
    been taken (`askme.md:139-148`). The question was answered before it was asked.
  - **A LEAN IS NOT A DECISION.** An artifact expressing a preference or a hunch has decided nothing,
    and treating it as a decision is the opposite failure (`askme.md:149-154`).
  - **WHEN GENUINELY UNSURE ON A BLOCKING QUESTION, ASK** (`askme.md:161-162`). Silently downgrading a
    question its author marked load-bearing is the failure that rule exists to stop.
- **R2.6** A worker that resolves a question itself MUST still record a `D-*` decision row
  (`plan-review.md:246-262`). R2.1 adds a path for the genuinely unanswerable question; it does not
  license asking instead of thinking, and R2.5's sort is what keeps the escalated set small.

### R3. Park and continue

- **R3.1** An item whose turn reported questions MUST receive a NON-TERMINAL disposition
  `awaiting-human`, distinct from every state in `TERMINAL_STATES` (`oc_runipd.py:317-335`) and distinct
  from `blocked` (which is terminal and overloaded).
- **R3.2** The driver MUST continue dispatching every other satisfiable item. Parking one item MUST NOT
  end the run.
- **R3.3** `awaiting-human` MUST NOT be in `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:337`), so a parked
  item's work can never merge to main.
- **R3.4** A parked item's lane MUST be preserved and paused, reusing the shipped path of
  `lane_preserved_for_missing_input` (`oc_runipd.py:6795-6815`) and recording `preserved_lane_id`,
  `preserved_base`, and `preserved_branch` so `:4414-4440` resolves the same lane on resume.
- **R3.5** Parking MUST propagate to dependents, because a dependent of an unanswered artifact cannot be
  reviewed or executed honestly. Reuse the reverse-edge fixed-point propagation of `:4227-4281`.
- **R3.6 (FAIL-OPEN HAZARD, stated because the analogous code does the opposite).** When no queued item is
  satisfiable, the existing selection loop marks EVERY remaining item `dependency-blocked` and BREAKS out
  of the run (`oc_runipd.py:352`). A drain caused by parked questions MUST NOT be treated as run failure
  and MUST NOT mark unrelated items blocked. Getting this wrong reproduces exactly the head-of-line stall
  this spec exists to prevent.

### R4. Deduplicate and order before asking

- **R4.1** Questions MUST be deduplicated ACROSS the queue by a `fingerprint`, not only within one
  artifact. `plan-review.md:236` already requires within-artifact dedup; a Set of sibling plans mostly asks
  the same few questions, so cross-artifact dedup is where the UX is won or lost.
- **R4.1a (THE FINGERPRINT IS DRIVER-COMPUTED, NOT WORKER-SUPPLIED).** The driver MUST compute the
  fingerprint from the question's normalized text plus the decision it asks for. A worker MAY propose one,
  and the driver MUST NOT trust it. Two reasons, both load-bearing: a worker-supplied fingerprint makes
  dedup depend on 74 independent model judgements, which is exactly the kind of non-determinism that makes
  a UX guarantee unenforceable; and R8.1 requires host parity, which is impossible if each host's model
  invents its own key. Normalization MUST be deterministic and MUST be defined in ONE place shared by both
  hosts.
- **R4.1b** Fingerprint collisions MUST fail toward ASKING SEPARATELY. Merging two genuinely different
  questions applies one human answer to a decision the human never considered, which is a wrong answer
  carrying their name; asking one extra question merely costs a prompt. When the driver cannot decide,
  it MUST NOT merge.
- **R4.2** One human answer to a deduplicated question MUST apply to every artifact that raised it, and the
  answer record MUST name every artifact it was applied to, so a later reader can see the blast radius of
  one decision.
- **R4.3** The bulk ask MUST be ordered by how many parked items each answer unblocks, descending, so the
  first answers free the most work.
- **R4.3a** Where unblock counts are equal, EXECUTE questions MUST be asked before REVIEW questions, per
  the cost-of-delay asymmetry of 0.35: a parked execute lane's base goes stale while it waits, whereas a
  parked review is re-runnable at any time for the same cost.
- **R4.4** The bulk ask MUST report, BEFORE the first question, the number of distinct questions, the
  number of artifacts affected, and the unblock count of each question, so the human can see the shape of
  the sitting and decide whether to start it now or later. A sitting whose size is unknown until it ends
  is one a human will abandon midway.

Rationale for R4 as a REQUIREMENT and not a nicety: asking 74 questions serially at the drain merely moves
the wall the design exists to remove.

### R4a. Mid-run visibility (a question announces itself when it is parked, not when the run ends)

THE DEFECT THIS PREVENTS, stated because the first draft of this spec had it. A human starts a 4-hour
run and leaves. Questions park at 0:15, 1:30 and 2:45. If questions surface only at the DRAIN, the human
returns at 3:00, sees a run still working, and has no signal that three questions are waiting. Worse, each
parked item parks its dependents (R3.5), so the run may be doing far less useful work than its progress
display implies. A question that exists and is invisible is the same as a question never asked.

- **R4a.1** The driver MUST write the open-questions projection AT THE MOMENT an item parks, not at the
  drain. The renderer already exists (`set_records.render_open_questions`, `:86-92`, computing
  raised-minus-answered from `question_raised` records) and the file name is already defined
  (`set_records.OPEN_QUESTIONS_FILE`, `:42`). This requirement is about WHEN it is written.
- **R4a.2** `aw runs questions` MUST therefore work against an IN-FLIGHT run. It already reads that
  projection and already returns exit 0 for open, 1 for none, 2 for missing (`run_cli.py:138-152`), so
  satisfying R4a.1 satisfies this; a test MUST pin it so a later change cannot make the verb
  drain-only.
- **R4a.3** The runner statusline MUST carry a live count of parked questions, so the signal is visible
  on the console the human walked away from. Extend `format_statusline`
  (`render_stream.py:1117-1133`); do not invent a second status surface.
- **R4a.4** The driver MUST emit a terminal bell on the FIRST park of a run, and MUST NOT repeat it per
  question. Rationale: there is currently NO notification surface anywhere in the runners (verified
  2026-09-12: no bell, no `notify-send`, no hook), and for an unattended multi-hour run one byte is the
  difference between noticing at 0:15 and at 4:00. Once per run, because a bell per question in a
  74-item queue is noise the human will suppress, which would defeat the purpose.
- **R4a.5** The bell MUST be suppressed when the output stream is not a TTY, and MUST be suppressed by
  the presentation override flags that already govern runner output. A bell written into a pipe or a CI
  log is corruption of that log, not a notification.
- **R4a.6** `aw attention` MUST surface a nonzero parked-question count for an active run, so the
  standing "what needs attention?" view answers this question without the human knowing to run a
  run-specific verb. The item MUST map to the cross-tree class `ready`, not `blocked`, per the ruling in
  OQ-01: a parked question is something a human can clear NOW, and classing it `blocked` would hide it
  from the default view at exactly the moment it is actionable.

### R4b. A runaway escalation is a defect, not a workload

THE FAILURE THIS PREVENTS. A prompt regression, a misread instruction, or a model that has learned to ask
rather than think can make EVERY worker escalate. Without a bound, a 74-item run parks all 74, does zero
useful work, and (per R7.3) reports a NON-FAILURE exit. The human returns to 74 questions and no progress,
with nothing telling them the cause was systemic. Worse, they may start answering, which spends hours
servicing a bug.

The diagnosis matters: a run in which nearly everything escalates is evidence that the WORKER'S
CLASSIFICATION (R2.5) is broken, not evidence that the human owes 74 decisions.

- **R4b.1** The driver MUST bound the proportion of dispatched items that may park before it stops
  dispatching, with a configurable threshold and a conservative default.
- **R4b.2** On breaching the threshold the driver MUST stop dispatching, MUST report the breach naming the
  observed ratio, and MUST state explicitly that a runaway escalation rate is more likely a defect in the
  prompt or the worker's classification than a genuine backlog of human decisions.
- **R4b.3** A breach MUST be a distinct outcome from the ordinary parked-run exit of R7.3. R7.3 says "some
  questions are waiting, this is normal"; a breach says "this run is not working, do not start answering".
  Reporting both identically would hide the defect inside the feature.
- **R4b.4** A breach MUST NOT discard any work: items already parked keep their preserved lanes (R3.4) and
  their recorded questions, and the answer file is still written. Stopping dispatch is not a rollback.
- **R4b.5** The threshold MUST NOT apply to a queue too small to distinguish a runaway from a coincidence.
  A minimum absolute count is required alongside the ratio, so a 2-item run with 1 parked item is not
  diagnosed as systemic.

### R5. The drain, and the asynchronous answer file

- **R5.1** When no item is dispatchable and parked questions exist, the driver MUST write them to a durable
  answer file in the run directory, deduplicated and ordered per R4.
- **R5.2** The file MUST be human-editable, MUST identify each question by `question_id`, and MUST state
  the exact command that resumes the run.
- **R5.3** When a human is present (R7.1), the driver MUST additionally offer the bulk ask at the terminal,
  and on completion MUST re-dispatch the parked items IN THE SAME RUN.
- **R5.3a (THE REGRESS MUST BE BOUNDED).** A re-dispatched turn may discover NEW emergent questions, which
  would park it again. The number of ask-and-re-dispatch rounds within one run MUST be bounded, with a
  low default. On reaching the bound the driver MUST stop re-dispatching, leave the remaining items parked,
  and write the answer file. Rationale: an unbounded loop can hold a human at the console indefinitely,
  answering questions generated by their own previous answers, which is a worse experience than being told
  to come back. A second round is usually legitimate (the answer changed the plan); a fifth is evidence the
  artifact needs authoring work, not more answers.
- **R5.4** Every answer MUST be recorded as a `human_answer` ledger record with `actor == "human"`, honoring
  the existing rule that consent is never synthesized (`run_ledger_schema.py:446-451`), and MUST resolve via
  disposition `answered_by_human` (`:107`).
- **R5.5** A resumed turn MUST receive the answers for its artifact in its prompt.
- **R5.6 (STALENESS).** An answer MUST record the artifact content hash it was given against. If the
  artifact changed materially since, the driver MUST surface the answer as STALE and MUST NOT silently
  apply it. A stale answer applied to a rewritten plan is a wrong answer with a human's name on it.

### R6. Verdict semantics

- **R6.1** A parked question MUST NOT be recorded as a NO-GO readiness. `awaiting-human` means the question
  has not been ASKED yet; NO-GO asserts a reviewed plan is not ready. Conflating them is the bias of 0.2.
- **R6.2** After answers are applied and the item is re-reviewed, the verdict MUST be computed normally,
  including NO-GO if warranted.
- **R6.3** No agent may write a `- Readiness:` value for a review it did not perform. This restates the
  standing prohibition and is listed because this design introduces a second review round where the
  temptation is new.

### R7. Unattended runs stay fail-closed

- **R7.1** Human presence MUST be decided by the existing predicate `runner_shared.is_interactive_run`
  (`:2184-2206`), which already returns false under `--unattended`/`--full-auto` EVEN WITH a TTY.
- **R7.2** Under automation the driver MUST NOT ask, MUST NOT synthesize an answer, and MUST NOT infer one
  from a default. It parks, writes the answer file, and exits cleanly. Basis: `askme.md:226-236`,
  `run_gates.py:154-164`, and `25kzda:1118` ("A TTY prompt records presence, not organizational identity").
- **R7.3** A run whose only incomplete items are `awaiting-human` MUST exit with a distinct, non-failure
  status naming the count of parked items and the answer file path.

### R8. Host parity

- **R8.1** Both runners MUST implement identical behavior. The carrier is the outcome JSON, which both
  already parse, so parity costs no host-specific parsing.
- **R8.2** Antigravity has NO permission lever (`lane_containment.py:729-733`) and runs with
  `--dangerously-skip-permissions` (`agy_runipd.py:2738-2739`). Because R2.4 uses the outcome JSON rather
  than a permission-gated tool, this asymmetry does not affect the design. Stated explicitly so a future
  reader does not "fix" it by relaxing a permission.

## 4. Testable acceptance criteria

- **A1** (R1.1, R1.2) A queue containing the nine measured plans of 0.2 produces a pre-flight batch
  containing all their open questions, including `Blocking: no` ones. A `--blocking-only` run asks none of
  them.
- **A2** (R1.3) The sweep prompt returns on timeout without an answer and does not call `input()`. Assert
  by patching the clock, not by waiting.
- **A3** (R2.1, R2.3) A worker fixture writing `questions[]` and exiting 0 is parked; assert the child was
  not killed and no `StallTimeout` was raised.
- **A4** (R3.2) A 10-item queue where item 3 parks completes the other 9 in the same run.
- **A5** (R3.3) A parked item's branch is never merged to main; assert main's head is unchanged.
- **A6** (R3.4, R5.5) A parked execute turn with a commit in its lane resumes on the SAME lane, with the
  commit still present, the SAME recorded `preserved_base`, and the answer in its prompt. Asserting the
  base too, not only the commit, because the base is where staleness (0.35) would bite unnoticed. This is
  the criterion that proves the maintainer's isolation argument.
- **A7** (R3.5) A dependent of a parked item is itself parked, to a fixed point, with a reason naming the
  upstream question.
- **A8** (R3.6) A queue drained entirely by parked questions exits non-failure, and no unrelated item is
  marked `dependency-blocked`. This is the regression test for the fail-open hazard.
- **A9** (R4.1, R4.2) 74 artifacts raising the same fingerprint produce ONE prompt, and one answer resolves
  all 74.
- **A10** (R4.3) Ordering is by unblock count descending, asserted on a fixture with known counts.
- **A10a** (R2.5) A worker fixture given a question whose owning artifact states a rule decidable once
  measured does NOT escalate it: it measures, applies the rule, and records a `D-*` row. This is the
  2026-09-08 failure of `askme.md:139-148` as a regression test.
- **A10b** (R2.5) A worker fixture genuinely unsure on a `Blocking: yes` question DOES escalate it.
- **A10c** (R4a.1, R4a.2) `aw runs questions` against a run with one item parked and the queue still
  advancing prints that question and exits 0. This is the 4-hour-gap regression test: assert MID-RUN,
  never after the drain.
- **A10d** (R4a.3) The statusline of a run with 3 parked items reports 3.
- **A10e** (R4a.4) The bell is emitted once on the first park and not again on the second or third.
- **A10f** (R4a.5) With the output stream not a TTY, no bell byte appears anywhere in the captured output.
- **A10g** (R4a.6) `aw attention` reports a nonzero parked-question count for an active run holding one.
- **A11** (R5.4) An answer written with a non-human actor is refused by the existing ledger rule.
- **A12** (R5.6) An answer given against artifact hash H, applied after the artifact changes to H', is
  reported STALE and not applied.
- **A13** (R6.1) A parked item carries no `- Readiness: no-go`.
- **A14** (R7.2) With `--unattended` AND a TTY present, no prompt is emitted, no answer is synthesized, and
  the answer file is written.
- **A15** (R8.1) The same fixture parks identically on both hosts.
- **A16** (R1.3) The sweep prompt captures a free-text answer, and its timeout is NOT
  `GATE_PROMPT_TIMEOUT`. Assert the distinct value, so a later refactor cannot quietly collapse the two
  prompts back together and reintroduce a 10-second window on a question requiring thought.
- **A17** (R1.6) A pre-flight sweep over 74 artifacts sharing one fingerprint asks ONE question, not 74.
  The pre-flight twin of A9, asserted separately because the first draft applied dedup only at the drain.
- **A18** (R1.7) A sweep interrupted after the 4th of 15 answers retains all 4 durably in their artifacts,
  and the run proceeds with 11 parked.
- **A19** (R4.1a) Two hosts given the identical question text compute the identical fingerprint, and a
  worker-proposed fingerprint that disagrees is ignored.
- **A20** (R4.1b) Two questions the driver cannot confidently merge are asked separately.
- **A21** (R4.3a) In a queue holding a parked review and a parked execute with EQUAL unblock counts, the
  execute question is asked first.
- **A22** (R4b.1, R4b.2) A fixture in which every worker escalates stops dispatching at the threshold and
  reports the observed ratio with the systemic-defect diagnosis.
- **A23** (R4b.3) A threshold breach and an ordinary parked-run completion produce DISTINGUISHABLE exit
  reporting.
- **A24** (R4b.4) After a breach, every already-parked item still has its preserved lane and its recorded
  question, and the answer file exists.
- **A25** (R4b.5) A 2-item run with 1 parked item does NOT breach.
- **A26** (R5.3a) A fixture whose re-dispatched turns always raise a new question stops after the bounded
  number of rounds and writes the answer file, rather than looping.
- **A27** (R1.3a) No sweep code path reaches an unbounded read. Assert statically (no `readline()` or bare
  `input()` in the sweep module) as well as behaviorally, because the failure mode is a silent hang.
- **A28** (R1.4) The sweep runs at the pre-flight seam: assert it completes BEFORE the first item is
  dispatched and after selection resolves.
- **A29** (R2.2) An outcome JSON entry missing any required field is rejected with a diagnostic naming the
  field, rather than being silently dropped. A dropped question is an unasked question.
- **A30** (R2.4) A worker emitting an `AW_MISSING_INPUT` token is handled by the missing-input path and is
  NOT treated as a question, and vice versa. The two carriers stay distinct.
- **A31** (R2.6) A worker that resolves a question from evidence records a `D-*` row; assert the row exists
  and cites a source.
- **A32** (R3.1) `awaiting-human` is absent from `TERMINAL_STATES` and from every success set. Assert
  against the actual constants on both hosts, so a later edit cannot make a parked item terminal.
- **A33** (R4.4) The pre-ask summary states the distinct-question count, the affected-artifact count, and
  each question's unblock count, BEFORE the first question is rendered.
- **A34** (R5.1, R5.2) The answer file exists, identifies each question by `question_id`, and contains the
  literal resume command. Assert the command actually runs (spawn it in a fixture), because a documented
  command that does not work is the usability failure `DEPENDENCY_BLOCK_RECOVERY_HINT`
  (`oc_runipd.py:342-357`) exists to prevent.
- **A35** (R5.3) With a human present, answering at the drain re-dispatches the parked items in the SAME
  run; assert no second invocation was needed.
- **A36** (R6.2) A re-reviewed item whose answer does not clear the underlying finding still receives NO-GO.
  Answering a question is not approval.
- **A37** (R6.3) A re-review round writes no `- Readiness:` value it did not itself earn; assert no
  unattested value appears after a parked-then-resumed cycle.
- **A38** (R7.3) A run whose only incomplete items are parked exits with the distinct non-failure status,
  naming the parked count and the answer file path.
- **A39** (R8.2) The antigravity path parks correctly WITHOUT any permission configuration, proving the
  design does not depend on a lever that host lacks.

## 5. Alternatives rejected, and why

- **Live mid-turn pause and ask.** Rejected per 0.3: head-of-line blocking on the 74-IPD case, a fight with
  the 600s stall watchdog, and a permission relaxation none of the rest of the design needs. It was the
  author's initial recommendation and the maintainer's throughput objection defeated it.
- **Pre-flight sweep alone.** Insufficient. It structurally cannot ask an EMERGENT question
  (`plan-review.md:236-240`), which is the class 0.2 is about. Retained as R1 for the questions it CAN ask.
- **A new stdout token (`AW_ASK_HUMAN:`).** Rejected per R2.4: needs a parser per host, whereas the outcome
  JSON is already parsed and versioned on both.
- **Fixing verdict semantics only** (stop NO-GOing on evidence-resolved questions). Rejected as
  insufficient alone: it lets an `aw` review reach GO but the human still never sees the question. R6 keeps
  the useful half.
- **Auto-triggering `/askme` before a run.** Rejected: `askme` is an ATTENDED serial workflow whose Step 5
  explicitly refuses to act under a runner (`askme.md:226-236`). Invoking it from a runner would violate
  its own contract. R1 implements the front-loading intent natively instead.

## 6. Open questions

### OQ-01: Should a parked question be visible in `aw attention` as its own class, or fold into `blocked`?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-12 from repository evidence, not deferred, because
  leaving it open invites the harmful default. `aw attention` maps a native status onto a cross-tree class,
  and the two candidates are not equally correct. `blocked` means the item cannot proceed until something
  else happens; `ready` means someone can act NOW. A parked question is the definition of the latter: the
  ONLY thing it needs is a human decision, and the human is the reader of that view. Classing it `blocked`
  would hide it from the default view precisely when a human could clear it, reintroducing the invisibility
  defect R4a exists to fix. RULING: `awaiting-human` maps to `ready`, and R4a.6's count is what makes it
  actionable. Recorded here rather than left to whoever wires the status map, which is how the wrong default
  would have been chosen silently.

### OQ-02: Does the pre-flight sweep of R1 also cover specs and backlog items, or plans only?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: a run's queue is plans, so plans-only is coherent and complete. But a
  spec carrying an open question that a queued plan depends on is a real gate, and `aw attention` already
  shows OQ counts for specs. Non-blocking because plans-only ships correct behavior for the measured
  defect and widening the scope later adds a source, not a redesign.
