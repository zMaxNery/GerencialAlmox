from __future__ import annotations

import tkinter as tk
from typing import Callable

import customtkinter as ctk


class TecladoFixo(ctk.CTkFrame):
    """
    Teclado virtual fixo da tela de inventário.
    """

    def __init__(
        self,
        parent,
        ao_proximo: Callable[[], None] | None = None,
        altura_tecla: int = 40,
        ao_alterar: Callable[[object], None] | None = None,
    ) -> None:
        super().__init__(parent)

        self._alvo = None
        self._ao_proximo = ao_proximo
        self._ao_alterar = ao_alterar
        self._altura = altura_tecla

        self._build()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def definir_alvo(self, campo) -> None:
        """Define o campo (CTkEntry) que receberá o que for digitado."""
        self._alvo = campo

    def registrar_campo(self, campo) -> None:
        """Faz o teclado acompanhar o foco deste campo."""
        campo.bind(
            "<FocusIn>",
            lambda _evento, c=campo: self.definir_alvo(c),
            add="+",
        )

    # ------------------------------------------------------------------
    # Construção
    # ------------------------------------------------------------------
    def _build(self) -> None:
        # Quatro colunas de mesma largura
        for coluna in range(4):
            self.grid_columnconfigure(
                coluna,
                weight=1,
                uniform="tecla",
            )

        # Disposição fixa das teclas
        disposicao = (
            ("1", 0, 0), ("2", 0, 1), ("3", 0, 2), ("A", 0, 3),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2), ("G", 1, 3),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2), ("L", 2, 3),
            ("0", 3, 0), (".", 3, 1), ("/", 3, 2), ("X", 3, 3),
        )

        for tecla, linha, coluna in disposicao:

            if tecla.isdigit():
                cor = "#26384D"
                hover = "#354F6B"
            else:
                cor = "#246B57"
                hover = "#31866C"

            botao = ctk.CTkButton(
                self,
                text=tecla,
                height=self._altura,
                corner_radius=12,
                fg_color=cor,
                hover_color=hover,
                text_color="#FFFFFF",
                font=ctk.CTkFont(
                    size=25,
                    weight="bold",
                ),
                command=lambda valor=tecla: self._digitar(valor),
            )

            botao.grid(
                row=linha,
                column=coluna,
                sticky="nsew",
                padx=4,
                pady=4,
            )

        # Controles inferiores
        controles = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )

        controles.grid(
            row=4,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(10, 4),
        )

        controles.grid_columnconfigure(
            (0, 1),
            weight=1,
            uniform="controle",
        )

        ctk.CTkButton(
            controles,
            text="⌫  Apagar",
            height=self._altura,
            corner_radius=12,
            fg_color="#B94A48",
            hover_color="#963B39",
            font=ctk.CTkFont(size=19, weight="bold"),
            command=self._apagar,
        ).grid(
            row=0,
            column=0,
            padx=4,
            sticky="ew",
        )

        ctk.CTkButton(
            controles,
            text="Próximo  ▶",
            height=self._altura,
            corner_radius=12,
            fg_color="#2E8B57",
            hover_color="#247447",
            font=ctk.CTkFont(size=19, weight="bold"),
            command=self._proximo,
        ).grid(
            row=0,
            column=1,
            padx=4,
            sticky="ew",
        )


    # ------------------------------------------------------------------
    # Ações das teclas
    # ------------------------------------------------------------------
    def _entry(self):
        if self._alvo is None:
            return None
        return getattr(self._alvo, "_entry", self._alvo)

    def _digitar(self, valor: str) -> None:
        entry = self._entry()
        if entry is None:
            return

        try:
            if entry.selection_present():
                entry.delete("sel.first", "sel.last")
            entry.insert("insert", valor)
            entry.focus_set()
            if self._ao_alterar is not None:
                self._ao_alterar(self._alvo)
        except tk.TclError:
            pass

    def _apagar(self) -> None:
        entry = self._entry()
        if entry is None:
            return

        try:
            if entry.selection_present():
                entry.delete("sel.first", "sel.last")
            else:
                posicao = entry.index("insert")
                if posicao > 0:
                    entry.delete(posicao - 1)
            entry.focus_set()
            if self._ao_alterar is not None:
                self._ao_alterar(self._alvo)
        except tk.TclError:
            pass

    def _proximo(self) -> None:
        if self._ao_proximo is not None:
            self._ao_proximo()
