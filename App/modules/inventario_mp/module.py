from modules.inventario_mp.view import InventarioMP

NOME = "Inventário MP"
ORDEM = 7


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = InventarioMP(parent)
    view.pack(fill="both", expand=True)
