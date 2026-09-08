# Runner profiles: short aliases for a model choice

A RUNNER PROFILE lets you type `gem` instead of repeating
`--model google/gemini-3.7-flash --variant high` on every run. This page is the complete user
contract: every way to create a profile, every way to run with one, the exact override
precedence, where the file lives, what it will never contain, and what happens when something
is wrong.

This is about WHICH MODEL A RUN LAUNCHES. It is unrelated to
[model profiles](model-profiles.md), which are evidence-backed transport and reasoning-tier
defaults for a workflow. Different concept, similar word.

## The short version

```bash
aw oc profile add                 # interactive: pick a model, name it, confirm
aw run as gem 3cm15q              # run an IPD with that profile
aw oc profile list                # see what you have
```

Nothing is ever written without your confirmation, and no profile is created or made default
for you. If you have no profiles, every command behaves exactly as it did before this feature
existed.

## Creating a profile

### Interactively

```bash
aw oc profile add                 # asks for the name too
aw oc profile add gem             # name given, asks for the rest
```

The interview asks for a name, a model, a variant, and an optional OpenCode agent, shows you
the exact profile and the equivalent `opencode run` command line, and then asks whether to save
it. Save defaults to NO.

The model list comes from your own installation, read only:

- If `opencode models` answers, you get that list, with case-insensitive substring filtering
  (`/flash`) and paging for long catalogs.
- If it cannot answer, the exact reason is printed and you are asked to type an exact
  `provider/model` identifier instead. Discovery failure never blocks you, and it is never
  reported as an empty catalog.
- You can always type an exact identifier with `m`, including a private model that no catalog
  lists.

Reading the catalog never refreshes it, never edits your OpenCode configuration, and never
touches your providers or credentials. Refreshing OpenCode's own model list remains the job of
`aw oc update-models`.

`q`, `quit`, `cancel`, `abort`, an empty required answer, EOF, and Ctrl-C all abandon the
interview, and an abandoned interview writes nothing at all.

### Noninteractively (scripts)

```bash
aw oc profile add sol --model openai/gpt-5.6-sol --variant medium --yes
```

The noninteractive form is deliberately all-or-nothing: it requires a NAME, a `--model`, and
`--yes`. A half-specified profile refuses (exit 2) rather than having a model chosen for it, and
without a TTY an incomplete invocation refuses instead of blocking on a prompt no one can
answer.

Optional flags: `--variant`, `--oc-agent` (spelled that way because `--agent` selects
machine-readable output), `--replace` to overwrite an existing name, and `--set-default`.

### During `aw setup`

Interactive `aw setup` offers this once, after your repositories are installed, with a question
that DEFAULTS TO NO. It is offered once per `aw setup` invocation, not once per repository,
because profiles are per-user rather than per-project.

These runs create no profile and change no default, by design:

- `aw setup --yes`. `--yes` preauthorizes install mutations; it does not consent to a model
  choice, which is a cost and behavior decision that stays yours.
- Any noninteractive run (piped, redirected, or in CI).
- Answering `n`, answering nothing, or hitting EOF or Ctrl-C at the question.

`aw install` never offers it: installing into one more repository is not a moment to reconsider
your model. Use `aw oc profile add` whenever you want it.

## Running with a profile

Four canonical forms, all equivalent in how they resolve a launch:

```bash
aw run as gem 3cm15q          # host-neutral, named profile: the PROFILE picks the host
aw run ipd 3cm15q             # host-neutral, unqualified: default_runner picks the host
aw oc run as gem 3cm15q       # OpenCode explicitly, named profile
aw oc run 3cm15q              # OpenCode explicitly, its default profile if you set one
```

Direct flags keep working, with or without a profile:

```bash
aw oc run 3cm15q --model openai/gpt-5.6-sol --variant medium
aw run as gem 3cm15q --variant max     # profile fields, with the variant overridden
```

`as` and `ipd` are FIXED grammar. The profile name is read only from the position immediately
after the literal `as`, so the command position is decided before any configuration file is
read. Two consequences worth knowing:

- A profile may be named `status`, `report`, `run`, `show`, or `evidence` without shadowing any
  command.
- No profile ever becomes a command. For a profile named `gem`, none of the spellings `gem`,
  `gemrun`, `rungem`, `run gem`, `run-gem`, or `run:gem` exist as an `aw` command, and none will
  be added. The only way a profile name is read is after `as`.

`as` and `default` are the only names a profile cannot take, because `aw run as default` would
be ambiguous in the grammar itself.

Everything after the profile or selector belongs to the host runner and is forwarded verbatim,
so `aw run as gem X --flag` behaves identically to `aw oc run as gem X --flag`. For the real
flag set, see `aw oc run --help`.

## Precedence: exactly what wins

Per FIELD (`model`, `variant`, `agent`), highest first:

1. An explicit `--model` / `--variant` / `--agent` on the command line.
2. The profile you named with `as <profile>`.
3. The per-runner default profile (`aw oc profile default gem`).
4. The host's own default (no argument is passed at all).

Resolution is PER FIELD, which is the part people get wrong: `aw run as gem --variant max` uses
`gem`'s model and agent and only replaces its variant. An explicit flag never discards the rest
of the profile, and a stored value never overrides an explicit flag.

For `validate` (whether an independent verifier turn runs) the chain is a TRI-STATE, and an
absent level falls through rather than reading as false:

1. An explicit `--validate` / `--no-validate`.
2. The profile's own `validate`.
3. The store's `defaults.validate`.
4. The shipped default, which is off.

This exists because verification is worth different amounts on different models. A profile whose
model rarely benefits can record `validate: false` while a cheaper one records `true`, instead of
your having to remember a flag on every invocation.

## Verifying with a different model

An independent verifier turn is worth most when it is genuinely independent, and a second opinion
from the same model is the one least likely to catch what the first missed. A profile can therefore
name the profile that VERIFIES its work:

```json
{
  "schema_version": 2,
  "profiles": {
    "cheap": {"runner": "oc", "model": "vendor/fast-1", "verify_with": "strong"},
    "strong": {"runner": "oc", "model": "vendor/deep-9", "variant": "high"}
  }
}
```

Now `aw oc run as cheap <selector>` executes with `vendor/fast-1` and, when verification runs,
verifies with `vendor/deep-9`. You can override it for one run, or set a fallback for every
profile that does not name its own:

```bash
aw oc run as cheap <selector> --verify-with strong   # for this run only
```

Precedence, highest first, on the same tri-state rule as `validate`:

1. An explicit `--verify-with <profile>`.
2. The profile's own `verify_with`.
3. The store's `defaults.verify_with`.
4. Nothing, which means the verifier uses the EXECUTOR's own launch. That is what every run did
   before this field existed, so a store without it behaves exactly as it always has.

Four things are worth knowing:

- IT IS A PROFILE NAME, not a model. A reference reuses a whole profile that has already been
  validated, including its variant and agent, and there is deliberately no way to write a bare
  model here.
- IT SAYS WHICH, NOT WHETHER. `validate` decides whether a verifier turn runs at all;
  `verify_with` decides which profile runs it when one does. They are independent, so you can set
  a verifier profile on a run with verification off, and the setting simply waits.
- RESOLUTION IS ONE HOP. If the profile you verify with names a `verify_with` of its own, that
  value is ignored while it is acting as the verifier. There is no chain, so there is no loop.
- IT IS OPENCODE ONLY. The Antigravity runner does not read runner profiles at all, so it neither
  honors `verify_with` nor any other profile field. Verifying under a DIFFERENT RUNNER than the one
  that executed is also not available: this routes the model, not the host.

A reference that names a profile which does not exist is refused when the store is read, before a
run has any durable side effect. That refusal is deliberate: falling back to the executor's model
would leave you believing an independent model checked the work when the same model did.

This field arrived with `schema_version` 2. A store still declaring version 1 is read exactly as
before and is never rewritten unless you save a change, but a store this version of `aw` WRITES is
declared as version 2 and an older `aw` will refuse it and tell you to upgrade rather than treat it
as empty.

### Which host runs it

`aw run as <profile>` asks the PROFILE, which names exactly one runner. `aw run ipd` has no
profile to ask, so it requires `default_runner` to be configured and REFUSES (exit 2) when it is
not. It does not assume OpenCode: guessing would launch a model you did not choose, and with a
paid model you would find out from the bill.

## Defaults are separate, explicit decisions

Saving a profile changes nothing about what an unqualified run does. The two defaults are
independent questions, both defaulting to NO, and declining either preserves its current value:

```bash
aw oc profile default gem        # gem is used when you name no profile
aw oc profile default --clear    # back to the host's own default
```

- The DEFAULT PROFILE (per runner) applies to `aw oc run <selector>` when you name no profile
  and pass no explicit `--model`.
- The DEFAULT RUNNER (`default_runner`) is what makes the unqualified host-neutral form
  `aw run ipd <selector>` work at all.

## Managing what you have

```bash
aw oc profile list               # every profile, its model/variant/agent, and the default
aw oc profile show gem           # one profile and the exact OpenCode launch it expands to
aw oc profile remove gem         # removing the current default requires an explicit decision
aw oc profile add gem --replace ...   # there is no silent overwrite
```

`list` and `show` accept `--json` and `--agent` for machine-readable output, like every other
`aw` verb.

## Storage and privacy

The file is `runner-profiles.json` in your user configuration directory
(`${XDG_CONFIG_HOME:-~/.config}/agent-workflows/`).

- It is USER-LOCAL and per-machine. It is never written into your repository and is never
  committed, because a model identifier can be institution-specific and would disclose local
  topology in a public project.
- It is separate from `config.json` on purpose, so this feature is not coupled to that file's
  pending restructuring.
- Writes are ATOMIC: the whole new document is validated first, then replaced in one operation.
  An interrupted or invalid write leaves your previous file byte for byte unchanged.

A profile holds only structured launch fields: `runner`, `model`, `variant`, `agent`, `validate`,
and `verify_with`. It is NOT a command, an argv fragment, a shell string, an environment mapping, an
executable path, a prompt, a permission set, or a place for a token or an API key. Every one of
those keys is refused by name, and any unrecognized key is refused too. A raw arguments field
would turn `aw run as gem` into a quoting and injection surface; a credential field would turn a
convenience file into a secret store. There is no field through which a secret could be stored,
so there is none to leak.

Repository-shared profiles do not exist in this version, for the disclosure reason above.
OpenCode is the only runner with an adapter; a second host needs its own adapter rather than a
widened schema.

## Durability: a running run does not change under you

When a run starts, the RESOLVED launch identity is frozen into that run's `state.json` before
anything is executed: the model, the variant, the agent, which profile was requested, which was
actually applied, the store's path, and a digest of the store's contents, plus per-field
provenance recording whether each value came from an explicit flag, the named profile, the
default profile, or the host default.

Every later turn of that run, including recovery, review, and the independent verifier turn,
uses the frozen values. So editing a profile, repointing it at another model, or deleting it
outright does not change a run already in flight, and `resume` never re-resolves. That
provenance record is also why an operator reading `state.json` months later can tell an explicit
flag from a profile that has since been edited.

When a verifier profile applies, its resolved launch is frozen BESIDE the executor's, with its own
provenance, and the verifier turn uses that one. Because it is frozen too, `--verify-with` is
refused on `resume`: honoring a profile name there would mean re-reading the store, which is the one
thing a resume must never do. Start a new run to verify with a different profile.

You can see the identity before committing to anything:

```bash
aw oc run as gem 3cm15q --prepare-only    # prints the resolved Launch line, runs nothing
```

## When something is wrong

Every one of these fails BEFORE the run has any durable side effect: no run id, no run
directory, no partial state.

| Situation | What happens |
|---|---|
| Unknown profile name | Exit 2, names the profile and how to list the real ones. Nothing is created. |
| Malformed or unsupported `runner-profiles.json` | Exit 2 with the parse error. It is NEVER treated as empty, because that would silently launch the host default model instead of the one you configured. |
| A profile belonging to another runner | Refused rather than launched by the wrong host. |
| `aw run ipd` with no `default_runner` | Exit 2, naming the command that sets one. |
| A runner that is valid in the schema but has no adapter in this build | Refused, and reported as unimplemented rather than as a typo. |
| A dangling default profile (points at a name that no longer exists) | Refused at load, so a broken store surfaces at once. |
| A duplicate name without `--replace` | Refused, and the existing profile survives untouched. |
| A `verify_with` naming a profile that does not exist | Refused, because falling back to the executor's model would let you believe an independent model verified the work. |
| `--verify-with` passed to `resume` | Exit 2. The verifier launch is frozen at creation; omit the flag to use it, or start a new run. |
| A store written by a newer `aw` (a higher `schema_version`) | Refused with the version and the advice to upgrade, never treated as empty. |

If the store is malformed, `aw setup` reports it and does NOT offer the interview, so a file you
can still repair by hand is never written over.

## Quick reference

| You want | Run |
| --- | --- |
| Create a profile interactively | `aw oc profile add` |
| Create one from a script | `aw oc profile add gem --model provider/model --yes` |
| Run an IPD with a profile | `aw run as gem <selector>` |
| Run with your default runner and profile | `aw run ipd <selector>` |
| Run naming OpenCode explicitly | `aw oc run as gem <selector>` |
| Override one field for one run | `aw run as gem <selector> --variant max` |
| Verify with a different model | Add `"verify_with": "strong"` to the profile, or `--verify-with strong` |
| See the resolved launch without running | `aw oc run as gem <selector> --prepare-only` |
| See what you have | `aw oc profile list` |
| Set or clear the default profile | `aw oc profile default gem` / `--clear` |
| Remove a profile | `aw oc profile remove gem` |
