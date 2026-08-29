from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk

from modules.requisicoes_devolvidas.scripts import Scripts


class HistoricoDevolucoesView(ctk.CTkFrame):
    COLUMNS = (
        "devolvido_em",
        "requisitado_em",
        "material",
        "dimensao",
        "entregue",
        "devolvido",
        "rastreabilidade",
        "estoque",
        "setor_dest",
        "operador",
        "observacao",
    )

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.scripts = Scripts(self)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_filters()
        self._build_table()
        self.after(100, self.scripts.refresh)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        ctk.CTkLabel(
            header,
            text="Histórico de devoluções",
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
            side="left", padx=(10, 4), pady=10
        )
        self.setor_filter = ctk.CTkOptionMenu(
            filtros,
            width=115,
            values=["TODOS"],
            command=lambda _v: self.scripts._apply_filters(),
        )
        self.setor_filter.set("TODOS")
        self.setor_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Data evento:").pack(
            side="left", padx=(4, 4), pady=10
        )
        self.data_filter = ctk.CTkOptionMenu(
            filtros,
            width=125,
            values=["TODAS"],
            command=lambda _v: self.scripts._apply_filters(),
        )
        self.data_filter.set("TODAS")
        self.data_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Estoque:").pack(
            side="left", padx=(4, 4), pady=10
        )
        self.estoque_filter = ctk.CTkOptionMenu(
            filtros,
            width=105,
            values=["TODOS"],
            command=lambda _v: self.scripts._apply_filters(),
        )
        self.estoque_filter.set("TODOS")
        self.estoque_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Pesquisar:").pack(
            side="left", padx=(6, 4), pady=10
        )
        self.pesquisa_filter = ctk.CTkEntry(
            filtros,
            width=330,
            placeholder_text=(
                "Requisição, material, rastreabilidade, operador, observação..."
            ),
        )
        self.pesquisa_filter.pack(side="left", padx=(0, 4), pady=10)
        self.pesquisa_filter.bind(
            "<KeyRelease>", lambda _e: self.scripts._apply_filters()
        )

        ctk.CTkButton(
            filtros,
            text="⌨",
            width=44,
            command=self.scripts.abrir_teclado_pesquisa,
        ).pack(side="left", padx=(0, 6), pady=10)

        ctk.CTkButton(
            filtros,
            text="Limpar",
            width=80,
            command=self.scripts._clear_filters,
        ).pack(side="left", padx=(0, 8), pady=10)

        self.counter_label = ctk.CTkLabel(filtros, text="0 registro(s)")
        self.counter_label.pack(side="right", padx=10, pady=10)

    def _build_table(self) -> None:
        style = ttk.Style()
        style.configure(
            "Devolucoes.Treeview",
            font=("Arial", 12),
            rowheight=36,
        )
        style.configure(
            "Devolucoes.Treeview.Heading",
            font=("Arial", 14, "bold"),
        )

        container = ctk.CTkFrame(self)
        container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(8, 20))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            container,
            columns=self.COLUMNS,
            show="headings",
            style="Devolucoes.Treeview",
        )

        self.tree.tag_configure(
            "linha_par", background="#BEBEBE", foreground="#000000"
        )
        self.tree.tag_configure(
            "linha_impar", background="#FFFFFF", foreground="#000000"
        )
        # Exclusões ficam com um tom vermelho muito leve apenas para distinguir
        # o evento sem prejudicar a leitura da tabela.
        self.tree.tag_configure(
            "exclusao_par", background="#F4D8D8", foreground="#000000"
        )
        self.tree.tag_configure(
            "exclusao_impar", background="#FBEAEA", foreground="#000000"
        )

        labels = {
            "devolvido_em": "Dt/Hr Evento",
            "requisitado_em": "Dt/Hr Req",
            "material": "Material",
            "dimensao": "Dimensão",
            "entregue": "Qtd. Req.",
            "devolvido": "Qtd. Dev.",
            "rastreabilidade": "Rastreabilidade",
            "estoque": "Estoque",
            "setor_dest": "Setor",
            "operador": "Operador",
            "observacao": "Observação",
        }
        widths = {
            "devolvido_em": 150,
            "requisitado_em": 150,
            "material": 280,
            "dimensao": 120,
            "entregue": 110,
            "devolvido": 110,
            "rastreabilidade": 180,
            "estoque": 110,
            "setor_dest": 110,
            "operador": 150,
            "observacao": 260,
        }

        for column in self.COLUMNS:
            self.tree.heading(column, text=labels[column])
            self.tree.column(column, width=widths[column], anchor="center")

        self.tree.column("material", anchor="w")
        self.tree.column("dimensao", anchor="w")
        self.tree.column("observacao", anchor="w")

        y_scroll = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
