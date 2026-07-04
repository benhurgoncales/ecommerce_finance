import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go

from utils.database import run_query
from utils.filters import render_filters
from utils.formatting import fmt_brl, fmt_pct, fmt_mes
from utils.styles import load_css, sidebar_logo, kpi_card, page_header, section, chart_layout, DESP_CORES, CANAL_CORES
from utils import queries

st.set_page_config(page_title="Visão Geral", page_icon="📈", layout="wide")
load_css()
sidebar_logo()

mes_inicio, mes_fim = render_filters()
p     = {"inicio": mes_inicio, "fim": mes_fim}
label = f"{fmt_mes(mes_inicio)} → {fmt_mes(mes_fim)}"

page_header("📈 Visão Geral", label, "Faturamento, lucro e composição de despesas")

# ── KPIs ──────────────────────────────────────────────────────────────────
with st.spinner("Carregando…"):
    df_m = run_query(queries.METRICAS_GERAIS, p)

def margem_cor(m: float) -> str:
    if m < 0:  return "#DC2626"
    if m <= 3: return "#D97706"
    return "#059669"

receita = float(df_m["receita_bruta"].iloc[0] or 0)
lucro   = float(df_m["lucro_liquido"].iloc[0] or 0)
margem  = float(df_m["margem_pct"].iloc[0] or 0)
cor     = margem_cor(margem)

c1, c2, c3 = st.columns(3, gap="medium")

c1.markdown(kpi_card("Faturamento Bruto", fmt_brl(receita), "#2563EB", "💰"), unsafe_allow_html=True)
c2.markdown(kpi_card("Lucro Líquido",     fmt_brl(lucro),   cor, "📊"), unsafe_allow_html=True)
c3.markdown(kpi_card("Margem Líquida",    fmt_pct(margem),  cor, "📐"), unsafe_allow_html=True)

st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

# ── Gráficos: Faturamento e Lucro por Canal ───────────────────────────────
with st.spinner():
    df_fat = run_query(queries.FATURAMENTO_POR_CANAL, p)
    df_luc = run_query(queries.LUCRO_POR_CANAL, p)

col1, col2 = st.columns(2, gap="large")

# Gráfico 1 — Faturamento por canal
with col1:
    section("Faturamento por Canal")

    fig1 = go.Figure(go.Pie(
        labels=df_fat["Canal"],
        values=df_fat["Receita Bruta"],
        marker=dict(
            colors=CANAL_CORES[:len(df_fat)],
            line=dict(color="white", width=2),
        ),
        textinfo="percent",
        textposition="inside",
        textfont=dict(size=12, color="white", family="system-ui,-apple-system,sans-serif"),
        insidetextorientation="horizontal",
        hovertemplate="<b>%{label}</b><br>Receita: R$ %{value:,.0f}<br>%{percent}<extra></extra>",
        hole=0.35,
        sort=False,
    ))
    fig1.update_layout(
        paper_bgcolor="white",
        font=dict(family="system-ui,-apple-system,sans-serif", color="#1E293B", size=12),
        height=340,
        margin=dict(l=8, r=8, t=40, b=8),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle", y=0.5,
            xanchor="left",   x=1.0,
            font=dict(size=12, color="#1E293B"),
        ),
    )
    st.plotly_chart(fig1, use_container_width=True)

# Gráfico 2 — Lucro Líquido por canal
with col2:
    section("Lucro Líquido por Canal")

    cores_luc = [
        "#059669" if v >= 0 else "#DC2626"
        for v in df_luc["Lucro Líquido"]
    ]
    labels_luc = [
        f"R$ {v:,.0f}  ({p_:.1f}%)".replace(",", ".")
        for v, p_ in zip(df_luc["Lucro Líquido"], df_luc["% Lucro"])
    ]

    fig2 = go.Figure(go.Bar(
        x=df_luc["Lucro Líquido"],
        y=df_luc["Canal"],
        orientation="h",
        marker_color=cores_luc,
        text=labels_luc,
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Lucro: R$ %{x:,.2f}<extra></extra>",
        cliponaxis=False,
    ))
    fig2.add_vline(x=0, line_color="#CBD5E1", line_width=1)
    fig2.update_layout(**chart_layout(
        height=340, showlegend=False,
        xaxis=dict(tickprefix="R$ ", tickformat=",.0f", showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(autorange="reversed", showgrid=False),
        margin=dict(l=8, r=160, t=40, b=8),
    ))
    st.plotly_chart(fig2, use_container_width=True)

# ── Composição das Despesas ────────────────────────────────────────────────
section("Composição das Despesas por Mês")

with st.spinner():
    df_d = run_query(queries.DESPESAS_COMPOSICAO, p)

df_d["Mês"] = df_d["competencia"].apply(fmt_mes)

fig3 = go.Figure()
for cat, cor in DESP_CORES.items():
    if cat not in df_d.columns:
        continue
    fig3.add_trace(go.Bar(
        x=df_d["Mês"], y=df_d[cat], name=cat,
        marker_color=cor,
        hovertemplate=f"<b>%{{x}}</b><br>{cat}: R$ %{{y:,.2f}}<extra></extra>",
    ))
fig3.update_layout(**chart_layout(
    height=360,
    yaxis=dict(tickprefix="R$ ", tickformat=",.0f"),
    barmode="stack",
    bargap=0.35,
))
st.plotly_chart(fig3, use_container_width=True)
