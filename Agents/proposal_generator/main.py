import logging
import time
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from agents.core.agent_base import AgentResult, AgentStatus, BaseAgent

logger = logging.getLogger(__name__)


class ProposalGeneratorInput(BaseModel):
    """Input model for the ProposalGeneratorAgent."""

    business_objective: str = Field(..., description="The core business objective.")
    value_drivers: List[Dict[str, Any]] = Field(
        ..., description="Detailed value drivers identified."
    )
    roi_analysis: Dict[str, Any] = Field(
        ..., description="The complete ROI analysis output."
    )
    risk_analysis: Dict[str, Any] = Field(
        ..., description="The complete risk analysis output."
    )
    output_format: str = Field(
        default="markdown", description="The desired output format (e.g., markdown, json)."
    )


class ProposalGeneratorAgent(BaseAgent):
    """An agent that generates a business proposal from various analyses."""

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        start_time = time.monotonic()
        """Generates a business proposal."""
        try:
            validated_inputs = ProposalGeneratorInput(**inputs)
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            execution_time_ms = (time.monotonic() - start_time) * 1000
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"message": f"Invalid input: {e}"},
                execution_time_ms=execution_time_ms,
            )

        # Placeholder for proposal generation logic
        proposal = self._generate_proposal(validated_inputs)
        execution_time_ms = (time.monotonic() - start_time) * 1000
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data={"proposal": proposal},
            execution_time_ms=execution_time_ms,
        )

    def _generate_proposal(self, inputs: ProposalGeneratorInput) -> str:
        """Private method to generate the proposal content."""
        if inputs.output_format == "markdown":
            return "# Business Proposal\n\n(Markdown content placeholder)"
        elif inputs.output_format == "json":
            return '{"title": "Business Proposal", "body": "JSON content placeholder"}'
        else:
            return "Unsupported format"
