from modules.importador_requisicoes.view import ImportadorEmailsView

NOME = "Importar Requisições"
ORDEM = 1

def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = ImportadorEmailsView(parent)
    view.pack(fill="both", expand=True)
