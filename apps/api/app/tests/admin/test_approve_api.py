import pytest


@pytest.mark.asyncio
async def test_admin_listing_approve_via_api(client, auth_user):
    """Test that approving a listing works when created via API."""
    # Create a super admin user
    _super_admin = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a regular user to own the property
    _owner = await auth_user(email="owner@test.az", role="user")

    # Login as owner to create property
    owner_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "owner@test.az", "password": "supersecret1"},
    )
    assert owner_login.status_code == 200

    # Create a property in draft status (since owners can only create drafts)
    property_data = {
        "title": "Test Property",
        "description": "A test property",
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
    print(f"Create response status: {create_response.status_code}")
    print(f"Create response body: {create_response.text}")
    assert create_response.status_code == 201
    property_data = create_response.json()
    property_id = property_data["id"]

    # Submit the property for review (changes status from draft to pending_review)
    submit_response = await client.post(f"/api/v1/properties/{property_id}/submit")
    assert submit_response.status_code == 200

    # Verify the property is now in pending_review status
    get_response = await client.get(f"/api/v1/properties/{property_id}")
    assert get_response.status_code == 200
    property_data = get_response.json()
    assert property_data["status"] == "pending_review"

    # Now login as super admin again (since we switched to owner)
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert admin_login.status_code == 200

    # Approve the property as super admin
    approve_response = await client.post(
        f"/api/v1/admin/listings/{property_id}/approve",
        params={"reason": "Test approval via API"},
    )
    print(f"Approve response status: {approve_response.status_code}")
    print(f"Approve response body: {approve_response.text}")

    # Should be successful
    assert approve_response.status_code == 200

    approve_data = approve_response.json()
    assert approve_data["message"] == "Listing approved successfully"
    assert approve_data["old_status"] == "pending_review"
    assert approve_data["new_status"] == "active"
