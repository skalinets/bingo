import base64
import json
import secrets
from os import environ

from fasthtml import common as ft
from fasthtml.core import Beforeware
from fasthtml.starlette import Request, Response
from redis.asyncio.client import Redis
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorTransport,
    PublicKeyCredentialDescriptor,
    UserVerificationRequirement,
)

RP_ID = environ.get("RP_ID", "localhost")
RP_NAME = "Бінго"
RP_ORIGIN = environ.get("RP_ORIGIN", "http://localhost:5001")

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
    background-color: var(--accent);
    color: #FFFFFF;
}

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

fit_text_js = ft.Script("""
function fitText(el) {
    var maxW = el.clientWidth - 8, maxH = el.clientHeight - 8;
    if (!maxW || !maxH) return;
    var span = el.querySelector('.fit-text');
    if (!span) return;
    var lo = 10, hi = 60, best = lo;
    while (lo <= hi) {
        var mid = Math.floor((lo + hi) / 2);
        span.style.fontSize = mid + 'px';
        if (span.scrollWidth <= maxW && span.scrollHeight <= maxH) {
            best = mid; lo = mid + 1;
        } else { hi = mid - 1; }
    }
    span.style.fontSize = best + 'px';
}
function fitAllCells() {
    document.querySelectorAll('.bingo-cell:not(.cell-input-wrapper)').forEach(fitText);
}
document.addEventListener('DOMContentLoaded', fitAllCells);
document.addEventListener('htmx:afterSwap', fitAllCells);
""")

webauthn_js = ft.Script("""
function base64urlToBuffer(b) {
    b = b.replace(/-/g, '+').replace(/_/g, '/');
    while (b.length % 4) b += '=';
    var bin = atob(b), arr = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return arr.buffer;
}
function bufferToBase64url(buf) {
    var arr = new Uint8Array(buf), bin = '';
    for (var i = 0; i < arr.length; i++) bin += String.fromCharCode(arr[i]);
    return btoa(bin).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/, '');
}
async function webauthnRegister(formEl) {
    var fd = new FormData(formEl);
    var res = await fetch('/register/begin', {method: 'POST', body: fd});
    if (!res.ok) { alert(await res.text()); return; }
    var opts = await res.json();
    opts.challenge = base64urlToBuffer(opts.challenge);
    opts.user.id = base64urlToBuffer(opts.user.id);
    if (opts.excludeCredentials) {
        opts.excludeCredentials = opts.excludeCredentials.map(function(c) {
            c.id = base64urlToBuffer(c.id); return c;
        });
    }
    var cred;
    try { cred = await navigator.credentials.create({publicKey: opts}); }
    catch(e) { alert('Passkey creation failed: ' + e.message); return; }
    var body = JSON.stringify({
        id: cred.id,
        rawId: bufferToBase64url(cred.rawId),
        type: cred.type,
        response: {
            attestationObject: bufferToBase64url(cred.response.attestationObject),
            clientDataJSON: bufferToBase64url(cred.response.clientDataJSON)
        }
    });
    var r2 = await fetch('/register/complete', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: body
    });
    if (r2.ok) { window.location.href = '/'; }
    else { alert(await r2.text()); }
}
async function webauthnLogin(formEl) {
    var fd = new FormData(formEl);
    var res = await fetch('/login/begin', {method: 'POST', body: fd});
    if (!res.ok) { alert(await res.text()); return; }
    var opts = await res.json();
    opts.challenge = base64urlToBuffer(opts.challenge);
    if (opts.allowCredentials) {
        opts.allowCredentials = opts.allowCredentials.map(function(c) {
            c.id = base64urlToBuffer(c.id); return c;
        });
    }
    var assertion;
    try { assertion = await navigator.credentials.get({publicKey: opts}); }
    catch(e) { alert('Passkey auth failed: ' + e.message); return; }
    var body = JSON.stringify({
        id: assertion.id,
        rawId: bufferToBase64url(assertion.rawId),
        type: assertion.type,
        response: {
            authenticatorData: bufferToBase64url(assertion.response.authenticatorData),
            clientDataJSON: bufferToBase64url(assertion.response.clientDataJSON),
            signature: bufferToBase64url(assertion.response.signature),
            userHandle: assertion.response.userHandle
                ? bufferToBase64url(assertion.response.userHandle) : null
        }
    });
    var r2 = await fetch('/login/complete', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: body
    });
    if (r2.ok) { window.location.href = '/'; }
    else { alert(await r2.text()); }
}
async function webauthnConditionalLogin() {
    if (!window.PublicKeyCredential ||
        !PublicKeyCredential.isConditionalMediationAvailable) return;
    var available = await PublicKeyCredential.isConditionalMediationAvailable();
    if (!available) return;
    try {
        var opts = await (await fetch('/login/conditional')).json();
        opts.challenge = base64urlToBuffer(opts.challenge);
        if (opts.allowCredentials) {
            opts.allowCredentials = opts.allowCredentials.map(function(c) {
                c.id = base64urlToBuffer(c.id); return c;
            });
        }
        var assertion = await navigator.credentials.get({
            publicKey: opts, mediation: 'conditional'
        });
        var ar = assertion.response;
        var body = JSON.stringify({
            id: assertion.id,
            rawId: bufferToBase64url(assertion.rawId),
            type: assertion.type,
            response: {
                authenticatorData: bufferToBase64url(ar.authenticatorData),
                clientDataJSON: bufferToBase64url(ar.clientDataJSON),
                signature: bufferToBase64url(ar.signature),
                userHandle: ar.userHandle
                    ? bufferToBase64url(ar.userHandle) : null
            }
        });
        var r2 = await fetch('/login/complete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: body
        });
        if (r2.ok) { window.location.href = '/'; }
    } catch(e) { /* user cancelled or not available */ }
}
async function webauthnRecoveryRegister(formEl) {
    var res = await fetch('/recover/passkey/begin', {method: 'POST'});
    if (!res.ok) { alert(await res.text()); return; }
    var opts = await res.json();
    opts.challenge = base64urlToBuffer(opts.challenge);
    opts.user.id = base64urlToBuffer(opts.user.id);
    if (opts.excludeCredentials) {
        opts.excludeCredentials = opts.excludeCredentials.map(function(c) {
            c.id = base64urlToBuffer(c.id); return c;
        });
    }
    var cred;
    try { cred = await navigator.credentials.create({publicKey: opts}); }
    catch(e) { alert('Passkey creation failed: ' + e.message); return; }
    var body = JSON.stringify({
        id: cred.id,
        rawId: bufferToBase64url(cred.rawId),
        type: cred.type,
        response: {
            attestationObject: bufferToBase64url(cred.response.attestationObject),
            clientDataJSON: bufferToBase64url(cred.response.clientDataJSON)
        }
    });
    var r2 = await fetch('/recover/passkey/complete', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: body
    });
    if (r2.ok) { window.location.href = '/'; }
    else { alert(await r2.text()); }
}
""")


async def _before(req, session):
    if not session.get("user_id"):
        return ft.RedirectResponse("/login", status_code=303)


bware = Beforeware(
    _before,
    skip=[
        r"/",
        r"/login",
        r"/login/begin",
        r"/login/complete",
        r"/login/conditional",
        r"/register",
        r"/register/begin",
        r"/register/complete",
        r"/change_rows",
        r"/template/\d+",
        r"/show_bingo/\d+",
        r"/create_bingo",
        r"/logout",
        r"/recover",
        r"/recover/send",
        r"/recover/verify/.+",
        r".*\.css",
        r".*\.js",
        r".*\.ico",
        r".*\.png",
        r".*\.jpg",
    ],
)

app, rt = ft.fast_app(
    live=True, hdrs=(google_fonts, custom_css, fit_text_js, webauthn_js), before=bware
)


def create_bingo_inpput(i: int):
    return ft.Div(
        ft.Input(type="text", name="item", cls="cell-input", placeholder=f"#{i + 1}"),
        cls="bingo-cell cell-input-wrapper",
    )


def create_bingo_text(items):
    def _f(i: int):
        return ft.Div(
            ft.Span(items[i], cls="fit-text"),
            cls="bingo-cell cell-unselected",
        )

    return _f


def create_bingo_cell_edit(items, bingo_id, selected_items):
    def _f(i: int):
        cls = (
            "bingo-cell cell-toggled"
            if i in selected_items
            else "bingo-cell cell-unselected"
        )
        return ft.Div(
            ft.Span(items[i], cls="fit-text"),
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
        return ft.Div(ft.Span(items[i], cls="fit-text"), cls=cls)

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
def get(session):
    user_id = session.get("user_id")
    if user_id:
        nav = ft.Div(
            ft.Form(
                ft.Button(
                    "Вийти",
                    cls="btn-secondary",
                    style="height:40px;padding:8px 20px;",
                ),
                action="/logout",
                method="POST",
            ),
            style="position:absolute;top:16px;right:16px;",
        )
        form = ft.Form(
            _get_grid_area(),
            ft.Button("Створити Шаблон", cls="btn-primary"),
            hx_post="/create_template",
        )
        content = ft.Div(form)
    else:
        nav = ft.Div()
        content = ft.Div(
            ft.A(
                "Увійти",
                href="/login",
                cls="btn-primary",
                style="margin-bottom:12px;",
            ),
            ft.A("Зареєструватися", href="/register", cls="btn-secondary"),
            style="display:flex;flex-direction:column;align-items:center;gap:8px;",
        )
    return ft.Main(
        nav,
        ft.Div(
            ft.H1("БІНГО", cls="page-title"),
            ft.P("Конструктор", cls="page-subtitle"),
            ft.P(
                "Створіть власну бінго-картку",
                cls="page-hint",
            ),
            content,
            cls="page-container",
        ),
        style="position:relative;",
    )


@rt("/create_template", methods=["POST"])
async def post_create_template(cols: int, rows: int, request: Request, session):
    form_data = await request.form()
    items = form_data.getlist("item")
    template_id = await create_template_in_db(
        cols=cols,
        rows=rows,
        items=items,
        user_id=session.get("user_id"),
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


@rt("/register")
def get_register():
    return ft.Main(
        ft.Div(
            ft.H1("БІНГО", cls="page-title"),
            ft.P("Реєстрація", cls="page-subtitle"),
            ft.Form(
                ft.Input(
                    type="email",
                    name="email",
                    placeholder="Електронна пошта",
                    required=True,
                    cls="cell-input",
                    style="width:300px;height:48px;margin-bottom:12px;",
                ),
                ft.Input(
                    type="text",
                    name="display_name",
                    placeholder="Відображуване ім'я",
                    cls="cell-input",
                    style="width:300px;height:48px;margin-bottom:16px;",
                ),
                ft.Button(
                    "Зареєструватися з Passkey",
                    cls="btn-primary",
                    type="submit",
                ),
                onsubmit="event.preventDefault(); webauthnRegister(this)",
            ),
            ft.A(
                "Вже є акаунт? Увійти",
                href="/login",
                cls="btn-secondary",
                style="margin-top:12px;",
            ),
            cls="page-container",
        ),
    )


@rt("/register/begin", methods=["POST"])
async def post_register_begin(request: Request):
    form_data = await request.form()
    email = form_data.get("email", "").strip().lower()
    display_name = form_data.get("display_name", "").strip() or email
    if not email:
        return Response("Введіть електронну пошту", status_code=400)
    existing = await get_user_by_email(email)
    if existing:
        return Response("Ця пошта вже зареєстрована", status_code=400)
    token = secrets.token_urlsafe(32)
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=secrets.token_bytes(32),
        user_name=email,
        user_display_name=display_name,
        authenticator_selection=None,
    )
    await store_challenge(token, options.challenge)
    resp = Response(
        content=options_to_json(options),
        media_type="application/json",
    )
    ck = dict(httponly=True, max_age=300, samesite="lax")
    resp.set_cookie("webauthn_token", token, **ck)
    resp.set_cookie("webauthn_email", email, **ck)
    resp.set_cookie("webauthn_display_name", display_name, **ck)
    return resp


@rt("/register/complete", methods=["POST"])
async def post_register_complete(request: Request, session):
    token = request.cookies.get("webauthn_token")
    email = request.cookies.get("webauthn_email")
    display_name = request.cookies.get("webauthn_display_name", email)
    if not token or not email:
        return Response("Сесію реєстрації не знайдено", status_code=400)
    challenge = await get_and_delete_challenge(token)
    if not challenge:
        return Response("Виклик прострочений", status_code=400)
    body = await request.json()
    try:
        verification = verify_registration_response(
            credential=body,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=RP_ORIGIN,
        )
    except Exception as e:
        return Response(f"Помилка верифікації: {e}", status_code=400)
    user_id = await create_user_in_db(email, display_name)
    cred_id_b64 = (
        base64.urlsafe_b64encode(verification.credential_id).decode().rstrip("=")
    )
    pub_key_b64 = (
        base64.urlsafe_b64encode(verification.credential_public_key)
        .decode()
        .rstrip("=")
    )
    transports = ""
    if hasattr(body.get("response", {}), "get"):
        transports = ",".join(body.get("response", {}).get("transports", []))
    await store_credential(
        user_id=user_id,
        credential_id_b64=cred_id_b64,
        public_key_b64=pub_key_b64,
        sign_count=verification.sign_count,
        transports=transports,
    )
    session["user_id"] = str(user_id)
    session["email"] = email
    resp = Response(status_code=200)
    resp.delete_cookie("webauthn_token")
    resp.delete_cookie("webauthn_email")
    resp.delete_cookie("webauthn_display_name")
    return resp


@rt("/login")
def get_login():
    return ft.Main(
        ft.Div(
            ft.H1("БІНГО", cls="page-title"),
            ft.P("Вхід", cls="page-subtitle"),
            ft.Form(
                ft.Input(
                    type="email",
                    name="email",
                    placeholder="Електронна пошта",
                    required=True,
                    cls="cell-input",
                    style="width:300px;height:48px;margin-bottom:16px;",
                    autocomplete="username webauthn",
                ),
                ft.Button(
                    "Увійти з Passkey",
                    cls="btn-primary",
                    type="submit",
                ),
                onsubmit="event.preventDefault(); webauthnLogin(this)",
            ),
            ft.A(
                "Забув доступ?",
                href="/recover",
                cls="btn-secondary",
                style="margin-top:12px;",
            ),
            ft.A(
                "Немає акаунту? Зареєструватися",
                href="/register",
                cls="btn-secondary",
                style="margin-top:8px;",
            ),
            cls="page-container",
        ),
        ft.Script(
            "document.addEventListener("
            "'DOMContentLoaded', webauthnConditionalLogin);"
        ),
    )


def _build_allow_credentials(creds):
    allow_credentials = []
    for c in creds:
        transports = []
        if c.get("transports"):
            for t in c["transports"].split(","):
                t = t.strip()
                if t:
                    try:
                        transports.append(AuthenticatorTransport(t))
                    except ValueError:
                        pass
        allow_credentials.append(
            PublicKeyCredentialDescriptor(
                id=_b64_to_bytes(c["credential_id"]),
                transports=transports or None,
            )
        )
    return allow_credentials


@rt("/login/begin", methods=["POST"])
async def post_login_begin(request: Request):
    form_data = await request.form()
    email = form_data.get("email", "").strip().lower()
    if not email:
        return Response("Введіть електронну пошту", status_code=400)
    user = await get_user_by_email(email)
    if not user:
        return Response("Користувача не знайдено", status_code=400)
    creds = await get_credentials_for_user(user["id"])
    allow_credentials = _build_allow_credentials(creds)
    token = secrets.token_urlsafe(32)
    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    await store_challenge(token, options.challenge)
    resp = Response(
        content=options_to_json(options),
        media_type="application/json",
    )
    ck = dict(httponly=True, max_age=300, samesite="lax")
    resp.set_cookie("webauthn_token", token, **ck)
    resp.set_cookie("webauthn_email", email, **ck)
    return resp


@rt("/login/complete", methods=["POST"])
async def post_login_complete(request: Request, session):
    token = request.cookies.get("webauthn_token")
    if not token:
        return Response("Сесію входу не знайдено", status_code=400)
    challenge = await get_and_delete_challenge(token)
    if not challenge:
        return Response("Виклик прострочений", status_code=400)
    body = await request.json()
    cred_id_b64 = body.get("id", "")
    cred_data = await get_credential_by_id(cred_id_b64)
    if not cred_data:
        return Response("Ключ не знайдено", status_code=400)
    email = request.cookies.get("webauthn_email", "")
    if email:
        user = await get_user_by_email(email)
        if not user or user["id"] != cred_data["user_id"]:
            return Response("Невірний ключ для цього користувача", status_code=400)
    else:
        user = await get_user_by_id(cred_data["user_id"])
        if not user:
            return Response("Користувача не знайдено", status_code=400)
    try:
        verification = verify_authentication_response(
            credential=body,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=RP_ORIGIN,
            credential_public_key=_b64_to_bytes(cred_data["public_key"]),
            credential_current_sign_count=int(cred_data["sign_count"]),
        )
    except Exception as e:
        return Response(f"Помилка верифікації: {e}", status_code=400)
    await update_credential_sign_count(cred_id_b64, verification.new_sign_count)
    session["user_id"] = str(user["id"])
    session["email"] = user.get("email", "")
    resp = Response(status_code=200)
    resp.delete_cookie("webauthn_token")
    resp.delete_cookie("webauthn_email")
    return resp


@rt("/login/conditional")
async def get_login_conditional():
    token = secrets.token_urlsafe(32)
    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=[],
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    await store_challenge(token, options.challenge)
    resp = Response(
        content=options_to_json(options),
        media_type="application/json",
    )
    ck = dict(httponly=True, max_age=300, samesite="lax")
    resp.set_cookie("webauthn_token", token, **ck)
    return resp


@rt("/recover")
def get_recover():
    return ft.Main(
        ft.Div(
            ft.H1("БІНГО", cls="page-title"),
            ft.P("Відновлення доступу", cls="page-subtitle"),
            ft.P(
                "Введіть вашу електронну пошту для отримання посилання",
                cls="page-hint",
            ),
            ft.Form(
                ft.Input(
                    type="email",
                    name="email",
                    placeholder="Електронна пошта",
                    required=True,
                    cls="cell-input",
                    style="width:300px;height:48px;margin-bottom:16px;",
                ),
                ft.Button(
                    "Надіслати посилання",
                    cls="btn-primary",
                    type="submit",
                ),
                action="/recover/send",
                method="POST",
            ),
            ft.A(
                "Повернутися до входу",
                href="/login",
                cls="btn-secondary",
                style="margin-top:12px;",
            ),
            cls="page-container",
        ),
    )


@rt("/recover/send", methods=["POST"])
async def post_recover_send(request: Request):
    form_data = await request.form()
    email = form_data.get("email", "").strip().lower()
    if email:
        user = await get_user_by_email(email)
        if user:
            token = secrets.token_urlsafe(32)
            await store_recovery_token(user["id"], token)
            await send_recovery_email(email, token)
    return ft.Main(
        ft.Div(
            ft.H1("БІНГО", cls="page-title"),
            ft.P("Перевірте пошту", cls="page-subtitle"),
            ft.P(
                "Якщо акаунт з такою поштою існує, "
                "ми надіслали посилання для відновлення.",
                cls="page-hint",
            ),
            ft.A("На сторінку входу", href="/login", cls="btn-primary"),
            cls="page-container",
        ),
    )


@rt("/recover/verify/{token}")
async def get_recover_verify(token: str, session):
    user_id = await get_and_delete_recovery_token(token)
    if not user_id:
        return ft.Main(
            ft.Div(
                ft.H1("БІНГО", cls="page-title"),
                ft.P("Помилка", cls="page-subtitle"),
                ft.P(
                    "Посилання недійсне або прострочене.",
                    cls="page-hint",
                ),
                ft.A("Спробувати знову", href="/recover", cls="btn-primary"),
                cls="page-container",
            ),
        )
    session["user_id"] = str(user_id)
    user = await get_user_by_id(user_id)
    if user:
        session["email"] = user.get("email", "")
    return ft.RedirectResponse("/recover/passkey", status_code=303)


@rt("/recover/passkey")
def get_recover_passkey(session):
    return ft.Main(
        ft.Div(
            ft.H1("БІНГО", cls="page-title"),
            ft.P("Новий Passkey", cls="page-subtitle"),
            ft.P(
                "Зареєструйте новий passkey для вашого акаунту",
                cls="page-hint",
            ),
            ft.Form(
                ft.Button(
                    "Зареєструвати новий Passkey",
                    cls="btn-primary",
                    type="submit",
                ),
                onsubmit="event.preventDefault(); webauthnRecoveryRegister(this)",
            ),
            cls="page-container",
        ),
    )


@rt("/recover/passkey/begin", methods=["POST"])
async def post_recover_passkey_begin(session):
    user_id = session.get("user_id")
    if not user_id:
        return Response("Не авторизовано", status_code=401)
    user = await get_user_by_id(user_id)
    if not user:
        return Response("Користувача не знайдено", status_code=400)
    email = user.get("email", "")
    token = secrets.token_urlsafe(32)
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=secrets.token_bytes(32),
        user_name=email,
        user_display_name=user.get("display_name", email),
        authenticator_selection=None,
    )
    await store_challenge(token, options.challenge)
    resp = Response(
        content=options_to_json(options),
        media_type="application/json",
    )
    ck = dict(httponly=True, max_age=300, samesite="lax")
    resp.set_cookie("webauthn_token", token, **ck)
    return resp


@rt("/recover/passkey/complete", methods=["POST"])
async def post_recover_passkey_complete(request: Request, session):
    user_id = session.get("user_id")
    if not user_id:
        return Response("Не авторизовано", status_code=401)
    token = request.cookies.get("webauthn_token")
    if not token:
        return Response("Сесію реєстрації не знайдено", status_code=400)
    challenge = await get_and_delete_challenge(token)
    if not challenge:
        return Response("Виклик прострочений", status_code=400)
    body = await request.json()
    try:
        verification = verify_registration_response(
            credential=body,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=RP_ORIGIN,
        )
    except Exception as e:
        return Response(f"Помилка верифікації: {e}", status_code=400)
    cred_id_b64 = (
        base64.urlsafe_b64encode(verification.credential_id).decode().rstrip("=")
    )
    pub_key_b64 = (
        base64.urlsafe_b64encode(verification.credential_public_key)
        .decode()
        .rstrip("=")
    )
    transports = ""
    if hasattr(body.get("response", {}), "get"):
        transports = ",".join(body.get("response", {}).get("transports", []))
    await store_credential(
        user_id=user_id,
        credential_id_b64=cred_id_b64,
        public_key_b64=pub_key_b64,
        sign_count=verification.sign_count,
        transports=transports,
    )
    resp = Response(status_code=200)
    resp.delete_cookie("webauthn_token")
    return resp


@rt("/logout", methods=["POST"])
def post_logout(session):
    session.clear()
    return ft.RedirectResponse("/", status_code=303)


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


async def create_template_in_db(cols, rows, items, user_id=None):
    template_id = await db.incr("template_id")
    mapping = {
        "cols": cols,
        "rows": rows,
    }
    if user_id:
        mapping["user_id"] = user_id
    await db.hset(
        f"template:{template_id}",
        mapping=mapping,
    )
    await db.lpush(f"template_items:{template_id}", *items)
    return template_id


async def create_bingo_from_template_in_db(template_id, user_id=None):
    bingo_id = await db.incr("bingo_id")
    bingo_key = f"bingo:{bingo_id}"
    template = await get_template_from_db(template_id)
    mapping = {
        "template_id": template_id,
        "cols": template["cols"],
        "rows": template["rows"],
    }
    if user_id:
        mapping["user_id"] = user_id
    await db.hset(
        bingo_key,
        mapping=mapping,
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


# --- Auth DB helpers ---


def _b64_to_bytes(b64):
    padded = b64 + "=" * (-len(b64) % 4)
    return base64.urlsafe_b64decode(padded)


async def create_user_in_db(email, display_name):
    email = email.lower()
    was_set = await db.setnx(f"email:{email}", "pending")
    if not was_set:
        raise ValueError(f"Email '{email}' already taken")
    user_id = await db.incr("user_id")
    await db.hset(
        f"user:{user_id}",
        mapping={
            "email": email,
            "display_name": display_name,
        },
    )
    await db.set(f"email:{email}", str(user_id))
    return user_id


async def get_user_by_email(email):
    email = email.lower()
    user_id = await db.get(f"email:{email}")
    if not user_id or user_id == "pending":
        return None
    user_data = await db.hgetall(f"user:{user_id}")
    if not user_data:
        return None
    user_data["id"] = user_id
    return user_data


async def get_user_by_id(user_id):
    user_data = await db.hgetall(f"user:{user_id}")
    if not user_data:
        return None
    user_data["id"] = str(user_id)
    return user_data


async def store_credential(
    user_id, credential_id_b64, public_key_b64, sign_count, transports=""
):
    await db.hset(
        f"credential:{credential_id_b64}",
        mapping={
            "user_id": str(user_id),
            "public_key": public_key_b64,
            "sign_count": str(sign_count),
            "transports": transports,
        },
    )
    await db.sadd(f"user_credentials:{user_id}", credential_id_b64)


async def get_credentials_for_user(user_id):
    cred_ids = await db.smembers(f"user_credentials:{user_id}")
    creds = []
    for cid in cred_ids:
        data = await db.hgetall(f"credential:{cid}")
        if data:
            data["credential_id"] = cid
            creds.append(data)
    return creds


async def get_credential_by_id(credential_id_b64):
    data = await db.hgetall(f"credential:{credential_id_b64}")
    if not data:
        return None
    data["credential_id"] = credential_id_b64
    return data


async def update_credential_sign_count(credential_id_b64, new_count):
    await db.hset(f"credential:{credential_id_b64}", "sign_count", str(new_count))


async def store_challenge(token, challenge):
    if isinstance(challenge, bytes):
        challenge_b64 = base64.urlsafe_b64encode(challenge).decode().rstrip("=")
    else:
        challenge_b64 = challenge
    await db.setex(f"challenge:{token}", 300, challenge_b64)


async def get_and_delete_challenge(token):
    key = f"challenge:{token}"
    challenge_b64 = await db.get(key)
    if challenge_b64:
        await db.delete(key)
        return _b64_to_bytes(challenge_b64)
    return None


async def store_recovery_token(user_id, token):
    await db.setex(f"recovery:{token}", 1800, str(user_id))


async def get_and_delete_recovery_token(token):
    key = f"recovery:{token}"
    user_id = await db.get(key)
    if user_id:
        await db.delete(key)
        return user_id
    return None


async def send_recovery_email(email, token):
    url = f"{RP_ORIGIN}/recover/verify/{token}"
    print(f"[RECOVERY] Magic link for {email}: {url}")
