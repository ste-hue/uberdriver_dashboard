import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Uber Driver Dashboard (2024 & 2025)", layout="wide")

@st.cache_data
def load_local_data():
    """
    Loads local CSVs for trips & payments (no file upload).
    Creates atomic timestamp columns for both.
    """
    # --- Load Trips ---
    trips_df = pd.read_csv("analysis/cleaned_driver_trips_2024_2025.csv")
    trips_df["Local Dropoff Timestamp"] = pd.to_datetime(trips_df["Local Dropoff Timestamp"], errors="coerce")
    trips_df.dropna(subset=["Local Dropoff Timestamp"], inplace=True)

    # Add atomic columns
    trips_df["year"] = trips_df["Local Dropoff Timestamp"].dt.year
    trips_df["month"] = trips_df["Local Dropoff Timestamp"].dt.month
    trips_df["day"] = trips_df["Local Dropoff Timestamp"].dt.day
    trips_df["hour"] = trips_df["Local Dropoff Timestamp"].dt.hour
    trips_df["day_of_week"] = trips_df["Local Dropoff Timestamp"].dt.day_name()

    # --- Load Payments ---
    payments_df = pd.read_csv("analysis/cleaned_driver_payments_2024_2025.csv")
    payments_df["Local Timestamp"] = pd.to_datetime(payments_df["Local Timestamp"], errors="coerce")
    payments_df.dropna(subset=["Local Timestamp"], inplace=True)

    # Add atomic columns
    payments_df["year"] = payments_df["Local Timestamp"].dt.year
    payments_df["month"] = payments_df["Local Timestamp"].dt.month
    payments_df["day"] = payments_df["Local Timestamp"].dt.day
    payments_df["hour"] = payments_df["Local Timestamp"].dt.hour
    payments_df["day_of_week"] = payments_df["Local Timestamp"].dt.day_name()

    return trips_df, payments_df

def main():
    st.title("🚗 Uber Driver Dashboard – Single Page View")
    st.caption("Visualize 2024 & 2025 data in one place—no file uploads, no tabs, just insights.")

    # --- LOAD DATA ---
    with st.spinner("Loading local CSV data..."):
        trips_df, payments_df = load_local_data()

    if trips_df.empty or payments_df.empty:
        st.error("No data found in local CSV files. Please check file paths.")
        st.stop()

    # =============================
    # 1. COMBINED DATE RANGE FILTER
    # =============================
    # We'll unify the date range across trips & payments
    min_date = min(trips_df["Local Dropoff Timestamp"].min(), payments_df["Local Timestamp"].min())
    max_date = max(trips_df["Local Dropoff Timestamp"].max(), payments_df["Local Timestamp"].max())

    st.sidebar.header("Global Date Filter")
    start_date = st.sidebar.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

    # Filter trips
    trips_mask = (
        (trips_df["Local Dropoff Timestamp"] >= pd.to_datetime(start_date)) &
        (trips_df["Local Dropoff Timestamp"] <= pd.to_datetime(end_date))
    )
    filtered_trips = trips_df[trips_mask].copy()

    # Filter payments
    pay_mask = (
        (payments_df["Local Timestamp"] >= pd.to_datetime(start_date)) &
        (payments_df["Local Timestamp"] <= pd.to_datetime(end_date))
    )
    filtered_payments = payments_df[pay_mask].copy()

    # =============================
    # 2. KEY METRICS & OVERVIEW
    # =============================
    st.subheader("Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_trips = len(filtered_trips)
        st.metric("Total Trips", f"{total_trips:,}")
    with col2:
        avg_distance = filtered_trips["Trip Distance (miles)"].mean() if not filtered_trips.empty else 0
        st.metric("Avg Trip Distance (mi)", f"{avg_distance:.2f}")
    with col3:
        total_payments = filtered_payments["Local Amount"].sum() if not filtered_payments.empty else 0
        st.metric("Total Earnings", f"${total_payments:,.2f}")
    with col4:
        # Just an example: average payment amount
        avg_payment = filtered_payments["Local Amount"].mean() if not filtered_payments.empty else 0
        st.metric("Avg Payment", f"${avg_payment:,.2f}")

    # =============================
    # 3. TOP DAYS (TRIPS & PAYMENTS)
    # =============================
    st.subheader("Top Days of the Week")
    colA, colB = st.columns(2)

    with colA:
        st.markdown("**Top Day(s) by Number of Trips**")
        if not filtered_trips.empty:
            # Count how many trips per day_of_week
            day_trip_count = (
                filtered_trips.groupby("day_of_week")["Local Dropoff Timestamp"]
                .count()
                .reset_index()
                .rename(columns={"Local Dropoff Timestamp": "trip_count"})
            )
            day_trip_count.sort_values("trip_count", ascending=False, inplace=True)
            st.dataframe(day_trip_count.head(3))
        else:
            st.info("No trips in selected date range.")

    with colB:
        st.markdown("**Top Day(s) by Earnings**")
        if not filtered_payments.empty:
            day_pay_sums = (
                filtered_payments.groupby("day_of_week")["Local Amount"]
                .sum()
                .reset_index()
                .sort_values(by="Local Amount", ascending=False)
            )
            st.dataframe(day_pay_sums.head(3).style.format({"Local Amount": "${:,.2f}"}))
        else:
            st.info("No payments in selected date range.")

    # =============================
    # 4. DAILY EARNINGS LINE CHART
    # =============================
    st.subheader("Daily Total Earnings")
    if not filtered_payments.empty:
        filtered_payments["date_only"] = filtered_payments["Local Timestamp"].dt.date
        daily_pay = (
            filtered_payments.groupby("date_only")["Local Amount"]
            .sum()
            .reset_index()
        )
        fig_pay = px.line(
            daily_pay,
            x="date_only",
            y="Local Amount",
            title="Daily Earnings Over Time",
            labels={"date_only": "Date", "Local Amount": "USD"},
            markers=True
        )
        fig_pay.update_yaxes(tickprefix="$")
        st.plotly_chart(fig_pay, use_container_width=True)
    else:
        st.info("No payment data for selected range.")

    # =============================
    # 5. AVERAGE TRIP DISTANCE BY DAY_OF_WEEK (BAR)
    # =============================
    st.subheader("Average Trip Distance by Day of Week")
    if not filtered_trips.empty:
        avg_dist_day = (
            filtered_trips.groupby("day_of_week")["Trip Distance (miles)"]
            .mean()
            .reset_index()
        )
        fig_dist = px.bar(
            avg_dist_day,
            x="day_of_week",
            y="Trip Distance (miles)",
            title="Avg Trip Distance by Day of Week",
            labels={"Trip Distance (miles)": "Miles"},
            color="Trip Distance (miles)",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    else:
        st.info("No trip data for selected range.")

    # =============================
    # 6. "TOP 10" TABLES (OPTIONAL)
    # =============================
    st.subheader("Top 10 Highest-Paying Single Trips (If Applicable)")
    if "Local Original Fare" in filtered_trips.columns and not filtered_trips.empty:
        # Sort by fare desc
        top_trips = filtered_trips.sort_values("Local Original Fare", ascending=False).head(10)
        st.dataframe(
            top_trips[["Local Dropoff Timestamp", "Local Original Fare", "Trip Distance (miles)"]]
            .style.format({"Local Original Fare": "${:,.2f}"})
        )
    else:
        st.info("No 'Local Original Fare' column found, or no trip data available.")

    st.subheader("Top 10 Largest Payment Records")
    if not filtered_payments.empty:
        # Sort by 'Local Amount' desc
        top_payments = filtered_payments.sort_values("Local Amount", ascending=False).head(10)
        st.dataframe(
            top_payments[["Local Timestamp", "Local Amount", "Category"]]
            .style.format({"Local Amount": "${:,.2f}"})
        )
    else:
        st.info("No payment data for selected range.")

    st.write("---")
    st.success("All insights in one place! Adjust the date range in the sidebar to see different results.")

if __name__ == "__main__":
    main()