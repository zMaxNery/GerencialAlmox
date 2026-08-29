from __future__ import annotations

import unicodedata
from typing import Iterable

def _normalizar(valor) -> str:
    texto = str(valor or "").casefold().strip()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(ch for ch in texto if not unicodedata.combining(ch))

def corresponde_pesquisa(
    row: dict,
    pesquisa: str,
    campos: Iterable[str],
) -> bool:
    """Pesquisa todos os termos informados em qualquer campo da tabela."""
    termos = [_normalizar(termo) for termo in str(pesquisa or "").split()]
    termos = [termo for termo in termos if termo]
    if not termos:
        return True

    texto = " ".join(_normalizar(row.get(campo)) for campo in campos)
    return all(termo in texto for termo in termos)
