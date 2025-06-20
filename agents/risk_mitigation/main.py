"""
Risk Mitigation Agent

This agent identifies, quantifies, and provides mitigation strategies for project risks.
It performs comprehensive risk assessment, impact analysis, and develops actionable
risk mitigation plans with cost-benefit analysis.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.types import KnowledgeEntity

logger = logging.getLogger(__name__)

class RiskCategory(Enum):
    """Categories of project risks."""
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    MARKET = "market"
    REGULATORY = "regulatory"
    SECURITY = "security"
    VENDOR = "vendor"
    RESOURCE = "resource"
    TIMELINE = "timeline"
    QUALITY = "quality"

class RiskSeverity(Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"

class RiskProbability(Enum):
    """Risk probability levels."""
    VERY_HIGH = "very_high"  # >80%
    HIGH = "high"            # 60-80%
    MEDIUM = "medium"        # 40-60%
    LOW = "low"              # 20-40%
    VERY_LOW = "very_low"    # <20%

class MitigationStrategy(Enum):
    """Types of risk mitigation strategies."""
    AVOID = "avoid"
    MITIGATE = "mitigate"
    TRANSFER = "transfer"
    ACCEPT = "accept"
    MONITOR = "monitor"

class RiskMitigationAgent(BaseAgent):
    """Production-ready agent for comprehensive risk assessment and mitigation planning."""

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Enhanced validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': [
                    'project_details', 'identified_risks'
                ],
                'field_types': {
                    'project_details': 'object',
                    'identified_risks': 'array',
                    'risk_tolerance': 'string',
                    'budget_constraints': 'object',
                    'timeline_constraints': 'object'
                },
                'field_constraints': {
                    'risk_tolerance': {'enum': [s.value for s in RiskSeverity]}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Risk assessment templates
        self.risk_templates = {
            'technical': {
                'impact_multiplier': 0.8,
                'typical_mitigation_cost': 0.15,
                'resolution_time_weeks': 4
            },
            'financial': {
                'impact_multiplier': 1.0,
                'typical_mitigation_cost': 0.05,
                'resolution_time_weeks': 2
            },
            'operational': {
                'impact_multiplier': 0.7,
                'typical_mitigation_cost': 0.10,
                'resolution_time_weeks': 6
            },
            'market': {
                'impact_multiplier': 0.9,
                'typical_mitigation_cost': 0.20,
                'resolution_time_weeks': 12
            }
        }
        
        # Probability mappings
        self.probability_values = {
            'very_high': 0.9,
            'high': 0.7,
            'medium': 0.5,
            'low': 0.3,
            'very_low': 0.1
        }

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Enhanced validation for risk mitigation inputs."""
        errors = []
        
        # Validate project details
        project_details = inputs.get('project_details', {})
        if not isinstance(project_details, dict):
            errors.append("Project details must be an object")
        else:
            required_project_fields = ['budget', 'timeline_months', 'expected_value']
            for field in required_project_fields:
                if field not in project_details:
                    errors.append(f"Project details missing required field: {field}")
                elif not isinstance(project_details[field], (int, float)):
                    errors.append(f"Project details field '{field}' must be numeric")
        
        # Validate identified risks
        risks = inputs.get('identified_risks', [])
        if not isinstance(risks, list):
            errors.append("Identified risks must be an array")
        elif not risks:
            errors.append("At least one risk must be identified")
        else:
            for i, risk in enumerate(risks):
                if not isinstance(risk, dict):
                    errors.append(f"Risk {i} must be an object")
                    continue
                
                required_risk_fields = ['name', 'category', 'probability', 'impact']
                for field in required_risk_fields:
                    if field not in risk:
                        errors.append(f"Risk {i} missing required field: {field}")
        
        return errors

    def _assess_risk_impact(self, risk: Dict[str, Any], 
                          project_value: float) -> Dict[str, float]:
        """Assess the quantitative impact of a risk."""
        probability_str = risk.get('probability', 'medium')
        impact_description = risk.get('impact', {})
        category = risk.get('category', 'operational')
        
        # Get probability value
        probability = self.probability_values.get(probability_str, 0.5)
        
        # Calculate financial impact
        if isinstance(impact_description, dict):
            financial_impact = impact_description.get('financial_loss', project_value * 0.1)
            schedule_delay_weeks = impact_description.get('schedule_delay_weeks', 2)
            quality_impact_percent = impact_description.get('quality_impact_percent', 5)
        else:
            # Default impacts based on category
            template = self.risk_templates.get(category, self.risk_templates['operational'])
            financial_impact = project_value * template['impact_multiplier'] * 0.1
            schedule_delay_weeks = template['resolution_time_weeks']
            quality_impact_percent = 10
        
        # Calculate expected value of risk
        expected_financial_loss = financial_impact * probability
        expected_schedule_impact = schedule_delay_weeks * probability
        
        return {
            'probability': probability,
            'financial_impact': financial_impact,
            'expected_financial_loss': expected_financial_loss,
            'schedule_delay_weeks': schedule_delay_weeks,
            'expected_schedule_impact': expected_schedule_impact,
            'quality_impact_percent': quality_impact_percent
        }

    def _determine_mitigation_strategy(self, risk: Dict[str, Any], 
                                     impact_assessment: Dict[str, float],
                                     risk_tolerance: str) -> Dict[str, Any]:
        """Determine the optimal mitigation strategy for a risk."""
        probability = impact_assessment['probability']
        financial_impact = impact_assessment['financial_impact']
        category = risk.get('category', 'operational')
        
        # Risk score calculation
        risk_score = probability * financial_impact
        
        # Strategy selection based on risk score and tolerance
        tolerance_thresholds = {
            'critical': {'avoid': 10000, 'mitigate': 5000, 'transfer': 2000},
            'high': {'avoid': 50000, 'mitigate': 20000, 'transfer': 8000},
            'medium': {'avoid': 100000, 'mitigate': 40000, 'transfer': 15000},
            'low': {'avoid': 200000, 'mitigate': 80000, 'transfer': 30000}
        }
        
        thresholds = tolerance_thresholds.get(risk_tolerance, tolerance_thresholds['medium'])
        
        if risk_score >= thresholds['avoid']:
            strategy = MitigationStrategy.AVOID
        elif risk_score >= thresholds['mitigate']:
            strategy = MitigationStrategy.MITIGATE
        elif risk_score >= thresholds['transfer']:
            strategy = MitigationStrategy.TRANSFER
        else:
            strategy = MitigationStrategy.ACCEPT
        
        # Calculate mitigation cost
        template = self.risk_templates.get(category, self.risk_templates['operational'])
        mitigation_cost = financial_impact * template['typical_mitigation_cost']
        
        # Cost-benefit analysis
        risk_reduction = self._get_strategy_effectiveness(strategy)
        cost_benefit_ratio = (financial_impact * probability * risk_reduction) / max(mitigation_cost, 1)
        
        return {
            'strategy': strategy.value,
            'mitigation_cost': mitigation_cost,
            'risk_reduction_percent': risk_reduction * 100,
            'cost_benefit_ratio': cost_benefit_ratio,
            'implementation_time_weeks': template['resolution_time_weeks'],
            'residual_risk_score': risk_score * (1 - risk_reduction)
        }

    def _get_strategy_effectiveness(self, strategy: MitigationStrategy) -> float:
        """Get the effectiveness of a mitigation strategy."""
        effectiveness_map = {
            MitigationStrategy.AVOID: 0.95,
            MitigationStrategy.MITIGATE: 0.75,
            MitigationStrategy.TRANSFER: 0.85,
            MitigationStrategy.ACCEPT: 0.0,
            MitigationStrategy.MONITOR: 0.10
        }
        return effectiveness_map.get(strategy, 0.5)

    def _generate_mitigation_actions(self, risk: Dict[str, Any], 
                                   strategy: Dict[str, Any]) -> List[str]:
        """Generate specific mitigation actions based on risk and strategy."""
        actions = []
        risk_name = risk.get('name', 'Unknown Risk')
        category = risk.get('category', 'operational')
        strategy_type = strategy['strategy']
        
        # Category-specific action templates
        action_templates = {
            'technical': {
                'avoid': [f"Redesign system architecture to eliminate {risk_name}",
                         "Use proven technologies instead of experimental ones"],
                'mitigate': [f"Implement robust testing for {risk_name}",
                           "Create technical contingency plans",
                           "Establish code review processes"],
                'transfer': [f"Outsource {risk_name} management to specialists",
                           "Purchase technical insurance coverage"]
            },
            'financial': {
                'avoid': [f"Restructure project to avoid {risk_name}",
                         "Secure fixed-price contracts"],
                'mitigate': [f"Establish financial controls for {risk_name}",
                           "Create budget reserves",
                           "Implement cost monitoring systems"],
                'transfer': [f"Purchase insurance for {risk_name}",
                           "Use financial hedging instruments"]
            }
        }
        
        # Get category-specific actions or defaults
        category_actions = action_templates.get(category, action_templates['technical'])
        strategy_actions = category_actions.get(strategy_type, [f"Monitor and manage {risk_name}"])
        
        actions.extend(strategy_actions)
        
        # Add general monitoring actions
        if strategy_type != 'avoid':
            actions.append(f"Establish regular monitoring for {risk_name}")
            actions.append(f"Define escalation procedures for {risk_name}")
        
        return actions

    def _calculate_overall_risk_profile(self, risk_assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall project risk profile."""
        if not risk_assessments:
            return {}
        
        total_expected_loss = sum(r['impact_assessment']['expected_financial_loss'] for r in risk_assessments)
        total_mitigation_cost = sum(r['mitigation_plan']['mitigation_cost'] for r in risk_assessments)
        
        # Risk distribution by category
        category_risks = {}
        for assessment in risk_assessments:
            category = assessment['risk']['category']
            if category not in category_risks:
                category_risks[category] = {'count': 0, 'total_impact': 0}
            category_risks[category]['count'] += 1
            category_risks[category]['total_impact'] += assessment['impact_assessment']['expected_financial_loss']
        
        # Overall risk level
        if total_expected_loss > 100000:
            overall_risk_level = RiskSeverity.CRITICAL
        elif total_expected_loss > 50000:
            overall_risk_level = RiskSeverity.HIGH
        elif total_expected_loss > 20000:
            overall_risk_level = RiskSeverity.MEDIUM
        else:
            overall_risk_level = RiskSeverity.LOW
        
        return {
            'total_expected_loss': total_expected_loss,
            'total_mitigation_cost': total_mitigation_cost,
            'net_risk_exposure': total_expected_loss - total_mitigation_cost,
            'risk_distribution': category_risks,
            'overall_risk_level': overall_risk_level.value,
            'risk_count': len(risk_assessments),
            'mitigation_roi': (total_expected_loss / max(total_mitigation_cost, 1)) if total_mitigation_cost > 0 else 0
        }

    def _calculate_confidence_level(self, inputs: Dict[str, Any], 
                                  risk_assessments: List[Dict[str, Any]]) -> float:
        """Calculate confidence level for the risk analysis."""
        confidence_factors = []
        
        # Data completeness factor
        risks = inputs.get('identified_risks', [])
        complete_risks = sum(1 for risk in risks 
                           if all(field in risk for field in ['name', 'category', 'probability', 'impact']))
        data_completeness = complete_risks / len(risks) if risks else 0
        confidence_factors.append(data_completeness * 0.4)
        
        # Risk assessment depth factor
        detailed_assessments = sum(1 for assessment in risk_assessments 
                                 if isinstance(assessment.get('risk', {}).get('impact'), dict))
        assessment_depth = detailed_assessments / len(risk_assessments) if risk_assessments else 0
        confidence_factors.append(assessment_depth * 0.3)
        
        # Mitigation planning factor
        actionable_plans = sum(1 for assessment in risk_assessments 
                             if len(assessment.get('mitigation_plan', {}).get('actions', [])) > 0)
        planning_quality = actionable_plans / len(risk_assessments) if risk_assessments else 0
        confidence_factors.append(planning_quality * 0.3)
        
        return sum(confidence_factors)

    def _generate_recommendations(self, risk_profile: Dict[str, Any], 
                                risk_assessments: List[Dict[str, Any]]) -> List[str]:
        """Generate strategic recommendations for risk management."""
        recommendations = []
        
        overall_risk = risk_profile.get('overall_risk_level', 'medium')
        total_expected_loss = risk_profile.get('total_expected_loss', 0)
        mitigation_roi = risk_profile.get('mitigation_roi', 0)
        
        # Overall risk recommendations
        if overall_risk == 'critical':
            recommendations.append("CRITICAL: Project faces significant risk exposure. Consider project restructuring or additional safeguards.")
        elif overall_risk == 'high':
            recommendations.append("HIGH RISK: Implement comprehensive risk management program with regular monitoring.")
        
        # ROI-based recommendations
        if mitigation_roi > 3:
            recommendations.append("Strong ROI for risk mitigation. Implement all recommended mitigation strategies.")
        elif mitigation_roi < 1:
            recommendations.append("Low ROI for some mitigation strategies. Prioritize high-impact, low-cost mitigations.")
        
        # Category-specific recommendations
        risk_distribution = risk_profile.get('risk_distribution', {})
        highest_category = max(risk_distribution.items(), key=lambda x: x[1]['total_impact'], default=(None, {}))[0]
        if highest_category:
            recommendations.append(f"Focus risk management efforts on {highest_category} risks - highest impact category.")
        
        # Top risk recommendations
        high_impact_risks = [r for r in risk_assessments 
                           if r['impact_assessment']['expected_financial_loss'] > total_expected_loss * 0.3]
        if high_impact_risks:
            top_risk = high_impact_risks[0]['risk']['name']
            recommendations.append(f"Prioritize mitigation of '{top_risk}' - highest expected impact.")
        
        recommendations.append("Establish monthly risk review meetings and update assessments quarterly.")
        recommendations.append("Create risk escalation procedures and communication protocols.")
        
        return recommendations

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Execute comprehensive risk mitigation analysis."""
        start_time = time.monotonic()
        
        try:
            logger.info(f"Starting risk mitigation analysis for agent {self.agent_id}")
            
            # Validate inputs
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": f"Validation failed: {validation_result.errors[0]}"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Extract inputs
            project_details = inputs['project_details']
            identified_risks = inputs['identified_risks']
            risk_tolerance = inputs.get('risk_tolerance', 'medium')
            
            # Perform risk assessments
            risk_assessments = []
            project_value = project_details.get('expected_value', 100000)
            
            for risk in identified_risks:
                # Assess impact
                impact_assessment = self._assess_risk_impact(risk, project_value)
                
                # Determine mitigation strategy
                mitigation_plan = self._determine_mitigation_strategy(
                    risk, impact_assessment, risk_tolerance
                )
                
                # Generate specific actions
                mitigation_actions = self._generate_mitigation_actions(risk, mitigation_plan)
                mitigation_plan['actions'] = mitigation_actions
                
                risk_assessments.append({
                    'risk': risk,
                    'impact_assessment': impact_assessment,
                    'mitigation_plan': mitigation_plan
                })
            
            # Calculate overall risk profile
            risk_profile = self._calculate_overall_risk_profile(risk_assessments)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(inputs, risk_assessments)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(risk_profile, risk_assessments)
            
            # Prepare response data
            response_data = {
                'project_details': project_details,
                'risk_assessments': risk_assessments,
                'overall_risk_profile': risk_profile,
                'confidence_level': confidence_level,
                'recommendations': recommendations,
                'summary': {
                    'total_risks_identified': len(identified_risks),
                    'overall_risk_level': risk_profile.get('overall_risk_level', 'unknown'),
                    'total_expected_loss': risk_profile.get('total_expected_loss', 0),
                    'total_mitigation_cost': risk_profile.get('total_mitigation_cost', 0),
                    'net_risk_exposure': risk_profile.get('net_risk_exposure', 0),
                    'confidence_score': confidence_level
                }
            }
            
            # Store in MCP memory
            await self._store_analysis_results(response_data)
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"Risk mitigation analysis completed in {execution_time_ms}ms")
            
            return AgentResult(
                status=AgentStatus.SUCCESS,
                data=response_data,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"Risk mitigation analysis failed: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Analysis failed: {str(e)}"},
                execution_time_ms=execution_time_ms
            )

    async def _store_analysis_results(self, analysis_data: Dict[str, Any]) -> None:
        """Store analysis results in MCP episodic memory."""
        try:
            memory_entry = KnowledgeEntity(
                entity_id=f"risk_mitigation_analysis_{int(time.time())}",
                entity_type="risk_mitigation_analysis",
                attributes={
                    "agent_id": self.agent_id,
                    "total_risks": analysis_data['summary']['total_risks_identified'],
                    "risk_level": analysis_data['summary']['overall_risk_level'],
                    "expected_loss": analysis_data['summary']['total_expected_loss'],
                    "mitigation_cost": analysis_data['summary']['total_mitigation_cost'],
                    "confidence_level": analysis_data['confidence_level'],
                    "timestamp": time.time()
                },
                content=f"Risk mitigation analysis: {analysis_data['summary']['total_risks_identified']} risks, "
                       f"{analysis_data['summary']['overall_risk_level']} level, "
                       f"${analysis_data['summary']['total_expected_loss']:,.2f} expected loss"
            )
            
            await self.mcp_client.store_memory(memory_entry)
            logger.info("Risk mitigation analysis results stored in MCP memory")
            
        except Exception as e:
            logger.error(f"Failed to store risk mitigation analysis in MCP memory: {e}")
