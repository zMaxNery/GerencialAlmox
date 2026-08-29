from modules.aponta_baixa_totvs.view import View

NOME = "Baixas TOTVS"
ORDEM = 6


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = View(parent)
    view.pack(fill="both", expand=True)
