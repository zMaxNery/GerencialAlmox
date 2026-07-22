from modules.importador_emails.view import ImportadorEmailsView

NOME = "Importar E-mails"
ORDEM = 10


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = ImportadorEmailsView(parent)
    view.pack(fill="both", expand=True)
