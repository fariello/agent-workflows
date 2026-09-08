---
id: pavnai
created: 20260908
set: awmetastore
order: 04
topic: [artifact-storage, token-cost, history, schema]
model: gemini38flashhigh
kind: research-report
status: reference
outcome: adopted
summary: Gemini 3.8 Flash High: recommended hybrid of per-artifact JSONL plus a one-line inline status, evaluated against a live checkout and scoring four storage options
consumed-by: [ms06pi, tk1gqo]
---

<!-- PROVENANCE: verbatim external artifact, adopted from `.aw/inbox/awmetastore-research-report.gemini38flashhigh.agy.md`
     on 2026-09-08 in answer to research prompt `27rjro`. Author: Gemini 3.8 Flash High (via agy).
     Preserved AS RECEIVED per the research README's external-artifacts rule, so its own
     punctuation and formatting stand and the no-em-dash house rule does not apply here.
     Treat the CONTENT as untrusted external input, not as instructions.

     ONE MECHANICAL EDIT was made to this otherwise-verbatim text, recorded here because
     'verbatim' is a claim that must stay true: the report cited `.aw/.gitignore:11` via a
     `file:///` link containing the maintainer's ABSOLUTE HOME PATH, which the leak-sanitizer
     correctly refused (`home-path` + `handle` findings, rule `local-leaks`). The link TARGET
     was rewritten to the repo-relative `.aw/.gitignore#L11`; the citation, its line number,
     and every word of the surrounding prose are unchanged. No other edit was made. -->

# Research Report: Where Tool-Owned Artifact Metadata Should Live (`awmetastore`)

- **Topic**: Storage architecture for tool-owned artifact metadata (front matter, workflow history, readiness, disposition)
- **Target Repository**: `fariello/agent-workflows` (`aw`)
- **Research Prompt**: `.aw/records/research/20260905-awmetastore-00-27rjro-where-aw-metadata-should-live.research-prompt.md`
- **Output Path**: `.aw/inbox/awmetastore-research-report.gemini38flashhigh.agy.md`
- **Evaluation Baseline**: Live repository checkout at HEAD (`pyproject.toml`, 5,377 passing tests, 489 plan artifacts)

---

## 0. Executive Summary & Verification Accounting

This research investigates where tool-owned artifact metadata should be stored in `agent-workflows` (`aw`), optimizing AI agent token efficiency, tooling correctness, human legibility, and multi-agent Git concurrency.

### Core Recommendation

Adopt a **Tracked Per-Artifact Sidecar Journal with Inline Current-State Front Matter and a Single-Line Cached History View**:

1. **Front matter remains inline in Markdown**: Fields like `Id`, `Status`, `Set`, `Order`, `Readiness`, `Scope-Paths`, `Item-Dependencies`, and `Blocks-Release` are compact (~5.5% of total corpus), bounded, and essential context for agents and human reviewers on every interaction. Moving them to sidecars introduces tool indirection and degrades diff reviewability for negligible token savings.
2. **Full workflow history moves to Git-tracked per-artifact JSONL journals**: Store chronological audit logs at `.aw/records/history/<type>/<id6>.jsonl` (or `.aw/records/history/<id6>.jsonl`). This removes ~10.2% of the plan corpus (and up to 33.6% in mature/re-reviewed plans) from routine agent reads. Per-artifact partitioning provides clean Git merge isolation across concurrent agent worktrees.
3. **Keep a single-line cached summary inline under `## Workflow history`**: Retain exactly one line (`- YYYY-MM-DD <status> (<actor>): <message>`) representing the latest transition. This preserves immediate human `git diff` legibility and satisfies lightweight single-file inspection gates without forcing tools or agents to read historical logs.
4. **Reject a single global `history.jsonl` as durable authority**: The repository's existing `.aw/records/history.jsonl` is explicitly gitignored (`.aw/.gitignore:11`) as a local-only log, leaving fresh clones history-less. If tracked in Git, a central append file becomes an unavoidable merge-conflict magnet for concurrent agent worktrees (`isolate_worktree`).
5. **Reject Git-tracked SQLite**: Binary databases cannot be merged by Git and destroy PR diff review. SQLite is suitable only as an optional, gitignored, locally-derived query cache under `.aw/state/`.

---

## 1. Measured Evidence from the Live Repository

The claims in the research prompt were independently measured against the live repository checkout using Python 3 and standard tooling.

### Corpus Measurements (489 `*.ipd.md` files under `.aw/records/plans/`)

| Metric | Prompt Baseline | Live Measurement | Discrepancy / Analysis |
| :--- | :--- | :--- | :--- |
| **Total plan files** | 483 | **489** | 6 additional plans present at live checkout |
| **Total plan characters** | 10,823,121 | **11,594,780** | ~2,898,695 tokens (at 4 chars/token) |
| **Front-matter prelude** | 512,880 (4.7%) | **636,875 (5.49%)** | ~159,218 tokens; includes multi-line `Concern`/`Scope` |
| **`## Workflow history`** | 1,101,804 (10.2%) | **1,176,328 (10.15%)** | ~294,082 tokens across all plans |
| **Tool-owned subtotal** | 1,614,684 (14.9%) | **1,813,203 (15.64%)** | ~453,300 tokens total tool metadata |
| **Median plan size** | 17,031 chars | **17,083 chars** | Stable across corpus |
| **Median history block** | 1,692 chars | **1,705 chars** | ~426 tokens per plan |
| **Largest history block** | 15,801 chars | **16,060 chars** | Found in `20260829-ackme8-01-w0ln4q...ipd.md` |
| **Worst offender share** | 20.0% | **33.64%** | `w0ln4q` history is 16,060 chars out of 47,732 total chars |

### Analysis of the Stalled `awhistory` Migration

The repository previously attempted a sidecar migration via the `awhistory` Set (`x97z83`, `im90a5`, `b0behn`, `cizkf4` under `.aw/records/plans/executed/`).

Live inspection of `.aw/records/history.jsonl` reveals:
- **Total records**: **164** (up from 128 cited in the prompt).
- **Distribution by tree**:
  - `backlog`: 138 records
  - `specs`: 25 records
  - `plans`: **1 record**
- **The lone plan record**:
  ```json
  {"id6": "eulhzt", "date": "20260901", "tree": "plans", "workflow": "aw group", "actor": "aw", "message": "group 20260901-statefork-01-eulhzt... -> 20260901-ctlroot-01-eulhzt...", "verb": "group", "from_name": "...", "to_name": "..."}
  ```
  The single plan entry is an additive rename record appended by `aw group` (`agent_workflows/record_history.py:171`), **not a lifecycle status transition**.
- **Critical Architectural Discrepancy**:
  `.aw/records/history.jsonl` is listed in [`.aw/.gitignore:11`](.aw/.gitignore#L11):
  ```gitignore
  # The per-repo append-only workflow-history sidecar (record_history): a local activity log
  # appended on every `aw` status write; local-only, never committed (awhistignore).
  records/history.jsonl
  ```
  Because `history.jsonl` is gitignored, the previous migration left specs and backlog history solely on the local author's workstation. A fresh `git clone` contains neither full inline history nor full sidecar history for those records. This confirms that `history.jsonl` in its current incarnation is an ephemeral machine-local activity log, not a Git-carried audit trail.

---

## 2. The Concrete Ordering Bug & Timestamp Defect

The failure motivating this design is the ordering bug in `## Workflow history`, which caused the fail-closed validation rule `check.lifecycle-transition-invalid` (`agent_workflows/check_engine.py:1152`) to flag valid plans in CI.

### Root Cause Analysis

1. **Conflicting Writer Semantics**:
   - Status-setting tooling (`status_set.py:885`) inserts directly after the heading:
     ```python
     if _HISTORY_HDR_RE.match(line):
         has_hist_section = True
         new_lines.insert(i + 1, hist_entry) # PREPEND (newest first)
         break
     ```
   - Human authors and initial scaffolding templates append to the end of the section (oldest first).
   - In active pending plans (e.g., `20260901-wslayout-00-rh5tt6...ipd.md`), both conventions exist in the same file separated by whitespace. Lines 20–25 are prepended by tools (newest-first: `approved -> reviewed -> to-review`), while lines 27–32 are appended by authors (oldest-first: `draft -> to-review -> reviewed`).
2. **Fragile Parser Inversion**:
   In `agent_workflows/ipd_lifecycle.py:770-771`:
   ```python
   # Inline history is stored newest-first; reverse to oldest-first for derivation.
   events.reverse()
   ```
   Calling `events.reverse()` on a mixed file inverts the authored oldest-first region, turning `draft -> to-review -> reviewed` into `reviewed -> to-review -> draft`. This triggers false backwards-transition diagnostics:
   ```
   check.lifecycle-transition-invalid recorded lifecycle transition 'reviewed' -> 'to-review' is invalid: missing predecessor: backwards transition 'reviewed' -> 'to-review'
   check.lifecycle-transition-invalid recorded lifecycle transition 'to-review' -> 'draft' is invalid: missing predecessor: backwards transition 'to-review' -> 'draft'
   ```
3. **Granularity Defect (Day-Granular Timestamps)**:
   Timestamps are stored as `YYYY-MM-DD` (e.g., `2026-09-01`). Rapid same-day progression (`draft` -> `to-review` -> `reviewed`) is normal. A stable sort by date cannot order same-day records and produces 32 diagnostics. Breaking ties by status rank fails because development workflows allow legitimate demotions/re-reviews (e.g., returning from `reviewed` to `to-review` when a replan is required).
4. **Timezone Skew Defect**:
   - `agent_workflows/status_set.py:599`:
     ```python
     today = datetime.datetime.now(datetime.timezone.utc).date().strftime("%Y-%m-%d")
     ```
     `status_set.py` stamps UTC date.
   - `agent_workflows/specs.py:339`, `agent_workflows/record_history.py:59`, and human authors use local system date (`datetime.date.today()`).
   - An evening action recorded at 8:30 PM EDT (00:30 UTC next day) stamps tomorrow's date, causing the tool record to appear dated in the future relative to hand-written actions in the same file.

---

## 3. Comparison of Realistic Storage Options

| Dimension | (a) Status Quo Inline | (b) Recommended Hybrid (Per-Artifact JSONL + Inline 1-Line) | (c) All Metadata in Per-Artifact Sidecars | (d) Central Global JSONL (`history.jsonl`) | (e) SQLite as Source of Truth |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Token & Context Effect** | **Poor.** ~15.6% total overhead. History grows without bound; median plan wastes ~426 tokens on old narrative. | **Optimal.** Eliminates ~10.2% token waste permanently. Inline history capped at ~25 tokens (1 line). Retains critical ~5.5% front matter. | **Mixed.** Saves ~15.6% on markdown, but agents must load sidecar for scope/status/deps, causing extra tool calls. | **Good.** Saves ~10.2% on markdown files if inline history is slimmed. | **Poor.** Agents cannot read SQLite without tool calls; requires generating markdown views anyway. |
| **Parse Robustness** | **Fragile.** Regex scraping over free-form Markdown; ambiguous prepend vs. append. | **High.** Standard `json.loads` on JSONL; strict schema, monotonic sequence integer, ISO UTC timestamps. | **High.** Standard JSON/JSONL parser. | **High.** Standard JSONL parser. | **Highest.** Relational schema, ACID constraints, typed columns. |
| **Git Merge Concurrency** | **Moderate.** Collisions occur only if concurrent agents touch the same plan file. | **Excellent.** Zero merge conflicts between agents working on different plans. Independent sidecars per artifact. | **Excellent.** Independent sidecars per artifact. | **Fatal.** Global conflict magnet. Git 3-way merge fails when concurrent agents append to EOF of the same file. | **Fatal.** Binary `.sqlite` files cannot be merged by Git. Immediate repo corruption. |
| **Human Diff Legibility** | **Good.** All changes visible in `git diff`, but cluttered by lengthy history entries. | **High.** `git diff` shows front-matter changes and the single-line transition summary clearly in the Markdown diff. | **Poor.** Status/scope hidden in separate JSON; reviewers must examine two disjoint diffs. | **Poor.** History diffs are separated into a giant central log file far from the plan body. | **Zero.** Binary diffs in Git. Unusable for PR reviews without export scripts. |
| **Crash & Write Safety** | **Good.** Handled via POSIX atomic file replace (`_core.atomic_write`). | **Excellent.** Per-artifact appends with file locking (`filelock`) and atomic replace on the inline summary. | **Excellent.** Atomic file write via `_atomic_write_json`. | **Poor.** `record_history.append` lacks file locking; concurrent multi-process writes interleave and corrupt JSON lines. | **Excellent.** ACID transactions and WAL mode. |
| **Migration Cost** | **Zero.** Current state. | **Moderate.** Refactors history access in 19 modules; maintains backward-compatible fallback reader. | **High.** Requires rewriting all front-matter readers and authoring workflows across the codebase. | **High.** Stalled on plans due to lint and concurrency concerns. | **Extremely High.** Completely rewrites storage architecture and Git workflow. |

---

## 4. Elimination of the Ordering Bug: Schema & Semantics

To eliminate the ordering bug structurally by construction, the durable record must carry monotonic causality and precise temporal coordinates.

### Per-Artifact Event Journal Schema

Each record in `.aw/records/history/<type>/<id6>.jsonl` is a self-contained JSON object:

```json
{
  "seq": 4,
  "id6": "rh5tt6",
  "ts": "2026-09-04T18:42:15.120Z",
  "from_status": "to-review",
  "to_status": "reviewed",
  "kind": "transition",
  "actor": "opencode/pt3-claude-opus-5-1m-us",
  "workflow": "aw plan-review",
  "message": "APPROVE WITH REVISIONS APPLIED; PR-024..PR-030 fixed",
  "evidence": {
    "git_commit": "3e05c2ba",
    "gate_cleared": "kw5y2s"
  }
}
```

### Key Ordering Guarantees

1. **Monotonic Sequence (`seq: int`)**:
   Starts at `1` for artifact creation and increments by `1` on every append. The sequence number provides an absolute, unambiguous causal ordering that does not depend on file line order, system clock skew, or date parsing.
2. **Strict ISO 8601 UTC Millisecond Timestamps (`ts: str`)**:
   Formatted as `YYYY-MM-DDTHH:MM:SS.mmmZ`. Standardizing universally on UTC with sub-second precision eliminates both the day-granularity collision problem and the local-vs-UTC evening skew defect.
3. **Explicit State Transitions (`from_status` and `to_status`)**:
   Distinguishes status transitions from non-status workflow notes (`kind: "note"`, where `from_status == to_status == null`).
4. **Legitimate Rollback / Demotion Edges**:
   In `agent_workflows/ipd_lifecycle.py:716`, `validate_transition` currently treats any backward move in rank as a `missing predecessor` violation. With explicit `from_status` and `to_status`, the transition engine recognizes legitimate backward transitions (such as `reviewed -> to-review` on replan, or `approved -> reviewed` on reopened gates) as valid rollback transitions when accompanied by appropriate actor authorization and note rationale.

---

## 5. Single Source of Truth, Drift Detection, and Repair

When metadata is shared between inline Markdown and sidecars, clear authority boundaries are required to maintain repository integrity.

### Authority Boundaries

- **Authoritative Operational Contract**: The Markdown front matter (`- Status:`, `- Readiness:`, `- Scope-Paths:`, etc.) is the source of truth for current artifact state and scope boundaries. Agents and tools read this directly.
- **Authoritative Audit Log**: The per-artifact JSONL file (`.aw/records/history/<type>/<id6>.jsonl`) is the immutable source of truth for the complete historical sequence of events.
- **Materialized Cache View**: The single inline history line under `## Workflow history` in Markdown is a deterministic projection of the latest event in the sidecar.

### Invariants & Drift Detection

The tool suite (`aw check`, `aw doctor`, `check_engine.py`) enforces two deterministic invariants:

1. **Status Alignment Invariant**:
   `markdown.meta["Status"] == sidecar.latest_transition.to_status`
   If an agent or human hand-edits `- Status: approved` without recording a transition in the sidecar, `check_status_untooled` flags `check.status-history-drift`.
2. **Materialized View Invariant**:
   `markdown.history_line == format_inline_history(sidecar.latest_event)`
   If the inline line does not match the byte projection of the latest sidecar event, `aw check` emits `check.history-view-drift`.

### Deterministic Repair Mechanism

Drift is repaired using `aw history sync <id6>` (or `aw doctor --fix`):
- If the sidecar has a new event that was not reflected in Markdown (e.g., interrupted write), the tool updates the Markdown file's `- Status:` and `## Workflow history` line from the sidecar.
- If Markdown was edited directly by a human with an intentional status change, `aw history sync` appends a new transition record to the sidecar with `actor: "human"`, sequence `N+1`, and timestamp `now()`.

---

## 6. Incremental, Safe Migration Path

The previous migration stalled because `ipd_lint` rule IPD-S405 (`ipd_lint.py:788`) required an inline `executed` history entry, and developers feared mass lint failures across 480+ plans in `executed/`.

### Migration Strategy

The migration must be phased, backward-compatible, and zero-downtime for active agents.

```
Phase 0: Grandfathering & Safe Rules
  └─► Phase 1: Dual-Mode Reader Layer (`record_history.py`)
        └─► Phase 2: Dual-Write Cutover in CLI Writers (`status_set.py`)
              └─► Phase 3: Update Verification Checks (IPD-S405 & Lifecycle)
                    └─► Phase 4: Progressive / On-Demand Corpus Migration
```

#### Phase 0: Grandfathering Historical Records
- Enforce that `executed/`, `superseded/`, and `not-executed/` directories are treated as frozen audit archives. Linter checks on transitional history sequence apply only to `pending/` plans.

#### Phase 1: Dual-Mode Reader Layer (`record_history.py`)
- Implement a unified reader API: `read_history(repo_root, id6, markdown_text=None) -> List[HistoryRecord]`.
- Logic: If `.aw/records/history/<type>/<id6>.jsonl` exists, parse and return its structured records. If absent, fall back to parsing inline `## Workflow history` lines from the Markdown text.
- This allows existing and migrated artifacts to coexist transparently across all 19 consuming modules.

#### Phase 2: Dual-Write Cutover in CLI Writers (`status_set.py`, `specs.py`, `backlog.py`)
- Update `status_set.py:880`:
  1. Append a structured record to `.aw/records/history/<type>/<id6>.jsonl` with `seq`, UTC timestamp, `from_status`, and `to_status`.
  2. Rewrite the inline `## Workflow history` block in the Markdown file to retain **only the latest one record**.
  3. Track `.aw/records/history/` in Git (remove any ignore rule).

#### Phase 3: Update Verification Checks
- Update `ipd_lint.py` IPD-S405: The check for an `executed` entry queries `read_history()`. Because the latest entry of an executed plan is always `executed`, the single inline line also satisfies legacy parsers.
- Update `ipd_lifecycle._plan_status_events`: Instead of reversing the Markdown text lines, read events chronologically from `read_history()`, ordered by `seq`. This immediately resolves the 15 false diagnostics in `check.lifecycle-transition-invalid`.
- Update `attention_contract.last_history_at`: Derive date from the latest structured record rather than scanning raw Markdown lines.

#### Phase 4: Progressive Corpus Migration
- Active plans are migrated on write as they transition through normal agent activity.
- A batch migration command (`aw history migrate [--pending | --all]`) reads legacy inline history, seeds the per-artifact JSONL file with sequential `seq` numbers, and slims the inline block to the latest entry.
- Because the dual-mode reader is already active, this migration can be performed set-by-set without stopping active workflows.

---

## 7. What NOT to Do (Explicitly Rejected Alternatives)

1. **Do NOT use a single central `history.jsonl` as the durable authority**:
   While convenient for global queries, a central file in a Git-tracked multi-agent repository is a fatal merge-conflict bottleneck. When multiple agents run concurrent tasks in isolated worktrees (`oc_runipd`), concurrent appends to the end of a single file trigger unresolvable Git merge conflicts. Furthermore, the repository's current `history.jsonl` is gitignored (`.aw/.gitignore:11`), violating the requirement that Git serve as the audit log.
2. **Do NOT use Git-tracked SQLite**:
   Checking a SQLite database into Git produces opaque binary diffs in PR reviews and cannot be merged by Git during concurrent branch merges. SQLite is acceptable only as an untracked, local query cache derived from Markdown/JSONL.
3. **Do NOT move front matter out of Markdown**:
   Front matter accounts for only 5.5% of corpus tokens. Stripping fields like `Id`, `Status`, `Scope-Paths`, and `Item-Dependencies` into a sidecar saves very few tokens while forcing every agent to perform extra tool calls to understand its task. It also makes status and scope changes invisible in pull request diffs.
4. **Do NOT completely eliminate inline history**:
   Completely deleting `## Workflow history` from Markdown destroys human review context in `git diff`. Keeping a single cached line of the latest transition provides optimal legibility with zero meaningful token penalty (~25 tokens).
5. **Do NOT attempt a one-time global re-ordering of all Markdown history files**:
   Normalizing 489 files by hand without changing the underlying write primitives does not fix the root cause. Writers would continue to disagree, timestamps would remain day-granular, and same-day ordering ambiguities would persist.

---

## 8. Summary of Affected Modules (The 19 Modules)

The 19 modules referencing `## Workflow history` and their target migration roles:

| Module | Current Functionality | Migration Action |
| :--- | :--- | :--- |
| `agent_workflows/attention.py:251` | Parses history boundary for attention reporting | Delegate to `record_history.read_history` |
| `agent_workflows/attention_contract.py:522` | Scans lines for `last_history_at` | Read date from latest `HistoryRecord` |
| `agent_workflows/backlog.py:611,631` | Splits/renders inline backlog history | Uses sidecar + latest inline line |
| `agent_workflows/check_engine.py:1009,1161` | Validates transitions & checks untooled edits | Read chronological stream by `seq` |
| `agent_workflows/cli.py:504,4542` | CLI verb definitions and help text | Update help text to reflect sidecars |
| `agent_workflows/doctor.py:812` | Advises running `aw set` instead of hand edits | Unchanged; continues advising tool usage |
| `agent_workflows/engine.py:4586` | Historical sanity check | Delegate to unified reader |
| `agent_workflows/hooks/status_untooled_gate.py:10` | Staged pre-commit hook checking history line | Verifies matching latest transition line |
| `agent_workflows/ipd_lifecycle.py:577,751` | Derives status from inline events | Reads `read_history` ordered by `seq` |
| `agent_workflows/ipd_lint.py:296,788` | IPD-S405 check for `executed` entry | Check latest record in `read_history` |
| `agent_workflows/ipd_schema.py:42` | Heading constant `H_WORKFLOW_HISTORY` | Retain constant for single-line section |
| `agent_workflows/plan_readiness.py:186` | `extract_newest_history_entry` | Read head record from `read_history` |
| `agent_workflows/record_history.py:278` | Sidecar writer and migration logic | Expand into primary per-artifact store |
| `agent_workflows/releases.py:72,259` | Reads release history | Delegate to `read_history` |
| `agent_workflows/review_findings.py:6` | References history for review finding context | Read structured review records from sidecar |
| `agent_workflows/selectors.py:316` | History boundary stripping | Use unified body parser |
| `agent_workflows/set_records.py:347` | Extracts prose body after history block | Unchanged or simplified |
| `agent_workflows/specs.py:196,343` | Slims inline history to latest-one | Unchanged (already implements hybrid) |
| `agent_workflows/status_set.py:872` | Prepends history line under heading | Append to per-artifact JSONL; replace inline line |
