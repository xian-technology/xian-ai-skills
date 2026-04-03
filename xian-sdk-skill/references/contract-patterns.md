# Xian Contract Patterns

Current contract snippets for Xian smart contracts written in Python.

## Table of Contents

- [Basic Token](#basic-token)
- [Access Control](#access-control)
- [Pausable Contract](#pausable-contract)
- [Upgradeable Router Pattern](#upgradeable-router-pattern)
- [State Patterns](#state-patterns)
- [Event Logging](#event-logging)
- [Time-based Logic](#time-based-logic)

## Basic Token

```python
Transfer = LogEvent(
    event="Transfer",
    params={
        "from": {"type": str, "idx": True},
        "to": {"type": str, "idx": True},
        "amount": {"type": (int, float, decimal)},
    },
)

balances = Hash(default_value=0)
approvals = Hash(default_value=0)
metadata = Hash()

@construct
def seed():
    metadata["token_name"] = "My Token"
    metadata["token_symbol"] = "MTK"
    metadata["operator"] = ctx.caller
    balances[ctx.caller] = 1_000_000

@export
def transfer(amount: float, to: str):
    assert amount > 0, "Amount must be positive"
    assert balances[ctx.caller] >= amount, "Insufficient balance"
    balances[ctx.caller] -= amount
    balances[to] += amount
    Transfer({"from": ctx.caller, "to": to, "amount": amount})

@export
def approve(amount: float, to: str):
    assert amount >= 0, "Cannot approve negative balances"
    approvals[ctx.caller, to] = amount

@export
def transfer_from(amount: float, to: str, main_account: str):
    assert amount > 0, "Amount must be positive"
    assert approvals[main_account, ctx.caller] >= amount, "Not approved"
    assert balances[main_account] >= amount, "Insufficient balance"
    approvals[main_account, ctx.caller] -= amount
    balances[main_account] -= amount
    balances[to] += amount
    Transfer({"from": main_account, "to": to, "amount": amount})

@export
def balance_of(address: str) -> float:
    return balances[address]
```

## Access Control

```python
owner = Variable()

@construct
def seed():
    owner.set(ctx.caller)

def only_owner():
    assert ctx.caller == owner.get(), "Only owner"

@export
def transfer_ownership(new_owner: str):
    only_owner()
    owner.set(new_owner)
```

## Pausable Contract

```python
paused = Variable(default_value=False)
owner = Variable()

@construct
def seed():
    owner.set(ctx.caller)

def only_owner():
    assert ctx.caller == owner.get(), "Only owner"

def when_not_paused():
    assert not paused.get(), "Contract is paused"

@export
def pause():
    only_owner()
    paused.set(True)

@export
def unpause():
    only_owner()
    paused.set(False)
```

## Upgradeable Router Pattern

Use an explicit router/forwarder contract instead of mutating code in place.

```python
implementation = Variable()
owner = Variable()

@construct
def seed(impl_contract: str):
    implementation.set(impl_contract)
    owner.set(ctx.caller)

@export
def upgrade(new_impl: str):
    assert ctx.caller == owner.get(), "Only owner"
    implementation.set(new_impl)

@export
def execute(function: str, kwargs: dict):
    impl = importlib.import_module(implementation.get())
    assert importlib.has_export(impl, function), "Missing export"
    return importlib.call(impl, function, kwargs)
```

## State Patterns

### Mapping with Default

```python
balances = Hash(default_value=0)
```

### Nested Mapping

```python
allowances = Hash(default_value=0)

allowances[owner, spender] = 100
allowed = allowances[owner, spender]
```

### Mutable Variable Helpers

```python
settings = Variable(default_value={})
queue = Variable(default_value=[])

@export
def configure(mode: str):
    settings["mode"] = mode

@export
def enqueue(item: str):
    queue.append(item)
```

## Event Logging

Use `LogEvent`, not a returned dict payload.

```python
Action = LogEvent(
    event="Action",
    params={
        "actor": {"type": str, "idx": True},
        "value": {"type": int},
    },
)

@export
def do_work(value: int):
    Action({"actor": ctx.caller, "value": value})
```

## Time-based Logic

Use `now`, not `datetime.datetime.now()`.

```python
import datetime

lock_until = Hash()

@export
def lock(days: int):
    lock_until[ctx.caller] = now + datetime.timedelta(days=days)

@export
def unlock():
    assert now >= lock_until[ctx.caller], "Still locked"
```
