# ⚙️ School Lab Administrator Guide

This guide helps school computer lab administrators maintain, configure, and troubleshoot the CBSE History Museum AI Lab server.

---

## 📁 Critical File Directories

All generated and configuration data is stored inside the main project directory:
* **`config.json`**: Global server settings (API URL, directories, FPS, compression).
* **`prompt_library.json`**: The editable list of prompts for the 187 curriculum events.
* **`events_data.json`**: The main timeline database containing event detail paths.
* **`assets/generated/images/`**: Saved raw static PNG drawings.
* **`assets/generated/gifs/`**: Saved compiled animated looping GIFs.
* **`generation_logs.json`**: Structured diagnostic logs.

---

## 🛠️ Server Troubleshooting & Diagnostics

### 1. The status shows "Server Offline" 🔴 in the Teacher Portal
* Check if the command window hosting `python server.py` is open.
* Check if the Fooocus console window is open and listening.
* Verify the IP address matches. If the host IP changed (e.g. via school router DHCP renewal), update the **Fooocus Local Server API Link** in the portal's Settings tab to point to the new IP.

### 2. High GPU/CPU Load
* Image generation is computationally heavy. By default, the backend employs a **concurrency-constrained FIFO queue** (capacity limit = 1) in `queue_manager.py`. This ensures that even if multiple teachers submit jobs at the same time, the server will process them one by one, preventing thermal throttling or crash states.

### 3. Cleaning Up Disk Space
* If teachers run hundreds of generations, the `assets/generated/` folder will grow.
* You can safely run the cleanup script to remove unused assets:
  ```cmd
  python cleanup_unused_gifs.py
  ```
  *This identifies and deletes generated GIF/PNG files that are no longer linked to any events in `events_data.json`.*

### 4. Reverting the Entire Database
* If you want to reset all timeline events back to their initial state (reverting custom animations and resetting to fallbacks), run:
  ```cmd
  python process_timeline.py
  ```
  *This fetches a fresh copy of the curriculum API and rebuilds the local index.*

---

## 📜 Reviewing Execution Logs

Navigate to the **System Logs** tab in the Teacher Portal to view live reports, or open `generation_logs.json` in a text editor.
* **`request` logs**: Trace who requested which generation, the mode chosen, and timestamps.
* **`error` logs**: Display precise tracebacks (e.g. internet connection drops, out of memory errors).
* **`performance` logs**: Log rendering time. Average pipeline compilation time is:
  * Procedural Cards: <1s.
  * Pollinations Cloud: 5s - 12s.
  * Fooocus Local: 8s - 25s (depending on GPU power).
