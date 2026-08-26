import "dotenv/config";
import hardhatEthers from "@nomicfoundation/hardhat-ethers";
import hardhatVerify from "@nomicfoundation/hardhat-verify";

const config = {
  plugins: [hardhatEthers, hardhatVerify],

  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },

  networks: {
    hardhat: {
      type: "edr-simulated",
    },

    local: {
      type: "http",
      url: process.env.LOCAL_RPC_URL || "http://127.0.0.1:7545",
      chainId: 1337,
      accounts: process.env.LOCAL_MNEMONIC
        ? { mnemonic: process.env.LOCAL_MNEMONIC }
        : [],
    },

    amoy: {
      type: "http",
      url:
        process.env.AMOY_RPC_URL ||
        "https://rpc-amoy.polygon.technology",
      chainId: 80002,
      accounts: process.env.DEPLOYER_PRIVATE_KEY
        ? [process.env.DEPLOYER_PRIVATE_KEY]
        : [],
    },
  },

  etherscan: {
    apiKey: process.env.POLYGONSCAN_API_KEY || "",
  },
};

export default config;
