from flask import Flask, render_template_string, request, jsonify
import sqlite3, pandas as pd, json
import os

app = Flask(__name__)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'retail_analytics.db')

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Retail Customer Intelligence</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f5f5f5;color:#1a1a1a}
header{background:#534AB7;color:#fff;padding:16px 24px;display:flex;align-items:center;gap:12px}
header h1{font-size:18px;font-weight:500}
header span{font-size:13px;opacity:.75;margin-left:auto}
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:20px 24px 0}
.kpi{background:#fff;border:0.5px solid #e0e0e0;border-radius:10px;padding:14px 16px}
.kpi label{font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.5px}
.kpi .val{font-size:24px;font-weight:500;color:#1a1a1a;margin-top:4px}
.kpi .sub{font-size:11px;color:#888;margin-top:2px}
.search-bar{padding:16px 24px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.search-bar input,.search-bar select{padding:8px 12px;border:0.5px solid #d0d0d0;border-radius:8px;font-size:13px;background:#fff;outline:none}
.search-bar input{flex:1;min-width:180px}
.search-bar button{padding:8px 18px;background:#534AB7;color:#fff;border:none;border-radius:8px;font-size:13px;cursor:pointer}
.search-bar button:hover{background:#3C3489}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#fafafa;font-weight:500;color:#555;text-align:left;padding:10px 12px;border-bottom:1px solid #eee;position:sticky;top:0}
td{padding:10px 12px;border-bottom:0.5px solid #f0f0f0;color:#333}
tr:hover td{background:#f9f8ff}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500}
.badge-high{background:#FAECE7;color:#993C1D}
.badge-medium{background:#FAEEDA;color:#633806}
.badge-low{background:#E1F5EE;color:#085041}
.badge-champions{background:#EEEDFE;color:#3C3489}
.badge-loyal{background:#E1F5EE;color:#085041}
.badge-atrisk{background:#FAEEDA;color:#633806}
.badge-lost{background:#FAECE7;color:#993C1D}
.table-wrap{background:#fff;border:0.5px solid #e0e0e0;border-radius:10px;margin:0 24px 24px;overflow:auto;max-height:420px}
.section-title{padding:16px 24px 4px;font-size:13px;font-weight:500;color:#534AB7}
#count{font-size:12px;color:#888;padding:0 24px 8px}
</style>
</head>
<body>
<header>
  <svg width="22" height="22" fill="none" stroke="#fff" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>
  <h1>Retail Customer Intelligence Dashboard</h1>
  <span>Personal Project &nbsp;|&nbsp; 10,000 transactions · 1,104 customers</span>
</header>

<div class="kpi-row" id="kpis"></div>

<div class="search-bar">
  <input id="search" type="text" placeholder="Search customer ID or city..." oninput="load()">
  <select id="seg" onchange="load()">
    <option value="">All segments</option>
    <option>Champions</option>
    <option>Loyal customers</option>
    <option>At-risk</option>
    <option>Lost / inactive</option>
  </select>
  <select id="risk" onchange="load()">
    <option value="">All churn risk</option>
    <option>High</option>
    <option>Medium</option>
    <option>Low</option>
  </select>
  <button onclick="load()">Search ↗</button>
</div>
<div id="count"></div>
<p class="section-title">Customer list</p>
<div class="table-wrap">
  <table>
    <thead><tr>
      <th>Customer ID</th><th>City</th><th>Orders</th>
      <th>Lifetime value</th><th>Segment</th><th>Churn risk</th><th>Last order</th>
    </tr></thead>
    <tbody id="tbody"></tbody>
  </table>
</div>

<script>
async function kpis(){
  const r = await fetch('/api/kpis'); const d = await r.json();
  document.getElementById('kpis').innerHTML = [
    ['Total revenue','₹'+d.revenue,'across all orders'],
    ['Customers',d.customers,'unique buyers'],
    ['Avg order value','₹'+d.aov,'per transaction'],
    ['High churn risk',d.churn_high,'customers flagged']
  ].map(([l,v,s])=>`<div class="kpi"><label>${l}</label><div class="val">${v}</div><div class="sub">${s}</div></div>`).join('');
}
async function load(){
  const q=document.getElementById('search').value;
  const seg=document.getElementById('seg').value;
  const risk=document.getElementById('risk').value;
  const r=await fetch(`/api/customers?q=${encodeURIComponent(q)}&seg=${encodeURIComponent(seg)}&risk=${encodeURIComponent(risk)}`);
  const d=await r.json();
  document.getElementById('count').textContent = `Showing ${d.length} customers`;
  const segClass={Champions:'champions','Loyal customers':'loyal','At-risk':'atrisk','Lost / inactive':'lost'};
  document.getElementById('tbody').innerHTML = d.map(c=>`
    <tr>
      <td><b>${c.customer_id}</b></td>
      <td>${c.city}</td>
      <td>${c.total_orders}</td>
      <td>₹${Number(c.lifetime_value).toLocaleString('en-IN')}</td>
      <td><span class="badge badge-${segClass[c.segment]||'loyal'}">${c.segment}</span></td>
      <td><span class="badge badge-${(c.churn_risk||'').toLowerCase()}">${c.churn_risk||'—'}</span></td>
      <td>${c.last_order}</td>
    </tr>`).join('');
}
kpis(); load();
</script>
</body>
</html>'''

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/kpis')
def api_kpis():
    conn = get_db()
    row = conn.execute('''
        SELECT ROUND(SUM(total_amount),0) revenue,
               COUNT(DISTINCT customer_id) customers,
               ROUND(AVG(total_amount),0) aov
        FROM transactions''').fetchone()
    
    BASE = os.path.dirname(os.path.abspath(__file__))
    churn_df = pd.read_csv(os.path.join(BASE, 'data', 'churn_scores.csv'))
    churn_high = int((churn_df['churn_risk'] == 'High').sum())
    conn.close()
    rev = int(row['revenue'])
    return jsonify({
        'revenue': f'{rev/1e5:.1f}L',
        'customers': int(row['customers']),
        'aov': f"{int(row['aov']):,}",
        'churn_high': churn_high
    })

@app.route('/api/customers')
def api_customers():
    q    = request.args.get('q','').strip()
    seg  = request.args.get('seg','').strip()
    risk = request.args.get('risk','').strip()

    BASE = os.path.dirname(os.path.abspath(__file__))
    churn_df = pd.read_csv(os.path.join(BASE, 'data', 'churn_scores.csv'))

    
    conn = get_db()
    customers_df = pd.read_sql('SELECT * FROM customers', conn)
    conn.close()

    df = customers_df.merge(
        churn_df[['customer_id','segment','churn_risk']],
        on='customer_id', how='left'
    )
    df = df.rename(columns={'total_spent':'lifetime_value','last_order':'last_order','total_orders':'total_orders'})

    if q:
        df = df[df['customer_id'].str.contains(q, case=False) | df['city'].str.contains(q, case=False)]
    if seg:
        df = df[df['segment'] == seg]
    if risk:
        df = df[df['churn_risk'] == risk]

    df = df.sort_values('lifetime_value', ascending=False).head(100)
    return jsonify(df[['customer_id','city','total_orders','lifetime_value','segment','churn_risk','last_order']].fillna('—').to_dict('records'))

if __name__ == '__main__':
    app.run(debug=False)
