"""Local git-hook entry points packaged with agent_workflows.

These modules back the `repo: local` hooks in a target repo's `.pre-commit-config.yaml`; they run on
the acting machine at commit time (best-effort, LOCAL prevention - never a remote/CI gate).
"""
