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


def test_hello():
    assert 1 == 1


async def test_redis():
    db = Redis(host="localhost", port=6379)
    await db.set("name", "John")
    assert await db.get("name") == b"John"


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

    bingo_id = await create_bingo_from_template_in_db(template_id, [0, 3])
    bingo = await get_bingo_from_db(bingo_id)

    assert bingo == {
        "id": bingo_id,
        "cols": 2,
        "rows": 2,
        "selected_items": {0, 3},
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

    bingo_id = await create_bingo_from_template_in_db(template_id, [0, 3])
    await toggle_bingo_in_db(bingo_id, 1)
    await toggle_bingo_in_db(bingo_id, 3)
    bingo = await get_bingo_from_db(bingo_id)
    assert {0, 1} == bingo["selected_items"]
