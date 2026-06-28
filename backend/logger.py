import os
import json
import time
from datetime import datetime

LOG_FILE = "generation_logs.json"

def log_event(event_type: str, details: dict):
    """
    Log an event to the generation_logs.json file.
    Types: 'request', 'error', 'response', 'performance'
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "details": details
    }
    
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    logs.append(log_entry)
    
    # Cap at 500 entries to save space
    if len(logs) > 500:
        logs = logs[-500:]
        
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to write log: {e}")

def get_logs(limit: int = 100):
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            return logs[-limit:]
    except Exception:
        return []
