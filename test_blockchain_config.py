#!/usr/bin/env python3
"""
Test blockchain configuration and TouristIDClient initialization
"""

import sys

sys.path.append(".")

from app.core.config import settings


def test_blockchain_config():
    """Test if blockchain configuration is loaded correctly"""
    print("🔧 Blockchain Configuration:")
    print(f"   CONTRACT_ADDRESS: {settings.contract_address}")
    print(f"   OWNER_ADDRESS: {settings.owner_address}")
    print(f"   PRIVATE_KEY: {settings.private_key[:10]}...")
    print(f"   BLOCKCHAIN_RPC_URL: {settings.blockchain_rpc_url}")
    print(f"   BLOCKCHAIN_CHAIN_ID: {settings.blockchain_chain_id}")

    if not settings.contract_address:
        print("❌ CONTRACT_ADDRESS is empty")
        return False
    if not settings.owner_address:
        print("❌ OWNER_ADDRESS is empty")
        return False
    if not settings.private_key:
        print("❌ PRIVATE_KEY is empty")
        return False
    if not settings.blockchain_rpc_url:
        print("❌ BLOCKCHAIN_RPC_URL is empty")
        return False

    print("✅ All blockchain config values are set")

    # Test TouristIDClient initialization
    try:
        from app.utils.blockchain import TouristIDClient

        print("\n🔗 Testing TouristIDClient initialization...")
        client = TouristIDClient()
        print("✅ TouristIDClient initialized successfully")
        print(f"   Connected to: {client.w3.is_connected()}")
        print(f"   Chain ID: {client.chain_id}")
        print(f"   Owner: {client.owner}")
        print(f"   Contract Address: {client.contract.address}")
        return True
    except Exception as e:
        print(f"❌ TouristIDClient initialization failed: {str(e)}")
        return False


if __name__ == "__main__":
    test_blockchain_config()
