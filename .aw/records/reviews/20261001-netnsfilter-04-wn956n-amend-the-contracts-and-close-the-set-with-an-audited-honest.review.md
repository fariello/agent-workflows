# Review findings: plan wn956n

- Subject-Id: wn956n
- Subject-Type: ipd
- Reviewed-At: 2026-10-11
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-1001 (MEDIUM, fixed), PR-1002 (MEDIUM, fixed), PR-1003 (HIGH, fixed), PR-1004 (HIGH, fixed), PR-1005 (MEDIUM, fixed), PR-1006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `d96a0ea68`. The plan was committed and byte-identical to the lane input
(sha256 prefix `962025dc306ec387`), so no pre-review snapshot was taken. `aw ipd lint --phase author --agent` -> `clean`
before review; `--phase review-finalize --agent` -> `clean` after. `- Kind: child`. Dependency `2j4pd0` is `reviewed`
with a blocking OQ-04 (allow-list source), so this plan cannot dispatch before that is answered and `2j4pd0` executes;
the `executed:2j4pd0` edge already enforces that ordering.

Re-measured: the spec path in Scope-Paths exists. `grep -n -F` on it: `deny push-capable` 2 lines (5.2 bullet
"deny push-capable network routes and withhold remote credentials" and 6.1 limit 4 "**No-push and hook guarantees
require control of execution.**"), and "the honest answer for every host today is NO" is present. Guarantee row 1 now
reads "a push attempt is prohibited, but no mechanism detects or aborts on one. The guarantee is not in force today
and fails closed" (rewritten by `tb6lw3`). 5.2 already carries "MEASURED FEASIBILITY AND BOUNDS (plan `x2dwu5`)" and
"FIRST PROBED ANSWER (plan `pi3bk8`)". The module docstring has no "Network scoping and container isolation are out
of scope here"; it reads "Network denial is measured and cannot separate a git remote from the model API on one port,
so none is applied". Its runner-safety bullet list names `supports_deny_tcp_port` but not `supports_egress_filtering`,
while `RUNNER_SAFETY_CAPABILITIES` has four members under the comment "The two runner-safety capability names", and
`probe_runner_safety_capabilities` says "Decide the two runner-safety capabilities". `aw host capabilities opencode`:
`yes supports_egress_filtering ... proves namespace creation and partition, NOT that any destination policy is
enforced, and proves nothing about whether a confined process could remove the boundary`. `aw check` exits 1 and
`aw research index --check` exits 1 on pre-existing populations, which confirms E-05's delta bar.

Term counts with `grep -c -i -F` on the spec: `deny push-capable` 2, `push denial` 6, `no-push` 8 (2 case-sensitive),
`deny_push` 7, `push` 33 lines.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-1001 | MEDIUM | IN-SCOPE | Evidence accuracy | Module docstring now reads "Network denial is measured and cannot separate a git remote from the model API on one port, so none is applied" | E-01, Concern and F-1 quote a sentence that no longer exists, so the executor cannot find the edit target. Child `rozdkp`'s review (PR-704) predicted this. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-quoted in every place it appeared. |
| PR-1002 | MEDIUM | UNDER-SCOPE | Spec consistency | Spec 5.2 "FIRST PROBED ANSWER (plan `pi3bk8`)", the `x2dwu5` gap sentence naming netns+proxy, the `sv9ce4` carrier pointer; row 1 rewritten by `tb6lw3` | E-02 did not mention the 5.2 paragraphs it must reconcile, and it quoted row 1's old text. A naive amendment would produce a second "first probed answer" and leave a stale gap statement. | Overall:Low | FIXED | E-02 now names both paragraphs and requires both to be reconciled. Row 1 is re-quoted. F-6 updated and F-10 added. |
| PR-1003 | HIGH | IN-SCOPE | Documentation correctness | `2j4pd0` review PR-805: egress filtering engages only when an allow list is declared, and a hardened run without one is unchanged | E-03 and V-03 required the docs to say hardened "requires a declared allow list and REFUSES to start without one". That contradicts the corrected child design, so the docs would misstate behavior to operators. | Overall:Low | FIXED | E-03 and V-03 now document behavior conditional on the allow list, and require reading child 03's executed V-04. |
| PR-1004 | HIGH | UNDER-SCOPE | Honest limits | `2j4pd0` review PR-800/E-07 (host AF_UNIX escape), OQ-04, F-12 (worker fetches its model catalog); the probe note "proves nothing about whether a confined process could remove the boundary" | The capability bullet and the Set statement omitted the limits child 03's review measured, and treated the probe as if it proved non-evadability. | Overall:Low | FIXED | E-01 now requires reading `2j4pd0`'s V-03, V-06 and V-07 and adds a fifth limit (the probe proves the partition only). E-05 and V-05 now deny six things, including default runs and hardened runs without an allow list. F-11 added. |
| PR-1005 | MEDIUM | IN-SCOPE | Audit thoroughness | `no-push` measured at 2 lines case-sensitive vs 8 case-insensitive; CHANGELOG is excluded from sub-check (d) although OQ-02 calls it "most likely to be quoted" | The fixed terms left the grep command unfixed, so case sensitivity decided the audit's reach, which is the exact defect F-3 names. The audit also skipped the file this plan itself writes. | Overall:Low | FIXED | One fixed command, `grep -n -i -F`, counting lines, over all four files including CHANGELOG. Review-time counts recorded as context only. |
| PR-1006 | LOW | IN-SCOPE | Docstring count / OQ contract | "The two runner-safety capability names" and "Decide the two runner-safety capabilities" against a four-member tuple; OQ-02 had `- Owner: none` | E-01's "correct any prose that counts" did not identify these two stale counts. The OQ owner was empty. | Overall:Low | FIXED | Both sites named in E-01 and V-01. Owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What should the docs say about a hardened run with no allow list? | Filesystem confinement stays, with no egress filtering; filtering engages only with a declared allow list. | Keep "refuses without one": rejected because it contradicts `2j4pd0` PR-805 and `m0kl28` OQ-01. | `2j4pd0` E-04 as revised. | yes |
| D-2 | How should the audit grep be fixed? | `grep -n -i -F`, counting lines, over spec, docstring, docs and CHANGELOG. | Case-sensitive: rejected, since it misses limit 4's "**No-push". | Review measurement 2 vs 8. | yes |
