---
name: xian-sdk
description: Build applications on the Xian blockchain using the current Python SDK. Use when writing wallets, bots, contract deployment tooling, indexers, or backend services that talk to Xian nodes.
---

# Xian SDK Skill

Use this skill when working with the current Xian Python SDK.

Important packaging detail:

- install package: `xian-tech-py`
- import module: `xian_py`

## Installation

```bash
pip install xian-tech-py

# Optional HD wallet support
pip install "xian-tech-py[hd]"

# Optional Ethereum wallet compatibility helpers
pip install "xian-tech-py[eth]"
```

## Default Workflow

1. Create or load a wallet.
2. Connect `Xian` or `XianAsync` to the node RPC.
3. Use `estimate_stamps(...)` or `simulate(...)` before expensive writes.
4. Submit writes with `mode="commit"` or `wait_for_tx=True` when downstream
   logic depends on confirmed chain state.
5. Use indexed reads for blocks, txs, events, and state history when the node
   exposes BDS-backed APIs.

## Quick Reference

```python
from xian_py import Xian, XianAsync, Wallet

wallet = Wallet()
xian = Xian("http://127.0.0.1:26657", wallet=wallet)

balance = xian.get_balance(wallet.public_key)
state = xian.get_state("currency", "balances", wallet.public_key)

quote = xian.estimate_stamps("currency", "transfer", {
    "to": "recipient",
    "amount": 10,
})

tx = xian.send(
    amount=10,
    to_address="recipient",
    mode="commit",
)

receipt = xian.wait_for_tx(tx.tx_hash)
events = xian.list_events("currency", "Transfer", limit=25)
```

## Wallets

### Basic Wallet

```python
from xian_py import Wallet

wallet = Wallet()
restored = Wallet("ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8")

print(wallet.public_key)
```

### HD Wallet

```python
from xian_py.wallet import HDWallet

hd = HDWallet()
print(hd.mnemonic_str)

wallet0 = hd.get_wallet([44, 0, 0, 0, 0])
wallet1 = hd.get_wallet([44, 0, 0, 0, 1])
```

## Reads

### Contract State

```python
from xian_py import Xian

xian = Xian("http://127.0.0.1:26657")

balance = xian.get_state("currency", "balances", "some_address")
allowance = xian.get_state("currency", "approvals", "owner", "spender")
source = xian.get_contract("currency")
runtime_code = xian.get_contract_code("currency")
```

### Read-Only Call and Simulation

```python
result = xian.call("currency", "balance_of", {"address": wallet.public_key})

simulation = xian.simulate("currency", "transfer", {
    "to": "recipient",
    "amount": 5,
})

stamps = xian.estimate_stamps("currency", "transfer", {
    "to": "recipient",
    "amount": 5,
})
```

## Writes

### Simple Transfer

```python
tx = xian.send(
    amount=25,
    to_address="recipient",
    token="currency",
    mode="commit",
)

print(tx.tx_hash)
```

### Generic Contract Call

```python
tx = xian.send_tx(
    contract="currency",
    function="approve",
    kwargs={"to": "spender", "amount": 100},
    mode="commit",
)
```

### Approval Helper

```python
tx = xian.approve(
    contract="con_dex",
    token="currency",
    amount=500,
    mode="commit",
)
```

## Contract Deployment

Contract names must start with a lowercase ASCII letter and then use only
lowercase ASCII letters, digits, or underscores.

```python
code = '''
balances = Hash(default_value=0)

@construct
def seed():
    balances[ctx.caller] = 1000

@export
def transfer(to: str, amount: float):
    assert amount > 0, "Amount must be positive"
    assert balances[ctx.caller] >= amount, "Insufficient balance"
    balances[ctx.caller] -= amount
    balances[to] += amount
'''

tx = xian.submit_contract(
    name="my_token",
    code=code,
    mode="commit",
)
```

See `references/contract-patterns.md` for current contract snippets.

## Indexed Data

These methods are the right choice when the node is running with BDS/indexed
reads enabled.

```python
blocks = xian.list_blocks(limit=20)
block = xian.get_block(100)
indexed_tx = xian.get_indexed_tx("ABC123...")
sender_txs = xian.list_txs_by_sender(wallet.public_key, limit=50)
contract_txs = xian.list_txs_by_contract("con_dex", limit=50)
events = xian.list_events("con_pairs", "Swap", limit=25)
state_history = xian.get_state_history("currency.balances:some_address", limit=25)
dev_rewards = xian.get_developer_rewards(wallet.public_key)
```

## Async Pattern

```python
import asyncio
from xian_py import XianAsync, Wallet

async def main():
    wallet = Wallet()
    async with XianAsync("http://127.0.0.1:26657", wallet=wallet) as xian:
        balance, status = await asyncio.gather(
            xian.get_balance(wallet.public_key),
            xian.get_node_status(),
        )

        tx = await xian.send_tx(
            contract="currency",
            function="transfer",
            kwargs={"to": "recipient", "amount": 3},
            mode="commit",
        )

        receipt = await xian.wait_for_tx(tx.tx_hash)
        return balance, status, receipt

asyncio.run(main())
```

## Event and Block Watching

```python
for block in xian.watch_blocks():
    print(block.height, block.hash)
```

For contract events, prefer indexed polling with `list_events(...)` and an
`after_id` cursor when you need restart-safe consumers.

## SDK Guidance

- Prefer `mode="commit"` for writes that feed a later step.
- Prefer `estimate_stamps(...)` over hardcoding stamp values.
- Prefer `approve(...)` and other helper methods when they fit.
- Prefer indexed APIs for analytics, explorers, and bots.
- Treat `get_contract(...)` as original contract source and
  `get_contract_code(...)` as compiled/runtime code.

## Resources

- [xian-tech-py on PyPI](https://pypi.org/project/xian-tech-py/)
- [xian-technology/xian-py](https://github.com/xian-technology/xian-py)
- [xian-technology/xian-contracting](https://github.com/xian-technology/xian-contracting)
- [xian docs](https://docs.xian.org)
