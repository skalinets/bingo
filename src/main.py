from fasthtml import common as ft
from fasthtml.starlette import Request, Response
from redis.asyncio.client import Redis

# from icecream import ic
from itertools import chain

gridlink = ft.Link(
    rel="stylesheet",
    href="https://cdnjs.cloudflare.com/ajax/libs/flexboxgrid/6.3.1/flexboxgrid.min.css",
    type="text/css",
)
app, rt = ft.fast_app(live=True, hdrs=(ft.picolink, gridlink))


@rt("/change_rows", methods=["POST"])
def change_rows(rows: int, cols: int):
    rows = rows or 2
    cols = cols or 2
    return get_bingo_grid(cols, rows)


def get_row(cols, control, current_row):
    r = [
        ft.Div(
            ft.Div(
                control((current_row - 1) * cols + i),
                cls="box",
                style="background-color: green;",
            ),
            cls=f"col-xs-{12//cols}",
        )
        for i in range(cols)
    ]
    return r


def create_bingo_inpput(i: int):
    return (
        ft.Input(
            type="text",
            name="item",
            cls="box",
            style="background-color: green; color: white",
        ),
    )


def create_bingo_text(items):
    def _f(i: int):
        return ft.P(items[i], cls="box", style="background-color: green; color: white")

    return _f


def get_bingo_grid(cols=2, rows=2, control_factory=create_bingo_inpput):
    my_rows = [get_row(cols, control_factory, r) for r in range(rows)]
    my_rows = list(chain.from_iterable(my_rows))
    divs = ft.Div(
        *my_rows,
        cls="row",
        style="background-color: #fbf;",
    )

    return ft.Div(*divs, cls="row", style="color: #fff;")


@rt("/")
def get():
    form = ft.Form(
        ft.Group(_i("cols"), ft.P("X", style="padding: 10px"), _i("rows")),
        ft.Div(get_bingo_grid(), id="items", cls="row"),
        ft.Button("Create"),
        hx_post="/create_template",
    )
    return ft.Main(ft.Div(form, style="padding: 16px;"), title="sdfds")


@rt("/create_template", methods=["POST"])
async def post_create_template(cols: int, rows: int, request: Request):
    form_data = await request.form()
    items = form_data.getlist("item")
    template_id = await create_template_in_db(
        cols=cols,
        rows=rows,
        items=items,
    )
    return Response(
        status_code=200, headers={"HX-Redirect": f"/template/{template_id}"}
    )


@rt("/template/{template_id}")
async def get_template_route(template_id: int):
    template = await get_template_from_db(template_id)
    items = template["items"]
    return ft.Container(
        ft.P(f"Template {template_id}"),
        ft.A("Back", href="/"),
        get_bingo_grid(template["cols"], template["rows"], create_bingo_text(items)),
        ft.Button("Create Bingo", hx_post=f"/create_bingo?template_id={template_id}"),
    )


def create_bingo_text2(items, bingo_id, selected_items):
    def _f(i: int):
        color = "green" if i in selected_items else "red"
        return ft.P(
            items[i],
            cls="box",
            style=f"background-color: {color}; color: white",
            hx_trigger="click",
            hx_post=f"/trigger?id={i}&bingo_id={bingo_id}",
            hx_target="#grid",
        )

    return _f


@rt("/trigger", methods=["POST"])
async def post_trigger(request: Request, id: int, bingo_id: str):
    print("sadfasdfasdfasdf")
    await toggle_bingo_in_db(bingo_id, id)
    return await _get_edit_grid(bingo_id)


async def _get_edit_grid(bingo_id):
    bingo = await get_bingo_from_db(bingo_id)
    items = bingo["items"]
    selected_items = bingo["selected_items"]
    return get_bingo_grid(
        bingo["cols"],
        bingo["rows"],
        create_bingo_text2(items, bingo_id, selected_items),
    )


# Template 687
# bingo 153


@rt("/edit_bingo")
async def edit_bingo(bingo_id: str):
    grid = await _get_edit_grid(bingo_id)
    return ft.Container(
        grid,
        id="grid",
    )


@rt("/create_bingo", methods=["POST"])
async def post_create_bingo(template_id: int, request: Request):
    bingo_id = await create_bingo_from_template_in_db(template_id)
    return Response(
        status_code=200, headers={"HX-Redirect": f"/edit_bingo?bingo_id={bingo_id}"}
    )


ft.serve()

db = Redis(host="localhost", port=6379, decode_responses=True)


async def get_template_items(template_id):
    template_items = await db.lrange(f"template_items:{template_id}", 0, -1)
    # TODO: fix reverse
    template_items.reverse()
    return template_items


async def get_template_from_db(template_id):
    template = await db.hgetall(f"template:{template_id}")
    template_items = await get_template_items(template_id)
    return {
        "cols": int(template["cols"]),
        "rows": int(template["rows"]),
        "items": template_items,
    }


async def create_template_in_db(cols, rows, items):
    template_id = await db.incr("template_id")
    await db.hset(
        f"template:{template_id}",
        mapping={
            "cols": cols,
            "rows": rows,
        },
    )
    await db.lpush(f"template_items:{template_id}", *items)
    return template_id


def _i(i):
    return ft.Input(
        value="2",
        name=i,
        hx_target="#items",
        hx_post="/change_rows",
        hx_trigger="change",
        type="number",
        min="2",
        max="5",
    )


async def create_bingo_from_template_in_db(template_id):
    bingo_id = await db.incr("bingo_id")
    bingo_key = f"bingo:{bingo_id}"
    # sel_items_key = f"selected_items:{bingo_id}"
    # await db.sadd(sel_items_key, *selected_items)
    template = await get_template_from_db(template_id)
    await db.hset(
        bingo_key,
        mapping={
            "template_id": template_id,
            "cols": template["cols"],
            "rows": template["rows"],
        },
    )
    return bingo_id


async def get_bingo_from_db(bingo_id):
    bingo_key = f"bingo:{bingo_id}"
    db_bingo = await db.hgetall(bingo_key)
    items = await get_template_items(db_bingo["template_id"])
    selected_items = set(map(int, await db.smembers(f"selected_items:{bingo_id}")))
    return {
        "id": bingo_id,
        "items": items,
        "selected_items": selected_items,
        "cols": int(db_bingo["cols"]),
        "rows": int(db_bingo["rows"]),
    }


async def toggle_bingo_in_db(bingo_id, item):
    has_member = await db.sismember(f"selected_items:{bingo_id}", item)
    func = [db.sadd, db.srem][has_member]
    await func(f"selected_items:{bingo_id}", item)
