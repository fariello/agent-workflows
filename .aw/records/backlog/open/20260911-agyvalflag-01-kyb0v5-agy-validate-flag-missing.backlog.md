- Id: kyb0v5
- Status: open
- Set: agyvalflag
- Priority: high
- Work-Kind: bug
- Summary: aw agy run registers no --validate/--no-validate flag, so its verifier default cannot be overridden

## Workflow history
- 2026-09-11 created (aw backlog): Filed 2026-09-10 from an /askme round, on the maintainer's ruling that no defect may be raised without a carrier. MEASURED at HEAD 2cdc5fe5: grep for '--validate' returns 8 hits in oc_runipd.py (registered at :7871 and :7942) and ZERO in agy_runipd.py; 'aw agy run --help' shows no validate flag at all, while 'aw oc run --help' does. The maintainer states this is not acceptable: BOTH hosts need flags to turn the verifier on or off, and only the DEFAULTS were meant to differ (agy on, oc off). So agy's verifier is currently unconditional. Note plan mp289j's F-12 recorded the observation ('registers no --validate at all') but treated it only as evidence weakening that plan's cost argument, and no carrier was filed for the gap itself. Scope: register --validate/--no-validate on agy_runipd with agy's ON default preserved, mirroring oc's flag surface and the runner_profiles.py:57 precedence chain (explicit flag > profile > shipped default). Do NOT change either host's default as part of this.
