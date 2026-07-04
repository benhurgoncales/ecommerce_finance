import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

from utils.database import run_query, _engine
from utils.styles import load_css, sidebar_logo, page_header
from utils.formatting import fmt_mes, fmt_brl

st.set_page_config(page_title="Lançamentos", page_icon="✏️", layout="wide")
load_css()
sidebar_logo()

page_header("✏️ Lançamentos", "", "Insira os dados mensais de receitas, folha e despesas")

# ── Seletor de competência ────────────────────────────────────────────────────
MESES = {
    "Janeiro": "01", "Fevereiro": "02", "Março":    "03",
    "Abril":   "04", "Maio":      "05", "Junho":    "06",
    "Julho":   "07", "Agosto":    "08", "Setembro": "09",
    "Outubro": "10", "Novembro":  "11", "Dezembro": "12",
}

col_ano, col_mes, _ = st.columns([1, 2, 5])
with col_ano:
    ano = st.selectbox("Ano", [2025, 2026, 2027], index=1, key="sel_ano")
with col_mes:
    mes_nome = st.selectbox(
        "Mês", list(MESES.keys()),
        index=datetime.now().month - 1,
        key="sel_mes",
    )

comp = f"{ano}-{MESES[mes_nome]}"
st.caption(f"Referência: **{fmt_mes(comp)}** ({comp}) — use vírgula para decimais: ex. **1500,50**")
st.divider()


# ── Helpers de valor monetário ────────────────────────────────────────────────
def to_br(v) -> str:
    """Float → string BR sem separador de milhar: 1500.5 → '1500,50'"""
    try:
        return f"{float(v):.2f}".replace(".", ",")
    except Exception:
        return "0,00"


def parse_br(s) -> float:
    """Aceita '1500,50', '1.500,50', '1500.50' → 1500.5"""
    if pd.isna(s) or str(s).strip() == "":
        return 0.0
    s = str(s).strip().replace("R$", "").replace(" ", "")
    if "," in s and "." in s:
        # 1.500,50 → remove ponto (milhar) e troca vírgula por ponto
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # 1500,50 → troca vírgula por ponto
        s = s.replace(",", ".")
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


# ── Helpers de escrita no banco ───────────────────────────────────────────────
def db_write(sql: str, params: dict):
    with _engine().connect() as conn:
        conn.execute(text(sql), params)
        conn.commit()


def recalcular_dre(c: str):
    with _engine().connect() as conn:
        conn.execute(text("SELECT recalcular_dre(:c)"), {"c": c})
        conn.commit()


# ── SQL de carga ──────────────────────────────────────────────────────────────
SQL_RECEITAS = """
SELECT
    c.id          AS canal_id,
    c.nome        AS "Canal",
    COALESCE(r.receita_bruta,  0) AS "Receita Bruta",
    COALESCE(r.imposto,        0) AS "Imposto (DAS)",
    COALESCE(r.custo_produto,  0) AS "Custo do Produto",
    COALESCE(r.frete,          0) AS "Frete",
    COALESCE(r.tarifa,         0) AS "Tarifa Plataforma",
    COALESCE(r.desconto_cupom, 0) AS "Desconto / Cupom",
    COALESCE(r.afiliado,       0) AS "Afiliados",
    COALESCE(r.outros_cmv,     0) AS "Outros CMV",
    COALESCE(r.ads,            0) AS "Ads (Anúncios)"
FROM canais c
LEFT JOIN receitas r ON r.canal_id = c.id AND r.competencia = :comp
WHERE c.ativo = true
ORDER BY c.nome
"""

SQL_FOLHA = """
SELECT
    fu.id          AS func_id,
    fu.nome        AS "Funcionário",
    fu.tipo        AS tipo_raw,
    CASE fu.tipo
        WHEN 'pro_labore' THEN 'Pró-labore'
        WHEN 'autonomo'   THEN 'Autônomo'
        WHEN 'clt'        THEN 'CLT'
    END            AS "Tipo",
    COALESCE(fp.salario_bruto, 0) AS "Salário Bruto",
    COALESCE(fp.bonus,         0) AS "Bônus",
    COALESCE(fp.fgts,          0) AS "FGTS",
    COALESCE(fp.inss_retido,   0) AS "INSS Retido"
FROM funcionarios fu
LEFT JOIN folha_pagamento fp
       ON fp.funcionario_id = fu.id AND fp.competencia = :comp
WHERE fu.ativo = true
ORDER BY fu.nome
"""

SQL_DESPESAS = """
SELECT
    cd.nome     AS "Categoria",
    d.descricao AS "Descrição",
    d.tipo      AS "Tipo",
    d.valor     AS "Valor"
FROM despesas d
JOIN categorias_despesa cd ON cd.id = d.categoria_id
WHERE d.competencia = :comp
ORDER BY cd.ordem, d.descricao
"""

SQL_CATS = "SELECT id, nome FROM categorias_despesa ORDER BY ordem"

DESPESAS_TEMPLATE = [
    {"Categoria": "Administrativo",         "Descrição": "Aluguel",              "Tipo": "fixo",     "Valor": "0,00"},
    {"Categoria": "Administrativo",         "Descrição": "Contador",             "Tipo": "fixo",     "Valor": "0,00"},
    {"Categoria": "Administrativo",         "Descrição": "Embalagem",            "Tipo": "variavel", "Valor": "0,00"},
    {"Categoria": "Administrativo",         "Descrição": "Ferramentas",          "Tipo": "fixo",     "Valor": "0,00"},
    {"Categoria": "Administrativo",         "Descrição": "Outros Operacionais",  "Tipo": "eventual", "Valor": "0,00"},
    {"Categoria": "Educação e Capacitação", "Descrição": "Trilha do Ecommerce",  "Tipo": "eventual", "Valor": "0,00"},
    {"Categoria": "Marketing",              "Descrição": "Outros Marketing",     "Tipo": "variavel", "Valor": "0,00"},
    {"Categoria": "Marketing",              "Descrição": "Tráfego Pago Externo", "Tipo": "variavel", "Valor": "0,00"},
]

# Configuração de coluna de valor (TextColumn com vírgula)
def col_valor(label: str, help_txt: str = "Ex: 1500,50") -> st.column_config.TextColumn:
    return st.column_config.TextColumn(label, help=help_txt, width="medium")


# ── Abas ──────────────────────────────────────────────────────────────────────
tab_rec, tab_folha, tab_desp = st.tabs([
    "💰 Receitas por Canal",
    "👥 Folha de Pagamento",
    "💸 Despesas",
])

COLS_REC = ["Receita Bruta", "Imposto (DAS)", "Custo do Produto", "Frete",
            "Tarifa Plataforma", "Desconto / Cupom", "Afiliados", "Outros CMV", "Ads (Anúncios)"]
COLS_FOLHA = ["Salário Bruto", "Bônus", "FGTS", "INSS Retido"]


# ════════════════════════════════════════════════════════════════════════════════
# ABA 1 — RECEITAS POR CANAL
# ════════════════════════════════════════════════════════════════════════════════
with tab_rec:
    st.markdown("Preencha os valores de **cada canal** para o mês selecionado. Use vírgula para decimais.")

    df_rec = run_query(SQL_RECEITAS, {"comp": comp})
    # Converte colunas numéricas para string BR
    for col in COLS_REC:
        df_rec[col] = df_rec[col].apply(to_br)

    df_rec_edit = st.data_editor(
        df_rec,
        column_config={
            "canal_id":          None,
            "Canal":             st.column_config.TextColumn("Canal", disabled=True, width="medium"),
            "Receita Bruta":     col_valor("Receita Bruta"),
            "Imposto (DAS)":     col_valor("Imposto (DAS)"),
            "Custo do Produto":  col_valor("Custo do Produto"),
            "Frete":             col_valor("Frete"),
            "Tarifa Plataforma": col_valor("Tarifa Plataforma"),
            "Desconto / Cupom":  col_valor("Desconto / Cupom"),
            "Afiliados":         col_valor("Afiliados"),
            "Outros CMV":        col_valor("Outros CMV"),
            "Ads (Anúncios)":    col_valor("Ads (Anúncios)"),
        },
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key=f"editor_rec_{comp}",
    )

    # Preview dos totais em tempo real
    rb   = sum(parse_br(v) for v in df_rec_edit["Receita Bruta"])
    imp  = sum(parse_br(v) for v in df_rec_edit["Imposto (DAS)"])
    cmv  = sum(parse_br(df_rec_edit[c].iloc[i]) for c in COLS_REC[2:-1] for i in range(len(df_rec_edit)))
    ads  = sum(parse_br(v) for v in df_rec_edit["Ads (Anúncios)"])
    lucro_bruto = rb - imp - cmv - ads

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receita Bruta Total",  fmt_brl(rb))
    c2.metric("Impostos + CMV",       fmt_brl(imp + cmv))
    c3.metric("Ads Total",            fmt_brl(ads))
    c4.metric("Lucro Bruto Estimado", fmt_brl(lucro_bruto),
              delta=f"{(lucro_bruto/rb*100):.1f}% margem" if rb > 0 else None)

    st.divider()
    if st.button("💾 Salvar Receitas", type="primary", key="btn_rec"):
        try:
            for _, row in df_rec_edit.iterrows():
                db_write("""
                    INSERT INTO receitas
                        (canal_id, competencia, receita_bruta, imposto, custo_produto,
                         frete, tarifa, desconto_cupom, afiliado, outros_cmv, ads)
                    VALUES
                        (:cid, :comp, :rb, :imp, :cp, :fr, :tar, :desc, :af, :ocmv, :ads)
                    ON CONFLICT (canal_id, competencia) DO UPDATE SET
                        receita_bruta  = EXCLUDED.receita_bruta,
                        imposto        = EXCLUDED.imposto,
                        custo_produto  = EXCLUDED.custo_produto,
                        frete          = EXCLUDED.frete,
                        tarifa         = EXCLUDED.tarifa,
                        desconto_cupom = EXCLUDED.desconto_cupom,
                        afiliado       = EXCLUDED.afiliado,
                        outros_cmv     = EXCLUDED.outros_cmv,
                        ads            = EXCLUDED.ads,
                        atualizado_em  = NOW()
                """, {
                    "cid":  str(row["canal_id"]),
                    "comp": comp,
                    "rb":   parse_br(row["Receita Bruta"]),
                    "imp":  parse_br(row["Imposto (DAS)"]),
                    "cp":   parse_br(row["Custo do Produto"]),
                    "fr":   parse_br(row["Frete"]),
                    "tar":  parse_br(row["Tarifa Plataforma"]),
                    "desc": parse_br(row["Desconto / Cupom"]),
                    "af":   parse_br(row["Afiliados"]),
                    "ocmv": parse_br(row["Outros CMV"]),
                    "ads":  parse_br(row["Ads (Anúncios)"]),
                })
            recalcular_dre(comp)
            run_query.clear()
            st.success(f"✅ Receitas de {fmt_mes(comp)} salvas! DRE atualizada.")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")


# ════════════════════════════════════════════════════════════════════════════════
# ABA 2 — FOLHA DE PAGAMENTO
# ════════════════════════════════════════════════════════════════════════════════
with tab_folha:
    st.markdown("Informe a remuneração de **cada funcionário** no mês. Use vírgula para decimais.")

    df_folha = run_query(SQL_FOLHA, {"comp": comp})
    for col in COLS_FOLHA:
        df_folha[col] = df_folha[col].apply(to_br)

    df_folha_edit = st.data_editor(
        df_folha,
        column_config={
            "func_id":       None,
            "tipo_raw":      None,
            "Funcionário":   st.column_config.TextColumn("Funcionário", disabled=True, width="medium"),
            "Tipo":          st.column_config.TextColumn("Tipo",        disabled=True, width="small"),
            "Salário Bruto": col_valor("Salário Bruto"),
            "Bônus":         col_valor("Bônus"),
            "FGTS":          col_valor("FGTS", "CLT: calculado automaticamente (8%) se deixado em 0,00"),
            "INSS Retido":   col_valor("INSS Retido", "Informativo — não é custo extra"),
        },
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key=f"editor_folha_{comp}",
    )

    total_folha = sum(
        parse_br(row["Salário Bruto"]) + parse_br(row["Bônus"]) + parse_br(row["FGTS"])
        for _, row in df_folha_edit.iterrows()
    )
    st.caption("💡 **FGTS** calculado automaticamente (8% de Salário + Bônus) para CLT se deixado em 0,00.")
    st.metric("Custo Total da Folha (estimado)", fmt_brl(total_folha))

    st.divider()
    if st.button("💾 Salvar Folha", type="primary", key="btn_folha"):
        try:
            for _, row in df_folha_edit.iterrows():
                sal  = parse_br(row["Salário Bruto"])
                bon  = parse_br(row["Bônus"])
                fgts = parse_br(row["FGTS"])
                if row["tipo_raw"] == "clt" and fgts == 0 and (sal + bon) > 0:
                    fgts = round((sal + bon) * 0.08, 2)

                db_write("""
                    INSERT INTO folha_pagamento
                        (funcionario_id, competencia, salario_bruto, bonus, fgts, inss_retido)
                    VALUES
                        (:fid, :comp, :sal, :bon, :fgts, :inss)
                    ON CONFLICT (funcionario_id, competencia) DO UPDATE SET
                        salario_bruto = EXCLUDED.salario_bruto,
                        bonus         = EXCLUDED.bonus,
                        fgts          = EXCLUDED.fgts,
                        inss_retido   = EXCLUDED.inss_retido,
                        atualizado_em = NOW()
                """, {
                    "fid":  str(row["func_id"]),
                    "comp": comp,
                    "sal":  sal,
                    "bon":  bon,
                    "fgts": fgts,
                    "inss": parse_br(row["INSS Retido"]),
                })
            recalcular_dre(comp)
            run_query.clear()
            st.success(f"✅ Folha de {fmt_mes(comp)} salva! DRE atualizada.")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")


# ════════════════════════════════════════════════════════════════════════════════
# ABA 3 — DESPESAS
# ════════════════════════════════════════════════════════════════════════════════
with tab_desp:
    st.markdown("Informe todas as despesas do mês. Use **+ Adicionar linha** para despesas extras.")

    df_desp_db = run_query(SQL_DESPESAS, {"comp": comp})
    df_cats    = run_query(SQL_CATS, {})
    cat_map    = dict(zip(df_cats["nome"], df_cats["id"]))
    CATS       = sorted(cat_map.keys())
    TIPOS      = ["fixo", "variavel", "eventual"]

    if df_desp_db.empty:
        df_desp = pd.DataFrame(DESPESAS_TEMPLATE)
    else:
        df_desp = df_desp_db.copy()
        df_desp["Valor"] = df_desp["Valor"].apply(to_br)

    df_desp_edit = st.data_editor(
        df_desp,
        column_config={
            "Categoria": st.column_config.SelectboxColumn(
                "Categoria", options=CATS, width="medium", required=True,
            ),
            "Descrição": st.column_config.TextColumn("Descrição", width="large", required=True),
            "Tipo": st.column_config.SelectboxColumn(
                "Tipo", options=TIPOS, width="small",
                help="fixo = todo mês | variavel = varia com volume | eventual = pontual",
            ),
            "Valor": col_valor("Valor"),
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key=f"editor_desp_{comp}",
    )

    total_desp = sum(parse_br(v) for v in df_desp_edit["Valor"])
    st.metric("Total de Despesas (estimado)", fmt_brl(total_desp))

    st.divider()
    if st.button("💾 Salvar Despesas", type="primary", key="btn_desp"):
        try:
            with _engine().connect() as conn:
                conn.execute(
                    text("DELETE FROM despesas WHERE competencia = :comp"),
                    {"comp": comp},
                )
                for _, row in df_desp_edit.iterrows():
                    desc = str(row.get("Descrição") or "").strip()
                    cat  = str(row.get("Categoria") or "").strip()
                    val  = parse_br(row.get("Valor"))
                    if not desc or not cat or val == 0:
                        continue
                    cat_id = cat_map.get(cat)
                    if not cat_id:
                        continue
                    conn.execute(text("""
                        INSERT INTO despesas (categoria_id, competencia, descricao, tipo, valor)
                        VALUES (:cat, :comp, :desc, :tipo, :val)
                    """), {
                        "cat":  cat_id,
                        "comp": comp,
                        "desc": desc,
                        "tipo": str(row.get("Tipo") or "fixo"),
                        "val":  val,
                    })
                conn.commit()
            recalcular_dre(comp)
            run_query.clear()
            st.success(f"✅ Despesas de {fmt_mes(comp)} salvas! DRE atualizada.")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
