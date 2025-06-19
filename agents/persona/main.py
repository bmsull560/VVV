import logging
from typing import Dict, Any, List

import time
from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class PersonaAgent(BaseAgent):
    """Identifies potential buyer personas from unstructured text using detailed profiles."""

    PERSONA_PROFILES = {
        "Financial Leader": {
            "title": "Financial Leader (CFO, VP Finance)",
            "keywords": ["cfo", "finance", "budget", "vp of finance", "financial officer", "roi", "cost"],
            "goals": ["Improve profitability", "Ensure predictable revenue", "Optimize resource allocation"],
            "challenges": ["Inaccurate forecasting", "High operational costs", "Lack of visibility into financial metrics"],
            "key_metrics": ["Return on Investment (ROI)", "Payback Period", "Net Present Value (NPV)", "Operating Margin"],
        },
        "Technical Leader": {
            "title": "Technical Leader (CIO, CTO, IT Manager)",
            "keywords": ["cio", "cto", "it manager", "head of it", "infrastructure", "security", "integration"],
            "goals": ["Ensure system reliability and security", "Drive innovation through technology", "Improve operational efficiency"],
            "challenges": ["Legacy system integration", "Cybersecurity threats", "Managing technical debt"],
            "key_metrics": ["System downtime", "Mean Time to Resolution (MTTR)", "IT project ROI"],
        },
        "Sales Leader": {
            "title": "Sales Leader (CRO, VP of Sales)",
            "keywords": ["cro", "vp of sales", "sales team", "sales leader", "revenue officer", "quota"],
            "goals": ["Increase sales velocity", "Improve forecast accuracy", "Grow market share"],
            "challenges": ["Long sales cycles", "Low lead conversion rates", "Inaccurate sales forecasting"],
            "key_metrics": ["Quota attainment", "Sales cycle length", "Lead-to-opportunity conversion rate"],
        },
        "Marketing Leader": {
            "title": "Marketing Leader (CMO, VP Marketing)",
            "keywords": ["cmo", "vp of marketing", "marketing lead", "demand generation", "brand", "pipeline"],
            "goals": ["Generate qualified pipeline", "Improve brand awareness", "Measure marketing ROI"],
            "challenges": ["Poor quality leads", "Difficulty proving marketing's impact on revenue", "High customer acquisition cost (CAC)"],
            "key_metrics": ["Marketing Qualified Leads (MQLs)", "Customer Acquisition Cost (CAC)", "Marketing-sourced pipeline"],
        },
    }

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Analyzes input text to identify and categorize buyer personas based on detailed profiles.

        Args:
            inputs: A dictionary with a 'text' key containing the user's input.
        """
        start_time = time.monotonic()

        if not isinstance(inputs, dict) or 'user_query' not in inputs:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(
                status=AgentStatus.FAILED, 
                data={"error": "Input must be a dictionary with a 'user_query' key."},
                execution_time_ms=execution_time_ms
            )

        input_text = inputs['user_query'].lower()

        identified_personas = []
        for persona_name, profile in self.PERSONA_PROFILES.items():
            keywords_found = [kw for kw in profile['keywords'] if kw in input_text]
            if keywords_found:
                persona_data = profile.copy()
                persona_data['evidence'] = keywords_found
                identified_personas.append(persona_data)

        execution_time_ms = int((time.monotonic() - start_time) * 1000)
        if not identified_personas:
            logger.info("No specific personas identified in the text.")
            return AgentResult(
                status=AgentStatus.COMPLETED, 
                data={"personas": [], "message": "No specific personas identified."},
                execution_time_ms=execution_time_ms
            )

        logger.info(f"Identified personas: {[p['title'] for p in identified_personas]}")
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data={'personas': identified_personas},
            execution_time_ms=execution_time_ms
        )
