import http.server
import socketserver
import json
import os
import urllib.request
import urllib.parse
import sys
import glob
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

PORT = 8000
DB_FILE = "events_data.json"
IMAGES_DIR = "images"

# --- BILINEAR INTERPOLATION SAMPLER ---

def bilinear_warp(img_np, map_x, map_y):
    H, W, C = img_np.shape
    
    # Clip coordinates to safe bounds
    map_x = np.clip(map_x, 0, W - 2)
    map_y = np.clip(map_y, 0, H - 2)
    
    # Get coordinates of 4 surrounding pixels
    x0 = np.floor(map_x).astype(np.int32)
    x1 = x0 + 1
    y0 = np.floor(map_y).astype(np.int32)
    y1 = y0 + 1
    
    # Interpolation weights
    wa = (x1 - map_x) * (y1 - map_y)
    wb = (map_x - x0) * (y1 - map_y)
    wc = (x1 - map_x) * (map_y - y0)
    wd = (map_x - x0) * (map_y - y0)
    
    wa = np.expand_dims(wa, axis=-1)
    wb = np.expand_dims(wb, axis=-1)
    wc = np.expand_dims(wc, axis=-1)
    wd = np.expand_dims(wd, axis=-1)
    
    # Sample pixels
    p00 = img_np[y0, x0]
    p10 = img_np[y0, x1]
    p01 = img_np[y1, x0]
    p11 = img_np[y1, x1]
    
    # Interpolate
    out = p00 * wa + p10 * wb + p01 * wc + p11 * wd
    return out.astype(np.float32)

# --- EFFECT 1: CAMPFIRE BURN ANIMATION ---

def generate_fire_frames(img_np, num_frames=24):
    H, W, C = img_np.shape
    
    # 1. Automatic Fire Region Detection
    # Search for bright warm pixels: R > 150, G > 90, R > B + 30
    fire_y, fire_x = np.where((img_np[..., 0] > 140) & (img_np[..., 1] > 80) & (img_np[..., 0] > img_np[..., 2] + 30))
    
    if len(fire_x) > 100:
        cx = int(np.mean(fire_x))
        cy = int(np.mean(fire_y))
        rx = int(np.std(fire_x) * 1.6)
        ry = int(np.std(fire_y) * 1.6)
    else:
        # Fallback to center-bottom
        cx, cy = W // 2, int(H * 0.72)
        rx, ry = int(W * 0.2), int(H * 0.2)
        
    rx = np.clip(rx, 60, W // 2)
    ry = np.clip(ry, 60, H // 2)
    
    # 2. Build Spatial Falloff Weight
    Y, X = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((X - cx) / rx)**2 + ((Y - cy) / ry)**2)
    spatial_weight = np.clip(1.0 - dist, 0.0, 1.0)
    spatial_weight = (np.cos(np.pi * (1.0 - spatial_weight) / 2.0))**2
    
    # 3. Build Color-based Fire Mask
    is_fire = (img_np[..., 0] > 140) & (img_np[..., 1] > 80) & (img_np[..., 0] > img_np[..., 2] + 30)
    mask_pil = Image.fromarray((is_fire * 255).astype(np.uint8), mode="L")
    mask_pil = mask_pil.filter(ImageFilter.GaussianBlur(radius=15))
    color_weight = np.array(mask_pil).astype(float) / 255.0
    
    # Combine Warp Mask
    warp_mask = color_weight * spatial_weight
    
    # 4. Setup Ember Sparks
    num_sparks = 18
    sparks = []
    np.random.seed(42)
    for i in range(num_sparks):
        lifetime = np.random.randint(8, 15)
        birth_frame = np.random.randint(0, num_frames)
        
        # Start coordinates near fire base
        start_x = np.random.randint(cx - int(rx * 0.6), cx + int(rx * 0.6))
        start_y = np.random.randint(cy - int(ry * 0.2), cy + int(ry * 0.4))
        
        vx_amp = np.random.uniform(2.0, 5.0)
        vx_freq = np.random.uniform(0.3, 0.6)
        vy = np.random.uniform(12.0, 20.0)
        size = np.random.uniform(1.2, 3.0)
        
        sparks.append({
            "lifetime": lifetime,
            "birth": birth_frame,
            "x0": start_x,
            "y0": start_y,
            "vx_amp": vx_amp,
            "vx_freq": vx_freq,
            "vy": vy,
            "size": size
        })
        
    frames = []
    for t in range(num_frames):
        # 5. Sinusoidal Warping
        phase_x = (Y / 35.0) - t * (2.0 * np.pi / num_frames)
        phase_y = (Y / 45.0) - t * (2.0 * np.pi / num_frames)
        
        dx = 8.0 * np.sin(phase_x) * warp_mask
        dy = -6.5 * (1.2 + np.cos(phase_y)) * warp_mask
        
        warped_np = bilinear_warp(img_np, X + dx, Y + dy)
        
        # 6. Global light flicker
        flicker = 1.0 + 0.05 * np.sin(t * (2.0 * np.pi / 6.0)) + 0.035 * np.sin(t * (2.0 * np.pi / 3.0) + 1.5)
        glow_mask = spatial_weight * (1.0 - color_weight)
        
        r_mod = 1.0 + (flicker - 1.0) * 0.9 * glow_mask
        g_mod = 1.0 + (flicker - 1.0) * 0.65 * glow_mask
        b_mod = 1.0 + (flicker - 1.0) * 0.15 * glow_mask
        
        warped_np[..., 0] *= r_mod
        warped_np[..., 1] *= g_mod
        warped_np[..., 2] *= b_mod
        
        warped_np = np.clip(warped_np, 0.0, 255.0).astype(np.uint8)
        
        frame_img = Image.fromarray(warped_np)
        draw = ImageDraw.Draw(frame_img)
        
        # 7. Render sparks
        for spark in sparks:
            age = (t - spark["birth"]) % num_frames
            if age < spark["lifetime"]:
                x = spark["x0"] + spark["vx_amp"] * np.sin(age * spark["vx_freq"])
                y = spark["y0"] - spark["vy"] * age
                
                progress = age / spark["lifetime"]
                current_size = spark["size"] * (1.0 - progress * 0.4)
                
                r = 255
                g = int(220 * (1.0 - progress) + 80 * progress)
                b = int(120 * (1.0 - progress) + 20 * progress)
                
                draw.ellipse([x - current_size, y - current_size, x + current_size, y + current_size], fill=(r, g, b))
                
        frames.append(frame_img)
        
    return frames

# --- EFFECT 2: SPINNING WHEEL ANIMATION ---

def generate_wheel_frames(img_np, num_frames=24):
    H, W, C = img_np.shape
    cx, cy = W // 2, H // 2
    r_max = int(W * 0.35)
    
    Y, X = np.mgrid[0:H, 0:W]
    dy = Y - cy
    dx = X - cx
    r = np.sqrt(dx**2 + dy**2)
    theta = np.arctan2(dy, dx)
    
    # Smooth rotation mask
    rot_mask = np.clip((r_max - r) / (r_max * 0.1), 0.0, 1.0)
    rot_mask = 3 * rot_mask**2 - 2 * rot_mask**3 # smoothstep
    
    frames = []
    for t in range(num_frames):
        angle = t * (2.0 * np.pi / num_frames)
        new_theta = theta + angle * rot_mask
        
        map_x = cx + r * np.cos(new_theta)
        map_y = cy + r * np.sin(new_theta)
        
        warped_np = bilinear_warp(img_np, map_x, map_y)
        warped_np = np.clip(warped_np, 0.0, 255.0).astype(np.uint8)
        frames.append(Image.fromarray(warped_np))
        
    return frames

# --- EFFECT 3: KEN BURNS PANNING/ZOOM ANIMATION ---

def generate_kenburns_frames(img_np, num_frames=20, zoom_factor=0.06):
    H, W, C = img_np.shape
    base_img = Image.fromarray(img_np.astype(np.uint8))
    
    frames = []
    for i in range(num_frames):
        t = i / (num_frames - 1)
        ease_t = 3 * t * t - 2 * t * t * t
        
        current_zoom = 1.0 + (zoom_factor * ease_t)
        crop_w = int(W / current_zoom)
        crop_h = int(H / current_zoom)
        
        # Diagonal pan displacement
        dx = int((W - crop_w) * ease_t)
        dy = int((H - crop_h) * ease_t)
        
        crop_box = (dx, dy, dx + crop_w, dy + crop_h)
        cropped_img = base_img.crop(crop_box)
        resized_img = cropped_img.resize((W, H), Image.Resampling.BILINEAR)
        frames.append(resized_img)
        
    # Return seamless ping-pong loop frames
    loop_frames = frames + frames[-2:0:-1]
    return loop_frames

# --- API INTEGRATION ---

def generate_fooocus_image(prompt, output_path, host):
    print(f"Calling Fooocus Local API at {host}...", file=sys.stderr)
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
        with urllib.request.urlopen(req, timeout=30) as response:
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
        print(f"REST API call failed: {e}. Trying Gradio client fallback...", file=sys.stderr)
        
    try:
        from gradio_client import Client
        client = Client(host, serialize=False)
        result = client.predict(
            prompt,                     # Prompt
            "",                         # Negative prompt
            "Cinematic",                # Style
            "Speed",                    # Performance
            "1024×1024",                # Aspect Ratio
            1,                          # Image Number
            12345,                      # Seed
            0.5,                        # Image Sharpness
            "None",                     # Guidance scale
        )
        if result and isinstance(result, list) and len(result) > 0:
            temp_path = result[0]
            Image.open(temp_path).save(output_path)
            return True
    except Exception as e:
        print(f"Gradio Client call failed: {e}", file=sys.stderr)
        
    return False

def generate_pollinations_image(prompt, output_path, seed_id):
    print(f"Calling Pollinations Cloud API...", file=sys.stderr)
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=384&model=flux&seed={seed_id}"
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(output_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"Pollinations Cloud API failed: {e}", file=sys.stderr)
        return False

def draw_procedural_card(title, year, era, grade, color_hex, output_path, size=(512, 512)):
    color_hex = color_hex.lstrip("#")
    r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    base_color = (int(r * 0.15), int(g * 0.15), int(b * 0.15))
    end_color = (15, 15, 20)
    
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    
    for y in range(size[1]):
        t = y / (size[1] - 1)
        curr_r = int(base_color[0] * (1 - t) + end_color[0] * t)
        curr_g = int(base_color[1] * (1 - t) + end_color[1] * t)
        curr_b = int(base_color[2] * (1 - t) + end_color[2] * t)
        draw.line([(0, y), (size[0], y)], fill=(curr_r, curr_g, curr_b))
        
    border_color = (int(r * 0.4), int(g * 0.4), int(b * 0.4))
    draw.rectangle([20, 20, size[0] - 21, size[1] - 21], outline=border_color, width=1)
    
    accent_color = (r, g, b)
    bracket_len = 15
    draw.line([(15, 20), (15 + bracket_len, 20)], fill=accent_color, width=2)
    draw.line([(20, 15), (20, 15 + bracket_len)], fill=accent_color, width=2)
    draw.line([(size[0] - 20 - bracket_len, 20), (size[0] - 15, 20)], fill=accent_color, width=2)
    draw.line([(size[0] - 20, 15), (size[0] - 20, 15 + bracket_len)], fill=accent_color, width=2)
    
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

# --- CUSTOM HTTP REQUEST HANDLER ---

class TimelineAdminHandler(http.server.SimpleHTTPRequestHandler):
    
    def log_message(self, format, *args):
        print(format % args, file=sys.stderr)

    def do_GET(self):
        if self.path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(b"[]")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/generate":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode('utf-8'))
            
            event_id = int(params.get("id"))
            prompt = params.get("prompt")
            mode = params.get("mode", "fooocus")
            host = params.get("host", "http://127.0.0.1:7865")
            effect = params.get("effect", "auto") # auto, kenburns, fire, wheel
            
            print(f"\n[API] Received generation request for Event {event_id} (Mode: {mode}, Effect: {effect})", file=sys.stderr)
            
            if not os.path.exists(DB_FILE):
                self.send_json_error("Database file events_data.json is missing.")
                return
                
            with open(DB_FILE, "r", encoding="utf-8") as f:
                events = json.load(f)
                
            event = next((e for e in events if e["id"] == event_id), None)
            if not event:
                self.send_json_error(f"Event with ID {event_id} not found in database.")
                return
                
            raw_path = os.path.join(IMAGES_DIR, f"event_{event_id}_raw.png")
            gif_path = os.path.join(IMAGES_DIR, f"event_{event_id}.gif")
            
            success = False
            
            # Phase 1: Generate static image based on selected mode
            if mode == "fooocus":
                success = generate_fooocus_image(prompt, raw_path, host)
                if not success:
                    self.send_json_error("Fooocus local generation failed. Make sure your local Fooocus server is running and API mode is accessible.")
                    return
            elif mode == "pollinations":
                success = generate_pollinations_image(prompt, raw_path, event_id)
                if not success:
                    self.send_json_error("Cloud Pollinations AI generation failed. Verify internet connection.")
                    return
            elif mode == "procedural":
                draw_procedural_card(event["title"], event["year"], event["era"], event["grade"], event["color"], raw_path)
                success = True
            else:
                self.send_json_error(f"Invalid mode specified: {mode}")
                return
                
            # Phase 2: Convert static image to looping GIF with selected effect
            if success and os.path.exists(raw_path):
                try:
                    img = Image.open(raw_path).convert("RGB")
                    # Scale down the raw image to 512x512 for fast processing
                    img = img.resize((512, 512), Image.Resampling.LANCZOS)
                    img_np = np.array(img).astype(np.float32)
                    
                    # Phase 2.1: Dynamic Auto-Detection of Effect based on Image Content
                    detected_effect = effect
                    if effect == "auto":
                        # Check prompt and title for wheel/rotation
                        event_title = event.get("title", "")
                        is_wheel = any(w in prompt.lower() or w in event_title.lower() for w in ["wheel", "spin", "rotate", "chariot", "potter", "chakra"])
                        
                        # Check image pixels for warm firelight
                        fire_y, fire_x = np.where((img_np[..., 0] > 140) & (img_np[..., 1] > 80) & (img_np[..., 0] > img_np[..., 2] + 35))
                        has_fire = len(fire_x) > 600
                        
                        if has_fire:
                            detected_effect = "fire"
                            print(f"[Auto-Detect] Found fire pixels ({len(fire_x)} px). Applying Campfire Burn effect.", file=sys.stderr)
                        elif is_wheel:
                            detected_effect = "wheel"
                            print(f"[Auto-Detect] Wheel/rotation keywords matched. Applying Spinning Wheel effect.", file=sys.stderr)
                        else:
                            detected_effect = "kenburns"
                            print(f"[Auto-Detect] Defaulting to Ken Burns panning effect.", file=sys.stderr)
                    
                    print(f"Applying effect '{detected_effect}' to generated image...", file=sys.stderr)
                    if detected_effect == "fire":
                        frames = generate_fire_frames(img_np)
                    elif detected_effect == "wheel":
                        frames = generate_wheel_frames(img_np)
                    else: # default to kenburns
                        frames = generate_kenburns_frames(img_np)
                        
                    # Save frames as looping GIF
                    palette_frames = [f.convert("P", palette=Image.Palette.ADAPTIVE) for f in frames]
                    palette_frames[0].save(
                        gif_path,
                        save_all=True,
                        append_images=palette_frames[1:],
                        duration=70 if detected_effect in ("fire", "wheel") else 100,
                        loop=0,
                        optimize=True
                    )
                    
                    # Cleanup raw static image
                    if os.path.exists(raw_path):
                        os.remove(raw_path)
                        
                    # Phase 3: Update database entry
                    event["image"] = f"images/event_{event_id}.gif"
                    event["is_ai_image"] = True
                    
                    with open(DB_FILE, "w", encoding="utf-8") as f:
                        json.dump(events, f, indent=4, ensure_ascii=False)
                        
                    print(f"[API] Successfully generated animated GIF and updated database.", file=sys.stderr)
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    response_payload = {
                        "success": True,
                        "image_path": f"images/event_{event_id}.gif",
                        "detected_effect": detected_effect
                    }
                    self.wfile.write(json.dumps(response_payload).encode("utf-8"))
                except Exception as e:
                    self.send_json_error(f"Error during GIF compilation: {str(e)}")
            else:
                self.send_json_error("Failed to generate base static image.")
                
        elif self.path == "/api/reset_event":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data.decode('utf-8'))
            event_id = int(params.get("id"))
            
            print(f"[API] Resetting Event {event_id} back to fallback clock GIF...", file=sys.stderr)
            
            if not os.path.exists(DB_FILE):
                self.send_json_error("Database file missing.")
                return
                
            with open(DB_FILE, "r", encoding="utf-8") as f:
                events = json.load(f)
                
            event = next((e for e in events if e["id"] == event_id), None)
            if not event:
                self.send_json_error(f"Event with ID {event_id} not found.")
                return
                
            custom_gif = os.path.join(IMAGES_DIR, f"event_{event_id}.gif")
            if os.path.exists(custom_gif):
                os.remove(custom_gif)
                
            curated_defaults = {
                10: "images/discovery_of_fire.gif",
                13: "images/bhimbetka_cave_art.gif",
                55: "images/gutenberg_press.gif"
            }
            
            if event_id in curated_defaults:
                event["image"] = curated_defaults[event_id]
                event["is_ai_image"] = True
            else:
                event["image"] = "images/history_fallback.png"
                event["is_ai_image"] = False
            
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=4, ensure_ascii=False)
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            
        else:
            self.send_response(404)
            self.end_headers()
            
    def send_json_error(self, message):
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "message": message}).encode("utf-8"))

# --- SERVER BOOT ---

if __name__ == "__main__":
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
        
    handler = TimelineAdminHandler
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"\n=======================================================", file=sys.stderr)
        print(f"🏛️  CBSE HISTORY MUSEUM - LOCAL DEVELOPMENT & LAB SERVER", file=sys.stderr)
        print(f"=======================================================", file=sys.stderr)
        print(f"  👉 Timeline Website:   http://localhost:{PORT}/index.html", file=sys.stderr)
        print(f"  👉 Teacher Lab Portal: http://localhost:{PORT}/admin.html", file=sys.stderr)
        print(f"=======================================================", file=sys.stderr)
        print(f"Press Ctrl+C to terminate.", file=sys.stderr)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server. Goodbye!", file=sys.stderr)
            sys.exit(0)
