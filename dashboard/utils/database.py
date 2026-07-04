import os
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def _get_config() -> tuple[str, str]:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return url, key
    except (KeyError, FileNotFoundError, AttributeError):
        pass
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL e SUPABASE_KEY não configurados. "
            "Defina no .env (local) ou nos Secrets do Streamlit Cloud."
        )
    return url, key


@st.cache_resource
def _client() -> Client:
    url, key = _get_config()
    return create_client(url, key)


@st.cache_data(ttl=300)
def run_query(fn_name: str, params: dict | None = None) -> pd.DataFrame:
    try:
        result = _client().rpc(fn_name, params or {}).execute()
        return pd.DataFrame(result.data or [])
    except Exception as e:
        msg = str(e).split("(Background")[0].strip()
        st.error(f"**Erro ao consultar o banco:** `{type(e).__name__}: {msg}`")
        st.stop()


def db_rpc(fn_name: str, params: dict | None = None) -> None:
    _client().rpc(fn_name, params or {}).execute()


def get_competencias() -> list[str]:
    df = run_query("fn_competencias")
    return df["competencia"].tolist()
