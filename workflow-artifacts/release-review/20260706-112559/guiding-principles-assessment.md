# Guiding-principles adherence (seed; owner = Section 5)

Source: GUIDING_PRINCIPLES.md (10 principles). Per-principle verdict completed in Section 5.

| # | Principle | Seed observation (Section 1) |
|---|-----------|------------------------------|
| P1 | Fix by default | The framework itself embodies it (fix-decision-policy.md). |
| P2 | Honest docs | Central to the repo; the main risk axis to check in Section 4. |
| P3 | Self-documenting | README quick-start + getting-started tour. |
| P4 | Durable cold-start knowledge | README/ARCHITECTURE/DECISIONS/GUIDING_PRINCIPLES present. |
| P5 | Externalize state | run records under workflow-artifacts/. |
| P6 | KISS / guard scope | 16 commands; watch benchmark for over-scope in Section 5. |
| P7 | General case / project-agnostic | tools are stdlib-only, portable. |
| P8 | Single source of truth | index.md is the manifest; VERSION single-sourced. |
| P9 | Design for the model | MUST/SHOULD tiering, exit gates. |
| P10 | Safety / reversibility | installer stages-not-commits; tools read-only/consent-gated. |
