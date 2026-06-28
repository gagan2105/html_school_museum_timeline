# 🏛️ CBSE School History Museum: AI-Powered Interactive Timeline

An interactive, high-fidelity digital museum timeline website designed to display historical events from the CBSE Social Science curriculum (Grades 6–10) with immersive visual storytelling. The project features an **AI Creator Studio**, content-based AI illustrations, unique sharing URLs, scannable QR codes, and a 3D virtual tour.

---

## 🚀 Key Features

1. **Interactive Timeline View (`index.html`)**:
   - Filter events dynamically by CBSE Grade Level (Grade 6 to 10) or search text content.
   - Beautiful responsive layouts with custom HSL-based color tokens corresponding to different historical eras.
2. **AI Creator Studio / Teacher Portal (`admin.html`)**:
   - **One-Click Generation**: Manually generate custom illustrations and animated GIFs for any historical event.
   - **Live status checking**: Automatically detects local AI server status (🟢 Online / 🔴 Offline) and shows helpful messages.
   - **AI Prompt Library**: Saves customizable prompt templates for all 187 CBSE curriculum events.
   - **Batch Mode**: Mass-generate illustrations and GIFs for multiple events with live progress status.
3. **15+ Custom Loop Animation Effects**:
   - Apply highly optimized, mathematically looped effects to images (e.g. fire burning, water flowing, flag waving, birds flying, screen-shake explosion) using a custom lightweight CPU-based Python rendering pipeline.
4. **Event Explorer Detail Page (`detail.html?id=ID`)**:
   - Deep-linking with unique URL query parameters for each event.
   - Structured sections highlighting historical **Cause & Effect** dynamics.
5. **Interactive 3D Virtual Tour (`3d.html`)**:
   - Enter a simulated virtual museum room with an automated robot tour guide navigating through historical display boards.

---

## 📁 Project Structure

* **`server.py`**: FastAPI server hosting REST APIs and serving frontend static files.
* **`backend/`**: Modular backend code:
  * `config.py`: Loads and saves global configurations.
  * `prompt_library.py`: Manages prompt templates for events.
  * `effects.py`: PIL & NumPy implementation of 15 loop animation effects.
  * `queue_manager.py`: FIFO background task queue, progress tracking, and retries.
  * `logger.py`: JSON logging system for requests, performance, and errors.
* **`index.html`** / **`timeline.js`** / **`timeline.css`**: Main timeline web application.
* **`admin.html`**: The teacher creator panel portal.
* **`detail.html`**: Detail view and QR code scan dialog.
* **`3d.html`** / **`3d.js`**: Interactive WebGL-based virtual museum tour space.

---

## 📖 Detailed Guides & Manuals

For step-by-step instructions on setting up, using, and maintaining the museum timeline:

1. 🛠️ **[Installation & LAN Setup Guide](docs/INSTALLATION_GUIDE.md)**: Installing Python, FastAPI, Fooocus, and making the server accessible over the school local network (LAN).
2. 👨‍🏫 **[Teacher Portal User Manual](docs/TEACHER_MANUAL.md)**: Working with Creator Studio, modifying prompts, applying animations, and running batch tasks.
3. ⚙️ **[Lab Administrator Guide](docs/ADMIN_GUIDE.md)**: Configuration parameters, troubleshooting, logs lookup, and database resets.
4. 🌐 **[REST API Reference](docs/API_DOCUMENTATION.md)**: Details on health endpoints, status polling, and generation routes.

---

## 🛠️ Quick Start

### 1. Initialize the Curriculum Database
```bash
python process_timeline.py
```

### 2. Launch the Museum Server
```bash
python server.py
```
Open your browser and navigate to:
* **Museum Timeline**: `http://localhost:8000/index.html`
* **Teacher Portal**: `http://localhost:8000/admin.html`