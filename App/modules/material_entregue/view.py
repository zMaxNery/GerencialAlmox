from __future__ import annotations

import getpass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk
from typing import Callable

import customtkinter as ctk

from modules._shared.almox_repository import AlmoxRepository
from modules._shared.search_utils import corresponde_pesquisa
from modules._shared.virtual_keyboard import abrir_teclado_virtual


class ResumoEntregasView(ctk.CTkFrame):
    COLUMNS = (
        "requisitado_em",
        "entregue_em",
        "material",
        "dimensao",
        "solicitado",
        "entregue",
        "excedente",
        "rastreabilidade",
        "estoque",
        "setor_dest",
        "observacao",
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
        self.after(100, self.refresh)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        ctk.CTkLabel(
            header,
            text="Materiais entregues",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Atualizar",
            command=self.refresh,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            header,
            text="Devolver",
            command=self.abrir_janela_devolucao,
        ).pack(side="right", padx=(0, 10))

    def _build_filters(self) -> None:
        filtros = ctk.CTkFrame(self)
        filtros.grid(row=1, column=0, sticky="ew", padx=20, pady=8)

        ctk.CTkLabel(filtros, text="Setor:").pack(side="left", padx=(10, 4), pady=10)
        self.setor_filter = ctk.CTkOptionMenu(
            filtros, width=120, values=["TODOS"],
            command=lambda _valor: self._apply_filters(),
        )
        self.setor_filter.set("TODOS")
        self.setor_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Data entrega:").pack(side="left", padx=(4, 4), pady=10)
        self.data_filter = ctk.CTkOptionMenu(
            filtros, width=125, values=["TODAS"],
            command=lambda _valor: self._apply_filters(),
        )
        self.data_filter.set("TODAS")
        self.data_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Estoque:").pack(side="left", padx=(4, 4), pady=10)
        self.estoque_filter = ctk.CTkOptionMenu(
            filtros, width=110, values=["TODOS"],
            command=lambda _valor: self._apply_filters(),
        )
        self.estoque_filter.set("TODOS")
        self.estoque_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Pesquisar:").pack(side="left", padx=(6, 4), pady=10)
        self.pesquisa_filter = ctk.CTkEntry(
            filtros,
            width=330,
            placeholder_text="Material, rastreabilidade, operador, observação...",
        )
        self.pesquisa_filter.pack(side="left", padx=(0, 4), pady=10)
        self.pesquisa_filter.bind("<KeyRelease>", lambda _event: self._apply_filters())
        ctk.CTkButton(
            filtros,
            text="⌨",
            width=44,
            command=lambda: abrir_teclado_virtual(self.pesquisa_filter),
        ).pack(side="left", padx=(0, 6), pady=10)

        ctk.CTkButton(
            filtros, text="Limpar", width=80, command=self._clear_filters
        ).pack(side="left", padx=(0, 8), pady=10)

        self.counter_label = ctk.CTkLabel(filtros, text="0 entrega(s)")
        self.counter_label.pack(side="right", padx=10, pady=10)
    def _build_table(self) -> None:
        style = ttk.Style()
        style.configure(
            "HistoricoEntregas.Treeview",
            font=("Arial", 12),
            rowheight=36,
        )
        style.configure(
            "HistoricoEntregas.Treeview.Heading",
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
            selectmode="browse",
            style="HistoricoEntregas.Treeview",
        )

        self.tree.tag_configure(
            "linha_par", background="#BEBEBE", foreground="#000000"
        )
        self.tree.tag_configure(
            "linha_impar", background="#FFFFFF", foreground="#000000"
        )

        labels = {
            "requisitado_em": "Dt/Hr Req",
            "entregue_em": "Dt/Hr Entrega",
            "material": "Material",
            "dimensao": "Dimensão",
            "solicitado": "Solicitado",
            "entregue": "Entregue",
            "excedente": "Excedente",
            "rastreabilidade": "Rastreabilidade",
            "estoque": "Estoque",
            "setor_dest": "Setor",
            "observacao": "Observação",
            "operador": "Operador",
        }
        widths = {
            "requisitado_em": 155,
            "entregue_em": 155,
            "material": 280,
            "dimensao": 120,
            "solicitado": 110,
            "entregue": 110,
            "excedente": 120,
            "rastreabilidade": 180,
            "estoque": 110,
            "setor_dest": 110,
            "observacao": 200,
            "operador": 150,
        }

        for column in self.COLUMNS:
            largura = widths[column]

            self.tree.heading(
                column,
                text=labels[column],
            )

            self.tree.column(
                column,
                width=largura,
                minwidth=largura,
                stretch=False,
                anchor="center",
            )

        self.tree.column("material", anchor="w")
        self.tree.column("dimensao", anchor="w")
        self.tree.column("observacao", anchor="w")
        self.tree.bind("<Double-1>", lambda _event: self.abrir_janela_devolucao())

        y_scroll = ctk.CTkScrollbar(
            container,
            orientation="vertical",
            command=self.tree.yview,

            # Espessura da barra vertical
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

            # Espessura da barra horizontal
            height=22,

            fg_color=("gray85", "gray20"),
            button_color=("#557A95", "#557A95"),
            button_hover_color=("#2F80ED", "#2F80ED"),

            corner_radius=6,
            border_spacing=3,
        )

        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    def refresh(self) -> None:
        try:
            if self.repository is None:
                self.repository = AlmoxRepository()

            self.all_rows = self.repository.listar_historico_entregas()

        except Exception as exc:
            messagebox.showerror("Materiais entregues", str(exc))
            return

        self._update_filter_options()
        self._apply_filters()

    def _update_filter_options(self) -> None:
        setores = self._unique_values("setor_dest")
        estoques = self._unique_values("localizacao_est")
        datas = sorted(
            {
                self._fmt_data(row.get("entregue_em"))
                for row in self.all_rows
                if row.get("entregue_em")
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
        data_entrega = self.data_filter.get().strip()
        estoque = self.estoque_filter.get().strip()
        pesquisa = self.pesquisa_filter.get().strip()
        campos = (
            "numero_requisicao",
            "material",
            "dimensao",
            "rastreabilidade",
            "localizacao_est",
            "setor_dest",
            "usuario",
            "observacao",
            "origem_entrega",
            "entregue_em",
            "data_requisicao",
        )

        filtrados: list[dict] = []
        for row in self.all_rows:
            if setor != "TODOS" and str(row.get("setor_dest") or "") != setor:
                continue
            if (
                data_entrega != "TODAS"
                and self._fmt_data(row.get("entregue_em")) != data_entrega
            ):
                continue
            if estoque != "TODOS" and str(row.get("localizacao_est") or "") != estoque:
                continue
            if not corresponde_pesquisa(row, pesquisa, campos):
                continue
            filtrados.append(row)

        self._fill_table(filtrados)
        self.counter_label.configure(text=f"{len(filtrados)} entrega(s)")
    def _fill_table(self, data: list[dict]) -> None:
        self.rows.clear()

        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for indice, row in enumerate(data):
            key = str(row.get("historico_entrega_id") or row["apontamento_entrega_id"])
            self.rows[key] = row

            tag = "linha_par" if indice % 2 == 0 else "linha_impar"

            self.tree.insert(
                "",
                "end",
                iid=key,
                values=(
                    self._fmt_request_datetime(row),
                    self._fmt_data_hora(row.get("entregue_em")),
                    row.get("material") or "",
                    row.get("dimensao") or "",
                    self._fmt(row.get("quantidade_solicitada")),
                    self._fmt(row.get("quantidade_entregue")),
                    self._fmt(row.get("quantidade_excedente")),
                    row.get("rastreabilidade") or "",
                    row.get("localizacao_est") or "",
                    row.get("setor_dest") or "",
                    row.get("observacao") or "",
                    row.get("usuario") or "",
                ),
                tags=(tag,),
            )

    def _confirmar_devolucao(
        self,
        row: dict,
        quantidade_texto: str,
        observacao: str,
    ) -> None:
        try:
            quantidade = Decimal(quantidade_texto.strip().replace(",", "."))
            if quantidade <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            messagebox.showerror(
                "Devolução",
                "Informe uma quantidade maior que zero.",
                parent=self.dialog_devolucao,
            )
            return

        disponivel = Decimal(str(row.get("quantidade_entregue") or 0))
        if quantidade > disponivel:
            messagebox.showerror(
                "Devolução",
                (
                    "A quantidade informada é maior que a quantidade disponível "
                    f"para devolução ({self._fmt(disponivel)})."
                ),
                parent=self.dialog_devolucao,
            )
            return

        try:
            if self.repository is None:
                self.repository = AlmoxRepository()

            consumo_id = row.get("consumo_material_fabrica_id")
            if consumo_id:
                self.repository.devolver_material_lote_fabrica(
                    consumo_material_fabrica_id=int(consumo_id),
                    quantidade=quantidade,
                    nome_operador=getpass.getuser(),
                    observacao=observacao,
                )
            else:
                self.repository.devolver_material(
                    apontamento_entrega_id=int(row["apontamento_entrega_id"]),
                    quantidade=quantidade,
                    nome_operador=getpass.getuser(),
                    observacao=observacao,
                )

        except Exception as exc:
            messagebox.showerror(
                "Devolução",
                str(exc),
                parent=self.dialog_devolucao,
            )
            return

        if self.dialog_devolucao is not None:
            self.dialog_devolucao.destroy()
            self.dialog_devolucao = None

        messagebox.showinfo(
            "Devolução",
            "Devolução registrada com sucesso.",
        )
        self.refresh()

    def _clear_filters(self) -> None:
        self.setor_filter.set("TODOS")
        self.data_filter.set("TODAS")
        self.estoque_filter.set("TODOS")
        self.pesquisa_filter.delete(0, "end")
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
    
    def abrir_janela_devolucao(self) -> None:
        selecionados = self.tree.selection()

        if not selecionados:
            messagebox.showinfo(
                "Devolução",
                "Selecione uma entrega na tabela.",
            )
            return

        row = self.rows.get(selecionados[0])

        if not row:
            return

        quantidade_disponivel = Decimal(
            str(row.get("quantidade_entregue") or 0)
        )

        if quantidade_disponivel <= 0:
            messagebox.showinfo(
                "Devolução",
                "Esta entrega já foi totalmente devolvida.",
            )
            self.refresh()
            return

        if self.repository is None:
            self.repository = AlmoxRepository()

        JanelaDevolucao(
            parent=self,
            row=row,
            repository=self.repository,
            on_success=self.refresh,
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
