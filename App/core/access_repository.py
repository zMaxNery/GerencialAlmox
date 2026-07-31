from __future__ import annotations

from typing import Any, Iterable

from core.supabase_client import get_supabase


class AccessRepository:
    """Acesso às tabelas de usuários, módulos, permissões e preferências."""

    def __init__(self) -> None:
        self.client = get_supabase()

    def buscar_usuario_windows(self, usuario_windows: str) -> dict[str, Any] | None:
        response = (
            self.client
            .table("app_usuarios")
            .select("id,usuario_windows,nome_exibicao,ativo,administrador,tema")
            .eq("usuario_windows", self._normalizar_usuario(usuario_windows))
            .limit(1)
            .execute()
        )
        dados = response.data or []
        return dados[0] if dados else None

    def listar_usuarios(self) -> list[dict[str, Any]]:
        response = (
            self.client
            .table("app_usuarios")
            .select(
                "id,usuario_windows,nome_exibicao,ativo,administrador,tema,"
                "ultimo_acesso,criado_em,atualizado_em"
            )
            .order("nome_exibicao")
            .order("usuario_windows")
            .execute()
        )
        return response.data or []

    def salvar_usuario(
        self,
        *,
        usuario_id: int | None,
        usuario_windows: str,
        nome_exibicao: str,
        ativo: bool,
        administrador: bool,
    ) -> dict[str, Any]:
        usuario_normalizado = self._normalizar_usuario(usuario_windows)
        nome = nome_exibicao.strip()

        if not usuario_normalizado:
            raise ValueError("Informe o usuário do Windows.")
        if not nome:
            raise ValueError("Informe o nome de exibição.")

        payload = {
            "usuario_windows": usuario_normalizado,
            "nome_exibicao": nome,
            "ativo": bool(ativo),
            "administrador": bool(administrador),
            "atualizado_em": "now()",
        }

        # PostgREST não interpreta now() dentro do JSON. Removemos o campo e
        # deixamos o trigger do banco atualizar atualizado_em.
        payload.pop("atualizado_em", None)

        if usuario_id is None:
            response = (
                self.client
                .table("app_usuarios")
                .insert(payload)
                .execute()
            )
        else:
            response = (
                self.client
                .table("app_usuarios")
                .update(payload)
                .eq("id", int(usuario_id))
                .execute()
            )

        dados = response.data or []
        if not dados:
            raise RuntimeError("O Supabase não retornou o usuário salvo.")
        return dados[0]

    def excluir_usuario(self, usuario_id: int) -> None:
        (
            self.client
            .table("app_usuarios")
            .delete()
            .eq("id", int(usuario_id))
            .execute()
        )

    def listar_modulos(self, somente_ativos: bool = False) -> list[dict[str, Any]]:
        query = (
            self.client
            .table("app_modulos")
            .select("codigo,nome,ordem,ativo")
        )
        if somente_ativos:
            query = query.eq("ativo", True)

        response = query.order("ordem").order("nome").execute()
        return response.data or []

    def sincronizar_modulos(self, modulos: Iterable[dict[str, Any]]) -> None:
        payload: list[dict[str, Any]] = []
        for modulo in modulos:
            codigo = str(modulo.get("codigo") or "").strip().lower()
            nome = str(modulo.get("nome") or codigo).strip()
            if not codigo:
                continue
            payload.append(
                {
                    "codigo": codigo,
                    "nome": nome or codigo,
                    "ordem": int(modulo.get("ordem", 999)),
                    "ativo": True,
                }
            )

        if not payload:
            return

        (
            self.client
            .table("app_modulos")
            .upsert(payload, on_conflict="codigo")
            .execute()
        )

    def listar_modulos_usuario(self, usuario_id: int) -> set[str]:
        response = (
            self.client
            .table("app_usuario_modulos")
            .select("modulo_codigo")
            .eq("usuario_id", int(usuario_id))
            .eq("permitido", True)
            .execute()
        )
        return {
            str(item.get("modulo_codigo") or "").strip().lower()
            for item in (response.data or [])
            if item.get("modulo_codigo")
        }

    def salvar_modulos_usuario(
        self,
        usuario_id: int,
        codigos_modulos: Iterable[str],
    ) -> None:
        usuario_id = int(usuario_id)
        (
            self.client
            .table("app_usuario_modulos")
            .delete()
            .eq("usuario_id", usuario_id)
            .execute()
        )

        codigos = sorted(
            {
                str(codigo).strip().lower()
                for codigo in codigos_modulos
                if str(codigo).strip()
            }
        )
        if not codigos:
            return

        payload = [
            {
                "usuario_id": usuario_id,
                "modulo_codigo": codigo,
                "permitido": True,
            }
            for codigo in codigos
        ]
        self.client.table("app_usuario_modulos").insert(payload).execute()

    def listar_preferencias_usuario(
        self,
        usuario_id: int,
    ) -> dict[str, dict[str, Any]]:
        response = (
            self.client
            .table("app_usuario_preferencias")
            .select("modulo_codigo,preferencias")
            .eq("usuario_id", int(usuario_id))
            .execute()
        )

        resultado: dict[str, dict[str, Any]] = {}
        for item in response.data or []:
            codigo = str(item.get("modulo_codigo") or "").strip().lower()
            preferencias = item.get("preferencias")
            if codigo and isinstance(preferencias, dict):
                resultado[codigo] = preferencias
        return resultado

    def salvar_tema(self, usuario_id: int, tema: str) -> None:
        (
            self.client
            .table("app_usuarios")
            .update({"tema": self._normalizar_tema(tema)})
            .eq("id", int(usuario_id))
            .execute()
        )

    def atualizar_ultimo_acesso(self, usuario_id: int) -> None:
        # A RPC usa now() no próprio PostgreSQL.
        self.client.rpc(
            "app_registrar_ultimo_acesso",
            {"p_usuario_id": int(usuario_id)},
        ).execute()

    def buscar_preferencias_modulo(
        self,
        usuario_id: int,
        modulo_codigo: str,
    ) -> dict[str, Any]:
        codigo = str(modulo_codigo or "").strip().lower()

        response = (
            self.client
            .table("app_usuario_preferencias")
            .select("preferencias")
            .eq("usuario_id", int(usuario_id))
            .eq("modulo_codigo", codigo)
            .limit(1)
            .execute()
        )

        dados = response.data or []

        if not dados:
            return {}

        preferencias = dados[0].get("preferencias")

        return preferencias if isinstance(preferencias, dict) else {}


    def salvar_filtros_padrao(
        self,
        usuario_id: int,
        modulo_codigo: str,
        filtros: dict[str, Any],
    ) -> None:
        codigo = str(modulo_codigo or "").strip().lower()

        if not codigo:
            raise ValueError("Código do módulo inválido.")

        preferencias_atuais = self.buscar_preferencias_modulo(
            usuario_id,
            codigo,
        )

        filtros_limpos = {
            str(chave).strip(): valor
            for chave, valor in filtros.items()
            if str(chave).strip()
            and valor not in (None, "")
        }

        preferencias_atuais["filtros_padrao"] = filtros_limpos

        payload = {
            "usuario_id": int(usuario_id),
            "modulo_codigo": codigo,
            "preferencias": preferencias_atuais,
        }

        (
            self.client
            .table("app_usuario_preferencias")
            .upsert(
                payload,
                on_conflict="usuario_id,modulo_codigo",
            )
            .execute()
        )

    @staticmethod
    def _normalizar_usuario(usuario_windows: str) -> str:
        return str(usuario_windows or "").strip().lower()

    @staticmethod
    def _normalizar_tema(tema: str) -> str:
        valor = str(tema or "Dark").strip().capitalize()
        return valor if valor in {"Dark", "Light", "System"} else "Dark"
