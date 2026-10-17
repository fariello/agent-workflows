---
id: gigsfc
created: 20261017
set: plainlang
order: 05
topic: [communication, plain-language, experiment]
model: opus55high
kind: findings
status: active
outcome: informational
summary: Experiment 2026-10-17: old vs new communication contract vs old+separate rewrite pass, 3 writer models x 3 real failures x 2 samples, blind-scored by 3 judge models
consumed-by: []
---

# Experiment: does the rewritten communication rule, or a separate rewrite pass, make agents' failure explanations easier to understand?

## Question

On 2026-10-17 the communication rule in `AGENTS.md` (`agent_workflows/reporting_contract.py`) was
rewritten from the four `ng0ga4` research reports (`8tcq84`, `o7v25q`, `ky28a9`, `ne3jy6`): a named
reader, failures told as observed-cause-effect-fix with "cause unknown" allowed, a repair rule for
"plain version", and an explicit statement that the word cap does not limit explanations. All four
reports also proposed a separate rewrite pass (a second model call that sees only the draft) as the
strongest lever outside the instructions. This experiment measures both against the old rule.

## Method

- **Scenarios.** Three real failures from this repository on 2026-10-16/17, each given as the raw
  investigation notes an agent would have (`scen/s1.md` a merge refused only because the test run
  exceeded a time limit; `s2.md` a statusline showing "1 fail" when nothing failed; `s3.md` a
  misleading error for a mistyped five-character id).
- **Writers.** Three models through their own CLIs, each started in an empty directory so no
  repository instruction file was loaded: GPT-6.1 Sol medium (`codex exec`), Claude Opus 5.5 high
  (`opencode run`), Gemini 3.8 Flash high (`agy -p`).
- **Conditions.** (1) `old`: the previous contract text pasted as the agent's communication policy;
  (2) `new`: the rewritten contract; (3) `old+rewrite`: the `old` reply passed, by the same model, to
  a separate rewrite call that saw only the draft and a short rewrite brief (`rewrite_prompt.txt`).
  Two samples per writer, scenario and condition: 54 messages.
- **Blind scoring.** Messages were shuffled under random ids (`blind/`, key in `blind_key.json`), and
  every message was scored by all three models as judge (162 judgements) against the reference
  notes and a list of required facts (`facts.json`, `judge_prompt.txt`). The judge was told to read
  as an engineer who has never seen the repository, and scored understanding (1-5), knowing what to
  do (1-5), unexplained terms (count), required facts conveyed (fraction), and false claims (list).
- All inputs, outputs and scores are in the companion `.data/` directory and can be re-run with the
  scripts there.

## Results

| Condition | Understand (1-5) | Know what to do (1-5) | Required facts | Unexplained terms | False claims per 100 words | Words |
|---|---|---|---|---|---|---|
| old rule | 4.56 | 3.83 | 0.86 | 1.1 | 0.46 | 126 |
| **new rule** | **4.74** | **4.43** | **0.95** | 1.5 | **0.29** | 234 |
| old + separate rewrite | 4.50 | 3.70 | 0.86 | 1.1 | 0.34 | 207 |

- **The new rule helped every writer**, most of all on "know what to do": GPT 3.39 to 4.17, Gemini
  3.44 to 4.44, Opus already high at 4.67 and unchanged. Across the 27 judge x writer x scenario
  cells, "know what to do" rose in 13 and fell in 3. Messages scored 5/5 for understanding rose from
  32 to 40 of 54.
- **The biggest gain was the scenario where the old replies were technically true but useless**
  (`s2`, the phantom "1 fail"): "know what to do" went from 2.61 to 4.17 and required facts from 0.77
  to 0.98. Under the old rule most replies said the count was a temporary artifact and stopped; under
  the new rule they also said what fixes it.
- **The separate rewrite pass did not help.** It made messages longer (126 to 207 words) without
  raising understanding (4.56 to 4.50) or "know what to do" (3.83 to 3.70), and it never recovered a
  fact the draft had left out (0.86 both), which is what it was instructed: the rewriter can only
  rephrase what it is given. Its false claims per message rose (0.46 to 0.70), mostly restated
  over-generalizations from the draft and a few new ones such as calling a time-limit exit a
  "timeout" or "four concurrent test processes".
- **False claims.** Counted per message the new rule looks worse (0.78 vs 0.46), but its messages
  are nearly twice as long; per 100 words it is lower (0.29 vs 0.46). Reading them, most judged
  "false claims" in every condition are small over-statements beyond the notes (for example "the
  retry was because the output did not match its spec" when the notes say only that a spec-anchor
  retry happened), not wrong diagnoses. The worst real errors (wrong mechanism for which items get
  the provisional status) appeared in Gemini's replies under all three conditions.
- **Unexplained terms rose slightly** under the new rule (1.1 to 1.5), because longer replies name
  more of the investigation's identifiers. Gemini's new-rule replies often explained a term and then
  kept using the raw symbol name in parentheses, which judges counted against them.

## Limits

- Judges are models, not the maintainer. Agreement on direction was consistent (all three judges
  rank new > old on both understanding and "know what to do"), but absolute scores differ by judge
  (the Opus judge counted 2-3 times as many unexplained terms as the others).
- One-shot replies with the policy in the prompt, not long sessions. This does not test whether the
  effect decays over many turns, which is the maintainer's main complaint and the question the
  research could not answer.
- Three scenarios, two samples each. The `s1` and `s3` differences are small; `s2` carries most of
  the effect.
- The judge's "false claims" list is itself noisy; numbers are directional.

## Conclusions

1. **Keep the new rule.** It measurably improved explanations for all three models, especially
   telling the reader what to do, at the cost of longer replies.
2. **Do not build a separate rewrite pass** for runner explanations on this evidence. It added length
   and some errors and could not add what the draft left out. The research's case for it (removing
   the writer's knowledge) is right about the cause but the rewriter, by the same token, cannot supply
   the missing facts. Revisit only if a rewrite design is found that keeps the writer's facts and
   removes only its shorthand.
3. **The open question is decay over a long session**, which this experiment did not test. The
   cheapest real measurement is the maintainer's own: count how often "plain version" (now also
   `/plain`) is needed per session before and after 2026-10-17.
