from __future__ import annotations

import getpass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk
from typing import Callable

import customtkinter as ctk

from core.almox_repository import AlmoxRepository


class DevolucaoDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        row: dict,
        formatar_quantidade: Callable[[object], str],
        confirmar: Callable[[str, str], None],
    ) -> None:
        super().__init__(parent)

        self._confirmar = confirmar
        self._formatar_quantidade = formatar_quantidade

        self.title("Devolver material")
        self.geometry("480x350")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Devolução de material",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 12))

        material = str(row.get("material") or "")
        dimensao = str(row.get("dimensao") or "")
        disponivel = formatar_quantidade(row.get("quantidade_entregue"))

        ctk.CTkLabel(
            self,
            text=f"{material} | {dimensao}",
            anchor="w",
            justify="left",
            wraplength=430,
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 6))

        ctk.CTkLabel(
            self,
            text=f"Quantidade disponível para devolução: {disponivel}",
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))

        ctk.CTkLabel(self, text="Quantidade a devolver:").grid(
            row=3, column=0, sticky="w", padx=20, pady=(0, 4)
        )
        self.quantidade_entry = ctk.CTkEntry(
            self,
            placeholder_text="Ex.: 1 ou 0,500",
            height=38,
        )
        self.quantidade_entry.grid(row=4, column=0, sticky="ew", padx=20)

        ctk.CTkLabel(self, text="Observação (opcional):").grid(
            row=5, column=0, sticky="w", padx=20, pady=(16, 4)
        )
        self.observacao_entry = ctk.CTkEntry(
            self,
            placeholder_text="Motivo ou comentário da devolução",
            height=38,
        )
        self.observacao_entry.grid(row=6, column=0, sticky="ew", padx=20)

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.grid(row=7, column=0, sticky="e", padx=20, pady=24)

        ctk.CTkButton(
            botoes,
            text="Cancelar",
            fg_color="gray45",
            hover_color="gray35",
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            botoes,
            text="Confirmar devolução",
            command=self._enviar,
        ).pack(side="left")

        self.after(100, self.quantidade_entry.focus_set)
        self.bind("<Return>", lambda _event: self._enviar())
        self.bind("<Escape>", lambda _event: self.destroy())

    def _enviar(self) -> None:
        quantidade = self.quantidade_entry.get().strip()
        observacao = self.observacao_entry.get().strip()
        self._confirmar(quantidade, observacao)


class VisaoAdministrativaView(ctk.CTkFrame):
    COLUMNS = (
        "data_requisicao",
        "hora_requisicao",
        "data_entrega",
        "hora_entrega",
        "material",
        "dimensao",
        "solicitado",
        "entregue",
        "rastreabilidade",
        "estoque",
        "setor",
        "observacao",
        "operador",
    )

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.repository: AlmoxRepository | None = None
        self.all_rows: list[dict] = []
        self.rows: dict[str, dict] = {}
        self.dialog_devolucao: DevolucaoDialog | None = None

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
            command=self._abrir_devolucao,
        ).pack(side="right")

    def _build_filters(self) -> None:
        filtros = ctk.CTkFrame(self)
        filtros.grid(row=1, column=0, sticky="ew", padx=20, pady=8)

        ctk.CTkLabel(filtros, text="Setor:").pack(
            side="left", padx=(10, 4), pady=10
        )
        self.setor_filter = ctk.CTkOptionMenu(
            filtros,
            width=120,
            values=["TODOS"],
            command=lambda _valor: self._apply_filters(),
        )
        self.setor_filter.set("TODOS")
        self.setor_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Data entrega:").pack(
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
            width=110,
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
            width=145,
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
            width=145,
            placeholder_text="Buscar",
        )
        self.rastreabilidade_filter.pack(side="left", padx=(0, 8), pady=10)
        self.rastreabilidade_filter.bind(
            "<KeyRelease>", lambda _event: self._apply_filters()
        )

        ctk.CTkButton(
            filtros,
            text="Limpar filtros",
            width=110,
            command=self._clear_filters,
        ).pack(side="left", padx=8, pady=10)

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
            "data_requisicao": "Dt Req.",
            "hora_requisicao": "Hr Req.",
            "data_entrega": "Dt Entr.",
            "hora_entrega": "Hr Entr.",
            "material": "Material",
            "dimensao": "Dimensão",
            "solicitado": "Solicitado",
            "entregue": "Entregue",
            "rastreabilidade": "Rastreabilidade",
            "estoque": "Estoque",
            "setor": "Setor",
            "observacao": "Observação",
            "operador": "Operador",
        }
        widths = {
            "data_requisicao": 100,
            "hora_requisicao": 85,
            "data_entrega": 100,
            "hora_entrega": 85,
            "material": 280,
            "dimensao": 120,
            "solicitado": 110,
            "entregue": 110,
            "rastreabilidade": 180,
            "estoque": 110,
            "setor": 110,
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
        self.tree.bind("<Double-1>", lambda _event: self._abrir_devolucao())

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
        setores = self._unique_values("setor")
        estoques = self._unique_values("localizacao")
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
        material = self.material_filter.get().strip().lower()
        rastreabilidade = self.rastreabilidade_filter.get().strip().lower()

        filtrados: list[dict] = []

        for row in self.all_rows:
            if setor != "TODOS" and str(row.get("setor") or "") != setor:
                continue

            if (
                data_entrega != "TODAS"
                and self._fmt_data(row.get("entregue_em")) != data_entrega
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

            filtrados.append(row)

        self._fill_table(filtrados)
        self.counter_label.configure(text=f"{len(filtrados)} entrega(s)")

    def _fill_table(self, data: list[dict]) -> None:
        self.rows.clear()

        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for indice, row in enumerate(data):
            key = str(row["apontamento_entrega_id"])
            self.rows[key] = row

            tag = "linha_par" if indice % 2 == 0 else "linha_impar"

            self.tree.insert(
                "",
                "end",
                iid=key,
                values=(
                    self._fmt_data(row.get("data_requisicao")),
                    self._fmt_hora(row.get("recebido_em_email")),
                    self._fmt_data(row.get("entregue_em")),
                    self._fmt_hora(row.get("entregue_em")),
                    row.get("material") or "",
                    row.get("dimensao") or "",
                    self._fmt(row.get("quantidade_solicitada")),
                    self._fmt(row.get("quantidade_entregue")),
                    row.get("rastreabilidade") or "",
                    row.get("localizacao") or "",
                    row.get("setor") or "",
                    row.get("observacao") or "",
                    row.get("nome_operador") or "",
                ),
                tags=(tag,),
            )

    def _abrir_devolucao(self) -> None:
        selecionado = self.tree.selection()
        if not selecionado:
            messagebox.showinfo(
                "Devolução",
                "Selecione uma entrega na tabela.",
            )
            return

        row = self.rows.get(selecionado[0])
        if row is None:
            messagebox.showerror("Devolução", "A entrega selecionada não foi encontrada.")
            return

        disponivel = Decimal(str(row.get("quantidade_entregue") or 0))
        if disponivel <= 0:
            messagebox.showinfo(
                "Devolução",
                "Esta entrega não possui quantidade disponível para devolução.",
            )
            return

        if self.dialog_devolucao is not None and self.dialog_devolucao.winfo_exists():
            self.dialog_devolucao.focus_force()
            return

        self.dialog_devolucao = DevolucaoDialog(
            self,
            row,
            self._fmt,
            lambda quantidade, observacao: self._confirmar_devolucao(
                row,
                quantidade,
                observacao,
            ),
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
        self.material_filter.delete(0, "end")
        self.rastreabilidade_filter.delete(0, "end")
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
