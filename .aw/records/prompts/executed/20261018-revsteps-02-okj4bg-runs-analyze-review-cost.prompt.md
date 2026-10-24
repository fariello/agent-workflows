<!-- aw-prompt: Kind: run-once | Id: okj4bg | Set: revsteps | Status: executed | Created: 2026-10-18 | Author: opencode (pt3-claude-opus-5.5) . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
# Add review-cost and experiment breakdowns to `aw runs analyze`

## Purpose

The maintainer is redesigning how the runners (`aw oc run`, `aw agy run`) review plans. Review is
about half of all recorded agent cost. The redesign will be decided by an experiment that runs the
same plans through different review variants and models. `aw runs analyze` and `aw runs query` must
be able to answer the questions in Section 3. Today they cannot answer most of them.

Your task: extend `aw runs analyze` (and the `aw runs query` views it feeds) so that each question in
Section 3 can be answered from data the runners ALREADY record. Where the data is not recorded,
do not invent it. Report it as missing (Section 5).

## 1. Facts already established (verify them before relying on them)

These were measured on 2026-10-17 in this checkout by reading run directories directly, not
through `aw runs analyze`. Re-check each one against the current code and data. If a fact is wrong,
say so in your report and use the correct behavior.

Run directory layout: `.aw/records/runs/<run-id>/`.

- `state.json`:
  - `queue`: one entry per queued item, with `id6`, `action` (`review`, `execute`, `plan`, ...),
    `position`, and `attempts`. 1,433 attempt records carry an `attempts[].model` value.
  - `options.model`: set in 336 of 533 runs.
  - `session_id`, `session_turn_counts`, `set_sessions`: session bookkeeping.
  - `driver`: the driver file path, its SHA-256, and a code fingerprint. There is no git commit and
    no user label.
- `sessions/<NN>-<id6>-attempt-<k>.jsonl`: the host's event stream for one attempt. `NN` is the
  queue position. A `-verify.jsonl` suffix marks a verifier turn, not the attempt itself. For
  OpenCode these lines are JSON objects with a `type` field:
  - `step_finish`: one per model step. `part.tokens` holds `input`, `output`, `reasoning`, and
    `cache.read` / `cache.write`. `part.cost` is the step cost in USD. Top-level `sessionID` names
    the host session.
  - `tool_use`: one per tool call. `part.tool` is the tool name (`bash`, `read`, `edit`, ...),
    `part.state.input` holds its arguments, and `part.state.output` holds its output text.
  - `step_start` and `text` are also present.
- `telemetry/*.jsonl`: per-execution start and end events. The `tool_versions.agent_workflows`
  field carries the package version, which includes the git commit as `+g<hash>` (example:
  `1.3.0rc2.dev11216+g8c054f848`). It is present in 292 of 533 runs.
- `events.jsonl`: run events. Relevant names seen: `defect-report-recorded` (1,071),
  `ipd-turn-retry`, `ipd-finalize-refused`, `ipd-begin-refused`, `clean-base-refused`.
- Antigravity runs (170) record tokens for 127 runs but cost for none.

A direct measurement over 1,311 OpenCode review attempts (one attempt = one session file above,
excluding `-verify` files, for queue items whose `action` is `review`) produced:

| Measure | Value |
| --- | --- |
| Total tokens | 16.05 billion (12.2 million per attempt on average) |
| Share of tokens that are cache reads | 98.8 percent |
| Median per attempt: cache-read tokens | 10.96 million |
| Median per attempt: new input tokens | 72,000 |
| Median per attempt: output tokens | 31,000 |
| Median model steps per attempt | 50 (90th percentile 112) |
| Median context size at the last step | 234,000 tokens |
| Recorded cost | $10,528 total, $7.83 median |
| Attempts in a session new to the run | 404, first-step context median 36,000, cost median $9.21, steps median 81 |
| Attempts in a session already used by an earlier item | 907, first-step context median 229,000, cost median $6.78, steps median 43 |
| Tool output bytes | `bash` 71 percent, `read` 27 percent |

The conclusion the redesign depends on: review cost is roughly the number of model steps
multiplied by the context size at each step, because each step re-sends the whole conversation and
the host bills it as a cache read. `aw runs analyze` should make that visible directly.

## 2. Constraints

- Follow `AGENTS.md`, including the execution contract (commit with `aw commit`, never push, paste
  real test output) and the rule against code-pinning tests: test by running the analysis on fixture
  run directories and asserting on the output.
- `aw runs analyze` writes only inside the gitignored analytics namespace. Keep it that way.
- Keep `aw runs query` bounded and allowlisted (no free-form expressions). Add new fields to the
  allowlists instead.
- Keep the existing refusal behavior for under-powered slices. Do not lower thresholds to produce
  numbers.
- Do not change how runners record data unless Section 4 requires it. If a question needs data
  that is not recorded, list it in your report (Section 5) instead of adding recording code,
  unless the change is a small, isolated addition to the run records. If you add recording, say
  exactly what you added and from which commit it is available.
- Do not invent prices. For runs with tokens but no cost, report tokens. A dollar estimate is
  allowed only when it is labeled as an estimate and names the price table used.

## 3. Questions the analysis must answer

For each question, add the grouping fields, metrics, or view needed, and make the HTML report show
it where useful.

1. **Token composition.** Per phase (review, execute, verifier, recovery), and per attempt: new
   input, cache-read, cache-write, output, and reasoning tokens, separately. Report each one's
   share of total tokens and, where cost exists, its share of cost. Today `token_total` hides that
   98.8 percent of review tokens are cache reads.
2. **Steps and context.** Per attempt: number of model steps, context size at the first step and
   at the last step (context = input + cache read + cache write for that step), and the maximum.
   Show cost against step count (for example by buckets of 25 steps).
3. **Session reuse.** Per attempt: whether its host session was new to the run or already used by
   an earlier queue item, and the context size it started with. This is needed to decide whether
   each plan review should get a fresh session.
4. **Tool use.** Per attempt and in total: tool call counts and output bytes per tool, and for
   `bash`, the most frequent command families (for example `grep`, `rg`, `aw ipd lint`,
   `git log`) and the files most often read (by path, counted, not their contents).
5. **Run version and label.** Group and filter by the git commit the run used (from
   `tool_versions.agent_workflows` where present) and by a run label. If no run label exists, see
   Section 4.
6. **Model.** Group and filter by model, using `attempts[].model` first and `options.model` as a
   fallback, and report which source each value came from. Report coverage (how many attempts
   have a model) per phase.
7. **Redo counts.** Per attempt and per model: re-asks, turn retries, refusals, and attempts per
   queue item (an item reviewed in 3 attempts counts 3). This answers "how often does a model need
   to be told to redo something".
8. **Experiment comparison.** For a set of runs selected by label: a table with one row per
   combination of plan id6, review variant, and model, showing cost (or tokens where cost is
   missing), steps, wall time, redo counts, and the review outcome (verdict or readiness, if the
   run records it).
9. **Review steps.** The redesigned review will run several prompts per review in one session, so
   one attempt will contain several steps. If the runner records which review step a prompt
   belongs to, group by it. If it does not, say what recording is needed (this is expected; the
   redesign has not been built).

## 4. Recording that may be required

Check whether each item below exists. If it does not, either add it (small, isolated changes only)
or list it in your report:

- A run label set at run start, for example `aw oc run ... --label <text>`, stored in `state.json`.
- The git commit (full hash) and whether the working tree was dirty, stored in `state.json` at run
  start for every run, not only in telemetry.
- An experiment variant field (for example `review_variant: grouped-6` or `single-12`), stored in
  `state.json`. The redesign will set it; analysis only needs to read it.
- The model on every attempt record.

## 5. Report

End with a short report that states:

1. Which of the questions in Section 3 can now be answered, with the exact `aw runs query` command
   for each.
2. Which cannot, and the exact data that is missing.
3. Every fact in Section 1 that you found to be wrong.
4. Any recording you added, and from which commit runs carry it.
5. The test command you ran and its actual output.
## Workflow history
- 2026-10-24 executed (aw set): Section 5 report filed as research gczlvd (plan avg8qv)
