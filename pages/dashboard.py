import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date # Import date
import os
from dotenv import load_dotenv
import json
import logging # Use logging module

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

# --- Configuration ---
DEFAULT_DAYS_RANGE = 90 # Default to 90 days back

# --- Helper Functions ---
def safe_get(data, key, default=0):
    """Safely get numeric data, handling potential errors or None."""
    val = data.get(key, default)
    if val == "Error" or val is None:
        return default
    try:
        return int(val) # Or float if necessary
    except (ValueError, TypeError):
        return default

def format_date_for_display(dt):
    """Format datetime object for display."""
    if isinstance(dt, datetime):
        return dt.strftime("%d %b %Y")
    if isinstance(dt, date):
        return dt.strftime("%d %b %Y")
    return str(dt)

# --- Main App ---
st.set_page_config(page_title="Melanoma Analytics", layout="wide")

# Check authentication
if "access_token" not in st.session_state or not st.session_state["access_token"]:
    st.warning("Please login first.")
    st.stop()

st.title("📊 Melanoma Detection Analytics")

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# Use a wider default range, or consider fetching min/max dates if feasible
default_start_date = date.today() - timedelta(days=DEFAULT_DAYS_RANGE)
default_end_date = date.today()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(default_start_date, default_end_date),
    min_value=date(2020, 1, 1), # Set a reasonable min date
    max_value=date.today() + timedelta(days=365*5), # Allow future dates if needed
    help=f"Select the start and end dates for the analysis. Default is last {DEFAULT_DAYS_RANGE} days."
)

if len(date_range) == 2:
    start_date, end_date = date_range
    # Ensure start_date is not after end_date
    if start_date > end_date:
        st.sidebar.error("Start date cannot be after end date.")
        st.stop()
    st.sidebar.info(f"Analyzing data from {format_date_for_display(start_date)} to {format_date_for_display(end_date)}")
else:
    st.error("Please select both start and end dates in the sidebar.")
    st.stop()


# --- Fetch Data ---
stats = None
activity_data = None
error_message = None

try:
    headers = {
        "Authorization": f"Bearer {st.session_state['access_token']}",
        "Content-Type": "application/json"
    }
    # Convert date objects to ISO strings for the API call
    params_stats = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
    params_activity = {
        "days": (end_date - start_date).days + 1 # Include end day
    }

    # Fetch stats data
    logging.info(f"Fetching stats from {BASE_URL}/dashboard/stats with params: {params_stats}")
    response_stats = requests.get(
        f"{BASE_URL}/dashboard/stats",
        headers=headers,
        params=params_stats,
        timeout=30 # Add timeout
    )
    logging.info(f"Stats Response Status: {response_stats.status_code}")

    # Fetch activity data
    logging.info(f"Fetching activity from {BASE_URL}/dashboard/user_activity with params: {params_activity}")
    response_activity = requests.get(
        f"{BASE_URL}/dashboard/user_activity",
        headers=headers,
        params=params_activity,
        timeout=30 # Add timeout
    )
    logging.info(f"Activity Response Status: {response_activity.status_code}")

    # Process Stats Response
    if response_stats.status_code == 200:
        try:
            stats = response_stats.json()
            logging.info(f"Parsed stats data: {stats}")
        except json.JSONDecodeError as e:
            error_message = f"Failed to parse statistics JSON response: {e}\nRaw response: {response_stats.text}"
            logging.error(error_message)
    else:
        error_message = f"Error fetching statistics: {response_stats.status_code} - {response_stats.text}"
        logging.error(error_message)

    # Process Activity Response
    if response_activity.status_code == 200:
        try:
            activity_data = response_activity.json()
            logging.info(f"Parsed activity data: {activity_data}")
        except json.JSONDecodeError as e:
            # Append to existing error message if any
            activity_error = f"Failed to parse activity JSON response: {e}\nRaw response: {response_activity.text}"
            error_message = f"{error_message}\n{activity_error}" if error_message else activity_error
            logging.error(activity_error)
    else:
        # Append to existing error message if any
        activity_error = f"Error fetching activity data: {response_activity.status_code} - {response_activity.text}"
        error_message = f"{error_message}\n{activity_error}" if error_message else activity_error
        logging.error(activity_error)


except requests.Timeout:
    error_message = f"Error: Request timed out connecting to the server at {BASE_URL}."
    logging.error(error_message)
except requests.RequestException as e:
    error_message = f"Error connecting to server: {e}. Please check if the server is running at {BASE_URL}."
    logging.error(error_message)


# --- Display Data ---
tab1, tab2, tab3 = st.tabs(["📅 Overview", "📈 User Activity", "🔬 Risk Analysis"])

# Display errors prominently if any occurred
if error_message:
    st.error(f"Failed to load dashboard data:\n{error_message}")
    # Optionally stop execution if data is crucial
    # st.stop()

with tab1:
    st.header("Overview")
    if stats:
        # Display raw data for debugging under an expander
        with st.expander("Show Raw Server Response (Stats)"):
            st.json(stats)

        # Display KPIs
        col1, col2, col3, col4 = st.columns(4)
        total_users = safe_get(stats, "total_users", "N/A")
        total_images = safe_get(stats, "total_images", 0)
        total_analyses = safe_get(stats, "total_analyses", 0)

        with col1:
            # Label is already correct
            st.metric("Total Users (System)", total_users)
        with col2:
            # Update label
            st.metric("Total Images (System, Period)", total_images)
        with col3:
            # Update label
            st.metric("Total Analyses (System, Period)", total_analyses)
        with col4:
            analysis_rate = (total_analyses / total_images * 100) if total_images > 0 else 0
            # Update label
            st.metric("Analysis Rate (System, Period)", f"{analysis_rate:.1f}%")


        # Charts
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.subheader("Analyses by Body Part")
            body_part_distribution = stats.get("body_part_distribution", [])
            if body_part_distribution and total_analyses > 0:
                try:
                    # Replace None _id with 'Not Specified'
                    for item in body_part_distribution:
                        if item["_id"] is None: item["_id"] = "Not Specified"
                    body_part_df = pd.DataFrame(body_part_distribution)
                    fig = px.pie(body_part_df, values="count", names="_id",
                               title=f"Distribution for {total_analyses} Analyses", hole=0.3)
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not display body part chart: {e}")
            elif total_analyses > 0:
                 st.info("Body part data not available for the analyses in this period.")
            else:
                st.info(f"No analyses found between {format_date_for_display(start_date)} and {format_date_for_display(end_date)}.")

        with col_chart2:
            st.subheader("Analyses by Risk Level")
            risk_distribution = stats.get("risk_distribution", [])
            if risk_distribution and total_analyses > 0:
                try:
                     # Replace None _id with 'Unknown'
                    for item in risk_distribution:
                        if item["_id"] is None: item["_id"] = "Unknown"
                    risk_df = pd.DataFrame(risk_distribution)
                    # Define colors for risk levels
                    color_map = {'benign': 'green', 'malignant': 'red', 'other': 'orange', 'unknown': 'grey', 'no se puede clasificar': 'purple', 'Unknown': 'grey'}
                    fig = px.bar(risk_df, x="_id", y="count",
                               title=f"Distribution for {total_analyses} Analyses",
                               labels={"_id": "Risk Classification", "count": "Number of Analyses"},
                               color="_id", # Color bars by classification
                               color_discrete_map=color_map)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not display risk chart: {e}")
            elif total_analyses > 0:
                 st.info("Risk classification data not available for the analyses in this period.")
            else:
                st.info(f"No analyses found between {format_date_for_display(start_date)} and {format_date_for_display(end_date)}.")
    elif not error_message:
        st.info("Waiting for statistics data...")
    # If there was an error, the message is displayed above the tabs


with tab2:
    st.header("User Activity")
    if activity_data:
         # Display raw data for debugging under an expander
        with st.expander("Show Raw Server Response (Activity)"):
            st.json(activity_data)

        daily_uploads = activity_data.get("daily_uploads", [])
        daily_analyses = activity_data.get("daily_analyses", [])

        # Convert to dataframes and handle potential missing keys/dates
        try:
            uploads_df = pd.DataFrame(daily_uploads) if daily_uploads else pd.DataFrame(columns=['_id', 'uploads'])
            analyses_df = pd.DataFrame(daily_analyses) if daily_analyses else pd.DataFrame(columns=['_id', 'analyses'])

            # Ensure date column is datetime
            if not uploads_df.empty: uploads_df['_id'] = pd.to_datetime(uploads_df['_id'])
            if not analyses_df.empty: analyses_df['_id'] = pd.to_datetime(analyses_df['_id'])

            # Merge dataframes on date for combined chart
            if not uploads_df.empty and not analyses_df.empty:
                 activity_df = pd.merge(uploads_df, analyses_df, on='_id', how='outer').fillna(0).sort_values('_id')
            elif not uploads_df.empty:
                 activity_df = uploads_df.rename(columns={'_id': 'date', 'uploads': 'Uploads'}).sort_values('date')
                 activity_df['Analyses'] = 0
            elif not analyses_df.empty:
                 activity_df = analyses_df.rename(columns={'_id': 'date', 'analyses': 'Analyses'}).sort_values('date')
                 activity_df['Uploads'] = 0
            else:
                 activity_df = pd.DataFrame(columns=['date', 'Uploads', 'Analyses'])


            if not activity_df.empty:
                fig = go.Figure()
                if 'Uploads' in activity_df.columns:
                     fig.add_trace(go.Scatter(
                        x=activity_df["date"],
                        y=activity_df["Uploads"],
                        name="Image Uploads",
                        mode="lines+markers"
                    ))
                if 'Analyses' in activity_df.columns:
                    fig.add_trace(go.Scatter(
                        x=activity_df["date"],
                        y=activity_df["Analyses"],
                        name="Analyses Performed",
                        mode="lines+markers"
                    ))
                fig.update_layout(
                    title=f"Daily Activity ({format_date_for_display(start_date)} - {format_date_for_display(end_date)})",
                    xaxis_title="Date",
                    yaxis_title="Count",
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No user activity data found between {format_date_for_display(start_date)} and {format_date_for_display(end_date)}.")

        except Exception as e:
            st.warning(f"Could not display activity chart: {e}")
            logging.error(f"Error processing activity data: {e}")

    elif not error_message:
        st.info("Waiting for activity data...")
     # If there was an error, the message is displayed above the tabs


with tab3:
    st.header("Risk Analysis")
    st.info("Detailed risk analysis visualizations coming soon...")
    # Potential ideas:
    # - Evolution of risk level for specific body parts over time
    # - Correlation between ABCDE criteria and final classification
    # - Map visualization if geolocation data is available