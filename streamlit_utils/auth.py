"""Streamlit authentication utilities"""
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Tuple
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


class StreamlitAuth:
    """Authentication manager for Streamlit app"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv("MOTHER_JWT_SECRET", "change-me")
        self.session_timeout = 3600  # 1 hour
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_api_key(provided_key: str, expected_key: str) -> bool:
        """Verify API key using constant-time comparison"""
        return hmac.compare_digest(provided_key, expected_key)
    
    @staticmethod
    def is_session_valid() -> bool:
        """Check if session is still valid"""
        if "login_time" not in st.session_state:
            return False
        
        login_time = st.session_state.login_time
        if datetime.now() - login_time > timedelta(seconds=3600):
            return False
        
        return True
    
    @staticmethod
    def require_authentication() -> bool:
        """Decorator to require authentication"""
        if not st.session_state.get("authenticated", False):
            st.warning("Please log in to access this page")
            return False
        
        if not StreamlitAuth.is_session_valid():
            st.session_state.authenticated = False
            st.error("Session expired. Please log in again.")
            return False
        
        return True
    
    @staticmethod
    def require_role(required_role: str) -> bool:
        """Check if user has required role"""
        user_role = st.session_state.get("role", "user")
        
        role_hierarchy = {
            "user": 1,
            "operator": 2,
            "admin": 3,
        }
        
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 10, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: dict[str, list[datetime]] = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        
        if key not in self.calls:
            self.calls[key] = []
        
        # Remove old calls outside time window
        self.calls[key] = [
            call_time for call_time in self.calls[key]
            if now - call_time < timedelta(seconds=self.time_window)
        ]
        
        # Check if we've exceeded limit
        if len(self.calls[key]) >= self.max_calls:
            return False
        
        # Add current call
        self.calls[key].append(now)
        return True
    
    def get_retry_after(self, key: str) -> int:
        """Get seconds until next call is allowed"""
        if key not in self.calls or not self.calls[key]:
            return 0
        
        oldest_call = self.calls[key][0]
        retry_after = oldest_call + timedelta(seconds=self.time_window)
        seconds_left = (retry_after - datetime.now()).total_seconds()
        
        return max(0, int(seconds_left))


# Global rate limiter instance
_rate_limiter = RateLimiter(max_calls=30, time_window=60)


def check_rate_limit(user_id: str) -> Tuple[bool, int]:
    """
    Check if user has exceeded rate limit.
    Returns: (is_allowed, retry_after_seconds)
    """
    is_allowed = _rate_limiter.is_allowed(user_id)
    retry_after = _rate_limiter.get_retry_after(user_id) if not is_allowed else 0
    
    return is_allowed, retry_after
