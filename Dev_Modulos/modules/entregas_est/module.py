from modules.entregas_est.view import EntregasEstView

NOME = "Entregas EST"
ORDEM = 20


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = EntregasEstView(parent)
    view.pack(fill="both", expand=True)
