from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.asyncio.client import Redis

from main import (
    _parse_bingo_items,
    create_bingo_from_template_in_db,
    create_template_in_db,
    create_user_in_db,
    get_and_delete_challenge,
    get_and_delete_recovery_token,
    get_bingo_from_db,
    get_credential_by_id,
    get_credentials_for_user,
    get_template_from_db,
    get_user_by_email,
    get_user_by_id,
    store_challenge,
    store_credential,
    store_recovery_token,
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
    user_id = await create_user_in_db("test@example.com", "Test User")
    user = await get_user_by_email("test@example.com")
    assert user is not None
    assert user["email"] == "test@example.com"
    assert user["display_name"] == "Test User"
    assert user["id"] == str(user_id)


async def test_duplicate_email_rejected():
    await create_user_in_db("dupe@example.com", "First")
    with pytest.raises(ValueError, match="already taken"):
        await create_user_in_db("dupe@example.com", "Second")


async def test_store_and_retrieve_credential():
    user_id = await create_user_in_db("cred@example.com", "Cred User")
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
    user_id = await create_user_in_db("multi@example.com", "Multi Key")
    await store_credential(user_id, "key1", "pub1", 0)
    await store_credential(user_id, "key2", "pub2", 0)
    creds = await get_credentials_for_user(user_id)
    assert len(creds) == 2
    cred_ids = {c["credential_id"] for c in creds}
    assert cred_ids == {"key1", "key2"}


async def test_update_credential_sign_count():
    user_id = await create_user_in_db("sign@example.com", "Sign User")
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


async def test_get_user_by_id():
    user_id = await create_user_in_db("byid@example.com", "By ID")
    user = await get_user_by_id(user_id)
    assert user is not None
    assert user["email"] == "byid@example.com"
    assert user["id"] == str(user_id)


async def test_get_user_by_id_not_found():
    user = await get_user_by_id("99999")
    assert user is None


# --- Recovery token tests ---


async def test_store_and_verify_recovery_token():
    user_id = await create_user_in_db("recover@example.com", "Recover")
    await store_recovery_token(str(user_id), "recov-tok-123")
    result = await get_and_delete_recovery_token("recov-tok-123")
    assert result == str(user_id)
    # Single-use
    again = await get_and_delete_recovery_token("recov-tok-123")
    assert again is None


async def test_recovery_token_invalid():
    result = await get_and_delete_recovery_token("nonexistent-token")
    assert result is None


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
        data={"items_text": "A\nB\nC\nD"},
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


def test_recover_page_public(client):
    resp = client.get("/recover")
    assert resp.status_code == 200


# --- WebAuthn ceremony tests (mocked) ---


def test_register_begin_returns_json(client):
    with (
        patch("main.get_user_by_email", new_callable=AsyncMock) as m1,
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
            data={"email": "new@example.com", "display_name": "New"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"


def test_login_begin_returns_json(client):
    with (
        patch("main.get_user_by_email", new_callable=AsyncMock) as m1,
        patch("main.get_credentials_for_user", new_callable=AsyncMock) as m2,
        patch("main.generate_authentication_options") as m3,
        patch("main.options_to_json") as m4,
        patch("main.store_challenge", new_callable=AsyncMock),
    ):
        m1.return_value = {"id": "1", "email": "u@example.com"}
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
        resp = client.post("/login/begin", data={"email": "u@example.com"})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"


def test_login_unknown_user_fails(client):
    with patch("main.get_user_by_email", new_callable=AsyncMock) as m1:
        m1.return_value = None
        resp = client.post("/login/begin", data={"email": "ghost@example.com"})
        assert resp.status_code == 400


def test_login_conditional_returns_json(client):
    with (
        patch("main.generate_authentication_options") as m1,
        patch("main.options_to_json") as m2,
        patch("main.store_challenge", new_callable=AsyncMock),
    ):
        mock_opts = MagicMock()
        mock_opts.challenge = b"\x00" * 32
        m1.return_value = mock_opts
        m2.return_value = '{"challenge":"AAAA","allowCredentials":[]}'
        resp = client.get("/login/conditional")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"


def test_recovery_send_unknown_email(client):
    with patch("main.get_user_by_email", new_callable=AsyncMock) as m1:
        m1.return_value = None
        resp = client.post("/recover/send", data={"email": "unknown@example.com"})
        assert resp.status_code == 200
        assert "Перевірте пошту" in resp.text


def test_recovery_verify_invalid_token(client):
    with patch("main.get_and_delete_recovery_token", new_callable=AsyncMock) as m1:
        m1.return_value = None
        resp = client.get("/recover/verify/bad-token", follow_redirects=False)
        assert resp.status_code == 200
        assert "недійсне" in resp.text


def test_recovery_verify_valid_token(client):
    with (
        patch("main.get_and_delete_recovery_token", new_callable=AsyncMock) as m1,
        patch("main.get_user_by_id", new_callable=AsyncMock) as m2,
    ):
        m1.return_value = "42"
        m2.return_value = {"id": "42", "email": "r@example.com", "display_name": "R"}
        resp = client.get("/recover/verify/good-token", follow_redirects=False)
        assert resp.status_code == 303
        assert "/recover/passkey" in resp.headers.get("location", "")


def test_recover_passkey_requires_auth(client):
    resp = client.get("/recover/passkey", follow_redirects=False)
    assert resp.status_code == 303
    assert "/login" in resp.headers.get("location", "")


def test_logout_clears_session(client):
    resp = client.post("/logout", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers.get("location", "") == "/"


def test_parse_bingo_items_4_items():
    items, side = _parse_bingo_items("A\nB\nC\nD")
    assert side == 2
    assert items == ["A", "B", "C", "D"]


def test_parse_bingo_items_5_items_padded():
    items, side = _parse_bingo_items("A\nB\nC\nD\nE")
    assert side == 3
    assert len(items) == 9
    assert items[:5] == ["A", "B", "C", "D", "E"]
    assert items[5:] == ["", "", "", ""]


def test_parse_bingo_items_9_items():
    items, side = _parse_bingo_items("\n".join(f"item{i}" for i in range(9)))
    assert side == 3
    assert len(items) == 9


def test_parse_bingo_items_26_capped():
    items, side = _parse_bingo_items("\n".join(f"x{i}" for i in range(26)))
    assert side == 5
    assert len(items) == 25


def test_parse_bingo_items_empty():
    items, side = _parse_bingo_items("")
    assert side == 0
    assert items == []


def test_parse_bingo_items_blank_lines():
    items, side = _parse_bingo_items("A\n\n  \nB\nC\nD")
    assert side == 2
    assert items == ["A", "B", "C", "D"]


def test_preview_grid_returns_html(client):
    resp = client.post("/preview_grid", data={"items_text": "A\nB\nC\nD"})
    assert resp.status_code == 200
    assert "preview-area" in resp.text


def test_preview_grid_empty_text(client):
    resp = client.post("/preview_grid", data={"items_text": ""})
    assert resp.status_code == 200
    assert "preview-area" in resp.text
    assert "grid" not in resp.text.lower() or "Введіть елементи" in resp.text


def test_preview_grid_missing_field(client):
    resp = client.post("/preview_grid", data={})
    assert resp.status_code == 200
    assert "preview-area" in resp.text


# --- Unicode / non-ASCII edge cases ---


def test_register_begin_unicode_display_name(client):
    """The bug: Ukrainian display name in cookie caused latin-1 encode error."""
    with (
        patch("main.get_user_by_email", new_callable=AsyncMock) as m1,
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
            data={"email": "ukr@example.com", "display_name": "Тарас Шевченко"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"


def test_register_begin_emoji_display_name(client):
    with (
        patch("main.get_user_by_email", new_callable=AsyncMock) as m1,
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
            data={"email": "emoji@example.com", "display_name": "User 🎲🎯"},
        )
        assert resp.status_code == 200


def test_register_begin_cjk_display_name(client):
    with (
        patch("main.get_user_by_email", new_callable=AsyncMock) as m1,
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
            data={"email": "cjk@example.com", "display_name": "用户名"},
        )
        assert resp.status_code == 200


async def test_create_user_unicode_display_name():
    await create_user_in_db("ukr@example.com", "Тарас Шевченко")
    user = await get_user_by_email("ukr@example.com")
    assert user["display_name"] == "Тарас Шевченко"


# --- Register edge cases ---


def test_register_begin_empty_email(client):
    resp = client.post(
        "/register/begin",
        data={"email": "", "display_name": "Nobody"},
    )
    assert resp.status_code == 400


def test_register_begin_whitespace_email(client):
    resp = client.post(
        "/register/begin",
        data={"email": "   ", "display_name": "Nobody"},
    )
    assert resp.status_code == 400


def test_register_begin_duplicate_email(client):
    with patch("main.get_user_by_email", new_callable=AsyncMock) as m1:
        m1.return_value = {"id": "1", "email": "taken@example.com"}
        resp = client.post(
            "/register/begin",
            data={"email": "taken@example.com", "display_name": "Dup"},
        )
        assert resp.status_code == 400


def test_register_begin_empty_display_name_falls_back_to_email(client):
    with (
        patch("main.get_user_by_email", new_callable=AsyncMock) as m1,
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
            data={"email": "fallback@example.com", "display_name": ""},
        )
        assert resp.status_code == 200
        # display_name should have fallen back to email
        m2.assert_called_once()
        call_kwargs = m2.call_args
        assert call_kwargs.kwargs.get(
            "user_display_name", call_kwargs[1].get("user_display_name")
        ) == "fallback@example.com"


def test_register_complete_missing_cookies(client):
    resp = client.post(
        "/register/complete",
        json={"id": "cred", "rawId": "abc", "type": "public-key", "response": {}},
    )
    assert resp.status_code == 400


def test_register_complete_expired_challenge(client):
    with patch("main.get_and_delete_challenge", new_callable=AsyncMock) as m1:
        m1.return_value = None
        resp = client.post(
            "/register/complete",
            json={"id": "cred", "rawId": "abc", "type": "public-key", "response": {}},
            cookies={
                "webauthn_token": "tok",
                "webauthn_email": "e@example.com",
                "webauthn_display_name": "Name",
            },
        )
        assert resp.status_code == 400


# --- Login edge cases ---


def test_login_begin_empty_email(client):
    resp = client.post("/login/begin", data={"email": ""})
    assert resp.status_code == 400


def test_login_begin_whitespace_email(client):
    resp = client.post("/login/begin", data={"email": "   "})
    assert resp.status_code == 400


def test_login_complete_missing_token(client):
    resp = client.post(
        "/login/complete",
        json={"id": "cred", "rawId": "abc", "type": "public-key", "response": {}},
    )
    assert resp.status_code == 400


def test_login_complete_expired_challenge(client):
    with patch("main.get_and_delete_challenge", new_callable=AsyncMock) as m1:
        m1.return_value = None
        resp = client.post(
            "/login/complete",
            json={"id": "cred", "rawId": "abc", "type": "public-key", "response": {}},
            cookies={"webauthn_token": "tok", "webauthn_email": "e@example.com"},
        )
        assert resp.status_code == 400


def test_login_complete_unknown_credential(client):
    with (
        patch("main.get_and_delete_challenge", new_callable=AsyncMock) as m1,
        patch("main.get_credential_by_id", new_callable=AsyncMock) as m2,
    ):
        m1.return_value = b"\x00" * 32
        m2.return_value = None
        resp = client.post(
            "/login/complete",
            json={
                "id": "unknown", "rawId": "abc",
                "type": "public-key", "response": {},
            },
            cookies={"webauthn_token": "tok", "webauthn_email": "e@example.com"},
        )
        assert resp.status_code == 400


# --- Create template edge cases ---


def test_create_template_empty_items(client):
    """Creating a template with no items should fail, not create an empty template."""
    import main

    with patch.object(main.bware, "f", new_callable=AsyncMock, return_value=None):
        resp = client.post(
            "/create_template",
            data={"items_text": ""},
        )
        assert resp.status_code == 400


def test_create_template_whitespace_only_items(client):
    import main

    with patch.object(main.bware, "f", new_callable=AsyncMock, return_value=None):
        resp = client.post(
            "/create_template",
            data={"items_text": "  \n\n  \n  "},
        )
        assert resp.status_code == 400


# --- Recovery passkey edge cases ---


def test_recover_passkey_begin_no_auth(client):
    resp = client.post("/recover/passkey/begin", follow_redirects=False)
    assert resp.status_code in (303, 401)


def test_recover_passkey_complete_no_auth(client):
    resp = client.post(
        "/recover/passkey/complete",
        json={"id": "cred", "rawId": "abc", "type": "public-key", "response": {}},
        follow_redirects=False,
    )
    assert resp.status_code in (303, 401)
