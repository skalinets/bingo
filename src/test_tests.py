from redis.asyncio.client import Redis

import pytest
import asyncio

from main import (
    create_bingo_from_template_in_db,
    create_template_in_db,
    get_bingo_from_db,
    get_template_from_db,
    toggle_bingo_in_db,
)

@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def db_for_test(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    db = Redis.from_url("redis://localhost:6379/1", decode_responses=True)
    db.flushdb()
    yield db
    db.flushdb()


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
