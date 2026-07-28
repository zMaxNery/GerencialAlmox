from modules.lancamentos_totvs.view import LancamentosTotvsView

NOME = "Baixas TOTVS"
ORDEM = 6


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = LancamentosTotvsView(parent)
    view.pack(fill="both", expand=True)
