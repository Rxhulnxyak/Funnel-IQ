import plotly.express as px
import pandas as pd
from statsmodels.stats.power import NormalIndPower

print("Generating CRO Recommendations & Priority Matrix...")

issues = [
    {"issue": "Mobile checkout UX redesign", "ease": 3, "revenue_impact": 850000, "sessions": 45000},
    {"issue": "Payment retry nudge", "ease": 8, "revenue_impact": 320000, "sessions": 8000},
    {"issue": "Add UPI shortcut on checkout", "ease": 9, "revenue_impact": 280000, "sessions": 12000},
    {"issue": "Cart abandonment email flow", "ease": 7, "revenue_impact": 540000, "sessions": 28000},
    {"issue": "Show EMI options on product page", "ease": 6, "revenue_impact": 420000, "sessions": 15000},
    {"issue": "COD first for Tier-2 users", "ease": 8, "revenue_impact": 190000, "sessions": 9000},
    {"issue": "Reduce checkout form fields", "ease": 5, "revenue_impact": 680000, "sessions": 35000},
    {"issue": "Landing page load speed (< 2s)", "ease": 4, "revenue_impact": 950000, "sessions": 60000},
    {"issue": "Trust badges on cart page", "ease": 9, "revenue_impact": 210000, "sessions": 22000},
    {"issue": "Push notification timing optimization", "ease": 7, "revenue_impact": 160000, "sessions": 7000},
]

df_issues = pd.DataFrame(issues)

def categorize(row):
    if row['ease'] >= 6 and row['revenue_impact'] >= 400000: return 'Quick Wins'
    if row['ease'] < 6 and row['revenue_impact'] >= 400000: return 'Major Projects'
    if row['ease'] >= 6 and row['revenue_impact'] < 400000: return 'Fill-ins'
    return 'Don\'t Bother'

df_issues['Category'] = df_issues.apply(categorize, axis=1)

color_discrete_map = {
    'Quick Wins': 'green',
    'Major Projects': 'orange',
    'Fill-ins': 'blue',
    'Don\'t Bother': 'grey'
}

fig = px.scatter(
    df_issues, x="ease", y="revenue_impact", size="sessions", color="Category",
    hover_name="issue", size_max=40, text="issue",
    color_discrete_map=color_discrete_map,
    title="CRO Priority Matrix: Ease of Implementation vs Revenue Impact"
)

fig.update_traces(textposition='top center')
fig.add_hline(y=400000, line_width=1, line_dash="dash", line_color="black")
fig.add_vline(x=6, line_width=1, line_dash="dash", line_color="black")
fig.update_layout(xaxis_title="Ease of Implementation (1=Hard, 10=Easy)", yaxis_title="Monthly Revenue Impact (₹)")
fig.write_html('reports/charts/14_priority_matrix.html')

print("A/B Test Sample Size Calculator")
def calculate_sample_size(baseline_rate, minimum_detectable_effect, alpha=0.05, power=0.8):
    effect_size = abs(minimum_detectable_effect) / (baseline_rate * (1 - baseline_rate)) ** 0.5
    analysis = NormalIndPower()
    n = analysis.solve_power(effect_size=effect_size, alpha=alpha, power=power, ratio=1.0, alternative='two-sided')
    return int(n)

# Example: Mobile checkout (from 1.4% to 1.47% -> 5% relative lift -> MDE = 0.0007)
baseline = 0.014
mde = 0.0007
n_size = calculate_sample_size(baseline, mde)
print(f"To detect a 5% relative lift from {baseline:.2%} baseline, you need {n_size} sessions per variant.")
