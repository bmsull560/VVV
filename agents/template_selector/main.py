"""
Template Selector Agent - Production Version

This agent analyzes user inputs and business context to select the most appropriate
business case template from a configurable library. It uses a weighted scoring model
and calculates a confidence score based on input quality to deliver reliable and
transparent template recommendations.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from pydantic import BaseModel, Field, ValidationError

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.core.mcp_client import MCPClient

logger = logging.getLogger(__name__)

# --- Enums for categorical data ---
class IndustryType(str, Enum):
    HEALTHCARE = "healthcare"
    FINANCIAL_SERVICES = "financial_services"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    EDUCATION = "education"
    GOVERNMENT = "government"
    TELECOMMUNICATIONS = "telecommunications"
    ENERGY = "energy"
    GENERIC = "generic"

class ComplexityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# --- Pydantic Models for Data Structure and Validation ---

class TemplateSelectorInput(BaseModel):
    """Input model for the TemplateSelectorAgent, providing structure and validation."""
    business_objective: str = Field(..., description="Primary business objective for the initiative.")
    industry: IndustryType = Field(..., description="Industry classification for context.")
    stakeholder_types: Optional[List[str]] = Field(None, description="List of key stakeholder roles.")
    complexity_level: Optional[ComplexityLevel] = Field(None, description="Estimated project complexity.")
    primary_value_drivers: Optional[List[str]] = Field(None, description="Key value drivers for the business case.")

class TemplateDefinition(BaseModel):
    """Defines the structure of a business case template in the database."""
    name: str
    description: str
    industries: List[IndustryType]
    objectives: List[str]
    stakeholders: List[str]
    complexity: List[ComplexityLevel]
    value_drivers: List[str]
    sections: List[str]

class SelectedTemplate(BaseModel):
    """Represents a single recommended template."""
    template_id: str
    template_name: str
    description: str
    match_score: float
    confidence_score: float
    overall_score: float
    sections: List[str]

class TemplateSelectorResult(BaseModel):
    """Output model for the agent's results."""
    selected_template: SelectedTemplate
    alternative_templates: List[SelectedTemplate]
    selection_rationale: str
    execution_metadata: Dict[str, Any]

# --- Main Agent Class ---

class TemplateSelectorAgent(BaseAgent):
    """
    Selects the most appropriate business case template using a configurable,
    weighted scoring model and robust input validation.
    """

    def __init__(self, agent_id: str, mcp_client: MCPClient, config: Dict[str, Any]):
        super().__init__(agent_id, mcp_client, config)
        self.scoring_weights = self.config.get('scoring_weights', {})
        self.template_database = self._load_template_database()

    def _load_template_database(self) -> Dict[str, TemplateDefinition]:
        """Loads and validates the template database from agent configuration."""
        db_config = self.config.get('template_database', {})
        validated_db = {}
        for key, template_data in db_config.items():
            try:
                validated_db[key] = TemplateDefinition(**template_data)
            except ValidationError as e:
                logger.error(f"Invalid template definition for '{key}': {e}")
                # In a production scenario, this might raise an exception
                # or prevent the agent from starting.
        if not validated_db:
            logger.warning("Template database is empty or failed to load. Agent may not function correctly.")
        return validated_db

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Main execution logic for the agent."""
        logger.info(f"Executing TemplateSelectorAgent with inputs: {inputs}")
        start_time = time.monotonic()
        try:
            # 1. Validate and structure inputs
            try:
                validated_inputs = TemplateSelectorInput(**inputs)
            except ValidationError as e:
                # Check if the error is specifically for the 'industry' field
                is_industry_error = any(err['loc'][0] == 'industry' for err in e.errors())
                if is_industry_error and 'industry' in inputs:
                    logger.warning(f"Unrecognized industry '{inputs['industry']}'. Falling back to generic.")
                    inputs['industry'] = IndustryType.GENERIC
                    validated_inputs = TemplateSelectorInput(**inputs) # Retry validation
                else:
                    raise # Re-raise if it's a different validation error

            logger.info(f"Input validation successful. Validated data: {validated_inputs.model_dump()}")

            # 2. Perform analysis
            recommendations = self._get_template_recommendations(validated_inputs)
            if not recommendations:
                raise ValueError("No suitable templates found for the given criteria.")

            # 3. Format and return result
            result_data = self._format_result(recommendations, validated_inputs)

            # 4. Record audit trail in MCP
            await self._record_mcp_audit(result_data, validated_inputs)

            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"Template selection completed in {execution_time_ms}ms. Selected: {result_data.selected_template.template_name}")
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=result_data.model_dump(),
                execution_time_ms=execution_time_ms
            )

        except ValidationError as e:
            logger.warning(f"Input validation failed: {e}")
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"message": f"Input validation error: {e}"},
                execution_time_ms=execution_time_ms
            )
        except Exception as e:
            logger.exception(f"An unexpected error occurred during template selection: {e}")
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"message": f"An unexpected error occurred: {e}"},
                execution_time_ms=execution_time_ms
            )

    def _get_template_recommendations(self, inputs: TemplateSelectorInput) -> List[SelectedTemplate]:
        """Scores all templates and returns a ranked list of recommendations."""
        scored_templates = []
        confidence_score, confidence_details = self._calculate_confidence_score(inputs)

        for template_id, template_def in self.template_database.items():
            match_score, _ = self._calculate_match_score(template_def, inputs)

            logger.debug(f"Scoring template '{template_id}': Match={match_score:.2f}, Confidence={confidence_score:.2f}")

            # Combine match score and confidence score
            overall_score = match_score * confidence_score

            scored_templates.append(SelectedTemplate(
                template_id=template_id,
                template_name=template_def.name,
                description=template_def.description,
                match_score=round(match_score, 4),
                confidence_score=round(confidence_score, 4),
                overall_score=round(overall_score, 4),
                sections=template_def.sections
            ))

        # Sort by the overall combined score
        scored_templates.sort(key=lambda x: x.overall_score, reverse=True)
        logger.info(f"Ranked top 3 templates: {[(t.template_name, t.overall_score) for t in scored_templates[:3]]}")
        return scored_templates

    def _calculate_match_score(self, template: TemplateDefinition, inputs: TemplateSelectorInput) -> Tuple[float, Dict[str, float]]:
        """Calculates a score based on how well the template matches the inputs."""
        total_score = 0.0
        component_scores = {}

        # Industry match
        score = 1.0 if inputs.industry in template.industries or IndustryType.GENERIC in template.industries else 0.0
        total_score += score * self.scoring_weights.get('industry_match', 0.25)
        component_scores['industry'] = score

        # Objective alignment
        score = 1.0 if inputs.business_objective.lower() in [obj.lower() for obj in template.objectives] else 0.0
        total_score += score * self.scoring_weights.get('objective_alignment', 0.30)
        component_scores['objective'] = score

        # Stakeholder fit
        if inputs.stakeholder_types:
            matching = set(inputs.stakeholder_types) & set(template.stakeholders)
            score = len(matching) / len(template.stakeholders) if template.stakeholders else 0.0
        else:
            score = 0.5 # Neutral score if not provided
        total_score += score * self.scoring_weights.get('stakeholder_fit', 0.15)
        component_scores['stakeholders'] = score

        # Complexity match
        if inputs.complexity_level:
            score = 1.0 if inputs.complexity_level in template.complexity else 0.2
        else:
            score = 0.5 # Neutral score
        total_score += score * self.scoring_weights.get('complexity_match', 0.15)
        component_scores['complexity'] = score

        # Value driver alignment
        if inputs.primary_value_drivers:
            matching = set(inputs.primary_value_drivers) & set(template.value_drivers)
            score = len(matching) / len(template.value_drivers) if template.value_drivers else 0.0
        else:
            score = 0.5 # Neutral score
        total_score += score * self.scoring_weights.get('value_driver_alignment', 0.15)
        component_scores['value_drivers'] = score

        return total_score, component_scores

    def _calculate_confidence_score(self, inputs: TemplateSelectorInput) -> Tuple[float, Dict[str, float]]:
        """
        Calculates a confidence score based on the proportion of provided optional fields.
        A higher score indicates a more complete input, leading to higher confidence.
        """
        optional_fields = ['stakeholder_types', 'complexity_level', 'primary_value_drivers']
        provided_count = sum(1 for field in optional_fields if getattr(inputs, field) is not None)

        total_optional = len(optional_fields)
        confidence = provided_count / total_optional if total_optional > 0 else 1.0

        details = {field: (1.0 if getattr(inputs, field) is not None else 0.0) for field in optional_fields}

        return confidence, details

    def _format_result(self, recommendations: List[SelectedTemplate], inputs: TemplateSelectorInput) -> TemplateSelectorResult:
        """Formats the final agent output."""
        selected = recommendations[0]
        alternatives = recommendations[1:3] # Return top 2 alternatives
        rationale = self._generate_selection_rationale(selected, inputs)

        execution_metadata = {
            "input_parameters": inputs.model_dump(),
            "total_templates_evaluated": len(self.template_database),
            "confidence_score": selected.confidence_score
        }

        return TemplateSelectorResult(
            selected_template=selected,
            alternative_templates=alternatives,
            selection_rationale=rationale,
            execution_metadata=execution_metadata
        )

    def _generate_selection_rationale(self, template: SelectedTemplate, inputs: TemplateSelectorInput) -> str:
        """Generates a human-readable rationale for the template selection."""
        parts = [
            f"The '{template.template_name}' was selected with an overall score of {template.overall_score:.2f}.",
            f"It is a strong match for the '{inputs.industry.value}' industry and the '{inputs.business_objective}' objective."
        ]
        if inputs.stakeholder_types:
            parts.append(f"It is well-suited for stakeholders including: {', '.join(inputs.stakeholder_types)}.")
        if inputs.complexity_level:
            parts.append(f"The template matches the project's '{inputs.complexity_level.value}' complexity.")

        return " ".join(parts)

    async def _record_mcp_audit(self, result: TemplateSelectorResult, inputs: TemplateSelectorInput):
        """Records the execution details to MCP episodic memory for audit purposes."""
        try:
            entity_name = f"template_selection_analysis_{int(time.time())}"
            await self.mcp_client.memory.create_entity(
                name=entity_name,
                entity_type="Analysis",
                observations=[
                    f"Agent '{self.agent_id}' performed template selection.",
                    f"Selected Template: {result.selected_template.template_name} (ID: {result.selected_template.template_id})",
                    f"Overall Score: {result.selected_template.overall_score:.4f}",
                    f"Input - Industry: {inputs.industry.value}",
                    f"Input - Objective: {inputs.business_objective}"
                ]
            )
            logger.info(f"Successfully recorded analysis in MCP under entity '{entity_name}'.")
        except Exception as e:
            logger.error(f"Failed to record analysis in MCP: {e}")
