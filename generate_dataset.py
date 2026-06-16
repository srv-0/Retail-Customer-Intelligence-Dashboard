import pandas as pd
import numpy as np
import sqlite3
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

N = 10000

categories = ['Electronics', 'Clothing', 'Groceries', 'Home & Kitchen', 'Sports', 'Books', 'Beauty']
products = {
    'Electronics':    [('Wireless Earbuds',2499),('Phone Charger',599),('USB Hub',899),('Laptop Stand',1299),('Webcam',2199)],
    'Clothing':       [('Cotton T-Shirt',499),('Denim Jeans',1299),('Formal Shirt',899),('Sneakers',2499),('Jacket',2999)],
    'Groceries':      [('Basmati Rice 5kg',499),('Olive Oil',799),('Mixed Nuts',599),('Protein Bar Pack',699),('Green Tea',299)],
    'Home & Kitchen': [('Air Fryer',3999),('Water Bottle',399),('Storage Box',299),('Knife Set',1299),('Coffee Mug',249)],
    'Sports':         [('Yoga Mat',799),('Resistance Bands',499),('Running Shoes',3499),('Water Jug',599),('Gym Gloves',399)],
    'Books':          [('Python Programming',699),('Data Science Guide',899),('Business Strategy',599),('Self Help',449),('Fiction Novel',299)],
    'Beauty':         [('Face Serum',999),('Sunscreen SPF50',499),('Hair Mask',399),('Lip Balm Pack',199),('Body Lotion',349)],
}

cities = ['Mumbai','Delhi','Bangalore','Hyderabad','Chennai','Pune','Kolkata','Ahmedabad','Jaipur','Lucknow']
payment_methods = ['Credit Card','Debit Card','UPI','Net Banking','Cash on Delivery']

num_customers = 1500
customer_ids = [f'CUST{str(i).zfill(4)}' for i in range(1, num_customers+1)]
customer_city = {c: random.choice(cities) for c in customer_ids}

# Bias: some customers buy much more than others (power law)
customer_weights = np.random.power(0.4, num_customers)
customer_weights /= customer_weights.sum()

rows = []
start_date = datetime(2023, 1, 1)
end_date   = datetime(2024, 12, 31)
date_range = (end_date - start_date).days

order_id = 1
for _ in range(N):
    cust = np.random.choice(customer_ids, p=customer_weights)
    cat  = random.choice(categories)
    prod_name, base_price = random.choice(products[cat])
    qty  = random.randint(1, 4)
    discount = round(random.choice([0, 0, 0, 5, 10, 15, 20]) / 100, 2)
    unit_price = base_price
    total = round(unit_price * qty * (1 - discount), 2)
    order_date = start_date + timedelta(days=random.randint(0, date_range))
    rating = random.choices([1,2,3,4,5], weights=[3,5,12,40,40])[0]
    returned = 1 if (rating <= 2 and random.random() < 0.4) else 0
    rows.append({
        'order_id':       f'ORD{str(order_id).zfill(6)}',
        'customer_id':    cust,
        'city':           customer_city[cust],
        'order_date':     order_date.strftime('%Y-%m-%d'),
        'category':       cat,
        'product_name':   prod_name,
        'quantity':       qty,
        'unit_price':     unit_price,
        'discount_pct':   discount,
        'total_amount':   total,
        'payment_method': random.choice(payment_methods),
        'rating':         rating,
        'returned':       returned,
    })
    order_id += 1

df = pd.DataFrame(rows)
df.to_csv('data/retail_transactions.csv', index=False)
print(f"Dataset created: {len(df)} rows, {df['customer_id'].nunique()} unique customers")
print(df.head(3).to_string())

# Load into SQLite
conn = sqlite3.connect('data/retail_analytics.db')
df.to_sql('transactions', conn, if_exists='replace', index=False)

conn.execute('''
CREATE TABLE IF NOT EXISTS customers AS
SELECT
    customer_id,
    city,
    COUNT(DISTINCT order_id)        AS total_orders,
    SUM(total_amount)               AS total_spent,
    ROUND(AVG(total_amount),2)      AS avg_order_value,
    MIN(order_date)                 AS first_order,
    MAX(order_date)                 AS last_order,
    ROUND(AVG(rating),2)            AS avg_rating
FROM transactions
GROUP BY customer_id, city
''')
conn.commit()
conn.close()
print("\nSQLite DB created: retail_analytics.db")
