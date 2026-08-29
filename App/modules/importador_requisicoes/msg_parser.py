from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import extract_msg
from bs4 import BeautifulSoup

from modules.importador_requisicoes.models import (
    EmailProcessado,
    ItemRequisicao,
    ItemResumoTotvs,
)

class MsgParser:
    DETAIL_REQUIRED = {"MATERIAL", "DIMENSAO", "QTDE", "RASTREABILIDADE"}
    SUMMARY_REQUIRED = {"REQUISICAO", "MATERIAL", "OS SO", "OF"}

    def parse(self, path: str | Path) -> EmailProcessado:
        msg_path = Path(path)

        if not msg_path.exists():
            raise FileNotFoundError(msg_path)

        if msg_path.suffix.lower() != ".msg":
            raise ValueError("O arquivo precisa ter extensão .msg.")

        message = extract_msg.Message(str(msg_path))
        try:
            html = message.htmlBody

            if isinstance(html, bytes):
                decoded = None
                for encoding in ("utf-8-sig", "cp1252", "latin1"):
                    try:
                        decoded = html.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                html = decoded or html.decode("utf-8", errors="replace")

            if not html:
                raise ValueError("A mensagem não possui corpo HTML com tabelas.")

            assunto = self._clean(message.subject)
            remetente = self._clean(message.sender)
            recebido_em = self._to_iso(message.date)
        finally:
            message.close()

        parsed = self.parse_html(
            html=html,
            caminho=msg_path,
            hash_arquivo=self.calcular_hash(msg_path),
            assunto=assunto,
            remetente=remetente,
            recebido_em=recebido_em,
        )

        if not parsed.itens_requisicao:
            raise ValueError("Nenhuma tabela detalhada de requisição foi encontrada.")

        if not parsed.itens_resumo:
            raise ValueError("Nenhuma tabela de resumo TOTVS foi encontrada.")

        return parsed

    def parse_html(
        self,
        html: str,
        caminho: Path,
        hash_arquivo: str,
        assunto: str,
        remetente: str,
        recebido_em: str | None,
    ) -> EmailProcessado:
        soup = BeautifulSoup(html, "lxml")
        all_text = self._normalize(soup.get_text(" ", strip=True))

        local_estoque = self._detect_stock_location(all_text)
        tipo_movimento = self._detect_movement_type(assunto, local_estoque)

        itens_requisicao: list[ItemRequisicao] = []
        itens_resumo: list[ItemResumoTotvs] = []

        for indice_tabela, table in enumerate(soup.find_all("table"), start=1):
            rows = self._extract_rows(table)
            if not rows:
                continue

            header_info = self._find_header(rows)
            if header_info is None:
                continue

            header_row_index, table_kind, tipo_material = header_info
            headers = [self._normalize(cell) for cell in rows[header_row_index]]

            for indice_linha, values in enumerate(
                rows[header_row_index + 1 :],
                start=header_row_index + 2,
            ):
                if not any(self._clean(value) for value in values):
                    continue

                padded = values + [""] * max(0, len(headers) - len(values))

                try:
                    if table_kind == "DETAIL":
                        item = self._parse_detail_row(
                            headers,
                            padded,
                            local_estoque,
                            tipo_material,
                            indice_tabela,
                            indice_linha,
                        )
                        if item:
                            itens_requisicao.append(item)
                    else:
                        item = self._parse_summary_row(
                            headers,
                            padded,
                            local_estoque,
                            tipo_material,
                            indice_tabela,
                            indice_linha,
                        )
                        if item:
                            itens_resumo.append(item)
                except Exception as exc:
                    raise ValueError(
                        f"Falha na tabela {indice_tabela}, linha {indice_linha}: {exc}"
                    ) from exc

        return EmailProcessado(
            caminho=caminho,
            hash_arquivo=hash_arquivo,
            assunto=assunto,
            remetente=remetente,
            recebido_em=recebido_em,
            tipo_requisicao=local_estoque,
            tipo_material=tipo_movimento,
            itens_requisicao=itens_requisicao,
            itens_resumo=itens_resumo,
        )

    def _parse_detail_row(
        self,
        headers: list[str],
        values: list[str],
        local_estoque: str,
        tipo_material: str,
        indice_tabela: int,
        indice_linha: int,
    ) -> ItemRequisicao | None:
        material = self._value(headers, values, lambda h: h == "MATERIAL")

        if not material or self._normalize(material) in {"TOTAL", "MATERIAL"}:
            return None

        return ItemRequisicao(
            tipo_material=tipo_material,
            local_estoque=local_estoque,
            material=material,
            dimensao=self._value(headers, values, lambda h: h == "DIMENSAO"),
            quantidade=self._parse_decimal(
                self._value(headers, values, lambda h: h in {"QTDE", "QUANTIDADE"})
            ),
            rastreabilidade=self._value(
                headers, values, lambda h: h == "RASTREABILIDADE"
            ),
            data_requisicao=self._parse_date(
                self._value(headers, values, lambda h: h == "DATA")
            ),
            maquina=self._value(headers, values, lambda h: h == "MAQUINA"),
            localizacao=self._value(headers, values, lambda h: h == "LOCALIZACAO"),
            setor=self._value(headers, values, lambda h: h == "SETOR"),
            peso_material_kg=self._parse_decimal(
                self._value(
                    headers,
                    values,
                    lambda h: h.startswith("PESO ")
                    and ("CHAPA" in h or "PERFIL" in h),
                )
            ),
            peso_requisitado_kg=self._parse_decimal(
                self._value(
                    headers,
                    values,
                    lambda h: h.startswith("PESO")
                    and "CHAPA" not in h
                    and "PERFIL" not in h,
                    prefer_last=True,
                )
            ),
            indice_tabela_origem=indice_tabela,
            indice_linha_origem=indice_linha,
        )

    def _parse_summary_row(
        self,
        headers: list[str],
        values: list[str],
        local_estoque: str,
        tipo_material: str,
        indice_tabela: int,
        indice_linha: int,
    ) -> ItemResumoTotvs | None:
        numero_requisicao = self._value(
            headers, values, lambda h: h == "REQUISICAO"
        )
        material = self._value(headers, values, lambda h: h == "MATERIAL")

        if not numero_requisicao and not material:
            return None

        if self._normalize(numero_requisicao) in {"TOTAL", "REQUISICAO"}:
            return None

        return ItemResumoTotvs(
            tipo_material=tipo_material,
            local_estoque=local_estoque,
            numero_requisicao=numero_requisicao,
            material=material,
            os_so=self._value(headers, values, lambda h: h == "OS SO"),
            numero_of=self._value(headers, values, lambda h: h == "OF"),
            peso_material_kg=self._parse_decimal(
                self._value(
                    headers,
                    values,
                    lambda h: h.startswith("PESO ")
                    and ("CHAPA" in h or "PERFIL" in h),
                )
            ),
            peso_requisitado_kg=self._parse_decimal(
                self._value(
                    headers,
                    values,
                    lambda h: h.startswith("PESO")
                    and "CHAPA" not in h
                    and "PERFIL" not in h,
                    prefer_last=True,
                )
            ),
            indice_tabela_origem=indice_tabela,
            indice_linha_origem=indice_linha,
        )

    def _find_header(
        self, rows: list[list[str]]
    ) -> tuple[int, str, str] | None:
        for index, row in enumerate(rows):
            normalized = [self._normalize(value) for value in row]
            normalized_set = set(normalized)

            tipo_material = ""
            if any("PESO CHAPA" in value for value in normalized):
                tipo_material = "CHAPA"
            elif any("PESO PERFIL" in value for value in normalized):
                tipo_material = "PERFIL"

            if not tipo_material:
                continue

            if self.DETAIL_REQUIRED.issubset(normalized_set):
                return index, "DETAIL", tipo_material

            if self.SUMMARY_REQUIRED.issubset(normalized_set):
                return index, "SUMMARY", tipo_material

        return None

    @staticmethod
    def _extract_rows(table) -> list[list[str]]:
        rows: list[list[str]] = []

        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"], recursive=False)
            if not cells:
                cells = tr.find_all(["th", "td"])

            values = [
                " ".join(cell.get_text(" ", strip=True).split()) for cell in cells
            ]
            if values:
                rows.append(values)

        return rows

    def _value(
        self,
        headers: list[str],
        values: list[str],
        predicate,
        prefer_last: bool = False,
    ) -> str:
        indexes = [index for index, header in enumerate(headers) if predicate(header)]
        if not indexes:
            return ""

        index = indexes[-1] if prefer_last else indexes[0]
        return self._clean(values[index] if index < len(values) else "")

    @staticmethod
    def calcular_hash(path: Path) -> str:
        # A identificação é baseada no Internet Message-ID. Quando ele não
        # existe, usa uma impressão digital canônica do conteúdo do e-mail.
        # Dessa forma, salvar o mesmo e-mail novamente como .msg não cria
        # uma chave diferente apenas porque o arquivo binário foi recriado.
        from modules._shared.email_identity import calcular_identificador_msg

        return calcular_identificador_msg(path)

    # Mantém o nome antigo para chamadas externas já existentes.
    calculate_hash = calcular_hash

    def _detect_stock_location(self, normalized_text: str) -> str:
        if "LOCAL DE ESTOQUE EST" in normalized_text:
            return "EST"
        if "LOCAL DE ESTOQUE FAB" in normalized_text:
            return "FAB"
        raise ValueError("Não foi possível identificar o local de estoque EST/FAB.")

    def _detect_movement_type(self, subject: str, stock_location: str) -> str:
        normalized = self._normalize(subject)

        if "RETALHO" in normalized:
            return "RETALHO"
        if "PECA INTEIRA" in normalized or "BARRA EM ESTOQUE" in normalized:
            return "PECA_INTEIRA"

        return "RETALHO" if stock_location == "FAB" else "PECA_INTEIRA"

    @staticmethod
    def _parse_decimal(value: str) -> Decimal:
        cleaned = value.strip().replace("R$", "").replace("kg", "").replace("KG", "")
        cleaned = re.sub(r"\s+", "", cleaned)

        if not cleaned or cleaned == "-":
            return Decimal("0")

        if "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")

        cleaned = re.sub(r"[^0-9.\-]", "", cleaned)

        try:
            return Decimal(cleaned or "0")
        except InvalidOperation as exc:
            raise ValueError(f"Número inválido: {value!r}") from exc

    @staticmethod
    def _parse_date(value: str) -> str | None:
        cleaned = value.strip()
        if not cleaned:
            return None

        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(cleaned, fmt).date().isoformat()
            except ValueError:
                continue

        match = re.search(r"(\d{2})/(\d{2})/(\d{4})", cleaned)
        if match:
            day, month, year = match.groups()
            return date(int(year), int(month), int(day)).isoformat()

        raise ValueError(f"Data inválida: {value!r}")

    @staticmethod
    def _to_iso(value) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value).strip() or None

    @staticmethod
    def _clean(value) -> str:
        if value is None:
            return ""
        return " ".join(str(value).replace("\xa0", " ").split()).strip()

    @classmethod
    def _normalize(cls, value) -> str:
        cleaned = cls._clean(value).upper()
        cleaned = "".join(
            char
            for char in unicodedata.normalize("NFKD", cleaned)
            if not unicodedata.combining(char)
        )
        return re.sub(r"[^A-Z0-9]+", " ", cleaned).strip()
