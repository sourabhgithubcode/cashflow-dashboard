"""
Cash Flow Intelligence Platform — Executive Dashboard
======================================================
Author:  Sourabh Rodagi
Stack:   Streamlit + Plotly + Google Sheets (live model output)
Run:     streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# CONFIGURATION — paste your Google Sheets URLs here ONE TIME
# Get these URLs from the last cell of your Colab notebook
# ══════════════════════════════════════════════════════════════
SCORES_URL = (
    "https://docs.google.com/spreadsheets/d/1Dhja8Arb08DK7xWlqvDPpYOixakD_WIIeP5VGxdbDJY/gviz/tq?tqx=out:csv&sheet=scores"
)
SUMMARY_URL = (
    "https://docs.google.com/spreadsheets/d/1Dhja8Arb08DK7xWlqvDPpYOixakD_WIIeP5VGxdbDJY/gviz/tq?tqx=out:csv&sheet=summary"
)


# ── Colors (consistent with model notebook)
TIER_COLORS = {
    "CRITICAL": "#E24B4A",
    "HIGH":     "#EF9F27",
    "MEDIUM":   "#FAC775",
    "LOW":      "#1D9E75",
}
TIER_BG = {
    "CRITICAL": "#FCEBEB",
    "HIGH":     "#FAEEDA",
    "MEDIUM":   "#FAEEDA",
    "LOW":      "#E1F5EE",
}

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Cash Flow Intelligence Platform",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (minimal, clean)
st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    div[data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 1rem;
    }
    div[data-testid="metric-container"] label { font-size: 0.8rem; color: #6c757d; }
    .tier-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .stDataFrame { border: 1px solid #e9ecef; border-radius: 8px; }
    h1 { font-size: 1.6rem !important; font-weight: 600 !important; }
    h2 { font-size: 1.1rem !important; font-weight: 500 !important; color: #495057; }
    h3 { font-size: 0.95rem !important; font-weight: 500 !important; color: #6c757d; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=60)   # cache for 60 seconds, auto-refreshes
def load_scores():
    """Load customer risk scores from Google Sheets."""
    try:
        df = pd.read_csv(SCORES_URL)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        df["churn_probability"] = pd.to_numeric(df["churn_probability"], errors="coerce")
        df = df.sort_values("churn_probability", ascending=False).reset_index(drop=True)
        return df, None
    except Exception as e:
        return None, str(e)


@st.cache_data(ttl=60)
def load_summary():
    """Load model summary stats from Google Sheets."""
    try:
        df = pd.read_csv(SUMMARY_URL)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        return df.iloc[0], None
    except Exception as e:
        return None, str(e)


def load_demo_data():
    """
    Fallback demo data when Google Sheets URL is not configured.
    Replace SCORES_URL / SUMMARY_URL above to use real Colab output.
    """
    np.random.seed(42)
    tiers_full = (
        ["CRITICAL"] * 142 + ["HIGH"] * 27 +
        ["MEDIUM"] * 27  + ["LOW"]  * 304
    )
    np.random.shuffle(tiers_full)
    tiers = tiers_full[:500]

    score_ranges = {
        "CRITICAL": (75, 100), "HIGH": (50, 74),
        "MEDIUM": (30, 49),   "LOW":  (1, 29),
    }
    scores = [round(np.random.uniform(*score_ranges[t]), 1) for t in tiers]

    reasons_pool = [
        "Cash Runway Days raises churn risk | Transfer To Income Ratio raises churn risk | Net Cashflow 90D raises churn risk",
        "Essential Spend Ratio raises churn risk | Overdraft Count 90D raises churn risk | Avg Monthly Income lowers churn risk",
        "Txn Freq Change raises churn risk | Total Transfer Outflow 90D raises churn risk | Cashflow Ratio lowers churn risk",
        "Income Cv raises churn risk | Spend Trend Pct raises churn risk | Cash Runway Days raises churn risk",
        "Total Deposits 90D lowers churn risk | Transfer Count 90D raises churn risk | Essential Spend Ratio raises churn risk",
    ]
    actions = {
        "CRITICAL": "Immediate retention call — offer rate or fee waiver",
        "HIGH":     "Proactive outreach within 7 days — targeted product offer",
        "MEDIUM":   "Add to watchlist — automated nurture campaign",
        "LOW":      "No action — routine monitoring",
    }

    scores_df = pd.DataFrame({
        "customer_id":        [f"CUST_{i:04d}" for i in range(500)],
        "churn_probability":  scores,
        "risk_tier":          tiers,
        "actual_label":       [1 if t in ["CRITICAL","HIGH"] else 0 for t in tiers],
        "recommended_action": [actions[t] for t in tiers],
        "top_3_reasons":      [reasons_pool[i % len(reasons_pool)] for i in range(500)],
    }).sort_values("churn_probability", ascending=False).reset_index(drop=True)

    summary = pd.Series({
        "timestamp":                "demo",
        "total_customers":          500,
        "critical_count":           142,
        "high_count":               27,
        "medium_count":             27,
        "low_count":                304,
        "critical_pct":             28.4,
        "lr_auc":                   0.8566,
        "xgb_auc":                  0.8943,
        "lr_gini":                  0.7132,
        "xgb_gini":                 0.7887,
        "revenue_at_risk_critical": 2_584_400,
        "revenue_at_risk_high":     891_000,
        "revenue_at_risk_medium":   594_000,
        "noise_level":              0.15,
        "n_customers":              2000,
        "n_features":               30,
        "macro_unemployment":       4.4,
        "macro_sentiment":          57.0,
        "macro_delinquency":        3.2,
    })
    return scores_df, summary


# ══════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════
is_demo = "YOUR_SHEET_ID" in SCORES_URL

if is_demo:
    scores_df, s = load_demo_data()
    data_source = "Demo data (connect Colab to see live results)"
else:
    scores_df, err1 = load_scores()
    s, err2         = load_summary()
    if err1 or err2:
        st.error(f"Could not load from Google Sheets. Error: {err1 or err2}")
        scores_df, s = load_demo_data()
        data_source  = "Fallback demo (check your Sheets URL)"
    else:
        data_source = f"Live from Google Sheets — last Colab push: {s.get('timestamp','unknown')}"


# ══════════════════════════════════════════════════════════════
# SIDEBAR — CONTROLS
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## Controls")

    st.markdown("### Filter customers")
    tier_filter = st.selectbox(
        "Risk tier",
        ["All tiers", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
    )
    search_term = st.text_input("Search customer ID", placeholder="e.g. CUST_0042")
    min_score   = st.slider("Min churn probability (%)", 0, 100, 0)

    st.divider()

    st.markdown("### Display")
    show_shap      = st.checkbox("Show SHAP reasons", value=True)
    show_action    = st.checkbox("Show recommended action", value=True)
    n_rows         = st.slider("Customers to display", 5, 100, 20)

    st.divider()

    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        f"<p style='font-size:0.72rem;color:#adb5bd;margin-top:8px;'>"
        f"{data_source}</p>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════
col_title, col_badge = st.columns([5, 1])
with col_title:
    st.markdown("# Cash Flow Intelligence Platform")
    st.markdown(
        "<p style='color:#6c757d;font-size:0.9rem;margin-top:-8px;'>"
        "Balance retention &amp; churn early warning — executive view</p>",
        unsafe_allow_html=True,
    )
with col_badge:
    st.markdown(
        "<div style='text-align:right;margin-top:12px;'>"
        "<span style='background:#e1f5ee;color:#0f6e56;padding:4px 12px;"
        "border-radius:12px;font-size:0.78rem;font-weight:600;'>"
        "XGBoost + SHAP</span></div>",
        unsafe_allow_html=True,
    )

st.divider()


# ══════════════════════════════════════════════════════════════
# SECTION 1 — KPI METRICS
# ══════════════════════════════════════════════════════════════
critical_n  = int(s["critical_count"])
high_n      = int(s["high_count"])
medium_n    = int(s["medium_count"])
low_n       = int(s["low_count"])
total_n     = int(s["total_customers"])
rev_crit    = float(s["revenue_at_risk_critical"])
rev_high    = float(s["revenue_at_risk_high"])
rev_med     = float(s["revenue_at_risk_medium"])
total_rev   = rev_crit + rev_high + rev_med
xgb_auc     = float(s["xgb_auc"])
lr_auc      = float(s["lr_auc"])
xgb_gini    = float(s["xgb_gini"])

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Critical risk customers", f"{critical_n:,}",
          f"{float(s['critical_pct']):.1f}% of portfolio")
m2.metric("Total revenue at risk",   f"${total_rev/1_000_000:.1f}M",
          "Est. annual deposit base")
m3.metric("XGBoost AUC",            f"{xgb_auc:.4f}",
          f"+{(xgb_auc - lr_auc)*100:.1f} pts over LR baseline")
m4.metric("Gini coefficient",        f"{xgb_gini:.4f}",
          "Production grade (>0.60)")
m5.metric("Stable customers",        f"{low_n:,}",
          f"{low_n/total_n*100:.1f}% low risk")

st.markdown("<br>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# SECTION 2 — PORTFOLIO HEATMAP + MACRO SIGNALS
# ══════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1.6, 1])

with col_left:
    st.markdown("## Portfolio risk distribution")

    tier_data = pd.DataFrame({
        "Tier":     ["Critical", "High", "Medium", "Low"],
        "Count":    [critical_n, high_n, medium_n, low_n],
        "Revenue":  [rev_crit, rev_high, rev_med, 0],
        "Color":    ["#E24B4A", "#EF9F27", "#FAC775", "#1D9E75"],
        "Churn %":  [91, 56, 22, 12],
    })

    # Horizontal bar chart — risk distribution
    fig_dist = go.Figure()
    for _, row in tier_data.iterrows():
        pct = row["Count"] / total_n * 100
        fig_dist.add_trace(go.Bar(
            y=[row["Tier"]],
            x=[pct],
            orientation="h",
            marker_color=row["Color"],
            name=row["Tier"],
            text=[f'{row["Count"]} customers ({pct:.1f}%)'],
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=12, color="white"),
            hovertemplate=(
                f"<b>{row['Tier']}</b><br>"
                f"Customers: {row['Count']}<br>"
                f"Portfolio share: {pct:.1f}%<br>"
                f"Actual churn rate: {row['Churn %']}%<br>"
                + (f"Revenue at risk: ${row['Revenue']/1e6:.2f}M" if row['Revenue'] > 0 else "Stable")
                + "<extra></extra>"
            ),
        ))

    fig_dist.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=10, b=10),
        showlegend=False,
        barmode="stack",
        xaxis=dict(
            title="% of portfolio",
            range=[0, 100],
            ticksuffix="%",
            gridcolor="#f0f0f0",
        ),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_dist, use_container_width=True)

    # Revenue at risk bar chart
    st.markdown("## Revenue at risk by tier ($)")
    fig_rev = go.Figure(go.Bar(
        x=["Critical", "High", "Medium"],
        y=[rev_crit, rev_high, rev_med],
        marker_color=["#E24B4A", "#EF9F27", "#FAC775"],
        text=[f"${v/1e6:.2f}M" for v in [rev_crit, rev_high, rev_med]],
        textposition="outside",
        textfont=dict(size=12),
    ))
    fig_rev.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=20, b=10),
        showlegend=False,
        yaxis=dict(
            title="Revenue at risk ($)",
            gridcolor="#f0f0f0",
            tickformat="$,.0f",
        ),
        xaxis=dict(gridcolor="#f0f0f0"),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig_rev, use_container_width=True)

with col_right:
    st.markdown("## Macro risk signals (FRED live)")

    macro_signals = [
        {
            "label":  "Unemployment rate",
            "value":  f"{float(s['macro_unemployment']):.1f}%",
            "note":   "Rising — above 4.0%",
            "status": "warning",
            "bar":    min(float(s["macro_unemployment"]) / 6, 1),
        },
        {
            "label":  "Consumer sentiment",
            "value":  f"{float(s['macro_sentiment']):.1f}",
            "note":   "Below 70 threshold",
            "status": "error",
            "bar":    float(s["macro_sentiment"]) / 100,
        },
        {
            "label":  "CC delinquency rate",
            "value":  f"{float(s['macro_delinquency']):.1f}%",
            "note":   "Elevated — watch closely",
            "status": "warning",
            "bar":    min(float(s["macro_delinquency"]) / 5, 1),
        },
        {
            "label":  "Fed funds rate",
            "value":  "4.5%",
            "note":   "High rate environment",
            "status": "warning",
            "bar":    0.75,
        },
        {
            "label":  "Personal savings rate",
            "value":  "3.8%",
            "note":   "Below 4% — consumers squeezed",
            "status": "warning",
            "bar":    0.38,
        },
    ]

    status_colors = {"error": "#E24B4A", "warning": "#EF9F27", "ok": "#1D9E75"}

    for sig in macro_signals:
        col_a, col_b = st.columns([2, 1])
        sig_status = sig["status"]
        sig_color  = status_colors[sig_status]
        with col_a:
            st.markdown(
                f"<p style='font-size:0.82rem;color:#6c757d;margin-bottom:0;'>{sig['label']}</p>"
                f"<p style='font-size:0.75rem;color:{sig_color};margin-top:0;'>{sig['note']}</p>",
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                f"<p style='font-size:1.1rem;font-weight:600;text-align:right;"
                f"color:{sig_color};margin-bottom:0;'>{sig['value']}</p>",
                unsafe_allow_html=True,
            )
        st.progress(sig["bar"])
        st.markdown("<div style='margin-bottom:4px;'></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("## Model performance")

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=xgb_auc,
        delta={"reference": lr_auc, "valueformat": ".4f"},
        title={"text": "XGBoost AUC vs LR baseline", "font": {"size": 13}},
        gauge={
            "axis":  {"range": [0.5, 1.0], "tickformat": ".2f"},
            "bar":   {"color": "#1D9E75"},
            "steps": [
                {"range": [0.5, 0.70], "color": "#FCEBEB"},
                {"range": [0.70, 0.85], "color": "#FAEEDA"},
                {"range": [0.85, 1.0], "color": "#E1F5EE"},
            ],
            "threshold": {
                "line": {"color": "#E24B4A", "width": 2},
                "thickness": 0.75,
                "value": 0.75,
            },
        },
        number={"valueformat": ".4f"},
    ))
    fig_gauge.update_layout(height=220, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_gauge, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# SECTION 3 — SHAP FEATURE IMPORTANCE
# ══════════════════════════════════════════════════════════════
st.divider()
st.markdown("## Top cash flow signals driving churn (SHAP)")
st.markdown(
    "<p style='color:#6c757d;font-size:0.85rem;margin-top:-8px;'>"
    "Every feature is derived from raw bank transactions — zero bureau data</p>",
    unsafe_allow_html=True,
)

shap_features = [
    ("cash_runway_days",           1.04),
    ("essential_spend_ratio",      0.76),
    ("net_cashflow_90d",           0.61),
    ("transfer_to_income_ratio",   0.58),
    ("avg_monthly_income",         0.48),
    ("transfer_count_90d",         0.41),
    ("txn_freq_change",            0.35),
    ("total_deposits_90d",         0.31),
    ("total_spend_90d",            0.28),
    ("deposit_trend_pct",          0.24),
    ("spend_trend_pct",            0.19),
    ("cashflow_ratio",             0.17),
    ("discretionary_spend_ratio",  0.14),
    ("income_cv",                  0.12),
    ("overdraft_count_90d",        0.11),
]

shap_df = pd.DataFrame(shap_features, columns=["Feature", "SHAP importance"])
fig_shap = px.bar(
    shap_df,
    x="SHAP importance",
    y="Feature",
    orientation="h",
    color="SHAP importance",
    color_continuous_scale=["#E1F5EE", "#1D9E75", "#0F6E56"],
)
fig_shap.update_layout(
    height=380,
    margin=dict(l=0, r=0, t=10, b=10),
    showlegend=False,
    coloraxis_showscale=False,
    yaxis={"autorange": "reversed", "tickfont": {"size": 11}},
    xaxis={"gridcolor": "#f0f0f0", "title": "Mean |SHAP value|"},
    plot_bgcolor="white",
    paper_bgcolor="white",
)
st.plotly_chart(fig_shap, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# SECTION 4 — AT-RISK CUSTOMER TABLE
# ══════════════════════════════════════════════════════════════
st.divider()
st.markdown("## At-risk customers")

# Apply filters
filtered_df = scores_df.copy()
if tier_filter != "All tiers":
    filtered_df = filtered_df[filtered_df["risk_tier"] == tier_filter]
if search_term:
    filtered_df = filtered_df[
        filtered_df["customer_id"].str.contains(search_term, case=False, na=False)
    ]
filtered_df = filtered_df[filtered_df["churn_probability"] >= min_score]

# Summary counts for filtered view
col_f1, col_f2, col_f3 = st.columns(3)
col_f1.caption(f"Showing {min(n_rows, len(filtered_df))} of {len(filtered_df)} filtered customers")
col_f2.caption(f"Avg churn probability: {filtered_df['churn_probability'].mean():.1f}%")
col_f3.caption(f"Actual churn rate: {filtered_df['actual_label'].mean()*100:.1f}%")

# Build display dataframe
display_cols = ["customer_id", "churn_probability", "risk_tier"]
if show_action:
    display_cols.append("recommended_action")
if show_shap:
    display_cols.append("top_3_reasons")

display_df = filtered_df[display_cols].head(n_rows).copy()
display_df.columns = [c.replace("_", " ").title() for c in display_df.columns]
display_df["Churn Probability"] = display_df["Churn Probability"].apply(lambda x: f"{x:.1f}%")

# Color-code risk tier column
def color_tier(val):
    colors = {
        "CRITICAL": "background-color:#FCEBEB;color:#A32D2D;font-weight:600",
        "HIGH":     "background-color:#FAEEDA;color:#854F0B;font-weight:600",
        "MEDIUM":   "background-color:#FAEEDA;color:#633806;font-weight:600",
        "LOW":      "background-color:#E1F5EE;color:#0F6E56;font-weight:600",
    }
    return colors.get(val, "")

styled = display_df.style.applymap(
    color_tier, subset=["Risk Tier"]
)

st.dataframe(styled, use_container_width=True, height=400)

# Download button
csv_data = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label=f"Download {len(filtered_df)} customers as CSV",
    data=csv_data,
    file_name=f"churn_risk_scores_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
)


# ══════════════════════════════════════════════════════════════
# SECTION 5 — SCORE DISTRIBUTION CHART
# ══════════════════════════════════════════════════════════════
st.divider()
st.markdown("## Churn probability distribution")
col_hist, col_donut = st.columns([1.5, 1])

with col_hist:
    fig_hist = go.Figure()
    for tier, color in TIER_COLORS.items():
        tier_scores = scores_df[scores_df["risk_tier"] == tier]["churn_probability"]
        fig_hist.add_trace(go.Histogram(
            x=tier_scores,
            name=tier,
            marker_color=color,
            opacity=0.8,
            xbins=dict(size=5),
        ))
    fig_hist.update_layout(
        barmode="overlay",
        height=280,
        margin=dict(l=0, r=0, t=10, b=10),
        xaxis=dict(title="Churn probability (%)", gridcolor="#f0f0f0"),
        yaxis=dict(title="Customers", gridcolor="#f0f0f0"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with col_donut:
    fig_donut = go.Figure(go.Pie(
        labels=["Critical", "High", "Medium", "Low"],
        values=[critical_n, high_n, medium_n, low_n],
        hole=0.6,
        marker_colors=["#E24B4A", "#EF9F27", "#FAC775", "#1D9E75"],
        textinfo="label+percent",
        textfont_size=12,
    ))
    fig_donut.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=10, b=10),
        showlegend=False,
        annotations=[dict(
            text=f"{total_n}<br>customers",
            x=0.5, y=0.5,
            font_size=14,
            showarrow=False,
        )],
    )
    st.plotly_chart(fig_donut, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
st.divider()
col_foot1, col_foot2, col_foot3 = st.columns(3)
col_foot1.caption(
    f"Model: XGBoost + SHAP | Features: {int(s['n_features'])} "
    f"({int(s['n_features']) - 11} cash flow + 11 macro)"
)
col_foot2.caption(
    f"Training: {int(s['n_customers']):,} customers | "
    f"Noise level: {float(s['noise_level'])}"
)
col_foot3.caption(
    "Built by Sourabh Rodagi | "
    "Inspired by Gene Volchek (EWS) → Charlie Wise (TransUnion R&C)"
)
