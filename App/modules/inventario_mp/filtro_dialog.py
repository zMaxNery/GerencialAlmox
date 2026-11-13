from __future__ import annotations

from datetime import date, datetime
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk


class FiltroInventarioDialog(ctk.CTkToplevel):
    """Janela para filtrar o Inventário MP por período e usuário(s)."""

    def __init__(
        self,
        parent,
        usuarios: list[str],
        filtros_atuais: dict,
        ao_aplicar: Callable[[dict], None],
        ao_limpar: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self.title("Filtrar Inventário MP")
        self.geometry("500x570")
        self.minsize(440, 480)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self.ao_aplicar = ao_aplicar
        self.ao_limpar = ao_limpar
        self.vars_usuarios: dict[str, ctk.BooleanVar] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self,
            text="Filtros da tabela",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(18, 4), sticky="w")

        ctk.CTkLabel(
            self,
            text="Deixe as datas vazias para não restringir o período.",
            text_color=("gray35", "gray70"),
        ).grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")

        periodo = ctk.CTkFrame(self)
        periodo.grid(row=2, column=0, padx=20, pady=(0, 12), sticky="ew")
        periodo.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(periodo, text="Data inicial (de)").grid(
            row=0, column=0, padx=10, pady=(10, 4), sticky="w"
        )
        ctk.CTkLabel(periodo, text="Data final (até)").grid(
            row=0, column=1, padx=10, pady=(10, 4), sticky="w"
        )

        data_de = filtros_atuais.get("data_de")
        data_ate = filtros_atuais.get("data_ate")
        self.ent_data_de = ctk.CTkEntry(
            periodo, placeholder_text="dd/mm/aaaa", height=36
        )
        self.ent_data_ate = ctk.CTkEntry(
            periodo, placeholder_text="dd/mm/aaaa", height=36
        )
        self.ent_data_de.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.ent_data_ate.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="ew")
        if data_de:
            self.ent_data_de.insert(0, data_de.strftime("%d/%m/%Y"))
        if data_ate:
            self.ent_data_ate.insert(0, data_ate.strftime("%d/%m/%Y"))

        usuarios_frame = ctk.CTkFrame(self)
        usuarios_frame.grid(row=3, column=0, padx=20, pady=(0, 12), sticky="nsew")
        usuarios_frame.grid_columnconfigure(0, weight=1)
        usuarios_frame.grid_rowconfigure(1, weight=1)

        topo_usuarios = ctk.CTkFrame(usuarios_frame, fg_color="transparent")
        topo_usuarios.grid(row=0, column=0, padx=10, pady=8, sticky="ew")
        topo_usuarios.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            topo_usuarios,
            text="Usuários",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            topo_usuarios,
            text="Marcar todos",
            width=105,
            height=28,
            command=lambda: self._marcar_todos(True),
        ).grid(row=0, column=1, padx=(4, 0))
        ctk.CTkButton(
            topo_usuarios,
            text="Limpar seleção",
            width=115,
            height=28,
            fg_color="gray",
            hover_color="dimgray",
            command=lambda: self._marcar_todos(False),
        ).grid(row=0, column=2, padx=(4, 0))

        lista = ctk.CTkScrollableFrame(
            usuarios_frame,
            label_text="Selecione um ou mais usuários",
        )
        lista.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        lista.grid_columnconfigure(0, weight=1)

        selecionados = filtros_atuais.get("usuarios")
        for linha, usuario in enumerate(usuarios):
            var = ctk.BooleanVar(
                value=True if selecionados is None else usuario in selecionados
            )
            self.vars_usuarios[usuario] = var
            ctk.CTkCheckBox(
                lista,
                text=usuario,
                variable=var,
            ).grid(row=linha, column=0, padx=8, pady=5, sticky="w")

        if not usuarios:
            ctk.CTkLabel(
                lista,
                text="Ainda não há usuários nos registros carregados.",
            ).grid(row=0, column=0, padx=8, pady=8, sticky="w")

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.grid(row=4, column=0, padx=20, pady=(0, 18), sticky="ew")
        botoes.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            botoes,
            text="Limpar filtros",
            fg_color="gray",
            hover_color="dimgray",
            command=self._limpar,
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(
            botoes,
            text="Cancelar",
            fg_color="#6C757D",
            hover_color="#5A6268",
            command=self.destroy,
        ).grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkButton(
            botoes,
            text="Aplicar",
            fg_color="#2E8B57",
            hover_color="#247447",
            command=self._aplicar,
        ).grid(row=0, column=2, padx=(5, 0), sticky="ew")

    def _marcar_todos(self, marcado: bool) -> None:
        for variavel in self.vars_usuarios.values():
            variavel.set(marcado)

    def _ler_data(self, entrada: ctk.CTkEntry, rotulo: str) -> date | None:
        valor = entrada.get().strip()
        if not valor:
            return None
        try:
            return datetime.strptime(valor, "%d/%m/%Y").date()
        except ValueError as exc:
            raise ValueError(
                f"{rotulo}: informe uma data válida no formato DD/MM/AAAA."
            ) from exc

    def _aplicar(self) -> None:
        try:
            data_de = self._ler_data(self.ent_data_de, "Data inicial")
            data_ate = self._ler_data(self.ent_data_ate, "Data final")
        except ValueError as exc:
            messagebox.showwarning("Data inválida", str(exc), parent=self)
            return

        if data_de and data_ate and data_de > data_ate:
            messagebox.showwarning(
                "Período inválido",
                "A data inicial não pode ser posterior à data final.",
                parent=self,
            )
            return

        usuarios = {
            usuario
            for usuario, variavel in self.vars_usuarios.items()
            if variavel.get()
        }
        if self.vars_usuarios and not usuarios:
            messagebox.showwarning(
                "Usuários não selecionados",
                "Marque ao menos um usuário ou use Limpar filtros.",
                parent=self,
            )
            return

        todos_marcados = (
            bool(self.vars_usuarios)
            and len(usuarios) == len(self.vars_usuarios)
        )
        self.ao_aplicar(
            {
                "data_de": data_de,
                "data_ate": data_ate,
                "usuarios": None if todos_marcados or not self.vars_usuarios else usuarios,
            }
        )
        self.destroy()

    def _limpar(self) -> None:
        self.ao_limpar()
        self.destroy()
