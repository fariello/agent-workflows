"""The reusable runner-profile interview: pick a model, pick a variant, preview, save.

`runprofile` Order 02 (`p0l1to`) E-02 / E-04. This module turns "I want to type `gem` instead of
`--model google/gemini-3.7-flash --variant high`" into a saved profile, WITHOUT the user editing
JSON or remembering a flag set. It is the human-facing half of the feature; the schema, the store,
the mutations and the resolution all belong to `agent_workflows.runner_profiles`
(`runprofile` Order 01, `f2mrsw`) and are CONSUMED here, never re-implemented. Order 05
(`p7xhhm`) decides where `aw setup` calls :func:`run_wizard`; keeping the interview here is what
makes that possible without duplicating any of it.

DEPENDENCY-INJECTED ON PURPOSE, and this is the design's load-bearing choice. Every input, every
line of output, the model catalog, and the store's read/write path arrive as :class:`WizardIO`
fields. Nothing here calls `input()`, `print()`, `subprocess`, or `store_path()` directly, so the
whole interview is unit-testable from a scripted transcript with no TTY, no OpenCode installation,
and no user configuration on disk. A wizard that could only be tested by hand is a wizard whose
cancel path is never tested, and the cancel path is exactly where a wizard corrupts a config.

FIVE BEHAVIORS THIS FILE EXISTS TO GUARANTEE. Each one is a way a plausible implementation would
have been wrong, and each has a named falsifier in `tests/test_runner_profile_wizard.py`:

1. DISCOVERY FAILURE IS NEVER GREEN-WASHED, AND NEVER FATAL. `oc_models.discover_models` reports
   an unavailable catalog with a NAMED reason (missing binary, timeout, nonzero exit, unparseable,
   no models). The interview states that reason verbatim and falls through to EXACT MANUAL ENTRY,
   because the model the user most wants may be a private one their catalog never lists. It does
   not pretend the catalog was empty, and it does not refuse to create the profile.
2. A LARGE CATALOG STAYS USABLE. The maintainer's own installation lists 140 models today
   (measured: `opencode models | wc -l` = 140), which is already past "dump it and ask for a
   number". Selection is case-insensitive substring FILTERING plus bounded PAGING
   (:data:`PAGE_SIZE`), stdlib-only; no fuzzy-search dependency.
3. VARIANT SUPPORT IS NOT OVERCLAIMED. OpenCode documents `--variant` as
   "model variant (provider-specific reasoning effort, e.g., high, max, minimal)" (measured from
   `opencode run --help`). So the common choices are offered LABELED as provider-specific, a
   custom exact value is always accepted, and "provider default" is stored as NO variant rather
   than as a guessed string. The wizard validates SHAPE and discovered membership; it never
   claims a provider accepts a value, and it never launches a paid model to find out.
4. THE PREVIEW IS EXACT. Before the save question the user sees the stored profile fields AND the
   equivalent OpenCode argv fragment, built from the same resolved values that will be written.
   An approximate preview would be worse than none, because it would be trusted.
5. NOTHING IS WRITTEN UNLESS THE USER SAYS YES. Save defaults to NO. Cancellation, EOF,
   KeyboardInterrupt, an exhausted retry budget, and a declined save all return without calling
   the writer at all, so a declined flow leaves the config bytes BYTE-IDENTICAL (asserted by
   byte comparison in the tests, not merely by inspection).

DEFAULTS ARE TWO SEPARATE QUESTIONS, BOTH DEFAULT NO (E-04). Saving `gem` must not silently
change what an unqualified `aw oc run` does: that is a different decision from creating an alias,
so it is a different question. "Make NAME the default OpenCode profile?" and "Make OpenCode the
default IPD runner?" are asked independently, the second only when it would actually change
something, and DECLINING EITHER PRESERVES ITS PRIOR VALUE. Every accepted change lands in ONE
atomic write (`runner_profiles.save`), so a wizard cannot leave a half-applied configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Mapping, Optional, Sequence, Tuple

from agent_workflows import oc_models, runner_profiles as rp

#: Models shown per page when the (possibly filtered) catalog is longer than this.
PAGE_SIZE = 20

#: Attempts allowed for one question before the interview gives up and writes nothing. Bounded so
#: a scripted/pipe-fed caller cannot loop forever, and so a confused user is not trapped.
MAX_ATTEMPTS = 5

#: The common variant words, offered as a CONVENIENCE and labeled provider-specific. This is not a
#: capability claim: OpenCode's own help calls `--variant` provider-specific, so a provider may
#: accept none of these, and a provider may accept something not listed (hence the custom option).
COMMON_VARIANTS: Tuple[str, ...] = ("low", "medium", "high", "max")

#: The runner this wizard configures. The schema's registry (`runner_profiles.RUNNER_REGISTRY`)
#: now holds a second row (`agy`), but this wizard still writes OpenCode profiles ONLY, and that
#: is deliberate rather than an oversight: a second host needs its own adapter, not a widened
#: wizard. `agy` has no dispatch adapter (`run_dispatch.RUNNER_ADAPTERS`), so offering it here
#: would let a user create by wizard a profile nothing in this build can launch.
RUNNER = "oc"

_CANCEL_WORDS = frozenset(("q", "quit", "cancel", "abort"))


def validate_optional_field(kind: str, value: str, model: str) -> str:
    """Validate a ``variant``/``agent`` token through the SCHEMA's own public validator.

    There is no public single-field validator in `runner_profiles`, and reaching for its private
    `_validate_field` would couple this module to an internal name. Instead this round-trips a
    minimal profile document through the public :func:`runner_profiles.parse_profile`, which is the
    exact code path a saved profile takes: a value accepted here is therefore guaranteed storable,
    and one refused here would have been refused at save time anyway. ``kind`` is ``"variant"`` or
    ``"agent"``; raises :class:`runner_profiles.ProfileSchemaError`.
    """

    if kind not in ("variant", "agent"):  # pragma: no cover - programming error
        raise ValueError(f"kind must be 'variant' or 'agent', got {kind!r}")
    probe = rp.parse_profile("probe", {"runner": RUNNER, "model": model, kind: value})
    validated = getattr(probe, kind)
    assert isinstance(validated, str)  # parse_profile guarantees it for a present value
    return validated


class WizardCancelled(Exception):
    """The user cancelled (explicit quit word, EOF, interrupt, or an exhausted retry budget).

    Raised INTERNALLY and converted into a :class:`WizardResult` with ``saved=False`` by
    :func:`run_wizard`, so a caller never has to catch it to keep the config intact.
    """


@dataclass
class WizardIO:
    """The whole outside world, injected.

    ``ask`` receives one prompt string and returns the raw line; it must raise ``EOFError`` at end
    of input and may raise ``KeyboardInterrupt``, both of which the interview treats as a cancel.
    ``emit`` receives one line of output. ``discover`` returns an :class:`oc_models.ModelCatalog`.
    ``load``/``save`` are the store boundary; leaving ``save`` unset makes the whole interview
    provably incapable of writing, which is how the read-only tests are written.
    """

    ask: Callable[[str], str]
    emit: Callable[[str], None]
    discover: Callable[[], oc_models.ModelCatalog] = oc_models.discover_models
    load: Callable[[], rp.ProfileConfig] = rp.load
    save: Optional[Callable[[rp.ProfileConfig], Any]] = None

    def line(self, text: str = "") -> None:
        self.emit(text)


@dataclass
class WizardResult:
    """What the interview did. ``saved`` is FALSE for every non-save path.

    ``config`` is the configuration as it stands after the interview (unchanged when nothing was
    saved), so a caller such as `aw setup` can chain a second profile without reloading.
    """

    saved: bool
    name: Optional[str] = None
    profile: Optional[rp.LaunchProfile] = None
    config: Optional[rp.ProfileConfig] = None
    made_default_profile: bool = False
    made_default_runner: bool = False
    cancelled: bool = False
    reason: str = ""
    messages: List[str] = field(default_factory=list)


# ==================================================================================================
# Question primitives
# ==================================================================================================


def _read(io: WizardIO, prompt: str) -> str:
    """Ask one question, converting EOF/interrupt/quit-word into :class:`WizardCancelled`."""

    try:
        raw = io.ask(prompt)
    except EOFError:
        raise WizardCancelled("end of input") from None
    except KeyboardInterrupt:
        raise WizardCancelled("interrupted") from None
    if raw is None:
        raise WizardCancelled("end of input")
    answer = str(raw).strip()
    if answer.lower() in _CANCEL_WORDS:
        raise WizardCancelled("cancelled at the prompt")
    return answer


def ask_yes_no(io: WizardIO, question: str, default: bool = False) -> bool:
    """Ask a yes/no question with an EXPLICIT rendered default; empty input takes the default.

    Every consequential question in this module passes ``default=False``. EOF and interrupt are a
    cancel rather than a silent yes, so an unattended pipe can never accept a change.
    """

    suffix = "[Y/n]" if default else "[y/N]"
    for _attempt in range(MAX_ATTEMPTS):
        answer = _read(io, f"{question} {suffix} ").lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        io.line("  Please answer y or n (or 'q' to cancel).")
    raise WizardCancelled("too many invalid answers")


def ask_profile_name(io: WizardIO, cfg: rp.ProfileConfig, replace: bool = False) -> str:
    """Ask for a profile name, validating it against the SCHEMA's grammar (never a local copy).

    An existing name is refused unless ``replace``, matching `runner_profiles.add_profile`'s
    no-clobber rule: overwriting `gem` because the user forgot it existed is how a run ends up on
    an unintended, possibly far more expensive, model.
    """

    for _attempt in range(MAX_ATTEMPTS):
        answer = _read(io, "Profile name (e.g. gem): ")
        if not answer:
            io.line("  A name is required (or 'q' to cancel).")
            continue
        try:
            name = rp.validate_profile_name(answer)
        except rp.ProfileSchemaError as exc:
            io.line(f"  {exc}")
            continue
        if name in cfg.profiles and not replace:
            io.line(
                f"  Profile {name!r} already exists "
                f"({cfg.profiles[name].model}). Choose another name, or re-run with --replace."
            )
            continue
        return name
    raise WizardCancelled("too many invalid profile names")


# ==================================================================================================
# Model selection (E-02): discovery, filtering, paging, exact manual entry
# ==================================================================================================


def filter_models(models: Sequence[str], needle: str) -> Tuple[str, ...]:
    """Case-insensitive substring filter, preserving catalog order (deterministic, stdlib-only)."""

    if not needle:
        return tuple(models)
    lowered = needle.lower()
    return tuple(m for m in models if lowered in m.lower())


def _report_catalog(io: WizardIO, catalog: oc_models.ModelCatalog) -> None:
    """State plainly where the list came from, or why there is no list. Never green-wash."""

    if catalog.source == oc_models.CATALOG_SOURCE_CLI:
        io.line(f"Found {len(catalog.models)} model(s) via 'opencode models'.")
        return
    if catalog.source == oc_models.CATALOG_SOURCE_CONFIG:
        io.line(
            f"Model discovery via 'opencode models' was unavailable ({catalog.reason}"
            f"{': ' + catalog.detail if catalog.detail else ''})."
        )
        io.line(
            f"Using the {len(catalog.models)} model id(s) declared in your OpenCode config "
            "instead. Your private models may not be listed; you can always type an exact id."
        )
        return
    io.line(
        f"Model discovery is unavailable ({catalog.reason or 'no models found'}"
        f"{': ' + catalog.detail if catalog.detail else ''})."
    )
    io.line("Enter the exact provider/model identifier you want to use.")


def ask_model_manual(io: WizardIO) -> str:
    """Ask for an EXACT `provider/model`, validated by the schema's own grammar.

    ALWAYS REACHABLE, by design: a private or brand-new model may be absent from any catalog, and
    a wizard that could only offer discovered models would simply refuse to configure it.
    """

    for _attempt in range(MAX_ATTEMPTS):
        answer = _read(io, "Exact provider/model (e.g. google/gemini-3.7-flash): ")
        if not answer:
            io.line("  A model identifier is required (or 'q' to cancel).")
            continue
        try:
            return rp.validate_model(answer)
        except rp.ProfileSchemaError as exc:
            io.line(f"  {exc}")
    raise WizardCancelled("too many invalid model identifiers")


def select_model(io: WizardIO, catalog: oc_models.ModelCatalog) -> str:
    """Choose a model: numeric pick from a filtered/paged catalog, or exact manual entry.

    The commands are deliberately few and always visible: a NUMBER picks, `/<text>` filters,
    `m` types an exact id, `n`/`p` page, `q` cancels. Every path returns a schema-valid model, so
    the caller never has to re-validate.
    """

    if not catalog.available:
        return ask_model_manual(io)

    models: Tuple[str, ...] = tuple(catalog.models)
    needle = ""
    page = 0

    for _attempt in range(MAX_ATTEMPTS * 4):
        shown = filter_models(models, needle)
        if not shown:
            io.line(f"  No model matches {needle!r}.")
            needle, page = "", 0
            continue
        pages = max(1, (len(shown) + PAGE_SIZE - 1) // PAGE_SIZE)
        page = max(0, min(page, pages - 1))
        start = page * PAGE_SIZE
        window = shown[start : start + PAGE_SIZE]

        io.line("")
        header = f"Models ({len(shown)}"
        if needle:
            header += f" matching {needle!r}"
        header += f"), page {page + 1}/{pages}:"
        io.line(header)
        for offset, model in enumerate(window, start=start + 1):
            io.line(f"  [{offset}] {model}")
        io.line(
            "Enter a number to pick, '/<text>' to filter, 'm' to type an exact id, "
            + ("'n' next page, 'p' previous page, " if pages > 1 else "")
            + "'q' to cancel."
        )

        answer = _read(io, "Model: ")
        lowered = answer.lower()
        if not answer:
            io.line("  Pick a number, or 'm' to type an exact id.")
            continue
        if answer.startswith("/"):
            needle, page = answer[1:].strip(), 0
            continue
        if lowered == "m":
            return ask_model_manual(io)
        if lowered == "n":
            if page + 1 < pages:
                page += 1
            else:
                io.line("  Already on the last page.")
            continue
        if lowered == "p":
            if page > 0:
                page -= 1
            else:
                io.line("  Already on the first page.")
            continue
        if answer.isdigit():
            index = int(answer)
            if 1 <= index <= len(shown):
                # Validate even a DISCOVERED id: `parse_models_output` uses the same grammar, so
                # this cannot fail today, and it is what keeps that true if either side changes.
                return rp.validate_model(shown[index - 1])
            io.line(f"  {index} is out of range (1-{len(shown)}).")
            continue
        io.line("  Unrecognized input. Enter a number, '/<text>', 'm', or 'q'.")
    raise WizardCancelled("too many invalid model selections")


# ==================================================================================================
# Variant and agent selection (E-02)
# ==================================================================================================


def select_variant(io: WizardIO, model: str) -> Optional[str]:
    """Choose a variant, or ``None`` for the provider's own default (stored as NO variant).

    The menu says PROVIDER-SPECIFIC because it is: OpenCode's `--variant` help calls it
    "provider-specific reasoning effort", so a listed word may be rejected by a given provider and
    an unlisted one may work. Option [1] stores nothing rather than guessing a word, which is the
    only honest representation of "whatever this model does by default".
    """

    io.line("")
    io.line(
        f"Variant for {model} (provider-specific; a provider may accept none of these):"
    )
    io.line("  [1] Provider default (store no variant)")
    for index, word in enumerate(COMMON_VARIANTS, start=2):
        io.line(f"  [{index}] {word}")
    io.line(f"  [{len(COMMON_VARIANTS) + 2}] Enter an exact custom variant")

    custom_choice = str(len(COMMON_VARIANTS) + 2)
    for _attempt in range(MAX_ATTEMPTS):
        answer = _read(io, "Variant [1]: ")
        if not answer or answer == "1":
            return None
        if answer == custom_choice:
            for _inner in range(MAX_ATTEMPTS):
                custom = _read(io, "Exact variant value: ")
                if not custom:
                    io.line("  Enter a value, or 'q' to cancel.")
                    continue
                try:
                    return validate_optional_field("variant", custom, model)
                except rp.ProfileSchemaError as exc:
                    io.line(f"  {exc}")
            raise WizardCancelled("too many invalid variant values")
        if answer.isdigit():
            index = int(answer)
            if 2 <= index <= len(COMMON_VARIANTS) + 1:
                return COMMON_VARIANTS[index - 2]
        io.line(f"  Pick 1-{custom_choice}, or 'q' to cancel.")
    raise WizardCancelled("too many invalid variant selections")


def ask_agent(io: WizardIO, model: str) -> Optional[str]:
    """Optionally bind an OpenCode agent. Empty input means "no agent", which is the default."""

    for _attempt in range(MAX_ATTEMPTS):
        answer = _read(io, "OpenCode agent (optional; press Enter for none): ")
        if not answer:
            return None
        try:
            return validate_optional_field("agent", answer, model)
        except rp.ProfileSchemaError as exc:
            io.line(f"  {exc}")
    raise WizardCancelled("too many invalid agent values")


# ==================================================================================================
# Preview (E-02): the EXACT profile and the EXACT argv fields
# ==================================================================================================


def opencode_argv_fields(profile: rp.LaunchProfile) -> List[str]:
    """The `opencode run` flags this profile expands to, in the order the runner appends them.

    Mirrors `oc_runipd.run_opencode` (`agent_workflows/oc_runipd.py:5068-5073`: `--model`, then
    `--variant`, then `--agent`, each only when set), so the preview is the real expansion rather
    than a plausible-looking one. An absent field prints nothing, which is exactly what the runner
    does: "pass no argument and let the host use its own default".
    """

    fields: List[str] = ["--model", profile.model]
    if profile.variant:
        fields += ["--variant", profile.variant]
    if profile.agent:
        fields += ["--agent", profile.agent]
    return fields


def preview_lines(name: str, profile: rp.LaunchProfile) -> List[str]:
    """The exact preview block: stored fields, then the equivalent OpenCode argv fragment."""

    lines = [
        "",
        f"Profile {name!r} will be stored as:",
        f"  runner:  {profile.runner}",
        f"  model:   {profile.model}",
        f"  variant: {profile.variant if profile.variant else '(provider default)'}",
        f"  agent:   {profile.agent if profile.agent else '(none)'}",
        "",
        "Equivalent OpenCode launch:",
        f"  opencode run {' '.join(opencode_argv_fields(profile))}",
    ]
    return lines


def emit_preview(io: WizardIO, name: str, profile: rp.LaunchProfile) -> None:
    for line in preview_lines(name, profile):
        io.line(line)


# ==================================================================================================
# The interview (E-02) + the default questions and the single atomic write (E-04)
# ==================================================================================================


def run_wizard(
    io: WizardIO,
    name: Optional[str] = None,
    *,
    replace: bool = False,
    ask_defaults: bool = True,
) -> WizardResult:
    """Run one profile interview end to end. Writes AT MOST ONCE, and only on an explicit yes.

    Sequence: name -> model -> variant -> agent -> EXACT preview -> save? (default NO) ->
    default-profile? (default NO) -> default-runner? (default NO, and only when it would change
    something) -> ONE atomic write of everything accepted.

    ``ask_defaults=False`` suppresses both default questions (a caller that has already decided,
    such as a fully specified noninteractive `add`). Every failure and every decline returns
    ``saved=False`` WITHOUT calling ``io.save``, so the stored bytes are untouched.
    """

    messages: List[str] = []

    def note(text: str) -> None:
        messages.append(text)
        io.line(text)

    try:
        cfg = io.load()
    except (rp.ProfileSchemaError, rp.ProfileStoreError) as exc:
        # A malformed store is NOT treated as empty (that would silently launch the host default
        # model); it is reported and nothing is written. `runner_profiles.load` owns that rule.
        note(f"Cannot read your runner profiles: {exc}")
        return WizardResult(saved=False, reason="unreadable-config", messages=messages)

    try:
        profile_name = (
            rp.validate_profile_name(name)
            if name is not None
            else ask_profile_name(io, cfg, replace=replace)
        )
        if name is not None and profile_name in cfg.profiles and not replace:
            note(
                f"Profile {profile_name!r} already exists "
                f"({cfg.profiles[profile_name].model}); pass --replace to overwrite it. "
                "Nothing was changed."
            )
            return WizardResult(
                saved=False, reason="exists", config=cfg, messages=messages
            )

        catalog = io.discover()
        _report_catalog(io, catalog)
        model = select_model(io, catalog)
        variant = select_variant(io, model)
        agent = ask_agent(io, model)

        profile = rp.LaunchProfile(
            runner=RUNNER, model=model, variant=variant, agent=agent
        )
        emit_preview(io, profile_name, profile)

        io.line("")
        if not ask_yes_no(io, f"Save profile {profile_name!r}?", default=False):
            note("Not saved; nothing was changed.")
            return WizardResult(
                saved=False, reason="declined", config=cfg, messages=messages
            )

        # ---- E-04: two SEPARATE default questions, both default NO ---------------------------
        make_default_profile = False
        make_default_runner = False
        if ask_defaults:
            current_default = cfg.default_profile_for(RUNNER)
            if current_default == profile_name:
                # Already the default: asking would imply it might be turned off, which this
                # question cannot do. Say so instead of asking a question with one real answer.
                io.line(f"{profile_name!r} is already your default OpenCode profile.")
                make_default_profile = False
            else:
                if current_default:
                    io.line(
                        f"Your current default OpenCode profile is {current_default!r} "
                        f"({cfg.profiles[current_default].model})."
                    )
                make_default_profile = ask_yes_no(
                    io,
                    f"Make {profile_name!r} the default OpenCode profile?",
                    default=False,
                )
            if cfg.default_runner != RUNNER:
                # ONLY asked when it would change something. `default_runner` matters for
                # host-neutral dispatch (`ygzq71`), so an unrelated user should not be quizzed.
                make_default_runner = ask_yes_no(
                    io, "Make OpenCode the default IPD runner?", default=False
                )

        # ---- ONE atomic write of everything accepted ------------------------------------------
        new_cfg = rp.add_profile(cfg, profile_name, profile, replace=replace)
        if make_default_profile:
            new_cfg = rp.set_default_profile(new_cfg, profile_name)
        if make_default_runner:
            new_cfg = rp.set_default_runner(new_cfg, RUNNER)

        if io.save is None:
            note("No writer was provided; nothing was written.")
            return WizardResult(
                saved=False, reason="no-writer", config=cfg, messages=messages
            )
        try:
            io.save(new_cfg)
        except (rp.RunnerProfileError, OSError) as exc:
            # `runner_profiles.save` validates the WHOLE document first and replaces atomically,
            # so a failure here leaves the previous bytes byte-identical.
            note(f"Could not save: {exc}. Nothing was changed.")
            return WizardResult(
                saved=False, reason="write-failed", config=cfg, messages=messages
            )

        note(
            f"Saved profile {profile_name!r}. Use it with: aw oc run as {profile_name}"
        )
        if make_default_profile:
            note(f"{profile_name!r} is now your default OpenCode profile.")
        if make_default_runner:
            note("OpenCode is now your default IPD runner.")
        return WizardResult(
            saved=True,
            name=profile_name,
            profile=profile,
            config=new_cfg,
            made_default_profile=make_default_profile,
            made_default_runner=make_default_runner,
            messages=messages,
        )
    except WizardCancelled as exc:
        note(f"Cancelled ({exc}); nothing was changed.")
        return WizardResult(
            saved=False,
            cancelled=True,
            reason="cancelled",
            config=cfg,
            messages=messages,
        )
    except rp.RunnerProfileError as exc:
        note(f"{exc}. Nothing was changed.")
        return WizardResult(
            saved=False, reason="invalid", config=cfg, messages=messages
        )


def run_session(
    io: WizardIO, *, replace: bool = False, max_profiles: int = 10
) -> List[WizardResult]:
    """Run the interview repeatedly, asking "Configure another profile?" between rounds.

    THE LOOP LIVES HERE AND NOWHERE ELSE (E-04). An automatic loop inside a noninteractive
    command would be a surprise at best and an unattended write loop at worst, so only an explicit
    interactive session caller (`aw oc profile add` on a TTY, or `aw setup` via Order 05) opts in.
    ``max_profiles`` bounds the session so a pipe cannot spin.
    """

    results: List[WizardResult] = []
    for _round in range(max(1, max_profiles)):
        result = run_wizard(io, replace=replace)
        results.append(result)
        if result.cancelled:
            break
        try:
            if not ask_yes_no(io, "Configure another profile?", default=False):
                break
        except WizardCancelled:
            break
    return results


# ==================================================================================================
# Rendering helpers shared with the CLI verbs (E-03)
# ==================================================================================================


def profile_dict(name: str, profile: rp.LaunchProfile) -> Mapping[str, Any]:
    """One profile as a JSON-ready mapping, including its exact OpenCode argv fields.

    Used by `aw oc profile list/show` for `--json`/`--agent` output. It carries only the schema's
    own fields, so there is no channel through which a credential could appear: the schema has no
    field for one (`runner_profiles.FORBIDDEN_PROFILE_KEYS`).
    """

    return {
        "name": name,
        "runner": profile.runner,
        "model": profile.model,
        "variant": profile.variant,
        "agent": profile.agent,
        "validate": profile.validate,
        "opencode_args": opencode_argv_fields(profile),
    }
