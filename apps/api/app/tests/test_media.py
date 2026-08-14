"""Phase 10: media production flow tests (validation, cover, reorder, delete)."""

from __future__ import annotations

import io
import uuid

import pytest

from app.tests.conftest import make_property_payload


def _png_bytes(width: int = 800, height: int = 600) -> bytes:
    """Generate a small valid PNG in memory."""
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (width, height), (120, 140, 200)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
async def seller(client, auth_user):
    user = await auth_user(email="media@test.az", is_verified=True)
    return {"user": user}


@pytest.fixture()
async def listing(client, seller, feature_catalog):
    payload = make_property_payload(seller["user"].id, status="draft", media=[])
    resp = await client.post("/api/v1/properties", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _fake_upload(monkeypatch):
    from app.api.v1 import endpoints

    monkeypatch.setattr(
        endpoints.properties,
        "upload_file",
        lambda c, n, t: "https://media.test/x.jpg",
    )


async def test_upload_validates_file_type(client, seller, listing):
    resp = await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("evil.txt", b"not an image", "text/plain")},
    )
    assert resp.status_code == 400


async def test_upload_sets_cover_and_returns_media(
    client, seller, listing, monkeypatch
):
    """Upload with storage mocked: first image becomes cover."""
    _fake_upload(monkeypatch)

    resp = await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("photo1.png", _png_bytes(), "image/png")},
    )
    assert resp.status_code == 201, resp.text
    media = resp.json()[0]["media"]
    assert len(media) == 1
    assert media[0]["is_cover"] is True
    assert media[0]["url"].startswith("https://media.test/")


async def test_set_cover_and_reorder(client, seller, listing, monkeypatch):
    _fake_upload(monkeypatch)

    await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("a.png", _png_bytes(), "image/png")},
    )
    second = await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("b.png", _png_bytes(), "image/png")},
    )
    media_list = second.json()[0]["media"]
    assert len(media_list) == 2
    first_id, second_id = media_list[0]["id"], media_list[1]["id"]
    assert media_list[0]["is_cover"] is True

    # Set second as cover
    set_cover = await client.patch(
        f"/api/v1/properties/{listing['id']}/media/{second_id}",
        json={"is_cover": True},
    )
    assert set_cover.status_code == 200
    covers = [m for m in set_cover.json()[0]["media"] if m["is_cover"]]
    assert len(covers) == 1
    assert covers[0]["id"] == second_id

    # Reorder (second first)
    reorder = await client.post(
        f"/api/v1/properties/{listing['id']}/media/reorder",
        json={"media_ids": [second_id, first_id]},
    )
    assert reorder.status_code == 200
    ordered = reorder.json()[0]["media"]
    assert [m["id"] for m in ordered] == [second_id, first_id]


async def test_reorder_mismatch_rejected(client, seller, listing, monkeypatch):
    _fake_upload(monkeypatch)
    await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("a.png", _png_bytes(), "image/png")},
    )

    resp = await client.post(
        f"/api/v1/properties/{listing['id']}/media/reorder",
        json={"media_ids": [str(uuid.uuid4())]},
    )
    assert resp.status_code == 400


async def test_delete_media_promotes_next_cover(client, seller, listing, monkeypatch):
    _fake_upload(monkeypatch)
    await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("a.png", _png_bytes(), "image/png")},
    )
    resp = await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("b.png", _png_bytes(), "image/png")},
    )
    media_list = resp.json()[0]["media"]
    cover = next(m for m in media_list if m["is_cover"])

    deleted = await client.delete(
        f"/api/v1/properties/{listing['id']}/media/{cover['id']}",
    )
    assert deleted.status_code == 200
    remaining = deleted.json()[0]["media"]
    assert len(remaining) == 1
    assert remaining[0]["is_cover"] is True


async def test_media_ownership_enforced(
    client, seller, listing, auth_user, monkeypatch
):
    _fake_upload(monkeypatch)
    resp = await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("a.png", _png_bytes(), "image/png")},
    )
    media_id = resp.json()[0]["media"][0]["id"]

    await auth_user(email="media2@test.az")

    denied = await client.delete(
        f"/api/v1/properties/{listing['id']}/media/{media_id}",
    )
    assert denied.status_code == 403


async def test_replace_media_replaces_file_and_cleans_old(
    client, seller, listing, monkeypatch
):
    from app.api.v1 import endpoints

    calls: dict[str, list] = {"uploads": [], "deletes": []}

    def _fake_upload(content, name, ctype):
        calls["uploads"].append(name)
        return f"https://media.test/{len(calls['uploads'])}.jpg"

    def _fake_delete(url):
        calls["deletes"].append(url)

    monkeypatch.setattr(endpoints.properties, "upload_file", _fake_upload)
    monkeypatch.setattr(endpoints.properties, "delete_file", _fake_delete)

    created = await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("a.png", _png_bytes(), "image/png")},
    )
    assert created.status_code == 201, created.text
    media_id = created.json()[0]["media"][0]["id"]

    replaced = await client.put(
        f"/api/v1/properties/{listing['id']}/media/{media_id}",
        files={"file": ("new.png", _png_bytes(), "image/png")},
    )
    assert replaced.status_code == 200, replaced.text
    media = replaced.json()[0]["media"][0]
    assert media["id"] == media_id
    assert media["url"] == "https://media.test/3.jpg"
    assert media["is_cover"] is True
    assert calls["deletes"] == ["https://media.test/1.jpg", "https://media.test/2.jpg"]


async def test_replace_media_validates_file(client, seller, listing, monkeypatch):
    _fake_upload(monkeypatch)
    created = await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("a.png", _png_bytes(), "image/png")},
    )
    media_id = created.json()[0]["media"][0]["id"]

    resp = await client.put(
        f"/api/v1/properties/{listing['id']}/media/{media_id}",
        files={"file": ("evil.txt", b"not an image", "text/plain")},
    )
    assert resp.status_code == 400


async def test_replace_media_ownership_enforced(
    client, seller, listing, auth_user, monkeypatch
):
    _fake_upload(monkeypatch)
    created = await client.post(
        f"/api/v1/properties/{listing['id']}/media",
        files={"files": ("a.png", _png_bytes(), "image/png")},
    )
    media_id = created.json()[0]["media"][0]["id"]

    await auth_user(email="media3@test.az")

    denied = await client.put(
        f"/api/v1/properties/{listing['id']}/media/{media_id}",
        files={"file": ("b.png", _png_bytes(), "image/png")},
    )
    assert denied.status_code == 403
