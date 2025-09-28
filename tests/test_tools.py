# tests/test_tools.py
import os
from agent.tools import FinanceData

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
EXCEL_FILE = os.path.join(FIXTURES_DIR, 'data.xlsx')

def test_revenue_vs_budget():
    fd = FinanceData(EXCEL_FILE)
    res = fd.revenue_vs_budget("2025-06")
    # check the values match fixture (adjust numbers to match your sheet)
    assert abs(res['actual_usd'] - 120000) < 1
    assert abs(res['budget_usd'] - 110000) < 1

def test_gross_margin_trend():
    fd = FinanceData(EXCEL_FILE)
    df = fd.gross_margin_trend(months=3, end_month="2025-06")
    assert len(df) == 3
    june_row = df[df['date'].dt.month == 6].iloc[0]
    # (120k - 48k)/120k = 0.6
    assert round(june_row['gross_margin_pct'], 2) == 0.6