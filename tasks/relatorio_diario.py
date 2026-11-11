import os
import requests
import pandas as pd
from core.logger import logger

# Essential task declarations for dynamic loader discovery
TASK_NAME = "relatorio_diario"
TASK_DESCRIPTION = "Baixa dados públicos de uma API, faz análise e agregação básica usando pandas, e despacha para webhook."
TASK_TRIGGER_TYPE = "cron"
# Configured by default to run at 08:00 every day
TASK_TRIGGER_ARGS = {
    "hour": "8",
    "minute": "0",
    "second": "0"
}

def execute():
    """
    Executes the scheduled daily report pipeline:
    1. Downloads mock/public API statistical data (falling back safely to mock if offline).
    2. Uses Pandas to read, clean, and compute aggregations.
    3. Dispatches a formatted notification payload to a target webhook.
    """
    logger.info("[relatorio_diario] Initializing Daily Report generation...")

    # For testing, we use a reliable mock data endpoint, or local failover
    api_url = os.getenv("API_REPORT_DATA_URL", "https://jsonplaceholder.typicode.com/posts")
    webhook_url = os.getenv("NOTIFICATIONS_WEBHOOK_URL", "")

    try:
        logger.info(f"[relatorio_diario] Fetching data from: {api_url}")
        response = requests.get(api_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
        else:
            raise requests.RequestException(f"HTTP code: {response.status_code}")

    except Exception as e:
        logger.warning(f"[relatorio_diario] API request failed ({e}). Falling back to internal mock data generator.")
        # Generates fallback structured dataframe data
        data = [
            {"userId": 1, "id": 101, "title": "System health OK", "body": "All backend operations normal."},
            {"userId": 1, "id": 102, "title": "Database backup completed", "body": "Automatic snapshots stored."},
            {"userId": 2, "id": 103, "title": "High CPU warning", "body": "Spike in CPU consumption resolved."},
            {"userId": 2, "id": 104, "title": "Disk usage critical", "body": "Purge script triggered."}
        ]

    # Convert to Pandas Dataframe
    df = pd.DataFrame(data)

    # Simple Pandas analytics/processing:
    # Let's count posts/alerts grouped by userId
    grouped_stats = df.groupby("userId").size().reset_index(name="counts")
    total_items = len(df)
    unique_users = df["userId"].nunique()

    # Formulating the report summary text
    summary_message = (
        f"📊 **RELATÓRIO DIÁRIO DE PROCESSAMENTO** 📊\n"
        f"- Total de registros analisados: {total_items}\n"
        f"- Usuários únicos afetados: {unique_users}\n\n"
        f"**Detalhamento por Usuário (Top 5):**\n"
    )
    for _, row in grouped_stats.head(5).iterrows():
        summary_message += f"  • Usuário ID {row['userId']}: {row['counts']} ocorrência(s)\n"

    logger.info(f"[relatorio_diario] Successfully generated summary:\n{summary_message}")

    # Dispatch via webhook
    if webhook_url:
        try:
            logger.info(f"[relatorio_diario] Sending webhook notification to configured endpoint...")
            # Detect Slack vs Discord format slightly or send generic JSON
            payload = {"content": summary_message, "text": summary_message}
            resp = requests.post(webhook_url, json=payload, timeout=10)
            logger.info(f"[relatorio_diario] Webhook response status code: {resp.status_code}")
        except Exception as err:
            logger.error(f"[relatorio_diario] Failed to dispatch webhook notification: {err}")
    else:
        logger.info("[relatorio_diario] No NOTIFICATIONS_WEBHOOK_URL set. Notification logged to console.")
