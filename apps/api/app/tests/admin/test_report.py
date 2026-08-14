import pytest
from sqlalchemy import select

from app.models.enums import (
    Currency,
    DealType,
    PropertyStatus,
    PropertyType,
    ReportReason,
    ReportStatus,
)
from app.models.report import Report
from app.models.user import User
from app.repositories.property import PropertyRepository
from app.schemas.property import PropertyCreate, PropertyLocationCreate


@pytest.mark.asyncio
async def test_admin_reports_requires_auth(client):
    """Test that admin reports endpoint requires authentication."""
    response = await client.get("/api/v1/admin/reports")
    assert response.status_code == 401  # Not authenticated


@pytest.mark.asyncio
async def test_admin_reports_requires_admin_role(client, auth_user):
    """Test that admin reports endpoint requires admin/moderator/super_admin role."""
    # Create a regular user
    _regular = await auth_user(email="regular@test.az", role="user")

    # Login as regular user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "regular@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Try to access admin reports
    response = await client.get("/api/v1/admin/reports")
    assert response.status_code == 403  # Insufficient permissions


@pytest.mark.asyncio
async def test_admin_reports_allows_moderator(client, auth_user):
    """Test that admin reports endpoint allows moderator role."""
    # Create a moderator user
    _moderator = await auth_user(email="moderator@test.az", role="moderator")

    # Login as moderator
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "moderator@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Access admin reports
    response = await client.get("/api/v1/admin/reports")
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
async def test_admin_reports_listing(client, auth_user, db):
    """Test that admin reports endpoint returns correct data."""
    # Create a super admin user
    _super_admin = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a test user to act as reporter directly in the database
    reporter_user = User(
        email="reporter@test.az",
        phone="+994500000002",
        password_hash="not-a-real-hash",
        full_name="Test Reporter",
        role="user",
    )
    db.add(reporter_user)
    await db.commit()
    await db.refresh(reporter_user)

    # Create a property for the reports to reference
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
        owner_id=reporter_user.id,
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

    report1 = Report(
        reporter_id=reporter_user.id,
        property_id=property_obj.id,
        reason=ReportReason.FAKE,
        description="Fake report",
        status=ReportStatus.OPEN,
    )
    report2 = Report(
        reporter_id=reporter_user.id,
        property_id=property_obj.id,
        reason=ReportReason.SCAM,
        description="Scam report",
        status=ReportStatus.RESOLVED,
    )
    db.add_all([report1, report2])
    await db.commit()

    # Access admin reports endpoint
    response = await client.get("/api/v1/admin/reports")
    assert response.status_code == 200

    data = response.json()
    assert len(data["data"]) >= 2

    # Check that we can find our test reports in the response
    reasons_in_response = [report["reason"] for report in data["data"]]
    assert "fake" in reasons_in_response
    assert "scam" in reasons_in_response

    # Test filtering by status
    response = await client.get("/api/v1/admin/reports?status=open")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    for report in data["data"]:
        assert report["status"] == "open"

    # Test search
    response = await client.get("/api/v1/admin/reports?search=scam")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert any(
        "scam" in (report["description"] or "").lower() for report in data["data"]
    )

    # Test pagination
    response = await client.get("/api/v1/admin/reports?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["pagination"]["limit"] == 1
    assert data["pagination"]["page"] == 1


@pytest.mark.asyncio
async def test_admin_report_detail(client, auth_user, db):
    """Test getting a specific report's details."""
    # Create a super admin user
    _super_admin = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a test user to act as reporter
    _reporter = await auth_user(email="reporter@test.az", role="user")

    # Re-login as super admin to override the cookies set by auth_user for reporter_user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a property for the report to reference
    # First get the reporter user from database to ensure we have the persistent object
    reporter_result = await db.execute(
        select(User).where(User.email == "reporter@test.az")
    )
    reporter = reporter_result.scalar_one()

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
        owner_id=reporter.id,
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

    # Create a test report
    report = Report(
        reporter_id=reporter.id,
        property_id=property_obj.id,
        reason=ReportReason.FAKE,
        description="Fake report",
        status=ReportStatus.OPEN,
    )
    db.add(report)
    await db.commit()

    # Get the report detail
    response = await client.get(f"/api/v1/admin/reports/{report.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(report.id)
    assert data["reason"] == "fake"
    assert data["description"] == "Fake report"
    assert data["status"] == "open"


@pytest.mark.asyncio
async def test_admin_report_update(client, auth_user, db):
    """Test updating a report's details."""
    # Create a super admin user
    _super_admin = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a test user to act as reporter
    _reporter = await auth_user(email="reporter@test.az", role="user")

    # Re-login as super admin to override the cookies set by auth_user for reporter_user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a property for the report to reference
    # First get the reporter user from database to ensure we have the persistent object
    reporter_result = await db.execute(
        select(User).where(User.email == "reporter@test.az")
    )
    reporter = reporter_result.scalar_one()

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
        owner_id=reporter.id,
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

    # Create a test report
    report = Report(
        reporter_id=reporter.id,
        property_id=property_obj.id,
        reason=ReportReason.FAKE,
        description="Fake report",
        status=ReportStatus.OPEN,
    )
    db.add(report)
    await db.commit()

    # Update the report
    update_data = {
        "description": "Updated fake report description",
        "status": "resolved",
    }
    response = await client.patch(
        f"/api/v1/admin/reports/{report.id}", json=update_data
    )
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(report.id)
    assert data["description"] == "Updated fake report description"
    assert data["status"] == "resolved"
    # Reason should remain unchanged
    assert data["reason"] == "fake"


@pytest.mark.asyncio
async def test_admin_report_delete(client, auth_user, db):
    """Test deleting a report."""
    # Create a super admin user
    _super_admin = await auth_user(email="superadmin@test.az", role="super_admin")

    # Login as super admin
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a test user to act as reporter
    _reporter = await auth_user(email="reporter@test.az", role="user")

    # Re-login as super admin to override the cookies set by auth_user for reporter_user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@test.az", "password": "supersecret1"},
    )
    assert login_response.status_code == 200

    # Create a property for the report to reference
    # First get the reporter user from database to ensure we have the persistent object
    reporter_result = await db.execute(
        select(User).where(User.email == "reporter@test.az")
    )
    reporter = reporter_result.scalar_one()

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
        owner_id=reporter.id,
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

    # Create a test report
    report = Report(
        reporter_id=reporter.id,
        property_id=property_obj.id,
        reason=ReportReason.FAKE,
        description="Fake report",
        status=ReportStatus.OPEN,
    )
    db.add(report)
    await db.commit()

    # Delete the report
    response = await client.delete(f"/api/v1/admin/reports/{report.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Report deleted successfully"
    assert data["report_id"] == str(report.id)

    # Verify the report is deleted
    response = await client.get(f"/api/v1/admin/reports/{report.id}")
    assert response.status_code == 404
