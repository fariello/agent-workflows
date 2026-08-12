"""Test package initialization.

Test isolation guard: redirect AW_HOME (and XDG_CONFIG_HOME) to a dedicated
throwaway directory for the whole test process UNLESS the caller already set
them. Without this, any test that resolves an AW project context without
injecting an explicit ``aw_home`` (e.g. constructing an ``ActionManager`` on a
temp repo) falls through to the platform default ``~/.aw`` and materializes a
per-project slot in the developer's REAL home that ``tearDown`` never removes,
polluting ``~/.aw/projects/`` with orphan ``myrepo-*``/``tmp*`` directories.

Setting AW_HOME in the environment is honored by the resolver's precedence
(explicit ``aw_home=`` arg > ``AW_HOME`` env > user config > platform default),
so tests that pass an explicit home or patch the environment still win; this
only backstops the ones that would otherwise escape to the real home.
"""

import atexit
import os
import shutil
import tempfile

if not os.environ.get("AW_HOME"):
    _AW_TEST_HOME = tempfile.mkdtemp(prefix="aw-test-home-")
    os.environ["AW_HOME"] = _AW_TEST_HOME
    # Keep the global user-config lookup inside the sandbox too, so no test can
    # read or write the developer's real ~/.config/agent-workflows.
    os.environ.setdefault("XDG_CONFIG_HOME", os.path.join(_AW_TEST_HOME, "xdg-config"))
    atexit.register(shutil.rmtree, _AW_TEST_HOME, True)

# Network/credential guard: a test may create a repo with a real remote (e.g. an
# https://github.com/... origin) and then reach code that probes it (git ls-remote /
# fetch). Without this, git blocks on an interactive credential prompt (the editor's
# "log in to github.com" popup) and the test hangs for the connection timeout. Force
# git to fail fast and never prompt. Tests that assert reachability behavior patch
# `_remote_reachable` explicitly; this only backstops the ones that would otherwise
# escape to the network. Set unconditionally so it applies under xdist workers too.
os.environ.setdefault("GIT_TERMINAL_PROMPT", "0")
os.environ.setdefault("GIT_ASKPASS", "/bin/echo")
os.environ.setdefault("SSH_ASKPASS", "/bin/echo")
os.environ.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes -o ConnectTimeout=5")
os.environ.setdefault("GIT_CONFIG_NOSYSTEM", "1")
