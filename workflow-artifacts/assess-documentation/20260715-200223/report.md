# Assessment - documentation (CHANGELOG-primary; framework is the subject)

Verdict: adequate for documentation (strong at the specialized/durable layer; the exceptions are a
CHANGELOG version mis-scoping and stale secondary/discoverability surfaces after a 6-IPD session).
IPD written: `.agents/plans/pending/20260715-2002-01-assess-documentation.md`
Run: 20260715-200223 | Method: two parallel read-only audit lanes (D84 dogfood) + coordinator synthesis.

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| F1 | HIGH | Low | engineer/operator | CHANGELOG files D80/D81/D82 (new features) under the `1.2.1` PATCH heading; their own IPDs scope them MINOR (semver: adding a convention is minor). |
| F2 | HIGH | Low | novice | TODO.md calls agent-comms "on trial / gated / would be its own IPD" and cites the retired draft spec; D81 already shipped it (canonical spec `20260715-1722-01`). |
| F3 | MEDIUM | Low | engineer | This repo's own AGENTS.md lacks the D81 "check your inbox" clause it now installs into others (pre-D81 generated, not re-synced). |
| F4 | MEDIUM | Low | novice (GitHub-web) | `.agents/plans/STATUS.md` stale: says 3 pending / 42 executed; reality 0 pending / 60 executed. |
| F5 | MEDIUM | Low | novice | `.agents/comms/` (default-on D81 feature) not discoverable from any top-level doc (README/ARCHITECTURE/AGENTS). |
| F6 | LOW | Low | engineer | CONTRIBUTING self-test module list omits `comms`/`plans` (+`pypi_links`). |
| F7 | LOW | Low | engineer | ARCHITECTURE test inventory omits `test_comms.py`/`test_plans_board.py`. |
| F8 | LOW | Low | novice | `.agents/README.md` omits `docs/` (+ future `comms/`); README lists only `prompts/` bucket. |

## Proposed plan (summary)

1. F1 (primary): move D80/D81/D82 bullets from `1.2.1 (pending)` to `1.3.0 (pending)`; revise the boundary
   note; result = 1.2.1 pure patch (D75/D76/D77/D78), 1.3.0 the feature minor. Human confirms the scoping.
2. F1c: decide + document D79's `aw plan-names` bucket line (lean: keep as a 1.2.1 bug fix).
3. F2: update TODO to reflect D81 shipped; repoint at the canonical spec; keep `aw comms` as open, drop the
   "gated" framing.
4. F3: regenerate this repo's AGENTS block via `aw install .` (do not hand-edit).
5. F4: regenerate STATUS.md via `aw plans --write-index`.
6. F5: surface `.agents/comms/` in ARCHITECTURE (subsection + repo-tree line) + README mention.
7. F6/F7/F8: small accuracy/navigation fixes to CONTRIBUTING, ARCHITECTURE, `.agents/README.md`, README.

## Deferred (with reason)

- None deferred on Remediation Risk (all fixes are Low). Explicitly OUT of scope (not deferred findings):
  the versioning mechanism, the release cut itself, building the `aw comms` helper, and the STATUS.md
  track-vs-ignore policy question.

## Recommended version-scoping table

| D-entry | What | Correct bucket | Currently in CHANGELOG |
|---|---|---|---|
| D75 | baked-VERSION re-bake fix | 1.2.1 PATCH | 1.2.1 (correct) |
| D76/D77 | aw install pre-flight parity + no-op-pull | 1.2.1 PATCH | 1.2.1 (correct) |
| D78 | plan-normalizer test flakiness (test-only) | 1.2.1 PATCH | 1.2.1 (correct) |
| D79 | docs/consistency pass | 1.2.1 (docs) + F1c bucket-line decision | 1.2.1 (partly) |
| D80 | readiness vocab + GO - PENDING HUMAN APPROVAL (new) | 1.3.0 MINOR | 1.2.1 (MIS-SCOPED) |
| D81 | .agents/comms/ convention (new) | 1.3.0 MINOR | 1.2.1 (MIS-SCOPED) |
| D82 | Set:/Order: plan front-matter (new) | 1.3.0 MINOR | 1.2.1 (MIS-SCOPED) |
| D83 | install-orchestrator unification (internal) | 1.3.0 MINOR | 1.3.0 (correct) |
| D84 | auto-parallel audit lanes (new workflow feature) | 1.3.0 MINOR | 1.3.0 (correct) |

Next step: review the IPD (optionally run plan-review on it) and approve before execution. This workflow
does not execute the plan.
