# Prompts (reusable prompt library)

Standalone, copy-paste prompts kept as origin and reference material. They are
independent of the installable workflows under `.agents/workflows/`, which are the
canonical, maintained versions of these ideas. When a prompt here has a maintained
successor, prefer the workflow; the prompt is retained to show where the workflow came
from and for direct copy-paste use in a tool that has no workflow installed.

These files are historical reference: they are not stamped with the framework version and
are not updated in lockstep with the workflows. Do not treat them as the current spec.

| File | What it is | Status / maintained successor |
|---|---|---|
| `modular-release-review-instruction-set-generation-prompt.md` | The meta-prompt used to generate the modular `release-review/` runbook hierarchy. | Historical. Its output is now the maintained `.agents/workflows/release-review/` framework. |
| `final-release-validation-executable.md` | A single-file autonomous "final review and release hardening" runbook prompt. | Superseded for repo use by `.agents/workflows/release-review/`. Its illustrative `repository-review/<RUN_ID>/` paths are not the shipped convention (the framework writes to `workflow-artifacts/`; see `DECISIONS.md` D19). |
| `fix-bar.md` | The "fix bar" decision policy (fix by default; defer only at Medium-High-or-higher Remediation Risk), written for RhodyPACT's IPD reviewer. | Origin note. The maintained version is `.agents/workflows/release-review/fix-decision-policy.md`; this prompt predates and inspired it. |
| `older-general-qaqc-prompt-library.md` | An older, broader library of copy-paste QA/QC, audit, sync, and release-readiness prompts. | Reference material. Lighter, general-purpose prompts not folded into a specific workflow. |

To run the maintained equivalents instead, see `.agents/workflows/index.md` (the workflow
manifest) or run `/list-workflows`.
