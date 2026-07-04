import streamlit as st

# ── Paleta ────────────────────────────────────────────────────────────────
C = {
    "blue":   "#2563EB",
    "green":  "#059669",
    "red":    "#DC2626",
    "amber":  "#D97706",
    "purple": "#7C3AED",
    "slate":  "#64748B",
    "bg":     "#F8FAFC",
    "white":  "#FFFFFF",
    "dark":   "#1E293B",
    "border": "#E2E8F0",
}

DESP_CORES = {
    "Folha":             "#E11D48",
    "Administrativo":    "#EA580C",
    "Marketing":         "#D97706",
    "Desp. Financeiras": "#7C3AED",
    "Tecnologia":        "#2563EB",
    "Educação":          "#059669",
}

CANAL_CORES = ["#2563EB","#059669","#D97706","#7C3AED","#E11D48","#EA580C","#0891B2"]


def chart_layout(
    height: int = 360,
    showlegend: bool = True,
    xaxis: dict | None = None,
    yaxis: dict | None = None,
    margin: dict | None = None,
    **kwargs,
) -> dict:
    """Retorna um dict de layout Plotly sem conflito de chaves."""
    layout = dict(
        paper_bgcolor="white",
        plot_bgcolor="#F8FAFC",
        font=dict(family="system-ui,-apple-system,sans-serif", color="#1E293B", size=12),
        margin={**dict(l=8, r=8, t=48, b=8), **(margin or {})},
        hoverlabel=dict(bgcolor="white", bordercolor="#E2E8F0", font_size=12),
        height=height,
        showlegend=showlegend,
        xaxis={
            "showgrid": False,
            "linecolor": "#E2E8F0",
            "tickfont": dict(size=11, color="#64748B"),
            **(xaxis or {}),
        },
        yaxis={
            "gridcolor": "#E2E8F0",
            "linecolor": "#E2E8F0",
            "tickfont": dict(size=11, color="#64748B"),
            **(yaxis or {}),
        },
    )
    if showlegend:
        layout["legend"] = dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#E2E8F0", borderwidth=1,
            font=dict(size=11),
        )
    layout.update(kwargs)
    return layout


def load_css():
    st.markdown("""
    <style>
    /* ── Base ──────────────────────────────────────────────── */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px;
    }

    /* ── Sidebar: tema branco ───────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding: 1.5rem 1.2rem;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #1E293B !important;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #64748B !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #E2E8F0 !important;
        margin: 0.8rem 0 !important;
    }

    /* ── KPI Cards ──────────────────────────────────────────── */
    .kpi-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 20px 22px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        border-left: 4px solid var(--accent, #2563EB);
        transition: box-shadow .15s;
    }
    .kpi-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.09); }
    .kpi-icon  { font-size: 18px; margin-bottom: 4px; }
    .kpi-label {
        color: #64748B; font-size: 11px; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.07em; margin: 0 0 6px 0;
    }
    .kpi-value {
        color: #1E293B; font-size: 26px; font-weight: 700;
        letter-spacing: -0.02em; margin: 0; line-height: 1.15;
    }
    .kpi-sub { color: #64748B; font-size: 12px; margin: 4px 0 0 0; }

    /* ── Period Badge ────────────────────────────────────────── */
    .period-badge {
        display: inline-block;
        background: #EFF6FF; color: #2563EB;
        padding: 4px 14px; border-radius: 20px;
        font-size: 13px; font-weight: 600;
        border: 1px solid #BFDBFE;
        white-space: nowrap;
    }

    /* ── Section Title ───────────────────────────────────────── */
    .section-title {
        font-size: 14px; font-weight: 700; color: #475569;
        text-transform: uppercase; letter-spacing: 0.06em;
        margin: 0 0 10px 0; padding-bottom: 6px;
        border-bottom: 2px solid #E2E8F0;
    }

    /* ── Divider ─────────────────────────────────────────────── */
    hr { border-color: #E2E8F0 !important; margin: 1rem 0 !important; }

    /* ── DataFrame ───────────────────────────────────────────── */
    .stDataFrame [data-testid="stDataFrameResizable"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)


def sidebar_logo():
    st.sidebar.markdown(
        '<h2 style="margin:0 0 4px;font-size:17px;font-weight:700;color:#1E293B">'
        '📊 Financeiro E-commerce</h2>'
        '<p style="margin:0;font-size:12px;color:#94A3B8">Dashboard de fechamento mensal</p>',
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, accent: str = "#2563EB",
             icon: str = "", sub: str = "") -> str:
    sub_html = f'<p class="kpi-sub">{sub}</p>' if sub else ""
    return (
        f'<div class="kpi-card" style="--accent:{accent}">'
        f'<div class="kpi-icon">{icon}</div>'
        f'<p class="kpi-label">{label}</p>'
        f'<p class="kpi-value">{value}</p>'
        f'{sub_html}</div>'
    )


def page_header(title: str, period: str, subtitle: str = ""):
    sub_html = (
        f'<p style="color:#64748B;margin:4px 0 0 0;font-size:13px">{subtitle}</p>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="display:flex;align-items:flex-start;'
        f'justify-content:space-between;margin-bottom:22px">'
        f'<div><h1 style="margin:0;font-size:22px;font-weight:700;color:#1E293B">{title}</h1>'
        f'{sub_html}</div>'
        f'<span class="period-badge">{period}</span></div>',
        unsafe_allow_html=True,
    )


def section(title: str):
    st.markdown(f'<p class="section-title">{title}</p>', unsafe_allow_html=True)
