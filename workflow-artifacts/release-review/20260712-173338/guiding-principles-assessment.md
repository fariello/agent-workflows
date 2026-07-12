# Guiding-principles adherence (GUIDING_PRINCIPLES.md, 10 principles)

- P1 fix-by-default: honored - 7/10 findings fixed; 3 deferred with stated axes.
- P2 honest docs: doc-accuracy findings (shim count, workflow count) fixed so docs match reality.
- P3 self-documenting: Term/--no-color fix + doc fixes improve it; no regression.
- P4 durable/append-only history: HELD - declined to rewrite ~18 executed plans' historical status (A8) precisely to respect P4.
- P5/P6 KISS/general-case: rc fix generalizes the comparator to the shape parse_describe already emits (removes a special-case inconsistency); no bloat.
- P7 single-source: honored (rc logic in one place; templates single-source).
- P8 no drift: the fixes REDUCE drift (doc<->reality, emit<->consume).
- P9 pointer-not-manual, P10 touch-only-region / never-push: honored - path-scoped commits, nothing pushed.
No principle violations introduced. Verdict: adherent.
