from __future__ import annotations

import getpass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk
from typing import Callable

import customtkinter as ctk

from modules._shared.search_utils import corresponde_pesquisa
from modules._shared.virtual_keyboard import abrir_teclado_virtual

from modules.material_entregue.scripts_devolucao import Scripts


class JanelaDevolucao(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.scripts = Scripts(self)

        self.row = row
        self.repository = repository
        self.on_success = on_success

        self.quantidade_disponivel = Decimal(
            str(row.get("quantidade_entregue") or 0)
        )

        self.quantidade_var = ctk.StringVar(value="")

        self.title("Devolver material")
        self.geometry("760x550")
        self.resizable(False, False)

        # Mantém a janela na frente e bloqueia a tela principal.
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.focus_force()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_form()
        self._build_keypad()

        self.protocol(
            "WM_DELETE_WINDOW",
            self._fechar,
        )

    def _build_header(self) -> None:
        material = self.row.get("material") or ""
        dimensao = self.row.get("dimensao") or ""

        header = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )

        header.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=20,
            pady=(20, 10),
        )

        ctk.CTkLabel(
            header,
            text="Devolver material",
            font=ctk.CTkFont(
                size=22,
                weight="bold",
            ),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=f"{material} | {dimensao}",
            font=ctk.CTkFont(size=16),
        ).pack(anchor="w", pady=(5, 0))

        ctk.CTkLabel(
            header,
            text=(
                "Disponível para devolução: "
                f"{self._fmt(self.quantidade_disponivel)}"
            ),
            text_color="#E6A23C",
            font=ctk.CTkFont(
                size=15,
                weight="bold",
            ),
        ).pack(anchor="w", pady=(5, 0))

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self)

        form.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(20, 10),
            pady=(0, 20),
        )

        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            form,
            text="Quantidade devolvida:",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=15,
            pady=(15, 5),
        )

        self.visor = ctk.CTkEntry(
            form,
            textvariable=self.quantidade_var,
            justify="right",
            height=55,
            font=ctk.CTkFont(
                size=26,
                weight="bold",
            ),
        )

        self.visor.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 15),
        )

        ctk.CTkLabel(
            form,
            text="Observação:",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=15,
            pady=(5, 5),
        )

        self.observacao_entry = ctk.CTkTextbox(
            form,
            height=120,
            font=ctk.CTkFont(size=14),
        )

        self.observacao_entry.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 15),
        )

        ctk.CTkButton(
            form,
            text="Confirmar devolução",
            height=45,
            command=self._confirmar,
        ).grid(
            row=4,
            column=0,
            sticky="ew",
            padx=15,
            pady=(5, 8),
        )

        ctk.CTkButton(
            form,
            text="Cancelar",
            height=40,
            fg_color="#555555",
            hover_color="#444444",
            command=self._fechar,
        ).grid(
            row=5,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 15),
        )

    def _build_keypad(self) -> None:
        keypad = ctk.CTkFrame(self)

        keypad.grid(
            row=1,
            column=1,
            sticky="ns",
            padx=(0, 20),
            pady=(0, 20),
        )

        for coluna in range(3):
            keypad.grid_columnconfigure(
                coluna,
                weight=1,
            )

        teclas = (
            ("7", 0, 0),
            ("8", 0, 1),
            ("9", 0, 2),
            ("4", 1, 0),
            ("5", 1, 1),
            ("6", 1, 2),
            ("1", 2, 0),
            ("2", 2, 1),
            ("3", 2, 2),
            ("0", 3, 0),
            ("00", 3, 1),
            (",", 3, 2),
        )

        for texto, linha, coluna in teclas:
            ctk.CTkButton(
                keypad,
                text=texto,
                width=70,
                height=62,
                font=ctk.CTkFont(
                    size=21,
                    weight="bold",
                ),
                command=lambda valor=texto: (
                    self._adicionar_tecla(valor)
                ),
            ).grid(
                row=linha,
                column=coluna,
                padx=5,
                pady=5,
            )

        ctk.CTkButton(
            keypad,
            text="⌫",
            height=50,
            command=self._apagar,
        ).grid(
            row=4,
            column=0,
            padx=5,
            pady=5,
            sticky="ew",
        )

        ctk.CTkButton(
            keypad,
            text="Limpar",
            height=50,
            command=self._limpar,
        ).grid(
            row=4,
            column=1,
            padx=5,
            pady=5,
            sticky="ew",
        )

        ctk.CTkButton(
            keypad,
            text="Tudo",
            height=50,
            command=self._preencher_tudo,
        ).grid(
            row=4,
            column=2,
            padx=5,
            pady=5,
            sticky="ew",
        )
    