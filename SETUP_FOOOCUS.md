# 🏛️ CBSE History Museum: Lab Server Fooocus Installation Guide

This guide describes how to install and host **Fooocus** on a school computer lab server so that teachers can manually generate custom animated historical illustrations and save them directly to the Museum Timeline.

---

## 💻 Prerequisites

For optimal generation speed, we recommend hosting Fooocus on a computer lab server with:
* **Operating System**: Windows 10/11 or Linux.
* **GPU**: NVIDIA Graphics Card with at least 4GB VRAM (6GB+ recommended).
* **RAM**: 8GB+ System RAM.
* **Storage**: 20GB of free space (for models and checkpoints).

---

## ⚙️ Step 1: Install & Set Up Fooocus

1. **Clone the official Fooocus Repository**:
   Open a terminal (Command Prompt / PowerShell) on the lab server and run:
   ```bash
   git clone https://github.com/lllyasviel/Fooocus.git
   cd Fooocus
   ```
   *(Alternatively, download the official zipped release from [Fooocus Releases](https://github.com/lllyasviel/Fooocus) and extract it).*

2. **First-Time Boot (Automatic Installation)**:
   * **Windows**: Double-click `run.bat`.
   * **Linux / Python command**: Run:
     ```bash
     python entry_with_update.py
     ```
   * **What happens now**: Fooocus will automatically create a virtual environment, install its dependencies (PyTorch, Gradio, etc.), and download the high-quality **SDXL Base Model** checkpoint. This initial download is around **6.6 GB** and may take a few minutes depending on your school internet speed.

3. **Verify Local Launch**:
   Once the setup completes, your default browser should automatically open `http://127.0.0.1:7865` displaying the Fooocus Web UI.

---

## 🌐 Step 2: Make Fooocus Accessible Over the School Network

By default, Fooocus only listens to requests coming from the host computer (`localhost`/`127.0.0.1`). To allow teachers to generate images from any client computer in the computer lab:

1. **Obtain the Server's Lab IP Address**:
   * Open Command Prompt on the server and run `ipconfig`.
   * Locate the active connection (e.g. Ethernet or Wi-Fi) and note the IPv4 Address (usually starts with `192.168.x.x` or `10.x.x.x`). Let's assume it is `192.168.1.50`.

2. **Start Fooocus in Listen Mode**:
   Stop the running server (Ctrl+C in the terminal) and restart it with the `--listen` flag:
   * **Windows cmd**: 
     ```cmd
     run.bat --listen
     ```
   * **Python direct**:
     ```bash
     python entry_with_update.py --listen
     ```
   * Fooocus will now listen on all network interfaces on port **7865**.

---

## 🎨 Step 3: Link Fooocus with the Teacher Portal

1. Start your History Museum Local Server in the timeline folder:
   ```bash
   python server.py
   ```
2. Open the Teacher Portal from any computer in the lab:
   ```
   http://192.168.1.50:8000/admin.html
   ```
   *(Replace `192.168.1.50` with your actual server IP).*

3. Click on any historical event in the left sidebar (e.g., *Discovery of fire*).
4. Select **Fooocus Local** under **2. Image Generator Mode**.
5. Set the **Local Fooocus Server URL** to the server's address:
   ```
   http://192.168.1.50:7865
   ```
6. Customize the prompt or leave the default, choose the **Animation Effect**, and click **Generate Image + GIF**.
7. The server will call the local Fooocus API, generate a high-quality static PNG plus an animated GIF motion version in one pass, and save both to update the Museum website immediately.
8. To process many events quickly, filter the list (optional) and click **Generate for All Filtered Events**.

---

## ⚡ Troubleshooting

* **Refused Connection Error**: Double check that the Fooocus terminal is open on the server and that the port number (`7865`) matches.
* **Firewall Blocks**: Ensure that Windows Defender Firewall on the server allows incoming connections on port `7865` for Private Networks.
* **No GPU Fallback**: If the server does not have a dedicated NVIDIA GPU, you can still test the Teacher Portal by selecting **Pollinations (Cloud)** mode. This connects to a free cloud generation service and requires no local Fooocus setup!
