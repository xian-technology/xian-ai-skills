---
name: xian-governance
description: Work with Xian's current validator governance and operator lifecycle. Use when changing membership flows, delegation behavior, governance/state-patch actions, evidence handling, or the localnet protocol-safety harness.
---

# Xian Governance Skill

Use this skill for the current Xian validator-governance and operator surface.

## Core Split

Treat governance work as a split responsibility:

- `xian-cli` is the human-facing operator control plane
- `xian-stack` is the runtime/backend and localnet harness layer
- on-chain validator/governance contracts define the actual policy and state

Do not collapse these into one concern when diagnosing issues. A broken operator
flow, a broken backend harness, and a broken contract policy are different
problems.

## When To Use This Skill

Use this skill when work touches any of these areas:

- validator membership add/remove/re-register flows
- delegation, undelegation, unbonding, and claim behavior
- governance proposal and voting lifecycle
- governance state-patch approval, scheduling, and activation
- `auto_top_n` or validator selection policy
- hybrid approval gating
- jailing, unjailing, slashing, or evidence submission
- localnet governance validation in `xian-stack`
- operator lifecycle UX in `xian-cli`

## Operator Control Plane

The current operator-facing workflow lives in `xian-cli`.

Important commands include:

- `xian network join`
- `xian node start`
- `xian node stop`
- `xian node status`
- `xian snapshot restore`
- `xian recovery validate` / `xian recovery apply`
- `xian doctor`

Use `xian-cli` when the task is about what an operator should do. Do not send
users to ad hoc container commands or Make targets if the CLI already owns that
flow.

For local source-tree work, keep uv explicit:

```bash
uv run --project /path/to/xian-cli xian node status <profile>
uv run --project /path/to/xian-cli xian doctor <profile>
```

For installed operator flows, use the installed console command:

```bash
xian node status <profile>
xian doctor <profile>
```

## Protocol Safety Validation Harness

For live validator/delegation/governance validation, prefer the focused
`xian-stack` harness instead of piecemeal manual testing:

```bash
make localnet-protocol-safety
```

This exercises a real 5-validator localnet whose genesis comes from the
`testnet` contract bundle in `xian-configs`
(`LOCALNET_PROTOCOL_SAFETY_GENESIS_NETWORK`).

## Contract Surface

On-chain policy lives in the `xian-configs` system contracts:

- `validators`: membership, bonding and votes. Proposals go through
  `propose_vote(type_of_vote, arg)`, `vote(...)` and `expire_vote(...)`.
  Vote types are `add_member`, `remove_member`, `jail_member`,
  `unjail_member`, `slash_member`, `set_member_power`,
  `change_registration_fee`, `chi_cost_change`, `change_types`,
  `update_policy`, `reward_change`, `dao_payout` and `topic_vote`.
  Operators use `register`, `update_registration`, `announce_leave`, `leave`,
  `bond_self`/`unbond_self`, `delegate`/`undelegate` and `claim_unbond`; reads
  include `get_active_validators`, `get_validator`, `get_policy_config` and
  `get_pending_candidates`.
- `governance`: state patches and governed contract calls
  (`propose_state_patch`, `propose_contract_call`, `vote`, `get_patch`,
  `is_patch_approved`).
- `rewards`, `chi_cost`, `dao`: reward split, chi price and DAO treasury,
  changed only through `validators` votes.

Neither contract code nor a governed state patch can change the protected
`__execution_policy` record. The fee policy (`__fee_policy`: fee mode and chi
caps) is set in genesis and is outside every contract's writable namespace.

The backend command surface also exposes the same flow through
`localnet-protocol-safety` with explicit flags such as:

- `--seed`
- `--nodes`
- `--port-offset`
- `--topology`
- `--genesis-network`
- `--log-level`
- `--rpc-timeout-seconds`
- `--bootstrap`
- `--build`

Prefer the Make target unless you specifically need backend-level overrides.
The Make target already invokes the required uv-backed Python projects for the
sibling workspace. `localnet-validator-governance` is retained only as a
`scripts/backend.py` subcommand alias for older callers; there is no Make target
with that name.

## What The Harness Covers

The protocol-safety runner is the default validation path when changing:

- governance proposal and voting behavior
- governance state-patch lifecycle
- validator membership changes
- self-bonding and delegation flows
- unbond and claim timing
- validator-set rebalance rules
- leave/announce-leave behavior
- jailing, slashing, and unjailing
- real CometBFT `DUPLICATE_VOTE` evidence handling

If your change affects these areas and you did not run the focused
protocol-safety runner, your validation is probably incomplete.

## Artifacts And Local Keys

The local protocol-safety runner writes artifacts under:

- `.artifacts/localnet-protocol-safety/<run-id>/`

It also relies on localnet validator key material in:

- `.localnet/network.json`

Treat those keys as disposable dev material only. Do not document them or
handle them like production credentials.

## Implementation Guidance

- keep `xian-cli` as the operator-facing source of truth
- keep `xian-stack` scripts/backend machine-facing and deterministic
- when changing validator policy, verify both contract semantics and runner
  expectations
- V2 reward-split proposals require four nonnegative numbers whose exact sum
  is one. For generic Python SDK arguments use values such as
  `[Decimal("0.7"), 0, 0, Decimal("0.3")]` with `from decimal import Decimal`.
  A generic JSON tool must encode each decimal as a `__fixed__` wrapper.
- when changing operator lifecycle behavior, check that `xian node status`
  still reports a coherent local/runtime/live picture
- when changing governance state patches, validate approval, scheduling, and
  activation, not just proposal creation
- when changing evidence handling, test actual end-to-end consequence on
  validator state

## Validation

Use the focused governance runner for governance-specific end-to-end changes:

```bash
make localnet-protocol-safety
```

For broader stack changes that might affect validator behavior indirectly, run
the full localnet harnesses as well:

```bash
make localnet-e2e
make localnet-node-report
```

`localnet-e2e` writes artifacts under:

- `.artifacts/localnet-e2e/<run-id>/`

`localnet-protocol-safety` writes artifacts under:

- `.artifacts/localnet-protocol-safety/<run-id>/`

For operator lifecycle work, also check the CLI surface directly:

```bash
xian node status <profile>
xian doctor <profile>
```

For release-grade stack validation, use:

```bash
make release-safety
```
