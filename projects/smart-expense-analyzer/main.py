# Smart Expense Analyzer - Version 1

expenses = [
    {"date": "2025-01-01", "category": "Rent", "amount": 1200},
    {"date": "2025-01-03", "category": "Food", "amount": 45},
    {"date": "2025-01-05", "category": "Food", "amount": 30},
    {"date": "2025-01-08", "category": "Transport", "amount": 60},
    {"date": "2025-01-10", "category": "Entertainment", "amount": 100},
]

total_spent = 0

for expense in expenses:
    total_spent += expense["amount"]

print("Total spent:", total_spent)
