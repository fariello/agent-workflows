# Walkthrough: run a host probe

Goal: from a clean state, run a host capability probe in an isolated environment that never
touches your real home directory.

## Why an isolated fixture

A probe runs a host command against a scaffolded fixture repo with a fixture HOME. The isolation
guard refuses a base directory that is (or contains) your real home, so a probe can never write
into your home.

## Reproduce a probe scaffold and command in a fixture

```
python3 -c "
import tempfile
from agent_workflows import host_capability_registry as r
base = tempfile.mkdtemp(prefix='aw-probe-')
fx = r.scaffold_probe_fixture(base, host='opencode', version='1.0.0', tier='T2')
cmds = r.render_probe_commands('opencode', '1.0.0', 'T2', base, fx.nonce)
print('fixture HOME:', fx.fixture_home)
print('probe file:', fx.probe_filename)
print(cmds.script_text)
"
```

The printed script exports an isolated HOME and the XDG directories, runs the host command,
runs the host diagnostics, and verifies the expected nonce side-effect file. Nothing runs
against your real home.

## Confirm the real HOME is refused

```
python3 -c "from agent_workflows import security_hardening as s; \
from pathlib import Path; \
r = s.check_real_home_excluded(Path.home()); \
print('real HOME accepted as probe base:', r.ok)"
```

The output is `False`: the real home is refused as a probe base.

## What a probe proves

A capability becomes `supported` only after a proven positive probe (resolved, followed, side
effect verified) plus the required fail-closed negative probes. Until then the capability is
`unverified` (see [../host-adapters.md](../host-adapters.md)).
