from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from sqlalchemy import text

TREBA_CONSULTA_CARTORIOS_URL = "https://extranet.tre-ba.jus.br/EndZE/"
HEADERS = {
    "User-Agent": "SIMOC-TREBA/1.2 (+uso-institucional; consulta-publica-tre-ba)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
ZE_RE = re.compile(r"(?P<zona>\d{1,3})\s*(?:ª|º|[o])?\s*ZE", re.I)
SEDE_RE = re.compile(r"Sede\s+da\s+", re.I)
EMAIL_RE = re.compile(r"[\w.\-]+@tre-ba\.jus\.br", re.I)
PHONE_RE = re.compile(r"\(?\d{2}\)?\s?\d{4,5}[- ]?\d{4}(?:\s*/\s*\d{4,5}[- ]?\d{4})?")


@dataclass(frozen=True)
class VinculoMunicipioZona:
    municipio: str
    zona: int
    sede: bool
    texto_original: str


def _clean(value: str | None) -> str:
    if value is None:
        return ""
    value = value.replace("\xa0", " ").replace("�", "ª")
    return re.sub(r"\s+", " ", value).strip()


def _response_text(resp: requests.Response) -> str:
    for encoding in ("utf-8", "iso-8859-1", "latin-1"):
        try:
            text_value = resp.content.decode(encoding)
            if "Munic" in text_value or "Zona" in text_value or "Cart" in text_value:
                return text_value
        except UnicodeDecodeError:
            continue
    return resp.text


def baixar_html_consulta(url: str = TREBA_CONSULTA_CARTORIOS_URL) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=40)
    resp.raise_for_status()
    return _response_text(resp)


def _vinculo_from_text(texto: str) -> VinculoMunicipioZona | None:
    texto = _clean(texto)
    if not texto or "Escolha" in texto:
        return None
    m = ZE_RE.search(texto)
    if not m:
        return None
    zona = int(m.group("zona"))
    municipio = _clean(texto[: m.start()].strip("-–—: "))
    municipio = SEDE_RE.sub("", municipio).strip("-–—: ")
    if not municipio:
        return None
    sede = bool(SEDE_RE.search(texto))
    return VinculoMunicipioZona(municipio=municipio, zona=zona, sede=sede, texto_original=texto)


def extrair_vinculos_municipio_zona(html: str) -> list[VinculoMunicipioZona]:
    soup = BeautifulSoup(html, "html.parser")
    encontrados: list[VinculoMunicipioZona] = []

    for option in soup.find_all("option"):
        vinculo = _vinculo_from_text(option.get_text(" "))
        if vinculo:
            encontrados.append(vinculo)

    if not encontrados:
        page_text = _clean(soup.get_text(" "))
        pattern = re.compile(
            r"(?P<municipio>[A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ][A-Za-zÁÀÂÃÉÊÍÓÔÕÚÜÇáàâãéêíóôõúüç' .-]+?)\s*-\s*(?P<sede>Sede\s+da\s+)?(?P<zona>\d{1,3})\s*(?:ª|º|o)?\s*ZE",
            re.I,
        )
        for m in pattern.finditer(page_text):
            encontrados.append(
                VinculoMunicipioZona(
                    municipio=_clean(m.group("municipio")),
                    zona=int(m.group("zona")),
                    sede=bool(m.group("sede")),
                    texto_original=_clean(m.group(0)),
                )
            )

    dedup: dict[tuple[str, int], VinculoMunicipioZona] = {}
    for item in encontrados:
        dedup[(item.municipio.casefold(), item.zona)] = item
    return sorted(dedup.values(), key=lambda x: (x.zona, x.municipio.casefold()))


def _build_zonas(vinculos: list[VinculoMunicipioZona]) -> list[dict]:
    zonas: dict[int, dict] = {}
    for v in vinculos:
        row = zonas.setdefault(
            v.zona,
            {
                "numero": v.zona,
                "municipio_sede": None,
                "municipios_abrangidos": [],
                "fonte_url": TREBA_CONSULTA_CARTORIOS_URL,
            },
        )
        if v.municipio not in row["municipios_abrangidos"]:
            row["municipios_abrangidos"].append(v.municipio)
        if v.sede or not row["municipio_sede"]:
            row["municipio_sede"] = v.municipio
    for row in zonas.values():
        row["municipio_sede"] = row["municipio_sede"] or row["municipios_abrangidos"][0]
    return [zonas[k] for k in sorted(zonas)]


def importar_zonas(conn, carregar_detalhes: bool = False) -> int:
    html = baixar_html_consulta()
    vinculos = extrair_vinculos_municipio_zona(html)
    if not vinculos:
        raise RuntimeError("Nenhum vínculo Município-Zona encontrado na consulta pública do TRE-BA.")

    zonas = _build_zonas(vinculos)
    total = 0
    for z in zonas:
        result = conn.execute(
            text(
                """
                insert into zonas_eleitorais
                (numero, municipio_sede, municipios_abrangidos, fonte_url, ativa, atualizado_em)
                values (:numero, :municipio_sede, :municipios_abrangidos, :fonte_url, true, now())
                on conflict (numero) do update set
                    municipio_sede = excluded.municipio_sede,
                    municipios_abrangidos = excluded.municipios_abrangidos,
                    fonte_url = excluded.fonte_url,
                    ativa = true,
                    atualizado_em = now()
                returning id
                """
            ),
            {
                "numero": z["numero"],
                "municipio_sede": z["municipio_sede"],
                "municipios_abrangidos": ", ".join(z["municipios_abrangidos"]),
                "fonte_url": z["fonte_url"],
            },
        )
        zona_id = result.scalar_one()
        conn.execute(text("delete from municipios_zona where zona_eleitoral_id = :id"), {"id": zona_id})
        for v in [v for v in vinculos if v.zona == z["numero"]]:
            conn.execute(
                text(
                    """
                    insert into municipios_zona (zona_eleitoral_id, municipio, sede)
                    values (:zona_id, :municipio, :sede)
                    on conflict (zona_eleitoral_id, municipio) do update set sede = excluded.sede
                    """
                ),
                {"zona_id": zona_id, "municipio": v.municipio, "sede": v.sede},
            )
        total += 1
    return total


def seed_zonas_bahia_padrao(conn) -> int:
    """Cria/atualiza a relação-base 001 a 205, conforme padrão usado no app anexo.

    A importação pública do TRE-BA deve complementar município-sede e municípios abrangidos.
    Este seed garante que o sistema tenha a relação completa de zonas da Bahia mesmo
    se a consulta pública estiver indisponível no momento da carga.
    """
    total = 0
    for numero in range(1, 206):
        conn.execute(
            text(
                """
                insert into zonas_eleitorais
                (numero, tribunal_sigla, uf, municipio_sede, municipios_abrangidos, fonte_url, ativa, atualizado_em)
                values (:numero, 'TRE-BA', 'BA', coalesce(:municipio_sede, 'A definir'), '', 'Relação-base do código anexo: 001 a 205', true, now())
                on conflict (numero) do update set
                    tribunal_sigla = coalesce(zonas_eleitorais.tribunal_sigla, 'TRE-BA'),
                    uf = coalesce(zonas_eleitorais.uf, 'BA'),
                    ativa = true,
                    atualizado_em = now()
                """
            ),
            {"numero": numero, "municipio_sede": None},
        )
        total += 1
    return total
