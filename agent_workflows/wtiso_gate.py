"""The ONE pure gate/predicate library + stable error codes for the wtiso migration (Phase 0,
`8zgybk` E-09; research x03wgn Section 8 Phase 0 item 5 and Section 5 Layer 5).

WHY THIS MODULE EXISTS AS A SKELETON. x03wgn Section 7 records the hazard "Hook rule differs from
driver: agent repairs one gate but fails another" and prescribes ONE pure policy library with stable
error codes, called by the pre-commit hook, the read-only `aw lane status`, the driver, finalize, and
integration. If each of those grew its own copy of a rule, the rules would drift and an agent could
satisfy one gate while violating another. Seeding the import surface in Phase 0 means every later
phase has exactly one place to add a rule, so drift is structurally impossible rather than merely
discouraged.

PHASE 0 SHIPS NO RULE LOGIC. Every predicate below raises `NotImplementedError` naming the wtiso
child that owns its body. That is deliberate: Phase 0 changes no production behavior. A caller
wiring itself to a predicate before its owning phase lands gets a loud failure, never a silent
permissive default. `tests/test_wtiso_taxonomy_freeze.py::test_gate_library_is_single_import_surface`
asserts only that this module imports and exposes the stable error codes.

STABLE ERROR CODES are the contract. They are the strings a hook prints, `aw lane status` reports,
and the driver matches on. They must not be renamed once a phase depends on one; add a new code
instead. Each is `AW_`-prefixed and uppercase so it is greppable in logs and diffs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only, no runtime import cost
    from pathlib import Path
    from typing import Any, Mapping, Sequence

# ---- stable error codes ---------------------------------------------------------------------------
# Format contract: an emitted violation is rendered as `<CODE>:<subject>:<why>`, matching the
# `AW_MISSING_INPUT:<path>:<why>` shape research x03wgn Section 4 specifies. Callers parse the code
# by exact string match; never by prefix or substring of a longer code.

#: A write touched a path outside the lane's declared scope (Scope-Paths / lease).
AW_GATE_SCOPE = "AW_GATE_SCOPE"

#: A worker attempted a driver-only lifecycle verb (begin/finalize/receipt/ledger write).
AW_LIFECYCLE_ROLE = "AW_LIFECYCLE_ROLE"

#: A required local input is absent from the lane. Emitted as `AW_MISSING_INPUT:<path>:<why>`;
#: the driver classifies it, materializes a safe copy if policy allows, and resumes. The original
#: checkout path is never granted (x03wgn Section 4, "Missing-input recovery").
AW_MISSING_INPUT = "AW_MISSING_INPUT"

#: A commit reached the tree without the hook's checks (for example `git commit --no-verify`).
#: Hooks are feedback only; the driver re-checks the same predicate over observable state.
AW_GATE_HOOK_BYPASS = "AW_GATE_HOOK_BYPASS"

#: A protected ref, git configuration, hook path, or another worktree's administration was mutated.
AW_GATE_PROTECTED_REF = "AW_GATE_PROTECTED_REF"

#: A permission ask (root or nested child session) went unanswered past its deadline.
AW_PERMISSION_DEADLINE = "AW_PERMISSION_DEADLINE"

#: A changed or created artifact could not be placed in exactly one retention class. `unknown`
#: retention blocks teardown (x03wgn Section 2 retention table).
AW_RETENTION_UNKNOWN = "AW_RETENTION_UNKNOWN"

#: A begin receipt is absent, forked, stale, or bound to a different attempt than the one running.
AW_RECEIPT_INVALID = "AW_RECEIPT_INVALID"

#: The tuple of every stable code this library defines, for exhaustive tests and docs.
ERROR_CODES: tuple[str, ...] = (
    AW_GATE_SCOPE,
    AW_LIFECYCLE_ROLE,
    AW_MISSING_INPUT,
    AW_GATE_HOOK_BYPASS,
    AW_GATE_PROTECTED_REF,
    AW_PERMISSION_DEADLINE,
    AW_RETENTION_UNKNOWN,
    AW_RECEIPT_INVALID,
)


# ---- predicate surface (bodies owned by later phases) ---------------------------------------------


def _unimplemented(predicate: str, owner: str) -> "NotImplementedError":
    """Build the uniform NotImplementedError a Phase-0 stub raises.

    Failing loudly (rather than returning a permissive default) is the point: a caller wired up
    before its owning phase lands must break visibly, never silently allow.
    """

    return NotImplementedError(
        "wtiso_gate.{0} is a Phase-0 skeleton; its rule body is owned by wtiso child {1}. "
        "Do not add rule logic outside that phase.".format(predicate, owner)
    )


def check_scope(
    changed_paths: "Sequence[str]", scope_paths: "Sequence[str]"
) -> "list[str]":
    """Return `AW_GATE_SCOPE` violations for changed paths outside `scope_paths`.

    Owner: `qcqhj7` (Phase 1) for the pure predicate; `rchpms` (Phase 2) wires the hook,
    `aw lane status`, the driver, and finalize to THIS function so the rules cannot diverge.
    """

    raise _unimplemented("check_scope", "qcqhj7")


def check_lifecycle_role(verb: str, role: str) -> "list[str]":
    """Return `AW_LIFECYCLE_ROLE` violations when a `worker` role invokes a driver-only verb.

    Owner: `rchpms` (Phase 2), which moves lifecycle authority into the driver and makes the
    worker-role lifecycle verbs refuse.
    """

    raise _unimplemented("check_lifecycle_role", "rchpms")


def format_missing_input(path: str, why: str) -> str:
    """Render the `AW_MISSING_INPUT:<path>:<why>` token from x03wgn Section 4.

    Owner: `qcqhj7` (Phase 1), which defines the response contract, the driver-side classifier,
    the safe materialization policy, and the resume path.
    """

    raise _unimplemented("format_missing_input", "qcqhj7")


def parse_missing_input(token: str) -> "tuple[str, str] | None":
    """Parse an `AW_MISSING_INPUT:<path>:<why>` token back into `(path, why)`, else `None`.

    Owner: `qcqhj7` (Phase 1). Paired with `format_missing_input` so emit and parse cannot drift.
    """

    raise _unimplemented("parse_missing_input", "qcqhj7")


def check_hook_bypass(
    repo: "Path", commit: str, scope_paths: "Sequence[str]"
) -> "list[str]":
    """Return `AW_GATE_HOOK_BYPASS` violations found by re-checking a commit the hook may have skipped.

    Hooks are corrective feedback, not authority (x03wgn Section 5 Layer 5): `--no-verify`,
    plumbing, and "no commit at all" all evade them, so the driver re-runs the SAME predicate over
    the observable end state. Owner: `rchpms` (Phase 2).
    """

    raise _unimplemented("check_hook_bypass", "rchpms")


def check_protected_refs(
    before: "Mapping[str, str]", after: "Mapping[str, str]"
) -> "list[str]":
    """Return `AW_GATE_PROTECTED_REF` violations by diffing before/after protected-ref snapshots.

    Owner: `2c122z` (Phase 5) for the integration block; `1o4eif` (Phase 6) adds the hardened
    OS-denied half.
    """

    raise _unimplemented("check_protected_refs", "2c122z")


def check_permission_deadline(
    events: "Sequence[Mapping[str, Any]]", deadline_seconds: float
) -> "list[str]":
    """Return `AW_PERMISSION_DEADLINE` violations for asks unanswered past `deadline_seconds`.

    Must consider NESTED child sessions, not only the root session: an invisible child-agent ask is
    the exact shape of the live qyaime deadlock (x03wgn Section 6 Layer 6). Owner: `qcqhj7` (Phase 1).
    """

    raise _unimplemented("check_permission_deadline", "qcqhj7")


def classify_retention(repo: "Path", path: str) -> str:
    """Return the retention class for `path`, one of the x03wgn Section 2 retention values.

    An unclassifiable artifact is `unknown`, which BLOCKS teardown; ignored status alone never
    authorizes deletion. Owner: `rchpms` (Phase 2).
    """

    raise _unimplemented("classify_retention", "rchpms")


def check_receipt(
    receipt: "Mapping[str, Any]", expected: "Mapping[str, Any]"
) -> "list[str]":
    """Return `AW_RECEIPT_INVALID` violations when a receipt does not authorize the exact attempt.

    Owner: `rchpms` (Phase 2), which makes the driver the sole receipt creator; `58ha43` (Phase 4)
    relocates the canonical receipt store and removes the in-lane copy.
    """

    raise _unimplemented("check_receipt", "rchpms")
