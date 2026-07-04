import streamlit as st
from utils.database import get_competencias
from utils.formatting import fmt_mes


def render_filters() -> tuple[str, str]:
    meses = get_competencias()
    if not meses:
        st.sidebar.error("Nenhum dado encontrado no banco.")
        st.stop()

    labels = {m: fmt_mes(m) for m in meses}

    st.sidebar.markdown("---")
    st.sidebar.markdown("**PERÍODO**")

    mes_inicio = st.sidebar.selectbox(
        "De", options=meses, format_func=lambda m: labels[m],
        index=0, key="mes_inicio",
    )
    mes_fim = st.sidebar.selectbox(
        "Até", options=meses, format_func=lambda m: labels[m],
        index=len(meses) - 1, key="mes_fim",
    )

    if mes_inicio > mes_fim:
        st.sidebar.warning("'De' não pode ser maior que 'Até'.")
        mes_fim = mes_inicio

    meses_count = meses.index(mes_fim) - meses.index(mes_inicio) + 1
    st.sidebar.markdown(
        f'<p style="color:#94A3B8;font-size:12px;margin-top:6px">'
        f'{fmt_mes(mes_inicio)} → {fmt_mes(mes_fim)} &nbsp;·&nbsp; {meses_count} {"mês" if meses_count == 1 else "meses"}'
        f'</p>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    return mes_inicio, mes_fim
