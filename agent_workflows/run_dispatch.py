"""Host-neutral run dispatch: `aw run as <profile>` and `aw run ipd <selector>`.

`runprofile` Order 04 (`ygzq71`) E-02. This module is a THIN DETERMINISTIC ROUTER and nothing
else. Its whole job is to answer ONE question - WHICH registered host runner owns this
invocation - and then hand the operator's tail to that runner's own parser verbatim. It is
deliberately NOT a second runner: it builds no prompt, spawns no shell, reconstructs no argv,
and re-implements no selector, session, or implicit-`start` logic.

WHY A ROUTER AT ALL. `aw oc run as gem X` already works (`3cm15q`), but it names the HOST in
every invocation. The surface the maintainer selected is host-neutral::

    aw run as gem SELECTOR      # named profile; the PROFILE decides the host
    aw run ipd SELECTOR         # unqualified; `default_runner` decides the host

THE COLLISION RULE, which is the reason this file exists rather than a dynamic subcommand.
`as` and `ipd` are FIXED grammar registered once in `cli.py`; a profile NAME is only ever read
from the bounded position immediately after the literal `as`. So a profile may be called
`status`, `report`, `show`, `evidence` or `run` without shadowing anything, because the command
position is decided BEFORE any configuration file is read. The inverse is equally load-bearing:
no profile ever MANUFACTURES a command, so `aw gem`, `aw gemrun`, `aw run gem`, `aw run-gem`,
`aw run:gem` and `aw rungem` do not exist and must never be invented. A dynamic route would
also make every FUTURE `aw run <verb>` addition silently reinterpret an existing invocation.

RESOLUTION IS NOT DUPLICATED HERE, and that is the second design rule. `runner_profiles`
(executed plan `f2mrsw`) owns the schema, the store, and the precedence chain, and the HOST
RUNNER applies it per launch (`oc_runipd.resolve_launch_profile`). This module therefore
resolves ONLY the runner and forwards the clause, so a launch field is applied EXACTLY ONCE.
Re-resolving `--model`/`--variant`/`--agent` here and injecting them into the forwarded argv
would double-apply them and would fork the precedence chain, which is precisely what the Set's
execution contract forbids.

FAIL CLOSED, NEVER FALL BACK. An unknown profile, an absent `default_runner`, a malformed
store, or a runner with no adapter is a REFUSAL with the exact setup command to fix it. There
is no "assume OpenCode" path: guessing the host would launch a model the operator did not
choose, and (with paid models) they would find out from the bill rather than from a diagnostic.
Every refusal happens BEFORE the host is invoked, so a bad invocation costs nothing durable.

Pure stdlib. The host adapter is imported LAZILY inside the adapter function, so routing to a
future non-OpenCode runner never pays for importing the OpenCode driver.
"""

from __future__ import annotations

import sys
from typing import Callable, Dict, List, Mapping, Optional, Sequence

from agent_workflows import runner_profiles

#: Exit code for every dispatch refusal. 2 is the repository's "cannot run / usage" class and
#: matches `oc_runipd`'s own `DriverError` contract, so a refusal here is indistinguishable in
#: kind from the same refusal raised one layer down.
EXIT_CANNOT_RUN = 2

#: The literal, FIXED grammar tokens. Kept as constants so `cli.py` and this module cannot
#: drift on the spelling, and so a test can assert the surface is exactly these two.
AS_TOKEN = "as"
IPD_TOKEN = "ipd"

_USAGE = (
    "usage: aw run as <profile> [SELECTOR ...]     # named profile; the profile picks the host\n"
    "       aw run ipd [SELECTOR ...]              # the configured default_runner picks the host"
)


class RunDispatchError(Exception):
    """A dispatch refusal: the runner could not be resolved, or has no adapter.

    Carries a message that NAMES THE FIX (the exact `aw oc profile ...` command), because the
    operator hitting this has a configuration gap, not a bug, and a bare "unknown runner" would
    leave them guessing.
    """


# ==================================================================================================
# The adapter registry (the host seam)
# ==================================================================================================


def _dispatch_opencode(argv: Sequence[str]) -> int:
    """Hand `argv` to the OpenCode driver's OWN parser and return its exit code unchanged.

    This is the entire OpenCode adapter, deliberately. `oc_runipd.main` already accepts the
    canonical `as <profile>` clause (`3cm15q` E-01, `oc_runipd.extract_profile_clause`) and owns
    the implicit-`start` shim, selector resolution, `--model`/`--variant`/`--agent`, `--help`,
    stdout/stderr, interruption handling and every exit code. Calling it IN-PROCESS (no
    subprocess, no shell, no rebuilt prompt) is what makes `aw run as gem X` behaviorally
    identical to `aw oc run as gem X` rather than merely similar.

    Imported lazily: the driver is a large module, and a run routed to a future non-OpenCode
    host must not pay to import it.
    """

    from agent_workflows import oc_runipd

    return oc_runipd.main(list(argv))


#: Canonical runner name -> adapter. THE HOST SEAM, and deliberately DATA rather than a
#: `register()` mutator so nothing at runtime can widen the set of hosts a run may reach.
#:
#: Version 1 registers OpenCode only, matching `runner_profiles.RUNNER_REGISTRY`. A runner that
#: is a valid SCHEMA value but has no row here is "registered but not implemented", which is a
#: distinct and separately-reported failure from "not a runner at all": the first is a roadmap
#: gap, the second is a typo, and telling the operator which one they hit is the difference
#: between a five-second fix and a bug report.
RUNNER_ADAPTERS: Dict[str, Callable[[Sequence[str]], int]] = {
    "oc": _dispatch_opencode,
}


def registered_runners() -> List[str]:
    """The canonical names of runners this router can actually dispatch to (sorted)."""

    return sorted(RUNNER_ADAPTERS)


def adapter_for(runner: str) -> Callable[[Sequence[str]], int]:
    """Return the adapter for canonical `runner`, or raise :class:`RunDispatchError`.

    Two distinct refusals, never collapsed into one message:

    * the name is not a runner AT ALL (rejected by :func:`runner_profiles.canonical_runner`), and
    * the name IS a schema-valid runner with NO adapter yet (registered-but-unimplemented).
    """

    try:
        canonical = runner_profiles.canonical_runner(runner)
    except runner_profiles.RunnerProfileError as exc:
        raise RunDispatchError(
            f"{exc} Runners this build can dispatch to: "
            f"{', '.join(registered_runners())}."
        ) from exc

    adapter = RUNNER_ADAPTERS.get(canonical)
    if adapter is None:
        raise RunDispatchError(
            f"runner {canonical!r} is a known runner but has no dispatch adapter in this "
            f"build, so `aw run` cannot launch it. Runners this build can dispatch to: "
            f"{', '.join(registered_runners())}. Use that host's own command directly, or "
            f"name a profile whose runner is one of them ('aw oc profile list')."
        )
    return adapter


# ==================================================================================================
# Runner resolution (profile -> runner, or default_runner -> runner)
# ==================================================================================================


def _load_config() -> runner_profiles.ProfileConfig:
    """Load the profile store, converting every typed failure into a dispatch refusal.

    A MALFORMED store must refuse rather than degrade to "empty", for the reason
    `runner_profiles` states in its own docstring: an empty config would silently launch the
    HOST DEFAULT model instead of the configured one.
    """

    try:
        return runner_profiles.load()
    except runner_profiles.RunnerProfileError as exc:
        raise RunDispatchError(f"runner profiles: {exc}") from exc


def resolve_named_runner(
    profile: str, cfg: Optional[runner_profiles.ProfileConfig] = None
) -> str:
    """Return the canonical runner that PROFILE runs on (E-02, named dispatch).

    The profile is the authority on its own host: `gem` names a model, and that model belongs to
    exactly one runner. So a named dispatch never consults `default_runner`, and never guesses.
    """

    config = cfg if cfg is not None else _load_config()
    try:
        return config.get(profile).runner
    except runner_profiles.RunnerProfileError as exc:
        raise RunDispatchError(f"runner profiles: {exc}") from exc


def resolve_default_runner(
    cfg: Optional[runner_profiles.ProfileConfig] = None,
) -> str:
    """Return the canonical runner for UNQUALIFIED dispatch (E-02, default dispatch).

    Delegates to :func:`runner_profiles.resolve` with ``generic=True`` rather than reading
    ``cfg.default_runner`` directly, so the "no runner was named and no default_runner is
    configured" refusal (and its remediation text) is authored ONCE, in the resolver that owns
    the precedence chain.
    """

    config = cfg if cfg is not None else _load_config()
    try:
        return runner_profiles.resolve(config, generic=True).runner
    except runner_profiles.RunnerProfileError as exc:
        raise RunDispatchError(f"runner profiles: {exc}") from exc


# ==================================================================================================
# The two routes
# ==================================================================================================


def _wants_route_help(tail: Sequence[str]) -> bool:
    """Is this an invocation that asks for THIS ROUTE's help rather than a host's?

    True only when the help token comes FIRST, i.e. before any profile or selector has been
    given (`aw run as --help`, `aw run ipd -h`). At that point the route owns the whole
    invocation and no host has been selected yet, so answering with the route's own grammar is
    the only answer available WITHOUT configuration - and `--help` must never fail closed merely
    because `default_runner` is unset.

    A help token appearing LATER (`aw run as gem --help`) is the HOST's, forwarded verbatim, so
    it stays byte-identical to `aw oc run as gem --help`.
    """

    return bool(tail) and tail[0] in ("-h", "--help")


ROUTE_HELP = f"""Run an IPD through a host runner, choosing the host WITHOUT naming it.

{_USAGE}

  aw run as gem 3cm15q            # launch with the saved profile 'gem'
  aw run as gem all --variant high    # profile fields, with the variant overridden
  aw run ipd 3cm15q               # launch with the configured default_runner

'as' and 'ipd' are FIXED grammar. A profile name is read ONLY from the position right after
'as', so a profile may be named 'status' or 'report' without shadowing a command, and no
profile ever becomes a command: 'aw gem', 'aw run gem' and 'aw run-gem' do not exist.

Every flag after the profile/selector belongs to the host runner and is forwarded verbatim;
see that host's own help (e.g. 'aw oc run --help') for the real flag set. Launch fields are
resolved once, by the host, with precedence: explicit --model/--variant/--agent > the named
profile > the per-runner default profile > the host's own default.

Manage profiles and defaults with 'aw oc profile' ('list', 'add', 'default')."""


def dispatch_named(tail: Sequence[str]) -> int:
    """Route `aw run as <profile> [SELECTOR ...]`. Returns the host runner's exit code.

    `tail` is everything after the literal `as`. Its FIRST token is the profile name by the
    fixed grammar (the position was decided by the parser, before configuration was read), and
    every later token belongs to the host.

    The forwarded argv re-states the clause as `as <profile> ...` so the HOST re-validates the
    name and applies the precedence chain itself. That is what keeps this route from forking
    resolution, and it is why an explicit `--model` in `tail` is applied exactly once.
    """

    tokens = [str(t) for t in tail]
    if _wants_route_help(tokens):
        print(ROUTE_HELP)
        return 0
    if not tokens:
        raise RunDispatchError(f"'as' requires a profile name.\n{_USAGE}")
    profile = tokens[0]
    if profile.startswith("-"):
        raise RunDispatchError(
            f"'as' requires a profile name, but got the option {profile!r}. The profile name "
            f"comes immediately after 'as'.\n{_USAGE}"
        )

    runner = resolve_named_runner(profile)
    adapter = adapter_for(runner)
    return adapter([AS_TOKEN, profile, *tokens[1:]])


def dispatch_default(tail: Sequence[str]) -> int:
    """Route `aw run ipd [SELECTOR ...]`. Returns the host runner's exit code.

    Forwards `tail` UNCHANGED (no `as` clause), which is what makes this exactly equivalent to
    the host's own unqualified form (`aw oc run SELECTOR`) once `default_runner` is `oc`. The
    host then applies its per-runner DEFAULT profile through the shared resolver, so the default
    profile reaches the launch through the same single path a named one does.
    """

    tokens = [str(t) for t in tail]
    if _wants_route_help(tokens):
        print(ROUTE_HELP)
        return 0

    runner = resolve_default_runner()
    adapter = adapter_for(runner)
    return adapter(tokens)


#: Fixed token -> route. Used by `cli.py` so the two entry points and their handlers are
#: registered from ONE table and a third spelling cannot be added in only one of the two places.
ROUTES: Mapping[str, Callable[[Sequence[str]], int]] = {
    AS_TOKEN: dispatch_named,
    IPD_TOKEN: dispatch_default,
}


def dispatch(token: str, tail: Sequence[str]) -> int:
    """Dispatch one fixed route, rendering a refusal on stderr as exit 2.

    THE ONE ENTRY POINT `cli.py` calls, from both its pre-`parse_args` forwarding block and its
    parsed-namespace branch, so the two routes cannot diverge in behavior or in error rendering.
    """

    route = ROUTES.get(token)
    if route is None:  # pragma: no cover - unreachable via the fixed parser grammar
        print(
            f"aw run: unknown dispatch route {token!r}. Valid routes: "
            f"{', '.join(sorted(ROUTES))}.\n{_USAGE}",
            file=sys.stderr,
        )
        return EXIT_CANNOT_RUN
    try:
        return route(tail)
    except RunDispatchError as exc:
        print(f"aw run {token}: {exc}", file=sys.stderr)
        return EXIT_CANNOT_RUN
