import pytest
from uuid import uuid4


@pytest.mark.asyncio
async def test_admin_listing_approve_endpoint_exists(client, auth_user):
    """Test that the admin listing approve endpoint exists and checks permissions."""
    # Create a super admin user
    _super_admin_user = await auth_user(email="superadmin@test.az", role="super_admin")
    
    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Try to approve a non-existent listing
    # Should get 404 (not found) not 403 (permission denied) if we have permissions
    property_id = uuid4()
    response = await client.post(f"/api/v1/admin/listings/{property_id}/approve")
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # If we have super admin permissions, we should get 404 (property not found)
    # If we don't have permissions, we should get 403
    # Let's check which one we get
    if response.status_code == 403:
        # This would mean we don't have permissions
        raise AssertionError("Got 403 Forbidden - insufficient permissions")
    elif response.status_code == 404:
        # This means we have permissions but the property doesn't exist
        # This is what we expect
        assert True
    else:
        # Unexpected status code
        raise AssertionError(f"Unexpected status code: {response.status_code}")
