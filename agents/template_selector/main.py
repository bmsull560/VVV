"""
Template Selector Agent - Production Version

This agent analyzes user inputs and business context to select the most appropriate
business case template from a configurable library. It uses a weighted scoring model
and calculates a confidence score based on input quality to deliver reliable and
transparent template recommendations.
"""

import logging
import textwrap
import time
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from pydantic import BaseModel, Field, ValidationError

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.core.mcp_client import MCPClient 
from memory.memory_types import KnowledgeEntity

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
    sections: List[str]
    confidence_score: float
    overall_score: float
    suggested_customizations: List[str] = Field(default_factory=list)

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
        if not self.scoring_weights:
            # Default weights if not provided in config
            self.scoring_weights = {
                'industry_match': 0.25,
                'objective_alignment': 0.30,
                'stakeholder_fit': 0.15,
                'complexity_match': 0.15,
                'value_driver_alignment': 0.15
            }
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
                    logger.warning(f"Unrecognized industry '{inputs['industry']}'. Falling back to generic industry type.")
                    inputs['industry'] = IndustryType.GENERIC
                    validated_inputs = TemplateSelectorInput(**inputs) # Retry validation
                else:
                    raise # Re-raise if it's a different validation error

            # Log redacted version to avoid logging potentially sensitive data
            redacted_inputs = {
                'business_objective': validated_inputs.business_objective,
                'industry': validated_inputs.industry,
                'fields_provided': {
                    'stakeholder_types': validated_inputs.stakeholder_types is not None,
                    'complexity_level': validated_inputs.complexity_level is not None,
                    'primary_value_drivers': validated_inputs.primary_value_drivers is not None
                }
            }
            logger.info(f"Input validation successful. Validated data: {redacted_inputs}")

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
                sections=template_def.sections,
                match_score=round(match_score, 4),
                confidence_score=round(confidence_score, 4),
                overall_score=round(overall_score, 4),
                suggested_customizations=self._generate_customizations(template_def, inputs)
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
            # Neutral score with slight preference for templates with fewer stakeholder types
            score = 0.5 - (len(template.stakeholders) / 100)
        total_score += score * self.scoring_weights.get('stakeholder_fit', 0.15)
        component_scores['stakeholders'] = score

        # Complexity match
        if inputs.complexity_level:
            score = 1.0 if inputs.complexity_level in template.complexity else 0.2
        else:
            # Neutral score with preference for medium complexity if not specified
            score = 0.7 if ComplexityLevel.MEDIUM in template.complexity else 0.5
        total_score += score * self.scoring_weights.get('complexity_match', 0.15)
        component_scores['complexity'] = score

        # Value driver alignment
        if inputs.primary_value_drivers:
            matching = set(inputs.primary_value_drivers) & set(template.value_drivers)
            score = len(matching) / len(template.value_drivers) if template.value_drivers else 0.0
        else:
            # Neutral score with preference for templates with more comprehensive value drivers
            score = 0.5 + min(0.2, len(template.value_drivers) / 20)
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
    
    def _generate_customizations(self, template: TemplateDefinition, inputs: TemplateSelectorInput) -> List[str]:
        """Generates suggested customizations based on the template and input mismatch areas."""
        customizations = []
        
        # Check for industry customization needs
        if inputs.industry not in template.industries and IndustryType.GENERIC not in template.industries:
            customizations.append(f"Customize industry-specific sections for {inputs.industry.value}")
        
        # Check for stakeholder customization needs
        if inputs.stakeholder_types:
            missing_stakeholders = set(inputs.stakeholder_types) - set(template.stakeholders)
            if missing_stakeholders:
                customizations.append(f"Add sections addressing {', '.join(missing_stakeholders)} stakeholder needs")
        
        # Check for value driver customization needs
        if inputs.primary_value_drivers:
            missing_drivers = set(inputs.primary_value_drivers) - set(template.value_drivers)
            if missing_drivers:
                customizations.append(f"Strengthen coverage of {', '.join(missing_drivers)} value drivers")
        
        # Check for complexity level
        if inputs.complexity_level and inputs.complexity_level not in template.complexity:
            if inputs.complexity_level == ComplexityLevel.HIGH and ComplexityLevel.MEDIUM in template.complexity:
                customizations.append("Expand detailed analysis sections for higher complexity project")
            elif inputs.complexity_level == ComplexityLevel.LOW and ComplexityLevel.MEDIUM in template.complexity:
                customizations.append("Simplify presentation for lower complexity project")
        
        return customizations

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
        # Create a more detailed, well-structured rationale with score breakdown
        rationale = f"""
The '{template.template_name}' template has been selected as the optimal choice with an overall score of {template.overall_score:.2f} out of 1.00.

Key factors that influenced this selection:
• Industry alignment: The template is specifically designed for the {inputs.industry.value} industry
• Business objective: Excellent match for "{inputs.business_objective}" initiatives
"""

        # Add stakeholder information if available
        if inputs.stakeholder_types:
            rationale += f"• Stakeholder focus: Well-suited for {', '.join(inputs.stakeholder_types)} needs\n"
        
        # Add complexity information if available
        if inputs.complexity_level:
            rationale += f"• Complexity: Appropriate for {inputs.complexity_level.value} complexity projects\n"
        
        # Add value driver information if available
        if inputs.primary_value_drivers:
            rationale += f"• Value drivers: Includes sections covering {', '.join(inputs.primary_value_drivers)}\n"
        
        # Add confidence information
        rationale += f"\nConfidence score: {template.confidence_score:.2f} - "
        if template.confidence_score > 0.8:
            rationale += "High confidence based on comprehensive input data."
        elif template.confidence_score > 0.5:
            rationale += "Moderate confidence. Additional input details could improve selection precision."
        else:
            rationale += "Low confidence due to limited input data. Consider providing more details for better template matching."
        
        # Add customization suggestions if any
        if template.suggested_customizations:
            rationale += "\n\nRecommended customizations:\n"
            for i, suggestion in enumerate(template.suggested_customizations, 1):
                rationale += f"{i}. {suggestion}\n"
        
        return rationale.strip()

    async def _record_mcp_audit(self, result: TemplateSelectorResult, inputs: TemplateSelectorInput):
        """Records the execution details to MCP episodic memory for audit purposes."""
        try:
            # Create a knowledge entity to store the template selection audit
            audit_entity = KnowledgeEntity(
                entity_type="template_selection_analysis",
                data={
                    "agent_id": self.agent_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "selected_template": {
                        "template_id": result.selected_template.template_id,
                        "template_name": result.selected_template.template_name,
                        "match_score": result.selected_template.match_score,
                        "confidence_score": result.selected_template.confidence_score,
                        "overall_score": result.selected_template.overall_score
                    },
                    "input_data": {
                        "industry": inputs.industry.value,
                        "business_objective": inputs.business_objective,
                        "has_stakeholder_types": inputs.stakeholder_types is not None,
                        "has_complexity_level": inputs.complexity_level is not None,
                        "has_primary_value_drivers": inputs.primary_value_drivers is not None
                    },
                    "alternative_templates": [
                        {
                            "template_id": template.template_id,
                            "template_name": template.template_name,
                            "overall_score": template.overall_score
                        }
                        for template in result.alternative_templates[:2]  # Include top 2 alternatives
                    ]
                }
            )
            
            # Use the new create_entities API style
            entities_result = await self.mcp_client.create_entities([audit_entity], user_id="system", role="agent")
            logger.info(f"Successfully recorded template selection analysis in MCP")
        except Exception as e:
            logger.error(f"Failed to record analysis in MCP: {e}")
