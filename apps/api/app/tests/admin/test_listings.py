import pytest
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.models.enums import PropertyStatus, DealType, PropertyType, UserRole, Currency
from app.models.property import Property, PropertyLocation
from app.models.user import User
from app.repositories.property import PropertyRepository
from app.schemas.property import PropertyCreate, PropertyLocationCreate
from sqlalchemy import select


@pytest.mark.asyncio
async def test_admin_listings_requires_auth(client):
    """Test that admin listings endpoint requires authentication."""
    response = await client.get("/api/v1/admin/listings")
    assert response.status_code == 401  # Not authenticated


@pytest.mark.asyncio
async def test_admin_listings_requires_admin_role(client, auth_user):
    """Test that admin listings endpoint requires admin/moderator/super_admin role."""
    # Create a regular user
    _regular_user = await auth_user(email="regular@test.az", role="user")
    
    # Login as regular user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Try to access admin listings
    response = await client.get("/api/v1/admin/listings")
    assert response.status_code == 403  # Insufficient permissions


@pytest.mark.asyncio
async def test_admin_listings_allows_moderator(client, auth_user):
    """Test that admin listings endpoint allows moderator role."""
    # Create a moderator user
    _moderator_user = await auth_user(email="moderator@test.az", role="moderator")
    
    # Login as moderator
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "moderator@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Access admin listings
    response = await client.get("/api/v1/admin/listings")
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
async def test_admin_listing_approve_requires_auth(client):
    """Test that approving a listing requires authentication."""
    property_id = uuid4()
    response = await client.post(f"/api/v1/admin/listings/{property_id}/approve")
    assert response.status_code == 401  # Not authenticated


@pytest.mark.asyncio
async def test_admin_listing_approve_requires_admin_role(client, auth_user):
    """Test that approving a listing requires admin/moderator/super_admin role."""
    # Create a regular user
    _regular_user = await auth_user(email="regular@test.az", role="user")
    
    # Login as regular user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Create a property to test with
    # First create a user to own the property
    owner_user = await auth_user(email="owner@test.az", role="user")
    
    # Login as owner to create property (simplified - in reality we'd need to create the property)
    # For this test, we'll just test the authorization aspect
    
    # Try to approve a listing (will fail with 404 since property doesn't exist, but should be 403 if not authorized)
    property_id = uuid4()
    response = await client.post(f"/api/v1/admin/listings/{property_id}/approve")
    # Should be 403 for insufficient permissions, not 401 (since we're authenticated)
    assert response.status_code == 403  # Insufficient permissions


@pytest.mark.asyncio
async def test_admin_listing_approve_success(client, auth_user, db):
    """Test that approving a listing works correctly for authorized users."""
    # Create a super admin user
    _super_admin_user = await auth_user(email="superadmin@test.az", role="super_admin")
    
    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Create a user to own the property
    owner_user = await auth_user(email="owner@test.az", role="user")
    
    # Get the owner user from database
    owner_result = await db.execute(
        select(User).where(User.email == "owner@test.az")
    )
    owner = owner_result.scalar_one()
    
    # Create a property using the repository (which will generate reference_code and slug)
    property_create = PropertyCreate(
        title="Test Property",
        description="A test property",
        deal_type=DealType.SALE,
        property_type=PropertyType.APARTMENT,
        price=100000,
        currency=Currency.AZN,
        rooms=2,
        bedrooms=1,
        bathrooms=1,
        area_total=50,
        area_living=30,
        area_land=None,
        floor=1,
        total_floors=5,
        building_type="new",
        repair_status="renovated",
        document_type="extract",
        seller_kind="owner",
        status=PropertyStatus.PENDING_REVIEW.value,
        owner_id=owner.id,
        location=PropertyLocationCreate(
            latitude=40.4093,
            longitude=49.8502,
            address_text="Narimanov r., Gənclik",
            city="Baku",
            district="Narimanov",
            settlement=None,
            neighborhood=None,
            metro=None,
        ),
        media=[],
        features=[],
        price_history=[],
    )
    
    property_repo = PropertyRepository(db)
    property_obj = await property_repo.create(property_create)
    await db.commit()
    
    # Approve the property
    response = await client.post(
        f"/api/v1/admin/listings/{property_obj.id}/approve",
        params={"reason": "Test approval"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Listing approved successfully"
    assert data["old_status"] == PropertyStatus.PENDING_REVIEW.value
    assert data["new_status"] == PropertyStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_admin_listing_reject_requires_reason(client, auth_user):
    """Test that rejecting a listing requires a reason."""
    # Create a moderator user
    _moderator_user = await auth_user(email="moderator@test.az", role="moderator")
    
    # Login as moderator
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "moderator@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Try to reject a listing without providing reason
    property_id = uuid4()
    response = await client.post(f"/api/v1/admin/listings/{property_id}/reject")
    # Should be 422 for validation error (missing required reason parameter)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_listings_bulk_actions_require_auth(client):
    """Test that bulk actions require authentication."""
    response = await client.post("/api/v1/admin/listings/bulk-approve", json=[])
    assert response.status_code == 401  # Not authenticated


@pytest.mark.asyncio
async def test_admin_listings_bulk_actions_require_admin_role(client, auth_user):
    """Test that bulk actions require admin/moderator/super_admin role."""
    # Create a regular user
    _regular_user = await auth_user(email="regular@test.az", role="user")
    
    # Login as regular user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Try to access bulk approve endpoint
    response = await client.post("/api/v1/admin/listings/bulk-approve", json=[])
    assert response.status_code == 403  # Insufficient permissions
