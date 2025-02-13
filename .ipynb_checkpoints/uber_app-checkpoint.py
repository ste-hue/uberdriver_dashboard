import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def load_trips_data():
    """
    Reads the driver trip data from CSV, converts timestamps to datetime,
    and adds a 'day_of_week' column for grouping.
    """
    df_trips = pd.read_csv("Driver/driver_lifetime_trips-0.csv")
    df_trips["Local Dropoff Timestamp"] = pd.to_datetime(
        df_trips["Local Dropoff Timestamp"],
        errors='coerce'
    )
    df_trips["day_of_week"] = df_trips["Local Dropoff Timestamp"].dt.day_name()
    return df_trips

def load_payments_data():
    """
    Reads the driver payments data from CSV, converts timestamps
    to datetime, and returns the resulting DataFrame.
    """
    df_pay = pd.read_csv("Driver/driver_payments-0.csv")
    df_pay["Local Timestamp"] = pd.to_datetime(
        df_pay["Local Timestamp"],
        errors='coerce'
    )
    return df_pay

def main():
    """Main function to run the Streamlit dashboard."""
    st.title("Uber Driver Data Dashboard")
    
    # 1. Load data
    trips_df = load_trips_data()
    payments_df = load_payments_data()

    # 2. Display DataFrame previews
    st.subheader("Driver Trips (first 5 rows)")
    st.write(trips_df.head())

    st.subheader("Driver Payments (first 5 rows)")
    st.write(payments_df.head())

    # 3. Display a simple summary of Trip Distance
    st.subheader("Trip Distance Summary")
    st.write(trips_df["Trip Distance (miles)"].describe())

    # 4. Group by 'day_of_week' and calculate mean trip distance
    avg_dist_by_day = trips_df.groupby("day_of_week")["Trip Distance (miles)"].mean()
    st.subheader("Average Trip Distance by Day of Week")
    st.write(avg_dist_by_day)

    # 5. Create and display a bar chart of average distances
    fig, ax = plt.subplots()
    avg_dist_by_day.plot(kind="bar", ax=ax, color="skyblue")
    ax.set_ylabel("Miles")
    ax.set_title("Mean Trip Distance per Day of Week")
    st.pyplot(fig)

    # Additional ideas:
    # - Summaries by 'hour_of_day'
    # - Payment analyses, such as total earnings by day

if __name__ == "__main__":
    main()