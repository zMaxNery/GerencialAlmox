"""Catálogo de códigos extraído da aba Base_de_Dados da planilha legada.

A consulta compara a bitola completa (não um trecho) e a qualidade. Assim,
"2X3/16" não pode ser confundido com "1.1/2X3/16". Se houver zero ou mais de
uma correspondência no catálogo, o registro fica marcado para conferência.
"""

from __future__ import annotations

import re

CODIGO_PENDENTE = "Não Identificado"

CATALOGO_PRODUTOS: tuple[tuple[str, str], ...] = (
    ("10000", "L45X4MM A572G50"),
    ("10001", "L45X5MM A572G50"),
    ("10002", "L40X4MM A572G50"),
    ("10003", "L45X3MM A572G50"),
    ("10004", "L40X5MM A572G50"),
    ("10024", "L100X10MM A572G50"),
    ("10025", "L100X8MM A572G50"),
    ("10104", "L3/4X1/8 A36"),
    ("10204", "L1X1/8 A36"),
    ("10300", "L1X3/16 A36"),
    ("10301", "L1.1/4X1/4 A36"),
    ("10304", "L1.1/4X1/8 A36"),
    ("10310", "L1.1/4X3/16 A36"),
    ("10354", "L1.1/2X1/8 A36"),
    ("10355", "L1.1/2X1/8 A572G50"),
    ("10357", "L1.1/2X3/16 A36"),
    ("10358", "L1.1/2X3/16 A572G50"),
    ("10360", "L1.1/2X1/4 A572G50"),
    ("10404", "L1.3/4X1/8 A36"),
    ("10405", "L1.3/4X1/8 A572G50"),
    ("10407", "L1.3/4X3/16 A36"),
    ("10408", "L1.3/4X3/16 A572G50"),
    ("10410", "L1.3/4X1/4 A36"),
    ("10411", "L1.3/4X1/4 A572G50"),
    ("10454", "L2X1/8 A36"),
    ("10455", "L2X1/8 A572G50"),
    ("10457", "L2X3/16 A36"),
    ("10458", "L2X3/16 A572G50"),
    ("10460", "L2X1/4 A36"),
    ("10461", "L2X1/4 A572G50"),
    ("10462", "L2X5/16 A572G50"),
    ("10464", "L2X5/16 A36"),
    ("10466", "L2X3/8 A36"),
    ("10467", "L2X3/8 A572G50"),
    ("10607", "L2.1/2X3/16 A36"),
    ("10608", "L2.1/2X3/16 A572G50"),
    ("10610", "L2.1/2X1/4 A36"),
    ("10611", "L2.1/2X1/4 A572G50"),
    ("10612", "L2.1/2X1/4 A572G60"),
    ("10613", "L2.1/2X5/16 A36"),
    ("10614", "L2.1/2X5/16 A572G50"),
    ("10616", "L2.1/2X3/8 A36"),
    ("10617", "L2.1/2X3/8 A572G50"),
    ("10707", "L3X3/16 A36"),
    ("10708", "L3X3/16 A572G50"),
    ("10710", "L3X1/4 A36"),
    ("10711", "L3X1/4 A572G50"),
    ("10713", "L3X5/16 A36"),
    ("10714", "L3X5/16 A572G50"),
    ("10715", "L3X3/8 A572G50"),
    ("10716", "L3X3/8 A36"),
    ("10717", "L3X5/16 A572G60"),
    ("10718", "L3X1/2 A36"),
    ("10719", "L3X1/2 A572G50"),
    ("10720", "L3.1/2X5/16 A36"),
    ("10730", "L3.1/2X1/4 A36"),
    ("10731", "L3.1/2X1/4 A572G50"),
    ("10733", "L3.1/2X5/16 A572G50"),
    ("10737", "L3.1/2X3/8 A36"),
    ("10738", "L3.1/2X3/8 A572G50"),
    ("10741", "L4X1/4 A572G60"),
    ("10742", "L4X1/4 A36"),
    ("10743", "L4X1/4 A572G50"),
    ("10744", "L4X5/16 A572G60"),
    ("10745", "L4X5/16 A36"),
    ("10746", "L4X5/16 A572G50"),
    ("10747", "L4X3/8 A36"),
    ("10748", "L4X3/8 A572G50"),
    ("10749", "L4X3/8 A572G60"),
    ("10752", "L4X1/2 A572G60"),
    ("10753", "L4X1/2 A36"),
    ("10754", "L4X1/2 A572G50"),
    ("10755", "L4X7/16 A36"),
    ("10756", "L4X5/8 A572G50"),
    ("10758", "L4X5/8 A572G60"),
    ("10763", "L5X5/16 A36"),
    ("10764", "L5X3/8 A36"),
    ("10765", "L5X3/8 A572G50"),
    ("10766", "L5X3/8 A572G60"),
    ("10767", "L5X5/8 A572G60"),
    ("10768", "L5X5/8 A572G50"),
    ("10769", "L5X5/16 A572G50"),
    ("10770", "L5X1/2 A36"),
    ("10771", "L5X1/2 A572G50"),
    ("10772", "L5X1/2 A572G60"),
    ("10784", "L6X3/8 A36"),
    ("10785", "L6X3/8 A572G50"),
    ("10790", "L6X1/2 A36"),
    ("10791", "L6X1/2 A572G50"),
    ("10792", "L6X1/2 A572G60"),
    ("10796", "L6X5/8 A36"),
    ("10797", "L6X5/8 A572G50"),
    ("10798", "L6X5/8 A572G60"),
    ("10803", "L6X3/4 A572G50"),
    ("10804", "L6X3/4 A36"),
    ("10818", "L8X5/8 A572G50"),
    ("10824", "L8X3/4 A36"),
    ("10870", "L4X3X1/4 A36"),
    ("10905", "L40X3MM A36"),
    ("10906", "L50X4MM A36"),
    ("10907", "L60X4MM A572G50"),
    ("10908", "L60X5MM A572G50"),
    ("10909", "L60X6MM A572G50"),
    ("10910", "L65X5MM A572G50"),
    ("10911", "L50X3MM A572G50"),
    ("10912", "L50X5MM A572G50"),
    ("10913", "L65X4MM A572G50"),
    ("10914", "L65X6MM A572G50"),
    ("10916", "L75X6MM A572G50"),
    ("10917", "L90X6MM A572G50"),
    ("10918", "L90X8MM A572G50"),
    ("10919", "L75X5MM A572G50"),
    ("10920", "L75X6MM A572G60"),
    ("10921", "L75X7MM A572G50"),
    ("10922", "L90X7MM A572G50"),
    ("10923", "L100X7MM A572G50"),
    ("10924", "L50X4MM A572G50"),
    ("BF00033", "L4X5/8 A36"),
    ("BF00129", "L155X60X6MM A36"),
    ("BF05666", "L40X3MM A572G50"),
    ("BF05683", "L1.1/4X1/8 A572G50"),
    ("BF05750", "L5X5/8 A36"),
    ("BF05966", "L75X8MM A572G50"),
    ("BF06674", "L1.1/2X1/4 A36"),
    ("BF08295", "L75X5MM A572G60"),
    ("BF08296", "L90X7MM A572G60"),
    ("BF08297", "L75X7MM A572G60"),
    ("BF08298", "L100X12MM A572G60"),
    ("BF08323", "L90X6MM A572G60"),
    ("BF08392", "L6X3/8 A572G60"),
    ("BF08496", "L50X4MM A572G60"),
    ("BF08570", "L7/8X1/8 A36"),
    ("BF08856", "L100X6MM A572G50"),
    ("BF09029", "L50X3MM A572G60"),
    ("BF10381", "L100X6MM A572G60"),
    ("BF11885", "L75X8MM A572G60"),
    ("BF11939", "L50X6MM A572G50"),
    ("BF12253", "L45X4MM A572G60"),
    ("BF12255", "L45X5MM A572G60"),
    ("BF12262", "L65X6MM A572G60"),
    ("BF13485", "L40X4MM A572G60"),
    ("ZZ4BB", "L100X12MM A572G50"),
    ("ZZ4CE", "L100X10MM A572G60"),
    ("ZZ4CF", "L100X7MM A572G60"),
    ("ZZ4CG", "L100X8MM A572G60"),
    ("ZZ4MS", "L8X3/4 A572G50"),
    ("ZZ4QG", "L65X5MM A572G60"),
    ("ZZ5X1", "L8X3/4 A572G60"),
    ("ZZ6V3", "L65X4MM A572G60"),
    ("ZZ6VX", "L40X5MM A572G60"),
    ("ZZ7CV", "L60X5MM A572G60"),
    ("ZZ7NI", "L60X4MM A572G60"),
    ("ZZ7NJ", "L60X6MM A572G60"),
    ("ZZ7NK", "L6X3/4 A572G60"),
    ("ZZ7NL", "L8X5/8 A572G60"),
    ("ZZBOC", "L90X8MM A572G60"),
    ("ZZCLU", "L2X1/8 A572G60"),
    ("ZZCYD", "L5X5/16 A572G60"),
    ("ZZDXN", "L3X1/4 A572G60"),
    ("ZZDXP", "L3X3/16 A572G60"),
    ("ZZE5Q", "L2.1/2X3/16 A572G60"),
    ("ZZFD0", "L45X3MM A572G60"),
    ("ZZFMN", "L40X3MM A572G60"),
    ("ZZGB4", "L50X5MM A572G60"),
    ("ZZHZL", "L5X7/16 A572G60"),
    ("ZZJNG", "L2X3/16 A572G60"),
    ("ZZJOJ", "L50X6MM A572G60"),
    ("ZZKW2", "L100X9MM A572G50"),
    ("ZZKW3", "L100X9MM A572G60"),
    ("ZZL85", "L2X1/4 A572G60"),
    ("ZZLOC", "L200X16 A572G60"),
    ("ZZLSC", "L3X3/8 A572G60"),
    ("TESTE", "TESTETESTE"),
)


def _compactar(valor: str | None) -> str:
    return re.sub(r"\s+", "", str(valor or "").upper().replace("×", "X"))


def _normalizar_bitola(valor: str | None) -> str:
    texto = _compactar(valor)
    if texto.startswith("L"):
        texto = texto[1:]
    if texto.endswith("MM"):
        texto = texto[:-2]
    return texto


def _normalizar_qualidade(valor: str | None) -> str:
    texto = _compactar(valor)
    if texto.startswith("A572"):
        texto = texto[4:]
    return texto


def _separar_descricao(descricao: str) -> tuple[str, str] | None:
    """Extrai bitola e qualidade de descrições como L45X4MM A572G50."""
    texto = _compactar(descricao)
    correspondencia = re.fullmatch(
        r"L?(.+?)(?:MM)?(A36|A572G50|A572G60)",
        texto,
    )
    if not correspondencia:
        return None

    bitola = _normalizar_bitola(correspondencia.group(1))
    qualidade = _normalizar_qualidade(correspondencia.group(2))
    if not bitola or not qualidade:
        return None
    return bitola, qualidade


def buscar_codigo_produto(
    bitola: str | None,
    qualidade: str | None,
) -> str | None:
    """Retorna código apenas quando existir uma única correspondência exata.

    Retorna None enquanto bitola ou qualidade estiverem vazias. Para uma busca
    completa sem resultado, ou com duplicidade no catálogo, retorna
    CODIGO_PENDENTE para que o usuário possa corrigir o código na edição.
    """
    bitola_busca = _normalizar_bitola(bitola)
    qualidade_busca = _normalizar_qualidade(qualidade)
    if not bitola_busca or not qualidade_busca:
        return None

    chave = (bitola_busca, qualidade_busca)
    correspondencias: list[str] = []
    for codigo, descricao in CATALOGO_PRODUTOS:
        if _separar_descricao(descricao) == chave:
            correspondencias.append(str(codigo).strip())

    # Não escolhe arbitrariamente nenhum código: ausência ou duplicidade exige
    # conferência manual do usuário.
    if len(correspondencias) != 1:
        return CODIGO_PENDENTE
    return correspondencias[0]
