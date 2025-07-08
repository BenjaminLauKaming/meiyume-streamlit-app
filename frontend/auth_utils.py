"""
Authentication utilities for Streamlit app
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta

DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000")

def get_jwt_token(username, password):
    """Get JWT token from Django backend"""
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/api/token/",
            json={
                "username": username,
                "password": password
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            tokens = response.json()
            return tokens
        else:
            st.error(f"Login failed: {response.status_code}")
            if response.status_code == 401:
                st.error("Invalid username or password")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend server")
        return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None

def refresh_jwt_token(refresh_token):
    """Refresh JWT token"""
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/api/token/refresh/",
            json={"refresh": refresh_token},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception:
        return None

def is_token_valid(token):
    """Check if JWT token is valid"""
    try:
        response = requests.post(
            f"{DJANGO_API_URL}/api/token/verify/",
            json={"token": token},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False

def get_auth_headers():
    """Get authentication headers for API requests"""
    if 'jwt_tokens' in st.session_state and st.session_state.jwt_tokens:
        access_token = st.session_state.jwt_tokens.get('access')
        if access_token:
            return {"Authorization": f"Bearer {access_token}"}
    return {}

def ensure_authenticated():
    """Ensure user is authenticated, refresh token if needed"""
    if 'jwt_tokens' not in st.session_state or not st.session_state.jwt_tokens:
        return False
    
    access_token = st.session_state.jwt_tokens.get('access')
    refresh_token = st.session_state.jwt_tokens.get('refresh')
    
    # Check if access token is valid
    if access_token and is_token_valid(access_token):
        return True
    
    # Try to refresh the token
    if refresh_token:
        new_tokens = refresh_jwt_token(refresh_token)
        if new_tokens:
            st.session_state.jwt_tokens.update(new_tokens)
            return True
    
    # Authentication failed
    st.session_state.jwt_tokens = None
    st.session_state.authenticated = False
    return False

def render_login_form():
    """Render login form for JWT authentication"""
    st.title("🔐 Login")
    st.info("Please login to access the CAD Analyzer")
    
    with st.form("jwt_login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            if username and password:
                with st.spinner("Authenticating..."):
                    tokens = get_jwt_token(username, password)
                    if tokens:
                        st.session_state.jwt_tokens = tokens
                        st.session_state.authenticated = True
                        st.session_state.user_info = {
                            "username": username,
                            "email": f"{username}@company.com"
                        }
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Login failed. Please check your credentials.")
            else:
                st.error("Please enter both username and password")
    
    # Quick login for development
    if st.button("🚀 Quick Login (testuser)", use_container_width=True):
        tokens = get_jwt_token("testuser", "testpass123")
        if tokens:
            st.session_state.jwt_tokens = tokens
            st.session_state.authenticated = True
            st.session_state.user_info = {
                "username": "testuser",
                "email": "test@example.com"
            }
            st.success("Quick login successful!")
            st.rerun()
        else:
            st.error("Quick login failed") 