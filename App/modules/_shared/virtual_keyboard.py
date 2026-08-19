from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tkinter import messagebox


def abrir_teclado_virtual(widget=None) -> None:
    """Abre o teclado virtual do Windows e devolve o foco ao campo informado."""
    if widget is not None:
        try:
            widget.focus_set()
        except Exception:
            pass

    candidatos = [
        Path(os.environ.get("CommonProgramFiles", r"C:\Program Files\Common Files"))
        / "microsoft shared"
        / "ink"
        / "TabTip.exe",
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "osk.exe",
    ]

    for caminho in candidatos:
        try:
            if caminho.exists():
                subprocess.Popen([str(caminho)])
                return
        except Exception:
            continue

    try:
        subprocess.Popen(["osk.exe"])
        return
    except Exception as exc:
        messagebox.showerror(
            "Teclado virtual",
            f"Não foi possível abrir o teclado virtual do Windows.\n\n{exc}",
        )
