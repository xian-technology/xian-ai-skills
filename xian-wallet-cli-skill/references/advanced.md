# Advanced wallet workflows

## DEX and NFT

- Quote with `dex quote TOKEN_IN TOKEN_OUT AMOUNT --from SENDER`.
  When an allowance is needed, request a separate `dex allowance` proposal
  for the exact amount and specified router. Wait for its finalized receipt
  before `dex prepare`. Review the input token, minimum received, recipient,
  pair, and deadline. Use a zero allowance if the owner asks to revoke it.
- Use `nft inspect COLLECTION TOKEN_ID` to verify ownership and metadata.
  Use `nft transfer COLLECTION TOKEN_ID --from SENDER --to RECIPIENT
  --out proposal.json` through the regular approval pipeline.

## x402

- `x402 quote URL --from SENDER --to PAYEE --asset TOKEN --max-amount AMOUNT
  --settlement CONTRACT --out offer.json` pins the chain, resource, payee,
  settlement contract and payment ceiling.
- Ask the owner or trusted signer to review and approve the exact offer with
  `x402 approve`. The agent can relay it with
  `x402 submit offer.json payment.json --out response.data`.
  Recover from an uncertain HTTP response using the same signed payment ID.
  Approval grants for token transfers do not cover x402 permits.

## Dapps and shielded assets

- The owner pairs with `walletconnect pair --account ACCOUNT --network PROFILE`
  and reviews each write request in the terminal. The service requires the
  optional installed transport and the owner's configured Reown project ID.
- Shielded recovery, sync, and proving run on the owner machine with its
  encrypted snapshot, the supported network's indexed history, and its
  matching trusted proving bundle. An agent can relay only the resulting
  reviewed public proposal and signed approval. Ordinary direct submission
  does not conceal origin transport metadata.
