---
name: xian-dex
description: Build against the current Xian DEX contracts. Use when quoting, swapping, adding or removing liquidity, reading DEX events, or designing autonomous trading flows on Xian.
---

# Xian DEX Skill

Use this skill when working with the current Xian DEX contracts.

Default client stack:

- install package: `xian-tech-py`
- import module: `xian_py`

## Contract Map

Current DEX surface:

- `con_pairs`
  - pair registry
  - reserves
  - LP token registration and pair-to-LP-token binding
  - DEX events such as `PairCreated`, `LpTokenRegistered`, `Mint`, `Burn`,
    `Swap`, `Sync`

- `con_lp_token`
  - XSC001-compatible LP token template
  - LP balances, transfers, and approvals for bound pair positions

- `con_dex`
  - quote helpers
  - direct router swaps
  - liquidity add/remove
  - fee-on-transfer token support
  - zero-fee trader controls

- `con_dex_helper`
  - single-pair `buy(...)` and `sell(...)`
  - slippage + deadline wrapper for common user flows

## First Rule

Prefer:

- the first-class `dex_*` MCP/HTTP tools when `xian-mcp-server` is available
- `con_dex_helper.buy(...)` / `sell(...)` for simple single-pair trades
- direct `con_dex` calls for multi-hop routes and liquidity operations

That matches the current contract split.

The canonical generated-client input is `xian-dex/dex-interface.json`. Do not
infer exported signatures or safety policies from old examples when that
manifest is available.

## Agent Tool Workflow

`xian-mcp-server` exposes a safe plan-first workflow over both MCP stdio and its
shared HTTP catalog:

- discovery: `dex_list_pairs`, `dex_get_pair`
- quotes: `dex_quote_exact_in`, `dex_quote_exact_out`
- server-issued plans: `dex_plan_swap`, `dex_plan_add_liquidity`,
  `dex_plan_remove_liquidity`
- gated submission: `dex_submit_swap`, `dex_submit_add_liquidity`,
  `dex_submit_remove_liquidity`
- low-latency live wait without BDS: `dex_wait_live_event`
- indexed verification/recovery: `dex_list_events`

Plans are structured audit JSON with the route and hop amounts, exact approval
and router calls, signer fee tier, slippage minimums, an absolute deadline,
fee-on-transfer selection, price impact, warnings, an opaque `plan_id`, a
canonical SHA-256 digest, and issue/expiry timestamps. Show the full plan to the
user before submission. After authorization, pass only `plan_id` and the private
key to the matching submit tool; never reconstruct or send calls to a submitter.

The server stores the canonical plan in a bounded process-local registry.
Submission atomically consumes it before wallet validation, simulation, or any
transaction, which prevents concurrent execution and replay after partial
multi-call failures. Plans expire quickly and do not survive a server restart;
if submission reports an unknown, expired, consumed, invalidated, or evicted
`plan_id`, create and confirm a fresh plan. Submission tools use the unsafe-wallet
gate and simulate by default.

The router has no exact-output transaction function. Exact-output quoting is
supported, while an exact-output swap plan becomes an exact-input call whose
input is capped by slippage and whose `amountOutMin` is the requested output.
Fee-on-transfer exact-output plans are rejected because they cannot guarantee
the received amount. The exact-input router spends that full input cap; unused
slippage headroom becomes additional output rather than a refund.

## Setup

```bash
uv add xian-tech-py
```

```python
from datetime import datetime, timedelta, timezone
from xian_py import Xian, Wallet

wallet = Wallet("your_private_key")
xian = Xian("http://127.0.0.1:26657", wallet=wallet)

def deadline(minutes: int = 5) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)
```

The current helper and router contracts require an absolute future
`datetime.datetime` deadline. Do not use the older relative `deadline_min`
pattern.

## Pair Discovery

Pairs are keyed by canonical token ordering.

```python
def canonical_tokens(token_a: str, token_b: str) -> tuple[str, str]:
    return (token_a, token_b) if token_a < token_b else (token_b, token_a)

token0, token1 = canonical_tokens("currency", "con_my_token")
pair_id = xian.get_state("con_pairs", "toks_to_pair", token0, token1)

if pair_id is None:
    raise ValueError("pair does not exist")

reserve0, reserve1, _ = xian.call("con_pairs", "getReserves", {"pair": pair_id})
```

## Quotes

### Single-Pair Quote

```python
amounts = xian.call("con_dex", "getAmountsOut", {
    "amountIn": 100,
    "src": "currency",
    "path": [pair_id],
})

expected_out = amounts[-1]
```

### Input Needed for a Target Buy

```python
fee_bps = xian.call("con_dex", "getTradeFeeBps", {})
input_needed = xian.call("con_dex", "getAmountIn", {
    "amountOut": 50,
    "reserveIn": reserve0,
    "reserveOut": reserve1,
    "feeBps": fee_bps,
})
```

## Approvals

Which contract you approve depends on the path:

- helper flow: approve `con_dex_helper`
- direct router flow: approve `con_dex`

### Helper Approval

```python
xian.approve(
    contract="con_dex_helper",
    token="currency",
    amount=250,
    mode="commit",
)
```

### Direct Router Approval

```python
xian.approve(
    contract="con_dex",
    token="currency",
    amount=250,
    mode="commit",
)
```

## Single-Pair Buy / Sell with `con_dex_helper`

### Buy

```python
tx = xian.send_tx(
    contract="con_dex_helper",
    function="buy",
    kwargs={
        "buy_token": "con_my_token",
        "sell_token": "currency",
        "amount": 50,
        "slippage": 1,
        "deadline": deadline(5),
    },
    mode="commit",
)
```

### Sell

```python
tx = xian.send_tx(
    contract="con_dex_helper",
    function="sell",
    kwargs={
        "sell_token": "con_my_token",
        "buy_token": "currency",
        "amount": 25,
        "slippage": 1,
        "deadline": deadline(5),
    },
    mode="commit",
)
```

## Direct Router Swaps

### Single Pair with Fee-On-Transfer Support

```python
tx = xian.send_tx(
    contract="con_dex",
    function="swapExactTokenForTokenSupportingFeeOnTransferTokens",
    kwargs={
        "amountIn": 100,
        "amountOutMin": 90,
        "pair": pair_id,
        "src": "currency",
        "to": wallet.public_key,
        "deadline": deadline(5),
    },
    mode="commit",
)
```

### Multi-Hop

```python
path = [pair_a, pair_b]

quoted = xian.call("con_dex", "getAmountsOut", {
    "amountIn": 100,
    "src": "currency",
    "path": path,
})

min_out = quoted[-1] * 0.99

tx = xian.send_tx(
    contract="con_dex",
    function="swapExactTokensForTokens",
    kwargs={
        "amountIn": 100,
        "amountOutMin": min_out,
        "path": path,
        "src": "currency",
        "to": wallet.public_key,
        "deadline": deadline(5),
    },
    mode="commit",
)
```

## Liquidity

### Add Liquidity

Approve both underlying tokens to `con_dex` first, then add liquidity. The pair
must have a registered bound LP token; bootstrap/operator code usually calls
`con_pairs.registerLpToken(...)` before pair creation. Only pass the optional
`lpToken` argument to `addLiquidity(...)` when it matches the registered token.

```python
tx = xian.send_tx(
    contract="con_dex",
    function="addLiquidity",
    kwargs={
        "tokenA": "currency",
        "tokenB": "con_my_token",
        "amountADesired": 1000,
        "amountBDesired": 500,
        "amountAMin": 990,
        "amountBMin": 495,
        "to": wallet.public_key,
        "deadline": deadline(10),
    },
    mode="commit",
)
```

### Remove Liquidity

LP balances and LP allowances live in the bound LP token contract, not in
`con_pairs`. Resolve the LP token, approve it to `con_dex`, then remove
liquidity.

```python
lp_token = xian.call("con_pairs", "lpTokenFor", {"pair": pair_id})

xian.approve(
    contract="con_dex",
    token=lp_token,
    amount=10,
    mode="commit",
)

tx = xian.send_tx(
    contract="con_dex",
    function="removeLiquidity",
    kwargs={
        "tokenA": "currency",
        "tokenB": "con_my_token",
        "liquidity": 10,
        "amountAMin": 9,
        "amountBMin": 4,
        "to": wallet.public_key,
        "deadline": deadline(10),
    },
    mode="commit",
)
```

## Events

Key indexed DEX events are on `con_pairs`:

- `PairCreated`
- `Mint`
- `Burn`
- `Swap`
- `Sync`
- `LpTokenRegistered`

LP token `Transfer`, `Approve`, `Mint`, and `Burn` events are on the bound LP
token contracts. Router admin events such as `ZeroFeeTraderUpdated` are on
`con_dex`.

```python
swaps = xian.list_events("con_pairs", "Swap", limit=50)
pair_created = xian.list_events("con_pairs", "PairCreated", limit=25)
router_events = xian.list_events("con_dex", "ZeroFeeTraderUpdated", limit=25)
```

For restart-safe consumers, store the last processed `event_id` and use
`after_id=...` on the next poll.

For a bounded low-latency wait, `dex_wait_live_event(contract, event, ...)`
subscribes directly to finalized CometBFT transaction events and does not need
BDS. Start the wait before the transaction or external activity you expect to
observe. It is intentionally non-durable: disconnects, process restarts, and
events finalized before subscription can be missed, and it returns no replay
cursor. Recover with `dex_list_events(after_id=...)` when BDS is available.

## Common Failure Cases

Current DEX assertions use `SNAKX:*` messages. Expect errors such as:

- `SNAKX: EXPIRED`
- `SNAKX: INVALID_PATH`
- `SNAKX: NO_PAIR`
- `SNAKX: INSUFFICIENT_OUTPUT_AMOUNT`
- `SNAKX: INSUFFICIENT_LIQUIDITY`

Treat them as normal routing/market validation failures, not transport errors.

## Autonomous Agent Pattern

The clean autonomous posture is a hybrid live-plus-recovery loop:

1. persist the last processed BDS `event_id` when durable recovery is required
2. use `dex_wait_live_event` for immediate finalized notifications
3. calculate the trade off-chain
4. approve and execute the trade
5. verify the confirmed tx receipt
6. reconcile with `dex_list_events(after_id=...)` after reconnect/startup
7. only then trigger side effects such as notifications or social posts

With `xian-mcp-server`, use these building blocks:

- `dex_list_events`
- `dex_wait_live_event`
- `dex_quote_exact_in` / `dex_quote_exact_out`
- `dex_plan_swap`
- `dex_submit_swap(private_key, plan_id)` after explicit authorization

The live event surface is a bounded WebSocket wait, not a durable queue. The
indexed event surface remains cursor-based polling. Persist `next_after_id` for
recovery and never assume a live timeout proves that no matching event was
finalized.

## Safety Rules

- Always set a short explicit deadline.
- Always quote before trading.
- Always use `amountOutMin` / slippage bounds.
- Prefer a dedicated trading wallet with capped approvals.
- Prefer helper flows for simple single-pair trades.
- Re-check the confirmed receipt before treating a trade as successful.
- Use direct CometBFT live events for speed and BDS/indexed reads for recovery;
  do not scrape the dashboard.
- Use uv-managed Python commands for SDK-based bots and deployment scripts.

## Resources

- [xian-tech-py on PyPI](https://pypi.org/project/xian-tech-py/)
- [xian-technology/xian-py](https://github.com/xian-technology/xian-py)
- [xian-technology/xian-dex](https://github.com/xian-technology/xian-dex)
- current DEX contracts:
  - `src/con_dex.py`
  - `src/con_dex_helper.py`
  - `src/con_pairs.py`
  - `src/con_lp_token.py`
