from __future__ import annotations

import re
from pathlib import Path
import pandas as pd
from sqlalchemy import text


def normalizar_freq(texto: str) -> str:
    t = (texto or "").lower()
    if "di" in t:
        return "diaria"
    if "seman" in t:
        return "semanal"
    if "quinzen" in t:
        return "quinzenal"
    if "bimes" in t:
        return "bimestral"
    if "trimes" in t:
        return "trimestral"
    if "anual" in t or "ano" in t:
        return "anual"
    return "mensal"


def importar_itens_ods(conn, ods_path: str | Path) -> int:
    ods_path = Path(ods_path)
    sheets = pd.read_excel(ods_path, sheet_name=None, engine="odf", header=None)
    total = 0
    for sheet_name, df in sheets.items():
        grupo_atual = sheet_name.strip() or "Geral"
        for _, row in df.iterrows():
            cells = [str(v).strip() for v in row.tolist() if pd.notna(v) and str(v).strip() and str(v).strip().lower() != "nan"]
            if not cells:
                continue
            joined = " | ".join(cells)
            lower = joined.lower()
            if any(x in lower for x in ["plano de ação", "monitoramento cartor", "sistema", "periodicidade"]):
                if len(cells) <= 2:
                    continue
            if len(cells) == 1 and len(cells[0]) < 35:
                grupo_atual = cells[0]
                continue

            descricao = max(cells, key=len)
            if len(descricao) < 8:
                continue
            frequencia = normalizar_freq(joined)
            criticidade = "alta" if any(x in lower for x in ["pje", "multa", "rae", "infodip", "sei"]) else "media"
            exige_evidencia = any(x in lower for x in ["sei", "document", "anex", "livro", "relatório", "relatorio"])
            conn.execute(
                text(
                    """
                    insert into itens_monitoramento
                    (grupo, descricao, responsavel_origem, frequencia, exige_evidencia, criticidade, ativo)
                    values (:grupo, :descricao, :responsavel, :frequencia, :exige, :criticidade, true)
                    on conflict (grupo, descricao) do update set
                        frequencia = excluded.frequencia,
                        exige_evidencia = excluded.exige_evidencia,
                        criticidade = excluded.criticidade,
                        ativo = true
                    """
                ),
                {
                    "grupo": grupo_atual[:120],
                    "descricao": descricao,
                    "responsavel": "Chefe de Cartório",
                    "frequencia": frequencia,
                    "exige": exige_evidencia,
                    "criticidade": criticidade,
                },
            )
            total += 1
    return total
