"""
Manual test script for refresh token functionality
This can be run manually when the backend server is running
"""
import requests
import time

BASE_URL = "http://localhost:8000/api"


def test_refresh_token_flow():
    """Test the refresh token flow manually"""

    # 1. Register a test user
    print("1. Registering test user...")
    register_data = {
        "username": "refreshtest",
        "email": "refreshtest@example.com",
        "password": "testpass123",
        "name": "Refresh Test User",
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("   ✓ User registered successfully")
        elif response.status_code == 400:
            # User already exists, that's okay for this test
            try:
                error_detail = response.json().get("detail", "")
                if "already registered" in error_detail.lower():
                    print("   ✓ User already exists (continuing)")
                else:
                    print(
                        f"   ✗ Registration failed: {response.status_code} - {error_detail}"
                    )
                    return
            except:
                print("   ✓ User already exists (continuing)")
        else:
            print(f"   ✗ Registration failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # 2. Login to get tokens
    print("\n2. Logging in to get tokens...")
    login_data = {"username": "refreshtest", "password": "testpass123"}

    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            print(f"   ✗ Login failed: {response.status_code} - {response.text}")
            return

        tokens = response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")

        if not access_token or not refresh_token:
            print(f"   ✗ Missing tokens in response: {tokens}")
            return

        print(f"   ✓ Got access token: {access_token[:20]}...")
        print(f"   ✓ Got refresh token: {refresh_token[:20]}...")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # 3. Use access token to get user info
    print("\n3. Using access token to get user info...")
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code != 200:
            print(
                f"   ✗ Failed to get user info: {response.status_code} - {response.text}"
            )
            return

        user = response.json()
        print(f"   ✓ Got user info: {user['username']} ({user['email']})")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # 4. Use refresh token to get new access token
    print("\n4. Using refresh token to get new access token...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/refresh", json={"refresh_token": refresh_token}
        )

        if response.status_code != 200:
            print(f"   ✗ Refresh failed: {response.status_code} - {response.text}")
            return

        new_tokens = response.json()
        new_access_token = new_tokens.get("access_token")
        new_refresh_token = new_tokens.get("refresh_token")

        if not new_access_token or not new_refresh_token:
            print(f"   ✗ Missing tokens in response: {new_tokens}")
            return

        print(f"   ✓ Got new access token: {new_access_token[:20]}...")
        print(f"   ✓ Got new refresh token: {new_refresh_token[:20]}...")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # 5. Use new access token to verify it works
    print("\n5. Using new access token to verify it works...")
    try:
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )

        if response.status_code != 200:
            print(
                f"   ✗ Failed to get user info: {response.status_code} - {response.text}"
            )
            return

        user = response.json()
        print(f"   ✓ New token works! User: {user['username']} ({user['email']})")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    # 6. Test invalid refresh token
    print("\n6. Testing invalid refresh token...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/refresh", json={"refresh_token": "invalid_token"}
        )

        if response.status_code == 401:
            print(f"   ✓ Invalid token correctly rejected")
        else:
            print(f"   ✗ Expected 401, got: {response.status_code} - {response.text}")
            return

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    print("Testing Refresh Token Functionality")
    print("=" * 50)
    print("Make sure the backend server is running on http://localhost:8000")
    print("=" * 50)
    test_refresh_token_flow()
