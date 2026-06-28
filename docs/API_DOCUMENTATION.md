# 🌐 CBSE History Museum Server API Documentation

The History Museum backend is built using FastAPI (Python) and runs on port `8000`.

---

## 🟢 Server Health Endpoint
Check health status, GPU hardware availability, and local AI server link.

### `GET /health`
* **Response**:
  ```json
  {
    "status": "healthy",
    "gpu": {
      "gpu_available": true,
      "gpu_device": "NVIDIA GeForce RTX 4060",
      "gpu_memory": "8.0 GB"
    },
    "fooocus_status": "online",
    "fooocus_url": "http://127.0.0.1:7865"
  }
  ```

---

## 🎨 Asset Generation Endpoints

### `POST /generate-image`
Queue a background job to generate a static PNG illustration.
* **Request Body**:
  ```json
  {
    "event_id": 10,
    "prompt": "A historical illustration representing Discovery of Fire...",
    "mode": "fooocus"
  }
  ```
  *(Modes: `"fooocus"`, `"pollinations"`, `"procedural"`)*
* **Response**:
  ```json
  {
    "job_id": "9fba243e-b816-43c3-b920-562a4d3393ea"
  }
  ```

### `POST /generate-gif`
Queue a background job to generate a static illustration and compile an animated looping GIF.
* **Request Body**:
  ```json
  {
    "event_id": 10,
    "prompt": "...",
    "mode": "fooocus",
    "effect": "fire"
  }
  ```
  *(Effects: `"auto"`, `"kenburns"`, `"fire"`, `"water"`, `"smoke"`, `"rain"`, `"snow"`, `"flag"`, etc.)*
* **Response**:
  ```json
  {
    "job_id": "bfd9921e-d419-4822-b91c-7f55f2ad34a0"
  }
  ```

### `POST /batch`
Queue multiple events for sequential batch asset generation.
* **Request Body**:
  ```json
  {
    "event_ids": [10, 13, 14],
    "job_type": "batch_gif",
    "mode": "pollinations",
    "effect": "auto"
  }
  ```
* **Response**:
  ```json
  {
    "job_id": "7ac1992e-bba1-419b-a3d1-921fa4d13ba0"
  }
  ```

---

## 📊 Status Polling

### `GET /status`
Query the progress of a specific job by ID, or fetch the last 50 recent jobs.
* **Query Parameters**:
  * `job_id` (optional): UUID of the generation job.
* **Response**:
  ```json
  {
    "job_id": "bfd9921e-d419-4822-b91c-7f55f2ad34a0",
    "event_ids": [10],
    "job_type": "gif_pipeline",
    "mode": "fooocus",
    "prompt": "...",
    "effect": "fire",
    "status": "creating_animation",
    "progress": 60.0,
    "message": "Applying animation effect 'fire'...",
    "error": null,
    "retry_count": 0,
    "results": []
  }
  ```

---

## 📜 Metadata & Config Endpoints

### `GET /api/events`
Fetch all curriculum events stored in the database.

### `POST /api/reset_event`
Revert an event back to its default fallback.
* **Request Body**: `{"id": 10}`

### `DELETE /api/delete_gif`
Delete customized image/GIF files from disk and revert the timeline event to the default.
* **Query Parameters**:
  * `event_id` (integer)

### `GET /api/settings` / `POST /api/settings`
Read or update global server parameters.

### `GET /api/prompts` / `POST /api/prompts`
Read or update prompt templates stored in the AI Prompt Library.
* **POST Request Body**:
  ```json
  {
    "event_id": 10,
    "imagePrompt": "Updated custom template...",
    "animation": "fire"
  }
  ```
