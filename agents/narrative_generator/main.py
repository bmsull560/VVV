import time
import logging
from typing import Dict, Any, List, Optional

from agents.core.agent_base import LLMAgent, AgentResult, AgentStatus, MCPClient

logger = logging.getLogger(__name__)

class NarrativeGeneratorAgent(LLMAgent):
    def __init__(self, agent_id: str, mcp_client: MCPClient, config: Dict[str, Any]):
        super().__init__(agent_id, mcp_client, config)
        logger.info(f"Initialized NarrativeGeneratorAgent with id: {self.agent_id}")

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Generates a narrative based on value drivers, personas, and ROI calculations.
        Expected inputs:
            - user_query: str (original user input for context)
            - value_drivers: List[Dict] (structured value drivers)
            - personas: List[Dict] (identified personas)
            - roi_summary: Dict (key financial metrics and ROI)
            - sensitivity_analysis_results: Optional[List[Dict]] (what-if scenarios)
        """
        start_time = time.monotonic()
        logger.info(f"Executing NarrativeGeneratorAgent with inputs: {list(inputs.keys())}")

        # Placeholder: Access inputs to show they are being considered (even if not used yet)
        user_query = inputs.get('user_query', 'No user query provided.')
        value_drivers = inputs.get('value_drivers', [])
        personas = inputs.get('personas', [])
        roi_summary = inputs.get('roi_summary', {})

        # Simulate narrative generation based on inputs
        narrative_parts = [
            f"Based on your initial query about '{user_query[:50]}...', we've identified key areas for value creation.",
            f"Focusing on {len(value_drivers)} value driver pillar(s) and {len(personas)} key persona(s), significant financial impact is projected.",
            f"The calculated ROI stands at {roi_summary.get('roi_percentage', 'N/A')}%, with a payback period of {roi_summary.get('payback_period_months', 'N/A')} months."
        ]
        
        if value_drivers:
            pillar_names = [vd.get('pillar', 'Unnamed Pillar') for vd in value_drivers]
            narrative_parts.append(f"The primary value pillars include: {', '.join(pillar_names)}.")

        generated_narrative = "\n".join(narrative_parts)
        key_points = [
            f"Projected ROI: {roi_summary.get('roi_percentage', 'N/A')}%",
            f"Identified {len(value_drivers)} value driver pillars.",
            f"Targeted {len(personas)} personas."
        ]

        output_data = {
            "narrative_text": generated_narrative,
            "key_points": key_points
        }

        execution_time_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(f"NarrativeGeneratorAgent completed in {execution_time_ms}ms")

        return AgentResult(
            status=AgentStatus.COMPLETED,
            data=output_data,
            execution_time_ms=execution_time_ms
        )

