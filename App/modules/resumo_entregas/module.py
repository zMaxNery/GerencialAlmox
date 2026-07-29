from modules.resumo_entregas.view import ResumoEntregasView

NOME = "Material Entregue"
ORDEM = 3


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = ResumoEntregasView(parent)
    view.pack(fill="both", expand=True)
