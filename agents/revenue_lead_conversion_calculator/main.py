"""
Revenue Lead Conversion Calculator Agent

This agent analyzes lead generation and conversion processes to quantify revenue opportunities,
optimize conversion funnels, and calculate the financial impact of lead conversion improvements.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from enum import Enum

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.types import KnowledgeEntity

logger = logging.getLogger(__name__)

class LeadSource(Enum):
    """Types of lead sources."""
    ORGANIC_SEARCH = "organic_search"
    PAID_SEARCH = "paid_search"
    SOCIAL_MEDIA = "social_media"
    EMAIL_MARKETING = "email_marketing"
    REFERRALS = "referrals"
    CONTENT_MARKETING = "content_marketing"
    WEBINARS = "webinars"
    EVENTS = "events"
    DIRECT = "direct"
    PARTNERSHIPS = "partnerships"

class ConversionStage(Enum):
    """Stages in the conversion funnel."""
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    INTENT = "intent"
    EVALUATION = "evaluation"
    PURCHASE = "purchase"

class LeadQuality(Enum):
    """Lead quality classifications."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"

class RevenueLeadConversionCalculatorAgent(BaseAgent):
    """Production-ready agent for lead conversion and revenue optimization analysis."""

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Enhanced validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': [
                    'lead_volume', 'conversion_funnel', 'customer_value'
                ],
                'field_types': {
                    'lead_volume': 'object',
                    'conversion_funnel': 'object',
                    'customer_value': 'object',
                    'time_period': 'string',
                    'improvement_scenarios': 'array',
                    'acquisition_costs': 'object'
                },
                'field_constraints': {
                    'time_period': {'enum': ['monthly', 'quarterly', 'annually']}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Conversion benchmarks by industry and lead source
        self.conversion_benchmarks = {
            'organic_search': {'awareness_to_interest': 0.25, 'interest_to_consideration': 0.15, 'consideration_to_purchase': 0.08},
            'paid_search': {'awareness_to_interest': 0.30, 'interest_to_consideration': 0.20, 'consideration_to_purchase': 0.12},
            'social_media': {'awareness_to_interest': 0.15, 'interest_to_consideration': 0.10, 'consideration_to_purchase': 0.05},
            'email_marketing': {'awareness_to_interest': 0.35, 'interest_to_consideration': 0.25, 'consideration_to_purchase': 0.15},
            'referrals': {'awareness_to_interest': 0.45, 'interest_to_consideration': 0.35, 'consideration_to_purchase': 0.25}
        }
        
        # Lead quality multipliers
        self.quality_multipliers = {
            'hot': 2.5,
            'warm': 1.8,
            'qualified': 2.0,
            'cold': 0.6,
            'unqualified': 0.3
        }

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Enhanced validation for lead conversion inputs."""
        errors = []
        
        # Validate lead volume structure
        lead_volume = inputs.get('lead_volume', {})
        if not isinstance(lead_volume, dict):
            errors.append("Lead volume must be an object")
        else:
            required_volume_fields = ['total_leads', 'lead_sources']
            for field in required_volume_fields:
                if field not in lead_volume:
                    errors.append(f"Lead volume missing required field: {field}")
        
        # Validate conversion funnel
        funnel = inputs.get('conversion_funnel', {})
        if not isinstance(funnel, dict):
            errors.append("Conversion funnel must be an object")
        else:
            required_funnel_fields = ['stages', 'conversion_rates']
            for field in required_funnel_fields:
                if field not in funnel:
                    errors.append(f"Conversion funnel missing required field: {field}")
        
        # Validate customer value
        customer_value = inputs.get('customer_value', {})
        if not isinstance(customer_value, dict):
            errors.append("Customer value must be an object")
        else:
            required_value_fields = ['average_deal_size', 'customer_lifetime_value']
            for field in required_value_fields:
                if field not in customer_value:
                    errors.append(f"Customer value missing required field: {field}")
                elif not isinstance(customer_value[field], (int, float)):
                    errors.append(f"Customer value field '{field}' must be numeric")
        
        return errors

    def _calculate_funnel_metrics(self, lead_volume: Dict[str, Any], 
                                funnel: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed funnel conversion metrics."""
        total_leads = lead_volume['total_leads']
        conversion_rates = funnel['conversion_rates']
        
        # Calculate conversions at each stage
        stages = ['awareness', 'interest', 'consideration', 'intent', 'evaluation', 'purchase']
        funnel_data = {'awareness': total_leads}
        
        for i in range(len(stages) - 1):
            current_stage = stages[i]
            next_stage = stages[i + 1]
            conversion_rate = conversion_rates.get(f"{current_stage}_to_{next_stage}", 0.1)
            
            funnel_data[next_stage] = funnel_data[current_stage] * conversion_rate
        
        # Calculate drop-off rates
        dropoff_rates = {}
        for i in range(len(stages) - 1):
            current_stage = stages[i]
            next_stage = stages[i + 1]
            dropoff_rates[f"{current_stage}_dropoff"] = (
                funnel_data[current_stage] - funnel_data[next_stage]
            ) / funnel_data[current_stage] if funnel_data[current_stage] > 0 else 0
        
        return {
            'funnel_volumes': funnel_data,
            'dropoff_rates': dropoff_rates,
            'overall_conversion_rate': funnel_data['purchase'] / total_leads if total_leads > 0 else 0,
            'qualified_leads': funnel_data.get('evaluation', 0),
            'converted_customers': funnel_data['purchase']
        }

    def _analyze_lead_sources(self, lead_volume: Dict[str, Any], 
                            funnel_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance by lead source."""
        lead_sources = lead_volume.get('lead_sources', {})
        source_analysis = {}
        
        for source, volume in lead_sources.items():
            # Apply benchmark conversion rates if available
            benchmark_rates = self.conversion_benchmarks.get(source, {})
            
            # Calculate source-specific conversions
            source_conversions = volume
            for stage_conversion, rate in benchmark_rates.items():
                source_conversions *= rate
            
            # Calculate source efficiency
            efficiency_score = source_conversions / volume if volume > 0 else 0
            
            source_analysis[source] = {
                'lead_volume': volume,
                'estimated_conversions': source_conversions,
                'conversion_efficiency': efficiency_score,
                'benchmark_applied': bool(benchmark_rates),
                'volume_percentage': volume / lead_volume['total_leads'] if lead_volume['total_leads'] > 0 else 0
            }
        
        return source_analysis

    def _calculate_revenue_impact(self, funnel_metrics: Dict[str, Any], 
                                customer_value: Dict[str, Any],
                                time_period: str = 'monthly') -> Dict[str, Any]:
        """Calculate financial impact of lead conversions."""
        converted_customers = funnel_metrics['converted_customers']
        avg_deal_size = customer_value['average_deal_size']
        lifetime_value = customer_value['customer_lifetime_value']
        
        # Time period multipliers
        period_multipliers = {
            'monthly': 1,
            'quarterly': 3,
            'annually': 12
        }
        multiplier = period_multipliers.get(time_period, 1)
        
        # Revenue calculations
        immediate_revenue = converted_customers * avg_deal_size * multiplier
        lifetime_revenue = converted_customers * lifetime_value
        
        # Additional metrics
        revenue_per_lead = immediate_revenue / funnel_metrics.get('funnel_volumes', {}).get('awareness', 1)
        customer_acquisition_cost = 0  # Will be calculated if acquisition costs provided
        
        return {
            'immediate_revenue': immediate_revenue,
            'lifetime_revenue': lifetime_revenue,
            'converted_customers_period': converted_customers * multiplier,
            'revenue_per_lead': revenue_per_lead,
            'average_deal_size': avg_deal_size,
            'customer_lifetime_value': lifetime_value,
            'time_period': time_period
        }

    def _analyze_improvement_scenarios(self, base_metrics: Dict[str, Any],
                                     scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze potential improvement scenarios."""
        scenario_results = {}
        base_revenue = base_metrics['immediate_revenue']
        
        for i, scenario in enumerate(scenarios):
            scenario_name = scenario.get('name', f"Scenario_{i+1}")
            improvements = scenario.get('improvements', {})
            
            # Apply improvements to base metrics
            improved_funnel = base_metrics['funnel_metrics']['funnel_volumes'].copy()
            
            # Apply conversion rate improvements
            for stage_improvement, improvement_rate in improvements.items():
                if stage_improvement in improved_funnel:
                    improved_funnel[stage_improvement] *= (1 + improvement_rate)
            
            # Recalculate revenue impact
            scenario_revenue = improved_funnel.get('purchase', 0) * base_metrics['customer_value']['average_deal_size']
            revenue_increase = scenario_revenue - base_revenue
            improvement_percentage = (revenue_increase / base_revenue * 100) if base_revenue > 0 else 0
            
            scenario_results[scenario_name] = {
                'scenario_revenue': scenario_revenue,
                'revenue_increase': revenue_increase,
                'improvement_percentage': improvement_percentage,
                'improved_conversions': improved_funnel.get('purchase', 0),
                'conversion_improvement': improved_funnel.get('purchase', 0) - base_metrics['funnel_metrics']['converted_customers'],
                'improvements_applied': improvements
            }
        
        return scenario_results

    def _calculate_confidence_level(self, inputs: Dict[str, Any], 
                                  analysis_results: Dict[str, Any]) -> float:
        """Calculate confidence level for the analysis."""
        confidence_factors = []
        
        # Data completeness factor
        required_data = ['lead_volume', 'conversion_funnel', 'customer_value']
        complete_data = sum(1 for field in required_data if field in inputs and inputs[field])
        data_completeness = complete_data / len(required_data)
        confidence_factors.append(data_completeness * 0.4)
        
        # Lead source diversity factor
        lead_sources = inputs.get('lead_volume', {}).get('lead_sources', {})
        source_diversity = min(len(lead_sources) / 5, 1.0) * 0.3
        confidence_factors.append(source_diversity)
        
        # Benchmark alignment factor
        funnel_rates = inputs.get('conversion_funnel', {}).get('conversion_rates', {})
        benchmark_alignment = 0.8 if funnel_rates else 0.5
        confidence_factors.append(benchmark_alignment * 0.3)
        
        return sum(confidence_factors)

    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations for lead conversion optimization."""
        recommendations = []
        
        funnel_metrics = analysis_results['funnel_metrics']
        source_analysis = analysis_results['lead_source_analysis']
        
        # Funnel optimization recommendations
        overall_conversion = funnel_metrics['overall_conversion_rate']
        if overall_conversion < 0.05:
            recommendations.append("CRITICAL: Overall conversion rate is very low (<5%). Focus on lead quality and funnel optimization.")
        elif overall_conversion < 0.10:
            recommendations.append("Conversion rate below industry average. Consider A/B testing landing pages and lead nurturing.")
        
        # Source-specific recommendations
        best_source = max(source_analysis.items(), key=lambda x: x[1]['conversion_efficiency'], default=(None, {}))
        worst_source = min(source_analysis.items(), key=lambda x: x[1]['conversion_efficiency'], default=(None, {}))
        
        if best_source[0] and worst_source[0]:
            recommendations.append(f"Top performing source: {best_source[0]}. Consider increasing investment.")
            recommendations.append(f"Underperforming source: {worst_source[0]}. Needs optimization or budget reallocation.")
        
        # Revenue optimization recommendations
        revenue_impact = analysis_results['revenue_impact']
        if revenue_impact['revenue_per_lead'] < 50:
            recommendations.append("Low revenue per lead. Focus on increasing average deal size or customer lifetime value.")
        
        # General recommendations
        recommendations.append("Implement lead scoring to prioritize high-quality prospects.")
        recommendations.append("Regular funnel analysis and conversion rate optimization should be ongoing.")
        
        return recommendations

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Execute comprehensive lead conversion analysis."""
        start_time = time.monotonic()
        
        try:
            logger.info(f"Starting lead conversion analysis for agent {self.agent_id}")
            
            # Validate inputs
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": f"Validation failed: {validation_result.errors[0]}"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Extract inputs
            lead_volume = inputs['lead_volume']
            conversion_funnel = inputs['conversion_funnel']
            customer_value = inputs['customer_value']
            time_period = inputs.get('time_period', 'monthly')
            improvement_scenarios = inputs.get('improvement_scenarios', [])
            
            # Perform analysis
            funnel_metrics = self._calculate_funnel_metrics(lead_volume, conversion_funnel)
            source_analysis = self._analyze_lead_sources(lead_volume, funnel_metrics)
            revenue_impact = self._calculate_revenue_impact(funnel_metrics, customer_value, time_period)
            
            # Analyze improvement scenarios
            scenario_analysis = {}
            if improvement_scenarios:
                base_metrics = {
                    'funnel_metrics': funnel_metrics,
                    'customer_value': customer_value,
                    'immediate_revenue': revenue_impact['immediate_revenue']
                }
                scenario_analysis = self._analyze_improvement_scenarios(base_metrics, improvement_scenarios)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(inputs, {
                'funnel_metrics': funnel_metrics,
                'source_analysis': source_analysis
            })
            
            # Generate recommendations
            analysis_results = {
                'funnel_metrics': funnel_metrics,
                'lead_source_analysis': source_analysis,
                'revenue_impact': revenue_impact
            }
            recommendations = self._generate_recommendations(analysis_results)
            
            # Prepare response data
            response_data = {
                'funnel_analysis': funnel_metrics,
                'lead_source_performance': source_analysis,
                'revenue_impact': revenue_impact,
                'improvement_scenarios': scenario_analysis,
                'confidence_level': confidence_level,
                'recommendations': recommendations,
                'summary': {
                    'total_leads': lead_volume['total_leads'],
                    'conversion_rate': funnel_metrics['overall_conversion_rate'],
                    'converted_customers': funnel_metrics['converted_customers'],
                    'immediate_revenue': revenue_impact['immediate_revenue'],
                    'revenue_per_lead': revenue_impact['revenue_per_lead'],
                    'confidence_score': confidence_level
                }
            }
            
            # Store in MCP memory
            await self._store_analysis_results(response_data)
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"Lead conversion analysis completed in {execution_time_ms}ms")
            
            return AgentResult(
                status=AgentStatus.SUCCESS,
                data=response_data,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"Lead conversion analysis failed: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Analysis failed: {str(e)}"},
                execution_time_ms=execution_time_ms
            )

    async def _store_analysis_results(self, analysis_data: Dict[str, Any]) -> None:
        """Store analysis results in MCP episodic memory."""
        try:
            memory_entry = KnowledgeEntity(
                entity_id=f"lead_conversion_analysis_{int(time.time())}",
                entity_type="lead_conversion_analysis",
                attributes={
                    "agent_id": self.agent_id,
                    "total_leads": analysis_data['summary']['total_leads'],
                    "conversion_rate": analysis_data['summary']['conversion_rate'],
                    "revenue_impact": analysis_data['summary']['immediate_revenue'],
                    "confidence_level": analysis_data['confidence_level'],
                    "timestamp": time.time()
                },
                content=f"Lead conversion analysis: {analysis_data['summary']['converted_customers']} conversions, "
                       f"${analysis_data['summary']['immediate_revenue']:,.2f} revenue, "
                       f"{analysis_data['summary']['conversion_rate']:.1%} conversion rate"
            )
            
            await self.mcp_client.store_memory(memory_entry)
            logger.info("Lead conversion analysis results stored in MCP memory")
            
        except Exception as e:
            logger.error(f"Failed to store lead conversion analysis in MCP memory: {e}")
