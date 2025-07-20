# AI agent

This notebook demonstrates a prototype **AI Agent** that can interact with users, process tasks using language models, and provide structured outputs. It's designed as a foundation for building smart assistants or automation tools using LLMs.

## 🔍 Features

- LLM-based interaction using OpenAI-compatible API
- Command parsing and task routing
- Clean agent class architecture (`MeetingSchedulerAgent`)
- Google Calendar integration (via Google API)
- Prompt formatting and structured output generation
- Custom metadata tagging and event scheduling

## 📁 File Structure

- `Sample_AI_Agent-Copy.ipynb` – The main Jupyter notebook with all code blocks and demonstrations.
- `Keys/` – Folder for storing your Google OAuth token credentials.
- `model_path` – Custom local LLM API endpoint.

## 🛠️ Requirements

Install the following Python packages before running the notebook:

```bash
pip install openai google-auth google-api-python-client
