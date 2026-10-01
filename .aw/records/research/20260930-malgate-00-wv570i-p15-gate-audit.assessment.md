---
id: wv570i
created: 20260930
set: malgate
order: 00
topic: []
model: 
kind: assessment
status: todo
outcome: none-yet
summary: P15 gate audit: every anti-malice mechanism with its keep, simplify, or delete decision and evidence
consumed-by: []
---

# P15 Gate Audit: Anti-Malice Mechanisms and Gates Inventory

- Date: 2026-09-30
- Plan: `bec7ee` (Order 01, Set `malgate`)
- Origin: Backlog `ariaau`
- Principle Under Review: GUIDING_PRINCIPLES P15 ("Guard against honest mistakes, never against a malicious agent", added 2026-09-26)

## Executive Summary

GUIDING_PRINCIPLES P15 was adopted to resolve a fundamental architectural tension: an agent operates as the same local operating system user with the same filesystem access as the maintainer. It can read, write, or modify tools, gates, test suites, instructions, and run records. Therefore, any mechanism that attempts to defend against a deliberately malicious or adversarial agent is futile by construction. Defenses built against a hypothetical hostile agent inevitably become brittle machinery (hidden secret tokens, path-based location guesses, forgery detection) that obstructs legitimate work and causes real recovery outages.

As required by backlog item `ariaau`, this research record provides a durable, comprehensive inventory of every anti-malice mechanism, gate, check, and justification across the repository. Each item is classified into one of four dispositions:
1. **KEEP**: The mechanism catches an honest mistake (sloppiness, concurrency race, data corruption, malformed input) with a clear message and remedy, or represents an honest-limit disclaimer.
2. **SIMPLIFY**: The mechanism or check is valuable, but its stated justification or phrasing appeals to anti-malice / adversarial models; it must be reframed as a clear refusal addressing an honest error.
3. **DELETE**: The mechanism exists solely to resist a deliberately hostile agent, or is an unimplemented stub guarding a caller that does not exist.
4. **ALREADY-DECIDED**: Settled by prior maintainer rulings or prior backlog designs (recorded here for complete provenance; not re-litigated).

---

## Deciding Test

To prevent arbitrary categorization, every item in this audit was evaluated against the following explicit test:

1. **The Honest Actor Test**: Could an honest user or agent acting in good faith accidentally trigger this check or condition through sloppiness, misunderstanding, or configuration error? Does the failure message name the underlying cause and provide actionable guidance or a deliberate override?
2. **The Same-User Vulnerability Test**: Does the mechanism assume the agent cannot edit the gate, the script, the test, or the environment? If the check can be trivially bypassed by an actor with the same user privileges (e.g. by editing the python code or environment variables), it cannot function as an anti-malice security boundary.
3. **The Active Caller Test**: Is the predicate or gate invoked by any active product or test workflow? A fail-loud stub protecting an imaginary caller creates cognitive drag and false assurance without catching any errors.

Applying these tests produces the following classification rules:
- **DELETE**: If the mechanism exists solely to stop a malicious agent, or if it guards a nonexistent caller.
- **SIMPLIFY**: If the mechanism catches real mistakes but is framed or documented as an anti-malice defense.
- **KEEP**: If the mechanism protects against honest errors, data corruption, or format violations, OR if the text is an honest-limit disclaimer stating that the repository does NOT defend against malice.
- **ALREADY-DECIDED**: If prior rulings have already settled the disposition.

---

## Re-Derived Enumeration Evidence (E-01)

The measurements below were conducted in this lane independently of prior plan text.

### 1. AST-Derived Caller Census for `agent_workflows/wtiso_gate.py`

Every `.py` file across the repository (466 Python files, excluding `agent_workflows/wtiso_gate.py` itself) was parsed into an Abstract Syntax Tree (AST) to detect any `Import`, `ImportFrom`, or attribute access on `wtiso_gate` or its nine exported functions.

- **AST Imports found**:
  - `agent_workflows/lane_containment.py:62: from agent_workflows.wtiso_gate import AW_MISSING_INPUT as _AW_MISSING_INPUT`
- **AST Calls found to any of the 9 predicates**:
  - `check_scope`: 0 calls
  - `check_lifecycle_role`: 0 calls
  - `format_missing_input`: 0 calls
  - `parse_missing_input`: 0 calls
  - `check_hook_bypass`: 0 calls
  - `check_protected_refs`: 0 calls
  - `check_permission_deadline`: 0 calls
  - `classify_retention`: 0 calls
  - `check_receipt`: 0 calls
- **Conclusion**: The entire 443-line module is consumed at exactly ONE location for ONE string constant (`AW_MISSING_INPUT`). All nine predicates have zero product callers and zero test callers.

### 2. Predicate Raise Check

Each of the nine predicates in `agent_workflows/wtiso_gate.py` was invoked directly using arguments matching their declared type annotations:

- `check_scope(['a.py'], ['a.py'])`: RETURNED `[]`
- `format_missing_input('foo/bar', 'need it')`: RETURNED `'AW_MISSING_INPUT:foo/bar:need it'`
- `parse_missing_input('AW_MISSING_INPUT:foo/bar:need it')`: RETURNED `('foo/bar', 'need it')`
- `check_permission_deadline([], 10.0)`: RETURNED `[]`
- `check_lifecycle_role('begin', 'worker')`: RAISED `NotImplementedError` ("wtiso_gate.check_lifecycle_role has no rule body; its owner is `rchpms` (Phase 2, RETIRED 2026-09-02, partly landed)...")
- `check_hook_bypass(Path('.'), 'HEAD', ['a.py'])`: RAISED `NotImplementedError` ("wtiso_gate.check_hook_bypass has no rule body; its owner is `rchpms` (Phase 2, RETIRED 2026-09-02; its observed-from-git half never landed and has NO successor plan)...")
- `check_protected_refs({'refs/heads/main': 'a'}, {'refs/heads/main': 'a'})`: RAISED `NotImplementedError` ("wtiso_gate.check_protected_refs has no rule body; its owner is `2c122z` (Phase 5, RETIRED UNLANDED 2026-09-02) and `1o4eif` (Phase 6)...")
- `classify_retention(Path('.'), 'a.py')`: RAISED `NotImplementedError` ("wtiso_gate.classify_retention has no rule body; its owner is `rchpms` (Phase 2, RETIRED 2026-09-02; its retention half never landed)...")
- `check_receipt({}, {})`: RAISED `NotImplementedError` ("wtiso_gate.check_receipt has no rule body; its owner is `rchpms` (Phase 2) and `58ha43` (Phase 4), BOTH RETIRED 2026-09-02...")

Summary: Exactly 5 predicates raise `NotImplementedError` referencing retired, unlanded phases. Exactly 4 predicates return values without raising, but none are called anywhere in the codebase.

### 3. Phrase Census Across `agent_workflows/`

A regex search was executed across `agent_workflows/*.py` for the vocabulary family (`malicious`, `determined same-user`, `hostile`, `adversarial`, `tamper`, `forge`, `deception`).
The hits split into two distinct classes:

- **Class (a): Honest-Limit Disclaimers & Integrity Protections (KEEP)**:
  - `runner_shared.py:22941-22948`: "1. A GATE CANNOT DETECT DECEPTION.", "3. A GENUINELY MALICIOUS AGENT WOULD REWRITE THE GATE.", "4. THE TARGET IS SLOPPINESS, NOT MALICE. An agent that broke something subtly and genuinely"
  - `host_sandbox_profile.py:31`: "from the correctness path; it is explicitly NOT a boundary against a MALICIOUS same-user worker"
  - `attention_contract.py:507`: "--by-human attestation (a conscious speed bump recording attributed human approval; NOT anti-malicious crypto)"
  - `work_cmd.py:15, 417, 433`: "HONEST label: the evidence is locally produced and forgeable by a privileged local agent... assurance: local-forgeable, not a CI-reproduced authority boundary"
  - `check_engine.py:535, 2927-2928`: "HONEST: the events are locally forgeable; this is a validity/consistency check, not a tamper-proof authority boundary."
  - `ipd_lifecycle.py:920-922, 1009-1010, 2243-2248, 2453`: "HONEST LIMIT: the local event stream is FORGEABLE by a privileged local agent... deterministic consistency check, NOT a tamper-proof authority boundary"
  - `run_ledger_store.py:1, 125, 173-174, 301`: "tamper-evident single-writer JSONL ledger store" (detects torn writes, damaged records, truncation; integrity checking against honest file corruption)
  - `run_analytics_*.py`: Hostile input data sanitation (e.g. `run_analytics_config.py:21: "hostile value"`, `run_analytics_schema.py:904: "hostile or malformed"`) protects the dashboard against malformed payloads.
  - `plan_readiness.py`, `artifact_adopt.py`, `ipd_lint.py`: Guarding against forged artifact front matter (e.g. unreviewed approval claims pasted by mistake).

- **Class (b): Justifications Proper & Misnomers (SIMPLIFY)**:
  - `ipd_lifecycle.py:4403`: "# checkout; hard enforcement against a determined same-user agent requires an OS sandbox or separate principal (`1o4eif`)" -> frames the sandbox as a defense against malicious agents.
  - `orchestrate_isolation.py:17`: "* E-04: Seeded orchestration adversarial protections against role collisions, leaked prose, unauthorized mutations, shared-worktree conflicts, stale branches" -> mislabels routine merge-safety and isolation checks as "adversarial protections".

### 4. Artifact and Citation Check

- `tests/test_containment_predicates.py`: **ABSENT** on disk. Deleted in commit `19313eed` (731 lines deleted). Cited 3 times in `wtiso_gate.py` docstrings.
- `tests/test_wtiso_adversarial.py`: **ABSENT** on disk. Deleted in commit `19313eed` (704 lines deleted). Cited 3 times in `wtiso_gate.py` docstrings.
- `tests/test_driver_attestation_gate.py`: **EXISTS** on disk. Validates driver attestation token mechanism (slated for deletion under `dvonrn`).

---

## Status of Authoring Facts 1 through 5

1. **Fact 1 (Pinning tests deleted)**: REPRODUCED. `tests/test_containment_predicates.py` and `tests/test_wtiso_adversarial.py` do not exist.
2. **Fact 2 (Zero product callers)**: REPRODUCED. AST scan across 466 files found zero callers for all nine predicates; the sole import is `AW_MISSING_INPUT` in `lane_containment.py`.
3. **Fact 3 (Five predicates raise, four return)**: REPRODUCED. Calling each with declared types confirms 5 raise `NotImplementedError` and 4 return.
4. **Fact 4 (Phrases split into disclaimers and justifications)**: REPRODUCED. The vast majority of vocabulary hits are compliant honest-limit disclaimers; only two sites are anti-malice justifications.
5. **Fact 5 (Driver token present and out of scope)**: REPRODUCED. Driver attestation token files and tests are present, governed by backlog `dvonrn`.

---

## Comprehensive Classification Table (E-02)

| # | Item / Symbol | Source Location | Measured Evidence | Disposition | Deciding Test / Rationale | Carrier or Keep-Reason |
|---|---|---|---|---|---|---|
| 1 | `wtiso_gate.check_lifecycle_role` | `agent_workflows/wtiso_gate.py:177` | Raises `NotImplementedError`; 0 product callers; real rule ships in `ipd_lifecycle.worker_role_active` with `AW-LIFECYCLE-ROLE-001` | **DELETE** | Stub guarding an nonexistent caller; actual lifecycle role guard already operates in `ipd_lifecycle` | Order 02 (`38pxaz`) |
| 2 | `wtiso_gate.check_hook_bypass` | `agent_workflows/wtiso_gate.py:245` | Raises `NotImplementedError`; 0 product callers; cited test deleted in `19313eed` | **DELETE** | A hook bypass check attempting to detect agent evasion is futile; stub is uncalled | Order 02 (`38pxaz`) |
| 3 | `wtiso_gate.classify_retention` | `agent_workflows/wtiso_gate.py:339` | Raises `NotImplementedError`; 0 product callers; retired owner `rchpms` | **DELETE** | Unimplemented stub for retired retention phase with zero callers | Order 02 (`38pxaz`) |
| 4 | `wtiso_gate.check_receipt` | `agent_workflows/wtiso_gate.py:381` | Raises `NotImplementedError`; 0 product callers; digest check already in `ipd_lifecycle` | **DELETE** | Pure predicate stub with no caller and no owner; real digest verification is elsewhere | Order 02 (`38pxaz`) |
| 5 | `wtiso_gate.check_protected_refs` | `agent_workflows/wtiso_gate.py:279` | Raises `NotImplementedError`; 0 product callers; cited test deleted in `19313eed` | **DELETE** | Attempt to detect protected ref tampering locally; stub is uncalled | Order 02 (`38pxaz`) |
| 6 | `wtiso_gate._unimplemented` | `agent_workflows/wtiso_gate.py:133` | Helper creating `NotImplementedError` for the five raising stubs | **DELETE** | Exists solely to serve the 5 deleted raising predicates | Order 02 (`38pxaz`) |
| 7 | `wtiso_gate.check_scope` | `agent_workflows/wtiso_gate.py:140` | Returns `[]`; 0 product callers; redundant with `ipd_lifecycle._scope_match` | **DELETE** | Zero product callers; `ipd_lifecycle` already implements scope checking with proper allowances | Order 02 (`38pxaz`) |
| 8 | `wtiso_gate.format_missing_input` | `agent_workflows/wtiso_gate.py:207` | Returns token string; 0 callers outside module; one-line delegation to `lane_containment` | **DELETE** | Trivial delegation with 0 callers; `lane_containment` is the real single definition | Order 02 (`38pxaz`) |
| 9 | `wtiso_gate.parse_missing_input` | `agent_workflows/wtiso_gate.py:226` | Returns parsed tuple; 0 callers outside module; one-line delegation to `lane_containment` | **DELETE** | Trivial delegation with 0 callers; `lane_containment` owns the parser | Order 02 (`38pxaz`) |
| 10 | `wtiso_gate.check_permission_deadline` | `agent_workflows/wtiso_gate.py:307` | Returns `[]`; 0 product callers; no wiring exists | **DELETE** | Zero product callers and no active consumer | Order 02 (`38pxaz`) |
| 11 | `wtiso_gate.AW_MISSING_INPUT` | `agent_workflows/wtiso_gate.py:81` | String constant; imported by `lane_containment.py:62` | **SIMPLIFY** | Re-home into `lane_containment.py` so `wtiso_gate.py` has no dependents | Order 02 (`38pxaz`) |
| 12 | `wtiso_gate` error codes (`AW_GATE_SCOPE`, etc.) | `agent_workflows/wtiso_gate.py:79-88` | Constants for unused predicates; 0 external references | **DELETE** | Dead constants associated with deleted predicates | Order 02 (`38pxaz`) |
| 13 | `wtiso_gate` dangling test citations | `agent_workflows/wtiso_gate.py` docstrings | 6 citations to `tests/test_containment_predicates.py` and `test_wtiso_adversarial.py` | **DELETE** | Strike citations to tests deleted in commit `19313eed` | Order 02 (`38pxaz`) |
| 14 | `ipd_lifecycle` sandbox justification | `agent_workflows/ipd_lifecycle.py:4403` | Comment citing "determined same-user agent requires an OS sandbox" | **SIMPLIFY** | Reframe sandbox as optional isolation for operators, not a fix for malicious agents | Order 03 (`dmjp0u`) |
| 15 | `orchestrate_isolation` docstring | `agent_workflows/orchestrate_isolation.py:17` | Docstring phrase "orchestration adversarial protections" | **SIMPLIFY** | Mislabels merge-safety and collision guards as adversarial; reword to isolation guards | Order 03 (`dmjp0u`) |
| 16 | Baseline banner disclaimers | `agent_workflows/runner_shared.py:22941-22948` | Comments: "TARGET IS SLOPPINESS, NOT MALICE", "GATE CANNOT DETECT DECEPTION" | **KEEP** | Compliant honest-limit disclaimer; documents what gates do NOT do | Retained (Honest-limit disclaimer) |
| 17 | Sandbox profile disclaimer | `agent_workflows/host_sandbox_profile.py:31` | Docstring: "explicitly NOT a boundary against a MALICIOUS same-user worker" | **KEEP** | Compliant honest-limit disclaimer; clarifies OS boundary vs agent boundaries | Retained (Honest-limit disclaimer) |
| 18 | `--by-human` attestation disclaimer | `agent_workflows/attention_contract.py:507` | Comment: "--by-human attestation... NOT anti-malicious crypto" | **KEEP** | Compliant honest-limit disclaimer; speed bump rather than cryptographic lock | Retained (Honest-limit disclaimer) |
| 19 | Local-forgeable evidence tags | `agent_workflows/work_cmd.py:15, 417, 433` | Tags and comments: "assurance: local-forgeable" | **KEEP** | Compliant honest-limit disclaimer; accurately states that local evidence lacks remote CI proof | Retained (Honest-limit disclaimer) |
| 20 | Event stream forgeability notices | `agent_workflows/check_engine.py:535, 2927-2928` | Comments: "events are locally forgeable; validity check, not tamper-proof boundary" | **KEEP** | Compliant honest-limit disclaimer | Retained (Honest-limit disclaimer) |
| 21 | Non-forgeable boundary doc | `agent_workflows/cli.py:1913` | Guidance: "forgeable by a privileged local agent; non-forgeable boundary is..." | **KEEP** | Compliant honest-limit disclaimer | Retained (Honest-limit disclaimer) |
| 22 | Git trailer consistency notices | `agent_workflows/git_commit_helper.py:24, 246` | Comments: "trailer is a consistency record, not tamper-proof provenance" | **KEEP** | Compliant honest-limit disclaimer | Retained (Honest-limit disclaimer) |
| 23 | Execution hook environment doc | `agent_workflows/hooks/executed_transition_gate.py:286` | Comment: "forged variable buys nothing an attacker did not already have" | **KEEP** | Compliant honest-limit rationale | Retained (Honest-limit disclaimer) |
| 24 | Lifecycle event forgeability notices | `agent_workflows/ipd_lifecycle.py:920-922, 1009-1010, 2243-2248, 2453` | Comments: "local event stream is FORGEABLE... NOT a tamper-proof authority boundary" | **KEEP** | Compliant honest-limit disclaimers across lifecycle state machine | Retained (Honest-limit disclaimer) |
| 25 | Tamper-evident hash chain | `agent_workflows/run_ledger_store.py:1, 125, 173-174, 301` | Append-only hash chain; raises `CorruptionError` on damaged blocks | **KEEP** | Protects against honest disk corruption, torn writes, and data truncation | Retained (Honest mistake / integrity) |
| 26 | Sensitive file permissions (`private_file`) | `agent_workflows/private_file.py:4` | Restricts POSIX permissions (`0o600`) on token and analytics salt | **KEEP** | Used by `run_analytics_privacy` for user privacy salt; token usage removed separately | Retained (User privacy protection) |
| 27 | Forged identity & readiness guards | `agent_workflows/plan_readiness.py`, `artifact_adopt.py`, `status_set.py`, `ipd_lint.py` | Validates that review records and identity headers exist on disk | **KEEP** | Catches honest copy-paste errors and accidental premature promotion | Retained (Honest mistake / schema validity) |
| 28 | Hostile payload validation | `agent_workflows/run_analytics_*.py` | Validates untrusted input data, JSON syntax errors, hostile paths | **KEEP** | Robust input sanitation preventing crashes from malformed data | Retained (Input robustness) |
| 29 | Benchmark seeded cases | `agent_workflows/benchmark_scorer.py`, `benchmark_metrics.py` | 14 seeded false-completion failure classes for evaluating evaluators | **KEEP** | Evaluation benchmark dataset; necessary to score agent performance | Retained (Test / benchmark ground truth) |
| 30 | Per-run driver attestation token | `agent_workflows/ipd_lifecycle.py:mint_driver_attestation`, `driver-attest.token` | Secret file written to restrict driver verbs; bypassed by same-user agents | **ALREADY-DECIDED** (DELETE) | Settled in backlog `dvonrn` D1: brittle secret token that impeded legitimate work | Carrier: `dvonrn` D1 |
| 31 | `--by-human` attestation flag | `agent_workflows/status_set.py`, spec `honest-human-approval-attestation` | Requires explicit flag to attest human approval; recorded in workflow history | **ALREADY-DECIDED** (KEEP) | Settled in backlog `ariaau` and spec: deliberate conscious speed bump, not a lock | Retained (Honest speed bump) |
| 32 | Suite-baseline adjudication | `agent_workflows/runner_shared.py:22936` | Compares failure count against baseline rather than failing on pre-existing issues | **ALREADY-DECIDED** (KEEP) | Settled in `daexj1` OQ-02 and `ariaau`: model honest-limits design | Retained (Model honest-limits gate) |
| 33 | Opt-in hardened OS sandbox | `agent_workflows/host_sandbox_profile.py`, plan `1o4eif` | OS bubblewrap/container isolation profile | **ALREADY-DECIDED** (KEEP) | Settled in backlog `dvonrn` D7: valid optional OS-level boundary | Retained (Optional OS boundary) |

Total enumerated items: 33.
Classification breakdown:
- **DELETE**: 11 items (all 11 in `wtiso_gate.py`, carried by Order 02 `38pxaz`).
- **SIMPLIFY**: 3 items (constant re-homing carried by `38pxaz`; two comment sites carried by Order 03 `dmjp0u`).
- **KEEP**: 15 items (honest-limit disclaimers, data integrity guards, user privacy salts, input validators, benchmark suites).
- **ALREADY-DECIDED**: 4 items (1 DELETE carried by `dvonrn`, 3 KEEP).

Every DELETE and SIMPLIFY item has an assigned carrier (`38pxaz`, `dmjp0u`, or `dvonrn`). Every KEEP item specifies the honest mistake, privacy rationale, or honest-limit disclaimer it represents.

---

## The Four Already-Decided Items (Detail)

Backlog `ariaau` explicitly named four items as already decided and instructed the audit not to reopen them. They are detailed here for complete repository provenance:

1. **The Per-Run Driver Attestation Token (`ipd_lifecycle`, plan `u27oh3`)**:
   - **Prior Decision**: **DELETE** (ruled in backlog `dvonrn` D1).
   - **Carrier**: Backlog `dvonrn` (lifegate).
   - **Rationale**: The token was written to `.aw/worktrees/.../driver-attest.token` with restrictive permissions to prevent worker agents from calling driver-only lifecycle verbs. In practice, because worker agents run as the same OS user, they could easily read or copy the token. Simultaneously, the token mechanism failed when a human ran commands from another worktree, blocking legitimate work. It was a textbook violation of P15: an ineffective anti-malice defense that inflicted real friction on honest actors.
2. **The `--by-human` Attestation Requirement**:
   - **Prior Decision**: **KEEP** (spec `honest-human-approval-attestation`).
   - **Rationale**: Spec `honest-human-approval-attestation` explicitly frames `--by-human` not as an unbreakable cryptographic lock, but as an attributed speed bump. An agent cannot accidentally approve a spec without actively passing an explicit flag that attributes the approval. It records who asserted human review without pretending to make forgery impossible.
3. **Suite-Baseline Adjudication**:
   - **Prior Decision**: **KEEP** (maintainer ruling 2026-09-08, `daexj1` OQ-02, reaffirmed 2026-09-20).
   - **Rationale**: The runner adjudicates test failures by comparing post-run failures to a pre-captured baseline. It does not attempt to detect whether an agent deliberately faked test outputs. The banner explicitly states: "A GATE CANNOT DETECT DECEPTION... THE TARGET IS SLOPPINESS, NOT MALICE". It represents the repository's gold-standard model for honest-mistake tooling.
4. **Opt-in Hardened OS Sandbox (`host_sandbox_profile.py`, plan `1o4eif`)**:
   - **Prior Decision**: **KEEP** (lifegate D7).
   - **Rationale**: When true isolation is required, P15 states that it must be provided by the operating system, never by application-level Python checks. The sandbox profile provides opt-in OS containment (e.g. bubblewrap / namespace boundaries). Its documentation clearly states that it is an optional operator boundary, not an internal guard against a co-located agent.

---

## Limits of this Audit (E-04)

An audit that claims completeness without acknowledging its methodological boundaries is misleading. The limits of this assessment are explicitly documented as follows:

1. **Methodological Limits of the Vocabulary Census**:
   The starting list from backlog `ariaau` was explicitly not exhaustive. While the AST walk over `wtiso_gate.py` was exhaustive for that module, the phrase census across `agent_workflows/` relies on lexical pattern matching (`malicious`, `determined same-user`, `hostile`, `adversarial`, `tamper`, `forge`, `deception`). This method **cannot detect** anti-malice mechanisms whose comments and docstrings avoid that specific vocabulary (for instance, an ad-hoc secret check documented with neutral terminology like "validate token" or "security check").
2. **Reference Sweep Obligations for Deletions**:
   Deleting code, error codes, or predicates changes public module surfaces that other plans, specs, or historical reviews might reference. The fact that an item is marked DELETE in this audit does not relieve the carrier (`38pxaz`) of its obligation to perform an exhaustive reference sweep across the repository (e.g. updating spec `7ckptx` and ensuring no dangling imports remain).
3. **Judgemental Nature of Classification**:
   Distinguishing between an honest-limit disclaimer (KEEP) and an anti-malice justification (SIMPLIFY) is an interpretive judgement based on the Deciding Test above. Reviewers may hold differing perspectives on whether a particular comment crosses the boundary into anti-malice justification. Stating the deciding criteria explicitly ensures that any future dispute can focus productively on the test criteria rather than subjective impressions of individual phrases.

---

## Conclusion & Next Actions

This audit confirms that the anti-malice mechanisms in `agent_workflows` are localized and cleanly separable:
1. `agent_workflows/wtiso_gate.py` is an uncalled, unpinned skeleton whose predicates should be removed and whose sole exported constant (`AW_MISSING_INPUT`) should be re-homed to `agent_workflows/lane_containment.py` (Order 02: `38pxaz`).
2. Two docstring/comment sites require reframing to describe honest mistake isolation rather than adversarial defense (Order 03: `dmjp0u`).
3. The remaining anti-malice vocabulary represents P15-compliant honest-limit disclaimers that must be carefully preserved to document the true boundaries of the system.
