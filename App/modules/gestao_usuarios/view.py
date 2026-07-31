from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox, ttk
from typing import Any

from core.access_repository import AccessRepository
from core.user_session import obter_usuario_atual


class GestaoUsuariosView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.repository = AccessRepository()
        self.usuario_logado = obter_usuario_atual()
        self.usuario_id_selecionado: int | None = None
        self.usuarios_por_item: dict[str, dict[str, Any]] = {}
        self.modulos: list[dict[str, Any]] = []
        self.vars_modulos: dict[str, ctk.BooleanVar] = {}

        if self.usuario_logado is None or not self.usuario_logado.administrador:
            raise PermissionError(
                "Somente administradores podem abrir a Gestão de Usuários."
            )

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)

        self._montar_cabecalho()
        self._montar_lista_usuarios()
        self._montar_formulario()
        self._carregar_dados()

    def _montar_cabecalho(self) -> None:
        ctk.CTkLabel(
            self,
            text="Gestão de Usuários",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")

    def _montar_lista_usuarios(self) -> None:
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, padx=(20, 10), pady=(10, 20), sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        botoes = ctk.CTkFrame(frame, fg_color="transparent")
        botoes.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        botoes.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            botoes,
            text="Novo usuário",
            command=self._novo_usuario,
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkButton(
            botoes,
            text="Atualizar lista",
            command=self._carregar_dados,
        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        colunas = ("nome", "windows", "status")
        self.tree = ttk.Treeview(frame, columns=colunas, show="headings", selectmode="browse")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("windows", text="Usuário")
        self.tree.heading("status", text="Status")
        self.tree.column("nome", width=180, anchor="w")
        self.tree.column("windows", width=150, anchor="w")
        self.tree.column("status", width=80, anchor="center")
        self.tree.grid(row=1, column=0, padx=(10, 0), pady=(0, 10), sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._selecionar_usuario)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, padx=(0, 10), pady=(0, 10), sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _montar_formulario(self) -> None:
        frame = ctk.CTkScrollableFrame(self, label_text="Cadastro e permissões")
        frame.grid(row=1, column=1, padx=(10, 20), pady=(10, 20), sticky="nsew")
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Nome de exibição:").grid(
            row=0, column=0, padx=10, pady=8, sticky="w"
        )
        self.ent_nome = ctk.CTkEntry(frame)
        self.ent_nome.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(frame, text="Usuário:").grid(
            row=1, column=0, padx=10, pady=8, sticky="w"
        )
        self.ent_windows = ctk.CTkEntry(frame)
        self.ent_windows.grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        self.var_ativo = ctk.BooleanVar(value=True)
        self.chk_ativo = ctk.CTkCheckBox(frame, text="Usuário ativo", variable=self.var_ativo)
        self.chk_ativo.grid(row=2, column=0, padx=10, pady=8, sticky="w")

        self.var_admin = ctk.BooleanVar(value=False)
        self.chk_admin = ctk.CTkCheckBox(
            frame,
            text="Administrador",
            variable=self.var_admin,
            command=self._atualizar_estado_modulos,
        )
        self.chk_admin.grid(row=2, column=1, padx=10, pady=8, sticky="w")

        ctk.CTkLabel(
            frame,
            text="Módulos",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=4, column=0, columnspan=2, padx=10, pady=(20, 8), sticky="w")

        self.frame_modulos = ctk.CTkFrame(frame)
        self.frame_modulos.grid(row=5, column=0, columnspan=2, padx=10, pady=8, sticky="ew")
        self.frame_modulos.grid_columnconfigure(0, weight=1)

        botoes = ctk.CTkFrame(frame, fg_color="transparent")
        botoes.grid(row=6, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        botoes.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            botoes,
            text="Salvar usuário",
            command=self._salvar_usuario,
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.btn_excluir = ctk.CTkButton(
            botoes,
            text="Excluir usuário",
            command=self._excluir_usuario,
            fg_color="#A93226",
            hover_color="#7B241C",
        )
        self.btn_excluir.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _carregar_dados(self) -> None:
        try:
            self.modulos = self.repository.listar_modulos(somente_ativos=False)
            usuarios = self.repository.listar_usuarios()
        except Exception as exc:
            messagebox.showerror("Erro", f"Não foi possível carregar os dados.\n\n{exc}")
            return

        self._montar_checkboxes_modulos()

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.usuarios_por_item.clear()

        for usuario in usuarios:
            item_id = self.tree.insert(
                "",
                "end",
                values=(
                    usuario.get("nome_exibicao", ""),
                    usuario.get("usuario_windows", ""),
                    "Ativo" if usuario.get("ativo") else "Inativo",
                ),
            )
            self.usuarios_por_item[item_id] = usuario

        if self.usuario_id_selecionado is None:
            self._novo_usuario()

    def _montar_checkboxes_modulos(self) -> None:
        for widget in self.frame_modulos.winfo_children():
            widget.destroy()
        self.vars_modulos.clear()

        for linha, modulo in enumerate(self.modulos):
            codigo = str(modulo.get("codigo") or "").strip().lower()
            if not codigo:
                continue
            var = ctk.BooleanVar(value=False)
            self.vars_modulos[codigo] = var
            checkbox = ctk.CTkCheckBox(
                self.frame_modulos,
                text=f"{modulo.get('nome', codigo)}  [{codigo}]",
                variable=var,
            )
            checkbox.grid(row=linha, column=0, padx=10, pady=6, sticky="w")

        self._atualizar_estado_modulos()

    def _novo_usuario(self) -> None:
        self.usuario_id_selecionado = None
        self.ent_nome.delete(0, "end")
        self.ent_windows.delete(0, "end")
        self.var_ativo.set(True)
        self.var_admin.set(False)
        for var in self.vars_modulos.values():
            var.set(False)
        self._atualizar_estado_modulos()
        self.btn_excluir.configure(state="disabled")
        self.ent_nome.focus_set()

    def _selecionar_usuario(self, _event=None) -> None:
        selecao = self.tree.selection()
        if not selecao:
            return

        usuario = self.usuarios_por_item.get(selecao[0])
        if usuario is None:
            return

        self.usuario_id_selecionado = int(usuario["id"])
        self.ent_nome.delete(0, "end")
        self.ent_nome.insert(0, usuario.get("nome_exibicao", ""))
        self.ent_windows.delete(0, "end")
        self.ent_windows.insert(0, usuario.get("usuario_windows", ""))
        self.var_ativo.set(bool(usuario.get("ativo")))
        self.var_admin.set(bool(usuario.get("administrador")))

        try:
            permitidos = self.repository.listar_modulos_usuario(self.usuario_id_selecionado)
        except Exception as exc:
            messagebox.showerror("Erro", f"Não foi possível carregar as permissões.\n\n{exc}")
            permitidos = set()

        for codigo, var in self.vars_modulos.items():
            var.set(codigo in permitidos)

        self._atualizar_estado_modulos()
        self.btn_excluir.configure(state="normal")

    def _atualizar_estado_modulos(self) -> None:
        estado = "disabled" if self.var_admin.get() else "normal"
        for widget in self.frame_modulos.winfo_children():
            if isinstance(widget, ctk.CTkCheckBox):
                widget.configure(state=estado)

    def _salvar_usuario(self) -> None:
        try:
            usuario = self.repository.salvar_usuario(
                usuario_id=self.usuario_id_selecionado,
                usuario_windows=self.ent_windows.get(),
                nome_exibicao=self.ent_nome.get(),
                ativo=self.var_ativo.get(),
                administrador=self.var_admin.get(),
            )
            usuario_id = int(usuario["id"])

            selecionados = [
                codigo
                for codigo, var in self.vars_modulos.items()
                if var.get()
            ]
            self.repository.salvar_modulos_usuario(usuario_id, selecionados)
            self.usuario_id_selecionado = usuario_id

        except Exception as exc:
            messagebox.showerror("Erro ao salvar", str(exc))
            return

        messagebox.showinfo(
            "Usuário salvo",
            "As permissões foram salvas. O usuário deve clicar em "
            "'Recarregar módulos' para atualizar o menu.",
        )
        self._carregar_dados()

    def _excluir_usuario(self) -> None:
        if self.usuario_id_selecionado is None:
            return

        if (
            self.usuario_logado is not None
            and self.usuario_id_selecionado == self.usuario_logado.id
        ):
            messagebox.showwarning(
                "Operação bloqueada",
                "Você não pode excluir o usuário administrador que está usando o sistema.",
            )
            return

        if not messagebox.askyesno(
            "Excluir usuário",
            "Confirma a exclusão deste usuário e de todas as suas permissões?",
        ):
            return

        try:
            self.repository.excluir_usuario(self.usuario_id_selecionado)
        except Exception as exc:
            messagebox.showerror("Erro ao excluir", str(exc))
            return

        self._novo_usuario()
        self._carregar_dados()
