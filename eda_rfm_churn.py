import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import sqlite3, warnings, os
warnings.filterwarnings('ignore')
os.makedirs('project_package/charts', exist_ok=True)

# ─── Load data ───────────────────────────────────────────────
conn = sqlite3.connect('data/retail_analytics.db')
df   = pd.read_sql('SELECT * FROM transactions', conn)
conn.close()
df['order_date'] = pd.to_datetime(df['order_date'])

PALETTE = ['#534AB7','#0F6E56','#D85A30','#BA7517','#185FA5','#3B6D11','#993356']
sns.set_theme(style='whitegrid', font_scale=0.95)

# ─── Chart 1: Monthly Revenue Trend ──────────────────────────
monthly = df.groupby(df['order_date'].dt.to_period('M'))['total_amount'].sum().reset_index()
monthly['order_date'] = monthly['order_date'].astype(str)
fig, ax = plt.subplots(figsize=(10,4))
ax.plot(monthly['order_date'], monthly['total_amount']/1e5, color='#534AB7', linewidth=2.2, marker='o', markersize=4)
ax.fill_between(range(len(monthly)), monthly['total_amount']/1e5, alpha=0.08, color='#534AB7')
ax.set_xticks(range(0, len(monthly), 3))
ax.set_xticklabels(monthly['order_date'][::3], rotation=30, ha='right', fontsize=9)
ax.set_title('Monthly revenue trend (₹ in lakhs)', fontsize=13, fontweight='normal', pad=12)
ax.set_ylabel('Revenue (₹ Lakhs)')
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'₹{x:.0f}L'))
plt.tight_layout(); plt.savefig('charts/01_monthly_revenue.png', dpi=150, bbox_inches='tight'); plt.close()
print("Chart 1 done")

# ─── Chart 2: Category Revenue ───────────────────────────────
cat_rev = df.groupby('category')['total_amount'].sum().sort_values(ascending=True)
colors  = PALETTE[:len(cat_rev)]
fig, ax = plt.subplots(figsize=(8,5))
bars = ax.barh(cat_rev.index, cat_rev.values/1e5, color=colors[::-1])
for bar in bars:
    ax.text(bar.get_width()+0.3, bar.get_y()+bar.get_height()/2,
            f'₹{bar.get_width():.1f}L', va='center', fontsize=9)
ax.set_title('Revenue by product category', fontsize=13, fontweight='normal', pad=12)
ax.set_xlabel('Revenue (₹ Lakhs)')
ax.set_xlim(0, cat_rev.max()/1e5 * 1.18)
plt.tight_layout(); plt.savefig('charts/02_category_revenue.png', dpi=150, bbox_inches='tight'); plt.close()
print("Chart 2 done")

# ─── RFM Segmentation ────────────────────────────────────────
snapshot = df['order_date'].max() + pd.Timedelta(days=1)
rfm = df.groupby('customer_id').agg(
    recency   = ('order_date', lambda x: (snapshot - x.max()).days),
    frequency = ('order_id',   'nunique'),
    monetary  = ('total_amount','sum')
).reset_index()

rfm['R_score'] = pd.qcut(rfm['recency'],   4, labels=[4,3,2,1], duplicates='drop').astype(int)
rfm['F_score'] = pd.qcut(rfm['frequency'], 4, labels=[1,2,3,4], duplicates='drop').astype(int)
rfm['M_score'] = pd.qcut(rfm['monetary'],  4, labels=[1,2,3,4], duplicates='drop').astype(int)
rfm['RFM_score'] = rfm['R_score'] + rfm['F_score'] + rfm['M_score']

def label(score):
    if score >= 10: return 'Champions'
    elif score >= 7: return 'Loyal customers'
    elif score >= 5: return 'At-risk'
    else: return 'Lost / inactive'

rfm['segment'] = rfm['RFM_score'].apply(label)
seg_summary = rfm.groupby('segment').agg(
    customers=('customer_id','count'),
    avg_monetary=('monetary','mean'),
    avg_recency=('recency','mean')
).reset_index().sort_values('avg_monetary', ascending=False)
print("\nRFM Segments:\n", seg_summary.to_string(index=False))

# Chart 3: RFM Segment Distribution
seg_colors = {'Champions':'#534AB7','Loyal customers':'#0F6E56','At-risk':'#BA7517','Lost / inactive':'#D85A30'}
seg_counts = rfm['segment'].value_counts()
fig, ax = plt.subplots(figsize=(7,5))
bars = ax.bar(seg_counts.index, seg_counts.values,
              color=[seg_colors[s] for s in seg_counts.index], width=0.55)
for bar in bars:
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+5,
            f'{bar.get_height()}', ha='center', fontsize=10, fontweight='normal')
ax.set_title('Customer segments by RFM score', fontsize=13, fontweight='normal', pad=12)
ax.set_ylabel('Number of customers')
plt.tight_layout(); plt.savefig('project_package/charts/03_rfm_segments.png', dpi=150, bbox_inches='tight'); plt.close()
print("Chart 3 done")

# ─── Churn Prediction ────────────────────────────────────────
# Label: churn = no purchase in last 90 days of dataset window
cutoff = df['order_date'].max() - pd.Timedelta(days=90)
churn_labels = df.groupby('customer_id')['order_date'].max().reset_index()
churn_labels['churned'] = (churn_labels['order_date'] < cutoff).astype(int)

features = rfm.merge(churn_labels[['customer_id','churned']], on='customer_id')
X = features[['recency','frequency','monetary','R_score','F_score','M_score']]
y = features['churned']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=150, random_state=42, class_weight='balanced')
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"\nChurn model accuracy: {acc:.2%}")
print(classification_report(y_test, y_pred, target_names=['Active','Churned']))

# Feature importance chart
imp = pd.Series(model.feature_importances_, index=X.columns).sort_values()
fig, ax = plt.subplots(figsize=(7,4))
ax.barh(imp.index, imp.values, color='#534AB7')
ax.set_title(f'Churn model — feature importance (accuracy {acc:.0%})', fontsize=13, fontweight='normal', pad=12)
ax.set_xlabel('Importance score')
plt.tight_layout(); plt.savefig('charts/04_churn_feature_importance.png', dpi=150, bbox_inches='tight'); plt.close()
print("Chart 4 done")

# Save churn risk scores
features['churn_probability'] = model.predict_proba(X)[:,1]
features['churn_risk'] = pd.cut(features['churn_probability'], bins=[0,.33,.66,1.0],
                                 labels=['Low','Medium','High'])
features.to_csv('data/churn_scores.csv', index=False)

# ─── Market Basket Analysis ───────────────────────────────────
basket = df.groupby(['order_id','category'])['quantity'].sum().unstack().fillna(0)
basket = basket.map(lambda x: 1 if x > 0 else 0)
freq_items = apriori(basket, min_support=0.05, use_colnames=True)
rules = association_rules(freq_items, metric='confidence', min_threshold=0.3)
rules = rules.sort_values('lift', ascending=False).head(12)
print(f"\nTop basket rules (lift > 1):\n{rules[['antecedents','consequents','support','confidence','lift']].head(5).to_string(index=False)}")

# Chart 5: Top bundles by lift
bundles = []
for i in range(len(rules)):
    a = list(rules.loc[i, 'antecedents'])[0]
    c = list(rules.loc[i, 'consequents'])[0]
    bundles.append(f"{a} -> {c}")
rules['bundle'] = bundles
top_rules = rules.head(8).sort_values('lift')
fig, ax = plt.subplots(figsize=(9,5))
bars = ax.barh(top_rules['bundle'], top_rules['lift'], color='#0F6E56')
for bar in bars:
    ax.text(bar.get_width()+0.01, bar.get_y()+bar.get_height()/2,
            f'{bar.get_width():.2f}×', va='center', fontsize=9)
ax.set_title('Market basket — top product bundle pairs by lift', fontsize=13, fontweight='normal', pad=12)
ax.set_xlabel('Lift score (>1 = meaningful association)')
ax.axvline(1, color='#D85A30', linestyle='--', linewidth=1, label='Baseline (lift=1)')
ax.legend(fontsize=9)
plt.tight_layout(); plt.savefig('charts/05_market_basket.png', dpi=150, bbox_inches='tight'); plt.close()
print("Chart 5 done")

# ─── Chart 6: RFM monetary distribution ──────────────────────
fig, ax = plt.subplots(figsize=(8,4))
for seg, color in seg_colors.items():
    data = rfm[rfm['segment']==seg]['monetary']
    ax.hist(data, bins=25, alpha=0.65, color=color, label=seg)
ax.set_title('Revenue distribution by customer segment', fontsize=13, fontweight='normal', pad=12)
ax.set_xlabel('Total spend per customer (₹)')
ax.set_ylabel('Number of customers')
ax.legend(fontsize=9)
plt.tight_layout(); plt.savefig('charts/06_segment_revenue_dist.png', dpi=150, bbox_inches='tight'); plt.close()
print("Chart 6 done")

print("\n All charts saved to project_package/charts/")
print(" Churn scores saved to data/churn_scores.csv")

# ─── Fix: Market Basket (pandas >= 2.1 uses .map not .applymap) ─
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from mlxtend.frequent_patterns import apriori, association_rules
import sqlite3, warnings
warnings.filterwarnings('ignore')

conn = sqlite3.connect('data/retail_analytics.db')
df   = pd.read_sql('SELECT * FROM transactions', conn)
conn.close()
df['order_date'] = pd.to_datetime(df['order_date'])
PALETTE = ['#534AB7','#0F6E56','#D85A30','#BA7517','#185FA5','#3B6D11','#993356']
sns.set_theme(style='whitegrid', font_scale=0.95)

basket = df.groupby(['order_id','category'])['quantity'].sum().unstack().fillna(0)
basket = basket.map(lambda x: 1 if x > 0 else 0)
freq_items = apriori(basket, min_support=0.05, use_colnames=True)
rules = association_rules(freq_items, metric='confidence', min_threshold=0.3)
rules = rules.sort_values('lift', ascending=False).head(12)
print(f"\nTop basket rules:\n{rules[['antecedents','consequents','support','confidence','lift']].head(5).to_string(index=False)}")

bundles = []
for i in range(len(rules)):
    a = list(rules.loc[i, 'antecedents'])[0]
    c = list(rules.loc[i, 'consequents'])[0]
    bundles.append(f"{a} -> {c}")
rules['bundle'] = bundles
top_rules = rules.head(8).sort_values('lift')
fig, ax = plt.subplots(figsize=(9,5))
bars = ax.barh(top_rules['bundle'], top_rules['lift'], color='#0F6E56')
for bar in bars:
    ax.text(bar.get_width()+0.01, bar.get_y()+bar.get_height()/2,
            f'{bar.get_width():.2f}×', va='center', fontsize=9)
ax.set_title('Market basket — top product bundle pairs by lift', fontsize=13, fontweight='normal', pad=12)
ax.set_xlabel('Lift score (>1 = meaningful association)')
ax.axvline(1, color='#D85A30', linestyle='--', linewidth=1, label='Baseline (lift=1)')
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig('charts/05_market_basket.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 5 done")

# Chart 6: Segment revenue distribution
rfm_data = pd.read_csv('data/churn_scores.csv')
seg_colors = {'Champions':'#534AB7','Loyal customers':'#0F6E56','At-risk':'#BA7517','Lost / inactive':'#D85A30'}

# Load original rfm to get segments  
snapshot = df['order_date'].max() + pd.Timedelta(days=1)
rfm = df.groupby('customer_id').agg(
    recency=('order_date', lambda x: (snapshot - x.max()).days),
    frequency=('order_id','nunique'),
    monetary=('total_amount','sum')
).reset_index()
rfm['RFM_score'] = (pd.qcut(rfm['recency'],4,labels=[4,3,2,1],duplicates='drop').astype(int) +
                    pd.qcut(rfm['frequency'],4,labels=[1,2,3,4],duplicates='drop').astype(int) +
                    pd.qcut(rfm['monetary'],4,labels=[1,2,3,4],duplicates='drop').astype(int))
rfm['segment'] = rfm['RFM_score'].apply(lambda s: 'Champions' if s>=10 else ('Loyal customers' if s>=7 else ('At-risk' if s>=5 else 'Lost / inactive')))

fig, ax = plt.subplots(figsize=(8,4))
for seg, color in seg_colors.items():
    data = rfm[rfm['segment']==seg]['monetary']
    ax.hist(data, bins=25, alpha=0.65, color=color, label=seg)
ax.set_title('Revenue distribution by customer segment', fontsize=13, fontweight='normal', pad=12)
ax.set_xlabel('Total spend per customer (₹)')
ax.set_ylabel('Number of customers')
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig('charts/06_segment_revenue_dist.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 6 done")
print("\n All 6 charts complete")
