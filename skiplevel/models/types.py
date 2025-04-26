# TODO: Define project types and interfaces

from typing import List, Optional
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

class AgentState(TypedDict, total=False):
    """
    The shared state passed between nodes in Skiplevel's LangGraph DAG.
    """
    messages: List[BaseMessage]
    reflection_text: str
    evaluation_result: Optional[dict]
    growth_advice: Optional[str]
