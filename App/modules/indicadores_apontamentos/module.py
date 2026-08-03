from modules.indicadores_apontamentos.view import IndicadoresApontamentosView

CODIGO = "indicadores_apontamentos"
NOME = "Indicadores de Entrega"
ORDEM = 8


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = IndicadoresApontamentosView(parent)
    view.pack(fill="both", expand=True)
