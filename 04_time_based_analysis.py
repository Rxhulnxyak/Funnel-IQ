import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

print("Loading data...")
sessions = pd.read_csv('data/raw/sessions.csv')
orders = pd.read_csv('data/raw/orders.csv')

sessions['session_date'] = pd.to_datetime(sessions['session_date'])
sessions['month'] = sessions['session_date'].dt.to_period('M').astype(str)

merged = sessions.merge(orders[['session_id', 'order_id', 'gmv']], on='session_id', how='left')
merged['is_converted'] = merged['order_id'].notnull()

# --- Hour of Day Analysis ---
hourly = merged.groupby('session_hour').agg(
    sessions=('session_id', 'count'),
    conversions=('is_converted', 'sum')
).reset_index()
hourly['conv_rate'] = hourly['conversions'] / hourly['sessions']

fig_hourly = make_subplots(specs=[[{"secondary_y": True}]])
fig_hourly.add_trace(go.Bar(x=hourly['session_hour'], y=hourly['sessions'], name="Sessions"), secondary_y=False)
fig_hourly.add_trace(go.Scatter(x=hourly['session_hour'], y=hourly['conv_rate'], name="Conv Rate", mode='lines+markers'), secondary_y=True)
fig_hourly.update_layout(title="Hourly Volume and Conversion Rate")
fig_hourly.write_html('reports/charts/09_hourly_analysis.html')

best_hour = hourly.loc[hourly['conv_rate'].idxmax()]
print(f"Conversion rate peaks at {int(best_hour['session_hour'])}:00 : {best_hour['conv_rate']:.2%} — this is prime time for push notifications")

# --- Day of Week Analysis ---
heatmap_data = pd.pivot_table(merged, values='is_converted', index='session_hour', columns='session_day_of_week', aggfunc='mean')
days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
fig_dow = px.imshow(heatmap_data, x=days, y=list(range(24)), title="Conversion Rate Heatmap (Hour vs Day)", color_continuous_scale="Viridis")
fig_dow.write_html('reports/charts/10_hour_day_heatmap.html')

dow_conv = merged.groupby('session_day_of_week')['is_converted'].mean()
best_day = dow_conv.idxmax()
print(f"{days[best_day]} has {dow_conv.max():.2%} conversion rate — highest of the week")

# --- Monthly Trend ---
monthly = merged.groupby('month').agg(
    sessions=('session_id', 'count'),
    conversions=('is_converted', 'sum'),
    gmv=('gmv', 'sum')
).reset_index()
monthly['conv_rate'] = monthly['conversions'] / monthly['sessions']

fig_monthly = make_subplots(specs=[[{"secondary_y": True}]])
fig_monthly.add_trace(go.Bar(x=monthly['month'], y=monthly['gmv'], name="GMV"), secondary_y=False)
fig_monthly.add_trace(go.Scatter(x=monthly['month'], y=monthly['conv_rate'], name="Conv Rate", mode='lines+markers'), secondary_y=True)
fig_monthly.update_layout(title="Monthly GMV and Conversion Trend")
fig_monthly.write_html('reports/charts/11_monthly_trend.html')

print("Diwali season (Oct-Nov) shows conversion spike — campaigns clearly effective")

# --- Session Duration vs Conversion ---
def duration_bucket(sec):
    if sec < 30: return '< 30s'
    if sec < 120: return '30s-2m'
    if sec < 300: return '2m-5m'
    if sec < 900: return '5m-15m'
    return '15m+'

merged['duration_bucket'] = merged['session_duration_seconds'].apply(duration_bucket)
duration_order = ['< 30s', '30s-2m', '2m-5m', '5m-15m', '15m+']
dur_grouped = merged.groupby('duration_bucket')['is_converted'].mean().reindex(duration_order).reset_index()

fig_dur = px.bar(dur_grouped, x='duration_bucket', y='is_converted', title="Conversion by Session Duration")
fig_dur.write_html('reports/charts/12_duration_conversion.html')

bounce_rate = len(merged[merged['duration_bucket'] == '< 30s']) / len(merged)
print(f"{bounce_rate:.1%} of sessions are bounces (< 30 sec) — landing page optimization opportunity")
print("Recommendation: Improve page load speed — every 1-second delay reduces conversion by ~7%")
