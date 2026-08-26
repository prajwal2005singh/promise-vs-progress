import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { network } from "hardhat";
import { Wallet } from "ethers";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATA_DIR = path.join(__dirname, "..", ".data");
const DEPLOYMENT_PATH = path.join(DATA_DIR, "local-chain.json");

async function codeExists(ethers, address) {
  if (!address) return false;

  const code = await ethers.provider.getCode(address);
  return code && code !== "0x";
}

async function main() {
  // Hardhat 3: obtain the ethers plugin through the network connection.
  const { ethers } = await network.connect();

  const networkName = "local";
  const isLocal = true;
  fs.mkdirSync(DATA_DIR, { recursive: true });

  // Local deployment is intentionally persistent. If the Ganache database
  // and deployment record already exist, do not deploy a second contract.
  if (isLocal && fs.existsSync(DEPLOYMENT_PATH)) {
    const existing = JSON.parse(
      fs.readFileSync(DEPLOYMENT_PATH, "utf8")
    );

    if (await codeExists(ethers, existing.contractAddress)) {
      console.log("Existing local ProgressRegistry found.");
      console.log("Contract:", existing.contractAddress);
      console.log("Chain ID:", existing.chainId);
      console.log("Deployment file:", DEPLOYMENT_PATH);
      return;
    }
  }

  const [deployer] = await ethers.getSigners();

  console.log(
    "Deploying ProgressRegistry with account:",
    deployer.address
  );

  const balance = await ethers.provider.getBalance(deployer.address);

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

  // Keep a test-only private key in the local deployment metadata so the
  // Python backend can sign transactions against the local test chain.
  // This file is ignored by git and must NEVER be used for production.
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

  const tx = await registry.setWriter(deployer.address, true);

  await tx.wait();

  console.log("Deployer wallet approved as a writer.");

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
      JSON.stringify(config, null, 2) + "\n",
      { mode: 0o600 }
    );

    console.log("\nPersistent local deployment saved to:");
    console.log(DEPLOYMENT_PATH);

    console.log(
      "\nThe backend can use it automatically with PVP_BLOCKCHAIN_MODE=local."
    );
  } else {
    console.log("\nExternal deployment complete.");
    console.log(`CONTRACT_ADDRESS=${address}`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
