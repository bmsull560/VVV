import logging
from typing import Dict, Any, List

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class ValueDriverAgent(BaseAgent):
    """Identifies key business value drivers from unstructured text using a hierarchical model."""

    # Tier 1 -> Tier 2 -> Tier 3 hierarchical value driver model
    VALUE_HIERARCHY = {
        "Cost Savings": {
            "tier_2_drivers": [
                {
                    "name": "Reduce Manual Labor",
                    "description": "Automating manual processes to reduce employee hours.",
                    "keywords": ["manual process", "time-consuming", "slow", "automate"],
                    "tier_3_metrics": [
                        {"name": "Hours saved per week", "type": "number", "default_value": 10},
                        {"name": "Average hourly rate", "type": "currency", "default_value": 50},
                    ]
                },
                {
                    "name": "Lower Operational Overhead",
                    "description": "Decreasing ongoing operational expenses.",
                    "keywords": ["overhead", "expense", "cost", "budget"],
                    "tier_3_metrics": [
                        {"name": "Monthly overhead reduction", "type": "currency", "default_value": 5000},
                    ]
                }
            ]
        },
        "Productivity Gains": {
            "tier_2_drivers": [
                {
                    "name": "Accelerate Task Completion",
                    "description": "Reducing the time it takes to complete key business tasks.",
                    "keywords": ["slow", "bottleneck", "time-consuming", "streamline"],
                    "tier_3_metrics": [
                        {"name": "Time saved per task (minutes)", "type": "number", "default_value": 60},
                        {"name": "Tasks per week", "type": "number", "default_value": 20},
                    ]
                },
            ]
        },
        "Risk Mitigation": {
            "tier_2_drivers": [
                {
                    "name": "Improve Security Posture",
                    "description": "Reducing the risk of security breaches and data loss.",
                    "keywords": ["security", "risk", "threat", "breach"],
                    "tier_3_metrics": [
                        {"name": "Estimated cost of a breach", "type": "currency", "default_value": 100000},
                        {"name": "Likelihood reduction (%)", "type": "percentage", "default_value": 50},
                    ]
                },
                {
                    "name": "Ensure Regulatory Compliance",
                    "description": "Avoiding fines and penalties associated with non-compliance.",
                    "keywords": ["compliance", "gdpr", "regulation"],
                    "tier_3_metrics": [
                        {"name": "Potential fine amount", "type": "currency", "default_value": 50000},
                    ]
                }
            ]
        },
        "Revenue Growth": {
            "tier_2_drivers": [
                {
                    "name": "Increase Lead Conversion",
                    "description": "Improving the rate at which leads become customers.",
                    "keywords": ["sales", "conversion", "leads"],
                    "tier_3_metrics": [
                        {"name": "Additional leads per month", "type": "number", "default_value": 100},
                        {"name": "Conversion rate increase (%)", "type": "percentage", "default_value": 5},
                        {"name": "Average deal size", "type": "currency", "default_value": 10000},
                    ]
                },
            ]
        }
    }

    def __init__(self, agent_id, mcp_client, config):
        super().__init__(agent_id, mcp_client, config)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Analyzes input text to find and categorize value drivers based on a hierarchical model.

        Args:
            inputs: A dictionary with a 'text' key containing the user's input.
        """
        if not isinstance(inputs, dict) or 'text' not in inputs:
            return AgentResult(status=AgentStatus.FAILED, data={"error": "Input must be a dictionary with a 'text' key."})

        input_text = inputs['text'].lower()
        
        identified_pillars = []
        for pillar_name, pillar_data in self.VALUE_HIERARCHY.items():
            matched_tier_2_drivers = []
            for tier_2_driver in pillar_data['tier_2_drivers']:
                keywords_found = [kw for kw in tier_2_driver['keywords'] if kw in input_text]
                if keywords_found:
                    # Add the Tier 2 driver and include which keywords were found
                    driver_copy = tier_2_driver.copy()
                    driver_copy['keywords_found'] = keywords_found
                    matched_tier_2_drivers.append(driver_copy)
            
            if matched_tier_2_drivers:
                identified_pillars.append({
                    "pillar": pillar_name,
                    "tier_2_drivers": matched_tier_2_drivers
                })

        if not identified_pillars:
            logger.info("No specific value drivers identified in the text.")
            return AgentResult(status=AgentStatus.COMPLETED, data={"drivers": [], "message": "No specific value drivers identified."})

        logger.info(f"Identified value driver pillars: {[p['pillar'] for p in identified_pillars]}")
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data={'drivers': identified_pillars}
        )
