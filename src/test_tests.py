from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.asyncio.client import Redis

from main import (
    create_bingo_from_template_in_db,
    create_template_in_db,
    create_user_in_db,
    get_and_delete_challenge,
    get_bingo_from_db,
    get_credential_by_id,
    get_credentials_for_user,
    get_template_from_db,
    get_user_by_username,
    store_challenge,
    store_credential,
    toggle_bingo_in_db,
    update_credential_sign_count,
)


@pytest.fixture(autouse=True)
async def db_for_test():
    import main

    # Recreate db on current event loop to avoid loop mismatch
    main.db = Redis.from_url("redis://localhost:6379/1", decode_responses=True)
    await main.db.flushdb()
    yield main.db
    await main.db.flushdb()


def test_hello():
    assert 1 == 1


async def test_create_new_bingo_template():
    template_id = await create_template_in_db(
        cols=2,
        rows=2,
        items=["A", "B", "C", "D"],
    )

    template = await get_template_from_db(template_id)

    assert template == {
        "cols": 2,
        "rows": 2,
        "items": ["A", "B", "C", "D"],
    }


async def test_create_bingo_from_template():
    template_id = await create_template_in_db(
        cols=2,
        rows=2,
        items=["A", "B", "C", "D"],
    )

    template = await get_template_from_db(template_id)

    assert template == {
        "cols": 2,
        "rows": 2,
        "items": ["A", "B", "C", "D"],
    }

    bingo_id = await create_bingo_from_template_in_db(template_id)
    bingo = await get_bingo_from_db(bingo_id)

    assert bingo == {
        "id": bingo_id,
        "cols": 2,
        "rows": 2,
        "selected_items": set(),
        "items": ["A", "B", "C", "D"],
        "template_id": str(template_id),
    }


async def test_toggle_item_in_bingo():
    template_id = await create_template_in_db(
        cols=2,
        rows=2,
        items=["A", "B", "C", "D"],
    )

    template = await get_template_from_db(template_id)

    assert template == {
        "cols": 2,
        "rows": 2,
        "items": ["A", "B", "C", "D"],
    }

    bingo_id = await create_bingo_from_template_in_db(template_id)
    await toggle_bingo_in_db(bingo_id, 1)
    await toggle_bingo_in_db(bingo_id, 3)
    await toggle_bingo_in_db(bingo_id, 3)
    bingo = await get_bingo_from_db(bingo_id)
    assert {1} == bingo["selected_items"]


# --- Auth DB helper tests ---


async def test_create_user():
    user_id = await create_user_in_db("testuser", "Test User")
    user = await get_user_by_username("testuser")
    assert user is not None
    assert user["username"] == "testuser"
    assert user["display_name"] == "Test User"
    assert user["id"] == str(user_id)


async def test_duplicate_username_rejected():
    await create_user_in_db("dupeuser", "First")
    with pytest.raises(ValueError, match="already taken"):
        await create_user_in_db("dupeuser", "Second")


async def test_store_and_retrieve_credential():
    user_id = await create_user_in_db("creduser", "Cred User")
    await store_credential(
        user_id=user_id,
        credential_id_b64="abc123",
        public_key_b64="pubkey456",
        sign_count=0,
        transports="internal,hybrid",
    )
    cred = await get_credential_by_id("abc123")
    assert cred is not None
    assert cred["user_id"] == str(user_id)
    assert cred["public_key"] == "pubkey456"
    assert cred["sign_count"] == "0"
    assert cred["transports"] == "internal,hybrid"

    creds = await get_credentials_for_user(user_id)
    assert len(creds) == 1
    assert creds[0]["credential_id"] == "abc123"


async def test_multiple_credentials_per_user():
    user_id = await create_user_in_db("multikey", "Multi Key")
    await store_credential(user_id, "key1", "pub1", 0)
    await store_credential(user_id, "key2", "pub2", 0)
    creds = await get_credentials_for_user(user_id)
    assert len(creds) == 2
    cred_ids = {c["credential_id"] for c in creds}
    assert cred_ids == {"key1", "key2"}


async def test_update_credential_sign_count():
    user_id = await create_user_in_db("signuser", "Sign User")
    await store_credential(user_id, "signcred", "pub", 5)
    await update_credential_sign_count("signcred", 10)
    cred = await get_credential_by_id("signcred")
    assert cred["sign_count"] == "10"


async def test_challenge_store_and_retrieve():
    await store_challenge("tok123", b"\x01\x02\x03")
    challenge = await get_and_delete_challenge("tok123")
    assert challenge == b"\x01\x02\x03"
    # Single-use: second retrieval returns None
    again = await get_and_delete_challenge("tok123")
    assert again is None


async def test_template_with_user_id():
    tid = await create_template_in_db(
        cols=2, rows=2, items=["A", "B", "C", "D"], user_id="42"
    )
    from main import db

    data = await db.hgetall(f"template:{tid}")
    assert data["user_id"] == "42"


async def test_template_without_user_id():
    tid = await create_template_in_db(cols=2, rows=2, items=["A", "B", "C", "D"])
    from main import db

    data = await db.hgetall(f"template:{tid}")
    assert "user_id" not in data


async def test_bingo_with_user_id():
    tid = await create_template_in_db(cols=2, rows=2, items=["A", "B", "C", "D"])
    bid = await create_bingo_from_template_in_db(tid, user_id="99")
    from main import db

    data = await db.hgetall(f"bingo:{bid}")
    assert data["user_id"] == "99"


# --- Route-level auth tests ---


@pytest.fixture
def client():
    from starlette.testclient import TestClient

    from main import app

    return TestClient(app, raise_server_exceptions=False)


def test_home_page_public(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_create_template_requires_auth(client):
    resp = client.post(
        "/create_template",
        data={"cols": "2", "rows": "2", "item": ["A", "B", "C", "D"]},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "/login" in resp.headers.get("location", "")


def test_edit_bingo_requires_auth(client):
    resp = client.get("/edit_bingo?bingo_id=1", follow_redirects=False)
    assert resp.status_code == 303
    assert "/login" in resp.headers.get("location", "")


def test_trigger_requires_auth(client):
    resp = client.post("/trigger?id=0&bingo_id=1", follow_redirects=False)
    assert resp.status_code == 303
    assert "/login" in resp.headers.get("location", "")


def test_register_page_public(client):
    resp = client.get("/register")
    assert resp.status_code == 200


def test_login_page_public(client):
    resp = client.get("/login")
    assert resp.status_code == 200


# --- WebAuthn ceremony tests (mocked) ---


def test_register_begin_returns_json(client):
    with (
        patch("main.get_user_by_username", new_callable=AsyncMock) as m1,
        patch("main.generate_registration_options") as m2,
        patch("main.options_to_json") as m3,
        patch("main.store_challenge", new_callable=AsyncMock),
    ):
        m1.return_value = None
        mock_opts = MagicMock()
        mock_opts.challenge = b"\x00" * 32
        m2.return_value = mock_opts
        m3.return_value = '{"challenge":"AAAA"}'
        resp = client.post(
            "/register/begin",
            data={"username": "newuser", "display_name": "New"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"


def test_login_begin_returns_json(client):
    with (
        patch("main.get_user_by_username", new_callable=AsyncMock) as m1,
        patch("main.get_credentials_for_user", new_callable=AsyncMock) as m2,
        patch("main.generate_authentication_options") as m3,
        patch("main.options_to_json") as m4,
        patch("main.store_challenge", new_callable=AsyncMock),
    ):
        m1.return_value = {"id": "1", "username": "u"}
        m2.return_value = [
            {
                "credential_id": "Y3JlZA",
                "public_key": "cHVi",
                "sign_count": "0",
                "transports": "",
            }
        ]
        mock_opts = MagicMock()
        mock_opts.challenge = b"\x00" * 32
        m3.return_value = mock_opts
        m4.return_value = '{"challenge":"AAAA"}'
        resp = client.post("/login/begin", data={"username": "u"})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"


def test_login_unknown_user_fails(client):
    with patch("main.get_user_by_username", new_callable=AsyncMock) as m1:
        m1.return_value = None
        resp = client.post("/login/begin", data={"username": "ghost"})
        assert resp.status_code == 400


def test_logout_clears_session(client):
    resp = client.post("/logout", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers.get("location", "") == "/"
