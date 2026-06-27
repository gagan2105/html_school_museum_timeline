# Teacher Image Generation Guide (Fooocus, Lab Server)

## 1) What is Fooocus?
Fooocus is a local AI image generation app with a simple web interface. Teachers can type prompts and generate scene images without coding.

Repo: https://github.com/lllyasviel/Fooocus

## 2) Lab Server Prerequisites
- **OS**: Windows 10/11 or Ubuntu 22.04+.
- **GPU**: NVIDIA GPU recommended (8 GB VRAM ideal, 6 GB usable with lower quality/speed).
- **RAM**: 16 GB recommended (8 GB minimum).
- **Python**: 3.10+.
- **Disk**: 25–40 GB free (models + outputs).
- **Network**: LAN access if multiple lab PCs should open the same Fooocus server.

## 3) Install and Run Fooocus
1. Open terminal on the lab server:
   ```bash
   git clone https://github.com/lllyasviel/Fooocus.git
   cd Fooocus
   ```
2. First run:
   - **Windows**: `run.bat`
   - **Linux**:
     ```bash
     python entry_with_update.py
     ```
3. Wait for model/dependency download.
4. Open the shown URL (usually `http://127.0.0.1:7865`).
5. For classroom LAN use, restart with listen mode:
   - Windows: `run.bat --listen`
   - Linux: `python entry_with_update.py --listen`

## 4) How Teachers Generate Images Manually
1. Open Fooocus in browser.
2. In prompt box, enter a scene prompt (use templates in `docs/SAMPLE_PROMPTS.md`).
3. Add a negative prompt to avoid modern artifacts.
4. Choose image size/aspect ratio, style, and number of images.
5. Click **Generate**.
6. Save selected output with clear filename (example naming below).

## 5) Suggested Settings for Historical Scenes
- **Aspect ratio**:
  - Timeline cards: `16:9` or `3:2`
  - Portrait/event detail: `4:5`
- **Style direction**: cinematic historical realism, warm color grading, natural textures.
- **Quality vs speed**:
  - Drafting: fewer steps / fast mode.
  - Final museum image: higher quality mode and 2–4 variations, then pick best.

## 6) Motion/GIF Sequence Workflow (Teacher Friendly)
Use Fooocus to generate **frame-like stills**, then assemble GIF separately.

1. Keep same base prompt and seed.
2. Generate 6–12 variations with tiny progressive edits only.
3. For fire/campfire scenes, motion expectation:
   - flame shape changes each frame,
   - orange/yellow intensity flickers,
   - smoke drifts gently upward,
   - nearby faces/objects show subtle warm light fluctuation.
4. Keep camera angle fixed for stable animation.
5. Export as ordered files: `event10_fire_f01.png ... event10_fire_f12.png`.
6. Build GIF from frames using existing repo scripts/tools.

## 7) Safety and Ethics (Classroom Use)
- Avoid prompts with violence, hate, sexual content, or stereotypes.
- Keep costumes/culture references respectful and age-appropriate.
- Teacher reviews all outputs before student display.
- Clearly mark AI-generated visuals when used in museum content.

## 8) Troubleshooting
- **Out of memory (OOM)**: lower resolution, reduce batch count, close other GPU apps.
- **Very slow generation**: use faster mode, smaller size, or run on stronger GPU.
- **Bad prompt output**: add clearer subject, era, lighting, camera angle, and negative prompt.
- **No network access from lab PCs**: run with `--listen`, then allow port `7865` in firewall.
