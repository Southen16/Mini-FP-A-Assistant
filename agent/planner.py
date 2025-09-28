# agent/planner.py
import re
from typing import Tuple, Dict

def classify(question: str) -> Tuple[str, Dict]:
    """
    Very small regex-based intent classifier for finance-related questions.
    Returns a tuple: (intent, parameters)
    """
    q = question.lower().strip()

    # Match "June 2025", "Jun 2025", "2025-06", "2025-06-01"
    month_match = re.search(r'([a-zA-Z]{3,9} \d{4}|\d{4}-\d{2}(?:-\d{2})?)', q)
    month = month_match.group(0) if month_match else None

    # Revenue vs Budget
    if "revenue" in q and "budget" in q:
        return "revenue_vs_budget", {"month": month}

    # Gross Margin Trend (with optional "last N months")
    if "gross margin" in q or "gross margin %" in q or "gross margin percent" in q:
        m = re.search(r"last (\d+) months", q)
        months = int(m.group(1)) if m else 3
        return "gross_margin_trend", {"months": months, "end_month": month}

    # Operating Expenses
    if "opex" in q or "operating expense" in q:
        return "opex_breakdown", {"month": month}

    # Cash Runway
    if "cash runway" in q or "runway" in q:
        return "cash_runway", {"as_of": month}

    # EBITDA / Earnings
    if "ebitda" in q or "earnings" in q or "operating profit" in q:
        return "ebitda_proxy", {"month": month}

    # Default fallback
    return "unknown", {}