# agent-workflows install manifest

This directory holds `managed-sections.json`, the ownership manifest the `agent-workflows`
installer maintains for this repository. You normally never edit it by hand; this note
explains what it is and why it exists so it is not mistaken for stray tooling output.

## What it records

For every file the installer wrote into this repo (the command shims under
`.opencode/commands/` and `.claude/commands/`, and other managed files) the manifest keeps
one record:

- the file path,
- a logical id, a kind, and the host tool (for example `opencode` or `claude`),
- the sha256 of the exact content the installer LAST WROTE for that file.

It also carries the framework version that produced it, and reserves space for two future
features (per-directive managed sections, and a per-file "declined" tombstone).

## Why it exists

Before this manifest, the installer decided whether YOU had edited a managed file by
comparing what was on disk to the NEW content it was about to generate. That meant any
change to the installer's OWN output format (for example adding a per-command
`argument-hint` line) made every previously installed file look hand-edited, and the
installer would warn "has manual modifications" about files it had written itself.

With the manifest, the installer compares your on-disk file to the hash of what IT last
wrote:

- if they match, the file is unchanged by you, so the installer updates it silently even
  when the new template differs (no false warning);
- if they differ, you really did edit it, so the installer reports it and does NOT
  overwrite it without your say-so (the usual overwrite prompt still applies).

The recorded hash is always the hash of what the installer just wrote, so the next upgrade
always compares against a fresh, correct baseline.

## Managed sections

The manifest also tracks the individually marked SECTIONS of the managed block in your
shared instruction files (AGENTS.md, and CLAUDE.md/GEMINI.md when present). That block uses
an outer `<!-- aw:block -->` .. `<!-- /aw:block -->` wrapper containing `<!-- aw:<slug> -->`
sections. For each section the manifest records its slug and the hash of what the installer
last wrote, keyed as `<file>#aw:<slug>`.

When you run install or update, each section is handled by four clear rules:
- if the on-disk section matches the new template, it is adopted silently and its hash is re-recorded;
- if the on-disk section matches what the installer last wrote, it is updated to the new template;
- if the on-disk section matches neither, your edited version is kept and the installer warns you by name;
- if no record exists and the on-disk section differs from the template, your version is kept and warned.

To replace a preserved section with the regenerated version, delete that section (from its `<!-- aw:<slug> -->` marker to the next marker) and re-run install. This also lets you decline a specific directive while keeping the rest. Any hand-authored block you keep in the same file that is NOT an `aw:block` (for example a differently named `NAME:BEGIN/END` block) is never touched.

## Should I commit it?

Yes. The manifest is tracked by default so the whole team shares one record of what the
installer owns. It is self-contained and does not depend on git history; deleting it is
safe (the next `aw install` rebuilds it by adopting the files already present), but keeping
it committed gives the cleanest upgrade behavior.
