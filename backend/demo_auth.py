#!/usr/bin/env python
"""
Demo script to test JWT authentication and photo management
Run the FastAPI server first: uvicorn app.main:app --reload
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


def demo_authentication():
    """Demonstrate user registration and login"""
    print("=" * 60)
    print("DEMO: User Authentication")
    print("=" * 60)

    # Register a new user
    print("\n1. Registering new user...")
    register_data = {
        "username": "demouser",
        "email": "demo@example.com",
        "password": "demopassword123",
        "name": "Demo User",
    }

    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    if response.status_code == 201:
        print("✓ User registered successfully")
        user_data = response.json()
        print(f"  User ID: {user_data['id']}")
        print(f"  Username: {user_data['username']}")
        print(f"  Email: {user_data['email']}")
    else:
        print(f"✗ Registration failed: {response.json()}")
        return None

    # Login
    print("\n2. Logging in...")
    login_data = {"username": "demouser", "password": "demopassword123"}

    response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    if response.status_code == 200:
        print("✓ Login successful")
        token_data = response.json()
        access_token = token_data["access_token"]
        print(f"  Access Token: {access_token[:50]}...")
        return access_token
    else:
        print(f"✗ Login failed: {response.json()}")
        return None


def demo_photo_management(token):
    """Demonstrate photo creation and management with authentication"""
    print("\n" + "=" * 60)
    print("DEMO: Photo Management")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {token}"}

    # Create a photo
    print("\n1. Creating a new photo...")
    photo_data = {
        "uuid": f"demo-photo-{datetime.now().timestamp()}",
        "original_filename": "demo_photo.jpg",
        "date": datetime.now().isoformat(),
        "title": "Demo Photo",
        "description": "A test photo created via API",
    }

    response = requests.post(
        f"{BASE_URL}/api/photos/", json=photo_data, headers=headers
    )
    if response.status_code == 201:
        print("✓ Photo created successfully")
        created_photo = response.json()
        photo_uuid = created_photo["uuid"]
        print(f"  Photo UUID: {photo_uuid}")
        print(f"  Title: {created_photo['title']}")
    else:
        print(f"✗ Photo creation failed: {response.json()}")
        return

    # List photos
    print("\n2. Listing user's photos...")
    response = requests.get(f"{BASE_URL}/api/photos/", headers=headers)
    if response.status_code == 200:
        photos_response = response.json()
        # Handle both old (list) and new (paginated) response formats
        if isinstance(photos_response, list):
            photos = photos_response
        else:
            photos = photos_response.get('items', [])
        print(f"✓ Found {len(photos)} photo(s)")
        for photo in photos:
            print(f"  - {photo['uuid']}: {photo.get('title', 'Untitled')}")
    else:
        print(f"✗ Failed to list photos: {response.json()}")

    # Update photo
    print("\n3. Updating photo title...")
    update_data = {"title": "Updated Demo Photo"}
    response = requests.patch(
        f"{BASE_URL}/api/photos/{photo_uuid}/", json=update_data, headers=headers
    )
    if response.status_code == 200:
        print("✓ Photo updated successfully")
        updated_photo = response.json()
        print(f"  New title: {updated_photo['title']}")
    else:
        print(f"✗ Failed to update photo: {response.json()}")

    # Get specific photo
    print("\n4. Getting photo details...")
    response = requests.get(f"{BASE_URL}/api/photos/{photo_uuid}/", headers=headers)
    if response.status_code == 200:
        photo = response.json()
        print("✓ Photo retrieved successfully")
        print(f"  UUID: {photo['uuid']}")
        print(f"  Title: {photo['title']}")
        print(f"  Description: {photo['description']}")
    else:
        print(f"✗ Failed to get photo: {response.json()}")

    # Delete photo
    print("\n5. Deleting photo...")
    response = requests.delete(f"{BASE_URL}/api/photos/{photo_uuid}/", headers=headers)
    if response.status_code == 200:
        print("✓ Photo deleted successfully")
    else:
        print(f"✗ Failed to delete photo: {response.json()}")


def demo_authorization():
    """Demonstrate that users can only access their own photos"""
    print("\n" + "=" * 60)
    print("DEMO: Authorization (Photo Ownership)")
    print("=" * 60)

    # Create two users
    print("\n1. Creating two users...")

    # User 1
    user1_data = {
        "username": "user1",
        "email": "user1@example.com",
        "password": "password123",
    }
    requests.post(f"{BASE_URL}/api/auth/register", json=user1_data)

    # User 2
    user2_data = {
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123",
    }
    requests.post(f"{BASE_URL}/api/auth/register", json=user2_data)

    # Login both users
    token1 = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": "user1", "password": "password123"},
    ).json()["access_token"]
    token2 = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": "user2", "password": "password123"},
    ).json()["access_token"]

    print("✓ Two users created and logged in")

    # User1 creates a photo
    print("\n2. User1 creates a photo...")
    photo_data = {
        "uuid": f"user1-photo-{datetime.now().timestamp()}",
        "original_filename": "user1_photo.jpg",
        "date": datetime.now().isoformat(),
    }
    response = requests.post(
        f"{BASE_URL}/api/photos/",
        json=photo_data,
        headers={"Authorization": f"Bearer {token1}"},
    )
    photo_uuid = response.json()["uuid"]
    print(f"✓ User1 created photo: {photo_uuid}")

    # User2 tries to access User1's photo
    print("\n3. User2 tries to access User1's photo...")
    response = requests.get(
        f"{BASE_URL}/api/photos/{photo_uuid}/",
        headers={"Authorization": f"Bearer {token2}"},
    )
    if response.status_code == 403:
        print("✓ Access denied (expected) - User2 cannot access User1's photo")
    else:
        print(f"✗ Unexpected result: {response.status_code}")

    # User2 tries to delete User1's photo
    print("\n4. User2 tries to delete User1's photo...")
    response = requests.delete(
        f"{BASE_URL}/api/photos/{photo_uuid}/",
        headers={"Authorization": f"Bearer {token2}"},
    )
    if response.status_code == 403:
        print("✓ Delete denied (expected) - User2 cannot delete User1's photo")
    else:
        print(f"✗ Unexpected result: {response.status_code}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("PhotoSafe API Demo")
    print("Make sure the FastAPI server is running at http://localhost:8000")
    print("=" * 60)

    try:
        # Test if server is running
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("\n✗ Server is not responding correctly")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to server. Please start it with:")
        print("   cd backend && uvicorn app.main:app --reload")
        exit(1)

    # Run demos
    token = demo_authentication()
    if token:
        demo_photo_management(token)

    demo_authorization()

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)
