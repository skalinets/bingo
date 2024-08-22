from redis.asyncio.client import Redis

# from redis import Redis
import pytest

from main import create_template, get_template


def test_hello():
    assert 1 == 1


# @pytest.mark.asyncio
async def test_redis():
    db = Redis(host="localhost", port=6379)
    await db.set("name", "John")
    assert await db.get("name") == b"John"


async def test_create_new_bingo_template():
    # db = Redis(host="localhost", port=6379)

    template_id = await create_template(
        cols=2,
        rows=2,
        items=["A", "B", "C", "D"],
    )

    template = await get_template(template_id)

    assert template == {
        "cols": 2,
        "rows": 2,
        "items": ["A", "B", "C", "D"],
    }
