# Smart Expense Analyzer
# Reads expenses from CSV and outputs summaries, trends, predictions, insights, and budget alerts.

import csv
import os
import calendar
from datetime import datetime

# ----------------------------
# Budget Configuration
# ----------------------------
DEFAULT_BUDGETS = {
    "Food": 400,
    "Transport": 250,
    "Entertainment": 200,
}

# Month-specific overrides (full-month budgets)
MONTHLY_BUDGET_OVERRIDES = {
    "2026-03": {"Rent": 1400},
    "2026-04": {"Rent": 1400},
    # Add more months as needed
}

# ----------------------------
# Income Override (Optional)
# ----------------------------
# Set to a number (e.g., 3300.00) to override paycheck-based projected monthly income.
# Set to None to use paycheck history.
INCOME_OVERRIDE_MONTHLY = 3300.00


# Special case: rent starts mid-month (prorated)
RENT_START = {
    "month": "2026-02",
    "start_day": 14,
    "full_month_amount": 1400,
}

# ----------------------------
# Rent Settings
# ----------------------------
RENT_AMOUNT = 1400.00
RENT_START_MONTH = "2026-02"
RENT_START_DAY = 14




# ----------------------------
# Data Loading
# ----------------------------
def load_expenses_from_csv(file_path):
    rows = []

    with open(file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            rows.append(
                {
                    "date": row["date"].strip(),
                    "description": row.get("description", "").strip(),
                    "amount": float(row["amount"]),
                    "type": row.get("type", "").strip().lower(),      # "income" or "expense"
                    "category": row.get("category", "").strip(),
                }
            )

    return rows


def load_all_monthly_csvs(data_folder="data"):
    all_rows = []

    # Grab files like 2025-11.csv, 2025-12.csv, 2026-02.csv
    monthly_files = sorted(
        f for f in os.listdir(data_folder)
        if f.endswith(".csv") and f[:4].isdigit() and f[4] == "-" and f[5:7].isdigit()
    )

    if not monthly_files:
        raise FileNotFoundError(
            f"No monthly CSV files found in '{data_folder}'. "
            "Expected files like '2025-11.csv'."
        )

    for filename in monthly_files:
        path = os.path.join(data_folder, filename)
        rows = load_expenses_from_csv(path)
        all_rows.extend(rows)

    return all_rows, monthly_files


# ----------------------------
# Core Calculations
# ----------------------------
def calculate_total_spent(expenses):
    total = 0
    for expense in expenses:
        total += expense["amount"]
    return total


def calculate_category_totals(expenses):
    category_totals = {}

    for expense in expenses:
        category = expense["category"]
        amount = expense["amount"]

        if category in category_totals:
            category_totals[category] += amount
        else:
            category_totals[category] = amount

    return category_totals


def calculate_monthly_totals(expenses):
    monthly_totals = {}

    for expense in expenses:
        date_obj = datetime.strptime(expense["date"], "%Y-%m-%d")
        month_key = date_obj.strftime("%Y-%m")

        if month_key in monthly_totals:
            monthly_totals[month_key] += expense["amount"]
        else:
            monthly_totals[month_key] = expense["amount"]

    return monthly_totals


def calculate_monthly_category_totals(expenses):
    monthly_category_totals = {}

    for expense in expenses:
        date_obj = datetime.strptime(expense["date"], "%Y-%m-%d")
        month_key = date_obj.strftime("%Y-%m")

        category = expense["category"]
        amount = expense["amount"]

        if month_key not in monthly_category_totals:
            monthly_category_totals[month_key] = {}

        if category in monthly_category_totals[month_key]:
            monthly_category_totals[month_key][category] += amount
        else:
            monthly_category_totals[month_key][category] = amount

    return monthly_category_totals


def calculate_month_over_month_change(monthly_totals):
    months = sorted(monthly_totals.keys())

    if len(months) < 2:
        return None

    changes = []

    for i in range(1, len(months)):
        previous_month = months[i - 1]
        current_month = months[i]

        previous_amount = monthly_totals[previous_month]
        current_amount = monthly_totals[current_month]

        change = current_amount - previous_amount
        percent_change = (change / previous_amount) * 100 if previous_amount != 0 else 0

        changes.append(
            {
                "from": previous_month,
                "to": current_month,
                "change": change,
                "percent_change": percent_change,
            }
        )

    return changes


# ----------------------------
# Prediction + Evaluation
# ----------------------------
def predict_monthly_spending(expenses, target_month):
    total_spent_so_far = 0
    days_with_data = set()

    for expense in expenses:
        date_obj = datetime.strptime(expense["date"], "%Y-%m-%d")
        month_key = date_obj.strftime("%Y-%m")

        if month_key == target_month:
            total_spent_so_far += expense["amount"]
            days_with_data.add(date_obj.day)

    if not days_with_data:
        return None

    latest_day = max(days_with_data)
    average_daily_spend = total_spent_so_far / latest_day

    year, month = map(int, target_month.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]

    predicted_total = average_daily_spend * days_in_month
    return total_spent_so_far, predicted_total


def evaluate_prediction(predicted, actual):
    error = predicted - actual
    percent_error = (error / actual) * 100 if actual != 0 else 0
    return error, percent_error


def predict_mid_month(expenses, target_month, cutoff_day):
    spent_until_cutoff = 0

    for expense in expenses:
        date_obj = datetime.strptime(expense["date"], "%Y-%m-%d")
        month_key = date_obj.strftime("%Y-%m")

        if month_key == target_month and date_obj.day <= cutoff_day:
            spent_until_cutoff += expense["amount"]

    if spent_until_cutoff == 0:
        return None

    year, month = map(int, target_month.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]

    average_daily_spend = spent_until_cutoff / cutoff_day
    predicted_total = average_daily_spend * days_in_month

    return predicted_total


# ----------------------------
# Insights + Budgets
# ----------------------------
def generate_insights(monthly_totals, monthly_category_totals, current_month, predicted_total=None):
    insights = []
    months = sorted(monthly_totals.keys())

    if len(months) >= 2:
        prev_month = months[-2]
        curr_total = monthly_totals[current_month]
        prev_total = monthly_totals[prev_month]

        delta = curr_total - prev_total
        pct = (delta / prev_total) * 100 if prev_total != 0 else 0

        direction = "up" if delta > 0 else "down" if delta < 0 else "flat"
        insights.append(
            f"Overall spending is {direction} vs last month ({prev_month}): "
            f"{delta:+.2f} ({pct:+.2f}%)."
        )

        prev_cats = monthly_category_totals.get(prev_month, {})
        curr_cats = monthly_category_totals.get(current_month, {})
        all_categories = set(prev_cats.keys()) | set(curr_cats.keys())

        if all_categories:
            biggest_cat = None
            biggest_delta = 0

            for cat in all_categories:
                d = curr_cats.get(cat, 0) - prev_cats.get(cat, 0)
                if abs(d) > abs(biggest_delta):
                    biggest_delta = d
                    biggest_cat = cat

            if biggest_cat is not None:
                change_word = (
                    "increased"
                    if biggest_delta > 0
                    else "decreased"
                    if biggest_delta < 0
                    else "stayed the same"
                )
                insights.append(
                    f"Biggest category change: {biggest_cat} {change_word} by {biggest_delta:+.2f} vs {prev_month}."
                )

    if predicted_total is not None:
        actual_so_far = monthly_totals[current_month]
        remaining = predicted_total - actual_so_far
        insights.append(
            f"Projection: you’ve spent {actual_so_far:.2f} so far in {current_month}. "
            f"At this pace, you’re projected to finish around {predicted_total:.2f} "
            f"({remaining:+.2f} remaining)."
        )

    return insights


def evaluate_budgets(monthly_category_totals, current_month, budgets):
    alerts = []
    month_data = monthly_category_totals.get(current_month, {})

    for category, budget in budgets.items():
        spent = month_data.get(category, 0)
        pct_used = (spent / budget) * 100 if budget > 0 else 0

        if pct_used >= 100:
            alerts.append(
                f"ALERT: {category} is OVER budget "
                f"({spent:.2f} / {budget:.2f}, {pct_used:.1f}%)."
            )
        elif pct_used >= 80:
            alerts.append(
                f"Warning: {category} is at {pct_used:.1f}% of budget "
                f"({spent:.2f} / {budget:.2f})."
            )

    return alerts

def get_budgets_for_month(month_key):
    budgets = DEFAULT_BUDGETS.copy()

    # Apply standard month overrides
    budgets.update(MONTHLY_BUDGET_OVERRIDES.get(month_key, {}))

    # Apply prorated rent for the rent-start month
    if month_key == RENT_START["month"]:
        budgets["Rent"] = prorated_rent_budget(
            month_key,
            RENT_START["start_day"],
            RENT_START["full_month_amount"],
        )

    return budgets


def prorated_rent_budget(month_key, start_day, full_month_amount):
    year, month = map(int, month_key.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]

    # Rent applies from start_day through end of month (inclusive)
    days_covered = days_in_month - start_day + 1
    daily_rate = full_month_amount / days_in_month

    return daily_rate * days_covered

def split_income_and_expenses(rows):
    income = [r for r in rows if r.get("type") == "income"]
    expenses = [r for r in rows if r.get("type") == "expense"]
    return income, expenses


def prorate_monthly_amount(month_key, start_day, full_month_amount):
    """
    Prorates a monthly amount from start_day through end-of-month (inclusive).
    Example: rent starts Feb 14 → only pay for Feb 14–Feb 28 (or 29).
    """
    year, month = map(int, month_key.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]

    days_covered = days_in_month - start_day + 1
    daily_rate = full_month_amount / days_in_month

    return daily_rate * days_covered

def estimate_paycheck_pattern(income_rows, months_back=2):
    """
    Returns:
      avg_paycheck_amount (float)
      avg_paychecks_per_month (float)
      recent_months_used (list[str])
    """
    if not income_rows:
        return 0.0, 0.0, []

    # Count paychecks per month and collect paycheck amounts
    paychecks_by_month = {}
    paycheck_amounts = []

    for r in income_rows:
        month_key = datetime.strptime(r["date"], "%Y-%m-%d").strftime("%Y-%m")
        paychecks_by_month[month_key] = paychecks_by_month.get(month_key, 0) + 1
        paycheck_amounts.append(r["amount"])

    months = sorted(paychecks_by_month.keys())
    recent_months = months[-months_back:] if len(months) >= months_back else months

    # Average paycheck amount across all income rows (simple + stable)
    avg_paycheck_amount = sum(paycheck_amounts) / len(paycheck_amounts)

    # Average paychecks per month across recent months
    avg_paychecks_per_month = (
        sum(paychecks_by_month[m] for m in recent_months) / len(recent_months)
        if recent_months else 0.0
    )

    return avg_paycheck_amount, avg_paychecks_per_month, recent_months

def estimate_baseline_nonrent_spending(monthly_category_totals, months_back=2):
    """
    Uses recent months of expense category totals to estimate baseline spending.
    Returns average monthly spending as a POSITIVE dollar amount.
    """
    months = sorted(monthly_category_totals.keys())
    recent_months = months[-months_back:] if len(months) >= months_back else months

    if not recent_months:
        return 0.0, []

    monthly_spend_values = []
    for m in recent_months:
        cat_map = monthly_category_totals.get(m, {})
        # category totals are negative (expenses), so abs() to get dollars spent
        nonrent_total = sum(abs(v) for cat, v in cat_map.items() if cat != "Rent")
        monthly_spend_values.append(nonrent_total)

    avg_nonrent = sum(monthly_spend_values) / len(monthly_spend_values)
    return avg_nonrent, recent_months

def rent_affordability_report(
    target_month,
    avg_paycheck_amount,
    avg_paychecks_per_month,
    baseline_nonrent_spend
):
    # Project income for the month
    if INCOME_OVERRIDE_MONTHLY is not None:
        projected_income = INCOME_OVERRIDE_MONTHLY
    else:
        projected_income = avg_paycheck_amount * avg_paychecks_per_month


    # Project rent for the month (prorated for start month)
    if target_month == RENT_START_MONTH:
        projected_rent = prorate_monthly_amount(target_month, RENT_START_DAY, RENT_AMOUNT)
    elif target_month > RENT_START_MONTH:
        projected_rent = RENT_AMOUNT
    else:
        projected_rent = 0.0  # before rent starts

    # Total projected spending
    projected_total_spend = baseline_nonrent_spend + projected_rent

    # Net
    projected_net = projected_income - projected_total_spend

    # Ratios (avoid division by zero)
    rent_pct_income = (projected_rent / projected_income) * 100 if projected_income > 0 else 0
    spend_pct_income = (projected_total_spend / projected_income) * 100 if projected_income > 0 else 0

    return {
        "month": target_month,
        "projected_income": projected_income,
        "baseline_nonrent_spend": baseline_nonrent_spend,
        "projected_rent": projected_rent,
        "projected_total_spend": projected_total_spend,
        "projected_net": projected_net,
        "rent_pct_income": rent_pct_income,
        "spend_pct_income": spend_pct_income,
    }


# ----------------------------
# Main Program
# ----------------------------
def main():
    rows, loaded_files = load_all_monthly_csvs("data")
    income_rows, expense_rows = split_income_and_expenses(rows)


    print(f"Rows loaded: {len(rows)} | income: {len(income_rows)} | expense: {len(expense_rows)}")

    if len(expense_rows) == 0:
        raise ValueError(
            "No expense rows found. Check that your CSV has a 'type' column with values 'expense' or 'income'."
    )



    total_income = calculate_total_spent(income_rows)
    total_expenses = calculate_total_spent(expense_rows)  # NOTE: this will be negative
    total_expenses_abs = abs(total_expenses)
    net_total = total_income + total_expenses  # income + (negative expense)
    category_totals = calculate_category_totals(expense_rows)  # expenses only
    monthly_expense_totals = calculate_monthly_totals(expense_rows)  # expenses only
    monthly_income_totals = calculate_monthly_totals(income_rows)  # income only
    monthly_category_totals = calculate_monthly_category_totals(expense_rows)  # expenses only


    current_month = max(monthly_expense_totals.keys())


    prediction = predict_monthly_spending(rows, current_month)
    predicted_total = prediction[1] if prediction is not None else None

    print(f"Total income: {total_income:.2f}")
    print(f"Total expenses: {total_expenses_abs:.2f}")
    print(f"Net cash flow: {net_total:.2f}")


    print("\nSpending by category:")
    for category, amount in category_totals.items():
        print(f"{category}: {amount:.2f}")

    print("\nExpenses by month:")
    for month, amount in monthly_expense_totals.items():
        print(f"{month}: {amount:.2f}")

    print("\nIncome by month:")
    for month, amount in monthly_income_totals.items():
        print(f"{month}: {amount:.2f}")

    avg_paycheck, avg_paychecks_per_month, income_months_used = estimate_paycheck_pattern(income_rows, months_back=2)
    baseline_nonrent, expense_months_used = estimate_baseline_nonrent_spending(monthly_category_totals, months_back=2)
    print(f"- Avg paycheck: {avg_paycheck:.2f}")
    print(f"- Avg paychecks/month (recent): {avg_paychecks_per_month:.2f} (months used: {', '.join(income_months_used)})")
    print(f"- Baseline non-rent spending/month: {baseline_nonrent:.2f} (months used: {', '.join(expense_months_used)})")

    print("\nRent affordability projection (based on recent history):")
    
    for month_key in ["2026-02", "2026-03"]:
        report = rent_affordability_report(
        month_key,
        avg_paycheck,
        avg_paychecks_per_month,
        baseline_nonrent
    )

    print(f"\nAffordability for {report['month']}:")
    print(f"  Projected income: {report['projected_income']:.2f}")
    print(f"  Baseline non-rent spend: {report['baseline_nonrent_spend']:.2f}")
    print(f"  Projected rent: {report['projected_rent']:.2f}")
    print(f"  Projected total spend: {report['projected_total_spend']:.2f}")
    print(f"  Projected net (income - spend): {report['projected_net']:.2f}")
    print(f"  Rent as % of income: {report['rent_pct_income']:.2f}%")
    print(f"  Total spend as % of income: {report['spend_pct_income']:.2f}%")



    mom_changes = calculate_month_over_month_change(monthly_expense_totals)
    current_month = max(monthly_expense_totals.keys())
    prediction = predict_monthly_spending(expense_rows, current_month)


    print("\nMonth-over-month change:")
    if mom_changes is None:
        print("Not enough data to calculate month-over-month change.")
    else:
        for change in mom_changes:
            print(
                f"{change['from']} → {change['to']}: "
                f"{change['change']:+.2f} ({change['percent_change']:+.2f}%)"
            )

    print("\nEnd-of-month prediction:")
    if prediction is None:
        print("Not enough data to predict spending.")
    else:
        spent_so_far, predicted_eom = prediction
        print(f"Spent so far in {current_month}: {spent_so_far:.2f}")
        print(f"Predicted end-of-month spending: {predicted_eom:.2f}")

    print("\nPrediction accuracy (historical simulation):")
    for month, actual in monthly_expense_totals.items():
        simulated_prediction = predict_mid_month(rows, month, cutoff_day=15)
        if simulated_prediction is None:
            continue

        error, percent_error = evaluate_prediction(simulated_prediction, actual)
        print(
            f"{month}: predicted {simulated_prediction:.2f}, "
            f"actual {actual:.2f}, "
            f"error {error:+.2f} ({percent_error:+.2f}%)"
        )

    print("\nInsights:")
    insights = generate_insights(monthly_expense_totals, monthly_category_totals, current_month, predicted_total=predicted_total)
    if not insights:
        print("No insights available yet (need at least 2 months of data).")
    else:
        for line in insights:
            print(f"- {line}")

    print("\nBudget Alerts:")
    budgets_for_current_month = get_budgets_for_month(current_month)
    budget_alerts = evaluate_budgets(monthly_category_totals, current_month, budgets_for_current_month)

    if not budget_alerts:
        print("All categories are within budget.")
    else:
        for alert in budget_alerts:
            print(f"- {alert}")



if __name__ == "__main__":
    main()
