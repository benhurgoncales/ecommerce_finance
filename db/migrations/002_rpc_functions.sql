-- ============================================================
-- 002_rpc_functions.sql
-- Funções PostgreSQL para acesso via supabase.rpc() (HTTPS)
-- Cole no SQL Editor do Supabase e execute tudo de uma vez
-- ============================================================

-- ─────────────────────────────────────────────────────────────────
-- FILTRO GLOBAL
-- ─────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION fn_competencias()
RETURNS TABLE(competencia text)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT DISTINCT competencia::text FROM dre_consolidada ORDER BY competencia;
$$;

-- ─────────────────────────────────────────────────────────────────
-- PÁGINA 1: VISÃO GERAL
-- ─────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION fn_metricas_gerais(inicio text, fim text)
RETURNS TABLE(receita_bruta numeric, lucro_liquido numeric, margem_pct numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    SUM(receita_bruta)::numeric,
    SUM(lucro_liquido)::numeric,
    ROUND(SUM(lucro_liquido) / NULLIF(SUM(receita_bruta), 0) * 100, 2)::numeric
  FROM dre_consolidada
  WHERE competencia BETWEEN inicio AND fim;
$$;

CREATE OR REPLACE FUNCTION fn_faturamento_por_canal(inicio text, fim text)
RETURNS TABLE("Canal" text, "Receita Bruta" numeric, "% Faturamento" numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    canal::text,
    SUM(receita_bruta)::numeric,
    ROUND(SUM(receita_bruta) / NULLIF(SUM(SUM(receita_bruta)) OVER (), 0) * 100, 1)::numeric
  FROM vw_receitas_calculadas
  WHERE competencia BETWEEN inicio AND fim
  GROUP BY canal
  ORDER BY SUM(receita_bruta) DESC;
$$;

CREATE OR REPLACE FUNCTION fn_lucro_por_canal(inicio text, fim text)
RETURNS TABLE("Canal" text, "Lucro Líquido" numeric, "% Lucro" numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    canal::text,
    SUM(margem_liquida)::numeric,
    ROUND(SUM(margem_liquida) / NULLIF(ABS(SUM(SUM(margem_liquida)) OVER ()), 0) * 100, 1)::numeric
  FROM vw_receitas_calculadas
  WHERE competencia BETWEEN inicio AND fim
  GROUP BY canal
  ORDER BY SUM(margem_liquida) DESC;
$$;

CREATE OR REPLACE FUNCTION fn_despesas_composicao(inicio text, fim text)
RETURNS TABLE(
  competencia          text,
  "Folha"              numeric,
  "Administrativo"     numeric,
  "Marketing"          numeric,
  "Desp. Financeiras"  numeric,
  "Tecnologia"         numeric,
  "Educação"           numeric
)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    competencia::text,
    desp_folha::numeric,
    desp_administrativo::numeric,
    desp_marketing::numeric,
    desp_financeiras::numeric,
    desp_tecnologia::numeric,
    desp_educacao::numeric
  FROM dre_consolidada
  WHERE competencia BETWEEN inicio AND fim
  ORDER BY competencia;
$$;

-- ─────────────────────────────────────────────────────────────────
-- PÁGINA 2: CANAIS
-- ─────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION fn_canais_comparativo(inicio text, fim text)
RETURNS TABLE(
  "Canal"              text,
  "Receita Bruta"      numeric,
  "Imposto"            numeric,
  "CMV Total"          numeric,
  "Margem Líquida R$"  numeric,
  "Margem Líquida %"   numeric,
  "Ads"                numeric
)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    canal::text,
    SUM(receita_bruta)::numeric,
    SUM(imposto)::numeric,
    SUM(cmv_total)::numeric,
    ROUND(SUM(margem_liquida), 2)::numeric,
    ROUND(SUM(margem_liquida) / NULLIF(SUM(receita_bruta), 0) * 100, 1)::numeric,
    SUM(ads)::numeric
  FROM vw_receitas_calculadas
  WHERE competencia BETWEEN inicio AND fim
  GROUP BY canal
  ORDER BY SUM(receita_bruta) DESC;
$$;

CREATE OR REPLACE FUNCTION fn_canais_margem_pct(inicio text, fim text)
RETURNS TABLE("Canal" text, "Margem %" numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    canal::text,
    ROUND(SUM(margem_liquida) / NULLIF(SUM(receita_bruta), 0) * 100, 1)::numeric
  FROM vw_receitas_calculadas
  WHERE competencia BETWEEN inicio AND fim
  GROUP BY canal
  ORDER BY 2 DESC;
$$;

-- ─────────────────────────────────────────────────────────────────
-- PÁGINA 3: DRE
-- ─────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION fn_dre_detalhe_canais(inicio text, fim text)
RETURNS TABLE(nome text, periodo numeric, acumulado numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    canal::text AS nome,
    ROUND(SUM(CASE WHEN competencia BETWEEN inicio AND fim
                   THEN receita_bruta ELSE 0 END), 2)::numeric,
    ROUND(SUM(CASE WHEN SUBSTRING(competencia,1,4) = SUBSTRING(fim,1,4)
                    AND competencia <= fim
                   THEN receita_bruta ELSE 0 END), 2)::numeric
  FROM vw_receitas_calculadas
  WHERE SUBSTRING(competencia,1,4) = SUBSTRING(fim,1,4)
  GROUP BY canal
  ORDER BY 2 DESC;
$$;

CREATE OR REPLACE FUNCTION fn_dre_detalhe_folha(inicio text, fim text)
RETURNS TABLE(nome text, periodo numeric, acumulado numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    (func.nome || CASE func.tipo
        WHEN 'pro_labore' THEN ' (pró-labore)'
        WHEN 'autonomo'   THEN ' (autônomo)'
        ELSE                   ' (CLT)'
      END)::text AS nome,
    ROUND(SUM(CASE WHEN f.competencia BETWEEN inicio AND fim
                   THEN f.salario_bruto + f.bonus + f.fgts ELSE 0 END), 2)::numeric,
    ROUND(SUM(CASE WHEN SUBSTRING(f.competencia,1,4) = SUBSTRING(fim,1,4)
                    AND f.competencia <= fim
                   THEN f.salario_bruto + f.bonus + f.fgts ELSE 0 END), 2)::numeric
  FROM folha_pagamento f
  JOIN funcionarios func ON func.id = f.funcionario_id
  WHERE SUBSTRING(f.competencia,1,4) = SUBSTRING(fim,1,4)
  GROUP BY func.nome, func.tipo
  ORDER BY 2 DESC;
$$;

CREATE OR REPLACE FUNCTION fn_dre_detalhe_despesas(inicio text, fim text)
RETURNS TABLE(categoria text, ordem int, nome text, periodo numeric, acumulado numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    cd.nome::text,
    cd.ordem::int,
    d.descricao::text,
    ROUND(SUM(CASE WHEN d.competencia BETWEEN inicio AND fim
                   THEN d.valor ELSE 0 END), 2)::numeric,
    ROUND(SUM(CASE WHEN SUBSTRING(d.competencia,1,4) = SUBSTRING(fim,1,4)
                    AND d.competencia <= fim
                   THEN d.valor ELSE 0 END), 2)::numeric
  FROM despesas d
  JOIN categorias_despesa cd ON cd.id = d.categoria_id
  WHERE SUBSTRING(d.competencia,1,4) = SUBSTRING(fim,1,4)
  GROUP BY cd.nome, cd.ordem, d.descricao
  ORDER BY cd.ordem, 4 DESC;
$$;

CREATE OR REPLACE FUNCTION fn_dre_periodo(inicio text, fim text)
RETURNS TABLE("Linha DRE" text, "Período" numeric, "Acumulado do Ano" numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
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
  FROM dre_consolidada WHERE competencia BETWEEN inicio AND fim
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
  WHERE SUBSTRING(competencia,1,4) = SUBSTRING(fim,1,4) AND competencia <= fim
)
SELECT linha::text, pval::numeric, aval::numeric
FROM (
  SELECT 1  ord,'(+) Receita Bruta'             linha,p.receita_bruta      pval,a.receita_bruta       aval FROM periodo p,acumulado a
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
ORDER BY ord;
$$;

-- ─────────────────────────────────────────────────────────────────
-- PÁGINA 4: CUSTOS E DESPESAS
-- ─────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION fn_total_despesas(inicio text, fim text)
RETURNS TABLE(total numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT SUM(total_despesas)::numeric FROM dre_consolidada
  WHERE competencia BETWEEN inicio AND fim;
$$;

CREATE OR REPLACE FUNCTION fn_despesas_por_categoria(inicio text, fim text)
RETURNS TABLE("Categoria" text, "R$" numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT categoria::text, SUM(total)::numeric
  FROM vw_despesas_por_categoria
  WHERE competencia BETWEEN inicio AND fim
  GROUP BY categoria
  ORDER BY 2 DESC;
$$;

CREATE OR REPLACE FUNCTION fn_top5_custos(inicio text, fim text)
RETURNS TABLE("Item" text, "Valor" numeric, "% do Total" numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  WITH total AS (
    SELECT SUM(total_despesas) AS grand_total
    FROM dre_consolidada
    WHERE competencia BETWEEN inicio AND fim
  ),
  itens AS (
    SELECT func.nome AS item, SUM(f.salario_bruto + f.bonus + f.fgts) AS valor
    FROM folha_pagamento f
    JOIN funcionarios func ON func.id = f.funcionario_id
    WHERE f.competencia BETWEEN inicio AND fim
    GROUP BY func.nome
    UNION ALL
    SELECT d.descricao, SUM(d.valor)
    FROM despesas d
    WHERE d.competencia BETWEEN inicio AND fim
    GROUP BY d.descricao
  )
  SELECT
    item::text,
    valor::numeric,
    ROUND(valor / NULLIF(t.grand_total, 0) * 100, 1)::numeric
  FROM itens, total t
  ORDER BY valor DESC
  LIMIT 5;
$$;

CREATE OR REPLACE FUNCTION fn_evolucao_despesas(inicio text, fim text)
RETURNS TABLE(competencia text, "Total Despesas" numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT competencia::text, total_despesas::numeric
  FROM dre_consolidada
  WHERE competencia BETWEEN inicio AND fim
  ORDER BY competencia;
$$;

CREATE OR REPLACE FUNCTION fn_despesas_detalhadas(inicio text, fim text)
RETURNS TABLE("Categoria" text, "Descrição" text, "Tipo" text, "Valor" numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    cd.nome::text,
    d.descricao::text,
    d.tipo::text,
    SUM(d.valor)::numeric
  FROM despesas d
  JOIN categorias_despesa cd ON cd.id = d.categoria_id
  WHERE d.competencia BETWEEN inicio AND fim
  GROUP BY cd.nome, d.descricao, d.tipo, cd.ordem
  ORDER BY cd.ordem, SUM(d.valor) DESC;
$$;

-- ─────────────────────────────────────────────────────────────────
-- PÁGINA 5: LANÇAMENTOS (leitura)
-- ─────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION fn_receitas_lancamentos(comp text)
RETURNS TABLE(
  canal_id           uuid,
  "Canal"            text,
  "Receita Bruta"    numeric,
  "Imposto (DAS)"    numeric,
  "Custo do Produto" numeric,
  "Frete"            numeric,
  "Tarifa Plataforma" numeric,
  "Desconto / Cupom" numeric,
  "Afiliados"        numeric,
  "Outros CMV"       numeric,
  "Ads (Anúncios)"   numeric
)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    c.id,
    c.nome::text,
    COALESCE(r.receita_bruta,  0)::numeric,
    COALESCE(r.imposto,        0)::numeric,
    COALESCE(r.custo_produto,  0)::numeric,
    COALESCE(r.frete,          0)::numeric,
    COALESCE(r.tarifa,         0)::numeric,
    COALESCE(r.desconto_cupom, 0)::numeric,
    COALESCE(r.afiliado,       0)::numeric,
    COALESCE(r.outros_cmv,     0)::numeric,
    COALESCE(r.ads,            0)::numeric
  FROM canais c
  LEFT JOIN receitas r ON r.canal_id = c.id AND r.competencia = comp
  WHERE c.ativo = true
  ORDER BY c.nome;
$$;

CREATE OR REPLACE FUNCTION fn_folha_lancamentos(comp text)
RETURNS TABLE(
  func_id        uuid,
  "Funcionário"  text,
  tipo_raw       text,
  "Tipo"         text,
  "Salário Bruto" numeric,
  "Bônus"        numeric,
  "FGTS"         numeric,
  "INSS Retido"  numeric
)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    fu.id,
    fu.nome::text,
    fu.tipo::text,
    CASE fu.tipo
      WHEN 'pro_labore' THEN 'Pró-labore'
      WHEN 'autonomo'   THEN 'Autônomo'
      WHEN 'clt'        THEN 'CLT'
    END::text,
    COALESCE(fp.salario_bruto, 0)::numeric,
    COALESCE(fp.bonus,         0)::numeric,
    COALESCE(fp.fgts,          0)::numeric,
    COALESCE(fp.inss_retido,   0)::numeric
  FROM funcionarios fu
  LEFT JOIN folha_pagamento fp ON fp.funcionario_id = fu.id AND fp.competencia = comp
  WHERE fu.ativo = true
  ORDER BY fu.nome;
$$;

CREATE OR REPLACE FUNCTION fn_despesas_lancamentos(comp text)
RETURNS TABLE("Categoria" text, "Descrição" text, "Tipo" text, "Valor" numeric)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT
    cd.nome::text,
    d.descricao::text,
    d.tipo::text,
    d.valor::numeric
  FROM despesas d
  JOIN categorias_despesa cd ON cd.id = d.categoria_id
  WHERE d.competencia = comp
  ORDER BY cd.ordem, d.descricao;
$$;

CREATE OR REPLACE FUNCTION fn_categorias_despesa()
RETURNS TABLE(id integer, nome text)
LANGUAGE sql STABLE SECURITY DEFINER AS $$
  SELECT id, nome::text FROM categorias_despesa ORDER BY ordem;
$$;

-- ─────────────────────────────────────────────────────────────────
-- ESCRITA: LANÇAMENTOS
-- ─────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION fn_upsert_receita(
  p_canal_id     uuid,
  p_competencia  text,
  p_receita_bruta  numeric,
  p_imposto        numeric,
  p_custo_produto  numeric,
  p_frete          numeric,
  p_tarifa         numeric,
  p_desconto_cupom numeric,
  p_afiliado       numeric,
  p_outros_cmv     numeric,
  p_ads            numeric
) RETURNS void LANGUAGE sql VOLATILE SECURITY DEFINER AS $$
  INSERT INTO receitas
    (canal_id, competencia, receita_bruta, imposto, custo_produto,
     frete, tarifa, desconto_cupom, afiliado, outros_cmv, ads)
  VALUES
    (p_canal_id, p_competencia, p_receita_bruta, p_imposto, p_custo_produto,
     p_frete, p_tarifa, p_desconto_cupom, p_afiliado, p_outros_cmv, p_ads)
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
    atualizado_em  = NOW();
$$;

CREATE OR REPLACE FUNCTION fn_upsert_folha(
  p_funcionario_id  uuid,
  p_competencia     text,
  p_salario_bruto   numeric,
  p_bonus           numeric,
  p_fgts            numeric,
  p_inss_retido     numeric
) RETURNS void LANGUAGE sql VOLATILE SECURITY DEFINER AS $$
  INSERT INTO folha_pagamento
    (funcionario_id, competencia, salario_bruto, bonus, fgts, inss_retido)
  VALUES
    (p_funcionario_id, p_competencia, p_salario_bruto, p_bonus, p_fgts, p_inss_retido)
  ON CONFLICT (funcionario_id, competencia) DO UPDATE SET
    salario_bruto = EXCLUDED.salario_bruto,
    bonus         = EXCLUDED.bonus,
    fgts          = EXCLUDED.fgts,
    inss_retido   = EXCLUDED.inss_retido,
    atualizado_em = NOW();
$$;

CREATE OR REPLACE FUNCTION fn_salvar_despesas(
  p_competencia text,
  p_linhas      jsonb
) RETURNS void LANGUAGE plpgsql VOLATILE SECURITY DEFINER AS $$
DECLARE
  linha jsonb;
BEGIN
  DELETE FROM despesas WHERE competencia = p_competencia;
  FOR linha IN SELECT * FROM jsonb_array_elements(p_linhas)
  LOOP
    INSERT INTO despesas (categoria_id, competencia, descricao, tipo, valor)
    VALUES (
      (linha->>'categoria_id')::integer,
      p_competencia,
      linha->>'descricao',
      linha->>'tipo',
      (linha->>'valor')::numeric
    );
  END LOOP;
END;
$$;

-- ─────────────────────────────────────────────────────────────────
-- GRANTS (permite acesso pelo anon key do Supabase)
-- ─────────────────────────────────────────────────────────────────

GRANT EXECUTE ON FUNCTION fn_competencias() TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_metricas_gerais(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_faturamento_por_canal(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_lucro_por_canal(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_despesas_composicao(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_canais_comparativo(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_canais_margem_pct(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_dre_detalhe_canais(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_dre_detalhe_folha(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_dre_detalhe_despesas(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_dre_periodo(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_total_despesas(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_despesas_por_categoria(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_top5_custos(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_evolucao_despesas(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_despesas_detalhadas(text,text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_receitas_lancamentos(text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_folha_lancamentos(text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_despesas_lancamentos(text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_categorias_despesa() TO anon, authenticated;

-- Recarrega schema cache do PostgREST
NOTIFY pgrst, 'reload schema';
GRANT EXECUTE ON FUNCTION fn_upsert_receita(uuid,text,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric,numeric) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_upsert_folha(uuid,text,numeric,numeric,numeric,numeric) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_salvar_despesas(text,jsonb) TO anon, authenticated;
