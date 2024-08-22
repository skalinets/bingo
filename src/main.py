from fasthtml import common as ft
from fasthtml.starlette import FormData, RedirectResponse, Request
from redis.asyncio.client import Redis
from icecream import ic
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


def get_row(cols, control, row):
    r = [
        ft.Div(
            ft.Div(
                control((row - 1) * cols + i),
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
            name="item",
            type="text",
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
    # ic(my_rows)
    divs = ft.Div(
        *my_rows,
        cls="row",
        style="background-color: #fbf;",
    )

    return ft.Div(*divs, cls="row", style="color: #fff;")


@rt("/")
def get():
    form = ft.Form(
        ft.Input(
            name="cols",
            hx_target="#items",
            hx_post="/change_rows",
            hx_trigger="change",
        ),
        ft.Input(
            name="rows",
            hx_target="#items",
            hx_post="/change_rows",
            hx_trigger="change",
        ),
        ft.Div(get_bingo_grid(), id="items", cls="row"),
        ft.Button("Create"),
        hx_post="/create_template",
    )
    return ft.Div(ft.P("Hello World!"), form)


@rt("/create_template", methods=["POST"])
async def post_create_template(cols: int, rows: int, request: Request):
    form_data = await request.form()
    items = form_data.getlist("item")
    template_id = await create_template(
        cols=cols,
        rows=rows,
        items=items,
    )
    return RedirectResponse(f"/template/{template_id}")
    # return template_id


@rt("/template/{template_id}")
async def get_template_route(template_id: int):
    template = await get_template(template_id)
    items = template["items"]
    return ft.Div(
        get_bingo_grid(template["cols"], template["rows"], create_bingo_text(items)),
    )


ft.serve()

db = Redis(host="localhost", port=6379, decode_responses=True)


async def get_template(template_id):
    template = await db.hgetall(f"template:{template_id}")
    template_items = await db.lrange(f"template_items:{template_id}", 0, -1)
    # TODO: fix reverse
    template_items.reverse()
    return {
        "cols": int(template["cols"]),
        "rows": int(template["rows"]),
        "items": template_items,
    }


async def create_template(cols, rows, items):
    template_id = await db.incr("template_id")
    await db.hmset(
        f"template:{template_id}",
        {
            "cols": cols,
            "rows": rows,
        },
    )
    await db.lpush(f"template_items:{template_id}", *items)
    return template_id
