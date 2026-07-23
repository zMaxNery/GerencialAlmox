from modules.devolucoes_entrega.view import HistoricoDevolucoesView

NOME = "Histórico Devoluções"
ORDEM = 40


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = HistoricoDevolucoesView(parent)
    view.pack(fill="both", expand=True)
