# app.py
import streamlit as st
from agent.tools import FinanceData
from agent.planner import classify
from matplotlib import pyplot as plt

st.set_page_config(page_title="CFO Copilot (mini)", layout="wide")

st.title("CFO Copilot — Mini FP&A Assistant")

with st.sidebar:
    st.header("Upload Excel File")
    excel_file = st.file_uploader("Upload data.xlsx", type=["xlsx"])
    if not excel_file:
        st.stop()

# load FinanceData from Excel
try:
    fd = FinanceData(excel_file)
    st.sidebar.success("Data loaded")
except Exception as e:
    st.sidebar.error(f"Failed to load data: {e}")
    st.stop()

st.markdown("Ask a finance question (examples):")
st.info(
    "- What was June 2025 revenue vs budget in USD?\n"
    "- Show Gross Margin % trend for the last 3 months.\n"
    "- Break down Opex by category for June 2025.\n"
    "- What is our cash runway right now?"
)

q = st.text_input("Ask CFO Copilot", value="", key="question_input")

if st.button("Ask") and q.strip():
    intent, params = classify(q)
    st.write(f"**Intent:** {intent}")

    if intent == 'revenue_vs_budget':
        month = params.get('month') or st.text_input("Month (fallback)", value="")
        if not month:
            st.error("Please specify a month (e.g., 'June 2025' or '2025-06').")
        else:
            res = fd.revenue_vs_budget(month)
            st.metric(
                label=f"Revenue Actual (USD) — {res['month'].strftime('%Y-%m')}",
                value=f"${res['actual_usd']:,.0f}",
                delta=f"${res['actual_usd'] - res['budget_usd']:,.0f}"
            )
            st.write(f"Budget (USD): ${res['budget_usd']:,.0f}")
            buf = fd.plot_revenue_vs_budget(month)
            st.image(buf)

    elif intent == 'gross_margin_trend':
        months = params.get('months', 3)
        end_month = params.get('end_month', None)
        gm_df = fd.gross_margin_trend(months=months, end_month=end_month)
        st.table(
            gm_df.assign(
                gross_margin_pct=lambda df: df['gross_margin_pct'].apply(
                    lambda x: f"{(x*100):.1f}%" if x is not None else "N/A"
                )
            )
        )
        buf = fd.plot_gross_margin(gm_df)
        st.image(buf)

    elif intent == 'opex_breakdown':
        month = params.get('month') or st.text_input("Month (fallback)", value="")
        if not month:
            st.error("Please specify a month.")
        else:
            df = fd.opex_breakdown(month)
            st.dataframe(df)
            fig, ax = plt.subplots()
            top = df.head(10)
            ax.bar(top['account'], top['amount_usd'])
            ax.set_xticklabels(top['account'], rotation=45, ha='right')
            ax.set_title(f"Opex breakdown — {month}")
            st.pyplot(fig)

    elif intent == 'cash_runway':
        as_of = params.get('as_of')
        res = fd.cash_runway_months(as_of_month=as_of)
        runway = res['runway_months']
        if runway == float('inf'):
            st.success(
                f"Runway: unlimited / not burning cash "
                f"(current cash ${res['current_cash_usd']:,.0f})"
            )
        else:
            st.metric("Cash runway (months)", f"{runway:.1f}")
            st.write(f"Current cash: ${res['current_cash_usd']:,.0f}")
            st.write(f"Avg monthly burn (3m): ${res['avg_monthly_burn_usd']:,.0f}")

    elif intent == 'ebitda_proxy':
        month = params.get('month') or st.text_input("Month (fallback)", value="")
        if not month:
            st.error("Please specify a month.")
        else:
            r = fd.ebitda_proxy(month)
            st.metric("EBITDA (proxy)", f"${r['ebitda_usd']:,.0f}")
            st.write(
                f"Revenue: ${r['revenue_usd']:,.0f}, "
                f"COGS: ${r['cogs_usd']:,.0f}, "
                f"Opex: ${r['opex_usd']:,.0f}"
            )

    else:
        st.warning("Sorry — I couldn't classify the question. Try phrasing it like the examples.")