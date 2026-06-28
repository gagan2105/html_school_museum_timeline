import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from backend.config import AppConfig

# --- BILINEAR WARP ---
def bilinear_warp(img_np, map_x, map_y):
    H, W, C = img_np.shape
    map_x = np.clip(map_x, 0, W - 2)
    map_y = np.clip(map_y, 0, H - 2)
    
    x0 = np.floor(map_x).astype(np.int32)
    x1 = x0 + 1
    y0 = np.floor(map_y).astype(np.int32)
    y1 = y0 + 1
    
    wa = (x1 - map_x) * (y1 - map_y)
    wb = (map_x - x0) * (y1 - map_y)
    wc = (x1 - map_x) * (map_y - y0)
    wd = (map_x - x0) * (map_y - y0)
    
    wa = np.expand_dims(wa, axis=-1)
    wb = np.expand_dims(wb, axis=-1)
    wc = np.expand_dims(wc, axis=-1)
    wd = np.expand_dims(wd, axis=-1)
    
    p00 = img_np[y0, x0]
    p10 = img_np[y0, x1]
    p01 = img_np[y1, x0]
    p11 = img_np[y1, x1]
    
    out = p00 * wa + p10 * wb + p01 * wc + p11 * wd
    return out.astype(np.float32)

# --- EFFECT GENERATORS ---

# 1. Fire Burning
def effect_fire(img_np, W, H, t, num_frames):
    # Detect warm fire pixels: R > 130, G > 70, R > B + 30
    fire_y, fire_x = np.where((img_np[..., 0] > 130) & (img_np[..., 1] > 70) & (img_np[..., 0] > img_np[..., 2] + 30))
    if len(fire_x) > 100:
        cx, cy = int(np.mean(fire_x)), int(np.mean(fire_y))
        rx, ry = int(np.std(fire_x) * 1.5), int(np.std(fire_y) * 1.5)
    else:
        cx, cy = W // 2, int(H * 0.75)
        rx, ry = int(W * 0.25), int(H * 0.2)
        
    rx = np.clip(rx, 50, W // 2)
    ry = np.clip(ry, 50, H // 2)
    
    Y, X = np.mgrid[0:H, 0:W]
    dist = np.sqrt(((X - cx) / rx)**2 + ((Y - cy) / ry)**2)
    spatial_weight = np.clip(1.0 - dist, 0.0, 1.0)
    spatial_weight = (np.cos(np.pi * (1.0 - spatial_weight) / 2.0))**2
    
    is_fire = (img_np[..., 0] > 130) & (img_np[..., 1] > 70) & (img_np[..., 0] > img_np[..., 2] + 30)
    mask_pil = Image.fromarray((is_fire * 255).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(radius=10))
    color_weight = np.array(mask_pil).astype(float) / 255.0
    warp_mask = color_weight * spatial_weight
    
    phase_x = (Y / 30.0) - t * (2.0 * np.pi / num_frames)
    phase_y = (Y / 40.0) - t * (2.0 * np.pi / num_frames)
    dx = 6.0 * np.sin(phase_x) * warp_mask
    dy = -5.0 * (1.2 + np.cos(phase_y)) * warp_mask
    
    warped_np = bilinear_warp(img_np, X + dx, Y + dy)
    
    # Glow/Flicker
    flicker = 1.0 + 0.06 * np.sin(t * (2.0 * np.pi / 6.0))
    glow_mask = spatial_weight * (1.0 - color_weight)
    warped_np[..., 0] *= 1.0 + (flicker - 1.0) * 0.8 * glow_mask
    warped_np[..., 1] *= 1.0 + (flicker - 1.0) * 0.5 * glow_mask
    warped_np[..., 2] *= 1.0 + (flicker - 1.0) * 0.1 * glow_mask
    
    frame_img = Image.fromarray(np.clip(warped_np, 0.0, 255.0).astype(np.uint8))
    draw = ImageDraw.Draw(frame_img)
    
    # Sparks (Deterministic based on t)
    random.seed(t + 42)
    for _ in range(5):
        sx = random.randint(cx - int(rx * 0.6), cx + int(rx * 0.6))
        sy = random.randint(cy - int(ry * 0.4), cy + int(ry * 0.4))
        sy -= int((t % num_frames) * (ry * 0.05)) # Rise
        sx += int(5 * math.sin(t / 2.0))
        size = random.uniform(1.0, 2.5)
        draw.ellipse([sx - size, sy - size, sx + size, sy + size], fill=(255, random.randint(150, 220), 50))
        
    return frame_img

# 2. Smoke Moving
def effect_smoke(img_np, W, H, t, num_frames):
    frame_img = Image.fromarray(img_np.astype(np.uint8))
    smoke_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(smoke_overlay)
    
    # Draw drifting smoke puffs
    random.seed(101)
    num_puffs = 6
    for i in range(num_puffs):
        lifetime = num_frames
        progress = (t / num_frames)
        y_travel = H * 0.8
        
        # Stagger start positions
        start_x = W // 2 + (i - num_puffs//2) * (W // 8)
        start_y = H * 0.8 - (i * (H // num_puffs))
        
        curr_y = (start_y - progress * y_travel) % H
        curr_x = start_x + (W // 15) * math.sin(2 * math.pi * progress + i)
        
        size = (W // 8) + (progress * (W // 6))
        alpha = int(60 * (1.0 - abs(curr_y / H - 0.2) / 0.8)) # Fade near top
        alpha = max(0, min(80, alpha))
        
        # Puffy circle
        draw.ellipse(
            [curr_x - size//2, curr_y - size//2, curr_x + size//2, curr_y + size//2],
            fill=(200, 200, 200, alpha)
        )
        
    # Apply soft blur to smoke overlay
    smoke_overlay = smoke_overlay.filter(ImageFilter.GaussianBlur(radius=15))
    return Image.alpha_composite(frame_img.convert("RGBA"), smoke_overlay).convert("RGB")

# 3. Water Flowing
def effect_water(img_np, W, H, t, num_frames):
    Y, X = np.mgrid[0:H, 0:W]
    # Mask lower 40% of the image (water region fallback) or blueish pixels
    blue_mask = (img_np[..., 2] > img_np[..., 0]) & (img_np[..., 2] > 80)
    water_mask = np.zeros((H, W), dtype=float)
    water_mask[int(H * 0.6):, :] = 1.0
    water_mask = np.maximum(water_mask, blue_mask.astype(float))
    water_mask_pil = Image.fromarray((water_mask * 255).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(radius=10))
    water_mask = np.array(water_mask_pil).astype(float) / 255.0
    
    phase = 2.0 * np.pi * t / num_frames
    dx = 4.0 * np.sin(X / 15.0 + phase) * water_mask
    dy = 2.0 * np.cos(Y / 10.0 + phase) * water_mask
    
    warped = bilinear_warp(img_np, X + dx, Y + dy)
    return Image.fromarray(np.clip(warped, 0.0, 255.0).astype(np.uint8))

# 4. Rain
def effect_rain(img_np, W, H, t, num_frames):
    frame_img = Image.fromarray(img_np.astype(np.uint8))
    rain_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(rain_overlay)
    
    # 40 rain streaks
    random.seed(99)
    for i in range(40):
        length = random.randint(15, 30)
        speed = random.randint(300, 500)
        x_init = random.randint(-50, W)
        y_init = random.randint(0, H)
        
        # Calculate current position with linear wrap
        y1 = (y_init + int((t / num_frames) * speed)) % H
        x1 = x_init + int((y1 - y_init) * 0.15) # slanted path
        
        x2 = x1 + int(length * 0.15)
        y2 = y1 + length
        
        draw.line([(x1, y1), (x2, y2)], fill=(220, 230, 255, random.randint(50, 120)), width=1)
        
    return Image.alpha_composite(frame_img.convert("RGBA"), rain_overlay).convert("RGB")

# 5. Snow
def effect_snow(img_np, W, H, t, num_frames):
    frame_img = Image.fromarray(img_np.astype(np.uint8))
    snow_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(snow_overlay)
    
    random.seed(77)
    for i in range(60):
        radius = random.uniform(1.5, 3.5)
        speed = random.randint(80, 160)
        sway_amp = random.uniform(5.0, 15.0)
        sway_phase = random.uniform(0, 2 * math.pi)
        
        x_init = random.randint(0, W)
        y_init = random.randint(0, H)
        
        y = (y_init + int((t / num_frames) * speed)) % H
        x = (x_init + int(sway_amp * math.sin(2 * math.pi * (t / num_frames) + sway_phase))) % W
        
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(255, 255, 255, random.randint(100, 200)))
        
    return Image.alpha_composite(frame_img.convert("RGBA"), snow_overlay).convert("RGB")

# 6. Flag Waving
def effect_flag(img_np, W, H, t, num_frames):
    Y, X = np.mgrid[0:H, 0:W]
    phase = 2.0 * np.pi * t / num_frames
    
    # Flag waving ripple propagating diagonally
    dx = 8.0 * np.sin(X / 25.0 - Y / 40.0 + phase)
    dy = 4.0 * np.cos(X / 30.0 + Y / 20.0 + phase)
    
    warped = bilinear_warp(img_np, X + dx, Y + dy)
    return Image.fromarray(np.clip(warped, 0.0, 255.0).astype(np.uint8))

# 7. Tree Leaves Moving
def effect_tree(img_np, W, H, t, num_frames):
    Y, X = np.mgrid[0:H, 0:W]
    # Leaf detection: high green or upper-half edges
    green_mask = (img_np[..., 1] > img_np[..., 0]) & (img_np[..., 1] > img_np[..., 2])
    mask = np.zeros((H, W), dtype=float)
    mask[:int(H * 0.4), :] = 0.5 # top fallback
    mask = np.maximum(mask, green_mask.astype(float))
    
    mask_pil = Image.fromarray((mask * 255).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(radius=8))
    mask = np.array(mask_pil).astype(float) / 255.0
    
    phase = 2.0 * np.pi * t / num_frames
    dx = 3.5 * np.sin(X / 10.0 + phase * 2) * mask
    dy = 2.0 * np.cos(Y / 8.0 + phase * 2) * mask
    
    warped = bilinear_warp(img_np, X + dx, Y + dy)
    return Image.fromarray(np.clip(warped, 0.0, 255.0).astype(np.uint8))

# 8. Clouds Drifting
def effect_clouds(img_np, W, H, t, num_frames):
    frame_img = Image.fromarray(img_np.astype(np.uint8))
    clouds_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(clouds_overlay)
    
    random.seed(88)
    for i in range(4):
        cloud_w = W // 3
        cloud_h = H // 6
        x_init = i * (W // 3)
        y = H // 12 + i * 20
        
        # Drift horizontally
        drift = int((t / num_frames) * W)
        x = (x_init + drift) % (W + cloud_w) - cloud_w
        
        # Draw soft puffy cloud
        draw.ellipse([x, y, x + cloud_w, y + cloud_h], fill=(255, 255, 255, 35))
        draw.ellipse([x + cloud_w//4, y - 10, x + 3*cloud_w//4, y + cloud_h], fill=(255, 255, 255, 35))
        
    clouds_overlay = clouds_overlay.filter(ImageFilter.GaussianBlur(radius=12))
    return Image.alpha_composite(frame_img.convert("RGBA"), clouds_overlay).convert("RGB")

# 9. Candle Flickering
def effect_candle(img_np, W, H, t, num_frames):
    # Detect the candle flame (brightest spot)
    bright_y, bright_x = np.where((img_np[..., 0] > 200) & (img_np[..., 1] > 170))
    if len(bright_x) > 5:
        cx, cy = int(np.mean(bright_x)), int(np.mean(bright_y))
    else:
        cx, cy = W // 2, H // 2
        
    Y, X = np.mgrid[0:H, 0:W]
    dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
    
    # Scale flame size
    scale_y = 1.0 + 0.12 * math.sin(4 * math.pi * t / num_frames)
    scale_x = 1.0 - 0.06 * math.sin(4 * math.pi * t / num_frames)
    
    # Warp mask around flame
    warp_mask = np.clip(1.0 - (dist / 40.0), 0.0, 1.0)
    dx = (X - cx) * (scale_x - 1.0) * warp_mask
    dy = (Y - cy) * (scale_y - 1.0) * warp_mask
    
    warped = bilinear_warp(img_np, X + dx, Y + dy)
    
    # Flicker light glow
    flicker_glow = 1.0 + 0.15 * math.sin(2 * math.pi * t / num_frames)
    glow_radius = 90.0
    glow_mask = np.clip(1.0 - (dist / glow_radius), 0.0, 1.0)
    
    warped[..., 0] *= 1.0 + (flicker_glow - 1.0) * 0.5 * glow_mask
    warped[..., 1] *= 1.0 + (flicker_glow - 1.0) * 0.3 * glow_mask
    warped[..., 2] *= 1.0 + (flicker_glow - 1.0) * 0.05 * glow_mask
    
    return Image.fromarray(np.clip(warped, 0.0, 255.0).astype(np.uint8))

# 10. Dust Particles
def effect_dust(img_np, W, H, t, num_frames):
    frame_img = Image.fromarray(img_np.astype(np.uint8))
    dust_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dust_overlay)
    
    random.seed(1234)
    for i in range(25):
        size = random.uniform(1.0, 3.0)
        x_init = random.randint(0, W)
        y_init = random.randint(0, H)
        
        # Floating movement (looping)
        dx = 10 * math.sin(2 * math.pi * (t / num_frames) + i)
        dy = 15 * math.cos(2 * math.pi * (t / num_frames) + i)
        
        x = (x_init + dx) % W
        y = (y_init + dy) % H
        
        draw.ellipse([x - size, y - size, x + size, y + size], fill=(255, 240, 200, random.randint(40, 110)))
        
    return Image.alpha_composite(frame_img.convert("RGBA"), dust_overlay).convert("RGB")

# 11. Crowd Movement
def effect_crowd(img_np, W, H, t, num_frames):
    Y, X = np.mgrid[0:H, 0:W]
    # Bobbing bottom half (crowd region)
    crowd_mask = np.zeros((H, W), dtype=float)
    crowd_mask[int(H * 0.55):, :] = 1.0
    crowd_mask_pil = Image.fromarray((crowd_mask * 255).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(radius=20))
    crowd_mask = np.array(crowd_mask_pil).astype(float) / 255.0
    
    phase = 2.0 * np.pi * t / num_frames
    dy = 2.5 * math.sin(phase) * crowd_mask
    dx = 1.0 * math.cos(phase + X / 40.0) * crowd_mask
    
    warped = bilinear_warp(img_np, X + dx, Y + dy)
    return Image.fromarray(np.clip(warped, 0.0, 255.0).astype(np.uint8))

# 12. Ocean Waves
def effect_ocean(img_np, W, H, t, num_frames):
    Y, X = np.mgrid[0:H, 0:W]
    # Water mask
    water_mask = np.zeros((H, W), dtype=float)
    water_mask[int(H * 0.5):, :] = 1.0
    water_mask_pil = Image.fromarray((water_mask * 255).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(radius=15))
    water_mask = np.array(water_mask_pil).astype(float) / 255.0
    
    phase = 2.0 * np.pi * t / num_frames
    dy = 5.0 * np.sin(X / 25.0 - phase) * water_mask
    dx = 3.0 * np.cos(Y / 15.0 - phase) * water_mask
    
    warped = bilinear_warp(img_np, X + dx, Y + dy)
    return Image.fromarray(np.clip(warped, 0.0, 255.0).astype(np.uint8))

# 13. Birds Flying
def effect_birds(img_np, W, H, t, num_frames):
    frame_img = Image.fromarray(img_np.astype(np.uint8))
    birds_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(birds_overlay)
    
    progress = t / num_frames
    # Fly from right-off-screen to left-off-screen
    x_base = W + 60 - progress * (W + 120)
    
    # Render 3 flocking birds
    flock = [
        (0, H // 6, 0),
        (35, H // 6 - 20, 0.5),
        (-25, H // 6 + 15, -0.3)
    ]
    
    # Flap wing cycle
    is_wings_up = math.sin(8 * math.pi * progress) > 0
    
    for dx, dy, phase_offset in flock:
        x = x_base + dx
        y = dy + 10 * math.sin(2 * math.pi * progress + phase_offset)
        
        # Only draw if on screen
        if -20 < x < W + 20:
            if is_wings_up:
                # Wings up V-shape
                draw.line([(x - 8, y + 4), (x, y), (x + 8, y + 4)], fill=(20, 20, 20, 200), width=2)
            else:
                # Wings down inverted-V
                draw.line([(x - 8, y - 2), (x, y), (x + 8, y - 2)], fill=(20, 20, 20, 200), width=2)
                
    return Image.alpha_composite(frame_img.convert("RGBA"), birds_overlay).convert("RGB")

# 14. Wind
def effect_wind(img_np, W, H, t, num_frames):
    # General sway warp
    Y, X = np.mgrid[0:H, 0:W]
    phase = 2.0 * np.pi * t / num_frames
    dx = 4.0 * math.sin(phase) * (Y / H) # sway increases towards top
    warped = bilinear_warp(img_np, X + dx, Y)
    
    frame_img = Image.fromarray(np.clip(warped, 0.0, 255.0).astype(np.uint8))
    wind_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(wind_overlay)
    
    # Draw fast blowing wind streaks
    random.seed(55)
    for i in range(8):
        y = random.randint(50, H - 50)
        length = random.randint(80, 160)
        speed = random.randint(600, 900)
        x_init = random.randint(-150, W)
        
        x1 = (x_init + int((t / num_frames) * speed)) % (W + length) - length
        x2 = x1 + length
        
        draw.line([(x1, y), (x2, y)], fill=(255, 255, 255, random.randint(30, 70)), width=1)
        
    return Image.alpha_composite(frame_img.convert("RGBA"), wind_overlay).convert("RGB")

# 15. Explosion
def effect_explosion(img_np, W, H, t, num_frames):
    # Explosion center (center-middle of screen)
    cx, cy = W // 2, H // 2
    
    # Camera shake: random offsets decaying after halfway
    shake_amp = 0
    if t < num_frames // 2:
        # High shake early on
        progress = t / (num_frames // 2)
        shake_amp = int(12 * (1.0 - progress))
        
    random.seed(t)
    dx = random.randint(-shake_amp, shake_amp) if shake_amp > 0 else 0
    dy = random.randint(-shake_amp, shake_amp) if shake_amp > 0 else 0
    
    # Apply shake
    Y, X = np.mgrid[0:H, 0:W]
    warped = bilinear_warp(img_np, X + dx, Y + dy)
    frame_img = Image.fromarray(np.clip(warped, 0.0, 255.0).astype(np.uint8))
    
    # Expand blast radius
    blast_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(blast_overlay)
    
    # Active explosion during first 60% of frames
    explode_limit = int(num_frames * 0.7)
    if t < explode_limit:
        prog = t / explode_limit
        r = prog * (W // 3)
        
        # Core fire glow
        alpha = int(220 * (1.0 - prog))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, int(200 * (1.0 - prog)), 50, alpha))
        
        # Hot white center
        r_core = r * 0.4
        draw.ellipse([cx - r_core, cy - r_core, cx + r_core, cy + r_core], fill=(255, 255, 200, alpha))
        
        # Outer blast particles
        for _ in range(8):
            angle = random.uniform(0, 2 * math.pi)
            dist = r * random.uniform(0.7, 1.2)
            px = cx + dist * math.cos(angle)
            py = cy + dist * math.sin(angle)
            psize = random.randint(4, 12)
            draw.ellipse([px - psize, py - psize, px + psize, py + psize], fill=(180, 80, 50, int(150 * (1.0 - prog))))
            
    return Image.alpha_composite(frame_img.convert("RGBA"), blast_overlay).convert("RGB")

# 16. Ken Burns (Default zoom/pan)
def effect_kenburns(img_np, W, H, t, num_frames):
    img = Image.open(Image.fromarray(img_np.astype(np.uint8))) # wait, no, img_np is float, let's load it correctly
    # Let's write standard Ken Burns loop
    # We will compute zoom ease-in ease-out
    # Since we need to return frame by frame:
    # t goes from 0 to num_frames - 1. We want a smooth ping-pong loop.
    # To do ping-pong: we can make t map from 0 -> N/2 -> 0.
    half = num_frames / 2
    if t < half:
        ease = t / half
    else:
        ease = (num_frames - t) / half
        
    ease_t = 3 * ease * ease - 2 * ease * ease * ease # smooth step
    
    zoom_factor = 0.08
    current_zoom = 1.0 + (zoom_factor * ease_t)
    crop_w = int(W / current_zoom)
    crop_h = int(H / current_zoom)
    
    # Diagonal pan
    dx = int((W - crop_w) * ease_t)
    dy = int((H - crop_h) * ease_t)
    
    base_img = Image.fromarray(img_np.astype(np.uint8))
    cropped = base_img.crop((dx, dy, dx + crop_w, dy + crop_h))
    return cropped.resize((W, H), Image.Resampling.BILINEAR)

# --- AUTO DETECT ---
def auto_detect_effect(prompt: str, title: str, img_np) -> str:
    prompt_l = prompt.lower()
    title_l = title.lower()
    
    # 1. Keywords check
    if any(w in prompt_l or w in title_l for w in ["fire", "burning", "flame", "campfire"]):
        return "fire"
    if any(w in prompt_l or w in title_l for w in ["wheel", "spin", "rotate", "chariot", "potter", "chakra"]):
        return "wheel"
    if any(w in prompt_l or w in title_l for w in ["rain", "monsoon"]):
        return "rain"
    if any(w in prompt_l or w in title_l for w in ["snow", "winter", "glacier"]):
        return "snow"
    if any(w in prompt_l or w in title_l for w in ["flag", "banner", "wave"]):
        return "flag"
    if any(w in prompt_l or w in title_l for w in ["tree", "forest", "leaves", "jungle"]):
        return "tree"
    if any(w in prompt_l or w in title_l for w in ["cloud", "sky", "storm"]):
        return "clouds"
    if any(w in prompt_l or w in title_l for w in ["candle", "lantern", "lamp", "flicker"]):
        return "candle"
    if any(w in prompt_l or w in title_l for w in ["smoke", "steam"]):
        return "smoke"
    if any(w in prompt_l or w in title_l for w in ["crowd", "people", "assembly", "march", "protest"]):
        return "crowd"
    if any(w in prompt_l or w in title_l for w in ["bird", "fly", "flock"]):
        return "birds"
    if any(w in prompt_l or w in title_l for w in ["wind", "breeze", "gale"]):
        return "wind"
    if any(w in prompt_l or w in title_l for w in ["explosion", "gunpowder", "bomb", "blast", "erupt"]):
        return "explosion"
    if any(w in prompt_l or w in title_l for w in ["water", "river", "canal", "aqueduct", "ocean", "sea", "bath", "waves"]):
        return "water"
        
    # 2. Color heuristics
    # Fire/Candle: check red/orange dominance
    red_glow = np.sum((img_np[..., 0] > 150) & (img_np[..., 1] > 90) & (img_np[..., 0] > img_np[..., 2] + 40))
    if red_glow > (img_np.shape[0] * img_np.shape[1] * 0.05):
        return "fire"
        
    # Water: check blue dominance
    blue_glow = np.sum((img_np[..., 2] > img_np[..., 0]) & (img_np[..., 2] > 110))
    if blue_glow > (img_np.shape[0] * img_np.shape[1] * 0.15):
        return "water"
        
    # Green/Tree leaves
    green_glow = np.sum((img_np[..., 1] > img_np[..., 0]) & (img_np[..., 1] > img_np[..., 2]))
    if green_glow > (img_np.shape[0] * img_np.shape[1] * 0.18):
        return "tree"
        
    return "kenburns"

# --- MAIN COMPILER ENTRY POINT ---
def animate_image(image_path: str, effect: str, output_path: str, config: AppConfig, prompt: str = "", title: str = "") -> str:
    """
    Load static image and apply effect to compile a high-quality looping GIF.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Source image not found: {image_path}")
        
    img = Image.open(image_path).convert("RGB")
    W, H = img.size
    
    # Scale down to image_size for speed & size optimization
    target_w = config.image_size
    scale = target_w / W
    target_h = int(H * scale)
    
    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    img_np = np.array(img).astype(np.float32)
    
    num_frames = config.fps * 2  # default 2-second loop
    
    if effect == "auto":
        effect = auto_detect_effect(prompt, title, img_np)
        
    frames = []
    
    # Custom effect mapping
    effect_fns = {
        "fire": effect_fire,
        "smoke": effect_smoke,
        "water": effect_water,
        "rain": effect_rain,
        "snow": effect_snow,
        "flag": effect_flag,
        "tree": effect_tree,
        "clouds": effect_clouds,
        "candle": effect_candle,
        "dust": effect_dust,
        "crowd": effect_crowd,
        "ocean": effect_ocean,
        "birds": effect_birds,
        "wind": effect_wind,
        "explosion": effect_explosion,
        "kenburns": effect_kenburns,
        "wheel": lambda np_img, w, h, t, nf: Image.fromarray(
            bilinear_warp(np_img, 
                          w//2 + (np.sqrt((np.mgrid[0:h, 0:w][1] - w//2)**2 + (np.mgrid[0:h, 0:w][0] - h//2)**2)) * np.cos(np.arctan2(np.mgrid[0:h, 0:w][0] - h//2, np.mgrid[0:h, 0:w][1] - w//2) + (t * (2.0 * np.pi / nf)) * np.clip((w*0.35 - np.sqrt((np.mgrid[0:h, 0:w][1] - w//2)**2 + (np.mgrid[0:h, 0:w][0] - h//2)**2)) / (w*0.035), 0, 1)),
                          h//2 + (np.sqrt((np.mgrid[0:h, 0:w][1] - w//2)**2 + (np.mgrid[0:h, 0:w][0] - h//2)**2)) * np.sin(np.arctan2(np.mgrid[0:h, 0:w][0] - h//2, np.mgrid[0:h, 0:w][1] - w//2) + (t * (2.0 * np.pi / nf)) * np.clip((w*0.35 - np.sqrt((np.mgrid[0:h, 0:w][1] - w//2)**2 + (np.mgrid[0:h, 0:w][0] - h//2)**2)) / (w*0.035), 0, 1))
            ).astype(np.uint8)
        )
    }
    
    effect_fn = effect_fns.get(effect, effect_kenburns)
    
    for t in range(num_frames):
        try:
            frame = effect_fn(img_np, target_w, target_h, t, num_frames)
            # Convert to palette mode with adaptive colors for lightweight GIFs
            frames.append(frame.convert("P", palette=Image.Palette.ADAPTIVE))
        except Exception as e:
            # Fallback frame on error
            frames.append(img.convert("P", palette=Image.Palette.ADAPTIVE))
            
    # Save as looping GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=config.animation_duration,
        loop=0,
        optimize=True
    )
    
    return effect
