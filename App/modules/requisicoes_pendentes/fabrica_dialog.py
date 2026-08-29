from __future__ import annotations

from decimal import Decimal, InvalidOperation
from tkinter import messagebox

import customtkinter as ctk

from modules._shared.almox_repository import AlmoxRepository


class JanelaUsoMaterialFabrica(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        repository: AlmoxRepository,
        item: dict,
        consulta: dict,
        quantidade_informada: Decimal,
        nome_operador: str,
        on_success,
        observacao: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.repository = repository
        self.item = item
        self.consulta = consulta
        self.quantidade_informada = Decimal(str(quantidade_informada))
        self.nome_operador = nome_operador
        self.observacao = observacao
        self.on_success = on_success

        self.lote_vars: dict[int, ctk.StringVar] = {}
        self.lote_entries: dict[int, ctk.CTkEntry] = {}
        self.lotes = list(consulta.get("lotes") or [])
        self.lote_ativo: int | None = None

        self.title("Usar material em fábrica")
        # self.geometry("700x700")
        self.after(0, lambda: self.state("zoomed"))
        # self.minsize(980, 660)
        # self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.focus_force()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._fechar)

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=22, pady=(18, 8))
        ctk.CTkLabel(
            header,
            text="Estoque da fábrica",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text=(
                f"Material: {self.item.get('material') or ''}   |   "
                f"Rastreabilidade da requisição: {self.item.get('rastreabilidade') or '-'}\n"
                f"Qtd entrega informada: {self._fmt(self.quantidade_informada)}   |   "
                f"Total em fábrica deste material: {self._fmt(self.consulta.get('quantidade_disponivel'))}"
            ),
            justify="left",
            font=ctk.CTkFont(size=16),
        ).pack(anchor="w", pady=(6, 0))

        area = ctk.CTkFrame(self, fg_color="transparent")
        area.grid(row=1, column=0, sticky="nsew", padx=22, pady=8)
        area.grid_columnconfigure(0, weight=1)
        area.grid_columnconfigure(1, weight=0)
        area.grid_rowconfigure(0, weight=1)

        self._build_lotes(area)
        self._build_keypad(area)
        self._build_footer()

    def _build_lotes(self, parent) -> None:
        corpo = ctk.CTkScrollableFrame(parent)
        corpo.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        corpo.grid_columnconfigure(0, weight=1)

        titulos = ("Rastreabilidade", "Disponível", "Usar")
        for col, titulo in enumerate(titulos):
            ctk.CTkLabel(
                corpo,
                text=titulo,
                font=ctk.CTkFont(size=16, weight="bold"),
            ).grid(row=0, column=col, sticky="ew", padx=10, pady=(8, 10))

        for linha, lote in enumerate(self.lotes, start=1):
            lote_id = int(lote["lote_id"])
            var = ctk.StringVar(value="")
            self.lote_vars[lote_id] = var

            ctk.CTkLabel(
                corpo,
                text=str(lote.get("rastreabilidade") or "SEM RASTREABILIDADE"),
                anchor="w",
                font=ctk.CTkFont(size=17, weight="bold"),
            ).grid(row=linha, column=0, sticky="ew", padx=10, pady=7)

            ctk.CTkLabel(
                corpo,
                text=self._fmt(lote.get("quantidade_disponivel")),
                font=ctk.CTkFont(size=17),
            ).grid(row=linha, column=1, sticky="ew", padx=10, pady=7)

            entry = ctk.CTkEntry(
                corpo,
                textvariable=var,
                width=155,
                height=50,
                justify="right",
                font=ctk.CTkFont(size=22, weight="bold"),
            )
            entry.grid(row=linha, column=2, sticky="e", padx=10, pady=7)
            entry.bind("<FocusIn>", lambda _e, lid=lote_id: self._selecionar_lote(lid))
            entry.bind("<Button-1>", lambda _e, lid=lote_id: self._selecionar_lote(lid))
            self.lote_entries[lote_id] = entry

        for var in self.lote_vars.values():
            var.trace_add("write", lambda *_: self._atualizar_resumo())

        if self.lotes:
            primeiro_id = int(self.lotes[0]["lote_id"])
            self.after(100, lambda: self._selecionar_lote(primeiro_id))

    def _build_keypad(self, parent) -> None:
        painel = ctk.CTkFrame(parent, width=315)
        painel.grid(row=0, column=1, sticky="ns")
        painel.grid_propagate(False)
        painel.grid_columnconfigure((0, 1, 2), weight=1)

        self.lote_ativo_label = ctk.CTkLabel(
            painel,
            text="Selecione um lote",
            wraplength=285,
            justify="center",
            text_color="#2F80ED",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.lote_ativo_label.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=(2, 10))

        teclas = (
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2),
            ("4", 3, 0), ("5", 3, 1), ("6", 3, 2),
            ("1", 4, 0), ("2", 4, 1), ("3", 4, 2),
            ("0", 5, 0), ("00", 5, 1), (",", 5, 2),
        )
        for texto, linha, coluna in teclas:
            ctk.CTkButton(
                painel,
                text=texto,
                height=66,
                font=ctk.CTkFont(size=24, weight="bold"),
                command=lambda valor=texto: self._tecla(valor),
            ).grid(row=linha, column=coluna, sticky="nsew", padx=5, pady=5)

        ctk.CTkButton(
            painel,
            text="⌫",
            height=54,
            font=ctk.CTkFont(size=20, weight="bold"),
            command=self._apagar,
        ).grid(row=6, column=0, sticky="ew", padx=5, pady=5)
        ctk.CTkButton(
            painel,
            text="Limpar",
            height=54,
            command=self._limpar_lote_ativo,
        ).grid(row=6, column=1, sticky="ew", padx=5, pady=5)
        ctk.CTkButton(
            painel,
            text="Máx.",
            height=54,
            command=self._maximo_lote_ativo,
        ).grid(row=6, column=2, sticky="ew", padx=5, pady=5)

    def _build_footer(self) -> None:
        rodape = ctk.CTkFrame(self)
        rodape.grid(row=2, column=0, sticky="ew", padx=22, pady=(8, 20))
        rodape.grid_columnconfigure((0, 1), weight=1)

        self.fabrica_resumo = ctk.CTkLabel(
            rodape,
            text="Selecionado fábrica: 0",
            height=48,
            corner_radius=7,
            # fg_color="#2F80ED",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        self.fabrica_resumo.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=(10, 6))

        self.estoque_resumo = ctk.CTkLabel(
            rodape,
            text=f"Complemento do estoque: {self._fmt(self.quantidade_informada)}",
            height=48,
            corner_radius=7,
            # fg_color="#D97706",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        self.estoque_resumo.grid(row=0, column=1, sticky="ew", padx=(5, 10), pady=(10, 6))

        acoes = ctk.CTkFrame(rodape, fg_color="transparent")
        acoes.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 10))
        for col in range(5):
            acoes.grid_columnconfigure(col, weight=1)

        ctk.CTkButton(
            acoes,
            text="Usar máximo possível",
            height=54,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._preencher_maximo,
        ).grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkButton(
            acoes,
            text="Limpar seleção",
            height=54,
            fg_color="#6C757D",
            hover_color="#5A6268",
            command=self._limpar,
        ).grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkButton(
            acoes,
            text="Somente estoque",
            height=54,
            fg_color="#D97706",
            hover_color="#B86205",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._somente_estoque,
        ).grid(row=0, column=2, padx=5, sticky="ew")
        ctk.CTkButton(
            acoes,
            text="Cancelar",
            height=54,
            fg_color="#C0392B",
            hover_color="#A93226",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._fechar,
        ).grid(row=0, column=3, padx=5, sticky="ew")
        ctk.CTkButton(
            acoes,
            text="Confirmar entrega",
            height=58,
            fg_color="#2E8B57",
            hover_color="#247447",
            font=ctk.CTkFont(size=17, weight="bold"),
            command=self._confirmar,
        ).grid(row=0, column=4, padx=5, sticky="ew")

        self._atualizar_resumo()

    def _selecionar_lote(self, lote_id: int) -> None:
        self.lote_ativo = lote_id
        lote = next((l for l in self.lotes if int(l["lote_id"]) == lote_id), None)
        if lote:
            rast = lote.get("rastreabilidade") or "SEM RASTREABILIDADE"
            self.lote_ativo_label.configure(text=f"Digitando para: {rast}")
        try:
            self.lote_entries[lote_id].focus_set()
            self.lote_entries[lote_id].icursor("end")
        except Exception:
            pass

    def _var_ativa(self) -> ctk.StringVar | None:
        if self.lote_ativo is None:
            return None
        return self.lote_vars.get(self.lote_ativo)

    def _tecla(self, valor: str) -> None:
        var = self._var_ativa()
        if var is None:
            return
        atual = var.get()
        if valor == ",":
            if "," in atual or "." in atual:
                return
            var.set((atual or "0") + ",")
            return
        novo = atual + valor
        sep = "," if "," in novo else "." if "." in novo else None
        if sep and len(novo.split(sep, 1)[1]) > 3:
            return
        if novo.startswith("00") and sep is None:
            novo = novo.lstrip("0") or "0"
        var.set(novo)

    def _apagar(self) -> None:
        var = self._var_ativa()
        if var is not None:
            var.set(var.get()[:-1])

    def _limpar_lote_ativo(self) -> None:
        var = self._var_ativa()
        if var is not None:
            var.set("")

    def _maximo_lote_ativo(self) -> None:
        if self.lote_ativo is None:
            return
        lote = next((l for l in self.lotes if int(l["lote_id"]) == self.lote_ativo), None)
        if not lote:
            return
        total_outros = Decimal("0")
        for lote_id, var in self.lote_vars.items():
            if lote_id == self.lote_ativo:
                continue
            texto = var.get().strip().replace(",", ".")
            if not texto:
                continue
            try:
                total_outros += Decimal(texto)
            except InvalidOperation:
                pass
        disponivel = Decimal(str(lote.get("quantidade_disponivel") or 0))
        restante = max(self.quantidade_informada - total_outros, Decimal("0"))
        usar = min(disponivel, restante)
        self.lote_vars[self.lote_ativo].set(self._fmt(usar).replace(".", ",") if usar > 0 else "")

    def _selecionados(self) -> list[dict]:
        selecionados: list[dict] = []
        lotes_por_id = {int(l["lote_id"]): l for l in self.lotes}
        for lote_id, var in self.lote_vars.items():
            texto = var.get().strip().replace(",", ".")
            if not texto:
                continue
            try:
                quantidade = Decimal(texto)
            except InvalidOperation as exc:
                raise ValueError("Há uma quantidade inválida na seleção da fábrica.") from exc
            if quantidade < 0:
                raise ValueError("A quantidade selecionada não pode ser negativa.")
            if quantidade == 0:
                continue
            disponivel = Decimal(str(lotes_por_id[lote_id].get("quantidade_disponivel") or 0))
            if quantidade > disponivel:
                raise ValueError(
                    f"O lote {lotes_por_id[lote_id].get('rastreabilidade') or lote_id} possui somente "
                    f"{self._fmt(disponivel)} disponível."
                )
            selecionados.append({"lote_id": lote_id, "quantidade": float(quantidade)})
        return selecionados

    def _total_selecionado(self) -> Decimal:
        try:
            return sum(
                (Decimal(str(item["quantidade"])) for item in self._selecionados()),
                Decimal("0"),
            )
        except ValueError:
            return Decimal("0")

    def _atualizar_resumo(self) -> None:
        total = self._total_selecionado()
        complemento = max(self.quantidade_informada - total, Decimal("0"))
        if hasattr(self, "fabrica_resumo"):
            self.fabrica_resumo.configure(text=f"Selecionado fábrica: {self._fmt(total)}")
        if hasattr(self, "estoque_resumo"):
            self.estoque_resumo.configure(text=f"Complemento do estoque: {self._fmt(complemento)}")

    def _preencher_maximo(self) -> None:
        restante = self.quantidade_informada
        for lote in self.lotes:
            lote_id = int(lote["lote_id"])
            disponivel = Decimal(str(lote.get("quantidade_disponivel") or 0))
            usar = min(disponivel, restante)
            self.lote_vars[lote_id].set(self._fmt(usar).replace(".", ",") if usar > 0 else "")
            restante -= usar
            if restante <= 0:
                restante = Decimal("0")
        self._atualizar_resumo()

    def _limpar(self) -> None:
        for var in self.lote_vars.values():
            var.set("")
        self._atualizar_resumo()

    def _confirmar(self) -> None:
        try:
            lotes = self._selecionados()
        except ValueError as exc:
            messagebox.showerror("Entrega de MP", str(exc), parent=self)
            return

        if not lotes:
            self._somente_estoque()
            return

        total_fabrica = sum(
            (Decimal(str(item["quantidade"])) for item in lotes), Decimal("0")
        )
        if total_fabrica > self.quantidade_informada:
            messagebox.showerror(
                "Entrega de MP",
                "O total selecionado na fábrica não pode ser maior que a quantidade da entrega.",
                parent=self,
            )
            return

        restante_req = Decimal(str(self.consulta.get("quantidade_restante_requisicao") or 0))
        if self.quantidade_informada > restante_req:
            messagebox.showerror(
                "Entrega de MP",
                (
                    "Para usar saldo de fábrica, a quantidade informada deve ser no máximo o restante "
                    "da requisição. Para uma entrega com excedente, use 'Somente estoque'."
                ),
                parent=self,
            )
            return

        try:
            resultado = self.repository.registrar_entrega_com_fabrica(
                item_requisicao_id=int(self.item["item_requisicao_id"]),
                quantidade_total=self.quantidade_informada,
                lotes=lotes,
                nome_operador=self.nome_operador,
                observacao=self.observacao,
            )
        except Exception as exc:
            messagebox.showerror("Entrega de MP", str(exc), parent=self)
            return

        messagebox.showinfo(
            "Entrega de MP",
            (
                "Entrega registrada.\n"
                f"Fábrica: {self._fmt(resultado.get('quantidade_fabrica'))}\n"
                f"Estoque: {self._fmt(resultado.get('quantidade_nova'))}\n"
                f"Restante: {self._fmt(resultado.get('quantidade_restante'))}"
            ),
            parent=self,
        )
        self._fechar()
        self.on_success()

    def _somente_estoque(self) -> None:
        try:
            resultado = self.repository.registrar_entrega(
                item_requisicao_id=int(self.item["item_requisicao_id"]),
                quantidade=self.quantidade_informada,
                nome_operador=self.nome_operador,
                observacao=self.observacao,
            )
        except Exception as exc:
            messagebox.showerror("Entrega de MP", str(exc), parent=self)
            return

        messagebox.showinfo(
            "Entrega de MP",
            (
                "Entrega registrada somente pelo estoque.\n"
                f"Aplicado: {self._fmt(resultado.get('quantidade_aplicada'))}\n"
                f"Excedente: {self._fmt(resultado.get('quantidade_excedente'))}"
            ),
            parent=self,
        )
        self._fechar()
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
        return f"{numero:.3f}".rstrip("0").rstrip(".") or "0"
