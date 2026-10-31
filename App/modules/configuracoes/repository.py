from __future__ import annotations

from typing import Any

from core.supabase_client import get_supabase


class ConfiguracoesRepository:
    """Acesso aos parâmetros configuráveis da aplicação."""

    def __init__(self) -> None:
        self.client = get_supabase()

    def listar_locais_estoque(self, somente_ativos: bool = False) -> list[dict[str, Any]]:
        query = (
            self.client.table("locais_estoque")
            .select("id,nome,ordem,ativo")
            .order("ordem")
            .order("nome")
        )
        if somente_ativos:
            query = query.eq("ativo", True)
        response = query.execute()
        return response.data or []

    def salvar_local_estoque(
        self,
        local_id: int | None,
        nome: str,
        nome_operador: str,
    ) -> dict[str, Any]:
        if not nome.strip():
            raise ValueError("Informe o nome do local.")
        if not nome_operador.strip():
            raise ValueError("Não foi possível identificar o usuário atual.")

        response = self.client.rpc(
            "salvar_local_estoque",
            {
                "p_id": int(local_id) if local_id is not None else None,
                "p_nome": nome.strip(),
                "p_usuario": nome_operador.strip(),
            },
        ).execute()
        return self._resultado_rpc(
            response.data,
            "O Supabase não retornou o resultado do cadastro do local.",
        )

    def alterar_status_local_estoque(
        self,
        local_id: int,
        ativo: bool,
        nome_operador: str,
    ) -> dict[str, Any]:
        response = self.client.rpc(
            "alterar_status_local_estoque",
            {
                "p_id": int(local_id),
                "p_ativo": bool(ativo),
                "p_usuario": nome_operador.strip(),
            },
        ).execute()
        return self._resultado_rpc(
            response.data,
            "O Supabase não retornou o resultado da alteração do status do local.",
        )

    def excluir_local_estoque(
        self,
        local_id: int,
        nome_operador: str,
    ) -> dict[str, Any]:
        response = self.client.rpc(
            "excluir_local_estoque",
            {
                "p_id": int(local_id),
                "p_usuario": nome_operador.strip(),
            },
        ).execute()
        return self._resultado_rpc(
            response.data,
            "O Supabase não retornou o resultado da exclusão do local.",
        )

    @staticmethod
    def _resultado_rpc(data: Any, mensagem: str) -> dict[str, Any]:
        if isinstance(data, list) and data:
            data = data[0]
        if isinstance(data, dict):
            return data
        raise RuntimeError(mensagem)
