import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

st.set_page_config(
    page_title="Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None
if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None
if "show_login_success" not in st.session_state:
    st.session_state["show_login_success"] = False

# Login form if not authenticated
if not st.session_state["access_token"]:
    st.title("📊 Analytics Dashboard Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            import requests
            try:
                response = requests.post(
                    f"{BASE_URL}/login",
                    json={"username": username, "password": password}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state["access_token"] = data["access_token"]
                    st.session_state["logged_in_user"] = username
                    st.session_state["show_login_success"] = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except requests.RequestException as e:
                st.error(f"Connection error: {e}")
    
    st.stop()

# Show success message after login
if st.session_state["show_login_success"]:
    st.success(f"Welcome back, {st.session_state['logged_in_user']}!")
    st.session_state["show_login_success"] = False  # Reset the flag

# If logged in, show logout button in sidebar
if st.session_state["access_token"]:
    with st.sidebar:
        st.write(f"Logged in as: {st.session_state['logged_in_user']}")
        if st.button("Logout"):
            st.session_state["access_token"] = None
            st.session_state["logged_in_user"] = None
            st.rerun()
