"""
Sensitivity Analysis Agent

This agent performs what-if analysis on financial models by varying input parameters
to assess risk, uncertainty, and model sensitivity across different scenarios.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import statistics

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.utils.calculations import (
    calculate_roi_metrics,
    calculate_confidence_score,
    calculate_volatility,
    calculate_risk_score,
    classify_risk_level,
    RiskLevel,
    detect_outliers_iqr,
    safe_divide
)
from memory.types import KnowledgeEntity

logger = logging.getLogger(__name__)

class SensitivityType(Enum):
    """Types of sensitivity analysis."""
    SINGLE_VARIABLE = "single_variable"
    MULTI_VARIABLE = "multi_variable"
    SCENARIO_ANALYSIS = "scenario_analysis"
    MONTE_CARLO = "monte_carlo"

class SensitivityAnalysisAgent(BaseAgent):
    """Production-ready agent for comprehensive sensitivity analysis and risk assessment."""

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Enhanced validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': [
                    'base_scenario', 'sensitivity_variables', 'analysis_type'
                ],
                'field_types': {
                    'base_scenario': 'object',
                    'sensitivity_variables': 'array',
                    'analysis_type': 'string',
                    'confidence_interval': 'number',
                    'scenario_count': 'integer',
                    'risk_tolerance': 'string'
                },
                'field_constraints': {
                    'confidence_interval': {'min': 0.01, 'max': 0.99},
                    'scenario_count': {'min': 10, 'max': 10000},
                    'analysis_type': {'enum': [t.value for t in SensitivityType]},
                    'risk_tolerance': {'enum': [r.value for r in RiskLevel]}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Analysis templates for different variable types
        self.variable_templates = {
            'revenue': {'volatility': 0.15, 'correlation': 0.8},
            'costs': {'volatility': 0.10, 'correlation': -0.6},
            'market_size': {'volatility': 0.20, 'correlation': 0.7},
            'adoption_rate': {'volatility': 0.25, 'correlation': 0.5},
            'pricing': {'volatility': 0.12, 'correlation': 0.9}
        }

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Enhanced validation for sensitivity analysis inputs."""
        errors = []
        
        # Validate base scenario structure
        base_scenario = inputs.get('base_scenario', {})
        required_base_fields = ['investment', 'annual_benefits', 'time_horizon']
        for field in required_base_fields:
            if field not in base_scenario:
                errors.append(f"Base scenario missing required field: {field}")
            elif not isinstance(base_scenario[field], (int, float)):
                errors.append(f"Base scenario field '{field}' must be numeric")
        
        # Validate sensitivity variables
        variables = inputs.get('sensitivity_variables', [])
        if not variables:
            errors.append("At least one sensitivity variable must be specified")
        
        for i, var in enumerate(variables):
            if not isinstance(var, dict):
                errors.append(f"Sensitivity variable {i} must be an object")
                continue
            
            required_var_fields = ['name', 'base_value', 'range_min', 'range_max']
            for field in required_var_fields:
                if field not in var:
                    errors.append(f"Variable {i} missing required field: {field}")
        
        return errors

    def _calculate_base_metrics(self, scenario: Dict[str, Any]) -> Dict[str, float]:
        """Calculate base financial metrics for a scenario."""
        investment = scenario['investment']
        annual_benefits = scenario['annual_benefits']
        time_horizon = scenario['time_horizon']
        
        # Basic ROI calculations
        total_benefits = annual_benefits * time_horizon
        net_benefit = total_benefits - investment
        roi_percentage = (net_benefit / investment) * 100 if investment > 0 else 0
        payback_period = investment / annual_benefits if annual_benefits > 0 else float('inf')
        
        # NPV calculation with 10% discount rate
        discount_rate = 0.10
        npv = -investment + sum(annual_benefits / ((1 + discount_rate) ** year) 
                              for year in range(1, int(time_horizon) + 1))
        
        return {
            'roi_percentage': roi_percentage,
            'net_benefit': net_benefit,
            'payback_period': payback_period,
            'npv': npv,
            'total_benefits': total_benefits
        }

    def _perform_single_variable_analysis(self, base_scenario: Dict[str, Any], 
                                        variables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform single-variable sensitivity analysis."""
        results = {}
        base_metrics = self._calculate_base_metrics(base_scenario)
        
        for variable in variables:
            var_name = variable['name']
            base_value = variable['base_value']
            range_min = variable['range_min']
            range_max = variable['range_max']
            
            # Test points across the range
            test_points = []
            scenarios = []
            
            for factor in [0.5, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5]:
                test_value = base_value * factor
                if range_min <= test_value <= range_max:
                    test_scenario = base_scenario.copy()
                    
                    # Apply variable change based on type
                    if var_name in ['revenue', 'annual_benefits']:
                        test_scenario['annual_benefits'] = test_value
                    elif var_name in ['costs', 'investment']:
                        test_scenario['investment'] = test_value
                    elif var_name == 'time_horizon':
                        test_scenario['time_horizon'] = max(1, int(test_value))
                    
                    metrics = self._calculate_base_metrics(test_scenario)
                    test_points.append(factor)
                    scenarios.append(metrics)
            
            # Calculate sensitivity metrics
            roi_values = [s['roi_percentage'] for s in scenarios]
            roi_range = max(roi_values) - min(roi_values) if roi_values else 0
            roi_std = statistics.stdev(roi_values) if len(roi_values) > 1 else 0
            
            results[var_name] = {
                'base_value': base_value,
                'test_points': test_points,
                'scenarios': scenarios,
                'roi_range': roi_range,
                'roi_volatility': roi_std,
                'sensitivity_score': safe_divide(roi_range, abs(base_metrics['roi_percentage']))
            }
        
        return results

    def _assess_risk_level(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall risk level based on sensitivity analysis."""
        # Extract sensitivity scores and volatilities
        sensitivities = []
        volatilities = []
        
        for var_name, results in analysis_results.items():
            if isinstance(results, dict) and 'sensitivity_score' in results:
                sensitivities.append(results['sensitivity_score'])
                volatilities.append(results.get('roi_volatility', 0))
        
        if not sensitivities:
            return {
                'overall_risk_level': RiskLevel.LOW.value,
                'average_sensitivity': 0,
                'maximum_sensitivity': 0,
                'average_volatility': 0,
                'risk_factors': []
            }
        
        # Use shared utility functions for calculations
        avg_sensitivity = statistics.mean(sensitivities)
        max_sensitivity = max(sensitivities)
        avg_volatility = calculate_volatility(volatilities) if len(volatilities) > 1 else statistics.mean(volatilities)
        
        # Calculate composite risk score (weighted combination)
        risk_score = calculate_risk_score(
            probability=min(1.0, max_sensitivity / 2.0),  # Normalize to 0-1
            impact=min(100.0, avg_volatility)  # Impact on scale of 0-100
        )
        
        # Use shared risk classification with custom thresholds
        custom_thresholds = {
            'critical': 40.0,  # max_sensitivity > 2.0 or avg_volatility > 50
            'high': 25.0,      # max_sensitivity > 1.0 or avg_volatility > 25  
            'medium': 10.0,    # max_sensitivity > 0.5 or avg_volatility > 10
            'low': 5.0
        }
        risk_level = classify_risk_level(risk_score, custom_thresholds)
        
        return {
            'overall_risk_level': risk_level.value,
            'average_sensitivity': avg_sensitivity,
            'maximum_sensitivity': max_sensitivity,
            'average_volatility': avg_volatility,
            'composite_risk_score': risk_score,
            'risk_factors': [
                var for var, res in analysis_results.items() 
                if isinstance(res, dict) and res.get('sensitivity_score', 0) > 1.0
            ]
        }

    def _calculate_confidence_level(self, inputs: Dict[str, Any], 
                                  analysis_results: Dict[str, Any]) -> float:
        """Calculate confidence level for the analysis using shared utilities."""
        # Extract data quality metrics
        variables = inputs.get('sensitivity_variables', [])
        complete_vars = sum(1 for var in variables 
                          if isinstance(var, dict) and 
                          all(key in var for key in ['name', 'min_value', 'max_value']))
        
        # Calculate data completeness ratio
        data_quality = safe_divide(complete_vars, len(variables), 0.0) if variables else 0.0
        
        # Calculate variance from sensitivity scores
        sensitivities = [
            res.get('sensitivity_score', 0) 
            for res in analysis_results.values() 
            if isinstance(res, dict)
        ]
        variance = calculate_volatility(sensitivities) if len(sensitivities) > 1 else 0.1
        
        # Use shared confidence calculation
        return calculate_confidence_score(
            data_quality=data_quality,
            sample_size=len(variables),
            variance=min(1.0, variance)  # Cap variance at 1.0
        )

    def _generate_recommendations(self, analysis_results: Dict[str, Any], 
                                risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        risk_level = risk_assessment['overall_risk_level']
        risk_factors = risk_assessment.get('risk_factors', [])
        
        if risk_level in ['critical', 'high']:
            recommendations.append(
                f"HIGH RISK: Project shows {risk_level} sensitivity. Consider risk mitigation strategies."
            )
            
            if risk_factors:
                recommendations.append(
                    f"Focus risk management on: {', '.join(risk_factors)}"
                )
        
        # Variable-specific recommendations
        for var_name, results in analysis_results.items():
            if isinstance(results, dict):
                sensitivity = results.get('sensitivity_score', 0)
                if sensitivity > 1.5:
                    recommendations.append(
                        f"Monitor {var_name} closely - high impact variable (sensitivity: {sensitivity:.2f})"
                    )
                elif sensitivity > 0.8:
                    recommendations.append(
                        f"Validate assumptions for {var_name} - moderate impact variable"
                    )
        
        # General recommendations
        if risk_level == 'low':
            recommendations.append("Project shows low sensitivity. Consider optimization opportunities.")
        
        recommendations.append("Conduct regular sensitivity updates as market conditions change.")
        
        return recommendations

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Execute comprehensive sensitivity analysis."""
        start_time = time.monotonic()
        
        try:
            logger.info(f"Starting sensitivity analysis for agent {self.agent_id}")
            
            # Validate inputs
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": f"Validation failed: {validation_result.errors[0]}"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Extract inputs
            base_scenario = inputs['base_scenario']
            sensitivity_variables = inputs['sensitivity_variables']
            analysis_type = inputs.get('analysis_type', SensitivityType.SINGLE_VARIABLE.value)
            
            # Perform sensitivity analysis
            if analysis_type == SensitivityType.SINGLE_VARIABLE.value:
                analysis_results = self._perform_single_variable_analysis(
                    base_scenario, sensitivity_variables
                )
            else:
                # Placeholder for other analysis types
                analysis_results = self._perform_single_variable_analysis(
                    base_scenario, sensitivity_variables
                )
            
            # Risk assessment
            risk_assessment = self._assess_risk_level(analysis_results)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(inputs, analysis_results)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(analysis_results, risk_assessment)
            
            # Prepare response data
            response_data = {
                'analysis_type': analysis_type,
                'base_scenario': base_scenario,
                'sensitivity_results': analysis_results,
                'risk_assessment': risk_assessment,
                'confidence_level': confidence_level,
                'recommendations': recommendations,
                'summary': {
                    'variables_analyzed': len(sensitivity_variables),
                    'overall_risk': risk_assessment['overall_risk_level'],
                    'confidence_score': confidence_level,
                    'key_risk_factors': risk_assessment.get('risk_factors', [])
                }
            }
            
            # Store in MCP memory
            await self._store_analysis_results(response_data)
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"Sensitivity analysis completed in {execution_time_ms}ms")
            
            return AgentResult(
                status=AgentStatus.SUCCESS,
                data=response_data,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"Sensitivity analysis failed: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Analysis failed: {str(e)}"},
                execution_time_ms=execution_time_ms
            )

    async def _store_analysis_results(self, analysis_data: Dict[str, Any]) -> None:
        """Store analysis results in MCP episodic memory."""
        try:
            memory_entry = KnowledgeEntity(
                entity_id=f"sensitivity_analysis_{int(time.time())}",
                entity_type="sensitivity_analysis",
                attributes={
                    "agent_id": self.agent_id,
                    "analysis_type": analysis_data['analysis_type'],
                    "risk_level": analysis_data['risk_assessment']['overall_risk_level'],
                    "confidence_level": analysis_data['confidence_level'],
                    "variables_count": analysis_data['summary']['variables_analyzed'],
                    "timestamp": time.time()
                },
                content=f"Sensitivity analysis results: {analysis_data['summary']['overall_risk']} risk, "
                       f"{analysis_data['summary']['confidence_score']:.2f} confidence"
            )
            
            await self.mcp_client.store_memory(memory_entry)
            logger.info("Sensitivity analysis results stored in MCP memory")
            
        except Exception as e:
            logger.error(f"Failed to store sensitivity analysis in MCP memory: {e}")
