"""
Generates static PNG screenshots of all dashboard charts for the README.
Run after generate_data.py:
    python3 generate_screenshots.py
"""

import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ── colours (mirror app.py) ───────────────────────────────────────────────
BRAND   = "#1B4F72"
ACCENT  = "#2E86C1"
WARNING = "#E67E22"
DANGER  = "#C0392B"
SUCCESS = "#1E8449"
MUTED   = "#717D7E"
BG      = "#F4F6F7"

OUT = "images"
os.makedirs(OUT, exist_ok=True)

# ── load & aggregate ──────────────────────────────────────────────────────
df = pd.read_csv("data/lendiq_metrics.csv", parse_dates=["date", "week_start"])

weekly = (
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

LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Arial, sans-serif", color="#1a1a2e"),
    margin=dict(l=60, r=40, t=60, b=50),
    height=380,
    width=900,
)

def add_threshold(fig, y, label, color, dash="dot"):
    fig.add_hline(
        y=y, line_dash=dash, line_color=color, line_width=1.8,
        annotation_text=label,
        annotation_position="top right",
        annotation_font_color=color,
        annotation_font_size=11,
    )

def save(fig, name):
    path = os.path.join(OUT, name)
    fig.write_image(path, scale=2)
    print(f"  ✓ {path}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. OVERVIEW — Loan Disbursal Volume
# ─────────────────────────────────────────────────────────────────────────────
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=weekly["week_start"], y=weekly["loan_disbursal_volume"],
    mode="lines", line=dict(color=BRAND, width=2.5),
    fill="tozeroy", fillcolor="rgba(27,79,114,0.10)",
    name="Disbursal Volume",
))
fig.update_layout(**LAYOUT,
    title=dict(text="Weekly Loan Disbursal Volume (₹)", font=dict(size=16, color=BRAND)),
    xaxis=dict(showgrid=False, tickformat="%b %y", title=""),
    yaxis=dict(showgrid=True, gridcolor="#e8e8e8", tickprefix="₹", tickformat=",.0f", title=""),
    showlegend=False,
)
save(fig, "01_loan_disbursal_volume.png")


# ─────────────────────────────────────────────────────────────────────────────
# 2. OVERVIEW — DAU Trend
# ─────────────────────────────────────────────────────────────────────────────
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=weekly["week_start"], y=weekly["dau"],
    mode="lines", line=dict(color=ACCENT, width=2.5),
    fill="tozeroy", fillcolor="rgba(46,134,193,0.10)",
))
fig.update_layout(**LAYOUT,
    title=dict(text="Daily Active Users — Weekly Avg", font=dict(size=16, color=BRAND)),
    xaxis=dict(showgrid=False, tickformat="%b %y", title=""),
    yaxis=dict(showgrid=True, gridcolor="#e8e8e8", tickformat=",", title=""),
    showlegend=False,
)
save(fig, "02_dau_trend.png")


# ─────────────────────────────────────────────────────────────────────────────
# 3. OVERVIEW — LTV:CAC Ratio
# ─────────────────────────────────────────────────────────────────────────────
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=weekly["week_start"], y=weekly["ltv_cac_ratio"],
    mode="lines", line=dict(color=SUCCESS, width=2.5),
    fill="tozeroy", fillcolor="rgba(30,132,73,0.10)",
))
add_threshold(fig, 3.0, "Min viable: 3×", DANGER)
fig.update_layout(**LAYOUT,
    title=dict(text="LTV:CAC Ratio", font=dict(size=16, color=BRAND)),
    xaxis=dict(showgrid=False, tickformat="%b %y", title=""),
    yaxis=dict(showgrid=True, gridcolor="#e8e8e8", tickformat=".2f", ticksuffix="×", title=""),
    showlegend=False,
)
save(fig, "03_ltv_cac_ratio.png")


# ─────────────────────────────────────────────────────────────────────────────
# 4. FUNNEL — Acquisition Funnel
# ─────────────────────────────────────────────────────────────────────────────
stages = ["Leads", "Applications", "Approvals", "Disbursals"]
values = [df["leads"].sum(), df["applications"].sum(),
          df["approvals"].sum(), df["disbursals"].sum()]

fig = go.Figure(go.Funnel(
    y=stages, x=values,
    textinfo="value+percent previous",
    textfont=dict(size=13),
    marker=dict(color=[BRAND, ACCENT, "#2980B9", "#5DADE2"]),
    connector=dict(line=dict(color="#cccccc", width=1)),
))
funnel_layout = {**LAYOUT, "height": 400, "width": 620}
fig.update_layout(**funnel_layout,
    title=dict(text="Acquisition Funnel — Full Year 2024", font=dict(size=16, color=BRAND)),
)
save(fig, "04_acquisition_funnel.png")


# ─────────────────────────────────────────────────────────────────────────────
# 5. FUNNEL — Activation Rate
# ─────────────────────────────────────────────────────────────────────────────
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=weekly["week_start"], y=weekly["activation_rate"],
    mode="lines", line=dict(color=SUCCESS, width=2.5),
    fill="tozeroy", fillcolor="rgba(30,132,73,0.10)",
))
add_threshold(fig, 0.60, "Min: 60%", WARNING)
fig.update_layout(**LAYOUT,
    title=dict(text="Activation Rate — Weekly Avg", font=dict(size=16, color=BRAND)),
    xaxis=dict(showgrid=False, tickformat="%b %y", title=""),
    yaxis=dict(showgrid=True, gridcolor="#e8e8e8", tickformat=".0%", title=""),
    showlegend=False,
)
save(fig, "05_activation_rate.png")


# ─────────────────────────────────────────────────────────────────────────────
# 6. FUNNEL — Churn Rate
# ─────────────────────────────────────────────────────────────────────────────
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=weekly["week_start"], y=weekly["churn_rate"],
    mode="lines", line=dict(color=WARNING, width=2.5),
    fill="tozeroy", fillcolor="rgba(230,126,34,0.10)",
))
add_threshold(fig, 0.05, "Max: 5%", DANGER)
fig.update_layout(**LAYOUT,
    title=dict(text="Churn Rate — Weekly Avg", font=dict(size=16, color=BRAND)),
    xaxis=dict(showgrid=False, tickformat="%b %y", title=""),
    yaxis=dict(showgrid=True, gridcolor="#e8e8e8", tickformat=".0%", title=""),
    showlegend=False,
)
save(fig, "06_churn_rate.png")


# ─────────────────────────────────────────────────────────────────────────────
# 7. RISK — NPA Rate
# ─────────────────────────────────────────────────────────────────────────────
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=weekly["week_start"], y=weekly["npa_rate"],
    mode="lines", line=dict(color=DANGER, width=2.5),
    fill="tozeroy", fillcolor="rgba(192,57,43,0.10)",
))
add_threshold(fig, 0.04, "Warn: 4%",     WARNING)
add_threshold(fig, 0.05, "Critical: 5%", DANGER)
fig.update_layout(**LAYOUT,
    title=dict(text="NPA Rate — Weekly Avg", font=dict(size=16, color=BRAND)),
    xaxis=dict(showgrid=False, tickformat="%b %y", title=""),
    yaxis=dict(showgrid=True, gridcolor="#e8e8e8", tickformat=".1%", title=""),
    showlegend=False,
)
save(fig, "07_npa_rate.png")


# ─────────────────────────────────────────────────────────────────────────────
# 8. RISK — Support Ticket Volume
# ─────────────────────────────────────────────────────────────────────────────
fig = go.Figure()
fig.add_trace(go.Bar(
    x=weekly["week_start"], y=weekly["support_ticket_volume"],
    marker_color=WARNING, opacity=0.85,
))
add_threshold(fig, 1050, "Warn: 150/day (×7 wk)", DANGER)
fig.update_layout(**LAYOUT,
    title=dict(text="Support Ticket Volume — Weekly Total", font=dict(size=16, color=BRAND)),
    xaxis=dict(showgrid=False, tickformat="%b %y", title=""),
    yaxis=dict(showgrid=True, gridcolor="#e8e8e8", tickformat=",", title=""),
    showlegend=False,
)
save(fig, "08_support_tickets.png")


# ─────────────────────────────────────────────────────────────────────────────
# 9. RISK — CAC vs LTV dual axis
# ─────────────────────────────────────────────────────────────────────────────
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(
    x=weekly["week_start"], y=weekly["cac"],
    name="CAC", mode="lines", line=dict(color=DANGER, width=2.5),
), secondary_y=False)
fig.add_trace(go.Scatter(
    x=weekly["week_start"], y=weekly["ltv"],
    name="LTV", mode="lines", line=dict(color=SUCCESS, width=2.5),
), secondary_y=True)
fig.update_layout(**LAYOUT,
    title=dict(text="CAC vs LTV (₹) — Weekly Avg", font=dict(size=16, color=BRAND)),
    xaxis=dict(showgrid=False, tickformat="%b %y"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
)
fig.update_yaxes(title_text="CAC (₹)", tickprefix="₹", tickformat=",",
                 showgrid=True, gridcolor="#e8e8e8", secondary_y=False)
fig.update_yaxes(title_text="LTV (₹)", tickprefix="₹", tickformat=",",
                 showgrid=False, secondary_y=True)
save(fig, "09_cac_vs_ltv.png")


print(f"\nAll screenshots saved to ./{OUT}/")
