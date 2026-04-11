---
name: xian-bds
description: Use Xian's indexed/BDS read and recovery surface correctly. Use when working with indexed blocks, transactions, events, state history, shielded wallet sync, or operator recovery flows.
---

# Xian BDS Skill

Use this skill when the task depends on indexed chain data instead of raw
consensus RPC.

## Core Model

- BDS is Xian's indexed read layer.
- Consensus and zk proof verification do not depend on BDS.
- Explorers, wallet history, event queries, and shielded note rediscovery do
  depend on BDS or an equivalent indexed recovery feed.

That means BDS is not consensus-critical, but it is operationally critical for
wallet-facing availability.

## When To Use It

Use BDS-backed reads for:

- paginated block and transaction history
- event queries by contract / event name
- state history and per-tx/per-block state inspection
- developer reward summaries
- shielded wallet sync and shielded note rediscovery

Do not use it for:

- basic consensus liveness checks that raw RPC already answers
- pretending shielded wallets are fully recoverable from seed material alone

## Preferred Client Surface

Use the typed `xian-tech-py` methods rather than hand-rolled GraphQL or raw
HTTP calls when possible.

```python
from xian_py import Xian

xian = Xian("http://127.0.0.1:26657")

status = xian.get_bds_status()
blocks = xian.list_blocks(limit=20)
txs = xian.list_txs_by_sender("sender_key", limit=50)
events = xian.list_events("con_pairs", "Swap", limit=25)
history = xian.get_state_history("currency.balances:alice", limit=25)
shielded = xian.list_shielded_wallet_history("tag-value", limit=100)
```

If an MCP client is available, prefer typed MCP tools over a generic GraphQL
escape hatch for the same reason: clearer schemas and safer agent behavior.

## Service-Node Requirement

The indexed surface is meant to be consumed from a service node or another node
with BDS enabled.

Operator-side posture:

- keep at least one indexed node available for wallet-facing services
- keep at least one archival recovery source or exported BDS snapshot
- validate snapshot import, not just snapshot export

## Standard Recovery Commands

`xian-stack` now standardizes BDS snapshot export/import through the backend
surface:

```bash
python3 ./scripts/backend.py bds-snapshot-export
python3 ./scripts/backend.py bds-snapshot-import
```

By default the archive lives under:

```bash
.cometbft/snapshots/xian-bds-snapshot.tar.gz
```

## Shielded Wallet Reality

The important split is:

- zk correctness is on-chain and survives indexer outages
- shielded wallet recovery needs indexed history or a saved `state_snapshot`

If every BDS node is lost and historical chain data is pruned away, older
shielded notes may become undiscoverable in practice unless users kept
`state_snapshot` backups or operators kept usable BDS snapshots / archival
history.

## Implementation Guidance

- Prefer `shielded_wallet_history` for wallet sync when available.
- Use lower-level event/tag/tx scans only as compatibility fallback.
- Version and document wallet-facing indexed read surfaces deliberately.
- Treat retention of encrypted payload blobs and snapshot export/import as part
  of the privacy product, not as optional ops polish.

## Validation

Check both the client read path and the operator recovery path:

```bash
pytest -q xian-py/tests
python3 ./scripts/backend.py bds-snapshot-export
python3 ./scripts/backend.py bds-snapshot-import
```
