# Linux Deployment

This deployment keeps Streamlit as the operator console and FastAPI as the Mother AI control plane. It does not require Google Cloud.

## 1. Prepare the host

Use a dedicated Linux user and Python 3.11 virtual environment.

Commands:
    git clone https://github.com/abbasshayek652-boop/AI-SYSTEM.git
    cd AI-SYSTEM
    python3.11 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements_streamlit.txt
    cp .env.example .env
    chmod 600 .env

Set real secrets only in .env or the service manager environment. Never commit them.

## 2. Run FastAPI

    source /opt/mother-ai/.venv/bin/activate
    cd /opt/mother-ai/AI-SYSTEM
    python -m mother_ai.run

Verify health with /healthz and readiness with /readyz.

## 3. Run Streamlit

    export API_BASE=http://127.0.0.1:8000
    streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501

## 4. systemd

Run FastAPI and Streamlit as separate services so they can restart independently.

FastAPI service: /etc/systemd/system/mother-ai-gateway.service

    [Unit]
    Description=Mother AI Gateway
    After=network.target

    [Service]
    User=motherai
    WorkingDirectory=/opt/mother-ai/AI-SYSTEM
    EnvironmentFile=/opt/mother-ai/AI-SYSTEM/.env
    ExecStart=/opt/mother-ai/AI-SYSTEM/.venv/bin/python -m mother_ai.run
    Restart=on-failure
    RestartSec=5

    [Install]
    WantedBy=multi-user.target

Streamlit service: /etc/systemd/system/mother-ai-streamlit.service

    [Unit]
    Description=Mother AI Streamlit Console
    After=mother-ai-gateway.service

    [Service]
    User=motherai
    WorkingDirectory=/opt/mother-ai/AI-SYSTEM
    EnvironmentFile=/opt/mother-ai/AI-SYSTEM/.env
    Environment=API_BASE=http://127.0.0.1:8000
    ExecStart=/opt/mother-ai/AI-SYSTEM/.venv/bin/streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
    Restart=on-failure
    RestartSec=5

    [Install]
    WantedBy=multi-user.target

Then run:
    sudo systemctl daemon-reload
    sudo systemctl enable --now mother-ai-gateway.service
    sudo systemctl enable --now mother-ai-streamlit.service

## 5. Operational checks

Verify health, readiness, authentication, connections, event recording and approvals. Binance must remain read-only and LinkedIn publishing must remain approval-gated.

Do not expose the FastAPI control plane directly to the public internet without deliberate HTTPS, authentication, firewall and reverse-proxy configuration.
