from __future__ import annotations

import getpass
import socket
from decimal import Decimal
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from core.almox_repository import AlmoxRepository
from modules.importador_emails.models import EmailProcessado
from modules.importador_emails.msg_parser import MsgParser

# Carrega a função de arrastar e soltar na tela
try:
    from tkinterdnd2 import DND_FILES
except ImportError:
    DND_FILES = None

class ImportadorEmailsView(ctk.CTkFrame):
    COLUMNS = (
        "arquivo",
        "local",
        "tipo",
        "detalhes",
        "resumos",
        "peso",
        "status",
    )

    def __init__(self, parent):
        super().__init__(parent, corner_radius=0)

        self.parser = MsgParser()
        self.repository: AlmoxRepository | None = None
        self.files: dict[str, dict] = {}

        self.drag_drop_ativo = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # Contrutor dos objetos da tela
        self._build_header()
        self._build_actions()
        self._build_table()

        self.after_idle(self._enable_drag_drop)

    # Cabeçalho com Título
    def _build_header(self) -> None:
        ctk.CTkLabel(
            self,
            text="Importador de requisições",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

    # Gatilhos de funções
    def _build_actions(self) -> None:
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=20, pady=8)

        # Btn selecionar arquivos
        ctk.CTkButton(
            actions, text="Selecionar arquivos", command=self._select_files
        ).pack(side="left", padx=(0, 8))

        # Btn analisar dados 
        ctk.CTkButton(actions, text="Analisar", command=self._analyze_all).pack(
            side="left", padx=8)

        # Btn importar requisições válidas
        ctk.CTkButton(
            actions, text="Importar válidos", command=self._import_all
        ).pack(side="left", padx=8)

        # Btn limpar emails da tela
        ctk.CTkButton(actions, text="Limpar", command=self._clear).pack(
            side="left", padx=8
        )

        self.status_label = ctk.CTkLabel(actions, text="Nenhum arquivo selecionado.")
        self.status_label.pack(side="right", padx=8)

    # Construtor da Tabela
    def _build_table(self) -> None:
        ### Formatação da tabela
        # Fonte e altura das linhas
        style = ttk.Style()
        style.configure(
            "Importador.Treeview",
            font=("Arial", 12),
            rowheight=36,
        )

        # Fonte do cabeçalho
        style.configure(
            "Importador.Treeview.Heading",
            font=("Arial", 14, "bold"),
        )

        container = ctk.CTkFrame(self)
        container.grid(row=3, column=0, sticky="nsew", padx=20, pady=(8, 20))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # Aplica a formatação e outras definições
        self.tree = ttk.Treeview(
            container,
            columns=self.COLUMNS,
            show="headings",
            selectmode="browse",
            style="Importador.Treeview"
        )

        # Configuração de cores da tabela
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

        headings = {
            "arquivo": "Arquivo",
            "local": "Local",
            "tipo": "Tipo",
            "detalhes": "Detalhes",
            "resumos": "Resumo",
            "peso": "Peso Líquido",
            "status": "Situação",
        }
        widths = {
            "arquivo": 360,
            "local": 60,
            "tipo": 110,
            "detalhes": 70,
            "resumos": 70,
            "peso": 100,
            "status": 250,
        }

        for column in self.COLUMNS:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="center")

        self.tree.column("arquivo", anchor="w")
        self.tree.column("status", anchor="w")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    # Carregador da função Drag-Drop
    def _enable_drag_drop(self) -> None:
        if self.drag_drop_ativo:
            return

        if DND_FILES is None:
            self.status_label.configure(
                text=(
                    "Drag-and-drop indisponível. "
                    "Use o botão Selecionar arquivos."
                )
            )
            return

        root = self.winfo_toplevel()

        if not getattr(root, "drag_drop_disponivel", False):
            erro = getattr(
                root,
                "drag_drop_erro",
                "tkinterdnd2 não inicializado.",
            )

            self.status_label.configure(
                text=f"Drag-and-drop indisponível: {erro}"
            )
            return

        try:
            self.tree.drop_target_register(DND_FILES)
            self.tree.dnd_bind(
                "<<Drop>>",
                self._on_drop_files,
            )

            self.drag_drop_ativo = True

            self.status_label.configure(
                text=(
                    "Arraste o email de requisição nessa tela "
                    "ou clique em Selecionar arquivos."
                )
            )

        except Exception as exc:
            self.status_label.configure(
                text=f"Drag-and-drop indisponível: {exc}"
            )

    # Ação quando soltar os arquivos na tela
    def _on_drop_files(self, event):
        try:
            # event.data é uma lista Tcl.
            # splitlist preserva caminhos com espaços.
            paths = self.tree.tk.splitlist(event.data)

            if not paths:
                self.status_label.configure(
                    text="Nenhum arquivo foi recebido."
                )
                return getattr(event, "action", "copy")

            self._add_files(paths)

        except Exception as exc:
            self.status_label.configure(
                text=f"Erro ao receber arquivos: {exc}"
            )

        return getattr(event, "action", "copy")

    # Seleção manual de arquivos
    def _select_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Selecionar email de requisição",
            filetypes=[("Email Outlook", "*.msg")],
        )
        self._add_files(paths)

    # Carregador e processador dos arquivos recebidos (apenas .msg)
    def _add_files(self, paths) -> None:
        adicionados = 0
        ignorados = 0
        duplicados = 0

        for raw_path in paths:
            try:
                path = Path(str(raw_path).strip().strip('"'))

                if not path.exists() or not path.is_file():
                    ignorados += 1
                    continue

                if path.suffix.lower() != ".msg":
                    ignorados += 1
                    continue

                key = str(path.resolve())

                if key in self.files:
                    duplicados += 1
                    continue

                self.files[key] = {
                    "path": path,
                    "parsed": None,
                    "status": "Aguardando análise",
                }

                adicionados += 1

            except (OSError, ValueError):
                ignorados += 1

        self._refresh_table()

        partes = []

        if adicionados:
            partes.append(f"{adicionados} arquivo(s) adicionado(s)")

        if duplicados:
            partes.append(f"{duplicados} duplicado(s)")

        if ignorados:
            partes.append(f"{ignorados} ignorado(s)")

        if partes:
            self.status_label.configure(text=" | ".join(partes))
        else:
            self.status_label.configure(
                text="Nenhum arquivo .msg válido foi adicionado."
            )

    # Função para analisar os arquivos recebidos
    def _analyze_all(self) -> None:
        if not self.files:
            messagebox.showinfo("Importador", "Selecione pelo menos um arquivo de requisição.")
            return

        for record in self.files.values():
            try:
                parsed = self.parser.parse(record["path"])
                record["parsed"] = parsed

                if parsed.diferenca_peso > Decimal("0.01"):
                    record["status"] = (
                        f"Válido; diferença de peso {parsed.diferenca_peso:.3f} kg"
                    )
                else:
                    record["status"] = "Válido"
            except Exception as exc:
                record["parsed"] = None
                record["status"] = f"Erro: {exc}"

            self._refresh_table()
            self.update_idletasks()

        valid_count = sum(1 for item in self.files.values() if item["parsed"])
        self.status_label.configure(
            text=f"Análise concluída: {valid_count}/{len(self.files)} válidos."
        )

    def _import_all(self) -> None:
        valid_records = [record for record in self.files.values() if record["parsed"]]
        if not valid_records:
            messagebox.showinfo("Importador", "Faça a analise dos arquivos antes de importar.")
            return

        try:
            repository = self._get_repository()
            repository.testar_conexao()
        except Exception as exc:
            messagebox.showerror("Supabase", str(exc))
            return

        importado_por = f"{getpass.getuser()}@{socket.gethostname()}"
        importados = 0
        duplicados = 0
        erros = 0

        for record in valid_records:
            parsed: EmailProcessado = record["parsed"]

            try:
                result = repository.importar_email(
                    parsed.payload_email(importado_por),
                    parsed.payload_itens_requisicao(),
                    parsed.payload_itens_resumo(),
                )

                status = str(result.get("status", "")).upper()
                if status == "DUPLICADO":
                    record["status"] = "Duplicado: já importado"
                    duplicados += 1
                else:
                    record["status"] = (
                        f"Importado (ID {result.get('importacao_id')})"
                    )
                    importados += 1
            except Exception as exc:
                record["status"] = f"Erro ao importar: {exc}"
                erros += 1

            self._refresh_table()
            self.update_idletasks()

        self.status_label.configure(
            text=(
                f"Importados: {importados} | Duplicados: {duplicados} | "
                f"Erros: {erros}"
            )
        )

    # Acesso ao banco de dados
    def _get_repository(self) -> AlmoxRepository:
        if self.repository is None:
            self.repository = AlmoxRepository()
        return self.repository

    # Limpa a tabela de importação 
    def _clear(self) -> None:
        self.files.clear()
        self._refresh_table()
        self.status_label.configure(text="Nenhum arquivo selecionado.")

    # Atualiza as informações da tabela
    def _refresh_table(self) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for indice, (key, record) in enumerate(self.files.items()):
            parsed: EmailProcessado | None = record["parsed"]

            if parsed:
                values = (
                    record["path"].name,
                    parsed.local_estoque,
                    parsed.tipo_movimento,
                    len(parsed.itens_requisicao),
                    len(parsed.itens_resumo),
                    f"{parsed.peso_detalhes:.3f}",
                    record["status"],
                )
            else:
                values = (
                    record["path"].name,
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    record["status"],
                )

            tag_linha = "linha_par" if indice % 2 == 0 else "linha_impar"

            self.tree.insert(
                "",
                "end",
                iid=key,
                values=values,
                tags=(tag_linha,),
            )
