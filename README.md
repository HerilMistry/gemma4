# Sanctuary

Sanctuary is a privacy-first, offline-capable Socratic CBT (Cognitive Behavioral Therapy) reasoning engine. It uses a local Gemma-based model to help users reframe cognitive distortions without any data leaving their device.

## Quick Start

### 1. Start Backend
```bash
# Navigate to backend
cd backend
# Install dependencies
pip install -r requirements.txt
# Launch server
python server.py
```
*Backend runs on: http://localhost:8000*

### 2. Start Frontend
```bash
# Navigate to frontend
cd frontend
# Install dependencies
npm install
# Launch UI
npm run dev
```
*Frontend runs on: http://localhost:3000*

## Key Features
- **Zero Telemetry**: 100% local processing; no data is sent to external servers.
- **Direct Inference**: Powered by `llama-cpp-python` for high-speed CPU inference.
- **Clinical RAG**: Grounded in therapeutic protocols via `ChromaDB`.
- **Safety First**: Integrated crisis detection and resource routing.
- **Secure Vault**: AES-256 GCM encryption for local journal storage.

## License
MIT
