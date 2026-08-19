from __future__ import annotations

import getpass
from decimal import Decimal, InvalidOperation
from tkinter import messagebox

import customtkinter as ctk

from modules._shared.almox_repository import AlmoxRepository
from modules._shared.virtual_keyboard import abrir_teclado_virtual


class JanelaInclusaoManualFabrica(ctk.CTkToplevel):
    def __init__(self, parent, repository: AlmoxRepository, on_success) -> None:
        super().__init__(parent)
        self.repository = repository
        self.on_success = on_success

        self.title("Incluir material em fábrica")
        self.geometry("700x540")
        self.minsize(650, 500)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.focus_force()
        self.grid_columnconfigure(0, weight=1)
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._fechar)

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 8))
        ctk.CTkLabel(
            header,
            text="Incluir material no estoque de fábrica",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="O lote será marcado como origem MANUAL e ficará disponível para compensar requisições do mesmo material.",
            wraplength=640,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="nsew", padx=20, pady=8)
        form.grid_columnconfigure(1, weight=1)

        self.material_entry = self._campo(form, 0, "Material:", "Código ou descrição")
        self.rastreabilidade_entry = self._campo(form, 1, "Rastreabilidade:", "Informe a rastreabilidade do lote")
        self.quantidade_entry = self._campo(form, 2, "Quantidade:", "Ex.: 12")

        ctk.CTkLabel(form, text="Observação:").grid(row=3, column=0, sticky="nw", padx=(12, 8), pady=8)
        self.observacao_entry = ctk.CTkTextbox(form, height=100)
        self.observacao_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=8)

        ctk.CTkLabel(form, text="Operador:").grid(row=4, column=0, sticky="w", padx=(12, 8), pady=8)
        ctk.CTkLabel(form, text=getpass.getuser(), anchor="w", font=ctk.CTkFont(weight="bold")).grid(
            row=4, column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=8
        )

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.grid(row=2, column=0, sticky="ew", padx=20, pady=(8, 18))
        ctk.CTkButton(botoes, text="Incluir material", height=44, command=self._confirmar).pack(side="right")
        ctk.CTkButton(
            botoes,
            text="Cancelar",
            height=44,
            fg_color="#555555",
            hover_color="#444444",
            command=self._fechar,
        ).pack(side="right", padx=(0, 10))

    def _campo(self, parent, row: int, label: str, placeholder: str) -> ctk.CTkEntry:
        ctk.CTkLabel(parent, text=label).grid(row=row, column=0, sticky="w", padx=(12, 8), pady=8)
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder)
        entry.grid(row=row, column=1, sticky="ew", padx=(0, 6), pady=8)
        ctk.CTkButton(parent, text="⌨", width=42, command=lambda: abrir_teclado_virtual(entry)).grid(
            row=row, column=2, padx=(0, 12), pady=8
        )
        return entry

    def _confirmar(self) -> None:
        material = self.material_entry.get().strip()
        rastreabilidade = self.rastreabilidade_entry.get().strip()
        if not material:
            messagebox.showerror("Materiais em fábrica", "Informe o material.", parent=self)
            return
        if not rastreabilidade:
            messagebox.showerror("Materiais em fábrica", "Informe a rastreabilidade.", parent=self)
            return
        try:
            quantidade = Decimal(self.quantidade_entry.get().strip().replace(",", "."))
            if quantidade <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            messagebox.showerror("Materiais em fábrica", "Informe uma quantidade maior que zero.", parent=self)
            return

        try:
            self.repository.incluir_material_fabrica_manual(
                material=material,
                rastreabilidade=rastreabilidade,
                quantidade=quantidade,
                nome_operador=getpass.getuser(),
                observacao=self.observacao_entry.get("1.0", "end").strip() or None,
            )
        except Exception as exc:
            messagebox.showerror("Materiais em fábrica", str(exc), parent=self)
            return

        messagebox.showinfo("Materiais em fábrica", "Material incluído com sucesso.", parent=self)
        self._fechar()
        self.on_success()

    def _fechar(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
