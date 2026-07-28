from modules.entregas_est.view import EntregasEstView

NOME = "Requisições"
ORDEM = 2


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = EntregasEstView(parent)
    view.pack(fill="both", expand=True)
