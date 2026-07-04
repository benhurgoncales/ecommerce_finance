"""
All SQL queries used across dashboard pages.
Params use SQLAlchemy :name syntax → pass as dict to run_query().
"""

# ── Página 1: Visão Geral ──────────────────────────────────────────────────

METRICAS_GERAIS = """
SELECT
    SUM(receita_bruta)                                           AS receita_bruta,
    SUM(lucro_liquido)                                           AS lucro_liquido,
    ROUND(SUM(lucro_liquido) / NULLIF(SUM(receita_bruta),0) * 100, 2) AS margem_pct
FROM dre_consolidada
WHERE competencia BETWEEN :inicio AND :fim
"""

FATURAMENTO_POR_CANAL = """
SELECT
    canal                                                                AS "Canal",
    SUM(receita_bruta)                                                   AS "Receita Bruta",
    ROUND(SUM(receita_bruta) / NULLIF(SUM(SUM(receita_bruta)) OVER (), 0) * 100, 1) AS "% Faturamento"
FROM vw_receitas_calculadas
WHERE competencia BETWEEN :inicio AND :fim
GROUP BY canal
ORDER BY SUM(receita_bruta) DESC
"""

LUCRO_POR_CANAL = """
SELECT
    canal                                                                      AS "Canal",
    SUM(margem_liquida)                                                        AS "Lucro Líquido",
    ROUND(SUM(margem_liquida) / NULLIF(ABS(SUM(SUM(margem_liquida)) OVER ()), 0) * 100, 1) AS "% Lucro"
FROM vw_receitas_calculadas
WHERE competencia BETWEEN :inicio AND :fim
GROUP BY canal
ORDER BY SUM(margem_liquida) DESC
"""

DESPESAS_COMPOSICAO = """
SELECT
    competencia,
    desp_folha           AS "Folha",
    desp_administrativo  AS "Administrativo",
    desp_marketing       AS "Marketing",
    desp_financeiras     AS "Desp. Financeiras",
    desp_tecnologia      AS "Tecnologia",
    desp_educacao        AS "Educação"
FROM dre_consolidada
WHERE competencia BETWEEN :inicio AND :fim
ORDER BY competencia
"""

# ── Página 2: Canais ──────────────────────────────────────────────────────

CANAIS_COMPARATIVO = """
SELECT
    canal                                                              AS "Canal",
    SUM(receita_bruta)                                                 AS "Receita Bruta",
    SUM(imposto)                                                       AS "Imposto",
    SUM(cmv_total)                                                     AS "CMV Total",
    ROUND(SUM(margem_liquida), 2)                                      AS "Margem Líquida R$",
    ROUND(SUM(margem_liquida) / NULLIF(SUM(receita_bruta),0) * 100,1) AS "Margem Líquida %",
    SUM(ads)                                                           AS "Ads"
FROM vw_receitas_calculadas
WHERE competencia BETWEEN :inicio AND :fim
GROUP BY canal
ORDER BY SUM(receita_bruta) DESC
"""

CANAIS_MARGEM_PCT = """
SELECT
    canal AS "Canal",
    ROUND(SUM(margem_liquida) / NULLIF(SUM(receita_bruta),0) * 100, 1) AS "Margem %"
FROM vw_receitas_calculadas
WHERE competencia BETWEEN :inicio AND :fim
GROUP BY canal
ORDER BY 2 DESC
"""

CANAIS_PARTICIPACAO = """
SELECT
    canal AS "Canal",
    ROUND(SUM(receita_bruta) / SUM(SUM(receita_bruta)) OVER () * 100, 1) AS "% Receita"
FROM vw_receitas_calculadas
WHERE competencia BETWEEN :inicio AND :fim
GROUP BY canal
ORDER BY SUM(receita_bruta) DESC
"""

# ── Página 3: DRE ────────────────────────────────────────────────────────

DRE_DETALHE_CANAIS = """
SELECT
    canal AS nome,
    ROUND(SUM(CASE WHEN competencia BETWEEN :inicio AND :fim
                   THEN receita_bruta ELSE 0 END), 2) AS periodo,
    ROUND(SUM(CASE WHEN SUBSTRING(competencia,1,4) = SUBSTRING(CAST(:fim AS TEXT),1,4)
                    AND competencia <= :fim
                   THEN receita_bruta ELSE 0 END), 2) AS acumulado
FROM vw_receitas_calculadas
WHERE SUBSTRING(competencia,1,4) = SUBSTRING(CAST(:fim AS TEXT),1,4)
GROUP BY canal
ORDER BY periodo DESC
"""

DRE_DETALHE_FOLHA = """
SELECT
    func.nome ||
        CASE func.tipo
            WHEN 'pro_labore' THEN ' (pró-labore)'
            WHEN 'autonomo'   THEN ' (autônomo)'
            ELSE                   ' (CLT)'
        END AS nome,
    ROUND(SUM(CASE WHEN f.competencia BETWEEN :inicio AND :fim
                   THEN f.salario_bruto + f.bonus + f.fgts ELSE 0 END), 2) AS periodo,
    ROUND(SUM(CASE WHEN SUBSTRING(f.competencia,1,4) = SUBSTRING(CAST(:fim AS TEXT),1,4)
                    AND f.competencia <= :fim
                   THEN f.salario_bruto + f.bonus + f.fgts ELSE 0 END), 2) AS acumulado
FROM folha_pagamento f
JOIN funcionarios func ON func.id = f.funcionario_id
WHERE SUBSTRING(f.competencia,1,4) = SUBSTRING(CAST(:fim AS TEXT),1,4)
GROUP BY func.nome, func.tipo
ORDER BY periodo DESC
"""

DRE_DETALHE_DESPESAS = """
SELECT
    cd.nome    AS categoria,
    cd.ordem,
    d.descricao AS nome,
    ROUND(SUM(CASE WHEN d.competencia BETWEEN :inicio AND :fim
                   THEN d.valor ELSE 0 END), 2) AS periodo,
    ROUND(SUM(CASE WHEN SUBSTRING(d.competencia,1,4) = SUBSTRING(CAST(:fim AS TEXT),1,4)
                    AND d.competencia <= :fim
                   THEN d.valor ELSE 0 END), 2) AS acumulado
FROM despesas d
JOIN categorias_despesa cd ON cd.id = d.categoria_id
WHERE SUBSTRING(d.competencia,1,4) = SUBSTRING(CAST(:fim AS TEXT),1,4)
GROUP BY cd.nome, cd.ordem, d.descricao
ORDER BY cd.ordem, periodo DESC
"""

DRE_PERIODO = """
WITH periodo AS (
    SELECT
        SUM(receita_bruta)       AS receita_bruta,
        SUM(impostos)            AS impostos,
        SUM(receita_liquida)     AS receita_liquida,
        SUM(cmv_total)           AS cmv_total,
        SUM(lucro_bruto)         AS lucro_bruto,
        SUM(desp_folha)          AS desp_folha,
        SUM(desp_administrativo) AS desp_administrativo,
        SUM(desp_marketing)      AS desp_marketing,
        SUM(desp_financeiras)    AS desp_financeiras,
        SUM(desp_tecnologia)     AS desp_tecnologia,
        SUM(desp_educacao)       AS desp_educacao,
        SUM(total_despesas)      AS total_despesas,
        SUM(ebitda)              AS ebitda,
        SUM(lucro_liquido)       AS lucro_liquido,
        CASE WHEN SUM(receita_bruta) > 0
             THEN ROUND(SUM(lucro_bruto)   / SUM(receita_bruta) * 100, 2) END AS margem_bruta_pct,
        CASE WHEN SUM(receita_bruta) > 0
             THEN ROUND(SUM(lucro_liquido) / SUM(receita_bruta) * 100, 2) END AS margem_liq_pct
    FROM dre_consolidada
    WHERE competencia BETWEEN :inicio AND :fim
),
acumulado AS (
    SELECT
        SUM(receita_bruta)       AS receita_bruta,
        SUM(impostos)            AS impostos,
        SUM(receita_liquida)     AS receita_liquida,
        SUM(cmv_total)           AS cmv_total,
        SUM(lucro_bruto)         AS lucro_bruto,
        SUM(desp_folha)          AS desp_folha,
        SUM(desp_administrativo) AS desp_administrativo,
        SUM(desp_marketing)      AS desp_marketing,
        SUM(desp_financeiras)    AS desp_financeiras,
        SUM(desp_tecnologia)     AS desp_tecnologia,
        SUM(desp_educacao)       AS desp_educacao,
        SUM(total_despesas)      AS total_despesas,
        SUM(ebitda)              AS ebitda,
        SUM(lucro_liquido)       AS lucro_liquido,
        CASE WHEN SUM(receita_bruta) > 0
             THEN ROUND(SUM(lucro_bruto)   / SUM(receita_bruta) * 100, 2) END AS margem_bruta_pct,
        CASE WHEN SUM(receita_bruta) > 0
             THEN ROUND(SUM(lucro_liquido) / SUM(receita_bruta) * 100, 2) END AS margem_liq_pct
    FROM dre_consolidada
    WHERE SUBSTRING(competencia,1,4) = SUBSTRING(CAST(:fim AS TEXT),1,4)
      AND competencia <= :fim
)
SELECT linha AS "Linha DRE", periodo AS "Período", acumulado_ano AS "Acumulado do Ano"
FROM (
    SELECT 1  ord,'(+) Receita Bruta'             linha,p.receita_bruta      AS periodo, a.receita_bruta       AS acumulado_ano FROM periodo p,acumulado a
    UNION ALL SELECT 2, '(-) Impostos',                 p.impostos,            a.impostos             FROM periodo p,acumulado a
    UNION ALL SELECT 3, '(=) Receita Líquida',          p.receita_liquida,     a.receita_liquida      FROM periodo p,acumulado a
    UNION ALL SELECT 4, '(-) CMV Total',                p.cmv_total,           a.cmv_total            FROM periodo p,acumulado a
    UNION ALL SELECT 5, '(=) Lucro Bruto',              p.lucro_bruto,         a.lucro_bruto          FROM periodo p,acumulado a
    UNION ALL SELECT 6, '    Margem Bruta %',           p.margem_bruta_pct,    a.margem_bruta_pct     FROM periodo p,acumulado a
    UNION ALL SELECT 7, '(-) Folha de Pagamento',       p.desp_folha,          a.desp_folha           FROM periodo p,acumulado a
    UNION ALL SELECT 8, '(-) Administrativo',           p.desp_administrativo, a.desp_administrativo  FROM periodo p,acumulado a
    UNION ALL SELECT 9, '(-) Marketing',                p.desp_marketing,      a.desp_marketing       FROM periodo p,acumulado a
    UNION ALL SELECT 10,'(-) Despesas Financeiras',     p.desp_financeiras,    a.desp_financeiras     FROM periodo p,acumulado a
    UNION ALL SELECT 11,'(-) Tecnologia e Ferramentas', p.desp_tecnologia,     a.desp_tecnologia      FROM periodo p,acumulado a
    UNION ALL SELECT 12,'(-) Educação e Capacitação',   p.desp_educacao,       a.desp_educacao        FROM periodo p,acumulado a
    UNION ALL SELECT 13,'(=) Total Despesas',           p.total_despesas,      a.total_despesas       FROM periodo p,acumulado a
    UNION ALL SELECT 14,'(=) EBITDA',                   p.ebitda,              a.ebitda               FROM periodo p,acumulado a
    UNION ALL SELECT 15,'(=) Lucro Líquido',            p.lucro_liquido,       a.lucro_liquido        FROM periodo p,acumulado a
    UNION ALL SELECT 16,'    Margem Líquida %',         p.margem_liq_pct,      a.margem_liq_pct       FROM periodo p,acumulado a
) sub
ORDER BY ord
"""

# ── Página 4: Custos ────────────────────────────────────────────────────

TOTAL_DESPESAS = """
SELECT SUM(total_despesas) AS total
FROM dre_consolidada
WHERE competencia BETWEEN :inicio AND :fim
"""

DESPESAS_POR_CATEGORIA = """
SELECT categoria AS "Categoria", SUM(total) AS "R$"
FROM vw_despesas_por_categoria
WHERE competencia BETWEEN :inicio AND :fim
GROUP BY categoria
ORDER BY 2 DESC
"""

CUSTO_POR_PESSOA = """
SELECT
    nome AS "Funcionário",
    SUM(custo_total) AS "Custo Total",
    ROUND(SUM(custo_total) / SUM(SUM(custo_total)) OVER () * 100, 1) AS "% Despesas"
FROM vw_custo_por_pessoa
WHERE competencia BETWEEN :inicio AND :fim
GROUP BY nome
ORDER BY 2 DESC
"""

TOP5_CUSTOS = """
WITH total AS (
    SELECT SUM(total_despesas) AS grand_total
    FROM dre_consolidada
    WHERE competencia BETWEEN :inicio AND :fim
),
itens AS (
    -- Funcionários (custo total individual)
    SELECT
        func.nome                       AS item,
        SUM(f.salario_bruto + f.bonus + f.fgts) AS valor
    FROM folha_pagamento f
    JOIN funcionarios func ON func.id = f.funcionario_id
    WHERE f.competencia BETWEEN :inicio AND :fim
    GROUP BY func.nome

    UNION ALL

    -- Despesas individuais por descrição
    SELECT
        d.descricao                     AS item,
        SUM(d.valor)                    AS valor
    FROM despesas d
    WHERE d.competencia BETWEEN :inicio AND :fim
    GROUP BY d.descricao
)
SELECT
    item                                                               AS "Item",
    valor                                                              AS "Valor",
    ROUND(valor / NULLIF(t.grand_total, 0) * 100, 1)                  AS "% do Total"
FROM itens, total t
ORDER BY valor DESC
LIMIT 5
"""

EVOLUCAO_DESPESAS = """
SELECT competencia, total_despesas AS "Total Despesas"
FROM dre_consolidada
WHERE competencia BETWEEN :inicio AND :fim
ORDER BY competencia
"""

DESPESAS_DETALHADAS = """
SELECT
    cd.nome      AS "Categoria",
    d.descricao  AS "Descrição",
    d.tipo       AS "Tipo",
    SUM(d.valor) AS "Valor"
FROM despesas d
JOIN categorias_despesa cd ON cd.id = d.categoria_id
WHERE d.competencia BETWEEN :inicio AND :fim
GROUP BY cd.nome, d.descricao, d.tipo, cd.ordem
ORDER BY cd.ordem, SUM(d.valor) DESC
"""
