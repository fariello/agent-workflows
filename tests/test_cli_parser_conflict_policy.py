"""Tests for CLI parser conflict-handler policy across all builders.

Guards that every parser builder in the package defaults to argparse's 'error'
conflict handler rather than 'resolve', so that duplicate option definitions
raise an ArgumentError at parser build time instead of silently overwriting
earlier registrations.

Note on the second '--agent' declaration:
`agent_workflows/cli.py` declares `--agent` twice on distinct shared parents:
once on `common` (with action='store_true') and once on `common_upgrade` (with
action='store_true', default=argparse.SUPPRESS). Today, these do not collide
because no parser inherits both parents simultaneously (162 parser objects carry
one `--agent` and 12 carry none). If a future command or refactor declares
`parents=[common, common_upgrade]`, that collision will raise loudly at parser
build time under this policy. That failure is the guard working as intended to
prevent silent option mutation, NOT a regression, and must be resolved by fixing
the parent inheritance or option names rather than reaching for 'resolve'.
"""

import argparse
from typing import Callable, Dict

import pytest

from agent_workflows import (
    agy_runipd,
    cli,
    layout_inventory,
    oc_models,
    oc_runipd,
    pwatch,
    upgrade_rehearsal,
)

BUILDERS: dict[str, Callable[[], argparse.ArgumentParser]] = {
    "cli": cli._build_parser,
    "oc_runipd": oc_runipd.build_parser,
    "agy_runipd": agy_runipd.build_parser,
    "layout_inventory": layout_inventory.build_parser,
    "oc_models": oc_models.build_parser,
    "upgrade_rehearsal": upgrade_rehearsal.build_parser,
    "pwatch": pwatch.build_parser,
}


def _collect_parser_objects(
    parser: argparse.ArgumentParser,
    seen: Dict[int, argparse.ArgumentParser] | None = None,
) -> Dict[int, argparse.ArgumentParser]:
    """Walk all reachable parser and subparser objects, deduplicated by id().

    Aliases in subparsers register the exact same parser object under multiple
    keys in _SubParsersAction.choices. Deduplicating by id() ensures every
    parser object is counted and inspected exactly once.
    """
    if seen is None:
        seen = {}
    pid = id(parser)
    if pid in seen:
        return seen
    seen[pid] = parser
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for subp in action.choices.values():
                _collect_parser_objects(subp, seen)
    return seen


@pytest.mark.parametrize("builder_name,builder", list(BUILDERS.items()))
def test_all_builders_construct_without_raising(
    builder_name: str, builder: Callable[[], argparse.ArgumentParser]
) -> None:
    """Every parser builder in the package must construct without raising."""
    parser = builder()
    assert isinstance(parser, argparse.ArgumentParser)


@pytest.mark.parametrize("builder_name,builder", list(BUILDERS.items()))
def test_every_reachable_parser_object_uses_error_handler(
    builder_name: str, builder: Callable[[], argparse.ArgumentParser]
) -> None:
    """Every reachable parser object from every builder must report _handle_conflict_error."""
    root = builder()
    parsers = _collect_parser_objects(root)
    assert len(parsers) >= 1

    for pid, p in parsers.items():
        handler = p._get_handler()
        assert handler.__name__ == "_handle_conflict_error", (
            f"Parser {p.prog!r} (id={pid}) in {builder_name} reported handler {handler.__name__}, "
            f"expected _handle_conflict_error"
        )
        assert handler.__func__ is argparse._ActionsContainer._handle_conflict_error


def test_cli_parser_object_count_lower_bound() -> None:
    """The root CLI parser tree must contain at least 150 distinct parser objects.

    Asserts a conservative lower bound rather than strict equality so ongoing
    command tree additions do not break this test.
    """
    root = cli._build_parser()
    parsers = _collect_parser_objects(root)
    assert len(parsers) >= 150


def test_duplicate_option_raises_argument_error_on_aw_parser() -> None:
    """Registering duplicate options on _AwArgumentParser raises ArgumentError at build time."""
    parser = cli._AwArgumentParser(prog="test-aw-parser")
    parser.add_argument("--dup-flag", help="First registration")

    with pytest.raises(
        argparse.ArgumentError, match="conflicting option string: --dup-flag"
    ):
        parser.add_argument("--dup-flag", help="Second registration")


def test_duplicate_option_raises_on_inherited_parent_action() -> None:
    """Registering an option colliding with a shared parent raises ArgumentError.

    This reproduces the scenario of plan p0l1to, verifying that a subparser
    inheriting a parent cannot silently overwrite or empty the parent's option_strings.
    """
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--agent", action="store_true", help="Shared machine flag")

    sub = cli._AwArgumentParser(prog="test-sub", parents=[common])
    with pytest.raises(
        argparse.ArgumentError, match="conflicting option string: --agent"
    ):
        sub.add_argument("--agent", help="Duplicate agent flag")

    # Confirm the parent action's option_strings remained intact and was not emptied
    assert common._actions[0].option_strings == ["--agent"]


def test_duplicate_option_raises_on_fresh_cli_tree() -> None:
    """Registering a colliding option on a freshly built CLI parser raises ArgumentError."""
    parser = cli._build_parser()
    with pytest.raises(
        argparse.ArgumentError, match="conflicting option string: --agent"
    ):
        parser.add_argument("--agent", help="Collision with existing --agent")
