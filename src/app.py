import streamlit as st

#Set page configuration
st.set_page_config(page_title="Backtester", layout="wide")

#Title and description
st.title("Trading Backtester")


# ---- Interactive widgets ----
# Text input returns a Python string. #Value is the default value will be changed.
ticker = st.text_input("Ticker", value="AAPL")


# Slider returns a Python int in number of years.
years = st.slider("Number of years to analyze", min_value=1, max_value=20, value=5)


# ---- Display current selections ----
# st.write prints objects in the app.
st.write("Selected settings:")
st.write("Ticker:", ticker)
st.write("Years:", years)


# ---- Action button ----
# Buttons are typically used to trigger an explicit action.
# Note: Streamlit re-runs this script top to bottom on every interaction.
if st.button("Confirm"):
    # Show a success message when the user confirms.
    st.success(f"Ready to backtest {ticker} over {years} years")