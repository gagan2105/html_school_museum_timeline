# CBSE School History Museum Timeline

An interactive, high-fidelity digital museum timeline website designed to display historical events from the CBSE Social Science curriculum (Grades 6–10) with immersive visual storytelling. The project features content-based AI illustrations, unique sharing URLs, dynamic QR codes for mobile scanning, and an interactive 3D virtual tour.

---

## 🏛️ Key Features

1. **Interactive Timeline View (`index.html`)**:
   - Filter events dynamically by CBSE Grade Level (Grade 6 to 10) or search text content.
   - Beautiful responsive layouts with custom HSL-based color tokens corresponding to different historical eras.
2. **Content-Based AI Illustrations & Motion GIFs**:
   - Featured timeline events use a small curated set of sample motion GIFs (Discovery of Fire, Bhimbetka cave art, Gutenberg press).
   - All other timeline events use the static fallback image (`images/history_fallback.png`) to keep repository media size controlled.
   - Dynamic zoom-and-pan CSS animations (Ken Burns motion effect) are applied to timeline illustrations.
3. **Event Explorer Detail Page (`detail.html?id=ID`)**:
   - Deep-linking with unique URL query parameters for each event.
   - Center-focused single-column layout for text-only entries, shifting automatically to a premium split-grid layout for illustrated entries.
   - Structured sections highlighting historical **Cause & Effect** dynamics.
4. **QR Code Generator**:
   - Directly scan the on-screen QR code to load the current event's detail page onto your smartphone—ideal for physical school museum displays.
5. **Interactive 3D Virtual Tour (`3d.html`)**:
   - Enter a simulated virtual museum room with an automated robot tour guide navigating through historical display boards.

---

## 📁 Project Structure

- **`index.html`** / **`timeline.js`** / **`timeline.css`**: Main interactive timeline workspace.
- **`detail.html`**: Premium layout rendering detailed historical breakdowns.
- **`3d.html`** / **`3d.js`**: Interactive WebGL-based virtual museum tour space.
- **`process_timeline.py`**: Python compiler script that loads CBSE APIs, fetches images, and builds the local database.
- **`events_data.json`**: Pre-compiled database mapping all 187 subtopic timeline entries.
- **`images/`**: Directory hosting content-based AI illustrations (`.png` files) and local fallbacks.
- **`docs/TEACHER_IMAGE_GENERATION_GUIDE.md`** / **`docs/SAMPLE_PROMPTS.md`**: Teacher self-service guide and prompt packs for manual Fooocus generation on a lab server.

---

## 🛠️ Local Installation & Setup

Follow these steps to run the interactive timeline locally on your machine:

### 1. Clone the Repository
Clone this repository to your local computer:
```bash
git clone https://github.com/gagan2105/html_school_museum_timeline.git
cd html_school_museum_timeline
```

### 2. Compile the Events Database & Assets
Compile the timeline events data and verify image mappings using the Python ETL compiler script:
```bash
python process_timeline.py
```
*(No external dependencies are required. The script uses native Python libraries to download and cache assets).*

### 3. Launch the Local Development Server
Start a local HTTP server to host the website and avoid CORS-blocking:
```bash
python -m http.server 8000
```

### 4. Open in Your Browser
Open your favorite web browser and navigate to:
```url
http://localhost:8000/index.html
```

---

## 📖 Usage Guide

* **Filtering & Searching**: Use the Grade filter pills or the text search bar on the landing page to narrow down the 187 events.
* **Deep Links**: Share links like `http://localhost:8000/detail.html?id=13` to navigate directly to specific entries.
* **Mobile Sync**: Click the **📱 QR Code** button on any detail page to generate a scannable code. Scan it with your phone's camera to read the display on the go.
* **3D Guide**: Tap **3D Tour** in the navigation bar to step inside the virtual gallery. Use keyboard arrows or look controls to navigate, or sit back and follow the automated robot guide.
* **Teacher Image Creation**: See `/docs/TEACHER_IMAGE_GENERATION_GUIDE.md` and `/docs/SAMPLE_PROMPTS.md` for manual Fooocus prompt workflow in a computer lab.