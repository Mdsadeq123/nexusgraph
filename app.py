import streamlit as st
import asyncio
import os
import uuid
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from graph import graph
from tools import analyze_code_safety

load_dotenv()

# Set up premium page configuration
st.set_page_config(
    page_title="NexusGraph", 
    page_icon="🌌", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Interactive & Minimalist CSS for an Elite SaaS Platform
st.markdown("""
<style>
    /* Import Professional Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Core Layout & Theme overrides */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #080A10 !important;
        color: #E2E8F0 !important;
    }
    
    /* Sidebar Styling - Minimalist Deep Dark */
    [data-testid="stSidebar"] {
        background-color: #05060A !important;
        border-right: 1px solid rgba(255, 255, 255, 0.03) !important;
    }
    
    /* Constrain main layout container for optimal reading experience (800px width) */
    .block-container {
        max-width: 800px !important;
        padding-top: 4rem !important;
        padding-bottom: 5rem !important;
        margin: 0 auto;
    }
    
    /* Header typography */
    .main-header {
        font-size: 2.4rem;
        font-weight: 700;
        color: #F8FAFC;
        letter-spacing: -0.05rem;
        margin-bottom: 6px;
    }
    
    .sub-header {
        font-size: 0.95rem;
        color: #64748B;
        margin-bottom: 2.2rem;
        font-weight: 400;
    }

    /* Interactive Telemetry Pills Container */
    .stats-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        padding-bottom: 1.5rem;
        margin-bottom: 2rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    }
    
    /* Elegant Interactive Minimal Pill Cards */
    .stat-pill {
        background-color: #0E131F !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 20px !important;
        padding: 0.35rem 0.85rem !important;
        font-size: 0.8rem !important;
        color: #94A3B8 !important;
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: default;
        user-select: none;
    }
    
    .stat-pill:hover {
        border-color: rgba(59, 130, 246, 0.3) !important;
        color: #F1F5F9 !important;
        transform: translateY(-1px);
        background-color: #121829 !important;
    }

    /* Soft pulse animation for statuses */
    @keyframes soft-pulse {
        0% { transform: scale(0.95); opacity: 0.6; }
        50% { transform: scale(1.1); opacity: 1; }
        100% { transform: scale(0.95); opacity: 0.6; }
    }
    .status-dot-pulse {
        height: 6px;
        width: 6px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
        animation: soft-pulse 2s infinite ease-in-out;
        box-shadow: 0 0 8px #10B981;
    }
    
    .status-dot-pulse.blue {
        background-color: #3B82F6;
        animation: soft-pulse 2s infinite ease-in-out;
        box-shadow: 0 0 8px #3B82F6;
    }

    /* Ultra-clean Chat Bubbles */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 1.6rem 0 !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03) !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        margin-bottom: 0 !important;
    }
    
    /* Code Elements Styling */
    code {
        font-family: 'JetBrains Mono', monospace !important;
        background-color: rgba(255, 255, 255, 0.04) !important;
        color: #E2E8F0 !important;
        padding: 0.15rem 0.35rem !important;
        border-radius: 4px !important;
        font-size: 0.85rem !important;
    }
    
    pre code {
        background-color: transparent !important;
        color: #CBD5E1 !important;
        padding: 0 !important;
    }

    /* Minimalist Expander style for Tool execution logs */
    div[data-testid="stExpander"] {
        background: #0E131F !important;
        border: 1px solid rgba(255, 255, 255, 0.03) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        margin-top: 0.6rem !important;
        margin-bottom: 0.6rem !important;
    }
    
    .streamlit-expanderHeader {
        background-color: transparent !important;
        border-bottom: none !important;
        color: #3B82F6 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 0.5rem 0.8rem !important;
    }
    
    .streamlit-expanderHeader:hover {
        color: #60A5FA !important;
    }
    
    /* Custom Card Button Styling for Prompt Suggestions */
    div.stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
        background: #0E131F !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        color: #94A3B8 !important;
        padding: 0.95rem 1.25rem !important;
        border-radius: 10px !important;
        font-size: 0.85rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100% !important;
        line-height: 1.4 !important;
    }
    
    div.stButton > button:hover {
        background: #121829 !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
        color: #F1F5F9 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* Clean chat input container at the bottom */
    .stChatInputContainer {
        background-color: #080A10 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
        padding: 4px 6px !important;
    }
    
    .stChatInputContainer:focus-within {
        border-color: #3B82F6 !important;
    }
    
    .stChatInputContainer textarea {
        color: #F8FAFC !important;
        font-size: 0.95rem !important;
    }
    
    /* Elegant Controls Buttons */
    .stButton>button[kind="secondary"] {
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #94A3B8 !important;
        padding: 0.4rem 1.2rem !important;
    }
    
    .stButton>button[kind="secondary"]:hover {
        border-color: rgba(255, 255, 255, 0.15) !important;
        color: #F1F5F9 !important;
    }

    /* Minimalist Security Analysis card */
    .security-report {
        background-color: #0E121E !important;
        border: 1px solid rgba(248, 113, 113, 0.15) !important;
        border-radius: 8px !important;
        padding: 1.25rem !important;
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }
    
    .security-report-header {
        font-size: 0.95rem;
        font-weight: 600;
        color: #F87171;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar UI with Compact, Clean Dashboard
with st.sidebar:
    st.markdown('''
    <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 1.5rem; margin-bottom: 0.25rem;">
        <span style="font-size: 1.6rem;">🌌</span>
        <h2 style="margin: 0; font-size: 1.25rem; font-weight: 700; color: #F8FAFC;">NexusGraph</h2>
    </div>
    <p style="color: #64748B; font-size: 0.75rem; font-weight: 500; margin-top: 0; margin-bottom: 2rem; letter-spacing: 0.05rem; text-transform: uppercase;">Stateful Agent Engine</p>
    ''', unsafe_allow_html=True)
    
    # Simple compact systems status indicator with pulsing lights
    st.markdown('''
    <div style="font-size: 0.8rem; color: #64748B; margin-bottom: 2rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span class="status-dot-pulse"></span>
            <span>Reasoning Engine: Active</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span class="status-dot-pulse"></span>
            <span>AST Guardrail: Secured</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.divider()
    
    if st.button("🗑️ Reset Memory", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.last_latency = "N/A"
        st.session_state.pending_prompt = None
        st.rerun()

# Main Application Layout
st.markdown('<h1 class="main-header">NexusGraph</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced Multi-Agent Conversational Engine with AST Guardrails & Stateful Memory</p>', unsafe_allow_html=True)

# Initialize session state for memory and thread tracking
if "thread_id" not in st.session_state:
    st.session_state.thread_id = "default_session"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_latency" not in st.session_state:
    st.session_state.last_latency = "N/A"

# Configuration for the checkpointer thread
config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Clean Horizontal Interactive Telemetry Pills
st.markdown(f'''
<div class="stats-bar">
    <div class="stat-pill"><span class="status-dot-pulse"></span> Core: <strong>Llama-3.1 70B</strong></div>
    <div class="stat-pill"><span class="status-dot-pulse blue"></span> Session: <strong>{st.session_state.thread_id[:12]}...</strong></div>
    <div class="stat-pill">⚡ Last Run: <strong>{st.session_state.last_latency}</strong></div>
    <div class="stat-pill">🛡️ Shield: <strong>AST Guardrail</strong></div>
</div>
''', unsafe_allow_html=True)

def render_messages():
    """Renders the message history in the Streamlit UI."""
    for msg in st.session_state.messages:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user", avatar="🧑‍💻"):
                st.write(msg.content)
        elif isinstance(msg, AIMessage):
            with st.chat_message("assistant", avatar="🌌"):
                if msg.content:
                    st.write(msg.content)
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        with st.expander(f"🛠  Executing `{tool_call['name']}`"):
                            st.json(tool_call['args'])
        elif isinstance(msg, ToolMessage):
            with st.chat_message("tool", avatar="⚙️"):
                with st.expander(f"✅ Result from `{msg.name}`"):
                    st.write(msg.content)

render_messages()

# If chat session is empty, show interactive click suggestions grid
if len(st.session_state.messages) == 0:
    st.markdown("<p style='font-size: 0.85rem; color: #64748B; margin-top: 1rem; margin-bottom: 0.75rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05rem;'>Quick Suggestion Actions:</p>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Web Search\n\nSearch the live web for the latest Generative AI advancements.", use_container_width=True):
            st.session_state.pending_prompt = "Search the web for the latest advancements in Generative AI in 2026."
            st.rerun()
        if st.button("🐍 Python Sandbox\n\nExecute safe code to calculate prime number factors in real time.", use_container_width=True):
            st.session_state.pending_prompt = "Write and execute a python script to compute the prime factors of 1530."
            st.rerun()
    with col2:
        if st.button("📂 File Analysis\n\nInspect project dependencies by reading requirements.txt.", use_container_width=True):
            st.session_state.pending_prompt = "Read the requirements.txt file and summarize the installed dependencies."
            st.rerun()
        if st.button("🧠 Code Search\n\nPerform a local RAG search to locate tools inside the workspace.", use_container_width=True):
            st.session_state.pending_prompt = "Use workspace semantic search to find where tools are declared in the codebase."
            st.rerun()

async def process_stream(input_dict, config):
    """Processes the asynchronous stream from the LangGraph engine."""
    placeholder = st.empty()
    full_response = ""
    start_time = time.time()
    
    # We use astream_events to get granular token-level streaming
    async for event in graph.astream_events(input_dict, config, version="v2"):
        kind = event["event"]
        
        # Token-level streaming for the LLM
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                full_response += content
                with placeholder.container():
                    with st.chat_message("assistant", avatar="🌌"):
                        st.write(full_response + "▌")
                        
    if full_response:
        with placeholder.container():
            with st.chat_message("assistant", avatar="🌌"):
                st.write(full_response)
                
    st.session_state.last_latency = f"{time.time() - start_time:.2f}s"
        
    # Re-fetch state to update messages with tool calls and results
    current_state = graph.get_state(config)
    if current_state and "messages" in current_state.values:
        st.session_state.messages = current_state.values["messages"]

# Handle Human-In-The-Loop Interruption
current_state = graph.get_state(config)
if current_state and current_state.next:
    if "sensitive_tools" in current_state.next:
        st.markdown("<br>", unsafe_allow_html=True)
        
        pending_tool_calls = []
        if current_state.values and "messages" in current_state.values:
            last_msg = current_state.values["messages"][-1]
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                pending_tool_calls = last_msg.tool_calls
        
        st.markdown(f'''
        <div class="security-report">
            <div class="security-report-header">
                <span>⚠️</span> SECURITY VERIFICATION REQUIRED
            </div>
            <p style="margin: 0 0 1rem 0; color: #CBD5E1; font-size: 0.9rem; line-height: 1.4;">
                The reasoning agent has requested a high-risk sandbox execution. Static analysis has generated the security report below:
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        if pending_tool_calls:
            for tc in pending_tool_calls:
                st.warning(f"Requested Tool: `{tc['name']}`")
                code_arg = tc['args'].get('code')
                if code_arg:
                    st.code(code_arg, language="python")
                    
                    # RUN AST SECURITY ANALYSIS
                    report = analyze_code_safety(code_arg)
                    
                    # Style based on Risk Level
                    color_map = {
                        "LOW": "#10B981",
                        "MEDIUM": "#F59E0B",
                        "HIGH": "#EF4444",
                        "CRITICAL": "#EF4444"
                    }
                    risk_color = color_map.get(report["risk_level"], "#EF4444")
                    
                    st.markdown(f'''
                    <div style="background-color: #07090F; border: 1px solid rgba(255, 255, 255, 0.04); border-radius: 8px; padding: 1rem; margin-top: 1rem; margin-bottom: 1rem;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.85rem;">
                            <span style="color: #94A3B8;">Threat Risk Profile</span>
                            <span style="color: {risk_color}; font-weight: 600;">{report["risk_level"]} RISK ({report["risk_score"]}/100)</span>
                        </div>
                        <p style="margin: 0.5rem 0 0.25rem 0; font-size: 0.8rem; text-transform: uppercase; color: #64748B; font-weight: 600;">AST Inspector Flags:</p>
                        <ul style="margin: 0; padding-left: 1.2rem; font-size: 0.85rem; color: #94A3B8; line-height: 1.4;">
                            {"".join([f"<li style='margin-bottom: 0.25rem;'>{f}</li>" for f in report["findings"]])}
                        </ul>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.json(tc['args'])
        
        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            if st.button("✅ Approve", type="primary", use_container_width=True):
                with st.spinner("Executing..."):
                    asyncio.run(process_stream(None, config))
                st.rerun()
        with col2:
            if st.button("❌ Reject", use_container_width=True):
                st.warning("Action Rejected. Execution halted.")
                st.stop()

# check for clicked suggestions
active_prompt = None
if st.session_state.get("pending_prompt"):
    active_prompt = st.session_state.pop("pending_prompt")

# Only show chat input if we are not blocked by HITL
if not (current_state and current_state.next and "sensitive_tools" in current_state.next):
    if prompt := st.chat_input("Ask NexusGraph a question...") or active_prompt:
        final_prompt = prompt if prompt else active_prompt
        with st.spinner("Thinking..."):
            asyncio.run(process_stream({"messages": [HumanMessage(content=final_prompt)]}, config))
            
        st.rerun()
