# Review findings: plan txl556

- Subject-Id: txl556
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane. The plan was byte-identical to the lane input and committed unchanged (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan. Prerequisite `j0ufrj` is `reviewed`, not executed; its contract and those of `epsti7`, `mtmqlm`, `4kkcex`, `qrup8m` and `mrlblc` were read from those plans.

Verified:
- `project_context.get_default_aw_home` resolves `AW_HOME`, then `XDG_CONFIG_HOME/agent-workflows`, then `~/.aw`; the root `conftest.py` sandboxes `AW_HOME` and `XDG_CONFIG_HOME` for every test.
- `pyproject.toml` declares `dependencies = ["filelock>=3"]` and `requires-python = ">=3.9"`; the wheel ships the whole `agent_workflows` package, so a `notify/` subpackage ships.
- `leak_sanitizer.build_ruleset(repo_root)` returns fail patterns (home paths, `vc-home`, private repo names, other account, `ses_` session ids, handle, user hints); `scan_text` reports findings and does not rewrite; `_rewrite_line` rewrites home paths only. MEASURED: on `"see /home/<u>/x/plan.md and ses_<long-token>"` scan reports `home-path, session-id`, and after `_rewrite_line` `session-id` remains. MEASURED: a `/srv/data/...` path yields no finding, while `render_stream._redact_absolute_paths` replaces it with `<path>`.
- `config.read_review_findings_gate` is the precedent for a never-raising tracked `project.json` key reader; `project_schema.parse_portable_policy` preserves unknown keys.
- `urllib.request.HTTPRedirectHandler.redirect_request` follows 301/302/303 for a POST (rewritten to GET), so a redirect would carry the body to another host unless refused.
- Spec `6kwd2e` R9.2, R9.7, R10.1-R10.8, A48, A49, A53, A55 read as cited. `j0ufrj` E-01 emits `answer-consumed` and `answer-stale` events and calls `consume_answers` at the top of `run_queue`; `4kkcex` E-04 writes pre-flight questions to the inbox from `initialize_run_core`, not from a park branch; `mtmqlm` E-05 makes `set_question_status` the only question-status writer.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Security (R10.3 sanitizer) | `leak_sanitizer._rewrite_line` home-path-only rewrite; measured `ses_` survives; `/srv/...` no finding | "Run text through the package leak sanitizer (build_ruleset + redaction used by aw sanitize)" names no redaction that exists for most leak classes: the shipped rewrite covers home paths only and `scan_text` only reports. An executor would ship session ids and non-home absolute paths off the machine. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | E-02 defines `sanitize_outbound` by guarantee: strip control chars, home rewrite, absolute-path redaction, replace every remaining fail-pattern match, re-scan and redact the field if anything remains, then truncate. V-02 demands all four leak classes. |
| PR-002 | HIGH | IN-SCOPE | Correctness (notify trigger) | old E-03 "at park (Order 02/03 write point) ... `notified` flag in the question file"; `4kkcex` E-04; `mtmqlm` E-05 | Hooking each park write point misses pre-flight-routed questions (written from `initialize_run_core`) and re-parks, and writing a `notified` flag into question files bypasses the single status writer and races the answer writer's lock. `runner_shared.py`/`question_inbox.py` were in scope but the host call sites (`oc_runipd`/`agy_runipd`) were not. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-03 is one `dispatch_checkpoint` at the top of both hosts' `run_queue` after `consume_answers` and before the summary, diffing open questions against `<run_dir>/notify/sent.jsonl`; question files are never modified. Scope-Paths now list both host files and drop `runner_shared.py`/`question_inbox.py`. |
| PR-003 | HIGH | UNDER-SCOPE | Security (inbound routing, R10.1/R10.5) | spec R10.1 "the core hands verified events to the shared writer"; old E-02 registry only | The core owned the registry and event dedup but had no function that verifies, dedups and writes an inbound answer, so Order 10 would map events to `write_answer` itself, which R10.1 assigns to the core. | all Low | FIXED | New E-06 (registry split out of E-02) adds `core.apply_inbound`: dedup, `verify`, routing, `write_answer` with channel and sender. Deferred notes Order 10 calls it. |
| PR-004 | MEDIUM | IN-SCOPE | Security (webhook URL) | spec R10.2 "secrets ... topic names"; incoming-webhook URLs embed credentials | The webhook URL is a credential but was printable in events and `health`, plain `http` was allowed, and `urllib` follows redirects for a POST. | C:Low; U:Low; S:Medium; F:Low; Overall:Medium | FIXED | E-04 shows only scheme and host, requires `https` except loopback, refuses redirects; V-04 demands each. |
| PR-005 | MEDIUM | IN-SCOPE | Correctness (Teams / Google Chat body) | Findings "one webhook channel covers them"; spec R10.8b | Incoming chat webhooks expect a `{"text": ...}` body, not `aw.notify/v1`, so the claimed coverage was not delivered by the specified body. | all Low | FIXED | E-04 adds `format` `aw`/`text`/`ntfy`; Findings records that Teams Workflow rendering is a hand-test item for Order 11. |
| PR-006 | MEDIUM | IN-SCOPE | Correctness (fail-closed config and policy) | old E-01 "warning if broader permissions are found"; "`notify_policy` ... as a ceiling" | A world-readable secrets file was only warned about; a malformed policy value had no defined effect; "create it" conflicted with Order 11 owning setup; env-configured channels had no mode. | all Low | FIXED | E-01: load never creates; `save_user_config` creates 0600; broad perms are tightened or the file is not read; malformed policy is `forbid`; env channels are terse; malformed config disables channels without failing the run (D-2, D-3). |
| PR-007 | MEDIUM | IN-SCOPE | Correctness (tracked-secret detection) | old E-01 "ignore and WARN on any channel secret found in tracked `.aw/config/`" | "Any channel secret" was undefined, so detection could not be implemented or tested. | all Low | FIXED | E-01 defines it as any `notify` or `notify_*` key except `notify_policy` in tracked `.aw/config/*.json`, reported without the value. |
| PR-008 | MEDIUM | UNDER-SCOPE | Testing / acks | old E-03 acknowledgement only for consumed; core tier rule (CONTRIBUTING "covers every first-party module") | A stale answer (Order 04 `answer-stale`) produced no acknowledgement, so the human never learns the reply was not applied (R10.1 `ack` intent); the new modules had no core-tier marker. | all Low | FIXED | E-03 sends a stale notice; E-05 marks the module `pytest.mark.core`. |
| PR-009 | LOW | IN-SCOPE | Process | OQ-01 `Owner: maintainer`; `-q`; doc sync "N/A" | OQ-01 was the author's resolution labelled maintainer; `-q` hides `N passed`; docs and CHANGELOG ownership unstated. | all Low | FIXED | Owner corrected (D-1); `-q` removed; Spec sync names Order 11 as docs and CHANGELOG owner. |

`aw ipd lint --phase review-finalize --agent`: `clean` (one `info` advisory `IPD-Z602` on clause count, kept).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Use Apprise? (OQ-01) | No; webhook plus command hook. | Apprise dependency (REJECTED: second runtime dependency). | `pyproject.toml` dependencies; spec R10.8b. | yes |
| D-2 | Effect of an unrecognized `notify_policy`? | Treat as `forbid` with a warning. | Ignore it (REJECTED: a typo would silently re-enable sends a repo meant to forbid). | spec R10.2 ceiling semantics; fail-closed precedent `config.REVIEW_GATE_DEFAULT`. | yes |
| D-3 | A secrets file with broad permissions? | Tighten to 0600, else refuse to read. | Warn only (REJECTED: leaves a token readable by other users). | spec R10.2 "file mode 0600". | yes |
| D-4 | Where does notification trigger? | One checkpoint dispatcher diffing open questions against `sent.jsonl`. | Hook every park writer with a flag in the question file (REJECTED: misses pre-flight routing, bypasses the single status writer). | `4kkcex` E-04; `mtmqlm` E-05; `j0ufrj` E-01. | yes |
| D-5 | Sanitizer scope beyond home paths? | Composed `sanitize_outbound` with a re-scan fallback. | Only `_rewrite_line` (REJECTED: measured to leak `ses_` ids and non-home paths). | measured at review. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`. Follow-up for Order 10 (`qrup8m`): its E-02 maps inbound events to `write_answer` itself and its E-04 names an `on_consumed` hook; under this revision it should call `core.apply_inbound` and receive acknowledgements through `dispatch_checkpoint`. It was not edited here (owning-plan rule; a reviewer of `qrup8m` should reconcile it).
