from __future__ import annotations

from decimal import Decimal
from tkinter import messagebox, ttk

import customtkinter as ctk

from core.almox_repository import AlmoxRepository


class VisaoAdministrativaView(ctk.CTkFrame):
    COLUMNS = (
        "origem",
        "data",
        "tipo",
        "material",
        "dimensao",
        "quantidade",
        "entregue",
        "rastreabilidade",
        "maquina",
        "localizacao",
        "setor",
        "conclusao",
    )

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)
        self.repository: AlmoxRepository | None = None
        self.all_rows: list[dict] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_filters()
        self._build_table()
        self.after(100, self.refresh)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        ctk.CTkLabel(
            header,
            text="Visão administrativa — FAB e EST entregues",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(side="left")
        ctk.CTkButton(header, text="Atualizar", command=self.refresh).pack(side="right")

    def _build_filters(self) -> None:
        filters = ctk.CTkFrame(self)
        filters.grid(row=1, column=0, sticky="ew", padx=20, pady=8)

        ctk.CTkLabel(filters, text="Buscar:").pack(side="left", padx=(10, 5), pady=10)
        self.search_entry = ctk.CTkEntry(
            filters,
            width=320,
            placeholder_text="Material, dimensão, máquina, setor...",
        )
        self.search_entry.pack(side="left", padx=5, pady=10)
        self.search_entry.bind("<KeyRelease>", lambda _event: self._apply_filter())

        ctk.CTkLabel(filters, text="Origem:").pack(side="left", padx=(20, 5), pady=10)
        self.origin_filter = ctk.CTkOptionMenu(
            filters,
            values=["TODOS", "FAB", "EST"],
            command=lambda _value: self._apply_filter(),
        )
        self.origin_filter.pack(side="left", padx=5, pady=10)

        self.counter_label = ctk.CTkLabel(filters, text="0 registro(s)")
        self.counter_label.pack(side="right", padx=10, pady=10)

    def _build_table(self) -> None:
        container = ctk.CTkFrame(self)
        container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(8, 20))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(container, columns=self.COLUMNS, show="headings")
        labels = {
            "origem": "Origem",
            "data": "Data",
            "tipo": "Tipo",
            "material": "Material",
            "dimensao": "Dimensão",
            "quantidade": "Quantidade",
            "entregue": "Entregue EST",
            "rastreabilidade": "Rastreabilidade",
            "maquina": "Máquina",
            "localizacao": "Localização",
            "setor": "Setor",
            "conclusao": "Conclusão",
        }
        widths = {
            "origem": 70,
            "data": 90,
            "tipo": 70,
            "material": 120,
            "dimensao": 180,
            "quantidade": 85,
            "entregue": 90,
            "rastreabilidade": 130,
            "maquina": 100,
            "localizacao": 110,
            "setor": 100,
            "conclusao": 145,
        }
        for column in self.COLUMNS:
            self.tree.heading(column, text=labels[column])
            self.tree.column(column, width=widths[column], anchor="center")
        self.tree.column("material", anchor="w")
        self.tree.column("dimensao", anchor="w")

        y_scroll = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    def refresh(self) -> None:
        try:
            if self.repository is None:
                self.repository = AlmoxRepository()
            self.all_rows = self.repository.listar_visao_administrativa()
        except Exception as exc:
            messagebox.showerror("Visão administrativa", str(exc))
            return
        self._apply_filter()

    def _apply_filter(self) -> None:
        search = self.search_entry.get().strip().lower()
        origin = self.origin_filter.get()

        filtered: list[dict] = []
        for row in self.all_rows:
            if origin != "TODOS" and row.get("stock_location") != origin:
                continue

            searchable = " ".join(
                str(row.get(field) or "")
                for field in (
                    "material",
                    "dimension",
                    "traceability",
                    "machine",
                    "location",
                    "sector",
                    "email_subject",
                )
            ).lower()
            if search and search not in searchable:
                continue
            filtered.append(row)

        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for row in filtered:
            self.tree.insert(
                "",
                "end",
                values=(
                    row.get("stock_location") or "",
                    row.get("request_date") or "",
                    row.get("material_type") or "",
                    row.get("material") or "",
                    row.get("dimension") or "",
                    self._fmt(row.get("quantity_requested")),
                    self._fmt(row.get("quantity_delivered")),
                    row.get("traceability") or "",
                    row.get("machine") or "",
                    row.get("location") or "",
                    row.get("sector") or "",
                    row.get("completed_at") or "Não se aplica (FAB)",
                ),
            )

        self.counter_label.configure(text=f"{len(filtered)} registro(s)")

    @staticmethod
    def _fmt(value) -> str:
        if value in (None, ""):
            return "0"
        number = Decimal(str(value))
        return f"{number:.3f}".rstrip("0").rstrip(".") or "0"
