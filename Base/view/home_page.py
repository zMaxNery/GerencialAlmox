import customtkinter as ctk
from core.module_loader import ModuleLoader

class HomePage(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurações gerais da tela
        ctk.set_appearance_mode("Dark")
        self.title("Teste")

        # Abre com a janeta já expandida
        self.after(0, lambda: self.state('zoomed'))

        # Configuração de Grid (Layout)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Barra lateral
        self.barra_lateral()

        # Construtor da tela principal
        self.tela_principal()

        # Carrega os módulos na raiz do projeto
        self.carregar_menu_modulos()

    def limpar_tela(self):
        for widget in self.conteudo_frame.winfo_children():
            widget.destroy()

    '''
    Configurações das janelas
    Barra lateral e Tela Principal
    '''
    def tela_principal(self):
        self.conteudo_frame = ctk.CTkFrame(self, corner_radius=0)
        self.conteudo_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.conteudo_frame.grid_columnconfigure(0, weight=1)
        
    # Constrói a barra lateral
    def barra_lateral(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Gerencial", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

    def btn_change_theme(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")

    def carregar_menu_modulos(self):

        modulos = ModuleLoader.carregar_modulos()

        linha = 1

        for modulo in modulos:

            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=modulo.NOME,
                command=lambda m=modulo: m.abrir(self.conteudo_frame)
            )

            btn.grid(
                row=linha,
                column=0,
                padx=20,
                pady=10
            )

            linha += 1
