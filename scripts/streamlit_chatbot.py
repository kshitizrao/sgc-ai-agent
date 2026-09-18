import streamlit as st
import requests
import uuid
import json
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="SGC AI Agent - Debug Chatbot",
    page_icon="🤖",
    layout="wide",
)

import os

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "models" not in st.session_state:
    st.session_state.models = []
if "mcp_tools" not in st.session_state:
    st.session_state.mcp_tools = []
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None

# Custom CSS for UI
st.markdown("""
<style>
    .debug-box {
        font-family: monospace;
        font-size: 0.8em;
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# API Helpers
# ---------------------------------------------------------------------
def fetch_models():
    try:
        res = requests.get(f"{API_BASE_URL}/v1/models")
        if res.status_code == 200:
            st.session_state.models = res.json().get("models", [])
    except Exception as e:
        st.sidebar.error(f"Failed to fetch models: {e}")

def fetch_mcp_tools():
    try:
        res = requests.get(f"{API_BASE_URL}/v1/mcp/tools")
        if res.status_code == 200:
            st.session_state.mcp_tools = res.json().get("tools", [])
    except Exception as e:
        st.sidebar.error(f"Failed to fetch tools: {e}")

def create_new_session(vehicle_id=None, phone_number=None):
    try:
        payload = {"vehicle_id": vehicle_id}
        if phone_number:
            payload["phone_number"] = phone_number
        res = requests.post(f"{API_BASE_URL}/v1/sessions", json=payload)
        if res.status_code == 200:
            st.session_state.session_id = res.json().get("session_id")
            st.session_state.messages = []
            fetch_history(st.session_state.session_id)
            st.sidebar.success(f"Session Active: {st.session_state.session_id[:8]}...")
    except Exception as e:
        st.sidebar.error(f"Failed to create session: {e}")

def fetch_history(session_id):
    try:
        res = requests.get(f"{API_BASE_URL}/v1/chat/history/{session_id}")
        if res.status_code == 200:
            history = res.json().get("messages", [])
            st.session_state.messages = [{"role": m["role"], "content": m["content"]} for m in history]
    except Exception as e:
        st.sidebar.error(f"Failed to fetch history: {e}")

def fetch_analytics(session_id):
    try:
        res = requests.get(f"{API_BASE_URL}/v1/analytics/sessions/{session_id}")
        if res.status_code == 200:
            return res.json()
    except Exception:
        return None

# ---------------------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Debug Settings")
    
    if st.button("Refresh Models & Tools"):
        fetch_models()
        fetch_mcp_tools()
        
    if not st.session_state.models:
        fetch_models()
    
    if st.session_state.models:
        st.session_state.selected_model = st.selectbox("LLM Model (Visual Only)", st.session_state.models)
        
    st.divider()
    
    st.subheader("Session Management")
    phone_no = st.text_input("Phone Number (Required)", value="")
    veh_id = st.text_input("Vehicle ID (Optional)", value="")
    if st.button("Start New Session"):
        if not phone_no:
            st.error("Phone number is required")
        else:
            create_new_session(veh_id if veh_id else None, phone_no)
        
    session_input = st.text_input("Or Load Existing Session ID:")
    if st.button("Load Session"):
        if session_input:
            st.session_state.session_id = session_input
            fetch_history(session_input)
            
    st.divider()
    if st.session_state.session_id:
        st.caption(f"Active Session: `{st.session_state.session_id}`")
        if st.button("Show Analytics"):
            analytics = fetch_analytics(st.session_state.session_id)
            if analytics:
                st.json(analytics)
            else:
                st.warning("No analytics found")

# ---------------------------------------------------------------------
# Main Chat Interface
# ---------------------------------------------------------------------
st.title("🤖 SGC Agent Debug UI")
st.markdown("Use this interface to test the agent, view API responses, and inspect thought processes.")

if not st.session_state.session_id:
    st.info("👈 Please start a new session or load an existing one from the sidebar.")
    st.stop()

# Display Chat History
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    with st.chat_message(role):
        st.markdown(content)
        # If it's an assistant message and we have debug info stored, we could display it.
        # But we don't have historical debug info in the simple message array unless we store it.
        if "debug_info" in msg:
            with st.expander("🔍 Agent Thought Process & Metadata"):
                st.json(msg["debug_info"])

# Chat Input
if prompt := st.chat_input("Type your message here..."):
    # Append user msg to UI immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Send to API
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                payload = {
                    "session_id": st.session_state.session_id,
                    "message": prompt
                }
                res = requests.post(f"{API_BASE_URL}/v1/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data.get("response", "")
                    st.markdown(response_text)
                    
                    # Construct debug info
                    debug_info = {
                        "intent": data.get("intent"),
                        "model_used": data.get("model_used"),
                        "requires_human_review": data.get("requires_human_review"),
                        "source_refs": data.get("source_refs", [])
                    }
                    
                    with st.expander("🔍 Agent Thought Process & Metadata", expanded=True):
                        st.json(debug_info)
                        if data.get("source_refs"):
                            st.write("**Source References (Tools used / DB Queries):**")
                            for ref in data["source_refs"]:
                                st.write(f"- {ref}")
                                
                    # Store to session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "debug_info": debug_info
                    })
                else:
                    st.error(f"API Error ({res.status_code}): {res.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")
