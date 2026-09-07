import json
import os

SESSION_FILE = "social_sessions.json"

def load_sessions():
    if not os.path.exists(SESSION_FILE):
        return {"youtube": {}, "instagram": {}, "tiktok": {}}
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_sessions(sessions):
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=4)

def add_social_account(platform: str, account_name: str, token_or_cookie: str):
    """Сохраняет токен авторизации или сессию для выбранной соцсети"""
    sessions = load_sessions()
    if platform in sessions:
        sessions[platform][account_name] = {
            "credential": token_or_cookie,
            "active": True
        }
        save_sessions(sessions)
        return True
    return False

def get_platform_accounts(platform: str):
    sessions = load_sessions()
    return sessions.get(platform, {})
