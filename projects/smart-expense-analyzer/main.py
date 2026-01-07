# Smart Expense Analyzer - Version 1 (Refactored)

def calculate_total_spent(expenses):
    total = 0
    for expense in expenses:
        total += expense["amount"]
    return total


expenses = [
    {"date": "2025-01-01", "category": "Rent", "amount": 1200},
    {"date": "2025-01-03", "category": "Food", "amount": 45},
    {"date": "2025-01-05", "category": "Food", "amount": 30},
    {"date": "2025-01-08", "category": "Transport", "amount": 60},
    {"date": "2025-01-10", "category": "Entertainment", "amount": 100},
]

total_spent = calculate_total_spent(expenses)

print("Total spent:", total_spent)
