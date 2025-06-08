# shared_auth_utils.py
import requests
import streamlit as st
import os
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import parse_qs

load_dotenv()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")

def get_temp_dir():
    """Get a shared temporary directory for session storage"""
    return Path(tempfile.gettempdir()) / "streamlit_shared_auth"

def save_shared_session(email, token):
    """Save session data to a shared location"""
    try:
        temp_dir = get_temp_dir()
        temp_dir.mkdir(exist_ok=True)
        
        session_data = {
            "email": email,
            "token": token
        }
        
        session_file = temp_dir / "current_session.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        return True
    except Exception as e:
        print(f"Error saving shared session: {e}")
        return False

def load_shared_session():
    """Load session data from shared location"""
    try:
        session_file = get_temp_dir() / "current_session.json"
        
        if not session_file.exists():
            return None
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Verify the token is still valid
        response = verify_token(session_data["token"])
        if response.status_code == 200:
            return session_data
        else:
            # Token is invalid, remove the session file
            session_file.unlink()
            return None
    except Exception as e:
        print(f"Error loading shared session: {e}")
        return None

def clear_shared_session():
    """Clear the shared session"""
    try:
        session_file = get_temp_dir() / "current_session.json"
        if session_file.exists():
            session_file.unlink()
    except Exception as e:
        print(f"Error clearing shared session: {e}")

def register_user(email, password):
    response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={"email": email, "password": password}
    )
    return response

def login_user(email, password):
    response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={"email": email, "password": password}
    )
    return response

def verify_otp(email, otp_code):
    response = requests.post(
        f"{AUTH_SERVICE_URL}/verify-otp",
        json={"email": email, "otp_code": otp_code}
    )
    return response

def verify_token(token):
    response = requests.get(
        f"{AUTH_SERVICE_URL}/verify-token",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def create_shared_session(token):
    """Create a session on the auth service"""
    response = requests.post(
        f"{AUTH_SERVICE_URL}/create-session",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response

def get_session_from_auth_service(session_id):
    """Get session data from auth service"""
    response = requests.get(f"{AUTH_SERVICE_URL}/get-session/{session_id}")
    return response

def is_logged_in():
    """Check if user is logged in (either in session state or shared session)"""
    # First check current session state
    if "access_token" in st.session_state and st.session_state.access_token is not None:
        return True
    
    # Then check shared session
    shared_session = load_shared_session()
    if shared_session:
        # Load shared session into current session state
        st.session_state.access_token = shared_session["token"]
        st.session_state.user_email = shared_session["email"]
        return True
    
    # Check URL parameters for session sharing
    query_params = st.experimental_get_query_params()
    if "session" in query_params:
        session_id = query_params["session"][0]
        response = get_session_from_auth_service(session_id)
        if response.status_code == 200:
            session_data = response.json()
            st.session_state.access_token = session_data["token"]
            st.session_state.user_email = session_data["email"]
            # Save to shared session for future use
            save_shared_session(session_data["email"], session_data["token"])
            # Clear the URL parameter
            st.experimental_set_query_params()
            return True
    
    return False

def get_cross_app_url(target_app_port, current_token):
    """Generate URL to switch to another app with shared session"""
    try:
        # Create a session on the auth service
        response = create_shared_session(current_token)
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            return f"http://localhost:{target_app_port}?session={session_id}"
        else:
            return f"http://localhost:{target_app_port}"
    except Exception as e:
        print(f"Error creating cross-app URL: {e}")
        return f"http://localhost:{target_app_port}"