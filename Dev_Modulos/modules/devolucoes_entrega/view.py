from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from tkinter import messagebox, ttk

import customtkinter as ctk

from core.almox_repository import AlmoxRepository


class HistoricoDevolucoesView(ctk.CTkFrame):
    COLUMNS = (
        "data_devolucao",
        "hora_devolucao",
        "data_requisicao",
        "hora_requisicao",
        "material",
        "dimensao",
        "entregue",
        "devolvido",
        "rastreabilidade",
        "estoque",
        "setor",
        "operador",
        "observacao",
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
            text="Histórico de devoluções",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Atualizar",
            command=self.refresh,
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
            command=lambda _valor: self._apply_filters(),
        )
        self.setor_filter.set("TODOS")
        self.setor_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Data devolução:").pack(
            side="left", padx=(4, 4), pady=10
        )
        self.data_filter = ctk.CTkOptionMenu(
            filtros,
            width=125,
            values=["TODAS"],
            command=lambda _valor: self._apply_filters(),
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
            command=lambda _valor: self._apply_filters(),
        )
        self.estoque_filter.set("TODOS")
        self.estoque_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Material:").pack(
            side="left", padx=(4, 4), pady=10
        )
        self.material_filter = ctk.CTkEntry(
            filtros,
            width=135,
            placeholder_text="Buscar",
        )
        self.material_filter.pack(side="left", padx=(0, 8), pady=10)
        self.material_filter.bind(
            "<KeyRelease>", lambda _event: self._apply_filters()
        )

        ctk.CTkLabel(filtros, text="Rastreabilidade:").pack(
            side="left", padx=(4, 4), pady=10
        )
        self.rastreabilidade_filter = ctk.CTkEntry(
            filtros,
            width=135,
            placeholder_text="Buscar",
        )
        self.rastreabilidade_filter.pack(side="left", padx=(0, 8), pady=10)
        self.rastreabilidade_filter.bind(
            "<KeyRelease>", lambda _event: self._apply_filters()
        )

        ctk.CTkLabel(filtros, text="Operador:").pack(
            side="left", padx=(4, 4), pady=10
        )
        self.operador_filter = ctk.CTkEntry(
            filtros,
            width=120,
            placeholder_text="Buscar",
        )
        self.operador_filter.pack(side="left", padx=(0, 8), pady=10)
        self.operador_filter.bind(
            "<KeyRelease>", lambda _event: self._apply_filters()
        )

        ctk.CTkButton(
            filtros,
            text="Limpar",
            width=80,
            command=self._clear_filters,
        ).pack(side="left", padx=8, pady=10)

        self.counter_label = ctk.CTkLabel(filtros, text="0 devolução(ões)")
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

        labels = {
            "data_devolucao": "Dt Dev.",
            "hora_devolucao": "Hr Dev.",
            "data_requisicao": "Dt Req.",
            "hora_requisicao": "Hr Req.",
            "material": "Material",
            "dimensao": "Dimensão",
            "entregue": "Qtd. Req.",
            "devolvido": "Qtd. Dev.",
            "rastreabilidade": "Rastreabilidade",
            "estoque": "Estoque",
            "setor": "Setor",
            "operador": "Operador",
            "observacao": "Observação",
        }
        widths = {
            "data_devolucao": 100,
            "hora_devolucao": 85,
            "data_requisicao": 100,
            "hora_requisicao": 85,
            "material": 280,
            "dimensao": 120,
            "entregue": 110,
            "devolvido": 110,
            "rastreabilidade": 180,
            "estoque": 110,
            "setor": 110,
            "operador": 150,
            "observacao": 230,
        }

        for column in self.COLUMNS:
            self.tree.heading(column, text=labels[column])
            self.tree.column(column, width=widths[column], anchor="center")

        self.tree.column("material", anchor="w")
        self.tree.column("dimensao", anchor="w")
        self.tree.column("observacao", anchor="w")

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

            self.all_rows = self.repository.listar_historico_devolucoes()

        except Exception as exc:
            messagebox.showerror("Histórico de devoluções", str(exc))
            return

        self._update_filter_options()
        self._apply_filters()

    def _update_filter_options(self) -> None:
        setores = self._unique_values("setor")
        estoques = self._unique_values("localizacao")
        datas = sorted(
            {
                self._fmt_data(row.get("devolvido_em"))
                for row in self.all_rows
                if row.get("devolvido_em")
            },
            reverse=True,
        )

        self._set_option_values(self.setor_filter, ["TODOS", *setores], "TODOS")
        self._set_option_values(
            self.estoque_filter, ["TODOS", *estoques], "TODOS"
        )
        self._set_option_values(self.data_filter, ["TODAS", *datas], "TODAS")

    def _apply_filters(self) -> None:
        setor = self.setor_filter.get().strip()
        data_devolucao = self.data_filter.get().strip()
        estoque = self.estoque_filter.get().strip()
        material = self.material_filter.get().strip().lower()
        rastreabilidade = self.rastreabilidade_filter.get().strip().lower()
        operador = self.operador_filter.get().strip().lower()

        filtrados: list[dict] = []

        for row in self.all_rows:
            if setor != "TODOS" and str(row.get("setor") or "") != setor:
                continue

            if (
                data_devolucao != "TODAS"
                and self._fmt_data(row.get("devolvido_em")) != data_devolucao
            ):
                continue

            if estoque != "TODOS" and str(row.get("localizacao") or "") != estoque:
                continue

            if material and material not in str(row.get("material") or "").lower():
                continue

            if rastreabilidade and rastreabilidade not in str(
                row.get("rastreabilidade") or ""
            ).lower():
                continue

            if operador and operador not in str(
                row.get("operador_devolucao") or ""
            ).lower():
                continue

            filtrados.append(row)

        self._fill_table(filtrados)
        self.counter_label.configure(text=f"{len(filtrados)} devolução(ões)")

    def _fill_table(self, data: list[dict]) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for indice, row in enumerate(data):
            tag = "linha_par" if indice % 2 == 0 else "linha_impar"

            self.tree.insert(
                "",
                "end",
                iid=str(row["devolucao_id"]),
                values=(
                    self._fmt_data(row.get("devolvido_em")),
                    self._fmt_hora(row.get("devolvido_em")),
                    self._fmt_data(row.get("data_requisicao")),
                    self._fmt_hora(row.get("recebido_em_email")),
                    row.get("material") or "",
                    row.get("dimensao") or "",
                    self._fmt(row.get("quantidade_entregue_original")),
                    self._fmt(row.get("quantidade_devolvida")),
                    row.get("rastreabilidade") or "",
                    row.get("localizacao") or "",
                    row.get("setor") or "",
                    row.get("operador_devolucao") or "",
                    row.get("observacao_devolucao") or "",
                ),
                tags=(tag,),
            )

    def _clear_filters(self) -> None:
        self.setor_filter.set("TODOS")
        self.data_filter.set("TODAS")
        self.estoque_filter.set("TODOS")
        self.material_filter.delete(0, "end")
        self.rastreabilidade_filter.delete(0, "end")
        self.operador_filter.delete(0, "end")
        self._apply_filters()

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
