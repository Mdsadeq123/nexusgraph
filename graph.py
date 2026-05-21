import asyncio
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage

import os
from dotenv import load_dotenv
load_dotenv()

from state import AgentState
from tools import safe_tools, sensitive_tools

# Initialize the LLM to use an NVIDIA model via OpenRouter
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "your_api_key"),
    model="meta-llama/llama-3.1-70b-instruct",
    temperature=0,
    streaming=True,
    default_headers={
        "HTTP-Referer": "http://localhost:8501",
        "X-Title": "NexusGraph"
    }
)

# Bind all tools to the LLM
all_tools = safe_tools + sensitive_tools
llm_with_tools = llm.bind_tools(all_tools)

# Define Tool Nodes
safe_tool_node = ToolNode(safe_tools)
sensitive_tool_node = ToolNode(sensitive_tools)

async def reasoning_agent(state: AgentState):
    """
    The reasoning agent analyzes the request, maintains conversation history,
    decides which tools to call, and intercepts infinite execution loops.
    """
    messages = state.get("messages", [])
    
    # 1. API Loop Cost Protection: Analyze tool failures in the message thread
    consecutive_errors = 0
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            # If the tool returned a failure or execution error
            if "failed" in msg.content.lower() or "error" in msg.content.lower() or "timeout" in msg.content.lower():
                consecutive_errors += 1
            else:
                break # Reset count on any successful tool result
        elif isinstance(msg, HumanMessage):
            break # Reset count if user supplied a new manual query
            
    # Forceful termination after 3 consecutive failures to safeguard API tokens
    if consecutive_errors >= 3:
        loop_preventer_msg = AIMessage(
            content=(
                "⚠️ **Loop Interceptor Armed**: Subprocess execution halted.\n\n"
                "To protect your OpenRouter token limits and prevent billing depletion, "
                "NexusGraph has safely terminated the execution thread after detecting "
                "**3 consecutive subprocess errors**. Please review your script syntax "
                "or files before retrying."
            )
        )
        return {
            "messages": [loop_preventer_msg],
            "sender": "reasoning_agent",
            "consecutive_errors": consecutive_errors
        }
        
    system_message = SystemMessage(
        content=(
            "You are Nexus, an advanced autonomous AI assistant. You have access to a suite of powerful tools:\n"
            "1. web_search: Search the live internet for current events and facts.\n"
            "2. read_file & write_file: Interact with the user's local file system.\n"
            "3. workspace_semantic_search: Perform dynamic semantic searches over all files in the current workspace directory to locate scripts, configurations, or relevant code blocks.\n"
            "4. execute_python_code: Write and run real Python code for complex reasoning, math, or data processing.\n\n"
            "Always explain your thought process before using a tool. If a task is complex, break it down step-by-step. "
            "Your code execution tool is highly sensitive and will prompt the user for approval, so use it responsibly."
        )
    )
    
    # Invoke LLM with state history
    response = await llm_with_tools.ainvoke([system_message] + messages)
    
    return {
        "messages": [response], 
        "sender": "reasoning_agent",
        "consecutive_errors": consecutive_errors
    }

def route_tools(state: AgentState) -> Literal["safe_tools", "sensitive_tools", "__end__"]:
    """
    Routes the workflow to safe tools, sensitive tools, or terminates the cycle.
    """
    messages = state.get("messages", [])
    if not messages:
        return "__end__"
        
    last_message = messages[-1]
    
    # If our reasoning agent aborted the loop with an intercept warning, terminate the graph immediately
    if isinstance(last_message, AIMessage) and "Loop Interceptor" in last_message.content:
        return "__end__"
        
    # Check if the LLM decided to call any tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # Check if any of the requested tools are sensitive
        sensitive_tool_names = [t.name for t in sensitive_tools]
        for tool_call in last_message.tool_calls:
            if tool_call["name"] in sensitive_tool_names:
                return "sensitive_tools"
        return "safe_tools"
    
    return "__end__"

# Build the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("reasoning_agent", reasoning_agent)
workflow.add_node("safe_tools", safe_tool_node)
workflow.add_node("sensitive_tools", sensitive_tool_node)

# Add Edges
workflow.add_edge(START, "reasoning_agent")

workflow.add_conditional_edges(
    "reasoning_agent",
    route_tools,
    {
        "safe_tools": "safe_tools",
        "sensitive_tools": "sensitive_tools",
        "__end__": END
    }
)

# Return to reasoning agent after tool execution
workflow.add_edge("safe_tools", "reasoning_agent")
workflow.add_edge("sensitive_tools", "reasoning_agent")

# Set up thread-level memory checkpointer
memory = MemorySaver()

# Compile the graph with an interrupt on the sensitive tools node for HITL
graph = workflow.compile(
    checkpointer=memory,
    interrupt_before=["sensitive_tools"]
)
