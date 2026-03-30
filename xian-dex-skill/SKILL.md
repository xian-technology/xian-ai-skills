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
  - LP balances and LP approvals
  - DEX events such as `PairCreated`, `Mint`, `Burn`, `Swap`, `Sync`

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

- `con_dex_helper.buy(...)` / `sell(...)` for simple single-pair trades
- direct `con_dex` calls for multi-hop routes and liquidity operations

That matches the current contract split.

## Setup

```bash
pip install xian-tech-py
```

```python
from datetime import datetime, timedelta, timezone
from xian_py import Xian, Wallet

wallet = Wallet("your_private_key")
xian = Xian("http://127.0.0.1:26657", wallet=wallet)

def deadline(minutes: int = 5) -> str:
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)
```

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

Approve both tokens to `con_dex` first, then:

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

LP balances and LP allowances live in `con_pairs`.

```python
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
- `TransferLiq`
- `ApproveLiq`

Router admin events such as `ZeroFeeTraderUpdated` are on `con_dex`.

```python
swaps = xian.list_events("con_pairs", "Swap", limit=50)
pair_created = xian.list_events("con_pairs", "PairCreated", limit=25)
router_events = xian.list_events("con_dex", "ZeroFeeTraderUpdated", limit=25)
```

For restart-safe consumers, store the last processed `event_id` and use
`after_id=...` on the next poll.

## Common Failure Cases

Current DEX assertions use `SNAKX:*` messages. Expect errors such as:

- `SNAKX: EXPIRED`
- `SNAKX: INVALID_PATH`
- `SNAKX: NO_PAIR`
- `SNAKX: INSUFFICIENT_OUTPUT_AMOUNT`
- `SNAKX: INSUFFICIENT_LIQUIDITY`

Treat them as normal routing/market validation failures, not transport errors.

## Autonomous Agent Pattern

Today, the clean autonomous posture is polling-based:

1. run against a service node with indexed reads
2. poll `Swap` / `Sync` / token events with an `after_id` cursor
3. calculate the trade off-chain
4. approve and execute the trade
5. verify the confirmed tx receipt
6. only then trigger side effects such as notifications or social posts

If you are implementing this inside `xian-intentkit`, the current building
blocks are:

- `xian_list_events`
- `xian_call_contract`
- `xian_send_contract_transaction`
- `twitter_post_tweet`

The current `xian-intentkit` trigger model is scheduled polling, not true push
subscription. Design the strategy around periodic checks.

## Safety Rules

- Always set a short explicit deadline.
- Always quote before trading.
- Always use `amountOutMin` / slippage bounds.
- Prefer a dedicated trading wallet with capped approvals.
- Prefer helper flows for simple single-pair trades.
- Re-check the confirmed receipt before treating a trade as successful.
- Use BDS/indexed reads for bots; do not scrape the dashboard.

## Resources

- [xian-tech-py on PyPI](https://pypi.org/project/xian-tech-py/)
- [xian-technology/xian-py](https://github.com/xian-technology/xian-py)
- [xian-technology/xian-contracts](https://github.com/xian-technology/xian-contracts)
- current DEX contracts:
  - `contracts/dex/src/con_dex.py`
  - `contracts/dex/src/con_dex_helper.py`
  - `contracts/dex/src/con_pairs.py`
