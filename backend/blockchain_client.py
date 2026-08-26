"""
blockchain_client.py — Promise vs Progress
===========================================
Local-first Web3 client for the ProgressRegistry smart contract.

PvP development uses a persistent local Ganache test chain by default.
The chain is NOT a public network. Its database lives under:
    blockchain/.data/ganache

The deployment metadata (contract address + test wallet key) is stored in:
    blockchain/.data/local-chain.json

The backend reads that file automatically when
PVP_BLOCKCHAIN_MODE=local (the default).

For a future public/testnet deployment, set PVP_BLOCKCHAIN_MODE=external and
provide the external RPC/private-key/contract variables.
"""

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DEFAULT_LOCAL_CONFIG = PROJECT_ROOT / "blockchain" / ".data" / "local-chain.json"

BLOCKCHAIN_MODE = os.getenv("PVP_BLOCKCHAIN_MODE", "local").strip().lower()
LOCAL_CHAIN_CONFIG = Path(
    os.getenv("PVP_LOCAL_CHAIN_CONFIG", str(DEFAULT_LOCAL_CONFIG))
)
if not LOCAL_CHAIN_CONFIG.is_absolute():
    LOCAL_CHAIN_CONFIG = (BASE_DIR / LOCAL_CHAIN_CONFIG).resolve()

# External chain settings are intentionally opt-in.
EXTERNAL_RPC_URL = os.getenv("POLYGON_RPC_URL")
EXTERNAL_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")
EXTERNAL_CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

RECORD_TYPE_EVIDENCE = 0
RECORD_TYPE_VERIFIED_PROGRESS = 1
RECORD_TYPE_AUDIT_UPDATE = 2

RECORD_TYPE_TO_INT = {
    "EVIDENCE": RECORD_TYPE_EVIDENCE,
    "VERIFIED_PROGRESS": RECORD_TYPE_VERIFIED_PROGRESS,
    "AUDIT_UPDATE": RECORD_TYPE_AUDIT_UPDATE,
}

CONTRACT_ABI = json.loads("""
[
  {"inputs":[{"internalType":"uint256","name":"projectId","type":"uint256"},
             {"internalType":"uint256","name":"referenceId","type":"uint256"},
             {"internalType":"uint8","name":"recordType","type":"uint8"},
             {"internalType":"bytes32","name":"dataHash","type":"bytes32"}],
   "name":"addRecord",
   "outputs":[{"internalType":"uint256","name":"recordIndex","type":"uint256"}],
   "stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"bytes32","name":"dataHash","type":"bytes32"}],
   "name":"isHashAnchored",
   "outputs":[{"internalType":"bool","name":"","type":"bool"}],
   "stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"index","type":"uint256"}],
   "name":"getRecord",
   "outputs":[{"components":[
        {"internalType":"uint256","name":"projectId","type":"uint256"},
        {"internalType":"uint256","name":"referenceId","type":"uint256"},
        {"internalType":"uint8","name":"recordType","type":"uint8"},
        {"internalType":"bytes32","name":"dataHash","type":"bytes32"},
        {"internalType":"address","name":"submittedBy","type":"address"},
        {"internalType":"uint256","name":"timestamp","type":"uint256"}],
     "internalType":"struct ProgressRegistry.Record","name":"","type":"tuple"}],
   "stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"projectId","type":"uint256"}],
   "name":"getProjectRecordIndexes",
   "outputs":[{"internalType":"uint256[]","name":"","type":"uint256[]"}],
   "stateMutability":"view","type":"function"},
  {"inputs":[],"name":"recordCount",
   "outputs":[{"internalType":"uint256","name":"","type":"uint256"}],
   "stateMutability":"view","type":"function"}
]
""")


class BlockchainClient:
    def __init__(self):
        self.enabled = False
        self.mode = BLOCKCHAIN_MODE
        self.w3 = None
        self.contract = None
        self.account = None
        self.private_key = None
        self.rpc_url = None
        self.contract_address = None
        self.chain_id = None

        try:
            self._configure()
        except Exception as exc:
            log.warning("Blockchain client disabled: %s", exc)

    def _configure(self):
        if self.mode == "disabled":
            log.info("Blockchain client disabled by PVP_BLOCKCHAIN_MODE=disabled")
            return

        if self.mode == "local":
            if not LOCAL_CHAIN_CONFIG.exists():
                raise RuntimeError(
                    f"Local chain config not found at {LOCAL_CHAIN_CONFIG}. "
                    "Start the persistent local chain and deploy the contract "
                    "with: cd blockchain && npm run chain:start, then npm run deploy:local."
                )

            config = json.loads(LOCAL_CHAIN_CONFIG.read_text(encoding="utf-8"))
            self.rpc_url = config.get("rpcUrl", "http://127.0.0.1:8545")
            self.private_key = config.get("deployerPrivateKey")
            self.contract_address = config.get("contractAddress")
            self.chain_id = int(config.get("chainId", 1337))

            if not self.private_key or not self.contract_address:
                raise RuntimeError(
                    "local-chain.json is missing deployerPrivateKey or contractAddress."
                )

        elif self.mode == "external":
            self.rpc_url = EXTERNAL_RPC_URL
            self.private_key = EXTERNAL_PRIVATE_KEY
            self.contract_address = EXTERNAL_CONTRACT_ADDRESS
            if not (self.rpc_url and self.private_key and self.contract_address):
                raise RuntimeError(
                    "External mode requires POLYGON_RPC_URL, DEPLOYER_PRIVATE_KEY "
                    "and CONTRACT_ADDRESS."
                )
        else:
            raise RuntimeError(
                f"Unknown PVP_BLOCKCHAIN_MODE={self.mode!r}. "
                "Use local, external, or disabled."
            )

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise RuntimeError(f"Cannot connect to blockchain RPC at {self.rpc_url}")

        actual_chain_id = self.w3.eth.chain_id
        if self.chain_id is not None and actual_chain_id != self.chain_id:
            raise RuntimeError(
                f"Chain ID mismatch: config={self.chain_id}, RPC={actual_chain_id}"
            )
        self.chain_id = actual_chain_id

        checksum_address = Web3.to_checksum_address(self.contract_address)
        if self.w3.eth.get_code(checksum_address) in (b"", b"\x00"):
            raise RuntimeError(
                f"No contract bytecode found at {checksum_address} on chain {self.chain_id}."
            )

        self.account = self.w3.eth.account.from_key(self.private_key)
        self.contract = self.w3.eth.contract(
            address=checksum_address,
            abi=CONTRACT_ABI,
        )
        self.contract_address = checksum_address
        self.enabled = True

        log.info(
            "Blockchain enabled: mode=%s chain_id=%s rpc=%s contract=%s account=%s",
            self.mode,
            self.chain_id,
            self.rpc_url,
            self.contract_address,
            self.account.address,
        )

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        digest = Web3.keccak(data).hex()
        return digest if digest.startswith("0x") else f"0x{digest}"

    @staticmethod
    def hash_text(text: str) -> str:
        digest = Web3.keccak(text=text).hex()
        return digest if digest.startswith("0x") else f"0x{digest}"

    def _require_enabled(self):
        if not self.enabled:
            raise RuntimeError(
                "Blockchain client is not available. Start the persistent local chain "
                "and deploy the contract first, or set PVP_BLOCKCHAIN_MODE=disabled."
            )

    def anchor_record(
        self,
        project_id: int,
        reference_id: int,
        record_type: str,
        data_hash: str,
    ) -> dict:
        self._require_enabled()

        if record_type not in RECORD_TYPE_TO_INT:
            raise ValueError(f"Unknown blockchain record type: {record_type}")

        data_hash_bytes = bytes.fromhex(data_hash.replace("0x", ""))
        record_type_int = RECORD_TYPE_TO_INT[record_type]

        nonce = self.w3.eth.get_transaction_count(
            self.account.address,
            "pending",
        )

        tx = self.contract.functions.addRecord(
            project_id,
            reference_id,
            record_type_int,
            data_hash_bytes,
        ).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "chainId": self.chain_id,
        })

        # Explicitly set gas only when the client did not estimate it.
        if "gas" not in tx:
            tx["gas"] = self.w3.eth.estimate_gas(tx)

        signed_tx = self.w3.eth.account.sign_transaction(
            tx,
            self.private_key,
        )
        tx_hash = self.w3.eth.send_raw_transaction(
            signed_tx.raw_transaction
        )

        log.info(
            "Anchoring local/external blockchain record: tx=%s",
            tx_hash.hex(),
        )

        receipt = self.w3.eth.wait_for_transaction_receipt(
            tx_hash,
            timeout=120,
        )

        status = (
            "CONFIRMED"
            if receipt.status == 1
            else "FAILED"
        )

        return {
            "tx_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "status": status,
            "chain_id": self.chain_id,
            "mode": self.mode,
        }

    def is_hash_anchored(self, data_hash: str) -> bool:
        self._require_enabled()
        data_hash_bytes = bytes.fromhex(data_hash.replace("0x", ""))
        return self.contract.functions.isHashAnchored(data_hash_bytes).call()

    def get_project_record_indexes(self, project_id: int) -> list[int]:
        self._require_enabled()
        return self.contract.functions.getProjectRecordIndexes(project_id).call()


blockchain_client = BlockchainClient()
