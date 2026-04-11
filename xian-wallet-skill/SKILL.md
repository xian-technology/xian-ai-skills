---
name: xian-wallet
description: Work with Xian's current browser and mobile wallets. Use when implementing wallet UX, provider approvals, network settings, watched assets, contract-call flows, or shielded snapshot recovery behavior.
---

# Xian Wallet Skill

Use this skill for the current Xian wallet products.

## Current Wallet Surface

There are two active wallet surfaces:

- browser wallet: `xian-wallet-browser`
  - Manifest V3 extension
  - injected `window.xian` provider
  - `@xian-tech/wallet-core` reusable controller and custody logic
- mobile wallet: `xian-wallet-mobile`
  - React Native app
  - mobile-specific controller with storage semantics kept close to
    `wallet-core`

Treat them as sibling products with aligned wallet semantics, not as unrelated
implementations.

## What They Already Do

Current wallet capabilities include:

- wallet creation and import
- encrypted local seed/private-key storage
- network preset management with active RPC and dashboard URLs
- watched assets with configurable decimals
- direct token sends
- advanced contract-call flows
- shielded `state_snapshot` storage, export, removal, and inclusion in wallet
  backup exports
- indexed-history checks to detect stale shielded snapshots

They are still missing richer mainstream-wallet layers such as full transaction
history and portfolio views.

## Browser Wallet Model

The browser wallet is provider-first:

- dapps talk to `window.xian`
- the background worker holds custody
- approvals survive MV3 worker suspension
- approval UIs should lead with structured summaries before raw payloads

Important provider approval kinds:

- `xian_requestAccounts`
- `xian_signMessage`
- `xian_signTransaction`
- `xian_sendTransaction`
- `xian_sendCall`
- `xian_watchAsset`

If you change request semantics, update both the provider handling and the
approval summary/warning logic.

## Mobile Wallet Model

The mobile wallet is app-first:

- direct send flow for token `transfer`
- advanced transaction screen for generic contract calls
- network status badge that checks current RPC reachability
- explorer links built from the configured dashboard URL

If a feature needs arbitrary contract execution, the current product answer is
the advanced transaction flow, not a new one-off screen by default.

## Token Factory And Other Contract Actions

There is no dedicated token-factory UI today.

Use the generic contract-call path instead:

- mobile: Advanced Transaction screen
- browser: provider `xian_sendCall` / wallet approval flow

That is the current place for:

- token factory calls
- governance calls
- admin/operator flows
- any other contract interaction that is not yet a first-class wallet action

Do not pretend the wallet has a dedicated factory workflow if it does not.

## Amounts And Decimals

Current wallet amount behavior:

- direct send flow accepts both `.` and `,` as decimal separators in the UI
- the wallet normalizes `,` to `.`
- positive integers can be promoted to `bigint` when they exceed JS safe
  integer range
- watched assets store decimals as display metadata

Important distinction:

- wallet UI input is convenience parsing
- contract/runtime semantics still depend on the called function and token
  contract

So if the node/runtime expects a numeric value, do not confuse wallet parsing
convenience with protocol-level numeric formats.

## Network Settings

Wallets keep:

- active network preset id
- `rpcUrl`
- optional `dashboardUrl`
- optional expected `chainId`

Use:

- RPC for real wallet operations and liveness
- dashboard URL for human explorer links

If a user reports "Node unreachable," validate the RPC endpoint first. A valid
dashboard URL does not make the wallet operational by itself.

## Shielded Snapshot Recovery

The wallets now treat shielded backups as first-class state:

- save/import a `state_snapshot`
- export a stored snapshot
- remove a stored snapshot
- include stored snapshots in encrypted wallet backups
- check indexed history after a stored snapshot to detect staleness

The important user-facing truth is:

- seed-only recovery is not the same as shielded wallet recovery
- shielded note rediscovery still depends on indexed history or a saved
  `state_snapshot`

Any wallet UX around privacy should keep that distinction explicit.

## When To Add A First-Class Wallet Flow

Add a dedicated wallet screen or action only when at least one of these is
true:

- the flow is common enough that generic contract-call UX is no longer good
  enough
- the flow needs special validation or summaries to avoid user mistakes
- the flow depends on wallet-managed secrets or recovery state

Otherwise prefer:

- advanced transaction flow
- provider request approvals
- watched-asset metadata updates

## Implementation Guidance

- keep browser and mobile backup/snapshot semantics aligned
- keep network preset semantics aligned
- prefer adding reusable logic in `wallet-core` or a wallet controller layer
  before duplicating UI-specific logic
- when changing approval semantics, review the structured approval copy and
  warnings, not just the request transport
- when changing privacy flows, review snapshot export/import and stale-history
  checks at the same time

## Validation

Use the repo-native checks for the affected wallet:

```bash
# Browser wallet
npm run test:browser --workspace xian-wallet-extension
npm run test:visual --workspace xian-wallet-extension

# Mobile wallet
npm test
```
