---
name: xian-node
description: Operate current Xian nodes with xian-tech-cli and xian-stack. Use when joining canonical networks, creating private networks, running validators or service nodes, and inspecting runtime health.
---

# Xian Node Skill

Use this skill for the current Xian operator flow.

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
- canonical network manifests for pinned release images and network metadata
- `xian-abci` for deterministic node-home/config rendering

Default production posture:

- canonical networks use manifest-pinned registry images
- development/private networks can opt into `local_build`
- Python package workflows use uv. Do not introduce Poetry, Pipenv, or
  manually-managed virtualenv instructions.

## Quick Reference

```bash
# Join a canonical network
xian network join validator-1 \
  --network mainnet \
  --template embedded-backend \
  --moniker "validator-1" \
  --generate-validator-key \
  --init-node \
  --restore-snapshot

# Start and inspect
xian node start validator-1
xian node status validator-1
xian node endpoints validator-1
xian node health validator-1

# Stop
xian node stop validator-1
```

## Join Mainnet or Testnet

Generate standalone validator material through the CLI when you need explicit
key custody before creating a profile:

```bash
xian keys validator generate --out-dir ./keys/validator-1
```

### Validator Example

```bash
xian network join validator-1 \
  --network mainnet \
  --template embedded-backend \
  --moniker "validator-1" \
  --generate-validator-key \
  --init-node \
  --restore-snapshot

xian node start validator-1
xian node status validator-1
xian node endpoints validator-1
```

### Service Node Example

```bash
xian network join service-1 \
  --network mainnet \
  --template embedded-backend \
  --moniker "service-1" \
  --service-node \
  --enable-dashboard \
  --enable-monitoring \
  --init-node \
  --restore-snapshot

xian node start service-1
xian node health service-1
```

## Local Build Override

Use this when you explicitly want the local checked-out repos instead of the
published canonical image.

```bash
xian network join dev-validator \
  --network mainnet \
  --template embedded-backend \
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
  --generate-validator-key \
  --init-node

xian node start localnet-1
xian node status localnet-1
```

Use `xian network create` when you need a new private network definition rather
than joining a canonical one.

## Optional Runtime Layers

The node profile can enable:

- `--service-node` for BDS/indexed reads
- `--enable-dashboard` for the explorer/dashboard service
- `--enable-monitoring` for Prometheus and Grafana
- `--enable-intentkit` for the optional `xian-intentkit` sidecar stack
- `--enable-dex-automation` for the optional deterministic DEX automation
  sidecar

Example:

```bash
xian network join agent-node \
  --network mainnet \
  --template embedded-backend \
  --service-node \
  --enable-dashboard \
  --enable-monitoring \
  --enable-intentkit \
  --enable-dex-automation \
  --init-node \
  --restore-snapshot
```

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

## Endpoints and Health

```bash
xian node endpoints validator-1
xian node health validator-1
```

Use:

- `node endpoints` for local URLs
- `node health` for machine-readable checks
- `node status` for the operator summary

## Direct Stack Backend

Use the raw backend only when you are working directly in `xian-stack` and need
to bypass the higher-level CLI. For operator workflows, use `xian-cli`.

```bash
uv run python ./scripts/backend.py start --no-service-node --no-dashboard --no-monitoring
uv run python ./scripts/backend.py status --no-service-node --no-dashboard --no-monitoring
uv run python ./scripts/backend.py endpoints --no-service-node --no-dashboard --no-monitoring
uv run python ./scripts/backend.py health --no-service-node --no-dashboard --no-monitoring
uv run python ./scripts/backend.py stop --no-service-node --no-dashboard --no-monitoring
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
uv run python ./scripts/backend.py localnet-status --timeout-seconds 2
make localnet-down
```

For product-level validation, use the heavier harnesses:

```bash
make localnet-e2e
make localnet-vm-e2e
make localnet-vm-report
make localnet-validator-governance
```

`localnet-e2e` and `localnet-vm-e2e` are stronger signals than "five nodes
started" because they exercise contracts, indexing, governance, restart
convergence, and VM rollout behavior.

## Operational Guidance

- Prefer canonical manifest-backed images for real networks.
- Use `local_build` only when you intentionally need unreleased local code.
- Use service-node mode when you need BDS, GraphQL, explorers, or indexed bot
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
