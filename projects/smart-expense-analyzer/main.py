# Smart Expense Analyzer
# Reads expenses from CSV and outputs summaries, trends, predictions, insights, and budget alerts.

import csv
import calendar
from datetime import datetime

# ----------------------------
# Budget Configuration
# ----------------------------
BUDGETS = {
    "Rent": 1500,
    "Food": 400,
    "Transport": 250,
    "Entertainment": 200,
}

# ----------------------------
# Data Loading
# ----------------------------
def load_expenses_from_csv(file_path):
    expenses = []

    with open(file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            expenses.append(
                {
                    "date": row["date"],
                    "category": row["category"],
                    "amount": float(row["amount"]),
                }
            )

    return expenses


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


# ----------------------------
# Main Program
# ----------------------------
def main():
    expenses = load_expenses_from_csv("data/expenses.csv")

    total_spent = calculate_total_spent(expenses)
    category_totals = calculate_category_totals(expenses)
    monthly_totals = calculate_monthly_totals(expenses)
    monthly_category_totals = calculate_monthly_category_totals(expenses)

    current_month = max(monthly_totals.keys())

    prediction = predict_monthly_spending(expenses, current_month)
    predicted_total = prediction[1] if prediction is not None else None

    print(f"Total spent: {total_spent:.2f}")

    print("\nSpending by category:")
    for category, amount in category_totals.items():
        print(f"{category}: {amount:.2f}")

    print("\nSpending by month:")
    for month, amount in monthly_totals.items():
        print(f"{month}: {amount:.2f}")

    mom_changes = calculate_month_over_month_change(monthly_totals)

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
    for month, actual in monthly_totals.items():
        simulated_prediction = predict_mid_month(expenses, month, cutoff_day=15)
        if simulated_prediction is None:
            continue

        error, percent_error = evaluate_prediction(simulated_prediction, actual)
        print(
            f"{month}: predicted {simulated_prediction:.2f}, "
            f"actual {actual:.2f}, "
            f"error {error:+.2f} ({percent_error:+.2f}%)"
        )

    print("\nInsights:")
    insights = generate_insights(monthly_totals, monthly_category_totals, current_month, predicted_total=predicted_total)
    if not insights:
        print("No insights available yet (need at least 2 months of data).")
    else:
        for line in insights:
            print(f"- {line}")

    print("\nBudget Alerts:")
    budget_alerts = evaluate_budgets(monthly_category_totals, current_month, BUDGETS)
    if not budget_alerts:
        print("All categories are within budget.")
    else:
        for alert in budget_alerts:
            print(f"- {alert}")


if __name__ == "__main__":
    main()
