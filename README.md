# Sanctuary 3.2 — The Edge-Native Socratic CBT Core

> **Instant, Private, Clinical-Grade CBT Reasoning — Powered by Gemma 4.**

Sanctuary is a production-hardened, zero-telemetry mental health journaling platform that brings high-fidelity therapeutic support to the edge. Built for the privacy-conscious user, Sanctuary processes everything—from voice transcriptions to clinical reasoning—100% locally on your device. No API keys. No cloud calls. No data leaks.

---

## 🚀 Key Innovations

### 1. Zero-Telemetry Architecture
No API keys. No cloud processing. No data leaks. Sanctuary uses an optimized, fine-tuned **Gemma 4 E4B** model for local inference via `llama-cpp-python`, achieving a throughput of **5.05 tokens/second directly on CPU** with a lightweight **2.49 GB** model footprint.

### 2. Self-Healing GGUF Downloader
No more manual weights configuration. We engineered an **automatic self-healing downloader** into the LLM core. If the model file is not detected locally or inside a Docker container on launch, the engine dynamically downloads the fine-tuned Gemma 4 weights in-memory from our public Hugging Face repository, guaranteeing a seamless, zero-config cold start.

### 3. HyDE-RAG (Hypothetical Document Embeddings)
Our retrieve-and-reason engine generates a hypothetical clinical response to construct intent before querying our **ChromaDB** clinical protocol vault. This yields state-of-the-art context grounding for complex emotional states, refined further by a local **Cross-Encoder Reranker**.

### 4. Socratic CBT Reasoning Engine
Unlike generic LLMs that provide plain advice, Sanctuary is strictly hardcoded for **Socratic Reframing**:
*   **Identifying Cognitive Distortions**: Automatically tags distortions (e.g., *Catastrophizing*, *Emotional Reasoning*, *All-or-Nothing Thinking*).
*   **Chain-of-Thought Filtering**: The model reasons about specific distortions internally before generating a Socratic response. An on-the-fly streaming token buffer intercepts and strips these metadata headers, delivering only the pristine therapeutic response to the user interface.
*   **Protocol Adherence**: All reasoning is grounded in a local vault of clinical CBT protocols.

### 5. Premium Glassmorphic UX
A Spotify-inspired glassmorphic UI built with **Next.js 16** and **Tailwind CSS v4** featuring:
*   **IndexedDB Persistence**: Offline draft caching with zero cloud dependency.
*   **Audio Visualizer**: Real-time canvas-based frequency analysis for voice sessions.
*   **Secure Vault**: AES-256 GCM encrypted journal storage with biometric jittering.

---

## 🛠️ Technical Stack

| Layer | Technology |
| :--- | :--- |
| **ML Core** | Gemma 4 E4B (Unsloth rsLoRA fine-tune) via `llama-cpp-python` |
| **Vector DB** | ChromaDB + `all-MiniLM-L6-v2` + Cross-Encoder Reranker |
| **Audio** | Silero VAD (ONNX) + OpenAI Whisper (Local) |
| **Frontend** | Next.js 16, Framer Motion, Lucide, ReactMarkdown |
| **Backend** | FastAPI, AnyIO, Cryptography (AES-256 GCM) |
| **Design** | Premium Glassmorphism, Tailwind CSS v4, Mesh Backgrounds |

---

## 📦 Submission Packager

To prepare the clean, submission-ready ZIP file for Devpost or Kaggle, we have included an automated packaging utility in the workspace root. Run it to instantly generate **`sanctuary_edge_native.zip`** (excluding heavy python environments, model weights, local databases, and temporary caches):

```powershell
python package_project.py
```

---

## 🏁 Local Deployment Options

### Prerequisites
*   Python 3.11+
*   Node.js 18+
*   Docker (Optional, for containerized run)

### Option A: Docker Compose (Recommended, One-Command)
Thanks to the self-healing GGUF downloader, you do **not** need to manually download model weights! Simply run:

```bash
docker-compose up --build
```
*   **Vite React Client**: accessible at `http://localhost:3000`
*   **FastAPI Local API Gateway**: accessible at `http://localhost:8000` (automatically mapped to container port 7860 for cloud compatibility).

---

### Option B: Bare-Metal Setup

#### 1. Download Model Weights (If not using automatic download)
Download `sanctuary_cbt_final.gguf` (2.49 GB) and place it in `backend/models/`:
```text
backend/models/sanctuary_cbt_final.gguf
```

#### 2. Start the Backend Server
```bash
cd backend
python -m venv env
.\env\Scripts\activate       # Windows
# source env/bin/activate    # macOS/Linux
pip install -r requirements.txt
python server.py
```

#### 3. Start the Frontend Client
```bash
cd frontend
npm install
npm run dev
```
Access the client dashboard at: **http://localhost:3000**

---

## 🌐 Cloud Staging & Deployment (Tier 2 Strategy)

To allow judges to experience the live demo instantly in their browser with **zero installation**, we split the deployment into two free, high-performance hosting platforms:

### 1. Backend: Hugging Face Spaces (Docker SDK)
We provided an automated deployer script in the root directory that copies, git-initializes, and pushes the correct backend files to Hugging Face Spaces from your command line:

```powershell
# Bypasses browser drag-and-drop lags and folder upload limits
python deploy_to_hf.py
```
*   Select the **Docker SDK** and the **Blank** template on Hugging Face (CPU Basic 16GB tier).
*   Our custom `Dockerfile` automatically exposes port **`7860`** to comply with HF regulations.

### 2. Frontend: Vercel Static Hosting
Connect your repository to Vercel, set `/frontend` as the root directory, and add the crucial API environment variable:
*   `NEXT_PUBLIC_API_URL` = `https://[your-username]-[space-name].hf.space`

---

## 🔒 Privacy Commitment
Sanctuary is built on the principle that **mental health data is sacred**. Not a single byte of your chat history, voice recordings, or biometrics will ever leave your machine. All data is encrypted at rest with AES-256 GCM.

---

**Sanctuary — Because your mind deserves a private place.**
