from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Accumulated conversation history
    messages: Annotated[list[AnyMessage], add_messages]
    # Tracks the sender node (e.g. 'reasoning_agent')
    sender: str
    # API Cost Protection: tracks consecutive tool failures to avoid infinite looping
    consecutive_errors: int
