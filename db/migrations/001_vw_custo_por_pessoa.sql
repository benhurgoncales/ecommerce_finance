-- View: vw_custo_por_pessoa
-- Custo total por funcionário no mês + percentual sobre total de despesas
-- Usada na Página 4 do Dashboard (Custos e Despesas → Gráfico por pessoa)

CREATE OR REPLACE VIEW vw_custo_por_pessoa AS
SELECT
    f.competencia,
    func.nome,
    func.tipo,
    f.salario_bruto + f.bonus + f.fgts                        AS custo_total,
    ROUND(
        (f.salario_bruto + f.bonus + f.fgts)
        / NULLIF(d.total_despesas, 0) * 100, 1
    )                                                          AS pct_total_despesas
FROM folha_pagamento f
JOIN funcionarios func ON func.id = f.funcionario_id
JOIN dre_consolidada d  ON d.competencia = f.competencia;

COMMENT ON VIEW vw_custo_por_pessoa IS 'Custo real por funcionário no mês com percentual sobre o total de despesas';
