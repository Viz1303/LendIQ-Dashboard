"""
LendIQ — B2B SaaS Lending Metrics Dashboard
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LendIQ Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BRAND   = "#1B4F72"
ACCENT  = "#2E86C1"
WARNING = "#E67E22"
DANGER  = "#C0392B"
SUCCESS = "#1E8449"
MUTED   = "#717D7E"
BG      = "#F4F6F7"

THRESHOLDS = {
    "npa_rate":        {"warn": 0.04, "critical": 0.05},
    "activation_rate": {"warn": 0.60},
    "churn_rate":      {"warn": 0.05},
    "ltv_cac_ratio":   {"warn": 3.0},
    "support_ticket_volume": {"warn": 150},
    "cac":             {"warn": 4500},
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(__file__), "data", "lendiq_metrics.csv")
    df = pd.read_csv(path, parse_dates=["date", "week_start"])
    return df

df_full = load_data()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bank-building.png", width=60)
    st.title("LendIQ")
    st.caption("B2B SaaS Lending · India")
    st.divider()

    page = st.radio(
        "Navigate",
        ["Overview", "Funnel & Retention", "Risk Monitor"],
        label_visibility="collapsed",
    )
    st.divider()

    min_date = df_full["date"].min().date()
    max_date = df_full["date"].max().date()
    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    else:
        start, end = pd.Timestamp(min_date), pd.Timestamp(max_date)

    st.divider()
    st.caption("Thresholds")
    st.markdown(
        "🟡 **Warn** · 🔴 **Critical**\n\n"
        "- NPA Rate: warn 4%, crit 5%\n"
        "- Activation: warn <60%\n"
        "- Churn: warn >5%\n"
        "- LTV:CAC: warn <3×\n"
        "- Tickets: warn >150/day\n"
        "- CAC: warn >₹4,500"
    )

df = df_full[(df_full["date"] >= start) & (df_full["date"] <= end)].copy()
df_weekly = (
    df.groupby("week_start")
    .agg(
        loan_disbursal_volume=("loan_disbursal_volume", "sum"),
        leads=("leads", "sum"),
        applications=("applications", "sum"),
        approvals=("approvals", "sum"),
        disbursals=("disbursals", "sum"),
        dau=("dau", "mean"),
        activation_rate=("activation_rate", "mean"),
        churn_rate=("churn_rate", "mean"),
        cac=("cac", "mean"),
        ltv=("ltv", "mean"),
        npa_rate=("npa_rate", "mean"),
        support_ticket_volume=("support_ticket_volume", "sum"),
        ltv_cac_ratio=("ltv_cac_ratio", "mean"),
    )
    .reset_index()
)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fmt_inr(val):
    if val >= 1e7:
        return f"₹{val/1e7:.1f} Cr"
    elif val >= 1e5:
        return f"₹{val/1e5:.1f} L"
    else:
        return f"₹{val:,.0f}"

def delta_pct(series):
    """WoW % change of the last two weekly values."""
    if len(series) < 2:
        return None
    last, prev = series.iloc[-1], series.iloc[-2]
    if prev == 0:
        return None
    return (last - prev) / abs(prev) * 100

def kpi_card(label, value, delta=None, fmt="number", inverse=False):
    """Render a single metric card."""
    if fmt == "inr":
        display = fmt_inr(value)
    elif fmt == "pct":
        display = f"{value:.1%}"
    elif fmt == "ratio":
        display = f"{value:.2f}×"
    else:
        display = f"{value:,.0f}"

    if delta is not None:
        arrow = "▲" if delta > 0 else "▼"
        good  = (delta > 0) if not inverse else (delta < 0)
        color = SUCCESS if good else DANGER
        delta_str = f'<span style="color:{color};font-size:0.85rem">{arrow} {abs(delta):.1f}%</span>'
    else:
        delta_str = ""

    st.markdown(
        f"""
        <div style="background:{BG};border-left:4px solid {BRAND};
                    border-radius:6px;padding:14px 18px;margin-bottom:4px;">
            <div style="font-size:0.78rem;color:{MUTED};text-transform:uppercase;
                        letter-spacing:.05em">{label}</div>
            <div style="font-size:1.7rem;font-weight:700;color:{BRAND};line-height:1.2">{display}</div>
            {delta_str}
        </div>
        """,
        unsafe_allow_html=True,
    )

def commentary_box(text):
    st.markdown(
        f"""
        <div style="background:#EAF2FF;border-left:4px solid {ACCENT};
                    border-radius:6px;padding:16px 20px;margin-top:8px;">
            <div style="font-size:0.78rem;font-weight:700;color:{ACCENT};
                        text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px">
                PM Commentary
            </div>
            <div style="font-size:0.88rem;color:#1a1a2e;white-space:pre-line;line-height:1.7">
                {text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def line_chart(df_w, x, y, title, color=ACCENT, y_fmt=None, threshold=None,
               threshold_label=None, threshold_color=DANGER,
               threshold2=None, threshold2_label=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_w[x], y=df_w[y],
        mode="lines", line=dict(color=color, width=2.5),
        fill="tozeroy", fillcolor=f"rgba(46,134,193,0.07)",
        hovertemplate="%{x|%d %b %Y}<br>" + (
            "%{y:.1%}" if y_fmt == "pct" else
            "₹%{y:,.0f}" if y_fmt == "inr" else
            "%{y:,.1f}×" if y_fmt == "ratio" else
            "%{y:,.0f}"
        ) + "<extra></extra>",
    ))
    if threshold is not None:
        fig.add_hline(
            y=threshold, line_dash="dot", line_color=threshold_color, line_width=1.5,
            annotation_text=threshold_label or f"Threshold {threshold}",
            annotation_position="top right",
            annotation_font_color=threshold_color,
        )
    if threshold2 is not None:
        fig.add_hline(
            y=threshold2, line_dash="dot", line_color=DANGER, line_width=1.5,
            annotation_text=threshold2_label or f"Critical {threshold2}",
            annotation_position="bottom right",
            annotation_font_color=DANGER,
        )
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=BRAND)),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(showgrid=False, tickformat="%b %y", title=""),
        yaxis=dict(
            showgrid=True, gridcolor="#e8e8e8",
            tickformat=".0%" if y_fmt == "pct" else
                       "₹,.0f" if y_fmt == "inr" else
                       ".2f" if y_fmt == "ratio" else ",",
            title="",
        ),
        height=280,
        showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 — OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
if page == "Overview":
    st.markdown(f"## Overview — North Star & Growth Health")
    st.caption(f"{start.strftime('%d %b %Y')} → {end.strftime('%d %b %Y')}")

    total_vol  = df["loan_disbursal_volume"].sum()
    avg_dau    = df["dau"].mean()
    avg_ratio  = df["ltv_cac_ratio"].mean()
    avg_activ  = df["activation_rate"].mean()

    d_vol   = delta_pct(df_weekly["loan_disbursal_volume"])
    d_dau   = delta_pct(df_weekly["dau"])
    d_ratio = delta_pct(df_weekly["ltv_cac_ratio"])
    d_activ = delta_pct(df_weekly["activation_rate"])

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Loan Disbursal Volume", total_vol,  d_vol,   fmt="inr")
    with c2: kpi_card("Avg DAU",               avg_dau,   d_dau,   fmt="number")
    with c3: kpi_card("LTV:CAC Ratio",         avg_ratio, d_ratio, fmt="ratio")
    with c4: kpi_card("Activation Rate",       avg_activ, d_activ, fmt="pct")

    st.divider()

    col_l, col_r = st.columns([2, 1])

    with col_l:
        fig_vol = line_chart(
            df_weekly, "week_start", "loan_disbursal_volume",
            "Weekly Loan Disbursal Volume (₹)",
            y_fmt="inr", color=BRAND,
        )
        st.plotly_chart(fig_vol, use_container_width=True)

        fig_dau = line_chart(
            df_weekly, "week_start", "dau",
            "Daily Active Users (weekly avg)",
            color=ACCENT,
        )
        st.plotly_chart(fig_dau, use_container_width=True)

    with col_r:
        # LTV:CAC ratio
        fig_ratio = line_chart(
            df_weekly, "week_start", "ltv_cac_ratio",
            "LTV:CAC Ratio",
            y_fmt="ratio",
            color=SUCCESS,
            threshold=3.0, threshold_label="Min: 3×", threshold_color=DANGER,
        )
        st.plotly_chart(fig_ratio, use_container_width=True)

        commentary_box(
            "NORTH STAR: Loan Disbursal Volume (₹)\n\n"
            "• Volume drop >10% WoW → investigate funnel drop-off; check lead quality and approval TAT.\n\n"
            "• DAU drop >10% WoW → product engagement issue; review push notifications and re-engagement flows.\n\n"
            "• LTV:CAC falls below 3× → pause top-of-funnel spend immediately. Do not scale acquisition until unit economics recover.\n\n"
            "Key call: High disbursal volume + rising NPA = false growth. Always read this page alongside the Risk Monitor."
        )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2 — FUNNEL & RETENTION
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Funnel & Retention":
    st.markdown("## Funnel & Retention")
    st.caption(f"{start.strftime('%d %b %Y')} → {end.strftime('%d %b %Y')}")

    total_leads = df["leads"].sum()
    total_apps  = df["applications"].sum()
    total_appv  = df["approvals"].sum()
    total_disb  = df["disbursals"].sum()
    avg_activ   = df["activation_rate"].mean()
    avg_churn   = df["churn_rate"].mean()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: kpi_card("Leads",        total_leads, fmt="number")
    with c2: kpi_card("Applications", total_apps,  fmt="number")
    with c3: kpi_card("Approvals",    total_appv,  fmt="number")
    with c4: kpi_card("Disbursals",   total_disb,  fmt="number")
    with c5: kpi_card("Activation Rate", avg_activ, delta_pct(df_weekly["activation_rate"]), fmt="pct")
    with c6: kpi_card("Churn Rate",   avg_churn, delta_pct(df_weekly["churn_rate"]), fmt="pct", inverse=True)

    st.divider()

    # ── Funnel waterfall ──────────────────────────────────────────────────
    stages  = ["Leads", "Applications", "Approvals", "Disbursals"]
    values  = [total_leads, total_apps, total_appv, total_disb]
    convs   = [100,
               round(total_apps / total_leads * 100, 1),
               round(total_appv / total_apps  * 100, 1),
               round(total_disb / total_appv  * 100, 1)]

    fig_funnel = go.Figure(go.Funnel(
        y=stages, x=values,
        textinfo="value+percent previous",
        marker=dict(color=[BRAND, ACCENT, "#2980B9", "#5DADE2"]),
        connector=dict(line=dict(color="#cccccc", width=1)),
    ))
    fig_funnel.update_layout(
        title=dict(text="Acquisition Funnel (period total)", font=dict(size=14, color=BRAND)),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=10, r=10, t=40, b=10),
        height=320,
    )

    col_l, col_r = st.columns([1, 2])

    with col_l:
        st.plotly_chart(fig_funnel, use_container_width=True)

        # Conversion rate summary
        st.markdown(
            f"""
            <div style="background:{BG};border-radius:6px;padding:12px 16px;font-size:0.85rem">
            <b>Conversion Rates</b><br>
            Leads → Apps: <b>{total_apps/total_leads:.0%}</b>
            {"  🔴" if total_apps/total_leads < 0.50 else "  ✅"}<br>
            Apps → Approvals: <b>{total_appv/total_apps:.0%}</b>
            {"  🔴" if total_appv/total_apps < 0.60 else "  ✅"}<br>
            Approvals → Disbursals: <b>{total_disb/total_appv:.0%}</b>
            {"  🔴" if total_disb/total_appv < 0.75 else "  ✅"}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_r:
        fig_activ = line_chart(
            df_weekly, "week_start", "activation_rate",
            "Activation Rate (weekly avg)",
            y_fmt="pct", color=SUCCESS,
            threshold=0.60, threshold_label="Min: 60%", threshold_color=WARNING,
        )
        st.plotly_chart(fig_activ, use_container_width=True)

        fig_churn = line_chart(
            df_weekly, "week_start", "churn_rate",
            "Churn Rate (weekly avg)",
            y_fmt="pct", color=WARNING,
            threshold=0.05, threshold_label="Max: 5%", threshold_color=DANGER,
        )
        st.plotly_chart(fig_churn, use_container_width=True)

    commentary_box(
        "FUNNEL & RETENTION\n\n"
        "• Leads → Applications < 50% → messaging/eligibility mismatch; A/B test landing page and eligibility checker copy.\n\n"
        "• Applications → Approvals < 60% → review bureau score cutoffs; check for model drift in underwriting.\n\n"
        "• Approvals → Disbursals < 75% → ops bottleneck (KYC TAT, bank mandate failures); escalate to ops lead.\n\n"
        "• Activation Rate < 60% → onboarding friction; audit Day-1 and Day-7 drop-off in product analytics, prioritise first-loan flow.\n\n"
        "• Churn Rate > 5% → trigger customer-success playbook; segment churned users by loan size, tenure, and repayment history.\n\n"
        "Key call: Fix activation before scaling acquisition — every rupee of CAC spent into a leaky funnel is wasted."
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3 — RISK MONITOR
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Risk Monitor":
    st.markdown("## Risk Monitor")
    st.caption(f"{start.strftime('%d %b %Y')} → {end.strftime('%d %b %Y')}")

    avg_npa     = df["npa_rate"].mean()
    avg_tickets = df["support_ticket_volume"].mean()
    avg_cac     = df["cac"].mean()
    avg_ltv     = df["ltv"].mean()

    npa_status = (
        "🔴 CRITICAL" if avg_npa > 0.05 else
        "🟡 ELEVATED" if avg_npa > 0.04 else
        "✅ NORMAL"
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("NPA Rate", avg_npa, delta_pct(df_weekly["npa_rate"]),
                 fmt="pct", inverse=True)
        st.markdown(
            f'<div style="font-size:0.8rem;font-weight:600;margin-top:-8px">{npa_status}</div>',
            unsafe_allow_html=True
        )
    with c2: kpi_card("Avg Support Tickets/Day", avg_tickets,
                      delta_pct(df_weekly["support_ticket_volume"]),
                      fmt="number", inverse=True)
    with c3: kpi_card("Avg CAC", avg_cac,
                      delta_pct(df_weekly["cac"]),
                      fmt="inr", inverse=True)
    with c4: kpi_card("Avg LTV", avg_ltv,
                      delta_pct(df_weekly["ltv"]),
                      fmt="inr")
    with c5: kpi_card("LTV:CAC Ratio", df["ltv_cac_ratio"].mean(),
                      delta_pct(df_weekly["ltv_cac_ratio"]),
                      fmt="ratio")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        fig_npa = line_chart(
            df_weekly, "week_start", "npa_rate",
            "NPA Rate (weekly avg)",
            y_fmt="pct", color=DANGER,
            threshold=0.04, threshold_label="Warn: 4%",  threshold_color=WARNING,
            threshold2=0.05, threshold2_label="Critical: 5%",
        )
        st.plotly_chart(fig_npa, use_container_width=True)

        fig_tickets = line_chart(
            df_weekly, "week_start", "support_ticket_volume",
            "Support Ticket Volume (weekly total)",
            color=WARNING,
            threshold=1050, threshold_label="Warn: 150/day (×7)",
            threshold_color=WARNING,
        )
        st.plotly_chart(fig_tickets, use_container_width=True)

    with col_r:
        # CAC vs LTV dual axis
        fig_cac_ltv = make_subplots(specs=[[{"secondary_y": True}]])
        fig_cac_ltv.add_trace(
            go.Scatter(
                x=df_weekly["week_start"], y=df_weekly["cac"],
                name="CAC", mode="lines",
                line=dict(color=DANGER, width=2.5),
            ),
            secondary_y=False,
        )
        fig_cac_ltv.add_trace(
            go.Scatter(
                x=df_weekly["week_start"], y=df_weekly["ltv"],
                name="LTV", mode="lines",
                line=dict(color=SUCCESS, width=2.5),
            ),
            secondary_y=True,
        )
        fig_cac_ltv.update_layout(
            title=dict(text="CAC vs LTV (₹)", font=dict(size=14, color=BRAND)),
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=10, r=10, t=40, b=10),
            height=280,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis=dict(showgrid=False, tickformat="%b %y"),
        )
        fig_cac_ltv.update_yaxes(title_text="CAC (₹)", tickprefix="₹", secondary_y=False, showgrid=True, gridcolor="#e8e8e8")
        fig_cac_ltv.update_yaxes(title_text="LTV (₹)", tickprefix="₹", secondary_y=True, showgrid=False)
        st.plotly_chart(fig_cac_ltv, use_container_width=True)

        fig_ratio = line_chart(
            df_weekly, "week_start", "ltv_cac_ratio",
            "LTV:CAC Ratio",
            y_fmt="ratio", color=ACCENT,
            threshold=3.0, threshold_label="Min viable: 3×", threshold_color=DANGER,
        )
        st.plotly_chart(fig_ratio, use_container_width=True)

    commentary_box(
        "RISK MONITOR\n\n"
        "• NPA Rate > 4% → review underwriting model performance; tighten bureau score cutoff by 10–15 points. "
        "Pause aggressive acquisition campaigns until NPA stabilises below 3.5%.\n\n"
        "• NPA Rate > 5% → escalate to credit committee immediately. Potential RBI reporting obligation under IRACP norms.\n\n"
        "• Support Tickets > 150/day → run taxonomy analysis on ticket categories. "
        "If >40% are repayment-related, it is a collections ops problem, not a product problem.\n\n"
        "• Sustained ticket spike AND NPA rising together → systemic failure (comms breakdown or product bug in repayment flow); "
        "declare a war-room response.\n\n"
        "• LTV:CAC below 3× → do not approve any new top-of-funnel spend until root cause is identified (LTV erosion vs CAC inflation).\n\n"
        "Key call: NPA is a lagging indicator. Monitor DPD 1–30 (early delinquency) as your real-time leading risk signal."
    )
