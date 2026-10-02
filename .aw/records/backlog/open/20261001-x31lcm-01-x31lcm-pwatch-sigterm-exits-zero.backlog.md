- Id: x31lcm
- Status: open
- Set: x31lcm
- Priority: low
- Work-Kind: chore
- Summary: Decide whether aw pwatch should exit 0 when SIGTERM'd, since a supervisor cannot distinguish that from a clean finish

## Workflow history
- 2026-10-01 created (aw backlog): Decide whether aw pwatch should exit 0 when SIGTERM'd, since a supervisor cannot distinguish that from a clean finish

MEASURED 2026-10-01 at HEAD `95fbd0667` while authoring plan `ug85or` (its F-06 and OQ-02): `pwatch` installs its OWN handlers for both signals (`signal.signal(signal.SIGINT, stop_cleanly)` and the SIGTERM twin, where `stop_cleanly` raises `SystemExit(0)`) and catches `(KeyboardInterrupt, SystemExit)` returning 0. A real `os.killpg` with SIGINT and with SIGTERM against a running `aw pwatch -m python` returned **0** both times. FOR SIGINT THAT IS PLAINLY RIGHT: a watch loop's normal end is a Ctrl-C, so reporting failure for the intended way to stop would itself be the defect. FOR SIGTERM IT IS ARGUABLE: a supervisor that terminates the process cannot distinguish that from a clean finish, where every other `aw` verb either returns 130 (via `cli.main`'s `except KeyboardInterrupt`) or dies `WIFSIGNALED` so the shell reports 143. THIS IS NOT FILED AS A BUG because no evidence establishes it is one; deciding it needs a survey of what actually supervises `pwatch`. NOTHING ELSE DEPENDS ON THE ANSWER: `pwatch` declares `exit_contract=(0, 1, 2)` and 0 is in that tuple, so its declaration is correct either way. Plan `ug85or` uses this measurement only as the counter-example proving no single signal-derived code could be enumerated in `exit_contract`.
