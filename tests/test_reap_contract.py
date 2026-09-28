"""Runtime guard asserting bound_expiry_reaper's reap contract matches the product call."""

from __future__ import annotations

import inspect
from pathlib import Path
import types
import typing
from typing import Any

import pytest

from agent_workflows import lane_containment, runner_shutdown


def _annotation_to_signature(annotation: Any) -> inspect.Signature:
    """Convert a reap annotation (Callable or Protocol) into an inspect.Signature.

    Follows three load-bearing conversion rules:
    (a) Dispatch on getattr(member, "_is_protocol", False), NOT hasattr(member, "__call__").
        Protocol classes inherit __call__ via their metaclass, so hasattr routes Protocols
        into the Callable branch.
    (b) Flatten Callable parameter list. For Callable[[A, B], R], get_args returns ([A, B], R),
        so param types arrive as a nested list that must be flattened.
    (c) Build Callable parameters as POSITIONAL_ONLY since Callable specifies positional args.
    """
    origin = typing.get_origin(annotation)
    if origin is typing.Union or (
        hasattr(types, "UnionType") and origin is types.UnionType
    ):
        members = [a for a in typing.get_args(annotation) if a is not type(None)]
        member = members[0] if len(members) == 1 else annotation
    else:
        member = annotation

    if getattr(member, "_is_protocol", False):
        raw_sig = inspect.signature(member.__call__)
        params = [p for name, p in raw_sig.parameters.items() if name != "self"]
        return raw_sig.replace(parameters=params)

    args = typing.get_args(member)
    if args:
        param_types = args[0]
        if isinstance(param_types, (list, tuple)):
            flat_params = list(param_types)
        else:
            flat_params = [param_types]
        params = [
            inspect.Parameter(
                f"__p{i}", inspect.Parameter.POSITIONAL_ONLY, annotation=pt
            )
            for i, pt in enumerate(flat_params)
        ]
        return_type = args[1] if len(args) > 1 else inspect.Signature.empty
        return inspect.Signature(parameters=params, return_annotation=return_type)

    return inspect.Signature()


def test_bound_expiry_reaper_reap_annotation_binds_product_call() -> None:
    """Assert bound_expiry_reaper's reap annotation binds the call the product makes."""
    hints = typing.get_type_hints(lane_containment.bound_expiry_reaper)
    raw_reap = hints.get("reap")
    sig = _annotation_to_signature(raw_reap)
    process_sentinel = object()
    run_dir = Path("/tmp/fake_run_dir")
    try:
        sig.bind(process_sentinel, run_dir=run_dir)
    except TypeError as exc:
        pytest.fail(f"Declared reap type {raw_reap} refuses product call: {exc}")


def test_clean_shutdown_signature_binds_product_call() -> None:
    """Assert runner_shutdown.clean_shutdown signature binds the same call."""
    process_sentinel = object()
    run_dir = Path("/tmp/fake_run_dir")
    sig = inspect.signature(runner_shutdown.clean_shutdown)
    try:
        sig.bind(process_sentinel, run_dir=run_dir)
    except TypeError as exc:
        pytest.fail(
            f"runner_shutdown.clean_shutdown signature refuses product call: {exc}"
        )
