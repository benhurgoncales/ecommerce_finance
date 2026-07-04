# Ecommerce Financeiro — Dashboard de Controle Financeiro

Dashboard financeiro para fechamento mensal, conectado ao PostgreSQL (Supabase) e construído com Streamlit.

---

## Estrutura do projeto

```
ecommerce-financeiro/
├── dashboard/                        # Dashboard Streamlit (4 páginas)
│   ├── Home.py                       # Página inicial
│   ├── pages/
│   │   ├── 1_Visao_Geral.py          # Métricas + gráficos de faturamento e lucro
│   │   ├── 2_Canais.py               # Performance por canal/plataforma
│   │   ├── 3_DRE_Completa.py         # DRE com abas Geral e Detalhada
│   │   └── 4_Custos_e_Despesas.py    # Análise de custos, top 5 e evolução
│   └── utils/
│       ├── database.py               # Conexão e cache de queries
│       ├── queries.py                # Todas as queries SQL
│       ├── filters.py                # Filtro de período (sidebar)
│       ├── formatting.py             # Formatação BRL, datas, percentuais
│       └── styles.py                 # CSS, paleta de cores, componentes
├── db/
│   ├── schema.sql                    # Schema completo do banco
│   ├── etl_carga_historico.py        # ETL de carga da planilha Excel
│   └── migrations/
│       └── 001_vw_custo_por_pessoa.sql
├── docs/
│   └── DRE_ECOMMERCE_OFICIAL.xlsx    # Planilha fonte dos dados históricos
├── .streamlit/
│   └── config.toml                   # Tema claro do Streamlit
├── requirements.txt
└── .env                              # Credenciais (não versionar)
```

---

## Configuração

### 1. Crie o arquivo `.env`

```env
SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_KEY=<sua-chave>
DATABASE_URL=postgresql://postgres:<senha>@db.<project-id>.supabase.co:6543/postgres?sslmode=require
```

> Use porta `6543` (pooler) — a 5432 pode estar bloqueada.

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure o banco de dados

Cole o conteúdo de `db/schema.sql` no SQL Editor do Supabase, depois aplique a migration `db/migrations/001_vw_custo_por_pessoa.sql`.

### 4. Carregue os dados históricos

```bash
python db/etl_carga_historico.py
```

### 5. Rode o dashboard

```bash
streamlit run dashboard/Home.py
```

Acesse: **http://localhost:8501**

---

## Páginas do dashboard

| Página | Objetivo |
|---|---|
| Visão Geral | Faturamento, lucro, margem e composição de despesas |
| Canais e Plataformas | Performance por canal com tabela e gráficos |
| DRE Completa | DRE vertical (Geral e Detalhada por funcionário/item) |
| Custos e Despesas | Top 5 custos, evolução mensal e tabela detalhada |

**Filtro global:** Período De → Até no sidebar — afeta todas as páginas.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Banco de dados | PostgreSQL via Supabase |
| Dashboard | Streamlit + Plotly |
| ETL | Python (pandas + openpyxl) |
| Conexão | SQLAlchemy + psycopg2 |
