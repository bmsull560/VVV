import time
import logging
import random
from typing import Dict, Any, List

from agents.core.agent_base import LLMAgent, AgentResult, AgentStatus, MCPClient

logger = logging.getLogger(__name__)

class CritiqueAgent(LLMAgent):
    def __init__(self, agent_id: str, mcp_client: MCPClient, config: Dict[str, Any]):
        super().__init__(agent_id, mcp_client, config)
        logger.info(f"Initialized CritiqueAgent with id: {self.agent_id}")

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Critiques a generated narrative, providing feedback and a confidence score.
        Expected inputs:
            - narrative_text: str (The generated narrative to be critiqued)
            - key_points: List[str] (The key points from the narrative)
        """
        start_time = time.monotonic()
        logger.info(f"Executing CritiqueAgent with inputs: {list(inputs.keys())}")

        narrative_text = inputs.get('narrative_text', '')
        key_points = inputs.get('key_points', [])

        # Placeholder: Simulate critique logic
        critique_summary = "The narrative provides a solid foundation."
        suggestions = []
        confidence = 0.85 # Start with a base confidence

        if len(narrative_text.split()) < 50:
            suggestions.append("Consider elaborating further on the value proposition to create a more detailed narrative.")
            confidence -= 0.10
        
        if not any("ROI" in point for point in key_points):
            suggestions.append("The key points should explicitly mention the projected ROI to immediately grab attention.")
            confidence -= 0.05
        
        if not suggestions:
            critique_summary += " It is clear, concise, and effectively uses the key data points."

        # Ensure confidence is within a reasonable range
        confidence = max(0.5, min(0.99, confidence))

        output_data = {
            "critique_summary": critique_summary,
            "suggestions": suggestions,
            "confidence_score": round(confidence, 2)
        }

        execution_time_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(f"CritiqueAgent completed in {execution_time_ms}ms")

        return AgentResult(
            status=AgentStatus.COMPLETED,
            data=output_data,
            execution_time_ms=execution_time_ms,
            confidence_score=output_data['confidence_score'] # Also populate the top-level score
        )

