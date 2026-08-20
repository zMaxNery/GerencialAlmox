from __future__ import annotations

import customtkinter as ctk


class TecladoVirtual(ctk.CTkToplevel):
    """Teclado virtual próprio da aplicação, sem chamar executáveis do Windows."""

    def __init__(self, widget) -> None:
        super().__init__(widget.winfo_toplevel())
        self.widget = widget
        self.maiusculas = True

        self.title("Teclado virtual")
        self.geometry("980x430")
        self.minsize(900, 390)
        self.resizable(True, False)
        self.transient(widget.winfo_toplevel())
        self.attributes("-topmost", True)

        self.grid_columnconfigure(0, weight=1)
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._fechar)

    def _widget_nativo(self):
        return (
            getattr(self.widget, "_entry", None)
            or getattr(self.widget, "_textbox", None)
            or self.widget
        )

    def _build(self) -> None:
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        ctk.CTkButton(
            topo,
            text="Fechar",
            width=100,
            height=38,
            fg_color="#C0392B",
            hover_color="#A93226",
            command=self._fechar,
        ).pack(side="right")

        corpo = ctk.CTkFrame(self)
        corpo.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

        linhas = [
            list("1234567890") + ["-", "."],
            list("QWERTYUIOP") + ["Ç"],
            list("ASDFGHJKL") + ["_"],
            list("ZXCVBNM") + ["@", "/"],
        ]
        max_colunas = max(len(linha) for linha in linhas)
        for coluna in range(max_colunas):
            corpo.grid_columnconfigure(coluna, weight=1)

        for linha_idx, teclas in enumerate(linhas):
            deslocamento = max((max_colunas - len(teclas)) // 2, 0)
            for coluna_idx, tecla in enumerate(teclas):
                ctk.CTkButton(
                    corpo,
                    text=tecla,
                    height=58,
                    font=ctk.CTkFont(size=20, weight="bold"),
                    command=lambda valor=tecla: self._digitar(valor),
                ).grid(
                    row=linha_idx,
                    column=coluna_idx + deslocamento,
                    sticky="nsew",
                    padx=4,
                    pady=4,
                )

        controles = ctk.CTkFrame(corpo, fg_color="transparent")
        controles.grid(
            row=len(linhas),
            column=0,
            columnspan=max_colunas,
            sticky="ew",
            padx=4,
            pady=(8, 4),
        )
        controles.grid_columnconfigure(2, weight=1)

        self.caixa_btn = ctk.CTkButton(
            controles,
            text="ABC",
            width=120,
            height=52,
            fg_color="#2F80ED",
            command=self._alternar_caixa,
        )
        self.caixa_btn.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            controles,
            text="⌫ Apagar",
            width=130,
            height=52,
            command=self._apagar,
        ).grid(row=0, column=1, padx=6, sticky="ew")

        ctk.CTkButton(
            controles,
            text="Espaço",
            height=52,
            font=ctk.CTkFont(size=18, weight="bold"),
            command=lambda: self._digitar(" "),
        ).grid(row=0, column=2, padx=6, sticky="ew")

        ctk.CTkButton(
            controles,
            text="Limpar",
            width=110,
            height=52,
            fg_color="#6C757D",
            hover_color="#5A6268",
            command=self._limpar,
        ).grid(row=0, column=3, padx=6, sticky="ew")

        ctk.CTkButton(
            controles,
            text="OK",
            width=110,
            height=52,
            fg_color="#2E8B57",
            hover_color="#247447",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self._fechar,
        ).grid(row=0, column=4, padx=(6, 0), sticky="ew")

    def _digitar(self, valor: str) -> None:
        if valor.isalpha():
            valor = valor.upper() if self.maiusculas else valor.lower()
        alvo = self._widget_nativo()
        try:
            alvo.insert("insert", valor)
            alvo.focus_set()
        except Exception:
            try:
                self.widget.insert("insert", valor)
                self.widget.focus_set()
            except Exception:
                pass

    def _apagar(self) -> None:
        alvo = self._widget_nativo()
        try:
            # Entry e Text suportam seleção através de tag/selection APIs diferentes.
            try:
                if alvo.selection_present():
                    alvo.delete("sel.first", "sel.last")
                    return
            except Exception:
                try:
                    ranges = alvo.tag_ranges("sel")
                    if ranges:
                        alvo.delete("sel.first", "sel.last")
                        return
                except Exception:
                    pass

            pos = alvo.index("insert")
            if isinstance(pos, int):
                if pos > 0:
                    alvo.delete(pos - 1, pos)
            else:
                alvo.delete(f"{pos}-1c", pos)
            alvo.focus_set()
        except Exception:
            pass

    def _limpar(self) -> None:
        alvo = self._widget_nativo()
        try:
            if hasattr(alvo, "get"):
                try:
                    alvo.delete("1.0", "end")
                except Exception:
                    alvo.delete(0, "end")
            alvo.focus_set()
        except Exception:
            pass

    def _alternar_caixa(self) -> None:
        self.maiusculas = not self.maiusculas
        self.caixa_btn.configure(
            text="ABC" if self.maiusculas else "abc",
            fg_color="#2F80ED" if self.maiusculas else ("#3B8ED0", "#1F6AA5"),
        )

    def _fechar(self) -> None:
        try:
            self.attributes("-topmost", False)
        except Exception:
            pass
        try:
            self.widget.focus_set()
        except Exception:
            pass
        self.destroy()


def abrir_teclado_virtual(widget=None) -> None:
    """Abre o teclado da própria aplicação para o campo informado."""
    if widget is None:
        return
    TecladoVirtual(widget)
