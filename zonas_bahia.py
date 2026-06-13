ZONAS_BAHIA = ["Não informado"] + [f"{i:03d}ª Zona Eleitoral - Bahia" for i in range(1, 206)]


def zona_label(numero: int, municipio_sede: str | None = None, uf: str = "BA") -> str:
    if municipio_sede:
        return f"{numero:03d}ª ZE - {municipio_sede}/{uf}"
    return f"{numero:03d}ª Zona Eleitoral - Bahia"
