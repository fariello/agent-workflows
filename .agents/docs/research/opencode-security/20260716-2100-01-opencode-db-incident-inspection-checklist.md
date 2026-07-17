# Incident inspection: what to look for in a user's opencode.db after an exposed server

Status: operational checklist (queries verified read-only against a live opencode.db on this host)
Date: 2026-07-16
Author: agent-workflows session (opencode)
Related: advisory `20260716-0850-01`; the `--hostname 0.0.0.0` exposure during the T5 test.
Run as: the AFFECTED user (for example `victim-user`) or root. The DB lives under that user's home and is mode 0600, so another non-root user cannot read it.

## What this can and cannot tell you (read first)

opencode's server writes NO HTTP access log (verified: `disableLogger`/`disableListenLog`; see advisory). So the DB is a PARTIAL forensic source:

- IT RECORDS (persisted as session data): sessions created, messages/prompts submitted, and TOOL/SHELL commands run through a session. So an attacker who created a session or ran `/shell` or drove the agent LEAVES TRACES here.
- IT DOES NOT RECORD: read-only API calls. `GET /file/content`, `GET /session`, `GET /config` create no session state and leave NO trace anywhere in opencode. A pure file-exfiltration attack is invisible to this DB.

Therefore: absence of suspicious rows here does NOT prove nothing happened (files could have been read silently). Presence of sessions/commands you did not create IS evidence of interactive abuse. For connection-level evidence you need the network layer (firewall/conntrack/journald/IDS/netflow) for the exposure window.

## Prerequisites

- The `sqlite3` CLI (`sudo apt install sqlite3`). Version 3.45+ has native `json_extract` and `datetime(...,'unixepoch','localtime')`, which is all we need. Installing the CLI does NOT touch the SQLite library bundled in opencode's runtime, so it is safe while opencode is running.
- The DB path: `~/.local/share/opencode/opencode.db` (data dir, not state dir).
- Open READ-ONLY and IMMUTABLE so you never disturb the live WAL of a running opencode: open the DB via the URI `"file:$DB?mode=ro&immutable=1"`. This is a safety flag, not optional decoration; do not open the live DB read-write.

## Set the exposure window

Set the start/end of the window the server was exposed (local time). For the T5 incident, this is roughly when `opencode serve --hostname 0.0.0.0` was started until it was killed. Everything created in this window that you did not personally do is suspect.

## The inspection queries (sqlite3 CLI)

Verified read-only against a live opencode.db (sqlite3 3.45). Set the DB path and window once, then run each query. `datetime(time_created/1000,'unixepoch','localtime')` renders the timestamps and `json_extract` pulls fields out of the JSON `data` columns, so no scripting is needed. Targeted queries only (the DB can be multiple GB; do not dump it).

    DB="$HOME/.local/share/opencode/opencode.db"
    URI="file:$DB?mode=ro&immutable=1"          # read-only + immutable: safe on a running opencode
    START="2026-07-16 20:00:00"                 # edit: start of exposure window (local time)
    END="2026-07-16 21:00:00"                   # edit: end of exposure window

Sessions CREATED in the window (attacker-created sessions are the strongest interactive-abuse signal):

    sqlite3 -box "$URI" "
      SELECT datetime(time_created/1000,'unixepoch','localtime') AS created, id, directory, substr(title,1,60) AS title
      FROM session
      WHERE time_created BETWEEN strftime('%s','$START')*1000 AND strftime('%s','$END')*1000
      ORDER BY time_created;"

User prompts submitted in the window (agent-driving via /session/{id}/message):

    sqlite3 -box "$URI" "
      SELECT datetime(time_created/1000,'unixepoch','localtime') AS t, session_id, substr(prompt,1,100) AS prompt
      FROM session_input
      WHERE time_created BETWEEN strftime('%s','$START')*1000 AND strftime('%s','$END')*1000
      ORDER BY time_created;"

Shell/tool COMMANDS run in the window (direct code-execution evidence):

    sqlite3 -box "$URI" "
      SELECT datetime(time_created/1000,'unixepoch','localtime') AS t,
             session_id,
             json_extract(data,'\$.tool') AS tool,
             json_extract(data,'\$.state.status') AS status,
             substr(json_extract(data,'\$.state.input.command'),1,100) AS command
      FROM part
      WHERE json_extract(data,'\$.type')='tool'
        AND time_created BETWEEN strftime('%s','$START')*1000 AND strftime('%s','$END')*1000
      ORDER BY time_created;"

Message role summary in the window (who spoke in each session):

    sqlite3 -box "$URI" "
      SELECT datetime(time_created/1000,'unixepoch','localtime') AS t,
             session_id, json_extract(data,'\$.role') AS role
      FROM message
      WHERE time_created BETWEEN strftime('%s','$START')*1000 AND strftime('%s','$END')*1000
      ORDER BY time_created LIMIT 200;"

Note: `strftime('%s',...)` interprets the window strings as UTC. If your window is in local time and that matters at the boundaries, either widen the window a bit or express START/END in UTC. `-box` just pretty-prints; use `-csv` if you want to save results.

## How to read the output

- Sessions created in the window that you do NOT recognize (especially ones you did not open in a TUI) are the strongest signal of an attacker-created session. Note: our own T3 test created stealth sessions on `victim-user`'s server, so some unfamiliar sessions in this window may be OURS from testing; correlate against the test log before alarming.
- Shell/tool commands you did not run are direct evidence of code execution via the server. Look for anything not matching your own activity (unexpected `curl`, `id`, reads of `~/.ssh`, `.env`, `env`, credential paths, network calls).
- Prompts in `session_input` you did not type indicate agent-driving via `/session/{id}/message`.
- REMEMBER the blind spot: file READS via `/file/content` leave nothing here. If the box was internet-reachable during the window, treat everything the user could read as potentially exfiltrated regardless of what the DB shows.

## Cross-check the network layer (the only source for reads / foreign IPs)

Run as the machine owner/root; opencode cannot help here:

    # connections to the exposed port during the window (if conntrack/firewall logging is on)
    sudo journalctl --since "2026-07-16 20:00" --until "2026-07-16 21:00" | grep -Ei '4096|opencode'
    # active/last connections to the port (point-in-time)
    ss -tnp | grep ':4096'
    # if ufw/iptables logging enabled:
    sudo grep -E 'DPT=4096' /var/log/syslog /var/log/ufw.log 2>/dev/null

If there is no network-layer logging, you cannot determine whether a remote party connected; assess based on whether the port was reachable beyond the trusted LAN during the window.

## After inspecting

- If you find only your own and the known test activity: interactive abuse is unlikely, but a silent file read cannot be excluded (see blind spot).
- If you find unexplained sessions/commands: treat as a potential compromise of everything `victim-user` could access; rotate any credentials reachable from that account (SSH keys, tokens, provider API keys, cloud creds) and review the network evidence.
- Going forward: never run an unsecured server, never bind `0.0.0.0`/`--mdns` on a networked host, and put HTTP access logging at a reverse proxy since opencode provides none (advisory `20260716-0850-01`, hardening how-to `20260716-0850-02`).
