# Email Scheduling AI agent for Groups  - AutoMeet AI by Clueless

This project demonstrates a prototype **AI Agent** capable of interacting with users, scheduling meetings via language models (LLMs), and generating structured metadata. It’s ideal as a base for building smart assistants, automation tools, or productivity bots.

---

## 🔍 Features

* 🧠 LLM-based command interpretation (OpenAI-compatible API)
* 📅 Google Calendar integration with OAuth
* 🏗️ Modular agent architecture (`MeetingSchedulerAgent`)
* 📥 Prompt parsing and structured metadata output
* 🧩 Custom event scheduling with tagging
* 🚀 Flask-based API for interaction

---

## 📁 File Structure

| File/Folder                 | Description                                               |
| --------------------------- | --------------------------------------------------------- |
| `Submission-notebook.ipynb` | Jupyter notebook with prototype agent and demonstrations  |
| `app.py`                    | Flask application to interact with the agent via HTTP     |
| `Keys/`                     | Folder to store your Google OAuth token (required)        |
| `doc/GoogleAuth.md`       | Guide to setting up Google Calendar API credentials       |
| `requirements.txt`          | Python dependencies list                                  |
| `model_path`                | OpenAI-compatible local endpoint (e.g., DeepSeek or Qwen) |

---

## 🛠️ Setup Instructions

### 1️⃣ Create and Activate a Virtual Environment (Python 3.10)

```bash
python3.10 -m venv venv
source venv/bin/activate  # For Linux/macOS
venv\Scripts\activate     # For Windows
```

### 2️⃣ Install Required Packages

```bash
pip install -r requirements.txt
```

---

## ⚙️ Running the Agent with VLLM

This project uses [VLLM](https://github.com/vllm-project/vllm) to serve high-performance local LLMs (e.g., DeepSeek 16B). Example command to start a server:

```bash
HIP_VISIBLE_DEVICES=0 vllm serve /home/user/Models/deepseek-ai/deepseek-moe-16b-chat \
    --trust-remote-code \
    --gpu-memory-utilization 0.9 \
    --swap-space 16 \
    --disable-log-requests \
    --dtype float16 \
    --tensor-parallel-size 1 \
    --host 0.0.0.0 \
    --port 3000 \
    --num-scheduler-steps 10 \
    --max-num-seqs 64 \
    --max-num-batched-tokens 4096 \
    --max-model-len 4096 \
    --distributed-executor-backend "mp"
```

📌 Make sure your `model_path` in code points to this local endpoint (e.g., `http://localhost:3000/v1/chat/completions`).

---

## 🔐 Google Calendar Integration

To enable Google Calendar scheduling:

1. Create a folder named `Keys/` in the project root.
2. Follow the instructions in [`doc/GoogleAuth.md`](docs/GoogleAuth.md) to obtain your OAuth token and save it inside `Keys/`.
3. Each user must have a separate token named `<username>.token`.

---

## 🚀 Running the Flask API

Use `app.py` to interact with the agent programmatically or via HTTP:

```bash
python app.py
```

This will start a Flask server that connects with the AI agent and LLM to parse meeting requests and schedule/reschedule events accordingly.

---

## 🧠 Models Used

* [`Qwen`](https://github.com/QwenLM)
* `DeepSeek 7B`
* ✅ **Finalized: `DeepSeek 16B`** — chosen for better context length support and faster inference with VLLM.

⚡ Inference latency: \~4 seconds per request with `vllm` on a GPU.

---

## ✅ Final Notes

* Ensure your VLLM server is running **before** sending any requests via `app.py`.
* Make sure to populate the `Keys/` folder and update your `model_path` correctly.
* This setup is modular, so you can swap out models or calendar providers with minimal changes.

---
