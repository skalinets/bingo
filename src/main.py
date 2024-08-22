from fasthtml import common as ft

app,rt = ft.fast_app()

@rt('/')
def get(): return ft.Div(ft.P('Hello World!'), hx_get="/change")

ft.serve()
