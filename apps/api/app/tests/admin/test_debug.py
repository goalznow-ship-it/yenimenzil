
import pytest

from app.models.enums import UserRole


@pytest.mark.asyncio
async def test_super_admin_can_access_me_endpoint(client, auth_user):
    """Test that a super admin can access the /me endpoint."""
    # Create a super admin user
    _super_admin_user = await auth_user(email="superadmin@test.az", role=UserRole.SUPER_ADMIN)
    
    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Access the /me endpoint
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    
    data = response.json()
    assert data["role"] == "super_admin"
    assert data["email"] == "superadmin@test.az"


@pytest.mark.asyncio
async def test_super_admin_can_access_admin_dashboard_stats(client, auth_user):
    """Test that a super admin can access the admin dashboard stats endpoint."""
    # Create a super admin user
    _super_admin_user = await auth_user(email="superadmin@test.az", role=UserRole.SUPER_ADMIN)
    
    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Access admin dashboard stats
    response = await client.get("/api/v1/admin/dashboard/stats")
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    assert response.status_code == 200
