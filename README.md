# Cash Flow Intelligence Platform — Streamlit Dashboard

## Setup (one time only)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get your Google Sheets URLs from Colab
Run the last cell (Step 14) in your Colab notebook.
Copy the two URLs that print out.

### 3. Paste URLs into app.py
Open app.py and replace these two lines near the top:

```python
SCORES_URL  = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/..."
SUMMARY_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/..."
```

Do this ONCE. Never change again unless you create a new sheet.

### 4. Run the dashboard
```bash
streamlit run app.py
```

Browser opens at http://localhost:8501 automatically.

---

## How live updates work

1. Open Colab notebook
2. Change any parameter (noise level, churn threshold, n customers)
3. Re-run cells 3 to 14
4. Click Refresh in the dashboard sidebar
5. Dashboard shows new results instantly

## Dashboard sections

- KPI strip — critical count, revenue at risk, AUC, stable base
- Portfolio heatmap — tier distribution + revenue by tier
- Macro signals — live FRED indicators with progress bars
- Model performance — AUC gauge vs LR baseline
- SHAP importance — top 15 cash flow features
- Customer table — filterable, searchable, downloadable
- Score distribution — histogram + donut chart

## Files

- app.py           — main dashboard (edit SCORES_URL and SUMMARY_URL here)
- requirements.txt — Python dependencies
- README.md        — this file

Built by Sourabh Rodagi
Inspired by Gene Volchek (EWS) directed toward Charlie Wise (TransUnion R&C)
