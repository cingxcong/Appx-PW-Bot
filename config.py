"""Runtime configuration.

All credentials must be supplied through environment variables.
Do not put live Telegram credentials or user session tokens in source control.
"""
import os


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


api_id = int(_required("API_ID"))
api_hash = _required("API_HASH")
bot_token = _required("BOT_TOKEN")
auth_users = [
    int(value.strip())
    for value in _required("AUTH_USERS").split(",")
    if value.strip().isdigit()
]
if not auth_users:
    raise RuntimeError("AUTH_USERS must contain at least one numeric Telegram user ID")
