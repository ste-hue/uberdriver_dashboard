import streamlit as st
import pandas as pd
import plotly.express as px

# Minimal page config
st.set_page_config(page_title="Uber Driver Dashboard (2024 & 2025)", layout="wide")

@st.cache_data
def load_trips_data():
    """Loads cleaned trips for 2024 & 2025."""
    df = pd.read_csv("analysis/cleaned_driver_trips_2024_2025.csv")
    df["Local Dropoff Timestamp"] = pd.to_datetime(df["Local Dropoff Timestamp"], errors="coerce")
    return df

@st.cache_data
def load_payments_data():
    """Loads cleaned payments for 2024 & 2025."""
    df = pd.read_csv("analysis/cleaned_driver_payments_2024_2025.csv")
    df["Local Timestamp"] = pd.to_datetime(df["Local Timestamp"], errors="coerce")
    return df

def main():
    st.title("🚗 Uber Dashboard – Years 2024 & 2025 Only")
    st.caption("All days are pre-selected. Remove any you don’t want. Simple & direct.")

    # ---- LOAD DATA ----
    with st.spinner("Loading data..."):
        trips_df = load_trips_data()
        payments_df = load_payments_data()

    # =============================
    # SIDEBAR FILTERS
    # =============================
    st.sidebar.header("Filter Options")

    # 1) Date Range Filters
    # --- Trips
    trips_min_date = trips_df["Local Dropoff Timestamp"].min()
    trips_max_date = trips_df["Local Dropoff Timestamp"].max()

    start_date_trips = st.sidebar.date_input(
        "Trips Start Date",
        value=trips_min_date,
        min_value=trips_min_date,
        max_value=trips_max_date
    )
    end_date_trips = st.sidebar.date_input(
        "Trips End Date",
        value=trips_max_date,
        min_value=trips_min_date,
        max_value=trips_max_date
    )

    # --- Payments
    pay_min_date = payments_df["Local Timestamp"].min()
    pay_max_date = payments_df["Local Timestamp"].max()

    start_date_pay = st.sidebar.date_input(
        "Payments Start Date",
        value=pay_min_date,
        min_value=pay_min_date,
        max_value=pay_max_date
    )
    end_date_pay = st.sidebar.date_input(
        "Payments End Date",
        value=pay_max_date,
        min_value=pay_min_date,
        max_value=pay_max_date
    )

    # 2) Day-of-Week Filter (Unified for Both)
    all_trip_days = trips_df["day_of_week"].dropna().unique()
    all_pay_days = payments_df["day_of_week"].dropna().unique()

    # Union of all possible days from trips & payments
    all_days = sorted(set(all_trip_days) | set(all_pay_days))

    # By default, select all
    selected_days = st.sidebar.multiselect("Days of Week (Trips & Payments)", all_days, default=all_days)

    # =============================
    # APPLY FILTERS
    # =============================
    # Trips Filter
    trips_mask = (
        (trips_df["Local Dropoff Timestamp"] >= pd.to_datetime(start_date_trips)) &
        (trips_df["Local Dropoff Timestamp"] <= pd.to_datetime(end_date_trips)) &
        (trips_df["day_of_week"].isin(selected_days))
    )
    filtered_trips = trips_df[trips_mask].copy()

    # Payments Filter
    pay_mask = (
        (payments_df["Local Timestamp"] >= pd.to_datetime(start_date_pay)) &
        (payments_df["Local Timestamp"] <= pd.to_datetime(end_date_pay)) &
        (payments_df["day_of_week"].isin(selected_days))
    )
    filtered_payments = payments_df[pay_mask].copy()

    # =============================
    # TABS
    # =============================
    tab1, tab2 = st.tabs(["📊 Trips", "💰 Payments"])

    # === TAB 1: TRIPS ===
    with tab1:
        st.subheader("Filtered Trips")
        st.write(f"**{len(filtered_trips)}** total trips in selection.")
        st.dataframe(filtered_trips.head(10))

        # Quick metric: Average Trip Distance
        if not filtered_trips.empty:
            avg_dist = filtered_trips["Trip Distance (miles)"].mean()
            st.metric("Average Trip Distance (mi)", f"{avg_dist:.2f}")

            # Daily average distance chart
            filtered_trips["date_only"] = filtered_trips["Local Dropoff Timestamp"].dt.date
            daily_trips = filtered_trips.groupby("date_only")["Trip Distance (miles)"].mean().reset_index()

            if not daily_trips.empty:
                fig_trips = px.line(
                    daily_trips,
                    x="date_only",
                    y="Trip Distance (miles)",
                    title="Average Daily Trip Distance",
                    labels={"date_only": "Date", "Trip Distance (miles)": "Miles"},
                    markers=True
                )
                st.plotly_chart(fig_trips, use_container_width=True)

    # === TAB 2: PAYMENTS ===
    with tab2:
        st.subheader("Filtered Payments")
        st.write(f"**{len(filtered_payments)}** payment records in selection.")
        st.dataframe(filtered_payments.head(10))

        if not filtered_payments.empty:
            # Key metric: total earnings
            total_earnings = filtered_payments["Local Amount"].sum()
            st.metric("Total Earnings (Filtered)", f"${total_earnings:,.2f}")

            # Daily payment timeline
            filtered_payments["date_only"] = filtered_payments["Local Timestamp"].dt.date
            daily_payments = filtered_payments.groupby("date_only")["Local Amount"].sum().reset_index()
            if not daily_payments.empty:
                fig_pay = px.line(
                    daily_payments,
                    x="date_only",
                    y="Local Amount",
                    title="Daily Total Payment",
                    labels={"date_only": "Date", "Local Amount": "USD"},
                    markers=True
                )
                st.plotly_chart(fig_pay, use_container_width=True)

            # Optional: Payment Category breakdown
            if "Category" in filtered_payments.columns:
                cat_sums = (
                    filtered_payments.groupby("Category")["Local Amount"]
                    .sum()
                    .reset_index()
                    .sort_values(by="Local Amount", ascending=False)
                )
                if not cat_sums.empty:
                    fig_cat = px.bar(
                        cat_sums,
                        x="Category",
                        y="Local Amount",
                        color="Local Amount",
                        color_continuous_scale="Blues",
                        title="Payments by Category"
                    )
                    st.plotly_chart(fig_cat, use_container_width=True)

    st.write("---")
    st.success("Done! Toggle 'Days of Week' or Date ranges in the sidebar to refine your view.")

if __name__ == "__main__":
    main()