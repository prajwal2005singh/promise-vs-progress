const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();

  console.log("Deploying ProgressRegistry with account:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", hre.ethers.formatEther(balance), "MATIC");

  const ProgressRegistry = await hre.ethers.getContractFactory("ProgressRegistry");
  const registry = await ProgressRegistry.deploy();
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  console.log("ProgressRegistry deployed to:", address);
  console.log("\nAdd this to backend/.env:");
  console.log(`CONTRACT_ADDRESS=${address}`);

  // Give the same wallet write access by default so the backend can start
  // anchoring records immediately after deploy. Add more writers later
  // with setWriter() if other services need to submit records too.
  const tx = await registry.setWriter(deployer.address, true);
  await tx.wait();
  console.log("Deployer wallet approved as a writer.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
