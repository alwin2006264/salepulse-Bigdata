import io
import random
import hashlib
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(page_title="SalesPulse | Big Data Analytics", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: rgba(90, 100, 150, 0.08); padding: 14px 16px; border-radius: 12px;}
.small-note {color: #6b7280; font-size: 0.9rem;}
</style>
""", unsafe_allow_html=True)

PRODUCTS = [
    ("P001", "Wireless Headphones", "Electronics", 199.99),
    ("P002", "Smart Watch", "Electronics", 249.99),
    ("P003", "Running Shoes", "Sports", 129.99),
    ("P004", "Yoga Mat", "Fitness", 49.99),
    ("P005", "Coffee Maker", "Home", 89.99),
    ("P006", "Laptop Stand", "Office", 59.99),
    ("P007", "Desk Lamp", "Home", 39.99),
    ("P008", "Water Bottle", "Fitness", 24.99),
    ("P009", "Backpack", "Accessories", 79.99),
    ("P010", "Bluetooth Speaker", "Electronics", 149.99),
    ("P011", "Protein Powder", "Fitness", 39.99),
    ("P012", "Desk Organizer", "Office", 29.99),
    ("P013", "Phone Case", "Accessories", 19.99),
    ("P014", "USB-C Cable", "Electronics", 14.99),
    ("P015", "Notebook Set", "Office", 12.99),
]
REGIONS = ["North", "South", "East", "West", "Central"]

@st.cache_data(show_spinner=False)
def make_sample_data(n_rows: int = 100_000) -> pd.DataFrame:
    rng = random.Random(42)
    end = datetime.now().date()
    rows = []
    for i in range(n_rows):
        pid, name, category, base_price = rng.choice(PRODUCTS)
        qty = rng.randint(1, 5)
        dt = end - timedelta(days=rng.randint(0, 364))
        price = base_price
        roll = rng.random()
        if roll < 0.012:
            price = None
        elif roll < 0.020:
            price = -base_price
        if roll >= 0.020 and roll < 0.025:
            dt_value = "not-a-date"
        else:
            dt_value = dt.isoformat()
        rows.append({
            "order_id": f"ORD-{rng.randint(1, max(1000, n_rows // 3)):07d}",
            "product_id": pid,
            "product_name": name,
            "category": category,
            "quantity": qty,
            "unit_price": price,
            "order_date": dt_value,
            "customer_id": f"CUST-{rng.randint(1000, 9999)}",
            "region": rng.choice(REGIONS),
        })
    return pd.DataFrame(rows)

ALIASES = {
    "order_id": ["order_id", "invoice", "invoiceno", "invoice_no", "transaction_id", "orderid"],
    "product_id": ["product_id", "stockcode", "stock_code", "sku", "item_id"],
    "product_name": ["product_name", "description", "product", "item_name", "name"],
    "category": ["category", "product_category", "type"],
    "quantity": ["quantity", "qty", "units", "units_sold"],
    "unit_price": ["unit_price", "unitprice", "price", "price_each", "rate"],
    "order_date": ["order_date", "invoicedate", "invoice_date", "date", "timestamp"],
    "customer_id": ["customer_id", "customerid", "customer", "client_id"],
    "region": ["region", "country", "location", "area"],
}

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in out.columns]
    rename = {}
    for target, choices in ALIASES.items():
        for col in out.columns:
            compact = col.replace("_", "")
            if col in choices or compact in [x.replace("_", "") for x in choices]:
                rename[col] = target
                break
    out = out.rename(columns=rename)
    required = ["order_id", "product_id", "product_name", "quantity", "unit_price", "order_date"]
    missing = [c for c in required if c not in out.columns]
    if missing:
        raise ValueError("Could not identify required columns: " + ", ".join(missing) + ". Expected order/invoice ID, product ID/name, quantity, unit price and order date.")
    if "category" not in out.columns:
        out["category"] = "Uncategorized"
    if "customer_id" not in out.columns:
        out["customer_id"] = "Unknown"
    if "region" not in out.columns:
        out["region"] = "Unknown"
    return out

def analyze_data(raw: pd.DataFrame):
    df = normalize_columns(raw)
    read_count = len(df)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce", utc=True).dt.tz_convert(None)
    missing_rows = int(df[["order_id", "product_id", "quantity", "unit_price", "order_date"]].isna().any(axis=1).sum())
    exact_duplicates = int(df.duplicated().sum())
    negative_prices = int((df["unit_price"] < 0).sum())
    invalid_dates = int(df["order_date"].isna().sum())
    invalid_quantity = int((df["quantity"] <= 0).sum())
    # Remove exact duplicate rows, invalid/missing key fields, non-positive quantity and non-positive prices.
    cleaned = df.drop_duplicates().copy()
    cleaned = cleaned.dropna(subset=["order_id", "product_id", "quantity", "unit_price", "order_date"])
    cleaned = cleaned[(cleaned["quantity"] > 0) & (cleaned["unit_price"] > 0)]
    cleaned["revenue"] = cleaned["quantity"] * cleaned["unit_price"]
    cleaned["month"] = cleaned["order_date"].dt.to_period("M").astype(str)
    cleaned["product_name"] = cleaned["product_name"].fillna("Unknown Product").astype(str)
    cleaned["category"] = cleaned["category"].fillna("Uncategorized").astype(str)
    cleaned["region"] = cleaned["region"].fillna("Unknown").astype(str)
    cleaned["customer_id"] = cleaned["customer_id"].fillna("Unknown").astype(str)
    dropped = read_count - len(cleaned)
    quality = round(100 * len(cleaned) / read_count, 2) if read_count else 0.0
    metrics = {
        "revenue": float(cleaned["revenue"].sum()),
        "orders": int(cleaned["order_id"].nunique()),
        "average_order_value": float(cleaned.groupby("order_id")["revenue"].sum().mean()) if not cleaned.empty else 0.0,
        "products": int(cleaned["product_id"].nunique()),
        "customers": int(cleaned.loc[cleaned["customer_id"] != "Unknown", "customer_id"].nunique()),
        "quality": quality,
        "records_read": read_count,
        "records_cleaned": len(cleaned),
        "records_dropped": dropped,
    }
    monthly = cleaned.groupby("month", as_index=False).agg(revenue=("revenue", "sum"), orders=("order_id", "nunique")).sort_values("month")
    products = cleaned.groupby(["product_id", "product_name", "category"], as_index=False).agg(
        revenue=("revenue", "sum"), units_sold=("quantity", "sum"), avg_price=("unit_price", "mean")
    ).sort_values("revenue", ascending=False).head(10)
    categories = cleaned.groupby("category", as_index=False).agg(revenue=("revenue", "sum"), units_sold=("quantity", "sum")).sort_values("revenue", ascending=False)
    quality_rows = pd.DataFrame([
        {"Check": "Rows with missing/invalid required fields", "Count": missing_rows},
        {"Check": "Exact duplicate rows", "Count": exact_duplicates},
        {"Check": "Negative unit prices", "Count": negative_prices},
        {"Check": "Invalid dates", "Count": invalid_dates},
        {"Check": "Non-positive quantities", "Count": invalid_quantity},
        {"Check": "Rows removed during cleaning", "Count": dropped},
    ])
    return cleaned, metrics, monthly, products, categories, quality_rows

st.title("📊 SalesPulse Analytics")
st.caption("Big Data Sales Intelligence Platform | Data quality, sales trends and product performance")

with st.sidebar:
    st.header("Data source")
    source = st.radio("Choose input", ["Generate sample dataset", "Upload CSV"], index=0)
    if source == "Generate sample dataset":
        n_rows = st.select_slider("Sample records", options=[1000, 5000, 10000, 25000, 50000, 100000], value=100000)
        raw = make_sample_data(n_rows)
        input_signature = ("sample", n_rows, datetime.now().date().isoformat())
        st.success(f"Generated {len(raw):,} sample records")
        st.caption("Sample data is synthetic and for demonstration only.")
    else:
        uploaded = st.file_uploader("Upload a sales CSV", type=["csv"])
        if uploaded is None:
            st.info("Upload a CSV to begin. You can use the sample dataset option to preview the dashboard.")
            st.stop()
        try:
            file_bytes = uploaded.getvalue()
            input_signature = ("upload", uploaded.name, hashlib.sha256(file_bytes).hexdigest())
            raw = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")
            st.stop()
    run_clicked = st.button("Run analysis", type="primary", use_container_width=True)

if ("analysis_cache" not in st.session_state or run_clicked
        or st.session_state.get("input_signature") != input_signature):
    try:
        with st.spinner("Cleaning records and calculating sales analytics..."):
            st.session_state.analysis_cache = analyze_data(raw)
            st.session_state.raw_cache = raw
            st.session_state.input_signature = input_signature
    except Exception as exc:
        st.error(f"Analysis could not be completed: {exc}")
        st.stop()

cleaned, metrics, monthly, products, categories, quality_rows = st.session_state.analysis_cache

st.subheader("Overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total revenue", f"${metrics['revenue']:,.2f}")
c2.metric("Orders", f"{metrics['orders']:,}")
c3.metric("Average order value", f"${metrics['average_order_value']:,.2f}")
c4.metric("Products", f"{metrics['products']:,}")
c5.metric("Data quality", f"{metrics['quality']:.1f}%")

st.caption(f"Records read: {metrics['records_read']:,} · Clean records: {metrics['records_cleaned']:,} · Removed: {metrics['records_dropped']:,}")

left, right = st.columns(2)
with left:
    st.subheader("Monthly revenue trend")
    if not monthly.empty:
        chart = monthly.set_index("month")["revenue"]
        st.line_chart(chart, y_label="Revenue")
    else:
        st.info("No valid dated sales records to chart.")
with right:
    st.subheader("Revenue by category")
    if not categories.empty:
        st.bar_chart(categories.set_index("category")["revenue"], y_label="Revenue")
    else:
        st.info("No valid categories to chart.")

st.subheader("Top 10 products by revenue")
if not products.empty:
    show_products = products.rename(columns={"product_id": "Product ID", "product_name": "Product", "category": "Category", "revenue": "Revenue", "units_sold": "Units sold", "avg_price": "Average unit price"}).copy()
    show_products["Revenue"] = show_products["Revenue"].round(2)
    show_products["Average unit price"] = show_products["Average unit price"].round(2)
    st.dataframe(show_products, use_container_width=True, hide_index=True)
else:
    st.info("No product results available.")

st.subheader("Data quality checks")
st.dataframe(quality_rows, use_container_width=True, hide_index=True)

st.subheader("Business insights")
if len(monthly) >= 2:
    previous = float(monthly.iloc[-2]["revenue"])
    latest = float(monthly.iloc[-1]["revenue"])
    if previous:
        change = (latest - previous) / previous * 100
        direction = "increased" if change >= 0 else "decreased"
        st.write(f"- Revenue {direction} by **{abs(change):.1f}%** between the last two months in the dataset.")
if not products.empty:
    top = products.iloc[0]
    st.write(f"- Highest-revenue product: **{top['product_name']}**, with **${top['revenue']:,.2f}** in revenue.")
if not categories.empty:
    top_cat = categories.iloc[0]
    st.write(f"- Highest-revenue category: **{top_cat['category']}**, with **${top_cat['revenue']:,.2f}** in revenue.")
st.write(f"- Data cleaning retained **{metrics['records_cleaned']:,} of {metrics['records_read']:,} records**. The quality percentage shown is the retained-row percentage after the cleaning rules, not an independent measure of every possible data issue.")

st.subheader("Processing pipeline")
steps = [
    ("1. Data ingestion", f"Loaded {metrics['records_read']:,} records"),
    ("2. Data validation", "Checked required fields, dates, prices and quantities"),
    ("3. Data cleaning", f"Retained {metrics['records_cleaned']:,}; removed {metrics['records_dropped']:,}"),
    ("4. Aggregation", "Calculated revenue, orders, monthly trends and product rankings"),
    ("5. Visualization", "Rendered dashboard charts and tables"),
]
for title, detail in steps:
    st.markdown(f"✅ **{title}** — {detail}")
st.info("Deployment note: this Streamlit edition runs the included analytics with Pandas. It is designed for a simple public demo. If your grading rubric requires distributed Spark execution, deploy/test a Spark-enabled backend separately and clearly label which engine processed the data.")

csv_bytes = cleaned.to_csv(index=False).encode("utf-8")
st.download_button("Download cleaned dataset (CSV)", data=csv_bytes, file_name="cleaned_sales_data.csv", mime="text/csv")
summary = pd.DataFrame([metrics]).to_csv(index=False).encode("utf-8")
st.download_button("Download summary metrics (CSV)", data=summary, file_name="sales_summary.csv", mime="text/csv")

st.divider()
st.caption("SalesPulse Analytics · College Big Data mini-project · Synthetic sample records are clearly identified; upload your own data for actual analysis.")
