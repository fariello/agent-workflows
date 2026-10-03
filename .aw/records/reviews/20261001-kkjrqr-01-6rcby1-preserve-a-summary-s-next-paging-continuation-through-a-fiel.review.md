# Review: Preserve a summary's next paging continuation through a --fields projection

- Subject-Id: 6rcby1
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits. `--phase review-finalize` was clean after them.

I re-verified the following at lane HEAD `51c5a7bbf`:

- `agent_schema._PRESERVED_FIELDS` is `_MANDATORY_FIELDS | {"applied", "total", "emitted", "omitted"}`, and its comment claims "every field validate_agent_record consults".
- `filter_record_fields` has its early return.
- `render_summary` has call sites only at `renderers.AgentRenderer.render_stream` and `run_analytics_cli._emit_query_agent`.
- The `run_analytics_cli` comment carries the sentence E-06 quotes.
- `docs/cli-output-contract.md` contains Section 6 `--fields`, Section 11.1 "`next`: the suggested broadening or fallback command", and Section 11.4 "a `next` recovery command".
- `d6u2hz` is open and was committed in `a976a53f8`.
- `kkjrqr` is graduated.
- `8jeh4x` is open and owns the reachability failure.
- Neither doc contains an em or en dash.

Live reproduction, run in-process with `--agent` placed after the subcommand:

| Command | Unprojected `next` | Under `--fields findings` |
|---|---|---|
| `releases show zzzzzz` | `aw releases list` | absent |
| `runs query bogusview` | `aw runs query schema` | absent |
| `find zzzzzz` (`complete: true`) | `aw find` | absent |

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Test validity (E) | review probe: `cli.main(["--agent","releases","show","zzzzzz"])` -> rc 2, stdout `''`, stderr sentence; `cli.main(["releases","show","zzzzzz","--dir",tmp,"--agent"])` -> `{"kind":"error",...,"next":"aw releases list"}` | E-01 tells the executor to drive `cli.main` "with `--agent`" but does not say where the flag goes. In-process, a leading or mid-path `--agent` yields HUMAN output. The test would then parse zero records, so it could pass vacuously or fail for the wrong reason. E-01 also does not isolate the command from the live tree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now requires the flags to come after the subcommand, a `--dir <tmp git repo>` fixture, and an assertion that exactly one agent record was parsed. The measured values are recorded. |
| PR-002 | MEDIUM | IN-SCOPE | Traceability (G) | `## Proposed changes` items 1-5 cite `(E-01)`..`(E-05)` while the checklist has E-01..E-06 | The Proposed-changes list folds E-02 into item 1 and labels every later item one E-id too low. A reader cross-referencing would point at the wrong item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The list is renumbered 1-6 and each item now cites its correct E-id. |
| PR-003 | MEDIUM | IN-SCOPE | Execution contract (G) | Required tests: "must list exactly the four `- Scope-Paths:` entries plus this plan plus `d6u2hz`"; `git log` shows `d6u2hz` already committed in `a976a53f8` | The staged-set check demands that a file appear which is already committed and outside the Scope-Paths. That demand is unsatisfiable, and it invites the executor to re-touch the carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The check now names Scope-Paths only and forbids re-staging `d6u2hz`. The Scope check sentence is corrected. |
| PR-004 | LOW | IN-SCOPE | Evidence accuracy | Required tests "rises by exactly the tests E-01 adds" vs E-06/V-06 "E-01 and E-02"; V-06 "if none exists say so plainly" while `8jeh4x` is open for that failure | Two problems: the count bar contradicts itself, and the owner of the reachability failure was left unresolved even though the repository answers it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The count bar now reads "E-01 and E-02" everywhere. `8jeh4x` is named in E-06, V-06 and Deferred. `aw check` is now compared against a pre-edit run. |
| PR-005 | LOW | UNDER-SCOPE | Execution contract (G) | `## Approval and execution gate` | The gate has no scope-fence semantics and does not say whether the runner or the executor owns the finalize transition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the scope fence (`--scope-reason`/`--scope-ack`), runner-vs-manual finalize ownership, a no-`git mv` rule, and the `kkjrqr` gate note. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does OQ-01's choice of fix (a), unconditional preservation, stand? | Yes | (b) preserve only when `complete` is false. Refuted: `find zzzzzz` strands with `complete: true` (re-measured). (c) document only. | review reproduction table; `docs/cli-output-contract.md` Section 11.1 | yes |
| D-2 | Should E-01 run against the live tree or a fixture? | A `--dir` tmp git repo fixture | The live tree (couples the test to concurrent writers; F-14's own warning) | review probe output with `--dir` | yes |
