from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ItemRequisicao:
    local_estoque: str
    tipo_material: str
    material: str
    dimensao: str
    quantidade: Decimal
    rastreabilidade: str
    data_requisicao: str | None
    maquina: str
    localizacao: str
    setor: str
    peso_material_kg: Decimal
    peso_requisitado_kg: Decimal
    indice_tabela_origem: int
    indice_linha_origem: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo_requisicao": self.local_estoque,
            "tipo_material": self.tipo_material,
            "material": self.material,
            "dimensao": self.dimensao,
            "quantidade": float(self.quantidade),
            "rastreabilidade": self.rastreabilidade,
            "data_requisicao": self.data_requisicao,
            "maquina": self.maquina,
            "localizacao_est": self.localizacao,
            "setor_dest": self.setor,
            "peso_material_kg": float(self.peso_material_kg),
            "peso_requisitado_kg": float(self.peso_requisitado_kg),
            "indice_tabela_origem": self.indice_tabela_origem,
            "indice_linha_origem": self.indice_linha_origem,
        }

@dataclass(slots=True)
class ItemResumoTotvs:
    local_estoque: str
    tipo_material: str
    numero_requisicao: str
    material: str
    os_so: str
    numero_of: str
    peso_material_kg: Decimal
    peso_requisitado_kg: Decimal
    indice_tabela_origem: int
    indice_linha_origem: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "tipo_requisicao": self.local_estoque,
            "tipo_material": self.tipo_material,
            "numero_requisicao": self.numero_requisicao,
            "material": self.material,
            "os_so": self.os_so,
            "numero_of": self.numero_of,
            "peso_material_kg": float(self.peso_material_kg),
            "peso_requisitado_kg": float(self.peso_requisitado_kg),
            "indice_tabela_origem": self.indice_tabela_origem,
            "indice_linha_origem": self.indice_linha_origem,
        }

@dataclass(slots=True)
class EmailProcessado:
    caminho: Path
    hash_arquivo: str
    assunto: str
    remetente: str
    recebido_em: str | None
    tipo_requisicao: str
    tipo_material: str
    itens_requisicao: list[ItemRequisicao] = field(default_factory=list)
    itens_resumo: list[ItemResumoTotvs] = field(default_factory=list)

    @property
    def peso_detalhes(self) -> Decimal:
        return sum(
            (item.peso_requisitado_kg for item in self.itens_requisicao),
            start=Decimal("0"),
        )

    @property
    def peso_resumos(self) -> Decimal:
        return sum(
            (item.peso_requisitado_kg for item in self.itens_resumo),
            start=Decimal("0"),
        )

    @property
    def diferenca_peso(self) -> Decimal:
        return abs(self.peso_detalhes - self.peso_resumos)

    def payload_email(self, importado_por: str) -> dict[str, Any]:
        return {
            "hash_arquivo": self.hash_arquivo,
            "nome_arquivo": self.caminho.name,
            "assunto": self.assunto,
            "remetente": self.remetente,
            "recebido_em": self.recebido_em,
            "tipo_requisicao": self.tipo_requisicao,
            "tipo_material": self.tipo_material,
            "importado_por": importado_por,
        }

    def payload_itens_requisicao(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.itens_requisicao]

    def payload_itens_resumo(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.itens_resumo]

# Apelidos temporários para facilitar a transição de imports antigos.
RequestItem = ItemRequisicao
SummaryItem = ItemResumoTotvs
ParsedEmail = EmailProcessado
