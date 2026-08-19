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

class JanelaDevolucao(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        row: dict,
        repository: AlmoxRepository,
        on_success,
    ):
        super().__init__(parent)

        self.row = row
        self.repository = repository
        self.on_success = on_success

        self.quantidade_disponivel = Decimal(
            str(row.get("quantidade_entregue") or 0)
        )

        self.quantidade_var = ctk.StringVar(value="")

        self.title("Devolver material")
        self.geometry("760x550")
        self.resizable(False, False)

        # Mantém a janela na frente e bloqueia a tela principal.
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.focus_force()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_form()
        self._build_keypad()

        self.protocol(
            "WM_DELETE_WINDOW",
            self._fechar,
        )

    def _build_header(self) -> None:
        material = self.row.get("material") or ""
        dimensao = self.row.get("dimensao") or ""

        header = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )

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
            text="Devolver material",
            font=ctk.CTkFont(
                size=22,
                weight="bold",
            ),
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text=f"{material} | {dimensao}",
            font=ctk.CTkFont(size=16),
        ).pack(anchor="w", pady=(5, 0))

        ctk.CTkLabel(
            header,
            text=(
                "Disponível para devolução: "
                f"{self._fmt(self.quantidade_disponivel)}"
            ),
            text_color="#E6A23C",
            font=ctk.CTkFont(
                size=15,
                weight="bold",
            ),
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
            text="Quantidade devolvida:",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=15,
            pady=(15, 5),
        )

        self.visor = ctk.CTkEntry(
            form,
            textvariable=self.quantidade_var,
            justify="right",
            height=55,
            font=ctk.CTkFont(
                size=26,
                weight="bold",
            ),
        )

        self.visor.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 15),
        )

        ctk.CTkLabel(
            form,
            text="Observação:",
        ).grid(
            row=2,
            column=0,
            sticky="w",
            padx=15,
            pady=(5, 5),
        )

        self.observacao_entry = ctk.CTkTextbox(
            form,
            height=120,
            font=ctk.CTkFont(size=14),
        )

        self.observacao_entry.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 15),
        )

        ctk.CTkButton(
            form,
            text="Confirmar devolução",
            height=45,
            command=self._confirmar,
        ).grid(
            row=4,
            column=0,
            sticky="ew",
            padx=15,
            pady=(5, 8),
        )

        ctk.CTkButton(
            form,
            text="Cancelar",
            height=40,
            fg_color="#555555",
            hover_color="#444444",
            command=self._fechar,
        ).grid(
            row=5,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 15),
        )

    def _build_keypad(self) -> None:
        keypad = ctk.CTkFrame(self)

        keypad.grid(
            row=1,
            column=1,
            sticky="ns",
            padx=(0, 20),
            pady=(0, 20),
        )

        for coluna in range(3):
            keypad.grid_columnconfigure(
                coluna,
                weight=1,
            )

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
                width=70,
                height=62,
                font=ctk.CTkFont(
                    size=21,
                    weight="bold",
                ),
                command=lambda valor=texto: (
                    self._adicionar_tecla(valor)
                ),
            ).grid(
                row=linha,
                column=coluna,
                padx=5,
                pady=5,
            )

        ctk.CTkButton(
            keypad,
            text="⌫",
            height=50,
            command=self._apagar,
        ).grid(
            row=4,
            column=0,
            padx=5,
            pady=5,
            sticky="ew",
        )

        ctk.CTkButton(
            keypad,
            text="Limpar",
            height=50,
            command=self._limpar,
        ).grid(
            row=4,
            column=1,
            padx=5,
            pady=5,
            sticky="ew",
        )

        ctk.CTkButton(
            keypad,
            text="Tudo",
            height=50,
            command=self._preencher_tudo,
        ).grid(
            row=4,
            column=2,
            padx=5,
            pady=5,
            sticky="ew",
        )

    def _adicionar_tecla(self, valor: str) -> None:
        atual = self.quantidade_var.get()

        if valor == ",":
            if "," in atual or "." in atual:
                return

            if not atual:
                atual = "0"

            self.quantidade_var.set(
                atual + ","
            )

            return

        novo_valor = atual + valor

        separador = (
            ","
            if "," in novo_valor
            else "."
            if "." in novo_valor
            else None
        )

        # O banco aceita até três casas decimais.
        if separador:
            decimais = novo_valor.split(
                separador,
                1,
            )[1]

            if len(decimais) > 3:
                return

        # Evita uma sequência desnecessária de zeros.
        if (
            novo_valor.startswith("00")
            and "," not in novo_valor
            and "." not in novo_valor
        ):
            novo_valor = novo_valor.lstrip("0") or "0"

        self.quantidade_var.set(
            novo_valor
        )

    def _apagar(self) -> None:
        atual = self.quantidade_var.get()

        self.quantidade_var.set(
            atual[:-1]
        )

    def _limpar(self) -> None:
        self.quantidade_var.set("")

    def _preencher_tudo(self) -> None:
        self.quantidade_var.set(
            self._fmt(
                self.quantidade_disponivel
            ).replace(".", ",")
        )

    def _confirmar(self) -> None:
        texto = (
            self.quantidade_var.get()
            .strip()
            .replace(",", ".")
        )

        try:
            quantidade = Decimal(texto)

            if quantidade <= 0:
                raise InvalidOperation

        except (InvalidOperation, ValueError):
            messagebox.showerror(
                "Devolução",
                "Informe uma quantidade maior que zero.",
                parent=self,
            )
            return

        if quantidade > self.quantidade_disponivel:
            messagebox.showerror(
                "Devolução",
                (
                    "A quantidade não pode ser maior que "
                    f"{self._fmt(self.quantidade_disponivel)}."
                ),
                parent=self,
            )
            return

        observacao = (
            self.observacao_entry
            .get("1.0", "end")
            .strip()
        )

        confirmado = messagebox.askyesno(
            "Confirmar devolução",
            (
                f"Devolver {self._fmt(quantidade)} do material "
                f"{self.row.get('material', '')}?"
            ),
            parent=self,
        )

        if not confirmado:
            return

        try:
            resultado = self.repository.devolver_material(
                apontamento_entrega_id=int(
                    self.row["apontamento_entrega_id"]
                ),
                quantidade=quantidade,
                nome_operador=getpass.getuser(),
                observacao=observacao,
            )

        except Exception as exc:
            messagebox.showerror(
                "Devolução",
                str(exc),
                parent=self,
            )
            return

        messagebox.showinfo(
            "Devolução",
            (
                "Devolução registrada.\n"
                "Quantidade restante nesta entrega: "
                f"{self._fmt(
                    resultado.get(
                        'quantidade_entregue_restante'
                    )
                )}"
            ),
            parent=self,
        )

        self.grab_release()
        self.destroy()

        self.on_success()

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

        return (
            f"{numero:.3f}"
            .rstrip("0")
            .rstrip(".")
            or "0"
        )
    
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
            key = str(row["apontamento_entrega_id"])
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
