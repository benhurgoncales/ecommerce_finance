"""
Nomes das funções PostgreSQL chamadas via supabase.rpc().
Params continuam com as mesmas chaves: {"inicio": ..., "fim": ...} ou {"comp": ...}
"""

# ── Página 1: Visão Geral ──────────────────────────────────────────────────
METRICAS_GERAIS         = "fn_metricas_gerais"
FATURAMENTO_POR_CANAL   = "fn_faturamento_por_canal"
LUCRO_POR_CANAL         = "fn_lucro_por_canal"
DESPESAS_COMPOSICAO     = "fn_despesas_composicao"

# ── Página 2: Canais ──────────────────────────────────────────────────────
CANAIS_COMPARATIVO      = "fn_canais_comparativo"
CANAIS_MARGEM_PCT       = "fn_canais_margem_pct"
CANAIS_PARTICIPACAO     = "fn_faturamento_por_canal"   # mesmo dado

# ── Página 3: DRE ────────────────────────────────────────────────────────
DRE_PERIODO             = "fn_dre_periodo"
DRE_DETALHE_CANAIS      = "fn_dre_detalhe_canais"
DRE_DETALHE_FOLHA       = "fn_dre_detalhe_folha"
DRE_DETALHE_DESPESAS    = "fn_dre_detalhe_despesas"

# ── Página 4: Custos e Despesas ──────────────────────────────────────────
TOTAL_DESPESAS          = "fn_total_despesas"
DESPESAS_POR_CATEGORIA  = "fn_despesas_por_categoria"
TOP5_CUSTOS             = "fn_top5_custos"
EVOLUCAO_DESPESAS       = "fn_evolucao_despesas"
DESPESAS_DETALHADAS     = "fn_despesas_detalhadas"
CUSTO_POR_PESSOA        = "fn_top5_custos"             # aposentado, fallback

# ── Página 5: Lançamentos ────────────────────────────────────────────────
RECEITAS_LANCAMENTOS    = "fn_receitas_lancamentos"
FOLHA_LANCAMENTOS       = "fn_folha_lancamentos"
DESPESAS_LANCAMENTOS    = "fn_despesas_lancamentos"
CATEGORIAS_DESPESA      = "fn_categorias_despesa"
