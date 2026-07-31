from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserContext:
    id: int
    usuario_windows: str
    nome_exibicao: str
    ativo: bool
    administrador: bool
    tema: str
    modulos_permitidos: set[str] = field(default_factory=set)
    preferencias: dict[str, dict[str, Any]] = field(default_factory=dict)

    def pode_acessar(self, codigo_modulo: str) -> bool:
        if not self.ativo:
            return False

        codigo = str(codigo_modulo or "").strip().lower()
        if not codigo:
            return False

        return self.administrador or codigo in self.modulos_permitidos

    def obter_preferencias(self, codigo_modulo: str) -> dict[str, Any]:
        codigo = str(codigo_modulo or "").strip().lower()
        return dict(self.preferencias.get(codigo, {}))
