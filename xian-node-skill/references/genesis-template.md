# Genesis File Reference

Do not hand-write Xian genesis. Generate it with the CLI or the stack, which
build the contract state from a committed `xian-configs` bundle, compute its
state root and write a matching CometBFT genesis:

```bash
xian network create localnet-1 --chain-id xian-localnet-1 \
  --template single-node-dev \
  --bootstrap-node localnet-1 \
  --generate-validator-key \
  --init-node

# or, from xian-stack, for a multi-node dev network
LOCALNET_NODES=5 make localnet-init
```

Use this reference only to inspect generated genesis. Editing serialized
state or balances by hand breaks the state root, and the node refuses to
start.

## Layout

A generated `config/genesis.json` has these top-level fields:

```json
{
  "genesis_time": "2026-11-13T18:22:43.179998Z",
  "chain_id": "xian-localnet-1",
  "initial_height": "0",
  "consensus_params": {
    "block": {"max_bytes": "22020096", "max_gas": "-1", "time_iota_ms": "1000"},
    "evidence": {
      "max_age_num_blocks": "100000",
      "max_age_duration": "172800000000000",
      "max_bytes": "1048576"
    },
    "validator": {"pub_key_types": ["ed25519"]},
    "version": {}
  },
  "validators": [
    {
      "address": "<VALIDATOR_ADDRESS>",
      "pub_key": {"type": "tendermint/PubKeyEd25519", "value": "<BASE64_PUBKEY>"},
      "power": "10",
      "name": "localnet-1"
    }
  ],
  "app_hash": "<STATE_ROOT_HEX>",
  "abci_genesis": {
    "hash": "<STATE_ROOT_HEX>",
    "number": 0,
    "genesis": [
      {"key": "__execution_policy", "value": {"execution_revision": "xvm-execution-14", "...": "..."}},
      {"key": "__fee_policy", "value": {"tx_fee_mode": "paid_metered", "max_tx_chi": 200000, "max_block_chi": 500000}},
      {"key": "currency.balances:<ACCOUNT>", "value": "..."}
    ],
    "origin": {"sender": "<FOUNDER_PUBLIC_KEY>", "signature": "<SIGNATURE>"}
  }
}
```

Xian keeps its application state in `abci_genesis`, not in CometBFT's
`app_state`:

| Field | Meaning |
|-------|---------|
| `abci_genesis.genesis` | Ordered `{key, value}` state entries: system contracts (`currency`, `validators`, `governance`, `dao`, `rewards`, `chi_cost`, `zk_registry`, ...) and the node-read records `__execution_policy` (never patchable), `__fee_policy` and `__runtime_features.*` (patchable by governance only to valid values) |
| `abci_genesis.hash` | State root of those entries (`xian-state-root-v3`) |
| `app_hash` | The same state root, so CometBFT's first block commits to it |
| `abci_genesis.origin` | Founder public key and signature over the genesis block (empty when no founder key signed it) |

At InitChain the node requires exactly one `__execution_policy` matching its
runtime and a valid `__fee_policy`, and it recomputes the state root and
compares it with `abci_genesis.hash`.

## Validator Entry

```json
{
  "address": "hex-encoded validator address (first 20 bytes of the pubkey sha256)",
  "pub_key": {
    "type": "tendermint/PubKeyEd25519",
    "value": "base64-encoded 32-byte ed25519 public key"
  },
  "power": "voting power (10 by default)",
  "name": "human-readable name"
}
```

The CometBFT validator set must match the active members that the
`validators` contract state in `abci_genesis` records; the generators keep the
two in sync.

### Deriving A Validator Address

```python
import base64
import hashlib

def pubkey_to_address(pubkey_hex: str) -> str:
    """Convert an ed25519 public key to its CometBFT address."""
    return hashlib.sha256(bytes.fromhex(pubkey_hex)).digest()[:20].hex().upper()

def pubkey_to_base64(pubkey_hex: str) -> str:
    """Convert a hex public key to the base64 form used in genesis."""
    return base64.b64encode(bytes.fromhex(pubkey_hex)).decode()
```

## Distributing Genesis

1. Generate once with `xian network create ... --init-node` (or
   `make localnet-init` for local multi-node work).
2. Give every node the same file. Compare installed copies as bytes and
   record the SHA-256; the node-home writer can reformat JSON, so pick the
   bootstrap home's `config/genesis.json` as the canonical bytes.
3. Each node keeps its own validator key and P2P key; never copy another
   node's `priv_validator_key.json`, `node_key.json` or signing state.
4. Start nodes after validator keys and peers match the same network. The first
   block is produced once more than two-thirds of the voting power is online.
5. A different allocation, fee policy or validator set means regenerating
   genesis before launch, never editing it afterwards.
