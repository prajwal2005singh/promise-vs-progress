import "dotenv/config";
import fs from "node:fs";
import path from "node:path";
import ganache from "ganache";

const __dirname = path.dirname(new URL(import.meta.url).pathname);
const root = path.resolve(__dirname, "..");
const dataDir = path.join(root, ".data");
const dbPath = path.join(dataDir, "ganache");

fs.mkdirSync(dataDir, { recursive: true });

const mnemonic = process.env.LOCAL_MNEMONIC ||
  "test test test test test test test test test test test junk";
const rpcPort = Number(process.env.LOCAL_RPC_PORT || 8545);
const chainId = Number(process.env.LOCAL_CHAIN_ID || 1337);

console.log("PvP persistent local blockchain");
console.log(`RPC:      http://127.0.0.1:${rpcPort}`);
console.log(`Chain ID: ${chainId}`);
console.log(`Database: ${dbPath}`);
console.log("Stop with Ctrl+C. The chain state remains on disk.");
console.log("");

const server = ganache.server({
  server: {
    host: "127.0.0.1",
    port: rpcPort,
  },
  chain: {
    chainId,
  },
  wallet: {
    mnemonic,
    totalAccounts: 10,
    defaultBalance: 1000,
  },
  database: {
    dbPath,
  },
  logging: {
    quiet: false,
  },
});

let shuttingDown = false;

const shutdown = (signal) => {
  if (shuttingDown) return;
  shuttingDown = true;

  console.log(`\nReceived ${signal}; stopping Ganache...`);

  server.close((error) => {
    if (error) {
      console.error("Failed to stop Ganache cleanly:", error);
      process.exitCode = 1;
      return;
    }

    console.log("Ganache stopped. Chain state remains on disk.");
  });
};

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));

try {
  await new Promise((resolve, reject) => {
    server.listen(rpcPort, "127.0.0.1", (error) => {
      if (error) reject(error);
      else resolve();
    });
  });

  console.log("Ganache started successfully.");
  console.log("Persistent local chain is ready.");
} catch (error) {
  console.error("Failed to start Ganache:", error);
  console.error("Make sure the ganache package is installed:");
  console.error("  npm install -D ganache@7.9.2");
  process.exit(1);
}
