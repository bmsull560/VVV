import logging
import time
import textwrap
from enum import Enum
from typing import Any, Dict, List, Optional

from agents.core.agent_base import AgentResult, AgentStatus, LLMAgent, MCPClient
from agents.core.mcp_client import KnowledgeEntity
from agents.utils.validation import validate_required_fields

logger = logging.getLogger(__name__)

class OutputFormat(str, Enum):
    """Enum for supported output formats."""
    MARKDOWN = "markdown"
    JSON = "json"

class BusinessCaseComposerAgent(LLMAgent):
    """
    A production-ready agent that composes a final business case document
    from the outputs of various upstream agents. Supports multiple output formats.
    """

    def __init__(self, agent_id: str, mcp_client: MCPClient, config: Dict[str, Any]):
        super().__init__(agent_id, mcp_client, config)
        self.acls = self.config.get("acls", {})
        logger.info(f"Initialized BusinessCaseComposerAgent with id: {self.agent_id}")

    def _validate_inputs(self, inputs: Dict[str, Any]) -> Optional[str]:
        """Validates the presence and basic structure of required inputs."""
        required = {
            "user_query": (str, "Initial user query is required."),
            "value_drivers": (list, "Value drivers list is required."),
            "roi_summary": (dict, "ROI summary is required."),
            "narrative_output": (dict, "Narrative output is required."),
        }
        error_message = validate_required_fields(inputs, required)
        if error_message:
            return error_message
        return None

    def _format_markdown_header(self, title: str) -> str:
        """Formats the main header for the Markdown document."""
        return f"# {title}\n\n"

    def _format_section(self, title: str, content: str) -> str:
        """Formats a standard section with a title and content."""
        return f"## {title}\n\n{textwrap.dedent(content)}\n\n"

    def _format_roi_summary_md(self, roi_summary: Dict[str, Any]) -> str:
        """Formats the ROI summary section into a Markdown table."""
        if not roi_summary:
            return "No ROI data available.\n"
        
        headers = ["Metric", "Value"]
        rows = [
            ["Total Annual Value", f"${roi_summary.get('total_annual_value', 0):,.2f}"],
            ["ROI Percentage", f"{roi_summary.get('roi_percentage', 0):.2f}%"],
            ["Payback Period (Months)", f"{roi_summary.get('payback_period_months', 0):.1f}"],
            ["Net Present Value (NPV)", f"${roi_summary.get('npv', 0):,.2f}"],
        ]
        
        header_line = f"| {' | '.join(headers)} |"
        separator_line = f"| {' | '.join(['---'] * len(headers))} |"
        row_lines = [f"| {' | '.join(map(str, row))} |" for row in rows]
        
        return "\n".join([header_line, separator_line] + row_lines)

    def _format_sensitivity_analysis_md(self, analysis: Optional[List[Dict[str, Any]]]) -> str:
        """Formats the sensitivity analysis into a Markdown table, if available."""
        if not analysis:
            return ""
        
        content = "### Sensitivity Analysis\n\n"
        headers = ["Variable", "Impact on ROI", "Risk Level"]
        rows = [[item.get('variable_name', 'N/A'), f"{item.get('roi_impact_percentage', 0):.2f}%", item.get('risk_level', 'N/A')] for item in analysis]
        
        header_line = f"| {' | '.join(headers)} |"
        separator_line = f"| {' | '.join(['---'] * len(headers))} |"
        row_lines = [f"| {' | '.join(map(str, row))} |" for row in rows]
        
        content += "\n".join([header_line, separator_line] + row_lines)
        return content + "\n\n"

    def _format_critique_md(self, critique: Dict[str, Any]) -> str:
        """Formats the AI critique section."""
        if not critique:
            return ""
        
        score = critique.get('confidence_score', 0.0)
        summary = critique.get('critique_summary', 'No critique available.')
        suggestions = critique.get('suggestions', [])
        
        content = f"### AI-Generated Critique (Confidence: {score:.2f})\n\n"
        content += f"**Summary:** {summary}\n\n"
        if suggestions:
            content += "**Suggestions for Improvement:**\n"
            for suggestion in suggestions:
                content += f"- {suggestion}\n"
        return content

    def _compose_markdown_document(self, inputs: Dict[str, Any]) -> str:
        """Assembles the full business case in Markdown format."""
        doc_parts = []
        
        title = f"Business Value Proposal for: {inputs['user_query']}"
        doc_parts.append(self._format_markdown_header(title))
        
        # Executive Summary
        executive_summary = inputs['narrative_output'].get('narrative_text', 'N/A')
        doc_parts.append(self._format_section("Executive Summary", executive_summary))
        
        # Value Drivers
        value_drivers_content = ""
        for driver in inputs['value_drivers']:
            value_drivers_content += f"- **{driver.get('name', 'Unnamed Driver')}:** {driver.get('description', 'No description.')}\n"
        doc_parts.append(self._format_section("Key Value Drivers", value_drivers_content))

        # Financial Projections
        roi_md = self._format_roi_summary_md(inputs['roi_summary'])
        doc_parts.append(self._format_section("Financial Projections (ROI)", roi_md))

        # Sensitivity Analysis (optional)
        sensitivity_md = self._format_sensitivity_analysis_md(inputs.get('sensitivity_analysis_results'))
        if sensitivity_md:
            doc_parts.append(sensitivity_md)

        # AI Critique (optional)
        critique_md = self._format_critique_md(inputs.get('critique_output', {}))
        if critique_md:
            doc_parts.append(self._format_section("AI Critique & Confidence", critique_md))

        # Conclusion
        doc_parts.append(self._format_section("Conclusion", "This proposal outlines a strong business case for moving forward, backed by data-driven financial analysis and strategic alignment with your objectives."))
        
        return "".join(doc_parts)

    def _compose_json_document(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Assembles the full business case in JSON format."""
        return {
            "title": f"Business Value Proposal for {inputs['user_query']}",
            "executive_summary": inputs['narrative_output'].get('narrative_text', 'N/A'),
            "value_drivers": inputs['value_drivers'],
            "financial_projections": inputs['roi_summary'],
            "sensitivity_analysis": inputs.get('sensitivity_analysis_results'),
            "ai_critique": inputs.get('critique_output'),
            "user_context": {
                "query": inputs['user_query'],
                "personas": inputs.get('personas', [])
            }
        }

    async def _store_analysis_in_mcp(self, inputs: Dict[str, Any], composed_document: Any) -> None:
        """Stores the analysis details and final document in MCP."""
        try:
            entity = KnowledgeEntity(
                entity_type="composed_business_case",
                data={
                    "inputs": inputs,
                    "composed_document": composed_document,
                    "agent_id": self.agent_id,
                    "timestamp": time.time(),
                },
                acls=self.acls
            )
            await self.mcp_client.create_entity(entity)
            logger.info("Successfully stored composed business case in MCP.")
        except Exception as e:
            logger.error(f"Failed to store business case in MCP: {e}", exc_info=True)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Executes the agent to compose the business case.
        Inputs:
            - output_format: str ("markdown" or "json") - Defaults to "json".
            - ... all other required inputs for composition.
        """
        start_time = time.monotonic()
        logger.info(f"Executing BusinessCaseComposerAgent with inputs: {list(inputs.keys())}")

        error_message = self._validate_inputs(inputs)
        if error_message:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"message": error_message},
                execution_time_ms=execution_time_ms,
            )

        output_format = inputs.get("output_format", "json")
        composed_document = None

        try:
            if output_format == OutputFormat.MARKDOWN:
                composed_document = self._compose_markdown_document(inputs)
            elif output_format == OutputFormat.JSON:
                composed_document = self._compose_json_document(inputs)
            else:
                execution_time_ms = int((time.monotonic() - start_time) * 1000)
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"message": f"Unsupported output format: {output_format}"},
                    execution_time_ms=execution_time_ms,
                )

            await self._store_analysis_in_mcp(inputs, composed_document)

            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"BusinessCaseComposerAgent completed in {execution_time_ms}ms")

            return AgentResult(
                status=AgentStatus.COMPLETED,
                data={"composed_business_case": composed_document, "format": output_format},
                execution_time_ms=execution_time_ms
            )

        except Exception as e:
            logger.error(f"An unexpected error occurred during business case composition: {e}", exc_info=True)
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"message": f"An unexpected error occurred: {e}"},
                execution_time_ms=execution_time_ms,
            )
