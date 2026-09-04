- Id: x8diyb
- Status: blocked
- Gate-Kind: artifact
- Gate-Ref: .aw/records/plans/pending/20260903-runflags-01-uyeko5-wire-the-spec-2-1-run-flag-surface-onto-both-host-runners.ipd.md
- Blocks-Release: next
- Set: rundepflags
- Priority: high
- Work-Kind: feature
- Summary: Build --with-dependencies closure expansion and --follow-generated graph joining (runflags E-05 registers them as refusals only)

## Workflow history
- 2026-09-04 blocked (aw set): status set to blocked
- 2026-09-04 created (aw backlog): Build --with-dependencies closure expansion and --follow-generated graph joining (runflags E-05 registers them as refusals only)

Spec `25kzda` 2.1 declares both flags; `runflags-01` (`uyeko5`) E-05 REGISTERS them but deliberately makes each REFUSE with 'not yet implemented', because the behavior is real graph work rather than a parser edit. Nothing owns that behavior, and `uyeko5`'s Deferred section promises a follow-up that did not exist until this item.

WHAT IS ACTUALLY MISSING:

- `--with-dependencies`: expand the selection to the TRANSITIVE declared dependency closure BEFORE the queue is frozen, and subject any newly introduced TYPE to the same mixed-type gate (so pulling in a spec alongside plans must re-trigger the `RUN-MIXED-TYPES` confirmation). Without the flag, dependencies outside the selection are checked against repository state but never silently enqueued.
- `--follow-generated`: a run that GENERATES a new IPD mid-flight joins it to the active graph. Without the flag it is reported as a next action only. Spec 2.1 also requires a generated IPD to resolve its own `Item-Dependencies` before review-readiness.

WHY IT IS GATED RATHER THAN OPEN: the flags do not exist until `uyeko5` E-05 lands, and the closure expansion has to run inside the queue-build path `uyeko5` is already editing. Doing it first would mean two sessions in the same runner code.

WHY IT IS NOT MERELY A UX GAP: a silent no-op here is a CORRECTNESS failure - an operator who passes `--with-dependencies` and gets no expansion believes prerequisites were queued when they were not. That is why E-05 refuses instead of accepting, and why this item exists rather than leaving the flags half-built.
