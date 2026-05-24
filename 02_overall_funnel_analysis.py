import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- 1. Load Data ---
print("Loading data...")
sessions = pd.read_csv('data/raw/sessions.csv')
events = pd.read_csv('data/raw/events.csv')
orders = pd.read_csv('data/raw/orders.csv')

# --- 2. Master Funnel Logic ---
FUNNEL_STAGES = [
    ('page_view',               'Session Started'),
    ('product_listing_view',    'Browsed Products'),
    ('product_detail_view',     'Viewed Product Detail'),
    ('add_to_cart',             'Added to Cart'),
    ('cart_view',               'Viewed Cart'),
    ('checkout_initiated',      'Started Checkout'),
    ('address_filled',          'Filled Address'),
    ('payment_method_selected', 'Selected Payment'),
    ('payment_initiated',       'Initiated Payment'),
    ('payment_success',         'Completed Purchase'),
]

# Calculate sessions reaching each stage
stage_counts = []
for event_name, stage_label in FUNNEL_STAGES:
    count = events[events['event_name'] == event_name]['session_id'].nunique()
    stage_counts.append({'stage_name': event_name, 'stage_label': stage_label, 'session_count': count})

funnel_df = pd.DataFrame(stage_counts)
total_sessions = funnel_df['session_count'].iloc[0]

funnel_df['overall_conv_rate'] = funnel_df['session_count'] / total_sessions
funnel_df['stage_conv_rate'] = funnel_df['session_count'] / funnel_df['session_count'].shift(1)
funnel_df.loc[0, 'stage_conv_rate'] = 1.0

funnel_df['dropoff_count'] = funnel_df['session_count'].shift(1) - funnel_df['session_count']
funnel_df['dropoff_rate'] = funnel_df['dropoff_count'] / funnel_df['session_count'].shift(1)

# Revenue leakage
total_gmv = orders['gmv'].sum()
total_orders = len(orders)
avg_order_value = total_gmv / total_orders if total_orders > 0 else 0
final_conv_rate = funnel_df['overall_conv_rate'].iloc[-1]

funnel_df['revenue_lost'] = funnel_df['dropoff_count'] * final_conv_rate * avg_order_value

print("Funnel DataFrame:")
print(funnel_df)

# Save processed data
funnel_df.to_csv('data/processed/funnel_overall.csv', index=False)

# --- 3. Visualizations ---
# Chart 1: Funnel Waterfall
fig_funnel = go.Figure(go.Funnel(
    y=funnel_df['stage_label'],
    x=funnel_df['session_count'],
    textinfo="value+percent initial",
    marker={"color": px.colors.sequential.Blues_r}
))
fig_funnel.update_layout(title="Overall Funnel Waterfall")
fig_funnel.write_html('reports/charts/01_funnel_waterfall.html')

# Chart 2: Drop-off Bar Chart
# Sort descending by dropoff_count
dropoff_df = funnel_df.dropna(subset=['dropoff_count']).sort_values('dropoff_count', ascending=True)
colors = ['grey'] * len(dropoff_df)
colors[-1] = 'red'
colors[-2] = 'red'

fig_dropoff = go.Figure(go.Bar(
    x=dropoff_df['dropoff_count'],
    y=dropoff_df['stage_label'],
    orientation='h',
    marker_color=colors,
    text=dropoff_df['revenue_lost'].apply(lambda x: f"₹{x/100000:.1f}L lost"),
    textposition='auto'
))
fig_dropoff.update_layout(title="Top Drop-off Stages (Volume)")
fig_dropoff.write_html('reports/charts/02_dropoff_bar.html')

# Chart 3: Conversion Rate Waterfall (Value Destruction)
fig_val_dest = go.Figure(go.Waterfall(
    name="Conversion",
    orientation="v",
    measure=["relative"] * (len(funnel_df)-1) + ["total"],
    x=funnel_df['stage_label'],
    y=[-x for x in funnel_df['dropoff_rate'].fillna(0).tolist()[1:]] + [final_conv_rate],
    connector={"line":{"color":"rgb(63, 63, 63)"}},
))
fig_val_dest.update_layout(title="Conversion Rate Erosion")
fig_val_dest.write_html('reports/charts/03_conversion_waterfall.html')

# Chart 4: Session Flow Sankey Diagram
# Simplified nodes
nodes = list(funnel_df['stage_label']) + ['Dropped Off']
drop_node_idx = len(nodes) - 1

source = []
target = []
value = []

for i in range(len(funnel_df)-1):
    # Flow to next stage
    source.append(i)
    target.append(i+1)
    value.append(funnel_df['session_count'].iloc[i+1])
    
    # Flow to drop off
    source.append(i)
    target.append(drop_node_idx)
    value.append(funnel_df['dropoff_count'].iloc[i+1])

fig_sankey = go.Figure(data=[go.Sankey(
    node = dict(
      pad = 15,
      thickness = 20,
      line = dict(color = "black", width = 0.5),
      label = nodes,
      color = "blue"
    ),
    link = dict(
      source = source,
      target = target,
      value = value
  ))])

fig_sankey.update_layout(title_text="Session Flow Sankey Diagram", font_size=10)
fig_sankey.write_html('reports/charts/04_sankey.html')

# --- 4. Payment Failure Analysis ---
payment_initiated = events[events['event_name'] == 'payment_initiated']
payment_failed = events[events['event_name'] == 'payment_failed']

payment_init_count = len(payment_initiated)
payment_fail_count = len(payment_failed)
payment_fail_rate = payment_fail_count / payment_init_count if payment_init_count > 0 else 0

print(f"Payment Failure Rate: {payment_fail_rate:.1%}")

import json
failed_reasons = []
for idx, row in payment_failed.iterrows():
    try:
        props = json.loads(row['event_properties'])
        failed_reasons.append(props.get('reason', 'unknown'))
    except:
        failed_reasons.append('unknown')

reasons_df = pd.Series(failed_reasons).value_counts().reset_index()
reasons_df.columns = ['Reason', 'Count']

fig_pie = px.pie(reasons_df, names='Reason', values='Count', title="Payment Failure Reasons")
fig_pie.write_html('reports/charts/05_payment_failure_pie.html')

# Summary Insights
print("\n--- Insights ---")
print(f"Total addressable revenue lost: ₹{funnel_df['revenue_lost'].sum()/100000:.1f} lakh per month")
top_leak = dropoff_df.iloc[-1]
print(f"Top leakage point: {top_leak['stage_label']} losing ₹{top_leak['revenue_lost']/100000:.1f} lakh/month")
