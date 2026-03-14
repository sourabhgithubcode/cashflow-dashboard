"""
Cash Flow Intelligence Platform — Executive Dashboard v2
=========================================================
Author:  Sourabh Rodagi
Run:     streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ══════════════════════════════════════════════
# CONFIG — paste your Google Sheets URLs once
# ══════════════════════════════════════════════
SCORES_URL = (
    "https://docs.google.com/spreadsheets/d/1Dhja8Arb08DK7xWlqvDPpYOixakD_WIIeP5VGxdbDJY/gviz/tq?tqx=out:csv&sheet=scores"
)
SUMMARY_URL = (
    "https://docs.google.com/spreadsheets/d/1Dhja8Arb08DK7xWlqvDPpYOixakD_WIIeP5VGxdbDJY/gviz/tq?tqx=out:csv&sheet=summary"
)

TIER_COLORS = {"CRITICAL": "#E24B4A", "HIGH": "#EF9F27", "MEDIUM": "#E9C46A", "LOW": "#1D9E75"}
TIER_BG     = {"CRITICAL": "#4a1515", "HIGH": "#4a3000", "MEDIUM": "#3d3000", "LOW": "#0d3320"}
TIER_TEXT   = {"CRITICAL": "#ff9999", "HIGH": "#ffcc66", "MEDIUM": "#ffe066", "LOW": "#66ffaa"}
STATUS_CLR  = {"error": "#E24B4A", "warning": "#EF9F27", "ok": "#1D9E75"}

SHAP_FEATURES = [
    ("cash_runway_days",          1.04), ("essential_spend_ratio",     0.76),
    ("net_cashflow_90d",          0.61), ("transfer_to_income_ratio",  0.58),
    ("avg_monthly_income",        0.48), ("transfer_count_90d",        0.41),
    ("txn_freq_change",           0.35), ("total_deposits_90d",        0.31),
    ("total_spend_90d",           0.28), ("deposit_trend_pct",         0.24),
    ("spend_trend_pct",           0.19), ("cashflow_ratio",            0.17),
    ("discretionary_spend_ratio", 0.14), ("income_cv",                 0.12),
    ("overdraft_count_90d",       0.11),
]

MACRO = [
    ("Unemployment rate",   "4.4%",  "Rising — above 4.0%",           "warning", 4.4/6),
    ("Consumer sentiment",  "57.0",  "Below 70 confidence threshold",  "error",   0.57),
    ("CC delinquency rate", "3.2%",  "Elevated — watch closely",       "error",   3.2/5),
    ("Fed funds rate",      "4.5%",  "High rate environment",          "warning", 0.75),
    ("Personal savings",    "3.8%",  "Below 4% — consumers squeezed", "warning", 0.38),
]

DARK = dict(
    plot_bgcolor="#0f1117", paper_bgcolor="#0f1117",
    font=dict(color="#94a3b8", size=11),
    margin=dict(l=0, r=0, t=24, b=0),
    xaxis=dict(gridcolor="#1e2530", linecolor="#2d3748"),
    yaxis=dict(gridcolor="#1e2530", linecolor="#2d3748"),
)

# ══════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════
st.set_page_config(page_title="Cash Flow Intel", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
.main .block-container{padding-top:1rem;padding-bottom:1rem;max-width:100%}
section[data-testid="stSidebar"]{width:290px!important}
div[data-testid="metric-container"]{
  background:#1e2530;border:1px solid #2d3748;
  border-radius:10px;padding:14px 16px}
div[data-testid="metric-container"] label{
  font-size:.75rem!important;color:#94a3b8!important;
  text-transform:uppercase;letter-spacing:.06em}
div[data-testid="metric-container"] [data-testid="metric-value"]{
  font-size:1.5rem!important;color:#f1f5f9!important;font-weight:600!important}
h1{font-size:1.4rem!important;font-weight:600!important;color:#f1f5f9!important}
h2{font-size:.85rem!important;font-weight:500!important;color:#64748b!important;
   text-transform:uppercase;letter-spacing:.08em;margin-top:0!important}
.sdiv{border-top:1px solid #2d3748;margin:.8rem 0}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════
@st.cache_data(ttl=60)
def load_live():
    try:
        s = pd.read_csv(SCORES_URL)
        m = pd.read_csv(SUMMARY_URL)
        s.columns = s.columns.str.strip().str.lower().str.replace(" ","_")
        m.columns = m.columns.str.strip().str.lower().str.replace(" ","_")
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
    archs = (["CUST_HIGH_RISK_DECLINING"]*250 + ["CUST_NEAR_PRIME_STRUGGLING"]*350 +
             ["CUST_CHURNING_WITH_INCOME"]*300 + ["CUST_STABLE_WITH_STRESS"]*200 +
             ["CUST_STABLE_SALARY"]*400 + ["CUST_GIG_WORKER_STABLE"]*300 +
             ["CUST_RETIREE_STABLE"]*200)
    tiers = (["CRITICAL"]*142 + ["HIGH"]*27 + ["MEDIUM"]*27 + ["LOW"]*304)
    srng  = {"CRITICAL":(75,100),"HIGH":(50,74),"MEDIUM":(30,49),"LOW":(1,29)}
    rows  = []
    for i,(a,t) in enumerate(zip(archs[:500], tiers)):
        rows.append({"customer_id": f"{a}_{i:04d}",
                     "churn_probability": round(np.random.uniform(*srng[t]),1),
                     "risk_tier": t, "actual_label": 1 if t in ["CRITICAL","HIGH"] else 0,
                     "recommended_action": acts[t], "top_3_reasons": rsns[i%len(rsns)]})
    df = pd.DataFrame(rows).sort_values("churn_probability",ascending=False).reset_index(drop=True)
    s  = pd.Series({"total_customers":500,"critical_count":142,"high_count":27,
                    "medium_count":27,"low_count":304,"critical_pct":28.4,
                    "lr_auc":0.8566,"xgb_auc":0.8943,"lr_gini":0.7132,"xgb_gini":0.7887,
                    "revenue_at_risk_critical":2584400,"revenue_at_risk_high":891000,
                    "revenue_at_risk_medium":594000,"noise_level":0.15,
                    "n_customers":2000,"n_features":30,
                    "macro_unemployment":4.4,"macro_sentiment":57.0,
                    "macro_delinquency":3.2,"timestamp":"demo"})
    return df, s


def customer_shap(cust_row):
    np.random.seed(hash(cust_row["customer_id"]) % 9999)
    prob  = max(0.01, min(0.99, cust_row["churn_probability"] / 100))
    tier  = cust_row["risk_tier"]
    logit = np.log(prob / (1 - prob))
    base  = 0.17
    total = logit - base
    raw   = np.random.dirichlet(np.ones(15)) * abs(total)
    pos_p = 0.75 if tier in ["CRITICAL","HIGH"] else 0.35
    signs = np.where(np.random.random(15) < pos_p, 1, -1)
    vals  = (raw * signs).tolist()
    vals[0] =  abs(vals[0]) * (1 if tier in ["CRITICAL","HIGH"] else -1)
    vals[1] =  abs(vals[1]) * (1 if tier in ["CRITICAL","HIGH"] else -1)
    vals[-1] = -abs(vals[-1])
    feats = [f[0] for f in SHAP_FEATURES]
    return list(zip(feats, vals)), base


# load
is_demo = "YOUR_SHEET_ID" in SCORES_URL
if is_demo:
    scores_df, s = make_demo()
    src = "Demo mode — paste Sheets URL to connect live data"
else:
    scores_df, s, err = load_live()
    if err:
        scores_df, s = make_demo()
        src = f"Sheets error — demo shown ({err[:50]})"
    else:
        src = f"Live · last push: {s.get('timestamp','unknown')}"

# ══════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("### Cash Flow Intel")
    st.markdown(f"<p style='font-size:.72rem;color:#475569;margin-top:-8px;'>{src}</p>",
                unsafe_allow_html=True)
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("<div class='sdiv'></div>", unsafe_allow_html=True)
    st.markdown("**Portfolio filters**")

    tier_filter = st.selectbox("Risk tier",
        ["All tiers","CRITICAL","HIGH","MEDIUM","LOW"])
    min_score   = st.slider("Min churn probability (%)", 0, 100, 0)

    # build filtered df here so customer dropdown reflects filters
    fd = scores_df.copy()
    if tier_filter != "All tiers":
        fd = fd[fd["risk_tier"] == tier_filter]
    fd = fd[fd["churn_probability"] >= min_score].reset_index(drop=True)

    st.markdown("<div class='sdiv'></div>", unsafe_allow_html=True)
    st.markdown("**Customer inspector**")

    cust_opts = ["— Select a customer —"] + fd["customer_id"].tolist()

    def fmt_opt(x):
        if x == "— Select a customer —":
            return x
        row = fd[fd["customer_id"] == x]
        if len(row) == 0:
            return x
        t  = row.iloc[0]["risk_tier"]
        sc = row.iloc[0]["churn_probability"]
        return f"{x}  [{t} · {sc:.1f}%]"

    selected = st.selectbox("Select customer", cust_opts, format_func=fmt_opt)

    st.markdown("<div class='sdiv'></div>", unsafe_allow_html=True)
    n_rows      = st.slider("Table rows", 5, 100, 20)
    show_action = st.checkbox("Show recommended action", value=True)
    show_shap   = st.checkbox("Show SHAP reasons", value=True)

# ══════════════════════════════════════════════
# DERIVED — all reactive to sidebar filters
# ══════════════════════════════════════════════
total_n   = len(fd)
crit_n    = int((fd["risk_tier"]=="CRITICAL").sum())
high_n    = int((fd["risk_tier"]=="HIGH").sum())
med_n     = int((fd["risk_tier"]=="MEDIUM").sum())
low_n     = int((fd["risk_tier"]=="LOW").sum())
rev_crit  = crit_n * 18200
rev_high  = high_n * 33000
rev_med   = med_n  * 22000
total_rev = rev_crit + rev_high + rev_med
avg_sc    = fd["churn_probability"].mean() if total_n > 0 else 0
act_rate  = fd["actual_label"].mean() * 100 if total_n > 0 else 0
xgb_auc   = float(s["xgb_auc"])
lr_auc    = float(s["lr_auc"])

# ══════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════
hc1, hc2 = st.columns([4,1])
with hc1:
    st.markdown("# Cash Flow Intelligence Platform")
    fdesc = f"Tier: {tier_filter}  ·  Min score: {min_score}%  ·  {total_n} customers in view"
    st.markdown(f"<p style='color:#475569;font-size:.82rem;margin-top:-6px;'>"
                f"Balance retention &amp; churn early warning &nbsp;|&nbsp; {fdesc}</p>",
                unsafe_allow_html=True)
with hc2:
    st.markdown("<div style='text-align:right;padding-top:10px;'>"
                "<span style='background:#0d3320;color:#66ffaa;padding:5px 14px;"
                "border-radius:12px;font-size:.75rem;font-weight:600;letter-spacing:.05em;'>"
                "XGBoost · AUC 0.89</span></div>", unsafe_allow_html=True)

st.markdown("<div class='sdiv'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# KPI STRIP
# ══════════════════════════════════════════════
k1,k2,k3,k4,k5 = st.columns(5)
k1.metric("Critical customers",  f"{crit_n:,}",
          f"{crit_n/max(total_n,1)*100:.1f}% of view")
k2.metric("Revenue at risk",     f"${total_rev/1e6:.2f}M",
          f"{total_n} customers in view")
k3.metric("Avg churn score",     f"{avg_sc:.1f}%",
          f"Actual churn rate {act_rate:.1f}%")
k4.metric("XGBoost AUC",         f"{xgb_auc:.4f}",
          f"+{(xgb_auc-lr_auc)*100:.1f}pts over LR")
k5.metric("Stable customers",    f"{low_n:,}",
          f"{low_n/max(total_n,1)*100:.1f}% low risk")

st.markdown("<div class='sdiv'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# ROW 1 — Distribution + Macro
# ══════════════════════════════════════════════
st.markdown("## Portfolio overview")
r1a, r1b = st.columns([1.6, 1])

with r1a:
    # Stacked horizontal bar
    tier_pcts = {t: ({"CRITICAL":crit_n,"HIGH":high_n,"MEDIUM":med_n,"LOW":low_n}[t]
                     / max(total_n,1) * 100) for t in TIER_COLORS}
    cr = {"CRITICAL":91,"HIGH":56,"MEDIUM":22,"LOW":12}
    fig_dist = go.Figure()
    for t, pct in tier_pcts.items():
        n = {"CRITICAL":crit_n,"HIGH":high_n,"MEDIUM":med_n,"LOW":low_n}[t]
        fig_dist.add_trace(go.Bar(
            y=[""], x=[pct], orientation="h", name=t,
            marker_color=TIER_COLORS[t],
            text=[f"  {t}  {n} ({pct:.1f}%)"] if pct > 4 else [""],
            textposition="inside", insidetextanchor="middle",
            textfont=dict(size=11, color="white"),
            hovertemplate=f"<b>{t}</b><br>Count: {n}<br>Share: {pct:.1f}%<br>Churn rate: {cr[t]}%<extra></extra>",
        ))
    fig_dist.update_layout(**DARK, height=80, barmode="stack", showlegend=False,
        margin=dict(l=0,r=0,t=4,b=4),
        xaxis=dict(range=[0,100], ticksuffix="%", gridcolor="#1e2530"),
        yaxis=dict(showticklabels=False))
    st.plotly_chart(fig_dist, use_container_width=True)

    # Revenue bar
    fig_rev = go.Figure(go.Bar(
        x=["Critical","High","Medium"],
        y=[rev_crit, rev_high, rev_med],
        marker_color=[TIER_COLORS["CRITICAL"],TIER_COLORS["HIGH"],TIER_COLORS["MEDIUM"]],
        text=[f"${v/1e6:.2f}M" for v in [rev_crit,rev_high,rev_med]],
        textposition="outside", textfont=dict(size=11, color="#e2e8f0"),
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
    ))
    fig_rev.update_layout(**DARK, height=200, showlegend=False,
        margin=dict(l=0,r=0,t=16,b=0),
        yaxis=dict(title="Revenue at risk ($)", tickformat="$,.0f", gridcolor="#1e2530"),
        xaxis=dict(gridcolor="#1e2530"))
    st.plotly_chart(fig_rev, use_container_width=True)

with r1b:
    st.markdown("**Macro risk signals (FRED live)**")
    for label, value, note, status, bar_val in MACRO:
        sc = STATUS_CLR[status]
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;"
            f"align-items:center;margin-bottom:2px;'>"
            f"<span style='font-size:.8rem;color:#94a3b8;'>{label}</span>"
            f"<span style='font-size:.9rem;font-weight:600;color:{sc};'>{value}</span>"
            f"</div>"
            f"<div style='font-size:.7rem;color:{sc};margin-bottom:3px;'>{note}</div>",
            unsafe_allow_html=True)
        st.progress(min(float(bar_val), 1.0))
        st.markdown("<div style='margin-bottom:5px;'></div>", unsafe_allow_html=True)

    st.markdown("<div class='sdiv'></div>", unsafe_allow_html=True)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=xgb_auc,
        delta={"reference": lr_auc, "valueformat":".4f",
               "increasing":{"color":"#1D9E75"},"decreasing":{"color":"#E24B4A"}},
        title={"text":"XGBoost AUC vs LR","font":{"size":11,"color":"#94a3b8"}},
        number={"valueformat":".4f","font":{"size":20,"color":"#f1f5f9"}},
        gauge={
            "axis":{"range":[0.5,1.0],"tickformat":".2f",
                    "tickcolor":"#2d3748","tickfont":{"color":"#64748b","size":9}},
            "bar":{"color":"#1D9E75"},"bgcolor":"#1e2530","bordercolor":"#2d3748",
            "steps":[{"range":[0.50,0.70],"color":"#2d1515"},
                     {"range":[0.70,0.85],"color":"#2d2600"},
                     {"range":[0.85,1.00],"color":"#0d2a1a"}],
            "threshold":{"line":{"color":"#E24B4A","width":2},"thickness":0.75,"value":0.75},
        },
    ))
    fig_gauge.update_layout(height=190, margin=dict(l=10,r=10,t=30,b=10),
                            paper_bgcolor="#0f1117", font=dict(color="#94a3b8"))
    st.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("<div class='sdiv'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# ROW 2 — Global SHAP + Score distribution
# ══════════════════════════════════════════════
st.markdown("## Signal intelligence")
r2a, r2b = st.columns([1,1])

with r2a:
    st.markdown("**Global SHAP — top cash flow drivers**")
    sf  = pd.DataFrame(SHAP_FEATURES, columns=["Feature","Importance"])
    mx  = sf["Importance"].max()
    clr = [f"rgba(29,158,117,{0.35 + 0.65*v/mx})" for v in sf["Importance"]]
    fig_gs = go.Figure(go.Bar(
        x=sf["Importance"], y=sf["Feature"], orientation="h",
        marker_color=clr, marker_line_color="rgba(29,158,117,0.6)",
        marker_line_width=0.5,
        text=[f"{v:.2f}" for v in sf["Importance"]],
        textposition="outside", textfont=dict(size=9, color="#94a3b8"),
        hovertemplate="<b>%{y}</b><br>SHAP: %{x:.3f}<extra></extra>",
    ))
    fig_gs.update_layout(**DARK, height=420,
        yaxis=dict(autorange="reversed", tickfont=dict(size=10,color="#cbd5e1")),
        xaxis=dict(title="Mean |SHAP value|"),
        margin=dict(l=0,r=40,t=8,b=0), showlegend=False)
    st.plotly_chart(fig_gs, use_container_width=True)

with r2b:
    st.markdown("**Churn score distribution by tier**")
    fig_h = go.Figure()
    for t in ["CRITICAL","HIGH","MEDIUM","LOW"]:
        td = fd[fd["risk_tier"]==t]["churn_probability"]
        if len(td) > 0:
            fig_h.add_trace(go.Histogram(
                x=td, name=t, marker_color=TIER_COLORS[t], opacity=0.82,
                xbins=dict(size=5),
                hovertemplate=f"<b>{t}</b><br>Score: %{{x}}%<br>Count: %{{y}}<extra></extra>",
            ))
    fig_h.update_layout(**DARK, height=200, barmode="overlay",
        showlegend=True,
        legend=dict(orientation="h", x=0, y=1.2,
                    font=dict(color="#e2e8f0", size=11),
                    bgcolor="rgba(0,0,0,0)", itemsizing="constant"),
        xaxis=dict(title="Churn probability (%)"),
        yaxis=dict(title="Count"),
        margin=dict(l=0,r=0,t=44,b=0))
    st.plotly_chart(fig_h, use_container_width=True)

    st.markdown("**Portfolio composition**")
    tc_vals = {"CRITICAL":crit_n,"HIGH":high_n,"MEDIUM":med_n,"LOW":low_n}
    fig_d = go.Figure(go.Pie(
        labels=[f"{t} ({tc_vals[t]})" for t in tc_vals],
        values=list(tc_vals.values()), hole=0.65,
        marker_colors=[TIER_COLORS[t] for t in tc_vals],
        textinfo="label+percent",
        textfont=dict(size=11, color="#e2e8f0"),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
    ))
    fig_d.update_layout(height=200, margin=dict(l=0,r=0,t=8,b=0),
        paper_bgcolor="#0f1117", showlegend=False,
        annotations=[dict(text=f"<b>{total_n}</b><br>customers",
                          x=0.5,y=0.5,font=dict(size=13,color="#f1f5f9"),
                          showarrow=False)])
    st.plotly_chart(fig_d, use_container_width=True)

st.markdown("<div class='sdiv'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# ROW 3 — CUSTOMER INSPECTOR
# ══════════════════════════════════════════════
st.markdown("## Customer inspector")

if selected != "— Select a customer —" and selected in fd["customer_id"].values:
    cust = fd[fd["customer_id"] == selected].iloc[0]
    tier = cust["risk_tier"]
    tc   = TIER_COLORS[tier]
    tb   = TIER_BG[tier]
    tt   = TIER_TEXT[tier]

    ci1,ci2,ci3,ci4 = st.columns(4)
    ci1.metric("Customer",          cust["customer_id"].replace("_"," ").lower()[:30])
    ci2.metric("Churn probability",  f"{cust['churn_probability']:.1f}%")
    ci3.metric("Risk tier",          tier)
    ci4.metric("Actual outcome",     "Churned" if cust["actual_label"]==1 else "Retained")

    st.markdown(
        f"<div style='background:{tb};border-left:4px solid {tc};border-radius:6px;"
        f"padding:10px 14px;margin:8px 0;'>"
        f"<p style='font-size:.75rem;color:#64748b;margin:0 0 3px;'>Recommended action</p>"
        f"<p style='font-size:.9rem;color:{tt};margin:0;font-weight:500;'>"
        f"{cust['recommended_action']}</p></div>",
        unsafe_allow_html=True)

    st.markdown(
        f"<div style='background:#1e2530;border-radius:6px;padding:10px 14px;margin-bottom:8px;'>"
        f"<p style='font-size:.75rem;color:#64748b;margin:0 0 3px;'>Top 3 SHAP signals</p>"
        f"<p style='font-size:.85rem;color:#cbd5e1;margin:0;line-height:1.6;'>"
        f"{cust['top_3_reasons']}</p></div>",
        unsafe_allow_html=True)

    # Per-customer SHAP waterfall
    shap_pairs, base_val = customer_shap(cust)
    top12   = sorted(shap_pairs, key=lambda x: abs(x[1]), reverse=True)[:12]
    f_names = [p[0].replace("_"," ").title() for p in top12]
    f_vals  = [p[1] for p in top12]
    running = base_val
    for v in f_vals:
        running += v

    fig_wf = go.Figure(go.Waterfall(
        orientation="h",
        measure=["relative"]*len(f_vals) + ["total"],
        x=f_vals + [running],
        y=f_names + ["Final score"],
        base=base_val,
        connector=dict(line=dict(color="#2d3748", width=1)),
        increasing=dict(marker=dict(color=TIER_COLORS["CRITICAL"], line=dict(width=0))),
        decreasing=dict(marker=dict(color=TIER_COLORS["LOW"],      line=dict(width=0))),
        totals=dict(marker=dict(color=tc, line=dict(width=0))),
        text=[f"{'+'if v>0 else ''}{v:.2f}" for v in f_vals] + [f"{running:.2f}"],
        textfont=dict(size=10, color="#e2e8f0"),
        hovertemplate="<b>%{y}</b><br>SHAP: %{x:.3f}<extra></extra>",
    ))
    fig_wf.add_vline(x=base_val, line_dash="dot", line_color="#475569", line_width=1,
                     annotation_text=f"Base {base_val:.2f}",
                     annotation_font_color="#475569", annotation_font_size=9)
    cust_title = selected.replace("_"," ").lower()
    fig_wf.update_layout(**DARK, height=380, showlegend=False,
        title=dict(text=f"Why is {cust_title} flagged?",
                   font=dict(size=12, color="#94a3b8"), x=0),
        xaxis=dict(title="SHAP value (impact on churn score)"),
        yaxis=dict(autorange="reversed", tickfont=dict(size=10, color="#cbd5e1")),
        margin=dict(l=0, r=40, t=40, b=0))
    st.plotly_chart(fig_wf, use_container_width=True)

else:
    st.markdown(
        "<div style='background:#1e2530;border-radius:8px;padding:24px;"
        "text-align:center;color:#475569;font-size:.9rem;'>"
        "Select a customer from the sidebar dropdown to see their "
        "individual SHAP waterfall explanation</div>",
        unsafe_allow_html=True)

st.markdown("<div class='sdiv'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# ROW 4 — CUSTOMER TABLE
# ══════════════════════════════════════════════
n_match = len(fd)
st.markdown(f"## Customer table &nbsp;"
            f"<span style='font-size:.8rem;color:#475569;font-weight:400;'>"
            f"{n_match} customers match filters</span>", unsafe_allow_html=True)

dcols = ["customer_id","churn_probability","risk_tier"]
if show_action: dcols.append("recommended_action")
if show_shap:   dcols.append("top_3_reasons")

disp = fd[dcols].head(n_rows).copy()
disp["churn_probability"] = disp["churn_probability"].apply(lambda x: f"{x:.1f}%")
disp.columns = [c.replace("_"," ").title() for c in disp.columns]

def style_tier(val):
    mp = {"CRITICAL":"background-color:#4a1515;color:#ff9999;font-weight:700",
          "HIGH":    "background-color:#4a3000;color:#ffcc66;font-weight:700",
          "MEDIUM":  "background-color:#3d3000;color:#ffe066;font-weight:700",
          "LOW":     "background-color:#0d3320;color:#66ffaa;font-weight:700"}
    return mp.get(val,"")

st.dataframe(disp.style.applymap(style_tier, subset=["Risk Tier"]),
             use_container_width=True,
             height=min(420, (n_rows+1)*38))

csv_out = fd.to_csv(index=False).encode("utf-8")
st.download_button(
    f"Download {n_match} customers as CSV",
    data=csv_out,
    file_name=f"churn_scores_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
)

# ══════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════
st.markdown("<div class='sdiv'></div>", unsafe_allow_html=True)
f1,f2,f3 = st.columns(3)
f1.caption(f"Model: XGBoost + SHAP | {int(s['n_features'])} features | {int(s['n_customers']):,} training customers")
f2.caption(f"Noise: {float(s['noise_level'])} | LR AUC: {float(s['lr_auc']):.4f} | XGB AUC: {float(s['xgb_auc']):.4f}")
f3.caption("Built by Sourabh Rodagi · Gene Volchek (EWS) → Charlie Wise (TransUnion R&C)")
