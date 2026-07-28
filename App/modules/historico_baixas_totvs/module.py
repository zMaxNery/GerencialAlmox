from modules.historico_baixas_totvs.view import HistoricoBaixasTotvsView

NOME = "Histórico Baixa"
ORDEM = 7


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = HistoricoBaixasTotvsView(parent)
    view.pack(fill="both", expand=True)
