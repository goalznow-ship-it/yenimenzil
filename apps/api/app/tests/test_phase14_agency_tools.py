"""Phase 14: agency tools (team invites, CSV listing import)."""

from __future__ import annotations

import io
import uuid

import pytest


@pytest.mark.asyncio
async def test_agency_invite_accept_flow(client, auth_user, db):
    from app.models.agency import Agent

    admin = await auth_user(email="invite-admin@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()

    agency_row = (
        await client.post(
            "/api/v1/agencies",
            json={"name": "İnkişaf Agentliyi", "slug": "inkisaf-agentliyi"},
        )
    ).json()

    boss = await auth_user(email="invite-boss@test.az", is_verified=True)
    boss.role = "agency_admin"
    await db.commit()
    db.add(
        Agent(
            user_id=boss.id,
            agency_id=uuid.UUID(agency_row["id"]),
            name=boss.full_name or boss.email,
            email=boss.email,
        )
    )
    await db.commit()

    invite_resp = await client.post(
        "/api/v1/agencies/me/invites",
        json={"email": "invite-agent@test.az", "role": "agent"},
    )
    assert invite_resp.status_code == 201, invite_resp.text
    invite = invite_resp.json()
    assert invite["status"] == "pending"
    token = invite["token"]

    listed = (await client.get("/api/v1/agencies/me/invites")).json()
    assert any(i["id"] == invite["id"] for i in listed)

    # wrong email cannot accept
    await auth_user(email="invite-stranger@test.az")
    stranger_client = await _other_client(client, auth_user, "invite-stranger@test.az")
    forbidden = await stranger_client.post(f"/api/v1/agencies/invites/{token}/accept")
    assert forbidden.status_code == 403

    # invitee accepts
    await auth_user(email="invite-agent@test.az")
    invitee_client = await _other_client(client, auth_user, "invite-agent@test.az")
    accepted = await invitee_client.post(f"/api/v1/agencies/invites/{token}/accept")
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["agency_id"] == agency_row["id"]

    # invite cannot be reused
    reused = await invitee_client.post(f"/api/v1/agencies/invites/{token}/accept")
    assert reused.status_code == 409

    # non-admin cannot list invites
    denied = await invitee_client.get("/api/v1/agencies/me/invites")
    assert denied.status_code == 403

    # cancel flow (re-authenticate shared client as agency boss)
    boss2 = await auth_user(email="invite-boss2@test.az", is_verified=True)
    boss2.role = "agency_admin"
    await db.commit()
    db.add(
        Agent(
            user_id=boss2.id,
            agency_id=uuid.UUID(agency_row["id"]),
            name=boss2.full_name or boss2.email,
            email=boss2.email,
        )
    )
    await db.commit()
    invite2 = (
        await client.post(
            "/api/v1/agencies/me/invites",
            json={"email": "invite-cancel@test.az", "role": "agent"},
        )
    ).json()
    cancelled = await client.delete(f"/api/v1/agencies/me/invites/{invite2['id']}")
    assert cancelled.status_code == 204

    # duplicate pending invite rejected
    dup1 = (
        await client.post(
            "/api/v1/agencies/me/invites",
            json={"email": "invite-dup@test.az", "role": "agent"},
        )
    ).json()
    assert dup1["status"] == "pending"
    dup2 = await client.post(
        "/api/v1/agencies/me/invites",
        json={"email": "invite-dup@test.az", "role": "agent"},
    )
    assert dup2.status_code == 409


@pytest.mark.asyncio
async def test_agency_csv_listing_import(client, auth_user, db):
    from app.models.agency import Agent

    admin = await auth_user(email="import-admin@test.az", is_verified=True)
    admin.role = "admin"
    await db.commit()
    agency_row = (
        await client.post(
            "/api/v1/agencies",
            json={"name": "İmport Agentliyi", "slug": "import-agentliyi"},
        )
    ).json()

    boss = await auth_user(email="import-boss@test.az", is_verified=True)
    boss.role = "agency_admin"
    await db.commit()
    db.add(
        Agent(
            user_id=boss.id,
            agency_id=uuid.UUID(agency_row["id"]),
            name=boss.full_name or boss.email,
            email=boss.email,
        )
    )
    await db.commit()

    csv_text = (
        "title,deal_type,property_type,price,currency,rooms,area_total,city,"
        "district,address_text,description,building_type\n"
        "Bakıda 3 otaqlı mənzil,sale,apartment,180000,AZN,3,85,Bakı,Nəsimi,"
        "Nizami küç. 5,Balaca təmir,new\n"
        "Kirayə studiya,rent,apartment,700,AZN,1,40,Bakı,Yasamal,,,old\n"
        "Səhv sətir (qiymət yoxdur),sale,apartment,,AZN,2,60,Bakı,,,,new\n"
    )
    response = await client.post(
        "/api/v1/agencies/me/import/listings",
        files={
            "file": ("listings.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["imported"] == 2
    assert result["skipped"] == 1
    assert result["errors"][0]["row"] == 4

    # imported rows are drafts owned by the agency
    listed = (await client.get("/api/v1/properties/mine?status=draft")).json()
    drafts = listed if isinstance(listed, list) else listed.get("data", [])
    assert len(drafts) == 2
    first_detail = (await client.get(f"/api/v1/properties/{drafts[0]['id']}")).json()
    assert first_detail["agency_id"] == agency_row["id"]

    # non-admin cannot import
    await auth_user(email="import-regular@test.az")
    regular_client = await _other_client(client, auth_user, "import-regular@test.az")
    denied = await regular_client.post(
        "/api/v1/agencies/me/import/listings",
        files={"file": ("l.csv", io.BytesIO(b"title,price\nx,1"), "text/csv")},
    )
    assert denied.status_code == 403


async def _other_client(client, auth_user, email):
    from app.tests.test_phase7_marketplace import _create_authenticated_client

    return await _create_authenticated_client(auth_user, email)
