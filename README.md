<p align="center">
  <img
    src="https://github.com/user-attachments/assets/b0907e3c-6258-4ac6-866d-54fc96a3d51d"
    alt="VT Manager Logo"
    width="300">
</p>

<table align="center">
  <tr>
    <td align="center">
      <img
        src="https://raw.githubusercontent.com/Mijin-VT/Professional-VTuber-Manager/refs/heads/master/icons/Manual.JPG"
        alt="Chat Interface"
        width="450">
    </td>
    <td align="center">
      <img
        src="https://raw.githubusercontent.com/Mijin-VT/Professional-VTuber-Manager/refs/heads/master/icons/image.png"
        alt="User Manual"
        width="450">
    </td>
  </tr>
</table>
 
# 🤖 VT Manager
> **Professional VTuber Management & Content Creation Assistant.**

Built with **CustomTkinter**, VT Manager provides a premium, offline-first dashboard tailored to help streaming talents analyze growth strategies, manage schedules, automate tasks with AI, and integrate real-time voice, OBS, and stream monitoring.

---

## 🌟 Key Features

### 1. 🎙️ Offline Conversational AI (Astra Valeria)
*   **Persona-Driven Management:** Astra Valeria is programmed as a female VTuber manager with 10+ years of experience in the Spanish, English, and Japanese-speaking streaming industry.
*   **Natural Conversational Flow:** A dynamic system prompt override prevents Astra from starting responses with repetitive, robotic greeting formulas (like *"Soy Astra Valeria..."*) unless explicitly asked, ensuring natural dialogue.
*   **Local Llama.cpp Integration:** Automatically launches a background `llama-server.exe` instance on startup with fallbacks to `llama-cli.exe` for zero-setup, zero-cost, 100% offline inferencing. Processes are safely terminated on window exit.

### 2. 🧠 Local Semantic Memory (Mem0)
*   **Zero-API Local Database:** Integrates long-term semantic memory utilizing a local Chroma vector database (`data/mem0_db`).
*   **On-Demand Embedding Extraction:** Extracts memory vectors using `sentence-transformers/all-MiniLM-L6-v2` loaded locally via `llama-cli.exe`, keeping conversations fully offline.
*   **Contextual Memory Retrieval:** Searches and retrieves past conversations, goals, user storylines, and moderator names dynamically before calling the LLM.

### 3. 🗣️ Multilingual Voice Interaction Module
*   **Microphone Audio Capture:** Records raw microphone input via `sounddevice` and `soundfile` at 16kHz mono (optimized for transcription models).
*   **Local Speech-to-Text (STT):** Transcribes voice inputs instantly using `faster-whisper`.
*   **Voice Cloning (MOSS-TTS):** Interfaces with MOSS-TTS servers for zero-shot voice cloning using Spanish, English, and Japanese reference files.
*   **Zero-Config SAPI5 Fallback:** If MOSS-TTS is offline, the app compiles dynamic PowerShell text-to-speech scripts on the fly, offering zero-dependency voice playback in ES, EN, and JA.
*   **Dynamic Language Detection:** Scans text patterns (looking for kanji/kana, accents, and pronouns) to automatically match the voice synthesis language.

### 4. 📅 Autonomous AI Task Management
*   **Persistent Storage:** Local tasks are saved in `data/tasks.json` with options to check, uncheck, and prioritize (High, Medium, Low).
*   **Autonomous Registration:** When you tell Astra to remember an appointment or add a goal, she appends special tags (e.g. `[ADD_TASK: description | priority]`). The chat engine automatically registers these in the database and cleans them from the final visible message bubble.

### 5. 🔍 Web Search & Success Strategies Analyzer
*   **Live Web Queries:** Uses `duckduckgo_search` to query the web in real-time for growth trends, game statistics, and streaming guidelines.
*   **Offline Fallback Success Catalog:** To ensure offline usability and bypass search engine blocks, the system embeds detailed growth blueprints for the world's top VTubers (*Ironmouse, Pekora, Gawr Gura, Shylily, Kuzuha, Filian*).

### 6. 📺 OBS, Twitch, & Kick Live Monitoring
*   **Websocket Stream Controller:** Establishes websocket connections to OBS Studio, Twitch API, and simulated Kick API streams.
*   **Live Metrics Panel:** Tracks active viewer counts, follow rate, sub count, stream status, and streaming events in real time.
*   **Context Ingestion:** Real-time channel performance is auto-injected into the LLM system prompt so Astra can offer advice based on live chat density or viewer drops.

### 7. 🎨 Modern UI/UX Layout
*   **DPI Awareness:** Dynamic scaling prevents window crashes on high-res Windows monitors.
*   **Responsive Markdown Bubbles:** Chat boxes dynamically render Markdown formatting, tables, bold text, and clickable hyperlinks.
*   **Map-Driven Chat Recovery:** Loads chat histories asynchronously when the widget receives the Tkinter `<Map>` event, bypassing layout height computation bugs.
*   **Automatic Model Detection:** Scans `./models` on startup to detect physical `.gguf` files and update model selection cards automatically.

---

## 📂 Project Architecture

The folder structure is organized as follows:

```
ARCHIVOS VALIDOS/
├── main.py                  # Main application entry point
├── debug_run.py             # Debugging runner (logs stack traces to debug_log.txt)
├── vtmanager.bat            # GUI application launcher (Standard, hidden console)
├── vtmanager_debug.bat      # Terminal application launcher (Shows logs and errors)
├── requirements.txt         # Required Python packages
├── ruvector.db              # Vector database for semantic intelligence
├── VTManager.spec           # PyInstaller build specification
├── README.md                # Project documentation
├── CLAUDE.md                # Developer commands cheatsheet
├── app/                     # Python application packages
│   ├── config_manager.py    # JSON settings manager (settings.json)
│   ├── hardware.py          # VRAM & CUDA hardware detection
│   ├── download_manager.py  # Asynchronous GGUF downloading with metrics (ETA & MB/s)
│   ├── model_catalog.py     # Local GGUF models catalog & templates
│   ├── mem0_manager.py      # Local semantic memory manager (Chroma DB)
│   ├── chat_interface.py    # LLM inference server manager & message sanitizer
│   ├── voice_manager.py     # Recording, Whisper STT, and SAPI5/MOSS voice synthesis
│   ├── streaming_api.py     # OBS Websockets, Twitch, and Kick controllers
│   ├── task_manager.py      # JSON task list manager
│   ├── theme.py             # HSL-tailored dark appearance token variables
│   ├── main_window.py       # Main Tkinter container & navigation controller
│   └── widgets/             # Individual UI page tabs (chat, settings, metrics, planning...)
├── bin/                     # Local llama.cpp CLI/Server executables & CUDA 13 DLLs
├── config/                  # Configuration directory (settings.json)
├── data/                    # Dynamic databases (chats, tasks.json, events) (Created automatically)
├── icons/                   # App branding assets & packaging icons (vtmanager.ico)
├── models/                  # Downloaded GGUF models directory (Created automatically)
└── plugins/                 # Extensible plugins catalog folder (Created automatically)
```

---

## 🚀 Installation & Running

### Option A: Windows GUI Installer (Recommended)  (En proceso) 
We provide a compiled Windows installer that automates all system and python dependencies (including Python 3.12, FFmpeg, and VC++ Redistributables via Winget):

1. Download the installer from this link
*   **https://github.com/Mijin-VT/Professional-VTuber-Manager/releases/download/v1.0.0/VTManager_Setup.exe** 
2. Double-click the file **`VTManager_Setup.exe`** 
3. Select your desired installation path.
4. Launch the application from your desktop or start menu shortcut!

---

### Option B: Easy Installation & Execution (INSTALL.bat & VBScript)

En lugar de escribir comandos uno a uno, solo necesitas hacer esto:

#### 1. Instalación (Un solo clic)
Haz doble clic en el archivo **`INSTALL.bat`**. Este archivo se encargará de hacer todo automáticamente en segundo plano:
*   Verificar e instalar Python 3.12 (si no lo tienes).
*   Instalar **FFmpeg** y **VC++ Redistributable** (si faltan).
*   Activar **Git LFS**.
*   Ejecutar `pip install -r requirements.txt` (que ya incluye todas las librerías de CustomTkinter, Mem0, fastrtc, kokoro, sounddevice, etc.).
*   Verificar que todo esté correcto.

#### 2. Ejecutar la Aplicación
Para abrir la aplicación, tienes tres opciones según lo que prefieras:
*   **`vtmanager.vbs` (Recomendado para el usuario final):** Abre la aplicación al 100% de forma invisible en segundo plano (sin mostrar ninguna molesta ventana negra de consola CMD).
*   **`vtmanager_debug.bat` o `python main.py` (Para desarrollo/pruebas):** Abre la aplicación mostrando la ventana de consola CMD para que puedas ver las salidas de depuración y logs en tiempo real.

---

### Option C: Manual Installation (Developers)

#### 1. Install System Dependencies
Before installing Python packages, ensure the following system-level tools are installed on your Windows machine:
*   **Python 3.10+**: Ensure Python is in your system `PATH`.
*   **FFmpeg**: Required by `pydub` and `fastrtc` for audio processing and format conversion.
*   **Microsoft Visual C++ Redistributable**: Required for Whisper and llama.cpp native binaries.
*   **Git LFS**: Required if you plan to clone/download large model assets. Activate it using:
    ```powershell
    git lfs install
    ```

#### 2. Install Python Dependencies
Install all required libraries (including CustomTkinter, SoundDevice, faster-whisper, Mem0, fastrtc, and kokoro-onnx) using:

```powershell
pip install -r requirements.txt
```

#### 3. Running the App
Execute the main script from the project root directory:

```powershell
python main.py
```

*To run the application cleanly in the background (hidden):*
Double-click the **`vtmanager.vbs`** file.

*To run with crash logging and standard output capturing:*
```powershell
python debug_run.py
```
This will automatically output logs to `debug_log.txt` and exceptions to `debug_crash.txt`.

---

## 🤖 Model Categories

The application's model selection page groups models into four categories optimized for different hardware configurations:

| Category | VRAM Recommended | Included Models | Description |
| :--- | :--- | :--- | :--- |
| **🚀 Large Models** | **24GB+** | Command-R 35B<br>Hermes-3-Llama-3-70B | Maximum intelligence, massive context window. Ideal for long-term storyline planning and strategic advice. |
| **⚡ Medium Models** | **16GB** | Mistral-Nemo-12B<br>Hermes-3-Llama-3.1-8B | Balanced category. Nemo-12B offers exceptional Spanish fluency and fast response times. |
| **💎 Light Models 2** | **6GB - 12GB** | Saiga-Llama3-Stheno-8B<br>Meta-Llama-3.1-8B | Optimized for mid-range gaming PCs (RTX 3060/4060). Saiga-Stheno-8B is customized for internet culture and informal conversation. |
| **📦 Light Models** | **4GB - 6GB** | Hermes-3-Llama-3.2-3B<br>Qwen-2.5-1.5B-Instruct<br>Yi-Coder-1.5B-Chat | Optimized for entry-level PCs (GTX 1050Ti/1650). Excellent for quick scheduling and programming scripts. |

---

## ⚙️ GPU Layer Allocation & VRAM Optimization

The application dynamically calculates how many model layers should be offloaded to the GPU to maximize token generation speeds while avoiding system crashes. The allocation logic is implemented in `app/hardware.py` and follows these rules:

1.  **Estimate Total RAM/VRAM usage:** A model's size in GB is converted to MB. Context overhead is estimated dynamically at `2MB` per layer per active context.
2.  **Establish Safety Margins:**
    *   **VRAM <= 8GB:** Leaves a strict **1.5GB safety margin** for the OS and background streaming apps (e.g., OBS, VTuber Studio).
    *   **8GB < VRAM < 12GB:** Leaves a **1GB safety margin** to prevent out-of-memory errors on mid-range cards.
    *   **VRAM >= 12GB:** Runs aggressively, leaving only a **512MB margin** for the OS since the rest can be dedicated entirely to the LLM.
3.  **Layer Offload Calculation:**
    $$\text{Offloaded Layers} = \text{Total Layers} \times \min\left(\frac{\text{Available VRAM} - \text{Margin}}{\text{Model Size (MB)}}, 1.0\right)$$
    If the calculation returns a fraction, the remaining layers are processed by the CPU, ensuring that even under-powered cards can run large models via hybrid CPU/GPU inference.
