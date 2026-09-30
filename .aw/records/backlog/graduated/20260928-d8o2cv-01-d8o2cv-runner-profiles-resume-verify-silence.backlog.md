- Id: d8o2cv
- Status: graduated
- Graduated-To: d8o2cv
- Set: d8o2cv
- Priority: low
- Work-Kind: chore
- Summary: docs/runner-profiles.md documents the per-host verification flag spelling difference for start but is silent on resume

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: gyd8sq
- 2026-09-28 created (aw backlog): Filed while authoring plan 7dz3wv (graduating xdgorn); measured at HEAD beb37773.

Measured live at HEAD `beb37773` while authoring plan `7dz3wv`.

WHAT IS MISSING. `docs/runner-profiles.md` has a "BOTH HOSTS HONOR THIS CHAIN" paragraph that correctly documents the per-host SPELLING difference on `start`: opencode accepts `--validate`/`--no-validate` with `--verify` and `--audit` as aliases, antigravity accepts `--validate`/`--no-validate` plus `--no-verify` (alias `--no-audit`), and a contradictory pair is refused. That is accurate for `start`.

It is SILENT on `resume`, where the two hosts differ again and in the operator's favor only on one of them:

  aw oc run resume --no-verify <run>    ACCEPTED; writes validate=False into the frozen state
  aw agy run resume --no-verify <run>   exit 2, 'unrecognized arguments: --no-verify'

Antigravity's `resume` parser registers NONE of the six verification spellings, so the verification decision cannot be changed on a resumed antigravity run at all. That matters most on antigravity precisely because it is the host that verifies BY DEFAULT (`runner_profiles.RUNNER_REGISTRY['agy'].validate_default` is True, against False for oc), so an operator resuming a long agy run and wanting to skip the verifier turn has no flag to reach for and gets an exit 2 rather than an explanation.

WHY IT IS A CHORE AND NOT A BUG. Nothing behaves incorrectly and the refusal is a clean exit 2, not a silent wrong answer; the cost is one confused documentation lookup, which is not a user-perceptible defect in the sense AGENTS.md defines.

SUGGESTED FIX: extend that paragraph with one or two sentences on the resume difference, noting that agy's resume registers none of the six and that oc's honors an explicit flag. Plan `7dz3wv` adds the same facts to spec `25kzda` Section 2.1c as a normative declaration; this item is the operator-facing half, deliberately kept separate because user-facing prose has a different audience and review standard than a spec section.
