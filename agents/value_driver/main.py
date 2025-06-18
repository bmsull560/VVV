import logging
from typing import Dict, Any, List

from ..core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class ValueDriverAgent(BaseAgent):
    """Identifies key business value drivers from unstructured text."""

    VALUE_KEYWORDS = {
        "Cost Savings": ["inefficient", "manual process", "overhead", "cost", "expense", "budget"],
        "Productivity Gains": ["slow", "bottleneck", "time-consuming", "automate", "streamline", "efficiency"],
        "Risk Mitigation": ["compliance", "security", "risk", "threat", "outage", "downtime", "GDPR"],
        "Revenue Growth": ["sales", "customer acquisition", "market share", "growth", "revenue", "conversion"],
    }

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Analyzes input text to find and categorize value drivers.

        Args:
            inputs: A dictionary with a 'text' key containing the user's input.
        """
        if not isinstance(inputs, dict) or 'text' not in inputs:
            return AgentResult(status=AgentStatus.FAILED, data={"error": "Input must be a dictionary with a 'text' key."})

        input_text = inputs['text'].lower()
        
        identified_drivers = []
        for pillar, keywords in self.VALUE_KEYWORDS.items():
            pillar_drivers = []
            for keyword in keywords:
                if keyword in input_text:
                    pillar_drivers.append(keyword)
            
            if pillar_drivers:
                identified_drivers.append({
                    "pillar": pillar,
                    "keywords_found": list(set(pillar_drivers))
                })

        if not identified_drivers:
            logger.info("No specific value drivers identified in the text.")
            return AgentResult(status=AgentStatus.COMPLETED, data={"drivers": [], "message": "No specific value drivers identified."})

        logger.info(f"Identified value drivers: {identified_drivers}")
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data={'drivers': identified_drivers}
        )
