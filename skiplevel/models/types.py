# File: skiplevel/models/types.py
# TODO: Define project types and interfaces

from typing import List, Optional
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict, Annotated
import operator

class AgentState(TypedDict, total=False):
    """
    The shared state passed between nodes in Skiplevel's LangGraph DAG.
    """
    messages: Annotated[List[BaseMessage], operator.add]
    reflection_text: str
    evaluation_result: Optional[str]
    growth_advice: Optional[str]
    next: Optional[str]
