from __future__ import annotations

import getpass
from decimal import Decimal, InvalidOperation
from tkinter import messagebox

import customtkinter as ctk

from modules._shared.almox_repository import AlmoxRepository
from modules._shared.virtual_keyboard import abrir_teclado_virtual


class JanelaRequisicaoManual(ctk.CTkToplevel):
    def __init__(self, parent, repository: AlmoxRepository, on_success) -> None:
        super().__init__(parent)
        self.repository = repository
        self.on_success = on_success

        self.title("Nova requisição manual")
        self.geometry("760x670")
        self.minsize(700, 620)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.focus_force()
        self.grid_columnconfigure(0, weight=1)

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._fechar)

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(20, 10))
        ctk.CTkLabel(
            header,
            text="Nova requisição manual",
            font=ctk.CTkFont(size=23, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="A numeração RM será gerada automaticamente e a linha seguirá o fluxo normal até Baixas TOTVS.",
            justify="left",
            wraplength=680,
        ).pack(anchor="w", pady=(4, 0))

        form = ctk.CTkScrollableFrame(self)
        form.grid(row=1, column=0, sticky="nsew", padx=22, pady=(0, 12))
        self.grid_rowconfigure(1, weight=1)
        form.grid_columnconfigure(1, weight=1)

        self.entries: dict[str, ctk.CTkEntry] = {}
        campos = [
            ("material", "Material", "Código ou descrição"),
            ("dimensao", "Dimensão", "Opcional"),
            ("quantidade", "Quantidade", "Ex.: 10"),
            ("rastreabilidade", "Rastreabilidade", "Opcional"),
            ("localizacao_est", "Estoque", "Ex.: EST"),
            ("setor_dest", "Setor", "Opcional"),
            ("peso_bruto_kg", "Peso bruto (kg)", "Peso Perfil / Peso Chapa"),
            ("peso_liquido_kg", "Peso líquido (kg)", "Peso (KG) / Baixa TOTVS"),
        ]

        for linha, (chave, titulo, placeholder) in enumerate(campos):
            ctk.CTkLabel(form, text=f"{titulo}:").grid(
                row=linha, column=0, sticky="w", padx=(12, 8), pady=7
            )
            entry = ctk.CTkEntry(form, placeholder_text=placeholder)
            entry.grid(row=linha, column=1, sticky="ew", padx=(0, 6), pady=7)
            ctk.CTkButton(
                form,
                text="⌨",
                width=42,
                command=lambda e=entry: abrir_teclado_virtual(e),
            ).grid(row=linha, column=2, padx=(0, 12), pady=7)
            self.entries[chave] = entry

        self.entries["localizacao_est"].insert(0, "EST")

        operador = getpass.getuser()
        ctk.CTkLabel(form, text="Operador:").grid(
            row=len(campos), column=0, sticky="w", padx=(12, 8), pady=7
        )
        ctk.CTkLabel(
            form,
            text=operador,
            anchor="w",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=len(campos), column=1, columnspan=2, sticky="ew", padx=(0, 12), pady=7)

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.grid(row=2, column=0, sticky="ew", padx=22, pady=(0, 20))
        ctk.CTkButton(
            botoes,
            text="Cadastrar requisição",
            height=44,
            command=self._confirmar,
        ).pack(side="right")
        ctk.CTkButton(
            botoes,
            text="Cancelar",
            height=44,
            fg_color="#555555",
            hover_color="#444444",
            command=self._fechar,
        ).pack(side="right", padx=(0, 10))

    def _decimal(self, chave: str, obrigatorio: bool = False) -> Decimal | None:
        texto = self.entries[chave].get().strip().replace(",", ".")
        if not texto:
            if obrigatorio:
                raise ValueError(f"Informe {chave.replace('_', ' ')}.")
            return None
        try:
            valor = Decimal(texto)
        except InvalidOperation as exc:
            raise ValueError(f"Valor inválido em {chave.replace('_', ' ')}.") from exc
        if valor < 0 or (obrigatorio and valor <= 0):
            raise ValueError(f"Valor inválido em {chave.replace('_', ' ')}.")
        return valor

    def _confirmar(self) -> None:
        material = self.entries["material"].get().strip()
        if not material:
            messagebox.showerror("Requisição manual", "Informe o material.", parent=self)
            return
        try:
            quantidade = self._decimal("quantidade", obrigatorio=True)
            peso_bruto = self._decimal("peso_bruto_kg")
            peso_liquido = self._decimal("peso_liquido_kg")
        except ValueError as exc:
            messagebox.showerror("Requisição manual", str(exc), parent=self)
            return

        try:
            resultado = self.repository.incluir_requisicao_manual(
                material=material,
                quantidade=quantidade,
                nome_operador=getpass.getuser(),
                dimensao=self.entries["dimensao"].get().strip() or None,
                rastreabilidade=self.entries["rastreabilidade"].get().strip() or None,
                localizacao_est=self.entries["localizacao_est"].get().strip() or "EST",
                setor_dest=self.entries["setor_dest"].get().strip() or None,
                peso_bruto_kg=peso_bruto,
                peso_liquido_kg=peso_liquido,
            )
        except Exception as exc:
            messagebox.showerror("Requisição manual", str(exc), parent=self)
            return

        numero = resultado.get("numero_requisicao") or "RM"
        messagebox.showinfo(
            "Requisição manual",
            f"Requisição {numero} cadastrada com sucesso.",
            parent=self,
        )
        self._fechar()
        self.on_success()

    def _fechar(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
