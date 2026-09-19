- Id: nyz8dt
- Status: graduated
- Blocks-Release: next
- Set: nyz8dt
- Priority: high
- Work-Kind: bug
- Summary: Unify the three divergent should_color implementations and stop FORCE_COLOR=0 forcing color on

## Workflow history
- 2026-09-19 graduated (aw set): Converted into lifeglyph child z8ddk0 on the maintainer's instruction 2026-09-19, after the three reasons for keeping it standalone were re-examined and two were found false. The gate travels with the plan, which carries Blocks-Release: next and Work-Kind: bug.
- 2026-09-19 created (aw backlog): Filed from the lifeglyph pow5sj OQ-02 investigation; carries the maintainer's 2026-09-19 ruling on NO_COLOR/FORCE_COLOR semantics.

## The defect

Three independent `should_color` implementations disagree with each other, and one of them inverts the
meaning of a value a user is likely to set deliberately. All four behaviors below were measured by
EXECUTION on 2026-09-19, not by reading the code.

| Implementation | Checks `TERM`? | `NO_COLOR` empty | `FORCE_COLOR` precedence |
|---|---|---|---|
| `term.py:90` (CLI commands) | yes (`dumb`/empty/unset -> off) | disables (presence test) | `NO_COLOR` first, `FORCE_COLOR` escapes it |
| `runner_shared.py:276` (both runners) | **no, ignores `TERM` entirely** | ignored (truthiness test) | `FORCE_COLOR` first |
| `pwatch.py:951` | no | ignored (`is None` test) | **ignores `FORCE_COLOR` completely** |

Four user-visible consequences:

1. **`FORCE_COLOR=0` FORCES COLOR ON, even to a pipe.** The string `"0"` is truthy in Python, so
   `os.environ.get("FORCE_COLOR")` passes. A user writing `FORCE_COLOR=0` means "do not force" and gets
   the exact opposite. This is the worst of the four because the value is common in CI configuration.
2. **`TERM=dumb aw oc run` emits color** while `TERM=dumb aw attention` does not, because
   `runner_shared.should_color` never reads `TERM`.
3. **`FORCE_COLOR=1 aw pwatch | cat` emits no color** while every other command does.
4. **`FORCE_COLOR=''` half-counts in `term.py`**: it is checked by PRESENCE on line 100 (so it cancels
   `NO_COLOR`) and by TRUTHINESS on line 103 (so it does not force). One variable, two tests, four lines
   apart.

## The ruling (maintainer, 2026-09-19)

**`NO_COLOR` is PRESENCE-ONLY. Any setting disables color, including the empty string. No value is
interpreted.** `term.py`'s current handling is therefore CORRECT and becomes the single definition;
`runner_shared.py` and `pwatch.py` are the ones that change.

**WHY: BECAUSE THAT IS WHAT THE TOOLS OUR USERS ALREADY USE DO, AND CONSISTENCY WITH THEM IS THE POINT.**
This is the whole rationale and it is deliberately not an appeal to the no-color.org text, which says
less than is usually claimed for it. Measured on a TTY, 2026-09-19, on this machine:

| `NO_COLOR` | `rg` 14.x | `bat` 0.24.0 | `fd` 9.0.0 |
|---|---|---|---|
| unset | COLOR | COLOR | COLOR |
| `""` (empty) | plain | plain | **COLOR** |
| `"0"` | plain | plain | plain |
| `"false"` / `"no"` / `"off"` | plain | plain | plain |
| `"1"` | plain | plain | plain |

Two things follow, and the second is why the ruling is a judgement rather than a deduction:

- **For any NON-EMPTY value the three tools are UNANIMOUS: it disables.** `0`, `false`, `no`, `off` all
  disable in all three. So interpreting falsey words, which was the intuitive option and was considered
  and rejected, would make `aw` the ONLY tool in a user's terminal that keeps color when `NO_COLOR=0`.
  Being the odd one out on a cross-tool convention is a worse outcome than the surprising reading of
  `0`, because the user cannot see which tool is the deviant one.
- **For the EMPTY string the ecosystem is genuinely SPLIT, two to one.** `rg` and `bat` disable, `fd`
  ignores it. There is no consensus to follow, so the majority was chosen. This divergence is recorded
  rather than hidden: a reasonable person could implement `fd`'s behavior instead, and `aw`'s own two
  implementations already split exactly this way, so ONE of them had to change regardless of the ruling.

MEASUREMENT GOTCHA, recorded so the next person reproducing this does not get a false result: on Debian
`/usr/sbin/bat` is an unrelated Qt application and `/usr/bin/fd` is not `fd` either. The real binaries
are `batcat` and `fdfind`. A first run against `/usr/sbin/bat` returned "plain" for every input, which
looks like a clean presence-only result and is actually a crashing binary.

**`FORCE_COLOR` INTERPRETS ITS VALUE: `0`/`false`/`no`/`off` mean NOT FORCING.** None of the three tools
above implements `FORCE_COLOR` at all, so they offer no guidance; the only precedent is the Node
ecosystem it was borrowed from, where `FORCE_COLOR=0` DISABLES and `1`/`2`/`3` select depth. Today's
behavior is backwards under that convention with nothing defending it.

**THE TRI-STATE PRINCIPLE, which is what makes the asymmetry coherent** (maintainer, 2026-09-19): a
prohibition being OFF does not mean the opposite is ON. Each variable has three states, not two:

| Variable | suppress | ignore (fall through to TTY detection) | force |
|---|---|---|---|
| `NO_COLOR` | any setting, including `""` | unset | n/a |
| `FORCE_COLOR` | n/a | unset, or `0`/`false`/`no`/`off` | any other non-empty value |

So `FORCE_COLOR=0` must fall through to ordinary TTY detection (color on a terminal, plain to a pipe).
It must NOT mean "suppress", which would make it a second `NO_COLOR`.

## Scope

- ONE shared `should_color` with ONE definition, consuming the rules above. `term.py` is the natural
  home since it is already the ANSI/capability boundary.
- `runner_shared.py:276` and `pwatch.py:951` consume it rather than reimplementing it. Note this makes
  the runners start honoring `TERM=dumb`, which is a behavior CHANGE and the correct one.
- Pin every cell of both tables above with a test. NONE of the empty-string or `0` cases is pinned
  today, which is why all four defects survived: the behavior is accidental, not contractual.
- `tests/test_term.py:48` `test_force_color_overrides_no_color` stays VALID and must keep passing:
  `FORCE_COLOR=1` beating `NO_COLOR=1` is unchanged by this ruling. Only the falsey values change.

## Relationship to other work

- **`yaxr4i`** (plan, `approved`, unexecuted) owns the FLAG surface and its E-02 adds the `--color`
  twin. The maintainer ruled 2026-09-19 for TWO flags, `--color` / `--no-color`, MUTUALLY EXCLUSIVE in
  one argparse group, with `--color` forcing color on (matching what `FORCE_COLOR` does today,
  including over a pipe and `TERM=dumb`). That plan should consume this item's env-var rules so flags
  and variables land on one precedence chain. Sequencing this after `yaxr4i` avoids writing the
  resolver twice.
- **`z8ddk0`** (plan, lifeglyph 09) NOW OWNS THIS WORK. This item is `graduated`, not `done`: the design
  is handed off and the code is not yet written.
- **`pow5sj`** (plan, lifeglyph 03) builds the color DEPTH resolver on the seam `z8ddk0` unifies, and
  declares `executed:z8ddk0`.

CORRECTION, 2026-09-19, recorded because this item's own first revision argued the opposite and a later
reader would otherwise inherit three false claims. This was filed standalone on the reasoning that
`pow5sj`'s scope excluded behavior changes, that the defect lived in three files the lifeglyph Set did
not own, and that `yaxr4i` would rewrite the surface anyway. The maintainer asked for those reasons to
be re-examined and TWO WERE FALSE: `pow5sj`, `bn026f` and `qdd5jq` all declare `agent_workflows/term.py`
in `- Scope-Paths:` and `qdd5jq` also declares `runner_shared.py`, so only `pwatch.py` was genuinely
outside the Set; and `yaxr4i` does NOT rewrite the engine, it asserts at its line 97 that "The color
ENGINE is already correct and complete... it does not need new color logic", a premise these very
measurements falsify, so it would never have fixed the divergence. The third claim was unsupported:
`pow5sj`'s Scope excludes the stage table, the rendering helpers, consumer conversion and per-stage
overrides, and says nothing about behavior changes. What actually pointed the other way is that
`pow5sj`'s V-01 already demanded proof of exactly ONE depth-resolver definition, which a three-engine
seam cannot honestly provide. The maintainer ruled to convert this item into a child.
- **Spec `uonrjg`** Section 9.3a.2 calls its top rung "unchanged, and unconditional", which is FALSE as
  written (`FORCE_COLOR` does currently defeat `NO_COLOR`). Section 9.3 four lines earlier requires
  preserving "current" behavior, and there are two current behaviors. That wording should be amended
  when this lands, via the declared-spec-edit path.
