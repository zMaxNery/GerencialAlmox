from __future__ import annotations

import tkinter as tk
from typing import Callable

import customtkinter as ctk


class TecladoFixo(ctk.CTkFrame):
    """Teclado virtual fixo, embutido na própria tela.

    Diferente do ``TecladoVirtual`` (que abre numa janela separada), este
    teclado fica sempre visível e digita no campo definido por
    ``definir_alvo``. Use ``registrar_campo`` para que o alvo acompanhe
    automaticamente o campo que recebeu o foco.
    """

    LINHAS = (
        list("1234567890") + ["-"],
        list("QWERTYUIOP") + ["Ç"],
        list("ASDFGHJKL") + ["/", '"'],
        list("ZXCVBNM") + [",", ".", "_", "+"],
    )

    def __init__(
        self,
        parent,
        ao_proximo: Callable[[], None] | None = None,
        altura_tecla: int = 46,
    ) -> None:
        super().__init__(parent)

        self._alvo = None
        self._maiusculas = True
        self._ao_proximo = ao_proximo
        self._altura = altura_tecla
        self._teclas_letras: list[tuple[ctk.CTkButton, str]] = []

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
                    column=coluna_idx,
                    sticky="nsew",
                    padx=3,
                    pady=2,
                )
                if tecla.isalpha():
                    self._teclas_letras.append((botao, tecla))

        controles = ctk.CTkFrame(self, fg_color="transparent")
        controles.grid(
            row=len(self.LINHAS),
            column=0,
            columnspan=colunas,
            sticky="ew",
            pady=(4, 2),
        )
        controles.grid_columnconfigure(1, weight=1)

        self.caixa_btn = ctk.CTkButton(
            controles,
            text="ABC",
            width=100,
            height=self._altura,
            fg_color="#2F80ED",
            command=self._alternar_caixa,
        )
        self.caixa_btn.grid(row=0, column=0, padx=3, sticky="ew")

        ctk.CTkButton(
            controles,
            text="Espaço",
            height=self._altura,
            font=ctk.CTkFont(size=18, weight="bold"),
            command=lambda: self._digitar(" "),
        ).grid(row=0, column=1, padx=3, sticky="ew")

        ctk.CTkButton(
            controles,
            text="⌫ Apagar",
            width=130,
            height=self._altura,
            command=self._apagar,
        ).grid(row=0, column=2, padx=3, sticky="ew")

        ctk.CTkButton(
            controles,
            text="Próximo ▶",
            width=130,
            height=self._altura,
            fg_color="#2E8B57",
            hover_color="#247447",
            command=self._proximo,
        ).grid(row=0, column=3, padx=3, sticky="ew")

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

        if valor.isalpha():
            valor = valor.upper() if self._maiusculas else valor.lower()

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

    def _alternar_caixa(self) -> None:
        self._maiusculas = not self._maiusculas
        self.caixa_btn.configure(
            text="ABC" if self._maiusculas else "abc",
            fg_color="#2F80ED" if self._maiusculas else ("#3B8ED0", "#1F6AA5"),
        )
        for botao, letra in self._teclas_letras:
            botao.configure(text=letra if self._maiusculas else letra.lower())

    def _proximo(self) -> None:
        if self._ao_proximo is not None:
            self._ao_proximo()
