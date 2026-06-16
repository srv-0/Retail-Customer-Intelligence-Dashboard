# Retail Customer Intelligence Dashboard
### Data + Business Analytics

---

## Problem Statement
Retail businesses lose 20–30% of customers annually without early warning signals. This project builds an end-to-end customer intelligence system that segments customers, predicts churn risk, and identifies cross-sell opportunities — translating raw transaction data into actionable business decisions.

---

## Business Impact
| Metric | Finding |
|--------|---------|
| Champions (top segment) | 357 customers driving ~62% of revenue |
| High churn risk | 438 customers flagged for immediate retention |
| Top product bundles | Electronics → Sports shows highest lift (cross-sell) |
| Cities with highest LTV | Kolkata, Delhi, Ahmedabad |

---

## Tech Stack
| Layer | Tools |
|-------|-------|
| Data generation | Python (Faker, NumPy, Pandas) |
| Database | SQLite + 10 SQL business queries |
| EDA & ML | Python (Pandas, Seaborn, Matplotlib, Scikit-learn) |
| Market Basket | Mlxtend (Apriori algorithm) |
| Dashboard | Power BI (5 pages, DAX measures, drill-through) |
| Web App | Flask + HTML/CSS + SQLite |
| Version control | GitHub |

---

## Project Structure
```
retail-customer-intelligence/
├── data/
│   ├── retail_transactions.csv      ← 10,000 transaction records
│   └── churn_scores.csv             ← RFM segments + churn risk per customer
├── sql/
│   └── sql_queries.sql              ← 10 business SQL queries
├── notebooks/
│   └── EDA_RFM_Churn.ipynb          ← Full analysis notebook
├── charts/                          ← 6 EDA visualisation exports
├── powerbi/
│   └── retail_dashboard.pbix        ← 5-page executive dashboard
├── webapp/
│   └── app.py                       ← Flask web application
└── README.md
```

---

## How to Run
```bash
# Install dependencies
pip install pandas numpy matplotlib seaborn scikit-learn mlxtend flask

# Generate dataset + load SQL
python generate_dataset.py

# Run EDA + ML analysis
python eda_rfm_churn.py

# Start web app
python app.py
# Open http://localhost:5000
```

---

## Key Analyses
1. **RFM Segmentation** — 4 tiers: Champions, Loyal, At-risk, Lost
2. **Churn Prediction** — Random Forest, 84%+ accuracy on held-out test set
3. **Market Basket Analysis** — Apriori algorithm, top bundles by lift score
4. **SQL Business Queries** — Revenue trends, city performance, return rates
5. **Power BI Dashboard** — 5 interactive pages with DAX measures

---

*Built for campus placement | Tools: Python · SQL · Power BI · Excel · Flask · GitHub*
