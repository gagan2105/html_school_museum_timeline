import os
from PIL import Image

def create_motion_gif(image_path, output_gif_path, num_frames=20, duration=90, zoom_factor=0.07, pan_direction="diagonal", target_width=480):
    print(f"Animating {image_path} -> {output_gif_path} (optimized)...")
    try:
        img = Image.open(image_path)
        # Convert to RGB if it is in RGBA/P mode to ensure clean GIF saving
        if img.mode in ("RGBA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[3])
            img = background
            
        # Downscale source image first to keep file sizes very small
        width, height = img.size
        scale = target_width / width
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        width, height = new_width, new_height
        
        frames = []
        for i in range(num_frames):
            # Slow ease-in ease-out interpolation
            t = i / (num_frames - 1)
            ease_t = 3 * t * t - 2 * t * t * t
            
            current_zoom = 1.0 + (zoom_factor * ease_t)
            crop_w = int(width / current_zoom)
            crop_h = int(height / current_zoom)
            
            # Panning offset calculation
            if pan_direction == "diagonal":
                dx = int((width - crop_w) * ease_t)
                dy = int((height - crop_h) * ease_t)
            elif pan_direction == "horizontal":
                dx = int((width - crop_w) * ease_t)
                dy = int((height - crop_h) / 2)
            elif pan_direction == "zoom_in":
                dx = int((width - crop_w) / 2)
                dy = int((height - crop_h) / 2)
            else:
                dx = int((width - crop_w) / 2)
                dy = int((height - crop_h) / 2)
                
            crop_box = (dx, dy, dx + crop_w, dy + crop_h)
            cropped_img = img.crop(crop_box)
            # Resize back to target dimension (with lanczos or bilinear for speed/quality balance)
            resized_img = cropped_img.resize((width, height), Image.Resampling.BILINEAR)
            # Convert to palette mode with dithering for compact GIF representation
            frames.append(resized_img.convert("P", palette=Image.Palette.ADAPTIVE))
            
        # Ping-pong loop for smooth back-and-forth movement
        loop_frames = frames + frames[-2:0:-1]
        
        loop_frames[0].save(
            output_gif_path,
            save_all=True,
            append_images=loop_frames[1:],
            duration=duration,
            loop=0,
            optimize=True
        )
        print(f"Successfully created optimized GIF: {output_gif_path} (size: {os.path.getsize(output_gif_path) / 1024 / 1024:.2f} MB)")
        return True
    except Exception as e:
        print(f"Error creating motion GIF for {image_path}: {e}")
        return False

def main():
    images_dir = "images"
    targets = [
        ("discovery_of_fire.png", "discovery_of_fire.gif", "diagonal"),
        ("bhimbetka_cave_art.png", "bhimbetka_cave_art.gif", "horizontal"),
        ("gutenberg_press.png", "gutenberg_press.gif", "diagonal")
    ]
    
    for src_name, dest_name, pan in targets:
        src_path = os.path.join(images_dir, src_name)
        dest_path = os.path.join(images_dir, dest_name)
        if os.path.exists(src_path):
            create_motion_gif(src_path, dest_path, pan_direction=pan)
        else:
            print(f"Source file not found: {src_path}")

if __name__ == "__main__":
    main()
