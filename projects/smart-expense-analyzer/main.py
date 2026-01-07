# Smart Expense Analyzer - Version 1 (Category Totals Added)

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


expenses = [
    {"date": "2025-01-01", "category": "Rent", "amount": 1200},
    {"date": "2025-01-03", "category": "Food", "amount": 45},
    {"date": "2025-01-05", "category": "Food", "amount": 30},
    {"date": "2025-01-08", "category": "Transport", "amount": 60},
    {"date": "2025-01-10", "category": "Entertainment", "amount": 100},
]

total_spent = calculate_total_spent(expenses)
category_totals = calculate_category_totals(expenses)

print("Total spent:", total_spent)
print("\nSpending by category:")

for category, amount in category_totals.items():
    print(f"{category}: {amount}")
