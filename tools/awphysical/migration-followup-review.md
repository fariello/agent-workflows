# Independent follow-up review of an AW physical-layout migration

Act as an independent migration reviewer. The migration executor has already reported its
result, but its summary is not evidence. Your job is to determine whether the repository and
all attached AW storage roots actually satisfy the approved physical-layout policy, whether
anything was lost or exposed, and what still requires review.

Do not assume there is a defect merely because this instruction is skeptical. Report only
findings supported by observed files, Git state, deterministic tool output, or a clearly
labeled inference. Do not repair, move, delete, stage, commit, push, change a remote, change
policy, rerun migration, or run cleanup during this review.

## Inputs to locate

Locate the migration evidence paths from `aw migrate-layout status --json` or ask the operator
for them if status cannot resolve them. You need:

1. The frozen pre-migration inventory JSON.
2. The human-approved migration-map JSON.
3. The migration transaction journal and final switch receipt.
4. The deterministic comparison report.
5. The deterministic postcheck report.
6. The current `aw context --json` output.
7. The target repository path and every companion, source, home, or custom Git boundary.
8. The retained legacy-root mapping and rollback instructions.
9. The scenario/test evidence cited for this repository's selected preset.

If any required input is missing, mark the review NO-GO and identify exactly what is missing.
Do not reconstruct missing evidence from the executor's prose.

## Review procedure

### 1. Establish authority and input freshness

- Run `aw migrate-layout status --json` and `aw context --json` from the target repository.
- Confirm the transaction ID, inventory ID, policy digest, migration-map digest, project ID,
  target identity, companion identity, source role, and Git common directories agree across
  all evidence.
- Confirm the current transaction phase is `verified` or `independently-reviewed`.
- Confirm there is one authoritative layout and the legacy writer is disabled.
- Treat stale, mismatched, ambiguous, or inaccessible evidence as NO-GO.

### 2. Re-run deterministic comparison and postcheck

- Re-run the production equivalents of:

  ```bash
  python3 tools/awphysical/aw_layout_compare.py <the exact saved bindings and evidence>
  python3 tools/awphysical/aw_layout_postcheck.py --context <current-context-evidence>
  ```

- Capture actual stdout, stderr, and exit status.
- Compare the new report IDs and findings with the saved reports.
- A nonzero status, skipped required check, stale input, partial report, or report mismatch is
  NO-GO. The executor's earlier green result cannot override it.

### 3. Check content accounting

- Confirm every inventory item appears exactly once in the approved migration map.
- For `copy` and `deduplicate`, confirm the destination exists and matches required hash/type.
- For `retain`, confirm the source still exists and matches the inventory.
- For `exclude`, confirm there is explicit human approval and a specific reason.
- Examine every unknown, modified-managed, foreign, collision, and unsupported item. Confirm it
  has an explicit disposition rather than being silently omitted.
- Confirm no destination item exists without a map/evidence origin unless it is a documented
  post-migration generated file with its own owner and test.

### 4. Check physical segregation and ownership

- Confirm canonical system content is under the resolved `system` root and does not contain
  records, mutable action progress, local config, caches, transaction files, or backups.
- Confirm portable project policy is under `config/project.json` or its approved external
  equivalent.
- Confirm machine-local config is not tracked.
- Confirm durable operational state is under `state/durable/`.
- Confirm locks, transactions, backups, cache, and temporary data are under `state/runtime/`
  and are not tracked.
- Confirm workflow-created plans, prompts, specifications, assessments, research,
  communications, incidents, and run evidence are under the resolved records root.
- Confirm host-required files outside `.aw/` are thin, generated, manifest-owned adapters and
  contain no independent workflow body or record.

### 5. Check each Git boundary independently

For the target, companion, and source repositories separately:

- Run `git status --short`.
- Run `git diff --cached --name-only`.
- Inspect the merge-base delta if the migration has been committed locally.
- Confirm every changed/staged path belongs to that repository's approved migration plan.
- Confirm no private companion path, candid record content, machine path, local config, or
  runtime state was written into a public target.
- Confirm no command staged or committed across repositories, and no migration command pushed.
- Do not infer remote privacy from its URL. Confirm only the explicit acknowledgement and
  observable remote/reachability facts the policy records.

### 6. Check routing and legacy behavior

- Compare the declared producer inventory with the producer evidence set. They must be equal.
- Exercise the approved non-mutating/sandbox probe for every producer class.
- Confirm each producer resolves exactly one intended destination and Git owner.
- Confirm no producer recreates `.agents/plans`, `.agents/prompts`, `.agents/docs`,
  `.agents/comms`, or `workflow-artifacts` as a write destination.
- Confirm legacy compatibility is read-only, bounded by version/time or migration state, and
  invalidates ambiguous dual copies.
- Confirm indexes, `aw attention`, `/whatnext`, actions, history, archive, and reference checks
  work when records/state are external.

### 7. Check source-checkout behavior when applicable

- Confirm source-checkout role was established through approved structural/identity evidence,
  not merely matching filenames or an origin URL.
- Confirm `aw install` cannot overwrite developer-owned canonical framework source.
- Confirm packaging and tests consume one canonical system source and no duplicate normative
  workflow tree remains.
- Confirm the framework repository's own records were preserved and routed like any other
  project's records.

### 8. Check recovery and retention

- Confirm rollback inputs, old-to-new mapping, hashes, and instructions remain accessible.
- Confirm retained legacy sources are read-only/non-authoritative and did not become newly
  public or newly tracked.
- Confirm a tested resume and rollback path exists for the final transaction phase.
- Confirm cleanup is still separately gated and cannot remove changed, foreign, unverified, or
  still-required retained material.
- Do not recommend cleanup until retention conditions and independent verification are met.

### 9. Check scenario and validation honesty

- Identify the exact row in `tools/awphysical/migration-scenarios.json` for this project.
- Confirm every required test/gate for that row actually ran after the final migration change.
- Inspect actual outputs and exit statuses. Do not accept a copied summary or model-authored
  `tests passed` statement.
- Confirm unsupported/skipped checks are labeled and do not contribute to a green verdict.
- Confirm the full repository regression suite and package/source gates ran when required.

## Finding rules

For each finding, record:

- Stable finding ID.
- Severity: BLOCKER, HIGH, MEDIUM, or LOW.
- Fact or inference.
- Exact evidence path, command, rule ID, or Git path.
- Expected contract.
- Observed result.
- Required owner/Order and next action.
- Whether migration completion or cleanup is blocked.

Do not report stylistic preferences, speculative future risks without a concrete failure path,
or duplicate symptoms as separate root causes. If a concern cannot be verified because evidence
is unavailable, report the missing evidence rather than asserting the defect.

## Required final report

Return these sections:

1. Verdict: GO, NO-GO, or REVIEW REQUIRED.
2. Evidence freshness and identity table.
3. Deterministic command results with actual exit statuses.
4. Content-accounting totals: inventoried, mapped, verified, retained, excluded, unexpected.
5. Physical-root and ownership table.
6. Git-boundary table for every repository.
7. Producer/consumer and legacy-write results.
8. Source-checkout results, or `not applicable` with reason.
9. Rollback, retention, and cleanup readiness.
10. Findings table ordered by severity.
11. Specific follow-up work, mapped to the owning IPD or a new corrective IPD.
12. A short statement of what you checked and what you could not check.

A GO verdict requires all deterministic gates to pass, complete content accounting, no open
BLOCKER/HIGH findings, correct Git/privacy boundaries, one authoritative writer, and verified
rollback retention. Otherwise return NO-GO or REVIEW REQUIRED and say exactly why.
