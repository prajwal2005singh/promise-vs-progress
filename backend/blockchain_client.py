"""
blockchain_client.py — Promise vs Progress
===========================================
Thin wrapper around web3.py that talks to the ProgressRegistry smart
contract deployed on Polygon Amoy (see /blockchain/contracts/ProgressRegistry.sol).

This module is deliberately the *only* place in the backend that knows
about web3/RPC details. Everything else (services, routes) calls the
plain Python functions below and doesn't need to think about gas,
nonces, or signing.

If POLYGON_RPC_URL / DEPLOYER_PRIVATE_KEY / CONTRACT_ADDRESS aren't set
(e.g. during local development without a deployed contract), the client
runs in "disabled" mode: hashing still works, but anchoring calls raise
a clear error instead of crashing on a missing connection.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL")
DEPLOYER_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

# RecordType enum values -- must match the Solidity enum order exactly.
RECORD_TYPE_EVIDENCE = 0
RECORD_TYPE_VERIFIED_PROGRESS = 1
RECORD_TYPE_AUDIT_UPDATE = 2

RECORD_TYPE_TO_INT = {
    "EVIDENCE": RECORD_TYPE_EVIDENCE,
    "VERIFIED_PROGRESS": RECORD_TYPE_VERIFIED_PROGRESS,
    "AUDIT_UPDATE": RECORD_TYPE_AUDIT_UPDATE,
}

# The ABI only needs the functions/events this backend actually calls.
# Regenerate from blockchain/artifacts after `npx hardhat compile` if the
# contract's public interface changes.
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
        self.enabled = bool(POLYGON_RPC_URL and DEPLOYER_PRIVATE_KEY and CONTRACT_ADDRESS)

        if not self.enabled:
            log.warning(
                "Blockchain client disabled: set POLYGON_RPC_URL, "
                "DEPLOYER_PRIVATE_KEY and CONTRACT_ADDRESS in backend/.env "
                "to enable on-chain anchoring. See /blockchain/README.md."
            )
            self.w3 = None
            self.contract = None
            self.account = None
            return

        self.w3 = Web3(Web3.HTTPProvider(POLYGON_RPC_URL))
        self.account = self.w3.eth.account.from_key(DEPLOYER_PRIVATE_KEY)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=CONTRACT_ABI
        )

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """keccak256 hash of raw bytes, hex-encoded with 0x prefix."""
        digest = Web3.keccak(data).hex()
        return digest if digest.startswith("0x") else f"0x{digest}"

    @staticmethod
    def hash_text(text: str) -> str:
        """keccak256 hash of a UTF-8 string (e.g. a description or URL)."""
        digest = Web3.keccak(text=text).hex()
        return digest if digest.startswith("0x") else f"0x{digest}"

    def _require_enabled(self):
        if not self.enabled:
            raise RuntimeError(
                "Blockchain client is not configured. Deploy the contract "
                "(see /blockchain/README.md) and set POLYGON_RPC_URL, "
                "DEPLOYER_PRIVATE_KEY and CONTRACT_ADDRESS in backend/.env."
            )

    def anchor_record(
        self,
        project_id: int,
        reference_id: int,
        record_type: str,
        data_hash: str
    ) -> dict:
        """
        Send a transaction that calls addRecord() on-chain. Blocks until
        the transaction is mined (fine for a prototype's request volume;
        for higher throughput this would move to a background worker).

        Returns a dict with tx_hash, block_number, and status so the
        caller can persist a BlockchainRecord row.
        """
        self._require_enabled()

        record_type_int = RECORD_TYPE_TO_INT[record_type]
        data_hash_bytes = bytes.fromhex(data_hash.replace("0x", ""))

        nonce = self.w3.eth.get_transaction_count(self.account.address)

        tx = self.contract.functions.addRecord(
            project_id,
            reference_id,
            record_type_int,
            data_hash_bytes
        ).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "chainId": self.w3.eth.chain_id,
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, DEPLOYER_PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        log.info("Anchoring record on-chain, tx sent: %s", tx_hash.hex())

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        status = "CONFIRMED" if receipt.status == 1 else "FAILED"

        return {
            "tx_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "status": status,
        }

    def is_hash_anchored(self, data_hash: str) -> bool:
        self._require_enabled()
        data_hash_bytes = bytes.fromhex(data_hash.replace("0x", ""))
        return self.contract.functions.isHashAnchored(data_hash_bytes).call()

    def get_project_record_indexes(self, project_id: int) -> list[int]:
        self._require_enabled()
        return self.contract.functions.getProjectRecordIndexes(project_id).call()


# Single shared instance -- import this from services, not the class.
blockchain_client = BlockchainClient()
