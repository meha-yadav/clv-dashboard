# CLV & Churn Dashboard

I built this as part of a customer analytics project using a real UK online retail dataset. The idea was simple — instead of just doing basic RFM analysis, I wanted to actually predict which customers are about to churn and how much revenue they're likely to bring in over the next 6 months.

---

## What it does

You upload your data and the dashboard gives you two things:

**Overview tab** — a bird's eye view of your entire customer base. Charts showing how churn risk is distributed, which customers are critical vs loyal, CLV spread across segments, and a full filterable table you can download.

**Drill down tab** — type in any customer ID and instantly see their churn risk gauge, predicted CLV, where they rank compared to every other customer, and what action to take with them.

---

## How I built it

The modelling happens in a Kaggle notebook (not included here — just the dashboard). The steps were:

1. Clean the transaction data — remove cancellations, nulls, negative quantities
2. Build an RFM summary table (one row per customer)
3. Fit a **BG/NBD model** to figure out which customers are still active vs silently churned
4. Fit a **Gamma-Gamma model** to estimate how much each customer spends per order
5. Combine both to get a **6-month CLV prediction** per customer
6. Export results to Excel, load into this dashboard

The models come from the `lifetimes` Python library. The dashboard is built with Streamlit and Plotly.

---

## Running it yourself

You'll need Python installed. Then:

```bash
pip install -r requirements.txt
streamlit run app.py
```

When it opens in your browser, just upload the Excel output from the Kaggle notebook and everything loads automatically.

---

## Stack

- Python, Pandas
- lifetimes (BG/NBD + Gamma-Gamma)
- Streamlit
- Plotly

---

## Dataset

[Online Retail Dataset](https://www.kaggle.com/datasets/lakshmi25npathi/online-retail-dataset) from Kaggle — ~500k transactions from a UK-based retailer between 2010 and 2011.

---

## What I'd add next

- Cohort analysis by signup month
- Country-level segmentation
- Email trigger integration for the "At Risk" segment
- Automated retraining when new data is uploaded
