# Genesis File Template

Prefer the current CLI or stack generators for normal work:

```bash
xian network create localnet-1 --chain-id xian-localnet-1 \
  --template single-node-dev --generate-validator-key --init-node

# or, from xian-stack, for a multi-node dev network
LOCALNET_NODES=5 make localnet-init
```

Use this reference only when you are inspecting or deliberately editing raw
CometBFT genesis material. A genesis file defines:

- Chain ID and initial time
- Consensus parameters
- Initial validators
- Initial contract state (optional)

## Minimal Genesis

```json
{
  "genesis_time": "2024-01-01T00:00:00.000000000Z",
  "chain_id": "xian-custom-1",
  "initial_height": "1",
  "consensus_params": {
    "block": {
      "max_bytes": "22020096",
      "max_gas": "-1"
    },
    "evidence": {
      "max_age_num_blocks": "100000",
      "max_age_duration": "172800000000000",
      "max_bytes": "1048576"
    },
    "validator": {
      "pub_key_types": ["ed25519"]
    },
    "version": {
      "app": "0"
    },
    "abci": {
      "vote_extensions_enable_height": "0"
    }
  },
  "validators": [
    {
      "address": "<VALIDATOR_ADDRESS>",
      "pub_key": {
        "type": "tendermint/PubKeyEd25519",
        "value": "<BASE64_PUBKEY>"
      },
      "power": "10",
      "name": "genesis-validator"
    }
  ],
  "app_hash": "",
  "app_state": {}
}
```

## Fields Explanation

### Required Fields

| Field | Description |
|-------|-------------|
| `genesis_time` | ISO 8601 timestamp for chain start |
| `chain_id` | Unique network identifier (e.g., `xian-mainnet-1`) |
| `validators` | Initial validator set with their public keys and voting power |

### Validator Entry

```json
{
  "address": "hex-encoded validator address (first 20 bytes of pubkey sha256)",
  "pub_key": {
    "type": "tendermint/PubKeyEd25519",
    "value": "base64-encoded 32-byte ed25519 public key"
  },
  "power": "voting power (usually 10 for equal weight)",
  "name": "human-readable name"
}
```

### Generating Validator Address

```python
import hashlib
import base64

def pubkey_to_address(pubkey_hex: str) -> str:
    """Convert ed25519 pubkey to CometBFT address."""
    pubkey_bytes = bytes.fromhex(pubkey_hex)
    sha = hashlib.sha256(pubkey_bytes).digest()
    return sha[:20].hex().upper()

def pubkey_to_base64(pubkey_hex: str) -> str:
    """Convert hex pubkey to base64 for genesis."""
    return base64.b64encode(bytes.fromhex(pubkey_hex)).decode()
```

## Multi-Validator Genesis

For a network with multiple validators:

```json
{
  "validators": [
    {
      "address": "ADDR1",
      "pub_key": {"type": "tendermint/PubKeyEd25519", "value": "KEY1"},
      "power": "10",
      "name": "validator-1"
    },
    {
      "address": "ADDR2", 
      "pub_key": {"type": "tendermint/PubKeyEd25519", "value": "KEY2"},
      "power": "10",
      "name": "validator-2"
    },
    {
      "address": "ADDR3",
      "pub_key": {"type": "tendermint/PubKeyEd25519", "value": "KEY3"},
      "power": "10",
      "name": "validator-3"
    }
  ]
}
```

Equal voting power (`"power": "10"`) means each validator has equal influence. Adjust for weighted voting.

## Initial State (app_state)

For Xian, `app_state` can include initial contract deployments and balances. Leave empty `{}` for a fresh chain, or pre-populate with contracts.

## Deploying Genesis

1. Prefer `xian network create ... --init-node` or `make localnet-init`.
2. If you are doing a raw low-level setup, place the file at
   `.cometbft/config/genesis.json`.
3. All validators must use identical genesis.
4. Start nodes after the validator keys and peer seeds match the same network.
   The first block is created once 2/3+ voting power is online.
