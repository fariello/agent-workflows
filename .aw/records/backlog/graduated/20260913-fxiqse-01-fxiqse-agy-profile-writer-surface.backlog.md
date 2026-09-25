- Id: fxiqse
- Status: graduated
- Graduated-To: agyprofile
- Set: fxiqse
- Priority: medium
- Work-Kind: feature
- Summary: Add a writer surface for antigravity runner profiles and defaults.validate

## Workflow history
- 2026-09-25 graduated (aw set): graduated into agyprofile plan 6o8q4k (to-review)
- 2026-09-13 created (aw backlog): Add a writer surface for antigravity runner profiles and defaults.validate

The validate tri-state now resolves on BOTH hosts (plan ybkmzp), so a stored per-model verification choice decides an antigravity run. NOTHING SHIPPED CAN WRITE THAT CONFIGURATION: the profile wizard hardcodes RUNNER = 'oc' (runner_profile_wizard.py), 'aw oc profile add' writes that constant, 'aw agy profile' does not exist (exit 2), and runner_profiles.set_validate_default has no caller in the package, so defaults.validate has no writer either. An operator can only hand-edit runner-profiles.json, which docs/runner-profiles.md now documents as the supported manual step.

The design questions this item owns, deliberately left open rather than pre-decided in a wiring plan: which verb writes an agy profile (a widened wizard with a host argument, a new 'aw agy profile' subcommand, or a host-neutral 'aw profile'), how it interacts with the oc-only wizard and 'aw oc profile default', and whether defaults.validate deserves its own verb given it is host-neutral. Note antigravity accepts no --profile flag and has no 'as <profile>' clause, so a written agy profile only applies via defaults.profiles.agy, which any writer surface must set for the profile to take effect.
