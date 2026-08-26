# Blockchain component — ProgressRegistry

PvP uses a **persistent local EVM test chain by default** during development.
The backend talks to it through `web3.py`; the chain is not a real public
network and does not require real funds or a Polygon RPC endpoint.

## Architecture

```text
backend (web3.py)
        |
        v
http://127.0.0.1:8545
        |
   Ganache local EVM
        |
  .data/ganache/      <- persistent chain database
        |
 ProgressRegistry.sol
```

The contract is deployed once to the persistent local chain. Its address and
the local test account metadata are stored in:

```text
blockchain/.data/local-chain.json
```

Both `.data/` and the deployment metadata are git-ignored because the private
key inside that file is **test-only**.

## Start the local persistent chain

From this directory:

```bash
cp .env.example .env
npm install
npm run chain:start
```

Keep that terminal running. The chain database lives at:

```text
blockchain/.data/ganache
```

so restarting Ganache with the same database path and mnemonic preserves the
contract and transaction history.

## Deploy the contract

In a second terminal:

```bash
cd blockchain
npm run deploy:local
```

The first deployment creates:

```text
blockchain/.data/local-chain.json
```

Running `npm run deploy:local` again detects the existing contract and does not
deploy another copy, as long as the persistent chain database still contains
that contract.

## Backend

The backend defaults to:

```env
PVP_BLOCKCHAIN_MODE=local
PVP_LOCAL_CHAIN_CONFIG=../blockchain/.data/local-chain.json
```

No Polygon key or real-network RPC is required.

Start the backend only after the local chain is running and the contract has
been deployed.

## Important: reset the development chain

To intentionally start a fresh chain and erase all local blockchain history:

```bash
rm -rf .data/ganache .data/local-chain.json
```

Then start Ganache and deploy again.

## External network

An external network remains available for later testing, but it is opt-in:

```env
PVP_BLOCKCHAIN_MODE=external
POLYGON_RPC_URL=...
DEPLOYER_PRIVATE_KEY=...
CONTRACT_ADDRESS=...
```

Do not use a real-funded private key for development.
