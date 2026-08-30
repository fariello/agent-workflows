"""Unified check engine: compose the existing per-type validators into one Drift list per record
type. Pure (returns Drift, never prints). Consumed by the `aw check <type>` verb (awcmdsurf)."""

from __future__ import annotations

import importlib.util
import re as _re
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

from agent_workflows import artifact_core as _core
from agent_workflows import artifact_naming as _naming
from agent_workflows import engine as _engine
from agent_workflows import (
    ipd_schema as _S,
)  # low-level; safe (no cycle) - ipddeps ovbnyq
from agent_workflows import record_producers as _rp

# Which check kinds each type supports today. "names" = filename-grammar conformity;
# "content" = front-matter/status/contract; "refs" = reference integrity (via the index drift).
SUPPORTED: Dict[str, tuple] = {
    "plans": ("names", "content", "refs"),
    "specs": ("names", "content"),
    "backlog": ("names", "content"),
    "research": ("names", "content", "refs"),
    "prompts": ("names",),
    "walkthroughs": ("names",),
    "roadmaps": ("names",),
    "releases": ("names", "content"),
}

# Spec id6-in-filename cutover (IPD ha55fi E-03 / OQ-01): specs are the last faceted type to adopt
# the id6-clustered grammar. To grandfather the existing legacy `YYYYMMDD-HHMM-NN-<slug>.spec.md`
# corpus while forcing id6 GOING FORWARD, a spec whose FILENAME date is at/after this cutover MUST
# be id6-clustered (`require_id6=True`); a pre-cutover spec stays conformant in either shape. There
# is NO pre-existing name-conformance cutover mechanism in this module to reuse (verified); this is
# the single configured boundary. Value chosen (run-20260828T035444Z-36740 DECISION 11-ha55fi-D1):
# strictly AFTER the newest existing legacy-named spec date (20260827), so ALL existing specs remain
# grandfathered. A future migration run that mass-renames the legacy specs may lower it.
SPEC_ID6_CUTOVER_DATE = (
    "20260828"  # compact YYYYMMDD; require_id6 iff filename date >= this
)

# --------------------------------------------------------------------------------------
# Versioned policy schema (agentadhere Phase 1, IPD uisjns).
#
# The shared policy engine is the host-independent deterministic core every later layer (atomic
# commands, git hooks, CI) calls, so the finding shape and the rule -> {severity, assurance,
# determinism} mapping must be STABLE and VERSIONED. This registry is that contract. Each rule id
# maps to its Phase-0 assurance class (spec pqsx96: I-01..I-15) and its determinism tag; the
# `enrich_drift` helper stamps those onto a `Drift` so the machine-readable `aw check` output carries
# the full documented shape. The DATA output carries `policy_schema_version` so a hook/CI can assert
# compatibility independently; it is reconciled with (not a replacement for) the agent envelope
# `aw.agent/v1` (OQ-01). An unregistered rule id is enriched conservatively (error/repository/
# deterministic) so a new rule is never SILENTLY unclassified.
POLICY_SCHEMA_VERSION = "aw.policy/v1"

# Assurance classes (Phase-0 catalog spec pqsx96 Section 2): the bare tokens used in the finding
# shape. `guidance` = cooperative agents should follow; `repository` = a noncompliant artifact must
# fail checks/merge (deterministic over the artifact; authoritative only when the same check gates
# merge in CI); `authority` = must survive a fully privileged local agent (needs external authority).
ASSURANCE_GUIDANCE = "guidance"
ASSURANCE_REPOSITORY = "repository"
ASSURANCE_AUTHORITY = "authority"

# Determinism tags (findings 7.2 / catalog): how a finding's truth was reached.
DET_DETERMINISTIC = "deterministic"
DET_HEURISTIC = "heuristic"
DET_ATTESTED = "attested"


class RuleSpec(NamedTuple):
    """One rule's stable policy metadata (agentadhere Phase 1)."""

    severity: str  # "error" | "warning" | "info"
    assurance: str  # ASSURANCE_*
    determinism: str  # DET_*
    invariant: (
        str  # the Phase-0 catalog invariant id it enforces (e.g. "I-03"), or "" if none
    )


# The versioned rule registry: stable rule id -> RuleSpec. Assurance classes trace to the Phase-0
# invariant catalog (spec pqsx96). Rules not listed here fall back to a conservative default.
RULE_REGISTRY: Dict[str, RuleSpec] = {
    # Naming grammar (catalog I-09).
    "check.name-nonconformant": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-09"
    ),
    # Untooled lifecycle status change (catalog I-03).
    "check.status-untooled": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-03"
    ),
    # Filename identity-slot / id6 uniqueness (catalog I-09 family).
    "check.setid-collision": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-09"
    ),
    "check.id6-collision": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-09"
    ),
    "check.id6-identity-slot": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-09"
    ),
    # Release-gate preservation (catalog I-07).
    "check.blocking-item-closed-without-gate": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    "check.from-backlog-gate-mismatch": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    "check.blocks-release-dangling": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    "check.from-backlog-dangling": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    "check.orphaned-live-blocker": RuleSpec(
        "warning", ASSURANCE_REPOSITORY, DET_HEURISTIC, "I-07"
    ),
    # revgate Order 01 (15zvu6) E-06: a `.review.md` whose `Plan-Id:` resolves to no plan. Same
    # SHAPE as the `*-dangling` rules above (an unresolvable cross-tree reference), but deliberately
    # `warning`, NOT `error` like its neighbours: a review left behind by a superseded or deleted plan
    # is UNTIDY, not dangerous, and nothing downstream reads it, so it must not block a commit or set
    # an exit code. The in-tree precedent for an advisory rule in this family is
    # `check.orphaned-live-blocker` directly above. It IS deterministic (a literal id6 set lookup,
    # no inference), hence DET_DETERMINISTIC rather than DET_HEURISTIC.
    "check.review-dangling": RuleSpec(
        "warning", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    # revgate Order 02 (plqjt7) E-01: an unfixed finding at or above the configured severity
    # threshold that was never escalated into a `Blocking: yes` open question. UNLIKE
    # `check.review-dangling` above (advisory, an untidy leftover), this one is an `error`: an unfixed
    # High/Blocker that gates nothing is the exact hole this Set exists to close, so it must set an
    # exit code. Deterministic: a closed-vocabulary severity compared against a configured threshold
    # via the ONE shared `review_findings.is_gating` predicate, plus a literal finding-id lookup in the
    # plan's parsed open questions. No inference, hence DET_DETERMINISTIC.
    #
    # Invariant: `""`. Deliberate, with a reason rather than an omission. The Phase-0 catalog (spec
    # pqsx96) invariants used above cover naming (I-09), lifecycle-status authority (I-03), release
    # gates (I-07), declared scope (I-01), dependency statements (I-08), and authoring nudges (I-12).
    # None of them is about REVIEW findings: the review tier did not exist as machine-readable data
    # until 15zvu6, so the catalog has no invariant for it yet. Claiming a neighbouring id would be a
    # false trace. `check.priority-invalid` above sets the precedent for a legitimately uncatalogued
    # rule id.
    "check.review-finding-unescalated": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, ""
    ),
    # revgate Order 04 (c621h9) E-07: a self-resolved review decision marked IRREVERSIBLE that was
    # never surfaced (no `Blocking: yes` open question, no note that the maintainer was told), or a
    # decision row with no `Reversible` judgement at all.
    #
    # `warning`, NOT `error`, and the difference from its Order 02 sibling directly above is
    # deliberate rather than an oversight. The preventive control already exists in the workflow (a
    # reviewer must escalate an irreversible decision at DECISION time), so this rule is the BACKSTOP
    # for someone who skipped it. Blocking here would be a third overlapping enforcement path
    # alongside Order 02's escalation gate and Order 03's dependency cascade, which
    # GUIDING_PRINCIPLES 6 warns against ("fix by default invites gold-plating"). The plan's OQ-01
    # resolved this as report-only on exactly that evidence. Registration is NOT bookkeeping: an
    # unregistered id falls back to `_DEFAULT_RULESPEC`, which is `error` with an EMPTY invariant, so
    # omitting this entry would silently contradict the report-only posture. In-tree advisory
    # precedents: `check.orphaned-live-blocker` and `check.review-dangling`.
    #
    # DO NOT READ `warning` AS "cannot fail anything" (measured, not assumed):
    # `artifact_core.drift_exit_code` exempts only `info`, so a `warning` DOES drive a nonzero
    # findings exit. The distinction this severity buys is that it adds no LIFECYCLE gate (no `aw ipd
    # lint` checkpoint, no begin/finalize refusal, no dependency block), unlike its `error` sibling
    # which Order 02 wired into two lint checkpoints. `info` is the severity that cannot affect an
    # exit code; this is deliberately not `info`, because an unescalated irreversible decision is a
    # real obligation, not a nudge.
    #
    # Deterministic: a closed-vocabulary `Reversible` classification (shared with `aw reviews
    # decisions` via `reviews.classify_reversible`) plus a literal `Blocking: yes` lookup in the
    # plan's parsed open questions. No inference, hence DET_DETERMINISTIC.
    #
    # Invariant `""`, deliberate and for the same reason the Order 02 rule states: the Phase-0 catalog
    # (spec pqsx96) covers naming (I-09), lifecycle-status authority (I-03), release gates (I-07),
    # declared scope (I-01), dependency statements (I-08), and authoring nudges (I-12). None is about
    # REVIEW-TIME DECISIONS, which did not exist as machine-readable data until this Set. Claiming a
    # neighbouring id would be a false trace.
    "check.review-decision-unescalated": RuleSpec(
        "warning", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, ""
    ),
    # Cross-IPD dependency statements (catalog I-08).
    "check.ipd-dependency-malformed": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-08"
    ),
    "check.ipd-dependency-dangling": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-08"
    ),
    "check.ipd-dependency-ambiguous": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-08"
    ),
    "check.ipd-dependency-cycle": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-08"
    ),
    "check.ipd-dependency-unresolved": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-08"
    ),
    # revgate Order 03 (7nkcgp) E-03: an `executed:<id6>` edge whose target RESOLVES FINE but carries
    # recorded unresolved gating findings, so it must not satisfy the edge.
    #
    # WHY A NEW ID RATHER THAN REUSING ONE. Reuse was evaluated and REJECTED on evidence. `_resolve_edge`
    # returns exactly three verdicts - `ok`, `dangling`, `ambiguous` - and all three are about IDENTITY
    # resolution: `dangling` means NO artifact has that id6, `ambiguous` means SEVERAL do. Reporting a
    # findings-blocked target (whose id6 resolves to exactly one artifact) as either would be a FALSE
    # statement about identity and would corrupt both rules' meaning for every other consumer. This
    # condition is about target QUALITY, which the existing vocabulary has no verdict for.
    #
    # Catalog invariant I-08 IS claimed here, unlike the Order 02 rule: this is a statement about a
    # cross-IPD DEPENDENCY edge's satisfaction, which is exactly what I-08 covers; only the input
    # (review findings) is new. Severity mirrors the rest of the family (`error`), and the evaluator
    # keeps the same phase split, so a pre-cutover corpus is not mass-failed.
    "check.ipd-dependency-findings-blocked": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-08"
    ),
    "check.ipd-missing-dependency-statement": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-08"
    ),
    # Recognized-but-optional Priority enum on a plan's own metadata (xprio 1b45el). An out-of-vocab
    # `- Priority:` value is an error; an absent Priority is silent (optional). The shared vocab is
    # backlog.PRIORITIES (not forked). This is a plain metadata-enum check (precedent: backlog's own
    # priority-invalid guard), NOT a cross-tree dangling/reference check.
    "check.priority-invalid": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, ""
    ),
    # Authoring-lifecycle nudge (catalog I-12): a finished draft should advance to to-review. This
    # is GUIDANCE and only detectable (placeholder-free draft), so info-severity + heuristic.
    "check.ipd-draft-ready-to-review": RuleSpec(
        "info", ASSURANCE_GUIDANCE, DET_HEURISTIC, "I-12"
    ),
    # Event-derived lifecycle transition validity (agentadhere Phase 3, IPD wqj1ne E-01; catalog
    # I-03). A plan whose inline history event stream contains an invalid/out-of-order/unauthorized
    # transition is flagged. Repository-class + deterministic over the (locally forgeable) events.
    "check.lifecycle-transition-invalid": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-03"
    ),
    # Declared-file-scope drift (agentadhere Phase 3, IPD wqj1ne E-02; catalog I-01). A plan with an
    # active begin receipt whose changed paths since the frozen base fall outside its Scope-Paths.
    "check.scope-drift": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-01"
    ),
    # Pre-push authorization feedback (agentadhere Phase 4, IPD diundn E-02; catalog I-02). This is
    # an AUTHORITY invariant: a LOCAL pre-push hook can only give feedback, NEVER enforce it (the
    # authoritative boundary is a protected branch / required CI / brokered credential). The
    # assurance class is `authority` precisely to make that honest limit explicit in the finding.
    "check.push-unauthorized": RuleSpec(
        "error", ASSURANCE_AUTHORITY, DET_HEURISTIC, "I-02"
    ),
}

# Conservative default for an unregistered rule id: treat it as an error-severity, repository-class,
# deterministic finding so a new rule is never SILENTLY unclassified (fail toward visible).
_DEFAULT_RULESPEC = RuleSpec("error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "")


def rule_spec(rule_id: str) -> RuleSpec:
    """Return the registered RuleSpec for a rule id, or the conservative default."""
    return RULE_REGISTRY.get(rule_id, _DEFAULT_RULESPEC)


def enrich_drift(
    drift: _core.Drift,
    *,
    observed: str = "",
    required: str = "",
    recovery: str = "",
) -> _core.Drift:
    """Stamp the versioned policy metadata (severity/assurance/determinism) onto a Drift.

    Looks up the rule id in RULE_REGISTRY (conservative default for an unknown rule), and fills the
    optional observed/required/recovery fields when the caller supplies them. Preserves the original
    location/rule/detail exactly. Idempotent-safe: re-enriching overwrites only the metadata fields.
    """
    spec = rule_spec(drift.rule)
    return drift._replace(
        observed=observed or drift.observed,
        required=required or drift.required,
        recovery=recovery or drift.recovery,
        assurance=drift.assurance or spec.assurance,
        determinism=drift.determinism or spec.determinism,
        severity=drift.severity or spec.severity,
    )


def finding_dict(
    drift: _core.Drift, repo_root: Optional[Path] = None
) -> Dict[str, object]:
    """Serialize a (possibly enriched) Drift into the full documented, JSON-safe finding shape.

    This is the machine-readable finding record the versioned policy engine emits (agentadhere
    Phase 1): a stable rule id, severity, assurance class, observed-vs-required, the exact recovery
    command, and the determinism tag, under a `schema_version`. Un-enriched fields are filled from
    the registry here so a raw Drift still serializes to the full shape.
    """
    spec = rule_spec(drift.rule)
    loc = drift.location
    if repo_root is not None:
        try:
            loc = str(
                Path(drift.location).resolve().relative_to(Path(repo_root).resolve())
            )
        except (ValueError, OSError):
            loc = drift.location
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "rule": drift.rule,
        "severity": drift.severity or spec.severity,
        "assurance": drift.assurance or spec.assurance,
        "determinism": drift.determinism or spec.determinism,
        "invariant": spec.invariant,
        "location": loc,
        "detail": drift.detail,
        "observed": drift.observed,
        "required": drift.required,
        "recovery": drift.recovery,
    }


_SKIP_NAMES = {"README.md", "INDEX.md", "STATUS.md"}
# The type->facet map is defined ONCE in the naming authority (IPD o6b8l3). check_names only checks
# clustered-facet types, so `comms` (no clustered check today) is intentionally omitted here.
_TYPE_FACET = {
    t: _naming.TYPE_FACET[t]
    for t in (
        "plans",
        "specs",
        "backlog",
        "prompts",
        "walkthroughs",
        "roadmaps",
        "releases",
    )
}


def _type_dirs(repo_root: Path, record_type: str) -> List[Path]:
    """Existing dirs to scan for a record type.

    `resolve_record_read_paths` only accepts the RecordClass values {plans, specs, research,
    prompts, comms, walkthroughs} and RAISES for `backlog`/`roadmaps`; those resolve directly.
    Also includes the literal `.aw/records/<type>` (+ legacy `.agents/<type>`) so a bare/unregistered
    repo resolves. De-duplicated by resolved path; unknown types yield [].
    """
    repo_root = Path(repo_root)
    out: List[Path] = []
    seen: set = set()

    def _add(p: Path) -> None:
        try:
            key = str(p.resolve())
        except OSError:
            return
        if key not in seen and p.is_dir():
            seen.add(key)
            out.append(p)

    if record_type == "backlog":
        for rel in (".aw/records/backlog", ".agents/backlog"):
            _add(repo_root / rel)
    elif record_type == "roadmaps":
        _add(repo_root / ".aw" / "records" / "roadmaps")
    else:
        try:
            for p in _rp.resolve_record_read_paths(
                record_type, target_repo=str(repo_root)
            ):
                _add(p)
        except Exception:
            pass
    # Literal fallback (bare repo, or types the resolver rejects).
    _add(repo_root / ".aw" / "records" / record_type)
    _add(repo_root / ".agents" / record_type)
    return out


def _iter_type_files(
    repo_root: Path, record_type: str, include_untracked: bool = False
):
    """Yield each non-index *.md path for the type, de-duplicated by resolved path and skipping ignored dirs."""
    ignored_dirs = _core.get_ignored_dirs(repo_root)
    seen: set = set()
    for d in _type_dirs(repo_root, record_type):
        if _core.is_ignored_path(
            d, repo_root, ignored_dirs, include_untracked=include_untracked
        ):
            continue
        for p in d.rglob("*.md"):
            if p.name in _SKIP_NAMES or _core.is_ignored_path(
                p, repo_root, ignored_dirs, include_untracked=include_untracked
            ):
                continue
            try:
                key = str(p.resolve())
            except OSError:
                continue
            if key in seen:
                continue
            seen.add(key)
            yield p


def _load_normalizer():
    """Load the shipped plan-name normalizer layout-agnostically (source checkout AND installed
    wheel), mirroring cli.py:2890. Returns the module or None if it cannot be located."""
    try:
        root = _engine.resolve_source_root(None)
    except SystemExit:
        return None
    script = root / "setup-repo" / "tools" / "normalize_plan_names.py"
    if not script.is_file():
        return None
    spec = importlib.util.spec_from_file_location("awcheck_npn", script)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_names(
    repo_root: Path,
    record_type: str,
    legacy: bool = False,
    include_untracked: bool = False,
) -> List[_core.Drift]:
    """Filename-grammar conformity for a type's files. Research is skipped (own grammar). If the
    normalizer cannot be located, returns [] (names simply not checked)."""
    facet = _TYPE_FACET.get(record_type)
    if facet is None:
        return []  # research + any type without a clustered facet
    npn = _load_normalizer()
    if npn is None:
        return []
    drift: List[_core.Drift] = []
    for p in _iter_type_files(
        repo_root, record_type, include_untracked=include_untracked
    ):
        # Spec id6 cutover (IPD ha55fi E-03): a spec dated at/after SPEC_ID6_CUTOVER_DATE must be
        # id6-clustered; a pre-cutover spec is grandfathered (legacy HHMM-NN name still conforms).
        require_id6 = record_type == "specs" and _spec_requires_id6(p.name)
        if npn.is_conformant(p.name, expected_type=facet, require_id6=require_id6):
            continue
        # legacy=True allows a name that FAILS is_conformant but is a RECOGNIZED legacy shape
        # (parse_name non-None) - e.g. hyphenated-date YYYY-MM-DD-<slug>.md. The classic
        # YYYYMMDD-HHMM-NN form is already is_conformant, so it never reaches here. This grandfather
        # path does NOT apply once require_id6 is in force (a post-cutover legacy spec must convert).
        if legacy and not require_id6 and npn.parse_name(p.name) is not None:
            continue
        detail = f"filename does not match the {record_type} grammar"
        if require_id6:
            detail = (
                f"spec dated at/after the id6 cutover ({SPEC_ID6_CUTOVER_DATE}) must be "
                f"id6-clustered; convert it with `aw rename specs {p.name} --to-id6 --apply`"
            )
        drift.append(
            _core.Drift(
                str(p),
                "check.name-nonconformant",
                detail,
            )
        )
    return drift


_SPEC_DATE_RE = _re.compile(r"\A(\d{8})-")


def _spec_requires_id6(filename: str) -> bool:
    """True iff a spec filename's leading YYYYMMDD date is at/after SPEC_ID6_CUTOVER_DATE.

    A name with no parseable leading date is treated as pre-cutover (require_id6=False) so an
    unusual/legacy shape is not force-failed by the cutover; the normal grammar check still applies.
    """
    m = _SPEC_DATE_RE.match(filename)
    if m is None:
        return False
    return m.group(1) >= SPEC_ID6_CUTOVER_DATE


def check_content(
    repo_root: Path,
    record_type: str,
    legacy: bool = False,
    include_untracked: bool = False,
) -> List[_core.Drift]:
    """Front-matter/status/contract validation, delegated to the existing per-type validators."""
    repo_root = Path(repo_root)
    drift: List[_core.Drift] = []
    if record_type == "specs":
        from agent_workflows import specs as _specs

        # Discover files via _type_dirs (robust for a bare repo), validate each with validate_spec.
        for p in _iter_type_files(
            repo_root, "specs", include_untracked=include_untracked
        ):
            try:
                drift.extend(_specs.validate_spec(p, p.read_text(encoding="utf-8")))
            except OSError:
                continue
    elif record_type == "backlog":
        from agent_workflows import backlog as _backlog

        for p in _iter_type_files(
            repo_root, "backlog", include_untracked=include_untracked
        ):
            try:
                drift.extend(_backlog.validate_item(p, p.read_text(encoding="utf-8")))
            except OSError:
                continue
    elif record_type == "plans":
        from agent_workflows import plans_index as _pidx

        dirs = _type_dirs(repo_root, "plans")
        if dirs:
            drift.extend(_pidx.check_drift(repo_root, dirs[0]))
        # ipddeps ovbnyq (spec 25kzda 2.10): the cross-IPD dependency check is a PLANS-scoped concern
        # (every dependency source is an IPD), so it runs in the plans-type content path - reached by
        # BOTH `aw check plans` and the `aw check all` fan-out, exactly once, never double-reported
        # (deliberately NOT also added to the collisions-only cross-tree sweep).
        try:
            drift.extend(check_ipd_dependencies(repo_root))
        except Exception:
            pass
        # xprio 1b45el E-02: validate the recognized-but-optional `- Priority:` enum on each plan
        # against the shared backlog.PRIORITIES (out-of-vocab -> error; absent -> silent). Runs in the
        # plans-type content path so BOTH `aw check plans` and `aw check all` surface it exactly once.
        try:
            drift.extend(
                check_plan_priority(repo_root, include_untracked=include_untracked)
            )
        except Exception:
            pass
        # agentadhere Phase 1 (IPD uisjns E-03; catalog invariant I-12): nudge a finished draft to
        # advance to `to-review`. Detect-and-nudge only (never auto-flips status).
        try:
            drift.extend(
                check_ipd_draft_ready(repo_root, include_untracked=include_untracked)
            )
        except Exception:
            pass
        # revgate Order 02 (plqjt7 E-01): an unfixed review finding at or above the configured
        # severity threshold that was never escalated into a `Blocking: yes` open question. Runs in
        # the PLANS-TYPE content path for the same documented reason `check_ipd_dependencies` above
        # does - the concern is plans-scoped (every finding names a plan) - so it is reached by BOTH
        # `aw check plans` and the `aw check all` fan-out, exactly once, and is deliberately NOT also
        # added to the collisions-only cross-tree sweep (which the full sweep alone reaches).
        try:
            drift.extend(
                check_review_finding_unescalated(
                    repo_root, include_untracked=include_untracked
                )
            )
        except Exception:
            pass
        # revgate Order 04 (c621h9 E-07): a self-resolved review decision marked IRREVERSIBLE that
        # was never surfaced to the maintainer. Same PLACEMENT as the Order 02 rule directly above,
        # and for the same documented reason (`check_ipd_dependencies`' "every dependency source is
        # an IPD" precedent): the concern is keyed off the PLAN, so it belongs in the plans-type
        # content path, reached by BOTH `aw check plans` and the `aw check all` fan-out exactly once,
        # and deliberately NOT in the collisions-only cross-tree sweep (which the full sweep alone
        # reaches). Note the consequence honestly: the rule fires while checking PLANS even though
        # the artifact it reads is a REVIEW. `aw check reviews` is not a valid type today and adding
        # one is out of scope. Advisory (`warning`), so it never sets an exit code. Fail-isolated in
        # the same shape as its neighbours.
        try:
            drift.extend(
                check_review_decision_unescalated(
                    repo_root, include_untracked=include_untracked
                )
            )
        except Exception:
            pass
        # agentadhere Phase 3 (IPD wqj1ne): event-derived transition validity (E-01) + declared
        # file-scope drift for a plan with an active begin receipt (E-02). Both fail-isolated.
        try:
            drift.extend(
                check_lifecycle_transitions(
                    repo_root, include_untracked=include_untracked
                )
            )
        except Exception:
            pass
        try:
            drift.extend(
                check_scope_drift(repo_root, include_untracked=include_untracked)
            )
        except Exception:
            pass
    elif record_type == "research":
        from agent_workflows import research_index as _ridx

        dirs = _type_dirs(repo_root, "research")
        if dirs:
            drift.extend(_ridx.check_drift(repo_root, dirs[0]))
    elif record_type == "releases":
        from agent_workflows import releases as _releases

        for p in _iter_type_files(repo_root, "releases"):
            try:
                drift.extend(
                    _releases.validate_release(p, p.read_text(encoding="utf-8"))
                )
            except OSError:
                continue
    # prompts / walkthroughs / roadmaps: no content validator today -> []
    return drift


def check_refs(repo_root: Path, record_type: str) -> List[_core.Drift]:
    """Reference integrity. DELEGATES to per-type ``check_drift`` (IPD 3cmnfc E-04): the dangling-
    citation detection for plans and research is delivered by ``plans_index.check_drift`` /
    ``research_index.check_drift`` (invoked via ``check_content``), both of which now consume the
    ONE unified dangling policy in ``artifact_refs`` (id6 handles + dead bare-filename via the
    resolver, OQ-01 option B; setid citations not checked). This stub returns [] to avoid
    double-counting and remains the documented SEAM for future per-type ref checks (e.g. the
    awrelease Blocks-Release dangling check folds in here)."""
    return []


_ID_LINE_RE = _re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")
_SET_LINE_RE = _re.compile(r"(?m)^- Set:\s*(.+?)\s*$")
_HHMM_RE = _re.compile(r"\A\d{4}\Z")
_HAS_DIGIT_RE = _re.compile(r"\d")


def _identity_slot_token(filename: str) -> "str | None":
    """Return the raw ``<id6>`` token in a filename's identity slot, or None.

    Uses the naming authority's clustered parse (single source, IPD o6b8l3). Excludes the legacy
    ``YYYYMMDD-HHMM-NN-<slug>`` shape, whose 4-digit HHMM coincidentally matches the ``<setid>``
    segment (mirrors ``plans_index.check_drift``): a real clustered set-id is kebab, never exactly
    4 digits. The returned token may still be a slug word (e.g. ``assess``); the caller applies the
    real-id6 discriminator once the global set of declared ids is known."""

    m = _naming.parse_clustered(filename)
    if not m or _HHMM_RE.match(m.group("set")):
        return None
    return m.group("id6")


def _is_real_id6(token: str, declared_ids: set) -> bool:
    """A slot token is a REAL id6 (not a slug's first word) iff it is declared as some file's
    frontmatter Id, OR it visibly mixes digits and letters (mirrors ``tmp/find_id6_dupes.py``'s
    oracle: slug words like ``assess``/``agents`` are all-letters, so this excludes them)."""

    return token in declared_ids or bool(_HAS_DIGIT_RE.search(token))


def _parse_setid(text: str):
    """Return (setid, descriptive-or-None) from a `- Set: <terse> (<descriptive>)` line, or
    (None, None). The setid is the first whitespace token before any '('."""
    m = _SET_LINE_RE.search(text)
    if not m:
        return None, None
    raw = m.group(1).strip()
    if not raw:
        return None, None
    setid = raw.split("(")[0].strip().split()[0] if raw.split("(")[0].strip() else None
    desc = None
    if "(" in raw and ")" in raw:
        desc = raw[raw.index("(") + 1 : raw.rindex(")")].strip() or None
    return setid, desc


def check_collisions(
    repo_root: Path, include_untracked: bool = False
) -> List[_core.Drift]:
    """Cross-tree id6 AND setid uniqueness, PLUS the filename identity-slot invariant (D140).

    Runs ONCE over every SUPPORTED type (collisions are global, not per-type):

    * frontmatter ``- Id:`` id6: a valid id6 declared on two different resolved files
      (``check.id6-collision``);
    * setid: the same setid under two different types, or the same setid with two different
      non-None descriptives (``check.setid-collision``);
    * filename IDENTITY-SLOT id6 (DECISIONS.md D140): the ``<id6>`` in a file's
      ``YYYYMMDD-<setid>-NN-<id6>-<slug>`` filename slot is that file's UNIQUE IDENTITY. It is
      validated by the precise rule (so it flags a foreign id6 in the slot but never mass-flags
      conformant files): (a) if the file DECLARES a frontmatter ``- Id:``, its slot id6 MUST EQUAL
      that declared ``- Id:``; (b) if the file declares NO ``- Id:``, its slot id6 MUST NOT equal
      any OTHER file's declared ``- Id:`` NOR any other file's slot id6 (it must be the sole holder
      of that id6). A violation emits ``check.id6-identity-slot`` naming the offending path AND the
      file that actually owns that id6. Legacy ``YYYYMMDD-HHMM-NN-<slug>`` names (no id6 slot) are
      exempt - only a filename whose slot parses as a real id6 via the naming authority is checked.
    """
    repo_root = Path(repo_root)
    drift: List[_core.Drift] = []
    seen_ids: Dict[str, str] = {}
    # setid -> (type, descriptive-or-None, first-path)
    seen_sets: Dict[str, tuple] = {}

    # First gather, for every file, its declared frontmatter Id and its filename identity-slot id6,
    # so the identity-slot rule (below) can be evaluated with global knowledge of who OWNS each id6.
    # A file "record": (path-str, declared_id-or-None, slot_id6-or-None).
    records: List[tuple] = []
    for record_type in SUPPORTED:
        for p in _iter_type_files(
            repo_root, record_type, include_untracked=include_untracked
        ):  # already deduped by resolved path
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            m = _ID_LINE_RE.search(text)
            declared_id = m.group(1) if m else None
            slot_id6 = _identity_slot_token(p.name)
            records.append((str(p), declared_id, slot_id6))

            if declared_id:
                id6 = declared_id
                if id6 in seen_ids:
                    drift.append(
                        _core.Drift(
                            str(p),
                            "check.id6-collision",
                            f"id6 {id6} also on {seen_ids[id6]}",
                        )
                    )
                else:
                    seen_ids[id6] = str(p)
            sid, desc = _parse_setid(text)
            if sid:
                if sid in seen_sets:
                    prev_type, prev_desc, prev_path = seen_sets[sid]
                    if prev_type != record_type:
                        drift.append(
                            _core.Drift(
                                str(p),
                                "check.setid-collision",
                                f"setid {sid} conflicts with {prev_path} (different type: {prev_type} vs {record_type})",
                            )
                        )
                    elif (
                        desc is not None and prev_desc is not None and desc != prev_desc
                    ):
                        drift.append(
                            _core.Drift(
                                str(p),
                                "check.setid-collision",
                                f"setid {sid} conflicts with {prev_path} (descriptive: {prev_desc!r} vs {desc!r})",
                            )
                        )
                else:
                    seen_sets[sid] = (record_type, desc, str(p))

    drift.extend(_check_identity_slots(records))
    return drift


def _check_identity_slots(records: List[tuple]) -> List[_core.Drift]:
    """Validate the filename identity-slot id6 invariant (D140) over pre-gathered file records.

    ``records`` is a list of ``(path_str, declared_id_or_None, slot_id6_or_None)``. Returns
    ``check.id6-identity-slot`` Drift for each file whose filename identity slot holds an id6 that
    is not that file's own unique identity. See ``check_collisions`` for the precise (a)/(b) rule.
    """
    drift: List[_core.Drift] = []
    # The set of all frontmatter-declared ids drives the real-id6 discriminator (a slot token that
    # is some file's declared Id is definitely a real id6; a slug word like "assess" is not).
    declared_ids = {declared_id for _p, declared_id, _s in records if declared_id}

    # Who OWNS each REAL id6? A file owns an id6 if it DECLARES it in frontmatter (declared_id), or -
    # for the sole-holder test - carries it as a REAL id6 in its own identity slot. Build both.
    declared_owner: Dict[str, str] = {}
    slot_holders: Dict[str, List[str]] = {}
    for path_str, declared_id, slot_id6 in records:
        if declared_id:
            # First declarer wins as the canonical owner (the id6-collision check above already
            # flags a second declarer); we only need one owner name for the message.
            declared_owner.setdefault(declared_id, path_str)
        if slot_id6 and _is_real_id6(slot_id6, declared_ids):
            slot_holders.setdefault(slot_id6, []).append(path_str)

    for path_str, declared_id, slot_id6 in records:
        if slot_id6 is None:
            continue  # legacy / no identity slot -> exempt
        if declared_id is not None:
            # Rule (a): the slot must equal the file's own declared identity. A file that DECLARES
            # an Id asserts a clustered identity, so its slot is compared unconditionally (the slot
            # token need not independently "look like" a real id6 - the declared Id proves intent).
            if slot_id6 != declared_id:
                owner = declared_owner.get(slot_id6)
                owner_str = (
                    f"; id6 {slot_id6} is owned by {owner}"
                    if owner and owner != path_str
                    else ""
                )
                drift.append(
                    _core.Drift(
                        path_str,
                        "check.id6-identity-slot",
                        f"filename identity-slot id6 {slot_id6} != this file's declared Id {declared_id}{owner_str}",
                    )
                )
        else:
            # Rule (b): no declared Id -> the slot id6 must be owned by NO ONE else (neither another
            # file's declared Id nor another file's slot). This is the p7dqwz reuse case. Guard with
            # the real-id6 discriminator so a legacy name whose slug's first word happens to match
            # [0-9a-z]{6} (e.g. "assess"/"agents") is NOT mass-flagged.
            if not _is_real_id6(slot_id6, declared_ids):
                continue
            owner = declared_owner.get(slot_id6)
            other_slot_holders = [
                h for h in slot_holders.get(slot_id6, []) if h != path_str
            ]
            if owner is not None and owner != path_str:
                drift.append(
                    _core.Drift(
                        path_str,
                        "check.id6-identity-slot",
                        f"filename identity-slot id6 {slot_id6} is another file's identity (declared by {owner}); this file declares no Id",
                    )
                )
            elif other_slot_holders:
                drift.append(
                    _core.Drift(
                        path_str,
                        "check.id6-identity-slot",
                        f"filename identity-slot id6 {slot_id6} is also in the identity slot of {other_slot_holders[0]}; this file declares no Id",
                    )
                )
    return drift


_STATUS_META_RE = _re.compile(r"(?m)^- Status:\s*(\S+)\s*$")
_PLANS_PREFIX = ".aw/records/plans/"
_EXECUTED_SEGMENT = "/executed/"


def _git_capture(repo_root: Path, args: List[str]):
    """Run a git command in ``repo_root``; return (returncode, stdout, stderr)."""
    import subprocess

    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _blob_text(repo_root: Path, ref: str, path: str) -> "str | None":
    """Content of ``path`` at ``ref`` (HEAD or the staged index ``:0:``), or None if absent."""
    spec = f":0:{path}" if ref == ":0:" else f"{ref}:{path}"
    rc, out, _err = _git_capture(repo_root, ["show", spec])
    return out if rc == 0 else None


def _status_meta(text: "str | None") -> "str | None":
    """The metadata ``- Status: <value>`` value (lowercased), or None."""
    if not text:
        return None
    m = _STATUS_META_RE.search(text)
    return m.group(1).strip().lower() if m else None


def _is_plan_ipd_path(path: str) -> bool:
    """True for a plan IPD record path under .aw/records/plans/** (a ``.ipd.md``)."""
    p = path.strip().replace("\\", "/")
    return p.startswith(_PLANS_PREFIX) and p.endswith(".ipd.md")


def _has_matching_history_line(text: "str | None", status: str) -> bool:
    """True iff the plan's ``## Workflow history`` carries a tool-authored transition line for
    ``status`` (predicate A, per OQ-01): a ``- <date> <status> (<actor>): ...`` line whose status
    token equals ``status``. Reuses ipd_lint's history parser + ``_HISTORY_LINE_RE`` (no 2nd parser).

    This catches the CARELESS hand-edit (a `- Status:` flip with NO note added). It does NOT catch a
    hand-edit that also writes a plausible line - that limit is accepted (safety net; see the IPD's
    efficacy ceiling). `aw set`/`aw ipd set` always append such a line on every transition."""
    if not text:
        return False
    from agent_workflows import ipd_lint as _lint

    want = status.strip().lower()
    doc = _lint.parse(text)
    for _lineno, line_text in doc.history_lines:
        m = _lint._HISTORY_LINE_RE.match(line_text.strip())
        if m and m.group(1).rstrip(":").lower() == want:
            return True
    return False


def check_status_untooled(repo_root: Path) -> List[_core.Drift]:
    """COMMIT-SCOPED detector for the careless UNTOOLED intermediate status change (proclint 79li67).

    Compares the STAGED index (``:0:``) against HEAD and flags each PLAN whose ``- Status:`` changed in
    THIS commit with NO matching tool-authored ``## Workflow history`` transition line for the new
    status value - the fingerprint of a hand-edited (non-``aw set``) status flip. ``aw set``/``aw ipd
    set`` append ``- <date> <status> (<actor>): <message>`` on every transition (status_set.py:504);
    a staged status change with no such matching line looks hand-edited. Emits ``check.status-untooled``
    naming the plan and the tool fix.

    Commit-scoping is the key simplification: ONLY files changed in the commit are examined, so
    historical records are never touched (NO grandfathering, NO whole-tree scan). ``executed/`` records
    are EXCLUDED (terminal; a move OUT of ``executed/`` is itself a staged change and IS checked - it
    gains a status delta). History-less types (prompts/releases) are never examined (plan IPDs only).

    Fast no-op when no plan status change is staged (e.g. ordinary ``aw check`` on a clean tree).
    """
    repo_root = Path(repo_root)
    rc, out, _err = _git_capture(
        repo_root, ["diff", "--cached", "--name-status", "-M", "--", _PLANS_PREFIX]
    )
    if rc != 0 or not out.strip():
        return []  # fast no-op: nothing staged under plans/
    drift: List[_core.Drift] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        code = parts[0].strip()
        if code.startswith("D"):
            continue  # a pure deletion carries no new status to attribute
        if code.startswith("R") and len(parts) >= 3:
            old_path, new_path = parts[1].strip(), parts[2].strip()
        elif len(parts) >= 2:
            new_path = parts[-1].strip()
            old_path = parts[1].strip() if code in ("C",) else None
            if code in ("M",):
                old_path = new_path  # same path, compare staged vs HEAD content
        else:
            continue
        if not _is_plan_ipd_path(new_path):
            continue
        # Exclude records already terminal in executed/. A move OUT of executed/ has a non-executed
        # new_path (so this guard passes) and IS checked; a plan inside executed/ is skipped.
        if _EXECUTED_SEGMENT in ("/" + new_path):
            continue
        staged_text = _blob_text(repo_root, ":0:", new_path)
        staged_status = _status_meta(staged_text)
        if staged_status is None:
            continue  # no status metadata staged -> nothing to attribute
        head_text = _blob_text(repo_root, "HEAD", old_path) if old_path else None
        head_status = _status_meta(head_text)
        if staged_status == head_status:
            continue  # status did not change in this commit
        # The status changed (or a new plan was added with a status): require a matching
        # tool-authored history line for the NEW status. Missing -> looks hand-edited.
        if not _has_matching_history_line(staged_text, staged_status):
            drift.append(
                _core.Drift(
                    new_path,
                    "check.status-untooled",
                    (
                        f"'- Status:' changed to '{staged_status}' in this commit with no matching "
                        f"tool-authored '## Workflow history' line; apply it via "
                        f"`aw set {staged_status} <id6>` (or `aw ipd set {staged_status} <id6>`) so "
                        f"the transition is attributed"
                    ),
                )
            )
    return drift


_DRAFT_READY_RULE = "check.ipd-draft-ready-to-review"


def check_ipd_draft_ready(
    repo_root: Path, include_untracked: bool = False
) -> List[_core.Drift]:
    """Detect-and-nudge (agentadhere Phase 1 E-03; catalog invariant I-12, assurance Guidance).

    Flag each plan at ``- Status: draft`` whose scaffold authoring placeholders are ALL resolved
    (via ``ipd_authoring.authoring_placeholders_resolved``) with an info-severity
    ``check.ipd-draft-ready-to-review`` finding whose recovery command is
    ``aw ipd set to-review <id6>``. A draft that still contains a scaffold placeholder is SILENT
    (correctly still a stub). This never changes any status: it is a NUDGE, closing the recurring
    miss where a finished draft is never advanced to ``to-review``. Only pending-dir plans are
    considered (a terminal-dir file is not a draft awaiting advance).
    """
    from agent_workflows import ipd_authoring as _authoring

    drift: List[_core.Drift] = []
    for p in _iter_type_files(repo_root, "plans", include_untracked=include_untracked):
        # Only nudge a plan that is actually in a pending lane (not executed/superseded/etc.).
        if "pending" not in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        m = _PLAN_STATUS_RE.search(text)
        if not m or m.group(1).strip().lower() != "draft":
            continue
        if not _authoring.authoring_placeholders_resolved(text):
            continue  # still a stub: stay silent
        mid = _ITEM_ID_RE.search(text)
        id6 = mid.group(1) if mid else p.stem
        recovery = f"aw ipd set to-review {id6}"
        drift.append(
            enrich_drift(
                _core.Drift(
                    str(p),
                    _DRAFT_READY_RULE,
                    "draft IPD has no remaining authoring placeholders; advance it to "
                    "to-review so it enters the review pipeline",
                ),
                observed="Status: draft (authoring complete)",
                required="Status: to-review",
                recovery=recovery,
            )
        )
    return drift


_LIFECYCLE_INVALID_RULE = "check.lifecycle-transition-invalid"
_SCOPE_DRIFT_RULE = "check.scope-drift"


def check_lifecycle_transitions(
    repo_root: Path, include_untracked: bool = False
) -> List[_core.Drift]:
    """Event-derived transition-validity (agentadhere Phase 3 E-01; catalog I-03).

    For each plan, derive its (date, status, actor) event stream from the INLINE history (via
    ``ipd_lifecycle`` reusing ``record_history``'s inline parser - no parallel log) and validate each
    consecutive transition with ``ipd_lifecycle.validate_transition``. A missing-predecessor /
    backwards / unauthorized-terminal transition in the recorded history is flagged. This runs
    ALONGSIDE the authoritative ``- Status:`` read (it validates the recorded events, it does not
    replace the field). HONEST: the events are locally forgeable; this is a validity/consistency
    check, not a tamper-proof authority boundary.
    """
    from agent_workflows import ipd_lifecycle as _life

    drift: List[_core.Drift] = []
    for p in _iter_type_files(repo_root, "plans", include_untracked=include_untracked):
        # Scope to PENDING-lane plans only. Terminal-dir plans (executed/superseded/not-executed/
        # reusable) carry slimmed, annotated, pre-rule histories that legitimately predate this
        # check; retroactively re-litigating them would be a whole-tree false-positive explosion
        # (the same grandfathering principle as the commit-scoped status-untooled/terminal gates).
        if "pending" not in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        events = _life._plan_status_events(text)
        if len(events) < 2:
            continue
        prev = events[0][1]
        for _date, status, actor in events[1:]:
            if status == prev:
                continue  # a same-status re-record (e.g. a duplicate `approved`) is not a transition
            # Only validate a transition whose TARGET is on the forward sequence; an alternate/
            # terminal disposition (superseded/not-executed/parked/reusable) is not a forward step.
            if _life._status_rank(status) < 0:
                prev = status
                continue
            check = _life.validate_transition(prev, status, actor=actor)
            if not check.ok:
                drift.append(
                    enrich_drift(
                        _core.Drift(
                            str(p),
                            _LIFECYCLE_INVALID_RULE,
                            f"recorded lifecycle transition {prev!r} -> {status!r} is invalid: "
                            f"{check.reason}",
                        ),
                        observed=f"{prev} -> {status} (actor {actor})",
                        required="a valid forward transition authored by the correct actor",
                        recovery="correct the plan history via `aw set <status> <id6>` "
                        "(or `aw ipd finalize` for the terminal transition)",
                    )
                )
            prev = status
    return drift


def check_scope_drift(
    repo_root: Path, include_untracked: bool = False
) -> List[_core.Drift]:
    """Declared-file-scope drift (agentadhere Phase 3 E-02; catalog I-01).

    For each plan that has an ACTIVE begin receipt (an in-flight execution with a frozen base HEAD +
    Scope-Paths), compare the paths this execution changed since the frozen base against the plan's
    declared Scope-Paths, REUSING the finalize scope helpers
    (``_paths_changed_by_this_execution``/``_scope_match``/``_frozen_scope_paths``/
    ``_is_implicitly_allowed``) - no forked comparator. A changed path outside the allowlist is
    flagged. A ``grandfathered``/absent Scope-Paths carries no allowlist (empty frozen list), so it
    is advisory-satisfied (never hard-flagged), honoring the sentinel.
    """
    from agent_workflows import ipd_lifecycle as _life

    drift: List[_core.Drift] = []
    for p in _iter_type_files(repo_root, "plans", include_untracked=include_untracked):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        m = _ITEM_ID_RE.search(text)
        if not m:
            continue
        plan_id = m.group(1)
        receipt = _life.read_receipt(repo_root, plan_id)
        if not receipt:
            continue  # no active execution -> nothing to reconcile
        base_head = str(receipt.get("base_head") or "").strip()
        if not base_head or base_head == "unversioned":
            continue
        scope_paths = _life._frozen_scope_paths(text)
        if not scope_paths:
            continue  # grandfathered/absent allowlist: advisory-satisfied, not hard-flagged
        try:
            plan_rel = str(p.resolve().relative_to(Path(repo_root).resolve())).replace(
                "\\", "/"
            )
        except (ValueError, OSError):
            plan_rel = p.name
        changed = _life._paths_changed_by_this_execution(repo_root, base_head)
        out_of_scope = [
            c
            for c in changed
            # `.aw/state/` and `.aw/worktrees/` are gitignored RUNTIME scratch (receipts, journals,
            # per-lane worktrees) - never part of a declared scope; exclude defensively in case a
            # repo has not gitignored them (git status normally elides them).
            if not c.replace("\\", "/").startswith((".aw/state/", ".aw/worktrees/"))
            and not _life._is_implicitly_allowed(c, plan_rel)
            and not any(_life._scope_match(c, pat) for pat in scope_paths)
        ]
        for c in sorted(set(out_of_scope)):
            drift.append(
                enrich_drift(
                    _core.Drift(
                        str(p),
                        _SCOPE_DRIFT_RULE,
                        f"changed path {c!r} is outside the plan's declared Scope-Paths",
                    ),
                    observed=f"changed: {c}",
                    required="a change within the declared Scope-Paths: "
                    + ", ".join(scope_paths),
                    recovery="restrict the change to Scope-Paths, or declare the path in the plan's "
                    "Scope-Paths (then re-`aw ipd begin`), or reconcile it at `aw ipd finalize`",
                )
            )
    return drift


def check_commit_invariants(repo_root: Path) -> List[_core.Drift]:
    """Aggregate the SHARED commit-scoped invariant rules for a pre-commit gate (agentadhere Phase 4,
    IPD diundn E-01; DECISION 17-diundn-D1).

    This COMPOSES the already-shared, commit/receipt-scoped rules - it introduces NO new policy
    logic, so the pre-commit hook that delegates here and ``aw check`` can never diverge (each
    finding still originates from its existing shared rule):

    * ``check.status-untooled`` (``check_status_untooled``) - a staged hand-edited intermediate
      plan status change;
    * ``check.blocking-item-closed-without-gate`` (``check_release_gate_consistency``) - a staged
      release-blocking backlog item closed without a preserved gate;
    * ``check.scope-drift`` (``check_scope_drift``) - for a plan with an ACTIVE begin receipt, a
      changed path outside its declared ``Scope-Paths`` (findings 5.3: enforce the staged-paths-
      within-declared-scope INVARIANT, not the command syntax).

    Each rule is commit/receipt-scoped, so on an ordinary clean commit this is a fast no-op. The
    per-drift ``recovery`` field (from the versioned finding shape) is what the hook TEACHES. HONEST
    LIMIT: this is a LOCAL best-effort gate (``--no-verify`` bypasses it, not cloned by default); the
    portable authority is ``aw check`` + CI.
    """
    drift: List[_core.Drift] = []
    for fn in (
        check_status_untooled,
        check_release_gate_consistency,
        check_scope_drift,
    ):
        try:
            drift.extend(fn(repo_root))
        except Exception:
            # A single rule's failure must not take down the whole pre-commit gate.
            continue
    # Enrich each drift with its registry metadata + recovery so the hook can teach the fix.
    return [enrich_drift(d) if not d.recovery else d for d in drift]


_PUSH_UNAUTHORIZED_RULE = "check.push-unauthorized"

# The env var an operator may set to acknowledge they are performing an authorized push. This is a
# LOCAL convenience acknowledgement ONLY - it is visible to and settable by the agent, so it is NOT
# independent authorization (findings 5.5). The pre-push hook uses it purely to distinguish an
# intended push from an accidental one; the AUTHORITATIVE control is a protected remote branch /
# required CI / brokered credential (the deferred external-authority set).
PUSH_ACK_ENV = "AW_PUSH_AUTHORIZED"


def check_push_authorization(repo_root: Path, ack: bool = False) -> List[_core.Drift]:
    """Pre-push authorization FEEDBACK (agentadhere Phase 4, IPD diundn E-02; catalog I-02).

    Returns a single ``check.push-unauthorized`` drift when ``ack`` is falsey (no local
    acknowledgement of an intended push), so the pre-push hook can PREVENT an accidental push and
    EXPLAIN what real authorization requires. HONEST (findings 5.5): this is LOCAL feedback only - a
    local env acknowledgement is NOT independent authorization (the agent can set it), and the hook
    is bypassable with ``--no-verify`` and not cloned by default. The AUTHORITATIVE boundary is a
    protected remote branch / required CI / brokered credential (the deferred external-authority
    set); this rule NEVER claims to be that boundary.
    """
    if ack:
        return []
    return [
        enrich_drift(
            _core.Drift(
                "<push>",
                _PUSH_UNAUTHORIZED_RULE,
                "a push was attempted with no local authorization acknowledgement; this LOCAL hook "
                "prevents an accidental push. It is NOT an authority boundary (it is bypassable and "
                "not cloned by default); real push authorization is a protected branch / required CI "
                "/ brokered credential",
            ),
            observed="push attempted without acknowledgement",
            required="an intended, externally-authorized push",
            recovery=f"if this push is intended and authorized, set {PUSH_ACK_ENV}=1 to acknowledge "
            "(local convenience only), or push through the authorized path (protected branch / CI)",
        )
    ]


def check_type(
    repo_root: Path,
    record_type: str,
    names_only: bool = False,
    legacy: bool = False,
    _from_all: bool = False,
    include_untracked: bool = False,
) -> List[_core.Drift]:
    """Compose the supported sub-checks for one type into a single Drift list."""
    kinds = SUPPORTED.get(record_type)
    if kinds is None:
        if _from_all:
            return []
        return [
            _core.Drift(
                record_type, "check.type-unsupported", "no checks for this type"
            )
        ]
    drift: List[_core.Drift] = []
    if names_only:
        if "names" in kinds:
            drift.extend(
                check_names(
                    repo_root,
                    record_type,
                    legacy=legacy,
                    include_untracked=include_untracked,
                )
            )
        return drift
    if "names" in kinds:
        drift.extend(
            check_names(
                repo_root,
                record_type,
                legacy=legacy,
                include_untracked=include_untracked,
            )
        )
    if "content" in kinds:
        drift.extend(
            check_content(
                repo_root,
                record_type,
                legacy=legacy,
                include_untracked=include_untracked,
            )
        )
    if "refs" in kinds:
        drift.extend(check_refs(repo_root, record_type))
    return drift


def check_types(
    repo_root: Path,
    types: List[str],
    names_only: bool = False,
    legacy: bool = False,
    collisions: bool = False,
    include_untracked: bool = False,
) -> List[_core.Drift]:
    """Fan out check_type over the given types (or every SUPPORTED type for the ['all'] sentinel),
    concatenating Drift; unsupported types are skipped. The ['all'] sentinel implies
    collisions=True; the cross-tree collision scan is appended exactly ONCE (never per type)."""
    if types == ["all"]:
        target = list(SUPPORTED.keys())
        collisions = True
    else:
        target = types
    drift: List[_core.Drift] = []
    for t in target:
        drift.extend(
            check_type(
                repo_root,
                t,
                names_only=names_only,
                legacy=legacy,
                _from_all=True,
                include_untracked=include_untracked,
            )
        )
    if collisions:
        drift.extend(check_collisions(repo_root, include_untracked=include_untracked))
        # awrelease Order 02: dangling Blocks-Release references are a cross-tree ref check, run once
        # alongside collisions in the full sweep.
        try:
            from agent_workflows import releases as _releases

            drift.extend(_releases.check_blocks_release(repo_root))
            # bklggrad ku93tn: dangling From-Backlog links (a plan pointing at a nonexistent backlog
            # item id6) are the same class of cross-tree ref check, run once in the full sweep.
            drift.extend(_releases.check_from_backlog(repo_root))
        except Exception:
            pass
        # revgate Order 01 (15zvu6): a review file pointing at a nonexistent plan is the same class
        # of cross-tree ref check, run once in the full sweep. ADVISORY (`warning`), so it reports
        # without setting an exit code.
        try:
            drift.extend(check_review_dangling(repo_root))
        except Exception:
            pass
        # proclint 79li67: the COMMIT-SCOPED untooled-status detector rides `aw check`/`aw check all`
        # (a fast no-op when no plan status change is staged), the intermediate-transition sibling of
        # the dulzpy pre-commit gate. It examines only commit-changed plan files (no whole-tree scan).
        try:
            drift.extend(check_status_untooled(repo_root))
        except Exception:
            pass
        # bklggrad orb9zb: release-gate close-legitimacy consistency rules (blocking item closed
        # without a preserved/satisfied gate; a From-Backlog plan whose Blocks-Release != the item's;
        # a still-open blocking item already graduated to a blocking plan). ERROR-severity rules fold
        # into the exit-blocking sweep; the WARN-severity findings are surfaced by attention only.
        try:
            drift.extend(check_release_gate_consistency(repo_root))
        except Exception:
            pass
    return drift


# ======================================================================================
# bklggrad orb9zb: shared close-legitimacy predicate for release-gated backlog items.
#
# ONE predicate consumed by three surfaces so they cannot diverge (the status_untooled_gate
# hook->check_engine pattern): the `aw backlog set done` setter gate (backlog.run_set), the
# `aw check` consistency rules below, and the child-03 opt-in pre-commit hook (which delegates
# here). A release-blocking backlog item (one carrying `- Blocks-Release: <R>`) may only leave the
# active-blocker set via `-> done` when the gate is provably HANDOFF'd, SATISFIED, or DE-GATED.
# ======================================================================================

_ID6_RE = _re.compile(r"\A[0-9a-z]{6}\Z")
_ITEM_ID_RE = _re.compile(r"(?m)^- Id:[ \t]*([0-9a-z]{6})[ \t]*$")
_ITEM_PRIORITY_RE = _re.compile(r"(?m)^- Priority:[ \t]*(\S+)[ \t]*$")
_META_BLOCKS_RELEASE_RE = _re.compile(r"(?m)^- Blocks-Release:[ \t]*(\S+)[ \t]*$")
_META_FROM_BACKLOG_RE = _re.compile(r"(?m)^- From-Backlog:[ \t]*(\S+)[ \t]*$")
_PLAN_STATUS_RE = _re.compile(r"(?m)^- Status:[ \t]*(\S+)[ \t]*$")

_PRIORITY_RANK = {"low": 0, "medium": 1, "high": 2}


def resolve_evidence_artifact(repo_root: Path, evidence: str) -> bool:
    """Shared evidence resolver (bklggrad orb9zb E-03): a resolvable close-evidence citation is a
    SAFE, in-tree, existing artifact path under the repo's records tree (an executed IPD, a records
    file, or another committed doc). Generalizes the specs `_evidence_resolvable` (which is
    executed-IPD-only) so a non-IPD backlog item (README/research/prompt/check work) can be closed
    `done` with a cited artifact. Path-traversal-safe: the resolved path must stay inside the repo.

    NOTE: this is intentionally MORE permissive than the specs predicate (any in-tree records
    artifact, not only executed IPDs). specs' `implementing -> implemented` keeps its own stricter
    predicate unchanged.
    """
    from agent_workflows import attention_contract as _A

    if not evidence or not _A.is_safe_descriptive(evidence):
        return False
    repo_root = Path(repo_root).resolve()
    candidate = (repo_root / evidence).resolve()
    # containment: candidate must be inside the repo root (no ../ escape)
    try:
        candidate.relative_to(repo_root)
    except ValueError:
        return False
    if not candidate.exists():
        return False
    norm = str(candidate).replace("\\", "/")
    # must live under a records/artifact tree (not, e.g., a source file or an arbitrary dotfile).
    # Accept the post-migration `.aw/records/` tree and the legacy `.agents/` records tree (plans,
    # docs, specs, etc.) so an executed IPD under either layout resolves.
    return (".aw/records/" in norm) or ("/.agents/" in norm)


def _iter_plan_ipds(repo_root: Path):
    """Yield (path, text) for every plan IPD under either layout's plans tree, skipping ignored dirs."""
    ignored_dirs = _core.get_ignored_dirs(repo_root)
    for base in (
        Path(repo_root) / ".aw" / "records" / "plans",
        Path(repo_root) / ".agents" / "plans",
    ):
        if not base.is_dir() or _core.is_ignored_path(base, repo_root, ignored_dirs):
            continue
        for p in sorted(base.rglob("*.ipd.md")):
            if p.name in _SKIP_NAMES or _core.is_ignored_path(
                p, repo_root, ignored_dirs
            ):
                continue
            try:
                yield p, p.read_text(encoding="utf-8")
            except OSError:
                continue


def _iter_spec_records(repo_root: Path):
    """Yield (path, text) for every spec under either layout's specs tree, skipping ignored dirs.

    bklgrad Order 01 (v58bvy) E-06: mirrors ``_iter_plan_ipds`` so a spec can participate in the
    ``From-Backlog`` handoff scan. Kept as its own iterator (rather than widening the plan one) so the
    plan-only callers keep their exact current behavior.
    """
    ignored_dirs = _core.get_ignored_dirs(repo_root)
    for base in (
        Path(repo_root) / ".aw" / "records" / "specs",
        Path(repo_root) / ".agents" / "specs",
    ):
        if not base.is_dir() or _core.is_ignored_path(base, repo_root, ignored_dirs):
            continue
        for p in sorted(base.rglob("*.spec.md")):
            if p.name in _SKIP_NAMES or _core.is_ignored_path(
                p, repo_root, ignored_dirs
            ):
                continue
            try:
                yield p, p.read_text(encoding="utf-8")
            except OSError:
                continue


def find_from_backlog_plans(repo_root: Path, item_id6: str) -> List[Tuple[Path, str]]:
    """Every plan whose `- From-Backlog:` names `item_id6`. Returns [(path, blocks_release_or_'')]."""
    out: List[Tuple[Path, str]] = []
    for p, text in _iter_plan_ipds(repo_root):
        mfb = _META_FROM_BACKLOG_RE.search(text)
        if mfb and mfb.group(1) == item_id6:
            mbr = _META_BLOCKS_RELEASE_RE.search(text)
            out.append((p, mbr.group(1) if mbr else ""))
    return out


def find_from_backlog_specs(repo_root: Path, item_id6: str) -> List[Tuple[Path, str]]:
    """Every spec whose `- From-Backlog:` names `item_id6`. Returns [(path, blocks_release_or_'')]."""
    out: List[Tuple[Path, str]] = []
    for p, text in _iter_spec_records(repo_root):
        mfb = _META_FROM_BACKLOG_RE.search(text)
        if mfb and mfb.group(1) == item_id6:
            mbr = _META_BLOCKS_RELEASE_RE.search(text)
            out.append((p, mbr.group(1) if mbr else ""))
    return out


def find_from_backlog_artifacts(
    repo_root: Path, item_id6: str
) -> List[Tuple[Path, str]]:
    """Every PLAN or SPEC whose `- From-Backlog:` names ``item_id6``.

    bklgrad Order 01 (v58bvy) E-06: the HANDOFF route previously scanned plan IPDs ONLY, so a
    spec-first graduation (a spec carrying `From-Backlog` plus the SAME `Blocks-Release`) was invisible
    and its backlog item could never legitimately close. A spec preserves the gate exactly as well as a
    plan does, so both are accepted here. Plans are yielded first so an existing plan-based handoff
    keeps producing the identical verdict it did before.
    """
    return list(find_from_backlog_plans(repo_root, item_id6)) + list(
        find_from_backlog_specs(repo_root, item_id6)
    )


class CloseVerdict(NamedTuple):
    """Structured verdict from `evaluate_blocking_close`.

    legitimate: may this transition proceed?
    severity:   'ok' (unchecked/allowed) | 'warn' (allowed, advisory) | 'error' (fail-closed).
    reason:     machine/human explanation.
    fixes:      the concrete remedies to offer on an error.
    path:       HANDOFF|SATISFIED|DE-GATED|None (which legitimacy path matched).
    """

    legitimate: bool
    severity: str
    reason: str
    fixes: Tuple[str, ...]
    path: Optional[str]


def evaluate_blocking_close(
    repo_root: Path,
    item_path: Path,
    target_status: str,
    evidence: Optional[str] = None,
    *,
    item_text: Optional[str] = None,
    prior_priority: Optional[str] = None,
) -> CloseVerdict:
    """The shared close-legitimacy predicate for a release-gated backlog item (bklggrad orb9zb).

    Reads the item's POST-mutation state (pass `item_text` to evaluate an in-memory item, e.g. after
    a same-call `--blocks-release -`/`--evidence`; else the file is read). Only items that carry a
    `- Blocks-Release:` line are gated; everything else returns legitimate/ok (unchecked).

    Transitions:
      -> done   : LEGITIMATE iff one of
                    HANDOFF  - a plan carrying `From-Backlog: <this id6>` AND the same `Blocks-Release`
                    SATISFIED- a resolvable `evidence` artifact citation
                    DE-GATED - the (post-mutation) item no longer carries Blocks-Release
                  else ILLEGITIMATE (severity error, fail-closed).
      -> parked : WARN (allowed): the gate is hidden from the active view; hint to de-gate.
      priority-demote of a blocker (prior_priority outranks the new one): WARN (allowed).
      everything else: ok (unchecked).
    """
    repo_root = Path(repo_root)
    text = (
        item_text
        if item_text is not None
        else Path(item_path).read_text(encoding="utf-8")
    )
    mid = _ITEM_ID_RE.search(text)
    item_id6 = mid.group(1) if mid else None
    mbr = _META_BLOCKS_RELEASE_RE.search(text)
    blocks_release = mbr.group(1) if mbr else None

    if target_status == "done":
        # DE-GATED: the post-mutation item carries no Blocks-Release -> nothing to preserve.
        if not blocks_release:
            return CloseVerdict(
                True, "ok", "no release gate to preserve", (), "DE-GATED"
            )
        # HANDOFF: a From-Backlog PLAN OR SPEC with the SAME Blocks-Release inherited the gate.
        # bklgrad Order 01 (v58bvy) E-06: this scanned plans only, which made a spec-first graduation
        # unclosable by construction even though a spec preserves the gate identically.
        if item_id6:
            for _p, carrier_br in find_from_backlog_artifacts(repo_root, item_id6):
                if carrier_br == blocks_release:
                    return CloseVerdict(
                        True,
                        "ok",
                        f"gate {blocks_release!r} handed off to a From-Backlog plan or spec",
                        (),
                        "HANDOFF",
                    )
        # SATISFIED: a resolvable evidence artifact citation.
        if evidence and resolve_evidence_artifact(repo_root, evidence):
            return CloseVerdict(
                True,
                "ok",
                f"gate {blocks_release!r} satisfied by resolvable evidence {evidence!r}",
                (),
                "SATISFIED",
            )
        # else fail-closed with the three fixes.
        return CloseVerdict(
            False,
            "error",
            (
                f"backlog item carries Blocks-Release {blocks_release!r}; closing it `done` would "
                f"silently drop that release gate"
            ),
            (
                "hand the gate to a plan: add `- From-Backlog: <this id6>` (and the same "
                "`- Blocks-Release`) to a plan via `aw ipd set ... --from-backlog <id6>`",
                "cite satisfying evidence: `aw backlog set done <item> --evidence <in-tree artifact path>`",
                "explicitly release the gate first: `aw backlog set done <item> --blocks-release -`",
            ),
            None,
        )

    # bklgrad Order 01 (v58bvy) E-03: `graduated` is EXPLICITLY legitimate for a release-gated item and
    # drops nothing: the item keeps its `Blocks-Release` field, and `aw attention` maps `graduated` to
    # `active` (not `done`), so it stays in the outstanding release-blocker set. This is stated as its
    # own branch rather than left to the trailing "unchecked" fall-through so it cannot be mistaken for
    # an oversight. Critically, `graduated` is NOT a substitute for `done`: reaching `done` still
    # requires HANDOFF / SATISFIED / DE-GATED above, so a release can never ship with its blockers
    # merely graduated.
    if target_status == "graduated" and blocks_release:
        return CloseVerdict(
            True,
            "ok",
            (
                f"graduated preserves gate {blocks_release!r} (item stays a release blocker; "
                f"`done` still requires handoff, evidence, or explicit de-gating)"
            ),
            (),
            None,
        )

    if target_status == "parked" and blocks_release:
        return CloseVerdict(
            True,
            "warn",
            (
                f"parking a release-blocking item hides gate {blocks_release!r} from the active "
                f"release-blocker view; de-gate (`--blocks-release -`) if it truly no longer blocks"
            ),
            (),
            None,
        )

    if (
        blocks_release
        and prior_priority is not None
        and target_status not in ("done", "parked")
    ):
        mp = _ITEM_PRIORITY_RE.search(text)
        new_priority = mp.group(1) if mp else None
        pr = _PRIORITY_RANK.get((prior_priority or "").lower())
        nr = _PRIORITY_RANK.get((new_priority or "").lower())
        if pr is not None and nr is not None and nr < pr:
            return CloseVerdict(
                True,
                "warn",
                (
                    f"demoting the priority of a release-blocking item ({prior_priority} -> "
                    f"{new_priority}) may contradict its Blocks-Release {blocks_release!r}"
                ),
                (),
                None,
            )

    return CloseVerdict(True, "ok", "unchecked transition", (), None)


def _backlog_done_dirs(repo_root: Path):
    for root_rel in (".aw/records/backlog", ".agents/backlog"):
        d = Path(repo_root) / root_rel / "done"
        if d.is_dir():
            yield d


_BACKLOG_DONE_RE = _re.compile(r"(?:^|/)backlog/done/[^/]+\.md$")


def _staged_backlog_done_items(repo_root: Path) -> List[str]:
    """Repo-relative paths of backlog items UNDER a `backlog/done/` dir that are added/modified/renamed
    in the STAGED index of the current commit (commit-scoped, like check_status_untooled). Empty when
    nothing under backlog/ is staged (fast no-op on an ordinary `aw check`)."""
    rc, out, _err = _git_capture(
        repo_root,
        [
            "diff",
            "--cached",
            "--name-status",
            "-M",
            "--",
            ".aw/records/backlog",
            ".agents/backlog",
        ],
    )
    if rc != 0 or not out.strip():
        return []
    paths: List[str] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        code = parts[0].strip()
        if code.startswith("D"):
            continue  # a deletion carries no new done state
        new_path = parts[-1].strip()
        if (
            _BACKLOG_DONE_RE.search(new_path.replace("\\", "/"))
            and new_path not in paths
        ):
            paths.append(new_path)
    return paths


def check_release_gate_consistency(repo_root: Path) -> List[_core.Drift]:
    """bklggrad orb9zb E-05: cross-tree consistency rules reusing `evaluate_blocking_close`.

    ERROR-severity (fold into the exit-blocking sweep):
      check.blocking-item-closed-without-gate - an already-`done` blocking item whose gate was not
        preserved/satisfied (the backstop for a hand-edit bypass of the setter gate).
      check.from-backlog-gate-mismatch - a `From-Backlog` plan whose `Blocks-Release` differs from
        the backlog item's Blocks-Release (a broken handoff).

    The WARN-severity `check.orphaned-live-blocker` (a still-open blocking item already graduated to
    a blocking plan) is surfaced via `release_gate_warnings`/attention, NOT here (it must not set the
    exit code).
    """
    repo_root = Path(repo_root)
    drift: List[_core.Drift] = []

    # Rule 1: the hand-edit-bypass backstop. COMMIT-SCOPED (the check_status_untooled philosophy):
    # only a backlog item whose close-to-`done` is STAGED in THIS commit is examined, so historical
    # `done/` items closed before this guard existed are grandfathered (never retroactively flagged).
    # A staged done+blocking item with no legitimate gate is the fingerprint of a hand-edit that
    # bypassed the `aw backlog set done` gate. Fast no-op when nothing under backlog/ is staged.
    for staged_path in _staged_backlog_done_items(repo_root):
        staged_text = _blob_text(repo_root, ":0:", staged_path)
        if not staged_text or not _META_BLOCKS_RELEASE_RE.search(staged_text):
            continue
        if _status_meta(staged_text) != "done":
            continue
        verdict = evaluate_blocking_close(
            repo_root, repo_root / staged_path, "done", item_text=staged_text
        )
        if not verdict.legitimate and verdict.severity == "error":
            drift.append(
                _core.Drift(
                    staged_path,
                    "check.blocking-item-closed-without-gate",
                    (
                        "a done backlog item staged in this commit still carries Blocks-Release with "
                        "no handoff (From-Backlog plan), resolvable evidence, or de-gate; close it "
                        "via `aw backlog set done` (which enforces the gate) rather than by hand"
                    ),
                )
            )

    # Rule 2: From-Backlog plan whose Blocks-Release differs from the backlog item's.
    from agent_workflows import backlog as _backlog

    item_gate: Dict[str, Tuple[str, str]] = {}  # id6 -> (blocks_release, item_path)
    for f in _backlog._iter_items(repo_root):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        mid = _ITEM_ID_RE.search(text)
        mbr = _META_BLOCKS_RELEASE_RE.search(text)
        if mid and mbr:
            item_gate[mid.group(1)] = (mbr.group(1), str(f))
    # bklgrad Order 01 (v58bvy) E-07: scan PLANS AND SPECS. A spec is now an accepted HANDOFF gate
    # carrier (E-06), so the consistency rule must cover it too or the checker and the setter diverge:
    # a spec could carry a mismatched gate, be accepted as a carrier by nothing, and never be flagged.
    for kind, iterator in (("plan", _iter_plan_ipds), ("spec", _iter_spec_records)):
        for p, text in iterator(repo_root):
            mfb = _META_FROM_BACKLOG_RE.search(text)
            if not mfb:
                continue
            target_id6 = mfb.group(1)
            if target_id6 not in item_gate:
                continue  # dangling From-Backlog is check.from-backlog-dangling's job (ku93tn)
            item_br, _item_path = item_gate[target_id6]
            mbr = _META_BLOCKS_RELEASE_RE.search(text)
            carrier_br = mbr.group(1) if mbr else None
            if carrier_br != item_br:
                drift.append(
                    _core.Drift(
                        str(p),
                        "check.from-backlog-gate-mismatch",
                        (
                            f"From-Backlog {kind}'s Blocks-Release {carrier_br!r} does not match "
                            f"backlog item {target_id6}'s Blocks-Release {item_br!r}"
                        ),
                    )
                )
    return drift


def release_gate_warnings(repo_root: Path) -> List[_core.Drift]:
    """bklggrad orb9zb E-06: WARN-severity release-gate findings for the attention human view. These
    NEVER set an exit code (returned separately from the exit-blocking `check_release_gate_consistency`).

      check.orphaned-live-blocker - a still-`open` blocking backlog item that has ALREADY been
        graduated to a blocking plan (a From-Backlog plan with the same Blocks-Release); it should
        probably be closed `done` via the handoff path.
    """
    repo_root = Path(repo_root)
    from agent_workflows import backlog as _backlog

    warnings: List[_core.Drift] = []
    for f in _backlog._iter_items(repo_root):
        if f.parent.name != "open":
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        mbr = _META_BLOCKS_RELEASE_RE.search(text)
        mid = _ITEM_ID_RE.search(text)
        if not mbr or not mid:
            continue
        for _p, plan_br in find_from_backlog_plans(repo_root, mid.group(1)):
            if plan_br == mbr.group(1):
                _id6 = mid.group(1)
                warnings.append(
                    _core.Drift(
                        str(f),
                        "check.orphaned-live-blocker",
                        (
                            "an open release-blocking item is already graduated to a From-Backlog "
                            "plan; close it `done` (the gate is preserved via handoff).\n"
                            f"    Fix: aw backlog set done {_id6}"
                        ),
                    )
                )
                break
    return warnings


# ======================================================================================
# ipddeps Order ovbnyq (spec 25kzda 2.9-2.11): the ONE shared cross-IPD dependency evaluator.
#
# Parses each `Item-Dependencies` statement once (child 01's `parse_item_dependencies`), resolves
# every typed id6 edge once against a repo identity index, builds ONE directed IPD->IPD graph,
# detects cycles, and emits the `check.ipd-dependency-*` rule family with phase/grandfather severity.
# Consumed by `aw check` (the plans-type content path) AND phased `aw ipd lint` AND (child 03) the
# hook - never duplicated. `aw check` uses phase="check" (post-cutover mandatoriness applies by the
# plan's own Date vs the cutover date; pre-cutover plans are grandfathered/advisory, so the current
# corpus is never mass-failed).
# ======================================================================================

_ITEM_DEPENDENCIES_RE = _re.compile(r"(?m)^- Item-Dependencies:[ \t]*(.*?)[ \t]*$")
_DATE_LINE_RE = _re.compile(r"(?m)^- Date:[ \t]*(\S+)[ \t]*$")

# Phases where a missing/unresolved/malformed/dangling/cyclic statement is BLOCKING (error). At the
# always-on `check`/`author` phase, a pre-cutover plan's missing statement is only an advisory
# (grandfathered) and an `unresolved` scaffold sentinel is advisory; later phases block.
_DEP_BLOCKING_PHASES = frozenset(
    ("review-finalize", "review-readiness", "pre-execution", "pre-transition")
)


class _DepIndex(NamedTuple):
    # id6 -> list of (record_type, status, path_str) owners (len>1 => ambiguous).
    owners: Dict[str, List[Tuple[str, Optional[str], str]]]


# revgate Order 03 (7nkcgp) E-03. An `executed:` edge whose target resolves but carries recorded
# unresolved gating findings. See the RULE_REGISTRY entry for why reuse of `dangling`/`ambiguous` was
# evaluated and rejected (they are identity verdicts; this is a target-quality verdict).
_REVIEW_DEP_BLOCKED_RULE = "check.ipd-dependency-findings-blocked"


def _findings_blocks_for(repo_root: Path, dep_id6: str, threshold: Optional[str]):
    """The shared predicate's verdict for one dependency target, or `()` when it does not block.

    Delegates ENTIRELY to ``review_findings.plan_gating_blocks``, the SAME function both host runners
    consume, so `aw check` and a live run cannot disagree about what blocks. This function
    re-implements no severity comparison, holds no threshold default, and never raises.
    """
    try:
        from agent_workflows import review_findings as _rf

        return _rf.plan_gating_blocks(repo_root, dep_id6, threshold)
    except Exception:
        return ()


def build_dependency_index(repo_root: Path) -> _DepIndex:
    """Build the repo identity index for dependency resolution: id6 -> [(record_type,status,path)].

    Uses the unified artifact inventory (plans/specs/backlog + more) so an edge's typed id6 can be
    resolved and a multi-owner id6 (ambiguous) detected. Lazy import avoids any import cycle.
    """
    owners: Dict[str, List[Tuple[str, Optional[str], str]]] = {}
    try:
        from agent_workflows import status_set as _ss

        records = _ss.inventory_all_artifacts(Path(repo_root))
    except Exception:
        return _DepIndex(owners)
    for rec in records:
        rid = getattr(rec, "id6", None)
        if not rid:
            continue
        owners.setdefault(rid, []).append((rec.record_type, rec.status, str(rec.path)))
    return _DepIndex(owners)


def _resolve_edge(
    edge: "_S.ItemDependency", index: _DepIndex
) -> Tuple[str, Optional[str]]:
    """Resolve one edge against the index. Returns (verdict, detail):
    verdict in {"ok","dangling","ambiguous"}. An `executed:`/state:ipd:.../exists:ipd: edge must
    resolve to a plans record; exists:spec:/state:spec: to a specs record; backlog to backlog."""
    want_rt = _S.ITEM_DEP_TYPE_TO_RECORD_TYPE.get(edge.target_type)
    hits = index.owners.get(edge.id6, [])
    typed = [h for h in hits if want_rt is None or h[0] == want_rt]
    if not typed:
        return "dangling", (
            f"{edge.canonical()}: no {edge.target_type} artifact has id6 {edge.id6}"
        )
    if len(typed) > 1:
        return "ambiguous", (
            f"{edge.canonical()}: id6 {edge.id6} matches multiple {edge.target_type} "
            f"artifacts ({', '.join(h[2] for h in typed)})"
        )
    return "ok", None


def _plan_date(text: str) -> Optional[str]:
    m = _DATE_LINE_RE.search(text)
    return m.group(1).strip() if m else None


def evaluate_ipd_dependencies(
    repo_root: Path,
    *,
    phase: str = "check",
    plans: Optional[List[Tuple[Path, str]]] = None,
    overlay: Optional[Dict[str, str]] = None,
) -> List[_core.Drift]:
    """The shared cross-IPD dependency evaluator. Returns Drift findings (deterministic order).

    `phase` selects severity: "check"/"author" grandfather a pre-cutover missing statement (advisory)
    and treat `unresolved` as advisory; the blocking phases make missing/unresolved/malformed/
    dangling/ambiguous/cycle errors. When `plans` is given (a single-plan lint), only those plan(s)
    are evaluated for per-statement findings, but the cycle graph is still built from the whole repo
    so an inter-plan cycle involving the target is caught.

    `overlay` (path_str -> text) is the STAGED-OVERLAY entry point (ipddeps mp88bl): the commit-scoped
    pre-commit hook passes the staged blob content of each staged `.ipd.md`, which OVERRIDES the
    on-disk text for BOTH the whole-repo cycle graph and the per-statement checks, so a staged edge
    that introduces/participates in a cycle is caught. Paths in `overlay` not already on disk are
    added to the graph (a newly-staged plan). Pure w.r.t. the overlay; no disk writes.
    """
    repo_root = Path(repo_root)
    from agent_workflows import config as _config

    cutover_date = _config.dependency_cutover_date(repo_root)
    index = build_dependency_index(repo_root)
    # revgate Order 03 (7nkcgp) E-03: resolve the findings threshold ONCE per evaluation rather than
    # per edge. `off` short-circuits the new check entirely inside the shared predicate.
    try:
        _findings_thr: Optional[str] = _config.findings_gate_threshold(repo_root)
    except Exception:
        _findings_thr = None

    # Gather every plan's declared Id + Item-Dependencies value (whole repo, for the graph). The
    # staged overlay (if any) overrides on-disk text and contributes any newly-staged plan path.
    overlay = dict(overlay or {})
    disk_plans: List[Tuple[Path, str]] = list(_iter_plan_ipds(repo_root))
    merged: Dict[str, str] = {str(p): text for p, text in disk_plans}
    for ov_ps, ov_text in overlay.items():
        merged[ov_ps] = ov_text
    all_plans: List[Tuple[Path, str]] = [
        (Path(ps), text) for ps, text in merged.items()
    ]
    own_id: Dict[str, str] = {}  # path_str -> declared id6
    dep_value: Dict[
        str, Optional[str]
    ] = {}  # path_str -> raw Item-Dependencies value (or None)
    plan_text: Dict[str, str] = {}
    for p, text in all_plans:
        ps = str(p)
        plan_text[ps] = text
        mid = _ID_LINE_RE.search(text)
        if mid:
            own_id[ps] = mid.group(1)
        mdep = _ITEM_DEPENDENCIES_RE.search(text)
        dep_value[ps] = mdep.group(1).strip() if mdep else None

    # Build the IPD->IPD edge graph (by owner id6) from ALL plans for cycle detection.
    edges_by_plan: Dict[str, List[str]] = {}
    for ps, oid in own_id.items():
        raw = dep_value.get(ps)
        if not raw:
            continue
        edges, _ready, err = _S.parse_item_dependencies(raw)
        if err:
            continue
        ipd_targets = [e.id6 for e in edges if e.target_type == "ipd"]
        if oid not in edges_by_plan:
            edges_by_plan[oid] = []
        edges_by_plan[oid].extend(ipd_targets)

    cycles = _S.item_dependency_cycles(edges_by_plan)
    # Map an owner id6 back to a path for cycle reporting.
    id_to_path: Dict[str, str] = {oid: ps for ps, oid in own_id.items()}

    drift: List[_core.Drift] = []
    blocking = phase in _DEP_BLOCKING_PHASES

    # Per-statement findings for the target set (default: all plans).
    target_plans = plans if plans is not None else all_plans
    for p, text in sorted(target_plans, key=lambda pt: str(pt[0])):
        ps = str(p)
        raw = dep_value.get(ps, None)
        if raw is None:
            raw = None
            mdep = _ITEM_DEPENDENCIES_RE.search(text)
            raw = mdep.group(1).strip() if mdep else None
        oid = own_id.get(ps)
        # (1) missing statement - CUTOVER-GATED: a grandfathered (pre-cutover / no-cutover) plan is
        # NEVER flagged for a missing statement, at ANY phase, so the existing corpus is not
        # mass-failed. Only a POST-cutover plan missing the field is a finding (error).
        if raw is None:
            if not _is_grandfathered_plan(text, cutover_date):
                drift.append(
                    _core.Drift(
                        ps,
                        _S.RULE_IPD_DEP_MISSING,
                        "IPD has no `- Item-Dependencies:` statement; add one via "
                        "`aw ipd dependencies set <id6> none|<edge...>` "
                        "(scaffold emits `unresolved`)",
                    )
                )
            continue
        # (2) unresolved sentinel
        if raw == _S.ITEM_DEPENDENCIES_UNRESOLVED:
            if blocking:
                drift.append(
                    _core.Drift(
                        ps,
                        _S.RULE_IPD_DEP_UNRESOLVED,
                        "Item-Dependencies is still the `unresolved` scaffold sentinel; "
                        "resolve it with `aw ipd dependencies set <id6> none|<edge...>`",
                    )
                )
            continue
        # (3) malformed
        edges, _ready, err = _S.parse_item_dependencies(raw)
        if err:
            drift.append(
                _core.Drift(
                    ps,
                    _S.RULE_IPD_DEP_MALFORMED,
                    f"malformed Item-Dependencies: {err}",
                )
            )
            continue
        # self-edge (a plan depending on its own id6) is malformed - the parser cannot see the
        # owner, so detect it here.
        if oid and any(e.id6 == oid for e in edges):
            drift.append(
                _core.Drift(
                    ps,
                    _S.RULE_IPD_DEP_MALFORMED,
                    f"malformed Item-Dependencies: self-dependency on own id6 {oid}",
                )
            )
            continue
        # (4)/(5) resolve each edge -> dangling / ambiguous
        for e in edges:
            verdict, detail = _resolve_edge(e, index)
            if verdict == "dangling":
                drift.append(_core.Drift(ps, _S.RULE_IPD_DEP_DANGLING, detail or ""))
            elif verdict == "ambiguous":
                drift.append(_core.Drift(ps, _S.RULE_IPD_DEP_AMBIGUOUS, detail or ""))
            elif verdict == "ok":
                # (7) revgate Order 03 (7nkcgp) E-03: the edge's identity is fine, but an `executed:`
                # edge additionally requires the target to be sound. Spec 25kzda Section 2.9 is
                # explicit that an `executed:` edge is satisfied only by "verified terminal execution,
                # not merely a file whose status text says `executed`", so an unresolved gating finding
                # on the target is a legitimate non-satisfaction rather than a novel restriction.
                #
                # Scoped to `executed:` DELIBERATELY: only that edge kind asserts work was completed
                # and verified. `exists:`/`state:` are structural checks and keep their semantics.
                if e.kind == "executed":
                    for blk in _findings_blocks_for(repo_root, e.id6, _findings_thr):
                        drift.append(
                            _core.Drift(
                                ps,
                                _REVIEW_DEP_BLOCKED_RULE,
                                (
                                    "dependency `{0}` resolves but does not satisfy the edge: "
                                    "{1} (recorded in {2})".format(
                                        e.canonical(),
                                        blk.describe(),
                                        Path(blk.review_path).name,
                                    )
                                ),
                            )
                        )

    # (6) cycles - report once per cycle, located at the (sorted-first) member's path if known.
    target_ids = {own_id.get(str(p)) for p, _t in target_plans}
    for cyc in cycles:
        # When evaluating a subset (lint of one plan), only report a cycle that involves a target.
        if plans is not None and not (set(cyc) & target_ids):
            continue
        member_paths = [id_to_path.get(c, c) for c in cyc]
        loc = sorted(pp for pp in member_paths if pp in plan_text) or [member_paths[0]]
        drift.append(
            _core.Drift(
                loc[0],
                _S.RULE_IPD_DEP_CYCLE,
                "cross-IPD dependency cycle: " + " -> ".join(cyc),
            )
        )

    return drift


def _is_grandfathered_plan(text: str, cutover_date: Optional[str]) -> bool:
    """A plan is grandfathered (missing-statement is advisory, not error) when there is no cutover
    in effect, or the plan's `- Date:` predates the cutover date. Fail-open: unparseable -> True."""
    if cutover_date is None:
        return True
    pdate = _plan_date(text)
    if not pdate:
        return True
    return pdate < cutover_date


def check_ipd_dependencies(repo_root: Path) -> List[_core.Drift]:
    """Repo-wide cross-IPD dependency check for `aw check` (phase="check"). Mirrors the
    `check_from_backlog` scan shape; wired into the plans-type content path so BOTH `aw check plans`
    and `aw check all` surface it exactly once (never double-reported)."""
    return evaluate_ipd_dependencies(repo_root, phase="check")


_PRIORITY_INVALID_RULE = "check.priority-invalid"


def check_plan_priority(
    repo_root: Path, include_untracked: bool = False
) -> List[_core.Drift]:
    """Validate the recognized-but-optional `- Priority:` enum on each plan (xprio 1b45el E-02).

    Priority is OPTIONAL on an IPD (schema RECOGNIZES it; the enum value check lives HERE, in
    `aw check`, per the documented convention). A plan carrying an out-of-vocab `- Priority:` value
    is flagged `check.priority-invalid`; a plan with a valid value (or NO Priority at all) is silent.
    The vocabulary is the SHARED `backlog.PRIORITIES` (imported, never forked). This is a plain
    metadata-enum check on the plan's OWN field (precedent: backlog.validate_item's priority guard),
    NOT a cross-tree dangling/reference check, so it runs in the plans-type content path (reached by
    both `aw check plans` and the `aw check all` fan-out, exactly once).
    """
    from agent_workflows import backlog as _backlog

    drift: List[_core.Drift] = []
    for p in _iter_type_files(repo_root, "plans", include_untracked=include_untracked):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        m = _ITEM_PRIORITY_RE.search(text)
        if not m:
            continue  # absent Priority is fine (optional)
        value = m.group(1).strip()
        if value in _backlog.PRIORITIES:
            continue
        mid = _ITEM_ID_RE.search(text)
        id6 = mid.group(1) if mid else p.stem
        drift.append(
            enrich_drift(
                _core.Drift(
                    str(p),
                    _PRIORITY_INVALID_RULE,
                    f"priority not in {sorted(_backlog.PRIORITIES)}: {value!r}",
                ),
                observed=f"Priority: {value}",
                required=f"one of {sorted(_backlog.PRIORITIES)} (or omit Priority)",
                recovery=f"aw ipd set {id6} --priority <low|medium|high>  (or --priority - to clear)",
            )
        )
    return drift


_REVIEW_DANGLING_RULE = "check.review-dangling"
_REVIEW_PLAN_ID_RE = _re.compile(r"(?m)^-[ \t]*Plan-Id:[ \t]*([0-9a-z]{6})[ \t]*$")


def check_review_dangling(repo_root: Path) -> List[_core.Drift]:
    """Flag a `.review.md` whose `- Plan-Id:` does not resolve to any plan (revgate 15zvu6 E-06).

    The cross-tree-reference sibling of `check.from-backlog-dangling`, but ADVISORY (`warning`): a
    review whose plan was deleted or superseded is untidy, not dangerous. It therefore rides the same
    full-sweep seam as the other dangling scans while never setting an exit code.

    Discovery goes through `review_findings.iter_review_files`, which resolves the tree via the ONE
    record-path authority (`record_producers.resolve_record_path`, registered by E-09). This function
    deliberately contains NO `.aw/records/reviews` path literal: a second hardcoded path is exactly
    the duplicate mechanism the house rules forbid.
    """
    drift: List[_core.Drift] = []
    try:
        from agent_workflows import review_findings as _rf
    except Exception:
        return drift

    known: set = set()
    for _p, text in _iter_plan_ipds(repo_root):
        mid = _ITEM_ID_RE.search(text)
        if mid:
            known.add(mid.group(1))

    ignored_dirs = _core.get_ignored_dirs(repo_root)
    for path in _rf.iter_review_files(repo_root):
        if _core.is_ignored_path(path, repo_root, ignored_dirs):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        m = _REVIEW_PLAN_ID_RE.search(text)
        if m is None:
            continue  # a missing/malformed Plan-Id is the parser's diagnostic, not this rule's
        plan_id = m.group(1)
        if plan_id in known:
            continue
        drift.append(
            enrich_drift(
                _core.Drift(
                    str(path),
                    _REVIEW_DANGLING_RULE,
                    f"Plan-Id {plan_id!r} does not resolve to any plan",
                ),
                observed=f"Plan-Id: {plan_id}",
                required="a Plan-Id matching an existing plan's `- Id:`",
                recovery=(
                    "correct the Plan-Id to the reviewed plan's id6, or retire the review "
                    "alongside the plan it reviewed"
                ),
            )
        )
    return drift


# --------------------------------------------------------------------------------------
# revgate Order 02 (plqjt7): unfixed findings at or above the threshold must be escalated.
#
# WHY THERE IS NO SECOND, DIRECT SEVERITY GATE HERE (E-03; maintainer decision 2026-08-29).
#
# This rule does NOT block on the finding. It blocks on the ABSENCE OF AN ESCALATION, and the
# escalated artifact - a `Blocking: yes` open question - is then caught by the PRE-EXISTING
# pre-execution gate in `ipd_lint.check_checkpoint` (`ipd_lint.py:681-693`, "unresolved blocking
# question at pre-execution"). One gate, reused, instead of two gates to keep in agreement.
#
# THE EVIDENCE FOR THAT REUSE, STATED HONESTLY. Measured over this repo's executed plans: 28 of 28
# `Blocking: yes` open questions are `resolved`, so no executed plan carries an unresolved blocking
# question. That is a CONSISTENCY FACT, NOT A CATCH RATE, and it must not be written up as one, for
# two reasons:
#   (a) part of it is TAUTOLOGICAL. `Blocking: yes` combined with `deferred` is ALREADY a structural
#       error at every phase via a DIFFERENT rule (`ipd_schema.open_question_error`,
#       `ipd_schema.py:1242-1243`), so `resolved` is the only legal terminal state a blocking question
#       can reach. The corpus could hardly show anything else.
#   (b) nothing in the corpus records whether the checkpoint gate EVER ACTUALLY STOPPED A RUN. Its
#       true catch rate is UNMEASURED, not perfect.
# The reuse is still the right design (one mechanism, already wired into `begin`/`finalize`), but its
# justification is "fewer moving parts", not "proven infallible".
#
# DO NOT "SIMPLIFY" THIS BY ADDING THE DIRECT SEVERITY GATE. A second gate that blocks on the finding
# itself was CONSIDERED AND DELIBERATELY REJECTED (maintainer preference for fewer pieces of code,
# 2026-08-29), not merely left undone. The known trade-off is recorded in the plan: this design blocks
# one step removed from the finding, so its weakness is a reviewer who records a finding and omits the
# escalation - which is precisely what THIS rule makes a deterministic error. If you believe the
# direct gate is needed anyway, RAISE IT rather than adding it silently.
# --------------------------------------------------------------------------------------

_REVIEW_UNESCALATED_RULE = "check.review-finding-unescalated"

#: Finding decisions that leave a finding UNFIXED and therefore require escalation.
#:
#: `replan` is deliberately EXCLUDED, matching the approved plan's E-01 wording ("whose decision is
#: `open` or `deferred`"). A `REPLAN` finding says the plan must be rewritten wholesale, which is a
#: different remedy than "execute it but answer this first"; a replanned plan is not heading for
#: execution in its current form. Named here as an explicit set so the choice is visible rather than
#: buried in a conditional.
_UNFIXED_DECISIONS = ("open", "deferred")


def _blocking_escalated_finding_ids(open_questions) -> set:
    """The finding ids escalated by a `Blocking: yes` open question.

    Reads the TYPED `- Finding:` subfield (the E-08 convention), NOT the free-text rationale prose.
    A substring search over prose would be both spoofable (any mention of "F-3" would satisfy the
    rule) and brittle, so the match is against a declared field only.

    One question may name SEVERAL findings (`- Finding: F-3, F-5`), which is why the value is split
    on commas and whitespace: a reviewer raising one blocking question that covers two related
    findings should not have to file it twice.

    The open question's own `Status` is deliberately NOT consulted, matching the approved plan's E-01
    wording ("has NO open question with `Blocking: yes` naming that finding id"). The honest residual:
    a reviewer who escalates, then marks the QUESTION `resolved` while leaving the FINDING `open`,
    satisfies this rule and is not blocked. That combination is self-inconsistent (a resolved
    escalation should have moved the finding to `fixed`) and is left to the semantic reviewer.
    """
    out: set = set()
    for oq in open_questions or []:
        if str(oq.get("Blocking", "")).strip().lower() != "yes":
            continue
        raw = str(oq.get("Finding", "")).strip()
        if not raw:
            continue
        for token in _re.split(r"[,;\s]+", raw):
            tok = token.strip().strip(".`").upper()
            if tok:
                out.add(tok)
    return out


def _review_index(repo_root: Path) -> Dict[str, List[Path]]:
    """Map a reviewed plan's id6 -> its review file(s), via the ONE discovery helper.

    Discovery is `review_findings.iter_review_files` (the record-path authority plus its documented
    bare-repo fallback), so this function holds NO `.aw/records/reviews` path literal of its own.
    """
    index: Dict[str, List[Path]] = {}
    try:
        from agent_workflows import review_findings as _rf
    except Exception:
        return index
    ignored_dirs = _core.get_ignored_dirs(repo_root)
    for path in _rf.iter_review_files(repo_root):
        if _core.is_ignored_path(path, repo_root, ignored_dirs):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            # Unreadable: recorded against the id6 we cannot learn, so it cannot be attributed to a
            # plan. `check.review-dangling` already owns the untidy-review surface; a file we cannot
            # read at all has no Plan-Id to key on.
            continue
        m = _REVIEW_PLAN_ID_RE.search(text)
        if m is None:
            continue
        index.setdefault(m.group(1), []).append(path)
    return index


def evaluate_review_finding_escalation(
    repo_root: Path,
    *,
    plan_path: Path,
    plan_text: str,
    open_questions=None,
    threshold: Optional[str] = None,
    review_index: Optional[Dict[str, List[Path]]] = None,
) -> List[_core.Drift]:
    """The ONE evaluator for `check.review-finding-unescalated`, shared by both host surfaces.

    `aw check` (via :func:`check_review_finding_unescalated`) and `aw ipd lint` (via
    ``ipd_lint.lint_file``) both call THIS function, so the sweep and the checkpoint gate cannot
    drift apart in what they consider escalated.

    Severity comparison is delegated to ``review_findings.is_gating``; this function does NOT
    re-implement it. Current-round semantics come from ``ReviewDocument.current_findings()``, so a
    finding raised in round 1 and fixed in round 2 is not current and never fires.

    THE THREE FAILURE MODES ARE DELIBERATE AND EXPLICIT (E-07), not inherited from an enclosing
    ``except Exception: pass``:

    (a) NO review artifact for this plan -> SILENT. This is the honest consequence of the
        acknowledged under-scope: a reviewer who records nothing is outside deterministic reach. It is
        also required for safety, since zero `.review.md` files exist against 428 plan files, so a
        fail-closed absent case would mass-fail the entire corpus on day one.
    (b) Artifact PRESENT but unparseable/malformed -> FAIL CLOSED, reported. A file that exists but
        cannot be trusted is an ERROR, not an absence, and treating it as an absence is the evasion
        path. Any parser diagnostic counts, INCLUDING an unrecognized severity: a `HGIH` typo would
        otherwise slip past ``is_gating`` silently, which is exactly the hole being closed.
    (c) Threshold ``off`` -> the rule is DISABLED entirely (15zvu6 E-05).
    """
    drift: List[_core.Drift] = []
    try:
        from agent_workflows import review_findings as _rf
        from agent_workflows import config as _cfg
    except Exception:
        return drift

    # (c) `off` disables the rule outright. Checked FIRST so a disabled gate does no work at all.
    thr = (
        threshold if threshold is not None else _cfg.findings_gate_threshold(repo_root)
    )
    if str(thr).strip().lower() in ("off", ""):
        return drift

    mid = _ITEM_ID_RE.search(plan_text)
    if mid is None:
        return drift  # no `- Id:` to join on; the metadata linter owns that complaint
    plan_id6 = mid.group(1)

    index = _review_index(repo_root) if review_index is None else review_index
    reviews = index.get(plan_id6) or []
    if not reviews:
        return drift  # (a) absent -> silent, by design

    if open_questions is None:
        try:
            from agent_workflows import ipd_lint as _lint

            open_questions = _lint.parse(plan_text).open_questions
        except Exception:
            open_questions = []
    escalated = _blocking_escalated_finding_ids(open_questions)

    for review_path in reviews:
        doc = _rf.parse_review_file(review_path)
        if doc.diagnostics:
            # (b) present but malformed -> FAIL CLOSED. Reported at the REVIEW path, because that is
            # the file to repair.
            codes = ", ".join(sorted({d.code for d in doc.diagnostics}))
            drift.append(
                enrich_drift(
                    _core.Drift(
                        str(review_path),
                        _REVIEW_UNESCALATED_RULE,
                        (
                            "review artifact for plan {0} is malformed ({1}), so its findings "
                            "cannot be checked for escalation".format(plan_id6, codes)
                        ),
                    ),
                    observed="unparseable review artifact: {0}".format(codes),
                    required=(
                        "a review artifact whose findings table parses, so gating findings are "
                        "machine-checkable"
                    ),
                    recovery=(
                        "repair the review artifact's findings table (see the reviews tree "
                        "README); a malformed artifact is reported rather than skipped so a "
                        "typo cannot hide a gating finding"
                    ),
                )
            )
            continue

        for finding in doc.current_findings():
            if finding.decision not in _UNFIXED_DECISIONS:
                continue
            if not _rf.is_gating(finding.severity, thr):
                continue
            if finding.id.strip().upper() in escalated:
                continue
            drift.append(
                enrich_drift(
                    _core.Drift(
                        str(plan_path),
                        _REVIEW_UNESCALATED_RULE,
                        (
                            "review finding {0} is {1}/{2} (at or above the `{3}` gate threshold) "
                            "but no `Blocking: yes` open question names it".format(
                                finding.id, finding.severity, finding.decision, thr
                            )
                        ),
                    ),
                    observed=(
                        "{0}: severity {1}, decision {2}, not escalated".format(
                            finding.id, finding.severity, finding.decision
                        )
                    ),
                    required=(
                        "an open question with `- Blocking: yes` and `- Finding: {0}`".format(
                            finding.id
                        )
                    ),
                    recovery=(
                        "either fix {0} and mark it `FIXED` in {1}, or add an `### OQ-NN:` entry "
                        "to the plan's `## Open questions` carrying `- Blocking: yes` and "
                        "`- Finding: {0}`".format(finding.id, review_path.name)
                    ),
                )
            )
    return drift


def check_review_finding_unescalated(
    repo_root: Path, include_untracked: bool = False
) -> List[_core.Drift]:
    """Sweep every PENDING-lane plan for unescalated gating review findings (plqjt7 E-01).

    Scoped to pending-lane plans, following the identical grandfathering precedent as
    ``check_ipd_draft_ready`` (:func:`check_ipd_draft_ready`) and ``check_lifecycle_transitions``:
    a terminal-dir plan's review predates this rule, and retroactively litigating the terminal corpus
    would be a whole-tree false-positive explosion.

    The review index is built ONCE for the whole sweep rather than per plan.
    """
    drift: List[_core.Drift] = []
    try:
        from agent_workflows import config as _cfg

        threshold = _cfg.findings_gate_threshold(repo_root)
    except Exception:
        return drift
    if str(threshold).strip().lower() in ("off", ""):
        return drift

    index = _review_index(repo_root)
    if not index:
        return drift  # nothing reviewed: every plan is the (a) absent case

    for p in _iter_type_files(repo_root, "plans", include_untracked=include_untracked):
        if "pending" not in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        drift.extend(
            evaluate_review_finding_escalation(
                repo_root,
                plan_path=p,
                plan_text=text,
                threshold=threshold,
                review_index=index,
            )
        )
    return drift


# --------------------------------------------------------------------------------------
# revgate Order 04 (c621h9 E-07): an IRREVERSIBLE self-resolved review decision that was never
# surfaced to the maintainer.
#
# WHY THIS IS ADVISORY AND NOT A GATE. The workflow already carries the PREVENTIVE control: E-03
# requires a reviewer to escalate an irreversible decision at DECISION time. This rule is the
# BACKSTOP for a reviewer who skipped that step. Adding a third BLOCKING path would overlap Order
# 02's escalation gate and Order 03's dependency cascade for no additional safety
# (GUIDING_PRINCIPLES 6: "fix by default invites gold-plating"), and the plan's own OQ-01 resolved
# this as report-only on that evidence.
#
# WHAT "ADVISORY" DOES AND DOES NOT MEAN HERE, stated precisely because it is easy to overclaim.
# The rule is registered `warning`, as the approved plan's E-07 directs. MEASURED: `warning` DOES
# contribute to a nonzero `aw check` findings exit - `artifact_core.drift_exit_code` exempts only
# `info` severity - so this rule CAN turn an otherwise-clean `aw check` into exit 1. What it does
# NOT do is block a LIFECYCLE transition: it adds no gate to `aw ipd lint`, no `begin`/`finalize`
# refusal, and no dependency-edge block, which is the sense in which OQ-01 resolved "nothing
# blocks". If you want a finding that cannot affect an exit code at all, that is `info` severity
# (the `check.ipd-draft-ready-to-review` detect-and-nudge shape), NOT this. If a skipped escalation
# is ever OBSERVED in practice, the fix is to add the gate deliberately, not to re-read this
# severity as stronger than it is.
# --------------------------------------------------------------------------------------

_REVIEW_DECISION_RULE = "check.review-decision-unescalated"


def evaluate_review_decision_escalation(
    repo_root: Path,
    *,
    plan_path: Path,
    plan_text: str,
    open_questions=None,
    review_index: Optional[Dict[str, List[Path]]] = None,
) -> List[_core.Drift]:
    """The ONE evaluator for `check.review-decision-unescalated`.

    A CURRENT-ROUND decision row marked `Reversible: no` must be surfaced, not merely logged: either
    raised in the reviewed plan as a `Blocking: yes` open question, or explicitly noted as told to the
    maintainer. A row that is neither is reported.

    CURRENT-ROUND ONLY, unlike `aw reviews decisions` (which audits every round on purpose). The two
    differ deliberately and the difference is not an inconsistency: an AUDIT asks "what did the agents
    decide" and a round-1 decision was still made, while a CHECK asks "is there an outstanding
    obligation today", and a decision superseded by a later round no longer carries one. This mirrors
    `current_findings()` usage in the Order 02 rule.

    `Reversible` classification is delegated to `reviews.classify_reversible`, so the check and the
    audit verb cannot disagree about what "irreversible" means.

    THE STATE MATRIX IS EXPLICIT, not inherited from an enclosing ``except Exception: pass``:

    (a) NO review artifact for this plan -> SILENT. Mandatory, not a preference: zero `.review.md`
        files exist against a 400+ plan corpus, so a fail-closed absent case would mass-report the
        entire tree on day one. It is also the honest consequence of the acknowledged under-scope, a
        reviewer who records nothing is outside deterministic reach.
    (b) Artifact PRESENT but malformed -> REPORTED, via the parser's own diagnostics. A file that
        exists but cannot be trusted is not an absence.
    (c) `Reversible` EMPTY or unrecognized -> REPORTED as unjudged. A blank is not a judgement, and
        silently reading it as "reversible" would let the whole obligation be skipped by omission.

    Neither (a), (b), nor (c) may raise.
    """
    drift: List[_core.Drift] = []
    try:
        from agent_workflows import review_findings as _rf
        from agent_workflows import reviews as _reviews
    except Exception:
        return drift

    mid = _ITEM_ID_RE.search(plan_text)
    if mid is None:
        return drift  # no `- Id:` to join on; the metadata linter owns that complaint
    plan_id6 = mid.group(1)

    index = _review_index(repo_root) if review_index is None else review_index
    reviews = index.get(plan_id6) or []
    if not reviews:
        return drift  # (a) absent -> silent, by design

    if open_questions is None:
        try:
            from agent_workflows import ipd_lint as _lint

            open_questions = _lint.parse(plan_text).open_questions
        except Exception:
            open_questions = []
    # Any blocking open question at all counts as escalation here, deliberately UNLIKE the Order 02
    # finding rule, which requires a typed `- Finding: <ID>` naming the specific finding. A decision
    # row has no equivalent typed back-reference field in the artifact schema, so demanding one would
    # be unsatisfiable. The honest residual: a plan with one blocking question and two irreversible
    # decisions satisfies this rule for both. Stated rather than hidden.
    has_blocking_question = any(
        str(oq.get("Blocking", "")).strip().lower() == "yes"
        for oq in (open_questions or [])
    )

    for review_path in reviews:
        doc = _rf.parse_review_file(review_path)
        if doc.diagnostics:
            # (b) present but malformed -> reported at the REVIEW path, the file to repair.
            codes = ", ".join(sorted({d.code for d in doc.diagnostics}))
            drift.append(
                enrich_drift(
                    _core.Drift(
                        str(review_path),
                        _REVIEW_DECISION_RULE,
                        (
                            "review artifact for plan {0} is malformed ({1}), so its recorded "
                            "decisions cannot be checked for escalation".format(
                                plan_id6, codes
                            )
                        ),
                    ),
                    observed="unparseable review artifact: {0}".format(codes),
                    required=(
                        "a review artifact whose Decisions section parses, so an irreversible "
                        "self-made decision is machine-checkable"
                    ),
                    recovery=(
                        "repair the review artifact's tables (see the reviews tree README); a "
                        "malformed artifact is reported rather than skipped so a typo cannot hide "
                        "an unescalated irreversible decision"
                    ),
                )
            )
            continue

        for dec in doc.current_decisions():
            verdict = _reviews.classify_reversible(dec.reversible)
            if verdict == "yes":
                continue
            if verdict == "no" and has_blocking_question:
                continue
            if verdict == "no" and _decision_notes_maintainer_told(dec):
                continue
            if verdict == "unknown":
                drift.append(
                    enrich_drift(
                        _core.Drift(
                            str(review_path),
                            _REVIEW_DECISION_RULE,
                            (
                                "recorded decision {0} has no `Reversible` judgement ({1!r}), so "
                                "whether it needs escalation cannot be determined".format(
                                    dec.id, dec.reversible
                                )
                            ),
                        ),
                        observed="{0}: Reversible is {1}".format(
                            dec.id,
                            "empty"
                            if not dec.reversible.strip()
                            else repr(dec.reversible),
                        ),
                        required="`Reversible: yes` or `Reversible: no` on every decision row",
                        recovery=(
                            "judge {0} on the COST OF BEING WRONG (can a later maintainer undo it?) "
                            "and set `Reversible` accordingly in {1}".format(
                                dec.id, review_path.name
                            )
                        ),
                    )
                )
                continue
            drift.append(
                enrich_drift(
                    _core.Drift(
                        str(plan_path),
                        _REVIEW_DECISION_RULE,
                        (
                            "decision {0} was self-resolved and marked irreversible, but it was "
                            "never surfaced: no `Blocking: yes` open question and no note that the "
                            "maintainer was told".format(dec.id)
                        ),
                    ),
                    observed="{0}: Reversible no, not escalated ({1})".format(
                        dec.id, (dec.question or "").strip()[:80] or "no question text"
                    ),
                    required=(
                        "an irreversible self-made decision is escalated: an open question with "
                        "`- Blocking: yes`, or a note on the row that the maintainer was told"
                    ),
                    recovery=(
                        "either add an `### OQ-NN:` entry carrying `- Blocking: yes` to the plan's "
                        "`## Open questions`, or tell the maintainer and record that on {0}'s row "
                        "in {1} (e.g. `Basis: ...; maintainer told <date>`)".format(
                            dec.id, review_path.name
                        )
                    ),
                )
            )
    return drift


#: Phrases on a decision row that assert the maintainer was told directly.
#:
#: A deliberately NARROW allowlist. The alternative, accepting any mention of "maintainer", would let
#: the row "the maintainer will hate this" satisfy the rule, which is the spoofable-prose failure mode
#: the Order 02 rule avoided by matching a typed field instead. There is no typed field available on a
#: decision row, so the match is at least pinned to an explicit told/notified/informed claim.
_MAINTAINER_TOLD_PHRASES = (
    "maintainer told",
    "told maintainer",
    "maintainer notified",
    "notified maintainer",
    "maintainer informed",
    "informed maintainer",
    "maintainer was told",
    "maintainer asked",
    "raised with maintainer",
    "raised with the maintainer",
)


def _decision_notes_maintainer_told(dec) -> bool:
    """True iff a decision row explicitly claims the maintainer was told.

    Checks the `Basis`, `Chosen`, and `Alternatives considered` cells, because a reviewer may
    reasonably note it in any of them, and the workflow's own example puts it in `Basis`.
    """
    blob = " ".join(
        (
            getattr(dec, "basis", "") or "",
            getattr(dec, "chosen", "") or "",
            getattr(dec, "alternatives", "") or "",
        )
    ).lower()
    return any(p in blob for p in _MAINTAINER_TOLD_PHRASES)


def check_review_decision_unescalated(
    repo_root: Path, include_untracked: bool = False
) -> List[_core.Drift]:
    """Sweep every PENDING-lane plan for an unescalated irreversible recorded decision (c621h9 E-07).

    Scoped to pending-lane plans, following the same grandfathering precedents as
    ``check_ipd_draft_ready`` and ``check_lifecycle_transitions``: a terminal plan's review predates
    this rule, and retroactively litigating the terminal corpus would be a whole-tree false-positive
    explosion.

    The review index is built ONCE for the whole sweep rather than per plan.
    """
    drift: List[_core.Drift] = []
    index = _review_index(repo_root)
    if not index:
        return drift  # nothing reviewed: every plan is the (a) absent case

    for p in _iter_type_files(repo_root, "plans", include_untracked=include_untracked):
        if "pending" not in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        drift.extend(
            evaluate_review_decision_escalation(
                repo_root,
                plan_path=p,
                plan_text=text,
                review_index=index,
            )
        )
    return drift
