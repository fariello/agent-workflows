"""Render documentation tables FROM the evidence registries (never hand-copied claims).

awoptimize Order 18 (`0zst62`) E-01 / E-02.

Support and performance tables in the operator/author/security documentation are GENERATED
from their evidence registries (Order 10 capability, Orders 12/13 benchmark) so documented
prose can never exceed a recorded claim (IPD Findings). This module renders:

  * :func:`render_support_table`   - host/version/feature support, FROM the capability
                                      registry (a feature shows ``supported`` only if the
                                      registry promoted it; everything else is ``unverified``).
  * :func:`render_model_profile_table` - model profiles as EVIDENCE-BACKED defaults: it
                                      distinguishes the model ID from the reasoning config, and
                                      renders benchmark date, task corpus, host, version,
                                      thresholds, uncertainty, and pending combinations FROM the
                                      benchmark/threshold registries. It emits NO universal
                                      quality claim.
  * :func:`render_benchmark_thresholds_table` - the release thresholds per risk class, FROM the
                                      threshold policy.

Every rendered table carries an explicit provenance line (source registry + as-of date) so a
reader can see the claim is evidence-backed. The prose in the docs themselves must contain NO
em/en dashes (ASCII only); the renderers here likewise emit ASCII hyphens only.

Pure stdlib (D138); no runtime YAML (D139). Python 3.9+.
"""

from __future__ import annotations

import datetime
from typing import Any, List, Mapping, Optional, Sequence

from agent_workflows import benchmark_corpus as bc
from agent_workflows import benchmark_thresholds as bt
from agent_workflows import host_adapters as ha
from agent_workflows import host_capability_registry as hcr
from agent_workflows import workflow_profile as wp

# The status string used for any claim not proven by the registry.
UNVERIFIED = hcr.STATUS_UNVERIFIED


def _as_of(now: Optional[datetime.datetime] = None) -> str:
    return (now or datetime.datetime.now(datetime.timezone.utc)).date().isoformat()


# ==================================================================================================
# Support table (from the capability registry, via the adapters)
# ==================================================================================================


def render_support_table(
    adapters: Mapping[str, ha.HostAdapter],
    now: Optional[datetime.datetime] = None,
) -> str:
    """Render the host support table FROM the evidence-gated adapters.

    The table body is the SAME as :func:`host_adapters.build_support_table` (the single
    generator), with an explicit provenance line prepended so the doc reader sees it is
    generated from the capability registry, not hand-written.
    """
    provenance = (
        f"Source: host capability-evidence registry (Order 10). As of {_as_of(now)}. "
        "A feature is 'supported' only where a live probe promoted it; every other cell is "
        "'unverified'."
    )
    body = ha.build_support_table(adapters)
    return provenance + "\n\n" + body


# ==================================================================================================
# Model profile table (evidence-backed defaults, NOT universal quality claims)
# ==================================================================================================


def render_model_profile_table(
    profiles: Sequence[Mapping[str, Any]],
    benchmark_date: str,
    task_corpus: Sequence[str] = bc.TASK_CLASSES,
    host: str = "",
    host_version: str = "",
    uncertainty: str = "",
    pending_combinations: Sequence[str] = (),
    now: Optional[datetime.datetime] = None,
) -> str:
    """Render a model-profile table as EVIDENCE-BACKED defaults.

    Each profile row distinguishes the MODEL ID from the REASONING configuration (they are
    different columns), and the table header records the benchmark date, the task corpus, the
    host/version the evidence came from, and the measurement uncertainty. Any combination not
    yet measured is listed under 'pending' rather than asserted. The renderer emits NO
    universal quality guarantee: the caption states these are defaults observed on a specific
    corpus/host, not a general claim.

    ``profiles`` is a sequence of ROW mappings. Each row carries a ``profile`` submapping (the
    TRANSPORT knobs, validated with :func:`workflow_profile.validate_profile`; the reasoning
    tier must be one of :data:`workflow_profile.REASONING_LEVELS`) and, SEPARATELY, a
    ``model_id`` string. The model ID is deliberately NOT part of the profile: a profile tunes
    transport (packet size, output format, reasoning tier) only, never the model identity or
    the workflow's semantics. Keeping them in different columns is the whole point of E-02.
    """
    lines: List[str] = []
    lines.append(
        "These are evidence-backed DEFAULTS observed on the task corpus and host below, "
        "not a universal quality claim about any model."
    )
    lines.append("")
    lines.append(f"- Benchmark date: {benchmark_date or '(unrecorded)'}")
    lines.append(f"- Task corpus: {', '.join(task_corpus) or '(none)'}")
    lines.append(f"- Host / version: {host or '(unspecified)'} {host_version}".rstrip())
    lines.append(f"- Measurement uncertainty: {uncertainty or '(unrecorded)'}")
    lines.append(f"- Rendered as of: {_as_of(now)}")
    lines.append("")
    lines.append("| Model ID | Profile | Reasoning config | Output format | Notes |")
    lines.append("|---|---|---|---|---|")
    for row in profiles:
        model_id = str(row.get("model_id", "(model id, distinct from profile)"))
        profile = dict(row.get("profile", {}))
        wp.validate_profile(profile)
        name = str(profile.get("name", ""))
        reasoning = str(profile.get("reasoning_level", "(default)"))
        out_fmt = str(profile.get("output_format", "(host default)"))
        notes = str(row.get("notes", ""))
        lines.append(f"| {model_id} | {name} | {reasoning} | {out_fmt} | {notes} |")
    if pending_combinations:
        lines.append("")
        lines.append("Pending (not yet measured; no claim made):")
        for combo in pending_combinations:
            lines.append(f"- {combo}")
    return "\n".join(lines)


# ==================================================================================================
# Benchmark thresholds table (from the threshold policy)
# ==================================================================================================


def render_benchmark_thresholds_table(
    policy: Optional[bt.ThresholdPolicy] = None,
    now: Optional[datetime.datetime] = None,
) -> str:
    """Render the release thresholds per risk class FROM the threshold policy.

    The non-negotiable invariants (0 critical escapes, 100% evidence validity) are visible in
    the table so a reader can see the release bar.
    """
    pol = policy or bt.ThresholdPolicy()
    provenance = (
        f"Source: benchmark threshold policy (Orders 12/13). As of {_as_of(now)}. "
        "Critical escapes must be 0 and evidence validity must be 1.0 (non-negotiable)."
    )
    lines = [
        provenance,
        "",
        "| Risk class | Min requirement recall | Min task correctness | Min test integrity | "
        "Max critical escapes | Min evidence validity |",
        "|---|---|---|---|---|---|",
    ]
    for risk_class in sorted(pol.thresholds):
        t = pol.thresholds[risk_class]
        lines.append(
            f"| {risk_class} | {t.min_requirement_recall} | {t.min_task_correctness} | "
            f"{t.min_test_integrity} | {t.max_critical_escapes} | {t.min_evidence_validity} |"
        )
    return "\n".join(lines)


__all__ = [
    "UNVERIFIED",
    "render_support_table",
    "render_model_profile_table",
    "render_benchmark_thresholds_table",
]
