# agent/tools.py
import pandas as pd
import numpy as np
from dateutil import parser
from typing import Optional, Dict
import matplotlib.pyplot as plt
import io


def _month_str_to_ts(m: str) -> pd.Timestamp:
    """
    Parse flexible month strings like:
    - "June 2025", "Jun 2025"
    - "2025-06", "2025-06-01"
    Returns first-of-month Timestamp.
    """
    dt = parser.parse(m)
    return pd.Timestamp(year=dt.year, month=dt.month, day=1)


class FinanceData:
    """
    Mini FP&A data handler:
    - Loads actuals, budget, FX, and cash from a single Excel file.
    - Provides core finance analysis methods (revenue vs budget, GM trend, opex breakdown, EBITDA, cash runway).
    """

    def __init__(self, excel_file: str):
        xls = pd.ExcelFile(excel_file)

        # Load actuals
        self.actuals = pd.read_excel(xls, "actuals", parse_dates=["month"])
        self.actuals.rename(columns={"month": "date", "account_category": "category"}, inplace=True)

        # Load budget
        self.budget = pd.read_excel(xls, "budget", parse_dates=["month"])
        self.budget.rename(columns={"month": "date", "account_category": "category"}, inplace=True)

        # Load cash
        self.cash = pd.read_excel(xls, "cash", parse_dates=["month"])
        self.cash.rename(columns={"month": "date", "cash_usd": "cash_balance"}, inplace=True)

        # Load FX
        self.fx = pd.read_excel(xls, "fx", parse_dates=["month"])
        self.fx.rename(columns={"month": "date", "rate_to_usd": "usd_rate"}, inplace=True)

        # Normalize dates to first-of-month
        for df in (self.actuals, self.budget, self.cash, self.fx):
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()

        # Ensure numeric values
        self.actuals["amount"] = pd.to_numeric(self.actuals["amount"], errors="coerce").fillna(0)
        self.budget["amount"] = pd.to_numeric(self.budget["amount"], errors="coerce").fillna(0)
        if "cash_balance" in self.cash.columns:
            self.cash["cash_balance"] = pd.to_numeric(self.cash["cash_balance"], errors="coerce").fillna(0)

        # Build FX map (date x currency -> USD rate), with ffill/bfill
        self.fx = self.fx.sort_values("date")
        self.fx_map = self.fx.pivot(index="date", columns="currency", values="usd_rate").sort_index().ffill().bfill()

    def _to_usd(self, df: pd.DataFrame, amount_col="amount", currency_col="currency") -> pd.DataFrame:
        """Convert amounts to USD using FX map (defaults to 1.0 if missing)."""
        tmp = df.copy()
        tmp["date"] = pd.to_datetime(tmp["date"]).dt.to_period("M").dt.to_timestamp()

        def lookup_rate(row):
            try:
                return self.fx_map.loc[row["date"], row[currency_col]]
            except Exception:
                if str(row.get(currency_col, "")).upper() == "USD":
                    return 1.0
                return 1.0

        tmp["usd_rate"] = tmp.apply(lookup_rate, axis=1)
        tmp["amount_usd"] = tmp[amount_col] * tmp["usd_rate"]
        return tmp

    # ---------------- Core Analysis Methods ---------------- #

    def revenue_vs_budget(self, month: str, entity: Optional[str] = None) -> Dict:
        """Return revenue actual vs budget (USD) for a given month."""
        ts = _month_str_to_ts(month)
        a = self.actuals[(self.actuals["date"] == ts) & (self.actuals["category"].str.lower() == "revenue")]
        b = self.budget[(self.budget["date"] == ts) & (self.budget["category"].str.lower() == "revenue")]
        if entity:
            a = a[a["entity"] == entity]
            b = b[b["entity"] == entity]
        a_usd = self._to_usd(a)["amount_usd"].sum()
        b_usd = self._to_usd(b)["amount_usd"].sum()
        return {"month": ts, "actual_usd": float(a_usd), "budget_usd": float(b_usd)}

    def gross_margin_trend(self, months: int = 3, end_month: Optional[str] = None) -> pd.DataFrame:
        """Return gross margin % for the last `months` ending at end_month (or latest available)."""
        end_ts = _month_str_to_ts(end_month) if end_month else self.actuals["date"].max()
        months_list = pd.period_range(end=end_ts.to_period("M"), periods=months, freq="M").to_timestamp()

        rows = []
        for ts in months_list:
            rev = self.actuals[(self.actuals["date"] == ts) & (self.actuals["category"].str.lower() == "revenue")]
            cogs = self.actuals[(self.actuals["date"] == ts) & (self.actuals["category"].str.lower() == "cogs")]
            rev_usd = self._to_usd(rev)["amount_usd"].sum()
            cogs_usd = self._to_usd(cogs)["amount_usd"].sum()
            gm = None if rev_usd == 0 else float((rev_usd - cogs_usd) / rev_usd)
            rows.append({
                "date": ts,
                "revenue_usd": float(rev_usd),
                "cogs_usd": float(cogs_usd),
                "gross_margin_pct": gm,
            })
        return pd.DataFrame(rows)

    def opex_breakdown(self, month: str, entity: Optional[str] = None) -> pd.DataFrame:
        """Return opex breakdown by account for a given month."""
        ts = _month_str_to_ts(month)
        opex = self.actuals[
            (self.actuals["date"] == ts) & (self.actuals["category"].str.lower().str.contains("opex|operating"))
        ]
        if entity:
            opex = opex[opex["entity"] == entity]
        o_usd = self._to_usd(opex)
        return (
            o_usd.groupby("category")["amount_usd"]
            .sum()
            .reset_index()
            .rename(columns={"category": "account"})
            .sort_values("amount_usd", ascending=False)
        )

    def ebitda_proxy(self, month: str, entity: Optional[str] = None) -> Dict:
        """Compute EBITDA proxy = Revenue – COGS – Opex (USD)."""
        ts = _month_str_to_ts(month)
        rev = self.actuals[(self.actuals["date"] == ts) & (self.actuals["category"].str.lower() == "revenue")]
        cogs = self.actuals[(self.actuals["date"] == ts) & (self.actuals["category"].str.lower() == "cogs")]
        opex = self.actuals[(self.actuals["date"] == ts) & (self.actuals["category"].str.lower().str.contains("opex|operating"))]
        if entity:
            rev, cogs, opex = rev[rev["entity"] == entity], cogs[cogs["entity"] == entity], opex[opex["entity"] == entity]

        rev_usd = self._to_usd(rev)["amount_usd"].sum()
        cogs_usd = self._to_usd(cogs)["amount_usd"].sum()
        opex_usd = self._to_usd(opex)["amount_usd"].sum()
        ebitda = rev_usd - cogs_usd - opex_usd
        return {
            "month": ts,
            "ebitda_usd": float(ebitda),
            "revenue_usd": float(rev_usd),
            "cogs_usd": float(cogs_usd),
            "opex_usd": float(opex_usd),
        }

    def cash_runway_months(self, as_of_month: Optional[str] = None, entity: Optional[str] = None) -> Dict:
        """Estimate cash runway (months) based on last 3 months avg net burn."""
        ts = _month_str_to_ts(as_of_month) if as_of_month else self.cash["date"].max()
        months = pd.period_range(end=ts.to_period("M"), periods=3, freq="M").to_timestamp()

        c = self.cash if not entity else self.cash[self.cash["entity"] == entity]
        c_usd = self._to_usd(c, amount_col="cash_balance", currency_col="currency")

        # Reindex to ensure all 3 months exist
        cs = c_usd.set_index("date").reindex(months).reset_index()
        cs["cash_balance_usd"] = cs["cash_balance"] * cs["usd_rate"]
        cs["cash_balance_usd"] = cs["cash_balance_usd"].ffill().bfill()

        # Compute monthly net burn
        cs["prev"] = cs["cash_balance_usd"].shift(1)
        cs["net_burn"] = cs["prev"] - cs["cash_balance_usd"]

        avg_burn = cs["net_burn"].dropna().mean()
        current_cash = cs["cash_balance_usd"].iloc[-1]

        runway = float("inf") if avg_burn <= 0 or np.isnan(avg_burn) else float(current_cash / avg_burn)

        return {
            "as_of": ts,
            "current_cash_usd": float(current_cash),
            "avg_monthly_burn_usd": float(avg_burn) if not np.isnan(avg_burn) else 0.0,
            "runway_months": runway,
        }

    # ---------------- Chart Helpers ---------------- #

    def plot_gross_margin(self, gm_df: pd.DataFrame) -> io.BytesIO:
        """Plot gross margin % trend and return image buffer."""
        fig, ax = plt.subplots()
        ax.plot(gm_df["date"].dt.strftime("%Y-%m"), gm_df["gross_margin_pct"] * 100, marker="o")
        ax.set_title("Gross Margin %")
        ax.set_ylabel("Gross margin (%)")
        ax.set_xlabel("Month")
        ax.grid(True)
        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        plt.close(fig)
        return buf

    def plot_revenue_vs_budget(self, month: str) -> io.BytesIO:
        """Plot actual vs budget revenue for a given month."""
        r = self.revenue_vs_budget(month)
        labels = ["Actual", "Budget"]
        values = [r["actual_usd"], r["budget_usd"]]
        fig, ax = plt.subplots()
        ax.bar(labels, values, color=["#4CAF50", "#2196F3"])
        ax.set_title(f"Revenue vs Budget ({r['month'].strftime('%Y-%m')})")
        ax.set_ylabel("USD")
        for i, v in enumerate(values):
            ax.text(i, v, f"${v:,.0f}", ha="center", va="bottom")
        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        plt.close(fig)
        return buf