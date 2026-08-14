import pytest
from sqlalchemy import select

from app.models.user import User


@pytest.mark.asyncio
async def test_admin_users_requires_auth(client):
    """Test that admin users endpoint requires authentication."""
    response = await client.get("/api/v1/admin/users")
    assert response.status_code == 401  # Not authenticated


@pytest.mark.asyncio
async def test_admin_users_requires_admin_role(client, auth_user):
    """Test that admin users endpoint requires admin/moderator/super_admin role."""
    # Create a regular user
    _regular = await auth_user(email="regular@test.az", role="user")

    # Login as regular user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Try to access admin users
    response = await client.get("/api/v1/admin/users")
    assert response.status_code == 403  # Insufficient permissions


@pytest.mark.asyncio
async def test_admin_users_allows_moderator(client, auth_user):
    """Test that admin users endpoint allows moderator role."""
    # Create a moderator user
    _moderator = await auth_user(email="moderator@test.az", role="moderator")

    # Login as moderator
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "moderator@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Access admin users
    response = await client.get("/api/v1/admin/users")
    assert response.status_code == 200

    data = response.json()
    # Check that expected fields are present
    assert "data" in data
    assert "pagination" in data
    assert "filters" in data
    assert isinstance(data["data"], list)
    assert isinstance(data["pagination"], dict)
    assert isinstance(data["filters"], dict)


@pytest.mark.asyncio
async def test_admin_users_listing(client, auth_user, db):
    """Test that admin users endpoint returns correct data."""
    # Create a super admin user
    _super_admin = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a few test users
    # Regular user
    _regular = await auth_user(email="regular@test.az", role="user")
    # Moderator user
    _moderator = await auth_user(email="moderator@test.az", role="moderator")
    # Admin user
    _admin = await auth_user(email="admin@test.az", role="admin")
    # Super admin user (already exists from above)

    # Get all users from database to verify counts
    result = await db.execute(select(User))
    all_users = result.scalars().all()
    assert len(all_users) >= 4  # At least the four we created

    # Access admin users endpoint
    response = await client.get("/api/v1/admin/users")
    assert response.status_code == 200

    data = response.json()
    assert len(data["data"]) >= 4

    # Check that we can find our test users in the response
    emails_in_response = [user["email"] for user in data["data"]]
    assert "regular@test.az" in emails_in_response
    assert "moderator@test.az" in emails_in_response
    assert "admin@test.az" in emails_in_response
    assert "superadmin@test.az" in emails_in_response

    # Test filtering by role
    response = await client.get("/api/v1/admin/users?role=moderator")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    for user in data["data"]:
        assert user["role"] == "moderator"

    # Test search
    response = await client.get("/api/v1/admin/users?search=regular")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert any("regular" in user["email"] for user in data["data"])

    # Test pagination
    response = await client.get("/api/v1/admin/users?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["pagination"]["limit"] == 2
    assert data["pagination"]["page"] == 1


@pytest.mark.asyncio
async def test_admin_user_detail(client, auth_user, db):
    """Test getting a specific user's details."""
    # Create a super admin user
    _super_admin = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a test user
    test_user = await auth_user(email="testuser@test.az", role="user")

    # Re-login as super admin to override the cookies set by auth_user for test_user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Get the user detail
    response = await client.get(f"/api/v1/admin/users/{test_user.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == "testuser@test.az"
    assert data["full_name"] == "Test Sahib"
    assert data["role"] == "user"
    assert data["is_active"] == True
    assert data["is_verified"] == False
    assert "profile" in data
    assert data["profile"]["avatar_url"] is None
    assert data["profile"]["bio"] is None


@pytest.mark.asyncio
async def test_admin_user_update(client, auth_user, db):
    """Test updating a user's details."""
    # Create a super admin user
    _super_admin = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a test user
    test_user = await auth_user(email="testuser@test.az", role="user")

    # Re-login as super admin to override the cookies set by auth_user for test_user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Update the user
    update_data = {
        "full_name": "Updated Name",
        "role": "moderator",
        "is_active": False,
    }
    response = await client.patch(
        f"/api/v1/admin/users/{test_user.id}", json=update_data
    )
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["full_name"] == "Updated Name"
    assert data["role"] == "moderator"
    assert data["is_active"] == False
    # Email should remain unchanged
    assert data["email"] == "testuser@test.az"


@pytest.mark.asyncio
async def test_admin_user_delete(client, auth_user, db):
    """Test deactivating a user."""
    # Create a super admin user
    _super_admin = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a test user
    test_user = await auth_user(email="testuser@test.az", role="user")

    # Re-login as super admin to override the cookies set by auth_user for test_user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Deactivate the user
    response = await client.delete(f"/api/v1/admin/users/{test_user.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "User deactivated successfully"
    assert data["user_id"] == str(test_user.id)

    # Verify the user is deactivated
    response = await client.get(f"/api/v1/admin/users/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == False
