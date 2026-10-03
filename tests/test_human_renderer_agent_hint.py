"""Behavior tests for HumanRenderer agent output hint line.

Validates that HumanRenderer outputs the accurate agent output hint and does not
assert the retracted automatic non-TTY switch promise.
"""

from agent_workflows.renderers import HumanRenderer
from agent_workflows.result_types import CommandResult, OutputContext, OutputMode


def test_human_renderer_agent_hint_normal_output():
    renderer = HumanRenderer()
    result = CommandResult(command="check", summary="All checks passed")
    rendered = renderer.render(
        result, OutputContext(mode=OutputMode.HUMAN, color=False)
    )

    lines = rendered.rstrip("\n").split("\n")
    assert lines[-1] == "Agent output: --agent"
    assert "automatic when piped" not in rendered


def test_human_renderer_agent_hint_with_color():
    renderer = HumanRenderer()
    result = CommandResult(command="check", summary="All checks passed")
    rendered = renderer.render(result, OutputContext(mode=OutputMode.HUMAN, color=True))

    lines = rendered.rstrip("\n").split("\n")
    assert lines[-1] == "Agent output: --agent"
    assert "automatic when piped" not in rendered


def test_human_renderer_suppress_agent_hint():
    renderer = HumanRenderer()
    result = CommandResult(
        command="check",
        summary="All checks passed",
        data={"suppress_agent_hint": True},
    )
    rendered = renderer.render(
        result, OutputContext(mode=OutputMode.HUMAN, color=False)
    )

    assert "Agent output:" not in rendered
    assert "automatic when piped" not in rendered
