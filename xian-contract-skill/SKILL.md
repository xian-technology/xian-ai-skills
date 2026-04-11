---
name: xian-contract
description: Author and validate current Xian smart contracts. Use when creating or updating contracts, token contracts, contract packages, runtime-facing tests, or deployment flows on Xian.
---

# Xian Contract Skill

Use this skill for current Xian contract authoring work.

## Core Split

Keep these roles separate:

- `xian-contracting`
  - runtime, compiler, storage semantics, metering, and lint rules
- `xian-contracts`
  - curated contract packages built on top of that runtime
- `xian-linter`
  - standalone lint wrapper around the runtime rule surface

If you are changing execution semantics, you are in `xian-contracting`.
If you are authoring or hardening a maintained contract package, you are in
`xian-contracts`.

## Contract Source Rules

Xian contracts use Python syntax, but they are not general Python.

Important authoring constraints enforced by the linter/runtime:

- only `@construct` and `@export` are valid decorators
- at most one `@construct`
- every contract must expose at least one `@export`
- exported arguments must have type annotations
- allowed annotation types are limited to:
  - `Any`
  - `bool`
  - `datetime.datetime`
  - `datetime.timedelta`
  - `dict`
  - `float`
  - `int`
  - `list`
  - `str`
- imports must stay at module level
- `from ... import ...` is not allowed; use plain `import`
- classes, async functions, nested functions, lambdas, `with`, `try`, and
  similar general-Python features are not part of the contract model

Do not write contracts as if they were ordinary backend Python modules.

## State Model

The normal authored storage surface is:

- `Variable()`
- `Hash()`
- `ForeignVariable()`
- `ForeignHash()`
- `LogEvent(...)`

Keep contract state explicit and deterministic. Avoid clever indirection when a
plain `Variable` or `Hash` will do.

## Event Style

Use the modern positional `LogEvent` style:

```python
TransferEvent = LogEvent(
    "Transfer",
    {
        "from": {"type": str, "idx": True},
        "to": {"type": str, "idx": True},
        "amount": {"type": float},
    },
)
```

Do not use the older keyword-heavy shape:

```python
LogEvent(event="Transfer", params={...})
```

For authored contracts, the normal form is `LogEvent("EventName", params)`.
Use explicit `contract=` / `name=` only when you genuinely need a different
storage/event binding, such as system-contract internals.

## Token Contracts

For fungible tokens, target the current XSC001 shape.

Current required surface:

- storage:
  - `balances`
  - `approvals`
  - `metadata`
- exports:
  - `change_metadata(key, value)`
  - `transfer(amount, to)`
  - `approve(amount, to)`
  - `transfer_from(amount, to, main_account)`
  - `balance_of(address)`
- required metadata fields:
  - `token_name`
  - `token_symbol`
  - `token_logo_url`
  - `token_logo_svg`
  - `token_website`

Current notes:

- the XSC001 checker does not require `metadata["operator"]`
- current user-facing tokens often still expose additional helpers such as
  `allowance(...)`, `get_metadata()`, `total_supply`, or operator rotation
- interface compliance is not the same as economic safety

If you are building a fungible token, start from current XSC001 expectations,
not from older ad hoc token clones.

## XSC002 And XSC003 Reality

Be precise here:

- legacy `currency.s.py` still contains permit logic labeled `XSC002`
- legacy streaming logic labeled `XSC003` exists historically and has since
  been extracted into the `stream-payments` package
- there are not separate curated `xsc002` / `xsc003` contract-standard packages
  in `xian-contracts` today

So:

- treat XSC001 as the current canonical fungible-token target
- treat permit/streaming compatibility as explicit feature work, not as an
  assumed default standard layer

## Package Layout In `xian-contracts`

For maintained contract packages, follow the repo layout exactly:

- one package per contract or tightly coupled contract system
- `README.md`
- `src/`
- `tests/`
- at least one `src/con_*.py` entrypoint

Keep package maturity explicit: `curated`, `candidate`, or `experimental`.
Do not present exploratory contracts as if they were production-ready.

## Validation

For package work in `xian-contracts`, start with:

```bash
uv sync --group dev
uv run python scripts/validate_contracts.py
uv run pytest
```

Use package-local tests when narrowing the loop:

```bash
uv run pytest contracts/xsc001/tests/test_xsc001.py
```

For runtime/lint changes in `xian-contracting` or `xian-linter`, run the repo's
own test surface rather than assuming `xian-contracts` coverage is enough.

## Local Testing

Use `ContractingClient` for local contract iteration and unit-style runtime
tests:

```python
from contracting.client import ContractingClient

client = ContractingClient()
client.submit(name="con_token", code=contract_source)
token = client.get_contract("con_token")
token.transfer(amount=10, to="bob")
```

This is the right tool for:

- fast contract behavior tests
- local storage assertions
- package-local unit tests

## Network Deployment

For real network deployment, use the public submission path.

With `xian-py`:

```python
from xian_py import Xian, Wallet

wallet = Wallet("your_private_key")
xian = Xian("http://127.0.0.1:26657", wallet=wallet)

result = xian.submit_contract(
    name="con_example",
    code=contract_source,
    args={"owner": "alice"}  # constructor args if needed
)
```

Under the hood this goes through:

- `submission.submit_contract(name=..., code=..., constructor_args=...)`

Current important deployment rules:

- non-`sys` deployments must use names starting with `con_`
- names must be lowercase ASCII with digits/underscores only
- names are capped at 64 characters
- source size is capped by the runtime submission limit
- contract factories should also deploy through `submission.submit_contract(...)`

Do not bypass `submission` as the public deployment boundary.

## Implementation Guidance

- prefer simple explicit state and exported methods over clever metaprogramming
- use current contract packages as pattern sources before inventing new local
  conventions
- when building a token, decide explicitly whether you are doing:
  - plain XSC001 fungible token behavior
  - fee-on-transfer / reflection behavior
  - shielded-note behavior
- keep contract docs and package status in sync with reality
- when changing a maintained package, add or update package-local tests in the
  same change
