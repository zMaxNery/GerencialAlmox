from __future__ import annotations

import getpass
from tkinter import ttk

import customtkinter as ctk

from modules.lancamentos_baixa_totvs.scipts import Scripts


class View(ctk.CTkFrame):
    COLUMNS = (
        "tipo",
        "requisicao",
        "material",
        "os_so",
        "of",
        "peso",
        "requisitado_em",
        "entregue_em",
        "operador",
    )

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.scripts = Scripts(self)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_filters()
        self._build_table()
        self._build_footer()

        self.after(100, self.scripts.refresh)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_box,
            text="Requisições para baixar",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkButton(
            header,
            text="Atualizar",
            width=110,
            command=self.scripts.refresh,
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
            command=lambda _value: self.scripts._apply_filters(),
        )
        self.type_filter.set("EST")
        self.type_filter.grid(row=0, column=1, padx=(0, 12), pady=10)

        ctk.CTkLabel(filters, text="Pesquisar:").grid(
            row=0, column=2, padx=(0, 5), pady=10
        )

        self.search_entry = ctk.CTkEntry(
            filters,
            placeholder_text="Requisição, material, OS-SO ou OF",
        )
        self.search_entry.grid(row=0, column=3, sticky="ew", padx=(0, 12), pady=10)
        self.search_entry.bind("<KeyRelease>", lambda _event: self.scripts._apply_filters())

        ctk.CTkButton(
            filters,
            text="Limpar filtros",
            width=115,
            command=self.scripts._clear_filters,
        ).grid(row=0, column=4, padx=(0, 12), pady=10)

    def _build_table(self) -> None:
        container = ctk.CTkFrame(self)
        container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(8, 8))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "LancamentosTotvs.Treeview",
            font=("Arial", 12),
            rowheight=36,
        )
        style.configure(
            "LancamentosTotvs.Treeview.Heading",
            font=("Arial", 14, "bold"),
        )

        self.tree = ttk.Treeview(
            container,
            columns=self.COLUMNS,
            show="headings",
            selectmode="extended",
            style="LancamentosTotvs.Treeview",
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
            "os_so": "OS-SO",
            "of": "OF",
            "peso": "Peso (KG)",
            "requisitado_em": "Dt/Hr Requisição",
            "entregue_em": "Dt/Hr Entrega",
            "operador": "Operador",
        }
        widths = {
            "tipo": 70,
            "requisicao": 125,
            "material": 250,
            "os_so": 125,
            "of": 110,
            "peso": 120,
            "requisitado_em": 190,
            "entregue_em": 170,
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
        self.tree.column("operador", anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.scripts._update_selection_count)

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
            text="Use Ctrl ou Shift para selecionar várias linhas.",
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
            command=self.scripts._select_visible,
        ).grid(row=1, column=2, padx=(0, 8), pady=(4, 10))

        ctk.CTkButton(
            footer,
            text="Limpar seleção",
            width=120,
            fg_color="#5E5E5E",
            hover_color="#4A4A4A",
            command=self.scripts._clear_selection,
        ).grid(row=1, column=3, sticky="w", padx=(0, 12), pady=(4, 10))

        ctk.CTkLabel(footer, text="Usuário:").grid(
            row=1, column=4, padx=(10, 5), pady=(4, 10)
        )

        self.admin_entry = ctk.CTkEntry(footer, width=180)
        self.admin_entry.insert(0, getpass.getuser())
        self.admin_entry.grid(row=1, column=5, padx=(0, 10), pady=(4, 10))

        ctk.CTkButton(
            footer,
            text="Marcar baixa",
            width=145,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.scripts.mark_as_posted,
        ).grid(row=1, column=6, padx=(0, 12), pady=(4, 10))
