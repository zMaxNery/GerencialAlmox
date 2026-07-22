from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class RequestItem:
    material_type: str
    stock_location: str
    material: str
    dimension: str
    quantity: Decimal
    traceability: str
    request_date: str | None
    machine: str
    location: str
    sector: str
    material_weight_kg: Decimal
    requested_weight_kg: Decimal
    source_table_index: int
    source_row_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "material_type": self.material_type,
            "stock_location": self.stock_location,
            "material": self.material,
            "dimension": self.dimension,
            "quantity": float(self.quantity),
            "traceability": self.traceability,
            "request_date": self.request_date,
            "machine": self.machine,
            "location": self.location,
            "sector": self.sector,
            "material_weight_kg": float(self.material_weight_kg),
            "requested_weight_kg": float(self.requested_weight_kg),
            "source_table_index": self.source_table_index,
            "source_row_index": self.source_row_index,
        }


@dataclass(slots=True)
class SummaryItem:
    material_type: str
    stock_location: str
    request_number: str
    material: str
    os_so: str
    of_number: str
    material_weight_kg: Decimal
    requested_weight_kg: Decimal
    source_table_index: int
    source_row_index: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "material_type": self.material_type,
            "stock_location": self.stock_location,
            "request_number": self.request_number,
            "material": self.material,
            "os_so": self.os_so,
            "of_number": self.of_number,
            "material_weight_kg": float(self.material_weight_kg),
            "requested_weight_kg": float(self.requested_weight_kg),
            "source_table_index": self.source_table_index,
            "source_row_index": self.source_row_index,
        }


@dataclass(slots=True)
class ParsedEmail:
    path: Path
    file_hash: str
    subject: str
    sender: str
    received_at: str | None
    stock_location: str
    movement_type: str
    request_items: list[RequestItem] = field(default_factory=list)
    summary_items: list[SummaryItem] = field(default_factory=list)

    @property
    def detail_weight(self) -> Decimal:
        return sum(
            (item.requested_weight_kg for item in self.request_items),
            start=Decimal("0"),
        )

    @property
    def summary_weight(self) -> Decimal:
        return sum(
            (item.requested_weight_kg for item in self.summary_items),
            start=Decimal("0"),
        )

    @property
    def weight_difference(self) -> Decimal:
        return abs(self.detail_weight - self.summary_weight)

    def email_payload(self, imported_by: str) -> dict[str, Any]:
        return {
            "file_hash": self.file_hash,
            "file_name": self.path.name,
            "subject": self.subject,
            "sender": self.sender,
            "received_at": self.received_at,
            "stock_location": self.stock_location,
            "movement_type": self.movement_type,
            "imported_by": imported_by,
        }

    def request_payload(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.request_items]

    def summary_payload(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.summary_items]
