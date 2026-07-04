import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def _get_db_url() -> str:
    # Streamlit Community Cloud: secrets set in the cloud dashboard
    try:
        return st.secrets["DATABASE_URL"]
    except (KeyError, FileNotFoundError, AttributeError):
        pass
    # Local development: .env file
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não configurado. Defina no .env ou nos Secrets do Streamlit Cloud.")
    return url


@st.cache_resource
def _engine():
    return create_engine(_get_db_url(), pool_pre_ping=True, pool_size=3, max_overflow=2)


@st.cache_data(ttl=300)
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    with _engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def get_competencias() -> list[str]:
    try:
        df = run_query(
            "SELECT DISTINCT competencia FROM dre_consolidada ORDER BY competencia"
        )
        return df["competencia"].tolist()
    except Exception as e:
        msg = str(e).split("(Background")[0].strip()
        st.error(f"**Erro de conexão com o banco:**\n\n`{type(e).__name__}: {msg}`")
        st.stop()
