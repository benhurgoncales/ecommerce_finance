-- ============================================================
-- PROJETO: Sistema Financeiro E-commerce
-- Banco:   PostgreSQL (Supabase)
-- ============================================================

-- ── Extensão para UUID ───────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. CANAIS
-- Cadastro dos canais de venda
-- ============================================================
CREATE TABLE canais (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome        VARCHAR(100) NOT NULL UNIQUE,
    tipo        VARCHAR(50)  NOT NULL
                    CHECK (tipo IN ('marketplace', 'proprio', 'social')),
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE,
    criado_em   TIMESTAMP    NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  canais       IS 'Cadastro dos canais de venda da empresa';
COMMENT ON COLUMN canais.tipo  IS 'marketplace = ML/Shopee/Shein | proprio = Site/WhatsApp | social = TikTok';

-- Dados iniciais
INSERT INTO canais (nome, tipo) VALUES
    ('Mercado Livre', 'marketplace'),
    ('Shopee',        'marketplace'),
    ('Shein',         'marketplace'),
    ('TikTok',        'social'),
    ('Bazar',         'proprio'),
    ('Site',          'proprio'),
    ('WhatsApp',      'proprio');


-- ============================================================
-- 2. RECEITAS
-- Lançamento mensal por canal — espelha o INPUT_PLATAFORMAS
-- ============================================================
CREATE TABLE receitas (
    id              UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    canal_id        UUID         NOT NULL REFERENCES canais(id),
    competencia     CHAR(7)      NOT NULL,   -- formato: "2025-01"
    receita_bruta   NUMERIC(12,2) NOT NULL DEFAULT 0,
    imposto         NUMERIC(12,2) NOT NULL DEFAULT 0,
    custo_produto   NUMERIC(12,2) NOT NULL DEFAULT 0,
    frete           NUMERIC(12,2) NOT NULL DEFAULT 0,
    tarifa          NUMERIC(12,2) NOT NULL DEFAULT 0,
    desconto_cupom  NUMERIC(12,2) NOT NULL DEFAULT 0,
    afiliado        NUMERIC(12,2) NOT NULL DEFAULT 0,
    outros_cmv      NUMERIC(12,2) NOT NULL DEFAULT 0,
    ads             NUMERIC(12,2) NOT NULL DEFAULT 0,
    criado_em       TIMESTAMP    NOT NULL DEFAULT NOW(),
    atualizado_em   TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT receitas_canal_mes_unique UNIQUE (canal_id, competencia),
    CONSTRAINT competencia_formato CHECK (competencia ~ '^\d{4}-(0[1-9]|1[0-2])$')
);

COMMENT ON TABLE  receitas             IS 'Receitas e custos variáveis por canal por mês';
COMMENT ON COLUMN receitas.competencia IS 'Mês de referência no formato YYYY-MM';
COMMENT ON COLUMN receitas.imposto     IS 'DAS / imposto sobre receita deduzido da receita bruta';
COMMENT ON COLUMN receitas.ads         IS 'Investimento em anúncios dentro da plataforma';

-- Colunas calculadas (views, não armazenadas)
-- receita_liquida  = receita_bruta - imposto
-- cmv_total        = custo_produto + frete + tarifa + desconto_cupom + afiliado + outros_cmv
-- lucro_bruto      = receita_liquida - cmv_total
-- margem_liquida   = lucro_bruto - ads


-- ============================================================
-- 3. CATEGORIAS DE DESPESA
-- Cadastro fixo das categorias
-- ============================================================
CREATE TABLE categorias_despesa (
    id      SERIAL      PRIMARY KEY,
    nome    VARCHAR(100) NOT NULL UNIQUE,
    ordem   SMALLINT     NOT NULL DEFAULT 0  -- ordem de exibição na DRE
);

COMMENT ON TABLE categorias_despesa IS 'Categorias de despesa para classificação na DRE';

INSERT INTO categorias_despesa (nome, ordem) VALUES
    ('Folha',                     1),
    ('Administrativo',            2),
    ('Marketing',                 3),
    ('Despesas Financeiras',      4),
    ('Tecnologia e Ferramentas',  5),
    ('Educação e Capacitação',    6);


-- ============================================================
-- 4. FUNCIONÁRIOS
-- Cadastro da equipe
-- ============================================================
CREATE TABLE funcionarios (
    id           UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    nome         VARCHAR(100) NOT NULL,
    tipo         VARCHAR(20)  NOT NULL
                     CHECK (tipo IN ('pro_labore', 'autonomo', 'clt')),
    ativo        BOOLEAN     NOT NULL DEFAULT TRUE,
    data_entrada DATE,
    criado_em    TIMESTAMP   NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  funcionarios      IS 'Cadastro dos membros da equipe';
COMMENT ON COLUMN funcionarios.tipo IS 'pro_labore = sócio | autonomo = sem registro | clt = registrado';

INSERT INTO funcionarios (nome, tipo, data_entrada) VALUES
    ('Ben-Hur', 'pro_labore', NULL),
    ('Camila',  'autonomo',   NULL),
    ('Jackson', 'clt',        NULL),
    ('Laura',   'clt',        NULL);


-- ============================================================
-- 5. FOLHA DE PAGAMENTO
-- Detalhe mensal por funcionário
-- ============================================================
CREATE TABLE folha_pagamento (
    id              UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    funcionario_id  UUID         NOT NULL REFERENCES funcionarios(id),
    competencia     CHAR(7)      NOT NULL,
    salario_bruto   NUMERIC(10,2) NOT NULL DEFAULT 0,
    bonus           NUMERIC(10,2) NOT NULL DEFAULT 0,
    fgts            NUMERIC(10,2) NOT NULL DEFAULT 0,  -- informado manualmente
    inss_retido     NUMERIC(10,2) NOT NULL DEFAULT 0,  -- informativo
    vr              NUMERIC(10,2) NOT NULL DEFAULT 0,  -- vale refeição
    vt              NUMERIC(10,2) NOT NULL DEFAULT 0,  -- vale transporte
    criado_em       TIMESTAMP    NOT NULL DEFAULT NOW(),
    atualizado_em   TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT folha_funcionario_mes_unique UNIQUE (funcionario_id, competencia),
    CONSTRAINT competencia_formato CHECK (competencia ~ '^\d{4}-(0[1-9]|1[0-2])$')
);

COMMENT ON TABLE  folha_pagamento            IS 'Lançamento mensal de remuneração por funcionário';
COMMENT ON COLUMN folha_pagamento.fgts       IS 'Valor informado manualmente pelo usuário';
COMMENT ON COLUMN folha_pagamento.inss_retido IS 'Valor retido do funcionário — informativo, não duplicar no custo';
COMMENT ON COLUMN folha_pagamento.vr         IS 'Vale Refeição — benefício, sem incidência de FGTS/INSS';
COMMENT ON COLUMN folha_pagamento.vt         IS 'Vale Transporte — benefício, sem incidência de FGTS/INSS';

-- Coluna calculada:
-- total_custo = salario_bruto + bonus + fgts + vr + vt  (INSS retido não soma — já está no bruto)


-- ============================================================
-- 6. DESPESAS
-- Lançamento mensal por categoria
-- ============================================================
CREATE TABLE despesas (
    id            UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    categoria_id  INTEGER      NOT NULL REFERENCES categorias_despesa(id),
    competencia   CHAR(7)      NOT NULL,
    descricao     VARCHAR(200) NOT NULL,
    tipo          VARCHAR(20)  NOT NULL DEFAULT 'fixo'
                      CHECK (tipo IN ('fixo', 'variavel', 'eventual')),
    valor         NUMERIC(12,2) NOT NULL DEFAULT 0,
    observacao    TEXT,
    criado_em     TIMESTAMP    NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT competencia_formato CHECK (competencia ~ '^\d{4}-(0[1-9]|1[0-2])$')
);

COMMENT ON TABLE  despesas            IS 'Despesas operacionais mensais por categoria';
COMMENT ON COLUMN despesas.tipo       IS 'fixo = recorrente | variavel = oscila com volume | eventual = pontual';
COMMENT ON COLUMN despesas.observacao IS 'Campo livre para anotações';

CREATE INDEX idx_despesas_competencia   ON despesas(competencia);
CREATE INDEX idx_despesas_categoria     ON despesas(categoria_id);


-- ============================================================
-- 7. METAS
-- Projeções mensais por canal
-- ============================================================
CREATE TABLE metas (
    id             UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    canal_id       UUID         NOT NULL REFERENCES canais(id),
    competencia    CHAR(7)      NOT NULL,
    meta_receita   NUMERIC(12,2) NOT NULL DEFAULT 0,
    meta_margem    NUMERIC(12,2) NOT NULL DEFAULT 0,
    criado_em      TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT metas_canal_mes_unique UNIQUE (canal_id, competencia),
    CONSTRAINT competencia_formato CHECK (competencia ~ '^\d{4}-(0[1-9]|1[0-2])$')
);

COMMENT ON TABLE metas IS 'Metas mensais de receita e margem por canal';


-- ============================================================
-- 8. DRE CONSOLIDADA
-- Gerada pelo ETL — não editar manualmente
-- ============================================================
CREATE TABLE dre_consolidada (
    id                  UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    competencia         CHAR(7)      NOT NULL UNIQUE,

    -- Receita
    receita_bruta       NUMERIC(14,2) NOT NULL DEFAULT 0,
    impostos            NUMERIC(14,2) NOT NULL DEFAULT 0,
    receita_liquida     NUMERIC(14,2) NOT NULL DEFAULT 0,

    -- CMV
    cmv_total           NUMERIC(14,2) NOT NULL DEFAULT 0,
    lucro_bruto         NUMERIC(14,2) NOT NULL DEFAULT 0,
    margem_bruta_pct    NUMERIC(6,4)  NOT NULL DEFAULT 0,  -- ex: 0.1523 = 15.23%

    -- Despesas por categoria
    desp_folha          NUMERIC(14,2) NOT NULL DEFAULT 0,
    desp_administrativo NUMERIC(14,2) NOT NULL DEFAULT 0,
    desp_marketing      NUMERIC(14,2) NOT NULL DEFAULT 0,
    desp_financeiras    NUMERIC(14,2) NOT NULL DEFAULT 0,
    desp_tecnologia     NUMERIC(14,2) NOT NULL DEFAULT 0,
    desp_educacao       NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_despesas      NUMERIC(14,2) NOT NULL DEFAULT 0,

    -- Resultado
    ebitda              NUMERIC(14,2) NOT NULL DEFAULT 0,
    ebitda_pct          NUMERIC(6,4)  NOT NULL DEFAULT 0,
    lucro_liquido       NUMERIC(14,2) NOT NULL DEFAULT 0,
    margem_liquida_pct  NUMERIC(6,4)  NOT NULL DEFAULT 0,

    gerado_em           TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT competencia_formato CHECK (competencia ~ '^\d{4}-(0[1-9]|1[0-2])$')
);

COMMENT ON TABLE  dre_consolidada          IS 'DRE mensal consolidada — gerada automaticamente pelo ETL';
COMMENT ON COLUMN dre_consolidada.gerado_em IS 'Timestamp da última execução do ETL';


-- ============================================================
-- 9. VIEWS ÚTEIS
-- ============================================================

-- Receita por canal com colunas calculadas
CREATE OR REPLACE VIEW vw_receitas_calculadas AS
SELECT
    r.competencia,
    c.nome                                              AS canal,
    c.tipo                                              AS tipo_canal,
    r.receita_bruta,
    r.imposto,
    r.receita_bruta - r.imposto                         AS receita_liquida,
    r.custo_produto + r.frete + r.tarifa
        + r.desconto_cupom + r.afiliado + r.outros_cmv  AS cmv_total,
    (r.receita_bruta - r.imposto)
        - (r.custo_produto + r.frete + r.tarifa
           + r.desconto_cupom + r.afiliado + r.outros_cmv) AS lucro_bruto,
    (r.receita_bruta - r.imposto)
        - (r.custo_produto + r.frete + r.tarifa
           + r.desconto_cupom + r.afiliado + r.outros_cmv)
        - r.ads                                          AS margem_liquida,
    CASE WHEN r.receita_bruta > 0
         THEN ROUND(
             ((r.receita_bruta - r.imposto)
              - (r.custo_produto + r.frete + r.tarifa
                 + r.desconto_cupom + r.afiliado + r.outros_cmv)
              - r.ads) / r.receita_bruta * 100, 2)
         ELSE 0 END                                      AS margem_liquida_pct,
    r.ads
FROM receitas r
JOIN canais c ON c.id = r.canal_id;

COMMENT ON VIEW vw_receitas_calculadas IS 'Receitas com margens calculadas por canal e mês';


-- Folha com custo total por funcionário
CREATE OR REPLACE VIEW vw_folha_calculada AS
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


-- Despesas por categoria e mês
CREATE OR REPLACE VIEW vw_despesas_por_categoria AS
SELECT
    d.competencia,
    cd.nome     AS categoria,
    cd.ordem,
    SUM(d.valor) AS total
FROM despesas d
JOIN categorias_despesa cd ON cd.id = d.categoria_id
GROUP BY d.competencia, cd.nome, cd.ordem
ORDER BY d.competencia, cd.ordem;

COMMENT ON VIEW vw_despesas_por_categoria IS 'Total de despesas agrupado por categoria e mês';


-- ============================================================
-- 10. FUNÇÃO: Recalcular DRE consolidada de um mês
-- Chamada pelo ETL após cada carga de dados
-- ============================================================
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

    -- Folha de pagamento
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
