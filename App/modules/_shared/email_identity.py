from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import extract_msg
from bs4 import BeautifulSoup


def calcular_identificador_msg(path: str | Path) -> str:
    """
    Prioridade:
    1. Internet Message-ID existente no e-mail;
    2. impressão digital de assunto, remetente, data e corpo.

    A chave final é um SHA-256 hexadecimal
    """
    msg_path = Path(path)

    if not msg_path.is_file():
        raise FileNotFoundError(msg_path)

    message = extract_msg.Message(str(msg_path))

    try:
        message_id = _limpar(getattr(message, "messageId", None))

        if message_id:
            origem = {
                "versao": 2,
                "tipo": "internet-message-id",
                "valor": _normalizar_message_id(message_id),
            }
        else:
            html = _decodificar_html(getattr(message, "htmlBody", None))
            corpo = _texto_canonico_html(html)

            if not corpo:
                corpo = _normalizar(getattr(message, "body", None))

            data_recebimento = (
                getattr(message, "receivedTime", None)
                or getattr(message, "date", None)
            )

            origem = {
                "versao": 2,
                "tipo": "conteudo-canonico",
                "assunto": _normalizar(getattr(message, "subject", None)),
                "remetente": _normalizar(getattr(message, "sender", None)),
                "recebido_em": _normalizar_data(data_recebimento),
                "corpo": corpo,
            }
    finally:
        message.close()

    serializado = json.dumps(
        origem,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()

def _normalizar_message_id(value: str) -> str:
    return value.strip().strip("<>").casefold()

def _decodificar_html(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, bytes):
        for encoding in ("utf-8-sig", "cp1252", "latin1"):
            try:
                return value.decode(encoding)
            except UnicodeDecodeError:
                continue

        return value.decode("utf-8", errors="replace")

    return str(value)

def _texto_canonico_html(html: str) -> str:
    if not html:
        return ""

    soup = BeautifulSoup(html, "lxml")

    for elemento in soup(["script", "style"]):
        elemento.decompose()

    return _normalizar(soup.get_text(" ", strip=True))

def _normalizar_data(value: Any) -> str:
    if value is None:
        return ""

    isoformat = getattr(value, "isoformat", None)

    if callable(isoformat):
        try:
            return str(isoformat())
        except Exception:
            pass

    return _normalizar(value)

def _limpar(value: Any) -> str:
    if value is None:
        return ""

    return " ".join(str(value).replace("\xa0", " ").split()).strip()

def _normalizar(value: Any) -> str:
    texto = _limpar(value).casefold()
    texto = unicodedata.normalize("NFKC", texto)
    return re.sub(r"\s+", " ", texto).strip()
