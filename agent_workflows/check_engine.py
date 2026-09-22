"""Unified check engine: compose the existing per-type validators into one Drift list per record
type. Pure (returns Drift, never prints). Consumed by the `aw check <type>` verb (awcmdsurf).

THE PLANS SWEEP RUNS THE WHOLE `IPD-*` LINT FAMILY, at the `author` CHECKPOINT ONLY (lintreach
`k9awrq`). `check_content`'s plans branch calls :func:`check_ipd_lint_reach`, which calls the REAL
`ipd_lint.lint_file`, so `aw check` reports what `aw ipd lint` would refuse and the two surfaces cannot
drift apart in what they consider conformant. It is reported under ONE umbrella code,
`check.ipd-lint-diagnostic`, carrying the underlying `IPD-*` code and message in its detail, and it is
registered `info` so it cannot move an exit code (see that registration for why `warning` would NOT
have been advisory here, and the plan's OQ-04 for the open question of whether it should ever block).

`author` IS THE ONLY DEFENSIBLE CHECKPOINT FOR A SWEEP, and the reason is recorded here because the
obvious "improvement" is to make it configurable or to default it to the stricter value. Measured at
HEAD `cd2e6adb`: `author` -> 0 diagnostics across 702 plans, while `pre-transition` -> 1199 across all
76 pending plans, 1196 of them `IPD-S404` ("not 'performed' at pre-transition"), which is the CORRECT
state of any plan that has not executed yet. Sweeping `pre-transition` would therefore mass-fail the
tree for being in its normal condition. `aw ipd lint` and `aw ipd begin` already apply that stricter
phase where it belongs, to ONE plan that is actually transitioning."""

from __future__ import annotations

import importlib.util
import re as _re
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

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
    # Setid SEMANTICS (catalog I-16, spec `2lcqno` N5): a setid used within ONE type with two
    # different descriptives. NOT I-09, which is filename-grammar conformance: I-09 governs a name's
    # SHAPE, while this rule governs whether one token may be REUSED, which the grammar is silent on.
    # Repointed here (spec `pqsx96` Section 4 held the code at I-09 deliberately until the rule was
    # re-scoped). Its two id6 neighbours below stay on I-09 on purpose: the identity-slot rule
    # genuinely does concern the filename slot.
    "check.setid-collision": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-16"
    ),
    # Filename identity-slot / id6 uniqueness (catalog I-09 family).
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
    # detrun Order bmh754 (spec 25kzda): the SPEC-side twin of `check.from-backlog-dangling` above - a
    # plan/spec whose `From-Spec:` id6 resolves to no spec. Same severity (`error`), same assurance
    # class, and the SAME invariant I-07 as its backlog twin, because a spec is an equally valid
    # release-gate handoff carrier (AGENTS.md), so a broken `From-Spec` breaks the same gate-preservation
    # invariant a broken `From-Backlog` does. Deterministic: a literal id6 set membership test against
    # `specs._existing_spec_ids`, no inference.
    "check.from-spec-dangling": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    "check.orphaned-live-blocker": RuleSpec(
        "warning", ASSURANCE_REPOSITORY, DET_HEURISTIC, "I-07"
    ),
    # nobugship rgaasb E-02: a LIVE `Work-Kind: bug` item carrying NO `- Blocks-Release:`. The
    # enforcement half of the maintainer's standing rule "we don't ship known bugs", written down by
    # sibling plan `zqs0px` in AGENTS.md ("Every live bug gates the next release") and defaulted at
    # creation by sibling `di08i9`. This rule is what makes the policy self-maintaining: documentation
    # and a creation default both leave the HAND-AUTHORED route open, which is measurably how the
    # violations accumulated unnoticed.
    #
    # `error`, matching its four I-07 siblings above, NOT a staged `warning` with a promise to tighten
    # later: a rule left permanently at `warning` is a recorded failure mode in this repository
    # (`rnkqrc` E-05). Behaviorally `warning` would fail an exit code anyway
    # (`artifact_core.drift_exit_code` exempts only `info`), so the distinction would buy nothing but
    # a weaker stated contract.
    #
    # I-07 IS THE RIGHT HOME AND THE FIT WAS VERIFIED, NOT ASSUMED: read at
    # `.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md:135`,
    # I-07 is "Release-gate preservation", assurance class "Repository invariant", and its control
    # column already names `evaluate_blocking_close` plus `check.blocking-item-closed-without-gate`,
    # `check.from-backlog-gate-mismatch` and `check.orphaned-live-blocker`.
    #
    # ONE HONEST TENSION, RECORDED RATHER THAN PAPERED OVER: I-07's catalog TEXT is phrased for the
    # CLOSE direction ("may close `done` only if the gate is provably preserved..."), while THIS rule
    # governs the OPEN direction (a live item must CARRY a gate). It is the same invariant's other
    # half and I-07 is still the correct home - a rule about whether a release gate exists to be
    # preserved belongs with the rules about preserving it - but a future reader comparing this
    # registration against the catalog wording would otherwise see a mismatch and re-litigate it.
    # Widening the catalog wording is a SPEC edit outside this plan's `- Scope-Paths:`, so it is
    # PROPOSED (see the plan's spec-sync section) and deliberately not performed here.
    #
    # Deterministic: a literal `- Work-Kind:` / `- Status:` / `- Blocks-Release:` token test through
    # the shared `backlog.parse_item`, plus a literal carrier lookup. No inference.
    "check.live-bug-ungated": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    # revgate Order 01 (15zvu6) E-06: a `.review.md` whose `Subject-Id:` resolves to no artifact of
    # its declared `Subject-Type:` (revsweep `eyh1fu` made that resolution type-directed; it was
    # plans-only before). Same
    # SHAPE as the `*-dangling` rules above (an unresolvable cross-tree reference), but deliberately
    # `warning`, NOT `error` like its neighbours: a review left behind by a superseded or deleted
    # subject is UNTIDY, not dangerous, and nothing downstream reads it, so it must not block a commit
    # or set an exit code. The in-tree precedent for an advisory rule in this family is
    # `check.orphaned-live-blocker` directly above. It IS deterministic (a literal id6 set lookup,
    # no inference), hence DET_DETERMINISTIC rather than DET_HEURISTIC.
    "check.review-dangling": RuleSpec(
        "warning", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    # revsweep 5slbpi E-04: a spec CURRENTLY at `- Status: reviewed` with no conforming review record
    # naming it. `error`, NOT the advisory severity its `check.review-dangling` neighbour directly
    # above carries, and the difference is deliberate rather than inherited: a stale review is untidy
    # leftover data nothing downstream reads, whereas a spec claiming `reviewed` with no review is a
    # FALSE LIFECYCLE CLAIM on the artifact that AUTHORIZES plans, which is exactly what invariant
    # I-03 (lifecycle-status authority) exists to police. Registration is not bookkeeping: an
    # unregistered id falls back to `_DEFAULT_RULESPEC` with an EMPTY invariant, so omitting this entry
    # would silently drop the I-03 trace. Deterministic: a literal `- Status:` token test plus the
    # shared `review_findings.review_attestation_missing` predicate (presence + declared type +
    # parseability of a record). No inference.
    "check.spec-review-unattested": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-03"
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
    # Recognized-but-optional Work-Kind enum on a plan's own metadata (wkindname ng2blv). Same class
    # as its Priority sibling above: an out-of-vocab `- Work-Kind:` value is an error; an ABSENT
    # Work-Kind is silent (optional), which is what keeps the existing corpus from being mass-failed.
    # The shared vocab is backlog.KINDS (not forked). NOTE this rule covers PLANS (and specs report
    # through `spec.work-kind-invalid` in validate_spec); BACKLOG keeps its own pre-existing
    # `backlog.kind-invalid` contract-drift path, where the field is REQUIRED. Two mechanisms by
    # design; nothing routes backlog through this registry.
    "check.work-kind-invalid": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, ""
    ),
    # Authoring-lifecycle nudge (catalog I-12): a finished draft should advance to to-review. This
    # is GUIDANCE and only detectable (placeholder-free draft), so info-severity + heuristic.
    "check.ipd-draft-ready-to-review": RuleSpec(
        "info", ASSURANCE_GUIDANCE, DET_HEURISTIC, "I-12"
    ),
    # lintreach Order 01 (`k9awrq`) E-02: the UMBRELLA code under which the whole `IPD-*` lint family
    # becomes reachable from the repo-wide sweep. Before this, `check_engine` called `ipd_lint.parse`
    # in three places but NEVER `lint_file`, so every `IPD-*` diagnostic was invisible to `aw check`
    # and to CI: a defect `aw ipd lint` REFUSES could be committed and would sit in the tree until
    # someone linted that exact file or tried to execute it.
    #
    # ONE UMBRELLA CODE, NOT ONE PER `IPD-*` DIAGNOSTIC, and the reason is OWNERSHIP rather than taste
    # (plan OQ-01, resolved). The `IPD-*` family is large, is owned and versioned by
    # `ipd_lint`/`ipd_schema`, and GROWS whenever a lint rule is added. Registering each code here
    # would mean every new lint rule needs a second registration in a different module, and a missed
    # one would fall through to `_DEFAULT_RULESPEC` and emit a code carrying NO severity contract. The
    # underlying `IPD-*` code and message travel in the finding's DETAIL, and the `recovery` command is
    # the per-file verb that prints all of them, so nothing an operator needs is lost.
    #
    # `info`, AND THAT IS A MEASUREMENT, NOT THE PLAN'S LITERAL WORD (DECISION 02-k9awrq-D1). The plan
    # says "advisory" and spells it `warning`, while its own F-14 records that `warning` DOES drive a
    # nonzero findings exit, and its V-02 requires the severity be proven by MEASURING the exit code
    # rather than by choosing a word. Driving `artifact_core.drift_exit_code` directly: `error` -> 1,
    # `warning` -> 1, `info` -> 0, empty -> 1. So `info` is the UNIQUE severity that is advisory in
    # BEHAVIOR, and `warning` would have satisfied the spelling while failing the requirement.
    #
    # WHY ADVISORY AT ALL, since the corpus is clean at `author` today (0 diagnostics across 702 plans,
    # measured at HEAD `cd2e6adb`) and a clean corpus would tolerate `error`. Because clean is NOT a
    # STABLE property, which the plan's OQ-04 states and leaves OPEN for the maintainer: `IPD-Q501`
    # fires on any plan with an unanswered `Blocking: yes` question, and this repository deliberately
    # produces those, so the count returns to nonzero every time a reviewer correctly escalates and the
    # maintainer has not yet answered. Review measured exactly that state (16 findings across 10
    # plans). A blocking tree-wide rule therefore makes EVERY agent's commit depend on maintainer
    # answer latency, which is the outcome `ipd_lint.check_open_questions` records the maintainer
    # REJECTING on 2026-09-08: the wider rule "would have forced an agent to edit other agents'
    # in-flight plans to get its own commit through". Promotion is OQ-04's to decide, and is a
    # one-token change to this entry.
    #
    # I-05 ("IPD finalize requires validation"), whose catalog control column already names
    # `aw ipd lint` conformance as the structural gate: the codes this rule carries are exactly that
    # structural/state family. NOT I-03 (lifecycle-status authority, which `check.status-untooled` and
    # `check.lifecycle-transition-invalid` own) and NOT I-09 (filename grammar).
    #
    # Deterministic: it is the SAME `ipd_lint.lint_file` call the per-file verb makes, with no rule
    # re-implemented and no inference.
    "check.ipd-lint-diagnostic": RuleSpec(
        "info", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-05"
    ),
    # IPD sk7ggr E-06: a per-type `aw check <type>` does NOT run the cross-tree collision scan, so a
    # clean per-type report must not be read as "collision-clean". This rule SAYS so on exactly those
    # runs. `info` is the whole point: it removes the silence without inventing a failure (a per-type
    # run examining no collisions is correct behavior, not drift), so `drift_exit_code` keeps the run
    # at exit 0. Same I-09 family as the collision rules whose absence it is reporting.
    "check.collisions-not-checked": RuleSpec(
        "info", ASSURANCE_GUIDANCE, DET_DETERMINISTIC, "I-09"
    ),
    # Event-derived lifecycle transition validity (agentadhere Phase 3, IPD wqj1ne E-01; catalog
    # I-03). A plan whose inline history event stream contains an invalid/out-of-order/unauthorized
    # transition is flagged. Repository-class + deterministic over the (locally forgeable) events.
    "check.lifecycle-transition-invalid": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-03"
    ),
    # Declared-file-scope drift (agentadhere Phase 3, IPD wqj1ne E-02; catalog I-01). A plan with a
    # LIVE begin receipt whose changed paths since the frozen base fall outside its Scope-Paths. LIVE
    # excludes a receipt whose plan is in a terminal lifecycle dir or whose base is unreachable from
    # HEAD (IPD rygds7; see `_receipt_is_live`).
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
    # wslayout Order 05 (30jug9), spec kw5y2s Section 6.2: the emitted machine-readable layout
    # document is ABSENT from, or STALE relative to, an INSTALLED workspace.
    #
    # WHY THIS RULE EXISTS AT ALL, since the reason decides its severity. Spec Section 2.3 rules the
    # emitted `.aw/system/layout.json` GITIGNORED, so git will never show a diff for it: there is no
    # review surface and no history to inspect. That makes this rule the ONLY loud-failure backstop
    # telling a user or a CI job to run an install before a non-Python tool tries to read the layout.
    #
    # `warning`, NOT `error`, and the distinction is honest rather than cosmetic. Behaviorally these
    # are equally loud: `artifact_core.drift_exit_code` fails the gate for anything that is not
    # `info`, so either severity exits 1 and fails CI. The class is what differs. An `error` in this
    # registry means a RECORD is malformed and a human authored it wrong; here the artifact is
    # GENERATED and the remedy is mechanical ("run `aw install`"), so `warning` states the condition
    # truthfully without weakening the gate.
    #
    # NEITHER RULE FIRES WITHOUT THE INSTALL MARKER (`.aw/system/VERSION`). A repo that has simply
    # never been installed has nothing to be missing or stale, and because the emitted files are
    # gitignored, EVERY fresh clone is in that state; keying on the marker is what keeps `aw check`
    # from failing on a fresh clone by design (30jug9 E-02, DECISION 05-30jug9-D1).
    "check.system-layout-missing": RuleSpec(
        "warning", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, ""
    ),
    "check.system-layout-drift": RuleSpec(
        "warning", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, ""
    ),
    # idxuntrack 02 (yvvf98) E-02: the generated plans/research manifests (`INDEX.json`/`INDEX.md`).
    # These replace the single conflated `stale-index` rule, and the SPLIT is the whole point: once
    # the manifests are gitignored generated views, ABSENT and STALE stop being the same condition.
    #
    # Both ids deliberately CONTAIN the substring `stale-index`, because five sites in `doctor.py`
    # classify findings with `"stale-index" in rule` rather than an equality test. Preserving the
    # substring keeps those matches working by construction instead of by five parallel edits, so a
    # future rename must preserve it too or update all five together (E-03).
    #
    # SEVERITY, following the `check.system-layout-*` precedent directly above for the identical
    # case (a generated, gitignored artifact whose remedy is mechanical, `aw index <type>`):
    #
    #   * MISSING -> `info`, the ONLY non-failing severity. `artifact_core.drift_exit_code` fails the
    #     gate for anything that is not `info`, so `warning` here would still exit 1 on every fresh
    #     clone and every fresh worktree, which is exactly the outcome untracking must not cause.
    #     A manifest that was never generated is not drift: there is nothing to be stale against.
    #   * STALE -> `warning`, which DOES fail the gate. A manifest present but not byte-equal to a
    #     rebuild is real drift a human can act on, and `warning` rather than `error` states the
    #     class honestly: the artifact is GENERATED, not hand-authored, so the remedy is mechanical.
    #
    # Registering both matters beyond taste: an UNREGISTERED rule falls through to
    # `_DEFAULT_RULESPEC` (severity `error`), which is what `stale-index` silently did, and is why
    # absence could not have been made non-failing by editing a message string.
    "check.stale-index-missing": RuleSpec(
        "info", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, ""
    ),
    "check.stale-index-stale": RuleSpec(
        "warning", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, ""
    ),
    # durablecapture Order 01 (`rnkqrc`) E-04: an IPD records an outstanding obligation (a
    # `## Deferred / out of scope` row, or an `open`/`deferred` question) that names NO durable
    # carrier, so reaching `executed` would delete it from every attention view.
    #
    # `error`, WHICH IS THE END STATE AND NOT THE WHOLE STORY. The maintainer's ruling (OQ-05) is
    # "This is a MUST, not a should", so the registered severity is the fail-closed one. The evaluator
    # DOWNGRADES a pre-cutover plan to `_CARRIER_LEGACY_SEVERITY` (`info`) per plan, and that direction
    # matters: registering the ADVISORY tier here instead would make an unclassified finding
    # non-failing, whereas registering `error` means anything the downgrade does not reach fails toward
    # visible. Registration is not bookkeeping either way: an unregistered id falls through to
    # `_DEFAULT_RULESPEC`, so omitting this entry would silently drop the invariant trace below.
    #
    # WHY THE STAGED TIER IS `info` AND NOT `warning` (measured, not assumed): `drift_exit_code` exempts
    # ONLY `info`, so a `warning` grandfather tier would exit 1 with 106 findings on a clean tree and
    # fail the CI that enforces `aw check plans` fail-closed. The exact precedent is
    # `check.stale-index-missing` above, for the identical dilemma, with the reason written down.
    #
    # Invariant I-07, claimed deliberately rather than left empty. I-07 is the release/obligation
    # PRESERVATION invariant its `check.blocking-item-closed-without-gate` and `check.from-backlog-*`
    # neighbours claim, and this rule is the same predicate shape (`evaluate_blocking_close`'s three
    # escapes) applied to the same concern: an obligation must survive in a place that is revisited.
    # Deterministic: a typed-field presence test plus a literal id6 lookup in the artifact inventory and
    # a closed-vocabulary status comparison. No prose is read, hence no heuristic.
    "check.ipd-uncarried-obligation": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-07"
    ),
    # findtier Order 02 (`3i6rso`) E-04: a record whose declared `- Id:` or `- Set:` is ABSENT from
    # its own filename. This is the EXCEPTION SET that forces `aw find`'s content fallback, and the
    # rule exists so the set is COUNTABLE (and provably not growing) rather than invisible.
    #
    # `warning`, NOT `error`, and the reason is a measured policy constraint rather than caution.
    # Every member on this tree today is grandfathered BY DECISION: eight are pre-id6-grammar names,
    # five of them `executed/` plans whose bodies must not be re-committed (AGENTS.md, enforced by
    # the `ipd-executed-gate` hook), and the rest are pre-cutover specs that `SPEC_ID6_CUTOVER_DATE`
    # above deliberately grandfathers. An `error` would therefore fail the tree for states the
    # maintainer CHOSE, and a future tightening pass must not promote it without first renaming the
    # corpus. The in-tree precedents for exactly this posture are `check.review-dangling` and
    # `check.orphaned-live-blocker`; this rule follows `check.review-dangling` (advisory, whole-tree,
    # deterministic, consumed by no lifecycle gate).
    #
    # DO NOT READ `warning` AS "cannot fail anything": `artifact_core.drift_exit_code` exempts only
    # `info`, so a `warning` does drive a nonzero findings exit. What the severity buys here is that
    # NO error-severity finding is added, so the advisory can never turn an otherwise-green tree red,
    # and that no lifecycle gate (`aw ipd lint`, begin/finalize, dependency resolution) consumes it.
    # It is deliberately not `info` either: an unlocatable-by-name record is a real obligation to
    # watch, not a nudge.
    #
    # I-09, matching the naming-grammar family (`check.name-nonconformant`, `check.id6-collision`,
    # `check.id6-identity-slot`): the finding is about a filename failing to carry the identity that
    # locates it. It SITS BESIDE `check.id6-identity-slot` rather than extending it, and covers the
    # population that rule exempts by construction (a name with no id6 slot at all); see
    # `check_name_identity` for the recorded extend-versus-add decision.
    "check.identity-absent-from-name": RuleSpec(
        "warning", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, "I-09"
    ),
    # idcapture Order 01 (`76w6mq`) E-05: a metadata-shaped `- Id: <id6>` line found OUTSIDE a
    # record's METADATA REGION. The companion to bounding the identity readers to that region
    # (`selectors.metadata_region`): bounding STOPS the false claim, and this rule SURFACES the
    # ambiguity instead of swallowing it silently (maintainer ruling 2026-09-05, "fix AND warn").
    #
    # `info`, AND THIS IS A MEASUREMENT RATHER THAN A PREFERENCE. The obvious choice is `warning`,
    # reasoning that the repository must not FAIL its own check for legitimately documenting its own
    # metadata format - and that reasoning is right while the label is wrong, because `warning` fails
    # the gate exactly as `error` does. Verified by driving `artifact_core.drift_exit_code` with each
    # value: `error` -> 1, `warning` -> 1, `info` -> 0, empty -> 1 (`artifact_core.py`, whose
    # docstring states only `info` is advisory). So registering `warning` would make `aw check` exit
    # nonzero on documents whose content is CORRECT, which is the failure mode backlog `gjadwm`
    # records as training agents to bypass a gate. The two shipped precedents for this exact
    # detect-and-nudge purpose are `check.ipd-draft-ready-to-review` and `check.stale-index-missing`,
    # both `info`. Registration is NOT optional bookkeeping either: an unregistered id falls through
    # to `_DEFAULT_RULESPEC` at severity `error`, so omitting this entry would fail the tree.
    #
    # I-09, joining the identity family (`check.id6-collision`, `check.id6-identity-slot`,
    # `check.identity-absent-from-name`): the finding is about WHERE a record's identity is declared.
    # Deterministic: a literal anchored-pattern position test against the region boundary, no prose
    # is interpreted and nothing is inferred.
    #
    # WHAT A FINDING MEANS, since the two cases differ and the rule cannot yet tell them apart: an
    # out-of-region `- Id:` is either a QUOTATION (harmless, and the reason this is advisory) or a
    # MISPLACED DECLARATION (a real defect whose identity no reader will ever see). Promoting the
    # severity would force the second to be fixed but would fail the tree for the first, so that
    # remains a future choice on a rule that by then has a clean corpus, not a change to make here.
    "check.id6-outside-metadata-region": RuleSpec(
        "info", ASSURANCE_GUIDANCE, DET_DETERMINISTIC, "I-09"
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


_RETIRED_PATH_SEGMENTS = frozenset(
    {"archive", "executed", "superseded", "not-executed", "parked", "done", "shipped"}
)
_RETIRED_STATUSES = frozenset(
    {
        "executed",
        "superseded",
        "not-executed",
        "parked",
        "done",
        "implemented",
        "shipped",
    }
)


def is_retired(path: Path, record_type: str = "") -> bool:
    """Return True if the artifact path or frontmatter status represents a retired/archived/terminal item."""
    try:
        parts_lower = [part.lower() for part in path.parts]
    except Exception:
        parts_lower = []
    if any(seg in parts_lower for seg in _RETIRED_PATH_SEGMENTS):
        return True

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False

    m = _STATUS_META_RE.search(text)
    if m and m.group(1).strip().lower() in _RETIRED_STATUSES:
        return True

    return False


def _iter_type_files(
    repo_root: Path,
    record_type: str,
    include_untracked: bool = False,
    include_retired: bool = False,
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
            if not include_retired and is_retired(p, record_type):
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
    include_retired: bool = False,
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
        repo_root,
        record_type,
        include_untracked=include_untracked,
        include_retired=include_retired,
    ):
        # Spec id6 cutover (IPD ha55fi E-03): a spec dated at/after the spec_id6 cutover must be
        # id6-clustered; a pre-cutover spec is grandfathered (legacy HHMM-NN name still conforms).
        require_id6 = record_type == "specs" and _spec_requires_id6(
            p.name, repo_root=repo_root
        )
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
            from agent_workflows import config as _config

            cutover_disp = (
                _config.resolve_cutover_date(repo_root, "spec_id6", compact=True)
                or SPEC_ID6_CUTOVER_DATE
            )
            detail = (
                f"spec dated at/after the id6 cutover ({cutover_disp}) must be "
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


def _spec_requires_id6(filename: str, repo_root: Optional[Path] = None) -> bool:
    """True iff a spec filename's leading YYYYMMDD date is at/after the spec_id6 cutover date.

    When repo_root is provided, resolves dynamically via resolve_cutover_date(repo_root, 'spec_id6').
    Falls back to the deprecated SPEC_ID6_CUTOVER_DATE constant when unconfigured or repo_root is omitted.
    A name with no parseable leading date is treated as pre-cutover (require_id6=False) so an
    unusual/legacy shape is not force-failed by the cutover; the normal grammar check still applies.
    """
    m = _SPEC_DATE_RE.match(filename)
    if m is None:
        return False
    cutover = None
    if repo_root is not None:
        from agent_workflows import config as _config

        cutover = _config.resolve_cutover_date(repo_root, "spec_id6", compact=True)
    if cutover is None:
        cutover = SPEC_ID6_CUTOVER_DATE
    return m.group(1) >= cutover


def check_content(
    repo_root: Path,
    record_type: str,
    legacy: bool = False,
    include_untracked: bool = False,
    include_retired: bool = False,
) -> List[_core.Drift]:
    """Front-matter/status/contract validation, delegated to the existing per-type validators."""
    repo_root = Path(repo_root)
    drift: List[_core.Drift] = []
    if record_type == "specs":
        from agent_workflows import specs as _specs

        # Discover files via _type_dirs (robust for a bare repo), validate each with validate_spec.
        for p in _iter_type_files(
            repo_root,
            "specs",
            include_untracked=include_untracked,
            include_retired=include_retired,
        ):
            try:
                drift.extend(_specs.validate_spec(p, p.read_text(encoding="utf-8")))
            except OSError:
                continue
    elif record_type == "backlog":
        from agent_workflows import backlog as _backlog

        for p in _iter_type_files(
            repo_root,
            "backlog",
            include_untracked=include_untracked,
            include_retired=include_retired,
        ):
            try:
                drift.extend(_backlog.validate_item(p, p.read_text(encoding="utf-8")))
            except OSError:
                continue
    elif record_type == "plans":
        from agent_workflows import plans_index as _pidx

        dirs = _type_dirs(repo_root, "plans")
        if dirs and include_retired:
            drift.extend(_pidx.check_drift(repo_root, dirs[0]))
        # ipddeps ovbnyq (spec 25kzda 2.10): the cross-IPD dependency check is a PLANS-scoped concern
        # (every dependency source is an IPD), so it runs in the plans-type content path - reached by
        # BOTH `aw check plans` and the `aw check all` fan-out, exactly once, never double-reported
        # (deliberately NOT also added to the collisions-only cross-tree sweep).
        try:
            drift.extend(
                check_ipd_dependencies(repo_root, include_retired=include_retired)
            )
        except Exception:
            pass
        # xprio 1b45el E-02: validate the recognized-but-optional `- Priority:` enum on each plan
        # against the shared backlog.PRIORITIES (out-of-vocab -> error; absent -> silent). Runs in the
        # plans-type content path so BOTH `aw check plans` and `aw check all` surface it exactly once.
        try:
            drift.extend(
                check_plan_priority(
                    repo_root,
                    include_untracked=include_untracked,
                    include_retired=include_retired,
                )
            )
        except Exception:
            pass
        # wkindname ng2blv E-05: validate the recognized-but-optional `- Work-Kind:` enum on each plan
        # against the shared backlog.KINDS (out-of-vocab -> error; absent -> silent). Same placement
        # and shape as the Priority sibling above, so both surface exactly once per check run.
        try:
            drift.extend(
                check_plan_work_kind(
                    repo_root,
                    include_untracked=include_untracked,
                    include_retired=include_retired,
                )
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
        # durablecapture Order 01 (`rnkqrc`) E-04: an outstanding obligation an IPD records with no
        # durable carrier. SAME PLACEMENT as its `check_review_finding_unescalated` neighbour above and
        # for the same documented reason (`check_ipd_dependencies`' "every dependency source is an IPD"
        # precedent): the concern is keyed off the PLAN, so it belongs in the plans-type content path,
        # reached by BOTH `aw check plans` and the `aw check all` fan-out exactly once, and deliberately
        # NOT in the collisions-only cross-tree sweep (which the full sweep alone reaches). Calls the
        # SAME evaluator `aw ipd lint --phase pre-transition` calls, so the two surfaces cannot disagree.
        # Fail-isolated in the same shape as every neighbour here.
        try:
            drift.extend(
                check_durable_carrier(repo_root, include_untracked=include_untracked)
            )
        except Exception:
            pass
        # lintreach Order 01 (`k9awrq`) E-02: run the REAL `ipd_lint.lint_file` at the `author`
        # checkpoint so the whole `IPD-*` family is reachable from the tree-wide verdict. SAME
        # PLACEMENT as every plans-scoped neighbour above and for the same documented reason
        # (`check_ipd_dependencies`' "every dependency source is an IPD" precedent): the concern is
        # keyed off the PLAN, so it belongs in the plans-type content path, reached by BOTH
        # `aw check plans` and the `aw check all` fan-out exactly once, and deliberately NOT in the
        # collisions-only cross-tree sweep. Advisory (`info`), so it cannot move any exit code. Runs
        # LAST among the plans rules so its added cost is attributable in a profile. Fail-isolated in
        # the same shape as every neighbour here.
        try:
            drift.extend(
                check_ipd_lint_reach(repo_root, include_untracked=include_untracked)
            )
        except Exception:
            pass
    elif record_type == "research":
        from agent_workflows import research_index as _ridx

        dirs = _type_dirs(repo_root, "research")
        if dirs and include_retired:
            drift.extend(_ridx.check_drift(repo_root, dirs[0]))
    elif record_type == "releases":
        from agent_workflows import releases as _releases

        for p in _iter_type_files(
            repo_root,
            "releases",
            include_untracked=include_untracked,
            include_retired=include_retired,
        ):
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

# idcapture Order 01 (`76w6mq`): the CHECKER's identity readers are bounded to the same METADATA
# REGION the selector's are, via the ONE shared helper `selectors.metadata_region`, so a quoted
# example block cannot be read as a declaration on EITHER surface.
#
# THIS MODULE HAD ITS OWN COPY OF THE DEFECT, and that is why bounding only the selector would have
# been a half-fix. `_ID_LINE_RE` / `_SET_LINE_RE` above are byte-identical twins of
# `selectors._ID_RE` / `selectors._SET_RE`, and `check_collisions` applied them to a WHOLE FILE
# BODY, so the two research documents quoting one `- Id: uyeko5` block were reported as a genuine
# `check.id6-collision` with each other. Measured before this change: 17 id6-collision findings, of
# which those 2 were manufactured by the quotation. Fixing only `selectors` would have left `aw
# check` asserting a collision that no verb could any longer see - two surfaces disagreeing about
# what identity IS, which is the precise defect shape `check_collisions`'s own docstring records.
#
# ONE helper, imported rather than re-derived: a second local region parser is how the reader drift
# documented at `selectors.read_front_matter_id` happened before.


def _metadata_region(text: str) -> str:
    """This module's accessor for the shared metadata-region boundary (`selectors`-owned)."""

    from agent_workflows import selectors as _sel

    return _sel.metadata_region(text)


def _read_declared_id(text: str) -> "str | None":
    """The record's DECLARED `- Id:` id6, read only from its metadata region, or None."""

    m = _ID_LINE_RE.search(_metadata_region(text))
    return m.group(1) if m else None


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
    (None, None). The setid is the first whitespace token before any '('.

    Bounded to the record's METADATA REGION (IPD `76w6mq`), like its `- Id:` sibling above, so a
    `- Set:` line inside quoted example prose is not read as this record's own Set declaration."""
    m = _SET_LINE_RE.search(_metadata_region(text))
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
    repo_root: Path,
    include_untracked: bool = False,
    include_retired: bool = False,
) -> List[_core.Drift]:
    """Cross-tree id6 AND setid uniqueness, PLUS the filename identity-slot invariant (D140).

    Runs ONCE over every SUPPORTED type (collisions are global, not per-type):

    * frontmatter ``- Id:`` id6: a valid id6 declared on two different resolved files
      (``check.id6-collision``);
    * setid: the same setid used WITHIN ONE type with two different non-None descriptives
      (``check.setid-collision``). A setid appearing under two DIFFERENT types is CORRECT and is
      NOT reported: DECISIONS D153 / spec ``2lcqno`` N1 rule that a setid is a SHARED cross-type
      TOPIC label, not an identity (identity is the id6, see ``check.id6-collision`` below), so
      research + specs + backlog + plans on one topic are MEANT to share the token. Do NOT re-add
      a cross-type branch as a "missing" check, and do not add an ``info`` variant of it either:
      spec ``2lcqno`` OQ-01 rejected that from measurement (it narrated the normal state on tens of
      setids per run, which trains a reader to treat correct behavior as remarkable). The
      comparison slot is keyed per ``(type, setid)`` for the same reason: a foreign-type file must
      not occupy the slot a within-type comparison needs;
    * filename IDENTITY-SLOT id6 (DECISIONS.md D140): the ``<id6>`` in a file's
      ``YYYYMMDD-<setid>-NN-<id6>-<slug>`` filename slot is that file's UNIQUE IDENTITY. It is
      validated by the precise rule (so it flags a foreign id6 in the slot but never mass-flags
      conformant files): (a) if the file DECLARES a frontmatter ``- Id:``, its slot id6 MUST EQUAL
      that declared ``- Id:``; (b) if the file declares NO ``- Id:``, its slot id6 MUST NOT equal
      any OTHER file's declared ``- Id:`` NOR any other file's slot id6 (it must be the sole holder
      of that id6). A violation emits ``check.id6-identity-slot`` naming the offending path AND the
      file that actually owns that id6. Legacy ``YYYYMMDD-HHMM-NN-<slug>`` names (no id6 slot) are
      exempt - only a filename whose slot parses as a real id6 via the naming authority is checked.

    THE id6 PASS IGNORES THE LIVENESS FILTER; ITS TWO NEIGHBOURS DO NOT (IPD ``sk7ggr`` E-05). Every
    other rule in this engine skips a RETIRED artifact by default, and for most rules that is right: a
    finished plan's own conformance is nobody's action item. IT IS WRONG FOR IDENTITY. An executed
    plan's id6 is permanently cited across the repository (``Item-Dependencies``, ``From-Backlog``,
    ``From-Spec``, review filenames, prose), so an id6 shared with a terminal artifact is a REAL
    collision and re-minting it is a real defect. Measured before this change: ``aw check all``
    reported 1 id6-collision and MISSED the one whose other side sits in ``executed/``, while
    ``aw doctor`` (which passes ``include_retired=True`` unconditionally) reported it. Two surfaces
    disagreeing about what identity IS is the defect; telling users to remember ``--all`` is not a fix.

    THE WIDENING IS DELIBERATELY NARROW, and this is load-bearing rather than fastidiousness. ONE
    enumeration feeds THREE rules, so widening it wholesale moves all three: measured, that ships
    ``check.setid-collision`` 39 -> 86 (overwhelmingly the LEGITIMATE pattern of a backlog item sharing
    a setid with the plan it graduated into, a policy question owned by backlog ``sjsoqq``) plus two
    ``check.id6-identity-slot`` FALSE POSITIVES (walkthroughs ``zpbx7o`` and ``y5od1h``, whose filename
    slot carries their own plan's id6 while declaring no ``- Id:`` - the documented walkthrough
    convention, not a defect). So the file set is enumerated ONCE, terminal artifacts included, and
    each file is tagged live-or-retired: the id6 pass consumes EVERY file, while the setid pass and the
    identity-slot pass consume only the files the caller's ``include_retired`` would have shown them.
    Do NOT "simplify" this by hoisting ``include_retired=True`` into the enumeration; that is the
    +47-finding regression this structure exists to prevent.
    """
    repo_root = Path(repo_root)
    drift: List[_core.Drift] = []
    seen_ids: Dict[str, str] = {}
    # (type, setid) -> (descriptive-or-None, first-path). KEYED PER TYPE, deliberately, and this is
    # load-bearing rather than tidiness (spec `2lcqno` N5): when the key was the setid ALONE the slot
    # held whichever file was seen FIRST, and `SUPPORTED` iterates `plans` first, so a foreign-type
    # predecessor occupied the slot the within-type descriptive comparison needs and a genuine
    # same-type conflict went unreported. Measured with one plan plus two conflicting specs: the
    # setid-keyed version reported two cross-type findings and never the real spec-vs-spec conflict.
    seen_sets: Dict[tuple, tuple] = {}

    # First gather, for every file, its declared frontmatter Id and its filename identity-slot id6,
    # so the identity-slot rule (below) can be evaluated with global knowledge of who OWNS each id6.
    # A file "record": (path-str, declared_id-or-None, slot_id6-or-None).
    #
    # IPD sk7ggr E-05: the enumeration is ALWAYS terminal-inclusive and each file is TAGGED instead,
    # so the three rules fed by this one loop can have different corpora (see the docstring). The id6
    # pass takes every file; the setid and identity-slot passes take only what the caller asked for.
    records: List[tuple] = []
    for record_type in SUPPORTED:
        for p in _iter_type_files(
            repo_root,
            record_type,
            include_untracked=include_untracked,
            include_retired=True,
        ):  # already deduped by resolved path
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            # IPD `76w6mq`: bounded to the metadata region, so a QUOTED example `- Id:` block is
            # not counted as this file DECLARING that id6 (which manufactured 2 of the 17 findings
            # measured before the fix, between two research docs quoting one plan's metadata).
            declared_id = _read_declared_id(text)
            slot_id6 = _identity_slot_token(p.name)
            # Is this file one the CALLER's liveness setting would have shown? With
            # include_retired=True the answer is always yes and `is_retired` (which reads the file) is
            # never called, so the default sweep pays nothing extra for the tag.
            caller_visible = include_retired or not is_retired(p, record_type)
            if caller_visible:
                records.append((str(p), declared_id, slot_id6))

            # The id6 pass: EVERY file, retired or not. A terminal id6 is permanently cited, so a
            # collision with one is real (docstring, and IPD sk7ggr F-3).
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
            # The setid pass keeps the caller's corpus: widening it would ship the +47 legitimate
            # backlog-shares-its-plan's-setid batch that belongs to `sjsoqq`.
            if not caller_visible:
                continue
            sid, desc = _parse_setid(text)
            if sid:
                set_key = (record_type, sid)
                if set_key in seen_sets:
                    prev_desc, prev_path = seen_sets[set_key]
                    # WITHIN-TYPE descriptive conflict ONLY. One setid carrying two different
                    # descriptives inside ONE type is a genuine inconsistency in that Set's own
                    # name. The cross-type comparison that used to live here was REMOVED per D153 /
                    # spec `2lcqno` N1 (see this function's docstring); it reported the endorsed
                    # normal state as an error.
                    if desc is not None and prev_desc is not None and desc != prev_desc:
                        drift.append(
                            _core.Drift(
                                str(p),
                                "check.setid-collision",
                                f"setid {sid} conflicts with {prev_path} (descriptive: {prev_desc!r} vs {desc!r})",
                            )
                        )
                else:
                    seen_sets[set_key] = (desc, str(p))

    drift.extend(_check_identity_slots(records))
    return drift


def check_id_outside_metadata_region(
    repo_root: Path,
    include_untracked: bool = False,
    include_retired: bool = False,
) -> List[_core.Drift]:
    """Report a metadata-shaped ``- Id: <id6>`` line found OUTSIDE a record's METADATA REGION.

    THE COMPANION TO BOUNDING THE READERS, AND THE REASON BOTH SHIP TOGETHER (IPD ``76w6mq`` E-05,
    maintainer ruling 2026-09-05 "fix AND warn"). Bounding identity extraction to the metadata region
    stops a quoted example block from CLAIMING an id6; on its own, though, it also makes such a line
    invisible. That silence is only correct for one of the two things an out-of-region ``- Id:`` can
    be:

    * a QUOTATION - legitimate cited content, which a repository documenting its own metadata format
      produces by design, and which must NOT be mangled (the fix belongs in the reader, never in the
      document); or
    * a MISPLACED DECLARATION - a record whose real identity sits below its first ``##`` heading,
      where no reader will ever look, so the record is effectively identity-less.

    This rule cannot yet tell them apart, which is exactly why it is ``info``-severity: it makes the
    ambiguity VISIBLE and COUNTABLE without failing a tree for correct behavior. See the registry
    entry for the measurement behind that severity (``warning`` fails the gate; only ``info`` does
    not).

    IT FIRES ON THE SHAPE, NEEDING NO COLLIDING COUNTERPART, which is what makes it strictly stronger
    than the collision rules for this defect class. ``check.id6-collision`` can only speak when TWO
    sides are scannable, so a lone document quoting an id6 whose owner is retired, or quoting an id6
    that exists nowhere at all, produces no collision finding; this rule still reports it.
    """

    repo_root = Path(repo_root)
    drift: List[_core.Drift] = []
    for record_type in SUPPORTED:
        for p in _iter_type_files(
            repo_root,
            record_type,
            include_untracked=include_untracked,
            include_retired=include_retired,
        ):
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            region_len = len(_metadata_region(text))
            for m in _ID_LINE_RE.finditer(text):
                if m.start() < region_len:
                    continue
                line_no = text.count("\n", 0, m.start()) + 1
                drift.append(
                    enrich_drift(
                        _core.Drift(
                            str(p),
                            "check.id6-outside-metadata-region",
                            f"`- Id: {m.group(1)}` at line {line_no} is outside the metadata region",
                        ),
                        observed=(
                            f"a metadata-shaped `- Id: {m.group(1)}` line appears at line {line_no}, "
                            "after this record's metadata region ends"
                        ),
                        required=(
                            "a record declares its identity ONLY in its metadata region (the bullet "
                            "block before the first `##` heading, or the leading `---` fence), so an "
                            "`- Id:` outside it is read by NO identity reader"
                        ),
                        recovery=(
                            "if this is a QUOTED example, no action is needed (it is correctly "
                            "ignored); if it is this record's real identity, move it into the "
                            "metadata region"
                        ),
                    )
                )
    return drift


def _check_identity_slots(records: List[tuple]) -> List[_core.Drift]:
    """Validate the filename identity-slot id6 invariant (D140) over pre-gathered file records.

    ``records`` is a list of ``(path_str, declared_id_or_None, slot_id6_or_None)``. Returns
    ``check.id6-identity-slot`` Drift for each file whose filename identity slot holds an id6 that
    is not that file's own unique identity. See ``check_collisions`` for the precise (a)/(b) rule.

    THIS RULE IS DELIBERATELY BLIND TO THE DECLARED-DUPLICATE SHAPE, AND THAT IS NOT A GAP TO CLOSE
    HERE (IPD ``sk7ggr`` E-03, OQ-01). Two files of DIFFERENT types that both DECLARE and both SLOT
    the same id6 produce ZERO findings from this function, by construction: rule (a) compares each
    file's slot against its OWN declared Id and both agree, and rule (b) is skipped for any file that
    declares an Id. Verified by direct call on exactly that synthetic pair.

    THE FACT IS NOT UNDETECTED, IT IS DETECTED ELSEWHERE. ``check_collisions``'s ``seen_ids`` pass
    reports that same pair as ONE ``check.id6-collision``, which is the correct and sufficient
    finding. The reason the live instance went unseen was never a missing rule: it was the retired
    filter (fixed by E-05, so the id6 pass now enumerates terminal artifacts) and an unbounded
    identity parser reading a ``- Id:`` out of quoted PROSE (owned by IPD ``76w6mq``).

    SO DO NOT "FIX" THIS BY ADDING A DECLARED-DUPLICATE CASE HERE. Doing so would emit
    ``check.id6-collision`` AND ``check.id6-identity-slot`` for one fact, handing an operator two
    findings and two remedies for a single problem. If you are here because a declared duplicate felt
    unreported, check whether you are looking at the DEFAULT sweep's output from before E-05.
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


# ======================================================================================
# findtier Order 02 (`3i6rso`): the declared-identity-absent-from-filename ADVISORY.
#
# WHY THIS EXISTS. `aw find` cannot trust a filename to carry a record's identity, so it keeps a
# mandatory CONTENT fallback that opens every record. That fallback can only ever be retired on
# EVIDENCE that the set of records whose filename omits their declared identity is small and not
# growing - and nothing counted that set. This report is that count. It is ADVISORY by design and
# renames NOTHING: every rename here is a maintainer call per record (see the RuleSpec comment).
#
# THE EXTEND-VERSUS-ADD DECISION (E-06), recorded here because a second identity comparator is the
# defect `check.id6-identity-slot` was written to avoid. That rule ALREADY enforces this rule's
# modern case - "if the file declares a frontmatter `- Id:`, its slot id6 must equal it" - but only
# for a filename whose slot PARSES as a real id6, so a legacy `YYYYMMDD-HHMM-NN-<slug>` name with no
# slot at all is exempt BY CONSTRUCTION. Measured at authoring on this tree: that rule produced ZERO
# findings and covered ZERO of the ten records this report names. DECISION: ADD A SIBLING rather than
# extend it, for two reasons. (1) SEVERITY: `check.id6-identity-slot` is `error` and must stay so (a
# foreign id6 in an id6-bearing slot is a real defect); this population is grandfathered and must be
# `warning`, and one rule id cannot carry two severities without lying to every consumer keyed on it.
# (2) SUBJECT: that rule compares a filename SLOT against a declaration; this one reports a
# declaration that appears NOWHERE in the filename, including names that have no slot. The
# discriminator is REUSED, not reimplemented: `_classify_identity_record` calls the shared
# `_is_real_id6` for exactly the reason F-13 names - `parse_clustered` reports the legacy name
# `20260817-1357-01-assess-...` as conformant with `id6='assess'` and `_ID6_RE` accepts `assess`, so a
# comparator trusting the parsed slot would mis-bucket a real member as modern drift.
#
# FOUR BUCKETS, because the remedies differ completely and a single count would be actively
# misleading on its first run:
#
#   * LEGACY      - a pre-id6-grammar or grandfathered name. Rename is OPTIONAL, a maintainer call.
#   * ARTIFACT    - the declaration is a QUOTED EXAMPLE in the body, not this file's own metadata.
#                   The FILENAME IS CORRECT and no rename is ever suggested; the fix is in the
#                   reader (`cqytxf`/`76w6mq`). Detected BY POSITION, never by record type or field:
#                   measured members span research prompts, a research report, AND a spec, and reach
#                   both the `Id` and `Set` fields, so a type- or field-keyed test would miss them
#                   and send a maintainer to rename an `implemented` spec.
#   * NON-ID      - the declared value is not an identifier at all (measured: a spec declaring the
#                   literal `set: <terse-id>` inside an illustrative code block). No rename can
#                   satisfy it, so none is offered.
#   * DRIFT       - a MODERN clustered name whose metadata simply disagrees with it. This is a real
#                   defect rather than a grandfathering question, so it is reported distinctly.
# ======================================================================================

_IDENTITY_RULE = "check.identity-absent-from-name"

#: The report's stated purpose, emitted on every finding so a count with no purpose is not ignored.
_IDENTITY_PURPOSE = "this is the exception set that forces `aw find`'s content fallback; it is expected to shrink"

# BOTH front-matter dialects, because the corpus uses both: the bullet form on plans/specs/backlog
# and the YAML form on research records. Reading only one silently under-counts.
_IDENT_ID_BULLET_RE = _re.compile(r"(?m)^- Id:[ \t]*(\S+)[ \t]*$")
_IDENT_ID_YAML_RE = _re.compile(r"(?m)^id:[ \t]*(\S+)[ \t]*$")
_IDENT_SET_BULLET_RE = _re.compile(r"(?m)^- Set:[ \t]*(.+?)[ \t]*$")
_IDENT_SET_YAML_RE = _re.compile(r"(?m)^set:[ \t]*(.+?)[ \t]*$")

# The metadata region's terminators for a BULLET-dialect record: the first fenced block or the first
# `##` heading, whichever comes first. A YAML-dialect record's region is its `---` envelope.
_IDENT_FENCE_RE = _re.compile(r"(?m)^[ \t]{0,3}(?:```|~~~)")
_IDENT_H2_RE = _re.compile(r"(?m)^##[ \t]")

# A legal identifier token: kebab lowercase alphanumerics. Anything else (a placeholder like
# `<terse-id>`, whitespace, punctuation) is NOT an identifier and can never be satisfied by a rename.
_IDENT_TOKEN_RE = _re.compile(r"\A[a-z0-9][a-z0-9-]*\Z")

#: `aw rename` takes a plural TYPE, and the suggested command must name the right one or it is worse
#: than no suggestion at all (the plan's F-10). Verified by running each suggested form at authoring.
#: `roadmaps` maps to `research`, NOT to itself: a `.roadmap.md` lives in the research tree and `aw
#: rename roadmaps <id6>` reports "no roadmaps artifact matched" while `aw rename research <id6>`
#: resolves it. The `comms`/`other` types are absent because no `aw rename` route exists for them.
_IDENT_RENAME_TYPE = {
    "plans": "plans",
    "specs": "specs",
    "backlog": "backlog",
    "prompts": "prompts",
    "walkthroughs": "walkthroughs",
    "roadmaps": "research",
    "releases": "releases",
    "research": "research",
}


def _identity_metadata_region(text: str) -> str:
    """Return the leading METADATA REGION of a record's text: the part in which a `- Id:`/`set:`
    line is this file's OWN declaration rather than a quoted example.

    Two dialects, one rule. A record opening with a `---` line is YAML-envelope dialect and its
    region is that envelope (a record whose envelope never closes has NO metadata region, so nothing
    in it is read as a declaration). Otherwise the region runs from the start of the file to the
    first fenced code block or the first `##` heading, whichever comes first.

    THIS IS THE POSITIONAL TEST that makes the ARTIFACT bucket a class rather than a hardcoded list
    of filenames. Verified over the whole corpus at authoring: bounding the read this way preserves
    the declaration of 1171 of 1173 `Id`-declaring records and 1141 of 1146 `Set`-declaring ones,
    and the handful it drops are EXACTLY the quoted-example members - which is the point.

    NOTE the duplication this deliberately accepts: `76w6mq` (pending at authoring) owns a bounded
    identity reader for the RESOLVER. When it lands, this helper should DELEGATE to it rather than
    keep its own bound; until then a report that read whole files would carry a known-false finding
    on five records, which is worse than a bound that will be consolidated.
    """

    lines = text.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        offset = len(lines[0])
        for line in lines[1:]:
            if line.strip() == "---":
                return text[: offset + len(line)]
            offset += len(line)
        return ""  # unterminated envelope: no trustworthy metadata region
    ends = [len(text)]
    for rx in (_IDENT_FENCE_RE, _IDENT_H2_RE):
        m = rx.search(text)
        if m is not None:
            ends.append(m.start())
    return text[: min(ends)]


def _identity_declared_values(text: str):
    """Return ((id_value, id_in_region), (set_value, set_in_region)) for one record's text.

    Each value is the STRIPPED declared token (or None when the field is absent anywhere), and the
    flag says whether the declaration was found inside the metadata region. A value present in the
    full body but NOT in the region is a QUOTED EXAMPLE, which is what the ARTIFACT bucket reports.

    QUOTING IS NORMALIZED HERE, and the case is live rather than hypothetical: one tracked record
    declares ``- Set: `awoptimize` `` with backticks, so an un-normalized comparison invents drift on
    a correctly-named file. Values are compared STRIPPED of backticks and quotes.
    """

    region = _identity_metadata_region(text)
    out = []
    for bullet_re, yaml_re, is_set in (
        (_IDENT_ID_BULLET_RE, _IDENT_ID_YAML_RE, False),
        (_IDENT_SET_BULLET_RE, _IDENT_SET_YAML_RE, True),
    ):
        # THE REGION IS SEARCHED FIRST, ACROSS BOTH DIALECTS, BEFORE THE FULL BODY IS CONSULTED, and
        # the ordering is a fix rather than a preference. A research record declares `set:` in its
        # YAML envelope but QUOTES a plan's `- Set:` bullet later in its body; searching by dialect
        # first meant the quoted BULLET shadowed the file's own YAML declaration, so a record whose
        # real Set is correct was read as an artifact. Region-first means a file's OWN declaration
        # always wins, and the full-body pass exists only to catch a field the record does not
        # actually declare - which is exactly the artifact bucket's definition.
        value = None
        in_region = False
        for haystack, is_region in ((region, True), (text, False)):
            for rx in (bullet_re, yaml_re):
                m = rx.search(haystack)
                if m is None:
                    continue
                raw = m.group(1).strip()
                if is_set:
                    # `- Set: <terse> (<descriptive>)`: the setid is the first token before any '('.
                    head = raw.split("(")[0].strip()
                    raw = head.split()[0] if head.split() else ""
                value = raw.strip("`\"'") or None
                in_region = is_region
                break
            if value is not None:
                break
        out.append((value, in_region))
    return out[0], out[1]


def _identity_name_is_modern(
    filename: str, declared_ids: set, own_id: "str | None"
) -> bool:
    """True iff ``filename`` carries a REAL id6 in its clustered identity slot.

    Reuses the shared `_is_real_id6` discriminator rather than trusting the parsed slot, which is
    load-bearing and not tidiness: `artifact_naming.parse_clustered` reports the LEGACY name
    `20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md` as conformant with `id6='assess'`
    (six lowercase alphanumerics), so a comparator trusting the parse would call that legacy record
    MODERN and bucket it as genuine drift. The permissive parse is used so a research record's
    `.<model>.<kind>` facet (a closed-enum miss for `parse_clustered`) is still recognized as modern.

    ``own_id`` IS CONSULTED, and the case that forced it is measured rather than hypothetical. The
    shared discriminator answers "is this token some file's id6?", which is FALSE for a token that is
    nobody's - so a MODERN name carrying a typo'd slot (`...-01-slotaa-a.ipd.md` declaring
    `- Id: fmbbb1`) would be classified LEGACY and reported as a grandfathered name, when it is in
    fact the exact condition `check.id6-identity-slot` already reports as an ERROR. A file that
    DECLARES an id6 asserts a clustered identity, so its slot is trusted as an identity slot
    unconditionally - the same reasoning `_check_identity_slots`' rule (a) states for itself.
    """

    m = _naming.parse_uniform_permissive(filename)
    if m is None:
        return False
    if _HHMM_RE.match(m.group("set")):
        return False  # legacy YYYYMMDD-HHMM-NN-<slug>, whose HHMM mimics a setid
    if own_id is not None:
        return True
    return _is_real_id6(m.group("id6"), declared_ids)


def _identity_rename_hint(
    record_type: str, selector: str, field: str, modern: bool
) -> str:
    """The exact `aw rename` a maintainer would run for one record, or "" when none applies.

    THE SELECTOR IS THE DECLARED id6 WHEREVER ONE EXISTS, not the filename, and that is the whole
    reason this helper exists rather than an f-string at the call site. Verified at authoring: `aw
    rename plans <legacy-filename> --to-id6` REFUSES with "no plan has Id '<filename>'" (the plans
    resolver is id-directed), while `aw rename plans <id6> --to-id6` resolves and prints the exact
    target name. A suggested command that refuses is worse than no suggestion (the plan's F-10), so a
    filename is only ever used when the record declares no id6 at all.

    `--to-id6` is the legacy-grammar conversion (it mints an id6 and injects it, reusing an existing
    `- Id:`); a MODERN name whose Set segment disagrees is re-clustered with `aw group ... --rename`
    instead, since the identity slot is already correct and only the cluster key is wrong.
    """

    rename_type = _IDENT_RENAME_TYPE.get(record_type)
    if rename_type is None or not selector:
        return ""
    if not modern:
        return f"aw rename {rename_type} {selector} --to-id6 --apply"
    if field == "Set":
        return f"aw group {rename_type} {selector} --set <setid> --rename --apply"
    return f"aw rename {rename_type} {selector} --slug <slug> --apply"


def check_name_identity(
    repo_root: Path,
    include_untracked: bool = False,
    include_retired: bool = False,
) -> List[_core.Drift]:
    """Report every record whose declared `- Id:` or `- Set:` is ABSENT from its own filename.

    ADVISORY (`warning`) and never a rename: see the block comment above for the four buckets, the
    positional artifact test, and the recorded extend-versus-add decision against
    `check.id6-identity-slot`.

    ``include_retired`` HONORS THE ENGINE'S ONE SCOPE CONTRACT rather than overriding it, and the
    consequence is important enough to state: most of this exception set is RETIRED (`executed/`
    plans and terminal specs), so the DEFAULT scope reports the LIVE members only - measured on this
    repository, 4 of 17 - and the FULL historical count needs `aw check --all` (or this function with
    ``include_retired=True``). Overriding the flag here was tried first and is WRONG: retirement
    filters visibility for the whole engine because AGENTS.md forbids editing a plan already in
    `executed/`, so a rule that ignored the flag would report findings whose remedy is not permitted
    on a scope the caller explicitly narrowed. THE COUNT IS STILL AVAILABLE, on one documented flag,
    which is a better trade than one rule with private scope semantics.
    """

    repo_root = Path(repo_root)
    types = list(SUPPORTED.keys())
    if "research" not in types:
        types.append("research")

    # Pass 1: read every record once (full body AND bounded region), so the discriminator below has
    # the global set of declared ids the shared `_is_real_id6` needs.
    scanned: List[tuple] = []
    seen: set = set()
    for record_type in types:
        for p in _iter_type_files(
            repo_root,
            record_type,
            include_untracked=include_untracked,
            include_retired=include_retired,
        ):
            try:
                key = str(p.resolve())
            except OSError:
                continue
            if key in seen:
                continue
            seen.add(key)
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            id_decl, set_decl = _identity_declared_values(text)
            scanned.append((record_type, p, id_decl, set_decl))

    declared_ids = {
        id_decl[0]
        for _t, _p, id_decl, _s in scanned
        if id_decl[0] and id_decl[1] and _ID6_RE.match(id_decl[0])
    }

    # A name that matches NO grammar at all is already reported by `check.name-nonconformant`, whose
    # remedy (rename it to the grammar) SUBSUMES this advisory's. Reporting it here too would
    # double-report one authoring mistake under a second rule id, which is exactly what
    # `check.review-dangling` documents refusing for the same reason. This rule's population is
    # names that are legitimately SHAPED but pre-id6 (grandfathered), not junk.
    junk_names = {
        Path(d.location).name
        for record_type in types
        for d in check_names(
            repo_root,
            record_type,
            include_untracked=include_untracked,
            include_retired=include_retired,
        )
        if d.rule == "check.name-nonconformant"
    }

    drift: List[_core.Drift] = []
    for record_type, p, id_decl, set_decl in scanned:
        if p.name in junk_names:
            continue
        # The selector `aw rename` actually resolves: the record's OWN declared id6 when it has one
        # (and only when it was declared in the metadata region, so a quoted example never becomes a
        # suggested target), else the filename.
        own_id = (
            id_decl[0] if (id_decl[1] and _ID6_RE.match(id_decl[0] or "")) else None
        )
        selector = own_id or p.name
        modern = _identity_name_is_modern(p.name, declared_ids, own_id)
        for field, (value, in_region) in (("Id", id_decl), ("Set", set_decl)):
            if not value or value in p.name:
                continue
            # The `Id` half of a MODERN name is `check.id6-identity-slot`'s subject already, and it
            # reports it at ERROR severity naming both ids AND the file that owns the foreign id6.
            # Re-reporting it here would double-report one mistake under a weaker rule id; this
            # rule's contribution is the population that rule EXEMPTS (a name with no id6 slot) plus
            # the `Set` segment, which no rule checked at all.
            if modern and field == "Id":
                continue
            drift.append(
                _identity_finding(
                    record_type, p, field, value, in_region, modern, selector
                )
            )
    return drift


def _identity_finding(
    record_type: str,
    path: Path,
    field: str,
    value: str,
    in_region: bool,
    modern: bool,
    selector: str,
) -> _core.Drift:
    """Build the one advisory finding for a (record, field) pair, bucketed and with its remedy."""

    # BUCKET PRECEDENCE, which is a decision rather than an accident of ordering. NON-IDENTIFIER is
    # tested FIRST because it is the strongest statement available about the remedy - NO filename
    # could ever satisfy the value - and it holds wherever the declaration sits, so it must not be
    # masked by the positional test. A record can legitimately be BOTH (the measured member is a
    # `<terse-id>` placeholder that also sits inside a fenced schema example), so the positional fact
    # is APPENDED to that finding rather than being allowed to replace it.
    quoted_note = (
        " (the declaration also sits outside the metadata region, in a quoted example)"
        if not in_region
        else ""
    )
    if not _IDENT_TOKEN_RE.match(value):
        bucket = "non-identifier"
        detail = (
            f"declared `{field}: {value}` is not an identifier (a documentation placeholder or "
            f"illustrative value), so no filename can satisfy it{quoted_note}"
        )
        recovery = (
            "no rename is possible: the declared value is not an identifier. If it is a schema "
            "example, move it inside a fenced block so it is not read as a declaration"
        )
    elif not in_region:
        bucket = "artifact"
        detail = (
            f"declared `{field}: {value}` is absent from the filename, but the declaration is a "
            f"QUOTED EXAMPLE in the body rather than this file's own metadata: THE FILENAME IS "
            f"CORRECT and must not be renamed"
        )
        recovery = (
            "no rename: fix the READER that harvests identity from a quoted block (see `cqytxf` / "
            "`76w6mq`), not this document"
        )
    elif modern:
        bucket = "drift"
        detail = (
            f"declared `{field}: {value}` is absent from an otherwise MODERN id6-clustered filename, "
            f"so the name and the metadata genuinely disagree"
        )
        recovery = _identity_rename_hint(record_type, selector, field, True) or (
            "reconcile the filename with the declared metadata"
        )
    else:
        bucket = "legacy"
        detail = (
            f"declared `{field}: {value}` is absent from this pre-id6-grammar filename, so the "
            f"record cannot be located by name; the rename is OPTIONAL and a maintainer call "
            f"(grandfathered, not overdue)"
        )
        recovery = _identity_rename_hint(record_type, selector, field, False) or (
            "converting this name to the id6 grammar is optional and a maintainer call"
        )
    return enrich_drift(
        _core.Drift(
            str(path),
            _IDENTITY_RULE,
            f"[{bucket}] {detail} ({_IDENTITY_PURPOSE})",
        ),
        observed=f"{field}: {value} (filename: {path.name})",
        required=f"the declared {field} appears in the filename, so the record is locatable by name",
        recovery=recovery,
    )


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


def _plan_disposition(repo_root: Path, plan_path: Path) -> Optional[str]:
    """The plan's lifecycle DISPOSITION: the FIRST path component under the plans dir.

    Deliberately the first component, NOT ``plan_path.parent.name``: ``aw archive plans`` shards a
    terminal plan into ``<disposition>/YYYYMM/`` (``plans_archive._shard_target``), so a
    parent-directory test would silently stop recognizing a sharded plan as terminal. This reuses the
    derivation ``plans_index.scan_plans`` already established (``rel.split("/", 1)[0]``) rather than
    inventing a third one. Returns None when the plan cannot be located under any plans dir.
    """
    try:
        resolved = plan_path.resolve()
    except OSError:
        return None
    for plans_dir in _type_dirs(repo_root, "plans"):
        try:
            rel = resolved.relative_to(plans_dir.resolve()).as_posix()
        except (ValueError, OSError):
            continue
        return rel.split("/", 1)[0] if "/" in rel else None
    return None


def _receipt_is_live(repo_root: Path, plan_path: Path, receipt: Dict) -> bool:
    """True when ``receipt`` can still describe an IN-FLIGHT execution (IPD rygds7 E-01/E-02).

    A begin receipt is execution AUTHORITY for one in-flight plan. Once that authority is spent the
    receipt must no longer drive a SCOPE ADVISORY about the current working tree, because the frozen
    base it carries no longer describes work any live execution owns. Two cases are rejected:

    * TERMINAL PLAN - the plan file sits in a terminal lifecycle directory (``plans.TERMINAL``:
      executed/superseded/not-executed). Disposition is read from the plan's PATH, not from its
      ``Status:`` text, because the directory is the authoritative encoding (the lifecycle setters
      move the file as the authoritative act) and status text may legitimately lag the move.
    * UNREACHABLE BASE - ``base_head`` is not an ancestor of HEAD, so the frozen baseline does not
      describe this history and a diff against it is meaningless.

    IMPORTANT, and the reason this is a liveness test for an ADVISORY only: a terminal plan's receipt
    is NOT necessarily garbage. A finalize journal in ``committed-incomplete`` re-runs finalize
    against a plan ALREADY in ``executed/`` (``ipd_lifecycle.finalize`` resume path), and the receipt
    is consumed only on the clean-complete path. So "terminal" licenses IGNORING the receipt here; it
    never licenses deleting it.

    FAIL SAFE, NOT FAIL OPEN (E-02): when liveness cannot be determined (git unavailable, unreadable
    path, ``merge-base`` error) the receipt is treated as NOT live and skipped. The asymmetry is
    deliberate and must not later be "corrected": a false refusal blocks a legitimate commit, while a
    missed advisory is recoverable, and this rule is explicitly documented as best-effort local
    FEEDBACK rather than an authority boundary (``hooks/precommit_scope_gate.py:17-19``: "git hooks
    are LOCAL, not cloned by default, and skippable with ``--no-verify``. This is OPT-IN best-effort
    FEEDBACK, not an authority boundary; the authoritative boundary is phase-5 CI running the same
    engine."). WHAT THIS DIRECTION COSTS, stated plainly: an environment where git cannot run
    silently disables this rule entirely rather than reporting that it could not run. That is
    acceptable ONLY because the authoritative boundary is CI (``.github/workflows/tests.yml`` runs
    ``aw check`` fail-closed) and NOT this local rule.

    WHAT THESE TWO TESTS DO **NOT** COVER, stated because their absence was mistaken for exhaustive
    and cost a graduation to discover (rcptstale ``wmnmei``, backlog ``v880xk``). LIVENESS IS NOT
    DISTANCE, and distance is not staleness. A plan sitting in ``pending/`` whose ``base_head`` IS an
    ancestor of HEAD passes BOTH tests here while being arbitrarily far behind: measured 2026-09-22
    across six live receipts, 4 to 344 non-merge commits, five of the six holding a lane worktree that
    was being actively worked. Nothing about such a base is stale in the sense of WRONG - it is
    correctly frozen for an execution still in flight - so no third test was added here. The defect
    those receipts produced was MISATTRIBUTION rather than spent authority: all 350 findings named
    OTHER agents' commits, because the advisory compared the frozen base against whichever tree the
    command happened to run in. That is fixed in :func:`check_scope_drift` by selecting the EXECUTION
    TREE (see :func:`_plan_execution_tree`), not by widening liveness, and deliberately so: this
    predicate answers "is this authority spent", which is a different question from "which tree does
    this authority describe".
    """
    from agent_workflows import plans as _plans

    try:
        disposition = _plan_disposition(repo_root, plan_path)
        if disposition is not None and disposition in _plans.TERMINAL:
            return False
        base_head = str(receipt.get("base_head") or "").strip()
        if not base_head:
            return False
        rc, _out, _err = _git_capture(
            repo_root, ["merge-base", "--is-ancestor", base_head, "HEAD"]
        )
        if rc != 0:
            return (
                False  # unreachable/unknown base, or git could not answer -> not live
            )
    except Exception:
        # Fail safe (see the docstring): an undeterminable liveness is treated as NOT live. This
        # local `except` is deliberate and must NOT be left to the aggregator's blanket
        # `except Exception` in `check_commit_invariants`, which would also swallow a genuine bug in
        # the comparison below.
        return False
    return True


#: How many offending paths a collapsed `check.scope-drift` finding NAMES before it tails off into
#: "and N more". Bounded rather than unlimited so one finding stays readable in a pre-commit hook's
#: stderr, and never zero: a finding that reports only a number is unactionable, which is half the
#: defect the collapse exists to fix (rcptstale `wmnmei` E-05).
_SCOPE_DRIFT_PATHS_NAMED = 10


def _summarize_paths(paths: Sequence[str]) -> str:
    """Render offending paths for ONE collapsed finding: every path, or the first N and a count tail.

    The tail says how many were withheld, so the reader always learns the true total rather than
    silently seeing a truncated list. Total is recoverable from the finding either way, because the
    detail states the count separately.
    """
    named = list(paths[:_SCOPE_DRIFT_PATHS_NAMED])
    rendered = ", ".join(repr(p) for p in named)
    remainder = len(paths) - len(named)
    if remainder > 0:
        rendered += f", and {remainder} more"
    return rendered


def _plan_execution_tree(
    repo_root: Path, plan_id: str, base_head: str
) -> Optional[Path]:
    """The TREE whose changes this plan's frozen ``base_head`` can honestly be compared against.

    Returns the plan's ISOLATED LANE WORKTREE when one exists and the frozen base is an ancestor of
    that lane's HEAD, and ``None`` otherwise. ``None`` means "no tree this advisory may speak about",
    and :func:`check_scope_drift` then reports NOTHING for the plan.

    WHY A TREE AND NOT A BASELINE (rcptstale ``wmnmei`` OQ-01, maintainer ruling 2026-09-10). The
    advisory's subject is a lane-isolated execution's OWN tree. Asked which of five candidate
    BASELINES the rule should compare against (the frozen base as-is, the merge-base, the plan's own
    commits, an age-gated skip, or commit-cohesion attribution), the maintainer rejected the axis:
    "This was intended to work on things like IPDs worked on in isolated worktrees not in items worked
    on in main ... I don't see a way to do this in main if more than one entity (human or agent) is
    working on main." That is correct, and it is why cohesion attribution was WITHDRAWN rather than
    deferred: measured 2026-09-22 it cut 350 findings to 164, but none of those 164 is verified to be
    the author's own work, so it would have bought quiet by compressing a misdirected measurement.
    Measuring the lane yields the answer on EVIDENCE: for the same six receipts the lane-measured
    out-of-scope counts were 0, 1, 5, 9 and 0, with one plan having no lane at all.

    ACCEPTED COST, stated because it is a REAL loss of coverage and nobody may later reintroduce a
    main-checkout comparison by calling it an oversight. Work performed by hand DIRECTLY in a shared
    main checkout now gets NO scope advisory at all. The maintainer accepted that explicitly, on the
    ground that no honest attribution exists there when several parties share one tree, and declined
    the offered variant that additionally printed a "scope not checked, not lane-isolated" line in
    favor of the plain silent form.

    THE ANCESTRY CHECK IS NOT REDUNDANT with :func:`_receipt_is_live`, which asks about THIS tree's
    HEAD. A lane can be cut from a DIFFERENT commit than the receipt froze (``allocate_worktree``
    attempt-scopes a STALE or HOLDS-WORK lane rather than adopting it, so lane and receipt legitimately
    disagree), and measured 2026-09-22 one of six contributors (``lc4unl``) was exactly that shape. A
    ``base..HEAD`` diff across such a fork would attribute main's own intervening commits to the plan,
    which is the very defect this function exists to remove, so an unusable lane base reports NOTHING.

    Single-tree checkouts and temp-repo fixtures are unaffected in the case that matters: a plan with
    no lane is silent, which is the rule's new contract rather than a fallback.
    """
    from agent_workflows import worktree_lease as _lease

    try:
        state = _lease.inspect_lane(Path(repo_root), plan_id)
        lane = state.worktree_path
        if lane is None or not lane.is_dir():
            return None
        rc, _out, _err = _git_capture(
            lane, ["merge-base", "--is-ancestor", base_head, "HEAD"]
        )
        if rc != 0:
            return None  # lane cut from a different base: the diff would not be this execution's
    except Exception:
        # Lane resolution is best-effort DISCOVERY, not an authority boundary, and the whole body is
        # guarded for the same reason `_receipt_is_live` fails safe: a rule that cannot establish its
        # SUBJECT must not invent one. Guarding the whole body rather than only the inspection is
        # deliberate - the ancestry probe shells out to git too, so an environment where git cannot
        # run must reach the same silent answer by either route. See `_receipt_is_live` for the cost
        # this direction accepts.
        return None
    return lane


def check_scope_drift(
    repo_root: Path, include_untracked: bool = False
) -> List[_core.Drift]:
    """Declared-file-scope drift (agentadhere Phase 3 E-02; catalog I-01).

    For each plan that has a LIVE begin receipt, compare the paths this execution changed since the
    frozen base against the plan's declared Scope-Paths, REUSING the finalize scope helpers
    (``_paths_changed_by_this_execution``/``_scope_match``/``_frozen_scope_paths``/
    ``_is_implicitly_allowed``) - no forked comparator. A changed path outside the allowlist is
    flagged. A ``grandfathered``/absent Scope-Paths carries no allowlist (empty frozen list), so it
    is advisory-satisfied (never hard-flagged), honoring the sentinel.

    LIVE is checked by ``_receipt_is_live`` and is narrower than "a receipt exists" (IPD rygds7): a
    receipt is IGNORED when (1) its plan sits in a TERMINAL lifecycle directory
    (executed/superseded/not-executed, read from the plan's path so a ``<disposition>/YYYYMM/`` shard
    still counts), or (2) its frozen ``base_head`` is NOT an ancestor of HEAD, so the baseline no
    longer describes this history. Both cases are receipts that cannot describe work in progress, and
    comparing the whole working tree against them attributed other agents' uncommitted files to a
    finished plan. Liveness FAILS SAFE (undeterminable -> skip); see ``_receipt_is_live`` for the
    rationale and its cost. Ignoring a terminal plan's receipt here is an ADVISORY decision only and
    is NOT a claim that the receipt is dead - it may still be required by an unfinished finalize
    transaction, and nothing here deletes one.

    WHICH TREE IS MEASURED IS PART OF THE RULE (rcptstale ``wmnmei``, backlog ``v880xk``, maintainer
    ruling 2026-09-10). The comparison runs against the plan's ISOLATED LANE WORKTREE, resolved by
    :func:`_plan_execution_tree`, and a plan with no usable lane is reported on NOT AT ALL. Before
    this, the rule diffed the frozen base against whichever tree the command happened to run in, which
    in a shared checkout is every co-worker's commits: measured 2026-09-22 at HEAD ``132e8333``, 350
    findings across six plans (216/94/21/11/6/2), of which 350 of 350 were COMMITTED intervening
    history and 0 were working-tree changes, while the same six measured in their own lanes yielded
    9/5/1/0 and two plans with no usable lane. The accepted cost is that hand work in a shared main
    checkout gets no advisory at all; see :func:`_plan_execution_tree` for why, and do not
    reintroduce a main-tree comparison on the argument that coverage was lost by accident.

    ONE FINDING PER PLAN, NOT ONE PER PATH. The finding carries the COUNT and the offending paths in
    its detail (bounded, with an explicit "and N more" tail) rather than multiplying into one Drift per
    file. A single frozen base used to emit one finding per intervening file, which is how 350 findings
    came from six causes and how a real signal became volume readers learn to skip. The collapse is
    UNCONDITIONAL (no threshold): a threshold is exactly the kind of unprincipled cutoff ``v880xk``
    rejected for receipt expiry, and the measured distribution shows no long tail of small honest
    drifts a threshold would preserve. The paths are NEVER dropped, because a plan genuinely touching
    three undeclared files must still say WHICH three; only their repetition as separate findings is.
    ``(rule, location)`` is unchanged by construction - the location was already the plan file - which
    is what ``tests/test_ci_check_parity.py`` compares, and ``recovery`` stays populated because the
    opt-in pre-commit gate prints that field verbatim as its teaching message.
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
        if not _receipt_is_live(repo_root, p, receipt):
            continue  # spent authority (terminal plan / unreachable base) -> not an in-flight scope
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
        # WHICH TREE: the plan's isolated lane, or nothing at all. See `_plan_execution_tree`.
        exec_tree = _plan_execution_tree(repo_root, plan_id, base_head)
        if exec_tree is None:
            continue  # not lane-isolated (or the lane's base is unusable) -> no honest subject
        changed = _life._paths_changed_by_this_execution(exec_tree, base_head)
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
        offenders = sorted(set(out_of_scope))
        if not offenders:
            continue
        drift.append(
            enrich_drift(
                _core.Drift(
                    str(p),
                    _SCOPE_DRIFT_RULE,
                    f"{len(offenders)} changed path"
                    + ("s are" if len(offenders) != 1 else " is")
                    + " outside the plan's declared Scope-Paths: "
                    + _summarize_paths(offenders),
                ),
                observed=f"changed ({len(offenders)}): " + _summarize_paths(offenders),
                required="a change within the declared Scope-Paths: "
                + ", ".join(scope_paths),
                recovery="restrict the change to Scope-Paths, or declare the path in the plan's "
                "Scope-Paths (then re-`aw ipd begin`), or reconcile it at `aw ipd finalize`",
            )
        )
    return drift


# ======================================================================================
# wslayout Order 05 (30jug9), spec kw5y2s Section 6.2: workspace layout health.
#
# ONE loader and ONE rule, shared by `aw layout` (which needs to KNOW which document it is
# showing) and by `aw check` / `aw doctor` (which need to REPORT that the document is absent or
# stale). Sharing the loader is the point: if the inspector and the checker parsed the emitted
# file differently, the CLI could display a document the checker calls invalid.
# ======================================================================================


def load_emitted_layout(repo_root: Path) -> Tuple[Optional[Dict], str]:
    """Load the install-emitted `.aw/system/layout.json`.

    Returns ``(document, error)``. Exactly one side is meaningful: on success ``document`` is the
    parsed mapping and ``error`` is ``""``; on failure ``document`` is ``None`` and ``error`` is a
    short human-readable reason.

    ABSENCE IS NOT AN ERROR HERE, and that asymmetry is deliberate. Spec Section 2.3 makes the file
    GITIGNORED, so a fresh clone legitimately has none; this loader therefore reports absence with
    the plain reason ``"absent"`` and lets each caller decide what it means (`aw layout` falls back
    to the in-process model; `aw check` reports it only when the workspace is actually installed).
    A file that exists but is unreadable, unparseable, or not a JSON OBJECT is a genuinely different
    condition and gets its own reason string.
    """

    import json

    target = Path(repo_root) / _engine.AW_LAYOUT_JSON_PATH
    if not target.is_file():
        return None, "absent"
    try:
        raw = target.read_text(encoding="utf-8")
    except OSError as exc:
        return None, "unreadable: {0}".format(exc)
    try:
        doc = json.loads(raw)
    except ValueError as exc:
        return None, "invalid JSON: {0}".format(exc)
    if not isinstance(doc, dict):
        return None, "not a JSON object (got {0})".format(type(doc).__name__)
    return doc, ""


def check_system_layout(repo_root: Path) -> List[_core.Drift]:
    """The workspace layout presence/drift rule (spec kw5y2s Section 6.2).

    Emits at most ONE finding, in one of two flavors:

    * ``check.system-layout-missing`` - the workspace is INSTALLED but `.aw/system/layout.json`
      (or its sibling schema) is absent, so a non-Python consumer has nothing to read.
    * ``check.system-layout-drift`` - the document is present but unparseable, structurally
      invalid against the model's own required keys, or its ``framework_version`` disagrees with
      the installed `.aw/system/VERSION`. The version comparison is the ONLY way a stale emitted
      file is detectable at all: it is gitignored, so there is no diff to review.

    SILENT WHEN THE WORKSPACE IS NOT INSTALLED. The gate is `.aw/system/VERSION`, the same install
    marker `engine.read_installed_version` consults. Three states are distinguished exactly as
    30jug9 E-02 requires: (a) no marker -> NO finding (never installed, or a deliberately-legacy
    `.agents/` layout, which `engine.emit_layout_artifacts` also skips); (b) marker present and the
    document absent -> ``missing``; (c) marker present and the document present but stale or
    invalid -> ``drift``. Without gate (a) every fresh clone would fail `aw check` by design, since
    the emitted artifacts are gitignored and therefore never present until an install runs.

    Read-only and deterministic: it reads at most three files and writes nothing.
    """

    root = Path(repo_root)
    installed_version = _engine.read_installed_version(root)
    if not installed_version:
        return []  # case (a): not an installed AW workspace; nothing can be missing or stale

    json_rel = _engine.AW_LAYOUT_JSON_PATH
    schema_rel = _engine.AW_LAYOUT_SCHEMA_PATH
    recovery = "run 'aw install {0}' to regenerate the emitted layout document".format(
        root
    )

    doc, err = load_emitted_layout(root)
    if doc is None and err == "absent":
        return [
            enrich_drift(
                _core.Drift(
                    json_rel,
                    "check.system-layout-missing",
                    "installed workspace (version {0}) has no emitted layout document; "
                    "non-Python consumers cannot read the hierarchy until an install "
                    "regenerates it".format(installed_version),
                ),
                observed="absent",
                required="present (emitted by 'aw install')",
                recovery=recovery,
            )
        ]
    if doc is None:
        return [
            enrich_drift(
                _core.Drift(
                    json_rel,
                    "check.system-layout-drift",
                    "emitted layout document is unusable ({0})".format(err),
                ),
                observed=err,
                required="a readable JSON object",
                recovery=recovery,
            )
        ]

    # Structural validity is checked against the MODEL's own required keys rather than a
    # hand-copied list, so a future schema change cannot leave this rule asserting a stale shape.
    from agent_workflows import layout as _layout

    model = _layout.build_default_layout()
    required = model.to_schema().get("required") or []
    missing_keys = [key for key in required if key not in doc]
    if missing_keys:
        return [
            enrich_drift(
                _core.Drift(
                    json_rel,
                    "check.system-layout-drift",
                    "emitted layout document is missing required key(s): {0}".format(
                        ", ".join(sorted(missing_keys))
                    ),
                ),
                observed="missing {0}".format(", ".join(sorted(missing_keys))),
                required="every key required by the current layout schema",
                recovery=recovery,
            )
        ]

    if doc.get("schema_version") != model.schema_version:
        return [
            enrich_drift(
                _core.Drift(
                    json_rel,
                    "check.system-layout-drift",
                    "emitted layout document declares schema_version {0!r}, but this "
                    "framework emits {1!r}".format(
                        doc.get("schema_version"), model.schema_version
                    ),
                ),
                observed=str(doc.get("schema_version")),
                required=str(model.schema_version),
                recovery=recovery,
            )
        ]

    emitted_version = doc.get("framework_version")
    if emitted_version != installed_version:
        return [
            enrich_drift(
                _core.Drift(
                    json_rel,
                    "check.system-layout-drift",
                    "emitted layout document is stale: framework_version {0!r} does not "
                    "match the installed {1} ({2!r})".format(
                        emitted_version, _engine.VERSION_FILE, installed_version
                    ),
                ),
                observed=str(emitted_version),
                required=installed_version,
                recovery=recovery,
            )
        ]

    # The SCHEMA sibling is reported last and as `missing`, not `drift`: the document itself is
    # fine, and the absent artifact is the local validation surface spec Section 6.1 item 3 emits
    # alongside it, so the remedy is the same regeneration.
    if not (root / schema_rel).is_file():
        return [
            enrich_drift(
                _core.Drift(
                    schema_rel,
                    "check.system-layout-missing",
                    "emitted layout document is present and current, but its JSON Schema "
                    "sibling is absent, so a non-Python consumer cannot validate it locally",
                ),
                observed="absent",
                required="present (emitted by 'aw install')",
                recovery=recovery,
            )
        ]

    return []


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
    * ``check.scope-drift`` (``check_scope_drift``) - for a plan with a LIVE begin receipt, a
      changed path outside its declared ``Scope-Paths`` (findings 5.3: enforce the staged-paths-
      within-declared-scope INVARIANT, not the command syntax). LIVE is verified, not assumed (IPD
      rygds7): a receipt is IGNORED when its plan is in a TERMINAL lifecycle directory or when its
      frozen ``base_head`` is not an ancestor of HEAD, since neither can describe an in-flight
      execution. That liveness test fails SAFE (undeterminable -> skip), consistent with this being
      best-effort local feedback; see ``_receipt_is_live``. The comparison measures the plan's
      ISOLATED LANE WORKTREE and is SILENT for a plan that has none (rcptstale ``wmnmei``), so hand
      work in a shared main checkout is NOT gated here; and it emits ONE finding per plan carrying
      the count and the offending paths, not one per path.

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
    include_retired: bool = False,
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
                    include_retired=include_retired,
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
                include_retired=include_retired,
            )
        )
    if "content" in kinds:
        drift.extend(
            check_content(
                repo_root,
                record_type,
                legacy=legacy,
                include_untracked=include_untracked,
                include_retired=include_retired,
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
    include_retired: bool = False,
) -> List[_core.Drift]:
    """Fan out check_type over the given types (or every SUPPORTED type for the ['all'] sentinel),
    concatenating Drift; unsupported types are skipped. The ['all'] sentinel implies
    collisions=True; the cross-tree collision scan is appended exactly ONCE (never per type).

    WHEN THE COLLISION SCAN IS SKIPPED, THE REPORT SAYS SO (IPD ``sk7ggr`` E-06). A per-type run does
    not perform the cross-tree scan, and before this change it rendered an UNQUALIFIED
    ``CONFORMS / errors 0 warnings 0`` and exited 0 over a tree that genuinely held an id6 collision:
    measured, ``aw check research`` told an author their tree was fine while ``uyeko5`` was duplicated
    inside it. A silent clean bill of health is the defect, so a skipped scan now emits ONE
    ``info``-severity ``check.collisions-not-checked`` finding naming the command that does check.

    WHY ``info`` AND NOT AN ERROR, i.e. why OQ-02's cheapest option is the right one. The three
    candidates were: run the repo-wide scan on every per-type check (correct but makes every narrow
    command pay a whole-repository inventory, which is how a check gets removed from a hook later);
    hide it behind a flag (a flag nobody passes removes no silence); or STATE the limit. The third
    costs one line, cannot slow anything down, and fully removes the false clean, which is the actual
    failure mode. ``drift_exit_code`` ignores ``info``, so a conformant per-type run still exits 0 and
    no existing caller's exit contract changes.
    """
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
                include_retired=include_retired,
            )
        )
    if not collisions:
        # IPD sk7ggr E-06: name the limit rather than rendering an unqualified clean. See this
        # function's docstring for why this is `info` and not an error.
        #
        # GATED ON HAVING ACTUALLY CHECKED SOMETHING. A target list containing no SUPPORTED type
        # (`check_types(['bogus'])`) checks nothing at all, and the fan-out deliberately returns []
        # there so one unknown member cannot poison a multi-type sweep. Announcing "collisions were not
        # examined" on that run would be noise attached to a run that examined NOTHING, and it would
        # also convert that deliberate empty result into a non-empty one. The notice exists to qualify
        # a CLEAN REPORT, so it is emitted only when there was a report to qualify.
        checked = [t for t in target if t in SUPPORTED]
        if checked:
            # The location is the SENTINEL `<collisions>` rather than a type name, following the
            # established `<git>`/`<layout>`/`<attention>` convention in `doctor._categorize_drift`.
            # WHY: this finding is about the SCAN, not about any file. Passing a bare type name made
            # the human renderer's path-resolving fallback guess a directory for it and attach an
            # unrelated per-type "Fix:" line; a sentinel is excluded from that path search by
            # construction, so the report stays truthful without editing `doctor.py` (which is outside
            # this plan's declared Scope-Paths).
            # The DETAIL is kept under 60 characters deliberately. `doctor.build_remediation` has no
            # case for this rule (that module is outside this plan's Scope-Paths), and its generic
            # fallback uses the detail AS THE TITLE when it is short enough, falling back to the bare
            # rule id otherwise. So a short detail is what makes the human report read as a sentence
            # about the scan instead of the rule id alone. The full explanation lives in
            # `observed`/`required`, which the agent-mode finding shape carries.
            drift.append(
                _core.Drift(
                    "<collisions>",
                    "check.collisions-not-checked",
                    "cross-tree collisions NOT checked by a per-type run",
                    observed=(
                        "a per-type check does not run the cross-tree collision scan, so a clean "
                        "result here does NOT mean collision-clean"
                    ),
                    required="run `aw check all` to validate cross-tree id6/setid uniqueness",
                    recovery="aw check all",
                    severity="info",
                )
            )
    if collisions:
        drift.extend(
            check_collisions(
                repo_root,
                include_untracked=include_untracked,
                include_retired=include_retired,
            )
        )
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
        # detrun bmh754: a dangling From-Spec link is the SPEC-side twin of the From-Backlog scan
        # directly above, so it rides the same once-per-full-sweep seam. Its own try/except (rather
        # than sharing the one above) so a failure in either scan cannot suppress the other.
        try:
            drift.extend(check_from_spec_dangling(repo_root))
        except Exception:
            pass
        # revgate Order 01 (15zvu6): a review file pointing at a nonexistent plan is the same class
        # of cross-tree ref check, run once in the full sweep. ADVISORY (`warning`), so it reports
        # without setting an exit code.
        try:
            drift.extend(check_review_dangling(repo_root))
        except Exception:
            pass
        # revsweep 5slbpi E-04: the OTHER half of the `->reviewed` attestation. The setter refuses the
        # transition; this rule catches a spec that reached `reviewed` some other way (a hand edit, a
        # pre-existing file). Same shared predicate, so the refusal and the finding cannot disagree.
        try:
            drift.extend(check_spec_review_attestation(repo_root))
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
        # nobugship rgaasb E-02: a LIVE bug-kind item with no release gate. Rides THIS
        # once-per-full-sweep seam beside its I-07 siblings above, and the placement is a decision with
        # two measured consequences rather than a default.
        #
        # (1) IT IS DELIBERATELY *NOT* ADDED INSIDE `check_release_gate_consistency`, even though that
        # would be the tidier-looking home. That function is composed by `check_commit_invariants`, the
        # opt-in PRE-COMMIT aggregator, and every rule in it is COMMIT- or RECEIPT-scoped for a reason
        # (its own Rule 1 examines only STAGED items). This rule is WHOLE-TREE, so putting it there
        # would refuse a commit because some OTHER party's bug item elsewhere in the tree is ungated -
        # exactly the shared-checkout failure AGENTS.md warns against.
        #
        # (2) IT IS THEREFORE NOT REPORTED BY `aw check backlog`, and that is a known, stated cost, not
        # an oversight: `check_type('backlog')` never reaches this block, so the whole I-07 family is
        # invisible to the type-scoped command (measured: `check_types(repo,['backlog'])` reports 0
        # while `['all']` reports the family). Wiring it into the backlog content path instead was
        # rejected because it would surface this ONE rule while its four siblings stayed invisible on
        # the same command, which is a more confusing contract than "the family lives on the full
        # sweep". Consumers must use `aw check` / `aw check all`.
        #
        # Own try/except, per the established pattern in this block, so a failure here cannot suppress
        # any other rule.
        try:
            drift.extend(check_live_bug_gate(repo_root))
        except Exception:
            pass
        # wslayout Order 05 (30jug9), spec kw5y2s Section 6.2: the emitted layout document is absent
        # or stale. A WORKSPACE-level rule, not a per-type one, so it rides this once-per-full-sweep
        # seam exactly like its neighbors above: fanning it out over `check_type` would emit the same
        # finding once per record type and would also fire it on `aw check plans`, where the state of
        # a generated system file is irrelevant. Own try/except, per the established pattern, so a
        # failure here cannot suppress any other rule.
        try:
            drift.extend(check_system_layout(repo_root))
        except Exception:
            pass
        # findtier Order 02 (`3i6rso`) E-04: the declared-identity-absent-from-filename advisory.
        # Rides THIS once-per-full-sweep seam, beside its naming-family neighbours, and the placement
        # is the plan's OQ-01 decision on a measured count rather than a default: 18 findings against
        # a tree already reporting 323, so a sweep rule is not a flood, and the sweep is the surface
        # agents and CI already run, which is what lets the count be WATCHED over time (a flag nobody
        # runs would be close to not shipping it). It is CROSS-TREE (every record type at once), so
        # fanning it out over `check_type` would emit each finding once per type. Own try/except, per
        # the established pattern here, so a failure cannot suppress any other rule.
        try:
            drift.extend(
                check_name_identity(
                    repo_root,
                    include_untracked=include_untracked,
                    include_retired=include_retired,
                )
            )
        except Exception:
            pass
        # idcapture Order 01 (`76w6mq`) E-05: a metadata-shaped `- Id:` outside the metadata region.
        # Rides THIS once-per-full-sweep seam beside its identity-family neighbours above, for the
        # same two reasons they do: it is CROSS-TREE (every record type at once), so fanning it out
        # over `check_type` would emit each finding once per type; and the full sweep is the surface
        # agents and CI already run, which is what lets the count be WATCHED rather than merely
        # available behind a flag nobody passes. `info`-severity, so it cannot turn a green tree red.
        # Own try/except, per the established pattern here, so a failure cannot suppress another rule.
        try:
            drift.extend(
                check_id_outside_metadata_region(
                    repo_root,
                    include_untracked=include_untracked,
                    include_retired=include_retired,
                )
            )
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
# wkindname ng2blv: FULL-LINE anchored on `- Work-Kind:` so it can never match the unrelated
# `- Gate-Kind:` field nor an IPD's REQUIRED structural `- Kind:` (both are distinct vocabularies).
_ITEM_WORK_KIND_RE = _re.compile(r"(?m)^- Work-Kind:[ \t]*(\S+)[ \t]*$")
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


# --------------------------------------------------------------------------------------
# graduate Order 01 (`jxxec8`): the REVERSE direction of the source link.
#
# `check.from-backlog-dangling` and `check.from-spec-dangling` ask the FORWARD question ("does THIS
# artifact's source link resolve?"). Nothing asked the reverse ("what already exists for this
# source?"), so whoever graduates a spec or backlog item had no way to see that the source already
# has plans. Measured at authoring: 33 sources carry MORE THAN ONE artifact, the largest being spec
# `25kzda` with ten, and spec `6m4kow` (the motivating case of backlog `6h7y2y`) already had three
# executed plans when that item was filed, two of whose premises had therefore already shipped.
#
# PLANS **AND** SPECS, NOT PLANS ONLY. A spec is an "equally valid gate carrier" (AGENTS.md), which
# is exactly why `find_from_backlog_artifacts` above exists: the handoff route once scanned plan
# IPDs only, so a spec-first graduation was invisible. Measured, SIX spec records carry a source
# link and they sit on the biggest clusters (`6m4kow`->`25kzda`, `77tr3o`->`kxkc04`,
# `c4gd2h`->`kjzlgw`, `7ckptx`->`vqv9im`, ...), so a plans-only index would answer "what exists for
# 25kzda" with nine plans and stay silent about the spec that already addresses it.
#
# EVERY SOURCE BULLET, NOT THE FIRST MATCH, and this is a MEASURED requirement. Six plans carry BOTH
# a `From-Backlog:` and a `From-Spec:` bullet (the four `orchretire` plans plus `h0zljh` and
# `4fodkt`), so the single-match `.search` the forward readers use - correct for THEIR question -
# would drop one edge per dual-link plan and under-report two real clusters. Hence `finditer`.
#
# ONE PASS OVER THE CORPUS, NOT ONE PASS PER SOURCE. `find_from_backlog_artifacts` is the right
# shared lookup for a SINGLE backlog id6 and is reused by `graduation_cluster` below for a
# cross-check; it cannot build the whole reverse map, because calling it per source re-walks the
# entire tree per source (the cost `plan_gates_by_backlog` already works around further down with a
# single-pass index). This builds the same single-pass shape and reuses the SAME field readers
# (`_META_FROM_BACKLOG_RE`, `_ITEM_FROM_SPEC_RE`) and the SAME iterators (`_iter_plan_ipds`,
# `_iter_spec_records`); it adds NO third parser for either field and NO new tree literal.
# --------------------------------------------------------------------------------------

#: The artifact types the reverse index covers, in report order. Plans first, mirroring
#: `find_from_backlog_artifacts`, so a cluster reads plan-then-spec.
GRADUATION_ARTIFACT_TYPES: Tuple[str, ...] = ("plan", "spec")

#: The two source KINDS a `From-*` bullet can name.
GRADUATION_SOURCE_KINDS: Tuple[str, ...] = ("backlog", "spec")


class GraduationArtifact(NamedTuple):
    """One artifact citing a source, as the pre-graduation view reports it.

    artifact_type: 'plan' | 'spec' (a cluster may MIX them, and `to-review` means a different thing
                   on each, so the type is carried rather than inferred from the path).
    id6:           the artifact's declared `- Id:`, or '' when it declares none (legacy specs).
    status:        its `- Status:` value, or '' when unreadable. This is what distinguishes
                   "already built" from "in flight", which is the whole point of the view.
    setid:         its `- Set:` terse id, or ''. One Set with many Orders is legitimate
                   decomposition; several DIFFERENT Sets is the case a human must look at.
    path:          repo-relative path, so the reader can open it.
    """

    artifact_type: str
    id6: str
    status: str
    setid: str
    path: str


def build_graduation_reverse_index(
    repo_root: Path,
) -> Dict[Tuple[str, str], List[GraduationArtifact]]:
    """Map every source `(kind, id6)` to the PLANS AND SPECS whose `From-*` bullet names it.

    ``kind`` is ``'backlog'`` or ``'spec'`` (i.e. which of the two link fields carried it), so a
    backlog item and a spec that happen to share an id6 prefix can never be conflated.

    Built in ONE pass over both iterators; every source bullet on an artifact is indexed, not the
    first. Artifacts are yielded plans-before-specs and path-sorted within a type, which makes the
    output stable for a test that asserts membership rather than order.
    """
    index: Dict[Tuple[str, str], List[GraduationArtifact]] = {}
    for artifact_type, iterator in (
        ("plan", _iter_plan_ipds),
        ("spec", _iter_spec_records),
    ):
        for path, text in iterator(repo_root):
            sources: List[Tuple[str, str]] = [
                ("backlog", m.group(1)) for m in _META_FROM_BACKLOG_RE.finditer(text)
            ] + [("spec", m.group(1)) for m in _ITEM_FROM_SPEC_RE.finditer(text)]
            if not sources:
                continue
            declared_id = _read_declared_id(text) or ""
            status_match = _PLAN_STATUS_RE.search(_metadata_region(text))
            setid, _descriptive = _parse_setid(text)
            try:
                rel = str(Path(path).resolve().relative_to(Path(repo_root).resolve()))
            except ValueError:
                rel = str(path)
            record = GraduationArtifact(
                artifact_type=artifact_type,
                id6=declared_id,
                status=status_match.group(1) if status_match else "",
                setid=setid or "",
                path=rel,
            )
            for key in sources:
                bucket = index.setdefault(key, [])
                if record not in bucket:
                    bucket.append(record)
    return index


class GraduationCluster(NamedTuple):
    """What the pre-graduation view knows about ONE source.

    source_kind/source_id6: the source this answers about.
    artifacts:              every plan and spec citing it (possibly empty, which is the COMMON and
                            reassuring answer, not an error).
    setids:                 the distinct Sets those artifacts belong to, sorted. One Set is
                            decomposition; several is the partly-visible duplication case.
    """

    source_kind: str
    source_id6: str
    artifacts: Tuple[GraduationArtifact, ...]
    setids: Tuple[str, ...]

    @property
    def artifact_count(self) -> int:
        """How many artifacts cite this source. NAMED `artifact_count` rather than `count` because
        this is a `NamedTuple`, so a `count` member would SHADOW `tuple.count` with an incompatible
        signature."""
        return len(self.artifacts)

    @property
    def terminal_artifacts(self) -> Tuple[GraduationArtifact, ...]:
        """The members that already reached a TERMINAL status, i.e. the costly case: work that has
        LANDED. Deliberately computed from the artifacts rather than from the directory, because a
        status is what a reader acts on."""
        return tuple(
            a for a in self.artifacts if a.status in GRADUATION_TERMINAL_STATUSES
        )


#: Statuses that mean the artifact's work is OVER (in either direction). Used only to HIGHLIGHT the
#: already-landed members, never to filter them out: a view that read `pending/` only would miss
#: every executed sibling and would be worst exactly where re-doing work is most expensive.
GRADUATION_TERMINAL_STATUSES: frozenset = frozenset(
    {
        "executed",
        "superseded",
        "not-executed",
        "implemented",
        "deferred",
        "parked",
    }
)


def graduation_cluster(
    repo_root: Path,
    source_id6: str,
    *,
    source_kind: Optional[str] = None,
    index: Optional[Dict[Tuple[str, str], List[GraduationArtifact]]] = None,
) -> GraduationCluster:
    """Every plan and spec already citing ``source_id6``, for the pre-graduation view.

    ``source_kind`` narrows to one link field; omitted (the usual case, since an operator types an
    id6 and not a field name) it UNIONS both, because an id6 is unique across the inventory so a
    token naming a backlog item cannot also name a spec.

    Pass ``index`` to reuse an already-built reverse index (the whole-corpus shape); otherwise one
    pass is built here. READ-ONLY: it reports and decides nothing, and it applies no
    ``count > 1`` judgement, because multiple artifacts per source is legitimate decomposition.
    """
    idx = index if index is not None else build_graduation_reverse_index(repo_root)
    kinds = (source_kind,) if source_kind else GRADUATION_SOURCE_KINDS
    artifacts: List[GraduationArtifact] = []
    for kind in kinds:
        for record in idx.get((kind, source_id6), []):
            if record not in artifacts:
                artifacts.append(record)
    setids = tuple(sorted({a.setid for a in artifacts if a.setid}))
    return GraduationCluster(
        source_kind=source_kind or "any",
        source_id6=source_id6,
        artifacts=tuple(artifacts),
        setids=setids,
    )


#: THE VIEW'S OWN HONESTY, AS DATA, so it can be rendered into the OUTPUT rather than living only in
#: a plan file. Backlog `6h7y2y` names three cases and requires the work to "say honestly which of
#: the three cases above it can and cannot detect"; a limit recorded only in a plan is invisible to
#: the person reading the view, which is exactly who needs it.
#:
#: Each row is (case, verdict, why). The verdicts are deliberately NOT all positive: over-claiming
#: here would be the same false confidence backlog `6h7y2y` exists to prevent.
GRADUATION_VIEW_LIMITS: Tuple[Tuple[str, str, str], ...] = (
    (
        "legitimate decomposition",
        "VISIBLE",
        "the Set and Order of each artifact are shown, so one Set with several Orders reads as the "
        "deliberate decomposition it is; a source with many artifacts is NOT a defect",
    ),
    (
        "accidental duplication",
        "PARTLY VISIBLE",
        "the view shows that two artifacts belong to DIFFERENT Sets, but it cannot compare their "
        "scopes, so it cannot tell overlapping work from adjacent work; a human must read them",
    ),
    (
        "already implemented",
        "NOT DETECTABLE",
        "there is no per-requirement tracking: a spec carries ONE whole-artifact status with no "
        "partial-implementation state, and `implemented` requires only a resolvable citation rather "
        "than semantic verification, so 'is requirement G5 built?' cannot be answered mechanically. "
        "Tracked by backlog `f1sw71`",
    ),
)

#: WHAT A ZERO-RESULT DOES AND DOES NOT PROVE. The index's input is the `From-Backlog:`/`From-Spec:`
#: BULLET, not the work, so an artifact that addresses a source without carrying such a link is
#: invisible to it. Reported with every answer, because a silence mistaken for "nothing exists" would
#: cause the very duplication the view exists to prevent.
GRADUATION_VIEW_COVERAGE: str = (
    "Searched: PLANS and SPECS (every lifecycle directory, including executed/ and the other "
    "terminal ones), matched by their `- From-Backlog:` / `- From-Spec:` bullet. Work that "
    "addresses this source WITHOUT carrying such a bullet is invisible here, so 'no artifacts' "
    "means 'nothing LINKED to it', never 'nothing exists'."
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


def _from_backlog_carrier_index(
    repo_root: Path,
) -> Dict[str, List[Tuple[Path, Optional[str]]]]:
    """ONE walk of the plans AND specs trees, indexed by the `- From-Backlog:` item id6 each
    artifact names: ``{item_id6: [(carrier_path, carrier_blocks_release_or_None), ...]}``.

    nobugship rgaasb E-01. THE SINGLE OWNER of "which artifacts carry a handoff for this item",
    consumed by BOTH `check_release_gate_consistency` (Rule 2) and `check_live_bug_gate`, so the two
    rules cannot disagree about what a carrier is and neither needs its own copy of the
    `Blocks-Release` / `From-Backlog` regexes.

    WHY AN INDEX RATHER THAN A PER-ITEM `find_from_backlog_artifacts` CALL, measured rather than
    assumed: `find_from_backlog_artifacts` re-walks the COMPLETE plans tree plus the specs tree on
    every call, so asking it once per candidate item costs O(items x corpus). Driven on this
    repository (671 plans, 34 specs, 65 candidate items): 65 per-item calls took 11.13 s, while this
    single shared walk produced the identical mapping in 207 ms - a 54x difference on a command a
    human waits on (`aw check all`). The exact same defect was already found and fixed one function
    below in `release_gate_warnings`, whose comment records it ("Calling `find_from_backlog_plans`
    for every open blocker re-walked the complete plans tree per item, even when no warning
    existed"); this helper generalizes that fix instead of re-learning it a third time.

    `find_from_backlog_artifacts` REMAINS the right call for a SINGLE known item (the setter gate and
    `evaluate_blocking_close`'s HANDOFF branch), and is deliberately left untouched: it is O(corpus)
    once, which is correct when there is exactly one item to answer for.

    The carrier gate is None when the artifact carries no `- Blocks-Release:` line at all, and is
    kept DISTINCT from the empty string so a caller can tell "no gate field" from a malformed one.
    """
    index: Dict[str, List[Tuple[Path, Optional[str]]]] = {}
    for iterator in (_iter_plan_ipds, _iter_spec_records):
        for p, text in iterator(repo_root):
            mfb = _META_FROM_BACKLOG_RE.search(text)
            if not mfb:
                continue
            mbr = _META_BLOCKS_RELEASE_RE.search(text)
            index.setdefault(mfb.group(1), []).append(
                (p, mbr.group(1) if mbr else None)
            )
    return index


def check_release_gate_consistency(repo_root: Path) -> List[_core.Drift]:
    """bklggrad orb9zb E-05: cross-tree consistency rules reusing `evaluate_blocking_close`.

    ERROR-severity (fold into the exit-blocking sweep):
      check.blocking-item-closed-without-gate - an already-`done` blocking item whose gate was not
        preserved/satisfied (the backstop for a hand-edit bypass of the setter gate).
      check.from-backlog-gate-mismatch - a LIVE `From-Backlog` plan or spec whose `Blocks-Release`
        differs from the backlog item's Blocks-Release (a broken handoff).

    RULE 2 IS NARROWED TO A LIVE CARRIER (nobugship rgaasb; maintainer ruling on parent `qmgn12`
    OQ-03, 2026-09-12). A carrier in a TERMINAL directory (`executed/`, `superseded/`,
    `not-executed/`) is SKIPPED. This is a restatement of the one-way obligation the rule already
    implements, not a new exemption, and the reasoning is the maintainer's: what this rule protects
    is a DROPPED HANDOFF, a plan being NON-blocking when it graduated from a BLOCKING item, so the
    gate silently vanishes between item and plan. A terminal carrier's work is DONE: it cannot drop a
    future obligation and there is no future release for it to gate, so flagging it demanded an edit
    `AGENTS.md` forbids ("Do NOT add commits to a plan already in `.aw/records/plans/executed/`") in
    order to assert a live claim on an artifact with no future. The rule was over-reaching.

    THE ASYMMETRY IS DELIBERATE AND IS THE OTHER HALF OF THE SAME RULING. A gated CARRIER under an
    UNGATED item is NOT a finding, because a plan can discover during execution that it gates a
    release for reasons its originating item never knew, and punishing it for being better informed
    than its own provenance would be wrong. Today that direction is additionally unreachable by
    construction (the `item_gate` map below is populated only for an item that HAS a gate), which is
    exactly why `tests/test_bug_gate_check.py` pins the zero-finding direction explicitly: without
    that test a refactor could silently make the rule symmetric and nothing would notice.

    Terminal classification uses the shipped `is_retired` predicate rather than a fresh path test,
    per the ruling. `is_retired` is chosen over the narrower `_EXECUTED_SEGMENT` literal because the
    ruled rationale ("work is DONE, there is no future release to gate") holds identically for a
    `superseded/` or `not-executed/` carrier; `_EXECUTED_SEGMENT` is used by the neighbouring
    staged-path rule only because that rule reasons about a git path string with no file to read.

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
    #
    # nobugship rgaasb E-01: the walk itself now comes from the shared `_from_backlog_carrier_index`
    # so this rule and `check_live_bug_gate` have ONE definition of a carrier between them.
    for target_id6, carriers in _from_backlog_carrier_index(repo_root).items():
        if target_id6 not in item_gate:
            continue  # dangling From-Backlog is check.from-backlog-dangling's job (ku93tn)
        item_br, _item_path = item_gate[target_id6]
        for p, carrier_br in carriers:
            # nobugship rgaasb: SKIP A TERMINAL CARRIER (parent qmgn12 OQ-03 ruling). See the
            # docstring: a finished plan's gate is history, not a live claim, and it cannot drop a
            # future obligation.
            if is_retired(p):
                continue
            if carrier_br != item_br:
                kind = "spec" if str(p).endswith(".spec.md") else "plan"
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


_LIVE_BUG_GATE_RULE = "check.live-bug-ungated"


def check_live_bug_gate(repo_root: Path) -> List[_core.Drift]:
    """A LIVE `Work-Kind: bug` backlog item carrying NO `- Blocks-Release:` (nobugship rgaasb E-01).

    THE RULE THIS ENFORCES IS WRITTEN DOWN, and this docstring deliberately POINTS AT that text
    rather than restating the policy, so the two cannot drift: `AGENTS.md`, section "Every live bug
    gates the next release" (written by sibling plan `zqs0px`). In short: we do not ship known bugs,
    so a `bug` MUST carry a release gate while it is LIVE.

    LIVE means `open`, `blocked` or `graduated`, which is the same live set `aw attention` uses. The
    two exclusions are deliberate rather than convenient:
      * `done` is NEVER flagged. A closed bug shipped or did not, and asserting a gate on it now
        would rewrite history. (Its own sibling rule `check.blocking-item-closed-without-gate`
        already governs the close direction.)
      * `parked` is NEVER flagged. A parked maybe is uncommitted work the attention view hides, so
        gating a release on one asserts an obligation nobody has taken on. This matches
        `backlog._GATE_DEFAULT_SKIP_STATUSES` exactly, so the creation default and this check agree.

    A GRADUATED ITEM WHOSE CARRIER HOLDS THE GATE IS SATISFIED, NOT FLAGGED, and this is the
    substantive design choice. `AGENTS.md` already defines a legitimate HANDOFF as a plan or spec
    carrying `- From-Backlog: <item>` plus the same `- Blocks-Release:`, and uses exactly that to let
    a gated item close without dropping its gate. The OPEN direction of the same invariant must
    recognise the same handoff or a correctly-handed-off bug would be flagged forever and the rule
    would train people to ignore it. The carrier lookup comes from the shared
    `_from_backlog_carrier_index`, so "what counts as a carrier" has one owner (and a SPEC is an
    equally valid carrier, per `find_from_backlog_artifacts`).

    THE EXEMPTION APPLIES TO ANY LIVE STATUS, NOT ONLY `graduated`. The discriminator is whether a
    handoff carrier holds a gate, not the item's own status: measured on this repository, two `open`
    items also have carriers, so keying the exemption on `graduated` would treat identical evidence
    differently depending on a status the handoff does not depend on.

    WHY THIS DOES NOT COMPOSE WITH `evaluate_blocking_close`, which is the obvious-looking reuse and
    is impossible: that predicate answers the CLOSE direction only, and every one of its branches
    keys on `blocks_release` being PRESENT. Driven on an ungated live bug it returns
    `CloseVerdict(legitimate=True, severity='ok', ...)` - for `target_status='done'` with reason
    'no release gate to preserve' and path 'DE-GATED', and for any other target 'unchecked
    transition'. An ABSENT gate is outside its domain by construction, so wrapping it would either
    report nothing or require rewriting a predicate three other surfaces depend on.

    DIVISION OF LABOUR WITH THE REST OF THE I-07 FAMILY, so no reader mistakes this for a duplicate:
    this rule catches an ABSENT gate; `check.blocks-release-dangling` catches an UNRESOLVABLE one;
    `check.from-backlog-gate-mismatch` catches a carrier CONTRADICTING its item; and
    `check.from-backlog-dangling` catches a carrier pointing at nothing.

    HONEST LIMIT: the rule keys on `- Work-Kind:`, which is an AUTHOR'S CLASSIFICATION. A genuine
    defect filed as `chore` or `followup` is invisible to it, and that leak is real and measured
    (backlog `59t9x5` was filed `chore` and reclassified `bug` by the maintainer). This is a strict
    improvement over nothing; it is NOT a completeness claim.
    """
    from agent_workflows import backlog as _backlog

    repo_root = Path(repo_root)
    live = _backlog.STATUSES - _backlog._GATE_DEFAULT_SKIP_STATUSES
    drift: List[_core.Drift] = []
    carrier_index: Optional[Dict[str, List[Tuple[Path, Optional[str]]]]] = None

    for f in _backlog._iter_items(repo_root):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        item = _backlog.parse_item(text)
        if item.kind not in _backlog.GATE_DEFAULT_KINDS:
            continue
        if (item.status or "") not in live:
            continue
        if item.blocks_release:
            continue
        # Only now is the carrier index needed, so a clean tree never pays for the walk.
        if carrier_index is None:
            carrier_index = _from_backlog_carrier_index(repo_root)
        if item.id and any(
            carrier_br for _p, carrier_br in carrier_index.get(item.id, ())
        ):
            continue  # HANDOFF: a From-Backlog carrier holds the gate (AGENTS.md)
        # `enrich_drift` with a structured `recovery`, matching the family's shape rather than
        # embedding the fix in the detail text: `recovery` is the field the human renderer prints as
        # the Fix line and the machine record carries verbatim, so a fix written into `detail` is
        # invisible where a reader looks for it (driven: the generic "inspect ... frontmatter"
        # fallback was printed instead).
        selector = item.id or f.name
        drift.append(
            enrich_drift(
                _core.Drift(
                    str(f),
                    _LIVE_BUG_GATE_RULE,
                    (
                        f"a LIVE (status {item.status!r}) Work-Kind: bug item carries no "
                        "- Blocks-Release:; we do not ship known bugs, so every live bug must "
                        "gate a release (AGENTS.md, 'Every live bug gates the next release')"
                    ),
                ),
                observed=f"Work-Kind: bug, Status: {item.status}, no Blocks-Release",
                required="- Blocks-Release: <release id6 or 'next'>, or a From-Backlog carrier "
                "holding the gate",
                recovery=(
                    f"aw backlog set {item.status} {selector} --blocks-release next"
                    "  (or hand the gate to the plan/spec that graduated it, or file an explicit "
                    "exemption if this bug genuinely does not gate the release)"
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

    # Build the plan handoff index once. Calling `find_from_backlog_plans` for every
    # open blocker re-walked the complete plans tree per item, even when no warning
    # existed. The warning needs only a source backlog id6 and its inherited release
    # gate, so this index preserves its plan-only semantics without the repeated scans.
    plan_gates_by_backlog: Dict[str, set[str]] = {}
    for _p, text in _iter_plan_ipds(repo_root):
        mfb = _META_FROM_BACKLOG_RE.search(text)
        if not mfb:
            continue
        mbr = _META_BLOCKS_RELEASE_RE.search(text)
        plan_gates_by_backlog.setdefault(mfb.group(1), set()).add(
            mbr.group(1) if mbr else ""
        )

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
        _id6 = mid.group(1)
        if mbr.group(1) in plan_gates_by_backlog.get(_id6, set()):
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

    Delegates ENTIRELY to ``review_findings.subject_gating_blocks``, the SAME function both host runners
    consume, so `aw check` and a live run cannot disagree about what blocks. This function
    re-implements no severity comparison, holds no threshold default, and never raises.
    """
    try:
        from agent_workflows import review_findings as _rf

        return _rf.subject_gating_blocks(repo_root, dep_id6, threshold)
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
    include_retired: bool = False,
    actions: Optional[Dict[str, str]] = None,
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

    `actions` (path_str -> ``"review"``/``"execute"``/``"orchestrate"``) is the CONSUMING ACTION for
    each evaluated plan, and it exists because spec 25kzda 2.9 makes `executed:` satisfaction
    ACTION-DEPENDENT. Its review row states that a review turn is satisfied by a target in
    `executed`, `reviewed`, or `approved` and that "terminal execution evidence is NOT required,
    because a review turn writes no code and therefore cannot be invalidated by an unexecuted
    prerequisite". So the findings-blocked check below (which is a statement about the TARGET's
    execution-readiness) does NOT apply to a review turn, and applying it there contradicts the spec.

    MEASURED DEFECT THIS CLOSES (2026-09-08): `aw oc run runanalytics orchprobe hostdefault ...` was
    refused at preflight because `m7gvuz` declares `executed:r2i1b1, executed:8tgg6g` and those two
    targets carry unresolved gating findings. But every one of those plans was `to-review`, i.e. the
    consuming action was `review`, and the run reviewed nothing at all: 8 selectors and 21 items were
    refused over an edge whose own spec row exempts them. Worse, it was CIRCULAR, because the
    `orchprobe` Set exists to fix orchestrator gate defects and the gate blocked reviewing it.

    ABSENT/UNKNOWN action is treated as the STRICT (execute) reading, so every existing caller
    (`aw check`, `aw ipd lint`, the pre-commit hook) keeps its current behavior unchanged and this
    parameter can only ever RELAX the gate for a turn that provably writes no code.
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
    _findings_cache: Dict[str, tuple] = {}

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
        # IPD `76w6mq`: the owner id6 is read from the plan's METADATA REGION, the same bound every
        # other identity reader uses, so a plan that QUOTES another plan's metadata block cannot be
        # entered into the dependency graph under the quoted id6. Measured at the time of the change:
        # no plan in the corpus changes its graph identity, so this is a fail-safe alignment rather
        # than a behavior change - which is exactly why it should be made now, before a plan
        # discussing `Item-Dependencies` (a normal thing for a plan about the graph to do) acquires a
        # quoted `- Id:` and silently takes over another plan's node.
        mid_declared = _read_declared_id(text)
        if mid_declared:
            own_id[ps] = mid_declared
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

    # Per-statement findings for the target set (default: all active plans or all plans if include_retired).
    target_plans = (
        plans
        if plans is not None
        else (
            all_plans
            if include_retired
            else [pt for pt in all_plans if not is_retired(pt[0])]
        )
    )
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
                #
                # ACTION-SCOPED (2026-09-08): spec 2.9's review row exempts a REVIEW turn from
                # execution-readiness entirely ("terminal execution evidence is NOT required, because
                # a review turn writes no code and therefore cannot be invalidated by an unexecuted
                # prerequisite"). An unresolved gating finding on the target is a statement about that
                # target's readiness to be BUILT ON, so it cannot bear on reading and critiquing the
                # dependent's prose. Absent/unknown action keeps the STRICT reading, so every
                # non-runner caller is unchanged and this can only relax a provably code-free turn.
                if e.kind == "executed" and (actions or {}).get(ps) != "review":
                    if e.id6 not in _findings_cache:
                        _findings_cache[e.id6] = tuple(
                            _findings_blocks_for(repo_root, e.id6, _findings_thr)
                        )
                    for blk in _findings_cache[e.id6]:
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


def check_ipd_dependencies(
    repo_root: Path,
    include_retired: bool = False,
) -> List[_core.Drift]:
    """Repo-wide cross-IPD dependency check for `aw check` (phase="check"). Mirrors the
    `check_from_backlog` scan shape; wired into the plans-type content path so BOTH `aw check plans`
    and `aw check all` surface it exactly once (never double-reported)."""
    return evaluate_ipd_dependencies(
        repo_root, phase="check", include_retired=include_retired
    )


_PRIORITY_INVALID_RULE = "check.priority-invalid"


def check_plan_priority(
    repo_root: Path,
    include_untracked: bool = False,
    include_retired: bool = False,
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
    for p in _iter_type_files(
        repo_root,
        "plans",
        include_untracked=include_untracked,
        include_retired=include_retired,
    ):
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


_WORK_KIND_INVALID_RULE = "check.work-kind-invalid"


def check_plan_work_kind(
    repo_root: Path,
    include_untracked: bool = False,
    include_retired: bool = False,
) -> List[_core.Drift]:
    """Validate the recognized-but-optional `- Work-Kind:` enum on each plan (wkindname ng2blv E-05).

    Work-Kind is OPTIONAL on an IPD (schema RECOGNIZES it; the enum value check lives HERE, in
    `aw check`, per the documented convention). A plan carrying an out-of-vocab `- Work-Kind:` value
    is flagged `check.work-kind-invalid`; a plan with a valid value (or NO Work-Kind at all) is
    silent. The vocabulary is the SHARED `backlog.KINDS` (imported, never forked). This is a plain
    metadata-enum check on the plan's OWN field, NOT a cross-tree dangling/reference check, so it runs
    in the plans-type content path (reached by both `aw check plans` and the `aw check all` fan-out,
    exactly once). Mirrors `check_plan_priority` line-for-line.
    """
    from agent_workflows import backlog as _backlog

    drift: List[_core.Drift] = []
    for p in _iter_type_files(
        repo_root,
        "plans",
        include_untracked=include_untracked,
        include_retired=include_retired,
    ):
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        m = _ITEM_WORK_KIND_RE.search(text)
        if not m:
            continue  # absent Work-Kind is fine (optional)
        value = m.group(1).strip()
        if value in _backlog.KINDS:
            continue
        mid = _ITEM_ID_RE.search(text)
        id6 = mid.group(1) if mid else p.stem
        drift.append(
            enrich_drift(
                _core.Drift(
                    str(p),
                    _WORK_KIND_INVALID_RULE,
                    f"work kind not in {sorted(_backlog.KINDS)}: {value!r}",
                ),
                observed=f"Work-Kind: {value}",
                required=f"one of {sorted(_backlog.KINDS)} (or omit Work-Kind)",
                recovery=(
                    f"aw ipd set {id6} --work-kind "
                    "<bug|feature|chore|security|followup>  (or --work-kind - to clear)"
                ),
            )
        )
    return drift


_REVIEW_DANGLING_RULE = "check.review-dangling"
_REVIEW_SUBJECT_ID_RE = _re.compile(
    r"(?m)^-[ \t]*Subject-Id:[ \t]*([0-9a-z]{6})[ \t]*$"
)
_REVIEW_SUBJECT_TYPE_RE = _re.compile(r"(?m)^-[ \t]*Subject-Type:[ \t]*(\S+)[ \t]*$")


def _review_subject_id_sets(repo_root: Path) -> Dict[str, set]:
    """The known-id6 set for each `Subject-Type`, keyed by the CLOSED vocabulary's own values.

    ONE place decides which tree a subject type resolves against (revsweep `eyh1fu` E-03). Both
    entries reuse the EXISTING typed iterators (`_iter_plan_ipds`, `_iter_spec_records`), so this
    helper adds no second "which ids exist" mechanism and, in particular, no `.aw/records/reviews`
    or specs-tree path literal of its own.

    A type in `review_findings.SUBJECT_TYPES` with no entry here would silently resolve against
    NOTHING and report every record of that type as dangling, so the mapping is asserted complete by
    a test rather than left to inspection.
    """
    return {
        "ipd": {
            m.group(1)
            for _p, text in _iter_plan_ipds(repo_root)
            for m in (_ITEM_ID_RE.search(text),)
            if m
        },
        "spec": {
            m.group(1)
            for _p, text in _iter_spec_records(repo_root)
            for m in (_ITEM_ID_RE.search(text),)
            if m
        },
    }


def check_review_dangling(repo_root: Path) -> List[_core.Drift]:
    """Flag a `.review.md` whose `- Subject-Id:` does not resolve to any artifact of its declared type.

    The cross-tree-reference sibling of `check.from-backlog-dangling`, but ADVISORY (`warning`): a
    review whose subject was deleted or superseded is untidy, not dangerous. It therefore rides the
    same full-sweep seam as the other dangling scans. Note `warning` does NOT mean "cannot fail
    anything": `artifact_core.drift_exit_code` exempts only `info`, so this rule can drive exit 1. What
    the severity buys is that NO LIFECYCLE GATE consumes it (no `aw ipd lint` checkpoint, no
    begin/finalize refusal, no dependency block).

    RESOLUTION IS TYPE-DIRECTED (revsweep `eyh1fu` E-03, spec `6m4kow` R-03): the id6 is resolved
    against the tree named by `- Subject-Type:`, not against the plans tree unconditionally, which is
    what makes a spec review filable at all. The per-type id sets come from
    :func:`_review_subject_id_sets`.

    AN ABSENT OR UNKNOWN `Subject-Type` IS NOT THIS RULE'S BUSINESS, exactly as a missing subject id
    already was not: it is a PARSE ERROR the parser reports (`REV-M101`/`REV-M102`), and reporting it
    here as well would double-report one authoring mistake under an advisory rule id. Critically, this
    rule does NOT fall back to the plans tree for such a record, because a defaulted type is precisely
    how a migration bug would hide.

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

    known_by_type = _review_subject_id_sets(repo_root)

    ignored_dirs = _core.get_ignored_dirs(repo_root)
    for path in _rf.iter_review_files(repo_root):
        if _core.is_ignored_path(path, repo_root, ignored_dirs):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        m = _REVIEW_SUBJECT_ID_RE.search(text)
        if m is None:
            continue  # a missing/malformed Subject-Id is the parser's diagnostic, not this rule's
        mt = _REVIEW_SUBJECT_TYPE_RE.search(text)
        subject_type = mt.group(1).strip().lower() if mt else ""
        known = known_by_type.get(subject_type)
        if known is None:
            # Absent or out-of-vocabulary type: the parser owns that complaint (see the docstring).
            # Deliberately NOT resolved against the plans tree as a fallback.
            continue
        subject_id = m.group(1)
        if subject_id in known:
            continue
        drift.append(
            enrich_drift(
                _core.Drift(
                    str(path),
                    _REVIEW_DANGLING_RULE,
                    f"Subject-Id {subject_id!r} does not resolve to any {subject_type}",
                ),
                observed=f"Subject-Id: {subject_id} (Subject-Type: {subject_type})",
                required=(
                    f"a Subject-Id matching an existing {subject_type}'s `- Id:`"
                ),
                recovery=(
                    "correct the Subject-Id to the reviewed artifact's id6 (or fix Subject-Type if "
                    "the wrong tree is being searched), or retire the review alongside the "
                    "artifact it reviewed"
                ),
            )
        )
    return drift


_SPEC_REVIEW_ATTESTATION_RULE = "check.spec-review-unattested"


def check_spec_review_attestation(repo_root: Path) -> List[_core.Drift]:
    """Flag a spec CURRENTLY at `- Status: reviewed` with no conforming review record.

    revsweep `5slbpi` E-04, spec `6m4kow` R-11/R-12. The setter half refuses the TRANSITION; this half
    catches a spec that reached `reviewed` some OTHER way - a hand edit, an import, a pre-toolkit
    file - because a gate that only guards the front door leaves the window open. Both halves consult
    the SAME predicate (`review_findings.review_attestation_missing`), which is what R-12 requires and
    what keeps the refusal a user meets and the finding a check reports from disagreeing about one spec.

    SCOPED TO `reviewed` AND NOTHING ELSE, which is also what makes grandfathering FREE rather than
    configured (`5slbpi` DECISION D2). `reviewed` is a TRANSIENT state on the way to `approved`, and
    measured at implementation NO spec in this repository sat there: the census was 15 `implemented`,
    5 `approved`, 2 `draft`, 2 `deferred`, 1 `to-review`, 1 `superseded`, 1 `implementing`. So the 20
    pre-existing `approved`/`implemented` specs - none of which has a review record and none of which
    ever will - are outside this rule BY CONSTRUCTION, with no cutover date to maintain. A rule keyed on
    "has this spec ever been reviewed" would instead have flagged all 20 and retroactively invalidated
    most of the specs tree, which R-13 forbids.

    `error` rather than the advisory severity its `check.review-dangling` neighbour carries, and the
    difference is deliberate: a stale review is untidy leftover data nothing reads, whereas a spec
    claiming `reviewed` with no review is a FALSE LIFECYCLE CLAIM on the artifact that authorizes plans.
    That is the invariant class I-03 (lifecycle-status authority) covers.

    Never raises: an unreadable specs or reviews tree yields no findings, because a crashing check is a
    disabled check.
    """
    drift: List[_core.Drift] = []
    try:
        from agent_workflows import review_findings as _rf
    except Exception:
        return drift

    for path, text in _iter_spec_records(repo_root):
        ms = _re.search(r"(?m)^-[ \t]*Status:[ \t]*(\S+)[ \t]*$", text)
        if ms is None or ms.group(1).strip().lower() != "reviewed":
            continue
        mid = _ITEM_ID_RE.search(text)
        id6 = mid.group(1) if mid else ""
        try:
            missing = _rf.review_attestation_missing(repo_root, id6, "spec")
        except Exception:
            continue
        if missing is None:
            continue
        drift.append(
            enrich_drift(
                _core.Drift(
                    str(path),
                    _SPEC_REVIEW_ATTESTATION_RULE,
                    f"spec is `reviewed` but {missing}",
                ),
                observed="- Status: reviewed with no conforming review record",
                # Deliberately describes the record by its FIELDS, not by a reviews-tree path. A path
                # string here would be a second hardcoded reviews location (the anti-duplication guard
                # `tests/test_review_findings.py::test_no_hardcoded_reviews_path_in_check_engine`
                # enforces its absence, and it cannot distinguish prose from a resolution path). The
                # authority for WHERE reviews live stays `review_findings.review_dirs`.
                required=(
                    "a `*.review.md` in the repository's reviews tree that PARSES and carries "
                    "`- Subject-Id: <this spec's id6>` plus `- Subject-Type: spec`"
                ),
                recovery=(
                    "run the spec review (`/spec-review <spec>`) to produce the record, or return the "
                    'spec to `to-review` with `aw specs set to-review <id6> --message "review not '
                    'recorded"` so the attested transition can be performed properly'
                ),
            )
        )
    return drift


_FROM_SPEC_DANGLING_RULE = "check.from-spec-dangling"
_ITEM_FROM_SPEC_RE = _re.compile(r"(?m)^-[ \t]*From-Spec:[ \t]*(\S+)[ \t]*$")


def check_from_spec_dangling(repo_root: Path) -> List[_core.Drift]:
    """Flag a plan (or spec) whose `- From-Spec:` does not resolve to an existing spec id6.

    detrun Order bmh754 (spec 25kzda): the SPEC-side sibling of `releases.check_from_backlog`, and the
    value-validation half of the `META_FROM_SPEC` schema recognition. The schema layer deliberately
    only stops the IPD-M103 "unknown field" error; whether the id6 actually resolves is a CROSS-TREE
    reference question, so it lives here on the same full-sweep seam as `check.from-backlog-dangling`,
    `check.blocks-release-dangling`, and `check.review-dangling`.

    `error`, matching `check.from-backlog-dangling` rather than the advisory `check.review-dangling`,
    and the difference is deliberate. A stale review is untidy leftover data that nothing downstream
    reads. A `From-Spec` link is LOAD-BEARING provenance: AGENTS.md makes a spec an "equally valid gate
    carrier" for a release gate, so a `From-Spec` pointing at nothing is a broken handoff claim of
    exactly the kind its `From-Backlog` twin already errors on. Severity parity between the two
    carriers of one handoff is the point.

    Discovery reuses the existing `_iter_plan_ipds` / `_iter_spec_records` iterators. This function
    contains NO new spec-id scanner and NO second spec-path literal: a second mechanism for "which
    spec ids exist" is precisely the drift GUIDING_PRINCIPLES P8 forbids.

    The known-id set is the UNION of two existing authorities, and the union is load-bearing rather
    than belt-and-braces (measured, not assumed): `_iter_spec_records` walks the in-tree
    `.aw/records/specs` / `.agents/specs` trees, while `specs._existing_spec_ids` goes through
    `record_producers.resolve_record_read_paths`, which in an EXTERNALLY-REDIRECTED project resolves
    to a path outside the repo entirely. Verified on a scratch repo: the resolver returned only
    `~/.aw/projects/<slug>/records/specs` and `_existing_spec_ids` was therefore EMPTY while the
    in-tree spec plainly existed, which made a perfectly valid link look dangling. Consulting either
    source alone yields false positives on some real layout; the union yields them on neither.

    Unresolvable-either-way is the only reported case, which is the correct bias for an `error` rule:
    over-reporting here would block commits on valid links.

    Scanned on plans AND specs for the same symmetry reason `check_from_backlog` scans both: the link's
    primary home is a plan, but tolerating it anywhere keeps one rule instead of two.
    """
    drift: List[_core.Drift] = []
    known: set = set()
    for _p, _t in _iter_spec_records(repo_root):
        m = _ITEM_ID_RE.search(_t)
        if m:
            known.add(m.group(1))
    try:
        from agent_workflows import specs as _specs

        known |= _specs._existing_spec_ids(Path(repo_root))
    except Exception:
        # Fail SAFE: a resolver failure must not turn every valid link into a finding. The in-tree
        # scan above already stands on its own; this only widens the set.
        pass
    if not known:
        # No spec identity is discoverable at all (no specs tree, or an unreadable one). We cannot
        # distinguish a dangling link from an invisible spec corpus, so report nothing rather than
        # flag every link in the repo. Same fail-safe posture as the sibling dangling scans.
        return drift

    for iterator in (_iter_plan_ipds, _iter_spec_records):
        for path, text in iterator(repo_root):
            m = _ITEM_FROM_SPEC_RE.search(text)
            if m is None:
                continue
            target = m.group(1)
            if target in known:
                continue
            drift.append(
                enrich_drift(
                    _core.Drift(
                        str(path),
                        _FROM_SPEC_DANGLING_RULE,
                        f"From-Spec {target!r} does not resolve to a spec",
                    ),
                    observed=f"From-Spec: {target}",
                    required="a From-Spec matching an existing spec's `- Id:`",
                    recovery=(
                        "correct the From-Spec to the source spec's id6 (`aw find specs` to look it "
                        "up), or drop the field if this plan did not graduate from a spec"
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
    """Map a reviewed artifact's id6 -> its review file(s), via the ONE discovery helper.

    Discovery is `review_findings.iter_review_files` (the record-path authority plus its documented
    bare-repo fallback), so this function holds NO `.aw/records/reviews` path literal of its own.

    KEYED ON THE NEUTRAL `- Subject-Id:` (revsweep `eyh1fu` E-05), and this is the load-bearing half of
    that change rather than bookkeeping. Four call sites read this index (the two escalation
    evaluators and their two sweeps), and `check.review-finding-unescalated` is an **`error`** wired
    into two `aw ipd lint` checkpoints. Had the field been renamed without repointing here, the index
    would come back EMPTY, every dependent rule would take its "nothing reviewed: every plan is the (a)
    absent case" early return, and an unfixed HIGH/BLOCKER would gate NOTHING - a SILENT fail-OPEN
    indistinguishable from compliance. That is why the migration carries a POSITIVE test that the
    escalation rule still fires, not merely a green `aw check`.

    ONE SHARED REGEX serves both this index and `check_review_dangling`, deliberately: the subject
    field has exactly one spelling, and a second matcher is the drift GUIDING_PRINCIPLES P8 forbids.

    NO `Subject-Type` FILTER IS APPLIED, and the omission is deliberate rather than overlooked. An id6
    is unique across trees (`check.id6-collision` polices that), so keying on the id alone cannot
    attribute a spec-subject record to a plan: the callers look the index up BY THE PLAN'S OWN id6,
    which no spec shares. Filtering here would add a second place that decides what a subject type
    means, for no additional safety.
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
            # read at all has no Subject-Id to key on.
            continue
        m = _REVIEW_SUBJECT_ID_RE.search(text)
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


# ======================================================================================
# durablecapture Order 01 (`rnkqrc`): the ONE durable-carrier predicate.
#
# WHAT IT REFUSES, in the maintainer's words (2026-09-05): "A note in an executed IPD is 100%
# guaranteed to be the same as not writing it anywhere." `attention_contract._PLANS_MAP` maps a plan's
# `executed` status to the `done` class, so an obligation recorded only in a terminal plan's prose
# leaves every attention view permanently and silently. The mandatory `## Deferred / out of scope (with
# reason)` section (`ipd_schema.H_DEFERRED`, in BOTH H2 orders) had NO consumer at all before this:
# `rg -c H_DEFERRED agent_workflows/ipd_lint.py` exited 1.
#
# THE MAINTAINER'S RULING (2026-09-10, this plan's OQ-05): "All defects require one or more backlogs or
# plans to address. The report is not needed. A backlog item or IPD is. This is a MUST, not a should."
# Hence the accepted carrier set below is exactly two record types, and a spec is NEVER sufficient
# (OQ-01, same ruling: a spec is supporting material). The run-record read an earlier revision of this
# plan mandated is DROPPED as unnecessary, not deferred: nothing here reads `.aw/records/runs/`.
#
# THE SHAPE IS `evaluate_blocking_close`'s, MIRRORED AND NOT REINVENTED (see `CloseVerdict` at
# :1963 and `evaluate_blocking_close` at :1980). Same verdict type, same three escapes, same
# one-predicate-two-surfaces property `evaluate_review_finding_escalation` states as its design intent:
# `aw check` (via `check_durable_carrier`) and `aw ipd lint --phase pre-transition` (via
# `ipd_lint._merge_durable_carrier`) both call `evaluate_durable_carrier`, so they cannot drift.
#
# IT IS A DECLARATION GATE, NOT A DETECTOR (OQ-04), and that honesty is the point rather than a
# caveat. Nothing here can tell that an author described a defect in prose and wrote no field. The
# predicate decides only mechanical facts: does a typed field exist, does its id6 resolve, is the
# target non-terminal. Prose is never read, which is also WHY a row saying "tracked in the backlog"
# with no typed field is refused: there is nothing there for the rule to see.
# ======================================================================================

_CARRIER_RULE = "check.ipd-uncarried-obligation"

#: HANDOFF targets: the record types a `- Carrier:` id6 may resolve to. TWO entries, per the ruling
#: above. `specs` is deliberately ABSENT: accepting a spec was offered to the maintainer and REJECTED
#: ("I don't know when 'just a spec' would be enough"), because it delegates exactly the judgement this
#: rule exists to remove. Adding it back needs a maintainer decision, not a tweak.
_CARRIER_TARGET_TYPES = ("backlog", "plans")

#: A carrier target's status that means the obligation is ALREADY HIDDEN, so pointing at it is not a
#: handoff. `executed` is the whole point of this plan (an executed plan classes `done` in
#: `aw attention`, which is the hiding place); `superseded`/`not-executed` are the plans tree's other
#: terminal dirs; `done` is the backlog's. `parked` is included because `attention_contract` maps it to
#: the `parked` class, which the default board HIDES, so a parked carrier is invisible by construction
#: exactly as an executed plan is. `graduated` is NOT here: it maps to `active`, so it is revisited.
_CARRIER_TERMINAL_STATUSES = frozenset(
    ("executed", "superseded", "not-executed", "done", "parked")
)

#: The cutover boundary for the `error` tier (E-05 option (c), DECISION 07-rnkqrc-D3). Compared against
#: the PLAN'S OWN `- Date:`, so no configuration is required and the boundary cannot silently be
#: absent. The precedent is `SPEC_ID6_CUTOVER_DATE` at the top of this module, a module constant
#: compared against the artifact's own date, whose value was chosen "strictly AFTER the newest existing
#: legacy-named spec date ... so ALL existing specs remain grandfathered". This value follows the same
#: rule: measured 2026-09-18, the newest plan `- Date:` in the corpus is 2026-09-17, so 20260919
#: grandfathers every plan that exists today (664 offending rows across all 106 pending plans) and
#: applies the error tier to plans authored after this rule ships.
#:
#: WHY NOT `config.dependency_cutover_date` (F-11): measured `None` in this repository, and an absent
#: marker grandfathers EVERYTHING, which would leave the `error` tier unreachable until someone set a
#: date, i.e. the rule would ship advisory-forever and quietly satisfy its own test.
CARRIER_CUTOVER_DATE = "20260919"  # compact YYYYMMDD

#: The severity a PRE-cutover (grandfathered) finding carries. `info`, and the choice is measured
#: rather than stylistic (DECISION 07-rnkqrc-D2). `artifact_core.drift_exit_code` exempts ONLY `info`,
#: so a `warning` here would exit 1 on a clean tree with 106 findings and fail CI (which enforces
#: `aw check plans` fail-closed), which is precisely the "turns the working tree red and trains every
#: agent to bypass `aw check`" outcome the plan's approval gate forbids. The exact in-tree precedent is
#: `check.stale-index-missing` above: "MISSING -> `info`, the ONLY non-failing severity ... `warning`
#: here would still exit 1 on every fresh clone".
#:
#: THIS IS A ROLLOUT TIER, NOT A SOFTENING (plan OQ-05: the ruling says MUST). The end state is
#: `error`, which is what the RULE_REGISTRY entry declares; this constant only spares a corpus that
#: predates the rule.
_CARRIER_LEGACY_SEVERITY = "info"

#: Only these OQ statuses carry a live obligation. A `resolved` question is answered and owes nothing.
#: `open` and `deferred` both leave something outstanding, which is exactly `_UNFIXED_DECISIONS`'
#: reasoning applied to a question instead of a finding.
_CARRIER_LIVE_OQ_STATUSES = frozenset(("open", "deferred"))

_CARRIER_DATE_RE = _re.compile(r"(?m)^- Date:[ \t]*(\d{4})-(\d{2})-(\d{2})[ \t]*$")


class CarrierObligation(NamedTuple):
    """One row that must name a durable carrier.

    kind:    "deferred" (a `## Deferred / out of scope` bullet) | "question" (an OQ block).
    locator: the human-facing handle (`OQ-05`, or `deferred row 3`).
    line:    1-based source line, or 0 when unknown.
    fields:  the row's parsed typed subfields (never its prose).
    """

    kind: str
    locator: str
    line: int
    fields: Dict[str, str]


def _plan_date_compact(text: str) -> Optional[str]:
    """The plan's own `- Date:` as compact YYYYMMDD, or None when absent/malformed."""
    m = _CARRIER_DATE_RE.search(text)
    if m is None:
        return None
    return "{0}{1}{2}".format(m.group(1), m.group(2), m.group(3))


def carrier_severity_for_plan(plan_text: str, repo_root: Optional[Path] = None) -> str:
    """The severity tier this plan's carrier findings get: `error` post-cutover, else the legacy tier.

    When repo_root is provided, queries resolve_cutover_date(repo_root, "carrier_obligations").
    Falls back to deprecated CARRIER_CUTOVER_DATE constant when unconfigured or repo_root is omitted.
    A plan with NO parseable `- Date:` is treated as PRE-cutover (grandfathered). That direction is
    deliberate: the metadata linter already owns the missing-Date complaint (`IPD-M101`), and inventing
    a second, harsher consequence for it here would make this rule fire on a defect it does not own.
    """
    date = _plan_date_compact(plan_text)
    if date is None:
        return _CARRIER_LEGACY_SEVERITY
    cutover = None
    if repo_root is not None:
        from agent_workflows import config as _config

        cutover = _config.resolve_cutover_date(
            repo_root, "carrier_obligations", compact=True
        )
    if cutover is None:
        cutover = CARRIER_CUTOVER_DATE
    return "error" if date >= cutover else _CARRIER_LEGACY_SEVERITY


def _deferred_section_obligations(plan_text: str) -> List[CarrierObligation]:
    """Every top-level `## Deferred / out of scope` bullet, with its indented typed subfields.

    Walks the FENCE-AWARE structural view (`ipd_lint._structural_lines`), so a bullet inside a code
    fence or a block quote is not mistaken for a row. Never raises: an unparseable plan yields no
    obligations, and the structural linter owns that complaint.
    """
    out: List[CarrierObligation] = []
    try:
        from agent_workflows import ipd_lint as _lint
    except Exception:
        return out
    try:
        struct = _lint._structural_lines(plan_text)
    except Exception:
        return out
    in_section = False
    index = 0
    current: Optional[CarrierObligation] = None
    fields: Dict[str, str] = {}

    def _flush():
        nonlocal current, fields
        if current is not None:
            out.append(current._replace(fields=dict(fields)))
        current = None
        fields = {}

    for lineno, raw in struct:
        mh = _lint._H2_RE.match(raw)
        if mh:
            _flush()
            in_section = mh.group(1).strip() == _S.H_DEFERRED
            continue
        if not in_section:
            continue
        if raw.startswith("- "):
            _flush()
            index += 1
            current = CarrierObligation(
                "deferred", "deferred row {0}".format(index), lineno, {}
            )
            continue
        msf = _S.DEFERRED_SUBFIELD_RE.match(raw)
        if msf and current is not None:
            fields[msf.group("field").strip()] = msf.group("value").strip()
    _flush()
    return out


def _question_obligations(open_questions) -> List[CarrierObligation]:
    """Every open question that still owes something (`Status:` open or deferred).

    A `resolved` question is EXCLUDED: it has been answered, and demanding a carrier for an answered
    question would fire on 464 executed-tree and 154 pending-tree questions that owe nothing (measured
    2026-09-18). This mirrors `_UNFIXED_DECISIONS`' reasoning: only an unfixed thing needs a home.
    """
    out: List[CarrierObligation] = []
    for oq in open_questions or []:
        status = (oq.get("Status") or "").strip().lower()
        if status not in _CARRIER_LIVE_OQ_STATUSES:
            continue
        try:
            line = int(oq.get("line", "0") or 0)
        except (TypeError, ValueError):
            line = 0
        out.append(
            CarrierObligation("question", oq.get("id", "OQ") or "OQ", line, dict(oq))
        )
    return out


def _carrier_index(repo_root: Path) -> Dict[str, List[Tuple[str, Optional[str], str]]]:
    """id6 -> [(record_type, status, path)] for the ACCEPTED carrier types only.

    Built from the SAME unified inventory `build_dependency_index` uses, so "does this id6 resolve" has
    one answer in this repository rather than two. Filtered to `_CARRIER_TARGET_TYPES` here (not in the
    inventory) so a spec sharing no id6 with a plan cannot accidentally satisfy a handoff.
    """
    index = build_dependency_index(repo_root)
    out: Dict[str, List[Tuple[str, Optional[str], str]]] = {}
    for id6, owners in index.owners.items():
        typed = [o for o in owners if o[0] in _CARRIER_TARGET_TYPES]
        if typed:
            out[id6] = typed
    return out


def _resolve_carrier(
    carrier_index: Dict[str, List[Tuple[str, Optional[str], str]]], id6: str
) -> Tuple[str, str]:
    """Resolve one carrier id6. Returns (verdict, detail) with verdict in
    {"ok", "dangling", "terminal"}.

    RESOLVES, DOES NOT MERELY PARSE (E-02). A dangling id6 FAILS, exactly as
    `check.from-backlog-dangling` fails a `From-Backlog` pointing at nothing. A target whose status is
    terminal FAILS TOO, and that case is the whole point of the plan: an `executed` plan classes `done`
    in `aw attention`, so handing an obligation to one hides it in the very place this rule exists to
    close.
    """
    owners = carrier_index.get(id6) or []
    if not owners:
        return "dangling", "carrier {0} resolves to no backlog item or plan".format(id6)
    live = [
        o
        for o in owners
        if (o[1] or "").strip().lower() not in _CARRIER_TERMINAL_STATUSES
    ]
    if live:
        return "ok", ""
    statuses = ", ".join(sorted({(o[1] or "?").strip().lower() for o in owners}))
    return "terminal", (
        "carrier {0} resolves only to a terminal/hidden artifact ({1}); nothing revisits it".format(
            id6, statuses
        )
    )


def evaluate_carrier_obligation(
    repo_root: Path,
    obligation: CarrierObligation,
    *,
    carrier_index: Optional[Dict[str, List[Tuple[str, Optional[str], str]]]] = None,
) -> CloseVerdict:
    """The per-row half of the shared predicate. Returns a `CloseVerdict` (never raises).

    Three escapes, exactly the ones `evaluate_blocking_close` proved:

      HANDOFF   - `- Carrier: <id6>` resolving to a backlog item or a NON-terminal plan.
      SATISFIED - `- Carrier-Evidence: <path>` resolving via the SHARED
                  `resolve_evidence_artifact` (the same resolver `aw backlog set done --evidence` uses).
      DECLINED  - `- Carrier-Declined: <reason>` with a non-empty reason. The reason's MERIT is the
                  reviewer's job, exactly as `open_question_error` says of an OQ rationale; requiring a
                  human-judged reason here would be a semantic claim this module cannot make.

    A MALFORMED reference is a FINDING, NOT AN EXCEPTION, following the parse-then-diagnose split the
    sibling evaluators use: `parse_carrier_ids` returns bad tokens instead of raising, so a good token
    beside a bad one still resolves. A gate that crashes on bad input is a gate that gets disabled.
    """
    fields = obligation.fields or {}
    if carrier_index is None:
        try:
            carrier_index = _carrier_index(repo_root)
        except Exception:
            carrier_index = {}

    fixes = (
        "hand it off: add `- Carrier: <id6>` naming an open backlog item or a pending plan "
        "(file one with `aw backlog new`)",
        "cite evidence it is already addressed: add `- Carrier-Evidence: <in-tree artifact path>`",
        "decline it explicitly, with a reason: add `- Carrier-Declined: <why this needs no carrier>`",
    )

    declined = (fields.get(_S.CARRIER_DECLINED_FIELD) or "").strip()
    if declined:
        return CloseVerdict(
            True, "ok", "obligation explicitly declined with a reason", (), "DECLINED"
        )

    evidence = (fields.get(_S.CARRIER_EVIDENCE_FIELD) or "").strip()
    if evidence:
        try:
            resolved = resolve_evidence_artifact(repo_root, evidence)
        except Exception:
            resolved = False
        if resolved:
            return CloseVerdict(
                True,
                "ok",
                "satisfied by resolvable evidence {0!r}".format(evidence),
                (),
                "SATISFIED",
            )
        return CloseVerdict(
            False,
            "error",
            "{0}: `Carrier-Evidence: {1}` does not resolve to an in-tree artifact".format(
                obligation.locator, evidence
            ),
            fixes,
            None,
        )

    raw_carrier = (fields.get(_S.CARRIER_FIELD) or "").strip()
    if raw_carrier:
        good, bad = _S.parse_carrier_ids(raw_carrier)
        if bad:
            return CloseVerdict(
                False,
                "error",
                "{0}: malformed `Carrier` reference(s) {1} (expected a bare 6-char id6)".format(
                    obligation.locator, ", ".join(repr(b) for b in bad)
                ),
                fixes,
                None,
            )
        problems: List[str] = []
        for id6 in good:
            verdict, detail = _resolve_carrier(carrier_index, id6)
            if verdict == "ok":
                return CloseVerdict(
                    True,
                    "ok",
                    "handed off to carrier {0}".format(id6),
                    (),
                    "HANDOFF",
                )
            problems.append(detail)
        return CloseVerdict(
            False,
            "error",
            "{0}: {1}".format(obligation.locator, "; ".join(problems)),
            fixes,
            None,
        )

    return CloseVerdict(
        False,
        "error",
        (
            "{0} records an outstanding obligation with NO durable carrier; once this plan reaches "
            "`executed` it classes `done` in `aw attention` and this vanishes with no record".format(
                obligation.locator
            )
        ),
        fixes,
        None,
    )


def evaluate_durable_carrier(
    repo_root: Path,
    *,
    plan_path: Path,
    plan_text: str,
    open_questions=None,
    carrier_index: Optional[Dict[str, List[Tuple[str, Optional[str], str]]]] = None,
) -> List[_core.Drift]:
    """The ONE evaluator for `check.ipd-uncarried-obligation`, shared by both host surfaces.

    `aw check` (via :func:`check_durable_carrier`) and `aw ipd lint --phase pre-transition` (via
    ``ipd_lint._merge_durable_carrier``) both call THIS function, so the sweep and the checkpoint gate
    cannot drift apart in what counts as carried. That single-predicate property is the stated design
    intent of the nearest precedent (:func:`evaluate_review_finding_escalation`) and is asserted
    directly by ``tests/test_durable_capture.py``.

    Returns AT MOST ONE Drift per plan, enumerating up to five offending locators plus the total count
    (DECISION 07-rnkqrc-D4). Measured 2026-09-18: 664 offending rows live in 106 pending plans, so a
    per-row Drift would add 664 lines to every clean `aw check plans`; the per-row verdicts still exist
    inside :func:`evaluate_carrier_obligation` and are what the tests assert on.

    Severity is per plan via :func:`carrier_severity_for_plan` (post-cutover `error`, else the
    grandfathered advisory tier). Never raises.
    """
    drift: List[_core.Drift] = []
    if open_questions is None:
        try:
            from agent_workflows import ipd_lint as _lint

            open_questions = _lint.parse(plan_text).open_questions
        except Exception:
            open_questions = []
    obligations = _deferred_section_obligations(plan_text) + _question_obligations(
        open_questions
    )
    if not obligations:
        return drift
    if carrier_index is None:
        try:
            carrier_index = _carrier_index(repo_root)
        except Exception:
            carrier_index = {}

    failures: List[Tuple[CarrierObligation, CloseVerdict]] = []
    for ob in obligations:
        verdict = evaluate_carrier_obligation(
            repo_root, ob, carrier_index=carrier_index
        )
        if not verdict.legitimate:
            failures.append((ob, verdict))
    if not failures:
        return drift

    severity = carrier_severity_for_plan(plan_text, repo_root=repo_root)
    shown = failures[:5]
    detail = "{0} obligation(s) name no durable carrier: {1}{2}".format(
        len(failures),
        "; ".join(v.reason for _ob, v in shown),
        ""
        if len(failures) == len(shown)
        else " (and {0} more)".format(len(failures) - len(shown)),
    )
    fixes = shown[0][1].fixes
    drift.append(
        enrich_drift(
            _core.Drift(str(plan_path), _CARRIER_RULE, detail, severity=severity),
            observed="{0} row(s)/question(s) with no `Carrier`, `Carrier-Evidence`, or "
            "`Carrier-Declined` field".format(len(failures)),
            required=(
                "every outstanding obligation an IPD records must name a durable carrier: an OPEN "
                "backlog item or a NON-TERMINAL plan (`- Carrier:`), resolvable evidence "
                "(`- Carrier-Evidence:`), or an explicit reason for declining "
                "(`- Carrier-Declined:`)"
            ),
            recovery=fixes[0] if fixes else "",
        )
    )
    return drift


def check_durable_carrier(
    repo_root: Path, include_untracked: bool = False
) -> List[_core.Drift]:
    """Sweep every PENDING-lane plan for an outstanding obligation with no durable carrier.

    Scoped to pending-lane plans, following the identical grandfathering precedent as
    :func:`check_review_finding_unescalated` and ``check_lifecycle_transitions``: a terminal plan is
    already past the transition this rule gates, and retroactively litigating 527 executed plans would
    be a whole-tree false-positive explosion. The `pre-transition` checkpoint is where a plan HEADING
    for terminal is caught, so nothing is lost by not sweeping the terminal tree.

    The carrier index is built ONCE for the whole sweep rather than per plan.
    """
    drift: List[_core.Drift] = []
    try:
        carrier_index = _carrier_index(repo_root)
    except Exception:
        return drift
    for p in _iter_type_files(repo_root, "plans", include_untracked=include_untracked):
        if "pending" not in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        drift.extend(
            evaluate_durable_carrier(
                repo_root,
                plan_path=p,
                plan_text=text,
                carrier_index=carrier_index,
            )
        )
    return drift


# ======================================================================================
# lintreach Order 01 (`k9awrq`): make the `IPD-*` lint family REACHABLE from the repo-wide sweep.
#
# THE DEFECT THIS CLOSES, measured rather than assumed. Before this, `check_engine` called
# `ipd_lint.parse` in three places but NEVER `ipd_lint.lint_file`, so the entire `IPD-*` diagnostic
# family was invisible to `aw check` and therefore to CI. The reproduction: a scaffolded plan given a
# fabricated `- Readiness: go-pending-approval` with no review verdict in its `## Workflow history`
# yields `IPD-M107` from `aw ipd lint --phase author`, while `aw check plans --agent` returned ZERO
# diagnostics naming that file. So a defect the per-file verb REFUSES could be committed and would sit
# in the tree until someone linted that exact file or tried to execute it.
#
# WHY IT MATTERS BEYOND ONE RULE: `aw check` is what an agent and CI are pointed at for a TREE-WIDE
# verdict, and `aw attention --check` is the fail-closed gate. A rule reachable only from a per-file
# verb fires only when someone ALREADY suspects that file. `IPD-M107` in particular guards a field the
# auto-approve predicate reads FIRST, so the sweep's blindness sat directly upstream of the gate that
# promotes a plan to `approved`.
#
# THE SHAPE IS `check_durable_carrier`'s, MIRRORED AND NOT REINVENTED (see :func:`check_durable_carrier`
# directly above): same pending-lane scope with the same recorded rationale, same one-Drift-per-plan
# enumeration, same fail-isolated call site in `check_content`. The difference is DIRECTION, and it is
# the point of this whole change: `evaluate_durable_carrier` is a check_engine predicate that `ipd_lint`
# calls, whereas this is an `ipd_lint` entry point that check_engine calls. Both give the same property
# `evaluate_review_finding_escalation`'s docstring states as its design intent - the sweep and the
# checkpoint gate cannot drift apart - because there is exactly ONE implementation of the rules.
#
# NOTHING IS RE-IMPLEMENTED HERE, deliberately and as the plan's central constraint. Re-deriving even
# one `IPD-*` rule inside this module would recreate the very drift this change closes. The function
# below contains no rule logic at all: it iterates, calls `lint_file`, and formats.
# ======================================================================================

_IPD_LINT_RULE = "check.ipd-lint-diagnostic"

#: The checkpoint the sweep lints at, and the ONLY defensible one. `author` is the phase valid for an
#: arbitrary pending plan. `pre-transition` was measured CATASTROPHIC for a sweep: 1199 diagnostics
#: across all 76 pending plans at HEAD `cd2e6adb` (1196 of them `IPD-S404`, "not 'performed' at
#: pre-transition"), which is the CORRECT state of any plan that has not executed yet, so sweeping it
#: would mass-fail the tree for being in its normal condition. Review independently measured the same
#: shape (1850 across 104). DO NOT make this configurable and DO NOT default it to the stricter value:
#: a future reader "improving" the sweep that way reintroduces exactly that mass failure, which is why
#: the number is recorded here beside the constant rather than only in the plan.
_IPD_LINT_SWEEP_CHECKPOINT = "author"

#: How many underlying diagnostics one plan's finding enumerates before it summarizes the rest.
#: Mirrors `evaluate_durable_carrier`'s DECISION 07-rnkqrc-D4 (five, then "(and N more)"), for the same
#: reason: a per-diagnostic Drift would let one badly-formed plan add dozens of lines to every
#: `aw check plans`. The full list always remains one command away via the `recovery` field.
_IPD_LINT_SHOWN = 5


def evaluate_ipd_lint_diagnostics(
    repo_root: Path,
    *,
    plan_path: Path,
    checkpoint: str = _IPD_LINT_SWEEP_CHECKPOINT,
) -> List[_core.Drift]:
    """Run the REAL `ipd_lint.lint_file` on one plan and return at most one umbrella Drift.

    This is the whole of the reachability change: `aw ipd lint` (per file) and `aw check plans` (via
    :func:`check_ipd_lint_reach`) now run the SAME `lint_file`, so the sweep cannot report a different
    verdict from the checkpoint gate. No `IPD-*` rule is re-implemented here; this function iterates
    and formats only.

    `ipd_lint` is imported INSIDE the function body, not at module scope, and that is required rather
    than stylistic: `ipd_lint.lint_file` already imports THIS module lazily (for the dependency
    RESOLUTION checks and the review-escalation/durable-carrier merges), so a module-level import here
    would close an import cycle. The established precedent for this exact pattern in this file is
    `check_scope_drift`, which imports `ipd_lifecycle` in its body for the same reason.

    ADVISORY BY MEASUREMENT: the emitted code is registered `info` in `RULE_REGISTRY`, the only
    severity `artifact_core.drift_exit_code` exempts, so this cannot move any caller's exit code. See
    that registration for why `warning` would NOT have been advisory.

    Never raises: a plan that cannot be read or linted yields no finding rather than breaking the
    sweep, matching every neighbouring plans-type rule.
    """
    drift: List[_core.Drift] = []
    try:
        from agent_workflows import ipd_lint as _lint

        result = _lint.lint_file(plan_path, checkpoint=checkpoint)
    except Exception:
        return drift
    diags = list(getattr(result, "diagnostics", None) or [])
    if not diags:
        return drift
    shown = diags[:_IPD_LINT_SHOWN]
    detail = "{0} lint diagnostic(s) at the `{1}` checkpoint: {2}{3}".format(
        len(diags),
        checkpoint,
        "; ".join("{0} {1}".format(d.code, d.message) for d in shown),
        ""
        if len(diags) == len(shown)
        else " (and {0} more)".format(len(diags) - len(shown)),
    )
    codes = ", ".join(sorted({d.code for d in diags}))
    drift.append(
        enrich_drift(
            _core.Drift(str(plan_path), _IPD_LINT_RULE, detail),
            observed="`aw ipd lint --phase {0}` reports {1} diagnostic(s) ({2})".format(
                checkpoint, len(diags), codes
            ),
            required=(
                "a plan must satisfy the `IPD-*` structural/state contract that "
                "`aw ipd lint` enforces, so a defect the per-file verb refuses cannot sit "
                "committed unnoticed"
            ),
            recovery="aw ipd lint {0} --phase {1}".format(plan_path, checkpoint),
        )
    )
    return drift


def check_ipd_lint_reach(
    repo_root: Path, include_untracked: bool = False
) -> List[_core.Drift]:
    """Sweep every PENDING-lane plan through the real `ipd_lint.lint_file` at the `author` checkpoint.

    PENDING-LANE SCOPE, AND IT IS WHAT MAKES `aw check` AND `aw doctor` AGREE (plan OQ-02/E-03,
    DECISION 02-k9awrq-D3). The hazard OQ-02 names is measured and specific: `_iter_type_files` skips
    retired paths unless `include_retired=True`, `executed/` counts as retired, and `doctor.py` passes
    `include_retired=True` UNCONDITIONALLY while `check_engine.check_types` defaults it to False -
    which already produced a real zero-versus-one disagreement between the two surfaces on the
    `check.id6-collision` rule. The `"pending" not in p.parts` guard below does not consult
    `include_retired` at all, so the two surfaces traverse an IDENTICAL set BY CONSTRUCTION rather than
    by coincidence, and no pending plan is excluded by the retired filter either (measured: 0 of 76
    pending plans are `is_retired`).

    IT ALSO COSTS NOTHING IN COVERAGE, which is why the constraint is free to satisfy.
    `ipd_lint.lint_text` returns `DISPOSITION_LEGACY` with NO diagnostics for any plan in a terminal
    directory unless the checkpoint is `post-transition` (see `_is_terminal_dir`), so linting the
    terminal corpus at `author` is guaranteed empty: measured at HEAD `cd2e6adb`, 626 of 702 plans
    returned `legacy/not evaluated`. Sweeping them would buy 626 file reads and 626 parses for a
    result that cannot contain a finding. The motivating defect (a fabricated `- Readiness:` on a plan
    heading for approval) lives in the pending lane by definition.

    This is the same scope, with the same reasoning, that every other pending-scoped plans rule in this
    module already uses: :func:`check_durable_carrier`, :func:`check_review_finding_unescalated`,
    ``check_lifecycle_transitions``, and the rule behind `check.review-decision-unescalated`.

    NOTE ON CITING THAT LAST ONE BY RULE ID RATHER THAN BY SYMBOL, since it looks inconsistent: its
    test (`tests/test_review_decisions.py`) asserts wiring-exactly-once by COUNTING that symbol's
    occurrences in this file's source text, so a prose mention here would read as a second call site and
    fail it. That brittleness is a known and documented pattern in this repository (see
    `tests/test_durable_capture.py`, which removed its own two `inspect.getsource` pins for the same
    reason); citing the rule id sidesteps it without weakening anyone's test.
    """
    drift: List[_core.Drift] = []
    for p in _iter_type_files(repo_root, "plans", include_untracked=include_untracked):
        if "pending" not in p.parts:
            continue
        drift.extend(evaluate_ipd_lint_diagnostics(repo_root, plan_path=p))
    return drift
