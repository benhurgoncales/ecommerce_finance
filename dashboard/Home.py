import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from utils.styles import load_css, sidebar_logo

st.set_page_config(
    page_title="Financeiro E-commerce",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css()
sidebar_logo()

st.markdown("""
<div style="max-width:680px;margin:48px auto 0;text-align:center">
    <h1 style="font-size:30px;font-weight:800;color:#1E293B;margin-bottom:8px">
        Dashboard Financeiro
    </h1>
    <p style="color:#64748B;font-size:15px;margin-bottom:40px">
        Visão completa do desempenho financeiro mensal do e-commerce.
        Selecione o período no menu lateral em qualquer página.
    </p>
</div>
""", unsafe_allow_html=True)

pages = [
    ("📈", "Visão Geral",          "Faturamento, lucro e tendências do período"),
    ("🛒", "Canais e Plataformas", "Performance e margem por canal de venda"),
    ("📋", "DRE Completa",         "Demonstrativo de resultado vs acumulado do ano"),
    ("💸", "Custos e Despesas",    "Para onde vai o dinheiro e quem pesa mais"),
]

cols = st.columns(2, gap="medium")
for i, (icon, title, desc) in enumerate(pages):
    with cols[i % 2]:
        st.markdown(f"""
        <div style="background:#fff;border-radius:12px;padding:24px;
                    border:1px solid #E2E8F0;margin-bottom:16px;
                    box-shadow:0 1px 3px rgba(0,0,0,0.04)">
            <div style="font-size:26px;margin-bottom:10px">{icon}</div>
            <h3 style="margin:0 0 6px;font-size:15px;font-weight:700;color:#1E293B">{title}</h3>
            <p style="margin:0;color:#64748B;font-size:13px">{desc}</p>
        </div>
        """, unsafe_allow_html=True)
