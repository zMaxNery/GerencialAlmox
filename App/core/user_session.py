from __future__ import annotations

from core.user_context import UserContext


_usuario_atual: UserContext | None = None

def definir_usuario_atual(usuario: UserContext | None) -> None:
    global _usuario_atual
    _usuario_atual = usuario

def obter_usuario_atual() -> UserContext | None:
    return _usuario_atual

def exigir_usuario_atual() -> UserContext:
    if _usuario_atual is None:
        raise RuntimeError("O usuário atual ainda não foi carregado.")
    return _usuario_atual
