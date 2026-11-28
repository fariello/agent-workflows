# IPD: Adopt AceLM artifact IDs

- Date: 2026-11-27
- Kind: child
- Concern: New artifact IDs are hard to recall and differ from the AceLM format.
- Scope: Agent Workflows artifact ID readers, new ID issuance, repository upgrade, and compatibility checks.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/artifact_naming.py, agent_workflows/artifact_adopt.py, agent_workflows/artifact_meta.py, agent_workflows/artifact_refs.py, agent_workflows/selectors.py, agent_workflows/check_engine.py, agent_workflows/research_contract.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_lint.py, agent_workflows/completion.py, agent_workflows/runner_shared.py, agent_workflows/git_commit_helper.py, agent_workflows/cli.py, agent_workflows/config.py, agent_workflows/migrations/chain.py, agent_workflows/migrations/artifact_ids.py, tests/test_artifact_id_transition.py, .aw/system/cutover/metastore-code.cutover.patch, .aw/system/workflows/migrate/migrate.md, .aw/records/specs/**/20260817-2147-01-uniform-artifact-naming-grammar.spec.md, .aw/records/specs/**/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md, .aw/records/specs/**/20260730-2152-01-agents-artifact-organization.spec.md
- Item-Dependencies: none
- Status: to-review
- Short-Description: Adopt the AceLM ID format for newly issued artifacts and preserve issued IDs
- Work-Kind: feature
- Priority: medium
- Set: acelm-ids
- Order: 1
- Highest E allocated: 04
- Author: OpenAI
- Id: 2mbc20

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-28 to-review (aw set): Prepared the AceLM ID adoption plan for review
- 2026-11-28 draft (OpenAI): created.

## Goal

Agent Workflows should adopt the ID format from [AceLM artifact identifiers, spec 3avyss](https://chatgpt.com/library?file_id=libfile_a0709a029fa481919aea67b4f8959a1c&account_id=a27d7fc2-8408-45e7-935f-06618cd7f36b). AceLM's approach is a better fit for human recall. In `43bim-tox82`, a reader can rehearse the middle as “bimtox” and use the numbers to confirm the match. The format gives both tools a shared grammar and about 15 times the six-character keyspace. The hyphen also rules out matches on unbroken hex strings.

## Detailed Implementation Checklist (TODO)

### Accept both formats

- [ ] E-01 Update Agent Workflows readers and shared ID helpers for both canonical forms.
  - Depends on: none
  - Expected outcome: Existing six-character IDs and `43bim-tox82` resolve through filenames, selectors, dependencies, reviews, and history. Only explicit ID lookup accepts `43bimtox82`.
  - Execution state: pending

### Issue the new format

- [ ] E-02 Add new-format allocation with a per-repository issuance gate.
  - Depends on: E-01
  - Expected outcome: Enabled repositories mint the AceLM format. The owning repository checks each allocation against prior and concurrent claims, including terminal records. Other repositories retain their prior issuance mode.
  - Execution state: pending

### Upgrade a repository

- [ ] E-03 Add the repository preflight and enablement path to the existing migration workflow where a persistent change is needed.
  - Depends on: E-02
  - Expected outcome: The preview identifies prerequisites, affected paths, and blockers. Explicit apply enables issuance only when supported tools are ready. Existing IDs remain resolvable throughout.
  - Execution state: pending

### Prove compatibility

- [ ] E-04 Rehearse the transition in an isolated Agent Workflows repository and synchronize the affected documentation.
  - Depends on: E-03
  - Expected outcome: The rehearsal covers both ID formats, rollback before issuance, and pausing issuance after a new ID exists. The command help and naming contract match the behavior exercised.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `artifact_core.mint_id6` checks a repository-wide inventory. Its current scan and generation are separate operations. New issuance must also address concurrent claims.
- `artifact_naming.parse_clustered` owns the clustered filename grammar. A hyphen inside the ID needs to remain inside the identity field. A review may carry its subject's ID in the filename.
- `aw migrate` already runs pending layout and metadata upgrades. `aw migrate metadata` tracks progress and supports recovery. The proposed ID enablement can reuse those patterns.

## Findings

Six-character assumptions also occur outside the shared matcher. Search the code, templates, and tests for ID regexes, length checks, hyphen splitting, and `id6` fields. Classify each site by use before replacing it. Some six-character tokens belong to other formats, and some `id6` fields are compatibility keys. Existing artifact filenames, citations, and append-only logs also depend on the issued ID.

## Proposed changes (ordered, validatable)

1. Upgrade readers first. Replace confirmed artifact-ID assumptions with the shared validator and the parser appropriate to each context. Audit selectors, completion, status and review checks, references, run and Git integration, metadata mirrors, history paths, and index rebuilds. Keep persisted key names readable. Test an ID inside a filename whose set name also contains hyphens, including a standalone spec that uses the new ID as its set name. Keep the canonical hyphen in free-text extraction and on disk.
2. Add the generator and reserve each ID at creation. Reuse the owning repository's write or integration lock where it covers the writers. A checkout-local lock cannot coordinate independent clones. Validate the publication conflict check for any such configuration before enabling issuance there. Report an allocation conflict without editing the existing record or its history.
3. Make enablement opt-in. Propose `aw migrate artifact-ids` only if a persistent upgrade needs migration machinery. If preflight shows that a config change and a rebuild of derived indexes suffice, use existing configuration and migration reporting. Keep existing layout and metadata upgrade order. Any ID-specific apply must be explicit because bare `aw migrate` already applies pending steps. Report exact planned changes, refuse stale previews, and reuse locking and recovery where applicable. Use targeted find and replace for code, templates, and generated fixtures. If a prerequisite layout upgrade moves a path, let its existing path map and reference updater handle the move. Preserve issued IDs, their typed references, historical prose, filenames, and authoritative history. A retry must reuse a completed enablement or recover an interrupted one.

~~~mermaid
flowchart TD
    A["Install dual-format readers"] --> B["Preview repository upgrade"]
    B --> C{"Readers and writers ready?"}
    C -->|No| D["Keep prior issuance mode"]
    C -->|Yes| E["Enable new issuance"]
    E --> F["Verify both formats"]
~~~

## Deferred / out of scope (with reason)

Existing artifacts keep their original IDs. Reissuing those IDs would need its own decision about external links and append-only history. AceLM changes and other identifier types are outside this implementation.

## Scope check

- Over-scope: Historical artifact rewrites and project-wide changes to unrelated identifier types.
- Under-scope: Include both the live readers and any staged metadata-cutover changes that would restore a six-character restriction. If the audit finds another affected caller, name it and justify its change in scope reconciliation.

## Required tests / validation

Run focused parser and allocation tests. Rehearse the upgrade on a mixed-format repository fixture. Use `aw find` and `aw check` on the fixture, then rebuild its index and repeat the resolution checks. The validation checklist specifies the evidence to capture.

## Spec / documentation sync

Use AceLM `3avyss` as the sole design reference. Align Agent Workflows' existing naming, organization, and metadata contracts listed in the scope with its adopted format. Update the migration workflow and command help to explain when a repository needs to run a migration and how to pause issuance.

## Open questions

None. The implementation verifies whether persistent changes require a separate migration subcommand.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect the evidence in a separate pass. Record the actual output before marking a validation item complete.

- [ ] V-01 validates E-01
  - Required evidence: Paste focused test output covering both canonical IDs, exact and compact lookup, free-text hex rejection, the repeated ID in a standalone spec filename, dependency resolution, review subject lookup, and history after index rebuild.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Paste test output for a forced collision with a terminal ID, two writers choosing the same ID, an interrupted creation and its retry, and issuance disabled and enabled. Include any publication configuration used to claim support for independent clones.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Paste the preview and apply results, the affected-path diff, and repeat-apply output. Show an old-reader refusal and an interrupted or stale apply that leaves the prior issuance setting recoverable. If configuration alone suffices, show that preflight reports no file-format migration.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Paste the mixed-format rehearsal output from creation, lookup, checks, and rebuild. Compare legacy filenames, typed references, and history bytes before and after. Show that pausing issuance preserves reads of the new ID. Include the docs and help diff.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: One ID contract spans readers, writers, and repository upgrades. Keep the issuance switch behind verification of the mixed-format path.

Run `aw ipd begin` after review and approval. Keep edits within the declared scope. If the work requires another file, justify the change in the two-way scope reconciliation at finalize. Record concrete evidence for every validation item before `aw ipd finalize`. Commit through the path-scoped Agent Workflows flow when executing an approved plan.
