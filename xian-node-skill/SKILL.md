---
name: xian-node
description: Operate current Xian nodes with xian-tech-cli and xian-stack. Use when creating or joining manifest-backed networks, running validator or indexed/BDS profiles, managing optional sidecars, and inspecting runtime health.
---

# Xian Node Skill

Use this skill for the current Xian operator flow. The current implementation is
manifest/profile driven: `xian network create` and `xian network join` write
operator artifacts, `xian node init` materializes the CometBFT home, and
`xian node start|stop|status|health|endpoints` delegates runtime work to
`xian-stack`.

Important packaging detail:

- install package: `xian-tech-cli`
- command name: `xian`

## Installation

```bash
uv tool install xian-tech-cli
xian --help
```

When you are working from a sibling source checkout instead of an installed
release, keep the uv project boundary explicit:

```bash
uv run --project /path/to/xian-cli xian --help
```

## Core Model

Xian node operations are split across:

- `xian-cli` for operator workflows and node profiles
- `xian-stack` for the runtime backend and Docker services
- `xian-configs` network manifests and templates for pinned release images,
  release provenance, default services, and network metadata
- `xian-abci` for deterministic node-home/config rendering

Default production posture:

- canonical networks use manifest-pinned registry images
- development/private networks default to or can opt into `local_build`
- templates prefill profile defaults; explicit CLI flags override templates
- Python package workflows use uv. Do not introduce Poetry, Pipenv, or
  manually-managed virtualenv instructions.
- `--restore-snapshot` is only valid when a snapshot URL is configured on the
  network/profile or passed with `--snapshot-url`.

## Quick Reference

```bash
# Inspect current templates and generate validator key material
xian network template list
xian keys validator generate --out-dir ./keys/validator-1

# Join a manifest-backed network
xian network join validator-1 \
  --network testnet \
  --template consortium-5 \
  --moniker "validator-1" \
  --validator-key-ref ./keys/validator-1/validator_key_info.json \
  --init-node

# Start and inspect
xian node start validator-1
xian node status validator-1
xian node endpoints validator-1
xian node health validator-1
xian doctor validator-1

# Stop
xian node stop validator-1
```

Use the network names that are present in the operator's `xian-configs`
checkout or passed via `--network-manifest`. Current examples use `testnet` and
`devnet`; replace them with `mainnet` only when that manifest exists in the
active configs source.

## Join A Manifest-Backed Network

Generate standalone validator material through the CLI when you need explicit
key custody before creating a profile:

```bash
xian keys validator generate --out-dir ./keys/validator-1
```

### Validator Example

```bash
xian network join validator-1 \
  --network testnet \
  --template consortium-5 \
  --moniker "validator-1" \
  --validator-key-ref ./keys/validator-1/validator_key_info.json \
  --stack-dir ../xian-stack \
  --init-node

xian node start validator-1
xian node status validator-1
xian node endpoints validator-1
```

### BDS Node Example

```bash
xian network join bds-1 \
  --network testnet \
  --template single-node-indexed \
  --moniker "bds-1" \
  --enable-bds \
  --enable-dashboard \
  --enable-monitoring \
  --stack-dir ../xian-stack \
  --init-node

xian node start bds-1
xian node health bds-1
```

If a profile should bootstrap from a signed or trusted snapshot, pass the
snapshot explicitly or rely on one in the manifest/profile:

```bash
xian network join validator-1 \
  --network testnet \
  --template consortium-5 \
  --validator-key-ref ./keys/validator-1/validator_key_info.json \
  --snapshot-url https://example.invalid/xian-snapshot.tar.gz \
  --snapshot-signing-key REPLACE_WITH_TRUSTED_ED25519_PUBLIC_KEY \
  --init-node \
  --restore-snapshot
```

## Local Build Override

Use this when you explicitly want the local checked-out repos instead of the
published canonical image.

```bash
xian network join dev-validator \
  --network testnet \
  --template consortium-5 \
  --moniker "dev-validator" \
  --node-image-mode local_build \
  --generate-validator-key \
  --init-node
```

## New Network / Private Network

```bash
xian network template list
xian network create localnet-1 \
  --chain-id xian-localnet-1 \
  --template single-node-dev \
  --bootstrap-node localnet-1 \
  --generate-validator-key \
  --init-node

xian node start localnet-1
xian node status localnet-1
```

Use `xian network create` when you need a new private network definition rather
than joining a canonical one.

## Optional Runtime Layers

The node profile can enable:

- `--enable-bds` for BDS/indexed reads
- `--enable-dashboard` for the explorer/dashboard service
- `--enable-monitoring` for Prometheus and Grafana
- `--enable-intentkit` for the optional `xian-intentkit` sidecar stack
- `--enable-dex-automation` for the optional deterministic DEX automation
  sidecar

Example:

```bash
xian network join agent-node \
  --network testnet \
  --template single-node-indexed \
  --enable-bds \
  --enable-dashboard \
  --enable-monitoring \
  --enable-intentkit \
  --enable-dex-automation \
  --init-node
```

Runtime tuning that belongs in the profile is also exposed here:

- `--enable-pruning` / `--blocks-to-keep`
- `--simulation-enabled`, `--simulation-max-concurrency`,
  `--simulation-timeout-ms`, and `--simulation-max-chi`
- `--parallel-execution-enabled`, `--parallel-execution-workers`, and
  `--parallel-execution-min-transactions`
- `--app-log-level`, `--app-log-json`, `--app-log-rotation-hours`, and
  `--app-log-retention-days`

## What `node status` Should Tell You

The current status flow is richer than a simple process check. It should be the
first command you reach for.

```bash
xian node status validator-1
```

Expect it to surface:

- profile/network identity
- runtime/backend reachability
- current image mode and image references
- manifest-derived release provenance when present
- dashboard / monitoring / intentkit reachability when enabled
- BDS, DEX automation, and other optional sidecar reachability when enabled
- effective snapshot and node-home initialization posture
- latest block age so stalled nodes are visible even when RPC responds

## Endpoints and Health

```bash
xian node endpoints validator-1
xian node health validator-1
```

Use:

- `node endpoints` for local URLs
- `node health` for machine-readable live checks
- `node status` for the operator summary
- `doctor` for broader workspace, profile, live-health, and recovery preflight

```bash
xian doctor validator-1
xian doctor validator-1 --skip-live-checks
xian snapshot restore validator-1
```

Only run `snapshot restore` when the effective network/profile has a snapshot
URL or you pass one explicitly.

## Direct Stack Backend

Use the raw backend only when you are working directly in `xian-stack` and need
to bypass the higher-level CLI. For operator workflows, use `xian-cli`. The CLI
uses `--enable-bds`; the raw backend uses `--bds-enabled`.

```bash
python3 ./scripts/backend.py start --no-bds-enabled --no-dashboard --no-monitoring
python3 ./scripts/backend.py status --no-bds-enabled --no-dashboard --no-monitoring
python3 ./scripts/backend.py endpoints --no-bds-enabled --no-dashboard --no-monitoring
python3 ./scripts/backend.py health --no-bds-enabled --no-dashboard --no-monitoring
python3 ./scripts/backend.py stop --no-bds-enabled --no-dashboard --no-monitoring
```

The CLI talks to the backend through the structured request contract
(`--request-json`). Do not duplicate CLI flag-to-backend translation in new
callers; either call the CLI or send the backend request object.

## Low-Level Config API

When changing node config rendering in `xian-abci` or `xian-stack`, use
`NodeConfigOptions` as the only ABCI config API:

```python
from xian.node_setup import NodeConfigOptions, render_node_configs

configs = render_node_configs(options=NodeConfigOptions(moniker="node-0"))
```

Do not add legacy keyword wrappers around `render_node_configs`,
`render_cometbft_config`, or `render_xian_config`.

## Localnet Validation

For a clean five-node topology smoke in `xian-stack`:

```bash
LOCALNET_NODES=5 make localnet-init localnet-build localnet-up
python3 ./scripts/backend.py localnet-status --timeout-seconds 2
make localnet-down
```

For product-level validation, use the heavier harnesses:

```bash
make localnet-e2e
make localnet-parallel-e2e
make localnet-node-report
make localnet-validator-governance
```

`localnet-e2e` and `localnet-parallel-e2e` are stronger signals than "five nodes
started" because they exercise contracts, indexing, governance, restart
convergence, and runtime-report behavior.

## Operational Guidance

- Prefer canonical manifest-backed images for real networks.
- Use `local_build` only when you intentionally need unreleased local code.
- Use BDS-enabled nodes when you need BDS, GraphQL, explorers, or indexed bot
  reads.
- Use the dashboard for human inspection, not as the only source of truth.
- Use `node health` and logs for automated checks and incident triage.
- Treat `.localnet/network.json` and generated validator keys as disposable
  local development material unless they were created explicitly for
  production custody.

## Resources

- [xian-tech-cli on PyPI](https://pypi.org/project/xian-tech-cli/)
- [xian-technology/xian-cli](https://github.com/xian-technology/xian-cli)
- [xian-technology/xian-stack](https://github.com/xian-technology/xian-stack)
- [xian node docs](https://docs.xian.org/node/)
