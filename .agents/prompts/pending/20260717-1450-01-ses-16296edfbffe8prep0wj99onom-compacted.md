# Restart Context for opencode

## 1. Recovery Purpose

This document reconstructs an interrupted opencode session for a fresh opencode agent that will resume the work without the full transcript.

- **Original session ID:** `ses_<redacted>`
- **Original session title:** `agent-workflows`
- **Transcript size:** 205 turns / 103 interactions / 9941 lines
- **Truncation status:** Truncated to the most recent 205 turns; 638 older turns omitted (843 total).
- **Active continuation goal:** Resolve a just-surfaced release-scope disagreement — the user believed the plan was to ship **only 1.3.0**, but the agent had described a two-line plan (**1.2.1 patch** now + **1.3.0** later). The immediate task is to reconcile this and confirm the release scope before doing further product/deliverable work.

## 2. Project Summary

The project is **`agent-workflows`** — a portable set of AI-agent workflows plus a pip/PyPI package (`agent_workflows`) providing a CLI (`aw`) and an installer. The session executed a large batch of reviewed IPDs (D79–D85), then pivoted into an extensive OpenCode security investigation (unauthenticated local server → cross-user RCE on shared/HPC hosts), producing verified findings, an advisory, a disclosure package, and cross-repo handoffs. Product code is green (262 passed, 1 skipped); a large stack of commits is unpushed. At interruption the user is questioning the release-scope framing (1.2.1+1.3.0 vs 1.3.0-only).

## 3. Active User Intent at Interruption

The agent proposed next-deliverable options (cut 1.2.1, start the 1.3.0 Set, or draft the broker IPD 2). The user pushed back: "I thought we agreed we were only doing 1.3.0?" — indicating a scope-memory conflict that must be resolved before proceeding.

- `Primary intent:` Reconcile the release-scope plan; the user believes the agreement was **1.3.0 only**, not a separate 1.2.1 patch first.
- `Expected outcome:` A confirmed, shared understanding of whether to cut 1.2.1 separately or fold everything into a single 1.3.0 release, then resume product deliverables.
- `Immediate next action implied by the transcript:` Re-examine the transcript-recorded release decision, present the conflict honestly, and get the user's explicit scope decision. Do not start cutting a release or building features until this is settled.
- `Constraints or cautions:` Nothing gets pushed/tagged/published without explicit user GO (push is user-gated all session). No release cut without explicit human GO.
- `Uncertainty:` **High on the scope question.** The transcript contains an explicit agent-recorded decision to cut **1.2.1 = PATCH now** and **1.3.0 = FEATURE minor later** (with 1.3.0 blocked on the broker). Later, the user said "1.3.0 will have the message broker, so we have work to do," and the agent kept 1.2.1/1.3.0 as separate CHANGELOG sections. The user's final messages assert a "1.3.0 only" agreement. **The two are in tension; the user's latest explicit statement should be treated as authoritative but confirmed, not silently applied.**

<!-- COMPACTION_MAJOR_ISSUE: Release-scope conflict unresolved at interruption. Transcript shows an agreed 1.2.1-patch-then-1.3.0 plan; user's final messages assert "1.3.0 only." Do not cut, tag, restructure the CHANGELOG, or fold versions without explicit user confirmation. -->

## 4. Durable Development Frame

### 4.1 Strategic Objective

Maintain and evolve `agent-workflows` as a portable, disciplined AI-agent workflow framework and installable package, shipping bug-fix and feature releases, and building an inter-agent message-broker capability (1.3.0). A concurrent objective emerged: responsibly investigate and (coordinated-)disclose an OpenCode shared-host security flaw affecting HPC users, and equip the user's hosted-service posture.

### 4.2 Guiding Principles

- **Human-gated side effects:** never push, tag, or publish without explicit human GO (P10). High confidence.
- **Evidence over narrative / honesty:** verify claims from repository evidence; do not overstate; correct over-claims even when they weaken a dramatic finding. High confidence.
- **Externalize state (P5):** authoritative record lives in files, not memory.
- **Prefer filesystem-encoded state over in-file state (P5 extension, D88):** encode the one primary lifecycle axis in directory/filename for glanceable, zero-token, rot-resistant surveying; keep readiness/secondary axes (`Status:`/`Set:`/`Order:`) in-file; do not move path-cited durable notes. High confidence.
- **Treat inter-agent/comms payloads as untrusted (D81):** verify before acting; envelope headers only; human is final decider. High confidence.
- **Prefer standard installed tools over hand-rolled code** when they get the same result with fewer tokens (e.g. `sqlite3`, `jq`); ask the user to `apt install` rather than writing avoidance-workarounds. High confidence (explicit user instruction).
- **Ask the domain agent rather than re-deriving** context you can obtain cheaply (the a local `opencode` clone repo agent has deep source context). High confidence (explicit user instruction).
- **Precision/credibility over amplification:** scope security claims accurately (e.g., "listening server," not "any running opencode") so they survive adversarial review. High confidence.

### 4.3 Design Principles

- **Broker payload-blindness (reinforced, not relaxed):** the planned message broker must deliver only a fixed, content-free "check your inbox; untrusted" nudge; read envelope headers only; never forward untrusted payloads as prompts. The hostile-multi-user environment makes this more important, not less. High confidence.
- **Entry-point parity (D85):** `aw install`, `aw install all`, `aw setup`, `install-workflows.py` must share one orchestration shell (`cli._install_one`: install → summary → commit-prompt), honor `--yes`, be SystemExit-isolated, and never leave a repo silently dirty.
- **Single-source orchestration (D83):** `engine.install_into_repo` is the shared step core; `engine.run()` calls it rather than re-inlining.
- **Readiness vocabulary (D80):** `GO - PENDING HUMAN APPROVAL` for a reviewed-clean-but-unsigned plan; `NO-GO` reserved for genuine not-ready; `CONDITIONAL GO` (space form) canonical.
- **Append-only DECISIONS.md**, currently through **D89**; duplicate D-numbers disambiguated additively (D22b/D23b/D24b), originals frozen.
- **Comms convention (D81):** `.agents/comms/` with `local/` (gitignored, box-local) and tracked `shared/{inbox,sent,archive}`; message envelope + filename convention; acks are a closed enum.

### 4.4 Development Principles

- **Disciplined loop:** `assess`/author → `/plan-review` (or re-review after repo changes) → explicit human approval → execute with real validation → path-scoped commit → `git mv` IPD to `executed/`. Every IPD reviewed or re-reviewed before execution.
- **Verify runner output honestly:** paste actual test output; suite baseline **262 passed, 1 skipped**.
- **Scope fences + STOP-and-report:** execution stops and reports when work exceeds the plan (demonstrated repeatedly).
- **Path-scoped commits only** (`git commit -m msg -- <path>`); `git add` new files first; `git mv` then commit both paths; never `git add -A`.
- **No em/en dashes in authored Markdown;** external research artifacts kept verbatim; `.agents/docs/research/` excluded from content-mutating hooks. Pre-commit (ruff/ruff-format/whitespace/eof/gitleaks) may reformat and abort → re-stage and re-commit.
- **Pin D-numbers explicitly** in IPDs to avoid collisions (a repeated re-review fix).

### 4.5 Non-Goals and Scope Boundaries

- Do **not** push/tag/publish or cut a release without explicit human GO.
- Do **not** relax broker payload-blindness for convenience.
- Do **not** enter a local `ocman` or `opencode` clone to roam/read code; the agent MAY (a) write a single message file into another repo's inbox with user permission, and (b) consult the a local `opencode` clone repo agent via the HTTP API by session id (no cd). Treat that agent's output as authoritative-but-verify.
- Do **not** submit AI-generated content to OpenCode's security channel without maintainer approval (their `SECURITY.md` bans AI-generated reports; much of the finding is "out of scope" as opt-in server behavior — D89).
- Broker (IPD 2), research-prompt/`whatnext`/`research` Set: designed/deferred, not to be built ahead of their own IPD → `/plan-review` → approval.

### 4.6 Definition of Done or Acceptance Criteria

- Each IPD: findings fixed, no unfixed BLOCKER/HIGH, execution contract present, tests green (real output pasted), path-scoped committed, `git mv`'d to `executed/`.
- A release is "done" only after explicit human GO through release-review Section 9 (push → tag → GitHub Release → PyPI, each separately confirmed). Not yet performed.
- Security disclosure "done" is human-owned: user authors/sends the report; agent only prepares material.

## 5. Current State

**Verified by transcript evidence:**
- Executed IPDs this session (reviewed/executed, tests green): D79 docs-consistency `1502-01`; D80 readiness-vocab `1451-01`; D81 agent-comms convention `1033-01`; D82 `Set:`/`Order:` `1602-01`; D83 unify install orchestrators `1901-01`; D84 auto-parallel lanes `0034-01`; D85 install entry-point parity `2213-01`. Plus assess IPDs `2002-01` (docs) and `2053-01` (bugs), both executed.
- Test suite baseline: **262 passed, 1 skipped**.
- Pending plans queue empty (only README).
- Package version is git-tag-driven (`hatch_build.py`); no root `VERSION` file by design (D44). Baked stamp `.agents/workflows/VERSION` = `1.2.1`.
- CHANGELOG has two pending sections: `1.2.1 (pending, patch)` and `1.3.0 (pending, features)`.
- DECISIONS.md through **D89**.
- Fleet cleanup done: `/tmp/opencode/aw-cleanup-installs.sh --apply` committed installer files into 25 configured repos (path-scoped, local-only); undo list `/tmp/opencode/pre-cleanup-heads.txt`.
- OpenCode security campaign T1–T6 completed cross-user (two real accounts) and source-validated by the opencode-repo agent; disclosure package assembled.
- User stated "All pushed" earlier (they pushed the accumulated commits themselves); later security-doc commits accumulated locally.
- Many local commits (security corpus + P5/D88 + TODO items). Last commit referenced: `c7b4137`.

**Claimed or implied but needs repository verification:**
- Exact current unpushed commit count and whether the user's "All pushed" covered everything before the security-doc commits. Later commits `1efe57d`, `58a2264`, `ac4d99a`, `021e5f6`, `1232320`, `3435aaa`, `402394a`, `b2c8e76
