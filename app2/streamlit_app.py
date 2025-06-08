import streamlit as st
import requests
import pandas as pd
import random
from shared_auth_utils import (
    register_user, login_user, verify_otp, verify_token, is_logged_in,
    save_shared_session, clear_shared_session, get_cross_app_url
)

st.set_page_config(page_title="App 2 - Analytics", page_icon="📈")

def main_app():
    st.title("📈 App 2 - Analytics")
    st.write(f"Welcome, {st.session_state.user_email}!")
    
    st.header("Analytics Content")
    st.info("This is App 2 - You can add your specific functionality here")
    
    # Sample analytics content
    chart_data = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
        'Sales': [random.randint(100, 500) for _ in range(5)]
    })
    st.line_chart(chart_data.set_index('Month'))
    
    # Quick access to App 1 with shared session
    st.header("Quick Access")
    app1_url = get_cross_app_url(8501, st.session_state.access_token)
    st.markdown(f'<a href="{app1_url}" target="_blank">🔗 Open App 1 (Shared Session)</a>', unsafe_allow_html=True)
    
    if st.button("Logout"):
        clear_shared_session()
        st.session_state.access_token = None
        st.session_state.user_email = None
        st.rerun()

def auth_page():
    st.title("🔐 Authentication - App 2")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.header("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if email and password:
                response = login_user(email, password)
                if response.status_code == 200:
                    st.session_state.pending_email = email
                    st.session_state.show_otp = True
                    st.success("OTP sent to your email!")
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Login failed"))
    
    with tab2:
        st.header("Register")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Register"):
            if reg_email and reg_password and reg_confirm:
                if reg_password != reg_confirm:
                    st.error("Passwords don't match")
                else:
                    response = register_user(reg_email, reg_password)
                    if response.status_code == 200:
                        st.success("Registration successful! You can now login.")
                    else:
                        st.error(response.json().get("detail", "Registration failed"))

def otp_page():
    st.title("🔐 Enter OTP")
    st.write(f"Please enter the OTP sent to {st.session_state.pending_email}")
    
    otp_code = st.text_input("OTP Code", max_chars=6)
    
    if st.button("Verify OTP"):
        if otp_code:
            response = verify_otp(st.session_state.pending_email, otp_code)
            if response.status_code == 200:
                token_data = response.json()
                st.session_state.access_token = token_data["access_token"]
                st.session_state.user_email = st.session_state.pending_email
                st.session_state.show_otp = False
                st.session_state.pending_email = None
                
                # Save to shared session
                save_shared_session(st.session_state.user_email, st.session_state.access_token)
                
                st.success("Login successful!")
                st.rerun()
            else:
                st.error(response.json().get("detail", "Invalid OTP"))

# Initialize session state
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "show_otp" not in st.session_state:
    st.session_state.show_otp = False
if "pending_email" not in st.session_state:
    st.session_state.pending_email = None

# Main app logic
if is_logged_in():
    # Verify token is still valid
    response = verify_token(st.session_state.access_token)
    if response.status_code == 200:
        main_app()
    else:
        clear_shared_session()
        st.session_state.access_token = None
        st.session_state.user_email = None
        st.error("Session expired. Please login again.")
        st.rerun()
elif st.session_state.show_otp:
    otp_page()
else:
    auth_page()