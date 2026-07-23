from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from core.supabase_client import get_supabase


class AlmoxRepository:
    """Acesso centralizado às tabelas, visões e RPCs do Supabase."""

    def __init__(self) -> None:
        self.client = get_supabase()

    def testar_conexao(self) -> None:
        self.client.table("importacoes_email").select("id").limit(1).execute()

    def importar_email(
        self,
        email_payload: dict[str, Any],
        itens_requisicao: list[dict[str, Any]],
        itens_resumo: list[dict[str, Any]],
    ) -> dict[str, Any]:
        response = self.client.rpc(
            "importar_email",
            {
                "p_email": email_payload,
                "p_itens_requisicao": itens_requisicao,
                "p_itens_resumo": itens_resumo,
            },
        ).execute()

        return self._obter_resultado_rpc(
            response.data,
            "O Supabase não retornou o resultado da importação.",
        )

    def listar_pendencias_est(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("vw_pendencias_est_operador")
            .select("*")
            .order("data_requisicao", desc=False)
            .order("item_requisicao_id", desc=False)
            .limit(2000)
            .execute()
        )
        return response.data or []

    def registrar_entrega(
        self,
        item_requisicao_id: int,
        quantidade: Decimal | str | float,
        nome_operador: str,
        observacao: str | None = None,
    ) -> dict[str, Any]:
        quantidade_normalizada = self._normalizar_quantidade(
            quantidade,
            "Quantidade entregue inválida.",
        )

        response = self.client.rpc(
            "registrar_entrega",
            {
                "p_item_requisicao_id": item_requisicao_id,
                "p_quantidade": float(quantidade_normalizada),
                "p_nome_operador": nome_operador.strip(),
                "p_observacao": observacao.strip() if observacao else None,
            },
        ).execute()

        return self._obter_resultado_rpc(
            response.data,
            "O Supabase não retornou o resultado do apontamento.",
        )

    def listar_visao_administrativa(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("vw_requisicoes_administrativo")
            .select("*")
            .order("data_requisicao", desc=True)
            .order("item_requisicao_id", desc=True)
            .limit(3000)
            .execute()
        )
        return response.data or []

    def listar_historico_entregas(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("vw_historico_entregas")
            .select("*")
            .order("entregue_em", desc=True)
            .order("apontamento_entrega_id", desc=True)
            .limit(5000)
            .execute()
        )
        return response.data or []

    def devolver_material(
        self,
        apontamento_entrega_id: int,
        quantidade: Decimal | str | float,
        nome_operador: str,
        observacao: str | None = None,
    ) -> dict[str, Any]:
        quantidade_normalizada = self._normalizar_quantidade(
            quantidade,
            "Quantidade devolvida inválida.",
        )

        response = self.client.rpc(
            "devolver_material",
            {
                "p_apontamento_entrega_id": apontamento_entrega_id,
                "p_quantidade": float(quantidade_normalizada),
                "p_nome_operador": nome_operador.strip(),
                "p_observacao": observacao.strip() if observacao else None,
            },
        ).execute()

        return self._obter_resultado_rpc(
            response.data,
            "O Supabase não retornou o resultado da devolução.",
        )

    def listar_historico_devolucoes(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("vw_historico_devolucoes")
            .select("*")
            .order("devolvido_em", desc=True)
            .order("devolucao_id", desc=True)
            .limit(5000)
            .execute()
        )
        return response.data or []

    @staticmethod
    def _normalizar_quantidade(
        quantidade: Decimal | str | float,
        mensagem: str,
    ) -> Decimal:
        try:
            return Decimal(str(quantidade).replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError(mensagem) from exc

    @staticmethod
    def _obter_resultado_rpc(data: Any, mensagem_erro: str) -> dict[str, Any]:
        if isinstance(data, list) and data:
            resultado = data[0]
            if isinstance(resultado, dict):
                return resultado

        if isinstance(data, dict):
            return data

        raise RuntimeError(mensagem_erro)
