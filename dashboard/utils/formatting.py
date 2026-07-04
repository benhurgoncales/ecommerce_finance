MESES_PT = {
    "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
    "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
    "09": "Set", "10": "Out", "11": "Nov", "12": "Dez",
}


def fmt_mes(competencia: str) -> str:
    """'2025-03'  →  'Mar/25'"""
    ano, mes = competencia.split("-")
    return f"{MESES_PT[mes]}/{ano[2:]}"


def fmt_brl(valor: float) -> str:
    """12345.6  →  'R$ 12.345,60'"""
    if valor is None:
        return "—"
    s = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    sinal = "-" if valor < 0 else ""
    return f"{sinal}R$ {s}"


def fmt_pct(valor: float, decimals: int = 2) -> str:
    if valor is None:
        return "—"
    return f"{valor:.{decimals}f}%"
