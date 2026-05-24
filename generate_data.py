import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
import json
import random
from faker import Faker
import os

fake = Faker('en_IN')
np.random.seed(42)
random.seed(42)

# --- Configuration ---
NUM_USERS = 40000
NUM_SESSIONS = 150000
START_DATE = datetime(2023, 7, 1)
END_DATE = datetime(2024, 6, 30)

CITIES = {
    'Mumbai': 'Maharashtra',
    'Delhi': 'Delhi',
    'Bangalore': 'Karnataka',
    'Hyderabad': 'Telangana',
    'Chennai': 'Tamil Nadu',
    'Pune': 'Maharashtra',
    'Kolkata': 'West Bengal',
    'Ahmedabad': 'Gujarat',
    'Jaipur': 'Rajasthan',
    'Lucknow': 'Uttar Pradesh'
}
CITY_WEIGHTS = [0.18, 0.15, 0.15, 0.1, 0.08, 0.08, 0.07, 0.07, 0.06, 0.06]

print("Generating Data for FunnelIQ...")

# --- 1. Generate Dates with Seasonality ---
# Peak in Oct-Nov (Diwali/Big Billion Days) -> 2.5x volume
# Dip in Jan-Feb
date_list = []
curr = START_DATE
while curr <= END_DATE:
    date_list.append(curr)
    curr += timedelta(days=1)

date_weights = []
for d in date_list:
    w = 1.0
    if d.month in [10, 11]: w = 2.5
    elif d.month in [1, 2]: w = 0.6
    if d.weekday() >= 5: w *= 1.3 # Weekend boost
    date_weights.append(w)

date_probs = np.array(date_weights) / sum(date_weights)
session_dates = np.random.choice(date_list, size=NUM_SESSIONS, p=date_probs)

# Sort sessions chronologically
session_dates.sort()

# --- 2. Generate Users ---
user_ids = [str(uuid.uuid4()) for _ in range(NUM_USERS)]
age_buckets = ['18-24', '25-34', '35-44', '45+']
age_probs = [0.25, 0.40, 0.20, 0.15]
genders = ['M', 'F', 'Other']
gender_probs = [0.55, 0.40, 0.05]
categories = ['fashion', 'electronics', 'home_decor', 'beauty', 'sports']

users_data = {
    'user_id': user_ids,
    'first_seen_date': [None]*NUM_USERS, # will fill later
    'age_bucket': np.random.choice(age_buckets, NUM_USERS, p=age_probs),
    'gender': np.random.choice(genders, NUM_USERS, p=gender_probs),
    'preferred_device': np.random.choice(['mobile', 'desktop', 'tablet'], NUM_USERS, p=[0.68, 0.27, 0.05]),
    'preferred_category': np.random.choice(categories, NUM_USERS),
    'email_opt_in': np.random.choice([True, False], NUM_USERS, p=[0.6, 0.4]),
    'push_opt_in': np.random.choice([True, False], NUM_USERS, p=[0.4, 0.6])
}

# Distribute sessions to users (Zipf distribution for repeat users)
# We have 150k sessions and 40k users.
session_user_ids = np.random.choice(user_ids, size=NUM_SESSIONS, p=np.random.dirichlet(np.ones(NUM_USERS), size=1)[0])

# --- 3. Generate Sessions ---
hours = list(range(24))
# Peak 8-10pm (20, 21, 22), Lunch 1-2pm (13, 14)
hour_weights = [1]*8 + [1.5]*3 + [2]*2 + [2.5]*2 + [2]*5 + [3.5]*3 + [1.5]
hour_probs = np.array(hour_weights) / sum(hour_weights)

sources = ['organic_search', 'paid_search', 'social_media', 'email_campaign', 'direct', 'affiliate', 'push_notification']
source_probs = [0.28, 0.22, 0.20, 0.12, 0.10, 0.05, 0.03]

landing_pages = ['homepage', 'category_page', 'product_page', 'sale_page', 'brand_page']

sessions = []
user_first_seen = {}

for i in range(NUM_SESSIONS):
    uid = session_user_ids[i]
    s_date = session_dates[i]
    
    if uid not in user_first_seen:
        user_first_seen[uid] = s_date
        is_new = True
    else:
        is_new = False
        
    hr = np.random.choice(hours, p=hour_probs)
    dt = s_date + timedelta(hours=int(hr), minutes=random.randint(0,59), seconds=random.randint(0,59))
    
    device = np.random.choice(['mobile', 'desktop', 'tablet'], p=[0.68, 0.27, 0.05])
    source = np.random.choice(sources, p=source_probs)
    city = np.random.choice(list(CITIES.keys()), p=CITY_WEIGHTS)
    
    is_logged_in = True if not is_new and random.random() > 0.3 else (random.random() > 0.7)
    
    utm = f"campaign_{source}_{dt.strftime('%b')}" if source in ['paid_search', 'social_media', 'affiliate'] else None
    
    # Session duration (mobile shorter)
    dur = random.expovariate(1/180) # avg 3 mins
    if device == 'mobile': dur *= 0.8
    if device == 'desktop': dur *= 1.3
    
    sessions.append({
        'session_id': str(uuid.uuid4()),
        'user_id': uid,
        'session_date': s_date.strftime('%Y-%m-%d'),
        'session_hour': hr,
        'session_day_of_week': s_date.weekday(),
        'device_type': device,
        'traffic_source': source,
        'landing_page': np.random.choice(landing_pages),
        'city': city,
        'state': CITIES[city],
        'is_new_user': is_new,
        'is_logged_in': is_logged_in,
        'session_duration_seconds': int(dur),
        'utm_campaign': utm,
        'timestamp': dt # internal use
    })

sessions_df = pd.DataFrame(sessions)

# Update users_data
for i, u in enumerate(user_ids):
    users_data['first_seen_date'][i] = user_first_seen.get(u, START_DATE).strftime('%Y-%m-%d')

# --- 4. Generate Events and Funnel logic ---
stages = [
    'page_view', 'product_listing_view', 'product_detail_view', 'add_to_cart', 
    'cart_view', 'checkout_initiated', 'address_filled', 'payment_method_selected', 
    'order_review', 'payment_initiated', 'payment_success'
]

# Baseline conversion probabilities from previous stage
# target end-to-end:
# 100% -> 72% -> 48% -> 31% -> 24% -> 16% -> 13% -> 10% -> 8.5% -> 7% -> 5.2%
conv_rates = {
    'page_view': 1.0,
    'product_listing_view': 0.72,
    'product_detail_view': 0.666, # 48/72
    'add_to_cart': 0.645, # 31/48
    'cart_view': 0.774, # 24/31
    'checkout_initiated': 0.666, # 16/24
    'address_filled': 0.812, # 13/16
    'payment_method_selected': 0.769, # 10/13
    'order_review': 0.85, # 8.5/10
    'payment_initiated': 0.823, # 7/8.5
    'payment_success': 0.742 # 5.2/7
}

events = []
orders = []
event_id_counter = 1

tier2_cities = ['Pune', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Lucknow']

def get_product_price(cat):
    if cat == 'fashion': return random.choice([499, 999, 1299, 1499, 2999])
    if cat == 'electronics': return random.choice([2999, 4999, 9999, 15999, 35999])
    if cat == 'home_decor': return random.choice([299, 599, 899, 1599, 2499])
    if cat == 'beauty': return random.choice([199, 399, 699, 999])
    if cat == 'sports': return random.choice([499, 899, 1999, 3999])
    return 999

for s in sessions:
    sid = s['session_id']
    uid = s['user_id']
    dt = s['timestamp']
    
    # Modifiers based on segment
    mod = 1.0
    if s['device_type'] == 'mobile': mod *= 0.9 # Overall slightly lower, heavily applied at checkout
    if s['traffic_source'] == 'social_media': mod *= 0.6
    if s['traffic_source'] == 'email_campaign': mod *= 1.3
    if s['is_new_user']: mod *= 0.4 # 60% lower conversion vs returning (returning is base/higher)
    if s['session_hour'] in [20, 21, 22]: mod *= 1.1 # Peak hours better
    
    curr_stage_idx = 0
    cat = np.random.choice(categories)
    price = get_product_price(cat)
    cart_value = price * random.randint(1, 3)
    
    payment_method = 'upi'
    
    for i, stage in enumerate(stages):
        if stage == 'page_view':
            prob = 1.0
        else:
            prob = conv_rates[stage] * mod
            
            # Specific stage modifiers
            if stage in ['checkout_initiated', 'address_filled', 'payment_method_selected'] and s['device_type'] == 'mobile':
                prob *= 0.8 # 20% lower conversion at checkout for mobile
            
            if stage == 'payment_success' and s['city'] in tier2_cities:
                prob *= 0.85 # 15% lower at payment for tier 2
                
        if random.random() <= prob:
            # Reached this stage
            props = {}
            if stage in ['product_detail_view', 'add_to_cart']:
                props = {'product_id': random.randint(1000, 5000), 'category': cat, 'price': price}
            elif stage == 'payment_method_selected':
                pm_probs = [0.42, 0.15, 0.05, 0.03, 0.35] if s['city'] not in tier2_cities else [0.35, 0.10, 0.05, 0.02, 0.48] # Tier 2 more COD
                payment_method = np.random.choice(['upi', 'credit_card', 'debit_card', 'netbanking', 'cod'], p=pm_probs)
                props = {'method': payment_method, 'amount': cart_value}
            
            events.append({
                'event_id': event_id_counter,
                'session_id': sid,
                'user_id': uid,
                'event_timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'event_name': stage,
                'event_properties': json.dumps(props),
                'page_url': f"/{stage.replace('_', '-')}",
                'time_on_page_seconds': random.randint(5, 120)
            })
            event_id_counter += 1
            dt += timedelta(seconds=random.randint(5, 60))
            
            # Special case for payment failures
            if stage == 'payment_initiated':
                # Will it fail before success? 15% chance
                if random.random() < 0.15:
                    fail_reasons = ['insufficient_funds', 'card_declined', 'bank_timeout', 'upi_error', 'session_timeout']
                    fail_reason = np.random.choice(fail_reasons, p=[0.2, 0.1, 0.3, 0.3, 0.1])
                    
                    if payment_method == 'upi' and fail_reason == 'card_declined': fail_reason = 'upi_error'
                    if payment_method == 'cod': continue # COD doesn't fail online payment usually
                    
                    dt_fail = dt + timedelta(seconds=random.randint(2, 15))
                    events.append({
                        'event_id': event_id_counter,
                        'session_id': sid,
                        'user_id': uid,
                        'event_timestamp': dt_fail.strftime('%Y-%m-%d %H:%M:%S'),
                        'event_name': 'payment_failed',
                        'event_properties': json.dumps({'method': payment_method, 'amount': cart_value, 'reason': fail_reason}),
                        'page_url': "/payment",
                        'time_on_page_seconds': random.randint(2, 10)
                    })
                    event_id_counter += 1
                    
            if stage == 'payment_success':
                # Create order
                orders.append({
                    'order_id': str(uuid.uuid4()),
                    'session_id': sid,
                    'user_id': uid,
                    'order_date': dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'gmv': cart_value,
                    'discount_applied': True if s['is_new_user'] else (random.random() > 0.5),
                    'coupon_code': 'WELCOME50' if s['is_new_user'] else ('SAVE20' if random.random() > 0.5 else None),
                    'discount_amount': cart_value * 0.2 if s['is_new_user'] else (cart_value * 0.1 if random.random() > 0.5 else 0),
                    'payment_method': payment_method,
                    'delivery_pincode': fake.postcode(),
                    'category': cat,
                    'is_first_order': s['is_new_user'],
                    'device_type': s['device_type']
                })
                
        else:
            break # Drop off

events_df = pd.DataFrame(events)
orders_df = pd.DataFrame(orders)

# Update users with order metrics
user_metrics = orders_df.groupby('user_id').agg(
    total_orders=('order_id', 'count'),
    total_revenue=('gmv', 'sum')
).reset_index()

users_df = pd.DataFrame(users_data)
# Add session counts
session_counts = sessions_df.groupby('user_id').size().reset_index(name='total_sessions')
users_df = users_df.merge(session_counts, on='user_id', how='left').fillna({'total_sessions': 0})
users_df = users_df.merge(user_metrics, on='user_id', how='left').fillna({'total_orders': 0, 'total_revenue': 0})

def get_loyalty(orders):
    if orders == 0: return 'new'
    if orders == 1: return 'bronze'
    if orders <= 3: return 'silver'
    return 'gold'

users_df['loyalty_tier'] = users_df['total_orders'].apply(get_loyalty)

# Drop the temporary timestamp column
sessions_df.drop(columns=['timestamp'], inplace=True)

# Save to CSV
print("Saving CSV files...")
sessions_df.to_csv('data/raw/sessions.csv', index=False)
events_df.to_csv('data/raw/events.csv', index=False)
users_df.to_csv('data/raw/users.csv', index=False)
orders_df.to_csv('data/raw/orders.csv', index=False)

print("Data generation complete!")
print(f"Total sessions: {len(sessions_df)}")
print(f"Total events: {len(events_df)}")
print(f"Total users: {len(users_df)}")
print(f"Total orders: {len(orders_df)}")
print(f"Overall conversion rate: {len(orders_df)/len(sessions_df):.2%}")
