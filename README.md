# Xian AI Skills

AI-agent skills for the [Xian](https://xian.org) blockchain.

These skills are meant for coding agents such as Codex, Claude Code, and other
tooling that needs current Xian workflows instead of stale repo-era guidance.

## Skills

### [`xian-sdk-skill`](./xian-sdk-skill/)

Build applications on Xian with the current Python SDK.

- install with `xian-tech-py`
- use current `xian_py` imports
- submit transactions, estimate chi, simulate calls, deploy contracts
- read indexed blocks, transactions, events, and state history
- build wallets, bots, and service integrations

### [`xian-node-skill`](./xian-node-skill/)

Operate Xian nodes with the current CLI and stack model.

- install with `xian-tech-cli`
- join canonical networks with manifest-pinned images
- run validators and service nodes
- start optional dashboard, monitoring, and `xian-intentkit`
- inspect health, endpoints, and runtime provenance

### [`xian-dex-skill`](./xian-dex-skill/)

Work with the current Xian DEX contracts.

- quote trades through `con_dex`
- use `con_dex_helper` for single-pair buy and sell flows
- use direct router calls for multi-hop swaps and liquidity management
- inspect DEX events through indexed reads
- build autonomous polling-based trading workflows safely

### [`xian-zk-skill`](./xian-zk-skill/)

Work with the current Xian shielded-note privacy stack.

- use the current `shielded-note-token` deposit / transfer / withdraw model
- use `xian-zk` wallet, proving, and snapshot APIs correctly
- understand relayer vs direct submission tradeoffs
- keep `state_snapshot` backups and indexed-history requirements straight

### [`xian-bds-skill`](./xian-bds-skill/)

Use Xian's indexed/BDS read surface and recovery model correctly.

- read indexed blocks, txs, events, and state history
- use the `shielded_wallet_history` feed for wallet sync
- understand what depends on BDS and what does not
- use standardized `xian-stack` BDS snapshot export/import for recovery

### [`xian-wallet-skill`](./xian-wallet-skill/)

Work with the current Xian browser and mobile wallets.

- understand current browser extension and mobile wallet responsibilities
- use advanced contract-call flows for token factory and other contract actions
- handle asset decimals, amount entry, and explorer/network settings correctly
- understand shielded snapshot backup and stale-history checks

### [`xian-contract-skill`](./xian-contract-skill/)

Author and validate current Xian smart contracts correctly.

- follow current `xian-contracting` execution and lint rules
- use the modern `LogEvent("Event", {...})` style
- target current XSC001 token shape for fungible tokens
- validate package layout, lint/compile checks, tests, and deployment paths

### [`xian-governance-skill`](./xian-governance-skill/)

Work with Xian's current validator governance and operator lifecycle.

- use `xian-cli` as the operator-facing control plane
- use `make localnet-validator-governance` for focused live governance coverage
- validate membership, delegation, state-patch, and evidence/slashing flows
- keep backend/runtime concerns separate from CLI/operator concerns

## Usage

Each skill folder contains a `SKILL.md` that an agent can read directly.

```bash
cp -r xian-sdk-skill /path/to/agent/skills/
cp -r xian-node-skill /path/to/agent/skills/
cp -r xian-dex-skill /path/to/agent/skills/
cp -r xian-zk-skill /path/to/agent/skills/
cp -r xian-bds-skill /path/to/agent/skills/
cp -r xian-wallet-skill /path/to/agent/skills/
cp -r xian-contract-skill /path/to/agent/skills/
cp -r xian-governance-skill /path/to/agent/skills/
```

## Resources

- [xian.org](https://xian.org)
- [xian-tech-py](https://pypi.org/project/xian-tech-py/)
- [xian-tech-cli](https://pypi.org/project/xian-tech-cli/)
- [xian-technology/xian-py](https://github.com/xian-technology/xian-py)
- [xian-technology/xian-cli](https://github.com/xian-technology/xian-cli)
- [xian-technology/xian-stack](https://github.com/xian-technology/xian-stack)
- [xian-technology/xian-dex](https://github.com/xian-technology/xian-dex)
- [xian-technology/xian-contracts](https://github.com/xian-technology/xian-contracts)
- [xian-technology/xian-contracting](https://github.com/xian-technology/xian-contracting)
- [xian-technology/xian-abci](https://github.com/xian-technology/xian-abci)

## License

MIT
