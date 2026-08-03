from __future__ import annotations

import calendar
import math
import statistics
import tkinter as tk
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk
from typing import Any, Callable

import customtkinter as ctk

from modules.indicadores_apontamentos.repository import IndicadoresRepository


class CalendarioPopup(ctk.CTkToplevel):
    """Calendário simples, feito apenas com CustomTkinter/Tkinter."""

    MESES = (
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
    )
    DIAS_SEMANA = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")

    def __init__(
        self,
        parent,
        data_atual: date,
        ao_selecionar: Callable[[date], None],
        ancora,
    ) -> None:
        super().__init__(parent)
        self._ao_selecionar = ao_selecionar
        self._data_selecionada = data_atual
        self._ano = data_atual.year
        self._mes = data_atual.month

        self.title("Selecionar data")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        self._cabecalho.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkButton(
            self._cabecalho,
            text="‹",
            width=34,
            command=self._mes_anterior,
        ).pack(side="left")

        self._titulo = ctk.CTkLabel(
            self._cabecalho,
            text="",
            width=180,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self._titulo.pack(side="left", padx=6)

        ctk.CTkButton(
            self._cabecalho,
            text="›",
            width=34,
            command=self._proximo_mes,
        ).pack(side="left")

        self._grade = ctk.CTkFrame(self)
        self._grade.pack(fill="both", padx=10, pady=4)

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=10, pady=(4, 10))

        ctk.CTkButton(
            rodape,
            text="Hoje",
            height=30,
            command=lambda: self._selecionar(date.today()),
        ).pack(fill="x")

        self._desenhar_mes()
        self.update_idletasks()

        x = ancora.winfo_rootx()
        y = ancora.winfo_rooty() + ancora.winfo_height() + 4
        self.geometry(f"+{x}+{y}")
        self.grab_set()
        self.focus_force()

    def _desenhar_mes(self) -> None:
        for widget in self._grade.winfo_children():
            widget.destroy()

        self._titulo.configure(text=f"{self.MESES[self._mes - 1]} {self._ano}")

        for coluna, nome in enumerate(self.DIAS_SEMANA):
            ctk.CTkLabel(
                self._grade,
                text=nome,
                width=38,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).grid(row=0, column=coluna, padx=2, pady=(4, 3))

        semanas = calendar.Calendar(firstweekday=0).monthdayscalendar(
            self._ano,
            self._mes,
        )

        hoje = date.today()
        for linha, semana in enumerate(semanas, start=1):
            for coluna, dia in enumerate(semana):
                if dia == 0:
                    ctk.CTkLabel(self._grade, text="", width=38).grid(
                        row=linha,
                        column=coluna,
                        padx=2,
                        pady=2,
                    )
                    continue

                valor = date(self._ano, self._mes, dia)
                selecionado = valor == self._data_selecionada
                eh_hoje = valor == hoje

                botao = ctk.CTkButton(
                    self._grade,
                    text=str(dia),
                    width=38,
                    height=32,
                    corner_radius=7,
                    border_width=1 if eh_hoje and not selecionado else 0,
                    command=lambda data_escolhida=valor: self._selecionar(
                        data_escolhida
                    ),
                )
                if not selecionado:
                    botao.configure(fg_color="transparent")
                botao.grid(row=linha, column=coluna, padx=2, pady=2)

    def _mes_anterior(self) -> None:
        if self._mes == 1:
            self._mes = 12
            self._ano -= 1
        else:
            self._mes -= 1
        self._desenhar_mes()

    def _proximo_mes(self) -> None:
        if self._mes == 12:
            self._mes = 1
            self._ano += 1
        else:
            self._mes += 1
        self._desenhar_mes()

    def _selecionar(self, valor: date) -> None:
        self._ao_selecionar(valor)
        self.destroy()


class CampoData(ctk.CTkFrame):
    """Campo de data com barras automáticas e botão de calendário."""

    def __init__(
        self,
        parent,
        titulo: str,
        valor: date,
        ao_confirmar: Callable[[], None],
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._ao_confirmar = ao_confirmar
        self.var = ctk.StringVar(value=valor.strftime("%d/%m/%Y"))

        ctk.CTkLabel(self, text=titulo).pack(side="left", padx=(0, 5))

        self.entry = ctk.CTkEntry(
            self,
            width=112,
            textvariable=self.var,
            placeholder_text="dd/mm/aaaa",
        )
        self.entry.pack(side="left")
        self.entry.bind("<KeyRelease>", self._formatar_digitacao)
        self.entry.bind("<Return>", lambda _event: self._ao_confirmar())

        self.botao_calendario = ctk.CTkButton(
            self,
            text="📅",
            width=38,
            command=self._abrir_calendario,
        )
        self.botao_calendario.pack(side="left", padx=(4, 0))

    def definir(self, valor: date) -> None:
        self.var.set(valor.strftime("%d/%m/%Y"))

    def obter(self, nome: str) -> date:
        texto = self.var.get().strip()
        try:
            return datetime.strptime(texto, "%d/%m/%Y").date()
        except ValueError as exc:
            raise ValueError(f"{nome} inválida. Use dd/mm/aaaa.") from exc

    def _formatar_digitacao(self, _event=None) -> None:
        digitos = "".join(char for char in self.var.get() if char.isdigit())[:8]

        if len(digitos) <= 2:
            texto = digitos
        elif len(digitos) <= 4:
            texto = f"{digitos[:2]}/{digitos[2:]}"
        else:
            texto = f"{digitos[:2]}/{digitos[2:4]}/{digitos[4:]}"

        if texto != self.var.get():
            self.var.set(texto)
            self.entry.icursor("end")

    def _abrir_calendario(self) -> None:
        try:
            data_atual = self.obter("Data")
        except ValueError:
            data_atual = date.today()

        CalendarioPopup(
            self,
            data_atual=data_atual,
            ao_selecionar=self.definir,
            ancora=self.entry,
        )


class GraficoIndicadores(tk.Canvas):
    """Gráfico responsivo sem dependências externas."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self._dados: list[dict[str, float | str]] = []
        self._titulo = ""
        self._series: list[tuple[str, str, str]] = []
        self.bind("<Configure>", lambda _event: self._desenhar())

    def definir_dados(
        self,
        dados: list[dict[str, float | str]],
        titulo: str,
        series: list[tuple[str, str, str]],
    ) -> None:
        self._dados = dados
        self._titulo = titulo
        self._series = series
        self._desenhar()

    @staticmethod
    def _paleta() -> tuple[str, str, str, list[str]]:
        if ctk.get_appearance_mode() == "Dark":
            return "#242424", "#F2F2F2", "#4A4A4A", ["#4F9DE8", "#55C2A3"]
        return "#F7F7F7", "#202020", "#D1D1D1", ["#2878B5", "#2D9D78"]

    def _desenhar(self) -> None:
        largura = max(self.winfo_width(), 300)
        altura = max(self.winfo_height(), 220)
        fundo, texto, grade, cores = self._paleta()

        self.configure(bg=fundo)
        self.delete("all")

        self.create_text(
            18,
            14,
            anchor="nw",
            text=self._titulo,
            fill=texto,
            font=("Arial", 14, "bold"),
        )

        if self._series:
            legenda_x = largura - 18
            for indice in range(len(self._series) - 1, -1, -1):
                _chave, nome, _sufixo = self._series[indice]
                largura_texto = max(len(nome) * 7, 70)
                legenda_x -= largura_texto
                self.create_rectangle(
                    legenda_x,
                    17,
                    legenda_x + 12,
                    29,
                    fill=cores[indice % len(cores)],
                    outline="",
                )
                self.create_text(
                    legenda_x + 17,
                    23,
                    anchor="w",
                    text=nome,
                    fill=texto,
                    font=("Arial", 10),
                )
                legenda_x -= 16

        if not self._dados:
            self.create_text(
                largura / 2,
                altura / 2,
                text="Nenhum dado no período selecionado.",
                fill=texto,
                font=("Arial", 12),
            )
            return

        margem_esquerda = 78
        margem_direita = 25
        margem_superior = 58
        margem_inferior = 52
        area_largura = max(largura - margem_esquerda - margem_direita, 20)
        area_altura = max(altura - margem_superior - margem_inferior, 20)

        valores = [
            float(linha.get(chave, 0) or 0)
            for linha in self._dados
            for chave, _nome, _sufixo in self._series
        ]
        maior = max(valores, default=0)
        maior = maior if maior > 0 else 1

        for indice in range(5):
            proporcao = indice / 4
            y = margem_superior + area_altura - area_altura * proporcao
            valor = maior * proporcao
            self.create_line(
                margem_esquerda,
                y,
                margem_esquerda + area_largura,
                y,
                fill=grade,
                dash=(2, 4),
            )
            self.create_text(
                margem_esquerda - 8,
                y,
                anchor="e",
                text=self._formatar_eixo(valor),
                fill=texto,
                font=("Arial", 9),
            )

        quantidade = len(self._dados)
        quantidade_series = max(len(self._series), 1)
        passo = area_largura / max(quantidade, 1)
        largura_grupo = min(passo * 0.72, 76)
        largura_barra = max(min(largura_grupo / quantidade_series - 3, 30), 3)
        largura_total = quantidade_series * largura_barra + (quantidade_series - 1) * 3
        pular_rotulo = max(1, math.ceil(quantidade / 12))

        for indice, linha in enumerate(self._dados):
            centro_x = margem_esquerda + passo * (indice + 0.5)
            inicio_x = centro_x - largura_total / 2

            for serie_indice, (chave, _nome, sufixo) in enumerate(self._series):
                valor = float(linha.get(chave, 0) or 0)
                altura_barra = area_altura * (valor / maior)
                x1 = inicio_x + serie_indice * (largura_barra + 3)
                x2 = x1 + largura_barra
                y1 = margem_superior + area_altura - altura_barra
                y2 = margem_superior + area_altura

                self.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=cores[serie_indice % len(cores)],
                    outline="",
                )

                if quantidade <= 8 and quantidade_series == 1:
                    self.create_text(
                        (x1 + x2) / 2,
                        max(y1 - 5, margem_superior),
                        anchor="s",
                        text=self._formatar_valor(valor, sufixo),
                        fill=texto,
                        font=("Arial", 9, "bold"),
                    )

            if indice % pular_rotulo == 0 or indice == quantidade - 1:
                self.create_text(
                    centro_x,
                    margem_superior + area_altura + 9,
                    anchor="n",
                    text=str(linha.get("rotulo", "")),
                    fill=texto,
                    font=("Arial", 9),
                )

        self.create_line(
            margem_esquerda,
            margem_superior + area_altura,
            margem_esquerda + area_largura,
            margem_superior + area_altura,
            fill=texto,
        )

    @staticmethod
    def _formatar_valor(valor: float, sufixo: str) -> str:
        if sufixo == "h":
            texto = f"{valor:,.1f}"
        else:
            texto = f"{valor:,.0f}"
        return texto.replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _formatar_eixo(valor: float) -> str:
        if abs(valor) >= 1_000_000:
            return f"{valor / 1_000_000:.1f} mi".replace(".", ",")
        if abs(valor) >= 1_000:
            return f"{valor / 1_000:.1f} mil".replace(".", ",")
        if abs(valor) >= 100:
            return f"{valor:.0f}"
        return f"{valor:.1f}".replace(".", ",")


class IndicadoresApontamentosView(ctk.CTkFrame):
    COLUNAS_OPERADORES = (
        "operador",
        "peso_bruto",
        "peso_liquido",
        "lead_time",
        "participacao",
    )

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.repository: IndicadoresRepository | None = None
        self.registros: list[dict[str, Any]] = []

        hoje = date.today()
        inicio_padrao = hoje - timedelta(days=6)

        self.agrupamento_var = ctk.StringVar(value="Diário")
        self.metrica_var = ctk.StringVar(value="Pesos bruto x líquido")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._construir_cabecalho()
        self._construir_filtros(inicio_padrao, hoje)
        self._construir_cartoes()
        self._construir_grafico()
        self._construir_tabela_operadores()

        self.after(100, self.atualizar)

    def _construir_cabecalho(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 6))

        bloco_titulo = ctk.CTkFrame(frame, fg_color="transparent")
        bloco_titulo.pack(side="left")

        ctk.CTkLabel(
            bloco_titulo,
            text="Indicadores de Entregas",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            bloco_titulo,
            text="Pesos das requisições entregues",
            font=ctk.CTkFont(size=12),
            text_color=("#666666", "#B5B5B5"),
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            frame,
            text="Atualizar",
            width=105,
            command=self.atualizar,
        ).pack(side="right", pady=4)

    def _construir_filtros(self, inicio: date, fim: date) -> None:
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, sticky="ew", padx=20, pady=7)
        frame.grid_columnconfigure(0, weight=1)

        linha_periodo = ctk.CTkFrame(frame, fg_color="transparent")
        linha_periodo.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        datas = ctk.CTkFrame(linha_periodo, fg_color="transparent")
        datas.pack(side="left")

        self.campo_data_inicial = CampoData(
            datas,
            titulo="De:",
            valor=inicio,
            ao_confirmar=self.atualizar,
        )
        self.campo_data_inicial.pack(side="left", padx=(0, 12))

        self.campo_data_final = CampoData(
            datas,
            titulo="Até:",
            valor=fim,
            ao_confirmar=self.atualizar,
        )
        self.campo_data_final.pack(side="left")

        atalhos = ctk.CTkFrame(linha_periodo, fg_color="transparent")
        atalhos.pack(side="right")

        ctk.CTkButton(
            atalhos,
            text="Mês atual",
            width=94,
            command=self._selecionar_mes_atual,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            atalhos,
            text="Últimos 7 dias",
            width=112,
            command=self._selecionar_ultimos_7_dias,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            atalhos,
            text="Últimos 30 dias",
            width=120,
            command=self._selecionar_ultimos_30_dias,
        ).pack(side="left", padx=4)

        opcoes = ctk.CTkFrame(frame, fg_color="transparent")
        opcoes.grid(row=1, column=0, sticky="e", padx=12, pady=(2, 10))

        ctk.CTkLabel(opcoes, text="Agrupar:").pack(side="left", padx=(0, 5))
        ctk.CTkOptionMenu(
            opcoes,
            width=105,
            values=["Diário", "Semanal", "Mensal"],
            variable=self.agrupamento_var,
            command=lambda _valor: self._atualizar_grafico(),
        ).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(opcoes, text="Gráfico:").pack(side="left", padx=(0, 5))
        ctk.CTkOptionMenu(
            opcoes,
            width=188,
            values=["Pesos bruto x líquido", "Lead time médio"],
            variable=self.metrica_var,
            command=lambda _valor: self._atualizar_grafico(),
        ).pack(side="left")

    def _construir_cartoes(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=2, column=0, sticky="ew", padx=20, pady=7)
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.card_peso_bruto = self._criar_cartao(
            frame,
            0,
            "Peso bruto entregue",
            "0 kg",
            "",
        )
        self.card_peso_liquido = self._criar_cartao(
            frame,
            1,
            "Peso líquido entregue",
            "0 kg",
            "",
        )
        self.card_lead_time = self._criar_cartao(
            frame,
            2,
            "Lead time médio",
            "0 h",
            "",
        )

    @staticmethod
    def _criar_cartao(
        parent,
        coluna: int,
        titulo: str,
        valor: str,
        descricao: str,
    ) -> ctk.CTkLabel:
        card = ctk.CTkFrame(parent)
        card.grid(
            row=0,
            column=coluna,
            sticky="ew",
            padx=(0 if coluna == 0 else 6, 0 if coluna == 2 else 6),
        )

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(12, 1))

        label = ctk.CTkLabel(
            card,
            text=valor,
            font=ctk.CTkFont(size=27, weight="bold"),
        )
        label.pack(anchor="w", padx=15, pady=(0, 1))

        ctk.CTkLabel(
            card,
            text=descricao,
            font=ctk.CTkFont(size=10),
            text_color=("#666666", "#B5B5B5"),
        ).pack(anchor="w", padx=15, pady=(0, 12))
        return label

    def _construir_grafico(self) -> None:
        frame = ctk.CTkFrame(self)
        frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=7)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        self.grafico = GraficoIndicadores(frame, height=300)
        self.grafico.grid(row=0, column=0, sticky="nsew", padx=7, pady=7)

    def _construir_tabela_operadores(self) -> None:
        frame = ctk.CTkFrame(self, height=190)
        frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(7, 18))
        frame.grid_propagate(False)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        cabecalho = ctk.CTkFrame(frame, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", padx=12, pady=(9, 4))

        ctk.CTkLabel(
            cabecalho,
            text="Resumo por ponte",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        container = ctk.CTkFrame(frame, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("Indicadores.Treeview", font=("Arial", 11), rowheight=29)
        style.configure(
            "Indicadores.Treeview.Heading",
            font=("Arial", 11, "bold"),
        )

        self.tree = ttk.Treeview(
            container,
            columns=self.COLUNAS_OPERADORES,
            show="headings",
            height=4,
            style="Indicadores.Treeview",
        )

        configuracao = {
            "operador": ("Operador", 230, "w"),
            "peso_bruto": ("Peso bruto", 145, "e"),
            "peso_liquido": ("Peso líquido", 145, "e"),
            "lead_time": ("Lead time", 135, "e"),
            "participacao": ("Participação", 120, "e"),
        }

        for coluna, (titulo, largura, ancora) in configuracao.items():
            self.tree.heading(coluna, text=titulo)
            self.tree.column(
                coluna,
                width=largura,
                minwidth=largura,
                stretch=coluna == "operador",
                anchor=ancora,
            )

        y_scroll = ctk.CTkScrollbar(
            container,
            orientation="vertical",
            command=self.tree.yview,
            width=18,
        )
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

    def atualizar(self) -> None:
        try:
            data_inicial = self.campo_data_inicial.obter("Data inicial")
            data_final = self.campo_data_final.obter("Data final")

            if data_final < data_inicial:
                raise ValueError("A data final não pode ser anterior à data inicial.")

            if self.repository is None:
                self.repository = IndicadoresRepository()

            self.registros = self.repository.listar_apontamentos(
                data_inicial,
                data_final,
            )
        except Exception as exc:
            messagebox.showerror("Indicadores de Entrega", str(exc))
            return

        self._atualizar_cartoes()
        self._atualizar_grafico()
        self._atualizar_tabela_operadores()

    def _atualizar_cartoes(self) -> None:
        peso_bruto = self._somar_campo("peso_bruto_entregue_kg")
        peso_liquido = self._somar_campo("peso_liquido_entregue_kg")
        lead_time = self._media_lead_time(self.registros)

        self.card_peso_bruto.configure(text=f"{self._fmt_decimal(peso_bruto)} kg")
        self.card_peso_liquido.configure(text=f"{self._fmt_decimal(peso_liquido)} kg")
        self.card_lead_time.configure(text=self._fmt_horas(lead_time))

    def _atualizar_grafico(self) -> None:
        agrupamento = self.agrupamento_var.get()
        metrica = self.metrica_var.get()

        grupos: dict[date, list[dict[str, Any]]] = defaultdict(list)
        for row in self.registros:
            data_entrega = self._data_iso(row.get("data_entrega"))
            if data_entrega is None:
                continue
            grupos[self._chave_periodo(data_entrega, agrupamento)].append(row)

        dados: list[dict[str, float | str]] = []
        for periodo in sorted(grupos):
            linhas = grupos[periodo]
            dados.append(
                {
                    "rotulo": self._rotulo_periodo(periodo, agrupamento),
                    "peso_bruto": float(self._somar_campo(
                        "peso_bruto_entregue_kg",
                        linhas,
                    )),
                    "peso_liquido": float(self._somar_campo(
                        "peso_liquido_entregue_kg",
                        linhas,
                    )),
                    "lead_time": self._media_lead_time(linhas),
                }
            )

        if metrica == "Lead time médio":
            titulo = f"Lead time médio por período — {agrupamento.lower()}"
            series = [("lead_time", "Lead time médio", "h")]
        else:
            titulo = f"Peso entregue por período — {agrupamento.lower()}"
            series = [
                ("peso_bruto", "Peso bruto", "kg"),
                ("peso_liquido", "Peso líquido", "kg"),
            ]

        self.grafico.definir_dados(dados, titulo, series)

    def _atualizar_tabela_operadores(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        grupos: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in self.registros:
            operador = str(row.get("usuario") or "NÃO INFORMADO").strip()
            grupos[operador].append(row)

        peso_liquido_total = self._somar_campo("peso_liquido_entregue_kg")
        linhas_operadores: list[tuple[Decimal, str, tuple[str, ...]]] = []

        for operador, linhas in grupos.items():
            peso_bruto = self._somar_campo("peso_bruto_entregue_kg", linhas)
            peso_liquido = self._somar_campo("peso_liquido_entregue_kg", linhas)
            lead_time = self._media_lead_time(linhas)
            participacao = (
                float(peso_liquido / peso_liquido_total * Decimal("100"))
                if peso_liquido_total > 0
                else 0
            )

            valores = (
                operador,
                f"{self._fmt_decimal(peso_bruto)} kg",
                f"{self._fmt_decimal(peso_liquido)} kg",
                self._fmt_horas(lead_time),
                f"{self._fmt_numero(participacao, 1)}%",
            )
            linhas_operadores.append(
                (peso_liquido, operador.casefold(), valores)
            )

        linhas_operadores.sort(key=lambda item: (-item[0], item[1]))

        for indice, (_peso, _operador, valores) in enumerate(linhas_operadores):
            tag = "linha_par" if indice % 2 == 0 else "linha_impar"
            self.tree.insert("", "end", values=valores, tags=(tag,))

        self.tree.tag_configure(
            "linha_par",
            background="#D5D5D5",
            foreground="#000000",
        )
        self.tree.tag_configure(
            "linha_impar",
            background="#FFFFFF",
            foreground="#000000",
        )

    def _selecionar_mes_atual(self) -> None:
        hoje = date.today()
        self._definir_periodo(hoje.replace(day=1), hoje)

    def _selecionar_ultimos_7_dias(self) -> None:
        hoje = date.today()
        self._definir_periodo(hoje - timedelta(days=6), hoje)

    def _selecionar_ultimos_30_dias(self) -> None:
        hoje = date.today()
        self._definir_periodo(hoje - timedelta(days=29), hoje)

    def _definir_periodo(self, inicio: date, fim: date) -> None:
        self.campo_data_inicial.definir(inicio)
        self.campo_data_final.definir(fim)
        self.atualizar()

    def _somar_campo(
        self,
        campo: str,
        registros: list[dict[str, Any]] | None = None,
    ) -> Decimal:
        linhas = self.registros if registros is None else registros
        return round(sum(
            (self._decimal(row.get(campo)) for row in linhas),
            start=Decimal("0"),
        ),2)

    def _media_lead_time(self, registros: list[dict[str, Any]]) -> float:
        valores = [
            float(self._decimal(row.get("lead_time_horas")))
            for row in registros
            if row.get("lead_time_horas") not in (None, "")
        ]
        return statistics.fmean(valores) if valores else 0

    @staticmethod
    def _data_iso(valor: Any) -> date | None:
        if valor in (None, ""):
            return None
        try:
            return date.fromisoformat(str(valor)[:10])
        except ValueError:
            return None

    @staticmethod
    def _decimal(valor: Any) -> Decimal:
        if valor in (None, ""):
            return Decimal("0")
        try:
            return Decimal(str(valor))
        except (InvalidOperation, ValueError, TypeError):
            return Decimal("0")

    @staticmethod
    def _chave_periodo(valor: date, agrupamento: str) -> date:
        if agrupamento == "Semanal":
            return valor - timedelta(days=valor.weekday())
        if agrupamento == "Mensal":
            return valor.replace(day=1)
        return valor

    @staticmethod
    def _rotulo_periodo(valor: date, agrupamento: str) -> str:
        if agrupamento == "Mensal":
            return valor.strftime("%m/%Y")
        if agrupamento == "Semanal":
            return valor.strftime("%d/%m")
        return valor.strftime("%d/%m")

    @staticmethod
    def _fmt_decimal(valor: Decimal) -> str:
        texto = f"{valor:,.3f}"
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
        return texto.rstrip("0").rstrip(",")

    @staticmethod
    def _fmt_numero(valor: float, casas: int = 1) -> str:
        texto = f"{valor:,.{casas}f}"
        return texto.replace(",", "X").replace(".", ",").replace("X", ".")

    @classmethod
    def _fmt_horas(cls, horas: float) -> str:
        if horas >= 48:
            return f"{cls._fmt_numero(horas / 24, 1)} dias"
        return f"{cls._fmt_numero(horas, 1)} h"
