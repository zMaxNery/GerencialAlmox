from __future__ import annotations

import getpass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

import customtkinter as ctk

from core.almox_repository import AlmoxRepository


class JanelaAjusteMaterialFabrica(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        repository: AlmoxRepository,
        row: dict,
        on_success,
    ) -> None:
        super().__init__(parent)

        self.repository = repository
        self.row = row
        self.on_success = on_success
        self.quantidade_var = ctk.StringVar(
            value=self._fmt(row.get("quantidade_disponivel")).replace(".", ",")
        )

        self.title("Ajustar material em fábrica")
        self.geometry("700x600")
        self.minsize(620, 560)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.focus_force()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_form()
        self._build_keypad()

        self.protocol("WM_DELETE_WINDOW", self._fechar)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=20,
            pady=(20, 10),
        )

        ctk.CTkLabel(
            header,
            text="Ajustar quantidade disponível",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=(
                f"{self.row.get('material') or ''} × "
                f"{self.row.get('rastreabilidade') or ''}"
            ),
            font=ctk.CTkFont(size=16),
        ).pack(anchor="w", pady=(5, 0))

        ctk.CTkLabel(
            header,
            text=(
                "O ajuste altera somente o saldo visual deste lote. "
                "Não cria entrega, devolução ou consumo."
            ),
            text_color="#E6A23C",
            wraplength=600,
            justify="left",
        ).pack(anchor="w", pady=(5, 0))

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self)
        form.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(20, 10),
            pady=(0, 20),
        )
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            form,
            text="Nova quantidade disponível:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        ctk.CTkEntry(
            form,
            textvariable=self.quantidade_var,
            justify="right",
            height=58,
            font=ctk.CTkFont(size=27, weight="bold"),
        ).grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 12))

        ctk.CTkLabel(form, text="Operador:").grid(
            row=2,
            column=0,
            sticky="w",
            padx=15,
            pady=(5, 4),
        )

        self.operador_entry = ctk.CTkEntry(form)
        self.operador_entry.insert(0, getpass.getuser())
        self.operador_entry.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 10),
        )

        ctk.CTkLabel(form, text="Observação:").grid(
            row=4,
            column=0,
            sticky="w",
            padx=15,
            pady=(5, 4),
        )

        self.observacao_entry = ctk.CTkTextbox(form, height=100)
        self.observacao_entry.grid(
            row=5,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 12),
        )

        ctk.CTkButton(
            form,
            text="Confirmar ajuste",
            height=45,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._confirmar,
        ).grid(row=6, column=0, sticky="ew", padx=15, pady=(6, 8))

        ctk.CTkButton(
            form,
            text="Cancelar",
            height=40,
            fg_color="#555555",
            hover_color="#444444",
            command=self._fechar,
        ).grid(row=7, column=0, sticky="ew", padx=15, pady=(0, 15))

    def _build_keypad(self) -> None:
        keypad = ctk.CTkFrame(self)
        keypad.grid(
            row=1,
            column=1,
            sticky="ns",
            padx=(0, 20),
            pady=(0, 20),
        )
        keypad.grid_columnconfigure((0, 1, 2), weight=1)

        teclas = (
            ("7", 0, 0),
            ("8", 0, 1),
            ("9", 0, 2),
            ("4", 1, 0),
            ("5", 1, 1),
            ("6", 1, 2),
            ("1", 2, 0),
            ("2", 2, 1),
            ("3", 2, 2),
            ("0", 3, 0),
            ("00", 3, 1),
            (",", 3, 2),
        )

        for texto, linha, coluna in teclas:
            ctk.CTkButton(
                keypad,
                text=texto,
                width=72,
                height=62,
                font=ctk.CTkFont(size=21, weight="bold"),
                command=lambda valor=texto: self._adicionar_tecla(valor),
            ).grid(row=linha, column=coluna, padx=5, pady=5)

        ctk.CTkButton(
            keypad,
            text="⌫",
            height=50,
            command=self._apagar,
        ).grid(row=4, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            keypad,
            text="Limpar",
            height=50,
            command=lambda: self.quantidade_var.set(""),
        ).grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkButton(
            keypad,
            text="Zerar",
            height=50,
            fg_color="#A94442",
            hover_color="#8A3836",
            command=lambda: self.quantidade_var.set("0"),
        ).grid(row=4, column=2, padx=5, pady=5, sticky="ew")

    def _confirmar(self) -> None:
        texto = self.quantidade_var.get().strip().replace(",", ".")
        try:
            nova_quantidade = Decimal(texto)
            if nova_quantidade < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            messagebox.showerror(
                "Materiais em fábrica",
                "Informe uma quantidade igual ou maior que zero.",
                parent=self,
            )
            return

        operador = self.operador_entry.get().strip()
        if not operador:
            messagebox.showinfo(
                "Materiais em fábrica",
                "Informe o nome do operador.",
                parent=self,
            )
            return

        observacao = self.observacao_entry.get("1.0", "end").strip()
        quantidade_anterior = Decimal(
            str(self.row.get("quantidade_disponivel") or 0)
        )

        confirmar = messagebox.askyesno(
            "Confirmar ajuste",
            (
                f"Alterar o saldo de {self._fmt(quantidade_anterior)} "
                f"para {self._fmt(nova_quantidade)}?\n\n"
                "Se o novo saldo for zero, o lote deixará de aparecer na tela."
            ),
            parent=self,
        )
        if not confirmar:
            return

        try:
            self.repository.ajustar_material_fabrica(
                lote_material_fabrica_id=int(
                    self.row["lote_material_fabrica_id"]
                ),
                nova_quantidade=nova_quantidade,
                nome_operador=operador,
                observacao=observacao,
            )
        except Exception as exc:
            messagebox.showerror("Materiais em fábrica", str(exc), parent=self)
            return

        messagebox.showinfo(
            "Materiais em fábrica",
            "Quantidade ajustada com sucesso.",
            parent=self,
        )
        self._fechar()
        self.on_success()

    def _adicionar_tecla(self, valor: str) -> None:
        atual = self.quantidade_var.get()

        if valor == ",":
            if "," in atual or "." in atual:
                return
            self.quantidade_var.set((atual or "0") + ",")
            return

        if atual == "0" and valor not in ("00",):
            atual = ""

        novo = atual + valor
        separador = "," if "," in novo else "." if "." in novo else None
        if separador and len(novo.split(separador, 1)[1]) > 3:
            return

        self.quantidade_var.set(novo)

    def _apagar(self) -> None:
        self.quantidade_var.set(self.quantidade_var.get()[:-1])

    def _fechar(self) -> None:
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    @staticmethod
    def _fmt(value) -> str:
        if value in (None, ""):
            return "0"
        numero = Decimal(str(value))
        return f"{numero:.3f}".rstrip("0").rstrip(".") or "0"


class MateriaisFabricaView(ctk.CTkFrame):
    COLUMNS = (
        "data_entrega",
        "hora_entrega",
        "material",
        "rastreabilidade",
        "quantidade",
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
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(20, 8),
        )

        ctk.CTkLabel(
            header,
            text="Materiais em fábrica",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Atualizar",
            command=self.refresh,
        ).pack(side="right")

        ctk.CTkButton(
            header,
            text="Ajustar quantidade",
            command=self.abrir_ajuste,
        ).pack(side="right", padx=(0, 10))

    def _build_filters(self) -> None:
        filtros = ctk.CTkFrame(self)
        filtros.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=8,
        )

        ctk.CTkLabel(filtros, text="Data:").pack(
            side="left",
            padx=(10, 4),
            pady=10,
        )
        self.data_filter = ctk.CTkOptionMenu(
            filtros,
            width=125,
            values=["TODAS"],
            command=lambda _valor: self._apply_filters(),
        )
        self.data_filter.set("TODAS")
        self.data_filter.pack(side="left", padx=(0, 8), pady=10)

        ctk.CTkLabel(filtros, text="Material:").pack(
            side="left",
            padx=(4, 4),
            pady=10,
        )
        self.material_filter = ctk.CTkEntry(
            filtros,
            width=180,
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
            width=170,
            placeholder_text="Buscar",
        )
        self.rastreabilidade_filter.pack(
            side="left",
            padx=(0, 8),
            pady=10,
        )
        self.rastreabilidade_filter.bind(
            "<KeyRelease>",
            lambda _event: self._apply_filters(),
        )

        ctk.CTkLabel(filtros, text="Operador:").pack(
            side="left",
            padx=(4, 4),
            pady=10,
        )
        self.operador_filter = ctk.CTkEntry(
            filtros,
            width=150,
            placeholder_text="Buscar",
        )
        self.operador_filter.pack(side="left", padx=(0, 8), pady=10)
        self.operador_filter.bind(
            "<KeyRelease>",
            lambda _event: self._apply_filters(),
        )

        ctk.CTkButton(
            filtros,
            text="Limpar filtros",
            width=110,
            command=self._clear_filters,
        ).pack(side="left", padx=8, pady=10)

        self.counter_label = ctk.CTkLabel(filtros, text="0 lote(s)")
        self.counter_label.pack(side="right", padx=10, pady=10)

    def _build_table(self) -> None:
        style = ttk.Style()
        style.configure(
            "MateriaisFabrica.Treeview",
            font=("Arial", 12),
            rowheight=36,
        )
        style.configure(
            "MateriaisFabrica.Treeview.Heading",
            font=("Arial", 14, "bold"),
        )

        container = ctk.CTkFrame(self)
        container.grid(
            row=2,
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
            style="MateriaisFabrica.Treeview",
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
            "data_entrega": "Dt Entr",
            "hora_entrega": "Hr Entr",
            "material": "Material",
            "rastreabilidade": "Rastreabilidade",
            "quantidade": "Quantidade",
            "operador": "Operador",
        }
        widths = {
            "data_entrega": 100,
            "hora_entrega": 85,
            "material": 430,
            "rastreabilidade": 240,
            "quantidade": 140,
            "operador": 200,
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
        self.tree.column("rastreabilidade", anchor="w")
        self.tree.column("operador", anchor="w")
        self.tree.bind("<Double-1>", lambda _event: self.abrir_ajuste())

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
            self.all_rows = self.repository.listar_materiais_fabrica()
        except Exception as exc:
            messagebox.showerror("Materiais em fábrica", str(exc))
            return

        self._update_filter_options()
        self._apply_filters()

    def abrir_ajuste(self) -> None:
        selecionados = self.tree.selection()
        if not selecionados:
            messagebox.showinfo(
                "Materiais em fábrica",
                "Selecione um lote na tabela.",
            )
            return

        row = self.rows.get(selecionados[0])
        if not row:
            self.refresh()
            return

        if self.repository is None:
            self.repository = AlmoxRepository()

        JanelaAjusteMaterialFabrica(
            parent=self,
            repository=self.repository,
            row=row,
            on_success=self.refresh,
        )

    def _update_filter_options(self) -> None:
        datas = sorted(
            {
                self._fmt_data(row.get("recebido_em"))
                for row in self.all_rows
                if row.get("recebido_em")
            },
            reverse=True,
        )
        values = ["TODAS", *datas]
        atual = self.data_filter.get()
        self.data_filter.configure(values=values)
        if atual not in values:
            self.data_filter.set("TODAS")

    def _apply_filters(self) -> None:
        data = self.data_filter.get().strip()
        material = self.material_filter.get().strip().lower()
        rastreabilidade = self.rastreabilidade_filter.get().strip().lower()
        operador = self.operador_filter.get().strip().lower()

        filtered: list[dict] = []
        for row in self.all_rows:
            quantidade = Decimal(str(row.get("quantidade_disponivel") or 0))
            if quantidade <= 0:
                continue

            if data != "TODAS" and self._fmt_data(row.get("recebido_em")) != data:
                continue

            if material and material not in str(row.get("material") or "").lower():
                continue

            if rastreabilidade and rastreabilidade not in str(
                row.get("rastreabilidade") or ""
            ).lower():
                continue

            if operador and operador not in str(
                row.get("nome_operador") or ""
            ).lower():
                continue

            filtered.append(row)

        self._fill_table(filtered)
        self.counter_label.configure(text=f"{len(filtered)} lote(s)")

    def _fill_table(self, data: list[dict]) -> None:
        self.rows.clear()
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for indice, row in enumerate(data):
            key = str(row["lote_material_fabrica_id"])
            self.rows[key] = row
            tag = "linha_par" if indice % 2 == 0 else "linha_impar"

            self.tree.insert(
                "",
                "end",
                iid=key,
                values=(
                    self._fmt_data(row.get("recebido_em")),
                    self._fmt_hora(row.get("recebido_em")),
                    row.get("material") or "",
                    row.get("rastreabilidade") or "",
                    self._fmt(row.get("quantidade_disponivel")),
                    row.get("nome_operador") or "",
                ),
                tags=(tag,),
            )

    def _clear_filters(self) -> None:
        self.data_filter.set("TODAS")
        self.material_filter.delete(0, "end")
        self.rastreabilidade_filter.delete(0, "end")
        self.operador_filter.delete(0, "end")
        self._apply_filters()

    @staticmethod
    def _parse_datetime(value) -> datetime | None:
        if not value:
            return None
        try:
            texto = str(value).strip().replace("Z", "+00:00")
            data_hora = datetime.fromisoformat(texto)
            if data_hora.tzinfo is not None:
                data_hora = data_hora.astimezone()
            return data_hora
        except (TypeError, ValueError):
            return None

    @classmethod
    def _fmt_data(cls, value) -> str:
        data_hora = cls._parse_datetime(value)
        return data_hora.strftime("%d/%m/%Y") if data_hora else ""

    @classmethod
    def _fmt_hora(cls, value) -> str:
        data_hora = cls._parse_datetime(value)
        return data_hora.strftime("%H:%M") if data_hora else ""

    @staticmethod
    def _fmt(value) -> str:
        if value in (None, ""):
            return "0"
        numero = Decimal(str(value))
        return f"{numero:.3f}".rstrip("0").rstrip(".") or "0"
