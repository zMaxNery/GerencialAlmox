from __future__ import annotations

import getpass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

import customtkinter as ctk

from core.almox_repository import AlmoxRepository


class VisaoAdministrativaView(ctk.CTkFrame):
    COLUMNS = (
        "data_requisicao",
        "hora_requisicao",
        "data_entrega",
        "material",
        "dimensao",
        "solicitado",
        "entregue",
        "rastreabilidade",
        "estoque",
        "setor",
        "observacao",
    )

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.repository: AlmoxRepository | None = None
        self.all_rows: list[dict] = []
        self.rows: dict[str, dict] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_header()
        self._build_filters()
        self._build_return_form()
        self._build_table()

        self.after(100, self.refresh)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(20, 8),
        )

        ctk.CTkLabel(
            header,
            text="Entregas realizadas",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Atualizar",
            command=self.refresh,
        ).pack(side="right")

    def _build_filters(self) -> None:
        filters = ctk.CTkFrame(self)
        filters.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=8,
        )

        ctk.CTkLabel(filters, text="Buscar:").pack(
            side="left",
            padx=(10, 5),
            pady=10,
        )

        self.search_entry = ctk.CTkEntry(
            filters,
            width=300,
            placeholder_text=(
                "Material, rastreabilidade, estoque, setor ou observação"
            ),
        )
        self.search_entry.pack(side="left", padx=5, pady=10)
        self.search_entry.bind(
            "<KeyRelease>",
            lambda _event: self._apply_filter(),
        )

        ctk.CTkLabel(filters, text="Data entrega:").pack(
            side="left",
            padx=(15, 5),
            pady=10,
        )

        self.delivery_date_filter = ctk.CTkOptionMenu(
            filters,
            width=125,
            values=["TODAS"],
            command=lambda _value: self._apply_filter(),
        )
        self.delivery_date_filter.pack(side="left", padx=5, pady=10)

        ctk.CTkLabel(filters, text="Setor:").pack(
            side="left",
            padx=(15, 5),
            pady=10,
        )

        self.sector_filter = ctk.CTkOptionMenu(
            filters,
            width=140,
            values=["TODOS"],
            command=lambda _value: self._apply_filter(),
        )
        self.sector_filter.pack(side="left", padx=5, pady=10)

        ctk.CTkButton(
            filters,
            text="Limpar filtros",
            width=110,
            command=self._clear_filters,
        ).pack(side="left", padx=10, pady=10)

        self.counter_label = ctk.CTkLabel(
            filters,
            text="0 entrega(s)",
        )
        self.counter_label.pack(side="right", padx=10, pady=10)

    def _build_return_form(self) -> None:
        form = ctk.CTkFrame(self)
        form.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=20,
            pady=8,
        )
        form.grid_columnconfigure(5, weight=1)

        ctk.CTkLabel(
            form,
            text="Entrega selecionada:",
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.selected_label = ctk.CTkLabel(
            form,
            text="Nenhuma",
            anchor="w",
        )
        self.selected_label.grid(
            row=0,
            column=1,
            columnspan=6,
            padx=10,
            pady=10,
            sticky="ew",
        )

        ctk.CTkLabel(
            form,
            text="Quantidade a devolver:",
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.return_quantity_entry = ctk.CTkEntry(
            form,
            width=140,
            placeholder_text="Ex.: 1",
        )
        self.return_quantity_entry.grid(
            row=1,
            column=1,
            padx=10,
            pady=10,
            sticky="w",
        )

        ctk.CTkLabel(form, text="Operador:").grid(
            row=1,
            column=2,
            padx=10,
            pady=10,
            sticky="w",
        )

        self.operator_entry = ctk.CTkEntry(form, width=170)
        self.operator_entry.insert(0, getpass.getuser())
        self.operator_entry.grid(
            row=1,
            column=3,
            padx=10,
            pady=10,
            sticky="w",
        )

        ctk.CTkLabel(form, text="Motivo:").grid(
            row=1,
            column=4,
            padx=10,
            pady=10,
            sticky="w",
        )

        self.return_note_entry = ctk.CTkEntry(
            form,
            placeholder_text="Informe o motivo da devolução",
        )
        self.return_note_entry.grid(
            row=1,
            column=5,
            padx=10,
            pady=10,
            sticky="ew",
        )

        ctk.CTkButton(
            form,
            text="Devolver material",
            command=self.return_material,
        ).grid(row=1, column=6, padx=10, pady=10)

    def _build_table(self) -> None:
        style = ttk.Style()
        style.configure(
            "Historico.Treeview",
            font=("Arial", 11),
            rowheight=32,
        )
        style.configure(
            "Historico.Treeview.Heading",
            font=("Arial", 12, "bold"),
        )

        container = ctk.CTkFrame(self)
        container.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(8, 20),
        )
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            container,
            columns=self.COLUMNS,
            show="headings",
            selectmode="browse",
            style="Historico.Treeview",
        )

        self.tree.tag_configure(
            "linha_par",
            background="#BEBEBE",
            foreground="#000000",
        )
        self.tree.tag_configure(
            "linha_impar",
            background="#FFFFFF",
            foreground="#000000",
        )
        self.tree.tag_configure(
            "devolvido",
            foreground="#A00000",
        )

        labels = {
            "data_requisicao": "Data requisição",
            "hora_requisicao": "Hora requisição",
            "data_entrega": "Data entrega",
            "material": "Material",
            "dimensao": "Dimensão",
            "solicitado": "Solicitado",
            "entregue": "Entregue",
            "rastreabilidade": "Rastreabilidade",
            "estoque": "Estoque",
            "setor": "Setor",
            "observacao": "Observação",
        }

        widths = {
            "data_requisicao": 105,
            "hora_requisicao": 95,
            "data_entrega": 100,
            "material": 160,
            "dimensao": 150,
            "solicitado": 85,
            "entregue": 80,
            "rastreabilidade": 135,
            "estoque": 90,
            "setor": 100,
            "observacao": 240,
        }

        for column in self.COLUMNS:
            self.tree.heading(column, text=labels[column])
            self.tree.column(
                column,
                width=widths[column],
                anchor="center",
            )

        self.tree.column("material", anchor="w")
        self.tree.column("dimensao", anchor="w")
        self.tree.column("observacao", anchor="w")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        y_scroll = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self.tree.yview,
        )
        x_scroll = ttk.Scrollbar(
            container,
            orient="horizontal",
            command=self.tree.xview,
        )

        self.tree.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    def refresh(self) -> None:
        try:
            if self.repository is None:
                self.repository = AlmoxRepository()

            self.all_rows = self.repository.listar_historico_entregas()

        except Exception as exc:
            messagebox.showerror("Entregas realizadas", str(exc))
            return

        self._update_filter_options()
        self._apply_filter()

    def _update_filter_options(self) -> None:
        current_date = self.delivery_date_filter.get()
        current_sector = self.sector_filter.get()

        dates = sorted(
            {
                self._fmt_date(row.get("entregue_em"))
                for row in self.all_rows
                if row.get("entregue_em")
            },
            reverse=True,
        )

        sectors = sorted(
            {
                str(row.get("setor")).strip()
                for row in self.all_rows
                if row.get("setor")
            }
        )

        date_values = ["TODAS", *dates]
        sector_values = ["TODOS", *sectors]

        self.delivery_date_filter.configure(values=date_values)
        self.sector_filter.configure(values=sector_values)

        self.delivery_date_filter.set(
            current_date if current_date in date_values else "TODAS"
        )
        self.sector_filter.set(
            current_sector if current_sector in sector_values else "TODOS"
        )

    def _apply_filter(self) -> None:
        search = self.search_entry.get().strip().lower()
        selected_date = self.delivery_date_filter.get()
        selected_sector = self.sector_filter.get()

        filtered: list[dict] = []

        for row in self.all_rows:
            if (
                selected_date != "TODAS"
                and self._fmt_date(row.get("entregue_em"))
                != selected_date
            ):
                continue

            if (
                selected_sector != "TODOS"
                and str(row.get("setor") or "") != selected_sector
            ):
                continue

            searchable = " ".join(
                str(row.get(field) or "")
                for field in (
                    "material",
                    "dimensao",
                    "rastreabilidade",
                    "localizacao",
                    "setor",
                    "observacao",
                    "nome_operador",
                )
            ).lower()

            if search and search not in searchable:
                continue

            filtered.append(row)

        self._fill_table(filtered)

    def _fill_table(self, data: list[dict]) -> None:
        selected = self.tree.selection()
        selected_id = selected[0] if selected else None

        self.rows.clear()

        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for index, row in enumerate(data):
            key = str(row["apontamento_entrega_id"])
            self.rows[key] = row

            tags = [
                "linha_par" if index % 2 == 0 else "linha_impar"
            ]

            if Decimal(str(row.get("quantidade_devolvida") or 0)) > 0:
                tags.append("devolvido")

            self.tree.insert(
                "",
                "end",
                iid=key,
                values=(
                    self._fmt_date(row.get("data_requisicao")),
                    self._fmt_time(row.get("recebido_em_email")),
                    self._fmt_date(row.get("entregue_em")),
                    row.get("material") or "",
                    row.get("dimensao") or "",
                    self._fmt_number(row.get("quantidade_solicitada")),
                    self._fmt_number(row.get("quantidade_entregue")),
                    row.get("rastreabilidade") or "",
                    row.get("localizacao") or "",
                    row.get("setor") or "",
                    row.get("observacao") or "",
                ),
                tags=tuple(tags),
            )

        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id)
            self.tree.focus(selected_id)

        self.counter_label.configure(text=f"{len(data)} entrega(s)")

    def _on_select(self, _event=None) -> None:
        selected = self.tree.selection()

        if not selected:
            self.selected_label.configure(text="Nenhuma")
            return

        row = self.rows.get(selected[0])
        if not row:
            return

        self.selected_label.configure(
            text=(
                f"{row.get('material', '')} | "
                f"{row.get('dimensao', '')} | "
                f"entregue nesta linha: "
                f"{self._fmt_number(row.get('quantidade_entregue'))}"
            )
        )

        self.return_quantity_entry.delete(0, "end")
        self.return_note_entry.delete(0, "end")

    def return_material(self) -> None:
        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                "Devolução",
                "Selecione uma entrega na tabela.",
            )
            return

        row = self.rows.get(selected[0])
        if not row:
            return

        try:
            quantity = Decimal(
                self.return_quantity_entry.get()
                .strip()
                .replace(",", ".")
            )

            if quantity <= 0:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            messagebox.showerror(
                "Devolução",
                "Informe uma quantidade maior que zero.",
            )
            return

        available = Decimal(
            str(row.get("quantidade_entregue") or 0)
        )

        if quantity > available:
            messagebox.showerror(
                "Devolução",
                "A quantidade devolvida não pode ser maior que "
                f"{self._fmt_number(available)}.",
            )
            return

        operator_name = self.operator_entry.get().strip()
        note = self.return_note_entry.get().strip()

        if not operator_name:
            messagebox.showinfo(
                "Devolução",
                "Informe o operador responsável.",
            )
            return

        if not note:
            messagebox.showinfo(
                "Devolução",
                "Informe o motivo da devolução.",
            )
            return

        confirmed = messagebox.askyesno(
            "Confirmar devolução",
            (
                f"Devolver {self._fmt_number(quantity)} do material "
                f"{row.get('material', '')}?\n\n"
                "A quantidade retornará para a tela de pendências."
            ),
        )

        if not confirmed:
            return

        try:
            if self.repository is None:
                self.repository = AlmoxRepository()

            result = self.repository.devolver_material(
                apontamento_entrega_id=int(
                    row["apontamento_entrega_id"]
                ),
                quantidade=quantity,
                nome_operador=operator_name,
                observacao=note,
            )

        except Exception as exc:
            messagebox.showerror("Devolução", str(exc))
            self.refresh()
            return

        messagebox.showinfo(
            "Devolução",
            (
                "Devolução registrada. Quantidade líquida restante "
                "nesta entrega: "
                f"{self._fmt_number(result.get('quantidade_entregue_restante'))}"
            ),
        )

        self.return_quantity_entry.delete(0, "end")
        self.return_note_entry.delete(0, "end")
        self.selected_label.configure(text="Nenhuma")
        self.refresh()

    def _clear_filters(self) -> None:
        self.search_entry.delete(0, "end")
        self.delivery_date_filter.set("TODAS")
        self.sector_filter.set("TODOS")
        self._apply_filter()

    @staticmethod
    def _parse_datetime(value) -> datetime | None:
        if not value:
            return None

        try:
            text = str(value).strip().replace("Z", "+00:00")
            parsed = datetime.fromisoformat(text)

            if parsed.tzinfo is not None:
                parsed = parsed.astimezone()

            return parsed

        except (TypeError, ValueError):
            return None

    @classmethod
    def _fmt_date(cls, value) -> str:
        parsed = cls._parse_datetime(value)
        if parsed:
            return parsed.strftime("%d/%m/%Y")

        if value:
            try:
                return datetime.strptime(
                    str(value)[:10],
                    "%Y-%m-%d",
                ).strftime("%d/%m/%Y")
            except ValueError:
                return str(value)

        return ""

    @classmethod
    def _fmt_time(cls, value) -> str:
        parsed = cls._parse_datetime(value)
        return parsed.strftime("%H:%M") if parsed else ""

    @staticmethod
    def _fmt_number(value) -> str:
        if value in (None, ""):
            return "0"

        number = Decimal(str(value))
        return f"{number:.3f}".rstrip("0").rstrip(".") or "0"
