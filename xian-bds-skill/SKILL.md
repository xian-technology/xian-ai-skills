---
name: xian-bds
description: Use Xian's optional BDS indexed reads and PostGraphile GraphQL. Check availability and freshness, query indexed blocks, transactions, events, state and DEX history, sync shielded wallets, or recover an index.
---

# Xian BDS Skill

## Choose a Read Surface

When enabled, BDS indexes finalized blocks in PostgreSQL for history, event
replay, token inventory, DEX candles, developer rewards, and shielded wallet
sync. Indexed ABCI routes require BDS on the queried node. PostGraphile is an
optional, read-only GraphQL API over that index. Consensus, transaction
submission, and zk proof verification work without either service.

1. Use CometBFT RPC for node status and direct ABCI state or contract reads for
   authoritative current values. A caught-up BDS index can still omit
   system-only state changes.
2. For indexed ABCI, call `get_bds_status()` (`/bds_status`) on the target RPC.
   A node with BDS disabled can return `Unknown query path: bds_status`.
   Check `worker_running`, `height_lag`, `alerts`, and `indexed_height` before
   relying on freshness. After a write, wait until the index reaches the
   transaction's finalized block before expecting the indexed record.
3. Check the GraphQL endpoint independently from the caller's network with a
   small query against the required schema. A BDS health response alone does
   not establish GraphQL reachability. If you use a separate indexed endpoint,
   confirm it serves the same chain.

Report unavailable or lagging history explicitly. Treat an empty page as a
successful result for the data covered by that index. A timeout, an ABCI
error, or a GraphQL `errors` response provides no evidence that a record is
absent. An archival RPC source can support index recovery when it retains the
missing block range.

## Preferred Client Surface

Prefer typed `xian-tech-py` methods. After confirming BDS is available on the
RPC node, use its indexed ABCI reads:

```python
from xian_py import Xian

with Xian("http://127.0.0.1:26657") as xian:
    status = xian.get_bds_status()
    blocks = xian.list_blocks(limit=20)
    txs = xian.list_txs_by_sender("sender_key", limit=50)
    events = xian.list_events("con_pairs", "Swap", limit=25)
    history = xian.get_state_history("currency.balances:alice", limit=25)
    token_contracts = xian.get_token_contracts(limit=20)
    token_balances = xian.get_token_balances("owner_key", include_zero=False)
    shielded = xian.list_shielded_wallet_history("tag-value", after_note_index=0)
```

The current Python client decodes V2 contract data recursively, including
exact decimals and wide integers. A numeric-looking string stored by the
contract remains text. Keep amounts exact when exporting indexed records.
In raw BDS rows and GraphQL JSON columns (event `data`, state values) a decimal
is `{"__fixed__": "1.5"}` and an integer outside the safe JavaScript range is
`{"__big_int__": "..."}`. MCP tools render decimal amounts as strings and wide
integers with `__big_int__`. BDS operator measurements can include fractional
timings.

For resumable event replay, use `list_events(..., after_id=0)` to read in
ascending order, then persist the last processed numeric event ID for the
next poll on the same index. Event IDs come from the BDS database, so verify
cursor continuity before switching or rebuilding the index. The SDK uses
indexed ABCI first and can fall back to GraphQL for `list_events` and
`get_events_for_tx`. When using the MCP `dex_list_events` tool across multiple
event sources, commit the returned cursor only when `complete` is true.

## Optional PostGraphile Endpoint

Use `xian node endpoints <profile>` for a managed node or get the query URL
from its operator. The stack defaults to `http://127.0.0.1:5000/graphql`
when the sidecar is running. `/graphiql` is the browser UI. Publishing the
endpoint is an operator choice made with `--public-query`.

Set `XIAN_GRAPHQL` for the MCP server or pass the query URL to the Python SDK:

```python
from xian_py import Xian, XianClientConfig

config = XianClientConfig(graphql_url="http://127.0.0.1:5000/graphql")
with Xian("http://127.0.0.1:26657", config=config) as xian:
    market = xian.get_dex_market_history("currency", "con_example_token", first=25)
```

For direct GraphQL, inspect the served schema. PostGraphile v5 uses `id` for
global IDs and `rowId` for numeric table IDs such as event cursors. Send
`BigInt` variables as strings. Use bounded connections, for example
`{ allBlocks(first: 1) { nodes { height } } }`. Public query mode requires
`first` or `last` on connections and limits offset, depth, and operation
cost. See `xian-docs-web/api/graphql.md` for query examples and
`xian-ai-guides/bds_graphql_schema.json` for the published schema snapshot.

## DEX Market History

Resolve a token pair in either order with `get_dex_market_history` in Python
or `dex_market_history` in MCP. Both use GraphQL. In Python pass `next_after`
as `after` for older fills and `candles.next_before` as `candle_before` for
older candles. The two cursors are independent. Each fill has a numeric event
ID and transaction hash. Amounts are exact decimals, and candle prices are
token1 per token0. Use current contract reads for live quotes.

If you already have a pair ID, `get_dex_candle_page(market_id=pair_id)` uses
indexed ABCI and works without GraphQL. Pass `next_before` as `end` for older
pages, keeping the pair, interval, and any `start` fixed with zero offset.
Continue until the cursor is null, even when a page is shorter than the limit.

## Index Recovery

Match the database, spool, snapshot, and RPC backfill source to the target
chain and its execution policy. Pruned RPC history cannot fill missing block
ranges. Use a compatible snapshot or a source with the required history.

Run the snapshot commands from `xian-stack`. Import replaces the target BDS
schema. Rehearse in an isolated instance and stop any BDS writer on the target
database before importing. Keep Postgres and the trusted RPC source available
for the restore.

```bash
uv run python ./scripts/backend.py bds-snapshot-export
uv run python ./scripts/backend.py bds-snapshot-import
```

The default archive is `.cometbft/snapshots/xian-bds-snapshot.tar.gz`. After
restoring, resume the writer and verify that indexed height advances and the
spool drains. The archive restores indexed PostgreSQL data. Full node recovery
also needs matching application and consensus stores.

For shielded wallet sync, prefer `shielded_wallet_history` and resume with
`after_note_index`. Lower-level event, tag, and transaction scans are
compatibility fallbacks. Shielded note rediscovery needs indexed history or
a saved `state_snapshot`. Keep a recoverable source for historical encrypted
payloads when serving wallet clients on a pruned chain.

## Validation

Exercise the same indexed read against a caught-up index, during lag, and
with the required service unavailable. Check that basic RPC tasks still work
with BDS disabled. For GraphQL, check the actual query and its pagination
against the target schema. For cross-repo BDS and snapshot behavior, use the
`xian-stack` localnet harness:

```bash
make localnet-e2e
```
