import customtkinter as ctk
from tkinterdnd2 import TkinterDnD

from core.module_loader import ModuleLoader

'''
Tela principal da aplicação
'''
class HomePage(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Start da lista de módulos encontrados
        self.botoes_modulos: list[ctk.CTkButton] = []

        # Carrega o Drag-Drop
        self.drag_drop_disponivel = False
        self.drag_drop_erro: str | None = None

        try:
            self.tkdnd_version = TkinterDnD.require(self)
            self.drag_drop_disponivel = True
        except Exception as exc:
            self.drag_drop_erro = str(exc)
            print(f"Drag-and-drop indisponível: {exc}")

        # Configurações gerais da tela
        ctk.set_appearance_mode("Dark")
        self.title("Teste")

        # Abre com a janela já expandida
        self.after(0, lambda: self.state('zoomed'))

        # Configuração de Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        '''
        Carrega elementos da tela
        '''
        # Barra lateral
        self.barra_lateral()

        # Construtor da tela principal
        self.tela_principal()

        # Carrega os módulos na raiz do projeto
        self.carregar_menu_modulos()

    '''
    Configurações das janelas
    Barra lateral e Tela Principal
    '''
    # Construtor da tela principal
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

        self.sidebar_frame.grid_rowconfigure(98, weight=1)

        self.btn_recarregar = ctk.CTkButton(self.sidebar_frame, text="Recarregar módulos", command=self.recarregar_modulos)
        self.btn_recarregar.grid(row=99, column=0, padx=20, pady=(10, 5), sticky="ew")

        self.btn_theme = ctk.CTkButton(self.sidebar_frame, text="Mudar tema", command=self.btn_change_theme)
        self.btn_theme.grid(row=100, column=0, padx=20, pady=20, sticky="s")

    '''
    Funções
    '''
    # Alternador de tema do APP
    def btn_change_theme(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")

    # Carregador de módulos
    def carregar_menu_modulos(self, recarregar: bool = False) -> int:
        '''
        Remove os botões antigos da barra lateral, caso existam
        '''
        # Destrói todos os botões mapeados pela lista principal
        for botao in self.botoes_modulos:
            try:
                botao.destroy()
            except Exception:
                pass

        # Limpa a Lista
        self.botoes_modulos.clear()

        modulos = ModuleLoader.carregar_modulos(recarregar=recarregar)

        linha = 1

        for modulo in modulos:
            botao = ctk.CTkButton(
                self.sidebar_frame,
                text=modulo.NOME,
                command=lambda m=modulo: self.abrir_modulo(m),
            )

            botao.grid(
                row=linha,
                column=0,
                padx=20,
                pady=10,
                sticky="ew",
            )

            self.botoes_modulos.append(botao)
            linha += 1

        return len(modulos)
    
    # Abre o módulo selecionado
    def abrir_modulo(self, modulo) -> None:
        self.limpar_tela()
        modulo.abrir(self.conteudo_frame)

    # Limpa a tela ativa
    def limpar_tela(self):
        for widget in self.conteudo_frame.winfo_children():
            widget.destroy()

    # Recarrega módulos da pasta "modules"
    def recarregar_modulos(self) -> None:
        try:
            self.limpar_tela()
            self.update_idletasks()

            quantidade = self.carregar_menu_modulos(
                recarregar=True
            )

            ctk.CTkLabel(
                self.conteudo_frame,
                text=(
                    "Módulos recarregados com sucesso.\n"
                    f"{quantidade} módulo(s) encontrado(s)."
                ),
                font=ctk.CTkFont(size=18, weight="bold"),
            ).pack(expand=True, padx=30, pady=30)

        except Exception as exc:
            ctk.CTkLabel(
                self.conteudo_frame,
                text=f"Erro ao recarregar módulos:\n{exc}",
                text_color="#E74C3C",
                font=ctk.CTkFont(size=16),
            ).pack(expand=True, padx=30, pady=30)
