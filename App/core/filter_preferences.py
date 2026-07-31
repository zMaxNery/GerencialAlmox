from __future__ import annotations

from typing import Any

from core.user_session import obter_usuario_atual


def obter_filtros_padrao(
    modulo_codigo: str,
) -> dict[str, Any]:
    usuario = obter_usuario_atual()

    if usuario is None:
        return {}

    preferencias = usuario.obter_preferencias(
        modulo_codigo
    )

    filtros = preferencias.get("filtros_padrao", {})

    return filtros if isinstance(filtros, dict) else {}

def aplicar_option_menu(
    widget,
    valor,
) -> None:
    """
    Seleciona o valor somente se ele existir nas opções
    atuais do OptionMenu.
    """
    if valor in (None, ""):
        return

    valor_procurado = str(valor).strip().casefold()
    valores = list(widget.cget("values") or [])

    for valor_existente in valores:
        if str(valor_existente).strip().casefold() == valor_procurado:
            widget.set(valor_existente)
            return

def aplicar_entry(
    widget,
    valor,
) -> None:
    if valor in (None, ""):
        return

    widget.delete(0, "end")
    widget.insert(0, str(valor))
