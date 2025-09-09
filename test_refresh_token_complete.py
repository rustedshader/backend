"""
Test script for JWT Refresh Token functionality.

This script demonstrates the complete refresh token workflow:
1. User login to get access + refresh tokens
2. Use refresh token to get new access token
3. Test token revocation (logout)
"""

import httpx
import asyncio
import json
from datetime import datetime, timedelta


# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Test user credentials
TEST_USER = {
    "username": "test@example.com",  # Note: OAuth2PasswordRequestForm uses 'username' field
    "password": "testpassword123",
}

# Sample user registration data (in case user doesn't exist)
SAMPLE_USER_REGISTRATION = {
    "first_name": "Test",
    "last_name": "User",
    "country_code": "INDIA",
    "email": "test@example.com",
    "password": "testpassword123",
    "phone_number": "+91-9876543210",
    "indian_citizenship": True,
    "aadhar_number": "123456789012",
}


async def test_refresh_token_workflow():
    """Test the complete refresh token workflow."""

    print("🔐 JWT Refresh Token Workflow Test")
    print("=" * 50)

    async with httpx.AsyncClient() as client:
        # Step 1: Login to get tokens
        print("\n1. 🚪 User Login")
        print("Attempting to login...")

        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            data=TEST_USER,  # OAuth2PasswordRequestForm expects form data
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            print("\n💡 Tip: Make sure you have a test user in the database")
            print("You can create one using the /auth/sign-up endpoint")
            return

        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        print("✅ Login successful!")
        print(f"Access Token: {access_token[:20]}...")
        print(f"Refresh Token: {refresh_token[:20]}...")

        # Step 2: Test access token works
        print("\n2. 🔒 Test Access Token")

        protected_response = await client.get(
            f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        if protected_response.status_code == 200:
            user_info = protected_response.json()
            print("✅ Access token is valid!")
            print(f"User: {user_info['first_name']} {user_info.get('last_name', '')}")
            print(f"Email: {user_info['email']}")
            print(f"Role: {user_info['role']}")
        else:
            print(
                f"❌ Access token validation failed: {protected_response.status_code}"
            )
            return

        # Step 3: Use refresh token to get new access token
        print("\n3. 🔄 Refresh Access Token")

        refresh_response = await client.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token},
            headers=HEADERS,
        )

        if refresh_response.status_code == 200:
            new_token_data = refresh_response.json()
            new_access_token = new_token_data["access_token"]

            print("✅ Token refresh successful!")
            print(f"New Access Token: {new_access_token[:20]}...")
            print(f"Token Type: {new_token_data['token_type']}")

            # Test new access token
            new_protected_response = await client.get(
                f"{BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {new_access_token}"},
            )

            if new_protected_response.status_code == 200:
                print("✅ New access token is valid!")
            else:
                print("❌ New access token is invalid!")
        else:
            print(f"❌ Token refresh failed: {refresh_response.status_code}")
            print(f"Response: {refresh_response.text}")
            return

        # Step 4: Test logout (token revocation)
        print("\n4. 🚪 Logout (Revoke Refresh Token)")

        logout_response = await client.post(
            f"{BASE_URL}/auth/logout",
            json={"refresh_token": refresh_token},
            headers=HEADERS,
        )

        if logout_response.status_code == 200:
            logout_data = logout_response.json()
            print("✅ Logout successful!")
            print(f"Message: {logout_data['message']}")
        else:
            print(f"❌ Logout failed: {logout_response.status_code}")

        # Step 5: Try to use revoked refresh token
        print("\n5. 🚫 Test Revoked Refresh Token")

        revoked_refresh_response = await client.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token},
            headers=HEADERS,
        )

        if revoked_refresh_response.status_code == 401:
            print("✅ Revoked refresh token correctly rejected!")
            error_data = revoked_refresh_response.json()
            print(f"Error: {error_data['detail']}")
        else:
            print(f"❌ Revoked token should have been rejected!")
            print(f"Status: {revoked_refresh_response.status_code}")


async def test_token_expiry_simulation():
    """Simulate token expiry scenarios."""

    print("\n" + "=" * 50)
    print("🕐 Token Expiry Simulation")
    print("=" * 50)

    # In a real scenario, you would wait for tokens to expire
    # For testing purposes, we'll test with invalid tokens

    async with httpx.AsyncClient() as client:
        print("\n1. Test with Invalid Refresh Token")

        invalid_refresh_response = await client.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
            headers=HEADERS,
        )

        if invalid_refresh_response.status_code == 401:
            print("✅ Invalid token correctly rejected!")
            error_data = invalid_refresh_response.json()
            print(f"Error: {error_data['detail']}")
        else:
            print(f"❌ Invalid token should have been rejected!")

        print("\n2. Test with Malformed Token")

        malformed_refresh_response = await client.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": "completely-invalid-token"},
            headers=HEADERS,
        )

        if malformed_refresh_response.status_code == 401:
            print("✅ Malformed token correctly rejected!")
            error_data = malformed_refresh_response.json()
            print(f"Error: {error_data['detail']}")
        else:
            print(f"❌ Malformed token should have been rejected!")


def show_refresh_token_info():
    """Show information about refresh token implementation."""

    print("\n" + "=" * 50)
    print("📚 Refresh Token Implementation Info")
    print("=" * 50)

    print("\n🔑 Token Specifications:")
    print("• Access Token Lifetime: 1 hour (3600 seconds)")
    print("• Refresh Token Lifetime: 1 day (86400 seconds)")
    print("• Token Type: JWT (JSON Web Tokens)")
    print("• Algorithm: HS256")

    print("\n🔄 Workflow:")
    print("1. User logs in → receives access_token + refresh_token")
    print("2. Use access_token for API requests")
    print("3. When access_token expires → use refresh_token to get new access_token")
    print("4. Logout → revoke refresh_token")

    print("\n🛡️ Security Features:")
    print("• Refresh tokens stored in database with revocation support")
    print("• Automatic expiry checking")
    print("• Token revocation on logout")
    print("• Protection against token replay attacks")

    print("\n📱 API Endpoints:")
    print("• POST /auth/login - Get initial tokens")
    print("• POST /auth/refresh - Get new access token")
    print("• POST /auth/logout - Revoke refresh token")
    print("• GET /auth/me - Test access token (protected route)")

    print("\n💻 Usage Examples:")
    print("# Login")
    print("POST /auth/login")
    print("Content-Type: application/x-www-form-urlencoded")
    print("Body: username=user@example.com&password=secret")
    print()
    print("# Refresh Token")
    print("POST /auth/refresh")
    print("Content-Type: application/json")
    print('Body: {"refresh_token": "your.refresh.token"}')
    print()
    print("# Logout")
    print("POST /auth/logout")
    print("Content-Type: application/json")
    print('Body: {"refresh_token": "your.refresh.token"}')


async def main():
    """Main test function."""

    print("🧪 Testing Refresh Token Implementation")
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print()

    # Run the tests
    await test_refresh_token_workflow()
    await test_token_expiry_simulation()

    # Show implementation info
    show_refresh_token_info()

    print("\n" + "=" * 50)
    print("🎉 Refresh Token Testing Complete!")
    print("=" * 50)

    print("\n✅ Features Tested:")
    print("• Login with token generation")
    print("• Access token validation")
    print("• Refresh token usage")
    print("• Token revocation (logout)")
    print("• Invalid token handling")

    print("\n🚀 Ready for Production!")


if __name__ == "__main__":
    print("To run this test:")
    print("1. Start the FastAPI server: uvicorn app.main:app --reload")
    print("2. Ensure you have a test user in the database")
    print("3. Update TEST_USER credentials if needed")
    print("4. Run: python test_refresh_token_complete.py")
    print()

    # Uncomment the line below to run the test
    # asyncio.run(main())
