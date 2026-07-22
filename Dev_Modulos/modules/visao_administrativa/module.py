from modules.visao_administrativa.view import VisaoAdministrativaView

NOME = "Visão Administrativa"
ORDEM = 30


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = VisaoAdministrativaView(parent)
    view.pack(fill="both", expand=True)
