- Id: dh3us4
- Status: blocked
- Gate-Kind: artifact
- Gate-Ref: .aw/records/plans/pending/20260903-runflags-01-uyeko5-wire-the-spec-2-1-run-flag-surface-onto-both-host-runners.ipd.md
- Set: retrypolicy
- Priority: medium
- Work-Kind: feature
- Summary: Implement the repository-policy tier of --retry-budget precedence (CLI > repo policy > default 2)

## Workflow history
- 2026-09-04 blocked (aw set): status set to blocked
- 2026-09-04 created (aw backlog): Implement the repository-policy tier of --retry-budget precedence (CLI > repo policy > default 2)

Spec `25kzda` 2.1 fixes a THREE-tier precedence for the retry budget: "The CLI value overrides repository policy; repository policy overrides the default of 2." `runflags-01` (`uyeko5`) E-04 implements CLI-over-default and deliberately does NOT invent a config surface for the middle tier, recording it as under-scope instead. So two of three tiers ship and the middle one is unowned.

WHAT IS MISSING: a repository-level place to set a default retry budget, consulted when no CLI flag is passed and falling back to `DEFAULT_RETRY_LIMIT` (`run_recovery.py:62`, currently `2`) when unset.

WHY IT IS NOT URGENT: the two shipped tiers give correct behavior for every invocation that either passes the flag or wants the default, which is every invocation today. The missing tier only matters once a repository wants a standing override different from 2.

WHY IT IS GATED ON `uyeko5`: that plan introduces the flag and the precedence chain this tier slots into; building the config surface first would mean designing a consumer for a flag that does not exist.

DESIGN CAUTION, so whoever takes it does not guess: `.aw/config/project.json` is the obvious home, but adding a key there is a schema change with its own validation and defaulting rules. Do NOT add an ad-hoc config read; follow whatever the project-config schema authority requires at that time.
