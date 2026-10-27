"""Streamlit interface for Astra AI."""

from __future__ import annotations

import logging
import sqlite3

import streamlit as st

from config import MODEL_OPTIONS, load_config
from database.db import initialize_database
from services.conversation_service import (
    add_message,
    clear_conversations,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    rename_conversation,
)
from services.document_service import DocumentError, extract_pdf
from services.gemini_service import GeminiServiceError, ReplyPreferences, generate_reply
from services.memory_service import (
    add_memory,
    delete_memory,
    get_settings,
    list_memories,
    save_settings,
    update_memory,
)
from utils.validation import clean_title, clean_user_message

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("astra")

st.set_page_config(page_title="Astra AI", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
      :root { --astra-bg: #090e1d; --astra-panel: #11192b; --astra-line: #26324a;
              --astra-text: #e8edf8; --astra-muted: #a5b0c8; --astra-violet: #a78bfa; --astra-cyan: #67e8f9; }
      .stApp { background: radial-gradient(ellipse at 82% 2%, rgba(67, 56, 130, .20), transparent 34%), var(--astra-bg); color: var(--astra-text); }
      [data-testid="stSidebar"] { background: #0d1424; border-right: 1px solid var(--astra-line); }
      [data-testid="stSidebar"] > div:first-child { padding-top: 1.15rem; }
      .block-container { max-width: 1020px; padding-top: 1.8rem; padding-bottom: 2rem; }
      .astra-brand { display:flex; align-items:center; gap:.65rem; margin:0 0 1rem; }
      .astra-mark { width:2.25rem; height:2.25rem; border-radius:12px; display:grid; place-items:center;
        background:linear-gradient(140deg,#7c3aed,#0891b2); color:white; font-size:1.25rem; box-shadow:0 5px 24px #6d28d933; }
      .astra-name { font-size:1.15rem; font-weight:720; letter-spacing:.02em; color:#f4f5ff; }
      .astra-caption { color:var(--astra-muted); font-size:.79rem; margin-top:-.1rem; }
      .welcome { padding:3.2rem 1rem 1.2rem; text-align:center; }
      .welcome-orbit { color:#b6a1ff; font-size:1rem; letter-spacing:.22em; text-transform:uppercase; }
      .welcome h1 { font-size:clamp(2rem,5vw,3.2rem); letter-spacing:-.04em; margin:.6rem 0 .4rem; color:#f5f5ff; }
      .welcome p { color:#b9c4db; max-width:650px; margin:0 auto 1.35rem; font-size:1.05rem; line-height:1.65; }
      .stChatMessage { background:rgba(17,25,43,.68); border:1px solid rgba(90,106,143,.19); border-radius:18px; padding:.95rem 1.1rem; }
      [data-testid="stChatInput"] { border-color:#35415d; }
      [data-testid="stChatInput"] textarea { color:#f2f4ff; }
      div[data-testid="stMarkdownContainer"] pre { border:1px solid #303e5a; border-radius:12px; }
      div[data-testid="stMarkdownContainer"] code { color:#a5e8f2; }
      .muted { color:var(--astra-muted); }
      [data-testid="stMetric"] { background:#11192b; border:1px solid var(--astra-line); padding:.8rem; border-radius:12px; }
      @media (max-width: 700px) { .block-container { padding:1rem .8rem 1.5rem; } .welcome { padding-top:1.8rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)

config = load_config()
try:
    initialize_database(config.database_path)
except sqlite3.Error:
    LOGGER.exception("Database initialization failed")
    st.error("Astra could not open its local database. Check the database path and file permissions.")
    st.stop()

if "active_conversation_id" not in st.session_state:
    st.session_state.active_conversation_id = None
if "document_text" not in st.session_state:
    st.session_state.document_text = None
if "document_name" not in st.session_state:
    st.session_state.document_name = None
if "pdf_upload_version" not in st.session_state:
    st.session_state.pdf_upload_version = 0
if "conversation_picker_version" not in st.session_state:
    st.session_state.conversation_picker_version = 0

stored_settings = get_settings(config.database_path)
settings = {
    "mode": stored_settings.get("mode", "Companion"),
    "style": stored_settings.get("style", "Warm and clear"),
    "length": stored_settings.get("length", "Balanced"),
    "level": stored_settings.get("level", "Standard"),
    "model": stored_settings.get("model", config.model),
    "memory_enabled": stored_settings.get("memory_enabled", True),
}

conversations = list_conversations(config.database_path)
conversation_ids = [item["id"] for item in conversations]
active_id = st.session_state.active_conversation_id
if active_id not in conversation_ids:
    active_id = None
    st.session_state.active_conversation_id = None

with st.sidebar:
    st.markdown(
        '<div class="astra-brand"><div class="astra-mark">✦</div><div><div class="astra-name">Astra AI</div>'
        '<div class="astra-caption">Your curious companion</div></div></div>',
        unsafe_allow_html=True,
    )
    if st.button("＋  New chat", use_container_width=True, type="primary"):
        st.session_state.active_conversation_id = None
        st.session_state.conversation_picker_version += 1
        st.rerun()

    st.markdown("##### Recent conversations")
    if conversations:
        picker_options = [None, *conversation_ids]
        active_index = picker_options.index(active_id) if active_id in picker_options else 0
        picked_id = st.selectbox(
            "Choose a conversation",
            options=picker_options,
            index=active_index,
            format_func=lambda key: "Select a conversation…" if key is None else next((c["title"] for c in conversations if c["id"] == key), "Conversation"),
            label_visibility="collapsed",
            key=f"conversation_picker_{st.session_state.conversation_picker_version}",
        )
        if picked_id != st.session_state.active_conversation_id:
            st.session_state.active_conversation_id = picked_id
            st.rerun()
        current = next((c for c in conversations if c["id"] == active_id), None)
        with st.expander("Manage this conversation"):
            with st.form("rename_conversation_form"):
                new_title = st.text_input("Rename", value=current["title"] if current else "")
                rename_clicked = st.form_submit_button("Save title", use_container_width=True)
            if rename_clicked and current:
                try:
                    rename_conversation(config.database_path, active_id, clean_title(new_title))
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
            confirm_delete = st.checkbox("Confirm delete", key="confirm_delete_conversation")
            if st.button("Delete conversation", disabled=not confirm_delete, use_container_width=True):
                delete_conversation(config.database_path, active_id)
                st.session_state.active_conversation_id = None
                st.session_state.conversation_picker_version += 1
                st.rerun()
    else:
        st.caption("Your saved conversations will appear here.")

    if conversations:
        with st.expander("Clear conversation history"):
            confirm_clear = st.checkbox("I understand this deletes all conversations", key="confirm_clear_history")
            if st.button("Delete all conversations", disabled=not confirm_clear, use_container_width=True):
                clear_conversations(config.database_path)
                st.session_state.active_conversation_id = None
                st.session_state.conversation_picker_version += 1
                st.rerun()

    st.divider()
    st.markdown("##### Astra settings")
    with st.form("settings_form"):
        mode = st.selectbox("Mode", ["Companion", "Learning", "Coding", "Space & Science"], index=["Companion", "Learning", "Coding", "Space & Science"].index(settings["mode"]) if settings["mode"] in ["Companion", "Learning", "Coding", "Space & Science"] else 0)
        level = st.selectbox("Explanation level", ["Beginner", "Standard", "Advanced"], index=["Beginner", "Standard", "Advanced"].index(settings["level"]) if settings["level"] in ["Beginner", "Standard", "Advanced"] else 1)
        style = st.selectbox("Response style", ["Warm and clear", "Concise", "Detailed and conversational"], index=["Warm and clear", "Concise", "Detailed and conversational"].index(settings["style"]) if settings["style"] in ["Warm and clear", "Concise", "Detailed and conversational"] else 0)
        lengths = ["Concise", "Balanced", "Detailed"]
        length = st.selectbox("Response length", lengths, index=lengths.index(settings["length"]) if settings["length"] in lengths else 1)
        # Keep the deployment's configured model selectable even if it is a custom value.
        models = list(dict.fromkeys([*MODEL_OPTIONS, config.model]))
        if settings["model"] not in models:
            models.append(settings["model"])
        model = st.selectbox("Gemini model", models, index=models.index(settings["model"]))
        memory_enabled = st.checkbox("Use saved memories in replies", value=bool(settings["memory_enabled"]))
        save_settings_clicked = st.form_submit_button("Save settings", use_container_width=True)
    if save_settings_clicked:
        save_settings(config.database_path, {"mode": mode, "level": level, "style": style, "length": length, "model": model, "memory_enabled": memory_enabled})
        st.toast("Settings saved")

    with st.expander("Long-term memory"):
        st.caption("Only memories you add here are saved. They stay in this device's SQLite database. Never store credentials.")
        with st.form("add_memory_form", clear_on_submit=True):
            memory_text = st.text_input("Add a preference or ongoing goal", max_chars=500)
            add_memory_clicked = st.form_submit_button("Add memory", use_container_width=True)
        if add_memory_clicked:
            try:
                add_memory(config.database_path, memory_text)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        for memory in list_memories(config.database_path):
            st.caption(memory["content"])
            left, right = st.columns([3, 1])
            with left:
                edited = st.text_input("Edit memory", value=memory["content"], key=f"memory_edit_{memory['id']}", label_visibility="collapsed")
            with right:
                if st.button("Save", key=f"memory_save_{memory['id']}"):
                    try:
                        update_memory(config.database_path, memory["id"], edited)
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            if st.button("Delete", key=f"memory_delete_{memory['id']}"):
                delete_memory(config.database_path, memory["id"])
                st.rerun()

    st.divider()
    if config.api_key:
        st.caption("● Gemini configured")
    else:
        st.caption("○ Gemini setup needed")
        st.info("Add GEMINI_API_KEY to a local .env file or Streamlit Cloud secrets to enable replies.")
    st.caption("Astra stores chats and memories in a local SQLite file.")
    with st.expander("About Astra"):
        st.write("A curious AI companion for learning, coding, science, and creative problem-solving.")
        st.caption("Astra uses Gemini for replies. It does not have live web search or execute pasted code.")

st.markdown('<div class="astra-brand"><div class="astra-mark">✦</div><div><div class="astra-name">Astra AI</div><div class="astra-caption">A little curiosity goes a long way.</div></div></div>', unsafe_allow_html=True)

with st.expander("Learn from a PDF", expanded=False):
    upload_key = f"pdf_upload_{st.session_state.pdf_upload_version}"
    uploaded = st.file_uploader("Upload a text-based PDF (up to 10 MB)", type=["pdf"], key=upload_key)
    if uploaded is not None and uploaded.name != st.session_state.document_name:
        try:
            extracted = extract_pdf(uploaded.name, uploaded.getvalue())
            st.session_state.document_text = extracted.text
            st.session_state.document_name = extracted.name
            st.success(f"Ready to ask about {extracted.name} ({extracted.page_count} pages).")
        except DocumentError as exc:
            st.session_state.document_text = None
            st.session_state.document_name = None
            st.error(str(exc))
    if st.session_state.document_name:
        st.caption(f"Current document: {st.session_state.document_name}")
        if st.button("Remove document"):
            st.session_state.document_text = None
            st.session_state.document_name = None
            st.session_state.pdf_upload_version += 1
            st.rerun()

if settings["mode"] == "Coding":
    with st.expander("Paste code for help"):
        code_to_review = st.text_area("Code (Astra will review it as text; it will not execute it)", height=180, key="coding_input")
        if st.button("Ask Astra to explain or debug this code"):
            if not code_to_review.strip():
                st.warning("Paste some code first.")
            else:
                st.session_state.pending_prompt = (
                    "Please explain or debug this code. Preserve its indentation, explain your reasoning, and do not claim it was executed.\n\n"
                    "```text\n" + code_to_review + "\n```"
                )
                st.rerun()

active_id = st.session_state.active_conversation_id
conversation = get_conversation(config.database_path, active_id) if active_id else None
if conversation and conversation["messages"]:
    for message in conversation["messages"]:
        speaker = "assistant" if message["role"] == "assistant" else "user"
        with st.chat_message(speaker, avatar="✦" if speaker == "assistant" else None):
            st.markdown(message["content"])
    with st.expander("Quick actions"):
        if settings["mode"] == "Learning":
            actions = [
                "Explain the last topic step by step.",
                "Give a concrete example of the last topic.",
                "Ask me a short quiz about the last topic, then explain each answer.",
                "Create a practical study plan for the last topic.",
            ]
        elif settings["mode"] == "Coding":
            actions = [
                "Explain the last code example line by line.",
                "Review the last solution for edge cases and maintainability.",
                "Show an alternative approach and compare its tradeoffs.",
            ]
        elif settings["mode"] == "Space & Science":
            actions = [
                "Separate established evidence, open research, and speculation in the last answer.",
                "Explain the key idea with an intuitive analogy.",
            ]
        else:
            actions = [
                "Break the last answer into smaller steps.",
                "Give a useful example of the last idea.",
            ]
        action_columns = st.columns(min(2, len(actions)))
        for action_index, action in enumerate(actions):
            if action_columns[action_index % len(action_columns)].button(action, key=f"quick_action_{action_index}", use_container_width=True):
                st.session_state.pending_prompt = action
                st.rerun()
else:
    st.markdown(
        '<div class="welcome"><div class="welcome-orbit">✦ A companion for curious minds</div>'
        '<h1>Where should we explore?</h1>'
        '<p>I’m Astra. Bring me a tricky concept, a stubborn bug, a big idea, or a question about the universe. We’ll work through it together.</p></div>',
        unsafe_allow_html=True,
    )
    suggestions = [
        "Explain a fascinating space discovery",
        "Teach me a Python concept",
        "Help me debug a program",
        "Explore an idea in quantum physics",
        "Help me plan a personal project",
    ]
    columns = st.columns(2)
    for index, suggestion in enumerate(suggestions):
        if columns[index % 2].button(suggestion, key=f"suggestion_{index}", use_container_width=True):
            st.session_state.pending_prompt = suggestion
            st.rerun()

prompt_from_composer = st.chat_input("Ask Astra anything…")
prompt = st.session_state.pop("pending_prompt", None) or prompt_from_composer
retry = st.session_state.pop("retry_last_message", False)

if prompt or retry:
    if prompt:
        try:
            cleaned_prompt = clean_user_message(prompt)
        except ValueError as exc:
            st.warning(str(exc))
            st.stop()
        active_id = st.session_state.active_conversation_id
        if not active_id:
            active_id = create_conversation(config.database_path)
            st.session_state.active_conversation_id = active_id
        add_message(config.database_path, active_id, "user", cleaned_prompt)
    active_id = st.session_state.active_conversation_id
    conversation = get_conversation(config.database_path, active_id)
    if conversation is None or not conversation["messages"]:
        st.error("Astra could not load this conversation. Start a new chat and try again.")
        st.stop()
    current_user = next((m for m in reversed(conversation["messages"]) if m["role"] == "user"), None)
    if prompt and current_user:
        with st.chat_message("user"):
            st.markdown(current_user["content"])
    try:
        with st.chat_message("assistant", avatar="✦"):
            with st.spinner("Astra is thinking…"):
                memories = [item["content"] for item in list_memories(config.database_path)] if settings["memory_enabled"] else []
                answer = generate_reply(
                    api_key=config.api_key,
                    model=settings["model"],
                    messages=conversation["messages"],
                    preferences=ReplyPreferences(
                        mode=settings["mode"], level=settings["level"], style=settings["style"],
                        response_length=settings["length"], model=settings["model"],
                    ),
                    memories=memories,
                    document=st.session_state.document_text,
                )
            st.markdown(answer)
        add_message(config.database_path, active_id, "assistant", answer)
    except GeminiServiceError as exc:
        st.error(str(exc))
        st.button("Retry last message", on_click=lambda: st.session_state.update({"retry_last_message": True}))
    except sqlite3.Error:
        LOGGER.exception("Conversation persistence failed")
        st.error("Astra could not save the reply. Check the local database file and try again.")
