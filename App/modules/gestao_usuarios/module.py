from modules.gestao_usuarios.view import GestaoUsuariosView

CODIGO = "gestao_usuarios"
NOME = "Gestão de Usuários"
ORDEM = 100


def abrir(parent):
    for widget in parent.winfo_children():
        widget.destroy()

    view = GestaoUsuariosView(parent)
    view.pack(fill="both", expand=True)
