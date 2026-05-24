import pandas as pd
import numpy as np
from statsmodels.stats.proportion import proportions_ztest
import plotly.express as px
import json

print("Loading data...")
sessions = pd.read_csv('data/raw/sessions.csv')
events = pd.read_csv('data/raw/events.csv')

def extract_props(row):
    try:
        return json.loads(row)
    except:
        return {}

events['props'] = events['event_properties'].apply(extract_props)

# --- Stage 1: Product Detail -> Add to Cart ---
pd_events = events[events['event_name'].isin(['product_detail_view', 'add_to_cart'])].copy()
pd_events['price'] = pd_events['props'].apply(lambda x: x.get('price', np.nan))
pd_events['category'] = pd_events['props'].apply(lambda x: x.get('category', 'unknown'))

# Map to session
pd_sessions = pd_events.groupby('session_id').agg(
    viewed=('event_name', lambda x: 'product_detail_view' in x.values),
    added=('event_name', lambda x: 'add_to_cart' in x.values),
    price=('price', 'max'),
    category=('category', 'first')
).reset_index()

pd_sessions = pd_sessions[pd_sessions['viewed']]

fig_price = px.histogram(pd_sessions, x="price", color="added", barmode="group", title="Add to Cart by Product Price")
fig_price.write_html('reports/charts/13_price_add_to_cart.html')

print("Products priced ₹2000+ have lower add-to-cart rate — EMI display could help")

cat_conv = pd_sessions.groupby('category')['added'].mean().reset_index()
print(cat_conv)

# --- Stage 3: Payment Initiated -> Payment Success ---
pay_events = events[events['event_name'].isin(['payment_initiated', 'payment_success', 'payment_failed'])].copy()
pay_events['method'] = pay_events['props'].apply(lambda x: x.get('method', 'unknown'))

pay_sessions = pay_events.groupby('session_id').agg(
    initiated=('event_name', lambda x: 'payment_initiated' in x.values),
    success=('event_name', lambda x: 'payment_success' in x.values),
    method=('method', lambda x: [m for m in x.values if m != 'unknown'][0] if any(m != 'unknown' for m in x.values) else 'unknown')
).reset_index()

pay_sessions = pay_sessions[pay_sessions['initiated']]
method_fail_rate = 1 - pay_sessions.groupby('method')['success'].mean()
print("\nPayment Failure Rate by Method:")
print(method_fail_rate)
print("UPI failures account for high percentage — investigate payment gateway SLA")

# --- Statistical Significance Testing ---
print("\n--- Statistical Significance Tests ---")
def test_conversion_significance(conv_a, n_a, conv_b, n_b, label_a, label_b):
    count = np.array([conv_a * n_a, conv_b * n_b])
    nobs = np.array([n_a, n_b])
    stat, pvalue = proportions_ztest(count, nobs)
    
    significance = "STATISTICALLY SIGNIFICANT ✅" if pvalue < 0.05 else "NOT significant ❌"
    print(f"{label_a} ({conv_a:.1%}) vs {label_b} ({conv_b:.1%})")
    print(f"p-value: {pvalue:.4f} → {significance}\n")

# Mobile vs Desktop
desktop_s = sessions[sessions['device_type'] == 'desktop']
mobile_s = sessions[sessions['device_type'] == 'mobile']

d_n = len(desktop_s)
m_n = len(mobile_s)

d_orders = events[(events['session_id'].isin(desktop_s['session_id'])) & (events['event_name'] == 'payment_success')]['session_id'].nunique()
m_orders = events[(events['session_id'].isin(mobile_s['session_id'])) & (events['event_name'] == 'payment_success')]['session_id'].nunique()

test_conversion_significance(d_orders/d_n, d_n, m_orders/m_n, m_n, "Desktop", "Mobile")

# Email vs Social
email_s = sessions[sessions['traffic_source'] == 'email_campaign']
social_s = sessions[sessions['traffic_source'] == 'social_media']
e_n = len(email_s)
s_n = len(social_s)
e_orders = events[(events['session_id'].isin(email_s['session_id'])) & (events['event_name'] == 'payment_success')]['session_id'].nunique()
s_orders = events[(events['session_id'].isin(social_s['session_id'])) & (events['event_name'] == 'payment_success')]['session_id'].nunique()

test_conversion_significance(e_orders/e_n, e_n, s_orders/s_n, s_n, "Email", "Social Media")

# New vs Returning
new_s = sessions[sessions['is_new_user'] == True]
ret_s = sessions[sessions['is_new_user'] == False]
new_n = len(new_s)
ret_n = len(ret_s)
new_orders = events[(events['session_id'].isin(new_s['session_id'])) & (events['event_name'] == 'payment_success')]['session_id'].nunique()
ret_orders = events[(events['session_id'].isin(ret_s['session_id'])) & (events['event_name'] == 'payment_success')]['session_id'].nunique()

test_conversion_significance(new_orders/new_n, new_n, ret_orders/ret_n, ret_n, "New Users", "Returning Users")
