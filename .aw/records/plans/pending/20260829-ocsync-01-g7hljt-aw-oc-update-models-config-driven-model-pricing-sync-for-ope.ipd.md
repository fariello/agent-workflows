# IPD: aw oc update-models: config-driven model/pricing sync for OpenCode gateways

- Date: 2026-08-29
- Kind: child
- Concern: OpenCode users must hand-maintain per-model pricing in their opencode.json, so `cost` blocks silently drift from what their configured OpenAI-compatible gateway actually charges, corrupting spend estimates. There is no tool-agnostic way to refresh them from the gateway itself.
- Scope: Add a generic, config-driven `aw oc update-models` (alias `sync-models`) subcommand that resolves the user's OpenCode config the way OpenCode does, discovers each OpenAI-compatible provider from that config (no hardcoded hosts), probes each provider's baseURL for a LiteLLM-style pricing endpoint, and strict-syncs the `models` block (ids, `input`/`output`/`cache_read`/`cache_write` in $/M tokens) for providers that expose pricing while leaving providers that do not (plain OpenAI, Google, etc.) untouched. Preview by default; `--apply` writes with a timestamped backup.
- Scope-Paths: agent_workflows/oc_models.py, agent_workflows/cli.py, tests/test_oc_models.py, tests/test_oc_models_cli.py
- Item-Dependencies: none
- Status: reviewed
- Set: ocsync
- Order: 1
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: g7hljt

## Workflow history
- 2026-08-29 /plan-review (opencode / its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006 all FIXED; no open questions; readiness GO - PENDING HUMAN APPROVAL.
- 2026-08-29 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed.
- 2026-08-29 to-review (aw set): Completed IPD authoring; ready for review.

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give OpenCode users a tool-agnostic `aw oc update-models` that refreshes each OpenAI-compatible provider's model list and pricing directly from the gateway declared in their own OpenCode config, so `cost` blocks stay accurate without hardcoding any particular gateway host into the published package.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Core sync module

- [ ] E-01 Create `agent_workflows/oc_models.py` with OpenCode config discovery: resolve the active config path using OpenCode's own precedence (`$OPENCODE_CONFIG`, then a project `opencode.json`/`opencode.jsonc` walking up from cwd, then `$XDG_CONFIG_HOME/opencode/opencode.json` or `~/.config/opencode/opencode.json`), returning the first that exists. Pure function, no network. A resolved `.jsonc` (or any file stdlib `json` cannot parse) is classified UNSUPPORTED-FOR-WRITE and reported as a skip with an actionable message, never parsed by stripping comments and never rewritten: stdlib `json.dump` cannot round-trip comments, so writing one would silently destroy user content. Reading `.jsonc` for a preview-only diff is also out of scope for this plan (see Deferred).
  - Depends on: none
  - Expected outcome: `resolve_config_path(env, cwd)` returns the expected path for each precedence case; missing config returns None; a `.jsonc` target returns the UNSUPPORTED-FOR-WRITE classification rather than raising or silently reformatting.
  - Execution state: pending
- [ ] E-02 In `oc_models.py`, add provider discovery + a LiteLLM pricing probe: iterate `provider.*` entries whose npm is `@ai-sdk/openai-compatible` (or that carry an `options.baseURL`), resolve the `apiKey` including OpenCode's `{file:~/path}` interpolation, and probe `<host>/model/info` then `<host>/model_group/info` (stripping a trailing `/v1`). Convert per-token costs to $/M tokens (input/output/cache_read/cache_write), preserve existing display names, and strict-sync the provider's `models` block. Providers with no pricing endpoint are left untouched. Network calls isolated behind an injectable fetch function so tests never hit the network. Credential-safety guardrails (all MUST): (a) send the bearer key ONLY over `https`; a non-https `baseURL` is skipped with a reported reason unless the user passes an explicit `--allow-insecure` opt-in, and even then never to a non-loopback host; (b) never include the key, the `Authorization` header, or the resolved key-file contents in any output, diff, log, exception message, or `--agent`/`--json` payload; (c) follow the `versioning.latest_pypi_version` failure shape (short timeout, blanket except, degrade to "no pricing" rather than raising); (d) treat the gateway response as untrusted input: validate types before use and ignore unknown/malformed cost fields instead of coercing them.
  - Depends on: E-01
  - Expected outcome: given a fake fetcher returning a LiteLLM payload, the synced `models` block matches expected ids + $/M costs; a provider whose fetch fails is left unchanged; an `http://` baseURL is skipped without any request being issued; a test asserts no output stream contains the fake key.
  - Execution state: pending
- [ ] E-03 In `oc_models.py`, add the `run(argv)`/`main` entry point and its flags: `--config PATH`, preview-by-default printing a per-provider diff and writing nothing (`--dry-run` accepted as an explicit synonym), `--apply` to write, `--no-backup`, `--allow-insecure`, and `--agent`/`--json` machine output consistent with the repo's output conventions. `--apply` is refused (exit nonzero, nothing written) when the resolved config is UNSUPPORTED-FOR-WRITE per E-01.
  - Depends on: E-02
  - Expected outcome: preview leaves the fixture byte-identical; each flag parses and takes effect; `--apply` on a `.jsonc` exits nonzero having written nothing.
  - Execution state: pending
- [ ] E-06 In `oc_models.py`, implement formatting-faithful serialization for the write path: detect the file's existing indent width from its first indented line and reuse it (falling back to 4) so a 2-space config is not silently reflowed, keep every non-`models` key's value and relative order intact, and document in `--help` that `--apply` rewrites the file with normalized JSON formatting (byte preservation is NOT claimed).
  - Depends on: E-03
  - Expected outcome: `--apply` on a 2-space fixture emits 2-space output; on a 4-space fixture emits 4-space; only `provider.<p>.models` values differ from the input; `--help` states the formatting caveat.
  - Execution state: pending

- [ ] E-04 Make the `--apply` write atomic and crash-safe: serialize to a temp file in the same directory, `os.replace` it over the target (atomic on POSIX), and write the timestamped `.bak` BEFORE the replace, so an interrupted run can never leave a truncated or partially written `opencode.json` (the file that gates the user's whole tool). Reuse the repo's existing atomic-write helper if one exists (search for an `_atomic_json`-style helper, e.g. the one referenced at `agent_workflows/cli.py:7311`) rather than adding a second mechanism.
  - Depends on: E-03
  - Expected outcome: a test simulating a failure mid-serialize leaves the original file intact and valid JSON; the temp file does not remain.
  - Execution state: pending

### Task group 2: CLI wiring

- [ ] E-05 Wire `oc_sub.add_parser("update-models", aliases=["sync-models"])` into `agent_workflows/cli.py` under the existing `oc` group (locate by the `p_oc = sub.add_parser` symbol) with `--config/--apply/--dry-run/--no-backup/--allow-insecure` flags, and dispatch `args.command in ("oc","opencode")` + `oc_command in ("update-models","sync-models")` to `oc_models.run(...)`. Use the parsed namespace, NOT `argparse.REMAINDER` (this verb has structured flags, unlike `runipd`). Update the `oc` group help string and the `_show_family_help` hint to mention the new verb.
  - Depends on: E-04
  - Expected outcome: `aw oc update-models --help` shows the flags; `aw oc --help` lists `update-models`; `aw oc` family help mentions it.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Subcommand groups are declared in `cli.py` via `sub.add_parser(...)` + a nested `add_subparsers(dest="<group>_command")`; the `oc` group already exists (`agent_workflows/cli.py:2616`, subparsers at `agent_workflows/cli.py:2622`) with dispatch at `agent_workflows/cli.py:7955`. Line numbers are indicative only; locate by symbol (`p_oc = sub.add_parser`, `args.command in ("oc", "opencode")`) rather than by line, since `cli.py` shifts.
- Host tooling lives in dedicated modules (`oc_runipd.py`, `agy_runipd.py`) exposing `main(argv)`; dispatch either forwards `argparse.REMAINDER` verbatim (runners, `agent_workflows/cli.py:7756`) or, for structured verbs, reads the parsed namespace. This command uses structured flags, not REMAINDER.
- Outbound HTTP has exactly one canonical precedent: `versioning.latest_pypi_version` (`agent_workflows/versioning.py:405-426`) uses stdlib `urllib.request` with an explicit HTTPS-only note (`# noqa: S310 (https only)`), a short timeout, and a blanket `except (urllib.error.URLError, OSError, ValueError, TimeoutError)` that returns None so a network failure never crashes the caller. This module MUST follow that shape (zero new dependencies, degrade gracefully).
- The repo treats hostnames as identifying info guarded by the leak-sanitizer (`agent_workflows/leak_sanitizer_config.py:37,189-192`), so gateway hosts and API keys must never be written to committed artifacts or emitted in machine output.
- Tests live under `tests/` as `test_oc_*.py` (`test_oc_runipd.py`, `test_oc_runipd_cli.py`); mirror that split (module logic vs CLI wiring).
- User-facing prose in shipped docs avoids em/en dashes per the repo contract; IPDs/plans/code comments are exempt.
- GUIDING_PRINCIPLES P7 (project-agnostic) and P6 (KISS/generality ladder) govern: no gateway host may be hardcoded; provider discovery is driven by the user's own config data.

## Findings

The `llmgw.its.uri.edu` gateway used during discovery is a LiteLLM proxy. Empirically:

| Endpoint | Pricing? | Notes |
|---|---|---|
| `GET /v1/models` (OpenAI std) | no | only id/object/created/owned_by |
| `GET /model_group/info` (LiteLLM) | yes | per-token input/output cost, context, capability flags |
| `GET /model/info` (LiteLLM) | yes | superset: adds `cache_read_input_token_cost`, `cache_creation_input_token_cost` |

OpenAI's `/v1/models` and Google's `/v1beta/models` expose no pricing, so those providers must be skipped, not errored. This is why the probe must gracefully no-op a provider that lacks a LiteLLM pricing endpoint. A standalone proof-of-concept (`~/.config/opencode/bin/update-uri-models.py`) already validated the per-token to $/M conversion, strict-sync, name preservation, and idempotency end-to-end; `oc_models.py` generalizes it to multi-provider, config-driven discovery.

Review-added findings verified against the repo and by direct experiment:

- Stdlib `json.load` raises `JSONDecodeError` on a `.jsonc` file containing `//` comments (verified experimentally), so the original plan's promise to resolve `opencode.jsonc` was unimplementable as written and, if patched by stripping comments, `json.dump` would destroy those comments on write. Resolved by classifying `.jsonc` UNSUPPORTED-FOR-WRITE (E-01) and deferring JSONC support explicitly.
- A fixed `json.dumps(..., indent=4)` reflows a 2-space config to 4-space (verified experimentally), contradicting the original claim that "the rest of the config round-trips unchanged." Resolved by detecting and reusing the file's existing indent, and by stating the formatting caveat honestly in `--help` (E-03) rather than overclaiming byte preservation.
- The only in-package precedent for outbound HTTP (`agent_workflows/versioning.py:405-426`) is HTTPS-only with a blanket failure path. The original plan specified neither a scheme restriction nor a failure mode while sending a bearer API key to a config-supplied URL, which would send the user's credential in cleartext for an `http://` baseURL. Resolved by the E-02 guardrails (https-only, opt-in loopback exception, never log the key, untrusted-response validation).
- The command rewrites `opencode.json`, the file that gates the user's entire tool. The original plan had no atomicity requirement, so an interrupted write could truncate it. Resolved by adding E-04 (temp file + `os.replace`, backup before replace, reuse the existing `_atomic_json`-style helper).

## Proposed changes (ordered, validatable)

1. New module `agent_workflows/oc_models.py` (discovery, probe, sync, atomic write, `main`).
2. `agent_workflows/cli.py`: register `update-models`/`sync-models` under `oc`; add dispatch; update help text.
3. New tests `tests/test_oc_models.py` (module logic with an injected fetcher, no network) and `tests/test_oc_models_cli.py` (parser + dispatch).

## Deferred / out of scope (with reason)

- `aw codex` / `aw hermes` equivalents: same idea for other agentic tools, but each reads a different config format. Deferred until those host groups exist; `oc_models.py` should keep the config-reader separable so a future `codex_models.py` can reuse the LiteLLM probe. Note this is a deliberate one-host implementation now (P6 generality ladder: shared core, thin specialization) and NOT a claim of multi-host support.
- Writing (or comment-preserving round-trip of) `opencode.jsonc`: stdlib `json` cannot parse comments and `json.dump` cannot preserve them, so a write would destroy user content. Adding a JSONC parser/serializer is a dependency and complexity increase not traceable to the current need. `.jsonc` is therefore detected and skipped with an actionable message (E-01) rather than silently mishandled. Revisit only if a real user hits it.
- Auto-scheduling (cron/systemd): environment-specific; out of scope. Users can wrap the command themselves.
- Non-LiteLLM pricing schemes: only the LiteLLM endpoints are probed; other OpenAI-compatible gateways with different pricing APIs are skipped (left untouched), not guessed.
- Pricing for providers with no pricing API (plain OpenAI, Google Gemini): verified during discovery to be unavailable from their APIs, so those `cost` blocks remain hand-maintained. The command must not touch them, and must not imply it refreshed them.

## Scope check

- Over-scope: none.
- Under-scope: none remaining. Review added E-04 (atomic write) after noting the plan mutated the user's primary tool config with no crash-safety, split E-06 (formatting-faithful serialization) out of the entry point on a density advisory, and hardened E-01/E-02 for the `.jsonc` write hazard and credential-over-http exposure. The six E-items cover discovery, probe, entry point, write-safety, CLI wiring, and serialization fidelity, each with a 1:1 validation item.

## Required tests / validation

- `python -m pytest tests/test_oc_models.py tests/test_oc_models_cli.py -q` passes (module logic with injected fetcher + CLI parser/dispatch). No test may perform real network I/O; the fetcher is injected in every case.
- Manual smoke against the real config: `aw oc update-models` (preview) prints a per-provider diff and leaves `opencode.json` byte-identical (verify by checksum, not by eye); after an `--apply`, a subsequent run reports up to date (idempotent).
- Credential-hygiene check on the evidence itself: before pasting any command output into this plan, confirm it contains no API key, `Authorization` header, or key-file contents. Run `aw sanitize --agent` and consume its output rather than eyeballing.
- Full repo suite `python -m pytest -q` remains green (no regressions in the `oc` group).

## Spec / documentation sync

- Update the `oc` group help string in `cli.py` (part of E-04).
- No separate spec doc required; the command is self-describing via `--help`. README mention optional and not required for this plan.

## Open questions

### OQ-01: Strict sync vs preserve-unknown for models absent from the gateway

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: Strict sync (a provider's `models` becomes an exact mirror of what its gateway returns) was chosen during discovery; models the gateway no longer lists are removed. Confirmed by the user for the URI gateway case.

### OQ-02: Should preview or apply be the default when the command is run bare?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: Preview is the default and `--apply` is required to write. Resolved from repository evidence rather than by asking: the repo's own convention for mutating verbs is dry-run-by-default (`aw ipd scaffold` previews unless `--apply`; `aw research new` is "Dry-run by default"), and GUIDING_PRINCIPLES P10 (safety and reversibility) requires defaulting to non-destructive action. `--dry-run` is retained as an explicit synonym for the default so existing muscle memory and scripts remain valid.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output for the discovery tests covering each precedence case ($OPENCODE_CONFIG wins; project file found by walking up; XDG path; ~/.config fallback), missing-config returning None, and a `.jsonc` target returning UNSUPPORTED-FOR-WRITE (asserting it neither raises nor is parsed).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing (a) synced models match expected $/M costs from a fake LiteLLM `/model/info` payload including cache_read/cache_write; (b) `/model_group/info` fallback used when `/model/info` is absent; (c) a fetch-failing provider left byte-identical; (d) an `http://` baseURL skipped with NO request issued (assert the injected fetcher was not called); (e) an assertion that the fake API key string appears in no captured stdout/stderr/JSON payload.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing preview leaves the fixture byte-identical (compare file bytes/checksum before and after), each flag parsing and taking effect, a `.bak` written on `--apply` and suppressed by `--no-backup`, and `--apply` on a `.jsonc` exiting nonzero with the file unmodified. Plus real-world smoke: pasted `aw oc update-models` (preview) output against the maintainer's own config showing a per-provider diff, with checksum evidence the config was not modified. Any pasted output MUST be inspected to confirm it contains no API key or key-file contents.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted pytest output for the atomicity test: an injected failure during serialization leaves the original config intact and parseable, no temp file remains in the directory, and the `.bak` predates the replace.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `aw oc update-models --help` and `aw oc --help` output showing the verb, aliases, and every flag; plus pasted pytest output from a CLI dispatch test asserting `oc_models.run` is invoked with the parsed flags for both `update-models` and the `sync-models` alias.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted pytest output showing a 2-space fixture round-trips as 2-space and a 4-space fixture as 4-space after `--apply`, that a diff of input vs output shows changes confined to `provider.*.models`, and pasted `--help` text containing the formatting caveat.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:

- Open questions: OQ-01 and OQ-02 are resolved (see above); no unresolved question blocks execution.
- Scope fence: touch ONLY the declared Scope-Paths (`agent_workflows/oc_models.py`, `agent_workflows/cli.py`, `tests/test_oc_models.py`, `tests/test_oc_models_cli.py`). Any change outside them requires a new plan, not an in-place widening. Do not modify the maintainer's personal `~/.config/opencode/opencode.json` as part of executing this plan; use fixtures for tests, and treat any real-config run as read-only preview evidence.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run, and never summarize output you did not capture. Before pasting, confirm the output contains no API key or key-file contents.
- Commits: path-scoped only (`git commit -m msg -- <path>`); never `git add -A`, never `-a`, never push. Never create a tag or release.
- Lifecycle move: implement E-01..E-06, run the validation suite, record evidence, confirm `aw ipd lint --phase pre-transition` conforms, and only then `git mv` this plan to `.aw/records/plans/executed/` with the terminal Status. If any validation fails, STOP and report rather than marking the plan executed.
