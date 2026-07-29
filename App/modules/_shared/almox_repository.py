from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from modules._shared.supabase_client import get_supabase


class AlmoxRepository:
    '''
    Acesso centralizado às tabelas, visões e RPCs do Supabase.
    '''
    def __init__(self) -> None:
        self.client = get_supabase()

    def testar_conexao(self) -> None:
        self.client.table("emails_importados").select("id").limit(1).execute()

    def importar_email(
        self,
        email_payload: dict[str, Any],
        itens_requisicao: list[dict[str, Any]],
        itens_resumo: list[dict[str, Any]],
    ) -> dict[str, Any]:
        response = self.client.rpc(
            "emails_importados",
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

    def email_ja_importado(self, hash_arquivo: str) -> dict[str, Any] | None:
        response = (
            self.client.table("importacoes_email")
            .select("id,nome_arquivo,assunto,importado_em,importado_por")
            .eq("hash_arquivo", hash_arquivo)
            .limit(1)
            .execute()
        )
        dados = response.data or []
        return dados[0] if dados else None

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

    def consultar_material_fabrica(
        self,
        item_requisicao_id: int,
    ) -> dict[str, Any]:
        response = self.client.rpc(
            "consultar_material_fabrica",
            {"p_item_requisicao_id": item_requisicao_id},
        ).execute()
        return self._obter_resultado_rpc(
            response.data,
            "O Supabase não retornou o saldo em fábrica.",
        )

    def registrar_entrega_material_fabrica(
        self,
        item_requisicao_id: int,
        quantidade_fabrica: Decimal | str | float,
        nome_operador: str,
        observacao: str | None = None,
    ) -> dict[str, Any]:
        quantidade_normalizada = self._normalizar_quantidade(
            quantidade_fabrica,
            "Quantidade da fábrica inválida.",
        )
        response = self.client.rpc(
            "registrar_entrega_material_fabrica",
            {
                "p_item_requisicao_id": item_requisicao_id,
                "p_quantidade_fabrica": float(quantidade_normalizada),
                "p_nome_operador": nome_operador.strip(),
                "p_observacao": observacao.strip() if observacao else None,
            },
        ).execute()
        return self._obter_resultado_rpc(
            response.data,
            "O Supabase não retornou o resultado da entrega pela fábrica.",
        )

    def registrar_entrega_mista(
        self,
        item_requisicao_id: int,
        quantidade_nova: Decimal | str | float,
        nome_operador: str,
        observacao: str | None = None,
    ) -> dict[str, Any]:
        quantidade_normalizada = self._normalizar_quantidade(
            quantidade_nova,
            "Quantidade de material novo inválida.",
        )
        response = self.client.rpc(
            "registrar_entrega_mista",
            {
                "p_item_requisicao_id": item_requisicao_id,
                "p_quantidade_nova": float(quantidade_normalizada),
                "p_nome_operador": nome_operador.strip(),
                "p_observacao": observacao.strip() if observacao else None,
            },
        ).execute()
        return self._obter_resultado_rpc(
            response.data,
            "O Supabase não retornou o resultado da entrega mista.",
        )

    def listar_materiais_fabrica(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("vw_materiais_fabrica")
            .select("*")
            .gt("quantidade_disponivel", 0)
            .order("recebido_em", desc=True)
            .order("lote_material_fabrica_id", desc=True)
            .limit(5000)
            .execute()
        )
        return response.data or []

    def ajustar_material_fabrica(
        self,
        lote_material_fabrica_id: int,
        nova_quantidade: Decimal | str | float,
        nome_operador: str,
        observacao: str | None = None,
    ) -> dict[str, Any]:
        quantidade_normalizada = self._normalizar_quantidade_nao_negativa(
            nova_quantidade,
            "Nova quantidade inválida.",
        )
        response = self.client.rpc(
            "ajustar_material_fabrica",
            {
                "p_lote_material_fabrica_id": lote_material_fabrica_id,
                "p_nova_quantidade": float(quantidade_normalizada),
                "p_nome_operador": nome_operador.strip(),
                "p_observacao": observacao.strip() if observacao else None,
            },
        ).execute()
        return self._obter_resultado_rpc(
            response.data,
            "O Supabase não retornou o resultado do ajuste.",
        )

    def listar_requisicoes_baixa(self) -> list[dict[str, Any]]:
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
            .gt("quantidade_entregue", 0)
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

    def listar_lancamentos_totvs_pendentes(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("vw_lancamentos_totvs_pendentes")
            .select("*")
            .order("recebido_em_email", desc=False)
            .order("item_resumo_totvs_id", desc=False)
            .limit(5000)
            .execute()
        )
        return response.data or []

    def marcar_baixa_administrativa_totvs(
        self,
        item_resumo_ids: list[int],
        nome_responsavel: str,
    ) -> dict[str, Any]:
        ids = sorted({int(item_id) for item_id in item_resumo_ids})
        if not ids:
            raise ValueError("Selecione ao menos uma linha para baixar.")

        responsavel = nome_responsavel.strip()
        if not responsavel:
            raise ValueError("Informe quem está realizando a baixa.")

        response = self.client.rpc(
            "marcar_baixa_administrativa_totvs",
            {
                "p_item_resumo_ids": ids,
                "p_baixado_por": responsavel,
            },
        ).execute()

        return self._obter_resultado_rpc(
            response.data,
            "O Supabase não retornou o resultado da baixa administrativa.",
        )

    def listar_baixas_administrativas_totvs(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("vw_baixas_administrativas_totvs")
            .select("*")
            .order("baixado_em", desc=True)
            .order("baixa_administrativa_id", desc=True)
            .limit(5000)
            .execute()
        )
        return response.data or []

    def estornar_baixa_administrativa_totvs(
        self,
        baixa_ids: list[int],
        nome_responsavel: str,
    ) -> dict[str, Any]:
        ids = sorted({int(baixa_id) for baixa_id in baixa_ids})
        if not ids:
            raise ValueError("Selecione ao menos uma baixa para estornar.")

        responsavel = nome_responsavel.strip()
        if not responsavel:
            raise ValueError("Informe quem está realizando o estorno.")

        response = self.client.rpc(
            "estornar_baixa_resumo_totvs",
            {
                "p_baixa_ids": ids,
                "p_estornado_por": responsavel,
            },
        ).execute()

        return self._obter_resultado_rpc(
            response.data,
            "O Supabase não retornou o resultado do estorno administrativo.",
        )

    @staticmethod
    def _normalizar_quantidade(
        quantidade: Decimal | str | float,
        mensagem: str,
    ) -> Decimal:
        try:
            valor = Decimal(str(quantidade).replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError(mensagem) from exc

        if valor <= 0:
            raise ValueError(mensagem)

        return valor

    @staticmethod
    def _normalizar_quantidade_nao_negativa(
        quantidade: Decimal | str | float,
        mensagem: str,
    ) -> Decimal:
        try:
            valor = Decimal(str(quantidade).replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError(mensagem) from exc

        if valor < 0:
            raise ValueError(mensagem)

        return valor

    @staticmethod
    def _obter_resultado_rpc(
        data: Any,
        mensagem_erro: str,
    ) -> dict[str, Any]:
        if isinstance(data, list) and data:
            resultado = data[0]
            if isinstance(resultado, dict):
                return resultado

        if isinstance(data, dict):
            return data

        raise RuntimeError(mensagem_erro)
