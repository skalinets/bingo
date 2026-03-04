import json
from os import environ

from fasthtml import common as ft
from fasthtml.starlette import Request, Response
from redis.asyncio.client import Redis

google_fonts = ft.Link(
    rel="stylesheet",
    href=(
        "https://fonts.googleapis.com/css2?"
        "family=Inter:wght@400;500;600&"
        "family=Permanent+Marker&"
        "family=Caveat:wght@400;700&"
        "display=swap"
    ),
)

custom_css = ft.Style("""
:root {
    --bg-page: #E8E0D0;
    --bg-card: #F5F0E6;
    --bg-elevated: #D9D0C0;
    --accent: #D63031;
    --accent-hover: #C0392B;
    --text-primary: #1A1A1A;
    --text-secondary: #4A4A4A;
    --text-tertiary: #7A7A7A;
    --cell-selected-show: #D63031;
    --cell-unselected: #FFFDF7;
    --border-standard: #2D2D2D;
}

*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Caveat', cursive;
    background-color: var(--bg-page);
    color: var(--text-primary);
    min-height: 100vh;
}

.page-container {
    max-width: 720px;
    margin: 0 auto;
    padding: 48px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
}

.page-title {
    font-family: 'Permanent Marker', cursive;
    font-size: 48px;
    font-weight: 400;
    color: var(--text-primary);
    text-align: center;
    margin-bottom: 4px;
}

.page-subtitle {
    font-family: 'Permanent Marker', cursive;
    font-size: 28px;
    font-weight: 400;
    color: var(--text-primary);
    text-align: center;
    margin-bottom: 8px;
}

.page-hint {
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    font-weight: 400;
    color: var(--text-secondary);
    text-align: center;
    margin-bottom: 32px;
}

.bingo-grid {
    display: grid;
    gap: 8px;
    margin-bottom: 32px;
}

.bingo-cell {
    width: 120px;
    height: 120px;
    border-radius: 4px;
    padding: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    font-family: 'Caveat', cursive;
    font-size: 20px;
    font-weight: 700;
    line-height: 1.1;
    word-break: break-word;
    overflow: hidden;
    border: 2px solid var(--border-standard);
    transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.bingo-cell[hx-post] {
    cursor: pointer;
}

.bingo-cell[hx-post]:hover {
    transform: scale(1.03);
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.cell-unselected {
    background-color: var(--cell-unselected);
    color: var(--text-primary);
}

.cell-toggled {
    background-color: var(--cell-unselected);
    color: var(--text-primary);
    position: relative;
}

.cell-toggled::after,
.cell-selected-show::after {
    content: 'V';
    position: absolute;
    font-family: 'Permanent Marker', cursive;
    color: var(--accent);
    opacity: 0.85;
    pointer-events: none;
}

.cell-selected-show {
    background-color: var(--cell-unselected);
    color: var(--text-primary);
    position: relative;
}

.check-v0::after {
    font-size: 80px; top: 5px; left: 12px;
    transform: rotate(-12deg);
}
.check-v1::after {
    font-size: 90px; top: 0px; left: 8px;
    transform: rotate(5deg);
}
.check-v2::after {
    font-size: 75px; top: 10px; left: 18px;
    transform: rotate(-20deg);
}
.check-v3::after {
    font-size: 85px; top: 2px; left: 5px;
    transform: rotate(10deg);
}
.check-v4::after {
    font-size: 70px; top: 15px; left: 20px;
    transform: rotate(-5deg);
}
.check-v5::after {
    font-size: 95px; top: -5px; left: 3px;
    transform: rotate(-15deg);
}
.check-v6::after {
    font-size: 78px; top: 8px; left: 15px;
    transform: rotate(18deg);
}
.check-v7::after {
    font-size: 88px; top: 3px; left: 10px;
    transform: rotate(-8deg);
}
.check-v8::after {
    font-size: 72px; top: 12px; left: 22px;
    transform: rotate(14deg);
}
.check-v9::after {
    font-size: 92px; top: -2px; left: 6px;
    transform: rotate(-22deg);
}

.cell-input-wrapper {
    padding: 0;
}

.cell-input {
    background-color: var(--cell-unselected);
    border: 2px solid var(--border-standard);
    border-radius: 4px;
    padding: 8px;
    font-family: 'Caveat', cursive;
    font-size: 16px;
    font-weight: 700;
    text-align: center;
    width: 100%;
    height: 100%;
    outline: none;
}

.cell-input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(214, 48, 49, 0.15);
}

.btn-primary {
    height: 52px;
    background-color: var(--accent);
    color: #FFFFFF;
    border: 2px solid var(--border-standard);
    border-radius: 8px;
    padding: 14px 40px;
    font-family: 'Inter', sans-serif;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.15s ease;
}

.btn-primary:hover {
    background-color: var(--accent-hover);
}

a.btn-primary {
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.btn-secondary {
    height: 52px;
    background-color: var(--bg-card);
    color: var(--text-primary);
    border: 2px solid var(--border-standard);
    border-radius: 8px;
    padding: 14px 40px;
    font-family: 'Inter', sans-serif;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.15s ease;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.btn-secondary:hover {
    background-color: var(--bg-elevated);
}

.grid-size-selector {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
}

.stepper {
    display: inline-flex;
    flex-direction: row;
    gap: 0;
}

.stepper-btn {
    width: 44px;
    height: 44px;
    border: 2px solid var(--border-standard);
    background: var(--bg-card);
    font-family: 'Inter', sans-serif;
    font-size: 20px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    padding: 0;
    color: var(--text-primary);
    transition: background-color 0.15s ease;
}

.stepper-btn:first-child {
    border-radius: 4px 0 0 4px;
}

.stepper-btn:last-child {
    border-radius: 0 4px 4px 0;
}

.stepper-btn:hover:not(:disabled) {
    background: var(--bg-elevated);
}

.stepper-btn:disabled {
    opacity: 0.3;
    cursor: default;
}

.stepper-val {
    width: 44px;
    height: 44px;
    border-top: 2px solid var(--border-standard);
    border-bottom: 2px solid var(--border-standard);
    background: var(--cell-unselected);
    font-family: 'Permanent Marker', cursive;
    font-size: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    user-select: none;
}

.grid-size-separator {
    font-family: 'Inter', sans-serif;
    font-size: 20px;
    font-weight: 600;
    color: var(--text-tertiary);
}
""")

app, rt = ft.fast_app(live=True, hdrs=(google_fonts, custom_css))


def create_bingo_inpput(i: int):
    return ft.Div(
        ft.Input(type="text", name="item", cls="cell-input", placeholder=f"#{i + 1}"),
        cls="bingo-cell cell-input-wrapper",
    )


def create_bingo_text(items):
    def _f(i: int):
        return ft.Div(items[i], cls="bingo-cell cell-unselected")

    return _f


def create_bingo_cell_edit(items, bingo_id, selected_items):
    def _f(i: int):
        cls = (
            f"bingo-cell cell-toggled check-v{i % 10}"
            if i in selected_items
            else "bingo-cell cell-unselected"
        )
        return ft.Div(
            items[i],
            cls=cls,
            hx_trigger="click",
            hx_post=f"/trigger?id={i}&bingo_id={bingo_id}",
            hx_target="#grid",
        )

    return _f


def create_bingo_cell_show(items, selected_items):
    def _f(i: int):
        cls = (
            f"bingo-cell cell-selected-show check-v{i % 10}"
            if i in selected_items
            else "bingo-cell cell-unselected"
        )
        return ft.Div(items[i], cls=cls)

    return _f


def get_bingo_grid(cols=2, rows=2, control_factory=create_bingo_inpput):
    total = cols * rows
    cells = [control_factory(i) for i in range(total)]
    return ft.Div(
        *cells,
        cls="bingo-grid",
        style=f"grid-template-columns: repeat({cols}, 120px); justify-content: center;",
        id="items",
    )


@rt("/change_rows", methods=["POST"])
def change_rows(rows: int, cols: int):
    cols = max(2, min(5, cols or 2))
    rows = max(2, min(5, rows or 2))
    return _get_grid_area(cols, rows)


@rt("/")
def get():
    form = ft.Form(
        _get_grid_area(),
        ft.Button("Створити Шаблон", cls="btn-primary"),
        hx_post="/create_template",
    )
    return ft.Main(
        ft.Div(
            ft.H1("БІНГО", cls="page-title"),
            ft.P("Конструктор", cls="page-subtitle"),
            ft.P(
                "Створіть власну бінго-картку",
                cls="page-hint",
            ),
            form,
            cls="page-container",
        ),
    )


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
    return ft.Main(
        ft.Div(
            ft.H1("БІНГО", cls="page-title"),
            ft.P(
                f"Шаблон #{template_id}",
                cls="page-subtitle",
            ),
            ft.P(
                f"{template['cols']}\u00d7{template['rows']} сітка",
                cls="page-hint",
            ),
            get_bingo_grid(
                template["cols"],
                template["rows"],
                create_bingo_text(items),
            ),
            ft.A(
                "Заповнити Бінго",
                href=f"/create_bingo?template_id={template_id}",
                cls="btn-primary",
            ),
            ft.A(
                "На головну",
                href="/",
                cls="btn-secondary",
                style="margin-top: 12px;",
            ),
            cls="page-container",
        ),
    )


@rt("/trigger", methods=["POST"])
async def post_trigger(request: Request, id: int, bingo_id: str):
    await toggle_bingo_in_db(bingo_id, id)
    return await _get_edit_grid(bingo_id)


async def _get_edit_grid(bingo_id):
    bingo = await get_bingo_from_db(bingo_id)
    items = bingo["items"]
    selected_items = bingo["selected_items"]
    return get_bingo_grid(
        bingo["cols"],
        bingo["rows"],
        create_bingo_cell_edit(items, bingo_id, selected_items),
    )


@rt("/edit_bingo")
async def edit_bingo(bingo_id: str):
    grid = await _get_edit_grid(bingo_id)
    form = ft.Form(
        ft.Hidden(name="bingo_id", value=bingo_id),
        ft.Button("Опублікувати", cls="btn-primary"),
        action="/publish_bingo",
        method="POST",
    )
    return ft.Main(
        ft.Div(
            ft.H1("БІНГО", cls="page-title"),
            ft.P("Редагувати", cls="page-subtitle"),
            ft.P(
                "Натисніть на клітинку, щоб обрати",
                cls="page-hint",
            ),
            ft.Div(grid, id="grid"),
            form,
            cls="page-container",
        ),
    )


@rt("/publish_bingo", methods=["POST"])
async def publish_bingo(bingo_id: str):
    return ft.RedirectResponse(f"/show_bingo/{bingo_id}")


@rt("/show_bingo/{bingo_id}")
async def show_bingo(bingo_id: str):
    bingo = await get_bingo_from_db(bingo_id)
    items = bingo["items"]
    selected_items = bingo["selected_items"]
    grid = get_bingo_grid(
        bingo["cols"],
        bingo["rows"],
        create_bingo_cell_show(items, selected_items),
    )
    return ft.Main(
        ft.Div(
            ft.H1("БІНГО", cls="page-title"),
            ft.P(
                f"{bingo['cols']}\u00d7{bingo['rows']} картка",
                cls="page-subtitle",
            ),
            grid,
            ft.A(
                "Створіть Власне Бінго",
                href=f"/template/{bingo['template_id']}",
                cls="btn-primary",
            ),
            cls="page-container",
        ),
    )


@rt("/create_bingo", methods=["GET", "POST"])
async def post_create_bingo(template_id: int, request: Request):
    bingo_id = await create_bingo_from_template_in_db(template_id)
    return (
        Response(
            status_code=200,
            headers={"HX-Redirect": f"/edit_bingo?bingo_id={bingo_id}"},
        )
        if request.headers.get("HX-Trigger")
        else ft.RedirectResponse(f"/edit_bingo?bingo_id={bingo_id}")
    )


ft.serve()

REDIS_URL = environ.get("REDIS_URL", "redis://localhost:6379/0")

db = Redis.from_url(REDIS_URL, decode_responses=True)


def _stepper(name, value, cols, rows):
    other_name = "rows" if name == "cols" else "cols"
    other_value = rows if name == "cols" else cols
    return ft.Div(
        ft.Button(
            "\u2212",
            cls="stepper-btn",
            hx_post="/change_rows",
            hx_target="#grid-area",
            hx_swap="outerHTML",
            hx_vals=json.dumps({name: max(2, value - 1), other_name: other_value}),
            disabled=(value <= 2),
        ),
        ft.Span(str(value), cls="stepper-val"),
        ft.Button(
            "+",
            cls="stepper-btn",
            hx_post="/change_rows",
            hx_target="#grid-area",
            hx_swap="outerHTML",
            hx_vals=json.dumps({name: min(5, value + 1), other_name: other_value}),
            disabled=(value >= 5),
        ),
        cls="stepper",
    )


def _get_grid_area(cols=2, rows=2):
    return ft.Div(
        ft.Div(
            _stepper("cols", cols, cols, rows),
            ft.Span("\u00d7", cls="grid-size-separator"),
            _stepper("rows", rows, cols, rows),
            cls="grid-size-selector",
        ),
        get_bingo_grid(cols, rows),
        ft.Hidden(name="cols", value=str(cols)),
        ft.Hidden(name="rows", value=str(rows)),
        id="grid-area",
    )


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


async def create_bingo_from_template_in_db(template_id):
    bingo_id = await db.incr("bingo_id")
    bingo_key = f"bingo:{bingo_id}"
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
    template_id = db_bingo["template_id"]
    items = await get_template_items(template_id)
    selected_items = set(map(int, await db.smembers(f"selected_items:{bingo_id}")))
    return {
        "id": bingo_id,
        "items": items,
        "selected_items": selected_items,
        "cols": int(db_bingo["cols"]),
        "rows": int(db_bingo["rows"]),
        "template_id": template_id,
    }


async def toggle_bingo_in_db(bingo_id, item):
    has_member = await db.sismember(f"selected_items:{bingo_id}", item)
    func = [db.sadd, db.srem][has_member]
    await func(f"selected_items:{bingo_id}", item)
