from __future__ import annotations

import getpass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from modules._shared.almox_repository import AlmoxRepository
from modules._shared.search_utils import corresponde_pesquisa
from modules._shared.virtual_keyboard import abrir_teclado_virtual
from modules.entregas_est.fabrica_dialog import JanelaUsoMaterialFabrica
from modules.entregas_est.manual_dialog import JanelaRequisicaoManual

if TYPE_CHECKING:
    from modules.entregas_est.view import View

class Scripts:
    def __init__(self, view: View) -> None:
        self.view = view
        self.repository: AlmoxRepository | None = None
        self.all_rows: list[dict] = []

    def refresh(self) -> None:
        try:
            if self.repository is None:
                self.repository = AlmoxRepository()

            self.all_rows = self.repository.listar_pendencias_est()
            self.view.saldos_fabrica.clear()

        except Exception as exc:
            messagebox.showerror("Requisições", str(exc))
            return

        self._update_filter_options()
        self._apply_filters()

    def _update_filter_options(self) -> None:
        setores = self._unique_values("setor_dest")
        estoques = self._unique_values("localizacao_est")
        datas = sorted(
            {
                self._fmt_date(row.get("data_requisicao"))
                for row in self.all_rows
                if row.get("data_requisicao")
            },
            reverse=True,
        )

        self._set_option_values(
            self.view.setor_filter,
            ["TODOS", *setores],
            "TODOS",
        )
        self._set_option_values(
            self.view.estoque_filter,
            ["TODOS", *estoques],
            "TODOS",
        )
        self._set_option_values(
            self.view.data_filter,
            ["TODAS", *datas],
            "TODAS",
        )

    def _apply_filters(self) -> None:
        setor=self.view.setor_filter.get().strip()
        data=self.view.data_filter.get().strip()
        estoque=self.view.estoque_filter.get().strip()
        pesquisa=self.view.pesquisa_filter.get().strip()
        campos=("numero_requisicao","nome_arquivo_email","material","dimensao",
                "rastreabilidade","setor_dest","localizacao_est","data_requisicao")
        filtered=[]
        for row in self.all_rows:
            if setor!="TODOS" and str(row.get("setor_dest") or "")!=setor: continue
            if data!="TODAS" and self._fmt_date(row.get("data_requisicao"))!=data: continue
            if estoque!="TODOS" and str(row.get("localizacao_est") or "")!=estoque: continue
            if not corresponde_pesquisa(row,pesquisa,campos): continue
            filtered.append(row)
        self._fill_table(filtered)
        self.view.counter_label.configure(text=f"{len(filtered)} item(ns)")
    def _fill_table(self, data: list[dict]) -> None:
        selected_before = self.view.tree.selection()
        selected_id = selected_before[0] if selected_before else None

        self.view.rows.clear()

        for item_id in self.view.tree.get_children():
            self.view.tree.delete(item_id)

        for indice, row in enumerate(data):
            key = str(row["item_requisicao_id"])
            self.view.rows[key] = row
            numero_requisicao = self._numero_requisicao(row)

            manual = numero_requisicao.upper().startswith("RM")
            if manual:
                tag_linha = "manual_par" if indice % 2 == 0 else "manual_impar"
            else:
                tag_linha = "linha_par" if indice % 2 == 0 else "linha_impar"
                
            self.view.tree.insert(
                "",
                "end",
                iid=key,
                values=(
                    self._fmt_request_datetime(row),
                    row.get("material") or "",
                    row.get("dimensao") or "",
                    self._fmt(row.get("quantidade_solicitada")),
                    self._fmt(row.get("quantidade_entregue")),
                    self._fmt(row.get("quantidade_restante")),
                    row.get("rastreabilidade") or "",
                    row.get("setor_dest") or "",
                    row.get("localizacao_est") or "",
                ),
                tags=(tag_linha,),
            )

        if selected_id and self.view.tree.exists(selected_id):
            self.view.tree.selection_set(selected_id)
            self.view.tree.focus(selected_id)
            self.view.tree.see(selected_id)
            self._on_select()

        # elif not data:
        #     self.view.selected_label.configure(text="Nenhum item encontrado")
        #     self.view.fabrica_label.grid_remove()
        #     self.view.quantidade_var.set("")

    def _on_select(self, _event=None) -> None:
        selected = self.view.tree.selection()
        if not selected:
            return

        row = self.view.rows.get(selected[0])
        if row is None:
            return

        # self.view.selected_label.configure(
        #     text=(
        #         f"{row.get('material', '')} | {row.get('rastreabilidade', '')}\n"
        #         f"Falta entregar: {self._fmt(row.get('quantidade_restante'))}"
        #     )
        # )
        self.view.quantidade_var.set("")
        self._atualizar_saldo_fabrica(row)

    def _atualizar_saldo_fabrica(self, row: dict) -> None:
        try:
            consulta = self._consultar_material_fabrica(row, forcar=False)
            disponivel = Decimal(
                str(consulta.get("quantidade_disponivel") or 0)
            )
        except Exception:
            self.view.fabrica_label.grid_remove()
            return

        if disponivel > 0:
            self.view.fabrica_label.configure(
                text=f"Em fábrica: {self._fmt(disponivel)} peça(s)"
            )
            self.view.fabrica_label.grid()
        else:
            self.view.fabrica_label.grid_remove()

    def _consultar_material_fabrica(
        self,
        row: dict,
        forcar: bool,
    ) -> dict:
        if self.repository is None:
            self.repository = AlmoxRepository()

        item_id = int(row["item_requisicao_id"])

        if not forcar and item_id in self.view.saldos_fabrica:
            return self.view.saldos_fabrica[item_id]

        consulta = self.repository.consultar_material_fabrica(
            item_requisicao_id=item_id,
        )
        self.view.saldos_fabrica[item_id] = consulta
        return consulta

    def _keypad_add(self, value: str) -> None:
        atual = self.view.quantidade_var.get()

        if value == ",":
            if "," in atual or "." in atual:
                return

            self.view.quantidade_var.set((atual or "0") + ",")
            return

        novo = f"{atual}{value}"

        if "," in novo:
            casas_decimais = len(novo.split(",", 1)[1])
            if casas_decimais > 3:
                return

        if novo.startswith("0") and "," not in novo:
            novo = novo.lstrip("0") or "0"

        self.view.quantidade_var.set(novo)

    def _keypad_backspace(self) -> None:
        self.view.quantidade_var.set(self.view.quantidade_var.get()[:-1])

    def _keypad_clear(self) -> None:
        self.view.quantidade_var.set("")

    def _keypad_fill_remaining(self) -> None:
        selected = self.view.tree.selection()
        if not selected:
            messagebox.showinfo(
                "Entrega de MP",
                "Selecione um item da lista.",
            )
            return

        row = self.view.rows.get(selected[0])
        if row is None:
            return

        self.view.quantidade_var.set(
            self._fmt(row.get("quantidade_restante")).replace(".", ",")
        )

    def _clear_filters(self) -> None:
        self.view.setor_filter.set("TODOS")
        self.view.data_filter.set("TODAS")
        self.view.estoque_filter.set("TODOS")
        self.view.pesquisa_filter.delete(0,"end")
        self._apply_filters()
    def abrir_teclado_pesquisa(self) -> None:
        abrir_teclado_virtual(self.view.pesquisa_filter)
    def abrir_requisicao_manual(self) -> None:
        if self.repository is None:
            self.repository=AlmoxRepository()
        JanelaRequisicaoManual(parent=self.view,repository=self.repository,on_success=self.refresh)
    def register_delivery(self) -> None:
        selected = self.view.tree.selection()
        if not selected:
            messagebox.showinfo(
                "Entrega de MP",
                "Selecione um item da lista.",
            )
            return

        usuario = getpass.getuser()
        # if not usuario:
        #     messagebox.showinfo(
        #         "Entrega de MP",
        #         "Informe o nome do operador.",
        #     )
        #     return

        quantidade = self._ler_quantidade_principal()
        if quantidade is None:
            return

        row = self.view.rows.get(selected[0])
        if row is None:
            messagebox.showerror(
                "Entrega de MP",
                "O item selecionado não está mais disponível.",
            )
            self.refresh()
            return

        if self.repository is None:
            self.repository = AlmoxRepository()

        try:
            consulta = self._consultar_material_fabrica(row, forcar=True)
        except Exception as exc:
            messagebox.showerror(
                "Entrega de MP",
                (
                    "Não foi possível verificar o saldo em fábrica.\n\n"
                    f"{exc}"
                ),
            )
            return

        disponivel = Decimal(str(consulta.get("quantidade_disponivel") or 0))

        if disponivel > 0:
            JanelaUsoMaterialFabrica(
                parent=self.view,
                repository=self.repository,
                item=row,
                consulta=consulta,
                quantidade_informada=quantidade,
                nome_operador=usuario,
                # observacao=self.view.note_entry.get().strip() or None,
                on_success=self._apos_registro,
            )
            return

        self._registrar_entrega_direta(
            row=row,
            quantidade=quantidade,
            usuario=usuario,
        )

    def _registrar_entrega_direta(
        self,
        row: dict,
        quantidade: Decimal,
        usuario: str,
    ) -> None:
        try:
            result = self.repository.registrar_entrega(
                item_requisicao_id=int(row["item_requisicao_id"]),
                quantidade=quantidade,
                nome_operador=usuario,
                # observacao=self.view.note_entry.get().strip() or None,
            )
        except Exception as exc:
            messagebox.showerror("Entrega de MP", str(exc))
            self.refresh()
            return

        messagebox.showinfo(
            "Entrega de MP",
            (
                "Entrega registrada.\n"
                f"Quantidade aplicada: "
                f"{self._fmt(result.get('quantidade_aplicada'))}\n"
                f"Excedente criado: "
                f"{self._fmt(result.get('quantidade_excedente'))}\n"
                f"Quantidade restante: "
                f"{self._fmt(result.get('quantidade_restante'))}"
            ),
        )

        self._apos_registro()

    def _apos_registro(self) -> None:
        self.view.quantidade_var.set("")
        # self.view.note_entry.delete(0, "end")
        self.view.fabrica_label.grid_remove()
        self.refresh()

    def _ler_quantidade_principal(self) -> Decimal | None:
        texto_quantidade = self.view.quantidade_var.get().strip().replace(",", ".")

        try:
            quantidade = Decimal(texto_quantidade)
            if quantidade <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            messagebox.showerror(
                "Entrega de MP",
                "Digite uma quantidade maior que zero.",
            )
            return None

        return quantidade

    @staticmethod
    def _numero_requisicao(row: dict) -> str:
        numero=str(row.get("numero_requisicao") or "").strip()
        if numero: return numero
        nome=str(row.get("nome_arquivo_email") or "").strip()
        return nome if nome.upper().startswith("RM") else ""
    def _rolar_horizontal(self, event) -> str:
        direcao = -1 if event.delta > 0 else 1
        self.view.tree.xview_scroll(direcao, "units")
        return "break"

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

    @classmethod
    def _fmt_request_datetime(cls, row: dict) -> str:
        data = cls._fmt_date(row.get("data_requisicao"))
        hora = cls._fmt_hora(row.get("recebido_em_email"))

        if data and hora:
            return f"{data} {hora}"
        if data:
            return data

        data_recebimento = cls._fmt_date(row.get("recebido_em_email"))
        if data_recebimento and hora:
            return f"{data_recebimento} {hora}"
        return data_recebimento or hora

    @staticmethod
    def _fmt_date(value) -> str:
        if value in (None, ""):
            return ""

        text = str(value)[:10]

        try:
            return datetime.strptime(text, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            return text

    @staticmethod
    def _fmt_hora(value) -> str:
        if not value:
            return ""

        try:
            texto = str(value).strip().replace("Z", "+00:00")
            data_hora = datetime.fromisoformat(texto)

            if data_hora.tzinfo is not None:
                data_hora = data_hora.astimezone()

            return data_hora.strftime("%H:%M")
        except (ValueError, TypeError):
            return ""

    @staticmethod
    def _fmt(value) -> str:
        if value in (None, ""):
            return "0"

        number = Decimal(str(value))
        text = f"{number:.3f}".rstrip("0").rstrip(".")
        return text or "0"
    