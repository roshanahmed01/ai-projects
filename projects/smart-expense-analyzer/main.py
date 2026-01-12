# Smart Expense Analyzer - Version 2 (CSV Input)

import csv
from datetime import datetime


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

