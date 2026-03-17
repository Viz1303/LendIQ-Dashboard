"""
LendIQ Synthetic Data Generator
Produces 12 months of realistic daily metrics for a B2B SaaS lending platform (India).
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
import os

np.random.seed(42)

START = date(2024, 1, 1)
END   = date(2024, 12, 31)
N     = (END - START).days + 1

dates = [START + timedelta(days=i) for i in range(N)]
df = pd.DataFrame({"date": dates})

df["month"]   = df["date"].apply(lambda d: d.month)
df["dow"]     = df["date"].apply(lambda d: d.weekday())          # 0=Mon
df["day_num"] = range(N)

# ── helpers ────────────────────────────────────────────────────────────────
growth  = 1 + 0.025 * df["day_num"] / 30                        # ~2.5% MoM lift

seasonal = {1:0.82, 2:0.88, 3:1.00, 4:1.06, 5:1.12, 6:1.18,
            7:1.10, 8:1.05, 9:1.00, 10:0.96, 11:1.02, 12:0.90}
seas = df["month"].map(seasonal).values

wknd = np.where(df["dow"].isin([5, 6]), 0.38, 1.0)             # weekends quiet

# ── Funnel ─────────────────────────────────────────────────────────────────
df["leads"] = np.maximum(
    10,
    (180 * growth * seas * wknd * np.random.lognormal(0, 0.18, N)).astype(int)
)
df["applications"] = (df["leads"] * np.random.uniform(0.54, 0.68, N)).astype(int)
df["approvals"]    = (df["applications"] * np.random.uniform(0.60, 0.73, N)).astype(int)
df["disbursals"]   = (df["approvals"]    * np.random.uniform(0.76, 0.89, N)).astype(int)

# ── North Star: Loan Disbursal Volume (₹) ──────────────────────────────────
# avg ticket ₹2.2L; scales with disbursals + noise
avg_ticket = 220_000
df["loan_disbursal_volume"] = (
    df["disbursals"] * avg_ticket
    * np.random.lognormal(0, 0.12, N)
).astype(int)

# ── Activation Rate ────────────────────────────────────────────────────────
# starts ~62%, slowly improves through the year as onboarding is refined
activation_base = 0.62 + 0.0012 * df["day_num"] / 30
df["activation_rate"] = np.clip(
    activation_base + np.random.normal(0, 0.03, N), 0.45, 0.82
).round(4)

# ── Churn Rate ─────────────────────────────────────────────────────────────
# slightly elevated mid-year (competition) then improves
churn_base = 0.052 + 0.004 * np.abs(df["month"].values - 6) / 6
df["churn_rate"] = np.clip(
    churn_base + np.random.normal(0, 0.006, N), 0.025, 0.10
).round(4)

# ── CAC (₹) ────────────────────────────────────────────────────────────────
# starts high, improves through the year as channel mix matures
cac_base = 4200 - 12 * df["day_num"] / 30
df["cac"] = np.clip(
    cac_base + np.random.normal(0, 350, N), 2200, 5800
).astype(int)

# ── LTV (₹) ────────────────────────────────────────────────────────────────
df["ltv"] = np.clip(
    22000 * seas * growth + np.random.normal(0, 2000, N), 14000, 40000
).astype(int)

# ── LTV:CAC Ratio ──────────────────────────────────────────────────────────
df["ltv_cac_ratio"] = (df["ltv"] / df["cac"]).round(2)

# ── DAU ────────────────────────────────────────────────────────────────────
df["dau"] = np.maximum(
    50,
    (1400 * growth * seas * wknd * np.random.lognormal(0, 0.10, N)).astype(int)
)

# ── NPA Rate ───────────────────────────────────────────────────────────────
# starts ~2.4%, portfolio aging lifts it, Q3 spike, partial Q4 recovery
npa_base = 0.024 + 0.0004 * df["day_num"] / 30
npa_drift = np.where(df["month"].isin([7, 8, 9]),  0.009,
            np.where(df["month"].isin([10, 11, 12]), 0.004, 0.0))
df["npa_rate"] = np.clip(
    npa_base + npa_drift + np.random.normal(0, 0.0025, N), 0.015, 0.070
).round(4)

# ── Support Ticket Volume ──────────────────────────────────────────────────
# correlated with NPA (more defaults → more borrower complaints)
df["support_ticket_volume"] = np.maximum(
    20,
    (90 * seas * (1 + 2.5 * df["npa_rate"])
     * np.random.lognormal(0, 0.20, N)).astype(int)
)

# ── Funnel Conversion ──────────────────────────────────────────────────────
df["funnel_conversion"] = (df["disbursals"] / df["leads"].replace(0, np.nan)).round(4)

# ── Week / Month labels (handy for Tableau) ────────────────────────────────
df["date"]        = pd.to_datetime(df["date"])
df["week_start"]  = df["date"] - pd.to_timedelta(df["date"].dt.dayofweek, unit="D")
df["month_label"] = df["date"].dt.strftime("%b %Y")

# Drop helper columns
df.drop(columns=["month", "dow", "day_num"], inplace=True)

os.makedirs("data", exist_ok=True)
out = "data/lendiq_metrics.csv"
df.to_csv(out, index=False)

print(f"✓ Wrote {len(df)} rows → {out}")
print("\nSample stats:")
print(df[["loan_disbursal_volume", "npa_rate", "activation_rate",
          "churn_rate", "cac", "ltv", "ltv_cac_ratio"]].describe().round(3))
