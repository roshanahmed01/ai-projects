# Smart Expense Analyzer - Version 2 (CSV Input)

import csv


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


expenses = load_expenses_from_csv("data/expenses.csv")

total_spent = calculate_total_spent(expenses)
category_totals = calculate_category_totals(expenses)

print("Total spent:", total_spent)
print("\nSpending by category:")

for category, amount in category_totals.items():
    print(f"{category}: {amount}")
