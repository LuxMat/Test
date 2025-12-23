from pathlib import Path  # Path utilities that work well on Windows, Mac, Linux
import pandas as pd       # Data handling
import streamlit as st    # UI framework
import plotly.graph_objects as go  # Interactive plotting
from plotly.subplots import make_subplots  # Two stacked charts sharing the same x-axis


# ---- Page setup ----
st.set_page_config(page_title="Trading Backtester", layout="wide")
st.title("Trading Backtester")


# ---- Data source ----
# We build a path relative to this file so the project becomes portable.
# src/app.py -> repo_root is one folder up from src
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "data" / "omxs_new.csv"

# Let the user override the path if needed.
# This is useful while you experiment with different datasets.
csv_path_str = st.sidebar.text_input("CSV path", value=str(DEFAULT_CSV))
csv_path = Path(csv_path_str)

st.sidebar.header("Time resolution")
# Resampling rules in pandas:
# D = daily, H = hourly, 15T = 15 minutes, 5T = 5 minutes
resolution = st.sidebar.selectbox("Resample to", ["D", "H", "15T", "5T"], index=0)


# ---- Load data ----
# We cache the loaded dataframe so the app feels fast when you change UI controls.
@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    # Try comma first. If the file is semicolon separated, pandas may read it as a single column.
    df_try = pd.read_csv(path)

    # If we got only 1 column, it often means the separator is actually ';'
    if df_try.shape[1] == 1:
        df_try = pd.read_csv(path, sep=";")

    return df_try


if not csv_path.exists():
    st.error(f"File not found: {csv_path}")
    st.stop()

df = load_csv(str(csv_path))


# ---- Normalize columns ----
# We need:
# 1) a time column (datetime)
# 2) a price column (numeric)
#
# Because CSV formats vary, we do a best-effort guess:
# - take the first column as time
# - choose a common price column name if it exists, otherwise take the first numeric column
df_columns = list(df.columns)

# Guess time column: first column
time_col = df_columns[0]

# Parse time column to datetime (errors='coerce' turns bad rows into NaT)
df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

# Drop rows where time parsing failed
df = df.dropna(subset=[time_col]).sort_values(time_col)

# Guess price column
common_price_names = ["Close", "close", "PRICE", "Price", "price", "Last", "last"]
price_col = None
for name in common_price_names:
    if name in df.columns:
        price_col = name
        break

# If no common name matched, pick the first numeric column (excluding the time column)
if price_col is None:
    numeric_cols = [c for c in df.columns if c != time_col and pd.api.types.is_numeric_dtype(df[c])]
    if not numeric_cols:
        # If numeric detection failed due to commas or spaces, try coercing all non-time columns
        for c in df.columns:
            if c == time_col:
                continue
            df[c] = pd.to_numeric(df[c], errors="coerce")
        numeric_cols = [c for c in df.columns if c != time_col and pd.api.types.is_numeric_dtype(df[c])]

    if not numeric_cols:
        st.error("Could not find a numeric price column. Check your CSV columns.")
        st.write("Columns:", df.columns.tolist())
        st.stop()

    price_col = numeric_cols[0]

# Make sure price is numeric
df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
df = df.dropna(subset=[price_col])

st.sidebar.caption(f"Detected time column: {time_col}")
st.sidebar.caption(f"Detected price column: {price_col}")


# ---- Resample to the selected time resolution ----
# We set the datetime column as the index so resample works.
df_resampled = (
    df.set_index(time_col)[price_col]
    .resample(resolution)
    .last()   # Use the last price in each bucket
    .dropna()
    .reset_index()
)

# Rename columns to a clean internal format
df_resampled = df_resampled.rename(columns={time_col: "time", price_col: "price"})


# ---- Plot: two stacked panels ----
# Row 1: price bar chart
# Row 2: indicator panel (empty placeholder for now)
fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,             # One time axis for both charts
    vertical_spacing=0.08,
    row_heights=[0.7, 0.3],        # Top chart larger than indicator chart
)

# Price bars
fig.add_trace(
    go.Bar(
        x=df_resampled["time"],
        y=df_resampled["price"],
        name="Price",
    ),
    row=1, col=1
)

# Indicator placeholder: we plot a zero line so the panel exists and is easy to extend later
fig.add_trace(
    go.Scatter(
        x=df_resampled["time"],
        y=[0] * len(df_resampled),
        mode="lines",
        name="Indicator placeholder",
    ),
    row=2, col=1
)

# Layout polish
# Layout polish
fig.update_layout(
    height=700,
    margin=dict(l=20, r=20, t=40, b=20),
)

# Add TradingView-like time navigation:
# 1) range slider at the bottom
# 2) quick range buttons (1M, 6M, 1Y, etc.)
fig.update_xaxes(
    rangeslider=dict(visible=True),
    rangeselector=dict(
        buttons=list([
            dict(count=1, label="1M", step="month", stepmode="backward"),
            dict(count=6, label="6M", step="month", stepmode="backward"),
            dict(count=1, label="1Y", step="year", stepmode="backward"),
            dict(count=5, label="5Y", step="year", stepmode="backward"),
            dict(step="all", label="All"),
        ])
    ),
    row=2, col=1  # Put the slider/buttons on the bottom axis (shared x-axis)
)

st.plotly_chart(fig, use_container_width=True)

# Quick debug view
with st.expander("Show resampled data preview"):
    st.dataframe(df_resampled.head(20))
