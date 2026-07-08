---
name: xian-contract
description: Write valid Xian smart contract source and tests from a product spec. Use when creating a new Xian contract, turning business rules into contract code, choosing storage/events/time/numeric patterns, writing ContractingClient tests, or preparing source-backed deployment snippets.
---

# Xian Contract Skill

Use this skill to write new Xian contract source that passes the current
`xian-contracting` linter/runtime and is practical to test locally.

If the task is about changing the compiler, runtime, linter, or maintained
contract package infrastructure rather than writing a contract, read the owning
repo's `AGENTS.md`/`README.md` and work in that repo directly.

## Default Workflow

1. Convert the request into a contract spec:
   - contract name, normally `con_*` for user-deployed contracts
   - actors and permissions
   - exported functions and argument types
   - state variables and hash keys
   - invariants and failure messages
   - events that wallets, indexers, or bots should consume
   - time, randomness, cross-contract, or token-standard needs
2. Read `references/contract-authoring-rules.md` before writing non-trivial
   source, and whenever the contract uses time, events, foreign state,
   cross-contract calls, randomness, or complex stored values.
3. Write the smallest explicit contract that satisfies the spec.
4. Write local tests with `ContractingClient` before adding deployment code.
5. If the user needs deployment, use source-backed deployment through
   `xian-py` and do not introduce public RPC defaults.

## Contract Shape

Start from this structure and add only the exports the spec needs:

```python
OwnerChanged = LogEvent(
    "OwnerChanged",
    {
        "old_owner": {"type": str, "idx": True},
        "new_owner": {"type": str, "idx": True},
    },
)

owner = Variable()

@construct
def seed(initial_owner: str = ""):
    if initial_owner == "":
        owner.set(ctx.caller)
    else:
        owner.set(initial_owner)

def require_owner():
    assert ctx.caller == owner.get(), "Only owner"

@export
def transfer_ownership(new_owner: str):
    require_owner()
    assert new_owner != "", "Owner required"
    old_owner = owner.get()
    owner.set(new_owner)
    OwnerChanged({"old_owner": old_owner, "new_owner": new_owner})

@export
def get_owner() -> str:
    return owner.get()
```

Keep helper functions top-level and undecorated. Use `assert` for contract
guards. Prefer clear failure messages because users and bots will see them.

## Hard Rules To Apply While Writing

- Do not import ordinary Python stdlib modules. Runtime names such as
  `datetime`, `decimal`, `random`, `hashlib`, `crypto`, `importlib`, `now`,
  `block_num`, and `block_hash` are injected.
- Use only `@construct`, `@export`, or `@export(typecheck=True|False)`.
- Use at most one decorator per function and at most one `@construct`.
- Include at least one `@export`.
- Annotate every exported argument.
- Keep helper functions top-level. Do not write classes, async functions,
  lambdas, nested functions, `try`, `with`, generators, or `from ... import`.
- Do not use names that start or end with `_`.
- Do not use semicolons or one-line compound statements.
- Do not use `in` with `Hash`; read the key and compare with `None` or the
  configured default value.
- Do not pass `contract=` or `name=` to `Variable`, `Hash`, or `LogEvent`.
- Keep hash keys free of `:` and `.`, and keep return payloads small.

## State And Events

Use explicit storage declarations:

```python
counter = Variable(default_value=0)
balances = Hash(default_value=0)
metadata = Hash()
```

Use `ForeignVariable` and `ForeignHash` only for read-only state from another
contract. Use `importlib.import_module(...)` when you need to call another
contract export.

Prefer `LogEvent("Name", params)` with at most three indexed parameters:

```python
Transfer = LogEvent(
    "Transfer",
    {
        "from": {"type": str, "idx": True},
        "to": {"type": str, "idx": True},
        "amount": {"type": float},
    },
)
```

Emit every declared field and no extra fields:

```python
Transfer({"from": ctx.caller, "to": to, "amount": amount})
```

## Numbers, Time, And Randomness

- Use `float` for user-facing decimal amounts. Xian executes those values as
  deterministic decimal-backed values, not binary floating point.
- Use `now` for chain time. Do not call wall-clock APIs.
- On on-demand networks, time advances only when blocks are produced.
- Use `datetime.timedelta(...)` directly when needed; do not import
  `datetime`.
- Use `random.seed()` before deterministic random helpers, and only use them
  for low-stakes/game-like behavior. They are not secret randomness.

## Local Tests

For a standalone contract, generate a focused test around the public exports and
important invariants:

```python
from pathlib import Path

import pytest
from contracting.local import ContractingClient

CONTRACT = Path("contracts/con_example.s.py").read_text()

@pytest.fixture
def client():
    c = ContractingClient(signer="alice")
    c.submit(CONTRACT, name="con_example")
    return c

def test_owner_can_transfer_ownership(client):
    contract = client.get_contract_proxy("con_example")
    contract.transfer_ownership(new_owner="bob")
    assert contract.get_owner() == "bob"

def test_non_owner_rejected(client):
    contract = client.get_contract_proxy("con_example")
    with pytest.raises(AssertionError):
        contract.transfer_ownership(new_owner="mallory", signer="mallory")
```

When the contract calls another contract, submit a minimal dependency contract
in the fixture before submitting the contract under test.

## Deployment Snippet

Only add deployment code when the user asks for it. Use source-backed
deployment:

```python
from pathlib import Path

from xian_py import Wallet, Xian

wallet = Wallet("your_private_key")
xian = Xian("http://127.0.0.1:26657", wallet=wallet)
source = Path("contracts/con_example.s.py").read_text()

tx = xian.deploy_contract(
    name="con_example",
    source=source,
    args={"initial_owner": wallet.public_key},
    mode="checktx",
    wait_for_tx=True,
)
```

Do not hardcode public RPC endpoints or public chain IDs in examples.

## Final Checklist

Before handing back contract code:

- Check every exported argument is annotated with an allowed type.
- Check every storage declaration is explicit and module-level.
- Check all writes are permissioned or intentionally public.
- Check every external call has a clear trust/permission assumption.
- Check events match the fields consumers need.
- Check time logic is evaluated during transactions, not assumed to run in the
  background.
- Check the contract has local tests for success paths and rejected paths.
- Check source-backed deployment examples use `deploy_contract(...)`.

## Resources

- `references/contract-authoring-rules.md` - current Xian contract writing rules
  distilled from `xian-ai-guides/contracting-guide.md` and reconciled with the
  current `xian-contracting` linter/runtime.
- [xian-technology/xian-contracting](https://github.com/xian-technology/xian-contracting)
- [xian-technology/xian-contracts](https://github.com/xian-technology/xian-contracts)
- [xian-technology/xian-py](https://github.com/xian-technology/xian-py)
