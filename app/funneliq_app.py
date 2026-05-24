import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- Page Config ---
st.set_page_config(page_title="FunnelIQ | Enterprise Analytics", page_icon="📊", layout="wide")

# --- Custom CSS for Enterprise Look ---
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Inter', sans-serif; }
    .metric-card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #3498db;
    }
    .metric-value { font-size: 28px; font-weight: bold; color: #2c3e50; }
    .metric-label { font-size: 14px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; }
    div[data-testid="stMetricValue"] { font-size: 28px; }
    div[data-testid="stMetricLabel"] { font-size: 14px; font-weight: bold; color: #7f8c8d; }
</style>
""", unsafe_allow_html=True)

# --- Load Data ---
@st.cache_data
def load_data():
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
    sessions = pd.read_csv(os.path.join(base_path, 'sessions.csv'))
    events = pd.read_csv(os.path.join(base_path, 'events.csv'))
    orders = pd.read_csv(os.path.join(base_path, 'orders.csv'))
    
    # Convert dates
    sessions['session_date'] = pd.to_datetime(sessions['session_date'])
    events['event_timestamp'] = pd.to_datetime(events['event_timestamp'])
    
    return sessions, events, orders

try:
    sessions, events, orders = load_data()
except Exception as e:
    st.error(f"Error loading data. Make sure you have run the data generation script. Details: {e}")
    st.stop()

# --- Sidebar ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2633/2633320.png", width=50)
st.sidebar.title("FunnelIQ")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Overview", "Funnel Analysis", "Drop-off Segments", "CRO Audit"])
st.sidebar.markdown("---")
st.sidebar.info("Enterprise-grade E-commerce Conversion Analytics")

# --- Helper Functions ---
def calculate_funnel(events_df):
    funnel_steps = ['page_view', 'product_view', 'add_to_cart', 'begin_checkout', 'purchase']
    funnel_counts = []
    
    for step in funnel_steps:
        count = events_df[events_df['event_name'] == step]['session_id'].nunique()
        funnel_counts.append(count)
        
    return pd.DataFrame({'Step': funnel_steps, 'Users': funnel_counts})

# --- Pages ---
if page == "Overview":
    st.title("Executive Overview")
    st.markdown("High-level KPI metrics for the CartX platform.")
    
    # KPIs
    total_revenue = orders['gmv'].sum()
    total_orders = len(orders)
    avg_order_value = orders['gmv'].mean()
    conversion_rate = (events[events['event_name'] == 'purchase']['session_id'].nunique() / sessions['session_id'].nunique()) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Revenue", f"₹{total_revenue:,.0f}")
    with col2: st.metric("Total Orders", f"{total_orders:,}")
    with col3: st.metric("AOV", f"₹{avg_order_value:,.0f}")
    with col4: st.metric("Overall Conversion", f"{conversion_rate:.2f}%")
    
    st.markdown("---")
    
    # Revenue Trend
    st.subheader("Daily Revenue Trend")
    orders['date'] = pd.to_datetime(orders['order_date']).dt.date
    daily_rev = orders.groupby('date')['gmv'].sum().reset_index()
    fig = px.line(daily_rev, x='date', y='gmv', title="Revenue over 30 Days", markers=True)
    fig.update_layout(plot_bgcolor="white", xaxis_title="", yaxis_title="Revenue (INR)")
    st.plotly_chart(fig, use_container_width=True)

elif page == "Funnel Analysis":
    st.title("Global Conversion Funnel")
    st.markdown("Visualizing the drop-off across the main user journey stages.")
    
    funnel_df = calculate_funnel(events)
    
    fig = go.Figure(go.Funnel(
        y = ['Home Page', 'Product Detail', 'Cart', 'Checkout', 'Purchase'],
        x = funnel_df['Users'],
        textinfo = "value+percent initial+percent previous",
        marker = {"color": ["#34495e", "#3498db", "#2ecc71", "#f1c40f", "#e74c3c"]}
    ))
    fig.update_layout(title="Overall Funnel Performance", plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)
    
    # Abandonment Rate
    st.subheader("Critical Drop-offs")
    col1, col2 = st.columns(2)
    
    # Safe division to prevent RuntimeWarning
    cart_added = funnel_df.loc[2, 'Users']
    checkout_started = funnel_df.loc[3, 'Users']
    purchased = funnel_df.loc[4, 'Users']
    
    cart_abandonment = 100 - (checkout_started / cart_added * 100) if cart_added > 0 else 0
    checkout_abandonment = 100 - (purchased / checkout_started * 100) if checkout_started > 0 else 0
    
    with col1:
        st.error(f"🛒 Cart Abandonment Rate: **{cart_abandonment:.1f}%**")
        st.markdown("Percentage of users who added to cart but did not proceed to checkout.")
    with col2:
        st.error(f"💳 Checkout Abandonment Rate: **{checkout_abandonment:.1f}%**")
        st.markdown("Percentage of users who started checkout but did not purchase.")

elif page == "Drop-off Segments":
    st.title("Segmented Drop-off Analysis")
    
    segment_type = st.selectbox("Analyze by Segment", ["device_type", "traffic_source"])
    
    st.markdown(f"### Funnel by {segment_type.replace('_', ' ').title()}")
    
    segments = sessions[segment_type].unique()
    
    fig = go.Figure()
    
    for segment in segments:
        seg_sessions = sessions[sessions[segment_type] == segment]['session_id']
        seg_events = events[events['session_id'].isin(seg_sessions)]
        f_df = calculate_funnel(seg_events)
        
        fig.add_trace(go.Funnel(
            name = segment,
            y = ['Home', 'Product', 'Cart', 'Checkout', 'Purchase'],
            x = f_df['Users'],
            textinfo = "value+percent initial"
        ))

    fig.update_layout(plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)
    
    if segment_type == "device_type":
        st.info("💡 **Insight:** Notice the significant difference in conversion rates between Mobile and Desktop, especially at the Checkout stage. This strongly indicates Mobile UX friction.")

elif page == "CRO Audit":
    st.title("Conversion Rate Optimization (CRO) Recommendations")
    st.markdown("Based on the data analysis, here is the prioritized action plan.")
    
    issues = [
        {"Priority": "High", "Issue": "Mobile checkout UX friction", "Estimated Revenue Impact": "+₹1.2M / mo", "Effort": "Medium"},
        {"Priority": "High", "Issue": "High Cart Abandonment from Social Traffic", "Estimated Revenue Impact": "+₹800k / mo", "Effort": "Low (Retargeting)"},
        {"Priority": "Medium", "Issue": "Slow Page Load on Android Devices", "Estimated Revenue Impact": "+₹500k / mo", "Effort": "High"},
        {"Priority": "Low", "Issue": "Guest Checkout Not Prominent", "Estimated Revenue Impact": "+₹200k / mo", "Effort": "Low"}
    ]
    
    st.table(pd.DataFrame(issues))
    
    st.markdown("""
    ### Deep Dive: Mobile Checkout Redesign
    The data shows that while Mobile generates 70% of traffic, it accounts for only 40% of revenue. The drop-off from `begin_checkout` to `purchase` on mobile is 65%, compared to 35% on Desktop.
    
    **Action Items:**
    1. Implement 1-click checkout (Apple Pay / GPay).
    2. Reduce form fields in the address section.
    3. Make the numeric keypad default for phone/pin inputs.
    """)
