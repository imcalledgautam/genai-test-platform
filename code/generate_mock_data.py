import pandas as pd
import random
from faker import Faker

fake = Faker()

# Define category mapping (category_id → category_name)
category_mapping = {
    1: "Groceries",
    2: "Entertainment",
    3: "Transportation",
    4: "Utilities",
    5: "Shopping",
    6: "Dining",
    7: "Health & Fitness",
    8: "Education",
    9: "Other"
}

# Define meaningful descriptions
category_descriptions = {
    "Groceries": ["Shopping at Coop", "Shopping at Migros", "Buying fresh produce at Denner", "Organic food at Alnatura", "Weekly grocery shopping"],
    "Entertainment": ["Cinema ticket at Pathé", "Concert ticket at Hallenstadion", "Netflix monthly subscription", "Zürich Opera House ticket", "Museum entry"],
    "Transportation": ["Fill up car at Esso", "Fill up car at Shell", "Train ticket Zürich to Bern", "Tram pass renewal", "Halb-Tax (Swiss railway discount)"],
    "Utilities": ["Electricity bill payment", "Swisscom internet subscription", "Mobile bill at Salt", "Gas bill", "Garbage collection fee"],
    "Shopping": ["Clothing at H&M", "Electronics at Interdiscount", "Furniture shopping at IKEA", "New smartphone at Digitec", "Shoe shopping at Ochsner Sport"],
    "Dining": ["Dinner at Vapiano", "Lunch at Tibits", "Coffee at Starbucks", "Fast food at McDonald's", "Weekend brunch at Sprüngli"],
    "Health & Fitness": ["Fitness abo at Holmes Place", "Yoga class subscription", "Doctor consultation at MedBase", "Pharmacy purchase at Amavita", "Health insurance premium"],
    "Education": ["Online course at Udemy", "University tuition fee", "Books purchase at Orell Füssli", "Software subscription for learning", "German language class"],
    "Other": ["Charity donation", "Gift purchase at Manor", "Unexpected expense", "Bank service fee", "Car parking fee"]
}

# Generate mock transactions
transactions = []
for _ in range(50):  # Generate 50 transactions
    transaction_date = fake.date_between(start_date="-1y", end_date="today")
    category_id = random.randint(1, 9)
    category_name = category_mapping[category_id]
    
    # Assign a relevant description from the category
    description = random.choice(category_descriptions[category_name])
    
    # Assign a realistic amount based on category
    if category_name in ["Groceries", "Dining", "Transportation"]:
        amount = round(random.uniform(10, 150), 2)
    elif category_name in ["Shopping", "Entertainment", "Health & Fitness"]:
        amount = round(random.uniform(20, 500), 2)
    elif category_name in ["Utilities", "Education"]:
        amount = round(random.uniform(50, 300), 2)
    else:
        amount = round(random.uniform(5, 1000), 2)

    transactions.append([transaction_date, amount, category_id, category_name, description])

# Create DataFrame
df = pd.DataFrame(transactions, columns=["transaction_date", "amount", "category_id", "category_name", "description"])

# Save as CSV
df.to_csv("transactions.csv", index=False)

print("transactions.csv created successfully!")
