# Review findings: plan w89bo8

- Subject-Id: w89bo8
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032752Z-4094028` at HEAD `2745954be`. The plan was
committed and byte-identical to the sealed lane input (rev-9, sha256 `b2856abd...`); no snapshot needed.
`- Kind: child`, so `IPD-S407` and `IPD-S408` do not apply. `aw ipd lint --phase author` clean before review;
`review-finalize` clean after.

Re-driven in-process with a throwaway `XDG_CONFIG_HOME`: `defaults.migrate_layout`, `color_depth`, `aw_home` ->
exit 0, `'\n'`; `defaults.backup` -> exit 0, `'true\n'`; `repos.search` -> exit 0, `'[]\n'`; `no.such.key` -> exit 2
"Unknown config key ... Valid keys: ..."; `config.normalize({"aw_home": ""})` drops the key; `config get` and
`conf get` description length 335, help 76; no `config get` key in `cli._DESCRIPTIONS`. All match F-01/F-03/F-07.
Suites at review HEAD: `python3 -m pytest` -> `2 failed, 5219 passed, 2 skipped` (both failures in
`tests/test_readiness_absence_invariant.py`, which pick the unrelated pending plan `l4vw9o`); `python3 -m pytest -m slow`
-> `237 passed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G executability / live-artifact baseline | `.aw/records/plans/executed/20260929-g0bdgg-01-ypnk56-...ipd.md` "- Status: executed"; `tests/test_subparser_descriptions.py` exists; `-m slow` -> `237 passed` | E-06/V-06 required the slow set to still fail `SubcommandDescriptionTests` with the same eight gaps and compared to fixed counts (`3692 passed`, `1 failed, 202 passed`). `ypnk56` has executed, so that demand is unsatisfiable on a correct execution, and the counts are live-artifact bars the rubric forbids. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06/V-06 now record a pre-change baseline at the executing HEAD and compare failing-node sets; both description-contract tests must pass. F-08/F-09, conventions, deferred, scope check and OQ-02 updated. |
| PR-002 | MEDIUM | IN-SCOPE | A correctness (documentation honesty) | OQ-01 (c) "`config show` or the config file is where to look"; driven `config show aw_home` -> `aw_home              = -` both unset and with hand-written `""` | The chosen replacement wording names `config show` as a route to the unset/empty distinction. It is not: `show` renders both states identically. Shipping it would repeat the defect the plan exists to fix. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 forbids naming any route (exit code, `--json`, `config show`); wording must say an empty value is not stored and reads as unset. OQ-01, F-04 and V-02 corrected. |
| PR-003 | LOW | IN-SCOPE | E testing | E-03 "requiring that it does not claim a nonzero or failing exit ... Anchor (2) on the specific falsehood" | The description guard was underspecified: a negative-only check is evaded by rewording, and how to detect a "claim" was left to the executor. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires a negative falsehood-token limb plus a positive authored exit-0 content anchor (same shape as `test_alias_shows_canonical_authored_prose`); V-03 demands both. |
| PR-004 | LOW | IN-SCOPE | G executability / stale references | gate "create `tests/test_subparser_descriptions.py`, which `ypnk56` creates"; "Backlog `uip0z6` is set `graduated` by the runner"; backlog file in `.aw/records/backlog/graduated/` | Scope fence and gate described `ypnk56` as pending and `uip0z6` as not yet graduated; both are stale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Fence now forbids editing `ypnk56`'s shipped test and `tests/test_cli.py`; gate states `uip0z6` is already graduated and closes via HANDOFF. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the replacement help name any route to the unset/empty distinction? | No; say an empty value is not stored and reads as unset | name `config show` (driven false); name the config file (toolkit ignores it, misleading); drop the topic silently (leaves the natural question unanswered) | driven `config show aw_home` identical in both states; `config.normalize` drops `""` | yes |
| D-2 | What baseline should E-06 compare against now that `ypnk56` executed? | Re-derived failing-node set at the executing HEAD | update to review-HEAD counts (would rot again) | rubric G live-artifact convention; measured suite drift | yes |
