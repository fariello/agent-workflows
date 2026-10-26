# Check R4: Engineering Rubric

For each item, verify the plan addresses it or justifies `Not applicable`.

### A. Correctness and data integrity
- Dependent writes are atomic; retries and handlers are idempotent.
- Concurrency, uniqueness, ordering, and partial-failure risks are handled.
- Production data-store syntax, types, constraints, and migrations are valid.
- Public data, audit, and serialized formats preserve required history and
  compatibility when relevant.

### C. Architecture and operability
- The design uses existing canonical mechanisms and avoids duplicate paths.
- New dependencies, services, abstractions, and async work are justified.
- State, caching, time, retries, failure handling, observability, rollout, and
  recovery are explicit when relevant.
- The plan provisions for real needs, not hypothetical scale.

### D. Anti-regression and domain invariants
- Name each affected invariant and map it to a test.
- Preserve intended correct behavior unless an approved change fixes it.
- Add characterization coverage for risky refactors.
- Do not freeze accidental behavior that project policy says to replace.
- Treat unexplained behavior changes as blockers.

### E. Testing and verification
Require concrete tests for applicable happy, validation, authorization,
constraint, failure, rollback, retry, concurrency, integration, accessibility,
and compatibility paths.

Use production-equivalent dependencies where differences matter.

State exact validation commands, environments, and expected evidence.

### F. KISS, principles, and UX
- Prefer the smallest correct design and reuse existing mechanisms.
- Variation should be data or configuration when appropriate.
- Map the plan to each project principle with verifiable outcomes.
- Minimize user effort and define loading, empty, error, success, and recovery
  states when user-facing.
- Include keyboard, semantic, focus, naming, contrast, and assistive feedback
  when accessibility applies.
- Prevent silent failure.

### Executability: Right-sizing and conceptual density
- **Right-sizing and conceptual density (per E-item):** Evaluate whether each E-item addresses exactly **one concern** and is **executable in one focused pass**. A passing count-based size check (`aw ipd lint`) measures only structural count (>18 E-leaves / >5 groups), NOT conceptual density. For each IPD and each E-item, ask:
  (a) Does one E-item name multiple distinct deliverables or touch multiple independent code regions/files?
  (b) Does it bundle multiple independent test-surfaces (would it need several unrelated V-items)?
  (c) Could it be executed and verified as two or more independent passes?
  (d) Would a faster/weaker model lose focus/context executing it as one item?
  If YES to any diagnostic question, recommend splitting into smaller child IPDs (an UNDER-SCOPE / REPLAN finding)—a passing count-based size lint does NOT clear this.
- **Maintainer sizing signals:** A maintainer's sizing or splitting question is an actionable FINDING to investigate by decomposition, never a signal to dismiss because the size lint passed.
- Another qualified agent or developer must be able to execute the plan without inventing missing architecture.

### Spec and documentation sync
Verify that the plan's `## Spec / documentation sync` section is truthful: check that all specs, documentation, and records affected by the proposed changes are identified, and that claims of no doc changes needed are substantiated by evidence.

Record notes in the review record's `### Step R4` subsection starting with `- Checked: <what was examined>`.
Record findings per `_findings.md` in the current round's single `### Findings` table.
