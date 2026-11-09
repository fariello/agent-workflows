- Id: 6wu5mn
- Target-Id: uog8nc

## Summary

This walkthrough records the execution and verification of plan `uog8nc` (Set `writestd`, Order 8). Every live backlog item (statuses `open`, `graduated`, `parked`) at baseline commit `4ec01293618ccd240cd8b97db9c3ebefa147a8e4` was swept against the technical writing standard (`.aw/system/workflows/technical-writing/technical-writing.md`).

Total live items swept: 57 (6 graduated, 36 open, 15 parked).
Each item received one workflow history annotation line recording the proofread per spec `ecmw83` R-08 with meaning unchanged, verified by the backlog sweep guard script to preserve all protected elements (metadata, stable IDs, numbers, inline code spans, modal counts, non-diagram fenced blocks, and quoted text).

## Table of Items Swept

| Item ID | Status | Lines Changed | Diagrams Added/Corrected | Unresolved Count | Path |
| --- | --- | --- | --- | --- | --- |
| `ms06pi` | graduated | 1 | 0 | 0 | `.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md` |
| `wcbpqf` | graduated | 1 | 0 | 0 | `.aw/records/backlog/graduated/20260929-denypush-01-wcbpqf-decide-port-denial-capability-posture.backlog.md` |
| `vmrhj0` | graduated | 1 | 0 | 0 | `.aw/records/backlog/graduated/20260930-vmrhj0-01-vmrhj0-retry-allowlist-legacy-token-only.backlog.md` |
| `pyhq6s` | graduated | 1 | 0 | 0 | `.aw/records/backlog/graduated/20261001-setdispgate-01-pyhq6s-blast-radius-test-rejects-non-plan-dep-edge.backlog.md` |
| `1vd74h` | graduated | 1 | 0 | 0 | `.aw/records/backlog/graduated/20261002-sbh1o1-01-1vd74h-decide-spec-anchor-stale-gating.backlog.md` |
| `kvwwt0` | graduated | 1 | 0 | 0 | `.aw/records/backlog/graduated/20261012-cleancfg-01-kvwwt0-clean-target-stages-system-and-records.backlog.md` |
| `zvyo35` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261023-awinstallfix-01-zvyo35-install-noop-clean-reporting-and-skip-commit.backlog.md` |
| `dthgoi` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261023-tabcomp-01-dthgoi-completion-install-verify-shell-loader.backlog.md` |
| `tg80ht` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261024-specplan-01-tg80ht-spec-to-plan-graduation-and-runner-dispatch.backlog.md` |
| `n4a06q` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-reslife-01-n4a06q-research-triage-backfill.backlog.md` |
| `k899rl` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-rk25gap-01-k899rl-prompt-run-contract.backlog.md` |
| `l90ejs` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-rk25gap-01-l90ejs-bind-finding-codes.backlog.md` |
| `m429wp` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-rk25gap-01-m429wp-run-type-selectors.backlog.md` |
| `my4fki` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-rk25gap-01-my4fki-host-prompt-verb.backlog.md` |
| `oboc47` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-rk25gap-01-oboc47-aw-hooks-install.backlog.md` |
| `aoyivs` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-specaudit-01-aoyivs-6m4kow-stale-text.backlog.md` |
| `bkr6b0` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-specaudit-01-bkr6b0-7ckptx-restore-tests.backlog.md` |
| `hwaukk` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-specaudit-01-hwaukk-77tr3o-r2-terminal-children.backlog.md` |
| `okjz5y` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-specaudit-01-okjz5y-i4gpto-restore-tests.backlog.md` |
| `s6zc2f` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-specaudit-01-s6zc2f-w15vzb-amend-and-finish.backlog.md` |
| `t8nqyh` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-specaudit-01-t8nqyh-specs-check-id6-unreadable.backlog.md` |
| `xa7pqe` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-specaudit-01-xa7pqe-c4gd2h-restore-tests.backlog.md` |
| `xoetwv` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-specaudit-01-xoetwv-r07vma-tests-and-ac9.backlog.md` |
| `xvwlis` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-specaudit-01-xvwlis-llbr2b-post-approval-text.backlog.md` |
| `qph7c5` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261025-writestd-01-qph7c5-adopt-writing-standard.backlog.md` |
| `n2lr3g` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261026-askmerequired-01-n2lr3g-mandatory-askme-for-human-decisions.backlog.md` |
| `67n5as` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261026-revsteps-01-67n5as-author-k3yx72-stage-2-plans-orders-03-06-07-08-res.backlog.md` |
| `c1f6rd` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261101-awfed-01-c1f6rd-federate-projects-across-repos.backlog.md` |
| `m1wdj8` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261101-compplace-01-m1wdj8-companion-config-placement-drift.backlog.md` |
| `nq1src` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261105-execrecord-01-nq1src-implement-execution-record.backlog.md` |
| `fme4h4` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261105-fme4h4-01-fme4h4-runner-question-timeout-notification-and-formattin.backlog.md` |
| `f4p4vn` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261105-runindex-01-f4p4vn-implement-run-index.backlog.md` |
| `ucuqq6` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261105-ucuqq6-01-ucuqq6-runner-askme-questions-and-clarification-loop.backlog.md` |
| `mniobx` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261106-adopttypes-01-mniobx-adopt-supports-prompts-not-just-research.backlog.md` |
| `rdqciq` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261106-specflow-01-rdqciq-measure-agy-sandbox.backlog.md` |
| `hqt8tb` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261107-awnamespace-01-hqt8tb-slash-command-syntax.backlog.md` |
| `ggp2pf` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261107-ggp2pf-01-ggp2pf-records-root-resolver-divergence.backlog.md` |
| `k3kye2` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261107-k3kye2-01-k3kye2-artifact-meta-writer-leak-scan-treats-sibling-chec.backlog.md` |
| `kmo4bc` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261107-kmo4bc-01-kmo4bc-thorough-tier-layout-and-spec-template-failures.backlog.md` |
| `vqnb4v` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261107-vqnb4v-01-vqnb4v-artifact-meta-freshness-clobber.backlog.md` |
| `z90pda` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261107-z90pda-01-z90pda-artifact-meta-reviews-table-keys-rows-by-subject-i.backlog.md` |
| `w93his` | open | 1 | 0 | 0 | `.aw/records/backlog/open/20261108-w93his-01-w93his-retry-fresh-session.backlog.md` |
| `2seinm` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260815-2seinm-01-2seinm-extract-ci-verify-loop.backlog.md` |
| `5114n4` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260815-agent-comms-trust-01-5114n4-agent-comms-verifiable-provenance.backlog.md` |
| `5wmo8y` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260815-agent-comms-trust-01-5wmo8y-agent-comms-trust-tiers.backlog.md` |
| `w1ib6z` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260815-agent-comms-trust-01-w1ib6z-aw-comms-helper-tool.backlog.md` |
| `cm6wdt` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260815-cm6wdt-01-cm6wdt-audit-workflows-for-scriptable-work.backlog.md` |
| `zpez3o` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260815-human-approval-01-zpez3o-specs-approval-ergonomics.backlog.md` |
| `n3of99` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260815-n3of99-01-n3of99-reeval-bounded-iteration-roadmap.backlog.md` |
| `na1821` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260815-na1821-01-na1821-repo-exclude-globs-batch-install.backlog.md` |
| `nm69aj` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260815-nm69aj-01-nm69aj-unified-status-transition-verb.backlog.md` |
| `uaogjp` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260815-uaogjp-01-uaogjp-aw-block-do-not-edit-directive.backlog.md` |
| `sv0sf3` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-should-reviews-move-to-per-type-subdirs.backlog.md` |
| `phawyy` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260906-depreview-01-phawyy-dependency-blocked-reason-not-persisted.backlog.md` |
| `m15n3k` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260918-m15n3k-01-m15n3k-clean-delta-build-phases.backlog.md` |
| `w07sbr` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20260921-w07sbr-01-w07sbr-runner-stop-trigger-slow-tests-fail.backlog.md` |
| `szjsgj` | parked | 1 | 0 | 0 | `.aw/records/backlog/parked/20261017-rq-01-szjsgj-signal-question-channel.backlog.md` |

## Unresolved Annotations

No Unresolved annotations; no carrier filed.

## Suggested Summary Wording and Guard-Blocked Cases

None. All 57 items conformed to required structure and criteria without requiring summary rewording or encountering guard-blocked cases.

## Baseline Outputs (E-01)

### Record Format Check
- `grep -c metadata_schema .aw/config/project.json`: 0
- Count of live backlog items lacking `- Status:` or `## Workflow history`: 0

### Baseline Commit (BASE)
`4ec01293618ccd240cd8b97db9c3ebefa147a8e4`

### Error Diagnostics from `aw check all --agent --verbose` at BASE
```
check.blocking-item-closed-without-gate	.aw/records/backlog/done/20261107-suth7l-01-suth7l-artifact-meta-legacy-loader-disagrees-with-status.backlog.md
check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-04-jsgs0f-spec-refinement.agy.gemini38flashhigh.prompt.md
check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-05-z1zu8c-spec-refinement.codex.gpt61solmedium.prompt.md
check.name-nonconformant	.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md
check.name-nonconformant	.aw/records/specs/draft/20261025-specflow-02-1tx9t8-synthesis-independent-candidate.codex.gpt-6-astra-medium.spec.md
check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-01-hj6b60-spec-generation.agy.gemini38flashhigh.prompt.md
check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-02-g1k32q-spec-generation.codex.gpt61solmedium.prompt.md
check.prompt-metadata-missing	.aw/records/prompts/executed/20261024-specflow-03-443ltw-spec-generation.opencode.opus55high.prompt.md
check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-04-jsgs0f-spec-refinement.agy.gemini38flashhigh.prompt.md
check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-05-z1zu8c-spec-refinement.codex.gpt61solmedium.prompt.md
check.prompt-metadata-missing	.aw/records/prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md
```

### Live Backlog Items with Statuses at BASE
```
aw: invoked in checkout /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc but imported agent_workflows from /mnt/md1/VC/agent-workflows; re-running with /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc's package (set AW_NO_REEXEC=1 to disable)
●  graduated     ms06pi  .aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md
●  graduated     wcbpqf  .aw/records/backlog/graduated/20260929-denypush-01-wcbpqf-decide-port-denial-capability-posture.backlog.md
●  graduated     vmrhj0  .aw/records/backlog/graduated/20260930-vmrhj0-01-vmrhj0-retry-allowlist-legacy-token-only.backlog.md
●  graduated     pyhq6s  .aw/records/backlog/graduated/20261001-setdispgate-01-pyhq6s-blast-radius-test-rejects-non-plan-dep-edge.backlog.md
●  graduated     1vd74h  .aw/records/backlog/graduated/20261002-sbh1o1-01-1vd74h-decide-spec-anchor-stale-gating.backlog.md
●  graduated     kvwwt0  .aw/records/backlog/graduated/20261012-cleancfg-01-kvwwt0-clean-target-stages-system-and-records.backlog.md
◕  open          zvyo35  .aw/records/backlog/open/20261023-awinstallfix-01-zvyo35-install-noop-clean-reporting-and-skip-commit.backlog.md
◕  open          dthgoi  .aw/records/backlog/open/20261023-tabcomp-01-dthgoi-completion-install-verify-shell-loader.backlog.md
◕  open          tg80ht  .aw/records/backlog/open/20261024-specplan-01-tg80ht-spec-to-plan-graduation-and-runner-dispatch.backlog.md
◕  open          n4a06q  .aw/records/backlog/open/20261025-reslife-01-n4a06q-research-triage-backfill.backlog.md
◕  open          k899rl  .aw/records/backlog/open/20261025-rk25gap-01-k899rl-prompt-run-contract.backlog.md
◕  open          l90ejs  .aw/records/backlog/open/20261025-rk25gap-01-l90ejs-bind-finding-codes.backlog.md
◕  open          m429wp  .aw/records/backlog/open/20261025-rk25gap-01-m429wp-run-type-selectors.backlog.md
◕  open          my4fki  .aw/records/backlog/open/20261025-rk25gap-01-my4fki-host-prompt-verb.backlog.md
◕  open          oboc47  .aw/records/backlog/open/20261025-rk25gap-01-oboc47-aw-hooks-install.backlog.md
◕  open          aoyivs  .aw/records/backlog/open/20261025-specaudit-01-aoyivs-6m4kow-stale-text.backlog.md
◕  open          bkr6b0  .aw/records/backlog/open/20261025-specaudit-01-bkr6b0-7ckptx-restore-tests.backlog.md
◕  open          hwaukk  .aw/records/backlog/open/20261025-specaudit-01-hwaukk-77tr3o-r2-terminal-children.backlog.md
◕  open          okjz5y  .aw/records/backlog/open/20261025-specaudit-01-okjz5y-i4gpto-restore-tests.backlog.md
◕  open          s6zc2f  .aw/records/backlog/open/20261025-specaudit-01-s6zc2f-w15vzb-amend-and-finish.backlog.md
◕  open          t8nqyh  .aw/records/backlog/open/20261025-specaudit-01-t8nqyh-specs-check-id6-unreadable.backlog.md
◕  open          xa7pqe  .aw/records/backlog/open/20261025-specaudit-01-xa7pqe-c4gd2h-restore-tests.backlog.md
◕  open          xoetwv  .aw/records/backlog/open/20261025-specaudit-01-xoetwv-r07vma-tests-and-ac9.backlog.md
◕  open          xvwlis  .aw/records/backlog/open/20261025-specaudit-01-xvwlis-llbr2b-post-approval-text.backlog.md
◕  open          qph7c5  .aw/records/backlog/open/20261025-writestd-01-qph7c5-adopt-writing-standard.backlog.md
◕  open          n2lr3g  .aw/records/backlog/open/20261026-askmerequired-01-n2lr3g-mandatory-askme-for-human-decisions.backlog.md
◕  open          67n5as  .aw/records/backlog/open/20261026-revsteps-01-67n5as-author-k3yx72-stage-2-plans-orders-03-06-07-08-res.backlog.md
◕  open          c1f6rd  .aw/records/backlog/open/20261101-awfed-01-c1f6rd-federate-projects-across-repos.backlog.md
◕  open          m1wdj8  .aw/records/backlog/open/20261101-compplace-01-m1wdj8-companion-config-placement-drift.backlog.md
◕  open          nq1src  .aw/records/backlog/open/20261105-execrecord-01-nq1src-implement-execution-record.backlog.md
◕  open          fme4h4  .aw/records/backlog/open/20261105-fme4h4-01-fme4h4-runner-question-timeout-notification-and-formattin.backlog.md
◕  open          f4p4vn  .aw/records/backlog/open/20261105-runindex-01-f4p4vn-implement-run-index.backlog.md
◕  open          ucuqq6  .aw/records/backlog/open/20261105-ucuqq6-01-ucuqq6-runner-askme-questions-and-clarification-loop.backlog.md
◕  open          mniobx  .aw/records/backlog/open/20261106-adopttypes-01-mniobx-adopt-supports-prompts-not-just-research.backlog.md
◕  open          rdqciq  .aw/records/backlog/open/20261106-specflow-01-rdqciq-measure-agy-sandbox.backlog.md
◕  open          hqt8tb  .aw/records/backlog/open/20261107-awnamespace-01-hqt8tb-slash-command-syntax.backlog.md
◕  open          ggp2pf  .aw/records/backlog/open/20261107-ggp2pf-01-ggp2pf-records-root-resolver-divergence.backlog.md
◕  open          k3kye2  .aw/records/backlog/open/20261107-k3kye2-01-k3kye2-artifact-meta-writer-leak-scan-treats-sibling-chec.backlog.md
◕  open          kmo4bc  .aw/records/backlog/open/20261107-kmo4bc-01-kmo4bc-thorough-tier-layout-and-spec-template-failures.backlog.md
◕  open          vqnb4v  .aw/records/backlog/open/20261107-vqnb4v-01-vqnb4v-artifact-meta-freshness-clobber.backlog.md
◕  open          z90pda  .aw/records/backlog/open/20261107-z90pda-01-z90pda-artifact-meta-reviews-table-keys-rows-by-subject-i.backlog.md
◕  open          w93his  .aw/records/backlog/open/20261108-w93his-01-w93his-retry-fresh-session.backlog.md
◇  parked        2seinm  .aw/records/backlog/parked/20260815-2seinm-01-2seinm-extract-ci-verify-loop.backlog.md
◇  parked        5114n4  .aw/records/backlog/parked/20260815-agent-comms-trust-01-5114n4-agent-comms-verifiable-provenance.backlog.md
◇  parked        5wmo8y  .aw/records/backlog/parked/20260815-agent-comms-trust-01-5wmo8y-agent-comms-trust-tiers.backlog.md
◇  parked        w1ib6z  .aw/records/backlog/parked/20260815-agent-comms-trust-01-w1ib6z-aw-comms-helper-tool.backlog.md
◇  parked        cm6wdt  .aw/records/backlog/parked/20260815-cm6wdt-01-cm6wdt-audit-workflows-for-scriptable-work.backlog.md
◇  parked        zpez3o  .aw/records/backlog/parked/20260815-human-approval-01-zpez3o-specs-approval-ergonomics.backlog.md
◇  parked        n3of99  .aw/records/backlog/parked/20260815-n3of99-01-n3of99-reeval-bounded-iteration-roadmap.backlog.md
◇  parked        na1821  .aw/records/backlog/parked/20260815-na1821-01-na1821-repo-exclude-globs-batch-install.backlog.md
◇  parked        nm69aj  .aw/records/backlog/parked/20260815-nm69aj-01-nm69aj-unified-status-transition-verb.backlog.md
◇  parked        uaogjp  .aw/records/backlog/parked/20260815-uaogjp-01-uaogjp-aw-block-do-not-edit-directive.backlog.md
◇  parked        sv0sf3  .aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-should-reviews-move-to-per-type-subdirs.backlog.md
◇  parked        phawyy  .aw/records/backlog/parked/20260906-depreview-01-phawyy-dependency-blocked-reason-not-persisted.backlog.md
◇  parked        m15n3k  .aw/records/backlog/parked/20260918-m15n3k-01-m15n3k-clean-delta-build-phases.backlog.md
◇  parked        w07sbr  .aw/records/backlog/parked/20260921-w07sbr-01-w07sbr-runner-stop-trigger-slow-tests-fail.backlog.md
◇  parked        szjsgj  .aw/records/backlog/parked/20261017-rq-01-szjsgj-signal-question-channel.backlog.md
```

### `aw backlog check --agent` Advisory Count at BASE
```
aw: invoked in checkout /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc but imported agent_workflows from /mnt/md1/VC/agent-workflows; re-running with /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc's package (set AW_NO_REEXEC=1 to disable)
{"schema":"aw.agent/v1","kind":"result","cmd":"backlog check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1147,"findings":0,"evidence":["backlog"],"next":null}
```

### Baseline Guard Run Result
```
TOTAL live=57 checked=57 problems=0
```

## Final Sweep Guard and Backlog Check Outputs (E-03)

### Full Guard Output (`backlog_guard.py --final`)
```
.aw/records/backlog/graduated/20260905-awmetastore-01-ms06pi-decide-where-aw-metadata-lives.backlog.md	quoted-elsewhere=14	diagrams=0->0	modals=9->9	sweep-notes=1	problems=0
.aw/records/backlog/graduated/20260929-denypush-01-wcbpqf-decide-port-denial-capability-posture.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=5->5	sweep-notes=1	problems=0
.aw/records/backlog/graduated/20260930-vmrhj0-01-vmrhj0-retry-allowlist-legacy-token-only.backlog.md	quoted-elsewhere=6	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/graduated/20261001-setdispgate-01-pyhq6s-blast-radius-test-rejects-non-plan-dep-edge.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0
.aw/records/backlog/graduated/20261002-sbh1o1-01-1vd74h-decide-spec-anchor-stale-gating.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0
.aw/records/backlog/graduated/20261012-cleancfg-01-kvwwt0-clean-target-stages-system-and-records.backlog.md	quoted-elsewhere=6	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261023-awinstallfix-01-zvyo35-install-noop-clean-reporting-and-skip-commit.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261023-tabcomp-01-dthgoi-completion-install-verify-shell-loader.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0
.aw/records/backlog/open/20261024-specplan-01-tg80ht-spec-to-plan-graduation-and-runner-dispatch.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-reslife-01-n4a06q-research-triage-backfill.backlog.md	quoted-elsewhere=5	diagrams=0->0	modals=2->2	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-rk25gap-01-k899rl-prompt-run-contract.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-rk25gap-01-l90ejs-bind-finding-codes.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-rk25gap-01-m429wp-run-type-selectors.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-rk25gap-01-my4fki-host-prompt-verb.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-rk25gap-01-oboc47-aw-hooks-install.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-aoyivs-6m4kow-stale-text.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-bkr6b0-7ckptx-restore-tests.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-hwaukk-77tr3o-r2-terminal-children.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-okjz5y-i4gpto-restore-tests.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=2->2	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-s6zc2f-w15vzb-amend-and-finish.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-t8nqyh-specs-check-id6-unreadable.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-xa7pqe-c4gd2h-restore-tests.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-xoetwv-r07vma-tests-and-ac9.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-specaudit-01-xvwlis-llbr2b-post-approval-text.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261025-writestd-01-qph7c5-adopt-writing-standard.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261026-askmerequired-01-n2lr3g-mandatory-askme-for-human-decisions.backlog.md	quoted-elsewhere=6	diagrams=0->0	modals=4->4	sweep-notes=1	problems=0
.aw/records/backlog/open/20261026-revsteps-01-67n5as-author-k3yx72-stage-2-plans-orders-03-06-07-08-res.backlog.md	quoted-elsewhere=5	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/open/20261101-awfed-01-c1f6rd-federate-projects-across-repos.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=26->26	sweep-notes=1	problems=0
.aw/records/backlog/open/20261101-compplace-01-m1wdj8-companion-config-placement-drift.backlog.md	quoted-elsewhere=4	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261105-execrecord-01-nq1src-implement-execution-record.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261105-fme4h4-01-fme4h4-runner-question-timeout-notification-and-formattin.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261105-runindex-01-f4p4vn-implement-run-index.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261105-ucuqq6-01-ucuqq6-runner-askme-questions-and-clarification-loop.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=50->50	sweep-notes=1	problems=0
.aw/records/backlog/open/20261106-adopttypes-01-mniobx-adopt-supports-prompts-not-just-research.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=4->4	sweep-notes=1	problems=0
.aw/records/backlog/open/20261106-specflow-01-rdqciq-measure-agy-sandbox.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-awnamespace-01-hqt8tb-slash-command-syntax.backlog.md	quoted-elsewhere=7	diagrams=0->0	modals=2->2	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-ggp2pf-01-ggp2pf-records-root-resolver-divergence.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-k3kye2-01-k3kye2-artifact-meta-writer-leak-scan-treats-sibling-chec.backlog.md	quoted-elsewhere=9	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-kmo4bc-01-kmo4bc-thorough-tier-layout-and-spec-template-failures.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-vqnb4v-01-vqnb4v-artifact-meta-freshness-clobber.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261107-z90pda-01-z90pda-artifact-meta-reviews-table-keys-rows-by-subject-i.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/open/20261108-w93his-01-w93his-retry-fresh-session.backlog.md	quoted-elsewhere=8	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-2seinm-01-2seinm-extract-ci-verify-loop.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-agent-comms-trust-01-5114n4-agent-comms-verifiable-provenance.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-agent-comms-trust-01-5wmo8y-agent-comms-trust-tiers.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-agent-comms-trust-01-w1ib6z-aw-comms-helper-tool.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-cm6wdt-01-cm6wdt-audit-workflows-for-scriptable-work.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-human-approval-01-zpez3o-specs-approval-ergonomics.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-n3of99-01-n3of99-reeval-bounded-iteration-roadmap.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-na1821-01-na1821-repo-exclude-globs-batch-install.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-nm69aj-01-nm69aj-unified-status-transition-verb.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260815-uaogjp-01-uaogjp-aw-block-do-not-edit-directive.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260829-reviewloc-01-sv0sf3-should-reviews-move-to-per-type-subdirs.backlog.md	quoted-elsewhere=1	diagrams=0->0	modals=3->3	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260906-depreview-01-phawyy-dependency-blocked-reason-not-persisted.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260918-m15n3k-01-m15n3k-clean-delta-build-phases.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20260921-w07sbr-01-w07sbr-runner-stop-trigger-slow-tests-fail.backlog.md	quoted-elsewhere=3	diagrams=0->0	modals=0->0	sweep-notes=1	problems=0
.aw/records/backlog/parked/20261017-rq-01-szjsgj-signal-question-channel.backlog.md	quoted-elsewhere=2	diagrams=0->0	modals=1->1	sweep-notes=1	problems=0
TOTAL live=57 checked=57 problems=0
```

### Final `aw backlog check --agent` Output
```
aw: invoked in checkout /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc but imported agent_workflows from /mnt/md1/VC/agent-workflows; re-running with /mnt/md1/VC/agent-workflows/.aw/worktrees/uog8nc's package (set AW_NO_REEXEC=1 to disable)
{"schema":"aw.agent/v1","kind":"result","cmd":"backlog check","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":1147,"findings":0,"evidence":["backlog"],"next":null}
```
