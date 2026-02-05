# 🐍 Xian AI Skills

AI agent skills for the [Xian](https://xian.org) blockchain — a Layer 1 with native Python smart contracts on CometBFT.

These skills give AI agents (OpenClaw, Codex, Claude Code, etc.) the knowledge to build on Xian, deploy nodes, write smart contracts, and interact with the network programmatically.

## Skills

### [`xian-sdk-skill`](./xian-sdk-skill/)

Build applications on Xian using the [xian-py](https://github.com/xian-network/xian-py) Python SDK.

- Wallet creation (basic, HD/BIP39, Ethereum-derived)
- Token transfers and contract interactions
- Smart contract deployment and validation
- State queries and transaction simulation
- Async/batch operations
- Encrypted messaging
- Common patterns: DEX swaps, token services

### [`xian-node-skill`](./xian-node-skill/)

Deploy and manage Xian blockchain nodes via [xian-stack](https://github.com/xian-network/xian-stack).

- Join mainnet or testnet
- Create new networks
- Validator and service node setup
- Node monitoring and troubleshooting
- CometBFT configuration
- Docker-based deployment

## Usage

Each skill folder contains a `SKILL.md` that AI agents read to learn the relevant APIs and workflows. Point your agent at the skill folder or copy it into your agent's skill directory.

**OpenClaw example:**
```bash
# Install via ClawdHub (when available)
clawdhub install xian-sdk-skill
clawdhub install xian-node-skill
```

**Manual:**
```bash
# Copy into your agent's skills directory
cp -r xian-sdk-skill /path/to/agent/skills/
cp -r xian-node-skill /path/to/agent/skills/
```

## Resources

- [xian.org](https://xian.org) — Project site
- [xian-py](https://github.com/xian-network/xian-py) — Python SDK
- [xian-stack](https://github.com/xian-network/xian-stack) — Node deployment
- [xian-core](https://github.com/xian-network/xian-core) — Core node software
- [Xian Standard Contracts](https://github.com/xian-network/xian-standard-contracts) — Token standards

## License

MIT
