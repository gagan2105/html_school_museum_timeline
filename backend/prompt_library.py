import os
import json

PROMPT_LIB_FILE = "prompt_library.json"
EVENTS_DATA_FILE = "events_data.json"

def get_clean_cause(event: dict) -> str:
    cause_text = event.get("cause_effect", "")
    cause_text = cause_text.replace("Cause & effect details not available.", "").strip()
    # Find the Cause / Effect segments
    if "Cause:" in cause_text:
        # Keep it simple
        return cause_text[:120]
    return cause_text[:100]

def initialize_prompt_library():
    if os.path.exists(PROMPT_LIB_FILE):
        return
    
    # Load events to generate default prompt library
    if not os.path.exists(EVENTS_DATA_FILE):
        return
        
    try:
        with open(EVENTS_DATA_FILE, "r", encoding="utf-8") as f:
            events = json.load(f)
            
        library = {}
        for e in events:
            event_id = str(e["id"])
            title = e["title"]
            clean_cause = get_clean_cause(e)
            
            # Formulate template
            prompt_parts = [f"A historical illustration representing {title}."]
            if clean_cause:
                prompt_parts.append(clean_cause)
            prompt_parts.append(f"Era: {e['era']}, Year: {e['year']}.")
            prompt_parts.append("Cinematic lighting, oil painting illustration style, highly detailed, masterwork.")
            
            # Map default animations based on keywords
            animation = "auto"
            title_lower = title.lower()
            if any(w in title_lower for w in ["fire", "burn", "flame", "campfire"]):
                animation = "fire"
            elif any(w in title_lower for w in ["wheel", "spin", "rotate", "chariot", "potter", "chakra"]):
                animation = "wheel"
            elif any(w in title_lower for w in ["water", "river", "canal", "aqueduct", "ocean", "sea", "bath"]):
                animation = "water"
            elif any(w in title_lower for w in ["rain", "monsoon"]):
                animation = "rain"
            elif any(w in title_lower for w in ["snow", "winter", "ice"]):
                animation = "snow"
            elif any(w in title_lower for w in ["flag", "banner"]):
                animation = "flag"
            elif any(w in title_lower for w in ["tree", "forest", "leaves"]):
                animation = "tree"
            elif any(w in title_lower for w in ["cloud", "sky", "storm"]):
                animation = "clouds"
            elif any(w in title_lower for w in ["candle", "lantern", "lamp"]):
                animation = "candle"
            elif any(w in title_lower for w in ["smoke", "steam"]):
                animation = "smoke"
            elif any(w in title_lower for w in ["crowd", "people", "assembly", "revolt", "march"]):
                animation = "crowd"
            elif any(w in title_lower for w in ["bird", "fly", "pigeon"]):
                animation = "birds"
            elif any(w in title_lower for w in ["wind", "breeze"]):
                animation = "wind"
            elif any(w in title_lower for w in ["explosion", "gunpowder", "bomb", "blast"]):
                animation = "explosion"
                
            library[event_id] = {
                "title": title,
                "imagePrompt": " ".join(prompt_parts),
                "animation": animation
            }
            
        with open(PROMPT_LIB_FILE, "w", encoding="utf-8") as f:
            json.dump(library, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error initializing prompt library: {e}")

def load_prompt_library() -> dict:
    initialize_prompt_library()
    if os.path.exists(PROMPT_LIB_FILE):
        try:
            with open(PROMPT_LIB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_prompt_library(library: dict):
    with open(PROMPT_LIB_FILE, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=4, ensure_ascii=False)

def get_prompt_for_event(event_id: int) -> dict:
    lib = load_prompt_library()
    ev_id_str = str(event_id)
    if ev_id_str in lib:
        return lib[ev_id_str]
    return {
        "title": f"Event {event_id}",
        "imagePrompt": f"A historical illustration for event {event_id}.",
        "animation": "auto"
    }

def update_prompt_for_event(event_id: int, image_prompt: str, animation: str):
    lib = load_prompt_library()
    ev_id_str = str(event_id)
    if ev_id_str not in lib:
        lib[ev_id_str] = {}
    lib[ev_id_str]["imagePrompt"] = image_prompt
    lib[ev_id_str]["animation"] = animation
    save_prompt_library(lib)
