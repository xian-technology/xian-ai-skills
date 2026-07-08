# Xian Contract Authoring Rules

Use this reference when writing new Xian contract source. It is distilled from
`xian-ai-guides/contracting-guide.md` and checked against the current
`xian-contracting` linter/runtime.

## Table Of Contents

- [Execution Model](#execution-model)
- [Language Subset](#language-subset)
- [Runtime Names](#runtime-names)
- [Decorators And Annotations](#decorators-and-annotations)
- [Storage](#storage)
- [Events](#events)
- [Cross-Contract Calls](#cross-contract-calls)
- [Numbers](#numbers)
- [Time](#time)
- [Randomness](#randomness)
- [Limits And Metering](#limits-and-metering)
- [Patterns](#patterns)

## Execution Model

Xian contracts use a restricted Python subset. They are parsed, linted,
compiled, and executed by the node's pinned runtime. Write deterministic source:
no filesystem, network, wall-clock, process, reflection, or host-environment
behavior.

Current repos target Python 3.14+, but contract authors should not use general
new Python features unless the Xian linter/runtime explicitly allows them.

## Language Subset

Allowed in normal contract code:

- assignments and augmented assignments, except augmented `*`, `**`, `<<`, and
  `>>`
- arithmetic: `+`, `-`, `*`, `/`, `//`, `%`, `**`
- comparisons: `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`, `is`,
  `is not`
- boolean logic: `and`, `or`, `not`
- `if` / `elif` / `else`
- `for` and `while`
- `assert`
- top-level `def`
- `return`
- lists, dicts, tuples, list comprehensions, subscripts, and ordinary slices
- module-level `import some_contract` for non-stdlib modules

Forbidden or unsafe:

- `class`
- `async` / `await`
- `lambda`
- `try` / `except` / `finally`
- `with`
- `yield`, `yield from`, and generator expressions
- `from x import y`
- nested function definitions
- imports inside functions
- stdlib/builtin imports such as `os`, `sys`, `json`, `datetime`, `decimal`
- names that start or end with `_`
- semicolons
- one-line compound statements such as `if ok: return value`
- set literals and set comprehensions. The `set` and `frozenset` names are
  allowed, but `{1, 2}` and `{x for x in xs}` are rejected.

Allowed builtins include:

```text
Exception False None True abs all any ascii bin bool bytearray bytes chr dict
divmod filter float format frozenset hex int isinstance issubclass len list map
max min oct ord pow range reversed round set sorted str sum tuple zip
```

Treat everything outside that list as unavailable.

## Runtime Names

These names are injected and should be used directly:

- storage/runtime: `Variable`, `Hash`, `ForeignVariable`, `ForeignHash`,
  `LogEvent`, `ctx`, `Any`
- helper modules/values: `datetime`, `decimal`, `hashlib`, `crypto`, `random`,
  `importlib`, `now`, `block_num`, `block_hash`

`decimal` is the Xian deterministic decimal constructor, not the Python stdlib
module. `datetime` is a deterministic bridge with `datetime.datetime(...)`,
`datetime.timedelta(...)`, and unit constants such as `datetime.DAYS`.

Context fields commonly used in authored contracts:

- `ctx.caller`
- `ctx.signer`
- `ctx.this`
- `ctx.owner`
- `ctx.entry`
- `ctx.submission_name`

## Decorators And Annotations

Valid decorator forms:

- `@construct`
- `@export`
- `@export(typecheck=True)`
- `@export(typecheck=False)`

Rules:

- a contract needs at least one `@export`
- at most one `@construct`
- at most one decorator per function
- helper functions are top-level and undecorated
- every `@export` argument must be annotated
- return annotations are optional, but when present must use an allowed
  annotation type

Allowed annotation bases:

- `Any`
- `bool`
- `bytearray`
- `bytes`
- `datetime.datetime`
- `datetime.timedelta`
- `dict`
- `float`
- `frozenset`
- `int`
- `list`
- `set`
- `str`

Subscripted annotations are accepted when the base is allowed, such as
`list[int]` or `dict[str, int]`.

Use `float` for user-facing decimal quantities. Runtime values can encode more
types than the annotation surface; leave return annotations off when returning a
valid but awkward nested value.

## Storage

Declare storage explicitly at module level:

```python
counter = Variable(default_value=0)
balances = Hash(default_value=0)
settings = Hash()
```

Rules:

- `Variable`, `Hash`, `ForeignVariable`, `ForeignHash`, and `LogEvent` must be
  explicit module-level declarations.
- Tuple unpacking for ORM declarations is rejected.
- Do not pass `contract=` or `name=` to `Variable`, `Hash`, or `LogEvent`; the
  compiler/runtime injects them.
- `ForeignVariable` and `ForeignHash` are read-only.
- `Hash` supports at most 16 key dimensions.
- Hash key components must not contain `:` or `.`.
- The encoded hash key must be at most 1024 bytes.
- Hash slices are forbidden.
- `key in my_hash` is forbidden.
- Missing hash keys return the configured `default_value`, otherwise `None`.

Recommended existence pattern:

```python
pool = pools[pool_id]
assert pool is not None, "Missing pool"
```

Avoid:

```python
if pool_id in pools:
    ...
```

## Events

Prefer the positional `LogEvent("Name", params)` style:

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

`indexed(str)` is also present in current contracts, but the dict form makes the
indexing decision explicit and is easier for agents to modify safely.

Rules:

- at most three indexed parameters
- every declared parameter must be emitted
- no unexpected emitted parameters
- emitted values must match declared types
- each emitted value must be at most 1024 bytes once string-encoded

Allowed event value types are `str`, `int`, `float`, `bool`, and
decimal-backed values.

Emit events after state changes that consumers care about:

```python
Transfer({"from": ctx.caller, "to": to, "amount": amount})
```

## Cross-Contract Calls

For dynamic calls, use injected `importlib`:

```python
@export
def pay(token_name: str, to: str, amount: float):
    token = importlib.import_module(token_name)
    token.transfer(amount=amount, to=to)
```

Contract names imported with `importlib.import_module(...)` must be lowercase,
contain only alphanumeric characters or `_`, not start with `_`, and not be
digits-only.

Use `ForeignVariable` or `ForeignHash` when the contract only needs read-only
foreign state:

```python
currency_balances = ForeignHash(
    foreign_contract="currency",
    foreign_name="balances",
)
```

When trusting another contract's interface matters, enforce the shape before
calling:

```python
token = importlib.import_module("currency")
required = [
    importlib.Func("transfer", args=("amount", "to")),
    importlib.Var("balances", Hash),
]
assert importlib.enforce_interface(token, required)
```

## Numbers

Contract authors use `float` syntax for user-facing decimal values, but Xian
executes those as deterministic decimal-backed values.

```python
price = 10.5
fee = decimal("0.0025")
total = price + fee
```

Guidance:

- Do not model token amounts as integer base units unless the product
  specifically needs that.
- Avoid binary-floating-point assumptions.
- Keep arithmetic explicit and bounded.
- Validate positive amounts and sufficient balances before writes.

## Time

Use `now` for consensus block time:

```python
@export
def unlock():
    assert now >= unlock_time.get(), "Too early"
```

Rules and consequences:

- `now` is consensus block time, not validator wall-clock time.
- every transaction in the same block sees the same `now`
- on `on_demand` networks, time does not advance while the chain is idle
- time-based logic runs only when a transaction executes
- use `datetime.timedelta(...)` directly; do not `import datetime`

Avoid designs that assume autonomous background execution at a specific time.

## Randomness

Use deterministic random only for low-stakes or game-like logic:

```python
@export
def roll() -> int:
    random.seed()
    return random.randint(1, 6)
```

It is deterministic and predictable from public inputs. Do not use it for
security, lotteries with value, validator selection, or secret generation.

## Limits And Metering

Important current limits:

- recursion depth: 1024
- max hash dimensions: 16
- max hash key size: 1024 bytes
- max contract source submission size: 128 KiB
- max return value size: 128 KiB
- max sequence / binary allocation size: 128 KiB

Current byte costs:

- reads: 1 chi / byte
- writes: 25 chi / byte
- return values: 1 chi / byte

Practical guidance:

- keep keys compact
- avoid large return dicts and giant event fields
- avoid write-heavy loops over unbounded user-controlled data
- cache repeated reads into local variables and write once

## Patterns

### Permission Guard

```python
owner = Variable()

@construct
def seed():
    owner.set(ctx.caller)

def require_owner():
    assert ctx.caller == owner.get(), "Only owner"
```

### Efficient State Update

Prefer:

```python
sender = ctx.caller
balance = balances[sender]
assert balance >= amount, "Insufficient balance"
balances[sender] = balance - amount
```

over repeatedly reading/writing the same key.

### Time Lock

```python
unlock_at = Hash(default_value=None)

@export
def lock(days: int):
    assert days > 0, "Invalid duration"
    unlock_at[ctx.caller] = now + datetime.timedelta(days=days)

@export
def unlock():
    target = unlock_at[ctx.caller]
    assert target is not None, "Nothing locked"
    assert now >= target, "Too early"
    unlock_at[ctx.caller] = None
```

### Token-Like Transfer

```python
Transfer = LogEvent(
    "Transfer",
    {
        "from": {"type": str, "idx": True},
        "to": {"type": str, "idx": True},
        "amount": {"type": float},
    },
)

balances = Hash(default_value=0)

@export
def transfer(amount: float, to: str):
    assert amount > 0, "Amount must be positive"
    sender = ctx.caller
    sender_balance = balances[sender]
    assert sender_balance >= amount, "Insufficient balance"
    balances[sender] = sender_balance - amount
    balances[to] += amount
    Transfer({"from": sender, "to": to, "amount": amount})
```

## LLM Checklist

Before returning generated contract source:

1. Use injected runtime names directly; do not import stdlib helpers.
2. Ensure at least one `@export`.
3. Use at most one `@construct`.
4. Use at most one decorator per function.
5. Keep helper functions top-level.
6. Annotate every `@export` argument.
7. Keep return annotations within the allowed annotation bases or omit them.
8. Use `float` for user-facing decimal amounts.
9. Never rely on wall-clock time; use `now`.
10. Never use `in` on `Hash`.
11. Keep hash keys free of `:` and `.`.
12. Treat `ForeignVariable` and `ForeignHash` as read-only.
13. Keep return payloads, event values, and writes small.
14. Call `random.seed()` before deterministic random helpers.
15. Prefer explicit, flat, assert-driven logic over clever Python tricks.
