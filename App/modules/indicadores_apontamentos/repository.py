from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from core.supabase_client import get_supabase


class IndicadoresRepository:
    """Consulta a visão de indicadores sem alterar dados operacionais."""

    _FUSO = ZoneInfo("America/Sao_Paulo")
    _TAMANHO_PAGINA = 1000

    def __init__(self) -> None:
        self.client = get_supabase()

    def listar_apontamentos(
        self,
        data_inicial: date,
        data_final: date,
    ) -> list[dict[str, Any]]:
        if data_final < data_inicial:
            raise ValueError("A data final não pode ser anterior à data inicial.")

        inicio = datetime.combine(data_inicial, time.min, tzinfo=self._FUSO)
        fim_exclusivo = datetime.combine(
            data_final + timedelta(days=1),
            time.min,
            tzinfo=self._FUSO,
        )

        campos = ",".join(
            (
                "apontamento_entrega_id",
                "item_requisicao_id",
                "email_importado_id",
                "data_entrega",
                "entregue_em",
                "usuario",
                "peso_bruto_entregue_kg",
                "peso_liquido_entregue_kg",
                "lead_time_horas",
            )
        )

        resultado: list[dict[str, Any]] = []
        inicio_pagina = 0

        while True:
            fim_pagina = inicio_pagina + self._TAMANHO_PAGINA - 1

            response = (
                self.client
                .table("vw_indicadores_apontamentos")
                .select(campos)
                .gte("entregue_em", inicio.isoformat())
                .lt("entregue_em", fim_exclusivo.isoformat())
                .order("entregue_em", desc=False)
                .order("apontamento_entrega_id", desc=False)
                .range(inicio_pagina, fim_pagina)
                .execute()
            )

            pagina = response.data or []
            resultado.extend(pagina)

            if len(pagina) < self._TAMANHO_PAGINA:
                break

            inicio_pagina += self._TAMANHO_PAGINA

        return resultado
