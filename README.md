# 🌿 Sanctuary 3.2 — The Local-First Socratic Core

> **Instant, Private, Clinical-Grade CBT Reasoning.**

Sanctuary is a production-hardened, zero-telemetry mental health platform designed to bring high-fidelity therapeutic support to the edge. Built for the privacy-conscious user, Sanctuary processes everything—from voice transcriptions to clinical reasoning—100% locally on your device.

---

## 🚀 Key Innovations

### 1. Zero-Telemetry Architecture
No API keys. No cloud processing. No data leaks. Sanctuary uses an optimized **Sanctuary Core (Gemma 4 based)** model for local inference via `llama-cpp-python`.

### 2. HyDE-RAG (Hypothetical Document Embeddings)
Our RAG engine doesn't just search; it *reasons*. By generating a hypothetical clinical response before querying our **ChromaDB** clinical protocol vault, Sanctuary achieves state-of-the-art retrieval relevance for complex emotional queries.

### 🧠 Clinical Grounding: Socratic CBT
Unlike generic LLMs that provide "advice," Sanctuary is strictly programmed for **Socratic Reframing**. It uses the following clinical techniques:
- **Identifying Cognitive Distortions**: Automatically tags distortions like *Catastrophizing*, *Emotional Reasoning*, and *Black-and-White Thinking*.
- **Guided Discovery**: Instead of giving answers, the Sanctuary Core asks targeted questions to help users find their own evidence-based reframes.
- **Protocol Adherence**: All reasoning is grounded in a local vault of clinical CBT protocols.

### 3. Tiered Safety Hierarchy
Sanctuary implements a multi-level triage system:
- **Level 1**: Real-time keyword crisis detection.
- **Level 2**: Behavioral biometric analysis (typing cadence & acoustic jitter).
- **Level 3**: Clinical grounding via RAG injection for severe distress.

### 4. Premium Spotify-Native UX
A high-fidelity, glassmorphic UI built with **Next.js** and **Tailwind**, featuring:
- **PWA Ready**: Install Sanctuary as a native mobile app for a zero-distraction experience.
- **Audio Visualizer**: Real-time frequency analysis for voice sessions.
- **Secure Vault**: AES-256 GCM encrypted journal storage.
- **Snappy Orchestration**: Min-P sampling for stable, clinical-grade token delivery.

---

## 🛠️ Technical Stack

- **ML Core**: Gemma 4 (Sanctuary Fine-tune) via `llama-cpp-python`
- **Vector DB**: ChromaDB
- **Audio**: Silero VAD + OpenAI Whisper (Local)
- **Frontend**: Next.js 14, Framer Motion, Lucide
- **Backend**: FastAPI, AnyIO, Cryptography (AES-256 GCM)
- **Design**: Premium Glassmorphism & Mesh Backgrounds

---

## 📖 Quick Start

### 1. Backend
```bash
cd backend
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
python server.py
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
*Access Sanctuary at: http://localhost:3000*

---

## 🛡️ Privacy Commitment
Sanctuary is built on the principle that **mental health data is sacred**. We guarantee that not a single byte of your chat history, voice, or biometrics will ever leave your machine.

---

## 🏆 Hackathon Goals
- [x] Full Local-First Inference
- [x] Clinical CBT Grounding (RAG)
- [x] Industry-Standard PII Sanitization
- [x] Premium Mobile-Native UX
- [x] Multi-Session Chat History
- [x] PWA (Progressive Web App) Integration

**Sanctuary — Because your mind deserves a private place.**
