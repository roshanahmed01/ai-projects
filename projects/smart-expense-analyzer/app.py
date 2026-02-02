import os
import streamlit as st

# Import functions from your existing engine file (main.py)
from main import (
    load_all_monthly_csvs,
    split_income_and_expenses,
    calculate_total_spent,
    calculate_category_totals,
    calculate_monthly_totals,
    calculate_monthly_category_totals,
    estimate_baseline_nonrent_spending,
    rent_affordability_report,
)

# ----------------------------
# Streamlit Page Setup
# ----------------------------
st.set_page_config(page_title="Smart Expense Analyzer", layout="wide")
st.title("Smart Expense Analyzer")
st.caption("Real spending + income analysis with rent affordability projections.")

# ----------------------------
# Sidebar Controls
# ----------------------------
st.sidebar.header("Settings")

data_folder = st.sidebar.text_input("Data folder", value="data")

use_income_override = st.sidebar.checkbox("Override monthly income", value=True)
income_override_value = st.sidebar.number_input(
    "Monthly income override ($)",
    min_value=0.0,
    value=3300.0,
    step=50.0,
    disabled=not use_income_override,
)

rent_amount = st.sidebar.number_input("Monthly rent ($)", min_value=0.0, value=1400.0, step=50.0)
rent_start_month = st.sidebar.text_input("Rent start month (YYYY-MM)", value="2026-02")
rent_start_day = st.sidebar.number_input("Rent start day", min_value=1, max_value=31, value=14, step=1)

months_back = st.sidebar.slider("Months of history to estimate baseline", min_value=1, max_value=6, value=2)

st.sidebar.divider()
st.sidebar.header("Projections")
proj_month_1 = st.sidebar.text_input("Projection month 1 (YYYY-MM)", value="2026-02")
proj_month_2 = st.sidebar.text_input("Projection month 2 (YYYY-MM)", value="2026-03")

# ----------------------------
# Load Data
# ----------------------------
try:
    rows, loaded_files = load_all_monthly_csvs(data_folder)
except Exception as e:
    st.error(f"Could not load monthly CSVs from '{data_folder}'. Error: {e}")
    st.stop()

income_rows, expense_rows = split_income_and_expenses(rows)

# Basic sanity check
st.write(f"**Loaded files:** {', '.join(loaded_files)}")
st.write(f"**Rows loaded:** {len(rows)} | **Income rows:** {len(income_rows)} | **Expense rows:** {len(expense_rows)}")

if len(expense_rows) == 0:
    st.error("No expense rows found. Make sure your CSVs include a 'type' column with 'expense' rows.")
    st.stop()

# ----------------------------
# Core Metrics
# ----------------------------
total_income = calculate_total_spent(income_rows)
total_expenses_raw = calculate_total_spent(expense_rows)  # negative
total_expenses = abs(total_expenses_raw)
net_cash_flow = total_income + total_expenses_raw

col1, col2, col3 = st.columns(3)
col1.metric("Total income", f"${total_income:,.2f}")
col2.metric("Total expenses", f"${total_expenses:,.2f}")
col3.metric("Net cash flow", f"${net_cash_flow:,.2f}")

# ----------------------------
# Breakdown Tables
# ----------------------------
category_totals = calculate_category_totals(expense_rows)  # negative values
monthly_expense_totals = calculate_monthly_totals(expense_rows)  # negative values
monthly_income_totals = calculate_monthly_totals(income_rows)  # positive
monthly_category_totals = calculate_monthly_category_totals(expense_rows)  # negative

# Make tables friendlier (convert expense totals to positive for display)
category_display = {k: abs(v) for k, v in category_totals.items()}
monthly_expense_display = {k: abs(v) for k, v in monthly_expense_totals.items()}

left, right = st.columns(2)

with left:
    st.subheader("Spending by category")
    st.dataframe(
        [{"Category": k, "Spent": v} for k, v in sorted(category_display.items(), key=lambda x: -x[1])]
    )

with right:
    st.subheader("Expenses by month")
    st.dataframe(
        [{"Month": k, "Spent": v} for k, v in sorted(monthly_expense_display.items())]
    )

st.subheader("Income by month")
st.dataframe(
    [{"Month": k, "Income": v} for k, v in sorted(monthly_income_totals.items())]
)

# ----------------------------
# Rent Affordability
# ----------------------------
st.header("Rent affordability projections")

baseline_nonrent, baseline_months = estimate_baseline_nonrent_spending(monthly_category_totals, months_back=months_back)

st.write(
    f"Baseline non-rent spending estimate: **${baseline_nonrent:,.2f}/month** "
    f"(based on months: {', '.join(baseline_months) if baseline_months else 'N/A'})"
)

# We pass paycheck-derived values as placeholders; rent_affordability_report uses them
# but your engine might override income in its own file.
# In the UI, we'll apply override here explicitly for clarity.

def affordability_with_ui_override(target_month: str):
    # Start with engine report
    report = rent_affordability_report(
        target_month=target_month,
        avg_paycheck_amount=0.0,
        avg_paychecks_per_month=0.0,
        baseline_nonrent_spend=baseline_nonrent,
    )

    # Apply UI override for income (single monthly income)
    if use_income_override:
        report["projected_income"] = float(income_override_value)

    # Apply rent settings from UI (full vs prorated handled here)
    # If engine already handles rent, we overwrite to match UI settings.

    # Prorate if start month
    if target_month == rent_start_month:
        # prorated amount from start_day to end of month
        import calendar as _cal
        year, month = map(int, target_month.split("-"))
        days_in_month = _cal.monthrange(year, month)[1]
        days_covered = days_in_month - int(rent_start_day) + 1
        daily_rate = float(rent_amount) / days_in_month
        projected_rent = daily_rate * days_covered
    elif target_month > rent_start_month:
        projected_rent = float(rent_amount)
    else:
        projected_rent = 0.0

    report["projected_rent"] = projected_rent
    report["projected_total_spend"] = report["baseline_nonrent_spend"] + projected_rent
    report["projected_net"] = report["projected_income"] - report["projected_total_spend"]
    report["rent_pct_income"] = (projected_rent / report["projected_income"] * 100) if report["projected_income"] > 0 else 0
    report["spend_pct_income"] = (report["projected_total_spend"] / report["projected_income"] * 100) if report["projected_income"] > 0 else 0

    return report

rep1 = affordability_with_ui_override(proj_month_1)
rep2 = affordability_with_ui_override(proj_month_2)

def status_label(rep):
    # Simple, interpretable rules of thumb
    if rep["projected_income"] <= 0:
        return "❌ Not affordable (no income)"
    if rep["projected_net"] < 0:
        return "❌ Not affordable (negative net)"
    if rep["rent_pct_income"] > 40 or rep["spend_pct_income"] > 85:
        return "⚠️ Tight"
    return "✅ Comfortable"

c1, c2 = st.columns(2)

with c1:
    st.subheader(f"{rep1['month']} — {status_label(rep1)}")
    st.json(rep1)

with c2:
    st.subheader(f"{rep2['month']} — {status_label(rep2)}")
    st.json(rep2)
