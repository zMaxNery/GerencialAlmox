from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import extract_msg
from bs4 import BeautifulSoup

from modules.importador_emails.models import ParsedEmail, RequestItem, SummaryItem


class MsgParser:
    DETAIL_REQUIRED = {"MATERIAL", "DIMENSAO", "QTDE", "RASTREABILIDADE"}
    SUMMARY_REQUIRED = {"REQUISICAO", "MATERIAL", "OS SO", "OF"}

    def parse(self, path: str | Path) -> ParsedEmail:
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

            subject = self._clean(message.subject)
            sender = self._clean(message.sender)
            received_at = self._to_iso(message.date)
        finally:
            message.close()

        parsed = self.parse_html(
            html=html,
            path=msg_path,
            file_hash=self.calculate_hash(msg_path),
            subject=subject,
            sender=sender,
            received_at=received_at,
        )

        if not parsed.request_items:
            raise ValueError("Nenhuma tabela detalhada de requisição foi encontrada.")
        if not parsed.summary_items:
            raise ValueError("Nenhuma tabela de resumo TOTVS foi encontrada.")

        return parsed

    def parse_html(
        self,
        html: str,
        path: Path,
        file_hash: str,
        subject: str,
        sender: str,
        received_at: str | None,
    ) -> ParsedEmail:
        soup = BeautifulSoup(html, "lxml")
        all_text = self._normalize(soup.get_text(" ", strip=True))

        stock_location = self._detect_stock_location(all_text)
        movement_type = self._detect_movement_type(subject, stock_location)

        request_items: list[RequestItem] = []
        summary_items: list[SummaryItem] = []

        for table_index, table in enumerate(soup.find_all("table"), start=1):
            rows = self._extract_rows(table)
            if not rows:
                continue

            header_info = self._find_header(rows)
            if header_info is None:
                continue

            header_row_index, table_kind, material_type = header_info
            headers = [self._normalize(cell) for cell in rows[header_row_index]]

            for source_row_index, values in enumerate(
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
                            stock_location,
                            material_type,
                            table_index,
                            source_row_index,
                        )
                        if item:
                            request_items.append(item)
                    else:
                        item = self._parse_summary_row(
                            headers,
                            padded,
                            stock_location,
                            material_type,
                            table_index,
                            source_row_index,
                        )
                        if item:
                            summary_items.append(item)
                except Exception as exc:
                    raise ValueError(
                        f"Falha na tabela {table_index}, linha {source_row_index}: {exc}"
                    ) from exc

        return ParsedEmail(
            path=path,
            file_hash=file_hash,
            subject=subject,
            sender=sender,
            received_at=received_at,
            stock_location=stock_location,
            movement_type=movement_type,
            request_items=request_items,
            summary_items=summary_items,
        )

    def _parse_detail_row(
        self,
        headers: list[str],
        values: list[str],
        stock_location: str,
        material_type: str,
        table_index: int,
        row_index: int,
    ) -> RequestItem | None:
        material = self._value(headers, values, lambda h: h == "MATERIAL")
        if not material or self._normalize(material) in {"TOTAL", "MATERIAL"}:
            return None

        return RequestItem(
            material_type=material_type,
            stock_location=stock_location,
            material=material,
            dimension=self._value(headers, values, lambda h: h == "DIMENSAO"),
            quantity=self._parse_decimal(
                self._value(headers, values, lambda h: h in {"QTDE", "QUANTIDADE"})
            ),
            traceability=self._value(
                headers, values, lambda h: h == "RASTREABILIDADE"
            ),
            request_date=self._parse_date(
                self._value(headers, values, lambda h: h == "DATA")
            ),
            machine=self._value(headers, values, lambda h: h == "MAQUINA"),
            location=self._value(headers, values, lambda h: h == "LOCALIZACAO"),
            sector=self._value(headers, values, lambda h: h == "SETOR"),
            material_weight_kg=self._parse_decimal(
                self._value(
                    headers,
                    values,
                    lambda h: h.startswith("PESO ")
                    and ("CHAPA" in h or "PERFIL" in h),
                )
            ),
            requested_weight_kg=self._parse_decimal(
                self._value(
                    headers,
                    values,
                    lambda h: h.startswith("PESO")
                    and "CHAPA" not in h
                    and "PERFIL" not in h,
                    prefer_last=True,
                )
            ),
            source_table_index=table_index,
            source_row_index=row_index,
        )

    def _parse_summary_row(
        self,
        headers: list[str],
        values: list[str],
        stock_location: str,
        material_type: str,
        table_index: int,
        row_index: int,
    ) -> SummaryItem | None:
        request_number = self._value(
            headers, values, lambda h: h == "REQUISICAO"
        )
        material = self._value(headers, values, lambda h: h == "MATERIAL")

        if not request_number and not material:
            return None
        if self._normalize(request_number) in {"TOTAL", "REQUISICAO"}:
            return None

        return SummaryItem(
            material_type=material_type,
            stock_location=stock_location,
            request_number=request_number,
            material=material,
            os_so=self._value(headers, values, lambda h: h == "OS SO"),
            of_number=self._value(headers, values, lambda h: h == "OF"),
            material_weight_kg=self._parse_decimal(
                self._value(
                    headers,
                    values,
                    lambda h: h.startswith("PESO ")
                    and ("CHAPA" in h or "PERFIL" in h),
                )
            ),
            requested_weight_kg=self._parse_decimal(
                self._value(
                    headers,
                    values,
                    lambda h: h.startswith("PESO")
                    and "CHAPA" not in h
                    and "PERFIL" not in h,
                    prefer_last=True,
                )
            ),
            source_table_index=table_index,
            source_row_index=row_index,
        )

    def _find_header(
        self, rows: list[list[str]]
    ) -> tuple[int, str, str] | None:
        for index, row in enumerate(rows):
            normalized = [self._normalize(value) for value in row]
            normalized_set = set(normalized)

            material_type = ""
            if any("PESO CHAPA" in value for value in normalized):
                material_type = "CHAPA"
            elif any("PESO PERFIL" in value for value in normalized):
                material_type = "PERFIL"

            if not material_type:
                continue

            if self.DETAIL_REQUIRED.issubset(normalized_set):
                return index, "DETAIL", material_type

            if self.SUMMARY_REQUIRED.issubset(normalized_set):
                return index, "SUMMARY", material_type

        return None

    @staticmethod
    def _extract_rows(table) -> list[list[str]]:
        rows: list[list[str]] = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"], recursive=False)
            if not cells:
                cells = tr.find_all(["th", "td"])
            values = [" ".join(cell.get_text(" ", strip=True).split()) for cell in cells]
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
    def calculate_hash(path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                hasher.update(chunk)
        return hasher.hexdigest()

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
