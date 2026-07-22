import customtkinter as ctk

NOME = "Módulo Teste"
ORDEM = 50

def abrir(parent):

    # Limpa a área principal
    for widget in parent.winfo_children():
        widget.destroy()

    titulo = ctk.CTkLabel(
        parent,
        text="Módulo carregado com sucesso!",
        font=ctk.CTkFont(size=24, weight="bold")
    )

    titulo.pack(pady=30)

    descricao = ctk.CTkLabel(
        parent,
        text="O carregamento dinâmico está funcionando."
    )

    descricao.pack(pady=10)

    botao = ctk.CTkButton(
        parent,
        text="Clique aqui",
        command=lambda: print("Botão do módulo funcionando")
    )

    botao.pack(pady=20)