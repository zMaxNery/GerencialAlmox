from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from modules._shared.almox_repository import AlmoxRepository
from modules._shared.search_utils import corresponde_pesquisa
from modules._shared.virtual_keyboard import abrir_teclado_virtual

if TYPE_CHECKING:
    from modules.devolucoes_entrega.view import HistoricoDevolucoesView


class Scripts:
    def __init__(self, histDevolucao: HistoricoDevolucoesView) -> None:
        self.histDevolucao = histDevolucao
        self.repository: AlmoxRepository | None = None
        self.all_rows: list[dict] = []

    def refresh(self) -> None:
        try:
            if self.repository is None:
                self.repository = AlmoxRepository()

            self.all_rows = self.repository.listar_historico_devolucoes()
        except Exception as exc:
            messagebox.showerror("Histórico de devoluções", str(exc))
            return

        self._update_filter_options()
        self._apply_filters()

    def _update_filter_options(self) -> None:
        setores = self._unique_values("setor_dest")
        estoques = self._unique_values("localizacao_est")
        datas = sorted(
            {
                self._fmt_data(row.get("devolvido_em"))
                for row in self.all_rows
                if row.get("devolvido_em")
            },
            reverse=True,
        )

        self._set_option_values(
            self.histDevolucao.setor_filter,
            ["TODOS", *setores],
            "TODOS",
        )
        self._set_option_values(
            self.histDevolucao.estoque_filter,
            ["TODOS", *estoques],
            "TODOS",
        )
        self._set_option_values(
            self.histDevolucao.data_filter,
            ["TODAS", *datas],
            "TODAS",
        )

    def _apply_filters(self) -> None:
        setor = self.histDevolucao.setor_filter.get().strip()
        data = self.histDevolucao.data_filter.get().strip()
        estoque = self.histDevolucao.estoque_filter.get().strip()
        pesquisa = self.histDevolucao.pesquisa_filter.get().strip()

        campos = (
            "numero_requisicao",
            "tipo_evento",
            "material",
            "dimensao",
            "rastreabilidade",
            "localizacao_est",
            "setor_dest",
            "operador_devolucao",
            "operador_entrega",
            "observacao_devolucao",
            "devolvido_em",
            "data_requisicao",
        )

        rows: list[dict] = []
        for row in self.all_rows:
            if setor != "TODOS" and str(row.get("setor_dest") or "") != setor:
                continue
            if (
                data != "TODAS"
                and self._fmt_data(row.get("devolvido_em")) != data
            ):
                continue
            if (
                estoque != "TODOS"
                and str(row.get("localizacao_est") or "") != estoque
            ):
                continue
            if not corresponde_pesquisa(row, pesquisa, campos):
                continue
            rows.append(row)

        self._fill_table(rows)
        self.histDevolucao.counter_label.configure(
            text=f"{len(rows)} registro(s)"
        )

    def _fill_table(self, data: list[dict]) -> None:
        for item_id in self.histDevolucao.tree.get_children():
            self.histDevolucao.tree.delete(item_id)

        for indice, row in enumerate(data):
            tipo_evento = str(row.get("tipo_evento") or "DEVOLUCAO").upper()
            eh_exclusao = tipo_evento == "EXCLUSAO"

            if eh_exclusao:
                tag = "exclusao_par" if indice % 2 == 0 else "exclusao_impar"
            else:
                tag = "linha_par" if indice % 2 == 0 else "linha_impar"

            # Prefixar o iid pelo tipo de evento evita qualquer colisão entre
            # IDs de devolução e IDs de exclusão.
            registro_id = row.get("devolucao_id")
            iid = f"{tipo_evento}:{registro_id}"

            quantidade_referencia = (
                ""
                if eh_exclusao
                else self._fmt(row.get("quantidade_entregue_original"))
            )
            quantidade_devolvida = (
                ""
                if eh_exclusao
                else self._fmt(row.get("quantidade_devolvida"))
            )

            self.histDevolucao.tree.insert(
                "",
                "end",
                iid=iid,
                values=(
                    self._fmt_data_hora(row.get("devolvido_em")),
                    self._fmt_request_datetime(row),
                    row.get("material") or "",
                    row.get("dimensao") or "",
                    quantidade_referencia,
                    quantidade_devolvida,
                    row.get("rastreabilidade") or "",
                    row.get("localizacao_est") or "",
                    row.get("setor_dest") or "",
                    row.get("operador_devolucao") or "",
                    row.get("observacao_devolucao") or "",
                ),
                tags=(tag,),
            )

    def _clear_filters(self) -> None:
        self.histDevolucao.setor_filter.set("TODOS")
        self.histDevolucao.data_filter.set("TODAS")
        self.histDevolucao.estoque_filter.set("TODOS")
        self.histDevolucao.pesquisa_filter.delete(0, "end")
        self._apply_filters()

    def abrir_teclado_pesquisa(self) -> None:
        abrir_teclado_virtual(self.histDevolucao.pesquisa_filter)

    def _unique_values(self, field: str) -> list[str]:
        return sorted(
            {
                str(row.get(field)).strip()
                for row in self.all_rows
                if row.get(field) not in (None, "")
            },
            key=str.lower,
        )

    @staticmethod
    def _set_option_values(
        option_menu: ctk.CTkOptionMenu,
        values: list[str],
        default: str,
    ) -> None:
        atual = option_menu.get()
        option_menu.configure(values=values)
        if atual not in values:
            option_menu.set(default)

    @staticmethod
    def _converter_data_hora(value) -> datetime | None:
        if value in (None, ""):
            return None

        texto = str(value).strip().replace("Z", "+00:00")
        try:
            data_hora = datetime.fromisoformat(texto)
        except ValueError:
            try:
                return datetime.strptime(texto[:10], "%Y-%m-%d")
            except ValueError:
                return None

        if data_hora.tzinfo is not None:
            data_hora = data_hora.astimezone()

        return data_hora

    @classmethod
    def _fmt_data_hora(cls, value) -> str:
        data_hora = cls._converter_data_hora(value)
        return data_hora.strftime("%d/%m/%Y %H:%M") if data_hora else ""

    @classmethod
    def _fmt_request_datetime(cls, row: dict) -> str:
        data = cls._fmt_data(row.get("data_requisicao"))
        hora = cls._fmt_hora(row.get("recebido_em_email"))

        if data and hora:
            return f"{data} {hora}"
        if data:
            return data
        return cls._fmt_data_hora(row.get("recebido_em_email"))

    @classmethod
    def _fmt_data(cls, value) -> str:
        data_hora = cls._converter_data_hora(value)
        return data_hora.strftime("%d/%m/%Y") if data_hora else ""

    @classmethod
    def _fmt_hora(cls, value) -> str:
        data_hora = cls._converter_data_hora(value)
        return data_hora.strftime("%H:%M") if data_hora else ""

    @staticmethod
    def _fmt(value) -> str:
        if value in (None, ""):
            return "0"

        number = Decimal(str(value))
        return f"{number:.3f}".rstrip("0").rstrip(".") or "0"
