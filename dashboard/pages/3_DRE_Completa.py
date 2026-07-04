import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd

from utils.database import run_query
from utils.filters import render_filters
from utils.formatting import fmt_brl, fmt_mes
from utils.styles import load_css, sidebar_logo, page_header
from utils import queries

st.set_page_config(page_title="DRE Completa", page_icon="📋", layout="wide")
load_css()
sidebar_logo()

mes_inicio, mes_fim = render_filters()
p     = {"inicio": mes_inicio, "fim": mes_fim}
label = f"{fmt_mes(mes_inicio)} → {fmt_mes(mes_fim)}"

page_header("📋 DRE Completa", label, "Demonstrativo de resultado do período vs acumulado do ano")

# ── Classificação de linhas ───────────────────────────────────────────────
TOTAIS  = {"(=) Receita Líquida","(=) Lucro Bruto","(=) Total Despesas","(=) EBITDA","(=) Lucro Líquido"}
PCT     = {"    Margem Bruta %","    Margem Líquida %"}
RECEITA = {"(+) Receita Bruta"}

CAT_TO_DRE = {
    "Administrativo":           "(-) Administrativo",
    "Marketing":                "(-) Marketing",
    "Despesas Financeiras":     "(-) Despesas Financeiras",
    "Tecnologia e Ferramentas": "(-) Tecnologia e Ferramentas",
    "Educação e Capacitação":   "(-) Educação e Capacitação",
}


def margem_cor(m: float) -> str:
    if m < 0:  return "#DC2626"
    if m <= 3: return "#D97706"
    return "#059669"


def fmt_val(linha, val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    v = float(val)
    return f"{v:.2f}%" if linha in PCT else fmt_brl(v)


def style_dre(row, cor_lucro: str):
    linha  = row["Linha DRE"]
    base   = "font-size:13.5px;padding:7px 12px;"
    is_sub = str(linha).startswith("   ↳")
    if is_sub:
        return [base + "color:#64748B;background:#FAFAFA;font-size:12.5px;padding-left:32px"] * len(row)
    if linha == "(=) Lucro Líquido":
        return [base + f"font-weight:700;background:#EFF6FF;color:{cor_lucro};border-top:1px solid #BFDBFE"] * len(row)
    if linha == "    Margem Líquida %":
        return [base + f"font-style:italic;font-weight:600;color:{cor_lucro};background:#FAFAFA"] * len(row)
    if linha in TOTAIS:
        return [base + "font-weight:700;background:#EFF6FF;color:#1E293B;border-top:1px solid #BFDBFE"] * len(row)
    if linha in PCT:
        return [base + "font-style:italic;color:#64748B;background:#FAFAFA"] * len(row)
    if linha in RECEITA:
        return [base + "color:#059669;font-weight:600"] * len(row)
    if str(linha).startswith("(-)"):
        return [base + "color:#DC2626"] * len(row)
    return [base] * len(row)


def render_tabela(df):
    # Extrai margem numérica antes de formatar
    mask = df["Linha DRE"] == "    Margem Líquida %"
    margem_val = float(df.loc[mask, "Período"].iloc[0]) if mask.any() else 0
    cor_lucro  = margem_cor(margem_val)

    df_fmt = df.copy()
    df_fmt["Período"]          = [fmt_val(r["Linha DRE"], r["Período"])          for _, r in df.iterrows()]
    df_fmt["Acumulado do Ano"] = [fmt_val(r["Linha DRE"], r["Acumulado do Ano"]) for _, r in df.iterrows()]

    st.dataframe(
        df_fmt.style.apply(style_dre, cor_lucro=cor_lucro, axis=1),
        use_container_width=True,
        hide_index=True,
        height=min(40 * len(df) + 60, 700),
        column_config={
            "Linha DRE":        st.column_config.TextColumn("Linha DRE",        width="large"),
            "Período":          st.column_config.TextColumn("Período",           width="medium"),
            "Acumulado do Ano": st.column_config.TextColumn("Acumulado do Ano",  width="medium"),
        },
    )
    st.markdown("""
    <div style="display:flex;gap:20px;margin-top:8px;flex-wrap:wrap">
        <span style="font-size:12px;color:#64748B"><span style="color:#059669;font-weight:700">■</span> Receita</span>
        <span style="font-size:12px;color:#64748B"><span style="color:#DC2626;font-weight:700">■</span> Custo / Despesa</span>
        <span style="font-size:12px;color:#64748B"><span style="color:#2563EB;font-weight:700">■</span> Totais</span>
        <span style="font-size:12px;color:#64748B"><span style="color:#94A3B8;font-weight:700">■</span> Subtotais / %</span>
    </div>
    """, unsafe_allow_html=True)


# ── Abas ─────────────────────────────────────────────────────────────────
tab_geral, tab_detalhe = st.tabs(["🗂 DRE Geral", "🔍 DRE Detalhada"])

# ─────────────────────────────────────────────────────────────────────────
# ABA 1 — DRE GERAL (comportamento original)
# ─────────────────────────────────────────────────────────────────────────
with tab_geral:
    with st.spinner("Carregando DRE…"):
        df = run_query(queries.DRE_PERIODO, p)
    render_tabela(df)


# ─────────────────────────────────────────────────────────────────────────
# ABA 2 — DRE DETALHADA
# ─────────────────────────────────────────────────────────────────────────
with tab_detalhe:
    with st.spinner("Carregando DRE detalhada…"):
        df_sum    = run_query(queries.DRE_PERIODO, p)
        df_canais = run_query(queries.DRE_DETALHE_CANAIS,   p)
        df_folha  = run_query(queries.DRE_DETALHE_FOLHA,    p)
        df_desp   = run_query(queries.DRE_DETALHE_DESPESAS, p)

    # Índice do resumo: linha → (periodo, acumulado)
    idx = {r["Linha DRE"]: (r["Período"], r["Acumulado do Ano"]) for _, r in df_sum.iterrows()}

    def row(linha, periodo, acumulado):
        return {"Linha DRE": linha, "Período": periodo, "Acumulado do Ano": acumulado}

    def sub(nome, periodo, acumulado):
        return {"Linha DRE": f"   ↳ {nome}", "Período": periodo, "Acumulado do Ano": acumulado}

    linhas = []

    # (+) Receita Bruta + detalhe por canal
    linhas.append(row("(+) Receita Bruta", *idx["(+) Receita Bruta"]))
    for _, r in df_canais.iterrows():
        linhas.append(sub(r["nome"], r["periodo"], r["acumulado"]))

    # Impostos e resultado operacional
    linhas.append(row("(-) Impostos",        *idx["(-) Impostos"]))
    linhas.append(row("(=) Receita Líquida", *idx["(=) Receita Líquida"]))
    linhas.append(row("(-) CMV Total",       *idx["(-) CMV Total"]))
    linhas.append(row("(=) Lucro Bruto",     *idx["(=) Lucro Bruto"]))
    linhas.append(row("    Margem Bruta %",  *idx["    Margem Bruta %"]))

    # (-) Folha de Pagamento + detalhe por funcionário
    linhas.append(row("(-) Folha de Pagamento", *idx["(-) Folha de Pagamento"]))
    for _, r in df_folha.iterrows():
        linhas.append(sub(r["nome"], r["periodo"], r["acumulado"]))

    # Demais categorias de despesa + detalhe por item
    desp_por_cat = {}
    for _, r in df_desp.iterrows():
        desp_por_cat.setdefault(r["categoria"], []).append(r)

    for cat, dre_linha in CAT_TO_DRE.items():
        linhas.append(row(dre_linha, *idx[dre_linha]))
        for r in desp_por_cat.get(cat, []):
            linhas.append(sub(r["nome"], r["periodo"], r["acumulado"]))

    # Resultados finais
    for linha in ["(=) Total Despesas", "(=) EBITDA", "(=) Lucro Líquido", "    Margem Líquida %"]:
        linhas.append(row(linha, *idx[linha]))

    df_det = pd.DataFrame(linhas)
    render_tabela(df_det)
