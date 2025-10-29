# Entities and Relationships
## There are three main entities:

### 1. Transactions

transaction_id (Primary Key, integer)
transaction_date (date)
amount (decimal)
category_id (Foreign Key → Categories)
description (text)

### 2. Categories

category_id (Primary Key, integer)
category_name (text, e.g., Groceries, Rent, Entertainment)
budget_limit (decimal, monthly spending limit per category)


## Relationships:

One Category → Many Transactions
One Account → Many Transactions

SQL
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT NOT NULL,
    budget_limit DECIMAL NOT NULL
);

CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY,
    transaction_date DATE NOT NULL,
    amount DECIMAL NOT NULL,
    category_id INTEGER,
    description TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);


