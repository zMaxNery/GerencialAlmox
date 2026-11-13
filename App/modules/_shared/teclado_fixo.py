from __future__ import annotations

import tkinter as tk
from typing import Callable

import customtkinter as ctk


class TecladoFixo(ctk.CTkFrame):
    """Teclado virtual fixo da tela de inventário.

    Exibe somente as letras A, G, L e X e os números de 0 a 9.
    Os controles Apagar e Próximo continuam disponíveis para facilitar
    o preenchimento dos campos.
    """

    LINHAS = (
        list("1234567890"),
        list("AGLX"),
    )

    def __init__(
        self,
        parent,
        ao_proximo: Callable[[], None] | None = None,
        altura_tecla: int = 46,
    ) -> None:
        super().__init__(parent)

        self._alvo = None
        self._ao_proximo = ao_proximo
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
        colunas = max(len(linha) for linha in self.LINHAS)
        for coluna in range(colunas):
            self.grid_columnconfigure(coluna, weight=1, uniform="tecla")

        for linha_idx, teclas in enumerate(self.LINHAS):
            # Centraliza a fileira de letras abaixo dos números.
            deslocamento = (colunas - len(teclas)) // 2

            for coluna_idx, tecla in enumerate(teclas):
                botao = ctk.CTkButton(
                    self,
                    text=tecla,
                    width=40,
                    height=self._altura,
                    font=ctk.CTkFont(size=19, weight="bold"),
                    command=lambda valor=tecla: self._digitar(valor),
                )
                botao.grid(
                    row=linha_idx,
                    column=coluna_idx + deslocamento,
                    sticky="nsew",
                    padx=3,
                    pady=2,
                )

        controles = ctk.CTkFrame(self, fg_color="transparent")
        controles.grid(
            row=len(self.LINHAS),
            column=0,
            columnspan=colunas,
            sticky="ew",
            pady=(4, 2),
        )
        controles.grid_columnconfigure((0, 1), weight=1, uniform="controle")

        ctk.CTkButton(
            controles,
            text="⌫ Apagar",
            height=self._altura,
            command=self._apagar,
        ).grid(row=0, column=0, padx=3, sticky="ew")

        ctk.CTkButton(
            controles,
            text="Próximo ▶",
            height=self._altura,
            fg_color="#2E8B57",
            hover_color="#247447",
            command=self._proximo,
        ).grid(row=0, column=1, padx=3, sticky="ew")

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
        except tk.TclError:
            pass

    def _proximo(self) -> None:
        if self._ao_proximo is not None:
            self._ao_proximo()
