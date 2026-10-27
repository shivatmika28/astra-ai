# Astra AI

Astra is a chat-based AI companion for learning, coding, science, space exploration, and creative problem-solving. It uses Google's official `google-genai` SDK for real Gemini responses, Streamlit for the interface, and SQLite for local conversation and preference storage.

## Features

- Gemini-backed multi-turn chat with configurable model, response style, length, and explanation level.
- Companion, Learning, Coding, and Space & Science modes.
- Persistent conversations: create, load, rename, and delete.
- Explicitly managed long-term memories, with an option to keep them out of model requests.
- Text-based PDF upload for grounded questions with page labels. PDFs are limited to 10 MB and extracted text stays in the current app session.
- Markdown and code formatting, useful setup errors, and responsive dark styling.
- No telemetry, web search, code execution, or fabricated offline answers.

## Technology

Python 3.11 or newer, Streamlit, Google's `google-genai` Python SDK, python-dotenv, pypdf, SQLite, and pytest. The default model is `gemini-3.8-flash`; change it with `GEMINI_MODEL` or the in-app model setting. See Google's [Gemini models documentation](https://ai.google.dev/gemini-api/docs/models) for current model availability.

## Project structure

```text
app.py                     Streamlit interface
config.py                  Environment and secret configuration
system_prompt.py           Astra personality, modes, and instruction building
services/gemini_service.py Gemini requests and context formatting
services/conversation_service.py Conversation and message operations
services/memory_service.py User-controlled memories and settings
services/document_service.py PDF validation and extraction
database/db.py             SQLite connections and initialization
database/schema.sql        Database schema
utils/validation.py        User input checks
tests/                     Offline automated tests
```

## Prerequisites

- Python 3.11 or newer.
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) to generate replies. The interface and local history can still be explored without one.

## Install and run on Windows (PowerShell)

From the repository folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder with your key. If PowerShell blocks activation, use the environment's Python directly instead of changing system-wide policy:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Start the application:

```powershell
streamlit run app.py
```

## Install and run on macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env and set GEMINI_API_KEY
streamlit run app.py
```

## Configuration

The application reads `GEMINI_API_KEY` and `GEMINI_MODEL` from the process environment or a local `.env` file. `.env` is ignored by Git. `GEMINI_MODEL` defaults to `gemini-3.8-flash`; supported choices are also available in the sidebar. To use a different model, set `GEMINI_MODEL` or choose one in Astra settings. API keys are never shown in the interface.

The SQLite database defaults to `data/astra.sqlite3`. Set `ASTRA_DB_PATH` to choose another local path. The database contains conversation text, user-added memories, and settings. Disable “Use saved memories in replies” to keep them out of Gemini requests; disabling this setting does not delete the saved memories.

## Conversations, memory, and documents

Chats and messages are saved to SQLite as you use the app. Create a new chat, select a recent conversation, rename it, or confirm deletion from the sidebar. Each chat's context is limited to the latest 20 messages. Long-term memories are separate and are stored only when you add them in the sidebar. Never save passwords, API keys, or other credentials as memories.

PDF extraction happens locally. The app sends extracted document text to Gemini along with a question when the document is active. Page markers are included for citations. Only text-based PDFs are supported; scanned PDFs need OCR, which is not included. PDF content is held in the current session and is not stored in the conversation database. Remove the document when you are done.

Local SQLite data stays on the machine running Astra. On Streamlit Community Cloud, storage may be ephemeral and can be reset when the app restarts; use a deployment with persistent storage if chat retention matters.

## Run tests

```powershell
python -m pytest -q
```

Tests use mocked Gemini responses and local temporary databases. They do not require an API key or make paid requests.

## Deploy with Streamlit Community Cloud

1. Push this repository to GitHub.
2. Create an app in [Streamlit Community Cloud](https://share.streamlit.io/) and select the repository, branch, and `app.py`.
3. In the app's settings, add a secret in TOML format:

   ```toml
   GEMINI_API_KEY = "your-real-key"
   GEMINI_MODEL = "gemini-3.8-flash"
   ```

4. Restart the app. Never put real credentials in GitHub files or commit `.env`.

## Security and privacy

- Gemini credentials are read from environment variables, `.env`, or Streamlit secrets.
- SQL statements use parameters; PDFs are type- and size-checked and are never executed.
- Pasted code is sent as text only. Astra does not execute user code.
- Conversation text and explicit memories are stored locally without encryption. Protect the machine and database file accordingly.
- No third-party analytics or telemetry are included.
- If an API key was exposed, revoke it and create a replacement.

## Troubleshooting

- **Gemini setup needed:** set `GEMINI_API_KEY` in `.env` or Streamlit secrets, then restart the app.
- **Authentication error:** confirm the key is active and belongs to the Gemini API project.
- **Model unavailable:** choose a currently supported model in settings or change `GEMINI_MODEL`.
- **Rate limit:** wait before retrying; Astra does not automatically repeat paid requests.
- **PDF has no readable text:** use a text-based PDF. OCR is not available.
- **Database error:** check that the parent directory is writable and `ASTRA_DB_PATH` is valid.

## Known limitations and next steps

Astra has no live web search, speech, image understanding, OCR, automatic memory extraction, cancellation, or streaming responses. Gemini's answers are model-generated and should be checked for high-stakes decisions. Future additions could include optional search with citations, PDF OCR, export/import, and persistent cloud storage.
