# 👨‍🏫 CBSE History Museum: Teacher User Manual

Welcome! This manual helps you customize the school's History Museum Timeline by generating high-quality historical illustrations and animated GIFs without needing to write code or run complex commands.

---

## 🎨 Getting Started with the Creator Studio

1. Open your browser and navigate to the **Teacher Portal** (e.g. `http://localhost:8000/admin.html`).
2. The left sidebar contains a list of all **187 curriculum events** from CBSE Grades 6 to 10.
3. Use the search bar to find events by keyword (e.g., *French Revolution*, *Mahatma Gandhi*, *Invention of the Wheel*), or filter by Grade level.
4. Click on an event to load it. The workspace on the right will update.

---

## 🖼️ Step-by-Step Asset Generation

### 1. Review or Edit the Image Prompt
* Every event has a pre-written prompt. You can click on the textbox and edit it to add details (e.g. *"add a golden sunset in the background"*, *"oil painting style"*).
* If you make a mistake, click **Restore Template** to revert.

### 2. Choose Generator Mode
* **Fooocus Local (Recommended)**: Uses the local computer lab server GPU to generate high-resolution cinematic artwork.
* **Pollinations (Cloud Fallback)**: Runs generation in the cloud. Useful if the local AI server is offline or if your computer lab server lacks a graphics card (requires school internet access).
* **Procedural (Instant)**: Draws a clean, stylized text card matching the event's grade color scheme (great for quick fallbacks).

### 3. Select a Loop Animation Effect
* Select the desired motion style from the dropdown. There are **15+ custom effects** including:
  * **Auto-Detect**: Scans your text and automatically selects fire for campfires, water for rivers, etc.
  * **Ken Burns**: Classic cinematic slow zoom and pan.
  * **Campfire Burn**: Adds rising warm sparks and a gentle warp flicker.
  * **Water Flowing**: Rippling current effect.
  * **Birds Flying**: Renders a silhouette flock flying across the sky with flapping wings.
  * **Explosion**: Creates a screen shake and expanding fireball.

### 4. Click Build
* Click **Gen Image Only** to create a static drawing.
* Click **Build Animated GIF** to run the full pipeline (Gen Image + Apply Animation).
* **Track progress** using the visual step indicator (Connecting ➡️ Sending ➡️ Generating ➡️ Animating ➡️ Saving).

### 5. Review & Apply
* Inspect the result in the **Preview Panel**.
* Click **Apply to Timeline** to set it as the active asset on the main website.
* Click **Download GIF** to save the file to your computer.
* Click **Reset Fallback** if you want to remove the customization and return to the default clock animation.

---

## 🚀 Batch Operations (Mass Generator)

If you are setting up a classroom computer room or starting a new semester, you can generate assets for multiple events at once:

1. Toggle the sidebar mode to **Batch Select**.
2. Tick the checkboxes next to the events you want to customize, or use **All** to select everything in your current filter.
3. In the Batch Panel, select whether to build **Static Images** or **Animated GIFs**, select the Generation Mode, and click **Start Processing Batch Queue**.
4. The server will queue the jobs sequentially, preventing GPU overload, and show a progress bar. You can view successful and failed jobs in real-time in the Batch Console!
