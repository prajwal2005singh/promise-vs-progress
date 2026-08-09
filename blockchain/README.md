# Blockchain component — ProgressRegistry

This is the tamper-proof layer described in the project spec: a smart
contract on **Polygon** that stores a hash of every piece of citizen
evidence and every admin-verified progress update, so the audit trail
can't be silently edited later — not even by the backend's own database.

**What actually goes on-chain:** only `keccak256` hashes and small
integers (project id, evidence id, record type, timestamp). Photos and
report text stay off-chain in the normal database/file storage; the
contract is a public proof log, not a file store.

## Files

```
blockchain/
  contracts/ProgressRegistry.sol   the smart contract
  scripts/deploy.js                deployment script
  test/ProgressRegistry.test.js    unit tests (5 passing, see below)
  hardhat.config.js                network config (local + Polygon Amoy)
  .env.example                     env vars you need to fill in
```

## What the contract does

- `addRecord(projectId, referenceId, recordType, dataHash)` — anchors a
  new hash. Only wallets marked as `writers` (i.e. the backend's server
  wallet) can call this.
- `recordType` is one of `EVIDENCE` (0), `VERIFIED_PROGRESS` (1), or
  `AUDIT_UPDATE` (2).
- `isHashAnchored(hash)` — anyone can call this to independently confirm
  a given file's hash was really anchored, without trusting the backend.
- `getProjectRecordIndexes(projectId)` — returns every record index tied
  to a project, i.e. its full audit trail.
- `owner` can add/remove writer wallets and transfer ownership, so the
  day-to-day signing key can be rotated without losing control of the
  contract.

I compiled this with solc 0.8.20 and ran the test suite (`test/ProgressRegistry.test.js`)
against a real EVM instance — all 5 tests pass, covering: ownership setup,
writer permissions, rejecting non-writer calls, anchoring + reading a
record, and rejecting a zero hash.

## Setting it up (takes about 15 minutes)

1. **Get an RPC endpoint.** Sign up free at [Alchemy](https://alchemy.com)
   or [Infura](https://infura.io), create an app for **Polygon Amoy**
   (the current public testnet — Mumbai was retired), and copy the HTTPS
   URL.
2. **Create a throwaway wallet.** Add a new account in MetaMask — don't
   reuse a wallet with real funds. Export its private key.
3. **Get free test MATIC.** Go to the
   [Polygon faucet](https://faucet.polygon.technology), select "Amoy",
   and paste your wallet address.
4. **Fill in the env file:**
   ```bash
   cd blockchain
   cp .env.example .env
   # edit .env: paste AMOY_RPC_URL and DEPLOYER_PRIVATE_KEY
   ```
5. **Install and deploy:**
   ```bash
   npm install
   npx hardhat compile
   npx hardhat test              # optional, re-runs the 5 tests locally
   npx hardhat run scripts/deploy.js --network amoy
   ```
   This prints the deployed contract address — copy it.
6. **Wire it into the backend.** In `backend/.env`, set:
   ```
   POLYGON_RPC_URL=<same AMOY_RPC_URL as above>
   DEPLOYER_PRIVATE_KEY=<same private key as above>
   CONTRACT_ADDRESS=<address printed by the deploy script>
   ```
   The backend's `blockchain_client.py` reads these and calls the
   contract using `web3.py`. See `backend/routes/blockchain.py` for the
   API endpoints this exposes.

## Why Polygon (and Amoy specifically)

Polygon has sub-cent gas fees, which matters here since every citizen
photo upload could eventually trigger a transaction — on Ethereum
mainnet that would be prohibitively expensive for a civic-tech tool.
Amoy is Polygon's current public testnet, free to use with faucet MATIC,
which is what you want for a student/prototype build. Moving to Polygon
mainnet later is just a config change (new RPC URL, real MATIC for gas).
