from modules.requisicoes_pendentes.view import View

NOME = "Requisições"
ORDEM = 2


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = View(parent)
    view.pack(fill="both", expand=True)
