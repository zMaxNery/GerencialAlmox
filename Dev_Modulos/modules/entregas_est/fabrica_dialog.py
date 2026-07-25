from __future__ import annotations

from decimal import Decimal, InvalidOperation
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from core.almox_repository import AlmoxRepository


class JanelaUsoMaterialFabrica(ctk.CTkToplevel):
    """Decide a origem do material quando há saldo disponível na fábrica."""

    OPCAO_SOMENTE_FABRICA = "Somente fábrica"
    OPCAO_MISTA = "Fábrica + estoque"
    OPCAO_SOMENTE_ESTOQUE = "Somente estoque"

    def __init__(
        self,
        parent,
        repository: AlmoxRepository,
        item: dict,
        consulta: dict,
        quantidade_informada: Decimal,
        nome_operador: str,
        observacao: str | None,
        on_success: Callable[[], None],
    ) -> None:
        super().__init__(parent)

        self.repository = repository
        self.item = item
        self.consulta = consulta
        self.quantidade_informada = Decimal(str(quantidade_informada))
        self.nome_operador = nome_operador
        self.observacao = observacao
        self.on_success = on_success

        self.quantidade_disponivel = Decimal(
            str(consulta.get("quantidade_disponivel") or 0)
        )
        self.quantidade_restante = Decimal(
            str(
                consulta.get("quantidade_restante_requisicao")
                or item.get("quantidade_restante")
                or 0
            )
        )

        self.quantidade_var = ctk.StringVar(value="")
        self.modo_var = ctk.StringVar(value=self.OPCAO_SOMENTE_FABRICA)

        self.title("Origem do material")
        self.geometry("780x640")
        self.minsize(740, 610)
        self.resizable(True, True)
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.focus_force()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_mode()
        self._build_form()
        self._build_keypad()
        self._atualizar_modo(self.OPCAO_SOMENTE_FABRICA)

        self.protocol("WM_DELETE_WINDOW", self._fechar)

    def _build_header(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=20,
            pady=(20, 8),
        )

        ctk.CTkLabel(
            frame,
            text="Material disponível na fábrica",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w")

        material = self.consulta.get("material") or self.item.get("material") or ""
        rastreabilidade = (
            self.consulta.get("rastreabilidade")
            or self.item.get("rastreabilidade")
            or ""
        )

        ctk.CTkLabel(
            frame,
            text=f"{material} × {rastreabilidade}",
            font=ctk.CTkFont(size=16),
        ).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(
            frame,
            text=(
                f"Em fábrica: {self._fmt(self.quantidade_disponivel)}   |   "
                f"Falta na requisição: {self._fmt(self.quantidade_restante)}   |   "
                f"Digitado: {self._fmt(self.quantidade_informada)}"
            ),
            text_color="#E6A23C",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", pady=(5, 0))

    def _build_mode(self) -> None:
        self.segmented = ctk.CTkSegmentedButton(
            self,
            values=[
                self.OPCAO_SOMENTE_FABRICA,
                self.OPCAO_MISTA,
                self.OPCAO_SOMENTE_ESTOQUE,
            ],
            variable=self.modo_var,
            command=self._atualizar_modo,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.segmented.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=20,
            pady=(4, 12),
        )
        self.segmented.set(self.OPCAO_SOMENTE_FABRICA)

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self)
        form.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=(20, 10),
            pady=(0, 20),
        )
        form.grid_columnconfigure(0, weight=1)
        form.grid_rowconfigure(3, weight=1)

        self.instrucao_label = ctk.CTkLabel(
            form,
            text="",
            anchor="w",
            justify="left",
            wraplength=390,
            font=ctk.CTkFont(size=14),
        )
        self.instrucao_label.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=15,
            pady=(15, 8),
        )

        self.quantidade_label = ctk.CTkLabel(
            form,
            text="Quantidade:",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.quantidade_label.grid(
            row=1,
            column=0,
            sticky="w",
            padx=15,
            pady=(5, 4),
        )

        self.quantidade_entry = ctk.CTkEntry(
            form,
            textvariable=self.quantidade_var,
            justify="right",
            height=58,
            font=ctk.CTkFont(size=27, weight="bold"),
        )
        self.quantidade_entry.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=15,
            pady=(0, 12),
        )

        self.previa_label = ctk.CTkLabel(
            form,
            text="",
            anchor="nw",
            justify="left",
            wraplength=390,
            font=ctk.CTkFont(size=14),
        )
        self.previa_label.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=15,
            pady=(4, 12),
        )

        ctk.CTkButton(
            form,
            text="Confirmar apontamento",
            height=46,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._confirmar,
        ).grid(
            row=4,
            column=0,
            sticky="ew",
            padx=15,
            pady=(10, 8),
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

        self.quantidade_var.trace_add(
            "write",
            lambda *_args: self._atualizar_previa(),
        )

    def _build_keypad(self) -> None:
        keypad = ctk.CTkFrame(self)
        keypad.grid(
            row=2,
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
            text="Máximo",
            height=50,
            command=self._preencher_maximo,
        ).grid(row=4, column=2, padx=5, pady=5, sticky="ew")

    def _atualizar_modo(self, modo: str) -> None:
        if modo == self.OPCAO_SOMENTE_FABRICA:
            valor_inicial = min(
                self.quantidade_informada,
                self.quantidade_disponivel,
                self.quantidade_restante,
            )
            self.quantidade_label.configure(
                text="Quantidade a usar da fábrica:"
            )
            self.instrucao_label.configure(
                text=(
                    "Use somente o material que já está na fábrica. "
                    "A quantidade pode ser menor que o saldo e gerar uma entrega parcial."
                )
            )

        elif modo == self.OPCAO_MISTA:
            valor_inicial = self.quantidade_informada
            self.quantidade_label.configure(
                text="Quantidade nova enviada do estoque:"
            )
            self.instrucao_label.configure(
                text=(
                    "O sistema utilizará primeiro todo o saldo possível da fábrica. "
                    "A quantidade abaixo representa somente o material novo enviado "
                    "pelo operador."
                )
            )

        else:
            valor_inicial = self.quantidade_informada
            self.quantidade_label.configure(
                text="Quantidade nova enviada do estoque:"
            )
            self.instrucao_label.configure(
                text=(
                    "Ignore o saldo em fábrica e registre somente o material novo "
                    "digitado no apontamento."
                )
            )

        self.quantidade_var.set(
            self._fmt(valor_inicial).replace(".", ",")
        )
        self._atualizar_previa()

    def _preencher_maximo(self) -> None:
        modo = self.modo_var.get()

        if modo == self.OPCAO_SOMENTE_FABRICA:
            valor = min(self.quantidade_disponivel, self.quantidade_restante)
        elif modo == self.OPCAO_MISTA:
            valor = max(
                self.quantidade_restante
                - min(self.quantidade_disponivel, self.quantidade_restante),
                Decimal("0"),
            )
        else:
            valor = self.quantidade_restante

        self.quantidade_var.set(self._fmt(valor).replace(".", ","))

    def _atualizar_previa(self) -> None:
        quantidade = self._ler_quantidade(silencioso=True)
        if quantidade is None:
            self.previa_label.configure(text="")
            return

        modo = self.modo_var.get()

        if modo == self.OPCAO_SOMENTE_FABRICA:
            usado = min(
                quantidade,
                self.quantidade_disponivel,
                self.quantidade_restante,
            )
            saldo_final = max(
                self.quantidade_disponivel - usado,
                Decimal("0"),
            )
            restante = max(self.quantidade_restante - usado, Decimal("0"))

            self.previa_label.configure(
                text=(
                    f"Usado da fábrica: {self._fmt(usado)}\n"
                    f"Saldo final na fábrica: {self._fmt(saldo_final)}\n"
                    f"Restará na requisição: {self._fmt(restante)}"
                )
            )
            return

        if modo == self.OPCAO_MISTA:
            fabrica = min(self.quantidade_disponivel, self.quantidade_restante)
            restante_apos_fabrica = max(
                self.quantidade_restante - fabrica,
                Decimal("0"),
            )
            novo_aplicado = min(quantidade, restante_apos_fabrica)
            excedente = max(quantidade - novo_aplicado, Decimal("0"))
            restante_final = max(
                restante_apos_fabrica - novo_aplicado,
                Decimal("0"),
            )

            self.previa_label.configure(
                text=(
                    f"Usado da fábrica: {self._fmt(fabrica)}\n"
                    f"Material novo aplicado: {self._fmt(novo_aplicado)}\n"
                    f"Novo excedente: {self._fmt(excedente)}\n"
                    f"Restará na requisição: {self._fmt(restante_final)}"
                )
            )
            return

        novo_aplicado = min(quantidade, self.quantidade_restante)
        excedente = max(quantidade - novo_aplicado, Decimal("0"))
        restante_final = max(
            self.quantidade_restante - novo_aplicado,
            Decimal("0"),
        )

        self.previa_label.configure(
            text=(
                "O saldo existente na fábrica não será utilizado.\n"
                f"Material novo aplicado: {self._fmt(novo_aplicado)}\n"
                f"Novo excedente: {self._fmt(excedente)}\n"
                f"Restará na requisição: {self._fmt(restante_final)}"
            )
        )

    def _confirmar(self) -> None:
        quantidade = self._ler_quantidade()
        if quantidade is None:
            return

        modo = self.modo_var.get()

        try:
            if modo == self.OPCAO_SOMENTE_FABRICA:
                limite = min(
                    self.quantidade_disponivel,
                    self.quantidade_restante,
                )
                if quantidade > limite:
                    messagebox.showerror(
                        "Material em fábrica",
                        (
                            "A quantidade máxima disponível para esta opção é "
                            f"{self._fmt(limite)}."
                        ),
                        parent=self,
                    )
                    return

                resultado = self.repository.registrar_entrega_material_fabrica(
                    item_requisicao_id=int(self.item["item_requisicao_id"]),
                    quantidade_fabrica=quantidade,
                    nome_operador=self.nome_operador,
                    observacao=self.observacao,
                )

            elif modo == self.OPCAO_MISTA:
                resultado = self.repository.registrar_entrega_mista(
                    item_requisicao_id=int(self.item["item_requisicao_id"]),
                    quantidade_nova=quantidade,
                    nome_operador=self.nome_operador,
                    observacao=self.observacao,
                )

            else:
                resultado = self.repository.registrar_entrega(
                    item_requisicao_id=int(self.item["item_requisicao_id"]),
                    quantidade=quantidade,
                    nome_operador=self.nome_operador,
                    observacao=self.observacao,
                )

        except Exception as exc:
            messagebox.showerror(
                "Entrega de MP",
                str(exc),
                parent=self,
            )
            return

        if modo == self.OPCAO_SOMENTE_ESTOQUE:
            mensagem = (
                "Entrega registrada somente com material novo.\n\n"
                f"Quantidade restante: "
                f"{self._fmt(resultado.get('quantidade_restante'))}\n"
                f"Excedente criado: "
                f"{self._fmt(resultado.get('quantidade_excedente'))}"
            )
        else:
            mensagem = (
                "Apontamento registrado.\n\n"
                f"Fábrica: {self._fmt(resultado.get('quantidade_fabrica'))}\n"
                f"Material novo aplicado: "
                f"{self._fmt(resultado.get('quantidade_nova_aplicada'))}\n"
                f"Excedente criado: "
                f"{self._fmt(resultado.get('quantidade_excedente'))}\n"
                f"Restante da requisição: "
                f"{self._fmt(resultado.get('quantidade_restante'))}"
            )

        messagebox.showinfo(
            "Entrega de MP",
            mensagem,
            parent=self,
        )

        self._fechar()
        self.on_success()

    def _ler_quantidade(self, silencioso: bool = False) -> Decimal | None:
        texto = self.quantidade_var.get().strip().replace(",", ".")

        try:
            quantidade = Decimal(texto)
            if quantidade <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            if not silencioso:
                messagebox.showerror(
                    "Entrega de MP",
                    "Informe uma quantidade maior que zero.",
                    parent=self,
                )
            return None

        return quantidade

    def _adicionar_tecla(self, valor: str) -> None:
        atual = self.quantidade_var.get()

        if valor == ",":
            if "," in atual or "." in atual:
                return
            self.quantidade_var.set((atual or "0") + ",")
            return

        novo = atual + valor
        separador = "," if "," in novo else "." if "." in novo else None

        if separador and len(novo.split(separador, 1)[1]) > 3:
            return

        if novo.startswith("00") and not separador:
            novo = novo.lstrip("0") or "0"

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
