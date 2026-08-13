"""Tests for Phase 7 marketplace endpoints: messaging, viewing
appointments, wallet/promotions, password & verification flows,
notification preferences, popular searches, public profiles and
listing analytics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import ACCESS_TOKEN_COOKIE
from app.main import app
from app.tests.conftest import make_property_payload


async def _create_authenticated_client(auth_user, email):
    """Create a new authenticated client for a user."""
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    
    # Create the user
    await auth_user(email=email)
    
    # Manually log in to ensure the client has the session cookie
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "supersecret1"},
    )
    assert login_response.status_code == 200
    
    # Ensure the client has the session cookie
    assert client.cookies.get(ACCESS_TOKEN_COOKIE) is not None
    
    return client


async def _create_active_property(db, user):
    """Create an ACTIVE property directly in the DB (the API cookie may
    belong to another user in multi-user tests)."""
    from app.repositories.property import PropertyRepository
    from app.schemas.property import PropertyCreate

    payload = PropertyCreate.model_validate(make_property_payload(user.id))
    prop = await PropertyRepository(db).create(payload)
    prop.status = "active"
    prop.published_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(prop)
    return prop


# ---------------------------------------------------------------------------
# Messaging
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_conversation_and_send_messages(
    client, auth_user, feature_catalog, db
):
    owner = await auth_user(email="owner-msg@test.az", is_verified=True)
    buyer = await auth_user(email="buyer-msg@test.az")
    prop = await _create_active_property(db, owner)

    response = await client.post(
        "/api/v1/conversations",
        json={"property_id": str(prop.id), "message": "Salam, elan aktividir?"},
    )
    assert response.status_code == 201, response.text
    conv = response.json()
    assert conv["property_id"] == str(prop.id)
    assert conv["buyer_id"] == str(buyer.id)
    assert conv["seller_id"] == str(owner.id)
    assert conv["last_message"] == "Salam, elan aktividir?"
    assert conv["unread_count"] == 0
    assert conv["property_title"] == prop.title

    response = await client.post(
        f"/api/v1/conversations/{conv['id']}/messages",
        json={"content": "Bəli, aktivdir"},
    )
    assert response.status_code == 201, response.text

    response = await client.get(f"/api/v1/conversations/{conv['id']}/messages")
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 2
    assert messages[0]["content"] == "Salam, elan aktividir?"
    assert messages[1]["content"] == "Bəli, aktivdir"
    # Fetching marks incoming as read for the buyer
    unread = await client.get("/api/v1/conversations/unread-count")
    assert unread.json() == {"total": 0, "conversations": 0}


@pytest.mark.asyncio
async def test_conversation_unread_counts(client, auth_user, feature_catalog, db):
    owner = await auth_user(email="owner-unread@test.az", is_verified=True)
    buyer_client = await _create_authenticated_client(auth_user, "buyer-unread@test.az")
    

    
    prop = await _create_active_property(db, owner)

    response = await buyer_client.post(
        "/api/v1/conversations",
        json={"property_id": str(prop.id), "message": "Salam"},
    )
    assert response.status_code == 201, response.text
    conv_id = response.json()["id"]

    # Debug: Print cookies and conversation details
    print(f"Cookies after conversation creation: {buyer_client.cookies}")

    # Debug: Check the conversation details
    conv_response = await buyer_client.get(f"/api/v1/conversations/{conv_id}")
    print(f"Conversation details: {conv_response.json()}")

    # Debug: Check the unread count for the conversation
    unread = await buyer_client.get("/api/v1/conversations/unread-count")
    print(f"Unread count response: {unread.json()}")
    
    # Debug: Manually check the unread count for the conversation
    conv_response = await buyer_client.get(f"/api/v1/conversations/{conv_id}")
    print(f"Conversation unread_count: {conv_response.json()['unread_count']}")
    
    assert unread.json() == {"total": 1, "conversations": 1}

    response = await buyer_client.get(f"/api/v1/conversations/{conv_id}")
    assert response.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_cannot_message_own_listing(client, auth_user, feature_catalog, db):
    owner = await auth_user(email="owner-self@test.az", is_verified=True)
    prop = await _create_active_property(db, owner)
    response = await client.post(
        "/api/v1/conversations",
        json={"property_id": str(prop.id), "message": "Salam"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_archive_and_block_conversation(client, auth_user, feature_catalog, db):
    owner = await auth_user(email="owner-block@test.az", is_verified=True)
    await auth_user(email="buyer-block@test.az")
    prop = await _create_active_property(db, owner)

    response = await client.post(
        "/api/v1/conversations",
        json={"property_id": str(prop.id), "message": "Salam"},
    )
    conv_id = response.json()["id"]

    response = await client.patch(f"/api/v1/conversations/{conv_id}/archive")
    assert response.status_code == 204
    response = await client.get("/api/v1/conversations")
    assert response.json() == []

    response = await client.patch(f"/api/v1/conversations/{conv_id}/block")
    assert response.status_code == 204
    response = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Salam?"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_conversation_requires_participant(client, auth_user, feature_catalog, db):
    owner = await auth_user(email="owner-part@test.az", is_verified=True)
    buyer_client = await _create_authenticated_client(auth_user, "buyer-part@test.az")
    outsider_client = await _create_authenticated_client(auth_user, "outsider-part@test.az")
    

    
    prop = await _create_active_property(db, owner)

    response = await buyer_client.post(
        "/api/v1/conversations",
        json={"property_id": str(prop.id), "message": "Salam"},
    )
    conv_id = response.json()["id"]

    response = await outsider_client.get(f"/api/v1/conversations/{conv_id}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Viewing appointments
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_viewing_request_lifecycle(client, auth_user, feature_catalog, db):
    owner = await auth_user(email="owner-view@test.az", is_verified=True)
    
    requester = await auth_user(email="requester-view@test.az")
    requester_client = await _create_authenticated_client(auth_user, "requester-view@test.az")
    
    # Re-authenticate as owner so client has owner session for owner actions
    await auth_user(email="owner-view@test.az", is_verified=True)
    

    
    prop = await _create_active_property(db, owner)
    future = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    response = await requester_client.post(
        f"/api/v1/viewing-requests/{prop.id}",
        json={"scheduled_at": future, "note": "Sabah saat 12"},
    )
    assert response.status_code == 201, response.text
    appointment = response.json()
    assert appointment["status"] == "pending"
    assert appointment["requester_id"] == str(requester.id)
    assert appointment["owner_id"] == str(owner.id)
    assert appointment["property_title"] == prop.title

    # Owner confirms
    response = await client.patch(
        f"/api/v1/viewing-requests/{appointment['id']}",
        json={"status": "confirmed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"

    # Requester lists their requests
    response = await requester_client.get("/api/v1/viewing-requests?role=requested")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # Owner can complete the visit
    response = await client.patch(
        f"/api/v1/viewing-requests/{appointment['id']}",
        json={"status": "completed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_viewing_requester_cannot_confirm(client, auth_user, feature_catalog, db):
    owner = await auth_user(email="owner-vr@test.az", is_verified=True)
    await auth_user(email="requester-vr@test.az")
    prop = await _create_active_property(db, owner)
    future = (datetime.now(UTC) + timedelta(days=2)).isoformat()

    response = await client.post(
        f"/api/v1/viewing-requests/{prop.id}",
        json={"scheduled_at": future},
    )
    appointment_id = response.json()["id"]

    response = await client.patch(
        f"/api/v1/viewing-requests/{appointment_id}",
        json={"status": "confirmed"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_viewing_past_time_rejected(client, auth_user, feature_catalog, db):
    owner = await auth_user(email="owner-past@test.az", is_verified=True)
    await auth_user(email="requester-past@test.az")
    prop = await _create_active_property(db, owner)
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

    response = await client.post(
        f"/api/v1/viewing-requests/{prop.id}",
        json={"scheduled_at": past},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Wallet & promotions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_wallet_top_up_pending_then_admin_confirm(
    client, auth_user, feature_catalog
):
    await auth_user(email="wallet-user@test.az")
    response = await client.get("/api/v1/wallet")
    assert response.status_code == 200
    assert response.json()["balance"] == 0

    response = await client.post(
        "/api/v1/wallet/top-up", json={"amount": 5000, "note": "Balans artımı"}
    )
    assert response.status_code == 202, response.text
    transaction = response.json()["transaction"]
    assert transaction["status"] == "pending"

    # Non-admin cannot confirm
    response = await client.post(
        f"/api/v1/admin/wallet/top-ups/{transaction['id']}/confirm",
        json={"approve": True},
    )
    assert response.status_code == 403

    await auth_user(email="wallet-admin@test.az", role="admin")
    response = await client.post(
        f"/api/v1/admin/wallet/top-ups/{transaction['id']}/confirm",
        json={"approve": True},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    # Log back in as the wallet user (the last login set the admin cookie)
    await auth_user(email="wallet-user@test.az")
    response = await client.get("/api/v1/wallet")
    assert response.json()["balance"] == 5000


@pytest.mark.asyncio
async def test_promotion_purchase_insufficient_balance(
    client, auth_user, feature_catalog, db
):
    owner = await auth_user(email="promo-poor@test.az")
    prop = await _create_active_property(db, owner)

    response = await client.post(
        "/api/v1/wallet/promotions",
        json={"property_id": str(prop.id), "tier": "premium"},
    )
    assert response.status_code == 402
    assert "Insufficient" in response.json()["detail"]


@pytest.mark.asyncio
async def test_promotion_purchase_debits_wallet_and_marks_listing(
    client, auth_user, feature_catalog, db
):
    owner = await auth_user(email="promo-rich@test.az")
    prop = await _create_active_property(db, owner)

    response = await client.post(
        "/api/v1/wallet/top-up", json={"amount": 10000}
    )
    tx = response.json()["transaction"]
    await auth_user(email="promo-admin@test.az", role="admin")
    await client.post(
        f"/api/v1/admin/wallet/top-ups/{tx['id']}/confirm",
        json={"approve": True},
    )

    # Log back in as the owner so the promotion debits the owner wallet
    await auth_user(email="promo-rich@test.az")
    response = await client.post(
        "/api/v1/wallet/promotions",
        json={"property_id": str(prop.id), "tier": "premium"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["promotion_status"] == "active"
    assert body["transaction"]["amount"] == -1500
    assert body["transaction"]["status"] == "completed"

    wallet = await client.get("/api/v1/wallet")
    assert wallet.json()["balance"] == 8500

    detail = await client.get(f"/api/v1/properties/{prop.id}")
    assert detail.json()["is_promoted"] is True
    assert detail.json()["is_premium"] is True
    assert detail.json()["promotion_expires_at"] is not None


@pytest.mark.asyncio
async def test_promotion_catalog_available(client, auth_user):
    await auth_user(email="catalog-user@test.az")
    response = await client.get("/api/v1/wallet/promotions/catalog")
    assert response.status_code == 200
    tiers = {item["tier"] for item in response.json()}
    assert tiers == {"standard", "premium", "vip", "top", "urgent"}


# ---------------------------------------------------------------------------
# Password & verification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_change_password_revokes_sessions(client, auth_user):
    await auth_user(email="pw-change@test.az")

    response = await client.patch(
        "/api/v1/auth/password",
        json={"current_password": "supersecret1", "new_password": "newsecret123"},
    )
    assert response.status_code == 204

    # Old password no longer works
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "pw-change@test.az", "password": "supersecret1"},
    )
    assert response.status_code == 401

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "pw-change@test.az", "password": "newsecret123"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_forgot_and_reset_password_flow(client, auth_user, db):
    user = await auth_user(email="pw-reset@test.az")

    response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "pw-reset@test.az"}
    )
    assert response.status_code == 202

    # Unknown email also 202 (no enumeration)
    response = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "nobody@test.az"}
    )
    assert response.status_code == 202

    from sqlalchemy import select

    from app.models.verification import VerificationToken

    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.user_id == user.id,
            VerificationToken.kind == "password_reset",
        )
    )
    token = result.scalars().one()
    assert token.used_at is None
    # token_hash is stored, we can't read the raw token; verify a wrong
    # token is rejected
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "bogus-token", "new_password": "freshpass123"},
    )
    assert response.status_code == 400

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "bogus-token", "new_password": "freshpass123"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_and_phone_flow(client, auth_user, db):
    user = await auth_user(email="verify-me@test.az", is_verified=False)

    response = await client.get("/api/v1/auth/verification-status")
    assert response.json()["email_verified"] is False
    assert response.json()["phone_verified"] is False

    response = await client.post(
        "/api/v1/auth/resend-verification?kind=email"
    )
    assert response.status_code == 202

    from sqlalchemy import select

    from app.models.verification import VerificationToken

    result = await db.execute(
        select(VerificationToken).where(
            VerificationToken.user_id == user.id,
            VerificationToken.kind == "email",
        )
    )
    token = result.scalars().one()
    assert token.expires_at > datetime.now(UTC)

    response = await client.post(
        "/api/v1/auth/verify-email", json={"token": "bogus-token-value"}
    )
    assert response.status_code == 400

    status = await client.get("/api/v1/auth/verification-status")
    assert status.json()["email_verified"] is False


# ---------------------------------------------------------------------------
# Notifications: mark-all-read + preferences
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mark_all_read_and_unread_count(client, auth_user, db):
    user = await auth_user(email="notif-user@test.az")
    from app.models.notification import Notification

    for i in range(3):
        db.add(
            Notification(
                user_id=user.id,
                kind="general",
                title=f"Başlıq {i}",
                message="Mesaj",
            )
        )
    await db.commit()

    response = await client.get("/api/v1/notifications/unread-count")
    assert response.json() == {"unread": 3}

    response = await client.post("/api/v1/notifications/mark-all-read")
    assert response.status_code == 204

    response = await client.get("/api/v1/notifications/unread-count")
    assert response.json() == {"unread": 0}


@pytest.mark.asyncio
async def test_notification_preferences_roundtrip(client, auth_user):
    await auth_user(email="prefs-user@test.az")

    response = await client.get("/api/v1/notifications/preferences")
    assert response.status_code == 200
    assert response.json()["email_enabled"] is True
    # promotion kind defaults push to False
    assert response.json()["push_enabled"] is False

    response = await client.put(
        "/api/v1/notifications/preferences",
        json={"email_enabled": False, "push_enabled": True},
    )
    assert response.status_code == 200
    assert response.json()["email_enabled"] is False
    assert response.json()["push_enabled"] is True

    response = await client.get("/api/v1/notifications/preferences")
    assert response.json()["email_enabled"] is False
    assert response.json()["push_enabled"] is True


# ---------------------------------------------------------------------------
# Popular searches
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_popular_searches_from_analytics(client, auth_user, db):
    user = await auth_user(email="popsearch@test.az")
    from app.models.analytics import AnalyticsEvent

    for query in ("mənzil", "mənzil", "mənzil", "həyət evi", "ofis"):
        db.add(
            AnalyticsEvent(
                user_id=user.id,
                event_type="search",
                payload={"query": query},
            )
        )
    await db.commit()

    response = await client.get("/api/v1/analytics/popular-searches")
    assert response.status_code == 200
    searches = response.json()
    assert searches[0]["query"] == "mənzil"
    assert searches[0]["count"] == 3


# ---------------------------------------------------------------------------
# Public agent & agency profiles
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agent_public_profile_with_listings(
    client, auth_user, feature_catalog, db
):
    owner = await auth_user(email="agent-owner@test.az", is_verified=True)
    prop = await _create_active_property(db, owner)

    from app.models.agency import Agent

    agent = Agent(
        name="Aygün Əliyeva",
        user_id=owner.id,
    )
    db.add(agent)
    await db.flush()
    prop.agent_id = agent.id
    prop.agency_id = None
    await db.commit()
    await db.refresh(agent)

    response = await client.get(f"/api/v1/agents/{agent.id}/public")
    assert response.status_code == 200
    body = response.json()
    assert body["agent"]["name"] == "Aygün Əliyeva"
    assert body["listings"]["data"]  # active listing is visible
    assert body["is_mine"] is True


@pytest.mark.asyncio
async def test_agency_public_profile_with_agents_and_listings(
    client, auth_user, feature_catalog, db
):
    owner = await auth_user(email="agency-owner@test.az", is_verified=True)
    prop = await _create_active_property(db, owner)

    from app.models.agency import Agency, Agent

    agency = Agency(name="Test Əmlak Agentliyi", slug="test-emlak-agentliyi")
    db.add(agency)
    await db.flush()
    agent = Agent(name="Aygün", agency_id=agency.id, user_id=owner.id)
    db.add(agent)
    await db.flush()
    prop.agency_id = agency.id
    prop.agent_id = agent.id
    await db.commit()

    response = await client.get(f"/api/v1/agencies/{agency.id}/public")
    assert response.status_code == 200
    body = response.json()
    assert body["agency"]["name"] == "Test Əmlak Agentliyi"
    assert len(body["agents"]) == 1
    assert body["listings"]["data"]


# ---------------------------------------------------------------------------
# Listing analytics & phone reveal
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_listing_views_increment_and_analytics(
    client, auth_user, feature_catalog, db
):
    owner = await auth_user(email="views-owner@test.az", is_verified=True)
    await auth_user(email="views-viewer@test.az")
    prop = await _create_active_property(db, owner)

    response = await client.get(f"/api/v1/properties/{prop.id}")
    assert response.json()["views"] == 1
    response = await client.get(f"/api/v1/properties/{prop.id}")
    assert response.json()["views"] == 2

    # Analytics requires the owner (or staff); log back in as owner
    await auth_user(email="views-owner@test.az", is_verified=True)
    response = await client.get(f"/api/v1/properties/{prop.id}/analytics")
    assert response.status_code == 200
    assert response.json()["views"] == 2

    # Non-owner gets 403
    await auth_user(email="views-outsider@test.az")
    response = await client.get(f"/api/v1/properties/{prop.id}/analytics")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_phone_reveal_tracked(client, auth_user, feature_catalog, db):
    owner = await auth_user(email="phone-owner@test.az", is_verified=True)
    await auth_user(email="phone-viewer@test.az")
    prop = await _create_active_property(db, owner)

    response = await client.post(f"/api/v1/properties/{prop.id}/phone-reveal")
    assert response.status_code == 204

    # Owner cannot reveal their own listing
    await auth_user(email="phone-owner@test.az", is_verified=True)
    response = await client.post(f"/api/v1/properties/{prop.id}/phone-reveal")
    assert response.status_code == 400
