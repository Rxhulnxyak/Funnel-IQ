import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json

print("Loading data...")
sessions = pd.read_csv('data/raw/sessions.csv')
events = pd.read_csv('data/raw/events.csv')
orders = pd.read_csv('data/raw/orders.csv')

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

def build_segment_funnel(segment_col, df_sessions, df_events):
    results = []
    unique_segments = df_sessions[segment_col].unique()
    
    for seg in unique_segments:
        seg_sessions = df_sessions[df_sessions[segment_col] == seg]['session_id']
        seg_events = df_events[df_events['session_id'].isin(seg_sessions)]
        
        counts = []
        for event_name, stage_label in FUNNEL_STAGES:
            count = seg_events[seg_events['event_name'] == event_name]['session_id'].nunique()
            counts.append(count)
        
        results.append({
            'segment': seg,
            'counts': counts,
            'total_sessions': len(seg_sessions)
        })
    return results

# --- Segment 1: By Device Type ---
device_funnels = build_segment_funnel('device_type', sessions, events)
# Chart: Grouped bar chart for conversion rate at each stage
fig_device = go.Figure()
for dfun in device_funnels:
    conv_rates = [c / dfun['total_sessions'] for c in dfun['counts']]
    fig_device.add_trace(go.Bar(
        name=dfun['segment'],
        x=[l for _, l in FUNNEL_STAGES],
        y=conv_rates
    ))
fig_device.update_layout(barmode='group', title='Conversion Rate at Each Stage by Device')
fig_device.write_html('reports/charts/06_device_funnel.html')

# Mobile vs Desktop conversion rate comparison
desktop_cr = next(d['counts'][-1]/d['total_sessions'] for d in device_funnels if d['segment']=='desktop')
mobile_cr = next(d['counts'][-1]/d['total_sessions'] for d in device_funnels if d['segment']=='mobile')
print(f"Mobile conversion rate: {mobile_cr:.2%} vs Desktop: {desktop_cr:.2%} - gap of {(desktop_cr - mobile_cr)*100:.1f} percentage points")
print("Recommendation: Mobile checkout UX needs to be redesigned — reduce form fields, add UPI shortcuts")

# --- Segment 2: By Traffic Source ---
source_funnels = build_segment_funnel('traffic_source', sessions, events)
source_cr = {d['segment']: d['counts'][-1]/d['total_sessions'] for d in source_funnels}
fig_source = px.bar(x=list(source_cr.keys()), y=list(source_cr.values()), title="Overall Conversion Rate by Traffic Source")
fig_source.write_html('reports/charts/07_source_conversion.html')

best_source = max(source_cr, key=source_cr.get)
print(f"{best_source} converts at {source_cr[best_source]:.2%} — highest of all channels")
print("Recommendation: Shift 15% of social budget to email/referral campaigns")

# --- Segment 3: By City Tier ---
tier1 = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai']
tier2 = ['Pune', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Lucknow']
sessions['city_tier'] = sessions['city'].apply(lambda x: 'Tier 1' if x in tier1 else ('Tier 2' if x in tier2 else 'Tier 3'))
tier_funnels = build_segment_funnel('city_tier', sessions, events)

# Payment method mix by tier
tier2_sessions = sessions[sessions['city_tier'] == 'Tier 2']['session_id']
tier2_orders = orders[orders['session_id'].isin(tier2_sessions)]
tier2_cod_rate = len(tier2_orders[tier2_orders['payment_method'] == 'cod']) / len(tier2_orders) if len(tier2_orders) > 0 else 0

print(f"Tier-2 cities have {tier2_cod_rate:.1%} COD rate — checkout should show COD as first option for these users")

# --- Segment 4: Combined Heatmap ---
pivot = pd.pivot_table(
    sessions.merge(orders[['session_id', 'order_id']], on='session_id', how='left'),
    values='order_id', 
    index='traffic_source', 
    columns='device_type', 
    aggfunc=lambda x: x.count() / len(x) # conversion rate
)

fig_heat = px.imshow(pivot, text_auto=".2%", title="Conversion Rate Heatmap (Source vs Device)", color_continuous_scale="RdYlGn")
fig_heat.write_html('reports/charts/08_source_device_heatmap.html')

best_combo = pivot.unstack().idxmax()
worst_combo = pivot.unstack().idxmin()
print(f"Best: {best_combo[1]} × {best_combo[0]} = {pivot.loc[best_combo[1], best_combo[0]]:.2%} conversion")
print(f"Worst: {worst_combo[1]} × {worst_combo[0]} = {pivot.loc[worst_combo[1], worst_combo[0]]:.2%} conversion")
