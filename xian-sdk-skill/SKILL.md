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

The V2 examples use the source SDK. Check out the matching `xian-contracting`
and `xian-py` revisions as sibling directories. From their parent directory
run the following commands. The profile check prints `xian_vm_v2`.
[Pinned SDK setup](https://github.com/xian-technology/xian-docs-web/blob/main/tools/xian-py.md#install)

```bash
uv sync --project xian-py --frozen
uv run --project xian-py --no-sync python -c 'from xian_py import XianClientConfig; print(XianClientConfig().vm_profile)'
```

Add `--extra hd` for mnemonic wallets, `--extra eth` for Ethereum wallet
compatibility, `--extra app` for application helpers or `--extra compile`
for offline compiler inspection to the sync command as needed. Execute your
script with `uv run --project xian-py --no-sync python your_script.py`.

## Default Workflow

1. Create or load a wallet.
2. Connect `Xian` or `XianAsync` to the node RPC.
3. Use `estimate_chi(...)` or `simulate(...)` before expensive writes.
4. Prefer helper clients such as `xian.token()`, `xian.contract()`,
   `xian.events(...)`, and `xian.state_key(...)` for app code when they fit.
5. Submit writes with `mode="checktx", wait_for_tx=True` or `mode="commit"`
   when downstream logic depends on confirmed chain state.
6. Use indexed reads for blocks, txs, events, token inventory, and state history when the node
   exposes BDS-backed APIs.

## Quick Reference

The current Python and TypeScript SDKs default to `xian_vm_v2`. Signing,
simulation, reads and receipt decoding use the same profile. A client for
an archived V1 test fixture needs an explicit `XianClientConfig(vm_profile="xian_vm_v1")`
in Python or `vmProfile: "xian_vm_v1"` in TypeScript. Low-level Python
transaction helpers take `vm_profile` directly. The chain profile comes from
genesis. A client setting cannot change how validators execute a contract.

```python
from decimal import Decimal
from xian_py import Wallet, Xian

wallet = Wallet()
xian = Xian("http://127.0.0.1:26657", wallet=wallet)

balance = xian.token().balance_of(wallet.public_key)
state = xian.state_key("currency", "balances", wallet.public_key).get()

quote = xian.estimate_chi("currency", "transfer", {
    "to": "recipient",
    "amount": Decimal("10.000000000000000000000000000001"),
})

tx = xian.token().transfer(
    "recipient",
    Decimal("10.000000000000000000000000000001"),
    mode="checktx",
    wait_for_tx=True,
)

receipt = tx.receipt or xian.wait_for_tx(tx.tx_hash)
events = xian.events("currency", "Transfer").list(limit=25)
```

### Amounts at the API boundary

- For generic contract kwargs, use Python `int` or `Decimal(text)`. Python
  binary floats are rejected. An ordinary string remains a string. Token
  convenience methods such as `transfer` also accept decimal text. V2
  contract reads decode to Python integers and `ContractingDecimal` values.
- In TypeScript pass `fixed("1.25")` from `@xian-tech/client` for a decimal
  and `9007199254740993n` for a wide integer. Keep amount input as text until
  conversion. Fractional or unsafe JavaScript numbers lose the source digits.
- For MCP token and DEX amount fields, pass decimal text or a safe integer.
  For generic MCP kwargs, pass `{"amount":{"__fixed__":"1.25"}}`. On the
  V2 wire, integers outside ±(2^53−1) use `{"__big_int__":"9007199254740993"}`.
  Wrapper text is canonical, with no exponent, plus sign, negative zero,
  redundant leading zeros or fractional trailing zeros.
- For a Xian–Solana bridge request, send `token_amount` as decimal text.
  Enforce the token's configured precision before converting Solana amounts
  to integer base units. Construct a Xian token transfer from the exact
  human-unit amount. [Bridge API](https://github.com/xian-technology/xian-bridge#api)

## Wallets

### Basic Wallet

```python
from xian_py import Wallet

wallet = Wallet()
restored = Wallet("ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8")
from_seed = Wallet.from_mnemonic("word1 word2 ...")

print(wallet.public_key)
```

### HD Wallet

```python
from xian_py.wallet import HDWallet

hd = HDWallet()
print(hd.mnemonic_str)

wallet0 = hd.get_wallet(account_index=0)
wallet1 = hd.get_wallet(account_index=1)
```

`HDWallet.get_wallet` and `Wallet.from_mnemonic` share the browser/mobile indexed
derivation. The same phrase and account index produce the same Xian account;
both Python methods default to index `0`. Use an integer index from `0` through
`4294967295`, not a derivation-path list. Retain the account index with recovery
material. MCP HD-wallet tools use this same scheme and default to account `0`;
pass `account_index` to select another account.

## Reads

### Contract State

```python
from xian_py import Xian

xian = Xian("http://127.0.0.1:26657")

balance = xian.get_state("currency", "balances", "some_address")
allowance = xian.get_state("currency", "approvals", "owner", "spender")
source = xian.get_contract_source("currency")
vm_ir = xian.get_contract_ir("currency")
```

### Read-Only Call and Simulation

```python
result = xian.call("currency", "balance_of", {"address": wallet.public_key})

simulation = xian.simulate("currency", "transfer", {
    "to": "recipient",
    "amount": 5,
})

chi_quote = xian.estimate_chi("currency", "transfer", {
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

Public non-system contract deployments must use names that start with `con_`.
Names must be lowercase ASCII with digits and underscores only, and they are
capped by the runtime submission rules.

```python
code = '''
balances = Hash(default_value=0)

@construct
def seed():
    balances[ctx.caller] = 1000

@export
def transfer(to: str, amount: decimal):
    assert amount > 0, "Amount must be positive"
    assert balances[ctx.caller] >= amount, "Insufficient balance"
    balances[ctx.caller] -= amount
    balances[to] += amount
'''

tx = xian.deploy_contract(
    name="con_my_token",
    source=code,
    mode="commit",
)
```

`deploy_contract(...)` is the app-facing source deployment helper.
`submit_contract(...)` remains the lower-level public submission call. Both
submit source; the node derives Xian VM IR from that source.

See `references/contract-patterns.md` for quick snippets. For writing a new
contract from a product spec, use the `xian-contract` skill when available.

## Indexed Data

These methods are the right choice when the node is running with BDS/indexed
reads enabled.
Use DEX candle `market_id` values reported by the indexer, often pair id values;
do not invent token-pair strings.

```python
blocks = xian.list_blocks(limit=20)
block = xian.get_block(100)
indexed_tx = xian.get_indexed_tx("ABC123...")
sender_txs = xian.list_txs_by_sender(wallet.public_key, limit=50)
contract_txs = xian.list_txs_by_contract("con_dex", limit=50)
events = xian.list_events("con_pairs", "Swap", limit=25)
state_history = xian.get_state_history("currency.balances:some_address", limit=25)
dev_rewards = xian.get_developer_rewards(wallet.public_key)
token_contracts = xian.get_token_contracts(limit=20)
token_balances = xian.get_token_balances(wallet.public_key, include_zero=False)
shielded_tags = xian.list_shielded_output_tags("tag-value", limit=100)
dex_candles = xian.list_dex_candles(market_id="7", interval="1m", limit=100)
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
    print(block.height, block.block_hash)
```

For contract events, prefer indexed polling with `list_events(...)` and an
`after_id` cursor when you need restart-safe consumers.

## SDK Guidance

- Prefer `mode="checktx", wait_for_tx=True` or `mode="commit"` for writes that
  feed a later step.
- Prefer `estimate_chi(...)` over hardcoding chi values. Omitting `chi` makes
  the SDK supply `estimate + max(ceil(estimate * 5%), 10)`. A chain caps one
  transaction at `max_tx_chi` (200,000 chi by default) in every fee mode and
  rejects a larger `chi_supplied` at CheckTx; the block cap (500,000 by
  default) counts supplied chi, so oversupplying also shrinks block capacity.
- On paid networks the balance must cover `chi_supplied / chi_rate`; for a
  `currency.transfer` the amount plus that reservation must fit the balance.
  `chi_rate` (chi per XIAN) is chain state, read it with
  `xian.get_state("chi_cost", "S", "value")` instead of hardcoding it; only a
  validator governance vote changes it.
- Simulation runs with at most the chain's `max_tx_chi`, so a transaction that
  needs more fails in simulation rather than after submission.
- With current `xian-runtime-types`, `str()` of a returned `ContractingDecimal`
  is plain fixed-point text
  (`1000`, not `1E+3`) and format specs such as `f"{amount:.2f}"` work.
- Prefer helper clients (`token()`, `contract()`, `events(...)`,
  `state_key(...)`) and helpers such as `approve(...)` when they fit.
- Prefer indexed APIs for analytics, explorers, and bots.
- Treat `get_contract_source(...)` as original contract source and
  `get_contract_ir(...)` as Xian VM IR.
- Use uv for Python dependency and command examples. Do not recommend Poetry or
  manual virtualenv setup for current Xian Python repos.

## Resources

- [xian-tech-py on PyPI](https://pypi.org/project/xian-tech-py/)
- [xian-technology/xian-py](https://github.com/xian-technology/xian-py)
- [xian-technology/xian-contracting](https://github.com/xian-technology/xian-contracting)
- [xian docs](https://docs.xian.org)
