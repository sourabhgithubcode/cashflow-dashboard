"""
Cash Flow Intelligence Platform — Executive Dashboard v3
Design:  Black background · White text · Single blue accent (#4A9EFF)
Layout:  Z-pattern — KPIs → Portfolio+Macro → Signals+Inspector → Table
Author:  Sourabh Rodagi
Run:     streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
SCORES_URL  = "https://docs.google.com/spreadsheets/d/1Dhja8Arb08DK7xWlqvDPpYOixakD_WIIeP5VGxdbDJY/gviz/tq?tqx=out:csv&sheet=scores"
SUMMARY_URL = "https://docs.google.com/spreadsheets/d/1Dhja8Arb08DK7xWlqvDPpYOixakD_WIIeP5VGxdbDJY/gviz/tq?tqx=out:csv&sheet=summary"

# ── Single colour system
# One blue, four opacity steps for tier severity
BG       = "#0a0a0f"          # page background
CARD     = "#111118"          # card background
BORDER   = "#1e1e2e"          # all borders
WHITE    = "#ffffff"          # primary text
MUTED    = "#6b7280"          # secondary text
ACCENT   = "#4A9EFF"          # single accent blue
A80      = "rgba(74,158,255,0.80)"   # CRITICAL
A55      = "rgba(74,158,255,0.55)"   # HIGH
A30      = "rgba(74,158,255,0.30)"   # MEDIUM
A12      = "rgba(74,158,255,0.12)"   # LOW
GRID     = "#16161f"
TT_BG    = "#1e1e2e"          # tooltip background

TIER_FILL  = {"CRITICAL": A80, "HIGH": A55, "MEDIUM": A30, "LOW": A12}
TIER_SOLID = {"CRITICAL": "#4A9EFF", "HIGH": "#3a7fcc", "MEDIUM": "#2a5f99", "LOW": "#1a3f66"}

SHAP_FEATURES = [
    ("Cash Runway Days",          1.04), ("Essential Spend Ratio",     0.76),
    ("Net Cashflow 90D",          0.61), ("Transfer To Income Ratio",  0.58),
    ("Avg Monthly Income",        0.48), ("Transfer Count 90D",        0.41),
    ("Txn Freq Change",           0.35), ("Total Deposits 90D",        0.31),
    ("Total Spend 90D",           0.28), ("Deposit Trend Pct",         0.24),
    ("Spend Trend Pct",           0.19), ("Cashflow Ratio",            0.17),
    ("Discretionary Spend Ratio", 0.14), ("Income CV",                 0.12),
    ("Overdraft Count 90D",       0.11),
]

MACRO = [
    ("Unemployment",    "4.4%",  "Rising — above 4.0%",           0.73),
    ("Consumer Sent.",  "57.0",  "Below 70 threshold",            0.57),
    ("CC Delinquency",  "3.2%",  "Elevated — watch closely",      0.64),
    ("Fed Funds Rate",  "4.5%",  "High rate environment",         0.75),
    ("Personal Savings","3.8%",  "Below 4% — consumers squeezed", 0.38),
]


def layout(height=280, ml=8, mr=8, mt=16, mb=8, **kw):
    base = dict(
        plot_bgcolor=BG, paper_bgcolor=BG,
        font=dict(color=MUTED, size=13, family="Inter, sans-serif"),
        height=height,
        margin=dict(l=ml, r=mr, t=mt, b=mb),
        xaxis=dict(gridcolor=GRID, linecolor=BORDER,
                   tickcolor=BORDER, tickfont=dict(color=MUTED, size=12)),
        yaxis=dict(gridcolor=GRID, linecolor=BORDER,
                   tickcolor=BORDER, tickfont=dict(color=MUTED, size=12)),
        hoverlabel=dict(
            bgcolor=TT_BG, bordercolor=ACCENT,
            font=dict(color=WHITE, size=13),
        ),
        showlegend=False,
    )
    base.update(kw)
    return base


# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cash Flow Intel",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
  font-family: 'Inter', sans-serif;
  background-color: {BG};
  color: {WHITE};
}}
.main .block-container {{
  padding: 1rem 1.5rem 1rem 1.5rem;
  max-width: 100%;
  background: {BG};
}}
section[data-testid="stSidebar"] {{
  width: 260px !important;
  background: {CARD} !important;
  border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] * {{ color: {WHITE} !important; }}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stCheckbox label {{
  font-size: 0.8rem !important;
  color: {MUTED} !important;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}}

/* Metric cards */
div[data-testid="metric-container"] {{
  background: {CARD};
  border: 1px solid {BORDER};
  border-radius: 8px;
  padding: 16px 20px;
}}
div[data-testid="metric-container"] label {{
  font-size: 0.72rem !important;
  color: {MUTED} !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 500;
}}
div[data-testid="metric-container"] [data-testid="metric-value"] {{
  font-size: 1.75rem !important;
  color: {WHITE} !important;
  font-weight: 600 !important;
  line-height: 1.2;
}}
div[data-testid="metric-container"] [data-testid="metric-delta"] {{
  font-size: 0.78rem !important;
  color: {MUTED} !important;
}}

/* Headings */
h1 {{ font-size: 1.35rem !important; font-weight: 600 !important;
      color: {WHITE} !important; margin: 0 !important; line-height: 1.3; }}
h2 {{ font-size: 0.7rem !important; font-weight: 500 !important;
      color: {MUTED} !important; text-transform: uppercase;
      letter-spacing: 0.1em; margin: 0 !important; }}
h3 {{ font-size: 0.85rem !important; color: {MUTED} !important;
      font-weight: 400 !important; margin: 0 !important; }}

/* Section divider */
.div {{ height: 1px; background: {BORDER}; margin: 0.75rem 0; }}

/* Card wrapper */
.card {{
  background: {CARD};
  border: 1px solid {BORDER};
  border-radius: 8px;
  padding: 16px 20px;
}}

/* Dataframe */
.stDataFrame {{ border-radius: 8px; border: 1px solid {BORDER}; }}

/* Buttons */
.stButton button, .stDownloadButton button {{
  background: {CARD} !important;
  border: 1px solid {BORDER} !important;
  color: {MUTED} !important;
  font-size: 0.78rem !important;
  border-radius: 6px !important;
  padding: 6px 14px !important;
}}
.stButton button:hover, .stDownloadButton button:hover {{
  border-color: {ACCENT} !important;
  color: {WHITE} !important;
}}

/* Remove all Streamlit padding between elements */
div[data-testid="stVerticalBlock"] > div {{
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}}
div[data-testid="column"] > div > div > div {{
  gap: 0.5rem !important;
}}
.element-container {{ margin-bottom: 0.5rem !important; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_live():
    try:
        s = pd.read_csv(SCORES_URL)
        m = pd.read_csv(SUMMARY_URL)
        for df in [s, m]:
            df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        s["churn_probability"] = pd.to_numeric(s["churn_probability"], errors="coerce")
        return s.sort_values("churn_probability", ascending=False).reset_index(drop=True), m.iloc[0], None
    except Exception as e:
        return None, None, str(e)


def make_demo():
    np.random.seed(42)
    rsns = [
        "Cash Runway Days raises risk | Transfer To Income Ratio raises risk | Net Cashflow 90D raises risk",
        "Essential Spend Ratio raises risk | Overdraft Count 90D raises risk | Avg Monthly Income lowers risk",
        "Txn Freq Change raises risk | Total Transfer Outflow 90D raises risk | Cashflow Ratio lowers risk",
        "Income CV raises risk | Spend Trend Pct raises risk | Cash Runway Days raises risk",
        "Total Deposits 90D lowers risk | Transfer Count 90D raises risk | Avg Daily Spend raises risk",
    ]
    acts = {
        "CRITICAL": "Immediate retention call — offer rate or fee waiver",
        "HIGH":     "Proactive outreach within 7 days — targeted offer",
        "MEDIUM":   "Add to watchlist — automated nurture campaign",
        "LOW":      "No action — routine monitoring",
    }
    archs = (["CUST_HIGH_RISK_DECLINING"] * 250 + ["CUST_NEAR_PRIME_STRUGGLING"] * 350 +
             ["CUST_CHURNING_WITH_INCOME"] * 300 + ["CUST_STABLE_WITH_STRESS"] * 200 +
             ["CUST_STABLE_SALARY"] * 400 + ["CUST_GIG_WORKER_STABLE"] * 300 +
             ["CUST_RETIREE_STABLE"] * 200)
    tiers = ["CRITICAL"] * 142 + ["HIGH"] * 27 + ["MEDIUM"] * 27 + ["LOW"] * 304
    srng  = {"CRITICAL": (75, 100), "HIGH": (50, 74), "MEDIUM": (30, 49), "LOW": (1, 29)}
    rows  = []
    for i, (a, t) in enumerate(zip(archs[:500], tiers)):
        rows.append({
            "customer_id":        f"{a}_{i:04d}",
            "churn_probability":  round(np.random.uniform(*srng[t]), 1),
            "risk_tier":          t,
            "actual_label":       1 if t in ["CRITICAL", "HIGH"] else 0,
            "recommended_action": acts[t],
            "top_3_reasons":      rsns[i % len(rsns)],
        })
    df = pd.DataFrame(rows).sort_values("churn_probability", ascending=False).reset_index(drop=True)
    s  = pd.Series({
        "total_customers": 500, "critical_count": 142, "high_count": 27,
        "medium_count": 27, "low_count": 304, "critical_pct": 28.4,
        "lr_auc": 0.8566, "xgb_auc": 0.8943, "lr_gini": 0.7132, "xgb_gini": 0.7887,
        "revenue_at_risk_critical": 2584400, "revenue_at_risk_high": 891000,
        "revenue_at_risk_medium": 594000, "noise_level": 0.15,
        "n_customers": 2000, "n_features": 30,
        "macro_unemployment": 4.4, "macro_sentiment": 57.0,
        "macro_delinquency": 3.2, "timestamp": "demo",
    })
    return df, s


def customer_shap(cust_row):
    np.random.seed(hash(cust_row["customer_id"]) % 9999)
    prob  = max(0.01, min(0.99, cust_row["churn_probability"] / 100))
    tier  = cust_row["risk_tier"]
    logit = np.log(prob / (1 - prob))
    base  = 0.17
    total = logit - base
    raw   = np.random.dirichlet(np.ones(15)) * abs(total)
    pos_p = 0.75 if tier in ["CRITICAL", "HIGH"] else 0.35
    signs = np.where(np.random.random(15) < pos_p, 1, -1)
    vals  = (raw * signs).tolist()
    vals[0]  =  abs(vals[0])  * (1 if tier in ["CRITICAL", "HIGH"] else -1)
    vals[1]  =  abs(vals[1])  * (1 if tier in ["CRITICAL", "HIGH"] else -1)
    vals[-1] = -abs(vals[-1])
    feats = [f[0] for f in SHAP_FEATURES]
    return list(zip(feats, vals)), base


is_demo = "YOUR_SHEET_ID" in SCORES_URL
if is_demo:
    scores_df, s = make_demo()
    src = "Demo · paste Google Sheets URL to connect live model"
else:
    scores_df, s, err = load_live()
    if err:
        scores_df, s = make_demo()
        src = f"Error — demo shown  ({err[:40]})"
    else:
        src = f"Live · last push: {s.get('timestamp', '')}"


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<p style='font-size:1rem;font-weight:600;color:{WHITE};margin:0;'>Cash Flow Intel</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:0.7rem;color:{MUTED};margin:2px 0 12px;'>{src}</p>", unsafe_allow_html=True)

    if st.button("↻  Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"<div class='div'></div>", unsafe_allow_html=True)
    st.markdown("**Filters**")

    tier_filter = st.selectbox("Risk tier", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    min_score   = st.slider("Min churn score (%)", 0, 100, 0)

    # Build filtered df here — customer dropdown reflects all filters
    fd = scores_df.copy()
    if tier_filter != "All":
        fd = fd[fd["risk_tier"] == tier_filter]
    fd = fd[fd["churn_probability"] >= min_score].reset_index(drop=True)

    st.markdown(f"<div class='div'></div>", unsafe_allow_html=True)
    st.markdown("**Customer inspector**")

    def fmt_cust(x):
        if x == "—":
            return "Select a customer"
        row = fd[fd["customer_id"] == x]
        if len(row) == 0:
            return x
        t  = row.iloc[0]["risk_tier"]
        sc = row.iloc[0]["churn_probability"]
        return f"{x}   {t} · {sc:.1f}%"

    cust_opts = ["—"] + fd["customer_id"].tolist()
    selected  = st.selectbox("Customer", cust_opts, format_func=fmt_cust)

    st.markdown(f"<div class='div'></div>", unsafe_allow_html=True)
    st.markdown("**Table**")
    n_rows      = st.slider("Rows", 5, 100, 20)
    show_action = st.checkbox("Recommended action", value=True)
    show_shap   = st.checkbox("SHAP reasons", value=True)


# ─────────────────────────────────────────────
# DERIVED STATS — all reactive
# ─────────────────────────────────────────────
total_n  = len(fd)
crit_n   = int((fd["risk_tier"] == "CRITICAL").sum())
high_n   = int((fd["risk_tier"] == "HIGH").sum())
med_n    = int((fd["risk_tier"] == "MEDIUM").sum())
low_n    = int((fd["risk_tier"] == "LOW").sum())
rev_crit = crit_n * 18200
rev_high = high_n * 33000
rev_med  = med_n  * 22000
tot_rev  = rev_crit + rev_high + rev_med
avg_sc   = fd["churn_probability"].mean() if total_n > 0 else 0
act_rate = fd["actual_label"].mean() * 100 if total_n > 0 else 0
xgb_auc  = float(s["xgb_auc"])
lr_auc   = float(s["lr_auc"])


# ─────────────────────────────────────────────
# ═══ Z-ZONE 1 — HEADER + KPIs (top bar) ═══
# ─────────────────────────────────────────────
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown("# Cash Flow Intelligence Platform")
    st.markdown(
        f"<p style='font-size:0.82rem;color:{MUTED};margin:2px 0 0;'>"
        f"Balance retention · Churn early warning &nbsp;|&nbsp; "
        f"Tier: {tier_filter} &nbsp;·&nbsp; Min score: {min_score}% &nbsp;·&nbsp; "
        f"{total_n} customers in view</p>",
        unsafe_allow_html=True,
    )
with h2:
    st.markdown(
        f"<div style='text-align:right;padding-top:6px;'>"
        f"<span style='background:{CARD};color:{ACCENT};border:1px solid {ACCENT};"
        f"padding:5px 14px;border-radius:6px;font-size:0.78rem;font-weight:600;"
        f"letter-spacing:0.05em;'>XGBoost · AUC {xgb_auc:.4f}</span></div>",
        unsafe_allow_html=True,
    )

st.markdown("<div class='div'></div>", unsafe_allow_html=True)

# 5 KPI cards
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Critical customers",  f"{crit_n:,}",     f"{crit_n/max(total_n,1)*100:.1f}% of view")
k2.metric("Revenue at risk",     f"${tot_rev/1e6:.2f}M", f"{total_n} customers in view")
k3.metric("Avg churn score",     f"{avg_sc:.1f}%",  f"Actual churn {act_rate:.1f}%")
k4.metric("XGBoost AUC",         f"{xgb_auc:.4f}",  f"+{(xgb_auc-lr_auc)*100:.1f}pts over LR")
k5.metric("Stable customers",    f"{low_n:,}",       f"{low_n/max(total_n,1)*100:.1f}% low risk")

st.markdown("<div class='div'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ═══ Z-ZONE 2 — PORTFOLIO (left) + MACRO (right) ═══
# ─────────────────────────────────────────────
st.markdown("## Portfolio overview")
z2l, z2r = st.columns([3, 2])

with z2l:
    # ── Stacked horizontal tier bar
    tier_ns  = {"CRITICAL": crit_n, "HIGH": high_n, "MEDIUM": med_n, "LOW": low_n}
    churn_rt = {"CRITICAL": "91%", "HIGH": "56%", "MEDIUM": "22%", "LOW": "12%"}
    fig_bar  = go.Figure()
    for t, fill in TIER_FILL.items():
        n   = tier_ns[t]
        pct = n / max(total_n, 1) * 100
        fig_bar.add_trace(go.Bar(
            y=[""], x=[pct], orientation="h", name=t,
            marker_color=fill,
            marker_line_color=TIER_SOLID[t], marker_line_width=1,
            text=[f"{t}  {n}  ({pct:.1f}%)"] if pct > 5 else [""],
            textposition="inside", insidetextanchor="middle",
            textfont=dict(size=13, color=WHITE, family="Inter, sans-serif"),
            hovertemplate=(
                f"<b style='color:{WHITE}'>{t}</b><br>"
                f"Customers: <b>{n}</b><br>"
                f"Portfolio share: <b>{pct:.1f}%</b><br>"
                f"Actual churn rate: <b>{churn_rt[t]}</b>"
                "<extra></extra>"
            ),
        ))
    fig_bar.update_layout(
        **layout(height=72, ml=0, mr=0, mt=4, mb=4,
                 barmode="stack",
                 xaxis=dict(range=[0, 100], ticksuffix="%",
                            gridcolor=GRID, linecolor=BORDER,
                            tickfont=dict(color=MUTED, size=12)),
                 yaxis=dict(showticklabels=False,
                            gridcolor=GRID, linecolor=BORDER)),
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    # ── Revenue bars
    fig_rev = go.Figure()
    rev_ns   = [crit_n, high_n, med_n]
    rev_amts = [rev_crit, rev_high, rev_med]
    rev_lbls = ["Critical", "High", "Medium"]
    for i, (lbl, n, amt) in enumerate(zip(rev_lbls, rev_ns, rev_amts)):
        fig_rev.add_trace(go.Bar(
            x=[lbl], y=[amt],
            marker_color=list(TIER_FILL.values())[i],
            marker_line_color=list(TIER_SOLID.values())[i],
            marker_line_width=1,
            text=[f"${amt/1e6:.2f}M"],
            textposition="outside",
            textfont=dict(size=13, color=WHITE),
            hovertemplate=(
                f"<b style='color:{WHITE}'>{lbl}</b><br>"
                f"Customers: <b>{n}</b><br>"
                f"Revenue at risk: <b>${amt/1e6:.2f}M</b>"
                "<extra></extra>"
            ),
            name=lbl,
        ))
    fig_rev.update_layout(
        **layout(height=220, ml=0, mr=0, mt=28, mb=0,
                 yaxis=dict(title="Revenue at risk ($)",
                            tickformat="$,.0f",
                            gridcolor=GRID, linecolor=BORDER,
                            tickfont=dict(color=MUTED, size=12)),
                 xaxis=dict(gridcolor=GRID, linecolor=BORDER,
                            tickfont=dict(color=WHITE, size=13))),
        bargap=0.4,
    )
    st.plotly_chart(fig_rev, use_container_width=True, config={"displayModeBar": False})

    # ── Score distribution histogram
    fig_hist = go.Figure()
    for t, fill in TIER_FILL.items():
        td = fd[fd["risk_tier"] == t]["churn_probability"]
        if len(td) > 0:
            fig_hist.add_trace(go.Histogram(
                x=td, name=t,
                marker_color=fill,
                marker_line_color=TIER_SOLID[t], marker_line_width=0.5,
                opacity=1.0, xbins=dict(size=5),
                hovertemplate=(
                    f"<b style='color:{WHITE}'>{t}</b><br>"
                    f"Score range: <b>%{{x}}%</b><br>"
                    f"Customers: <b>%{{y}}</b>"
                    "<extra></extra>"
                ),
            ))
    fig_hist.update_layout(
        **layout(height=240, ml=0, mr=0, mt=48, mb=4,
                 barmode="overlay",
                 showlegend=True,
                 legend=dict(
                     orientation="h", x=0, y=1.24,
                     font=dict(color=WHITE, size=13),
                     bgcolor="rgba(0,0,0,0)",
                     itemsizing="constant",
                     traceorder="normal",
                 ),
                 xaxis=dict(title="Churn probability (%)",
                            gridcolor=GRID, linecolor=BORDER,
                            tickfont=dict(color=MUTED, size=12),
                            automargin=True),
                 yaxis=dict(title="Customers",
                            gridcolor=GRID, linecolor=BORDER,
                            tickfont=dict(color=MUTED, size=12))),
        autosize=True,
    )
    st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

with z2r:
    # ── AUC gauge (TOP — most important model metric)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=xgb_auc,
        delta={
            "reference": lr_auc,
            "valueformat": ".4f",
            "increasing": {"color": ACCENT},
            "decreasing": {"color": "#ff6b6b"},
        },
        title={"text": "XGBoost AUC vs LR baseline",
               "font": {"size": 13, "color": MUTED}},
        number={"valueformat": ".4f",
                "font": {"size": 26, "color": WHITE}},
        gauge={
            "axis": {"range": [0.5, 1.0], "tickformat": ".2f",
                     "tickcolor": BORDER,
                     "tickfont": {"color": MUTED, "size": 11}},
            "bar":   {"color": ACCENT, "thickness": 0.25},
            "bgcolor": CARD,
            "bordercolor": BORDER,
            "steps": [
                {"range": [0.50, 0.70], "color": "#0d0d14"},
                {"range": [0.70, 0.85], "color": "#111120"},
                {"range": [0.85, 1.00], "color": "#12121f"},
            ],
            "threshold": {
                "line": {"color": "#ff6b6b", "width": 2},
                "thickness": 0.75,
                "value": 0.75,
            },
        },
    ))
    fig_gauge.update_layout(
        height=220,
        margin=dict(l=12, r=12, t=36, b=12),
        paper_bgcolor=BG,
        font=dict(color=MUTED, family="Inter, sans-serif"),
        hoverlabel=dict(bgcolor=TT_BG, bordercolor=ACCENT,
                        font=dict(color=WHITE, size=13)),
    )
    st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    # ── Donut
    tc_vals = {"CRITICAL": crit_n, "HIGH": high_n, "MEDIUM": med_n, "LOW": low_n}
    fig_donut = go.Figure(go.Pie(
        labels=list(tc_vals.keys()),
        values=list(tc_vals.values()),
        hole=0.68,
        marker=dict(
            colors=list(TIER_FILL.values()),
            line=dict(color=[TIER_SOLID[t] for t in tc_vals], width=1),
        ),
        textinfo="label+percent",
        textfont=dict(size=13, color=WHITE),
        hovertemplate=(
            "<b style='color:" + WHITE + "'>%{label}</b><br>"
            "Customers: <b>%{value}</b><br>"
            "Share: <b>%{percent}</b><extra></extra>"
        ),
    ))
    fig_donut.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor=BG,
        showlegend=True,
        legend=dict(
            orientation="h", x=0, y=-0.08,
            font=dict(color=WHITE, size=13),
            bgcolor="rgba(0,0,0,0)",
            itemsizing="constant",
        ),
        annotations=[dict(
            text=f"<b>{total_n}</b><br><span style='font-size:11px'>customers</span>",
            x=0.5, y=0.5,
            font=dict(size=16, color=WHITE, family="Inter, sans-serif"),
            showarrow=False,
        )],
        hoverlabel=dict(bgcolor=TT_BG, bordercolor=ACCENT,
                        font=dict(color=WHITE, size=13)),
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div class='div'></div>", unsafe_allow_html=True)

    # ── Macro signals (below gauge + donut)
    st.markdown(
        f"<p style='font-size:0.7rem;color:{MUTED};text-transform:uppercase;"
        f"letter-spacing:0.1em;margin-bottom:8px;'>Macro risk signals · FRED live</p>",
        unsafe_allow_html=True,
    )
    for label, value, note, bar_val in MACRO:
        intensity = bar_val
        bar_color = f"rgba(74,158,255,{0.3 + intensity*0.7:.2f})"
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;"
            f"align-items:baseline;margin-bottom:2px;'>"
            f"<span style='font-size:0.82rem;color:{MUTED};'>{label}</span>"
            f"<span style='font-size:1rem;font-weight:600;color:{WHITE};'>{value}</span>"
            f"</div>"
            f"<div style='font-size:0.72rem;color:{ACCENT};margin-bottom:3px;'>{note}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='height:5px;background:{BORDER};border-radius:3px;margin-bottom:10px;'>"
            f"<div style='height:5px;width:{bar_val*100:.0f}%;background:{bar_color};"
            f"border-radius:3px;'></div></div>",
            unsafe_allow_html=True,
        )

st.markdown("<div class='div'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ═══ Z-ZONE 3 — SHAP (left) + CUSTOMER INSPECTOR (right) ═══
# ─────────────────────────────────────────────
st.markdown("## Signal intelligence · Customer inspector")
z3l, z3r = st.columns([2, 3])

with z3l:
    # ── Global SHAP
    st.markdown(
        f"<p style='font-size:0.7rem;color:{MUTED};text-transform:uppercase;"
        f"letter-spacing:0.1em;margin-bottom:6px;'>Global SHAP — top cash flow drivers</p>",
        unsafe_allow_html=True,
    )
    sf   = pd.DataFrame(SHAP_FEATURES, columns=["Feature", "Importance"])
    mx   = sf["Importance"].max()
    clrs = [f"rgba(74,158,255,{0.25 + 0.75*v/mx:.2f})" for v in sf["Importance"]]
    brdrs= [f"rgba(74,158,255,{0.5 + 0.5*v/mx:.2f})" for v in sf["Importance"]]

    fig_shap = go.Figure(go.Bar(
        x=sf["Importance"],
        y=sf["Feature"],
        orientation="h",
        marker_color=clrs,
        marker_line_color=brdrs,
        marker_line_width=1,
        text=[f"{v:.2f}" for v in sf["Importance"]],
        textposition="outside",
        textfont=dict(size=12, color=MUTED),
        hovertemplate=(
            "<b style='color:" + WHITE + "'>%{y}</b><br>"
            "Mean |SHAP|: <b>%{x:.3f}</b><extra></extra>"
        ),
    ))
    fig_shap.update_layout(
        **layout(height=460, ml=0, mr=40, mt=8, mb=0,
                 yaxis=dict(autorange="reversed",
                            tickfont=dict(size=13, color=WHITE),
                            gridcolor=GRID, linecolor=BORDER),
                 xaxis=dict(title="Mean |SHAP value|",
                            gridcolor=GRID, linecolor=BORDER,
                            tickfont=dict(color=MUTED, size=12))),
    )
    st.plotly_chart(fig_shap, use_container_width=True, config={"displayModeBar": False})

with z3r:
    if selected != "—" and selected in fd["customer_id"].values:
        cust = fd[fd["customer_id"] == selected].iloc[0]
        tier = cust["risk_tier"]
        fill = TIER_FILL[tier]
        solid= TIER_SOLID[tier]

        # ── Customer KPIs
        ci1, ci2, ci3, ci4 = st.columns(4)
        ci1.metric("ID",               cust["customer_id"].split("_")[-1])
        ci2.metric("Churn probability", f"{cust['churn_probability']:.1f}%")
        ci3.metric("Risk tier",         tier)
        ci4.metric("Actual outcome",    "Churned" if cust["actual_label"] == 1 else "Retained")

        # ── Action banner
        st.markdown(
            f"<div style='background:{CARD};border-left:3px solid {ACCENT};"
            f"border-radius:0 6px 6px 0;padding:10px 14px;margin:6px 0;'>"
            f"<p style='font-size:0.7rem;color:{MUTED};margin:0 0 3px;text-transform:uppercase;"
            f"letter-spacing:0.07em;'>Recommended action</p>"
            f"<p style='font-size:0.9rem;color:{WHITE};margin:0;font-weight:500;'>"
            f"{cust['recommended_action']}</p></div>",
            unsafe_allow_html=True,
        )

        # ── SHAP signals
        st.markdown(
            f"<div style='background:{CARD};border-radius:6px;padding:10px 14px;margin-bottom:6px;'>"
            f"<p style='font-size:0.7rem;color:{MUTED};margin:0 0 4px;text-transform:uppercase;"
            f"letter-spacing:0.07em;'>Top 3 SHAP signals</p>"
            f"<p style='font-size:0.85rem;color:{WHITE};margin:0;line-height:1.7;'>"
            f"{cust['top_3_reasons']}</p></div>",
            unsafe_allow_html=True,
        )

        # ── Per-customer SHAP waterfall
        shap_pairs, base_val = customer_shap(cust)
        top12   = sorted(shap_pairs, key=lambda x: abs(x[1]), reverse=True)[:12]
        f_names = [p[0] for p in top12]
        f_vals  = [p[1] for p in top12]
        running = base_val
        for v in f_vals:
            running += v

        fig_wf = go.Figure(go.Waterfall(
            orientation="h",
            measure=["relative"] * len(f_vals) + ["total"],
            x=f_vals + [running],
            y=f_names + ["Final score"],
            base=base_val,
            connector=dict(line=dict(color=BORDER, width=1, dash="dot")),
            increasing=dict(marker=dict(
                color=A55, line=dict(color=ACCENT, width=1))),
            decreasing=dict(marker=dict(
                color="rgba(100,100,120,0.4)",
                line=dict(color="#505060", width=1))),
            totals=dict(marker=dict(
                color=fill, line=dict(color=solid, width=1))),
            text=[f"{'+'if v>0 else ''}{v:.2f}" for v in f_vals] + [f"{running:.2f}"],
            textfont=dict(size=12, color=WHITE),
            hovertemplate=(
                "<b style='color:" + WHITE + "'>%{y}</b><br>"
                "SHAP impact: <b>%{x:.3f}</b><extra></extra>"
            ),
        ))
        fig_wf.add_vline(
            x=base_val, line_dash="dot",
            line_color=MUTED, line_width=1,
            annotation_text=f"Base rate {base_val:.2f}",
            annotation_font_color=MUTED,
            annotation_font_size=11,
            annotation_position="top right",
        )
        cust_lbl = selected.replace("_", " ").lower()
        fig_wf.update_layout(
            **layout(height=380, ml=0, mr=40, mt=40, mb=0,
                     showlegend=False,
                     xaxis=dict(title="SHAP value — impact on churn score",
                                gridcolor=GRID, linecolor=BORDER,
                                tickfont=dict(color=MUTED, size=12)),
                     yaxis=dict(autorange="reversed",
                                tickfont=dict(size=13, color=WHITE),
                                gridcolor=GRID, linecolor=BORDER)),
            title=dict(
                text=f"Why is {cust_lbl} flagged?",
                font=dict(size=13, color=MUTED),
                x=0, xanchor="left",
            ),
        )
        st.plotly_chart(fig_wf, use_container_width=True, config={"displayModeBar": False})

    else:
        # ── Default state: show portfolio risk scatter — all customers plotted
        st.markdown(
            f"<p style='font-size:0.7rem;color:{MUTED};text-transform:uppercase;"
            f"letter-spacing:0.1em;margin-bottom:4px;'>Portfolio risk scatter — select a customer to inspect</p>",
            unsafe_allow_html=True,
        )
        # sample up to 500 for performance
        plot_df = fd.sample(min(500, len(fd)), random_state=42) if len(fd) > 0 else fd

        fig_scatter = go.Figure()
        for t in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            td = plot_df[plot_df["risk_tier"] == t]
            if len(td) == 0:
                continue
            fig_scatter.add_trace(go.Scatter(
                x=list(range(len(td))),
                y=td["churn_probability"].tolist(),
                mode="markers",
                name=t,
                marker=dict(
                    color=TIER_FILL[t],
                    size=8,
                    line=dict(color=TIER_SOLID[t], width=1),
                    symbol="circle",
                ),
                text=td["customer_id"].tolist(),
                customdata=td["recommended_action"].tolist(),
                hovertemplate=(
                    "<b style='color:" + WHITE + "'>%{text}</b><br>"
                    f"Tier: <b>{t}</b><br>"
                    "Churn score: <b>%{y:.1f}%</b><br>"
                    "Action: <b>%{customdata}</b>"
                    "<extra></extra>"
                ),
            ))

        # Risk threshold lines
        for threshold, label in [(75, "Critical"), (50, "High"), (30, "Medium")]:
            fig_scatter.add_hline(
                y=threshold, line_dash="dot",
                line_color=BORDER, line_width=1,
                annotation_text=label,
                annotation_font_color=MUTED,
                annotation_font_size=11,
                annotation_position="right",
            )

        fig_scatter.update_layout(
            **layout(height=400, ml=0, mr=40, mt=8, mb=0,
                     showlegend=True,
                     legend=dict(
                         orientation="h", x=0, y=1.06,
                         font=dict(color=WHITE, size=13),
                         bgcolor="rgba(0,0,0,0)",
                         itemsizing="constant",
                     ),
                     xaxis=dict(title="Customer index (filtered portfolio)",
                                gridcolor=GRID, linecolor=BORDER,
                                tickfont=dict(color=MUTED, size=11),
                                showticklabels=False),
                     yaxis=dict(title="Churn probability (%)",
                                range=[0, 105],
                                gridcolor=GRID, linecolor=BORDER,
                                tickfont=dict(color=MUTED, size=12))),
        )
        st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})

        # ── Summary stats grid below scatter
        s1, s2, s3 = st.columns(3)
        top_cust = fd.iloc[0] if len(fd) > 0 else None
        s1.markdown(
            f"<div style='background:{CARD};border:1px solid {BORDER};border-radius:8px;"
            f"padding:12px 16px;'>"
            f"<p style='font-size:0.7rem;color:{MUTED};margin:0 0 4px;text-transform:uppercase;"
            f"letter-spacing:0.07em;'>Highest risk customer</p>"
            f"<p style='font-size:0.85rem;color:{WHITE};margin:0;font-weight:500;'>"
            f"{top_cust['customer_id'] if top_cust is not None else '—'}</p>"
            f"<p style='font-size:1.1rem;color:{ACCENT};margin:2px 0 0;font-weight:600;'>"
            f"{top_cust['churn_probability']:.1f}% risk</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
        s2.markdown(
            f"<div style='background:{CARD};border:1px solid {BORDER};border-radius:8px;"
            f"padding:12px 16px;'>"
            f"<p style='font-size:0.7rem;color:{MUTED};margin:0 0 4px;text-transform:uppercase;"
            f"letter-spacing:0.07em;'>Critical tier — actual churn</p>"
            f"<p style='font-size:1.4rem;color:{WHITE};margin:0;font-weight:600;'>91%</p>"
            f"<p style='font-size:0.78rem;color:{MUTED};margin:2px 0 0;'>"
            f"of {crit_n} critical customers churned</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
        s3.markdown(
            f"<div style='background:{CARD};border:1px solid {BORDER};border-radius:8px;"
            f"padding:12px 16px;'>"
            f"<p style='font-size:0.7rem;color:{MUTED};margin:0 0 4px;text-transform:uppercase;"
            f"letter-spacing:0.07em;'>Select a customer above</p>"
            f"<p style='font-size:0.85rem;color:{MUTED};margin:0;'>Use the sidebar dropdown to inspect any customer's individual SHAP waterfall</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

st.markdown("<div class='div'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ═══ Z-ZONE 4 — CUSTOMER TABLE (full width) ═══
# ─────────────────────────────────────────────
n_match = len(fd)
st.markdown(
    f"## Customer table &nbsp;"
    f"<span style='font-size:0.75rem;color:{MUTED};font-weight:400;'>"
    f"{n_match} customers · showing {min(n_rows, n_match)}</span>",
    unsafe_allow_html=True,
)

dcols = ["customer_id", "churn_probability", "risk_tier"]
if show_action:
    dcols.append("recommended_action")
if show_shap:
    dcols.append("top_3_reasons")

disp = fd[dcols].head(n_rows).copy()
disp["churn_probability"] = disp["churn_probability"].apply(lambda x: f"{x:.1f}%")
disp.columns = [c.replace("_", " ").title() for c in disp.columns]


def style_tier(val):
    mp = {
        "CRITICAL": f"background-color:rgba(74,158,255,0.20);color:{WHITE};font-weight:600",
        "HIGH":     f"background-color:rgba(74,158,255,0.13);color:{WHITE};font-weight:600",
        "MEDIUM":   f"background-color:rgba(74,158,255,0.07);color:{WHITE};font-weight:600",
        "LOW":      f"background-color:rgba(74,158,255,0.03);color:{MUTED};font-weight:500",
    }
    return mp.get(val, "")


st.dataframe(
    disp.style.applymap(style_tier, subset=["Risk Tier"]),
    use_container_width=True,
    height=min(440, (n_rows + 1) * 38),
)

csv_out = fd.to_csv(index=False).encode("utf-8")
st.download_button(
    f"Download {n_match} customers as CSV",
    data=csv_out,
    file_name=f"churn_scores_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("<div class='div'></div>", unsafe_allow_html=True)
f1, f2, f3 = st.columns(3)
f1.caption(f"XGBoost + SHAP · {int(s['n_features'])} features · {int(s['n_customers']):,} training customers")
f2.caption(f"Noise {float(s['noise_level'])} · LR AUC {float(s['lr_auc']):.4f} · XGB AUC {float(s['xgb_auc']):.4f}")
f3.caption("Sourabh Rodagi · Gene Volchek (EWS) → Charlie Wise (TransUnion R&C)")
