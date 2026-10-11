# SalesPulse Analytics — Streamlit deployment

A Streamlit version of the SalesPulse sales analytics dashboard. It supports a generated sample dataset and uploaded CSV files, data cleaning, KPI calculations, monthly trends, product/category analytics, data-quality checks, and CSV downloads.

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy a public live link with Streamlit Community Cloud

1. Create or sign in to GitHub.
2. Create a new repository, for example `salespulse-streamlit`.
3. Upload `app.py`, `requirements.txt`, and `README.md` to the repository root.
4. Visit https://share.streamlit.io/ and connect GitHub if prompted.
5. Choose **Create app**, select the repository and branch, set the main file path to `app.py`, and deploy.
6. Wait for the build to finish. Streamlit Community Cloud will provide a public URL you can share with your teacher.

## Dataset schema

The CSV should contain equivalents of these columns: order/invoice ID, product ID, product name/description, quantity, unit price, and order date. Optional columns include category, customer ID, and region/country. Common retail column names such as `InvoiceNo`, `StockCode`, `Description`, `Quantity`, `UnitPrice`, `InvoiceDate`, `CustomerID`, and `Country` are supported.

## Important project note

This deployable Streamlit edition uses Pandas for straightforward cloud deployment. The original ZIP includes PySpark-related scripts, but they are not automatically executed by this Streamlit app. If your course requires actual distributed processing, include a Spark-backed run and verify it separately; do not claim that the Streamlit demo executed Spark unless it did.
