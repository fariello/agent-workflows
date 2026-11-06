# Review findings: plan uog8nc

- Subject-Id: uog8nc
- Subject-Type: ipd
- Reviewed-At: 2026-11-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `3c7f9c987` in runner review-sweep lane `run-20261106T033613Z-1047571` (non-interactive). The lane-input copy (revision 2) is byte-identical to the tracked plan (committed, unmodified), so no pre-review snapshot. `aw ipd lint --phase author` was clean before revisions with zero findings. After revisions `--phase review-finalize` is clean with zero findings.

Controlling context: the maintainer's `g4719s` OQ-02 answer (2026-11-05) keeps the standard at `.aw/system/workflows/technical-writing/technical-writing.md` with no dash rule of its own. Sibling Order 07 `sfez3e` was reviewed in the same lane (commit `13f9026a8`, merged as `3c7f9c987`); this plan has the same sweep shape and its fixes follow that review, adapted to backlog items.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern | "18 open, 6 graduated, 15 parked ... about 76 KB" as fact | Re-measured 27/6/15, about 143 KB, marked as context | PR-006. |
| Scope | "per changed item"; listed fields | Every swept item; whole metadata block and other protected elements | PR-001, PR-002. |
| E-02, E-03 (old) | Sweep, then note changed items by id6 | One item unit per item: proofread, diagram, annotate, note, guard, commit | PR-001, PR-003, PR-007. |
| E-03 (new) | Metadata diff, "no metadata changed" | Full guard with `--final` | PR-002. |
| E-04 | `<date>-writestd-08-backlog-sweep-walkthrough.md` | `set_records.write_walkthrough` with own id6 and `Target-Id` | PR-005. |
| E-05 (new) | none | Backlog carrier for `Unresolved` annotations | PR-004. |
| E-06 | Check, gate, commit | Adds sanitizer and committed-path proof | PR-010. |
| Conventions, gate | `standards/technical-artifact-writing.md`; "Purpose and scope" | Shipped path; actual section names | PR-008. |
| Gate | Partial contract | Full execution contract | PR-009. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No: backlog items are not contracts other code relies on, and no spec or interface changes.
2. No.
3. Moderate: 6 E-items in 3 task groups; 48 small files of one record type.
4. Yes: four directory Scope-Paths.
5. Yes, bounded: a rewording can break a quoted passage or a code citation another artifact relies on, and a changed metadata field could move an item between release-gate states. The guard covers both.

Tier: standard.

### Step R1

- Checked: spec `ecmw83` R-04, R-08, R-11, MD-5, N3, AC-06, AC-08; the shipped standard's section names (no "Purpose and scope"); `aw find backlog --status-not done` (27 open, 6 graduated, 15 parked; no `blocked/` directory); total size 142,592 bytes, largest item 32,268 bytes; no em or en dash in live items; no Mermaid block in live items; metadata field census (48 items each carry `Id`, `Status`, `Set`, `Priority`, `Work-Kind`, `Summary`; 13 carry `Blocks-Release`; 4 `Graduated-To`); `aw backlog note --help` ("Item selector: an id6, a filename, a stem, or a path"); `set_records.write_walkthrough`; D140; `.aw/records/walkthroughs/README.md`.
- Probe: in a scratch git repo inside the lane, `aw backlog note zvyo35 --message ...` prepended `- 2026-11-06 note (aw backlog): ...` under `## Workflow history` and changed nothing else.
- Concern counts were stale (18 open measured as 27; 76 KB measured as 143 KB) (PR-006).

### Step R2

- Checked: E/V bijection 6/6; each `V-*` demands pasted commands, hashes, or guard output; no runtime-observation demand; spec trace cites `ecmw83` R-04, R-08, R-11, AC-06, AC-08 qualified; `- Item-Dependencies:` match orchestrator `8fvkmp` row 08; every Scope-Path resolves (`check_engine.stale_record_scope_paths` reports none for this plan); `aw check all` has no non-info diagnostic for this plan.

### Step R3

- Checked: no code or trust boundary. E-06 runs `aw sanitize --agent` because the records are public and rewording could introduce a local path.

### Step R4

- Checked: invariants mapped to the guard: metadata block (covers every gate and release-gate field and `Summary`), headings, stable IDs, inline code spans, numbers, non-diagram fenced blocks, history records, modal verbs, text quoted elsewhere, and exactly one sweep note per item. The guard is a validation script kept under `.aw/state/`, not a repository test.
- Guard sensitivity measured in a scratch copy: a `- Priority:` change, a shortened code-span citation, and a changed quoted passage each produced a problem line and exit 1; an `aw backlog note` alone gave `--final` `problems=0`. Full run at HEAD: about 9 seconds, `TOTAL live=48 checked=48 problems=0`.
- Right-sizing: 48 items at about 143 KB fit one E-item of per-item committed units; no split needed.
- Spec sync: N/A, substantiated (no spec file is in scope).

### Step R7

- Checked against `sfez3e` (same lane, already revised): same guard, unit, carrier, and walkthrough design; different `Unresolved` prefix (`BW-` here, `SW-` there) so the two carriers do not collide. `sfez3e` E-06 may create a carrier in `backlog/open/` before this plan runs; it is live at BASE and swept. `381ml6` (Order 09) depends on this plan and is reviewed separately.

### Step S5

- Checked: no pre-existing open question; dash handling follows the maintainer ruling and AC-06 as written (D-1); other choices recorded as D-2 to D-4. No question needs the human.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | high | UNDER-SCOPE | D invariant | `ecmw83` R-08 "Each swept artifact must get one history line" | Only changed items were noted. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Every swept item gets the note; `--final` checks exactly one per item. |
| PR-002 | high | UNDER-SCOPE | D invariant; E testing | `ecmw83` R-08; 159 passages in live items quoted elsewhere; code-span citations | Only listed metadata keys were diffed; nothing caught a changed heading, ID, code citation, number, history record, or quoted passage, and unlisted keys such as `Graduated-To` were unprotected. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Guard script added and measured; whole metadata block protected. |
| PR-003 | medium | IN-SCOPE | R4 right-sizing | old E-02 | E-02 bundled proofreading, dash replacement, diagrams, and annotation for all items with no commit or resume rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Item unit with ordered steps, one commit per item, resume rule. |
| PR-004 | medium | UNDER-SCOPE | G executability | walkthroughs README "nothing scans its contents for outstanding work" | `Unresolved` annotations lived only in an untracked walkthrough. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-05 files one backlog carrier. |
| PR-005 | medium | IN-SCOPE | R1 references | D140; `set_records.write_walkthrough` | The walkthrough name lacked the clustered grammar and its own id6. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-04 uses `write_walkthrough`. |
| PR-006 | low | IN-SCOPE | R2 live counts | Concern "18 open ... about 76 KB" | Stale live-artifact counts stated as fact. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Re-measured and marked as context; E-01 re-derives. |
| PR-007 | medium | IN-SCOPE | D invariant | `technical-writing.md` "This standard adds no dash rule of its own"; `g4719s` OQ-02 | E-02 required replacing every prose dash, assuming the widened rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Reword only dashes the advisory reports (AC-06 as written); AC-06 deferred to `8fvkmp`. |
| PR-008 | high | IN-SCOPE | R1 references | `g4719s` OQ-02 answer | Conventions and gate named `standards/technical-artifact-writing.md` and a "Purpose and scope" section, neither of which exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Shipped path and real section names. |
| PR-009 | medium | IN-SCOPE | G execution contract | plan gate | Gate lacked fence-as-declaration wording, the paste-output MUST, never `git add -A`, finalize ownership, and Order preconditions. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Gate rewritten. |
| PR-010 | low | UNDER-SCOPE | B privacy | AGENTS.md leak-sanitizer paragraph | No sanitizer run over rewritten public records. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-06 runs `aw sanitize --agent`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Remove every prose dash from backlog items? | Only dashes `backlog.prose-dash` reports | Remove all; ignore dashes | `g4719s` OQ-02 maintainer answer 2026-11-05; `ecmw83` AC-06; 0 dashes in live items at review | yes |
| D-2 | Note every swept item or only changed ones? | Every swept item | Changed only | `ecmw83` R-08 | yes |
| D-3 | Protect `- Summary:` though R-08 does not name it? | Protect the whole metadata block; suggest wording in the walkthrough | Allow summary edits | Original plan convention (duplicate detection identity surface); R-08 identity clause | yes |
| D-4 | Should the sweep re-verify and update stale `path:line` citations in items? | No; keep every code span | Re-verify and rewrite | A writing correction does not change evidence (standard "How it combines with other rules" item 3); re-verifying citations is a separate task | yes |

## Round 2

Re-reviewed at HEAD `604e5498f` in runner review-sweep lane `run-20261106T170833Z-1417128` (non-interactive). The lane-input copy (revision 2) is byte-identical to the tracked plan (committed, unmodified), so no pre-review snapshot. `aw ipd lint --phase author` was clean before revisions; `--phase review-finalize` is clean after them. Round 1 findings PR-001..PR-010 stay fixed. This round applies to `uog8nc` the guard defects that the round 2 review of sibling `sfez3e` measured (its PR-101..PR-104), re-measured here on backlog items. All mutations ran in a scratch clone under `.aw/state/uog8nc-review/` (gitignored); no tracked item was modified.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Concern | 48 live items (27 open) | 49 live items (28 open), still context only | Re-measured; E-01 re-derives. |
| Scope | "metadata block" | "title line or metadata fields ... every `- Key:` field before the first `## ` heading" | PR-101. |
| Definitions, "Do not change" bullet | Whole pre-heading block frozen; modals `must`/`should`/`may`; IDs like `R-08` | Title and `- Key:` fields frozen, preamble prose proofread; modals include `shall`, `never`, and `not` forms; IDs include `D140` and id6 | PR-101, PR-102, PR-103. |
| E-01, V-01 | Baseline only | Format check against the metadata cutover first, with pasted evidence | PR-104. |
| Findings | none | Two bullets: `cxxmyv` cutover risk; round 2 guard measurements | PR-102..PR-104. |
| Required tests, guard script | Round 1 guard | Revised guard and its re-measured behavior | PR-101..PR-103. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No: it edits backlog item text only; no spec, interface, or contract changes.
2. No: no code guarding private data, commits, worktrees, merges, or the sandbox.
3. No: 49 small items (about 143 KB), 6 E-items in 3 task groups, one procedure.
4. Yes: four directory Scope-Paths.
5. Yes, moderately: a rewording can change what an item asks for or break a quoted-text citation, but each item is its own commit and is easy to revert.

Tier: standard.

### Step R1

- Checked: guard script extracted verbatim from the plan; `aw backlog note --help` (takes a path); scratch probe of `aw backlog note <path>` followed by `--final` gave `sweep-notes=1 problems=0`; `aw find backlog --status-not done` (49 live: 28 open, 6 graduated, 15 parked); `aw backlog check --agent` clean; zero em or en dashes in live items; `.aw/config/project.json` has no `metadata_schema` key.
- Census of live items: 1 item has a prose preamble before the first `## ` heading (`ms06pi`, 42 lines starting "MAINTAINER DIRECTION 2026-09-05"); 191 bare id6 references and 17 decision numbers lie outside code spans; 48 negated modals or `never`.

### Step R2

- Checked: E/V bijection 6/6; the new E-01 clause has its V-01 demand; dependencies and Scope-Paths unchanged.

### Step R3

- Checked: no code or trust boundary; E-06 runs `aw sanitize --agent`.

### Step R4

- Guard sensitivity, scratch clone of HEAD `604e5498f`. Round 1 guard (g1) against revised guard (g2): preamble reword in `ms06pi`, g1 exit 1 `metadata block changed` (false refusal), g2 exit 0; `must` to `must not` in `n2lr..`, g1 exit 0 (missed), g2 exit 1 `modal count fell: must 2->1`; `must not` to `must`, g1 exit 0, g2 exit 1; `never` to `always` in `c1f6rd`, g1 exit 0, g2 exit 1; `should` to `may`, both exit 1; `25kzda` removed from `c1f6rd` body, g2 exit 1 `stable id removed: 25kzda`; `- Summary:` change and `- Priority:` change, both exit 1; unchanged tree, both exit 0. Full g2 run: `TOTAL live=49 checked=49 problems=0`, exit 0, about 9.5 seconds.

### Step S5

- Checked: no open question. The cutover ordering is resolved from evidence, as in `sfez3e` round 2 D-1 (D-1 below).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | medium | IN-SCOPE | R4 executability | guard `parts` returned `lines[:end]`; item `ms06pi` 42-line preamble; scratch reword gave `metadata block changed` | The guard froze every line before the first `## ` heading, so the one item with a prose preamble could not be proofread. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Guard compares only the title and `- Key:` fields with continuation lines; definitions say preamble prose is proofread. Re-measured. |
| PR-102 | high | UNDER-SCOPE | D invariant | guard modal regex matched only bare `must`, `should`, `may`; scratch `must` to `must not` gave exit 0 | Negating or un-negating an obligation, or dropping a `never`, passed the guard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | Modal regex counts `must`, `should`, `may`, `shall`, `never`, each with optional `not`. Re-measured. |
| PR-103 | medium | UNDER-SCOPE | D invariant | guard `stable_id` pattern; 191 bare id6 references and 17 decision numbers outside code spans | Decision numbers and bare id6 references were unprotected, though the plan forbids changing stable IDs. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | `stable_id` also matches `D\d{2,4}`, four-digit IDs, and six-character base36 tokens with a digit and a letter. Re-measured. |
| PR-104 | medium | UNDER-SCOPE | R7 cross-plan | `cxxmyv` Concern "runs migration `m0001`"; `4sd62s` Section 5.2 "Delete the legacy bullet block" | If `cxxmyv` lands first, the guard and `aw backlog note` work on a format that no longer exists. | C:Low; U:Low; S:Low; F:Low; Overall:Low | fixed | E-01 checks for `metadata_schema` and for `- Status:`/`## Workflow history` in every live item and stops with a report if either fails; V-01 pastes the check. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `uog8nc` handle the `cxxmyv` metadata cutover landing first? | Precondition check in E-01 that stops with a report | An `Item-Dependencies` edge on `cxxmyv` (wrong direction); rewrite for the log format now (not shipped) | `cxxmyv` `Attended: required`, Status `reviewed`; `4sd62s` Section 5.2; no `metadata_schema` key at HEAD | yes |
| D-2 | Protect bare id6 tokens, accepting false matches? | Protect them | Protect only backticked ids | Plan Scope forbids changing a stable ID; a false match only blocks a rewording, never permits one | yes |
