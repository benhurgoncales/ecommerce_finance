-- Migration: adiciona VR (Vale Refeição) e VT (Vale Transporte) à folha de pagamento
-- Benefícios não entram na base de cálculo do FGTS, mas somam ao custo total da empresa.

ALTER TABLE folha_pagamento
    ADD COLUMN IF NOT EXISTS vr NUMERIC(10,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS vt NUMERIC(10,2) NOT NULL DEFAULT 0;

COMMENT ON COLUMN folha_pagamento.vr IS 'Vale Refeição — benefício, sem incidência de FGTS/INSS';
COMMENT ON COLUMN folha_pagamento.vt IS 'Vale Transporte — benefício, sem incidência de FGTS/INSS';


-- ─────────────────────────────────────────────────────────────────
-- VIEWS: incluir VR/VT no custo total por funcionário
-- ─────────────────────────────────────────────────────────────────

DROP VIEW IF EXISTS vw_folha_calculada CASCADE;
CREATE VIEW vw_folha_calculada AS
SELECT
    f.competencia,
    func.nome,
    func.tipo,
    f.salario_bruto,
    f.bonus,
    f.fgts,
    f.inss_retido,
    f.vr,
    f.vt,
    f.salario_bruto + f.bonus + f.fgts + f.vr + f.vt  AS custo_total_empresa
FROM folha_pagamento f
JOIN funcionarios func ON func.id = f.funcionario_id;

COMMENT ON VIEW vw_folha_calculada IS 'Folha com custo real para a empresa por funcionário';

DROP VIEW IF EXISTS vw_custo_por_pessoa CASCADE;
CREATE VIEW vw_custo_por_pessoa AS
SELECT
    f.competencia,
    func.nome,
    func.tipo,
    f.salario_bruto + f.bonus + f.fgts + f.vr + f.vt          AS custo_total,
    ROUND(
        (f.salario_bruto + f.bonus + f.fgts + f.vr + f.vt)
        / NULLIF(d.total_despesas, 0) * 100, 1
    )                                                          AS pct_total_despesas
FROM folha_pagamento f
JOIN funcionarios func ON func.id = f.funcionario_id
JOIN dre_consolidada d  ON d.competencia = f.competencia;

COMMENT ON VIEW vw_custo_por_pessoa IS 'Custo real por funcionário no mês com percentual sobre o total de despesas';


-- ─────────────────────────────────────────────────────────────────
-- recalcular_dre: soma de folha agora inclui VR/VT
-- ─────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION recalcular_dre(p_competencia CHAR(7))
RETURNS VOID AS $$
DECLARE
    v_receita_bruta      NUMERIC(14,2);
    v_impostos           NUMERIC(14,2);
    v_cmv_total          NUMERIC(14,2);
    v_ads_total          NUMERIC(14,2);
    v_receita_liquida    NUMERIC(14,2);
    v_lucro_bruto        NUMERIC(14,2);
    v_desp_folha         NUMERIC(14,2);
    v_desp_adm           NUMERIC(14,2);
    v_desp_mkt           NUMERIC(14,2);
    v_desp_fin           NUMERIC(14,2);
    v_desp_tec           NUMERIC(14,2);
    v_desp_edu           NUMERIC(14,2);
    v_total_despesas     NUMERIC(14,2);
    v_ebitda             NUMERIC(14,2);
    v_lucro_liquido      NUMERIC(14,2);
BEGIN
    -- Receitas agregadas
    SELECT
        COALESCE(SUM(receita_bruta), 0),
        COALESCE(SUM(imposto), 0),
        COALESCE(SUM(custo_produto + frete + tarifa + desconto_cupom + afiliado + outros_cmv), 0),
        COALESCE(SUM(ads), 0)
    INTO v_receita_bruta, v_impostos, v_cmv_total, v_ads_total
    FROM receitas
    WHERE competencia = p_competencia;

    v_receita_liquida := v_receita_bruta - v_impostos;
    v_lucro_bruto     := v_receita_liquida - v_cmv_total - v_ads_total;

    -- Folha de pagamento (inclui VR/VT)
    SELECT COALESCE(SUM(salario_bruto + bonus + fgts + vr + vt), 0)
    INTO v_desp_folha
    FROM folha_pagamento
    WHERE competencia = p_competencia;

    -- Despesas por categoria
    SELECT COALESCE(SUM(d.valor), 0) INTO v_desp_adm
    FROM despesas d JOIN categorias_despesa cd ON cd.id = d.categoria_id
    WHERE d.competencia = p_competencia AND cd.nome = 'Administrativo';

    SELECT COALESCE(SUM(d.valor), 0) INTO v_desp_mkt
    FROM despesas d JOIN categorias_despesa cd ON cd.id = d.categoria_id
    WHERE d.competencia = p_competencia AND cd.nome = 'Marketing';

    SELECT COALESCE(SUM(d.valor), 0) INTO v_desp_fin
    FROM despesas d JOIN categorias_despesa cd ON cd.id = d.categoria_id
    WHERE d.competencia = p_competencia AND cd.nome = 'Despesas Financeiras';

    SELECT COALESCE(SUM(d.valor), 0) INTO v_desp_tec
    FROM despesas d JOIN categorias_despesa cd ON cd.id = d.categoria_id
    WHERE d.competencia = p_competencia AND cd.nome = 'Tecnologia e Ferramentas';

    SELECT COALESCE(SUM(d.valor), 0) INTO v_desp_edu
    FROM despesas d JOIN categorias_despesa cd ON cd.id = d.categoria_id
    WHERE d.competencia = p_competencia AND cd.nome = 'Educação e Capacitação';

    v_total_despesas := v_desp_folha + v_desp_adm + v_desp_mkt
                      + v_desp_fin  + v_desp_tec + v_desp_edu;
    v_ebitda         := v_lucro_bruto - v_total_despesas;
    v_lucro_liquido  := v_ebitda;

    -- Upsert na dre_consolidada
    INSERT INTO dre_consolidada (
        competencia,
        receita_bruta, impostos, receita_liquida,
        cmv_total, lucro_bruto,
        margem_bruta_pct,
        desp_folha, desp_administrativo, desp_marketing,
        desp_financeiras, desp_tecnologia, desp_educacao,
        total_despesas,
        ebitda, ebitda_pct,
        lucro_liquido, margem_liquida_pct,
        gerado_em
    ) VALUES (
        p_competencia,
        v_receita_bruta, v_impostos, v_receita_liquida,
        v_cmv_total, v_lucro_bruto,
        CASE WHEN v_receita_bruta > 0
             THEN ROUND(v_lucro_bruto / v_receita_bruta, 4) ELSE 0 END,
        v_desp_folha, v_desp_adm, v_desp_mkt,
        v_desp_fin, v_desp_tec, v_desp_edu,
        v_total_despesas,
        v_ebitda,
        CASE WHEN v_receita_bruta > 0
             THEN ROUND(v_ebitda / v_receita_bruta, 4) ELSE 0 END,
        v_lucro_liquido,
        CASE WHEN v_receita_bruta > 0
             THEN ROUND(v_lucro_liquido / v_receita_bruta, 4) ELSE 0 END,
        NOW()
    )
    ON CONFLICT (competencia) DO UPDATE SET
        receita_bruta       = EXCLUDED.receita_bruta,
        impostos            = EXCLUDED.impostos,
        receita_liquida     = EXCLUDED.receita_liquida,
        cmv_total           = EXCLUDED.cmv_total,
        lucro_bruto         = EXCLUDED.lucro_bruto,
        margem_bruta_pct    = EXCLUDED.margem_bruta_pct,
        desp_folha          = EXCLUDED.desp_folha,
        desp_administrativo = EXCLUDED.desp_administrativo,
        desp_marketing      = EXCLUDED.desp_marketing,
        desp_financeiras    = EXCLUDED.desp_financeiras,
        desp_tecnologia     = EXCLUDED.desp_tecnologia,
        desp_educacao       = EXCLUDED.desp_educacao,
        total_despesas      = EXCLUDED.total_despesas,
        ebitda              = EXCLUDED.ebitda,
        ebitda_pct          = EXCLUDED.ebitda_pct,
        lucro_liquido       = EXCLUDED.lucro_liquido,
        margem_liquida_pct  = EXCLUDED.margem_liquida_pct,
        gerado_em           = NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION recalcular_dre IS 'Recalcula e atualiza a DRE consolidada para o mês informado. Chamada pelo ETL após cada carga.';


-- ─────────────────────────────────────────────────────────────────
-- RPCs de leitura: incluir VR/VT
-- ─────────────────────────────────────────────────────────────────

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
                   THEN f.salario_bruto + f.bonus + f.fgts + f.vr + f.vt ELSE 0 END), 2)::numeric,
    ROUND(SUM(CASE WHEN SUBSTRING(f.competencia,1,4) = SUBSTRING(fim,1,4)
                    AND f.competencia <= fim
                   THEN f.salario_bruto + f.bonus + f.fgts + f.vr + f.vt ELSE 0 END), 2)::numeric
  FROM folha_pagamento f
  JOIN funcionarios func ON func.id = f.funcionario_id
  WHERE SUBSTRING(f.competencia,1,4) = SUBSTRING(fim,1,4)
  GROUP BY func.nome, func.tipo
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
    SELECT func.nome AS item, SUM(f.salario_bruto + f.bonus + f.fgts + f.vr + f.vt) AS valor
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

DROP FUNCTION IF EXISTS fn_folha_lancamentos(text);

CREATE OR REPLACE FUNCTION fn_folha_lancamentos(comp text)
RETURNS TABLE(
  func_id        uuid,
  "Funcionário"  text,
  tipo_raw       text,
  "Tipo"         text,
  "Salário Bruto" numeric,
  "Bônus"        numeric,
  "FGTS"         numeric,
  "INSS Retido"  numeric,
  "VR"           numeric,
  "VT"           numeric
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
    COALESCE(fp.inss_retido,   0)::numeric,
    COALESCE(fp.vr,            0)::numeric,
    COALESCE(fp.vt,            0)::numeric
  FROM funcionarios fu
  LEFT JOIN folha_pagamento fp ON fp.funcionario_id = fu.id AND fp.competencia = comp
  WHERE fu.ativo = true
  ORDER BY fu.nome;
$$;


-- ─────────────────────────────────────────────────────────────────
-- fn_upsert_folha: nova assinatura com p_vr, p_vt
-- (assinatura muda → precisa dropar a versão antiga)
-- ─────────────────────────────────────────────────────────────────

DROP FUNCTION IF EXISTS fn_upsert_folha(uuid, text, numeric, numeric, numeric, numeric);

CREATE OR REPLACE FUNCTION fn_upsert_folha(
  p_funcionario_id  uuid,
  p_competencia     text,
  p_salario_bruto   numeric,
  p_bonus           numeric,
  p_fgts            numeric,
  p_inss_retido     numeric,
  p_vr              numeric,
  p_vt              numeric
) RETURNS void LANGUAGE sql VOLATILE SECURITY DEFINER AS $$
  INSERT INTO folha_pagamento
    (funcionario_id, competencia, salario_bruto, bonus, fgts, inss_retido, vr, vt)
  VALUES
    (p_funcionario_id, p_competencia, p_salario_bruto, p_bonus, p_fgts, p_inss_retido, p_vr, p_vt)
  ON CONFLICT (funcionario_id, competencia) DO UPDATE SET
    salario_bruto = EXCLUDED.salario_bruto,
    bonus         = EXCLUDED.bonus,
    fgts          = EXCLUDED.fgts,
    inss_retido   = EXCLUDED.inss_retido,
    vr            = EXCLUDED.vr,
    vt            = EXCLUDED.vt,
    atualizado_em = NOW();
$$;

GRANT EXECUTE ON FUNCTION fn_dre_detalhe_folha(text,text)                          TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_top5_custos(text,text)                                TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_folha_lancamentos(text)                               TO anon, authenticated;
GRANT EXECUTE ON FUNCTION fn_upsert_folha(uuid,text,numeric,numeric,numeric,numeric,numeric,numeric) TO anon, authenticated;

-- Recarrega schema cache do PostgREST
NOTIFY pgrst, 'reload schema';
