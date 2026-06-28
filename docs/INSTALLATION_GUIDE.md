# 🛠️ CBSE History Museum Local Installation Guide

This guide details the complete process for setting up the CBSE History Museum and its AI generation backend on a local school computer lab server.

---

## 💻 Hardware Recommendations

### Lab Server Host
* **Operating System**: Windows 10/11 64-bit or Ubuntu Linux.
* **Processor**: Intel Core i5/i7 (10th gen or newer) or AMD Ryzen 5/7.
* **Graphics Card (Recommended)**: Dedicated NVIDIA GPU with at least 6GB VRAM (e.g. RTX 3060, RTX 4060) to host local image models.
* **Memory**: 16GB RAM.
* **Storage**: At least 30GB of free SSD storage.

### Client Computers (Teacher/Student PCs)
* Standard browser-enabled workstation connected to the school's local area network (LAN/Wi-Fi).

---

## ⚙️ Step 1: Install Python & Server Prerequisites

1. Download and install Python 3.10+ (ensure you tick the box **"Add Python to PATH"** during installation).
2. Open a terminal (Command Prompt or PowerShell) and verify the installation:
   ```cmd
   python --version
   ```
3. Install required libraries on the server:
   ```cmd
   pip install fastapi uvicorn pillow numpy pydantic torch torchvision
   ```

---

## 🏛️ Step 2: Download & Initialize the Museum Website

1. Extract the project folder on the host lab server (e.g. `C:\school_timeline\`).
2. Open terminal in the directory and run the initialization script to download core assets and compile the curriculum database:
   ```cmd
   python process_timeline.py
   ```
   *This downloads the 187 CBSE History curriculum topics from the central educational repository, generates default styles, and outputs `events_data.json`.*

---

## 🎨 Step 3: Set Up Local AI Model (Fooocus)

1. Open a new command window on the server, clone the Fooocus repository:
   ```cmd
   git clone https://github.com/lllyasviel/Fooocus.git
   cd Fooocus
   ```
2. Run the startup script to download checkpoints:
   * **Windows**: Run `run.bat`
   * **Linux**: Run `python entry_with_update.py`
3. *Note: The first launch will download the high-definition SDXL base model (approx. 6.6GB). Ensure you have a stable network connection during this step.*

---

## 🌐 Step 4: LAN Network Configuration

To make both the timeline server and the AI model accessible to all computer screens in the lab:

### 1. Get the Server's IP Address
* Open Command Prompt on the server and run `ipconfig`.
* Locate the **IPv4 Address** of the active connection (e.g., `192.168.1.100`).

### 2. Run the Fooocus AI Server in Network Mode
* Restart Fooocus using the `--listen` flag to receive external connections:
  ```cmd
  run.bat --listen
  ```

### 3. Run the Museum Server in Network Mode
* Run the FastAPI backend:
  ```cmd
  python server.py
  ```
  *The server is configured to bind to `0.0.0.0:8000`, making it visible across the entire LAN.*

---

## 👨‍🏫 Step 5: Connecting from Client Screens

1. Open any browser (Chrome, Edge, Firefox) on a client PC in the computer lab.
2. Go to the timeline:
   ```url
   http://192.168.1.100:8000/index.html
   ```
3. Go to the Teacher Portal:
   ```url
   http://192.168.1.100:8000/admin.html
   ```
4. Click the **Global Settings** tab.
5. In the **Fooocus Local Server API Link** box, enter the AI URL:
   ```url
   http://192.168.1.100:7865
   ```
6. Click **Save Configurations**. The header indicator will light up green 🟢 **Online**!
