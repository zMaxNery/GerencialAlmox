from modules.resumo_requisicoes.view import VisaoAdministrativaView

NOME = "Resumo"
ORDEM = 30


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = VisaoAdministrativaView(parent)
    view.pack(fill="both", expand=True)
