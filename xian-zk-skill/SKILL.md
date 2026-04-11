---
name: xian-zk
description: Build against Xian's current shielded-note privacy stack. Use when working on shielded-note-token flows, proof generation, shielded wallets, relayers, or privacy-token operational constraints.
---

# Xian ZK Skill

Use this skill for the current Xian shielded-note stack.

## Core Model

- Xian privacy is note-based, not "private balances per public address."
- The production-facing primitive is `shielded-note-token`, with:
  - public deposit into shielded notes
  - shielded transfer between note owners
  - public withdraw back to a visible address
- Recipients are identified by `owner_public`, derived from a private owner
  secret.
- Viewing keys are separate from spend authority. A wallet can disclose note
  contents without disclosing the spend key.
- The same token can still expose public balances for deposit/withdraw and for
  integrations that operate on the token's public side.

## Main Components

- `xian-contracts/contracts/shielded-note-token`
- `xian-contracting/packages/xian-zk`
- `zk_registry` for registry-backed verifying-key lookup
- browser and mobile wallet shielded flows
- `xian-stack` shielded relayer for proof-bound private submission

## Default Workflow

1. Create or restore a `ShieldedWallet` for the token's `asset_id`.
2. Sync wallet note state from `shielded_wallet_history` or indexed fallbacks.
3. Build a deposit / transfer / withdraw request from wallet state.
4. Produce proofs locally or through the trusted local prover service.
5. Submit directly to the node or through the shielded relayer.
6. Persist an updated `state_snapshot` after the wallet catches up.

## Key APIs

Important `xian-zk` surface:

- `asset_id_for_contract(contract_name)`
- `ShieldedWallet.generate(asset_id)`
- `ShieldedWallet.from_parts(...)`
- `ShieldedWallet.from_json(snapshot_json)`
- `ShieldedWallet.from_seed_json(seed_json)`
- `ShieldedWallet.sync_records(records)`
- `ShieldedWallet.build_deposit(...)`
- `ShieldedWallet.build_transfer(...)`
- `ShieldedWallet.build_withdraw(...)`
- `ShieldedWallet.to_json()`
- `ShieldedWallet.export_seed_json()`
- `ShieldedNoteProverClient(...)`
- `ShieldedCommandProverClient(...)`
- `ShieldedRelayTransferProverClient(...)`
- `payload_discovery_tags(payload_hex)`

## Submission Modes

### Direct Submission

Use direct node submission when you care mainly about correctness and local
testing.

Tradeoff:

- the chain verifies the proof
- but the submitting node / network path can still observe transaction origin

### Relayed Submission

Use the stack-managed shielded relayer when you want proof-bound submission
without the wallet directly posting the transaction.

Tradeoff:

- improves network-origin privacy posture
- but the relayer is an operator service with its own policy, rate limits, and
  logging/retention posture

## Recovery And Availability

Two backup artifacts matter:

- `seed_backup`: minimal long-term secret material
- `state_snapshot`: rich resume artifact with synced wallet state

These are not interchangeable.

If you only keep the seed, the wallet still needs indexed historical data to
rediscover old notes. Export `state_snapshot` regularly for user-level
recovery, and keep BDS snapshot export/import operational at the network side.

## Constraints You Should Not Hand-Wave

- `ShieldedNoteProver.build_insecure_dev_bundle()` is for local tests only.
- `build_random_bundle(...)` is a single-party random setup, not an MPC
  ceremony.
- `xian-zk-prover-service` is a trusted local proving companion. It improves
  deployability but still sees witness material.
- zk correctness does not depend on BDS, but wallet recovery and note
  rediscovery do depend on indexed history or an equivalent recovery feed.

## Implementation Guidance

- Prefer the protocol-shaped `shielded_wallet_history` feed for wallet sync.
- Keep wallet logic responsible for note selection and snapshot persistence.
- Keep contracts responsible for proof verification, root/nullifier checks, and
  deterministic state advancement.
- Be explicit about privacy guarantees. Shielded transfers hide note values and
  recipients at the proof layer, but they do not automatically hide network
  origin or all metadata.

## Validation

When you need end-to-end coverage, prefer the stack harnesses instead of
isolated contract tests:

```bash
make -C xian-stack localnet-e2e
```
