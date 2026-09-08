# IPD: Privacy-safe incremental per-run analytics cache

- Date: 2026-09-08
- Kind: child
- Concern: Avoid repeated corpus rescans while ensuring cached analytics facts are complete, fresh, atomic, and safe to share at the metrics level.
- Scope: Define and implement a versioned per-run cache, content freshness fingerprints, privacy projection, locking, atomic replacement, and cache observability.
- Scope-Paths: agent_workflows/run_analytics_cache.py, agent_workflows/run_analytics_privacy.py, tests/test_run_analytics_cache.py, tests/test_run_analytics_privacy.py
- Item-Dependencies: executed:xbwq8n
- Status: approved
- Readiness: go-pending-approval
- Set: runanalytics
- Order: 2
- Highest E allocated: 06
- Author: Codex
- Id: bzz5e6
- Approval: 2026-09-08, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-08 approved (aw set): status set to approved
- 2026-09-08 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. PR-031..PR-041, ALL ELEVEN FIXED, no open questions remain. The verdict token is stated explicitly because `plan_readiness.newest_verdict` reads the newest review record's first verdict token and falls back to a negative scan when none is present. THE PRINCIPAL FINDING IS SIZING, AND THE COUNT-BASED LINT CANNOT SEE IT (PR-031, new F-1): E-02 as authored named SIX independent deliverables (freshness decisions, stable-source reuse, incomplete-run rechecks, locking, atomic replacement, corruption recovery) across at least four unrelated test surfaces, and E-03 bundled a consumer-facing observability contract with five test families. `aw ipd lint` reported conforming and `IPD-Z602` was silent on all three items, verified by CALLING `ipd_schema.e_item_density_advisory` on each (all None) rather than inferring it from the clean lint. The decisive evidence that this is a template and not a judgement: every one of the Set's TEN children carries exactly three E-items, and a privacy boundary plus a locking protocol are not the same size as a CLI or a docs pass. Split into six items in three groups; the linter then EARNED its keep by catching the stale `Highest E allocated` (`IPD-I304`) and three `IPD-I303` bijection gaps. SECOND, THE LOCK CONVENTION POINTED AT THE WRONG API (PR-032, F-3): the plan said to use `filelock`'s 'established locking approach', but `platform_lock` is the package's single lock authority, enforced by a guard test against a top-level `import fcntl`. Its docstring records three properties a direct caller gets wrong, one of them severe: `filelock` MUST NOT probe a holder because its POSIX backend opens `O_CREAT | O_TRUNC`, so a FAILED acquire DESTROYS the record of the live holder that just refused, corrupting the very diagnostic being read; a second `acquire()` on the same object SUCCEEDS via a per-object counter (a silent mutual-exclusion failure); and exactly ONE caller may block, so a blocking analytics cache would HANG a driver rather than fail it. THIRD, A SHIPPED DETECTOR ALREADY COVERS MOST OF THE FORBIDDEN SET AND WENT UNMENTIONED (PR-033, F-4): measured, `leak_sanitizer.scan_text` returns `home-path` and `handle` at `fail` severity on a raw home path plus username, so it is the correct INDEPENDENT read-side oracle for a write-side allowlist, and writing a second sanitizer would fork a module whose docstring exists to keep ONE code path. V-04 now requires the detector be run over the produced cache AND a CONTROL run proving the same detector flags the same canaries in raw form, because 'clean' and 'not looking' are otherwise indistinguishable. ALSO FIXED: the most detailed prose in the plan pointed at a DENYLIST while E-01 said allowlist, so the forbidden list is now labelled a TEST CORPUS and the gate makes denylist-filtering an explicit stop condition (PR-034); 'No open questions' hid TWO unmade decisions, now OQ-01 and OQ-02 RESOLVED from repository evidence (salt lives in the gitignored analytics subtree, per-box, never committed, correlation scoped to one box and one cache generation, with `config/local.json` rejected as a user-facing surface; lock contention SKIPS with a recorded reason rather than becoming the package's second blocking caller) (PR-035); the Deferred section deferred to items that do not match, since Order 07 is the SPA and Order 08 the query CLI, neither a 'retention CLI', and `analytics/snapshots/` is RESERVED by Order 01 (PR-036); the gate carried NO execution contract at all, the identical omission Order 01's review found, so a full fence plus path-scoped-commit, never-push, paste-actual-output and lifecycle rules were added (PR-037); the Goal wrote the cache path as prose without naming Order 01's resolver, risking re-creation of the six-site literal Order 01 exists to remove and mis-siting the cache for any non-`repository` `records_backend` (PR-038); no baseline was recorded, measured `2 failed, 5655 passed, 3 skipped, 2 xfailed` with both failures pre-existing and pinned to the live plan corpus (PR-039); four escaped backtick pairs rendered literally, where Order 01's review found six (PR-040); and approved spec `kw5y2s` enumerates a `state/runtime/cache/` class, a tension now recorded with the runs-root siting justified, the spec marked IMMUTABLE here, and a genuine conflict made a STOP-and-raise (PR-041). WHAT THE PLAN GOT RIGHT AND KEEPS: the privacy analysis separating 'raw' as unsummarized metric facts from 'raw' as source records, the insistence that one projection feed every downstream consumer, the refusal to call the cache anonymous or release-safe, and the correct freshness insight that a resumed run reuses its directory so mtime cannot establish staleness.

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): fixed the cache hierarchy, freshness protocol, allowed data classes, redaction boundary, and failure behavior.

## Goal

Store one reusable normalized summary per source run beneath `<resolved-runs-root>/analytics/cache/<source-root-id>/<run-id>/`. Reuse it only when all analytics-relevant source state is unchanged, and guarantee that the cache contains no prompt, conversation, source text, command text, secrets, raw host identity, or raw absolute path.

RESOLVE THE PATH THROUGH ORDER 01's RESOLVER, NEVER BY COMPOSING IT. `<resolved-runs-root>` is the output of `runner_shared.state_root` as Order 01 (`xbwq8n`) rewrites it to consult project-context, plus the `analytics/cache/` constant that same item exposes. Order 01's review measured that the old `state_root` hardcoded `repo / ".aw" / "records" / "runs"` while the records root is RELOCATABLE (`records_backend` of `repository`/`companion`/`home`), and that the literal was built at SIX live sites. So a hand-composed cache path here would reintroduce the exact defect this Set's Order 01 exists to remove, and would put the cache in the wrong place for any non-`repository` backend. Use the constants and `path_is_within_analytics`; construct no literal.

## Detailed Implementation Checklist (TODO)

### Task group 1: Cache contract and privacy boundary

RIGHT-SIZING NOTE ADDED AT REVIEW, BECAUSE THE COUNT-BASED LINT DOES NOT CLEAR THIS. `aw ipd lint` reports conforming and its density advisory (`IPD-Z602`) is silent on all three items, verified by calling `ipd_schema.e_item_density_advisory` on each (all `None`). That measures STRUCTURAL count, not conceptual density. Measured semantically, E-02 as authored named SIX independent deliverables (freshness decisions, stable-source reuse, incomplete-run rechecks, locking, atomic replacement, corruption recovery) across at least four separate test surfaces, and E-03 bundled an observability API with five test families. Every one of the Set's ten children carries exactly three E-items, which is a uniform authoring shape rather than a per-child sizing judgement. The items below are therefore SPLIT, and the split is the plan's own stated rule ("each E-item must address one concern and be executable in one focused pass"). See F-1.

### Task group 1: Cache contract and privacy boundary

- [ ] E-01 Implement the versioned cache ENVELOPE and its strict loader, with unknown fields failing closed.
  - Depends on: none
  - Expected outcome: the envelope records schema/tool versions, source-root ID, run ID, completeness, source fingerprint, source coverage, generated time, metric facts, event facts, quality flags, and warnings; an unknown field is REFUSED with a diagnostic naming it rather than copied or silently dropped; a future schema version is refused with a forward-compatible diagnostic rather than misparsed.
  - Execution state: pending
- [ ] E-04 Implement the single allowlist-based privacy PROJECTOR that every persisted fact crosses.
  ALLOWLIST, NOT DENYLIST, and say why in the module docstring: the forbidden set enumerated in Findings can never be proven complete, so the projector must pass only explicitly named fields and refuse everything else by default. The Findings list is a TEST CORPUS for the read-side check, not the implementation strategy.
  REUSE THE EXISTING ENGINE AS THE INDEPENDENT CHECK, do not write a second sanitizer: `leak_sanitizer.scan_text` already flags home paths, handles, hostnames, remotes and secret-shaped strings at `fail` severity (measured at review). The projector is the write-side guarantee; that engine is the read-side proof it held.
  DOCUMENT THE HASHING CONTRACT CONCRETELY, since Findings requires a "documented local salt or stable source-root derivation that cannot be reversed or correlated across submissions unless the user explicitly opts into that scope": state where the salt lives, that it is per-box and NOT committed (the runs tree is gitignored, so it may live beside the cache), and that a salt rotation invalidates correlation by design. A salt whose storage is unspecified is a salt an executor will put somewhere shareable.
  - Depends on: E-01
  - Expected outcome: one projector function is the only path by which a fact reaches the envelope; it passes an explicit allowlist and refuses unknown keys; the hash derivation, salt location, non-committed status and correlation scope are documented in the module; no second sanitizer is introduced.
  - Execution state: pending

### Task group 2: Freshness, publication, and recovery

- [ ] E-02 Implement the FRESHNESS decision: a deterministic source fingerprint and the hit/rebuild verdict, including the in-progress and resumed cases.
  DIRECTORY MTIME IS INSUFFICIENT and the plan already knows it; state what the fingerprint actually covers (the analytics-relevant file identities plus terminal-versus-in-progress state) and that a run which is not terminal is NEVER treated as a stable hit, because a resumed run reuses its directory.
  - Depends on: E-01
  - Expected outcome: unchanged COMPLETED runs are hits without reparsing; new, resumed, in-progress, mutated and schema-changed runs rebuild; the fingerprint is deterministic across processes and independent of dict ordering.
  - Execution state: pending
- [ ] E-05 Implement PUBLICATION safety: `platform_lock` serialization, atomic replacement, and per-entry corruption isolation.
  USE `platform_lock`, NOT `filelock` DIRECTLY, and `artifact_core.atomic_write` (or state why not); see the conventions bullets for the three measured properties (non-blocking default, deliberate non-re-entrancy, and the `O_CREAT | O_TRUNC` probe hazard that makes `filelock` unsafe for observing a holder).
  A LOCK FAILURE MUST NOT BE A CACHE CORRUPTION AND MUST NOT BE SILENT: decide and state whether a busy lock skips that run with a recorded reason or waits, and note that only one caller in the package is permitted to block.
  - Depends on: E-02
  - Expected outcome: interruption never publishes a partial cache; one corrupt or unreadable entry is rebuilt without affecting other runs; a busy lock produces a recorded, machine-readable skip rather than a partial write or a silent pass; no raw `filelock` or `fcntl` use is introduced.
  - Execution state: pending

### Task group 3: Observability and proof

- [ ] E-03 Expose the machine-readable cache DECISIONS that downstream Orders consume.
  NAME THE CONSUMER CONTRACT, because five later Orders depend on it: per-run `hit`/`miss`/`rebuild`/`skip` with a reason, plus totals. Order 08 (`mm5p3v`, the `aw runs analyze`/query interface) is the surface that renders it, so the shape is a contract and not a debug print.
  - Depends on: E-05
  - Expected outcome: callers receive per-run hit/miss/rebuild/skip reasons and totals in a stable machine-readable shape; repeated unchanged analysis is byte-stable apart from explicitly volatile metadata and demonstrably reads fewer source files.
  - Execution state: pending
- [ ] E-06 Add the ADVERSARIAL privacy and failure-mode test suite, driven by seeded canaries and the shipped detector.
  THIS IS THE ITEM THAT MAKES THE PRIVACY CLAIM FALSIFIABLE, so it is separated from E-03's observability work rather than bundled with it.   Seed prompts, absolute paths, commands, hostnames, usernames, environment secrets and high-entropy tokens into fixtures; then assert BOTH that the projector refused them AND that `leak_sanitizer.scan_text` finds nothing in the produced cache files and diagnostics.
  DO NOT COMMIT THE CANARIES AS LITERALS, which this review demonstrated the hard way: pasting a measured detector result with its literal inputs made `aw sanitize --agent` FAIL on this plan file (F-10). Generate the fixtures at test time or assemble the sensitive strings from fragments, exactly as the detection engine does with its own patterns, and run the sanitizer over the TEST tree as well as the cache. A test corpus full of committed real-shaped secrets is a leak that ships. A hand-written substring assertion alone is not sufficient: it drifts from the detector and cannot catch a class nobody thought to seed.
  - Depends on: E-04, E-03
  - Expected outcome: seeded sensitive canaries appear in no cache JSON/JSONL, no diagnostic and no warning string; the shipped leak detector reports clean over the cache tree; mutation, concurrency, corruption and idempotence cases each have a named test; every numeric fact is proven conserved across encode/decode.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **DO NOT USE `filelock` DIRECTLY. USE `agent_workflows.platform_lock`.** The conventions bullet as authored said the repo "already depends on `filelock>=3`; use its established locking approach", which is true about the dependency and points at the wrong API. Measured: `platform_lock` is the package's SINGLE lock authority, exists specifically so no other module takes a POSIX-only or backend-specific dependency, and is enforced by a guard test that fails on a top-level `import fcntl` in any affected module (`tests/test_runner_stop_triggers.py:2120-2137`). Use `platform_lock.acquire(path)`, which returns a handle and raises `platform_lock.LockBusy`. Three properties its docstring records and a new caller must not relearn the hard way: acquisition is NON-BLOCKING by default and only ONE caller in the package is permitted to pass `blocking=True`; it is deliberately NOT re-entrant, and a fresh lock object is constructed per call because `filelock`'s per-object counter would otherwise let a second `acquire()` on the same object succeed; and `probe_free` (NOT `filelock`) is the only safe way to observe another holder, because `filelock`'s POSIX backend opens with `O_CREAT | O_TRUNC` and so a FAILED acquire destroys the record of the live holder. A cache that probes with `filelock` would silently corrupt exactly the diagnostics it is trying to read.
- **ATOMIC REPLACEMENT ALREADY HAS A HELPER**: `artifact_core.atomic_write` (`:118`) writes via a temp file plus `os.replace`, the pattern used at a dozen sites (`config.py:938`, `install_wizard.py:886`, `compat_migration.py:576`, ...). Reuse it or state precisely why a JSON/JSONL cache needs its own; do not hand-roll a thirteenth variant.
- Driver artifacts can change during execution and resume in the same directory. Directory mtime alone cannot establish freshness.
- `.aw/records/runs` is ignored and disposable, so cache recovery must rebuild rather than require migration or manual repair. Verified: `.aw/.gitignore` carries `records/runs/`.
- **THE PRIVACY BOUNDARY HAS AN EXISTING DETECTOR, AND IT IS THE RIGHT VERIFICATION ORACLE.** `leak_sanitizer` (re-exported as `local_leaks`, driven by `aw sanitize --agent`) already detects home paths, usernames/handles, hostnames, repo remotes, and secret-shaped strings, which is most of this plan's own forbidden set. Measured: `scan_text` over a string containing a real home path, the maintainer's username and an AWS-shaped key returns `home-path` and `handle` at `fail` severity. (Stated in words rather than pasted: the literal canary is itself a leak, which `aw sanitize --agent` flagged in this very file during review.) So E-01's projector is a WRITE-SIDE allowlist (the correct design, since a denylist cannot be complete), and this engine is the INDEPENDENT read-side check that the projector worked. Run it over the produced cache in V-01 rather than hand-asserting a list of canary substrings, which is weaker and drifts. Do NOT build a second sanitizer: `local_leaks` is deliberately a thin re-export of one engine so there is one code path, and Order 09 already owns export-time sanitization.
- ORDER 01 OWNS THE PATH AND THE CONTAINMENT PREDICATE. It exposes `analytics/`, `analytics/cache/`, `analytics/snapshots/`, `analytics/exports/` and `path_is_within_analytics()`. Also note `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS` already makes every analytics path worker-forbidden, so this cache is written by the coordinator or the human, NEVER from inside a lane turn, and that predicate must not be weakened to make it writable.
- Source run directories remain read-only. Writes are confined to the Order-01 reserved analytics subtree.
- Downstream report, query, export, and submission paths must consume the same privacy-projected facts rather than create weaker parallel sanitizers.

## Findings

The cache must retain raw numeric observations needed for aggregation, including timestamps, durations, resource samples, token components, monetary values, categorical activity labels, phase, IPD/set/run identifiers, model/provider, price-source metadata, outcome flags, and quality markers. “Raw” here means unsummarized metric facts, not raw source records.

The forbidden set includes prompt and response bodies, agent conversations, instructional file contents, source snippets, arbitrary event payloads, shell command text and arguments, environment values outside an explicit non-sensitive allowlist, usernames, hostnames, raw paths, repository remotes, branch names, commit messages, and secret-shaped strings. Hashed identifiers must use a documented local salt or stable source-root derivation that cannot be reversed or correlated across submissions unless the user explicitly opts into that scope.

TREAT THAT LIST AS A TEST CORPUS, NOT AS THE IMPLEMENTATION. An enumerated forbidden set can never be proven complete, so the projector must be an ALLOWLIST (E-04) and this list is what the adversarial suite (E-06) seeds. Added at review, because a plan that states a thorough denylist invites an executor to implement exactly that denylist.

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **THE THREE E-ITEMS WERE MECHANICALLY SIZED, NOT SIZED TO ONE CONCERN.** E-02 as authored named SIX independent deliverables (freshness decisions, stable-source reuse, incomplete-run rechecks, locking, atomic replacement, corruption recovery) spanning at least four unrelated test surfaces, and E-03 bundled a consumer-facing observability contract with five test families. Every one of the Set's TEN children carries exactly three E-items, which is an authoring template rather than a per-child judgement. The count-based lint cannot see this: it reported conforming and `IPD-Z602` was silent on all three items (verified by calling `ipd_schema.e_item_density_advisory` on each; all returned `None`). Split at review into six items against the plan's own stated rule. | `grep -c '^- \[ \] E-'` across all ten children -> `3` each; `e_item_density_advisory` -> `None`, `None`, `None`; `aw ipd lint --phase author` -> conforming both before and after the split |
| F-2 | **THE DEFERRED SECTION NAMED THE WRONG ORDERS.** It said "cache retention CLI and snapshots are Orders 07 and 08". Measured: Order 07 is `6eq3oq` (offline SPA and report bundle) and Order 08 is `mm5p3v` (`aw runs analyze` and query interface); neither is a retention CLI, and `analytics/snapshots/` is a namespace RESERVED by Order 01. An executor deferring to a non-existent item defers to nobody. | front matter of `20260908-runanalytics-07-6eq3oq-...`, `...-08-mm5p3v-...`; Order 01 E-01 expected outcome listing the four reserved subpaths |
| F-3 | **THE LOCKING CONVENTION POINTED AT THE WRONG API.** The plan said to use `filelock`'s "established locking approach". Measured, the package's established approach is `platform_lock`, which exists precisely so no other module depends on a lock backend directly and is enforced by a guard test against a top-level `import fcntl`. Its docstring records three properties a direct `filelock` caller would get wrong: non-blocking by default with exactly ONE caller permitted to block, deliberate NON-re-entrancy (a second `acquire()` on the same `filelock` object SUCCEEDS via a per-object counter, which would silently break mutual exclusion), and that `filelock` MUST NOT be used to PROBE a holder because its POSIX backend opens `O_CREAT | O_TRUNC`, so a FAILED acquire destroys the live holder's record. | `pyproject.toml:50`; `agent_workflows/platform_lock.py:1-58`; `tests/test_runner_stop_triggers.py:2120-2137` |
| F-4 | **A SHIPPED DETECTOR ALREADY COVERS MOST OF THE FORBIDDEN SET AND WAS NOT MENTIONED.** `leak_sanitizer` (re-exported as `local_leaks`, driven by `aw sanitize --agent`) detects home paths, handles/usernames, hostnames, remotes and secret-shaped strings. Measured: `scan_text` on a string containing a real home path and username returned `home-path` and `handle`, both at `fail` severity. That makes it the correct INDEPENDENT read-side oracle for the privacy claim, and it also means a second sanitizer here would be a fork of a module that is deliberately a single engine behind a thin re-export. | `python3 -c "leak_sanitizer.scan_text(...)"` -> 2 findings at `fail`; `local_leaks.py:1-16` (shim docstring: "ONE code path") |
| F-5 | THE PATH WAS AT RISK OF BEING COMPOSED FROM A LITERAL, which is the exact defect Order 01 exists to remove. Order 01's review measured that `state_root` hardcoded `repo/.aw/records/runs` while the records root is relocatable (`records_backend` of `repository`/`companion`/`home`) and that the literal appeared at SIX live sites. This plan's Goal wrote the path as prose without naming the resolver. | Order 01 `xbwq8n` workflow-history record and its E-01 expected outcome |
| F-6 | THE GATE CARRIED NO EXECUTION CONTRACT: no scope fence, no path-scoped-commit / never-push rule, no paste-actual-output honesty rule, no lifecycle-move instruction. The same gap was found and fixed in this Set's Order 01 at its review, so it is a Set-wide authoring pattern rather than a one-off. | plan gate section as authored (two sentences); Order 01's review record naming the identical omission |
| F-7 | FOUR ESCAPED BACKTICK PAIRS RENDERED LITERALLY (`\``) in the Goal, two conventions bullets and the validation section, so the rendered plan showed backslashes instead of code spans. Order 01's review recorded six occurrences of the same defect, again indicating a shared authoring pipeline. | `grep -n '\\\`'` -> lines 23, 44, 46, 78 before the fix |
| F-8 | ATOMIC REPLACEMENT ALREADY HAS A HELPER (`artifact_core.atomic_write`, temp file plus `os.replace`), used at roughly a dozen sites. The plan specified the pattern in prose without naming it, inviting a thirteenth hand-rolled variant. | `grep -n 'os.replace' agent_workflows/*.py` -> 12+ sites; `artifact_core.py:118` |
| F-10 | **A CANARY IS ITSELF A LEAK, DEMONSTRATED ACCIDENTALLY DURING THIS REVIEW.** Writing the measured `scan_text` result into this plan with its literal inputs made `aw sanitize --agent` fail on THIS FILE with `home-path` and `handle`. E-06 seeds exactly such canaries into fixtures, so the same hazard applies to the test corpus: keep seeded secrets in generated fixtures or assembled fragments, never as literals in a tracked file, and run the sanitizer over the TEST TREE too, not only over the cache. The engine's own convention is the model ("Sensitive literals are assembled from fragments in the engine module, never here", `local_leaks.py:16`). | `aw sanitize --agent` -> 2 findings at this file, then clean after rewording; `leak_sanitizer.py` fragment-assembly convention |
| F-9 | THE PLAN CLAIMED "No open questions" while leaving TWO decisions unmade that an executor cannot settle from repository evidence: where the hash salt lives and what happens when the cache lock is BUSY. Both are now stated as decisions the item must make and record, rather than as absent questions. | Findings' salt requirement with no location specified; E-02-as-authored naming "locking" with no contention behavior |

## Proposed changes (ordered, validatable)

1. Define cache and privacy schemas with strict loaders and forward-compatible version diagnostics.
2. Compute a deterministic manifest from analytics-relevant file identity and terminal/in-progress state, then publish through lock plus temporary-file rename.
3. Instrument cache behavior and attack the privacy boundary with seeded sensitive canaries.

## Deferred / out of scope (with reason)

- Parsing driver artifacts into facts is Order 05 (`8hald1`), which declares `- Item-Dependencies: executed:5f2h8i, executed:bzz5e6` and therefore consumes this cache.
- Cache retention CLI and snapshots: CORRECTED AT REVIEW (F-2). The plan said "Orders 07 and 08", but measured, Order 07 (`6eq3oq`) is the offline SPA and report bundle and Order 08 (`mm5p3v`) is the `aw runs analyze` / query CLI; neither is named "retention". Order 08 is the CLI surface that renders this cache's decisions (so E-03's shape is a contract to it), and the `analytics/snapshots/` namespace is RESERVED by Order 01 (`xbwq8n`), not created here. If a retention policy is genuinely nobody's item, that is a gap to raise rather than a deferral to assert.
- Exporting original raw run records is Order 09 (`ixis0c`, sanitized export and submission) and may never reuse the safe-cache label. Note Order 09 owns EXPORT-time sanitization, so this item must not build a second sanitizer for it, and must not let a downstream consumer treat "cache-projected" as "cleared for release".

## Scope check

- Over-scope: no source adapters, statistical aggregation, UI, runner modification, or network transport. Note `Scope-Paths` declares only NEW modules and their tests, so nothing existing is modified; if execution finds it must touch `runner_shared.py` (for example because Order 01's constants are insufficient), that is a signal to STOP and reconcile with Order 01 rather than to widen the fence silently, since nine plans depend on that resolver.
- Under-scope: includes schema evolution, incomplete-run invalidation, concurrency, partial failure, privacy tests, and observability needed by all downstream consumers. ADDED AT REVIEW and now in scope: the salt's storage location (OQ-01), the lock-contention behavior (OQ-02), and the independent read-side privacy check via the shipped detector (E-06). Each was implied by the plan's requirements without being anybody's deliverable.
- DECLARED-BUT-UNMODIFIED RISK: all four `Scope-Paths` entries are files that do not exist yet, so every one must be created. If any is not, `aw ipd finalize` requires a `--scope-ack` for it; an unwritten `run_analytics_privacy.py` in particular would mean the projector was folded into the cache module, which contradicts E-04's single-boundary requirement.

## Required tests / validation

- Required cases: first scan; unchanged completed run cache hit; one changed run rebuild; resumed/in-progress run rebuild; added run; removed run; schema-version change; interrupted write; concurrent analyzers; corrupt entry isolation; stale lock recovery if supported by the chosen lock API; deterministic projection; unknown-field refusal.
- Seed prompts, paths, commands, hostnames, usernames, environment secrets, and high-entropy tokens into fixtures and assert none occur in cache JSON/JSONL or diagnostics.
- Demonstrate conservation of every numeric fact across encode/decode.
- Focused tests, bare `python3 -m pytest`, and `git diff --check` pass. RUN THE SUITE BARE: the configured `addopts` already supply quiet, parallel and the fast subset, so do not add `-n0` or a second `-q`.
- MEASURED BASELINE AT REVIEW, so the executor does not mistake pre-existing red for its own: `2 failed, 5655 passed, 3 skipped, 2 xfailed`. Both failures are pinned to the live mutable plan corpus and neither is this plan's: `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` and `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`. Re-measure in the executing worktree and compare failing NODE IDS, never totals; the criterion is that the AFTER failure set minus the BEFORE failure set is EMPTY, not that the suite is green.
- RUN `aw sanitize --agent` OVER THE PRODUCED CACHE, not only over the tracked tree. The cache lives in a gitignored directory, so the default working-tree scan may not reach it; point the detector at the cache files explicitly (or call `leak_sanitizer.scan_text` on their contents) or the privacy claim is untested where it matters most.

## Spec / documentation sync

Order 10 (`9xycbh`) documents cache location, disposability, privacy claims and limitations, and rebuild behavior. Schema version and forbidden-field rationale belong in module-level developer documentation, not an always-loaded agent instruction.

ONE TENSION CHECKED RATHER THAN ASSUMED, so the executor does not discover it mid-implementation. Spec `kw5y2s` (`- Status: approved`, unified workspace hierarchy) DOES enumerate a runtime state class `state/runtime/cache/` described as "Fast indexing and search cache" (Section 3.2), while this Set deliberately sites the analytics cache under `<resolved-runs-root>/analytics/cache/` instead. That is a defensible choice and it is Order 01's, not this plan's: the analytics tree describes the local run corpus, so it belongs beside that corpus and inherits its gitignored disposability, whereas `state/runtime/` is workspace control state. Order 01's review already established that `kw5y2s` fixes `runs` only as a traversal exclusion and says nothing about an `analytics/` child, so NO spec amendment is forced. TREAT `kw5y2s` AS IMMUTABLE HERE: it is approved, a plan-time edit would invalidate the human attestation, and this plan declares no spec file in `Scope-Paths`. If execution concludes the two cache locations genuinely conflict, STOP and raise it rather than editing the spec or relocating the cache unilaterally, because nine plans depend on Order 01's namespace.

## Open questions

Two decisions were unmade behind the "No open questions" claim (F-9). Neither BLOCKS execution: both are resolvable by the executor from repository evidence, and each is recorded here so the choice is deliberate and reviewable rather than incidental.

### OQ-01: Where does the hash salt live, and what is its correlation scope?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: F-9
- Resolution or deferral rationale: RESOLVED AT REVIEW from repository evidence: the salt lives BESIDE THE CACHE, inside the gitignored analytics subtree, and is per-box and never committed. Three reasons, all from existing repository facts rather than preference. The runs tree carries `records/runs/` in `.aw/.gitignore`, so anything under it is untracked by construction and cannot leak into git history, which is the only storage property the Findings requirement actually needs. `.aw/config/local.json` is the other per-machine candidate and is REJECTED because it is a user-facing configuration surface whose keys the setup wizard manages, and a cryptographic salt is not a setting a human should see or edit. And the cache is DISPOSABLE by this plan's own convention, so losing the salt with the cache is correct behavior: a rebuilt cache SHOULD get fresh identifiers, since the alternative (a durable salt outliving the data it pseudonymizes) is what makes cross-submission correlation possible without consent. Correlation scope therefore defaults to ONE BOX AND ONE CACHE GENERATION, and any wider scope is Order 09's explicit opt-in to own, not this item's default. E-04 must document this in the module.

### OQ-02: What happens when the cache lock is BUSY?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: F-9
- Resolution or deferral rationale: RESOLVED AT REVIEW from repository evidence: SKIP that run with a recorded, machine-readable reason; do NOT wait. `platform_lock`'s docstring states that acquisition is non-blocking and that `project_registry.save_registry` is the ONLY caller permitted to pass `blocking=True`, adding that "several callers turn the already-held case into an operator-facing refusal and an accidental block would HANG a driver rather than fail it". An analytics cache is the weakest possible justification for becoming the second blocking caller: the work is recomputable, so a skip costs one rebuild while a hang costs the operator their run. The skip is not a silent pass, which is what makes it safe: E-03 already requires a per-run `skip` decision with a reason, so a contended entry is visible in the decision output rather than quietly treated as a hit. E-05 must implement it that way and V-05 must paste it.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: PASTE the envelope definition and the ACTUAL test output for a full round-trip showing every allowed numeric fact conserved exactly (not approximately: paste the before/after values for a float, an integer and a monetary amount). PASTE the refusal for an UNKNOWN field showing the diagnostic NAMES the offending key, and the refusal for a FUTURE schema version. A round-trip that silently drops an unknown field is a FAILED item, so paste the assertion that distinguishes refuse from drop.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: PASTE the projector and the proof it is the ONLY write path (a grep or AST showing no other function writes into the envelope). PASTE the allowlist refusal of an unlisted key. PASTE the documented hashing contract: the salt's location, that it is not committed, and the correlation scope. THEN paste the independent read-side check: `leak_sanitizer.scan_text` (or `aw sanitize --agent`) run over a produced cache containing seeded canaries, reporting CLEAN, together with a control run proving the same detector DOES flag those canaries in their raw form (measured at review: a raw home path and username return `home-path` and `handle` at `fail`). Without that control, a clean report cannot be distinguished from a detector that was not looking.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: PASTE the cache decision for each required case with its reason string: first scan, unchanged completed hit, one mutated run, a RESUMED run reusing its directory, an in-progress run, an added run, a removed run, and a schema-version change. PASTE proof the fingerprint is deterministic ACROSS SEPARATE PROCESSES (byte-identical), not merely repeatable within one. State explicitly that a non-terminal run is never a stable hit and paste the case proving it.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: PASTE the interrupted-write case showing no partial cache is published (the entry is either absent or the prior valid one). PASTE the corruption case showing ONE malformed entry is rebuilt while other runs are untouched. PASTE the concurrency case with two analyzers. PASTE the busy-lock behavior with its recorded reason, and state which choice was made (skip or wait) and why. PASTE a grep proving no raw `filelock` or `fcntl` import was added and that `platform_lock` is the lock path used; a lock implemented directly on `filelock` is a FAILED item.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: PASTE the machine-readable decision output for a mixed fixture (at least one hit, one rebuild, one skip) with totals. PASTE proof a second unchanged analysis reads FEWER source files, counted (an instrumented open/parse count before and after, not an assertion that it "should" be fewer). PASTE the byte-stability comparison of two consecutive unchanged runs with the volatile metadata fields named explicitly.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: PASTE the seeded-canary fixture list and the ACTUAL test output showing none of prompts, absolute paths, command text, hostnames, usernames, environment secrets or high-entropy tokens appears in any cache JSON/JSONL, diagnostic or warning. PASTE the numeric-conservation proof across encode/decode. PASTE a BARE `python3 -m pytest` summary line with before/after counts, comparing failing NODE IDS not totals, and `git diff --check`. Re-measure the baseline yourself: at review it was `2 failed, 5655 passed, 3 skipped, 2 xfailed`, both failures pre-existing and pinned to the live plan corpus, NEITHER caused by this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: cache validity and privacy projection are inseparable because every persisted fact must cross the same boundary. RESTATED AT REVIEW: that argument justifies keeping the two in ONE PLAN, and it does not justify keeping them in one E-ITEM. The six items below are each executable in one focused pass and are grouped so the boundary is still crossed exactly once (E-04 owns the only write path), which is what the cohesion claim actually requires.

Execution requires explicit human approval (`- Status: approved`). This is Order 02 of the `runanalytics` Set: it declares `- Item-Dependencies: executed:xbwq8n`, so the runner refuses dispatch until Order 01 is executed, and Orders 03, 05 and 10 each declare a dependency on THIS plan, so a weak cache contract propagates into most of the Set.

A passing implementation must not describe the cache as anonymous or safe for public release; it is minimized and redacted, with residual re-identification risk documented. STATE THAT LIMITATION IN THE MODULE ITSELF, not only here, because the module docstring is where a later consumer will look before deciding what is shareable.

Scope fence: touch ONLY the four paths in `Scope-Paths`. Do NOT compose the runs-root or analytics path from a literal; resolve it through Order 01's resolver and constants. Do NOT use `filelock` or `fcntl` directly; use `platform_lock`. Do NOT write a second sanitizer beside `leak_sanitizer`/`local_leaks`. Do NOT weaken `worktree_lease.FORBIDDEN_WORKER_PATH_HINTS` to make analytics writable from a lane. Do NOT parse driver artifacts into facts (Order 05) or add any CLI surface (Order 08). If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never `-a`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. THIS IS A SHARED CHECKOUT: other agents may be working in it concurrently, so never revert or sweep in changes you did not make.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

RE-LOCATE BY SYMBOL, NEVER BY A LINE NUMBER. Find `runner_shared.state_root` and the analytics constants, `path_is_within_analytics`, `platform_lock.acquire`/`LockBusy`/`probe_free`, `artifact_core.atomic_write`, and `leak_sanitizer.scan_text` by name. Both this Set's Order 01 and the driver modules are actively changing.

THE ITEM THAT MATTERS MOST IS V-04's CONTROL RUN. The privacy claim is the whole reason this child is fenced as it is, and "the detector reported clean" is indistinguishable from "the detector was not looking" unless the SAME detector is shown flagging the SAME canaries in their raw form. A clean scan with no control proves nothing.

THE SECOND-MOST IMPORTANT IS THE ALLOWLIST DIRECTION. A denylist built from the Findings list would pass every test written from that same list and fail on the first field nobody imagined, which is precisely how a privacy boundary leaks. If you find yourself filtering known-bad keys rather than passing known-good ones, stop.
