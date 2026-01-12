# Smart Expense Analyzer - Version 2 (CSV Input)

import csv
from datetime import datetime
import calendar


def load_expenses_from_csv(file_path):
    expenses = []

    with open(file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            expenses.append({
                "date": row["date"],
                "category": row["category"],
                "amount": float(row["amount"])
            })

    return expenses


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
        date_str = expense["date"]

        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        month_key = date_obj.strftime("%Y-%m")

        if month_key in monthly_totals:
            monthly_totals[month_key] += expense["amount"]
        else:
            monthly_totals[month_key] = expense["amount"]

    return monthly_totals


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
        percent_change = (change / previous_amount) * 100

        changes.append({
            "from": previous_month,
            "to": current_month,
            "change": change,
            "percent_change": percent_change
        })

    return changes

def predict_monthly_spending(expenses, target_month):
    total_spent = 0
    days_with_data = set()

    for expense in expenses:
        date_obj = datetime.strptime(expense["date"], "%Y-%m-%d")
        month_key = date_obj.strftime("%Y-%m")

        if month_key == target_month:
            total_spent += expense["amount"]
            days_with_data.add(date_obj.day)

    if not days_with_data:
        return None

    latest_day = max(days_with_data)
    average_daily_spend = total_spent / latest_day


    year, month = map(int, target_month.split("-"))
    days_in_month = calendar.monthrange(year, month)[1]

    predicted_total = average_daily_spend * days_in_month

    return total_spent, predicted_total





expenses = load_expenses_from_csv("data/expenses.csv")

total_spent = calculate_total_spent(expenses)
category_totals = calculate_category_totals(expenses)
monthly_totals = calculate_monthly_totals(expenses)

print("Total spent:", total_spent)
print("\nSpending by category:")

for category, amount in category_totals.items():
    print(f"{category}: {amount}")

print("\nSpending by month:")

for month, amount in monthly_totals.items():
    print(f"{month}: {amount}")

mom_changes = calculate_month_over_month_change(monthly_totals)

print("\nMonth-over-month change:")

if mom_changes is None:
    print("Not enough data to calculate month-over-month change.")
else:
    for change in mom_changes:
        print(
            f"{change['from']} → {change['to']}: "
            f"{change['change']} ({change['percent_change']:.2f}%)"
        )

current_month = max(monthly_totals.keys())

prediction = predict_monthly_spending(expenses, current_month)

print("\nEnd-of-month prediction:")

if prediction is None:
    print("Not enough data to predict spending.")
else:
    spent_so_far, predicted_total = prediction
    print(f"Spent so far in {current_month}: {spent_so_far:.2f}")
    print(f"Predicted end-of-month spending: {predicted_total:.2f}")
