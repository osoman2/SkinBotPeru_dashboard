import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

# Check authentication
if "access_token" not in st.session_state or not st.session_state["access_token"]:
    st.warning("Please login first")
    st.stop()

st.title("📊 Melanoma Detection Analytics")

# Date filter in sidebar
st.sidebar.header("Filters")
date_range = st.sidebar.date_input(
    "Date Range",
    value=(datetime.now() - timedelta(days=30), datetime.now()),
    max_value=datetime.now()
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    st.error("Please select both start and end dates")
    st.stop()

# Fetch dashboard stats
try:
    headers = {
        "Authorization": f"Bearer {st.session_state['access_token']}",
        "Content-Type": "application/json"
    }
    params = {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
    
    # Add tabs for different views
    tab1, tab2, tab3 = st.tabs(["Overview", "User Activity", "Risk Analysis"])
    
    with tab1:
        response = requests.get(
            f"{BASE_URL}/dashboard/stats",
            headers=headers,
            params=params
        )
        
        # Debug information (you can remove this in production)
        if response.status_code != 200:
            st.error(f"Server returned status code: {response.status_code}")
            st.error(f"Response content: {response.text}")
            st.stop()
            
        try:
            stats = response.json()
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON response: {str(e)}")
            st.error(f"Raw response: {response.text}")
            st.stop()
        
        # Display KPIs in columns
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Users", stats.get("total_users", 0))
        with col2:
            st.metric("Total Images", stats.get("total_images", 0))
        with col3:
            st.metric("Total Analyses", stats.get("total_analyses", 0))
        with col4:
            total_images = stats.get("total_images", 0)
            total_analyses = stats.get("total_analyses", 0)
            success_rate = (total_analyses / total_images * 100 
                          if total_images > 0 else 0)
            st.metric("Analysis Rate", f"{success_rate:.1f}%")
        
        # Charts
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Body Part Distribution")
            body_part_distribution = stats.get("body_part_distribution", [])
            if body_part_distribution:
                body_part_df = pd.DataFrame(body_part_distribution)
                fig = px.pie(body_part_df, values="count", names="_id", 
                           title="Distribution by Body Part")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No body part distribution data available")
        
        with col2:
            st.subheader("Risk Distribution")
            risk_distribution = stats.get("risk_distribution", [])
            if risk_distribution:
                risk_df = pd.DataFrame(risk_distribution)
                fig = px.bar(risk_df, x="_id", y="count", 
                           title="Distribution by Risk Level")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No risk distribution data available")
    
    with tab2:
        days = (end_date - start_date).days
        activity_response = requests.get(
            f"{BASE_URL}/dashboard/user_activity",
            headers=headers,
            params={"days": days}
        )
        
        if activity_response.status_code != 200:
            st.error(f"Failed to fetch activity data: {activity_response.text}")
            st.stop()
            
        activity_data = activity_response.json()
        
        st.subheader("Daily Activity")
        
        # Convert to dataframes
        daily_uploads = activity_data.get("daily_uploads", [])
        daily_analyses = activity_data.get("daily_analyses", [])
        
        if daily_uploads or daily_analyses:
            uploads_df = pd.DataFrame(daily_uploads)
            analyses_df = pd.DataFrame(daily_analyses)
            
            fig = go.Figure()
            if not uploads_df.empty:
                fig.add_trace(go.Scatter(
                    x=uploads_df["_id"],
                    y=uploads_df["uploads"],
                    name="Uploads",
                    mode="lines+markers"
                ))
            if not analyses_df.empty:
                fig.add_trace(go.Scatter(
                    x=analyses_df["_id"],
                    y=analyses_df["analyses"],
                    name="Analyses",
                    mode="lines+markers"
                ))
            fig.update_layout(
                title="Daily Activity Trends",
                xaxis_title="Date",
                yaxis_title="Count"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity data available for the selected period")
    
    with tab3:
        st.subheader("Risk Analysis Over Time")
        st.info("Risk analysis visualizations coming soon...")

except requests.RequestException as e:
    st.error(f"Error connecting to server: {str(e)}")
    st.error(f"Please check if the server is running at {BASE_URL}")
