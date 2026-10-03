- Id: 79d4ix
- Status: open
- Set: 79d4ix
- Priority: low
- Work-Kind: chore
- Summary: Decide whether to migrate the eight live legacy-token write sites or soften spec 25kzda's claim that the runner no longer writes them

## Workflow history
- 2026-10-02 created (aw backlog): Measured while authoring plan fr19jr (backlog ku8szz): spec 25kzda asserts legacy terminal status tokens 'are no longer written by the runner', and that is false at HEAD.

FILED BY PLAN `fr19jr` (from backlog `ku8szz`), whose F-08 measured this while sweeping for dead READERS of the terminal status vocabulary. That plan deliberately does not fix it, because the fix is a writer migration plus a spec reconciliation in the hottest file in the repository, and conflating it with an author-time checker would make both unreviewable.

THE CONTRADICTION. Spec `25kzda`'s 2026-09-25 amendment (in its `## Workflow history`) states that the legacy terminal status tokens "remain readable forever for backward compatibility on historical run records (via `TERMINAL_STATUS_ALIASES`), but **are no longer written by the runner**." That last clause is FALSE at HEAD.

THE EIGHT MEASURED IN-DOMAIN WRITE SITES, by symbol rather than by line, since an offset expires:

1. `oc_runipd`'s `except DriverError` handler sets `runnable["status"] = "failed-safely"`.
2. `agy_runipd`'s `except DriverError` handler sets `runnable["status"] = "failed-safely"` (the same fork on the other host).
3. `runner_shared.refuse_undispatchable_typed_entry` sets `item["status"] = "failed-safely"`.
4. `runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS` is the literal `"failed-safely"`, and is assigned to `item["status"]` on the finalize-exhausted path.
5. `runner_shared.TURN_RETRY_EXHAUSTED_STATUS` is the literal `"failed-safely"`, and is assigned to `item["status"]` on the turn-retry-exhausted path.
6. `lane_containment.BOUND_EXPIRY_DISPOSITION` is the literal `"failed-safely"`, returned as the `"disposition"` of `lane_containment.bound_expiry_record`.
7-8. `runner_shared` passes `suffix="merge-conflict"` to `write_prompt` at two sites. These are PROMPT FILENAME SUFFIXES, not item statuses, and are listed only so the census is complete; they are almost certainly NOT part of the defect.

Confirmed at RUNTIME, not only statically: `FINALIZE_RETRY_EXHAUSTED_STATUS`, `TURN_RETRY_EXHAUSTED_STATUS` and `BOUND_EXPIRY_DISPOSITION` all resolve to `'failed-safely'`; `'failed-safely' in TERMINAL_STATES_CANONICAL` is `False`; and `canonical_terminal_status('failed-safely')` is `'fail-gate'`. So the runner writes a token its own canonical set excludes.

WHY THIS IS NOT OBVIOUSLY A BUG, which is why the item is a DECISION rather than a fix. Each constant carries a comment explaining the choice as deliberate AT THE TIME it was made: `FINALIZE_RETRY_EXHAUSTED_STATUS`'s says `failed-safely` was chosen because it "ALREADY exists, is already in `TERMINAL_STATES`, is already rendered `FAILED` by the summary, and is already in `--retry-incomplete`'s set, so an operator keeps the manual route"; `TURN_RETRY_EXHAUSTED_STATUS`'s says it must be "An EXISTING terminal status, never a new one: `runner_shutdown.observe_ledger` declares a run incoherent on any status outside its closed set"; and `BOUND_EXPIRY_DISPOSITION`'s says `failed-safely` "is an EXISTING terminal state in both drivers' vocabulary, so a bound expiry stays visible to the reconcile/report machinery without new states." These are all sound statements that pre-date or ignore the `cyamvi` rename. So this is DRIFT between a spec sentence and shipped code, not carelessness.

AND NO USER-VISIBLE DEFECT IS MEASURED TODAY, which is why it is filed `chore` and carries no release gate. `failed-safely` is a key of `TERMINAL_STATUS_ALIASES`, so every reader that canonicalizes handles it correctly, and plan `qvfd4l` plus plan `fr19jr` together fixed the readers that did not. The cost is latent rather than live: a reader added in future that handles only canonical tokens would silently miss these records, which is exactly the defect class `ku8szz` and `qvfd4l` exist to prevent.

THE DECISION TO MAKE, and it is genuinely a choice rather than a lookup:

- (a) MIGRATE THE WRITERS to `fail-gate` and keep the spec sentence true. This needs care: `runner_shutdown.observe_ledger`'s closed set, `--retry-incomplete`'s set, and every summary-bar membership must already accept `fail-gate` before the switch, or a run becomes "incoherent" or an operator loses the manual retry route. It also rewrites what NEW run records say, while old records keep the legacy spelling, so both must stay readable either way.
- (b) SOFTEN THE SPEC SENTENCE to say the runner writes canonical tokens for its own terminal classifications but still writes `failed-safely` for these specific contained-failure paths, and say WHY. Cheaper and honest, but it leaves a vocabulary with two live spellings for one state, which is the condition the `cyamvi` rename set out to end.

EITHER WAY, the spec and the code must be changed TOGETHER in one plan, since `AGENTS.md` requires a plan that changes behavior a spec describes to carry the spec amendment in the same change, declared in `- Scope-Paths:`.

SUGGESTED WORK: re-measure the write sites first (the tree may have moved), decide (a) or (b) with the maintainer since it is a public-contract question, then write one plan carrying both the code change and the `25kzda` amendment, with a behavioral test pinning whichever spelling is chosen at each of the three constants.
