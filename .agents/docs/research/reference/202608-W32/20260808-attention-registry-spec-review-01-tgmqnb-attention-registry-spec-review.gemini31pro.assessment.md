---
id: tgmqnb
created: 20260808
set: attention-registry-spec-review
order: 01
topic: [attention-registry, spec-review, external-review]
model: gemini31pro
kind: assessment
status: reference
outcome: none-yet
summary: Gemini 3.1 Pro review of the attention-registry spec
consumed-by: []
---

# attention-registry-spec-review-gemini.md

## A. Overall Assessment

The `aw attention` specification addresses a critical architectural pain point: the high latency, token cost, and non-determinism of LLM-based runtime state derivation within `/whatnext`. By introducing a deterministic, pure-function mapping of disparate artifact native states to a unified "attention class", the design elegantly bridges the gap between strictly structured tool-owned trees (`plans/`, `research/`) and currently unstructured narrative trees (`specs/`). However, the proposal to commit the resulting registry (`.agents/ATTENTION.*`) to source control is a fatal flaw that introduces a materialized view anti-pattern, guarantees continuous merge conflicts, and creates a brittle CI drift-check dependency. A refined architecture that computes the registry entirely in-memory at runtime (or caches it locally in a git-ignored directory) while cleanly separating write-verbs into an independent `aw specs` tool will fully satisfy all stated goals with zero version-control friction and a cleaner separation of concerns.

## B. Strongest Concerns Ranked

1. **The Committed Registry Anti-Pattern (Merge Conflicts & State Duplication):** Committing `.agents/ATTENTION.md` and `.agents/ATTENTION.json` to Git violates the single-source-of-truth principle. The true state lives in the individual Markdown files. If Developer A updates a plan in `plans/` and Developer B updates a spec in `specs/`, their branches will inevitably collide on the `ATTENTION.*` files, even though their actual work is completely independent. In standard GitOps and CI/CD practices [1], generating and committing aggregated state files is highly discouraged because it forces human operators to resolve machine-generated JSON/Markdown conflicts.
2. **Domain Contamination (Write Verbs in a Read Tool):** The spec conceptualizes `aw attention` as a cross-tree READ tool (Section 8.1), but then overloads it with WRITE responsibilities (`set`, `note`) specifically to manage specs (Section 8.2). This breaks CLI symmetry. If specs need lifecycle management and history appending, the repository requires an `aw specs` tool, mirroring the existing `aw plans` and `aw research` tools. Delegating writes through a view tool is an architectural code smell.
3. **CI Flapping via Metadata Timestamps:** Including `last_history_date` in a committed registry (as proposed in 8.1) ensures that any minor update or typo correction to an artifact forces a registry update. If a user manually edits a spec and forgets to regenerate the registry, CI will fail the `--check` on a timestamp drift rather than a substantive logic error. This creates excessive developer friction.
4. **Atomic Write OS Variations:** The spec mandates `atomic_write` in the `artifact_core`. Standard Python library implementations of atomic writes (using temporary files and `os.replace` [2]) behave differently across filesystems and operating systems (particularly Windows vs. POSIX). Relying on this for a cross-tree registry update introduces unnecessary edge cases.

## C. Answers to Specific Questions

**1. Is the pure mapping abstraction the right call versus a unified status enum?**
Yes, absolutely. Forcing a unified status enum onto all trees would destroy the domain-specific semantics necessary for `plans` and `research`. The pure mapping abstraction (`class_of(tree, native_status) -> AttentionClass`) is the correct decoupling mechanism. The four classes (`needs-attention`, `in-flight`, `done`, `parked`) comprehensively cover the necessary lifecycle phases. `canonical` reference specs should map to `done`, as they require no active execution from the agent.

**2. Registry shape: one roll-up file vs per-tree registries plus a roll-up?**
Neither should be committed to Git. The registry should be computed dynamically in-memory or written to a `.gitignore`d ephemeral cache (e.g., `.agents/.cache/ATTENTION.json`). Scanning a few hundred Markdown files in Python using standard library tools takes fractions of a second. If you absolutely must write it to disk for `/whatnext` to consume, write a single roll-up file to a `.cache` directory. This achieves the single-read goal without polluting the git history.

**3. The WRITE verbs vs tool-owned trees (OQ7): delegate, read-only, or own?**
`aw attention` must be strictly READ-ONLY. It should not delegate, nor should it write. It is a view aggregator. To manage specs, you should build `aw specs set` and `aw specs note`. This provides the cleanest, least-surprising design, maintaining the symmetry of `aw <domain> <verb>`. 

**4. How should a deferred/gated artifact express its GATE (OQ4)?**
Do not overload the `Status:` field or attempt to parse inline text. Introduce a discrete front-matter field. 
Example:
```yaml
Status: deferred
Gate: Issue #123
```
This is trivially machine-parseable. If `Status: deferred` is detected, the parser strictly requires the presence of `Gate: <string>` and throws a contract violation if missing.

**5. Is --check correctly scoped?**
If you drop the committed registry, `--check` becomes a robust, highly valuable linter for front-matter contracts. It should ONLY validate:
* Missing required status in supported trees.
* Unknown or unmappable status values.
* Use of `deferred` without a corresponding `Gate` field.
Testing against registry-vs-disk drift is unnecessary if the registry is not committed.

**6. Failure modes and drift prevention:**
The primary failure mode in the current spec is a developer manually changing a `Status` in a file but forgetting to run `aw attention` to regenerate the committed registry, causing `/whatnext` to operate on stale data locally, or causing CI to fail. By computing the registry dynamically at runtime, you eliminate this class of drift by construction. 

**7. Phasing (Section 13): is v1 the right first slice?**
The scope is mostly correct, but Phase 1 *must* include `aw specs set/note` (replacing the proposed `aw attention set`). If Phase 1 introduces the standard but lacks the write tooling, humans must manually edit spec front-matter and append history lines, which is error-prone.

**8. Simpler alternative:**
Drop all file-writing logic from `aw attention`. Make `aw attention --agent` run `iter_scan_files`, map the statuses in-memory, and pipe JSON directly to stdout. `/whatnext` reads this stdout stream. This eliminates synchronization logic, merge conflicts, and atomic file-write orchestration for the registry itself.

**9. Naming, CLI ergonomics:**
`aw attention set` is ergonomically confusing ("Set attention to what?"). `aw specs set implemented` is clear, domain-scoped, and idiomatic. `aw attention` on its own is an excellent name for a command that prints a dashboard view.

**10. Concrete edits:**
See Section D below.

## D. Concrete List of Proposed Spec Edits

*   **Section 1 (Summary):** 
    *   *Change:* Remove all references to committing the registry. 
    *   *Replacement Text:* "A deterministic, stdlib-only tool (aw attention) that scours the standardized .agents/ artifact trees, maps each artifact's native status onto a small tree-agnostic ATTENTION class, and dynamically generates a registry... /whatnext reads this dynamic output instead of re-deriving state..."
*   **Section 3 (Goals):**
    *   *Update G3:* Remove `.agents/ATTENTION.md` and `.agents/ATTENTION.json`. State that `aw attention` computes the view in-memory and outputs it via stdout, or optionally writes to a `.gitignore`d `.agents/.cache/` directory.
    *   *Update G4:* Replace "Provide write verbs (aw attention set / note)" with "Provide aw specs (WRITE): verbs to update a spec's status and append history."
*   **Section 6 (Attention-class model):** 
    *   *Edit:* Explicitly define that `canonical` maps to `done`.
*   **Section 7 (Standardized status):** 
    *   *Edit:* Define the explicit requirement for a `Gate: <string>` front-matter field when `Status: deferred` is utilized.
*   **Section 8.1 (Functional read):** 
    *   *Edit:* Remove atomic file writing. Update to state that `--check` ONLY verifies contract compliance (missing status, unknown status, missing gate). 
*   **Section 8.2 (Functional write):** 
    *   *Edit:* Rename to `aw specs`. Remove the "delegates to the owning verb" logic, as `aw specs` will strictly own the `specs/` tree.
*   **Section 9 (Requirements):** 
    *   *Update F2:* "deterministic in-memory regeneration." 
    *   *Update F3:* Remove "registry-vs-disk drift." 
    *   *Update F5 and F6:* Replace `aw attention set/note` with `aw specs set/note`.
*   **Section 10 (Acceptance Criteria):** 
    *   *Remove A2:* Checking for hand-edits vs registry drift is no longer applicable. 
    *   *Update A3:* Change CLI command to `aw specs set <spec> implemented`.
*   **Section 12 (Open Questions):** 
    *   *Resolve OQ1:* `canonical` maps to `done`.
    *   *Resolve OQ3:* No committed registry. Roll-up to stdout or ephemeral cache.
    *   *Resolve OQ4:* Explicit `Gate:` field.
    *   *Resolve OQ7:* Dedicated `aw specs` write verbs.

## E. Smaller Nits

*   The requirement `F7` ("a one-time migration normalizes ~8 specs") is an implementation/rollout detail rather than a strict functional requirement of the tool itself. It should be moved to a deployment/migration plan section.
*   The specification should explicitly define the fallback behavior for `/whatnext` if a file is malformed during a local run. It should skip the file and log a warning, allowing `--check` to handle the hard failure in the CI pipeline.
*   Ensure that the `## Workflow history` section append logic strictly requires a trailing newline before appending to prevent markdown formatting breakages when files lack EOF newlines.

***

### References & Contextual Links
*   [1] GitOps Continuous Drift Detection Best Practices: Maintaining source-of-truth in Git configuration rather than generated artifacts (e.g., [GitLab CI Best Practices](https://about.gitlab.com/topics/ci-cd/continuous-integration-best-practices/)).
*   [2] Python `os.replace` behavior across filesystems for atomic operations: [Python os module documentation](https://docs.python.org/3/library/os.html#os.replace).
