from __future__ import annotations

from decimal import Decimal, InvalidOperation
from tkinter import messagebox

import customtkinter as ctk

from modules._shared.almox_repository import AlmoxRepository


class JanelaUsoMaterialFabrica(ctk.CTkToplevel):
    """Permite selecionar explicitamente os lotes/rastreabilidades consumidos."""

    def __init__(
        self,
        parent,
        repository: AlmoxRepository,
        item: dict,
        consulta: dict,
        quantidade_informada: Decimal,
        nome_operador: str,
        on_success,
        observacao: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.repository = repository
        self.item = item
        self.consulta = consulta
        self.quantidade_informada = Decimal(str(quantidade_informada))
        self.nome_operador = nome_operador
        self.observacao = observacao
        self.on_success = on_success
        self.lote_vars: dict[int, ctk.StringVar] = {}
        self.lotes = list(consulta.get("lotes") or [])

        self.title("Usar material em fábrica")
        self.geometry("820x650")
        self.minsize(760, 590)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.focus_force()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._fechar)

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 8))
        ctk.CTkLabel(
            header,
            text="Compensar com material em fábrica?",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text=(
                f"Material: {self.item.get('material') or ''}   |   "
                f"Rastreabilidade da requisição: {self.item.get('rastreabilidade') or '-'}\n"
                f"Entrega informada: {self._fmt(self.quantidade_informada)}   |   "
                f"Total em fábrica deste material: {self._fmt(self.consulta.get('quantidade_disponivel'))}"
            ),
            justify="left",
        ).pack(anchor="w", pady=(5, 0))

        corpo = ctk.CTkScrollableFrame(self)
        corpo.grid(row=1, column=0, sticky="nsew", padx=20, pady=8)
        corpo.grid_columnconfigure(1, weight=1)

        titulos = ("Rastreabilidade", "Disponível", "Usar")
        for col, titulo in enumerate(titulos):
            ctk.CTkLabel(
                corpo,
                text=titulo,
                font=ctk.CTkFont(weight="bold"),
            ).grid(row=0, column=col, sticky="ew", padx=8, pady=(4, 8))

        for linha, lote in enumerate(self.lotes, start=1):
            lote_id = int(lote["lote_id"])
            var = ctk.StringVar(value="")
            self.lote_vars[lote_id] = var
            ctk.CTkLabel(
                corpo,
                text=str(lote.get("rastreabilidade") or "SEM RASTREABILIDADE"),
                anchor="w",
            ).grid(row=linha, column=0, sticky="ew", padx=8, pady=5)
            ctk.CTkLabel(
                corpo,
                text=self._fmt(lote.get("quantidade_disponivel")),
            ).grid(row=linha, column=1, sticky="ew", padx=8, pady=5)
            ctk.CTkEntry(
                corpo,
                textvariable=var,
                width=130,
                justify="right",
            ).grid(row=linha, column=2, sticky="e", padx=8, pady=5)

        rodape = ctk.CTkFrame(self)
        rodape.grid(row=2, column=0, sticky="ew", padx=20, pady=(8, 20))
        rodape.grid_columnconfigure(0, weight=1)

        self.resumo_label = ctk.CTkLabel(rodape, text="", justify="left", anchor="w")
        self.resumo_label.grid(row=0, column=0, columnspan=4, sticky="ew", padx=10, pady=(10, 4))

        ctk.CTkButton(
            rodape,
            text="Usar máximo possível",
            command=self._preencher_maximo,
        ).grid(row=1, column=0, padx=8, pady=8, sticky="ew")
        ctk.CTkButton(
            rodape,
            text="Limpar seleção",
            command=self._limpar,
        ).grid(row=1, column=1, padx=8, pady=8, sticky="ew")
        ctk.CTkButton(
            rodape,
            text="Somente estoque",
            command=self._somente_estoque,
        ).grid(row=1, column=2, padx=8, pady=8, sticky="ew")
        ctk.CTkButton(
            rodape,
            text="Confirmar",
            command=self._confirmar,
        ).grid(row=1, column=3, padx=8, pady=8, sticky="ew")

        for var in self.lote_vars.values():
            var.trace_add("write", lambda *_: self._atualizar_resumo())
        self._atualizar_resumo()

    def _selecionados(self) -> list[dict]:
        selecionados: list[dict] = []
        lotes_por_id = {int(l["lote_id"]): l for l in self.lotes}
        for lote_id, var in self.lote_vars.items():
            texto = var.get().strip().replace(",", ".")
            if not texto:
                continue
            try:
                quantidade = Decimal(texto)
            except InvalidOperation as exc:
                raise ValueError("Há uma quantidade inválida na seleção da fábrica.") from exc
            if quantidade < 0:
                raise ValueError("A quantidade selecionada não pode ser negativa.")
            if quantidade == 0:
                continue
            disponivel = Decimal(str(lotes_por_id[lote_id].get("quantidade_disponivel") or 0))
            if quantidade > disponivel:
                raise ValueError(
                    f"O lote {lotes_por_id[lote_id].get('rastreabilidade') or lote_id} possui somente "
                    f"{self._fmt(disponivel)} disponível."
                )
            selecionados.append({"lote_id": lote_id, "quantidade": float(quantidade)})
        return selecionados

    def _total_selecionado(self) -> Decimal:
        try:
            return sum(
                (Decimal(str(item["quantidade"])) for item in self._selecionados()),
                Decimal("0"),
            )
        except ValueError:
            return Decimal("0")

    def _atualizar_resumo(self) -> None:
        total = self._total_selecionado()
        complemento = max(self.quantidade_informada - total, Decimal("0"))
        self.resumo_label.configure(
            text=(
                f"Fábrica selecionada: {self._fmt(total)}   |   "
                f"Complemento do estoque: {self._fmt(complemento)}"
            )
        )

    def _preencher_maximo(self) -> None:
        restante = self.quantidade_informada
        for lote in self.lotes:
            lote_id = int(lote["lote_id"])
            disponivel = Decimal(str(lote.get("quantidade_disponivel") or 0))
            usar = min(disponivel, restante)
            self.lote_vars[lote_id].set(self._fmt(usar).replace(".", ",") if usar > 0 else "")
            restante -= usar
            if restante <= 0:
                restante = Decimal("0")
        self._atualizar_resumo()

    def _limpar(self) -> None:
        for var in self.lote_vars.values():
            var.set("")
        self._atualizar_resumo()

    def _confirmar(self) -> None:
        try:
            lotes = self._selecionados()
        except ValueError as exc:
            messagebox.showerror("Entrega de MP", str(exc), parent=self)
            return

        if not lotes:
            self._somente_estoque()
            return

        total_fabrica = sum(
            (Decimal(str(item["quantidade"])) for item in lotes), Decimal("0")
        )
        if total_fabrica > self.quantidade_informada:
            messagebox.showerror(
                "Entrega de MP",
                "O total selecionado na fábrica não pode ser maior que a quantidade da entrega.",
                parent=self,
            )
            return

        restante_req = Decimal(str(self.consulta.get("quantidade_restante_requisicao") or 0))
        if self.quantidade_informada > restante_req:
            messagebox.showerror(
                "Entrega de MP",
                (
                    "Para usar saldo de fábrica, a quantidade informada deve ser no máximo o restante "
                    "da requisição. Para uma entrega com excedente, use 'Somente estoque'."
                ),
                parent=self,
            )
            return

        try:
            resultado = self.repository.registrar_entrega_com_fabrica(
                item_requisicao_id=int(self.item["item_requisicao_id"]),
                quantidade_total=self.quantidade_informada,
                lotes=lotes,
                nome_operador=self.nome_operador,
                observacao=self.observacao,
            )
        except Exception as exc:
            messagebox.showerror("Entrega de MP", str(exc), parent=self)
            return

        messagebox.showinfo(
            "Entrega de MP",
            (
                "Entrega registrada.\n"
                f"Fábrica: {self._fmt(resultado.get('quantidade_fabrica'))}\n"
                f"Estoque: {self._fmt(resultado.get('quantidade_nova'))}\n"
                f"Restante: {self._fmt(resultado.get('quantidade_restante'))}"
            ),
            parent=self,
        )
        self._fechar()
        self.on_success()

    def _somente_estoque(self) -> None:
        try:
            resultado = self.repository.registrar_entrega(
                item_requisicao_id=int(self.item["item_requisicao_id"]),
                quantidade=self.quantidade_informada,
                nome_operador=self.nome_operador,
                observacao=self.observacao,
            )
        except Exception as exc:
            messagebox.showerror("Entrega de MP", str(exc), parent=self)
            return
        messagebox.showinfo(
            "Entrega de MP",
            (
                "Entrega registrada somente pelo estoque.\n"
                f"Aplicado: {self._fmt(resultado.get('quantidade_aplicada'))}\n"
                f"Excedente: {self._fmt(resultado.get('quantidade_excedente'))}"
            ),
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

    @staticmethod
    def _fmt(value) -> str:
        if value in (None, ""):
            return "0"
        numero = Decimal(str(value))
        return f"{numero:.3f}".rstrip("0").rstrip(".") or "0"
