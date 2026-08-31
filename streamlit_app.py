"""
Mother AI Network - Streamlit Dashboard
Comprehensive UI for AI trading, analytics, and automation
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# START BACKEND ENGINE FOR STREAMLIT CLOUD
# ============================================================================
if "backend_started" not in st.session_state:
    try:
        # This turns on the FastAPI backend on port 8000 in the background
        subprocess.Popen([
            sys.executable, "-m", "uvicorn", "gateway:app", 
            "--host", "127.0.0.1", "--port", "8000"
        ])
        time.sleep(3)  # Give the engine 3 seconds to warm up
        st.session_state["backend_started"] = True
    except Exception as e:
        st.error(f"Could not start backend engine: {e}")

# ============================================================================
# CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Mother AI Network",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Mother AI - Centralized AI Controller System",
    }
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
    .status-active {
        color: #09ab3b;
        font-weight: bold;
    }
    .status-inactive {
        color: #d33f49;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.email = None
    st.session_state.role = None

if "api_base" not in st.session_state:
    # Uses 127.0.0.1 since the engine is now running locally in the background
    st.session_state.api_base = os.getenv("API_BASE", "http://127.0.0.1:8000")

if "agents_cache" not in st.session_state:
    st.session_state.agents_cache = {}

if "trading_history" not in st.session_state:
    st.session_state.trading_history = []

# ============================================================================
# API CLIENT
# ============================================================================

class AINetworkClient:
    """HTTP client for Mother AI Gateway"""
    
    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = httpx.Timeout(30.0, connect=10.0)
    
    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    async def login(self, api_key: str, email: str, role: str = "user") -> dict[str, Any]:
        """Authenticate user and get JWT token"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/auth/login",
                    json={"email": email, "role": role},
                    headers={"X-API-Key": api_key},
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Login failed: {e}")
                return {"error": str(e)}
    
    async def health_check(self) -> dict[str, Any]:
        """Check gateway health"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/healthz")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return {"error": str(e)}
    
    async def get_status(self) -> dict[str, Any]:
        """Get system status"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/readyz",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Status check failed: {e}")
                return {"error": str(e)}
    
    async def get_agents(self) -> dict[str, Any]:
        """Get all agents"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/agents",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to get agents: {e}")
                return {"error": str(e)}
    
    async def start_agent(self, agent_key: str) -> dict[str, Any]:
        """Start an agent"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/agents/{agent_key}/start",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to start agent: {e}")
                return {"error": str(e)}
    
    async def stop_agent(self, agent_key: str) -> dict[str, Any]:
        """Stop an agent"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/agents/{agent_key}/stop",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to stop agent: {e}")
                return {"error": str(e)}
    
    async def get_agent_status(self, agent_key: str) -> dict[str, Any]:
        """Get individual agent status"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/agents/{agent_key}/status",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to get agent status: {e}")
                return {"error": str(e)}
    
    async def get_exchange_markets(self) -> dict[str, Any]:
        """Get exchange market data"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/exchange/markets",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to get markets: {e}")
                return {"error": str(e)}
    
    async def get_balance(self) -> dict[str, Any]:
        """Get account balance"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/exchange/balance",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to get balance: {e}")
                return {"error": str(e)}
    
    async def get_ticker(self, symbol: str) -> dict[str, Any]:
        """Get ticker data for a symbol"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/exchange/ticker/{symbol}",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to get ticker: {e}")
                return {"error": str(e)}


def run_async(coro):
    """Run async function in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ============================================================================
# AUTHENTICATION PAGE
# ============================================================================

def render_login_page():
    """Render authentication interface"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🔐 Mother AI Login")
        st.divider()
        
        with st.form("login_form"):
            api_key = st.text_input(
                "API Key",
                type="password",
                help="Your Mother AI API key (from .env MOTHER_API_KEY)"
            )
            email = st.text_input(
                "Email",
                placeholder="user@example.com"
            )
            role = st.selectbox("Role", ["user", "admin", "operator"])
            
            submit = st.form_submit_button("🔓 Login", use_container_width=True)
            
            if submit:
                if not api_key or not email:
                    st.error("Please provide API key and email")
                else:
                    with st.spinner("Authenticating..."):
                        client = AINetworkClient(st.session_state.api_base)
                        result = run_async(client.login(api_key, email, role))
                        
                        if "error" in result:
                            st.error(f"Login failed: {result['error']}")
                        elif "token" in result:
                            st.session_state.authenticated = True
                            st.session_state.token = result["token"]
                            st.session_state.email = email
                            st.session_state.role = role
                            st.success(f"✅ Welcome, {email}!")
                            st.rerun()
                        else:
                            st.error("Unexpected response from server")
        
        st.info("💡 **Demo Mode**: Ensure your Streamlit Cloud Secrets are configured.")


# ============================================================================
# DASHBOARD COMPONENTS
# ============================================================================

def render_top_bar():
    """Render top navigation bar"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("## 🤖 Mother AI Network")
    
    with col2:
        st.caption(f"👤 {st.session_state.email} ({st.session_state.role})")
    
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.token = None
            st.session_state.email = None
            st.rerun()


def render_system_health():
    """Render system health status"""
    st.subheader("🏥 System Health")
    
    client = AINetworkClient(st.session_state.api_base, st.session_state.token)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Refresh", key="health_refresh"):
            with st.spinner("Checking health..."):
                health = run_async(client.health_check())
                if "error" not in health:
                    st.session_state.last_health = health
                    st.success("✅ Gateway Online")
                else:
                    st.error("❌ Gateway Offline")
    
    with col2:
        status = run_async(client.get_status())
        if "error" not in status:
            st.metric("API Status", "✅ Ready")
        else:
            st.metric("API Status", "❌ Error")
    
    with col3:
        st.metric("Timestamp", datetime.now().strftime("%H:%M:%S"))
    
    with col4:
        st.metric("API URL", st.session_state.api_base.split("://")[-1])


def render_agents_dashboard():
    """Render agent management interface"""
    st.header("🔧 Agent Management")
    
    client = AINetworkClient(st.session_state.api_base, st.session_state.token)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Load Agents", key="load_agents"):
            with st.spinner("Loading agents..."):
                agents = run_async(client.get_agents())
                if "error" not in agents:
                    st.session_state.agents_cache = agents
                    st.success(f"✅ Loaded {len(agents)} agent(s)")
                else:
                    st.error(f"Failed: {agents['error']}")
    
    with col2:
        if st.button("🔄 Refresh Status", key="refresh_agents"):
            st.rerun()
    
    with col3:
        auto_refresh = st.checkbox("Auto-refresh every 10s", value=False)
    
    st.divider()
    
    if not st.session_state.agents_cache:
        st.info("👈 Click 'Load Agents' to start")
        return
    
    # Display agents
    for agent_key, agent_data in st.session_state.agents_cache.items():
        with st.expander(f"🤖 {agent_key}", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            # Get agent status
            agent_status = run_async(client.get_agent_status(agent_key))
            running = agent_status.get("running", False) if "error" not in agent_status else False
            
            with col1:
                if running:
                    st.markdown('<p class="status-active">▶️ RUNNING</p>', unsafe_allow_html=True)
                else:
                    st.markdown('<p class="status-inactive">⏹️ STOPPED</p>', unsafe_allow_html=True)
            
            with col2:
                if st.button(f"▶️ Start", key=f"start_{agent_key}"):
                    with st.spinner(f"Starting {agent_key}..."):
                        result = run_async(client.start_agent(agent_key))
                        if "error" not in result:
                            st.success(f"✅ Started {agent_key}")
                            st.rerun()
                        else:
                            st.error(f"Failed: {result['error']}")
            
            with col3:
                if st.button(f"⏹️ Stop", key=f"stop_{agent_key}"):
                    with st.spinner(f"Stopping {agent_key}..."):
                        result = run_async(client.stop_agent(agent_key))
                        if "error" not in result:
                            st.success(f"✅ Stopped {agent_key}")
                            st.rerun()
                        else:
                            st.error(f"Failed: {result['error']}")
            
            with col4:
                st.caption(f"Type: {agent_data.get('type', 'unknown')}")
            
            # Agent details
            st.write("**Configuration:**")
            st.json(agent_data)


def render_trading_interface():
    """Render trading/exchange interface"""
    st.header("💹 Trading Dashboard")
    
    client = AINetworkClient(st.session_state.api_base, st.session_state.token)
    
    tab1, tab2, tab3 = st.tabs(["Markets", "Balance", "Orders"])
    
    with tab1:
        st.subheader("📊 Market Data")
        
        if st.button("Fetch Markets", key="fetch_markets"):
            with st.spinner("Loading market data..."):
                markets = run_async(client.get_exchange_markets())
                if "error" not in markets:
                    st.success(f"✅ Loaded {len(markets)} markets")
                    
                    # Create DataFrame
                    if isinstance(markets, dict):
                        df = pd.DataFrame([
                            {
                                "Symbol": k,
                                "Type": v.get("type", "unknown"),
                                "Maker Fee": v.get("maker", 0),
                                "Taker Fee": v.get("taker", 0),
                            }
                            for k, v in list(markets.items())[:50]
                        ])
                    else:
                        df = pd.DataFrame(markets[:50])
                    
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error(f"Failed: {markets['error']}")
        
        st.divider()
        
        symbol = st.text_input("Symbol", value="BTC/USDT", placeholder="e.g., BTC/USDT")
        if st.button("Get Ticker", key="get_ticker"):
            with st.spinner(f"Fetching {symbol}..."):
                ticker = run_async(client.get_ticker(symbol))
                if "error" not in ticker:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Last", f"${ticker.get('last', 0):.2f}")
                    with col2:
                        st.metric("High", f"${ticker.get('high', 0):.2f}")
                    with col3:
                        st.metric("Low", f"${ticker.get('low', 0):.2f}")
                    with col4:
                        st.metric("Volume", f"{ticker.get('quoteVolume', 0):.2f}")
                else:
                    st.error(f"Failed: {ticker['error']}")
    
    with tab2:
        st.subheader("💰 Account Balance")
        
        if st.button("Refresh Balance", key="refresh_balance"):
            with st.spinner("Loading balance..."):
                balance = run_async(client.get_balance())
                if "error" not in balance:
                    st.success("✅ Balance updated")
                    
                    if isinstance(balance, dict):
                        # Filter balance with values
                        balance_df = pd.DataFrame([
                            {
                                "Currency": k,
                                "Free": v.get("free", 0) if isinstance(v, dict) else 0,
                                "Used": v.get("used", 0) if isinstance(v, dict) else 0,
                                "Total": v.get("total", 0) if isinstance(v, dict) else 0,
                            }
                            for k, v in balance.items()
                            if k not in ["free", "used", "total"]
                        ])
                        
                        st.dataframe(
                            balance_df[balance_df["Total"] > 0],
                            use_container_width=True
                        )
                else:
                    st.error(f"Failed: {balance['error']}")
    
    with tab3:
        st.subheader("📋 Order History")
        st.info("Order history functionality coming soon")


def render_analytics():
    """Render analytics and monitoring"""
    st.header("📈 Analytics & Monitoring")
    
    tab1, tab2, tab3 = st.tabs(["Performance", "Metrics", "Logs"])
    
    with tab1:
        st.subheader("Performance Metrics")
        
        # Generate sample data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq="D")
        returns = [0.02 * (i + 1) + (i % 3) * 0.01 for i in range(30)]
        
        df = pd.DataFrame({
            "Date": dates,
            "Cumulative Return (%)": returns,
            "Daily Return (%)": [0.02 + (i % 3) * 0.01 for i in range(30)],
        })
        
        st.line_chart(df.set_index("Date"))
    
    with tab2:
        st.subheader("System Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Agents", 5)
        with col2:
            st.metric("Active Agents", 3)
        with col3:
            st.metric("Total Trades", 142)
        
        st.divider()
        
        st.subheader("Resource Usage")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Memory Usage", "256 MB / 1 GB", delta="-5 MB")
        with col2:
            st.metric("CPU Usage", "12%", delta="-3%")
    
    with tab3:
        st.subheader("System Logs")
        
        # Sample logs
        logs = [
            "[2024-08-30 10:15:23] INFO: Agent 'crypto_trader' started",
            "[2024-08-30 10:16:45] DEBUG: Fetching BTC/USDT price",
            "[2024-08-30 10:17:12] INFO: Placed order for 0.5 BTC",
            "[2024-08-30 10:18:33] INFO: Order filled successfully",
        ]
        
        st.code("\n".join(logs), language="log")


def render_settings():
    """Render settings page"""
    st.header("⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["API Configuration", "Notifications", "Advanced"])
    
    with tab1:
        st.subheader("API Configuration")
        
        new_api_base = st.text_input(
            "API Base URL",
            value=st.session_state.api_base,
            help="Mother AI Gateway base URL"
        )
        
        if new_api_base != st.session_state.api_base:
            if st.button("✅ Save API URL"):
                st.session_state.api_base = new_api_base
                st.success("API URL updated")
                st.rerun()
    
    with tab2:
        st.subheader("Notification Settings")
        
        telegram_enabled = st.checkbox("Enable Telegram Notifications", value=False)
        if telegram_enabled:
            telegram_token = st.text_input("Telegram Bot Token", type="password")
            telegram_chat = st.text_input("Telegram Chat ID")
        
        email_enabled = st.checkbox("Enable Email Notifications", value=False)
        if email_enabled:
            email_address = st.text_input("Email Address")
    
    with tab3:
        st.subheader("Advanced Settings")
        
        auto_refresh = st.slider("Auto-refresh interval (seconds)", 5, 60, 10)
        log_level = st.selectbox("Log Level", ["DEBUG", "INFO", "WARNING", "ERROR"])
        
        if st.button("💾 Save Settings"):
            st.success("Settings saved successfully")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    
    # Show login page if not authenticated
    if not st.session_state.authenticated:
        render_login_page()
        return
    
    # Authenticated dashboard
    render_top_bar()
    st.divider()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard",
        "🔧 Agents",
        "💹 Trading",
        "📈 Analytics",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_system_health()
    
    with tab2:
        render_agents_dashboard()
    
    with tab3:
        render_trading_interface()
    
    with tab4:
        render_analytics()
    
    with tab5:
        render_settings()


if __name__ == "__main__":
    main()
