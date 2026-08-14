import pytest
from sqlalchemy import select

from app.models.agency import Agency


@pytest.mark.asyncio
async def test_admin_agencies_requires_auth(client):
    """Test that admin agencies endpoint requires authentication."""
    response = await client.get("/api/v1/admin/agencies")
    assert response.status_code == 401  # Not authenticated


@pytest.mark.asyncio
async def test_admin_agencies_requires_admin_role(client, auth_user):
    """Test that admin agencies endpoint requires admin/moderator/super_admin role."""
    # Create a regular user
    _regular_user = await auth_user(email="regular@test.az", role="user")

    # Login as regular user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Try to access admin agencies
    response = await client.get("/api/v1/admin/agencies")
    assert response.status_code == 403  # Insufficient permissions


@pytest.mark.asyncio
async def test_admin_agencies_allows_moderator(client, auth_user):
    """Test that admin agencies endpoint allows moderator role."""
    # Create a moderator user
    _moderator_user = await auth_user(email="moderator@test.az", role="moderator")

    # Login as moderator
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "moderator@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Access admin agencies
    response = await client.get("/api/v1/admin/agencies")
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
async def test_admin_agencies_listing(client, auth_user, db):
    """Test that admin agencies endpoint returns correct data."""
    # Create a super admin user
    _super_admin_user = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a few test agencies
    agency1 = Agency(
        name="Test Agency 1",
        slug="test-agency-1",
        email="agency1@test.az",
        phone="+994500000001",
        website="https://agency1.test.az",
        description="First test agency",
        is_verified=False,
    )
    agency2 = Agency(
        name="Test Agency 2",
        slug="test-agency-2",
        email="agency2@test.az",
        phone="+994500000002",
        website="https://agency2.test.az",
        description="Second test agency",
        is_verified=True,
    )
    db.add_all([agency1, agency2])
    await db.commit()

    # Get all agencies from database to verify counts
    result = await db.execute(select(Agency))
    all_agencies = result.scalars().all()
    assert len(all_agencies) >= 2

    # Access admin agencies endpoint
    response = await client.get("/api/v1/admin/agencies")
    assert response.status_code == 200

    data = response.json()
    assert len(data["data"]) >= 2

    # Check that we can find our test agencies in the response
    names_in_response = [agency["name"] for agency in data["data"]]
    assert "Test Agency 1" in names_in_response
    assert "Test Agency 2" in names_in_response

    # Test filtering by is_verified
    response = await client.get("/api/v1/admin/agencies?is_verified=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    for agency in data["data"]:
        assert agency["is_verified"] == True

    # Test search
    response = await client.get("/api/v1/admin/agencies?search=Agency 1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert any("Agency 1" in agency["name"] for agency in data["data"])

    # Test pagination
    response = await client.get("/api/v1/admin/agencies?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["pagination"]["limit"] == 1
    assert data["pagination"]["page"] == 1


@pytest.mark.asyncio
async def test_admin_agency_detail(client, auth_user, db):
    """Test getting a specific agency's details."""
    # Create a super admin user
    _super_admin_user = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a test agency
    agency = Agency(
        name="Test Agency",
        slug="test-agency",
        email="agency@test.az",
        phone="+994500000001",
        website="https://agency.test.az",
        description="Test agency",
        is_verified=False,
    )
    db.add(agency)
    await db.commit()

    # Get the agency detail
    response = await client.get(f"/api/v1/admin/agencies/{agency.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(agency.id)
    assert data["name"] == "Test Agency"
    assert data["email"] == "agency@test.az"
    assert data["is_verified"] == False
    assert data["description"] == "Test agency"


@pytest.mark.asyncio
async def test_admin_agency_update(client, auth_user, db):
    """Test updating an agency's details."""
    # Create a super admin user
    _super_admin_user = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a test agency
    agency = Agency(
        name="Test Agency",
        slug="test-agency",
        email="agency@test.az",
        phone="+994500000001",
        website="https://agency.test.az",
        description="Test agency",
        is_verified=False,
    )
    db.add(agency)
    await db.commit()

    # Update the agency
    update_data = {
        "name": "Updated Agency Name",
        "is_verified": True,
    }
    response = await client.patch(
        f"/api/v1/admin/agencies/{agency.id}", json=update_data
    )
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(agency.id)
    assert data["name"] == "Updated Agency Name"
    assert data["is_verified"] == True
    # Other fields should remain unchanged
    assert data["email"] == "agency@test.az"


@pytest.mark.asyncio
async def test_admin_agency_delete(client, auth_user, db):
    """Test deactivating an agency."""
    # Create a super admin user
    _super_admin_user = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a test agency
    agency = Agency(
        name="Test Agency",
        slug="test-agency",
        email="agency@test.az",
        phone="+994500000001",
        website="https://agency.test.az",
        description="Test agency",
        is_verified=False,
    )
    db.add(agency)
    await db.commit()

    # Deactivate the agency
    response = await client.delete(f"/api/v1/admin/agencies/{agency.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Agency deactivated successfully"
    assert data["agency_id"] == str(agency.id)

    # Verify the agency is deactivated
    response = await client.get(f"/api/v1/admin/agencies/{agency.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["is_verified"] == False
