"""OPT-IN local pre-push gate: prevent an accidental push and EXPLAIN what real authorization needs
(agentadhere Phase 4, IPD diundn E-02).

This hook is CONVENIENCE / FEEDBACK ONLY - it is explicitly NOT an authority boundary. A local
pre-push hook is not cloned by default, is skippable with ``--no-verify``, and its acknowledgement
signal (the ``AW_PUSH_AUTHORIZED`` env var) is visible to and settable by the agent, so it provides
NO independent authorization (findings 5.5). The AUTHORITATIVE control for "no push without
authorization" (catalog invariant I-02) is a protected remote branch / required CI / brokered
credential - the deferred external-authority set. This hook only helps a cooperative operator avoid
an ACCIDENTAL push and teaches where real authorization comes from.

It delegates to the SINGLE shared ``check_engine.check_push_authorization`` surface (no forked
policy), so the hook and ``aw check`` describe the same invariant. The refusal message states the
honest local-only / bypassable limit explicitly.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple


def check(repo_root: Optional[Path] = None) -> Tuple[int, List[str]]:
    """Run the gate. Returns (exit_code, messages). exit 0 = ok (acknowledged), 1 = prevented.

    Delegates to the shared ``check_engine.check_push_authorization``. The local acknowledgement is
    the ``AW_PUSH_AUTHORIZED`` env var (convenience only, NOT independent authorization).
    """
    from agent_workflows import check_engine as _ce

    root = Path(repo_root) if repo_root is not None else Path(".")
    ack = os.environ.get(_ce.PUSH_ACK_ENV, "").strip() not in ("", "0", "false", "no")
    drift = _ce.check_push_authorization(root, ack=ack)
    if not drift:
        return 0, []
    messages: List[str] = []
    for d in drift:
        recovery = getattr(d, "recovery", "") or ""
        if recovery:
            messages.append(
                f"{d.location}: {d.rule}: {d.detail}\n      fix: {recovery}"
            )
        else:
            messages.append(f"{d.location}: {d.rule}: {d.detail}")
    return 1, messages


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry for the pre-push hook. Prints refusals to stderr; exits 0 (ok) or 1 (prevented)."""
    import sys

    exit_code, messages = check()
    if messages:
        sys.stderr.write(
            "aw pre-push authorization gate PREVENTED this push (local accidental-push guard; set "
            f"{'AW_PUSH_AUTHORIZED=1'} to acknowledge an intended, authorized push):\n"
        )
        for m in messages:
            sys.stderr.write(f"  - {m}\n")
        sys.stderr.write(
            "(HONEST LIMIT: this is a LOCAL, OPT-IN, bypassable (`--no-verify`) FEEDBACK hook, NOT an "
            "authority boundary and NOT independent authorization - a local env ack is settable by "
            "the agent. Real push authorization is a protected branch / required CI / brokered "
            "credential.)\n"
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
