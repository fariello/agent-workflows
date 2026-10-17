# Review findings: plan mrlblc

- Subject-Id: mrlblc
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan. Prerequisite `qrup8m` (and transitively `txl556`) are `reviewed`, revised earlier in this sweep; their contracts were read from the revised plans.

Verified:
- `command_surface.COMMAND_INVENTORY` declares leaves; `tests/test_command_surface_declarations.py` asserts zero undeclared parser leaves. MEASURED: command classes in use are `alias` (12), `bare` (1), `check` (23), `mutation` (83), `read` (57).
- MEASURED: `command_surface.discover_parser_roots(cli._build_parser())` returns 23 family roots; `tests/test_family_root_agent_conformance.py` runs `aw <root> --agent` for each non-exempt root (the exemption registry is empty) and requires a valid record with `exit` matching. `aw reviews --agent` emits `kind: error, outcome: cannot-run, exit: 2, next: ...`, produced by `cli._show_family_help`.
- `term.is_interactive` is the CLI presence predicate used by existing interactive verbs in `cli.py`.
- `txl556` (revised) E-01 `save_user_config` / `read_notify_policy` / `effective_channels`, E-03 `dispatch_checkpoint`, E-04 webhook formats `aw`/`text`/`ntfy` and URL-as-secret, E-06 `apply_inbound`; `qrup8m` (revised) E-01 `TelegramChannel` with `AW_NOTIFY_TELEGRAM_BASE_URL`, E-03 `TelegramReceiver` and `ensure_receiver` with the per-bot lock, E-05 `tests/fake_telegram.py`.
- Research `kdg4uz`: "Serialize setup polling through the same broker"; prefers an OS keyring. Research `js5p5k` A5 setup flow (deep link `t.me/<bot>?start=<phrase>`, about 5 minutes, button and reply test, save 0600 terse).
- Spec `6kwd2e` R10.2, R10.6, R10.9, A54 read as cited.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness (poll contention) | research `kdg4uz` "Serialize setup polling through the same broker"; `qrup8m` E-03 per-bot lock | Setup pairing, `test` and `listen` all call `getUpdates`, but none took the receiver lock, so running any of them beside a live runner would 409 the runner's receiver (stopping it) or steal its updates. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 step 5, E-02 `test` and E-06 `listen` take Order 10's per-bot lock and refuse with the holder named; E-01 advances the offset past pairing traffic. |
| PR-002 | HIGH | UNDER-SCOPE | Executability (CLI conformance) | `tests/test_family_root_agent_conformance.py`; `discover_parser_roots` (23 roots measured); `cli._show_family_help` | A new `notify` family root must answer `aw notify --agent` with a valid record or the conformance suite fails; the plan did not mention the family root, `_DESCRIPTIONS`, or which classes the leaves take. | all Low | FIXED | E-03 registers the family with `_show_family_help`, a description, and per-leaf declarations with classes and exit contracts (D-3); the test command includes the three conformance tests. |
| PR-003 | HIGH | IN-SCOPE | Right-sizing | old E-01 (Telegram setup plus webhook and command setup); old E-02 (four verbs incl. a long-running listener) | E-01 and E-02 each bundled independent deliverables and test surfaces; `listen` is a lifecycle-bearing foreground process unlike the other three verbs. | all Low | FIXED | Split: E-05 (webhook and command setup), E-06 (`listen`); E-02 keeps `status`/`disable`/`test`. |
| PR-004 | MEDIUM | IN-SCOPE | Security (secrets on argv) | old E-01 "`setup webhook --url`"; Findings | A webhook URL is a bearer credential, and `--url` puts it in shell history and process listings; output handling of the URL was unstated. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | E-05 warns on `--url`, adds `--url-stdin` and the env var, and shows only scheme and host; V-05 checks no output line holds the path. |
| PR-005 | MEDIUM | IN-SCOPE | Correctness (setup safety) | old E-01 | Non-TTY behavior, Ctrl-C/timeout handling, pairing acceptance from other users, the button/reply test being from the paired ids, and the write path were unspecified. | all Low | FIXED | E-01: requires a TTY, writes only via `save_user_config` at the end, accepts only a private message from the pairing sender and test answers from the paired ids, and every abort writes nothing. |
| PR-006 | MEDIUM | IN-SCOPE | Correctness (status, disable, listen semantics) | old E-02 | `status` sources (receiver holder, last success) and env-configured channels were undefined; `disable` on an env channel and `listen` with no run directory (event destination, SIGTERM, a second listener) were unstated. | all Low | FIXED | E-02 and E-06 define each; `listen` logs to `<AW_HOME>/notify/listen.jsonl`. |
| PR-007 | MEDIUM | IN-SCOPE | Testing (doc check, TTY) | old E-03 "commands match the implemented `--help` output"; old E-04 "stdin scripted" | "Match the help output" was not a checkable test; a `getpass` prompt cannot be scripted through a plain pipe. | all Low | FIXED | E-04 parses every `aw notify ...` line in the doc with the real parser (behavioral, not source-reading) and drives setup through a `pty`; module marked core. |
| PR-008 | LOW | IN-SCOPE | Process | `-q`; doc index; keyring | `-q` hides `N passed`; the new doc was not linked from `docs/README.md`; research's keyring recommendation was neither adopted nor declined. | all Low | FIXED | `-q` removed; `docs/README.md` added to scope; keyring declined in Deferred with reason (D-4). |

`aw ipd lint --phase review-finalize --agent`: `clean` (two `info` advisories `IPD-Z602` on E-01 and E-03 clause counts, kept: E-01 is one interactive flow tested by one fixture; E-03 is registration plus the docs that describe it).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How do setup/test/listen coexist with a live runner's receiver? | Take the per-bot lock and refuse when held. | Poll anyway (REJECTED: 409 stops the runner's receiver). | research `kdg4uz`; `qrup8m` E-03. | yes |
| D-2 | Presence predicate for setup? | `term.is_interactive()`. | `is_interactive_run` (REJECTED: runner-gate predicate keyed on runner flags). | existing interactive verbs in `cli.py`. | yes |
| D-3 | Command class for `test` and `listen`? | `mutation`. | `read` (REJECTED: they send off-machine and write answers); a new class (REJECTED: inventory has four). | measured class census. | yes |
| D-4 | OS keyring for the token? | Not in v1. | Keyring backend (REJECTED: new runtime dependency; spec requires only 0600 file or env). | spec R10.2; `pyproject.toml` dependencies. | yes |
| D-5 | How to test the doc against the CLI? | Parse each documented command with the real parser. | Compare help text (REJECTED: brittle and not a behavior). | AGENTS.md test-outcomes rule. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
