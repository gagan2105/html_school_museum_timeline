import os
import json
from pydantic import BaseModel

CONFIG_FILE = "config.json"
PROMPT_LIB_FILE = "prompt_library.json"

class AppConfig(BaseModel):
    fooocus_url: str = "http://127.0.0.1:7865"
    output_image_dir: str = "assets/generated/images/"
    output_gif_dir: str = "assets/generated/gifs/"
    image_size: int = 512
    animation_duration: int = 90  # ms per frame
    fps: int = 12
    gif_quality: int = 85
    theme: str = "dark"

def load_config() -> AppConfig:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig(**data)
        except Exception:
            pass
    return AppConfig()

def save_config(config: AppConfig):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config.dict(), f, indent=4, ensure_ascii=False)
    # Ensure directories exist
    os.makedirs(config.output_image_dir, exist_ok=True)
    os.makedirs(config.output_gif_dir, exist_ok=True)

# Ensure directories exist upon import
_initial_config = load_config()
os.makedirs(_initial_config.output_image_dir, exist_ok=True)
os.makedirs(_initial_config.output_gif_dir, exist_ok=True)
os.makedirs("images", exist_ok=True) # compatibility with old system
