from modules.configuracoes.view import ConfiguracoesView

CODIGO = "configuracoes"
NOME = "Est Inventário"
ORDEM = 90


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = ConfiguracoesView(parent)
    view.pack(fill="both", expand=True)
