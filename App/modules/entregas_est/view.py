from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk

from modules.entregas_est.scripts import Scripts


class EntregasEstView(ctk.CTkFrame):
    COLUMNS = (
        "data",
        "horario",
        "material",
        "dimensao",
        "solicitado",
        "entregue",
        "falta",
        "rastreabilidade",
        "setor_dest",
        "estoque",
    )

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.rows: dict[str, dict] = {}
        self.saldos_fabrica: dict[int, dict] = {}
        self.quantidade_var = ctk.StringVar(value="")

        self.scripts = Scripts(self)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_filters()
        self._build_content()

        self.after(100, self.scripts.refresh)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        ctk.CTkLabel(
            header,
            text="Requisições pendentes",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Atualizar",
            command=self.scripts.refresh,
        ).pack(side="right")

    def _build_filters(self) -> None:
        filtros = ctk.CTkFrame(self)
        filtros.grid(row=1, column=0, sticky="ew", padx=20, pady=8)

        ctk.CTkLabel(filtros, text="Setor:").pack(
            side="left",
            padx=(10, 4),
            pady=10,
        )
        self.setor_filter = ctk.CTkOptionMenu(
            filtros,
            width=120,
            values=["TODOS"],
            command=lambda _valor: self.scripts._apply_filters(),
        )
        self.setor_filter.set("TODOS")
        self.setor_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Data:").pack(
            side="left",
            padx=(4, 4),
            pady=10,
        )
        self.data_filter = ctk.CTkOptionMenu(
            filtros,
            width=120,
            values=["TODAS"],
            command=lambda _valor: self.scripts._apply_filters(),
        )
        self.data_filter.set("TODAS")
        self.data_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Estoque:").pack(
            side="left",
            padx=(4, 4),
            pady=10,
        )
        self.estoque_filter = ctk.CTkOptionMenu(
            filtros,
            width=120,
            values=["TODOS"],
            command=lambda _valor: self.scripts._apply_filters(),
        )
        self.estoque_filter.set("TODOS")
        self.estoque_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Material:").pack(
            side="left",
            padx=(4, 4),
            pady=10,
        )
        self.material_filter = ctk.CTkEntry(
            filtros,
            width=150,
            placeholder_text="Código ou descrição",
        )
        self.material_filter.pack(side="left", padx=(0, 8), pady=10)
        self.material_filter.bind(
            "<KeyRelease>",
            lambda _event: self.scripts._apply_filters(),
        )

        ctk.CTkLabel(filtros, text="Rastreabilidade:").pack(
            side="left",
            padx=(4, 4),
            pady=10,
        )
        self.rastreabilidade_filter = ctk.CTkEntry(
            filtros,
            width=150,
            placeholder_text="Buscar",
        )
        self.rastreabilidade_filter.pack(side="left", padx=(0, 8), pady=10)
        self.rastreabilidade_filter.bind(
            "<KeyRelease>",
            lambda _event: self.scripts._apply_filters(),
        )

        ctk.CTkButton(
            filtros,
            text="Limpar filtros",
            width=110,
            command=self.scripts._clear_filters,
        ).pack(side="left", padx=8, pady=10)

        self.counter_label = ctk.CTkLabel(
            filtros,
            text="0 item(ns)",
        )
        self.counter_label.pack(side="right", padx=10, pady=10)

    def _build_content(self) -> None:
        conteudo = ctk.CTkFrame(self, fg_color="transparent")
        conteudo.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(8, 20),
        )
        conteudo.grid_columnconfigure(0, weight=1)
        conteudo.grid_columnconfigure(1, weight=0)
        conteudo.grid_rowconfigure(0, weight=1)

        self._build_table(conteudo)
        self._build_keypad(conteudo)

    def _build_keypad(self, parent) -> None:
        painel = ctk.CTkFrame(parent, width=290)
        painel.grid(row=0, column=1, sticky="nse", padx=(10, 0))
        painel.grid_propagate(False)
        painel.grid_columnconfigure((0, 1, 2), weight=1)

        # ctk.CTkLabel(
        #     painel,
        #     text="Item selecionado",
        #     font=ctk.CTkFont(size=14, weight="bold"),
        # ).grid(
        #     row=0,
        #     column=0,
        #     columnspan=3,
        #     sticky="w",
        #     padx=12,
        #     pady=(12, 2),
        # )

        # self.selected_label = ctk.CTkLabel(
        #     painel,
        #     text="Nenhum item selecionado",
        #     anchor="w",
        #     justify="left",
        #     wraplength=260,
        # )
        # self.selected_label.grid(
        #     row=1,
        #     column=0,
        #     columnspan=3,
        #     sticky="ew",
        #     padx=12,
        #     pady=(0, 4),
        # )

        self.fabrica_label = ctk.CTkLabel(
            painel,
            text="",
            anchor="w",
            justify="left",
            text_color="#39A96B",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.fabrica_label.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=12,
            pady=(0, 8),
        )
        self.fabrica_label.grid_remove()

        ctk.CTkLabel(
            painel,
            text="Quantidade entregue",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(
            row=3,
            column=0,
            columnspan=3,
            sticky="w",
            padx=12,
            pady=(4, 4),
        )

        self.quantidade_display = ctk.CTkEntry(
            painel,
            textvariable=self.quantidade_var,
            height=58,
            justify="right",
            fg_color=("#FFFFFF", "#151515"),
            corner_radius=6,
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.quantidade_display.grid(
            row=4,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=12,
            pady=(0, 10),
        )

        botoes = (
            ("7", 5, 0),
            ("8", 5, 1),
            ("9", 5, 2),
            ("4", 6, 0),
            ("5", 6, 1),
            ("6", 6, 2),
            ("1", 7, 0),
            ("2", 7, 1),
            ("3", 7, 2),
            ("0", 8, 0),
            ("00", 8, 1),
            (",", 8, 2),
        )

        for texto, linha, coluna in botoes:
            ctk.CTkButton(
                painel,
                text=texto,
                height=48,
                font=ctk.CTkFont(size=18, weight="bold"),
                command=lambda valor=texto: self.scripts._keypad_add(valor),
            ).grid(
                row=linha,
                column=coluna,
                sticky="nsew",
                padx=5,
                pady=5,
            )

        ctk.CTkButton(
            painel,
            text="Apagar",
            command=self.scripts._keypad_backspace,
        ).grid(row=9, column=0, sticky="ew", padx=5, pady=5)

        ctk.CTkButton(
            painel,
            text="Limpar",
            command=self.scripts._keypad_clear,
        ).grid(row=9, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkButton(
            painel,
            text="Total",
            command=self.scripts._keypad_fill_remaining,
        ).grid(row=9, column=2, sticky="ew", padx=5, pady=5)

        # ctk.CTkLabel(
        #     painel,
        #     text="Operador:",
        # ).grid(
        #     row=10,
        #     column=0,
        #     columnspan=3,
        #     sticky="w",
        #     padx=12,
        #     pady=(12, 2),
        # )

        # self.operator_entry = ctk.CTkEntry(painel)
        # self.operator_entry.insert(0, getpass.getuser())
        # self.operator_entry.grid(
        #     row=11,
        #     column=0,
        #     columnspan=3,
        #     sticky="ew",
        #     padx=12,
        #     pady=(0, 8),
        # )

        # ctk.CTkLabel(
        #     painel,
        #     text="Observação:",
        # ).grid(
        #     row=12,
        #     column=0,
        #     columnspan=3,
        #     sticky="w",
        #     padx=12,
        #     pady=(2, 2),
        # )

        # self.note_entry = ctk.CTkEntry(
        #     painel,
        #     placeholder_text="Opcional",
        # )
        # self.note_entry.grid(
        #     row=13,
        #     column=0,
        #     columnspan=3,
        #     sticky="ew",
        #     padx=12,
        #     pady=(0, 10),
        # )

        ctk.CTkButton(
            painel,
            text="Registrar entrega",
            height=46,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.scripts.register_delivery,
        ).grid(
            row=14,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=12,
            pady=25,
        )

    def _build_table(self, parent) -> None:
        style = ttk.Style()
        style.configure(
            "Requisicoes.Treeview",
            font=("Arial", 12),
            rowheight=36,
        )
        style.configure(
            "Requisicoes.Treeview.Heading",
            font=("Arial", 14, "bold"),
        )

        container = ctk.CTkFrame(parent)
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            container,
            columns=self.COLUMNS,
            show="headings",
            selectmode="browse",
            style="Requisicoes.Treeview",
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

        labels = {
            "data": "Data",
            "horario": "Hr Req",
            "material": "Material",
            "dimensao": "Dimensão",
            "solicitado": "Solicitado",
            "entregue": "Entregue",
            "falta": "Falta",
            "rastreabilidade": "Rastreabilidade",
            "setor_dest": "Setor",
            "estoque": "Estoque",
        }
        widths = {
            "data": 110,
            "horario": 80,
            "material": 290,
            "dimensao": 120,
            "solicitado": 110,
            "entregue": 110,
            "falta": 70,
            "rastreabilidade": 180,
            "setor_dest": 110,
            "estoque": 110,
        }

        for column in self.COLUMNS:
            largura = widths[column]
            self.tree.heading(column, text=labels[column])
            self.tree.column(
                column,
                width=largura,
                minwidth=largura,
                stretch=False,
                anchor="center",
            )

        self.tree.column("material", anchor="w")
        self.tree.column("dimensao", anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.scripts._on_select)
        self.tree.bind(
            "<Shift-MouseWheel>",
            self.scripts._rolar_horizontal,
        )

        y_scroll = ctk.CTkScrollbar(
            container,
            orientation="vertical",
            command=self.tree.yview,
            width=22,
            fg_color=("gray85", "gray20"),
            button_color=("#557A95", "#557A95"),
            button_hover_color=("#2F80ED", "#2F80ED"),
            corner_radius=6,
            border_spacing=3,
        )

        x_scroll = ctk.CTkScrollbar(
            container,
            orientation="horizontal",
            command=self.tree.xview,
            height=22,
            fg_color=("gray85", "gray20"),
            button_color=("#557A95", "#557A95"),
            button_hover_color=("#2F80ED", "#2F80ED"),
            corner_radius=6,
            border_spacing=3,
        )

        self.tree.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    
