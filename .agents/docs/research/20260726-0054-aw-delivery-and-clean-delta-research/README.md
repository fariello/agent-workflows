# Research bundle: external delivery + clean-delta contribution (2026-07-26)

This directory holds the full evidence set produced from two staged research prompts and the
reconciliations that synthesize them. It is the durable evidence that IPD `20260723-1100-05`
(external / out-of-repo delivery) and IPD `20260723-1100-07` (clean-delta / per-class tracking
opt-out) were blocked on. It is documentation-graded (verified against first-party host docs as of
2026-07-26); no live per-host fixture was run, so "Followed" means documented, not reproduced.

## Contents

Files are numbered 01-05 within each set in the order gpt56, gemini36flash, gemini31pro, sonnet5,
reconciliation, so `ls` groups them cleanly. The two sets share the concern but were separate
research runs, so each keeps its own timestamp prefix.

Clean-delta set (`20260726-0054-NN-aw-delivery-and-clean-delta.<suffix>`):

- `01 .research-report.gpt56.md`
- `02 .research-report.gemini36flash.md`
- `03 .research-report.gemini31pro.md`
- `04 .research-report.sonnet5.md`
- `05 .reconciliation-report.md` - start here: reconciles the four into a single recommended
  architecture (skills-first discovery, a sibling companion repo for tracked artifacts, user-global
  per-repo mapping, a separate global ownership manifest, merge-base diff verification, phased plan
  with a Phase 0 conformance harness).

Host-probe set (`20260726-1045-NN-external-delivery-host-probe.<suffix>`):

- `01 .research-report.gpt56.md`
- `02 .research-report.gemini36flash.md`
- `03 .research-report.gemini31pro.md`
- `04 .research-report.sonnet5.md`
- `05 .reconciliation-report.md` - start here: reconciles the four into a per-host x per-tier
  (T1 out-of-repo pointer / T2 host-native skill / T3 user-global) verdict matrix.

The filenames above were normalized on filing into this bundle; the model outputs themselves are
unchanged (one model report stamps its own original `File Identifier` in its header, which was left
verbatim).

## Prompts that produced this

- `.agents/prompts/pending/20260725-2341-01-aw-delivery-and-clean-delta.research-prompt.md`
- `.agents/prompts/pending/20260725-0957-01-external-delivery-host-probe.research-prompt.md`

## A note on verbatim external artifacts

The underlying model reports are preserved VERBATIM as third-party evidence. Some contain em/en
dashes (the no-dash rule governs Markdown authored in this repo, not faithful external evidence).
One source report (`...gemini36.md`) originally cited a maintainer-specific `file:///home/...`
absolute path; that single path was abstracted to a portable placeholder to satisfy the local-leaks
sanitizer without altering the report's substance (a bracketed note marks the edit).
