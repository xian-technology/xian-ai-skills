---
name: xian-governance
description: Work with Xian's current validator governance and operator lifecycle. Use when changing membership flows, delegation behavior, governance/state-patch actions, evidence handling, or the localnet validator-governance harness.
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
- `xian doctor`

Use `xian-cli` when the task is about what an operator should do. Do not send
users to ad hoc container commands or Make targets if the CLI already owns that
flow.

## Governance Validation Harness

For live validator/delegation/governance validation, prefer the focused
`xian-stack` harness instead of piecemeal manual testing:

```bash
make localnet-validator-governance
```

This exercises a real 5-validator localnet seeded from canonical `testnet`
configuration.

The backend command surface also exposes the same flow through
`localnet-validator-governance` with explicit flags such as:

- `--seed`
- `--nodes`
- `--port-offset`
- `--topology`
- `--genesis-network`
- `--tracer-mode`
- `--rpc-timeout-seconds`
- `--bootstrap`
- `--build`

Prefer the Make target unless you specifically need backend-level overrides.

## What The Harness Covers

The validator-governance runner is the default validation path when changing:

- governance proposal and voting behavior
- governance state-patch lifecycle
- validator membership changes
- self-bonding and delegation flows
- unbond and claim timing
- validator-set rebalance rules
- leave/announce-leave behavior
- jailing, slashing, and unjailing
- real CometBFT `DUPLICATE_VOTE` evidence handling

If your change affects these areas and you did not run the focused governance
runner, your validation is probably incomplete.

## Artifacts And Local Keys

The local governance runner writes artifacts under:

- `.artifacts/localnet-validator-governance/<run-id>/`

It also relies on localnet validator key material in:

- `.localnet/network.json`

Treat those keys as disposable dev material only. Do not document them or
handle them like production credentials.

## Implementation Guidance

- keep `xian-cli` as the operator-facing source of truth
- keep `xian-stack` scripts/backend machine-facing and deterministic
- when changing validator policy, verify both contract semantics and runner
  expectations
- when changing operator lifecycle behavior, check that `xian node status`
  still reports a coherent local/runtime/live picture
- when changing governance state patches, validate approval, scheduling, and
  activation, not just proposal creation
- when changing evidence handling, test actual end-to-end consequence on
  validator state

## Validation

Use the focused governance runner for end-to-end changes:

```bash
make localnet-validator-governance
```

For operator lifecycle work, also check the CLI surface directly:

```bash
xian node status
xian doctor
```
