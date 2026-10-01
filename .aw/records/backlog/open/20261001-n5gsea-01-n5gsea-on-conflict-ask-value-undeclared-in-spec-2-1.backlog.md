- Id: n5gsea
- Status: open
- Set: n5gsea
- Priority: low
- Work-Kind: chore
- Summary: The shipped --on-conflict accepts a fifth value 'ask' that spec 25kzda 2.1 does not declare, a spec-versus-code divergence the deleted bidirectional guard never covered

## Workflow history
- 2026-10-01 created (aw backlog): Found while measuring rcp8c4: with the bidirectional flag-surface guard deleted, an actual spec-versus-code divergence now ships undetected

MEASURED at HEAD `af30ba67f`. Spec `25kzda` Section 2.1 declares the flag as `[--on-conflict <drop|refuse|force|prompt>]` and its prose bullet enumerates exactly those four values. The shipped flag accepts FIVE: `runner_shared.RUN_POLICY_FLAGS_BY_FLAG['--on-conflict'].choices` is `('drop', 'refuse', 'force', 'prompt', 'ask')`, argparse therefore accepts `--on-conflict ask` on BOTH hosts (verified by driving `oc_runipd.build_parser()` and `agy_runipd.build_parser()`, each returning `on_conflict='ask'` rather than exiting 2), and the row's `help` string names `ask` to operators. So an operator-visible value exists that the approved contract does not declare.

THE BEHAVIOR IS DELIBERATE AND IS NOT BROKEN, which is why this is a documentation divergence and not a bug. `runner_shared.resolve_on_conflict` normalizes `ask` to `prompt` before validating against `CANONICAL_ON_CONFLICT_CHOICES` (the four-value tuple), so `ask` is an intentional ALIAS and `resolve_on_conflict('ask')` returns `'prompt'`. The code even separates the two tuples by name (`ON_CONFLICT_CHOICES` for what argparse accepts, `CANONICAL_ON_CONFLICT_CHOICES` for what resolution yields), so the alias is designed rather than accidental. Nothing computes a wrong answer.

WHY IT MATTERS: `25kzda` 2.1 is the normative grammar an operator and every reviewer reads, and an accepted value absent from it is either an undocumented public surface or an unsanctioned one. A reader cannot tell which from the artifacts alone. The honest resolutions are (a) amend 2.1's grammar and prose bullet to declare `ask` as an alias of `prompt`, which is the likely correct answer since the code, the help text and both parsers already ship it, or (b) drop `ask` from `ON_CONFLICT_CHOICES` if it was never meant to be public. THAT CHOICE IS A MAINTAINER'S, because it decides whether a shipped operator-facing spelling is supported or removed, so this item should NOT be graduated by an agent picking one.

SECOND, SMALLER INSTANCE IN THE SAME MEASUREMENT: 2.1's `run` stanza also declares `--action`, which `RUN_POLICY_FLAGS` does not own (both hosts register it on their own parsers instead, at `oc_runipd.py` and `agy_runipd.py`). That one is a KNOWN and previously SANCTIONED exclusion rather than a divergence: the deleted `tests/test_run_flag_surface.py` carried it in an explicit `DECLARED_BUT_NOT_OWNED_HERE` register with the reason "revsweep-01 (\`76gsmv\`) registers it with its per-type legality refusal", recoverable from `git show 19313eed^:tests/test_run_flag_surface.py`. With that file gone the register is gone too, so the sanctioned-exclusion list now exists NOWHERE in the tree. Worth recording in whatever fix lands, so a future reader does not mistake `--action` for a tenth divergence.

WHY THIS IS NEWLY VISIBLE: `tests/test_run_flag_surface.py` compared spec 2.1's grammar stanza against `RUN_POLICY_FLAGS` in BOTH directions and was deleted in `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"). Re-running its exact extraction by hand against today's tree reproduces the `--action` gap; the `ask` gap is a CHOICE-VOCABULARY divergence that even that test never checked, since it compared flag SPELLINGS and never a row's `choices`. So this divergence would have shipped silently even before the trim.

RELATED BUT DISTINCT: `rcp8c4` owns the seven stale comments in `runner_shared.py` that still claim that deleted test guards this table. This item is the FIRST MEASURED CONSEQUENCE of that guard's absence, and `rcp8c4`'s fix is text-only by maintainer ruling, so it deliberately does not touch either divergence. `woxgyo` covers unrelated comment damage in the same doc-comment block.
