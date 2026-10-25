- Id: tg80ht
- Status: open
- Blocks-Release: next
- Set: specplan
- Priority: high
- Work-Kind: feature
- Summary: Spec-to-plan bridge: automate graduation, IPD set authoring, and runner dispatch for approved specs

## Workflow history
- 2026-10-25 created (aw backlog): Spec-to-plan bridge: automate graduation, IPD set authoring, and runner dispatch for approved specs


### Problem Statement

`agent-workflows` provides deep automation at the front end (research prompts, spec authoring, multi-agent adversarial refinement, and `/spec-review`) and at the back end (isolated worktree execution, dependency graph sorting, integration locks, `aw commit`, and execution verification).

However, an approved specification (such as `4sd62s` blocking release 2.0.0) hits an unpaved chasm:
1. **No Spec Graduation Command**: Unlike backlog items which have `aw backlog graduate`, specs have no `aw specs graduate` verb. While specs have a `- Graduated-To:` metadata field, it is merely a passive pointer that must be hand-edited after plans are manually created.
2. **Runner Blind Spot (`[RUN-UNDETERMINED-ACTION]`)**: If an operator runs `aw oc run <spec-id>` or `aw agy run <spec-id>`, the runner dispatch engine (`agent_workflows/runner_action.py`) raises `[RUN-UNDETERMINED-ACTION]` because no runner action is defined for specs.
3. **Missing Automated Plan Decomposition**: Decomposing a complex spec into a valid Implementation Plan Document (IPD) Set (orchestrator `00` plus child plans `01+`) with bijective `E-*`/`V-*` checklists, inherited release gates (`- Blocks-Release:`), and backward links (`- From-Spec:`) is completely manual.

The result is that approved specifications remain stranded as static documentation, creating a disconnect between design approval and autonomous execution.

### Proposed Solution and Scope

1. **Spec Graduation CLI Verb (`aw specs graduate`):**
   - Add `aw specs graduate <spec-id> [--set <setid>] [--apply]` to `agent_workflows/specs_cli.py`.
   - Verifies the spec is at status `approved`.
   - Sets `- Graduated-To: <setid>` on the spec and transitions its status to `implementing` (moving the file to `.aw/records/specs/implementing/`).
   - Scaffolds the initial IPD Set structure in `.aw/records/plans/pending/` with `- From-Spec: <spec-id>` and inherited `- Blocks-Release:` gates.

2. **Spec-to-Plan Decomposition Workflow (`/aw spec-plan` or `aw specs plan`):**
   - Create an automated authoring workflow (`.aw/system/workflows/spec-plan/spec-plan.md` and CLI subcommand `aw specs plan <spec-id>`).
   - Ingests an approved spec, parses its suggested plan decomposition, requirements (`FR-*`), and acceptance criteria (`AC-*`).
   - Dispatches a planning agent turn (via OpenCode or Antigravity) to author review-ready child IPDs with concrete `E-*` execution steps and `V-*` validation criteria.
   - Ensures all generated plans satisfy `aw ipd lint`.

3. **Runner Action for Approved Specs (`agent_workflows/runner_action.py`):**
   - Define a valid runner action for specs at status `approved`: map action to spec decomposition / plan set authoring.
   - Allows `aw oc run <spec-id>` or `aw agy run <spec-id>` to launch the planning session and produce the initial IPD Set rather than failing with `[RUN-UNDETERMINED-ACTION]`.

4. **Lifecycle and Attention View Integration:**
   - Ensure `aw attention` surfaces `implementing` specs with their active plan sets.
   - When all child plans in the graduated Set reach `executed`, guide the operator or runner to finalize the spec via `aw spec set implemented <spec-id> --evidence <final-plan>`.

### Acceptance Criteria

- AC-1: `aw specs graduate <spec-id>` validates approved status, writes `- Graduated-To: <setid>`, and transitions spec to `implementing`.
- AC-2: `runner_action.py` maps approved specs to a recognized planning action instead of raising `[RUN-UNDETERMINED-ACTION]`.
- AC-3: Spec-to-plan workflow scaffolds an orchestrator plan and child IPDs carrying `- From-Spec: <spec-id>` and inheriting `- Blocks-Release: <gate>`.
- AC-4: Generated IPD files pass `aw ipd lint` with zero structural findings.
- AC-5: Comprehensive tests in `tests/test_specs_graduate.py` and `tests/test_runner_action_specs.py`.
