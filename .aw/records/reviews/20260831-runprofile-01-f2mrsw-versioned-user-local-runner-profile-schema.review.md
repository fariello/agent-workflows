# Review: Versioned user-local runner profile schema and resolution

- Plan-Id: f2mrsw
- Reviewed-At: 2026-08-31
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `6a29f9c0`, working tree clean, plan committed and unchanged. Structural preflight
`aw ipd lint --phase author` reports `conforming`.

This is the strongest member of the Set and the only one with NO scope collision: its Scope-Paths are
`agent_workflows/runner_profiles.py` and `tests/test_runner_profiles.py`, both new, so it can execute
without waiting on any approved plan. It is also correctly placed at Order 01 with no dependencies.

Its Findings table is genuinely good and I verified the reasoning rather than accepting it: user-local
XDG storage instead of tracked `.aw/config/**` is the right call (a tracked profile would disclose an
institution-specific model id in a public repo, which the repo's own leak-sanitizer exists to prevent);
fixed structured fields instead of a raw `args` string correctly forecloses a command-injection surface
before aliases ever dispatch; referential integrity on the default pointer prevents a silent fallback
to a costlier or weaker model; and returning a resolution digest plus a complete snapshot is what keeps
a resumed run's execution identity stable when the config is edited mid-run. Each of those is a real
hazard with a proportionate control.

TWO REVISIONS APPLIED, both at the maintainer's explicit direction rather than from my own analysis.
The maintainer decided during this session (recorded in `novalnomerge-01` `evgi9n`'s deferral) that
per-model verification defaults belong in THIS plan, because it owns the profile schema and depends on
nothing. The measured gap: schema version 1 is
`{schema_version, default_runner, defaults, profiles}` with each profile carrying
`runner`/`model`/`variant`/`agent`, so profiles today route the verifier's IDENTITY but carry NOTHING
about whether verification runs at all.

1. PR-001, MEDIUM (maintainer-directed). Add a per-profile `validate` field. The operational need is
   concrete and measured: on this model an independent verifier turn added only nits for roughly 33%
   extra cost, so the maintainer runs with validation off; on Gemini it is needed. Without a
   per-profile field that choice is a global flag the operator must remember per invocation, which is
   exactly how the `vju5ba` bug went unnoticed for five overnight runs.
2. PR-002, MEDIUM (maintainer-directed). Add `validate` to the top-level `defaults` key AND fix its
   PRECEDENCE against an explicit `--validate`/`--no-validate` flag, which must still win. This half is
   the one that would otherwise be missed, and it matters because getting it wrong reproduces `vju5ba`
   in the opposite direction: a profile default silently overriding an explicit flag is the same class
   of defect as two flags that quietly cancel out. E-03 already implements "deterministic resolution",
   so this is an extension of existing machinery rather than new machinery.

Both are additive to a schema that does not yet exist in code, so the remediation risk is minimal.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | A. Correctness / H. Operability | E-01 defines schema v1 as `{schema_version, default_runner, defaults, profiles}` with per-profile `runner`, `model`, `variant`, `agent`; no verification field exists. Measured: profiles route the verifier's IDENTITY (`3m0urk` CID-2/CID-4) but never whether it RUNS. | A profile cannot express whether verification should run for that model. The maintainer's measured position is that the verifier adds only nits at ~33% cost on this model (so: off) while Gemini needs it (so: on), and with no per-profile field that becomes a flag the operator must remember every invocation. That is precisely the failure mode `vju5ba` demonstrated across five overnight runs. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (additive field on a schema not yet implemented) | FIXED | E-01 now includes an optional per-profile `validate` boolean beside `variant`, with the Opus-off / Gemini-on rationale recorded. Added as a Findings row and to Required tests. |
| PR-002 | MEDIUM | UNDER-SCOPE | A. Correctness | E-03 already implements "deterministic resolution" and a precedence order; `defaults` exists as a top-level key with no `validate` member | The fallback half plus the precedence question. Without deciding precedence explicitly, a profile-level default could silently override an EXPLICIT `--validate`/`--no-validate` flag, which is the same class of bug as `vju5ba` (two settings that quietly cancel each other) only inverted. An explicit flag must always win over a stored default. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now resolves `validate` through the precedence chain explicit flag > profile field > `defaults.validate` > shipped default, states that an explicit flag ALWAYS wins, and requires a test per precedence level. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the per-model verification default live here, in `novalnomerge-01` (`evgi9n`), or in a new plan? | HERE. This plan owns the profile schema and its precedence resolution, and it depends on nothing. | (a) Build it in `evgi9n`. Rejected and already deferred there: hardcoding a model policy in the runner would be knowingly temporary once this schema exists. (b) A separate new plan. Rejected: it would have to edit this plan's schema anyway, so it adds an artifact without adding separation. | Maintainer decision recorded in `evgi9n`'s Deferred section and its workflow history; this plan's E-01 owning schema v1 and E-03 owning resolution | yes |
| D-2 | Should an explicit `--validate`/`--no-validate` flag override a stored profile value? | YES, always. | Letting the profile win, or leaving precedence unstated. Both rejected: an unstated precedence is how `vju5ba` happened (two independently sensible defaults that cancelled), and a profile silently beating an explicit flag would make the flag a lie. | `vju5ba` root cause as measured in `evgi9n` (`--validate` default False vs `--no-self-finalize` default True); E-03's existing deterministic-resolution requirement | yes |
