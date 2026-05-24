# FunnelIQ — E-Commerce Conversion Analytics Platform

An enterprise-grade, end-to-end data analytics portfolio project simulating a real-world conversion rate optimization (CRO) ecosystem for a D2C e-commerce brand ("CartX").

## Project Overview
FunnelIQ goes beyond basic charts. It demonstrates the ability to handle raw event streams, process them into analytical datasets, run deep segmentations, write production-level SQL, and build interactive dashboards to communicate findings to stakeholders.

## Architecture & Workflow

1. **Synthetic Data Generation:** 
   - `generate_data.py` simulates 150k+ user sessions, mimicking real-world e-commerce behavior with deliberate bottlenecks built-in.
   - Outputs: `sessions.csv`, `events.csv`, `users.csv`, `orders.csv`.

2. **Exploratory Data Analysis (Jupyter Notebooks):**
   - `01_data_generation.ipynb`
   - `02_overall_funnel_analysis.ipynb`
   - `03_segmented_funnel_analysis.ipynb`
   - `04_time_based_analysis.ipynb`
   - `05_dropoff_root_cause.ipynb`
   - `06_cro_recommendations.ipynb`

3. **Data Warehousing (SQL):**
   - `sql/funnel_queries.sql` contains complex, CTE-based ANSI SQL queries for computing funnel metrics, abandonment rates, and ROI.

4. **Interactive Dashboarding (Streamlit):**
   - `app/funneliq_app.py` is a multipage Streamlit application acting as the executive dashboard.

5. **Reporting:**
   - `reports/cro_audit_report.md` summarizes actionable business insights.

## How to Run

1. **Setup Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Generate Data:**
   ```bash
   python generate_data.py
   ```

3. **Run Streamlit Dashboard:**
   ```bash
   streamlit run app/funneliq_app.py
   ```

## Key Business Insights Discovered
* **Mobile Friction:** Identified a severe drop-off (65%) at checkout for mobile users, indicating poor responsive UX.
* **Traffic Quality:** Paid Social drives high traffic and cart additions but suffers from the highest abandonment rate, suggesting a mismatch between ad messaging and final pricing.

## Tech Stack
* **Python:** Pandas, NumPy, SciPy (Statistical Testing)
* **Visualization:** Plotly, Seaborn
* **Dashboard:** Streamlit
* **Database Language:** SQL (Standard ANSI)
