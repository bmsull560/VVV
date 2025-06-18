import logging
from typing import Dict, Any, List

from ..core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class PersonaAgent(BaseAgent):
    """Identifies potential buyer personas from unstructured text."""

    PERSONA_KEYWORDS = {
        "Financial Leader (CFO, VP Finance)": ["cfo", "finance", "budget", "vp of finance", "financial officer"],
        "Technical Leader (CIO, CTO, IT Manager)": ["cio", "cto", "it manager", "head of it", "infrastructure", "security"],
        "Sales Leader (CRO, VP of Sales)": ["cro", "vp of sales", "sales team", "sales leader", "revenue officer"],
        "Marketing Leader (CMO, VP Marketing)": ["cmo", "vp of marketing", "marketing lead", "demand generation", "brand"],
    }

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Analyzes input text to identify and categorize buyer personas.

        Args:
            inputs: A dictionary with a 'text' key containing the user's input.
        """
        if not isinstance(inputs, dict) or 'text' not in inputs:
            return AgentResult(status=AgentStatus.FAILED, data={"error": "Input must be a dictionary with a 'text' key."})

        input_text = inputs['text'].lower()

        identified_personas = []
        for persona, keywords in self.PERSONA_KEYWORDS.items():
            if any(keyword in input_text for keyword in keywords):
                identified_personas.append({
                    "persona_type": persona,
                    "evidence": [k for k in keywords if k in input_text]
                })

        if not identified_personas:
            logger.info("No specific personas identified in the text.")
            return AgentResult(status=AgentStatus.COMPLETED, data={"personas": [], "message": "No specific personas identified."})

        logger.info(f"Identified personas: {identified_personas}")
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data={'personas': identified_personas}
        )
