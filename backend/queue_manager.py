import os
import time
import uuid
import json
import asyncio
import urllib.request
import urllib.parse
from pydantic import BaseModel
from typing import Dict, List, Optional
from backend.config import load_config
from backend.logger import log_event
from backend.effects import animate_image, auto_detect_effect
from PIL import Image

EVENTS_DATA_FILE = "events_data.json"

class GenerationJob(BaseModel):
    job_id: str
    event_ids: List[int]
    job_type: str  # "image_only", "gif_pipeline", "batch_image", "batch_gif"
    mode: str  # "fooocus", "pollinations", "procedural"
    prompt: Optional[str] = None
    effect: str = "auto"
    status: str = "queued"  # "queued", "connecting", "sending_prompt", "generating_image", "creating_animation", "saving_gif", "completed", "failed"
    progress: float = 0.0  # 0.0 to 100.0
    message: str = "Job added to queue."
    error: Optional[str] = None
    retry_count: int = 0
    results: List[dict] = []  # list of {event_id: int, image_path: str, gif_path: str, success: bool}

# In-memory database of jobs
JOBS: Dict[str, GenerationJob] = {}
# Active event generations to prevent duplicates
ACTIVE_EVENTS = set()

# Async Queue
job_queue = asyncio.Queue()

# Check server health
async def check_fooocus_online(url: str) -> bool:
    try:
        url_parsed = urllib.parse.urlparse(url)
        # Try connecting to the Gradio or REST endpoint
        # Default port is 7865, check with 2s timeout
        host = url_parsed.hostname or "127.0.0.1"
        port = url_parsed.port or 7865
        
        # Async socket connect
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=2.0
        )
        writer.close()
        await writer.wait_closed()
        return True
    except Exception:
        return False

def check_gpu_status():
    """
    Detect available GPU (if PyTorch is installed and CUDA is available, or otherwise)
    """
    try:
        import torch
        if torch.cuda.is_available():
            return {
                "gpu_available": True,
                "gpu_device": torch.cuda.get_device_name(0),
                "gpu_memory": f"{torch.cuda.get_device_properties(0).total_memory / (1024**3):.1f} GB"
            }
    except Exception:
        pass
    
    # Fallback/Detect Windows DXGI or Linux lspci
    return {
        "gpu_available": False,
        "gpu_device": "CPU Only",
        "gpu_memory": "N/A"
    }

def draw_procedural_card(title, year, era, grade, color_hex, output_path, size=(512, 512)):
    color_hex = color_hex.lstrip("#")
    r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    base_color = (int(r * 0.15), int(g * 0.15), int(b * 0.15))
    end_color = (15, 15, 20)
    
    img = Image.new("RGB", size)
    draw = ImageDraw_helper(img)
    
    # Gradient
    for y in range(size[1]):
        t = y / (size[1] - 1)
        curr_r = int(base_color[0] * (1 - t) + end_color[0] * t)
        curr_g = int(base_color[1] * (1 - t) + end_color[1] * t)
        curr_b = int(base_color[2] * (1 - t) + end_color[2] * t)
        draw.line([(0, y), (size[0], y)], fill=(curr_r, curr_g, curr_b))
        
    border_color = (int(r * 0.4), int(g * 0.4), int(b * 0.4))
    draw.rectangle([20, 20, size[0] - 21, size[1] - 21], outline=border_color, width=1)
    
    # Accents
    accent_color = (r, g, b)
    bracket_len = 15
    draw.line([(15, 20), (15 + bracket_len, 20)], fill=accent_color, width=2)
    draw.line([(20, 15), (20, 15 + bracket_len)], fill=accent_color, width=2)
    draw.line([(size[0] - 20 - bracket_len, 20), (size[0] - 15, 20)], fill=accent_color, width=2)
    draw.line([(size[0] - 20, 15), (size[0] - 20, 15 + bracket_len)], fill=accent_color, width=2)
    
    from PIL import ImageFont
    try:
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_year = ImageFont.truetype("arial.ttf", 18)
        font_meta = ImageFont.truetype("arial.ttf", 12)
    except IOError:
        font_title = ImageFont.load_default()
        font_year = ImageFont.load_default()
        font_meta = ImageFont.load_default()
        
    draw.text((35, 30), era.upper(), fill=(180, 180, 180), font=font_meta)
    
    words = title.split()
    lines = []
    curr_line = []
    for w in words:
        test = " ".join(curr_line + [w])
        if font_title.getlength(test) <= size[0] - 80:
            curr_line.append(w)
        else:
            if curr_line:
                lines.append(" ".join(curr_line))
            curr_line = [w]
    if curr_line:
        lines.append(" ".join(curr_line))
        
    line_h = 32
    y_start = (size[1] - len(lines) * line_h) // 2
    for idx, l in enumerate(lines):
        w_len = font_title.getlength(l)
        draw.text(((size[0] - w_len) // 2, y_start + idx * line_h), l, fill=(255, 255, 255), font=font_title)
        
    year_str = f"— {year} —"
    y_len = font_year.getlength(year_str)
    draw.text(((size[0] - y_len) // 2, size[1] - 60), year_str, fill=accent_color, font=font_year)
    
    img.save(output_path)

def ImageDraw_helper(img):
    from PIL import ImageDraw
    return ImageDraw.Draw(img)

# Main background generation step for a single event
async def process_single_event(
    event_id: int, 
    job: GenerationJob, 
    prompt_text: str, 
    config
) -> dict:
    timestamp = int(time.time())
    
    # 1. Load Event Data
    if not os.path.exists(EVENTS_DATA_FILE):
        raise FileNotFoundError("Missing events_data.json database file.")
        
    with open(EVENTS_DATA_FILE, "r", encoding="utf-8") as f:
        events = json.load(f)
        
    event = next((e for e in events if e["id"] == event_id), None)
    if not event:
        raise ValueError(f"Event with ID {event_id} not found.")
        
    # Paths
    img_filename = f"event_{event_id}_{timestamp}.png"
    gif_filename = f"event_{event_id}_{timestamp}.gif"
    
    raw_img_path = os.path.join(config.output_image_dir, img_filename)
    gif_path = os.path.join(config.output_gif_dir, gif_filename)
    
    success = False
    
    # 2. Check server if local Fooocus
    if job.mode == "fooocus":
        job.status = "connecting"
        job.message = f"Checking if local Fooocus server is online..."
        log_event("request", {"event_id": event_id, "mode": job.mode, "status": job.status})
        
        is_online = await check_fooocus_online(config.fooocus_url)
        if not is_online:
            raise ConnectionError(
                "❌ AI Image Server is not running. Please ask the lab administrator to start the Fooocus server."
            )
            
        job.status = "sending_prompt"
        job.message = f"Sending prompt to local Fooocus server at {config.fooocus_url}..."
        log_event("request", {"event_id": event_id, "status": job.status})
        
        # Perform image generation via Fooocus REST or Gradio client
        success = await generate_fooocus_image_async(prompt_text, raw_img_path, config.fooocus_url)
        if not success:
            raise RuntimeError(
                "❌ Local Fooocus server failed to generate image. Please check Fooocus console for errors."
            )
            
    elif job.mode == "pollinations":
        job.status = "connecting"
        job.message = "Connecting to Pollinations Cloud AI Service..."
        log_event("request", {"event_id": event_id, "mode": job.mode, "status": job.status})
        
        job.status = "sending_prompt"
        job.message = "Sending prompt to Pollinations Cloud API..."
        
        # Async download from pollinations
        success = await generate_pollinations_image_async(prompt_text, raw_img_path, event_id)
        if not success:
            raise RuntimeError(
                "❌ Cloud generation failed. Please verify your internet connection."
            )
            
    elif job.mode == "procedural":
        job.status = "generating_image"
        job.message = "Drawing themed procedural display card..."
        
        # Draw instantly
        draw_procedural_card(event["title"], event["year"], event["era"], event["grade"], event["color"], raw_img_path)
        success = True
        
    else:
        raise ValueError(f"Invalid generation mode: {job.mode}")
        
    if not success or not os.path.exists(raw_img_path):
        raise RuntimeError("Failed to save generated base static image.")
        
    # If job_type is image only, stop here
    if job.job_type == "image_only" or job.job_type == "batch_image":
        # Update database with static path
        relative_img = raw_img_path.replace("\\", "/")
        event["image"] = relative_img
        event["is_ai_image"] = (job.mode != "procedural")
        
        with open(EVENTS_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=4, ensure_ascii=False)
            
        return {
            "event_id": event_id,
            "image_path": relative_img,
            "gif_path": "",
            "success": True
        }
        
    # 3. Create Animation
    job.status = "creating_animation"
    job.message = f"Applying animation effect '{job.effect}'..."
    log_event("request", {"event_id": event_id, "effect": job.effect, "status": job.status})
    
    # Run CPU intensive animation in thread pool to prevent blocking the async loop
    loop = asyncio.get_running_loop()
    detected_effect = await loop.run_in_executor(
        None, 
        animate_image, 
        raw_img_path, 
        job.effect, 
        gif_path, 
        config, 
        prompt_text, 
        event["title"]
    )
    
    # 4. Saving GIF
    job.status = "saving_gif"
    job.message = "Optimizing and saving GIF to timeline assets..."
    
    # Wait briefly to let disk operations settle
    await asyncio.sleep(0.5)
    
    # Update events_data.json
    relative_gif = gif_path.replace("\\", "/")
    event["image"] = relative_gif
    event["is_ai_image"] = True
    
    with open(EVENTS_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)
        
    # Log success performance
    log_event("performance", {
        "event_id": event_id,
        "mode": job.mode,
        "effect": detected_effect,
        "gif_path": relative_gif
    })
    
    return {
        "event_id": event_id,
        "image_path": raw_img_path.replace("\\", "/"),
        "gif_path": relative_gif,
        "detected_effect": detected_effect,
        "success": True
    }

async def generate_pollinations_image_async(prompt: str, output_path: str, seed: int) -> bool:
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=384&model=flux&seed={seed}"
        
        # Async HTTP GET
        loop = asyncio.get_running_loop()
        def download():
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(output_path, 'wb') as f:
                    f.write(response.read())
            return True
            
        return await loop.run_in_executor(None, download)
    except Exception as e:
        print(f"Pollinations async failed: {e}")
        return False

async def generate_fooocus_image_async(prompt: str, output_path: str, host: str) -> bool:
    # Attempt REST API first
    loop = asyncio.get_running_loop()
    
    def rest_call():
        try:
            api_url = f"{host.rstrip('/')}/v1/generation/text-to-image"
            payload = {
                "prompt": prompt,
                "negative_prompt": "",
                "style_selections": ["Cinematic"],
                "performance_selection": "Speed",
                "aspect_ratio": "1024*1024",
                "image_number": 1,
                "sharpness": 2.0
            }
            req = urllib.request.Request(
                api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                img_url = None
                if isinstance(res_data, list) and len(res_data) > 0:
                    img_url = res_data[0].get("url")
                elif isinstance(res_data, dict):
                    if "images" in res_data:
                        img_url = res_data["images"][0].get("url")
                    elif "url" in res_data:
                        img_url = res_data["url"]
                
                if img_url:
                    urllib.request.urlretrieve(img_url, output_path)
                    return True
        except Exception as e:
            print(f"Fooocus REST call failed: {e}")
        return False
        
    def gradio_call():
        try:
            from gradio_client import Client
            client = Client(host, serialize=False)
            result = client.predict(
                prompt,
                "",
                "Cinematic",
                "Speed",
                "1024×1024",
                1,
                12345,
                0.5,
                "None"
            )
            if result and isinstance(result, list) and len(result) > 0:
                temp_path = result[0]
                Image.open(temp_path).save(output_path)
                return True
        except Exception as e:
            print(f"Gradio fallback failed: {e}")
        return False

    success = await loop.run_in_executor(None, rest_call)
    if not success:
        success = await loop.run_in_executor(None, gradio_call)
    return success

# Background Queue Processor
async def queue_worker():
    while True:
        job_id = await job_queue.get()
        job = JOBS.get(job_id)
        if not job:
            job_queue.task_done()
            continue
            
        config = load_config()
        job.status = "connecting"
        job.progress = 5.0
        
        total_events = len(job.event_ids)
        successful_events = []
        
        try:
            for idx, event_id in enumerate(job.event_ids):
                # Check for duplicates
                if event_id in ACTIVE_EVENTS:
                    continue
                ACTIVE_EVENTS.add(event_id)
                
                # Fetch prompt for event
                from backend.prompt_library import get_prompt_for_event
                prompt_data = get_prompt_for_event(event_id)
                prompt_text = job.prompt if job.prompt else prompt_data["imagePrompt"]
                
                # If doing batch mode, show progress per event
                event_progress_base = (idx / total_events) * 90.0
                
                retries = 3
                event_success = False
                event_err = None
                
                for attempt in range(retries):
                    try:
                        job.retry_count = attempt
                        res = await process_single_event(event_id, job, prompt_text, config)
                        successful_events.append(res)
                        event_success = True
                        break
                    except Exception as e:
                        event_err = str(e)
                        log_event("error", {"event_id": event_id, "error": event_err, "attempt": attempt})
                        await asyncio.sleep(2.0) # Wait before retry
                        
                ACTIVE_EVENTS.discard(event_id)
                
                if not event_success:
                    # Mark this event as failed in results
                    job.results.append({
                        "event_id": event_id,
                        "success": False,
                        "error": event_err or "Unknown generation failure."
                    })
                else:
                    job.results.append(successful_events[-1])
                    
                job.progress = 5.0 + ((idx + 1) / total_events) * 90.0
                
            # Finish job
            job.status = "completed"
            job.progress = 100.0
            job.message = f"Successfully processed {len(successful_events)} of {total_events} events."
            log_event("response", {"job_id": job_id, "status": job.status, "processed_count": len(successful_events)})
            
        except Exception as e:
            job.status = "failed"
            job.progress = 100.0
            job.error = str(e)
            job.message = f"Job failed: {str(e)}"
            log_event("error", {"job_id": job_id, "error": str(e)})
            
        finally:
            job_queue.task_done()
