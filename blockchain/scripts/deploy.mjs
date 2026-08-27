import "dotenv/config";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { network } from "hardhat";
import { Wallet } from "ethers";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATA_DIR = path.join(__dirname, "..", ".data");
const DEPLOYMENT_PATH = path.join(DATA_DIR, "local-chain.json");

const networkName = process.env.DEPLOY_NETWORK;
const isLocal = networkName === "local";

async function codeExists(ethers, address) {
  if (!address) return false;

  const code = await ethers.provider.getCode(address);
  return Boolean(code && code !== "0x");
}

async function main() {
  if (!networkName) {
    throw new Error(
      "DEPLOY_NETWORK must be set to local or amoy."
    );
  }

  // Hardhat 3 + hardhat-ethers
  const { ethers } = await network.connect();

  fs.mkdirSync(DATA_DIR, { recursive: true });

  if (isLocal && fs.existsSync(DEPLOYMENT_PATH)) {
    const existing = JSON.parse(
      fs.readFileSync(DEPLOYMENT_PATH, "utf8")
    );

    if (await codeExists(ethers, existing.contractAddress)) {
      const networkInfo = await ethers.provider.getNetwork();

      if (Number(networkInfo.chainId) === Number(existing.chainId)) {
        console.log("Existing local ProgressRegistry found.");
        console.log("Contract:", existing.contractAddress);
        console.log("Chain ID:", existing.chainId);
        console.log("Deployment file:", DEPLOYMENT_PATH);
        return;
      }

      console.warn(
        "Stored deployment chain ID differs from current chain; deploying a fresh contract."
      );
    }
  }

  const [deployer] = await ethers.getSigners();

  console.log(
    `Deploying ProgressRegistry on ${networkName} with account:`,
    deployer.address
  );

  const balance = await ethers.provider.getBalance(
    deployer.address
  );

  console.log(
    "Account balance:",
    ethers.formatEther(balance),
    "ETH"
  );

  const ProgressRegistry =
    await ethers.getContractFactory("ProgressRegistry");

  const registry = await ProgressRegistry.deploy();

  await registry.waitForDeployment();

  const address = await registry.getAddress();
  const networkInfo = await ethers.provider.getNetwork();

  let deployerPrivateKey = "";

  if (isLocal) {
    const mnemonic = process.env.LOCAL_MNEMONIC;

    if (!mnemonic) {
      throw new Error(
        "LOCAL_MNEMONIC is required for local deployment."
      );
    }

    const wallet = Wallet.fromPhrase(mnemonic);

    if (
      wallet.address.toLowerCase() !==
      deployer.address.toLowerCase()
    ) {
      throw new Error(
        `LOCAL_MNEMONIC first account ${wallet.address} does not match deployer ${deployer.address}`
      );
    }

    deployerPrivateKey = wallet.privateKey;
  }

  const tx = await registry.setWriter(
    deployer.address,
    true
  );

  await tx.wait();

  console.log(
    "Deployer wallet approved as a writer."
  );

  if (isLocal) {
    const config = {
      rpcUrl:
        process.env.LOCAL_RPC_URL ||
        "http://127.0.0.1:8545",
      chainId: Number(networkInfo.chainId),
      contractAddress: address,
      deployerAddress: deployer.address,
      deployerPrivateKey,
      deployedAt: new Date().toISOString(),
    };

    fs.writeFileSync(
      DEPLOYMENT_PATH,
      `${JSON.stringify(config, null, 2)}\n`,
      { mode: 0o600 }
    );

    console.log(
      "Persistent local deployment saved to:"
    );
    console.log(DEPLOYMENT_PATH);
  } else {
    console.log(
      "External deployment complete."
    );
    console.log(`CONTRACT_ADDRESS=${address}`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
