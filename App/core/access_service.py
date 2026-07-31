from __future__ import annotations

import getpass
from types import ModuleType
from typing import Iterable

from core.access_repository import AccessRepository
from core.user_context import UserContext


class AccessService:
    def __init__(self, repository: AccessRepository | None = None) -> None:
        self.repository = repository or AccessRepository()

    @staticmethod
    def obter_usuario_windows() -> str:
        """Identifica apenas a conta do Windows, sem domínio e sem computador."""
        return getpass.getuser().strip().lower()

    def carregar_usuario_atual(self) -> UserContext | None:
        usuario_windows = self.obter_usuario_windows()
        registro = self.repository.buscar_usuario_windows(usuario_windows)
        if registro is None:
            return None

        usuario_id = int(registro["id"])
        administrador = bool(registro.get("administrador"))
        ativo = bool(registro.get("ativo", True))

        modulos = set()
        preferencias = {}
        if ativo:
            if not administrador:
                modulos = self.repository.listar_modulos_usuario(usuario_id)
            preferencias = self.repository.listar_preferencias_usuario(usuario_id)
            self.repository.atualizar_ultimo_acesso(usuario_id)

        return UserContext(
            id=usuario_id,
            usuario_windows=str(registro.get("usuario_windows") or usuario_windows),
            nome_exibicao=str(registro.get("nome_exibicao") or usuario_windows),
            ativo=ativo,
            administrador=administrador,
            tema=str(registro.get("tema") or "Dark"),
            modulos_permitidos=modulos,
            preferencias=preferencias,
        )

    def sincronizar_modulos(self, modulos: Iterable[ModuleType]) -> None:
        self.repository.sincronizar_modulos(
            {
                "codigo": getattr(modulo, "CODIGO", ""),
                "nome": getattr(modulo, "NOME", ""),
                "ordem": getattr(modulo, "ORDEM", 999),
            }
            for modulo in modulos
        )

    def salvar_tema(self, usuario: UserContext, tema: str) -> None:
        self.repository.salvar_tema(usuario.id, tema)
        usuario.tema = tema
