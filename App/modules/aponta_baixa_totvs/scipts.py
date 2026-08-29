from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox
from typing import TYPE_CHECKING

from modules._shared.almox_repository import AlmoxRepository

if TYPE_CHECKING:
    from modules.aponta_baixa_totvs.view import View


class Scripts:
    def __init__(self, view: View):
        self.view = view
        self.repository: AlmoxRepository | None = None
        self.all_rows: list[dict] = []
        self.rows: dict[str, dict] = {}
    
    def refresh(self) -> None:
        try:
            if self.repository is None:
                self.repository = AlmoxRepository()

            self.all_rows = self.repository.listar_lancamentos_totvs_pendentes()
        except Exception as exc:
            messagebox.showerror("Lançamentos TOTVS", str(exc))
            return

        self._apply_filters()

    def _apply_filters(self) -> None:
        type_filter = self.view.type_filter.get().strip().upper()
        search = self.view.search_entry.get().strip().casefold()

        filtered: list[dict] = []

        for row in self.all_rows:
            row_type = str(row.get("tipo") or "").upper()
            if type_filter != "TODOS" and row_type != type_filter:
                continue

            if search:
                searchable = " ".join(
                    str(row.get(field) or "")
                    for field in (
                        "numero_requisicao",
                        "material",
                        "os_so",
                        "numero_of",
                    )
                ).casefold()
                if search not in searchable:
                    continue

            filtered.append(row)

        self._fill_table(filtered)
        self.view.counter_label.configure(text=f"{len(filtered)} linha(s)")

    def _fill_table(self, data: list[dict]) -> None:
        self.rows.clear()

        for item_id in self.view.tree.get_children():
            self.view.tree.delete(item_id)

        for index, row in enumerate(data):
            item_id = str(row["item_resumo_totvs_id"])
            self.rows[item_id] = row

            self.view.tree.insert(
                "",
                "end",
                iid=item_id,
                values=(
                    row.get("tipo") or "",
                    row.get("numero_requisicao") or "",
                    row.get("material") or "",
                    row.get("os_so") or "",
                    row.get("numero_of") or "",
                    self._fmt_number(row.get("peso_kg")),
                    self._fmt_request_datetime(row),
                    self._fmt_datetime(row.get("entregue_em")),
                    row.get("operador") or "",
                ),
                tags=("linha_par" if index % 2 == 0 else "linha_impar",),
            )

        self._update_selection_count()

    def mark_as_posted(self) -> None:
        selected = self.view.tree.selection()
        if not selected:
            messagebox.showinfo(
                "Lançamentos TOTVS",
                "Selecione ao menos uma linha para marcar a baixa.",
            )
            return

        admin_name = self.view.admin_entry.get().strip()
        if not admin_name:
            messagebox.showinfo(
                "Lançamentos TOTVS",
                "Informe seu usuário.",
            )
            return

        selected_rows = [self.rows[item_id] for item_id in selected if item_id in self.rows]
        if not selected_rows:
            messagebox.showerror(
                "Lançamentos TOTVS",
                "As linhas selecionadas não estão mais disponíveis.",
            )
            self.refresh()
            return

        question = (
            f"Confirmar a baixa de {len(selected_rows)} linha(s) selecionadas?\n\n"
        )

        if not messagebox.askyesno("Confirmar baixa", question):
            return

        try:
            result = self.repository.marcar_baixas_resumo_totvs(
                item_resumo_ids=[
                    int(row["item_resumo_totvs_id"])
                    for row in selected_rows
                ],
                nome_responsavel=admin_name,
            )
        except Exception as exc:
            messagebox.showerror("Lançamentos TOTVS", str(exc))
            self.refresh()
            return

        quantity = result.get("quantidade_baixada", len(selected_rows))
        messagebox.showinfo(
            "Lançamentos TOTVS",
            f"Baixa registrada para {quantity} linha(s).",
        )
        self.refresh()

    def _select_visible(self) -> None:
        children = self.view.tree.get_children()
        if children:
            self.view.tree.selection_set(*children)
        self._update_selection_count()

    def _clear_selection(self) -> None:
        selected = self.view.tree.selection()
        if selected:
            self.view.tree.selection_remove(*selected)
        self._update_selection_count()

    def _clear_filters(self) -> None:
        self.view.type_filter.set("EST")
        self.view.search_entry.delete(0, "end")
        self._apply_filters()

    def _update_selection_count(self, _event=None) -> None:
        self.view.selection_label.configure(
            text=f"{len(self.view.tree.selection())} selecionada(s)"
        )

    @classmethod
    def _fmt_request_datetime(cls, row: dict) -> str:
        request_date = cls._fmt_date(row.get("data_requisicao"))
        request_time = cls._fmt_time(row.get("recebido_em_email"))

        if request_date and request_time:
            return f"{request_date} {request_time}"
        if request_date:
            return request_date
        return cls._fmt_datetime(row.get("recebido_em_email"))

    @staticmethod
    def _parse_datetime(value) -> datetime | None:
        if value in (None, ""):
            return None

        try:
            parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone()
            return parsed
        except (TypeError, ValueError):
            return None

    @classmethod
    def _fmt_datetime(cls, value) -> str:
        parsed = cls._parse_datetime(value)
        if parsed is None:
            return ""
        return parsed.strftime("%d/%m/%Y %H:%M")

    @classmethod
    def _fmt_time(cls, value) -> str:
        parsed = cls._parse_datetime(value)
        if parsed is None:
            return ""
        return parsed.strftime("%H:%M")

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
    def _fmt_number(value) -> str:
        if value in (None, ""):
            return "0"

        try:
            number = Decimal(str(value).replace(",", "."))
        except InvalidOperation:
            return str(value)

        text = f"{number:.3f}".rstrip("0").rstrip(".")
        return text or "0"