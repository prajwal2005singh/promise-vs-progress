# Blockchain component — ProgressRegistry

PvP uses a **persistent local EVM test chain by default** during development.
The blockchain package is an ES module (`"type": "module"`). Hardhat's
configuration remains CommonJS in `hardhat.config.cjs` for compatibility with
Hardhat 2.

## Architecture

```text
backend (web3.py)
        |
        v
http://127.0.0.1:8545
        |
   Ganache local EVM
        |
  .data/ganache/        <- persistent chain database
        |
 ProgressRegistry.sol
```

The contract is deployed once to the persistent local chain. Its address and
local test account metadata are stored in:

```text
blockchain/.data/local-chain.json
```

`.data/` is local-only and must not be committed.

## Start the persistent local chain

From `blockchain/`:

```bash
cp .env.example .env
npm install
npm run chain:start
```

Keep that terminal running. The chain database remains at:

```text
blockchain/.data/ganache
```

Restarting Ganache with the same database path, mnemonic, and chain ID
preserves blocks, transactions, contract state, and account nonces.

## Deploy the contract

In another terminal:

```bash
cd blockchain
npm run deploy:local
```

The first run creates:

```text
blockchain/.data/local-chain.json
```

Running it again reuses the existing contract if it is still present on the
same persistent chain.

## Backend

The backend uses local mode by default:

```env
PVP_BLOCKCHAIN_MODE=local
LOCAL_RPC_URL=http://127.0.0.1:8545
PVP_LOCAL_CHAIN_CONFIG=../blockchain/.data/local-chain.json
```

The backend reads the deployed contract address and test private key from the
local deployment metadata automatically.

## Chain ID vs network ID

PvP explicitly uses **Chain ID 1337** for the local chain. Network ID is a
separate legacy/network identifier. Backend transaction signing uses the chain
ID returned by the node.

## Reset the local chain

To intentionally erase all local history:

```bash
rm -rf .data/ganache .data/local-chain.json
```

Then start Ganache and deploy again.

## External network

Polygon Amoy remains available but is explicitly opt-in:

```env
PVP_BLOCKCHAIN_MODE=external
POLYGON_RPC_URL=...
DEPLOYER_PRIVATE_KEY=...
CONTRACT_ADDRESS=...
```

Do not use real-funded credentials for local development.

## Local chain troubleshooting

The persistent chain uses Ganache as an imported Node module (not a spawned global binary). If `npm run chain:start` reports that Ganache is missing, run:

```bash
npm install -D ganache@7.9.2
npm run chain:check
npm run chain:start
```

The chain data is stored under `blockchain/.data/ganache/` and persists across restarts.

