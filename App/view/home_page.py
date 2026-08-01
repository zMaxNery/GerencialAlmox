from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox
from tkinterdnd2 import TkinterDnD

from core.access_service import AccessService
from core.module_loader import ModuleLoader
from core.user_context import UserContext
from core.user_session import definir_usuario_atual

class HomePage(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.botoes_modulos: list[ctk.CTkButton] = []
        self.access_service: AccessService | None = None
        self.usuario_atual: UserContext | None = None
        self.erro_acesso: str | None = None

        self._carregar_contexto_usuario()

        tema_inicial = (
            self.usuario_atual.tema
            if self.usuario_atual is not None
            else "Dark"
        )
        ctk.set_appearance_mode(tema_inicial)

        self.drag_drop_disponivel = False
        self.drag_drop_erro: str | None = None
        try:
            self.tkdnd_version = TkinterDnD.require(self)
            self.drag_drop_disponivel = True
        except Exception as exc:
            self.drag_drop_erro = str(exc)
            print(f"Drag-and-drop indisponível: {exc}")

        self.title("Controles Almox")
        self.after(0, lambda: self.state("zoomed"))
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.barra_lateral()
        self.tela_principal()
        self.carregar_menu_modulos()
        self._mostrar_situacao_usuario()

    def _carregar_contexto_usuario(self) -> None:
        self.usuario_atual = None
        self.erro_acesso = None

        try:
            self.access_service = AccessService()
            self.usuario_atual = self.access_service.carregar_usuario_atual()
        except Exception as exc:
            self.erro_acesso = str(exc)
            print(f"Erro ao carregar controle de acesso: {exc}")

        definir_usuario_atual(self.usuario_atual)

    def tela_principal(self):
        self.conteudo_frame = ctk.CTkFrame(self, corner_radius=0)
        self.conteudo_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=20,
            pady=20,
        )
        self.conteudo_frame.grid_columnconfigure(0, weight=1)
        self.conteudo_frame.grid_rowconfigure(0, weight=1)

    def barra_lateral(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=230, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(96, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Controles Almox",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        self.lbl_usuario = ctk.CTkLabel(
            self.sidebar_frame,
            text=self._texto_usuario_lateral(),
            justify="left",
            anchor="w",
            wraplength=190,
        )
        self.lbl_usuario.grid(
            row=97,
            column=0,
            padx=20,
            pady=(10, 5),
            sticky="ew",
        )

        self.btn_recarregar = ctk.CTkButton(
            self.sidebar_frame,
            text="Recarregar módulos",
            command=self.recarregar_modulos,
        )
        self.btn_recarregar.grid(
            row=98,
            column=0,
            padx=20,
            pady=(10, 5),
            sticky="ew",
        )

        self.btn_theme = ctk.CTkButton(
            self.sidebar_frame,
            text="Mudar tema",
            command=self.btn_change_theme,
        )
        self.btn_theme.grid(
            row=99,
            column=0,
            padx=20,
            pady=(10, 5),
            sticky="ew",
        )

        self.btn_fechar = ctk.CTkButton(
            self.sidebar_frame,
            text="Fechar",
            command=self.destroy,
            height=50,
            fg_color="#F92C15",
            hover_color="#961F12",
        )
        self.btn_fechar.grid(
            row=100,
            column=0,
            padx=20,
            pady=(5, 20),
            sticky="ew",
        )

    def _texto_usuario_lateral(self) -> str:
        usuario_windows = AccessService.obter_usuario_windows()
        if self.usuario_atual is None:
            return f"Usuário: {usuario_windows}\nSem acesso configurado"

        return (
            f"{self.usuario_atual.nome_exibicao}\n"
            f"{self.usuario_atual.usuario_windows}"
        )

    def btn_change_theme(self):
        novo_tema = (
            "Light"
            if ctk.get_appearance_mode() == "Dark"
            else "Dark"
        )
        ctk.set_appearance_mode(novo_tema)

        if (
            self.usuario_atual is not None
            and self.access_service is not None
            and self.usuario_atual.ativo
        ):
            try:
                self.access_service.salvar_tema(
                    self.usuario_atual,
                    novo_tema,
                )
            except Exception as exc:
                messagebox.showwarning(
                    "Falha ao gravar tema",
                    f"\n{exc}",
                )

    def carregar_menu_modulos(self, recarregar: bool = False) -> int:
        for botao in self.botoes_modulos:
            try:
                botao.destroy()
            except Exception:
                pass
        self.botoes_modulos.clear()

        modulos = ModuleLoader.carregar_modulos(recarregar=recarregar)

        if self.access_service is not None:
            try:
                self.access_service.sincronizar_modulos(modulos)
            except Exception as exc:
                self.erro_acesso = str(exc)
                print(f"Erro ao sincronizar catálogo de módulos: {exc}")

        if self.usuario_atual is None or not self.usuario_atual.ativo:
            return 0

        modulos_permitidos = [
            modulo
            for modulo in modulos
            if self.usuario_atual.pode_acessar(modulo.CODIGO)
        ]

        linha = 1
        for modulo in modulos_permitidos:
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

        return len(modulos_permitidos)

    def abrir_modulo(self, modulo) -> None:
        if (
            self.usuario_atual is None
            or not self.usuario_atual.pode_acessar(modulo.CODIGO)
        ):
            messagebox.showerror(
                "Acesso não permitido",
                "Seu usuário não possui acesso a este módulo.",
            )
            return

        self.limpar_tela()
        modulo.abrir(self.conteudo_frame)

    def limpar_tela(self):
        for widget in self.conteudo_frame.winfo_children():
            widget.destroy()

    def _mostrar_situacao_usuario(self) -> None:
        if self.erro_acesso:
            titulo = "Não foi possível consultar seus acessos"
            detalhe = self.erro_acesso
        elif self.usuario_atual is None:
            titulo = "Usuário sem acesso configurado"
            detalhe = (
                f"Usuário: {AccessService.obter_usuario_windows()}\n"
                "Solicitar cadastro."
            )
        elif not self.usuario_atual.ativo:
            titulo = "Usuário inativo"
            detalhe = ""
        elif not self.botoes_modulos:
            titulo = "Nenhum módulo liberado"
            detalhe = ""
        else:
            return

        ctk.CTkLabel(
            self.conteudo_frame,
            text=f"{titulo}\n\n{detalhe}",
            justify="center",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, sticky="nsew", padx=30, pady=30)

    def recarregar_modulos(self) -> None:
        try:
            self.limpar_tela()
            self.update_idletasks()

            self._carregar_contexto_usuario()
            self.lbl_usuario.configure(text=self._texto_usuario_lateral())

            quantidade = self.carregar_menu_modulos(recarregar=True)
            self._mostrar_situacao_usuario()

            if (
                self.usuario_atual is not None
                and self.usuario_atual.ativo
                and quantidade > 0
            ):
                ctk.CTkLabel(
                    self.conteudo_frame,
                    text=(
                        "Módulos e permissões recarregados com sucesso."
                    ),
                    font=ctk.CTkFont(size=18, weight="bold"),
                ).grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        except Exception as exc:
            ctk.CTkLabel(
                self.conteudo_frame,
                text=f"Erro ao recarregar módulos:\n{exc}",
                text_color="#E74C3C",
                font=ctk.CTkFont(size=16),
            ).grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
