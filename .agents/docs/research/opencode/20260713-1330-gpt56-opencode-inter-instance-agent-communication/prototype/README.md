# Experimental Prototype Materials

These files illustrate the recommended architecture. They are not a production plugin or daemon.

## Contents

- `schemas/peer-message.schema.json`: proposed envelope schema
- `examples/message.request.json`: example request
- `examples/message.response.json`: example result
- `plugin/opencode-peer.ts`: plugin-shaped adapter skeleton
- `broker/broker.py`: SQLite claim/lease demonstration
- `tests/test_broker.py`: basic broker state test

## Important limitations

- The plugin SDK method names must be checked against the generated SDK for the exact target OpenCode version.
- The plugin does not implement signature verification or human approval.
- The broker has no network API, authorization layer, audit chain, migrations, or secret storage.
- The JSON examples contain placeholder signatures.
- Do not deploy these files without completing the security and integration work in the roadmap.

## Broker demonstration

```bash
python3 broker/broker.py --db /tmp/peer.sqlite3 submit examples/message.request.json
python3 broker/broker.py --db /tmp/peer.sqlite3 claim agent:builder worker-1
```
