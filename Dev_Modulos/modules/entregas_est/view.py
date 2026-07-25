from __future__ import annotations

import getpass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

import customtkinter as ctk

from core.almox_repository import AlmoxRepository
from modules.entregas_est.fabrica_dialog import JanelaUsoMaterialFabrica


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
        "setor",
        "estoque",
    )

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.repository: AlmoxRepository | None = None
        self.all_rows: list[dict] = []
        self.rows: dict[str, dict] = {}
        self.saldos_fabrica: dict[int, dict] = {}
        self.quantidade_var = ctk.StringVar(value="")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_filters()
        self._build_content()

        self.after(100, self.refresh)

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
            command=self.refresh,
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
            command=lambda _valor: self._apply_filters(),
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
            command=lambda _valor: self._apply_filters(),
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
            command=lambda _valor: self._apply_filters(),
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
            lambda _event: self._apply_filters(),
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
            lambda _event: self._apply_filters(),
        )

        ctk.CTkButton(
            filtros,
            text="Limpar filtros",
            width=110,
            command=self._clear_filters,
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

        ctk.CTkLabel(
            painel,
            text="Item selecionado",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            padx=12,
            pady=(12, 2),
        )

        self.selected_label = ctk.CTkLabel(
            painel,
            text="Nenhum item selecionado",
            anchor="w",
            justify="left",
            wraplength=260,
        )
        self.selected_label.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=12,
            pady=(0, 4),
        )

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
                command=lambda valor=texto: self._keypad_add(valor),
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
            command=self._keypad_backspace,
        ).grid(row=9, column=0, sticky="ew", padx=5, pady=5)

        ctk.CTkButton(
            painel,
            text="Limpar",
            command=self._keypad_clear,
        ).grid(row=9, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkButton(
            painel,
            text="Total",
            command=self._keypad_fill_remaining,
        ).grid(row=9, column=2, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(
            painel,
            text="Operador:",
        ).grid(
            row=10,
            column=0,
            columnspan=3,
            sticky="w",
            padx=12,
            pady=(12, 2),
        )

        self.operator_entry = ctk.CTkEntry(painel)
        self.operator_entry.insert(0, getpass.getuser())
        self.operator_entry.grid(
            row=11,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=12,
            pady=(0, 8),
        )

        ctk.CTkLabel(
            painel,
            text="Observação:",
        ).grid(
            row=12,
            column=0,
            columnspan=3,
            sticky="w",
            padx=12,
            pady=(2, 2),
        )

        self.note_entry = ctk.CTkEntry(
            painel,
            placeholder_text="Opcional",
        )
        self.note_entry.grid(
            row=13,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=12,
            pady=(0, 10),
        )

        ctk.CTkButton(
            painel,
            text="Registrar entrega",
            height=46,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self.register_delivery,
        ).grid(
            row=14,
            column=0,
            columnspan=3,
            sticky="ew",
            padx=12,
            pady=(4, 12),
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
            "setor": "Setor",
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
            "setor": 110,
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
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind(
            "<Shift-MouseWheel>",
            self._rolar_horizontal,
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

    def refresh(self) -> None:
        try:
            if self.repository is None:
                self.repository = AlmoxRepository()

            self.all_rows = self.repository.listar_pendencias_est()
            self.saldos_fabrica.clear()

        except Exception as exc:
            messagebox.showerror("Requisições", str(exc))
            return

        self._update_filter_options()
        self._apply_filters()

    def _update_filter_options(self) -> None:
        setores = self._unique_values("setor")
        estoques = self._unique_values("localizacao")
        datas = sorted(
            {
                self._fmt_date(row.get("data_requisicao"))
                for row in self.all_rows
                if row.get("data_requisicao")
            },
            reverse=True,
        )

        self._set_option_values(
            self.setor_filter,
            ["TODOS", *setores],
            "TODOS",
        )
        self._set_option_values(
            self.estoque_filter,
            ["TODOS", *estoques],
            "TODOS",
        )
        self._set_option_values(
            self.data_filter,
            ["TODAS", *datas],
            "TODAS",
        )

    def _apply_filters(self) -> None:
        setor = self.setor_filter.get().strip()
        data = self.data_filter.get().strip()
        estoque = self.estoque_filter.get().strip()
        material = self.material_filter.get().strip().lower()
        rastreabilidade = self.rastreabilidade_filter.get().strip().lower()

        filtered: list[dict] = []

        for row in self.all_rows:
            if setor != "TODOS" and str(row.get("setor") or "") != setor:
                continue

            if (
                data != "TODAS"
                and self._fmt_date(row.get("data_requisicao")) != data
            ):
                continue

            if (
                estoque != "TODOS"
                and str(row.get("localizacao") or "") != estoque
            ):
                continue

            if material and material not in str(row.get("material") or "").lower():
                continue

            if rastreabilidade and rastreabilidade not in str(
                row.get("rastreabilidade") or ""
            ).lower():
                continue

            filtered.append(row)

        self._fill_table(filtered)
        self.counter_label.configure(text=f"{len(filtered)} item(ns)")

    def _fill_table(self, data: list[dict]) -> None:
        selected_before = self.tree.selection()
        selected_id = selected_before[0] if selected_before else None

        self.rows.clear()

        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for indice, row in enumerate(data):
            key = str(row["item_requisicao_id"])
            self.rows[key] = row
            tag_linha = "linha_par" if indice % 2 == 0 else "linha_impar"

            self.tree.insert(
                "",
                "end",
                iid=key,
                values=(
                    row.get("data_requisicao") or "",
                    self._fmt_hora(row.get("recebido_em_email")),
                    row.get("material") or "",
                    row.get("dimensao") or "",
                    self._fmt(row.get("quantidade_solicitada")),
                    self._fmt(row.get("quantidade_entregue")),
                    self._fmt(row.get("quantidade_restante")),
                    row.get("rastreabilidade") or "",
                    row.get("setor") or "",
                    row.get("localizacao") or "",
                ),
                tags=(tag_linha,),
            )

        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id)
            self.tree.focus(selected_id)
            self.tree.see(selected_id)
            self._on_select()

        elif not data:
            self.selected_label.configure(text="Nenhum item encontrado")
            self.fabrica_label.grid_remove()
            self.quantidade_var.set("")

    def _on_select(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return

        row = self.rows.get(selected[0])
        if row is None:
            return

        self.selected_label.configure(
            text=(
                f"{row.get('material', '')} | {row.get('dimensao', '')}\n"
                f"Rastreabilidade: {row.get('rastreabilidade', '')}\n"
                f"Falta: {self._fmt(row.get('quantidade_restante'))}"
            )
        )
        self.quantidade_var.set("")
        self._atualizar_saldo_fabrica(row)

    def _atualizar_saldo_fabrica(self, row: dict) -> None:
        try:
            consulta = self._consultar_material_fabrica(row, forcar=False)
            disponivel = Decimal(
                str(consulta.get("quantidade_disponivel") or 0)
            )
        except Exception:
            self.fabrica_label.grid_remove()
            return

        if disponivel > 0:
            self.fabrica_label.configure(
                text=f"Em fábrica: {self._fmt(disponivel)} peça(s)"
            )
            self.fabrica_label.grid()
        else:
            self.fabrica_label.grid_remove()

    def _consultar_material_fabrica(
        self,
        row: dict,
        forcar: bool,
    ) -> dict:
        if self.repository is None:
            self.repository = AlmoxRepository()

        item_id = int(row["item_requisicao_id"])

        if not forcar and item_id in self.saldos_fabrica:
            return self.saldos_fabrica[item_id]

        consulta = self.repository.consultar_material_fabrica(
            item_requisicao_id=item_id,
        )
        self.saldos_fabrica[item_id] = consulta
        return consulta

    def _keypad_add(self, value: str) -> None:
        atual = self.quantidade_var.get()

        if value == ",":
            if "," in atual or "." in atual:
                return

            self.quantidade_var.set((atual or "0") + ",")
            return

        novo = f"{atual}{value}"

        if "," in novo:
            casas_decimais = len(novo.split(",", 1)[1])
            if casas_decimais > 3:
                return

        if novo.startswith("0") and "," not in novo:
            novo = novo.lstrip("0") or "0"

        self.quantidade_var.set(novo)

    def _keypad_backspace(self) -> None:
        self.quantidade_var.set(self.quantidade_var.get()[:-1])

    def _keypad_clear(self) -> None:
        self.quantidade_var.set("")

    def _keypad_fill_remaining(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(
                "Entrega de MP",
                "Selecione um item da lista.",
            )
            return

        row = self.rows.get(selected[0])
        if row is None:
            return

        self.quantidade_var.set(
            self._fmt(row.get("quantidade_restante")).replace(".", ",")
        )

    def _clear_filters(self) -> None:
        self.setor_filter.set("TODOS")
        self.data_filter.set("TODAS")
        self.estoque_filter.set("TODOS")
        self.material_filter.delete(0, "end")
        self.rastreabilidade_filter.delete(0, "end")
        self._apply_filters()

    def register_delivery(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(
                "Entrega de MP",
                "Selecione um item da lista.",
            )
            return

        nome_operador = self.operator_entry.get().strip()
        if not nome_operador:
            messagebox.showinfo(
                "Entrega de MP",
                "Informe o nome do operador.",
            )
            return

        quantidade = self._ler_quantidade_principal()
        if quantidade is None:
            return

        row = self.rows.get(selected[0])
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
                parent=self,
                repository=self.repository,
                item=row,
                consulta=consulta,
                quantidade_informada=quantidade,
                nome_operador=nome_operador,
                observacao=self.note_entry.get().strip() or None,
                on_success=self._apos_registro,
            )
            return

        self._registrar_entrega_direta(
            row=row,
            quantidade=quantidade,
            nome_operador=nome_operador,
        )

    def _registrar_entrega_direta(
        self,
        row: dict,
        quantidade: Decimal,
        nome_operador: str,
    ) -> None:
        try:
            result = self.repository.registrar_entrega(
                item_requisicao_id=int(row["item_requisicao_id"]),
                quantidade=quantidade,
                nome_operador=nome_operador,
                observacao=self.note_entry.get().strip() or None,
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
        self.quantidade_var.set("")
        self.note_entry.delete(0, "end")
        self.fabrica_label.grid_remove()
        self.refresh()

    def _ler_quantidade_principal(self) -> Decimal | None:
        texto_quantidade = self.quantidade_var.get().strip().replace(",", ".")

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

    def _rolar_horizontal(self, event) -> str:
        direcao = -1 if event.delta > 0 else 1
        self.tree.xview_scroll(direcao, "units")
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
