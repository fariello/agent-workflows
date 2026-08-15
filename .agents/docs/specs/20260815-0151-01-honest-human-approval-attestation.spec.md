# Spec: honest human-approval attestation (replace `--yes-i-am-human` with `--by-human`)

- Date: 2026-08-15
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: the `aw specs set` human-only transition gate (D125's "anti-self-approval floor") forces a dishonest, high-friction ritual: to record a human's approval an agent must pass `--yes-i-am-human` (asserting it IS human, a falsehood) AND satisfy a TTY check its non-interactive shell cannot meet, so the human is repeatedly forced into their own terminal to run the command. The maintainer flagged both problems: it forces an agent to lie, and it is disproportionately strict for what the control actually is.
- Relation to prior work: REVISES D125's approval floor. Executes the `open` backlog item `honest-human-approval-attestation` (id 0zb1cd). Related backlog: `unified-status-transition-verb` (nm69aj, the future `aw set` migration target) and the parked `specs-approval-ergonomics` (zpez3o, OQ10). Touches `agent_workflows/attention_contract.py` (`TRANSITION_AUTHORITY`), `agent_workflows/specs.py` (`run_set`, `_human_confirmed`), `agent_workflows/cli.py`, `tests/test_specs_verbs.py`, `.agents/docs/specs/README.md`, and the AGENTS.md pointer.

## 1. One-line summary

Reframe the human-only approval gate from a TTY-enforced "prove you are human" control into an HONEST, non-TTY ATTESTATION SPEED BUMP: replace `--yes-i-am-human` with `--by-human`, which an agent (or a human) passes to record that a HUMAN approved a spec transition (`reviewed -> approved`), with attributed provenance in the workflow-history line. No TTY requirement, no false "I am human" claim.

## 2. Problem / motivation

- The floor (D125; `_human_confirmed` in `specs.py`) refuses `reviewed -> approved` unless `sys.stdin.isatty()` AND either `--yes-i-am-human` is passed on that TTY or the human types `approve` at a prompt. An executing agent has no TTY, so it can NEVER record an approval - even one the human explicitly gave in chat.
- Two concrete harms, both maintainer-reported (2026-08-09 awlayout, 2026-08-10 awphysical, 2026-08-15): (1) HONESTY - `--yes-i-am-human` forces the caller to assert "yes, I am human," which is false when an agent runs it on the human's behalf; the honest claim is "a human approved this." (2) FRICTION - the human is pushed into their own terminal to run a `--message`-mandatory, type-the-word-`approve` command for an approval they already gave; "that will dissuade people from using this."
- The DEEPER misconception the current design encodes: that the floor defends against a MALICIOUS agent self-approving. It does not and cannot - a malicious agent can rewrite the tool, the code, or the instructions telling other agents to approve. There is no local gate that stops that; attempting one is security theater. The floor's REAL and only defensible purpose is a CONSCIOUS SPEED BUMP: make an honest agent stop and confirm "did the human actually approve this?" before barreling ahead into a human-only transition. This spec re-states the floor's intent accordingly.
- Asymmetry that caused the surprise: PLANS already record human approval as an agent-written attributed `- Approval:` metadata line (no TTY); only SPECS carry the TTY floor. This spec brings specs in line with that honest, low-friction model while keeping the deliberate speed bump.

## 3. The reframed floor (what it is, and is NOT)

- It IS: a mandatory, EXPLICIT, distinct action (`--by-human`) that an agent must consciously choose in order to perform a human-only transition, recording attributed provenance. The friction is intentional: it prevents an honest agent from AUTO-advancing a transition the human must own, and it leaves a clear audit line.
- It is NOT: a cryptographic or TTY-based proof of humanity, and NOT a defense against a malicious/compromised agent (out of scope and not achievable locally, per Section 2). No token, keyfile, signature, or interactive prompt.
- Anti-self-approval, honestly stated: an agent must not SILENTLY or IMPLICITLY self-approve; it must record an EXPLICIT attributed human approval. Whether the human truly approved is a trust/provenance matter (the history line names who/how), exactly as it already is for PLANS.

## 4. Goals

- G1 `[Must]` Replace `--yes-i-am-human` with `--by-human` on `aw specs set`. `--by-human` is honored regardless of TTY (works in a non-interactive agent shell). Remove the `sys.stdin.isatty()` requirement and the typed-`approve` prompt from the human-only path.
- G2 `[Must]` A human-only transition (`->approved`) SUCCEEDS iff `--by-human` is passed, and is REFUSED with a clear message otherwise (the speed bump: an agent that does not pass it is stopped, told to attest only a real human approval).
- G3 `[Must]` The recorded approval is attributed: the workflow-history line records `approved (aw specs, --by-human)` plus the `--message` provenance (who approved / how, e.g. "human maintainer via chat"). `--message` remains required (it carries the provenance).
- G4 `[Must]` No dishonest surface: nothing requires asserting "I am human." `--by-human` reads as "a human approved this" (attested, agent-recordable).
- G5 `[Must]` Preserve every OTHER floor property: the legal transition table, `implemented` still needs a resolvable `--evidence` citation, `deferred` still needs a typed gate, atomic single-file write, no git side effects, byte-identical refusal on non-conformance.
- G6 `[Should]` Name the MIGRATION TARGET: a future unified positional verb `aw set human approved <identifier...>` (or `aw set approved --by-human <id...>`) folds this in across specs + plans + group ops (backlog nm69aj). This spec ships the `aw specs set --by-human` form now and records the target so the later verb is a rename/superset, not a redesign.
- G7 `[Must]` Stdlib only; Python 3.9; deterministic.

## 5. Non-goals

- NOT any token/keyfile/signature/crypto mechanism (explicitly rejected as theater, Section 2/3).
- NOT defending against a malicious or compromised agent.
- NOT building the unified `aw set` verb here (backlog nm69aj); only naming it as the migration target.
- NOT changing the `implemented` evidence gate or the `deferred` gate.

## 6. Functional design

- `agent_workflows/specs.py` `run_set`: for a transition whose `TRANSITION_AUTHORITY` marks `human_token: True`, require `getattr(args, "by_human", False)`; on absence, refuse with: "`<old> -> <new>` is a human-only transition; pass `--by-human` to attest (and record) that a human approved it. Use `--message` to say who/how." Remove `_human_confirmed` (the TTY/`--yes-i-am-human` logic) entirely.
- The approval history record includes the attestation marker, e.g. `- <date> approved (aw specs, --by-human): <message>`.
- `agent_workflows/cli.py`: replace the `--yes-i-am-human`/`dest=yes_i_am_human` argument on `specs set` with `--by-human` (`dest=by_human`, `action=store_true`), help: "Attest that a HUMAN approved this transition (records attributed approval; no TTY). Only for human-only transitions like reviewed -> approved."
- `attention_contract.TRANSITION_AUTHORITY`: keep `->approved` as `human_token: True` (its meaning is now "requires the `--by-human` attestation"), OR rename the key to `by_human: True` for clarity; either is acceptable as long as the contract doc + specs.py agree. Update the contract docstring that describes the floor to the reframed intent (speed bump, not TTY/anti-malicious).
- Docs: `.agents/docs/specs/README.md` and the AGENTS.md "What needs attention" pointer prose (`engine.agents_pointer_prose`) updated from "an agent may not set `approved` without an interactive human confirmation" to "an agent records human approval with `aw specs set --status approved --by-human --message ...` (an explicit attested speed bump; no TTY, no 'I am human' claim)."

## 7. Requirements

- F1 `aw specs set --status approved --by-human --message "..."` succeeds in a NON-TTY shell and records the attributed approval + history line.
- F2 `aw specs set --status approved` WITHOUT `--by-human` is refused with the speed-bump message (nonzero, file byte-identical).
- F3 `--yes-i-am-human` is removed from the CLI and code; no path asserts "I am human"; no `sys.stdin.isatty()` gate on approval.
- F4 The `implemented` evidence gate and `deferred` typed-gate are unchanged and still enforced.
- F5 Writes stay atomic + git-side-effect-free; a would-be non-conformant result is refused byte-identical.
- N1 stdlib only, Python 3.9, deterministic. N2 no em/en dashes in authored user-facing output.

## 8. Acceptance criteria

- A1 In a non-interactive (no-TTY) shell, `aw specs set --status approved --by-human --message "human maintainer via chat"` on a `reviewed` spec sets it `approved` and appends `- <date> approved (aw specs, --by-human): human maintainer via chat`.
- A2 The same command WITHOUT `--by-human` refuses (nonzero) with the speed-bump message and leaves the file byte-identical.
- A3 `aw specs set --help` shows `--by-human` and NOT `--yes-i-am-human`; grep of the codebase shows no remaining `yes-i-am-human`/`yes_i_am_human`/`_human_confirmed`.
- A4 `implementing -> implemented` still requires a resolvable `--evidence`; `-> deferred` still requires a valid gate (unchanged).
- A5 Full unittest suite green; `test_specs_verbs.py` updated: the old "no-TTY approved is refused even with --yes-i-am-human" test becomes "no-TTY approved SUCCEEDS with --by-human, and is refused WITHOUT it."
- A6 `aw specs check` and `aw attention --check` remain clean.

## 9. Constraints and dependencies

- Revises D125 (record the reframed floor + the flag change in a new DECISIONS entry on implementation). Depends on `attention_contract.TRANSITION_AUTHORITY` + `specs.py`. The AGENTS.md pointer regeneration follows the D104 empty-diff-invariant convention. This unblocks recording approvals for the two currently-stuck specs (this one + `20260813-1833-01` backlog tier) and `ipdexechist-01` without a TTY.

## 10. Risks and open questions

- OQ1 Authority-key naming: keep `TRANSITION_AUTHORITY['->approved']['human_token']` (re-interpreted) or rename to `by_human`? (Leaning: rename to `by_human` for honesty; minor, internal.)
- OQ2 Should PLANS' approval also route through a `--by-human`-style verb for consistency, or stay the current attributed `- Approval:` metadata convention until the unified `aw set` verb? (Leaning: leave plans as-is now; unify later under nm69aj.)
- OQ3 Should `--message` stay mandatory for approvals (provenance) or be optional with a default? (Leaning: mandatory - the provenance IS the point.)
- OQ4 Exact migration shape of the future unified verb (`aw set human approved <id>` vs `aw set approved --by-human <id>`)? Deferred to the nm69aj backlog item; this spec only requires forward-compatibility.

## 11. Next step

Drafted to `Status: to-review`. Next: `/plan-review`, then HUMAN APPROVAL, then an implementing IPD (its own `/plan-review` + approval) before code changes. Note the bootstrap irony: approving THIS spec is (per the current rule) the kind of TTY-gated approval it removes; once implemented, `--by-human` is the honest path for all future approvals. Do NOT edit `specs.py`/`cli.py` before the IPD is approved.

## Workflow history
- 2026-08-15 /spec (opencode its_direct/pt3-claude-opus-4.8-1m-us): drafted to Status: to-review. Reframes D125's approval floor from a TTY/anti-malicious control (rejected as theater) to an honest conscious speed bump, and replaces the dishonest `--yes-i-am-human` with a non-TTY `--by-human` attestation recording attributed human approval. Executes backlog item 0zb1cd; names the unified `aw set` verb (nm69aj) as the migration target. Maintainer-directed 2026-08-15 ("we just want a mechanism that makes an agent stop and think 'did the human approve this'... a simple approved-by-human is all that's needed... it does not force you to lie").
