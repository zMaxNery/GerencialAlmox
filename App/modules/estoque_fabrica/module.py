from modules.estoque_fabrica.view import MateriaisFabricaView

NOME = "Em Fábrica"
ORDEM = 4


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = MateriaisFabricaView(parent)
    view.pack(fill="both", expand=True)
