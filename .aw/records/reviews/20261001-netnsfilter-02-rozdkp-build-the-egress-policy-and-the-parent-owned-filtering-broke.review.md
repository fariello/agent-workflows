# Review findings: plan rozdkp

- Subject-Id: rozdkp
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-701 (HIGH, fixed), PR-702 (MEDIUM, fixed), PR-703 (MEDIUM, fixed), PR-704 (LOW, fixed), PR-705 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `09c6b12f3`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent` reported `clean` before review and
`--phase review-finalize --agent` reports `clean` after it. `- Kind: child`, so IPD-S407/S408 do not apply.

Evidence re-checked. Research `akmzyq` carries every quoted measurement: "unix socket across netns:
PARENT-PROXY-REACHED", "PROXY DENIED github.com" / "PROXY ALLOWED api.anthropic.com", "rc: 56 ... CONNECT tunnel
failed, response 403", the Finding 4 evasion table, and Finding 5 "`SO_ORIGINAL_DST` recovered `140.82.113.4:443`".
Research `uq4y6q` carries "net_port rule struct size: 16 (... NO address field)". `HardModeUnavailableError`,
`select_execution_profile` and "an UNPROBED host claims NOTHING" are all present in `host_sandbox_profile`, and
`BWRAP_STUB_MODES` and "UNVERIFIED on that machine" are present in `tests/test_host_sandbox_profile.py`.
`run_evidence.validate_finding_table` emits `RC-COUNT`. Every carrier resolves: `2j4pd0` (pending plan, depends on
`executed:rozdkp`), and `sv9ce4` and `wcbpqf` (backlog). Dependency `nxh5s4` is `reviewed`, not yet executed, so the
`executed:nxh5s4` edge is live and correct. Neither new path exists yet. The design is sound: deny by default,
refuse to guess, and keep the broker in the parent.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-701 | HIGH | UNDER-SCOPE | Rubric D/E (Set's core invariant untested) | E-06 as written: "one loopback listener ... plus a SECOND loopback listener", both on one address, so the ports must differ. V-03: "A pair differing in port does not meet this item." | The one property the Set exists for (the same-port destination partition) had no hermetic test. The only same-port evidence was a research run against the external network, and the test as designed proves only what Landlock already can. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now uses ONE live listener on port `P`, with `127.0.0.1:P` allowed and `localhost:P` refused (destination as requested, OQ-01; decided before resolving, so no DNS), plus a port-partition case. V-03 and V-06 now demand this pair. `127.0.0.2` was rejected: on this host it gave `Connection refused` for a listener bound to 127.0.0.1, and it is not configured by default on macOS CI. |
| PR-702 | MEDIUM | UNDER-SCOPE | Rubric E (CI portability) | `.github/workflows/tests.yml` matrix `os: [ubuntu-latest, macos-latest, windows-latest]`; the plan requires NO SKIPS on any host while E-03 mandates AF_UNIX. | `socket.AF_UNIX` is not guaranteed on Windows Python, so the "no skips on any host" bar collides with the transport the plan mandates. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The handler accepts a connected socket. Hermetic tests drive it over `socket.socketpair()`. The AF_UNIX-listener test is the single sanctioned `skipif`, which V-05 names. |
| PR-703 | MEDIUM | UNDER-SCOPE | Security lens (trust-boundary input) | E-03/E-04 log the client-chosen destination and echo the reason into the refusal message, with no input bounds specified | The confined client controls the CONNECT line. Without bounds, a CRLF in the target can forge log lines or response headers, an unbounded head can exhaust memory, and a world-reachable socket is an open proxy to allow-listed hosts for other local users. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now caps the head size, accepts only a `CONNECT host:port` line (`400` otherwise), takes the destination from the authority only, refuses control characters and invalid syntax, never echoes raw bytes, and places the socket in a parent-only directory that is unlinked on shutdown. V-03 demands evidence for each. |
| PR-704 | LOW | IN-SCOPE | Evidence accuracy (stale quote) | The plan quoted "Network scoping and container isolation are out of scope here" three times. `host_sandbox_profile` docstring now reads "network denial is measured and cannot separate a git remote from the model API on one port, so none is applied (network scoping is now measured rather than out of scope ...); container isolation remains out of scope here." | The quoted sentence no longer exists. The plan's reasoning still holds. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All three sites now carry the current wording. The Spec-sync note warns that child `wn956n` still quotes the old sentence and must re-anchor when it executes (not editable from this review's scope). |
| PR-705 | LOW | IN-SCOPE | OQ contract | OQ-01..03 were resolved with `- Owner: none` | The owner field did not record who decided. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Set to `- Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How can a hermetic test show a same-port refusal? | Hostname alias: `127.0.0.1:P` listed, `localhost:P` unlisted, one live listener. | (a) A second loopback address `127.0.0.2:P`: rejected, because a probe on this host refused it and macOS only configures 127.0.0.1 by default. (b) A stub upstream resolver: more machinery for the same proof. | OQ-01 (key on the destination as requested); probe output `127.0.0.2 [Errno 111] Connection refused`; CI matrix. | yes |
| D-2 | How should the broker stay testable on Windows CI? | A transport-neutral handler driven over `socketpair()`, with one sanctioned AF_UNIX `skipif`. | Linux-only skip for the whole file: rejected, because it is the skip-guards-nothing trap the conventions cite. | `tests.yml` matrix; `tests/test_host_sandbox_profile.py` "UNVERIFIED on that machine". | yes |
