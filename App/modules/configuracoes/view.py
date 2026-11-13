from __future__ import annotations

import getpass
from tkinter import messagebox, ttk

import customtkinter as ctk

from core.user_session import obter_usuario_atual
from modules.configuracoes.repository import ConfiguracoesRepository


class ConfiguracoesView(ctk.CTkFrame):
    """Tela administrativa para locais e futuras configurações da aplicação."""

    def __init__(self, parent) -> None:
        super().__init__(parent, corner_radius=0)

        self.usuario = obter_usuario_atual()
        if self.usuario is None or not self.usuario.ativo:
            raise PermissionError("É necessário estar conectado com um usuário ativo.")
        if not self.usuario.administrador:
            raise PermissionError("Somente administradores podem acessar Configurações.")

        self.repository = ConfiguracoesRepository()
        self.operador = getpass.getuser()
        self.local_id_selecionado: int | None = None
        self.locais_por_item: dict[str, dict] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._montar_tela()
        self._carregar_locais()

    def _montar_tela(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        cabecalho.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cabecalho,
            text="Configurações",
            font=ctk.CTkFont(size=26, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            cabecalho,
            text="Parâmetros gerais utilizados pelos módulos da aplicação.",
            font=ctk.CTkFont(size=14),
        ).grid(row=1, column=0, pady=(4, 0), sticky="w")

        corpo = ctk.CTkFrame(self)
        corpo.grid(row=1, column=0, padx=20, pady=(8, 20), sticky="nsew")
        corpo.grid_columnconfigure(0, weight=3)
        corpo.grid_columnconfigure(1, weight=2)
        corpo.grid_rowconfigure(0, weight=1)

        painel_lista = ctk.CTkFrame(corpo)
        painel_lista.grid(row=0, column=0, padx=(12, 8), pady=12, sticky="nsew")
        painel_lista.grid_columnconfigure(0, weight=1)
        painel_lista.grid_rowconfigure(1, weight=1)

        topo_lista = ctk.CTkFrame(painel_lista, fg_color="transparent")
        topo_lista.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        topo_lista.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            topo_lista,
            text="Locais de estoque",
            font=ctk.CTkFont(size=19, weight="bold"),
        ).grid(row=0, column=0, sticky="w")
        self.contador_label = ctk.CTkLabel(topo_lista, text="0 locais | 0 ativos")
        self.contador_label.grid(row=0, column=1, padx=(8, 0), sticky="e")

        self.tree = ttk.Treeview(
            painel_lista,
            columns=("ordem", "nome", "status"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("ordem", text="#")
        self.tree.heading("nome", text="Local de estoque")
        self.tree.heading("status", text="Uso")
        self.tree.column("ordem", width=55, minwidth=55, stretch=False, anchor="center")
        self.tree.column("nome", width=240, anchor="w")
        self.tree.column("status", width=100, minwidth=100, stretch=False, anchor="center")
        self.tree.grid(row=1, column=0, padx=(10, 0), pady=(0, 10), sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._selecionar_local)

        scroll = ttk.Scrollbar(painel_lista, orient="vertical", command=self.tree.yview)
        scroll.grid(row=1, column=1, padx=(0, 10), pady=(0, 10), sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)

        painel_form = ctk.CTkFrame(corpo)
        painel_form.grid(row=0, column=1, padx=(8, 12), pady=12, sticky="nsew")
        painel_form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            painel_form,
            text="Cadastro de local",
            font=ctk.CTkFont(size=19, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(18, 8), sticky="w")
        ctk.CTkLabel(
            painel_form,
            text="Nome do local",
            anchor="w",
        ).grid(row=1, column=0, padx=16, pady=(12, 4), sticky="ew")

        self.ent_nome = ctk.CTkEntry(
            painel_form,
            height=40,
            placeholder_text="Informe o nome do local",
        )
        self.ent_nome.grid(row=2, column=0, padx=16, sticky="ew")
        self.ent_nome.bind("<Return>", lambda _event: self._salvar_local())

        self.info_label = ctk.CTkLabel(
            painel_form,
            text=(
                "Cadastre quantos locais forem necessários.\n"
                "Bloquear um local impede novos lançamentos e\n"
                "alterações para esse local, mas preserva o histórico.\n"
                "É possível reativá-lo posteriormente."
            ),
            justify="left",
            anchor="w",
            wraplength=320,
        )
        self.info_label.grid(row=3, column=0, padx=16, pady=(14, 8), sticky="ew")

        botoes = ctk.CTkFrame(painel_form, fg_color="transparent")
        botoes.grid(row=4, column=0, padx=12, pady=12, sticky="ew")
        botoes.grid_columnconfigure((0, 1), weight=1)

        self.btn_salvar = ctk.CTkButton(
            botoes,
            text="Cadastrar local",
            command=self._salvar_local,
            fg_color="#2E8B57",
            hover_color="#247447",
        )
        self.btn_salvar.grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        self.btn_novo = ctk.CTkButton(
            botoes,
            text="Novo / limpar",
            command=self._novo_local,
            fg_color="#6C757D",
            hover_color="#5A6268",
        )
        self.btn_novo.grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        self.btn_status = ctk.CTkButton(
            botoes,
            text="Bloquear uso",
            command=self._alternar_status_local,
            fg_color="#B9770E",
            hover_color="#935F0D",
            state="disabled",
        )
        self.btn_status.grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        self.btn_excluir = ctk.CTkButton(
            botoes,
            text="Excluir local",
            command=self._excluir_local,
            fg_color="#C0392B",
            hover_color="#922B21",
            state="disabled",
        )
        self.btn_excluir.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        self.btn_atualizar = ctk.CTkButton(
            botoes,
            text="Atualizar lista",
            command=self._carregar_locais,
        )
        self.btn_atualizar.grid(row=2, column=0, columnspan=2, padx=4, pady=4, sticky="ew")

        self.status_label = ctk.CTkLabel(
            painel_form,
            text="",
            justify="left",
            anchor="w",
            wraplength=320,
        )
        self.status_label.grid(row=5, column=0, padx=16, pady=(4, 16), sticky="ew")

        outras = ctk.CTkFrame(self)
        outras.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        outras.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            outras,
            text="Outras configurações",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(12, 2), sticky="w")
        ctk.CTkLabel(
            outras,
            text="Área reservada para centralizar novas opções da aplicação.",
            anchor="w",
        ).grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

    def _carregar_locais(self, selecionar_id: int | None = None) -> None:
        try:
            locais = self.repository.listar_locais_estoque(somente_ativos=False)
        except Exception as exc:
            messagebox.showerror(
                "Configurações",
                f"Não foi possível carregar os locais de estoque.\n\n{exc}",
                parent=self.winfo_toplevel(),
            )
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.locais_por_item.clear()

        ativos = 0
        for indice, local in enumerate(locais, start=1):
            item_id = str(local["id"])
            ativo = bool(local.get("ativo", True))
            ativos += int(ativo)
            self.tree.insert(
                "",
                "end",
                iid=item_id,
                values=(indice, local.get("nome") or "", "Ativo" if ativo else "Bloqueado"),
                tags=("ativo" if ativo else "bloqueado",),
            )
            self.locais_por_item[item_id] = local

        self.tree.tag_configure("bloqueado", foreground="#C0392B")
        self.contador_label.configure(text=f"{len(locais)} locais | {ativos} ativos")

        if selecionar_id is not None and str(selecionar_id) in self.locais_por_item:
            item_id = str(selecionar_id)
            self.tree.selection_set(item_id)
            self.tree.see(item_id)
            self._selecionar_local()
        else:
            self._novo_local()

    def _selecionar_local(self, _event=None) -> None:
        selecao = self.tree.selection()
        if not selecao:
            return

        local = self.locais_por_item.get(selecao[0])
        if local is None:
            return

        self.local_id_selecionado = int(local["id"])
        self.ent_nome.delete(0, "end")
        self.ent_nome.insert(0, str(local.get("nome") or ""))
        ativo = bool(local.get("ativo", True))
        self.btn_salvar.configure(state="normal", text="Salvar alteração")
        self.btn_status.configure(
            state="normal",
            text="Bloquear uso" if ativo else "Liberar uso",
            fg_color="#B9770E" if ativo else "#2E8B57",
            hover_color="#935F0D" if ativo else "#247447",
        )
        self.btn_excluir.configure(state="normal")
        self._status(
            "Local ativo: disponível para novos lançamentos."
            if ativo
            else "Local bloqueado: não estará disponível em novos lançamentos."
        )

    def _novo_local(self) -> None:
        self.local_id_selecionado = None
        selecao = self.tree.selection()
        if selecao:
            self.tree.selection_remove(*selecao)
        self.ent_nome.delete(0, "end")
        self.btn_salvar.configure(text="Cadastrar local", state="normal")
        self.btn_status.configure(state="disabled", text="Bloquear uso")
        self.btn_excluir.configure(state="disabled")
        self._status("Informe o nome para cadastrar um novo local.")
        self.ent_nome.focus_set()

    def _salvar_local(self) -> None:
        nome = " ".join(self.ent_nome.get().split())
        if not nome:
            self._status("Informe o nome do local.", erro=True)
            self.ent_nome.focus_set()
            return

        try:
            resultado = self.repository.salvar_local_estoque(
                local_id=self.local_id_selecionado,
                nome=nome,
                nome_operador=self.operador,
            )
        except Exception as exc:
            self._status(str(exc), erro=True)
            return

        local_id = resultado.get("id")
        self._carregar_locais(selecionar_id=local_id)
        self._status("Local salvo com sucesso.")

    def _alternar_status_local(self) -> None:
        if self.local_id_selecionado is None:
            return

        local = self.locais_por_item.get(str(self.local_id_selecionado))
        if local is None:
            self._carregar_locais()
            return

        novo_status = not bool(local.get("ativo", True))
        nome = str(local.get("nome") or "")
        acao = "liberar" if novo_status else "bloquear"
        texto = (
            f"Deseja realmente {acao} o uso do local '{nome}'?\n\n"
            "O bloqueio impede novos lançamentos ou alterações para esse local.\n"
            "Os registros existentes serão preservados."
        )
        if not messagebox.askyesno(
            "Confirmar alteração",
            texto,
            parent=self.winfo_toplevel(),
        ):
            return

        try:
            self.repository.alterar_status_local_estoque(
                self.local_id_selecionado,
                novo_status,
                self.operador,
            )
        except Exception as exc:
            self._status(str(exc), erro=True)
            return

        local_id = self.local_id_selecionado
        self._carregar_locais(selecionar_id=local_id)
        self._status(
            f"Uso do local '{nome}' "
            f"{'liberado' if novo_status else 'bloqueado'} com sucesso."
        )

    def _excluir_local(self) -> None:
        if self.local_id_selecionado is None:
            self._status("Selecione um local para excluir.", erro=True)
            return

        nome = self.ent_nome.get().strip()
        confirmado = messagebox.askyesno(
            "Excluir local",
            (
                f"Deseja realmente excluir o local '{nome}'?\n\n"
                "Locais associados a lançamentos do Inventário MP não podem ser excluídos."
            ),
            icon="warning",
            parent=self.winfo_toplevel(),
        )
        if not confirmado:
            return

        try:
            self.repository.excluir_local_estoque(
                self.local_id_selecionado,
                self.operador,
            )
        except Exception as exc:
            self._status(str(exc), erro=True)
            return

        self._carregar_locais()
        self._status("Local excluído com sucesso.")

    def _status(self, mensagem: str, erro: bool = False) -> None:
        self.status_label.configure(
            text=mensagem,
            text_color="#E74C3C" if erro else "#27AE60",
        )
