<div align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/2633/2633320.png" alt="FunnelIQ Logo" width="100"/>
  <h1>FunnelIQ: E-Commerce Conversion Intelligence Platform</h1>
  <p><strong>Enterprise-grade User Journey & Drop-off Analytics System</strong></p>

  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
  ![PostgreSQL](https://img.shields.io/badge/SQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
  ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
  ![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
</div>

---

## 📖 Overview

**FunnelIQ** is an end-to-end data analytics portfolio project designed to simulate a real-world Conversion Rate Optimization (CRO) ecosystem for a D2C e-commerce brand ("CartX"). 

Moving beyond basic charting, this project demonstrates full-stack analytical capabilities—from raw event stream generation and exploratory data analysis (EDA) to complex SQL data warehousing and interactive executive dashboarding. 

## 🎯 The Business Problem
E-commerce platforms often experience high traffic but suffer from silent revenue leaks. Identifying exactly *where* and *why* users drop off—whether due to poor mobile UX, inefficient ad targeting, or friction in the checkout process—is critical for growth. FunnelIQ provides the intelligence needed to plug these leaks.

## 🏗️ Architecture & Workflow

The project is structured into 4 distinct phases:

### 1. Synthetic Data Engineering (`generate_data.py`)
- Engineered a robust data simulator using `Faker` and `pandas`.
- Generates **150,000+ realistic user sessions**, resulting in over 400,000 events, mimicking real-world behaviors, device disparities, and seasonal trends.

### 2. Exploratory Data Analysis (Jupyter Notebooks)
Deep-dive statistical analysis and segmentation to uncover hidden patterns:
- `02_overall_funnel_analysis.ipynb`: High-level conversion tracking.
- `03_segmented_funnel_analysis.ipynb`: Device and traffic source cohorts.
- `04_time_based_analysis.ipynb`: Time-to-purchase and temporal trends.
- `05_dropoff_root_cause.ipynb`: Hypothesis testing for abandonment.
- `06_cro_recommendations.ipynb`: Data-driven prioritization matrix.

### 3. Data Warehousing & SQL (`sql/funnel_queries.sql`)
- Production-ready, complex ANSI SQL queries utilizing **CTEs (Common Table Expressions)** and window functions.
- Calculates multi-step funnel conversion rates, time-to-purchase, and traffic source ROI.

### 4. Interactive Executive Dashboard (`app/funneliq_app.py`)
- A multi-page **Streamlit** application serving as a live executive dashboard.
- Features dynamic Plotly funnel charts, KPI metric cards, and segment drop-off tools for stakeholder presentations.

---

## 💡 Key Business Insights Discovered

Through rigorous data analysis, FunnelIQ identified two critical revenue leaks:

1. 📱 **The Mobile Friction Point:** 
   - **Data:** Mobile traffic accounts for ~60% of sessions but only ~40% of revenue. 
   - **Insight:** The drop-off rate from `begin_checkout` to `purchase` is **65% on Mobile** vs. 35% on Desktop.
   - **Action:** Implement 1-click checkout (Apple Pay/GPay) to recover an estimated **₹1.2M/month**.

2. 🛒 **Social Traffic Abandonment:** 
   - **Data:** Paid Social drives 30% of cart additions but only 15% of purchases.
   - **Insight:** High impulse click-through rates are met with unexpected shipping costs or long forms.
   - **Action:** Deploy aggressive cart-abandonment retargeting for social traffic cohorts.

*(Read the full strategic breakdown in the [CRO Audit Report](reports/cro_audit_report.md))*

---

## 📂 Repository Structure

```text
📦 Funnel-IQ
 ┣ 📂 app                   # Streamlit Dashboard application
 ┃ ┗ 📜 funneliq_app.py
 ┣ 📂 data                  
 ┃ ┗ 📂 raw                 # Generated datasets (sessions, events, users, orders)
 ┣ 📂 notebooks             # EDA and Statistical Analysis
 ┃ ┣ 📜 01_data_generation.ipynb
 ┃ ┣ 📜 02_overall_funnel_analysis.ipynb
 ┃ ┗ 📜 ...
 ┣ 📂 reports               # Business facing documentation
 ┃ ┗ 📜 cro_audit_report.md
 ┣ 📂 sql                   # Analytical queries
 ┃ ┗ 📜 funnel_queries.sql
 ┣ 📜 generate_data.py      # Core simulation engine
 ┣ 📜 requirements.txt      # Python dependencies
 ┗ 📜 README.md
```

---

## 🚀 Quick Start (Local Setup)

Want to run the analysis and dashboard locally? Follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Rxhulnxyak/Funnel-IQ.git
   cd Funnel-IQ
   ```

2. **Create a virtual environment & install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Generate the synthetic dataset:**
   *(Note: This generates ~100MB of data. Wait for it to complete.)*
   ```bash
   python generate_data.py
   ```

4. **Launch the Streamlit Dashboard:**
   ```bash
   streamlit run app/funneliq_app.py
   ```

---

## 🌐 Live Deployment
This dashboard is configured for seamless deployment on **Streamlit Community Cloud**. Simply connect this repository to Streamlit Cloud, point it to `app/funneliq_app.py`, and it will automatically build and host the live analytics platform.

---
<div align="center">
  <i>Designed and developed by <b>Rahul</b>.</i><br>
  <i>Showcasing Data Engineering, Product Analytics, and Business Intelligence.</i>
</div>
