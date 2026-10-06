"""
Grounding validation node for LangGraph pipeline.
Validates factual claims against retrieved evidence and strips citations on abstention.
"""

from typing import Any, Dict
from app.agent.state import AgentState
from app.services.grounding import validate_grounding


def validate_grounding_node(state: AgentState) -> Dict[str, Any]:
    return validate_grounding(state)
