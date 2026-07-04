import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go

from utils.database import run_query
from utils.filters import render_filters
from utils.formatting import fmt_mes
from utils.styles import load_css, sidebar_logo, page_header, section, chart_layout, CANAL_CORES
from utils import queries

st.set_page_config(page_title="Canais e Plataformas", page_icon="🛒", layout="wide")
load_css()
sidebar_logo()

mes_inicio, mes_fim = render_filters()
p     = {"inicio": mes_inicio, "fim": mes_fim}
label = f"{fmt_mes(mes_inicio)} → {fmt_mes(mes_fim)}"

page_header("🛒 Canais e Plataformas", label, "Performance e rentabilidade por canal de venda")

# ── Tabela ────────────────────────────────────────────────────────────────
section("Comparativo por Canal")

with st.spinner():
    df_tab = run_query(queries.CANAIS_COMPARATIVO, p)

st.dataframe(
    df_tab,
    use_container_width=True,
    hide_index=True,
    height=300,
    column_config={
        "Canal":             st.column_config.TextColumn("Canal",        width="medium"),
        "Receita Bruta":     st.column_config.NumberColumn("Receita Bruta",    format="R$ %.2f"),
        "Imposto":           st.column_config.NumberColumn("Imposto",          format="R$ %.2f"),
        "CMV Total":         st.column_config.NumberColumn("CMV Total",        format="R$ %.2f"),
        "Margem Líquida R$": st.column_config.NumberColumn("Margem R$",        format="R$ %.2f"),
        "Margem Líquida %":  st.column_config.NumberColumn("Margem %",         format="%.1f%%"),
        "Ads":               st.column_config.NumberColumn("Ads",              format="R$ %.2f"),
    },
)

st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

# ── Margem % por Canal ────────────────────────────────────────────────────
with col1:
    section("Margem Líquida % por Canal")
    with st.spinner():
        df_m = run_query(queries.CANAIS_MARGEM_PCT, p)

    cores = ["#DC2626" if v < 0 else "#059669" if v >= 15 else "#D97706"
             for v in df_m["Margem %"]]

    fig1 = go.Figure(go.Bar(
        x=df_m["Margem %"], y=df_m["Canal"], orientation="h",
        marker_color=cores,
        text=[f"{v:.1f}%" for v in df_m["Margem %"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Margem: %{x:.1f}%<extra></extra>",
    ))
    fig1.add_vline(x=0, line_color="#CBD5E1", line_width=1)
    fig1.update_layout(**chart_layout(
        height=320, showlegend=False,
        xaxis=dict(ticksuffix="%", zeroline=False),
        yaxis=dict(autorange="reversed", showgrid=False),
    ))
    st.plotly_chart(fig1, use_container_width=True)

# ── Participação ──────────────────────────────────────────────────────────
with col2:
    section("Participação no Faturamento")
    with st.spinner():
        df_p = run_query(queries.FATURAMENTO_POR_CANAL, p)

    fig2 = go.Figure(go.Pie(
        labels=df_p["Canal"],
        values=df_p["Receita Bruta"],
        marker=dict(
            colors=CANAL_CORES[:len(df_p)],
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
    fig2.update_layout(
        paper_bgcolor="white",
        font=dict(family="system-ui,-apple-system,sans-serif", color="#1E293B", size=12),
        height=320,
        margin=dict(l=8, r=8, t=40, b=8),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle", y=0.5,
            xanchor="left",   x=1.0,
            font=dict(size=12, color="#1E293B"),
        ),
    )
    st.plotly_chart(fig2, use_container_width=True)
