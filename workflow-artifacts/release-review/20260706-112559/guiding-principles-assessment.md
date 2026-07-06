# Guiding-principles adherence (owner: Section 5)

Source: GUIDING_PRINCIPLES.md (10 principles). Verdict per principle, with evidence.

| # | Principle | Verdict | Evidence / notes |
|---|-----------|---------|------------------|
| P1 | Fix by default; justify deferral | ADHERES | fix-decision-policy.md is the canonical policy; this very review applies it. |
| P2 | Honest not aspirational docs | MOSTLY (2 stale counts) | Strong overall, but S4-D1 (shims 15->16) and S4-D2 (three tools->four) are honesty slips introduced by D41. GP-tagged via those D findings; fix in S7. |
| P3 | Self-documenting / learn-as-you-go | ADHERES | README quick-start, getting-started tour, tool --help/--version. Minor: S4-D3 (tour omits benchmark route) is a self-documenting gap. |
| P4 | Durable cold-start knowledge | ADHERES (exemplary) | README/ARCHITECTURE/DECISIONS/GUIDING_PRINCIPLES; DECISIONS D1-D42 dated with why. |
| P5 | Externalize state | ADHERES | run records under workflow-artifacts/; this review is an instance. |
| P6 | KISS / guard scope creep | ADHERES (watch) | 16 commands / 29 lenses / 7 personas is a large surface, BUT: shared harness+catalog (assess/advise) keeps it single-sourced, and each capability is traceable to a stated need. benchmark is large but was explicitly requested with detailed requirements (not gold-plating). No over-scope finding; noted as the axis to keep watching. |
| P7 | General case / project-agnostic | ADHERES | tools are stdlib-only and portable; bench_env degrades on non-Linux honestly; bodies are tool-agnostic. |
| P8 | Single source of truth | ADHERES | index.md is the manifest (installer reads it); VERSION single-sourced and consistent across 3 surfaces; policies referenced not duplicated. |
| P9 | Design for the model that runs it | ADHERES | MUST/SHOULD tiering, exit gates, context-assembly ordering, per-section loop. |
| P10 | Safety / reversibility | ADHERES | installer stages-not-commits + backups; tools read-only or consent-gated; run_checks denylist; HPC submit needs per-submission consent. |

No standalone GP findings beyond those already captured as S4-D1/D2/D3 (which are the P2/P3
manifestations). No principle is violated in a way not already tracked.
