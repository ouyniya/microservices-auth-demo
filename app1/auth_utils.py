import requests
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")

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

def is_logged_in():
    return "access_token" in st.session_state and st.session_state.access_token is not None