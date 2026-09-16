# 🧠 Cortex Agent 3.1 — Autonomous Multi-Model Intelligence Studio

> **Cortex Agent 3.1** is a production-grade, enterprise autonomous intelligence platform engineered for agentic coding, deep research, live sandboxed Python execution, and deliverable synthesis. 
> Built with FastAPI, LangChain, NVIDIA NIM Frontier Models, and a Claude Code / Linear-inspired obsidian UI.

---

## ⚡ Key Architectural Capabilities

- **Frontier Multi-Model Intelligence**: Seamlessly switch across 7 frontier models:
  - **Cortex 5 Super** (`meta/llama-3.1-70b-instruct` / `nvidia/nemotron-3-super-120b`) — 120B MoE Flagship Autonomous Agent.
  - **Cortex 5 Ultra** (`deepseek-ai/deepseek-r1`) — 550B Frontier Reasoning & Architecture PRDs.
  - **Cortex 4 Deep** (`deepseek-ai/deepseek-r1`) — Chain-of-Thought Deduction & Proofs.
  - **Cortex 4 Omni** (`meta/llama-3.2-11b-vision-instruct`) — Multimodal UI & Screenshot Analysis.
  - **Cortex 3.5 Fast** (`meta/llama-3.1-8b-instruct`) — 6ms TTFT Sub-second Autocomplete.
- **Isolated Python 3.12 Sandbox Execution**: Safe sub-process execution of Python code with automatic high-resolution Matplotlib plot harvesting (`.png`, 300 DPI) and telemetry output.
- **Autonomous Tool Orchestration Loop**:
  - `web_search`: Real-time internet research via DuckDuckGo.
  - `fetch_webpage`: Deep full-page scraping and article extraction.
  - `execute_python`: Sandboxed mathematical, data science, and plotting engine.
  - `wikipedia_lookup` & `weather_lookup`: Live encyclopedic and atmospheric telemetry.
- **Claude-Style Artifacts Library**: Centralized sidebar repository harvesting all generated Markdown specifications, architectures, and scripts with split-panel preview and 1-click downloads.
- **Enterprise Security & Data Isolation**:
  - PBKDF2-HMAC-SHA256 password hashing with unique per-user cryptographic salts.
  - Signed HMAC-SHA256 session tokens.
  - Isolated SQLite WAL (Write-Ahead Logging) storage per user workspace.
  - Daily token rate-limiting (100,000 tokens/day) with real-time SSE usage telemetry.
- **Mathematical KaTeX Normalization**: Automatic LaTeX formula normalization for instant Notion, Obsidian, and Typora rendering.
- **Dual-Column Silicon Valley Auth Suite & Terminal Simulator**: Real-world interactive Claude Code terminal simulator directly on the landing page with 1-click frictionless guest test drive.

---

## 🛠️ Quickstart Installation

### 1. Clone & Setup Environment

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/cortex-agent.git
cd cortex-agent

# 2. Create Python virtual environment
python -m venv .venv

# 3. Activate environment
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Secrets

Copy `.env.example` to `.env` and configure your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# NVIDIA NIM API Key (Free at https://build.nvidia.com)
NVIDIA_API_KEY=nvapi-your-key-here

# Default Model Selection
MODEL_NAME=nvidia/nemotron-3-super-120b-a12b
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
MAX_OUTPUT_TOKENS=32768

# Secret key for JWT session tokens
SECRET_KEY=your-custom-secure-secret-key
```

> **CRITICAL SECURITY NOTE**: Never commit `.env` to Git. The `.gitignore` file is strictly configured to protect your credentials.

### 3. Launch the Application

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open your browser at **`http://127.0.0.1:8000`**.

---

## 📂 Project Structure

```text
cortex-agent/
├── main.py                  # FastAPI server, tool loop, SSE streaming & auth routes
├── database.py              # SQLite WAL storage, user auth, usage quotas & artifacts
├── sandbox.py               # Isolated Python 3.12 sandbox & plot harvesting
├── requirements.txt         # Production dependencies
├── .env.example             # Clean environment variables template
├── .gitignore               # Airtight secrets & database exclusion rules
├── LICENSE                  # Proprietary copyright license
└── static/                  # Silicon Valley frontend client
    ├── index.html           # Landing page, terminal simulator, model fleet & auth suite
    ├── style.css            # Obsidian design system, glassmorphism & typography
    └── app.js               # Reactive frontend engine, simulator runner & API client
```

---

## 📄 License & Intellectual Property

Copyright © 2026 Rohan. All Rights Reserved.
This project is proprietary and confidential. Unauthorized copying, distribution, modification, reverse engineering, or public deployment of this software without explicit permission is strictly prohibited. See `LICENSE` for details.
