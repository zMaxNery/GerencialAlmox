from __future__ import annotations

import getpass
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

import customtkinter as ctk

from core.almox_repository import AlmoxRepository


class EntregasEstView(ctk.CTkFrame):
    COLUMNS = (
        "data",
        "tipo",
        "material",
        "dimensao",
        "solicitado",
        "entregue",
        "falta",
        "rastreabilidade",
        "peso_mat",
        "peso_req",
        "maquina",
        "localizacao",
        "setor",
    )

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)
        self.repository: AlmoxRepository | None = None
        self.rows: dict[str, dict] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_form()
        self._build_table()
        self.after(100, self.refresh)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))

        ctk.CTkLabel(
            header,
            text="Requisições pendentes",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(header, text="Atualizar", command=self.refresh).pack(side="right")

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="ew", padx=20, pady=8)
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(form, text="Item selecionado:").grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        self.selected_label = ctk.CTkLabel(form, text="Nenhum")
        self.selected_label.grid(row=0, column=1, columnspan=5, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(form, text="Quantidade entregue:").grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )
        self.quantity_entry = ctk.CTkEntry(form, width=150, placeholder_text="Ex.: 1")
        self.quantity_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(form, text="Operador:").grid(
            row=1, column=2, padx=10, pady=10, sticky="w"
        )
        self.operator_entry = ctk.CTkEntry(form, width=180)
        self.operator_entry.insert(0, getpass.getuser())
        self.operator_entry.grid(row=1, column=3, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(form, text="Observação:").grid(
            row=1, column=4, padx=10, pady=10, sticky="w"
        )
        self.note_entry = ctk.CTkEntry(form, width=250)
        self.note_entry.grid(row=1, column=5, padx=10, pady=10, sticky="ew")

        ctk.CTkButton(
            form,
            text="Registrar entrega",
            command=self.register_delivery,
        ).grid(row=1, column=6, padx=10, pady=10)

    def _build_table(self) -> None:
        container = ctk.CTkFrame(self)
        container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(8, 20))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(container, columns=self.COLUMNS, show="headings")

        labels = {
            "data": "Data",
            "tipo": "Tipo",
            "material": "Material",
            "dimensao": "Dimensão",
            "solicitado": "Solicitado",
            "entregue": "Entregue",
            "falta": "Falta",
            "rastreabilidade": "Rastreabilidade",
            "peso_mat": "Peso Material",
            "peso_req": "Peso Requisitado",
            "maquina": "Máquina",
            "localizacao": "Localização",
            "setor": "Setor",
        }
        widths = {
            "data": 90,
            "tipo": 70,
            "material": 200,
            "dimensao": 100,
            "solicitado": 80,
            "entregue": 80,
            "falta": 80,
            "rastreabilidade": 150,
            "peso_mat": 110,
            "peso_req": 130,
            "maquina": 200,
            "localizacao": 90,
            "setor": 900,
        }

        for column in self.COLUMNS:
            self.tree.heading(column, text=labels[column])
            self.tree.column(column, width=widths[column], anchor="center")

        self.tree.column("material", anchor="w")
        self.tree.column("dimensao", anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

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
            data = self.repository.listar_pendencias_est()
        except Exception as exc:
            messagebox.showerror("Requisições", str(exc))
            return

        self.rows.clear()
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for row in data:
            key = str(row["request_item_id"])
            self.rows[key] = row
            self.tree.insert(
                "",
                "end",
                iid=key,
                values=(
                    row.get("request_date") or "",
                    row.get("material_type") or "",
                    row.get("material") or "",
                    row.get("dimension") or "",
                    self._fmt(row.get("quantity_requested")),
                    self._fmt(row.get("quantity_delivered")),
                    self._fmt(row.get("quantity_remaining")),
                    row.get("traceability") or "",
                    row.get("material_weight_kg") or "",
                    row.get("requested_weight_kg") or "",
                    row.get("machine") or "",
                    row.get("location") or "",
                    row.get("sector") or "",
                ),
            )

        self.selected_label.configure(text=f"{len(data)} item(ns) pendente(s)")

    def _on_select(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        row = self.rows[selected[0]]
        self.selected_label.configure(
            text=(
                f"{row.get('material', '')} | {row.get('dimension', '')} | "
                f"falta {self._fmt(row.get('quantity_remaining'))}"
            )
        )
        self.quantity_entry.delete(0, "end")
        self.quantity_entry.insert(0, self._fmt(row.get("quantity_remaining")))

    def register_delivery(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Entrega de MP", "Selecione um item da lista.")
            return

        operator_name = self.operator_entry.get().strip()
        if not operator_name:
            messagebox.showinfo("Entrega de MP", "Informe o nome do operador.")
            return

        try:
            quantity = Decimal(self.quantity_entry.get().strip().replace(",", "."))
            if quantity <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            messagebox.showerror("Entrega de MP", "Informe uma quantidade maior que zero.")
            return

        row = self.rows[selected[0]]
        try:
            result = self.repository.registrar_entrega(
                request_item_id=int(row["request_item_id"]),
                quantity=quantity,
                operator_name=operator_name,
                note=self.note_entry.get(),
            )
        except Exception as exc:
            messagebox.showerror("Entrega de MP", str(exc))
            self.refresh()
            return

        messagebox.showinfo(
            "Entrega de MP",
            "Entrega registrada. "
            f"Quantidade restante: {self._fmt(result.get('remaining_quantity'))}",
        )
        self.quantity_entry.delete(0, "end")
        self.note_entry.delete(0, "end")
        self.refresh()

    @staticmethod
    def _fmt(value) -> str:
        if value in (None, ""):
            return "0"
        number = Decimal(str(value))
        text = f"{number:.3f}".rstrip("0").rstrip(".")
        return text or "0"
