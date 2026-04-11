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

## Usage

Each skill folder contains a `SKILL.md` that an agent can read directly.

```bash
cp -r xian-sdk-skill /path/to/agent/skills/
cp -r xian-node-skill /path/to/agent/skills/
cp -r xian-dex-skill /path/to/agent/skills/
```

## Resources

- [xian.org](https://xian.org)
- [xian-tech-py](https://pypi.org/project/xian-tech-py/)
- [xian-tech-cli](https://pypi.org/project/xian-tech-cli/)
- [xian-technology/xian-py](https://github.com/xian-technology/xian-py)
- [xian-technology/xian-cli](https://github.com/xian-technology/xian-cli)
- [xian-technology/xian-stack](https://github.com/xian-technology/xian-stack)
- [xian-technology/xian-contracts](https://github.com/xian-technology/xian-contracts)

## License

MIT
