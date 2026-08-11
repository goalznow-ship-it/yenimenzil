
import pytest


@pytest.mark.asyncio
async def test_admin_dashboard_stats_requires_auth(client):
    """Test that admin dashboard stats requires authentication."""
    response = await client.get("/api/v1/admin/dashboard/stats")
    assert response.status_code == 401  # Not authenticated


@pytest.mark.asyncio
async def test_admin_dashboard_stats_requires_admin_role(client, auth_user):
    """Test that admin dashboard stats requires admin/moderator/super_admin role."""
    # Create a regular user
    _regular_user = await auth_user(email="regular@test.az", role="user")
    
    # Login as regular user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Try to access admin dashboard stats
    response = await client.get("/api/v1/admin/dashboard/stats")
    assert response.status_code == 403  # Insufficient permissions


@pytest.mark.asyncio
async def test_admin_dashboard_stats_allows_moderator(client, auth_user):
    """Test that admin dashboard stats allows moderator role."""
    # Create a moderator user
    _moderator_user = await auth_user(email="moderator@test.az", role="moderator")
    
    # Login as moderator
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "moderator@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Access admin dashboard stats
    response = await client.get("/api/v1/admin/dashboard/stats")
    assert response.status_code == 200
    
    data = response.json()
    # Check that all expected fields are present
    expected_fields = [
        "total_users", "active_users", "total_listings", "active_listings",
        "pending_review", "rejected_listings", "sold", "rented",
        "total_agencies", "total_agents", "reports_open",
        "listings_created_today", "listings_created_this_week"
    ]
    for field in expected_fields:
        assert field in data
        assert isinstance(data[field], int)


@pytest.mark.asyncio
async def test_admin_dashboard_stats_allows_admin(client, auth_user):
    """Test that admin dashboard stats allows admin role."""
    # Create an admin user
    _admin_user = await auth_user(email="admin@test.az", role="admin")
    
    # Login as admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Access admin dashboard stats
    response = await client.get("/api/v1/admin/dashboard/stats")
    assert response.status_code == 200
    
    data = response.json()
    # Check that all expected fields are present
    expected_fields = [
        "total_users", "active_users", "total_listings", "active_listings",
        "pending_review", "rejected_listings", "sold", "rented",
        "total_agencies", "total_agents", "reports_open",
        "listings_created_today", "listings_created_this_week"
    ]
    for field in expected_fields:
        assert field in data
        assert isinstance(data[field], int)


@pytest.mark.asyncio
async def test_admin_dashboard_stats_allows_super_admin(client, auth_user):
    """Test that admin dashboard stats allows super_admin role."""
    # Create a super admin user
    _super_admin_user = await auth_user(email="superadmin@test.az", role="super_admin")
    
    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Access admin dashboard stats
    response = await client.get("/api/v1/admin/dashboard/stats")
    assert response.status_code == 200
    
    data = response.json()
    # Check that all expected fields are present
    expected_fields = [
        "total_users", "active_users", "total_listings", "active_listings",
        "pending_review", "rejected_listings", "sold", "rented",
        "total_agencies", "total_agents", "reports_open",
        "listings_created_today", "listings_created_this_week"
    ]
    for field in expected_fields:
        assert field in data
        assert isinstance(data[field], int)


@pytest.mark.asyncio
async def test_admin_dashboard_charts_endpoints_require_auth(client):
    """Test that admin dashboard charts endpoints require authentication."""
    endpoints = [
        "/api/v1/admin/dashboard/charts/listings-over-time",
        "/api/v1/admin/dashboard/charts/users-over-time",
        "/api/v1/admin/dashboard/charts/deal-type-distribution",
        "/api/v1/admin/dashboard/charts/property-type-distribution",
    ]
    
    for endpoint in endpoints:
        response = await client.get(endpoint)
        assert response.status_code == 401  # Not authenticated


@pytest.mark.asyncio
async def test_admin_dashboard_charts_endpoints_allow_moderator(client, auth_user):
    """Test that admin dashboard charts endpoints allow moderator role."""
    # Create a moderator user
    _moderator_user = await auth_user(email="moderator@test.az", role="moderator")
    
    # Login as moderator
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "moderator@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Test each chart endpoint
    endpoints = [
        "/api/v1/admin/dashboard/charts/listings-over-time",
        "/api/v1/admin/dashboard/charts/users-over-time",
        "/api/v1/admin/dashboard/charts/deal-type-distribution",
        "/api/v1/admin/dashboard/charts/property-type-distribution",
    ]
    
    for endpoint in endpoints:
        response = await client.get(endpoint)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Check that each item in the list has the expected structure
        if len(data) > 0:
            item = data[0]
            if "listings-over-time" in endpoint or "users-over-time" in endpoint:
                assert "date" in item
                assert "count" in item
            elif "deal-type-distribution" in endpoint:
                assert "deal_type" in item
                assert "count" in item
            elif "property-type-distribution" in endpoint:
                assert "property_type" in item
                assert "count" in item
