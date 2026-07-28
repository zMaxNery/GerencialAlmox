from __future__ import annotations

import getpass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

import customtkinter as ctk

from modules._shared.almox_repository import AlmoxRepository


class HistoricoBaixasTotvsView(ctk.CTkFrame):
    """Baixas administrativas ativas, com possibilidade de estorno."""

    COLUMNS = (
        "tipo",
        "requisicao",
        "material",
        "peso",
        "baixado_por",
        "baixado_em",
        "entregue_em",
        "requisitado_em",
        "operador",
    )

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.repository: AlmoxRepository | None = None
        self.all_rows: list[dict] = []
        self.rows: dict[str, dict] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_filters()
        self._build_table()
        self._build_footer()

        self.after(100, self.refresh)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_box,
            text="Baixas administrativas do TOTVS",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text=(
                "O estorno devolve as linhas para a tela de lançamentos e "
                "libera novamente possíveis devoluções do operador."
            ),
            text_color=("gray35", "gray70"),
        ).pack(anchor="w", pady=(3, 0))

        ctk.CTkButton(
            header,
            text="Atualizar",
            width=110,
            command=self.refresh,
        ).grid(row=0, column=1, sticky="e")

    def _build_filters(self) -> None:
        filters = ctk.CTkFrame(self)
        filters.grid(row=1, column=0, sticky="ew", padx=20, pady=8)
        filters.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(filters, text="Tipo:").grid(
            row=0, column=0, padx=(12, 5), pady=10
        )

        self.type_filter = ctk.CTkOptionMenu(
            filters,
            width=110,
            values=["TODOS", "EST", "FAB"],
            command=lambda _value: self._apply_filters(),
        )
        self.type_filter.set("TODOS")
        self.type_filter.grid(row=0, column=1, padx=(0, 12), pady=10)

        ctk.CTkLabel(filters, text="Pesquisar:").grid(
            row=0, column=2, padx=(0, 5), pady=10
        )

        self.search_entry = ctk.CTkEntry(
            filters,
            placeholder_text="Requisição, material, responsável ou operador",
        )
        self.search_entry.grid(row=0, column=3, sticky="ew", padx=(0, 12), pady=10)
        self.search_entry.bind("<KeyRelease>", lambda _event: self._apply_filters())

        ctk.CTkButton(
            filters,
            text="Limpar filtros",
            width=115,
            command=self._clear_filters,
        ).grid(row=0, column=4, padx=(0, 12), pady=10)

    def _build_table(self) -> None:
        container = ctk.CTkFrame(self)
        container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(8, 8))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "HistoricoBaixasTotvs.Treeview",
            font=("Arial", 11),
            rowheight=34,
        )
        style.configure(
            "HistoricoBaixasTotvs.Treeview.Heading",
            font=("Arial", 12, "bold"),
        )

        self.tree = ttk.Treeview(
            container,
            columns=self.COLUMNS,
            show="headings",
            selectmode="extended",
            style="HistoricoBaixasTotvs.Treeview",
        )
        self.tree.tag_configure(
            "linha_par",
            background="#D7D7D7",
            foreground="#000000",
        )
        self.tree.tag_configure(
            "linha_impar",
            background="#FFFFFF",
            foreground="#000000",
        )

        labels = {
            "tipo": "Tipo",
            "requisicao": "Requisição",
            "material": "Material",
            "peso": "Peso (KG)",
            "baixado_por": "Quem baixou",
            "baixado_em": "Data/Hora Baixa",
            "entregue_em": "Data/Hora Entrega",
            "requisitado_em": "Data/Hora Requisição",
            "operador": "Operador",
        }
        widths = {
            "tipo": 70,
            "requisicao": 125,
            "material": 250,
            "peso": 105,
            "baixado_por": 180,
            "baixado_em": 170,
            "entregue_em": 170,
            "requisitado_em": 170,
            "operador": 220,
        }

        for column in self.COLUMNS:
            self.tree.heading(column, text=labels[column])
            self.tree.column(
                column,
                width=widths[column],
                minwidth=widths[column],
                stretch=False,
                anchor="center",
            )

        self.tree.column("material", anchor="w")
        self.tree.column("baixado_por", anchor="w")
        self.tree.column("operador", anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self._update_selection_count)

        y_scroll = ctk.CTkScrollbar(
            container,
            orientation="vertical",
            command=self.tree.yview,
            width=22,
        )
        x_scroll = ctk.CTkScrollbar(
            container,
            orientation="horizontal",
            command=self.tree.xview,
            height=22,
        )

        self.tree.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self)
        footer.grid(row=3, column=0, sticky="ew", padx=20, pady=(8, 20))
        footer.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            footer,
            text="Use Ctrl ou Shift para selecionar várias baixas.",
            text_color=("gray35", "gray70"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(10, 4))

        self.counter_label = ctk.CTkLabel(footer, text="0 linha(s)")
        self.counter_label.grid(row=1, column=0, sticky="w", padx=(12, 10), pady=(4, 10))

        self.selection_label = ctk.CTkLabel(footer, text="0 selecionada(s)")
        self.selection_label.grid(row=1, column=1, sticky="w", padx=(0, 12), pady=(4, 10))

        ctk.CTkButton(
            footer,
            text="Selecionar visíveis",
            width=135,
            command=self._select_visible,
        ).grid(row=1, column=2, padx=(0, 8), pady=(4, 10))

        ctk.CTkButton(
            footer,
            text="Limpar seleção",
            width=120,
            fg_color="#5E5E5E",
            hover_color="#4A4A4A",
            command=self._clear_selection,
        ).grid(row=1, column=3, sticky="w", padx=(0, 12), pady=(4, 10))

        ctk.CTkLabel(footer, text="Quem está estornando:").grid(
            row=1, column=4, padx=(10, 5), pady=(4, 10)
        )

        self.admin_entry = ctk.CTkEntry(footer, width=180)
        self.admin_entry.insert(0, getpass.getuser())
        self.admin_entry.grid(row=1, column=5, padx=(0, 10), pady=(4, 10))

        ctk.CTkButton(
            footer,
            text="Estornar baixa",
            width=145,
            height=40,
            fg_color="#B05A00",
            hover_color="#8F4900",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.reverse_posting,
        ).grid(row=1, column=6, padx=(0, 12), pady=(4, 10))

    def refresh(self) -> None:
        try:
            if self.repository is None:
                self.repository = AlmoxRepository()

            self.all_rows = self.repository.listar_baixas_administrativas_totvs()
        except Exception as exc:
            messagebox.showerror("Baixas TOTVS", str(exc))
            return

        self._apply_filters()

    def _apply_filters(self) -> None:
        type_filter = self.type_filter.get().strip().upper()
        search = self.search_entry.get().strip().casefold()

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
                        "baixado_por",
                        "operador",
                    )
                ).casefold()
                if search not in searchable:
                    continue

            filtered.append(row)

        self._fill_table(filtered)
        self.counter_label.configure(text=f"{len(filtered)} linha(s)")

    def _fill_table(self, data: list[dict]) -> None:
        self.rows.clear()

        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for index, row in enumerate(data):
            item_id = str(row["baixa_administrativa_id"])
            self.rows[item_id] = row

            self.tree.insert(
                "",
                "end",
                iid=item_id,
                values=(
                    row.get("tipo") or "",
                    row.get("numero_requisicao") or "",
                    row.get("material") or "",
                    self._fmt_number(row.get("peso_kg")),
                    row.get("baixado_por") or "",
                    self._fmt_datetime(row.get("baixado_em")),
                    self._fmt_datetime(row.get("entregue_em")),
                    self._fmt_request_datetime(row),
                    row.get("operador") or "",
                ),
                tags=("linha_par" if index % 2 == 0 else "linha_impar",),
            )

        self._update_selection_count()

    def reverse_posting(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(
                "Baixas TOTVS",
                "Selecione ao menos uma baixa para estornar.",
            )
            return

        admin_name = self.admin_entry.get().strip()
        if not admin_name:
            messagebox.showinfo(
                "Baixas TOTVS",
                "Informe quem está realizando o estorno.",
            )
            return

        selected_rows = [self.rows[item_id] for item_id in selected if item_id in self.rows]
        if not selected_rows:
            messagebox.showerror(
                "Baixas TOTVS",
                "As baixas selecionadas não estão mais disponíveis.",
            )
            self.refresh()
            return

        question = (
            f"Confirmar o estorno de {len(selected_rows)} baixa(s)?\n\n"
            "As linhas voltarão para a tela de lançamentos, desde que continuem "
            "atendendo às condições de liberação."
        )
        if not messagebox.askyesno("Confirmar estorno", question):
            return

        try:
            result = self.repository.estornar_baixa_administrativa_totvs(
                baixa_ids=[
                    int(row["baixa_administrativa_id"])
                    for row in selected_rows
                ],
                nome_responsavel=admin_name,
            )
        except Exception as exc:
            messagebox.showerror("Baixas TOTVS", str(exc))
            self.refresh()
            return

        quantity = result.get("quantidade_estornada", len(selected_rows))
        messagebox.showinfo(
            "Baixas TOTVS",
            f"Estorno registrado para {quantity} baixa(s).",
        )
        self.refresh()

    def _select_visible(self) -> None:
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(*children)
        self._update_selection_count()

    def _clear_selection(self) -> None:
        selected = self.tree.selection()
        if selected:
            self.tree.selection_remove(*selected)
        self._update_selection_count()

    def _clear_filters(self) -> None:
        self.type_filter.set("TODOS")
        self.search_entry.delete(0, "end")
        self._apply_filters()

    def _update_selection_count(self, _event=None) -> None:
        self.selection_label.configure(
            text=f"{len(self.tree.selection())} selecionada(s)"
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
