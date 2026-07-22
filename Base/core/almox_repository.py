from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from core.supabase_client import get_supabase


class AlmoxRepository:
    def __init__(self) -> None:
        self.client = get_supabase()

    def testar_conexao(self) -> None:
        self.client.table("email_imports").select("id").limit(1).execute()

    def importar_email(
        self,
        email_payload: dict[str, Any],
        request_items: list[dict[str, Any]],
        summary_items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        response = self.client.rpc(
            "import_email",
            {
                "p_email": email_payload,
                "p_request_items": request_items,
                "p_summary_items": summary_items,
            },
        ).execute()

        data = response.data
        if isinstance(data, list) and data:
            return data[0]
        if isinstance(data, dict):
            return data
        raise RuntimeError("O Supabase não retornou o resultado da importação.")

    def listar_pendencias_est(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("vw_operator_pending_est")
            .select("*")
            .order("request_date", desc=False)
            .order("request_item_id", desc=False)
            .limit(2000)
            .execute()
        )
        return response.data or []

    def registrar_entrega(
        self,
        request_item_id: int,
        quantity: Decimal | str | float,
        operator_name: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        try:
            normalized_quantity = Decimal(str(quantity).replace(",", "."))
        except InvalidOperation as exc:
            raise ValueError("Quantidade entregue inválida.") from exc

        response = self.client.rpc(
            "register_delivery",
            {
                "p_request_item_id": request_item_id,
                "p_quantity": float(normalized_quantity),
                "p_operator_name": operator_name.strip(),
                "p_note": note.strip() if note else None,
            },
        ).execute()

        data = response.data
        if isinstance(data, list) and data:
            return data[0]
        if isinstance(data, dict):
            return data
        raise RuntimeError("O Supabase não retornou o resultado do apontamento.")

    def listar_visao_administrativa(self) -> list[dict[str, Any]]:
        response = (
            self.client.table("vw_admin_requests")
            .select("*")
            .order("request_date", desc=True)
            .order("request_item_id", desc=True)
            .limit(3000)
            .execute()
        )
        return response.data or []
