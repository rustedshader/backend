# app/blockchain/tourist_id_client.py
from dataclasses import dataclass
from typing import Any, Tuple, Dict
from web3 import Web3
from web3.types import TxReceipt
from eth_account import Account
from hexbytes import HexBytes
from app.core.config import settings
import warnings
import logging

# Suppress ABI mismatch warnings from eth_utils
warnings.filterwarnings("ignore", message=".*MismatchedABI.*")
logging.getLogger("eth_utils.functional").setLevel(logging.ERROR)


# --- Minimal ABI for your TouristID contract ---
TOURIST_ID_ABI: list[dict] = [
    {"inputs": [], "stateMutability": "nonpayable", "type": "constructor"},
    {
        "inputs": [
            {"internalType": "address", "name": "sender", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "address", "name": "owner", "type": "address"},
        ],
        "name": "ERC721IncorrectOwner",
        "type": "error",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
        ],
        "name": "ERC721InsufficientApproval",
        "type": "error",
    },
    {
        "inputs": [{"internalType": "address", "name": "approver", "type": "address"}],
        "name": "ERC721InvalidApprover",
        "type": "error",
    },
    {
        "inputs": [{"internalType": "address", "name": "operator", "type": "address"}],
        "name": "ERC721InvalidOperator",
        "type": "error",
    },
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "ERC721InvalidOwner",
        "type": "error",
    },
    {
        "inputs": [{"internalType": "address", "name": "receiver", "type": "address"}],
        "name": "ERC721InvalidReceiver",
        "type": "error",
    },
    {
        "inputs": [{"internalType": "address", "name": "sender", "type": "address"}],
        "name": "ERC721InvalidSender",
        "type": "error",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ERC721NonexistentToken",
        "type": "error",
    },
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "OwnableInvalidOwner",
        "type": "error",
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "OwnableUnauthorizedAccount",
        "type": "error",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "owner",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "approved",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "tokenId",
                "type": "uint256",
            },
        ],
        "name": "Approval",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "owner",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "operator",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "bool",
                "name": "approved",
                "type": "bool",
            },
        ],
        "name": "ApprovalForAll",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "tokenId",
                "type": "uint256",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "tourist",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "bytes32",
                "name": "kycHash",
                "type": "bytes32",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "validUntil",
                "type": "uint256",
            },
        ],
        "name": "IDIssued",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "tokenId",
                "type": "uint256",
            }
        ],
        "name": "IDRevoked",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "previousOwner",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "newOwner",
                "type": "address",
            },
        ],
        "name": "OwnershipTransferred",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "from",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "to",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "tokenId",
                "type": "uint256",
            },
        ],
        "name": "Transfer",
        "type": "event",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "getApproved",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "getTouristInfo",
        "outputs": [
            {
                "components": [
                    {"internalType": "bytes32", "name": "kycHash", "type": "bytes32"},
                    {
                        "internalType": "bytes32",
                        "name": "itineraryHash",
                        "type": "bytes32",
                    },
                    {
                        "internalType": "uint256",
                        "name": "validUntil",
                        "type": "uint256",
                    },
                    {"internalType": "bool", "name": "isRevoked", "type": "bool"},
                ],
                "internalType": "struct TouristID.TouristInfo",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "operator", "type": "address"},
        ],
        "name": "isApprovedForAll",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "isValid",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "tourist", "type": "address"},
            {"internalType": "bytes32", "name": "kycHash", "type": "bytes32"},
            {"internalType": "bytes32", "name": "itineraryHash", "type": "bytes32"},
            {"internalType": "uint256", "name": "validityDuration", "type": "uint256"},
        ],
        "name": "issueID",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "renounceOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "revokeID",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
        ],
        "name": "safeTransferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "bytes", "name": "data", "type": "bytes"},
        ],
        "name": "safeTransferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "bool", "name": "approved", "type": "bool"},
        ],
        "name": "setApprovalForAll",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes4", "name": "interfaceId", "type": "bytes4"}],
        "name": "supportsInterface",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
        ],
        "name": "transferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "newOwner", "type": "address"}],
        "name": "transferOwnership",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


@dataclass
class TouristInfo:
    kycHash: str  # 0x…32 bytes hex
    itineraryHash: str  # 0x…32 bytes hex
    validUntil: int  # unix timestamp
    isRevoked: bool


class TouristIDClient:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.blockchain_rpc_url))
        if not self.w3.is_connected():
            raise RuntimeError("Web3 provider not connected")

        self.chain_id: int = int(settings.blockchain_chain_id)
        self.owner: str = self.w3.to_checksum_address(settings.owner_address)
        self.account = Account.from_key(settings.private_key)
        if self.account.address.lower() != self.owner.lower():
            raise ValueError("private_key does not match owner_address")

        self.contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(settings.contract_address),
            abi=TOURIST_ID_ABI,
        )

        # Sanity: ensure there's bytecode at the contract address
        code = self.w3.eth.get_code(self.contract.address)
        if code in (b"", HexBytes("0x")):
            raise RuntimeError("No contract code at contract_address")

    # ---------------- Utils ----------------

    def _build_common_tx(self) -> Dict[str, Any]:
        """
        EIP-1559 params tuned for Polygon Amoy (min tip ~25 gwei).
        Falls back to legacy if something goes wrong.
        """
        nonce = self.w3.eth.get_transaction_count(
            self.owner, block_identifier="pending"
        )
        try:
            latest_block = self.w3.eth.get_block("latest")
            base_fee = latest_block.get("baseFeePerGas")
            if base_fee is None:
                raise RuntimeError("No baseFeePerGas in block (1559 not active?)")

            # Try to get a suggested priority fee; not all clients expose it
            try:
                suggested_tip = self.w3.eth.max_priority_fee  # web3.py >=6 attr
            except Exception:
                # fee_history gives priority fee rewards percentiles; we pick median if available
                try:
                    fh = self.w3.eth.fee_history(1, "latest", [50])
                    rewards = fh.get("reward")
                    suggested_tip = rewards[0][0] if rewards and rewards[0] else 0
                except Exception:
                    suggested_tip = 0

            # Amoy enforces a relatively high min tip; use at least 30 gwei
            min_tip_gwei = 30
            tip = max(suggested_tip, self.w3.to_wei(min_tip_gwei, "gwei"))

            # Give headroom for base fee spikes
            max_fee = base_fee * 2 + tip

            return {
                "chainId": self.chain_id,
                "nonce": nonce,
                "type": 2,
                "maxPriorityFeePerGas": tip,
                "maxFeePerGas": max_fee,
            }
        except Exception:
            # Legacy fallback (some RPCs still accept it on PoS sidechains)
            # Keep it comfortably high to avoid "below minimum" errors.
            return {
                "chainId": self.chain_id,
                "nonce": nonce,
                "gasPrice": self.w3.to_wei(60, "gwei"),
            }

    @staticmethod
    def keccak32(data: bytes) -> str:
        """Hash arbitrary bytes to a bytes32 (0x… hex string)."""
        return Web3.to_hex(Web3.keccak(data))

    @staticmethod
    def _to_bytes32(value: Any) -> bytes:
        """
        Normalize value into a 32-byte binary suitable for bytes32 ABI:
        - accepts '0x…' hex, bare hex, bytes, bytearray, HexBytes
        """
        if isinstance(value, (bytes, bytearray, HexBytes)):
            b = HexBytes(value)
        else:
            s = str(value)
            if not s.startswith("0x"):
                s = "0x" + s
            b = HexBytes(s)
        if len(b) != 32:
            raise ValueError(f"bytes32 must be 32 bytes; got {len(b)} bytes")
        return bytes(b)

    @staticmethod
    def bytes32_from_text(text: str) -> str:
        """Convenience: keccak(text) -> 0x… hex string (32 bytes)."""
        return Web3.to_hex(Web3.keccak(text=text))

    def _sign_send_wait(
        self, tx: Dict[str, Any], gas_buffer: float = 1.1, timeout: int = 180
    ) -> TxReceipt:
        """Estimate gas (if missing), sign, broadcast, wait for receipt."""
        if "gas" not in tx:
            gas_estimate = self.w3.eth.estimate_gas(tx)
            tx["gas"] = int(gas_estimate * gas_buffer)
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        if receipt.status != 1:
            raise RuntimeError(f"Transaction failed: {tx_hash.hex()}")
        return receipt

    # ---------------- Reads ----------------

    def is_valid(self, token_id: int) -> bool:
        return bool(self.contract.functions.isValid(int(token_id)).call())

    def get_tourist_info(self, token_id: int) -> TouristInfo:
        kyc, itin, valid_until, revoked = self.contract.functions.getTouristInfo(
            int(token_id)
        ).call()
        return TouristInfo(
            kycHash=Web3.to_hex(kyc),
            itineraryHash=Web3.to_hex(itin),
            validUntil=int(valid_until),
            isRevoked=bool(revoked),
        )

    # ---------------- Writes (owner-only) ----------------

    def issue_id(
        self,
        tourist: str,
        kyc_hash_hex32: Any,
        itinerary_hash_hex32: Any,
        validity_seconds: int,
        value_wei: int = 0,
    ) -> Tuple[int, TxReceipt]:
        """
        Calls issueID(tourist, kycHash, itineraryHash, validityDuration)
        Accepts kyc_hash_hex32/itinerary_hash_hex32 as 0x-hex, bare hex, bytes, or HexBytes.
        Returns (tokenId, receipt). tokenId is parsed from IDIssued event (or -1 if not found).
        """
        tourist = self.w3.to_checksum_address(tourist)

        # ✅ Normalize to fixed 32-byte values for ABI
        kyc_b32 = self._to_bytes32(kyc_hash_hex32)
        itin_b32 = self._to_bytes32(itinerary_hash_hex32)

        fn = self.contract.functions.issueID(
            tourist, kyc_b32, itin_b32, int(validity_seconds)
        )
        tx = fn.build_transaction(
            self._build_common_tx() | {"from": self.owner, "value": int(value_wei)}
        )

        receipt = self._sign_send_wait(tx)

        # Parse tokenId from events with multiple fallback strategies
        token_id = -1

        # Strategy 1: Try to get IDIssued event
        try:
            for log in receipt.logs:
                try:
                    decoded_log = self.contract.events.IDIssued().process_log(log)
                    token_id = int(decoded_log["args"]["tokenId"])
                    break
                except Exception:
                    continue
        except Exception as e:
            print(f"Warning: Could not parse IDIssued event: {e}")

        # Strategy 2: If IDIssued failed, try Transfer event (ERC721 minting creates a Transfer from 0x0)
        if token_id == -1:
            try:
                for log in receipt.logs:
                    try:
                        decoded_log = self.contract.events.Transfer().process_log(log)
                        # Check if this is a mint (from address 0x0) to our tourist
                        if (
                            decoded_log["args"]["from"]
                            == "0x0000000000000000000000000000000000000000"
                            and decoded_log["args"]["to"].lower() == tourist.lower()
                        ):
                            token_id = int(decoded_log["args"]["tokenId"])
                            print(f"Got token ID {token_id} from Transfer event")
                            break
                    except Exception:
                        continue
            except Exception as e:
                print(f"Warning: Could not parse Transfer event: {e}")

        # Strategy 3: Final fallback - check balance (less reliable but better than nothing)
        if token_id == -1:
            try:
                balance = self.contract.functions.balanceOf(tourist).call()
                if balance > 0:
                    print(
                        f"Fallback: Tourist now has {balance} tokens after transaction"
                    )
                    # This doesn't give us the exact token ID, but we know the transaction succeeded
            except Exception:
                pass

        return token_id, receipt

    def revoke_id(self, token_id: int) -> TxReceipt:
        fn = self.contract.functions.revokeID(int(token_id))
        tx = fn.build_transaction(self._build_common_tx() | {"from": self.owner})
        return self._sign_send_wait(tx)


# ---------- Example usage ----------
if __name__ == "__main__":
    client = TouristIDClient()
    print("Connected to chain ID:", client.chain_id)
    print("Contract owner:", client.owner)

    # Prepare sample hashes (keccak over text) — returns '0x…' 32-byte hex
    kyc_hash = client.bytes32_from_text("test-kyc")
    itin_hash = client.bytes32_from_text("test-itinerary")

    # This also works even if you pass bare hex (no '0x') thanks to _to_bytes32:
    # kyc_hash = kyc_hash[2:]

    token_id, rcpt = client.issue_id(
        tourist=client.owner,  # mint to self for demo
        kyc_hash_hex32=kyc_hash,  # accepts 0x…, bare hex, bytes
        itinerary_hash_hex32=itin_hash,  # accepts 0x…, bare hex, bytes
        validity_seconds=3600,
    )
    print("Issued token:", token_id, rcpt.transactionHash.hex())

    info = client.get_tourist_info(token_id)
    print("Info:", info)

    print("Is valid?", client.is_valid(token_id))

    rcpt2 = client.revoke_id(token_id)
    print("Revoked in:", rcpt2.transactionHash.hex())
