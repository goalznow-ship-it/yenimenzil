from uuid import uuid4

import pytest

from app.models.property import Property


@pytest.mark.asyncio
async def test_admin_property_detail_requires_auth(client):
    """Test that admin property detail endpoint requires authentication."""
    property_id = uuid4()
    response = await client.get(f"/api/v1/admin/listings/{property_id}")
    assert response.status_code == 401  # Not authenticated


@pytest.mark.asyncio
async def test_admin_property_detail_requires_admin_role(client, auth_user):
    """Test that admin property detail endpoint requires admin/moderator/super_admin role."""
    # Create a regular user
    _regular_user = await auth_user(email="regular@test.az", role="user")

    # Login as regular user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Try to access admin property detail
    property_id = uuid4()
    response = await client.get(f"/api/v1/admin/listings/{property_id}")
    assert response.status_code == 403  # Insufficient permissions


@pytest.mark.asyncio
async def test_admin_property_detail_allows_moderator(client, auth_user):
    """Test that admin property detail endpoint allows moderator role."""
    # Create a moderator user
    _moderator_user = await auth_user(email="moderator@test.az", role="moderator")

    # Login as moderator
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "moderator@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Access admin property detail (will be 404 if property doesn't exist, but not 403)
    property_id = uuid4()
    response = await client.get(f"/api/v1/admin/listings/{property_id}")
    # Should be 404 (not found) not 403 (permission denied) if we have permissions
    assert response.status_code != 403

    # If we get 401, that means login failed
    if response.status_code == 401:
        raise AssertionError("Login failed - got 401 Unauthorized")

    # 404 is expected for non-existent property
    if response.status_code == 404:
        assert True  # This is what we expect
    else:
        # Any other 2xx status is also acceptable
        assert response.status_code < 400


@pytest.mark.asyncio
async def test_admin_property_detail_returns_correct_structure(client, auth_user):
    """Test that admin property detail returns the correct data structure when property exists."""
    # Create a super admin user
    _super_admin_user = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a regular user to own the property
    owner_user = await auth_user(email="owner@test.az", role="user")

    # Login as owner to create property
    owner_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@test.az", "password": "supersecret1"},
    )
    assert owner_login.status_code == 200

    # Create a property in draft status
    property_data = {
        "title": "Test Property for Detail",
        "description": "A test property for detail endpoint",
        "deal_type": "sale",
        "property_type": "apartment",
        "price": 100000,
        "currency": "AZN",
        "rooms": 2,
        "bedrooms": 1,
        "bathrooms": 1,
        "area_total": 50,
        "area_living": 30,
        "floor": 1,
        "total_floors": 5,
        "building_type": "new",
        "repair_status": "renovated",
        "document_type": "extract",
        "location": {
            "latitude": 40.4093,
            "longitude": 49.8502,
            "address_text": "Narimanov r., Gənclik",
            "city": "Baku",
            "district": "Narimanov",
            "neighborhood": "Gənclik",
            "metro": "Gənclik",
        },
        "features": ["elevator"],
        "media": [
            {
                "url": "https://example.com/image1.jpg",
                "alt": "Test image",
                "is_cover": True,
            }
        ],
    }

    # Create the property
    create_response = await client.post("/api/v1/properties", json=property_data)
    assert create_response.status_code == 201
    property_data = create_response.json()
    property_id = property_data["id"]

    # Now login as super admin again
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert admin_login.status_code == 200

    # Get the admin property detail
    detail_response = await client.get(f"/api/v1/admin/listings/{property_id}")
    assert detail_response.status_code == 200

    detail_data = detail_response.json()

    # Check that all required fields are present
    assert "id" in detail_data
    assert "title" in detail_data
    assert "seller" in detail_data
    assert "agency" in detail_data
    assert "agent" in detail_data
    assert "reports" in detail_data
    assert "moderation_timeline" in detail_data
    assert "analytics" in detail_data
    assert "duplicate_signals" in detail_data

    # Check seller information
    assert detail_data["seller"]["id"] == str(owner_user.id)
    assert detail_data["seller"]["email"] == "owner@test.az"
    assert detail_data["seller"]["full_name"] == "Test Sahib"

    # Check that basic property fields are present
    assert detail_data["title"] == "Test Property for Detail"
    assert detail_data["price"] == 100000.0
    assert detail_data["rooms"] == 2


@pytest.mark.asyncio
async def test_admin_property_detail_duplicate_detection(client, auth_user, db):
    """Two near-identical listings must surface as duplicate signals."""
    from app.tests.conftest import make_property_payload

    await auth_user(email="superadmin@test.az", role="super_admin")
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    owner = await auth_user(email="owner@test.az", role="owner")

    create_response = await client.post(
        "/api/v1/properties",
        json=make_property_payload(owner.id),
    )
    assert create_response.status_code == 201, create_response.text
    prop_id = create_response.json()["id"]

    # Re-login as super admin to override the cookies set by auth_user for owner
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Move the listing to pending_review so it can be approved
    from sqlalchemy import select as sa_select

    prop_result = await db.execute(sa_select(Property).where(Property.id == prop_id))
    prop_row = prop_result.scalar_one()
    prop_row.status = "pending_review"
    await db.commit()

    # Approve the first listing so it is active
    approve_response = await client.post(f"/api/v1/admin/listings/{prop_id}/approve")
    assert approve_response.status_code == 200, approve_response.text

    # Second listing: same owner, same district, ~same price/area/rooms
    duplicate_response = await client.post(
        "/api/v1/properties",
        json=make_property_payload(owner.id),
    )
    assert duplicate_response.status_code == 201, duplicate_response.text
    dup_id = duplicate_response.json()["id"]

    # The property creation call with the super admin cookie works, but the
    # second creation above may have reset cookies; re-login to be safe
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    dup_result = await db.execute(sa_select(Property).where(Property.id == dup_id))
    dup_row = dup_result.scalar_one()
    dup_row.status = "pending_review"
    await db.commit()

    approve_response = await client.post(f"/api/v1/admin/listings/{dup_id}/approve")

    # Get the admin detail for the first property
    detail_response = await client.get(f"/api/v1/admin/listings/{prop_id}")
    assert detail_response.status_code == 200
    detail_data = detail_response.json()

    assert "duplicate_signals" in detail_data
    signals = detail_data["duplicate_signals"]
    matches = [s for s in signals if s["id"] == dup_id]
    assert matches, f"expected duplicate signals for {dup_id}, got {signals}"
    match = matches[0]
    assert match["signals"]
    assert match["confidence"] >= 40
    assert match["flag_for_review"] is True
