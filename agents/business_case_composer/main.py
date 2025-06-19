import time
import logging
from typing import Dict, Any, List, Optional

from agents.core.agent_base import LLMAgent, AgentResult, AgentStatus, MCPClient

logger = logging.getLogger(__name__)

class BusinessCaseComposerAgent(LLMAgent):
    def __init__(self, agent_id: str, mcp_client: MCPClient, config: Dict[str, Any]):
        super().__init__(agent_id, mcp_client, config)
        logger.info(f"Initialized BusinessCaseComposerAgent with id: {self.agent_id}")

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Assembles a complete business case document from all prior agent outputs.
        Expected inputs:
            - user_query: str
            - value_drivers: List[Dict]
            - personas: List[Dict]
            - roi_summary: Dict
            - sensitivity_analysis_results: Optional[List[Dict]]
            - narrative_output: Dict (containing narrative_text, key_points)
            - critique_output: Dict (containing critique_summary, suggestions, confidence_score)
        """
        start_time = time.monotonic()
        logger.info(f"Executing BusinessCaseComposerAgent with inputs: {list(inputs.keys())}")

        # Extract inputs
        user_query = inputs.get('user_query', 'N/A')
        value_drivers = inputs.get('value_drivers', [])
        personas = inputs.get('personas', [])
        roi_summary = inputs.get('roi_summary', {})
        sensitivity_analysis_results = inputs.get('sensitivity_analysis_results')
        narrative_output = inputs.get('narrative_output', {})
        critique_output = inputs.get('critique_output', {})

        # Placeholder: Assemble into a structured document (dictionary for now)
        business_case_doc = {
            "title": f"Business Value Proposal for {user_query[:30]}...",
            "executive_summary": narrative_output.get('narrative_text', 'Executive summary placeholder.'),
            "table_of_contents": [
                "Introduction",
                "Understanding Your Needs",
                "Proposed Solution & Value Drivers",
                "Financial Projections (ROI)",
                "Sensitivity Analysis",
                "AI-Generated Narrative Critique",
                "Conclusion"
            ],
            "introduction": f"This document outlines the potential business value based on your query: '{user_query}'.",
            "understanding_your_needs": {
                "key_personas_addressed": [p.get('name', 'Unknown Persona') for p in personas],
                "challenges_identified": f"Based on the initial query, challenges related to {user_query[:50]}... are primary concerns."
            },
            "proposed_solution_value_drivers": {
                "overview": "Our proposed solution focuses on the following key value pillars:",
                "pillars": value_drivers # Simplified, actual would be more detailed
            },
            "financial_projections_roi": roi_summary,
            "sensitivity_analysis": {
                "summary": f"{len(sensitivity_analysis_results) if sensitivity_analysis_results else 0} scenarios considered.",
                "details": sensitivity_analysis_results
            },
            "ai_critique_and_confidence": {
                "narrative_critique": critique_output.get('critique_summary', 'N/A'),
                "suggestions_for_improvement": critique_output.get('suggestions', []),
                "overall_confidence_score": critique_output.get('confidence_score', 0.0)
            },
            "key_talking_points": narrative_output.get('key_points', []),
            "conclusion": "We are confident that this proposal addresses your key challenges and offers significant business value."
        }

        output_data = {"composed_business_case": business_case_doc}

        execution_time_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(f"BusinessCaseComposerAgent completed in {execution_time_ms}ms")

        return AgentResult(
            status=AgentStatus.COMPLETED,
            data=output_data,
            execution_time_ms=execution_time_ms
        )

