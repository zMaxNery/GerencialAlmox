from __future__ import annotations

import getpass
import socket
from decimal import Decimal
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from core.almox_repository import AlmoxRepository
from modules.importador_emails.models import ParsedEmail
from modules.importador_emails.msg_parser import MsgParser

try:
    import windnd
except ImportError:  # O botão de seleção continua funcionando sem drag-and-drop.
    windnd = None


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

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_header()
        self._build_actions()
        self._build_table()
        self._enable_drag_drop()

    def _build_header(self) -> None:
        ctk.CTkLabel(
            self,
            text="Importador de requisições (.msg)",
            font=ctk.CTkFont(size=25, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

    def _build_actions(self) -> None:
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=20, pady=8)

        ctk.CTkButton(
            actions, text="Selecionar arquivos", command=self._select_files
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(actions, text="Analisar", command=self._analyze_all).pack(
            side="left", padx=8
        )
        ctk.CTkButton(
            actions, text="Importar válidos", command=self._import_all
        ).pack(side="left", padx=8)
        ctk.CTkButton(actions, text="Limpar", command=self._clear).pack(
            side="left", padx=8
        )

        self.status_label = ctk.CTkLabel(actions, text="Nenhum arquivo selecionado.")
        self.status_label.pack(side="right", padx=8)

    def _build_table(self) -> None:
        container = ctk.CTkFrame(self)
        container.grid(row=3, column=0, sticky="nsew", padx=20, pady=(8, 20))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            container,
            columns=self.COLUMNS,
            show="headings",
            selectmode="browse",
        )
        headings = {
            "arquivo": "Arquivo",
            "local": "Local",
            "tipo": "Tipo",
            "detalhes": "Detalhes",
            "resumos": "Resumo",
            "peso": "Peso (kg)",
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

    def _enable_drag_drop(self) -> None:
        if windnd is None:
            return
        try:
            windnd.hook_dropfiles(self.drop_area, func=self._on_drop_files)
        except Exception as exc:
            self.status_label.configure(text=f"Drag-and-drop indisponível: {exc}")

    def _on_drop_files(self, raw_paths) -> None:
        decoded: list[str] = []
        for raw_path in raw_paths:
            if isinstance(raw_path, bytes):
                try:
                    decoded.append(raw_path.decode("utf-8"))
                except UnicodeDecodeError:
                    decoded.append(raw_path.decode("mbcs", errors="replace"))
            else:
                decoded.append(str(raw_path))
        self.after(0, lambda: self._add_files(decoded))

    def _select_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Selecionar mensagens Outlook",
            filetypes=[("Mensagem Outlook", "*.msg")],
        )
        self._add_files(paths)

    def _add_files(self, paths) -> None:
        for raw_path in paths:
            path = Path(raw_path)
            if path.suffix.lower() != ".msg":
                continue
            key = str(path.resolve())
            if key not in self.files:
                self.files[key] = {
                    "path": path,
                    "parsed": None,
                    "status": "Aguardando análise",
                }
        self._refresh_table()

    def _analyze_all(self) -> None:
        if not self.files:
            messagebox.showinfo("Importador", "Selecione pelo menos um arquivo .msg.")
            return

        for record in self.files.values():
            try:
                parsed = self.parser.parse(record["path"])
                record["parsed"] = parsed
                if parsed.weight_difference > Decimal("0.01"):
                    record["status"] = (
                        f"Válido; diferença de peso {parsed.weight_difference:.3f} kg"
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
            messagebox.showinfo("Importador", "Analise os arquivos antes de importar.")
            return

        try:
            repository = self._get_repository()
            repository.testar_conexao()
        except Exception as exc:
            messagebox.showerror("Supabase", str(exc))
            return

        imported_by = f"{getpass.getuser()}@{socket.gethostname()}"
        imported = 0
        duplicates = 0
        errors = 0

        for record in valid_records:
            parsed: ParsedEmail = record["parsed"]
            try:
                result = repository.importar_email(
                    parsed.email_payload(imported_by),
                    parsed.request_payload(),
                    parsed.summary_payload(),
                )
                status = str(result.get("status", "")).upper()
                if status == "DUPLICATE":
                    record["status"] = "Duplicado: já importado"
                    duplicates += 1
                else:
                    record["status"] = f"Importado (ID {result.get('import_id')})"
                    imported += 1
            except Exception as exc:
                record["status"] = f"Erro ao importar: {exc}"
                errors += 1
            self._refresh_table()
            self.update_idletasks()

        self.status_label.configure(
            text=f"Importados: {imported} | Duplicados: {duplicates} | Erros: {errors}"
        )

    def _get_repository(self) -> AlmoxRepository:
        if self.repository is None:
            self.repository = AlmoxRepository()
        return self.repository

    def _clear(self) -> None:
        self.files.clear()
        self._refresh_table()
        self.status_label.configure(text="Nenhum arquivo selecionado.")

    def _refresh_table(self) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        for key, record in self.files.items():
            parsed: ParsedEmail | None = record["parsed"]
            if parsed:
                values = (
                    record["path"].name,
                    parsed.stock_location,
                    parsed.movement_type,
                    len(parsed.request_items),
                    len(parsed.summary_items),
                    f"{parsed.detail_weight:.3f}",
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
            self.tree.insert("", "end", iid=key, values=values)
