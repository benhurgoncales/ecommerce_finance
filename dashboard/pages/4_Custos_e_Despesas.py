import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go

from utils.database import run_query
from utils.filters import render_filters
from utils.formatting import fmt_brl, fmt_mes
from utils.styles import load_css, sidebar_logo, kpi_card, page_header, section, chart_layout, DESP_CORES
from utils import queries

st.set_page_config(page_title="Custos e Despesas", page_icon="💸", layout="wide")
load_css()
sidebar_logo()

mes_inicio, mes_fim = render_filters()
p     = {"inicio": mes_inicio, "fim": mes_fim}
label = f"{fmt_mes(mes_inicio)} → {fmt_mes(mes_fim)}"

page_header("💸 Custos e Despesas", label, "Para onde vai o dinheiro e quem pesa mais")

# ── Card total ────────────────────────────────────────────────────────────
with st.spinner():
    df_total = run_query(queries.TOTAL_DESPESAS, p)

total = float(df_total["total"].iloc[0] or 0)
col_kpi, _ = st.columns([1, 3])
col_kpi.markdown(kpi_card("Total de Despesas do Período", fmt_brl(total), "#DC2626", "💸"), unsafe_allow_html=True)

st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

# ── Despesas por Categoria e Custo por Pessoa ─────────────────────────────
col1, col2 = st.columns(2, gap="large")

with col1:
    section("Despesas por Categoria")
    with st.spinner():
        df_cat = run_query(queries.DESPESAS_POR_CATEGORIA, p)

    fig1 = go.Figure(go.Bar(
        x=df_cat["R$"], y=df_cat["Categoria"], orientation="h",
        marker_color=[DESP_CORES.get(c, "#64748B") for c in df_cat["Categoria"]],
        text=[fmt_brl(v) for v in df_cat["R$"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
    ))
    fig1.update_layout(**chart_layout(
        height=320, showlegend=False,
        xaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
        yaxis=dict(autorange="reversed", showgrid=False),
    ))
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    section("Top 5 Maiores Custos")
    with st.spinner():
        df_top = run_query(queries.TOP5_CUSTOS, p)

    CORES_TOP5 = ["#2563EB", "#7C3AED", "#E11D48", "#EA580C", "#D97706"]
    labels_top = [
        f"R$ {v:,.0f}  ({p_:.1f}%)".replace(",", ".")
        for v, p_ in zip(df_top["Valor"], df_top["% do Total"])
    ]

    fig2 = go.Figure(go.Bar(
        x=df_top["Valor"],
        y=df_top["Item"],
        orientation="h",
        marker_color=CORES_TOP5[:len(df_top)],
        text=labels_top,
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>",
        cliponaxis=False,
    ))
    fig2.update_layout(**chart_layout(
        height=320, showlegend=False,
        xaxis=dict(tickprefix="R$ ", tickformat=",.0f", showticklabels=False, showgrid=False),
        yaxis=dict(autorange="reversed", showgrid=False),
        margin=dict(l=8, r=180, t=40, b=8),
    ))
    st.plotly_chart(fig2, use_container_width=True)

# ── Evolução das Despesas ─────────────────────────────────────────────────
section("Evolução das Despesas Totais")

with st.spinner():
    df_ev = run_query(queries.EVOLUCAO_DESPESAS, p)

df_ev["Mês"] = df_ev["competencia"].apply(fmt_mes)

fig3 = go.Figure(go.Bar(
    x=df_ev["Mês"], y=df_ev["Total Despesas"],
    marker_color="#DC2626",
    marker_line_width=0,
    text=[fmt_brl(v) for v in df_ev["Total Despesas"]],
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Total: R$ %{y:,.2f}<extra></extra>",
    cliponaxis=False,
))
fig3.update_layout(**chart_layout(
    height=320, showlegend=False,
    xaxis=dict(showgrid=False),
    yaxis=dict(tickprefix="R$ ", tickformat=",.0f", showticklabels=False, showgrid=False),
    margin=dict(l=8, r=8, t=56, b=8),
    bargap=0.35,
))
st.plotly_chart(fig3, use_container_width=True)

# ── Tabela detalhada ──────────────────────────────────────────────────────
section("Despesas Detalhadas")

with st.spinner():
    df_det = run_query(queries.DESPESAS_DETALHADAS, p)

st.dataframe(
    df_det,
    use_container_width=True,
    hide_index=True,
    height=380,
    column_config={
        "Categoria": st.column_config.TextColumn("Categoria", width="medium"),
        "Descrição": st.column_config.TextColumn("Descrição", width="large"),
        "Tipo":      st.column_config.TextColumn("Tipo",      width="small"),
        "Valor":     st.column_config.NumberColumn("Valor",   format="R$ %.2f"),
    },
)
