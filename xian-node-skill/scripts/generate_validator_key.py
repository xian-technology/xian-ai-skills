#!/usr/bin/env python3
"""Generate current Xian validator key material.

Prefer the CLI in normal operator workflows:

    xian keys validator generate --out-dir ./keys/validator-1

This helper exists as a portable fallback for agent contexts where the CLI is
not installed. It writes the same two-file shape expected by current
`xian network join --validator-key-ref` and `xian node init` flows:

- priv_validator_key.json
- validator_key_info.json
"""

import argparse
import base64
import hashlib
import json
from pathlib import Path
import secrets


def _load_signing_key(private_key_hex: str | None):
    """Create a PyNaCl signing key from a 32-byte hex seed or fresh entropy."""
    try:
        from nacl.signing import SigningKey
    except ImportError:
        print(
            "Error: PyNaCl not installed. Run this helper with: "
            'uv run --with pynacl python generate_validator_key.py'
        )
        raise SystemExit(1)

    if private_key_hex is None:
        return SigningKey(secrets.token_bytes(32))

    try:
        seed = bytes.fromhex(private_key_hex)
    except ValueError:
        raise SystemExit("private key must be valid hex") from None
    if len(seed) != 32:
        raise SystemExit("private key must be a 32-byte / 64-character hex seed")
    return SigningKey(seed)


def build_validator_material(private_key_hex: str | None = None) -> dict:
    """Build current validator metadata and CometBFT priv_validator_key JSON."""
    signing_key = _load_signing_key(private_key_hex)
    public_key = signing_key.verify_key.encode()
    private_key_with_public = signing_key.encode() + public_key
    priv_validator_key = {
        "address": hashlib.sha256(public_key).digest()[:20].hex().upper(),
        "pub_key": {
            "type": "tendermint/PubKeyEd25519",
            "value": base64.b64encode(public_key).decode("ascii"),
        },
        "priv_key": {
            "type": "tendermint/PrivKeyEd25519",
            "value": base64.b64encode(private_key_with_public).decode("ascii"),
        },
    }
    return {
        "validator_private_key_hex": signing_key.encode().hex(),
        "validator_public_key_hex": public_key.hex(),
        "priv_validator_key": priv_validator_key,
    }


def write_validator_files(out_dir: Path, payload: dict, *, force: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "priv_validator_key.json": payload["priv_validator_key"],
        "validator_key_info.json": payload,
    }
    for name, content in files.items():
        path = out_dir / name
        if path.exists() and not force:
            raise SystemExit(f"{path} already exists; pass --force to overwrite")
        path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate Xian validator keys")
    parser.add_argument(
        "--private-key",
        help="existing 64-character hex validator seed; omit to generate one",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="write priv_validator_key.json and validator_key_info.json here",
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--name",
        default="validator",
        help="Validator name for genesis entry",
    )
    parser.add_argument(
        "--power",
        default="10",
        help="Voting power (default: 10)",
    )
    parser.add_argument(
        "--genesis-entry",
        action="store_true",
        help="also output a genesis validator entry JSON",
    )
    args = parser.parse_args()

    payload = build_validator_material(args.private_key)

    if args.out_dir is not None:
        write_validator_files(args.out_dir, payload, force=args.force)
        print(f"Wrote {args.out_dir / 'priv_validator_key.json'}")
        print(f"Wrote {args.out_dir / 'validator_key_info.json'}")
    else:
        print(json.dumps(payload, indent=2))

    if args.genesis_entry:
        priv_validator_key = payload["priv_validator_key"]
        entry = {
            "address": priv_validator_key["address"],
            "pub_key": priv_validator_key["pub_key"],
            "power": args.power,
            "name": args.name,
        }
        print("\nGenesis validator entry:")
        print(json.dumps(entry, indent=2))


if __name__ == "__main__":
    main()
