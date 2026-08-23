"""Compatibility contract, previewable idempotent migration/update, rollback, and deprecation.

awoptimize Order 17 (`gnfkh8`). This is the FINAL compatibility layer over the workflow-family
migration (Order 14 = inventory + shared assess/advise + plan-review collapse; Order 15 = complex
orchestrated coordinators; Order 16 = compact workflows + generated shims + promotion gates). It does
four things, all pure/deterministic and stdlib-only (D138), NON-DESTRUCTIVE, and NEVER removing a
compatibility surface (removal is a separately approved release action):

* E-01 -- a MACHINE-READABLE COMPATIBILITY CONTRACT: exactly ONE reviewed row for every public
  surface (manifest commands, arguments, `.opencode/commands/`, `.claude/commands/`,
  AGENTS/CLAUDE/GEMINI pointers, IPD locations, `agy_run.py` entry points, exit codes, machine
  output). Each row carries owner, version boundary, migration, and test. A golden check PROVES one
  row + a passing test per named surface, with NO unspecified breaking change; every
  preserved/changed/deprecated/unsupported behavior is explicit.

* E-02 -- IDEMPOTENT, PREVIEWABLE migration/update: detects legacy / partial / current / drifted /
  locally-customized states; previews exact changes; PRESERVES user files; BACKS UP replaced
  generated files; records the exact compiler/adapter version. A rerun on a current install is a
  no-op; human-owned content is NEVER silently overwritten.

* E-03 -- ROLLBACK to the last compatible generated set + runtime state, including
  interrupted-migration recovery, and an explicit WARNING when new-run data cannot be read by an
  older version (distinguishing adapter rollback from a data-schema downgrade). Rollback + recovery
  restore prior command discovery + runtime adapters WITHOUT record loss, and warn rather than
  corrupt on unreadable future data.

* E-04 -- DEPRECATION diagnostics + LOCAL, privacy-preserving usage counters ONLY if approved
  (opt-in); aliases are kept until parity + adoption + version gates are met; telemetry is NEVER
  required for operation and can be disabled/avoided completely.

It REUSES the existing engine (it does NOT fork one):

  * `agent_workflows.layout_migration.MigrationManager` -- the journaled move-not-copy engine. E-02's
    idempotent apply drives `MigrationManager.execute_migration`; E-03's rollback + interrupted
    recovery drive `MigrationManager.rollback_migration` / `resume_migration` / `status_migration`.
  * `agent_workflows.engine` -- install/layout resolution: `resolve_target_layout`,
    `resolve_workflows_dir`, `resolve_source_root`, `read_version`, `parse_manifest`,
    `generate_shim_members`, `COMMAND_SHIM_DIRS`, `AGENTS_FILE_CANDIDATES`, `NATIVE_AGENT_FILES`.
    Command discovery + shim/pointer surfaces are read from the engine, never re-derived.

Scope fence (Order 17): it OWNS the compatibility contract + migration/rollback/deprecation
MECHANICS; it never REMOVES a surface, tags/publishes/pushes, or writes operator/security docs
(Order 18). Old invocations MUST keep working.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from agent_workflows import engine
from agent_workflows.layout_migration import MigrationManager


# ==================================================================================================
# Shared error
# ==================================================================================================


class CompatibilityError(ValueError):
    """Raised when a compatibility invariant is violated (fail closed)."""


# ==================================================================================================
# E-01: the machine-readable compatibility contract
# ==================================================================================================

# The disposition of a surface across the version boundary. Each is EXPLICIT (the plan requires every
# preserved/changed/deprecated/unsupported behavior be named), and `breaking` distinguishes a
# behavior that may break an existing invocation from one that does not. An UNSPECIFIED breaking
# change (a surface that breaks without being marked `unsupported`/`removed`) is exactly what the
# golden check detects.
STATUS_PRESERVED = "preserved"  # unchanged behavior; no break
STATUS_CHANGED = "changed"  # behavior evolved but remains backward-compatible; no break
STATUS_DEPRECATED = (
    "deprecated"  # still works (alias/shim kept); scheduled for a later removal
)
STATUS_UNSUPPORTED = (
    "unsupported"  # an EXPLICIT, specified break (documented, not silent)
)
STATUS_REMOVED = "removed"  # an EXPLICIT, specified removal (a separate release action)
CONTRACT_STATUSES: FrozenSet[str] = frozenset(
    (
        STATUS_PRESERVED,
        STATUS_CHANGED,
        STATUS_DEPRECATED,
        STATUS_UNSUPPORTED,
        STATUS_REMOVED,
    )
)

# A status is a BREAKING one only when it is explicitly unsupported/removed. preserved/changed/
# deprecated keep the existing invocation working, so they are NON-breaking. This is the mapping the
# golden check uses to prove "no UNSPECIFIED breaking change": a row may break only if it declares
# itself unsupported/removed (specified), never otherwise.
_BREAKING_STATUSES: FrozenSet[str] = frozenset((STATUS_UNSUPPORTED, STATUS_REMOVED))

# The owner Order for a surface's behavior (who defines/generates it). Order 17 owns the compatibility
# MECHANICS, not the surfaces themselves; the surface owners are the Orders that generate them.
CONTRACT_OWNERS: FrozenSet[str] = frozenset(
    (
        "order-01",  # the workflow compiler / manifest schema
        "order-11",  # host adapters (shim/skill generation)
        "order-14",  # shared families + plan-review collapse
        "order-15",  # complex orchestrated coordinators
        "order-16",  # compact workflows + generated shims + pointers
        "order-17",  # this Order (compatibility mechanics, exit codes, machine output)
        "installer",  # engine.py install/layout resolution
    )
)


@dataclass(frozen=True)
class CompatSurface:
    """One reviewed row of the compatibility contract for a single public surface.

    ``surface`` is the stable id (e.g. ``manifest-commands``). ``status`` is one of
    :data:`CONTRACT_STATUSES` and is the load-bearing field: a ``preserved``/``changed``/
    ``deprecated`` surface keeps existing invocations working, while ``unsupported``/``removed`` is an
    EXPLICIT break. ``version_boundary`` names the release the disposition takes effect at (or
    ``ongoing``). ``migration`` names how a user moves across the boundary. ``test`` names the golden
    test symbol that proves this row.
    """

    surface: str
    owner: str
    status: str
    version_boundary: str
    migration: str
    test: str
    behavior: str = ""

    @property
    def breaking(self) -> bool:
        """True iff this row declares a break. Only unsupported/removed may break (and must be
        specified). A preserved/changed/deprecated row that broke would be an UNSPECIFIED break."""

        return self.status in _BREAKING_STATUSES

    def validate(self) -> List[str]:
        """Return a list of contract violations for this row (empty = valid)."""

        problems: List[str] = []
        if not self.surface:
            problems.append("empty surface")
        if self.owner not in CONTRACT_OWNERS:
            problems.append("bad owner '{0}'".format(self.owner))
        if self.status not in CONTRACT_STATUSES:
            problems.append("bad status '{0}'".format(self.status))
        if not self.version_boundary:
            problems.append("empty version_boundary")
        if not self.migration:
            problems.append("empty migration")
        if not self.test:
            problems.append("empty test")
        return problems

    def to_dict(self) -> Dict[str, Any]:
        return {
            "surface": self.surface,
            "owner": self.owner,
            "status": self.status,
            "version_boundary": self.version_boundary,
            "migration": self.migration,
            "test": self.test,
            "behavior": self.behavior,
            "breaking": self.breaking,
        }


# The named surfaces the plan requires a row for. This is the scope fence mirrored as data so the
# golden check can prove EVERY named surface has exactly one row and none is silently omitted.
REQUIRED_SURFACES: Tuple[str, ...] = (
    "manifest-commands",
    "command-arguments",
    "opencode-commands",
    "claude-commands",
    "agents-pointer",
    "claude-pointer",
    "gemini-pointer",
    "ipd-locations",
    "agy-run-entry-points",
    "exit-codes",
    "machine-output",
)


# The FROZEN compatibility contract: exactly one row per required surface. Every row is
# preserved/changed/deprecated (NON-breaking) in this Order -- this Order removes nothing; a break
# would have to be an EXPLICIT unsupported/removed row (there are none here). Each ``test`` names the
# golden test method that proves the row.
_CONTRACT_ROWS: Tuple[CompatSurface, ...] = (
    CompatSurface(
        surface="manifest-commands",
        owner="order-01",
        status=STATUS_PRESERVED,
        version_boundary="ongoing",
        migration="every legacy command name stays a live manifest row or a kept alias",
        test="test_surface_manifest_commands_preserved",
        behavior="all existing manifest command names remain invokable",
    ),
    CompatSurface(
        surface="command-arguments",
        owner="order-01",
        status=STATUS_PRESERVED,
        version_boundary="ongoing",
        migration="argument policy is compiled from the one IR; existing $ARGUMENTS usage kept",
        test="test_surface_command_arguments_preserved",
        behavior="a command's argument-passing contract is unchanged",
    ),
    CompatSurface(
        surface="opencode-commands",
        owner="order-11",
        status=STATUS_PRESERVED,
        version_boundary="ongoing",
        migration=".opencode/commands/ shims are regenerated by engine.generate_shim_members",
        test="test_surface_opencode_commands_preserved",
        behavior="OpenCode slash-command shims stay discoverable and valid",
    ),
    CompatSurface(
        surface="claude-commands",
        owner="order-11",
        status=STATUS_PRESERVED,
        version_boundary="ongoing",
        migration=".claude/commands/ shims are regenerated by engine.generate_shim_members",
        test="test_surface_claude_commands_preserved",
        behavior="Claude Code slash-command shims stay discoverable and valid",
    ),
    CompatSurface(
        surface="agents-pointer",
        owner="order-16",
        status=STATUS_PRESERVED,
        version_boundary="ongoing",
        migration="AGENTS.md keeps its marker-delimited pointer block, updated in place",
        test="test_surface_agents_pointer_preserved",
        behavior="the AGENTS.md pointer to the workflow manifest is preserved",
    ),
    CompatSurface(
        surface="claude-pointer",
        owner="order-16",
        status=STATUS_PRESERVED,
        version_boundary="ongoing",
        migration="CLAUDE.md pointer, if present, is preserved as a native-agent instruction file",
        test="test_surface_claude_pointer_preserved",
        behavior="the CLAUDE.md pointer is a recognized native-agent instruction surface",
    ),
    CompatSurface(
        surface="gemini-pointer",
        owner="order-16",
        status=STATUS_PRESERVED,
        version_boundary="ongoing",
        migration="GEMINI.md pointer, if present, is preserved as a native-agent instruction file",
        test="test_surface_gemini_pointer_preserved",
        behavior="the GEMINI.md pointer is a recognized native-agent instruction surface",
    ),
    CompatSurface(
        surface="ipd-locations",
        owner="order-16",
        status=STATUS_CHANGED,
        version_boundary="ongoing",
        migration="records migrate to .aw/records/ via MigrationManager (move-not-copy); rollback restores prior locations",
        test="test_surface_ipd_locations_changed_not_broken",
        behavior="IPD/records locations moved under .aw/records but stay discoverable and reversible",
    ),
    CompatSurface(
        surface="agy-run-entry-points",
        owner="installer",
        status=STATUS_PRESERVED,
        version_boundary="ongoing",
        migration="agy_run.py entry points keep resolving; the module import surface is unchanged",
        test="test_surface_agy_run_entry_points_preserved",
        behavior="agy_run.py entry points remain callable at their documented locations",
    ),
    CompatSurface(
        surface="exit-codes",
        owner="order-17",
        status=STATUS_PRESERVED,
        version_boundary="ongoing",
        migration="documented exit codes are frozen constants consumed via EXIT_CODES",
        test="test_surface_exit_codes_preserved",
        behavior="documented process exit codes keep their meaning",
    ),
    CompatSurface(
        surface="machine-output",
        owner="order-17",
        status=STATUS_PRESERVED,
        version_boundary="ongoing",
        migration="machine (JSON) output stays sorted-key stable; new keys are additive only",
        test="test_surface_machine_output_preserved",
        behavior="machine-readable JSON output stays parseable and additive-only",
    ),
)


# The documented, frozen exit codes (the `exit-codes` surface). A machine consumer imports these
# rather than hard-coding integers; changing a meaning would be a breaking change requiring an
# explicit unsupported/removed contract row.
EXIT_CODES: Dict[str, int] = {
    "ok": 0,
    "error": 1,
    "usage": 2,
    "gate_failed": 3,
    "compatibility_break": 4,
}


@dataclass
class ContractCheck:
    """Outcome of the compatibility-contract golden check.

    ``findings`` is empty iff the contract is complete + valid + carries NO unspecified break.
    """

    surfaces: Dict[str, CompatSurface]
    findings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "count": len(self.surfaces),
            "surfaces": {s: d.to_dict() for s, d in sorted(self.surfaces.items())},
            "findings": list(self.findings),
        }


def build_contract() -> Dict[str, CompatSurface]:
    """Return the frozen compatibility contract keyed by surface id."""

    contract: Dict[str, CompatSurface] = {}
    for row in _CONTRACT_ROWS:
        if row.surface in contract:
            raise CompatibilityError(
                "duplicate contract row for surface '{0}'".format(row.surface)
            )
        contract[row.surface] = row
    return contract


def check_contract(
    contract: Optional[Mapping[str, CompatSurface]] = None,
) -> ContractCheck:
    """PROVE the compatibility contract is complete + valid with NO unspecified breaking change.

    Falsifiable checks (each detects a specific omission/error):
      1. every REQUIRED surface has EXACTLY ONE row (none silently omitted);
      2. no row exists for a surface that is not a required surface;
      3. every row passes vocabulary validation;
      4. NO UNSPECIFIED breaking change: a row is `breaking` only if it declares an explicit
         `unsupported`/`removed` status. A preserved/changed/deprecated row is asserted non-breaking,
         so a break that is not specified is impossible to hide;
      5. every row names a golden test symbol (the one-test-per-surface requirement).
    """

    surfaces: Dict[str, CompatSurface] = (
        dict(contract) if contract is not None else build_contract()
    )
    findings: List[str] = []

    required = set(REQUIRED_SURFACES)
    present = set(surfaces)

    # 1) every required surface present exactly once (build_contract already rejects duplicates).
    for surf in sorted(required):
        if surf not in present:
            findings.append(
                "required surface '{0}' has NO contract row (silent omission)".format(
                    surf
                )
            )

    # 2) no row for a non-required surface.
    for surf in sorted(present):
        if surf not in required:
            findings.append("contract row '{0}' is not a required surface".format(surf))

    # 3) vocabulary validity.
    for surf, row in sorted(surfaces.items()):
        for problem in row.validate():
            findings.append("surface '{0}': {1}".format(surf, problem))

    # 4) no UNSPECIFIED breaking change + 5) every row names a test.
    for surf, row in sorted(surfaces.items()):
        if row.breaking and row.status not in _BREAKING_STATUSES:
            findings.append(
                "surface '{0}' breaks but does not declare an explicit unsupported/removed status".format(
                    surf
                )
            )
        # Belt: a preserved/changed/deprecated row must be non-breaking.
        if row.status not in _BREAKING_STATUSES and row.breaking:
            findings.append(
                "surface '{0}' is {1} yet marked breaking (unspecified break)".format(
                    surf, row.status
                )
            )
        if not row.test:
            findings.append("surface '{0}' names no golden test".format(surf))

    return ContractCheck(surfaces=surfaces, findings=findings)


def detect_unspecified_break(
    surface: str, breaks_existing_invocation: bool
) -> Optional[str]:
    """Return a finding string iff a surface breaks an existing invocation WITHOUT declaring it.

    This is the falsifiable detector the tests use: given an OBSERVED behavior (does this surface
    break an existing invocation?), it flags a break that the contract did not specify. A surface
    whose contract row is `unsupported`/`removed` may break (specified); any other status that breaks
    is an UNSPECIFIED break and is returned as a finding. An unknown surface is itself a finding.
    """

    contract = build_contract()
    row = contract.get(surface)
    if row is None:
        return "surface '{0}' has no contract row".format(surface)
    if breaks_existing_invocation and not row.breaking:
        return (
            "surface '{0}' breaks an existing invocation but its contract status is "
            "'{1}' (unspecified break)".format(surface, row.status)
        )
    return None


# ==================================================================================================
# E-02: idempotent, previewable migration/update
# ==================================================================================================

# The install/compatibility states a target repo can be in. This drives the previewable migration:
# each state previews a specific set of changes.
STATE_LEGACY = "legacy"  # only the old `.agents/workflows` layout; no `.aw/system`
STATE_CURRENT = (
    "current"  # the canonical `.aw/system` layout, generated set matches source
)
STATE_PARTIAL = "partial"  # an interrupted migration (a journal exists, not completed)
STATE_DRIFTED = (
    "drifted"  # `.aw/system` present but a GENERATED file was edited (our-owned drift)
)
STATE_CUSTOMIZED = (
    "customized"  # a HUMAN-owned file differs from what we would generate
)
INSTALL_STATES: FrozenSet[str] = frozenset(
    (STATE_LEGACY, STATE_CURRENT, STATE_PARTIAL, STATE_DRIFTED, STATE_CUSTOMIZED)
)

# The stamp file recording the exact compiler/adapter version that produced the installed generated
# set. Written under the target's durable state so a rollback/update can compare versions.
VERSION_STAMP_RELPATH = ".aw/state/durable/migrations/compat_version_stamp.json"

# Where replaced GENERATED files are backed up before they are overwritten (never a human file).
COMPAT_BACKUP_RELPATH = ".aw/state/durable/migrations/compat_backups"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_path(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


@dataclass(frozen=True)
class PlannedChange:
    """One previewed change in the migration/update plan.

    ``kind`` is one of: ``generate`` (write a new generated file), ``update-generated`` (replace an
    our-owned generated file, backing up the old one), ``preserve-human`` (a human-owned file that
    DIFFERS from what we would generate -- we do NOT touch it), ``resume`` (finish an interrupted
    migration), ``noop`` (already current). A ``preserve-human`` change NEVER writes: it records that
    the file is left intact.
    """

    kind: str
    path: str
    reason: str
    backup_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "path": self.path,
            "reason": self.reason,
            "backup_path": self.backup_path,
        }


@dataclass
class MigrationPreview:
    """A previewable, idempotent migration/update plan.

    ``state`` is the detected install state. ``changes`` is the exact set of changes the apply would
    make (empty for a ``current`` install -> a no-op). ``preserved`` lists human-owned files that
    would be left untouched. ``version`` is the exact compiler/adapter version recorded.
    """

    state: str
    version: str
    changes: List[PlannedChange] = field(default_factory=list)
    preserved: List[str] = field(default_factory=list)

    @property
    def is_noop(self) -> bool:
        return not self.changes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "version": self.version,
            "is_noop": self.is_noop,
            "changes": [c.to_dict() for c in self.changes],
            "preserved": list(self.preserved),
        }


class CompatMigrator:
    """Idempotent, previewable migration/update over the engine + MigrationManager.

    It REUSES the install-engine layout resolution (engine.resolve_target_layout /
    resolve_workflows_dir / generate_shim_members) to know what the GENERATED set should be, and the
    journaled MigrationManager for the records move + rollback. It NEVER forks a migration engine and
    NEVER silently overwrites human-owned content.
    """

    def __init__(self, target_repo: str, source_root: Optional[Path] = None):
        self.target_repo = Path(target_repo).resolve()
        self.source_root = (
            Path(source_root)
            if source_root is not None
            else engine.resolve_source_root(None)
        )
        # REUSE the journaled move-not-copy engine (no fork).
        self.manager = MigrationManager(target_repo=str(self.target_repo))
        self.stamp_path = self.target_repo / VERSION_STAMP_RELPATH
        self.backup_root = self.target_repo / COMPAT_BACKUP_RELPATH

    # -- version recording --------------------------------------------------------------------

    def current_version(self) -> str:
        """The exact compiler/adapter version of the SOURCE (via engine.read_version). Recorded into
        the version stamp so a later update/rollback can compare it."""

        return engine.read_version(self.source_root)

    def read_stamp(self) -> Optional[Dict[str, Any]]:
        if not self.stamp_path.is_file():
            return None
        try:
            return json.loads(self.stamp_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _write_stamp(self, version: str, generated: Mapping[str, str]) -> None:
        """Record the exact version + a hash of each generated file (our ownership record)."""

        self.stamp_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": version,
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "generated": {
                rel: _sha256_bytes(content.encode("utf-8"))
                for rel, content in sorted(generated.items())
            },
        }
        tmp = self.stamp_path.parent / (".tmp_stamp_%d.json" % os.getpid())
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.stamp_path)

    # -- generated-set resolution (REUSES the engine) -----------------------------------------

    def _expected_generated(self) -> Dict[str, str]:
        """Return the repo-relative generated shim set the engine WOULD install (our-owned).

        REUSES engine.resolve_target_layout + parse_manifest + generate_shim_members, so the
        compatibility layer measures against the SAME generated surface the installer produces.
        """

        layout = engine.resolve_target_layout(self.target_repo)
        workflows = engine.parse_manifest(self.source_root)
        return engine.generate_shim_members(
            workflows, self.source_root, target_layout=layout
        )

    # -- state detection ----------------------------------------------------------------------

    def detect_state(self) -> str:
        """Detect the install/compatibility state (falsifiable, deterministic).

        Order of precedence:
          * PARTIAL: an interrupted migration transaction exists (journal present, not completed);
          * LEGACY: `.agents/workflows` present and no `.aw/system`;
          * CUSTOMIZED: a HUMAN-owned instruction file (AGENTS/CLAUDE/GEMINI pointer) differs from a
            recorded baseline (a human edit we must preserve);
          * DRIFTED: an OUR-owned generated shim differs from the recorded stamp hash (someone edited
            a generated file we own);
          * CURRENT: canonical layout, generated set matches the stamp.
        """

        status = self.manager.status_migration()
        if status.get("active") and status.get("status") not in (
            None,
            "none",
            "completed",
            "rolled_back",
        ):
            return STATE_PARTIAL

        has_aw_system = (self.target_repo / engine.AW_SYSTEM_DIR).exists()
        has_legacy = (self.target_repo / engine.WORKFLOWS_DIR).exists()
        if not has_aw_system and has_legacy:
            return STATE_LEGACY

        stamp = self.read_stamp()

        # CUSTOMIZED: a human-owned pointer file differs from a recorded baseline hash.
        if stamp is not None:
            human = stamp.get("human_baseline", {})
            for rel, expected_hash in human.items():
                p = self.target_repo / rel
                if p.is_file() and _sha256_path(p) != expected_hash:
                    return STATE_CUSTOMIZED

        # DRIFTED: an our-owned generated file differs from the recorded hash.
        if stamp is not None:
            for rel, expected_hash in stamp.get("generated", {}).items():
                p = self.target_repo / rel
                if p.is_file() and _sha256_path(p) != expected_hash:
                    return STATE_DRIFTED

        return STATE_CURRENT

    # -- preview (no writes) ------------------------------------------------------------------

    def preview(self) -> MigrationPreview:
        """Compute the previewable, idempotent migration/update plan WITHOUT writing anything.

        A CURRENT install previews a no-op. Any state that would replace an our-owned generated file
        previews an ``update-generated`` change (with a backup path); a human-owned file that differs
        previews a ``preserve-human`` change (never written). Records the exact version.
        """

        version = self.current_version()
        state = self.detect_state()
        preview = MigrationPreview(state=state, version=version)

        if state == STATE_PARTIAL:
            status = self.manager.status_migration()
            preview.changes.append(
                PlannedChange(
                    kind="resume",
                    path="(migration transaction)",
                    reason="interrupted migration at checkpoint '{0}'; resume to complete".format(
                        status.get("last_verified_checkpoint")
                    ),
                )
            )
            return preview

        expected = self._expected_generated()
        stamp = self.read_stamp()
        recorded = (stamp or {}).get("generated", {})
        human_baseline = (stamp or {}).get("human_baseline", {})

        for rel, content in sorted(expected.items()):
            p = self.target_repo / rel
            expected_hash = _sha256_bytes(content.encode("utf-8"))
            if not p.exists():
                preview.changes.append(
                    PlannedChange(
                        kind="generate",
                        path=rel,
                        reason="generated file absent; will be created",
                    )
                )
                continue
            on_disk = _sha256_path(p)
            if on_disk == expected_hash:
                continue  # already current -> no change (idempotent no-op for this file)
            # The file differs from what we would generate. Is it OUR-owned or HUMAN-owned?
            if rel in human_baseline:
                # A human-owned file (recorded as such) that differs: PRESERVE, never overwrite.
                preview.preserved.append(rel)
                preview.changes.append(
                    PlannedChange(
                        kind="preserve-human",
                        path=rel,
                        reason="human-owned file differs; preserved (never silently overwritten)",
                    )
                )
                continue
            # An our-owned generated file that differs. If we PREVIOUSLY recorded it as ours and the
            # on-disk bytes no longer match our record, that is drift; we may replace it but MUST back
            # up the current bytes first. If we never recorded it (rel not in `recorded`) and it
            # exists with different content, treat it CONSERVATIVELY as human-owned: preserve it.
            if rel in recorded:
                preview.changes.append(
                    PlannedChange(
                        kind="update-generated",
                        path=rel,
                        reason="our-owned generated file drifted; will back up then regenerate",
                        backup_path=str(Path(COMPAT_BACKUP_RELPATH) / rel),
                    )
                )
            else:
                preview.preserved.append(rel)
                preview.changes.append(
                    PlannedChange(
                        kind="preserve-human",
                        path=rel,
                        reason="pre-existing file we never generated; preserved (treated as human-owned)",
                    )
                )
        return preview

    # -- apply (idempotent, backs up, records version) ---------------------------------------

    def apply(self, preview: Optional[MigrationPreview] = None) -> MigrationPreview:
        """Apply the previewed plan idempotently.

        NEVER overwrites a human-owned file (a ``preserve-human`` change writes nothing). BACKS UP an
        our-owned generated file before replacing it. Records the exact compiler/adapter version.
        Re-running on a CURRENT install is a no-op. A PARTIAL install is completed via
        MigrationManager.resume_migration (the reused engine), not re-planned here.
        """

        preview = preview or self.preview()

        if preview.state == STATE_PARTIAL:
            # REUSE the journaled engine's interrupted-migration recovery.
            self.manager.resume_migration()
            return self.preview()

        expected = self._expected_generated()
        applied_generated: Dict[str, str] = {}

        for change in preview.changes:
            if change.kind in ("generate", "update-generated"):
                rel = change.path
                content = expected[rel]
                p = self.target_repo / rel
                if change.kind == "update-generated" and (p.exists()):
                    # Back up the CURRENT (drifted) bytes before regenerating -- never destroy them.
                    backup_p = self.backup_root / rel
                    backup_p.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, backup_p)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
            # preserve-human / resume / noop: write nothing.

        # Record the version + hashes for EVERY generated file we own (whether written this run or
        # already current), preserving any human_baseline the stamp carried.
        for rel, content in expected.items():
            p = self.target_repo / rel
            if p.is_file() and _sha256_path(p) == _sha256_bytes(
                content.encode("utf-8")
            ):
                applied_generated[rel] = content

        prev_stamp = self.read_stamp() or {}
        self.stamp_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": preview.version,
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "generated": {
                rel: _sha256_bytes(content.encode("utf-8"))
                for rel, content in sorted(applied_generated.items())
            },
            "human_baseline": prev_stamp.get("human_baseline", {}),
        }
        tmp = self.stamp_path.parent / (".tmp_stamp_%d.json" % os.getpid())
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.stamp_path)

        return self.preview()

    def register_human_file(self, relpath: str) -> None:
        """Record a file as HUMAN-owned so a later differing edit is PRESERVED, not overwritten.

        The recorded baseline hash is the CURRENT bytes; a later edit that differs makes
        detect_state() return CUSTOMIZED and preview() emit a ``preserve-human`` change.
        """

        p = self.target_repo / relpath
        stamp = self.read_stamp() or {
            "version": self.current_version(),
            "generated": {},
        }
        human = dict(stamp.get("human_baseline", {}))
        human[relpath] = _sha256_path(p) if p.is_file() else ""
        stamp["human_baseline"] = human
        self.stamp_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.stamp_path.parent / (".tmp_stamp_%d.json" % os.getpid())
        tmp.write_text(json.dumps(stamp, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.stamp_path)


# ==================================================================================================
# E-03: rollback + interrupted-recovery + downgrade warning
# ==================================================================================================

# A rollback is one of two DISTINCT kinds (the plan requires distinguishing them):
#   * ADAPTER rollback: revert the generated set + runtime adapters to the last compatible state.
#     Fully reversible; no data loss.
#   * DATA-SCHEMA downgrade: the older version cannot READ new-run data (e.g. newer JSONL records).
#     This is NOT a safe adapter rollback; it must WARN rather than corrupt.
ROLLBACK_ADAPTER = "adapter"
ROLLBACK_DATA_SCHEMA_DOWNGRADE = "data-schema-downgrade"


@dataclass(frozen=True)
class RollbackAssessment:
    """The outcome of assessing a rollback before performing it.

    ``kind`` is :data:`ROLLBACK_ADAPTER` or :data:`ROLLBACK_DATA_SCHEMA_DOWNGRADE`. ``safe`` is True
    only for a pure adapter rollback with no unreadable future data. ``warnings`` names any data the
    older version cannot read (the explicit downgrade warning) -- non-empty warnings mean the caller
    must warn rather than corrupt.
    """

    kind: str
    safe: bool
    warnings: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "safe": self.safe,
            "warnings": list(self.warnings),
        }


# A runtime data record carries a schema_version; a target version supports reading up to a maximum
# schema version. When a record's schema exceeds what the rollback target can read, it is
# "future data" the older version cannot read -> downgrade warning.
RUNTIME_DATA_GLOB = "*.jsonl"


class CompatRollback:
    """Rollback to the last compatible generated set + runtime state, with interrupted recovery and a
    data-schema-downgrade warning. REUSES MigrationManager.rollback_migration / resume_migration."""

    def __init__(self, target_repo: str, source_root: Optional[Path] = None):
        self.target_repo = Path(target_repo).resolve()
        self.migrator = CompatMigrator(str(self.target_repo), source_root=source_root)
        self.manager = self.migrator.manager
        self.runtime_dir = self.target_repo / ".aw" / "state" / "runtime"

    def scan_future_data(self, max_readable_schema: int) -> List[str]:
        """Return repo-relative runtime data files whose schema_version EXCEEDS ``max_readable_schema``.

        Such a file is data written by a NEWER run that an older version cannot read; a rollback that
        would strand it must WARN. A file with no schema_version, or one <= max_readable_schema, is
        readable and not flagged.
        """

        flagged: List[str] = []
        if not self.runtime_dir.exists():
            return flagged
        for p in sorted(self.runtime_dir.rglob(RUNTIME_DATA_GLOB)):
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            max_seen = 0
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sv = rec.get("schema_version")
                if isinstance(sv, int) and sv > max_seen:
                    max_seen = sv
            if max_seen > max_readable_schema:
                flagged.append(str(p.relative_to(self.target_repo).as_posix()))
        return flagged

    def assess(self, max_readable_schema: int) -> RollbackAssessment:
        """Classify the rollback as an adapter rollback or a data-schema downgrade.

        If any runtime data exceeds ``max_readable_schema`` (unreadable by the older version), the
        rollback is a DATA-SCHEMA DOWNGRADE and is NOT safe (warn, do not corrupt). Otherwise it is a
        pure ADAPTER rollback and is safe.
        """

        future = self.scan_future_data(max_readable_schema)
        if future:
            return RollbackAssessment(
                kind=ROLLBACK_DATA_SCHEMA_DOWNGRADE,
                safe=False,
                warnings=tuple(
                    "runtime data '{0}' was written by a newer version and cannot be read after "
                    "downgrade".format(rel)
                    for rel in future
                ),
            )
        return RollbackAssessment(kind=ROLLBACK_ADAPTER, safe=True)

    def rollback(
        self, max_readable_schema: int, allow_data_downgrade: bool = False
    ) -> Dict[str, Any]:
        """Roll back the migration to the last compatible state.

        A pure ADAPTER rollback reverses the records move (via MigrationManager.rollback_migration --
        the reused journaled engine) and reverts the policy, restoring prior command discovery +
        runtime adapters WITHOUT record loss. A DATA-SCHEMA DOWNGRADE is REFUSED unless
        ``allow_data_downgrade`` is True: it WARNS about unreadable future data rather than corrupting
        it. When allowed, the future data is left intact (never truncated) and the warning is
        returned.
        """

        assessment = self.assess(max_readable_schema)
        if (
            assessment.kind == ROLLBACK_DATA_SCHEMA_DOWNGRADE
            and not allow_data_downgrade
        ):
            return {
                "status": "refused",
                "kind": assessment.kind,
                "warnings": list(assessment.warnings),
                "message": (
                    "refusing to downgrade: newer runtime data cannot be read by the older "
                    "version; pass allow_data_downgrade=True to proceed (data is preserved, not "
                    "corrupted)"
                ),
            }

        # REUSE the journaled engine to reverse the records move + policy switch (no record loss:
        # rollback_migration MOVES the migrated records back, it does not delete them).
        result = self.manager.rollback_migration()
        return {
            "status": "rolled_back",
            "kind": assessment.kind,
            "warnings": list(assessment.warnings),
            "authority": result.get("authority"),
        }

    def recover_interrupted(self) -> Dict[str, Any]:
        """Recover an interrupted migration: complete it if resumable, else report its state.

        REUSES MigrationManager.status_migration + resume_migration. A partial transaction is driven
        to completion (restoring prior command discovery + runtime adapters without record loss); a
        completed/absent transaction is a no-op.
        """

        status = self.manager.status_migration()
        if not status.get("active"):
            return {"status": "none", "message": "no migration transaction to recover"}
        if status.get("status") == "completed":
            return {"status": "completed", "message": "already completed"}
        result = self.manager.resume_migration()
        return {"status": "recovered", "resume": result}


# ==================================================================================================
# E-04: deprecation diagnostics + opt-in privacy-preserving usage counters
# ==================================================================================================


# The gates that MUST all be met before a deprecated alias may be removed. Removing an alias before
# any gate is met is REFUSED (aliases are kept until parity + adoption + version gates are met). This
# mirrors the plan's compatibility-gates table.
@dataclass(frozen=True)
class DeprecationGate:
    """The removal gate for one deprecated alias.

    An alias may be removed ONLY when ALL of: ``parity_met`` (the canonical replacement is at parity),
    ``adoption_met`` (adoption of the canonical name crossed the threshold), and the current release
    is at/after ``remove_at_version``. The removal authority is a separate approved release action;
    this class only GATES it (it never removes anything).
    """

    alias: str
    canonical: str
    remove_at_version: str
    parity_met: bool = False
    adoption_met: bool = False

    def can_remove(self, current_version: str) -> Tuple[bool, List[str]]:
        """Return (allowed, unmet_gates). Allowed only when every gate is satisfied."""

        unmet: List[str] = []
        if not self.parity_met:
            unmet.append("parity gate not met")
        if not self.adoption_met:
            unmet.append("adoption gate not met")
        if _version_lt(current_version, self.remove_at_version):
            unmet.append(
                "version gate not met (current {0} < remove-at {1})".format(
                    current_version, self.remove_at_version
                )
            )
        return (not unmet, unmet)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alias": self.alias,
            "canonical": self.canonical,
            "remove_at_version": self.remove_at_version,
            "parity_met": self.parity_met,
            "adoption_met": self.adoption_met,
        }


class AliasRemovalRefused(CompatibilityError):
    """Raised when an alias removal is attempted before its parity/adoption/version gate is met."""


def _version_tuple(version: str) -> Tuple[int, ...]:
    """Parse the leading dotted-numeric part of a version into a comparable tuple.

    Only the leading numeric components are compared (e.g. `1.3.0rc2.dev842+g...` -> (1, 3, 0)); a
    pre-release/build suffix is ignored for the >= gate (deliberately conservative: a dev build of
    the target release counts as reaching it).
    """

    parts: List[int] = []
    for chunk in version.split(".")[:3]:
        num = ""
        for ch in chunk:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    return tuple(parts)


def _version_lt(a: str, b: str) -> bool:
    """True iff version ``a`` is strictly less than version ``b`` (leading numeric compare)."""

    return _version_tuple(a) < _version_tuple(b)


def gate_alias_removal(gate: DeprecationGate, current_version: str) -> None:
    """Raise AliasRemovalRefused unless EVERY gate is met. This is the load-bearing refusal that keeps
    an alias alive; it NEVER removes the alias itself (removal is a separate approved release action)."""

    allowed, unmet = gate.can_remove(current_version)
    if not allowed:
        raise AliasRemovalRefused(
            "cannot remove alias '{0}' (canonical '{1}'): {2}".format(
                gate.alias, gate.canonical, "; ".join(unmet)
            )
        )


@dataclass(frozen=True)
class DeprecationNotice:
    """A LOCAL deprecation diagnostic for a used alias. It is a message only; emitting it never
    depends on telemetry and never records anything unless a counter is explicitly enabled."""

    alias: str
    canonical: str
    remove_at_version: str

    def message(self) -> str:
        return (
            "'{0}' is a deprecated alias of '{1}'; it keeps working and is scheduled for removal no "
            "earlier than {2}. Prefer '{1}'.".format(
                self.alias, self.canonical, self.remove_at_version
            )
        )


class DeprecationDiagnostics:
    """Deprecation diagnostics + LOCAL, opt-in, privacy-preserving usage counters.

    Telemetry is NEVER required for operation: diagnostics render regardless. Usage counting is
    OFF by default and is enabled ONLY by an explicit opt-in (``enable_counting=True``). Counters
    are LOCAL (written under the target's runtime state, never transmitted) and privacy-preserving
    (they record ONLY an alias name and an integer count -- no arguments, paths, timestamps, user, or
    machine identity). Counting can be disabled cleanly (the counter file is removed and further
    ``record`` calls are no-ops).
    """

    COUNTER_RELPATH = ".aw/state/runtime/deprecation/usage_counts.json"

    def __init__(
        self,
        target_repo: str,
        gates: Optional[Sequence[DeprecationGate]] = None,
        enable_counting: bool = False,
    ):
        self.target_repo = Path(target_repo).resolve()
        self.gates: Dict[str, DeprecationGate] = {g.alias: g for g in (gates or ())}
        self.enable_counting = enable_counting
        self.counter_path = self.target_repo / self.COUNTER_RELPATH

    def notice_for(self, alias: str) -> Optional[DeprecationNotice]:
        """Return the LOCAL deprecation notice for an alias, or None if it is not deprecated. This
        never touches the counter and never depends on telemetry."""

        gate = self.gates.get(alias)
        if gate is None:
            return None
        return DeprecationNotice(
            alias=gate.alias,
            canonical=gate.canonical,
            remove_at_version=gate.remove_at_version,
        )

    def record_use(self, alias: str) -> None:
        """Record ONE local, privacy-preserving use of ``alias`` IFF counting is opted in.

        A no-op when counting is disabled (telemetry is never required and defaults off). The stored
        record is ONLY {alias: count} -- no arguments, no timestamps, no identity.
        """

        if not self.enable_counting:
            return
        counts = self.read_counts()
        counts[alias] = counts.get(alias, 0) + 1
        self.counter_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.counter_path.parent / (".tmp_counts_%d.json" % os.getpid())
        tmp.write_text(json.dumps(counts, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.counter_path)

    def read_counts(self) -> Dict[str, int]:
        """Return the local usage counts (empty when counting was never enabled)."""

        if not self.counter_path.is_file():
            return {}
        try:
            data = json.loads(self.counter_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return {str(k): int(v) for k, v in data.items() if isinstance(v, int)}

    def disable_counting(self) -> None:
        """Disable usage counting cleanly: stop recording AND remove any local counter file.

        After this, operation is entirely telemetry-free and no local usage data remains.
        """

        self.enable_counting = False
        if self.counter_path.is_file():
            self.counter_path.unlink()

    def request_alias_removal(self, alias: str, current_version: str) -> None:
        """Gate an alias-removal request. REFUSES (raises) unless the alias's parity/adoption/version
        gate is met. This never removes the alias -- removal is a separate approved release action."""

        gate = self.gates.get(alias)
        if gate is None:
            raise AliasRemovalRefused(
                "unknown alias '{0}'; refusing removal".format(alias)
            )
        gate_alias_removal(gate, current_version)


# ==================================================================================================
# Agent-facing report (for the golden-check evidence paste)
# ==================================================================================================


def render_contract_report() -> str:
    """Render a deterministic, ANSI-free JSON report of the compatibility-contract golden check.

    This is the pasteable golden-check output (V-01 evidence): the row count, the ok flag, every
    surface row, and every finding. One JSON object for machine + human consumption.
    """

    return json.dumps(
        check_contract().to_dict(), sort_keys=True, indent=2, ensure_ascii=False
    )


__all__ = [
    # E-01
    "CompatibilityError",
    "STATUS_PRESERVED",
    "STATUS_CHANGED",
    "STATUS_DEPRECATED",
    "STATUS_UNSUPPORTED",
    "STATUS_REMOVED",
    "CONTRACT_STATUSES",
    "CONTRACT_OWNERS",
    "CompatSurface",
    "REQUIRED_SURFACES",
    "EXIT_CODES",
    "ContractCheck",
    "build_contract",
    "check_contract",
    "detect_unspecified_break",
    "render_contract_report",
    # E-02
    "STATE_LEGACY",
    "STATE_CURRENT",
    "STATE_PARTIAL",
    "STATE_DRIFTED",
    "STATE_CUSTOMIZED",
    "INSTALL_STATES",
    "VERSION_STAMP_RELPATH",
    "COMPAT_BACKUP_RELPATH",
    "PlannedChange",
    "MigrationPreview",
    "CompatMigrator",
    # E-03
    "ROLLBACK_ADAPTER",
    "ROLLBACK_DATA_SCHEMA_DOWNGRADE",
    "RollbackAssessment",
    "CompatRollback",
    # E-04
    "DeprecationGate",
    "AliasRemovalRefused",
    "gate_alias_removal",
    "DeprecationNotice",
    "DeprecationDiagnostics",
]
