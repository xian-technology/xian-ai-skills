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
```

## Core Model

Xian node operations are split across:

- `xian-cli` for operator workflows and node profiles
- `xian-stack` for the runtime backend and Docker services
- canonical network manifests for pinned release images and network metadata

Default production posture:

- canonical networks use manifest-pinned registry images
- development/private networks can opt into `local_build`

## Quick Reference

```bash
# Join a canonical network
uv run xian network join validator-1 --network mainnet --moniker "validator-1"

# Start and inspect
uv run xian node start validator-1
uv run xian node status validator-1
uv run xian node endpoints validator-1
uv run xian node health validator-1

# Stop
uv run xian node stop validator-1
```

## Join Mainnet or Testnet

### Validator Example

```bash
uv run xian network join validator-1 \
  --network mainnet \
  --moniker "validator-1"

uv run xian node start validator-1
uv run xian node status validator-1
uv run xian node endpoints validator-1
```

### Service Node Example

```bash
uv run xian network join service-1 \
  --network mainnet \
  --moniker "service-1" \
  --service-node \
  --enable-dashboard \
  --enable-monitoring

uv run xian node start service-1
uv run xian node health service-1
```

## Local Build Override

Use this when you explicitly want the local checked-out repos instead of the
published canonical image.

```bash
uv run xian network join dev-validator \
  --network mainnet \
  --moniker "dev-validator" \
  --node-image-mode local_build
```

## New Network / Private Network

```bash
uv run xian network create localnet-1 \
  --chain-id xian-localnet-1 \
  --moniker "bootstrap-1" \
  --force

uv run xian node start localnet-1
```

Use `xian network create` when you need a new private network definition rather
than joining a canonical one.

## Optional Runtime Layers

The node profile can enable:

- `--service-node` for BDS/indexed reads
- `--enable-dashboard` for the explorer/dashboard service
- `--enable-monitoring` for Prometheus and Grafana
- `--enable-intentkit` for the optional `xian-intentkit` sidecar stack

Example:

```bash
uv run xian network join agent-node \
  --network mainnet \
  --service-node \
  --enable-dashboard \
  --enable-monitoring \
  --enable-intentkit
```

## What `node status` Should Tell You

The current status flow is richer than a simple process check. It should be the
first command you reach for.

```bash
uv run xian node status validator-1
```

Expect it to surface:

- profile/network identity
- runtime/backend reachability
- current image mode and image references
- manifest-derived release provenance when present
- dashboard / monitoring / intentkit reachability when enabled

## Endpoints and Health

```bash
uv run xian node endpoints validator-1
uv run xian node health validator-1
```

Use:

- `node endpoints` for local URLs
- `node health` for machine-readable checks
- `node status` for the operator summary

## Direct Stack Backend

Use the raw backend only when you are working directly in `xian-stack` and need
to bypass the higher-level CLI.

```bash
python3 ./scripts/backend.py start --no-service-node --no-dashboard --no-monitoring
python3 ./scripts/backend.py status --no-service-node --no-dashboard --no-monitoring
python3 ./scripts/backend.py endpoints --no-service-node --no-dashboard --no-monitoring
python3 ./scripts/backend.py health --no-service-node --no-dashboard --no-monitoring
python3 ./scripts/backend.py stop --no-service-node --no-dashboard --no-monitoring
```

## Operational Guidance

- Prefer canonical manifest-backed images for real networks.
- Use `local_build` only when you intentionally need unreleased local code.
- Use service-node mode when you need BDS, GraphQL, explorers, or indexed bot
  reads.
- Use the dashboard for human inspection, not as the only source of truth.
- Use `node health` and logs for automated checks and incident triage.

## Resources

- [xian-tech-cli on PyPI](https://pypi.org/project/xian-tech-cli/)
- [xian-technology/xian-cli](https://github.com/xian-technology/xian-cli)
- [xian-technology/xian-stack](https://github.com/xian-technology/xian-stack)
- [xian node docs](https://docs.xian.org/node/)
