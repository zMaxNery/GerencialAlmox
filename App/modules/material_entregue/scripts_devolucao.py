from __future__ import annotations

from decimal import Decimal
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from modules._shared.almox_repository import AlmoxRepository

if TYPE_CHECKING:
    from modules.material_entregue.view_devolucao import JanelaDevolucao

class Scripts:
    def __init__(self, janDevolucao: JanelaDevolucao) -> None:
        self.janDevolucao = janDevolucao
        self.repository: AlmoxRepository | None = None
        self.all_rows: list[dict] = []

    def _adicionar_tecla(self, valor: str) -> None:
        atual = self.quantidade_var.get()

        if valor == ",":
            if "," in atual or "." in atual:
                return

            if not atual:
                atual = "0"

            self.quantidade_var.set(
                atual + ","
            )

            return

        novo_valor = atual + valor

        separador = (
            ","
            if "," in novo_valor
            else "."
            if "." in novo_valor
            else None
        )

        # O banco aceita até três casas decimais.
        if separador:
            decimais = novo_valor.split(
                separador,
                1,
            )[1]

            if len(decimais) > 3:
                return

        # Evita uma sequência desnecessária de zeros.
        if (
            novo_valor.startswith("00")
            and "," not in novo_valor
            and "." not in novo_valor
        ):
            novo_valor = novo_valor.lstrip("0") or "0"

        self.quantidade_var.set(
            novo_valor
        )

    def _apagar(self) -> None:
        atual = self.quantidade_var.get()

        self.quantidade_var.set(
            atual[:-1]
        )

    def _limpar(self) -> None:
        self.quantidade_var.set("")

    def _preencher_tudo(self) -> None:
        self.quantidade_var.set(
            self._fmt(
                self.quantidade_disponivel
            ).replace(".", ",")
        )

    def _confirmar(self) -> None:
        texto = (
            self.quantidade_var.get()
            .strip()
            .replace(",", ".")
        )

        try:
            quantidade = Decimal(texto)

            if quantidade <= 0:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            messagebox.showerror(
                "Devolução",
                "Informe uma quantidade maior que zero.",
                parent=self,
            )
            return

        if quantidade > self.quantidade_disponivel:
            messagebox.showerror(
                "Devolução",
                (
                    "A quantidade não pode ser maior que "
                    f"{self._fmt(self.quantidade_disponivel)}."
                ),
                parent=self,
            )
            return

        observacao = (
            self.observacao_entry
            .get("1.0", "end")
            .strip()
        )

        confirmado = messagebox.askyesno(
            "Confirmar devolução",
            (
                f"Devolver {self._fmt(quantidade)} do material "
                f"{self.row.get('material', '')}?"
            ),
            parent=self,
        )

        if not confirmado:
            return

        try:
            consumo_id = self.row.get("consumo_material_fabrica_id")
            if consumo_id:
                resultado = self.repository.devolver_material_lote_fabrica(
                    consumo_material_fabrica_id=int(consumo_id),
                    quantidade=quantidade,
                    nome_operador=getpass.getuser(),
                    observacao=observacao,
                )
            else:
                resultado = self.repository.devolver_material(
                    apontamento_entrega_id=int(
                        self.row["apontamento_entrega_id"]
                    ),
                    quantidade=quantidade,
                    nome_operador=getpass.getuser(),
                    observacao=observacao,
                )

        except Exception as exc:
            messagebox.showerror(
                "Devolução",
                str(exc),
                parent=self,
            )
            return

        messagebox.showinfo(
            "Devolução",
            (
                "Devolução registrada.\n"
                "Quantidade restante nesta entrega: "
                f"{self._fmt(
                    resultado.get(
                        'quantidade_entregue_restante'
                    )
                )}"
            ),
            parent=self,
        )

        self.grab_release()
        self.destroy()

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

        return (
            f"{numero:.3f}"
            .rstrip("0")
            .rstrip(".")
            or "0"
        )