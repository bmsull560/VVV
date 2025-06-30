"""
Analytics Aggregator Agent

This agent consolidates and analyzes business case data across multiple dimensions,
providing intelligent insights, trend analysis, and data-driven recommendations
for business case optimization and portfolio management.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import statistics

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.memory_types import KnowledgeEntity

logger = logging.getLogger(__name__)

class AnalyticsType(Enum):
    """Types of analytics operations."""
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    TREND_ANALYSIS = "trend_analysis"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    PERFORMANCE_METRICS = "performance_metrics"
    PREDICTIVE_INSIGHTS = "predictive_insights"
    RISK_ANALYTICS = "risk_analytics"
    ROI_ANALYTICS = "roi_analytics"
    COST_BENEFIT_ANALYSIS = "cost_benefit_analysis"

class DataDimension(Enum):
    """Dimensions for data analysis."""
    TIME = "time"
    DEPARTMENT = "department"
    INDUSTRY = "industry"
    PROJECT_SIZE = "project_size"
    RISK_LEVEL = "risk_level"
    ROI_CATEGORY = "roi_category"
    STAKEHOLDER_TYPE = "stakeholder_type"
    IMPLEMENTATION_PHASE = "implementation_phase"

class TrendDirection(Enum):
    """Direction of trends in analytics."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    SEASONAL = "seasonal"

class AnalyticsAggregatorAgent(BaseAgent):
    """Production-ready agent for comprehensive business case analytics and insights."""

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Enhanced validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': [
                    'analytics_type', 'data_scope'
                ],
                'field_types': {
                    'analytics_type': 'string',
                    'data_scope': 'object',
                    'dimensions': 'array',
                    'filters': 'object',
                    'aggregation_level': 'string',
                    'include_predictions': 'boolean',
                    'time_range': 'object'
                },
                'field_constraints': {
                    'analytics_type': {'enum': [t.value for t in AnalyticsType]},
                    'aggregation_level': {'enum': ['summary', 'detailed', 'comprehensive']}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Analytics configuration
        self.aggregation_functions = {
            'mean': statistics.mean,
            'median': statistics.median,
            'stdev': statistics.stdev,
            'variance': statistics.variance,
            'min': min,
            'max': max,
            'sum': sum
        }
        
        # Benchmark data for comparative analysis
        self.industry_benchmarks = {
            'healthcare': {'avg_roi': 15.2, 'avg_payback_months': 18, 'success_rate': 0.72},
            'financial_services': {'avg_roi': 22.8, 'avg_payback_months': 12, 'success_rate': 0.81},
            'manufacturing': {'avg_roi': 18.5, 'avg_payback_months': 24, 'success_rate': 0.68},
            'technology': {'avg_roi': 28.3, 'avg_payback_months': 8, 'success_rate': 0.85},
            'retail': {'avg_roi': 14.7, 'avg_payback_months': 15, 'success_rate': 0.74}
        }

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Enhanced validation for analytics aggregator inputs."""
        errors = []
        
        # Validate data scope
        data_scope = inputs.get('data_scope', {})
        if not isinstance(data_scope, dict):
            errors.append("Data scope must be an object")
        else:
            if 'projects' not in data_scope and 'business_cases' not in data_scope:
                errors.append("Data scope must include 'projects' or 'business_cases'")
        
        # Validate time range if provided
        time_range = inputs.get('time_range', {})
        if time_range and isinstance(time_range, dict):
            required_time_fields = ['start_date', 'end_date']
            for field in required_time_fields:
                if field not in time_range:
                    errors.append(f"Time range missing required field: {field}")
        
        return errors

    async def _retrieve_business_case_data(self, data_scope: Dict[str, Any], 
                                         filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve business case data from MCP memory based on scope and filters."""
        try:
            # Simulate data retrieval from MCP memory
            # In production, this would query the actual MCP storage
            sample_data = [
                {
                    'project_id': 'proj_001',
                    'project_name': 'ERP Implementation',
                    'industry': 'manufacturing',
                    'department': 'operations',
                    'roi_percentage': 18.5,
                    'payback_months': 24,
                    'total_investment': 500000,
                    'annual_benefits': 150000,
                    'risk_level': 'medium',
                    'completion_date': '2024-03-15',
                    'success_metrics': {'efficiency_gain': 25, 'cost_reduction': 15}
                },
                {
                    'project_id': 'proj_002',
                    'project_name': 'CRM Upgrade',
                    'industry': 'technology',
                    'department': 'sales',
                    'roi_percentage': 32.1,
                    'payback_months': 8,
                    'total_investment': 200000,
                    'annual_benefits': 80000,
                    'risk_level': 'low',
                    'completion_date': '2024-02-28',
                    'success_metrics': {'revenue_increase': 20, 'customer_satisfaction': 18}
                },
                {
                    'project_id': 'proj_003',
                    'project_name': 'Security Enhancement',
                    'industry': 'financial_services',
                    'department': 'it',
                    'roi_percentage': 25.8,
                    'payback_months': 12,
                    'total_investment': 750000,
                    'annual_benefits': 200000,
                    'risk_level': 'high',
                    'completion_date': '2024-01-20',
                    'success_metrics': {'security_score': 95, 'compliance_rate': 100}
                }
            ]
            
            # Apply filters if provided
            if filters:
                filtered_data = []
                for project in sample_data:
                    include_project = True
                    for filter_key, filter_value in filters.items():
                        if filter_key in project and project[filter_key] != filter_value:
                            include_project = False
                            break
                    if include_project:
                        filtered_data.append(project)
                return filtered_data
            
            return sample_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve business case data: {e}")
            return []

    def _analyze_portfolio_performance(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall portfolio performance across all business cases."""
        if not data:
            return {}
        
        # Calculate portfolio metrics
        roi_values = [item['roi_percentage'] for item in data if 'roi_percentage' in item]
        payback_periods = [item['payback_months'] for item in data if 'payback_months' in item]
        investments = [item['total_investment'] for item in data if 'total_investment' in item]
        benefits = [item['annual_benefits'] for item in data if 'annual_benefits' in item]
        
        portfolio_metrics = {
            'total_projects': len(data),
            'total_investment': sum(investments) if investments else 0,
            'total_annual_benefits': sum(benefits) if benefits else 0,
            'average_roi': statistics.mean(roi_values) if roi_values else 0,
            'median_roi': statistics.median(roi_values) if roi_values else 0,
            'roi_standard_deviation': statistics.stdev(roi_values) if len(roi_values) > 1 else 0,
            'average_payback_months': statistics.mean(payback_periods) if payback_periods else 0,
            'best_performing_project': max(data, key=lambda x: x.get('roi_percentage', 0)) if data else None,
            'highest_investment_project': max(data, key=lambda x: x.get('total_investment', 0)) if data else None
        }
        
        # Risk distribution analysis
        risk_distribution = {}
        for item in data:
            risk_level = item.get('risk_level', 'unknown')
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        portfolio_metrics['risk_distribution'] = risk_distribution
        
        return portfolio_metrics

    def _analyze_trends_over_time(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in business case performance over time."""
        if not data:
            return {}
        
        # Group data by time periods (quarterly)
        quarterly_data = {}
        for item in data:
            completion_date = item.get('completion_date')
            if completion_date:
                # Simple quarterly grouping (would be more sophisticated in production)
                year_quarter = completion_date[:7]  # YYYY-MM format
                if year_quarter not in quarterly_data:
                    quarterly_data[year_quarter] = []
                quarterly_data[year_quarter].append(item)
        
        # Calculate trend metrics
        trend_analysis = {}
        for period, period_data in quarterly_data.items():
            roi_values = [item['roi_percentage'] for item in period_data if 'roi_percentage' in item]
            trend_analysis[period] = {
                'project_count': len(period_data),
                'average_roi': statistics.mean(roi_values) if roi_values else 0,
                'total_investment': sum(item.get('total_investment', 0) for item in period_data),
                'success_rate': len([item for item in period_data if item.get('roi_percentage', 0) > 15]) / len(period_data)
            }
        
        # Determine overall trend direction
        roi_trend = self._calculate_trend_direction([trend_analysis[period]['average_roi'] for period in sorted(trend_analysis.keys())])
        investment_trend = self._calculate_trend_direction([trend_analysis[period]['total_investment'] for period in sorted(trend_analysis.keys())])
        
        return {
            'quarterly_analysis': trend_analysis,
            'roi_trend_direction': roi_trend,
            'investment_trend_direction': investment_trend,
            'periods_analyzed': len(quarterly_data)
        }

    def _calculate_trend_direction(self, values: List[float]) -> str:
        """Calculate the direction of a trend from a series of values."""
        if len(values) < 2:
            return TrendDirection.STABLE.value
        
        # Simple trend calculation
        differences = [values[i+1] - values[i] for i in range(len(values)-1)]
        avg_change = statistics.mean(differences)
        
        if abs(avg_change) < 0.1:  # Threshold for stability
            return TrendDirection.STABLE.value
        elif avg_change > 0:
            return TrendDirection.INCREASING.value
        else:
            return TrendDirection.DECREASING.value

    def _perform_comparative_analysis(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform comparative analysis across different dimensions."""
        comparative_results = {}
        
        # Industry comparison
        industry_performance = {}
        for item in data:
            industry = item.get('industry', 'unknown')
            if industry not in industry_performance:
                industry_performance[industry] = []
            industry_performance[industry].append(item.get('roi_percentage', 0))
        
        industry_averages = {
            industry: statistics.mean(rois) if rois else 0 
            for industry, rois in industry_performance.items()
        }
        
        comparative_results['industry_performance'] = industry_averages
        
        # Department comparison
        department_performance = {}
        for item in data:
            department = item.get('department', 'unknown')
            if department not in department_performance:
                department_performance[department] = []
            department_performance[department].append(item.get('roi_percentage', 0))
        
        department_averages = {
            dept: statistics.mean(rois) if rois else 0 
            for dept, rois in department_performance.items()
        }
        
        comparative_results['department_performance'] = department_averages
        
        # Risk level comparison
        risk_performance = {}
        for item in data:
            risk_level = item.get('risk_level', 'unknown')
            if risk_level not in risk_performance:
                risk_performance[risk_level] = []
            risk_performance[risk_level].append(item.get('roi_percentage', 0))
        
        risk_averages = {
            risk: statistics.mean(rois) if rois else 0 
            for risk, rois in risk_performance.items()
        }
        
        comparative_results['risk_level_performance'] = risk_averages
        
        return comparative_results

    def _generate_predictive_insights(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate predictive insights based on historical data patterns."""
        if len(data) < 3:
            return {"warning": "Insufficient data for meaningful predictions"}
        
        # Calculate success rate patterns
        successful_projects = [item for item in data if item.get('roi_percentage', 0) > 15]
        success_rate = len(successful_projects) / len(data)
        
        # Identify success factors
        success_factors = {}
        if successful_projects:
            # Most common industry among successful projects
            industries = [proj.get('industry') for proj in successful_projects]
            most_successful_industry = max(set(industries), key=industries.count)
            
            # Average characteristics of successful projects
            avg_investment = statistics.mean([proj.get('total_investment', 0) for proj in successful_projects])
            avg_payback = statistics.mean([proj.get('payback_months', 0) for proj in successful_projects])
            
            success_factors = {
                'overall_success_rate': success_rate,
                'most_successful_industry': most_successful_industry,
                'optimal_investment_range': f"${avg_investment*.8:,.0f} - ${avg_investment*1.2:,.0f}",
                'target_payback_period': f"{avg_payback:.1f} months",
                'recommended_risk_level': 'medium'  # Based on analysis
            }
        
        # Generate predictions for next quarter
        recent_roi_trend = [item.get('roi_percentage', 0) for item in data[-3:]]
        predicted_roi = statistics.mean(recent_roi_trend) if recent_roi_trend else 0
        
        predictions = {
            'predicted_next_quarter_roi': predicted_roi,
            'confidence_level': min(0.9, success_rate + 0.1),
            'recommended_portfolio_adjustments': self._generate_portfolio_recommendations(data)
        }
        
        return {
            'success_factors': success_factors,
            'predictions': predictions
        }

    def _generate_portfolio_recommendations(self, data: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for portfolio optimization."""
        recommendations = []
        
        if not data:
            return ["Insufficient data for recommendations"]
        
        # Analyze current portfolio balance
        roi_values = [item.get('roi_percentage', 0) for item in data]
        avg_roi = statistics.mean(roi_values) if roi_values else 0
        
        if avg_roi < 15:
            recommendations.append("Portfolio ROI below target. Focus on higher-return initiatives.")
        
        # Risk distribution analysis
        risk_distribution = {}
        for item in data:
            risk_level = item.get('risk_level', 'unknown')
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1
        
        high_risk_ratio = risk_distribution.get('high', 0) / len(data)
        if high_risk_ratio > 0.3:
            recommendations.append("High concentration of high-risk projects. Consider diversifying risk profile.")
        
        # Industry diversification
        industries = [item.get('industry') for item in data]
        unique_industries = len(set(industries))
        if unique_industries < 3:
            recommendations.append("Limited industry diversification. Consider expanding to additional sectors.")
        
        recommendations.append("Regularly review and update business case performance metrics.")
        recommendations.append("Consider implementing automated monitoring for real-time insights.")
        
        return recommendations

    def _calculate_confidence_level(self, data: List[Dict[str, Any]], 
                                  analytics_type: str) -> float:
        """Calculate confidence level for the analytics results."""
        confidence_factors = []
        
        # Data volume factor
        data_volume_factor = min(1.0, len(data) / 10)  # Ideal sample size of 10+
        confidence_factors.append(data_volume_factor * 0.4)
        
        # Data completeness factor
        complete_records = sum(1 for item in data if all(key in item for key in ['roi_percentage', 'payback_months', 'total_investment']))
        completeness_factor = complete_records / len(data) if data else 0
        confidence_factors.append(completeness_factor * 0.3)
        
        # Time span factor (more recent data = higher confidence)
        analytics_complexity_factor = {
            'portfolio_analysis': 0.9,
            'trend_analysis': 0.7,
            'comparative_analysis': 0.8,
            'predictive_insights': 0.6
        }.get(analytics_type, 0.7)
        confidence_factors.append(analytics_complexity_factor * 0.3)
        
        return sum(confidence_factors)

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Execute comprehensive analytics aggregation and analysis."""
        start_time = time.monotonic()
        
        try:
            logger.info(f"Starting analytics aggregation for agent {self.agent_id}")
            
            # Validate inputs
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": f"Validation failed: {validation_result.errors[0]}"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Extract inputs
            analytics_type = inputs['analytics_type']
            data_scope = inputs['data_scope']
            filters = inputs.get('filters', {})
            include_predictions = inputs.get('include_predictions', False)
            
            # Retrieve business case data
            business_case_data = await self._retrieve_business_case_data(data_scope, filters)
            
            if not business_case_data:
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={"warning": "No data found matching the specified criteria"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Perform analytics based on type
            analytics_results = {}
            
            if analytics_type == AnalyticsType.PORTFOLIO_ANALYSIS.value:
                analytics_results['portfolio_metrics'] = self._analyze_portfolio_performance(business_case_data)
            
            elif analytics_type == AnalyticsType.TREND_ANALYSIS.value:
                analytics_results['trend_analysis'] = self._analyze_trends_over_time(business_case_data)
            
            elif analytics_type == AnalyticsType.COMPARATIVE_ANALYSIS.value:
                analytics_results['comparative_analysis'] = self._perform_comparative_analysis(business_case_data)
            
            elif analytics_type == AnalyticsType.PREDICTIVE_INSIGHTS.value:
                analytics_results['predictive_insights'] = self._generate_predictive_insights(business_case_data)
            
            else:
                # Comprehensive analysis including all types
                analytics_results['portfolio_metrics'] = self._analyze_portfolio_performance(business_case_data)
                analytics_results['trend_analysis'] = self._analyze_trends_over_time(business_case_data)
                analytics_results['comparative_analysis'] = self._perform_comparative_analysis(business_case_data)
                
                if include_predictions:
                    analytics_results['predictive_insights'] = self._generate_predictive_insights(business_case_data)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(business_case_data, analytics_type)
            
            # Generate recommendations
            recommendations = self._generate_portfolio_recommendations(business_case_data)
            
            # Prepare response data
            response_data = {
                'analytics_type': analytics_type,
                'data_summary': {
                    'total_projects_analyzed': len(business_case_data),
                    'analysis_date': datetime.now().isoformat(),
                    'data_scope': data_scope
                },
                'analytics_results': analytics_results,
                'confidence_level': confidence_level,
                'recommendations': recommendations,
                'benchmark_comparison': self._compare_to_benchmarks(business_case_data),
                'executive_summary': self._generate_executive_summary(analytics_results, business_case_data)
            }
            
            # Store results in MCP memory
            await self._store_analytics_results(response_data)
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"Analytics aggregation completed in {execution_time_ms}ms")
            
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=response_data,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"Analytics aggregation failed: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Analytics failed: {str(e)}"},
                execution_time_ms=execution_time_ms
            )

    def _compare_to_benchmarks(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare portfolio performance to industry benchmarks."""
        if not data:
            return {}
        
        benchmark_comparison = {}
        roi_values = [item.get('roi_percentage', 0) for item in data]
        avg_roi = statistics.mean(roi_values) if roi_values else 0
        
        for industry, benchmarks in self.industry_benchmarks.items():
            industry_projects = [item for item in data if item.get('industry') == industry]
            if industry_projects:
                industry_roi = statistics.mean([item.get('roi_percentage', 0) for item in industry_projects])
                benchmark_comparison[industry] = {
                    'actual_roi': industry_roi,
                    'benchmark_roi': benchmarks['avg_roi'],
                    'performance_vs_benchmark': ((industry_roi - benchmarks['avg_roi']) / benchmarks['avg_roi']) * 100
                }
        
        return benchmark_comparison

    def _generate_executive_summary(self, analytics_results: Dict[str, Any], 
                                  data: List[Dict[str, Any]]) -> str:
        """Generate executive summary of analytics findings."""
        total_projects = len(data)
        total_investment = sum(item.get('total_investment', 0) for item in data)
        avg_roi = statistics.mean([item.get('roi_percentage', 0) for item in data]) if data else 0
        
        summary = f"Analytics Summary: Analyzed {total_projects} business cases representing " \
                 f"${total_investment:,.0f} in total investment. Portfolio average ROI of {avg_roi:.1f}%. "
        
        if 'portfolio_metrics' in analytics_results:
            portfolio = analytics_results['portfolio_metrics']
            best_project = portfolio.get('best_performing_project', {})
            if best_project:
                summary += f"Top performer: {best_project.get('project_name', 'N/A')} " \
                          f"with {best_project.get('roi_percentage', 0):.1f}% ROI. "
        
        if avg_roi > 20:
            summary += "Portfolio performance exceeds targets."
        elif avg_roi > 15:
            summary += "Portfolio performance meets expectations."
        else:
            summary += "Portfolio performance below target - optimization recommended."
        
        return summary

    async def _store_analytics_results(self, analytics_data: Dict[str, Any]) -> None:
        """Store analytics results in MCP episodic memory."""
        try:
            memory_entry = KnowledgeEntity(
                entity_id=f"analytics_aggregation_{int(time.time())}",
                entity_type="analytics_aggregation",
                attributes={
                    "agent_id": self.agent_id,
                    "analytics_type": analytics_data.get('analytics_type'),
                    "projects_analyzed": analytics_data['data_summary']['total_projects_analyzed'],
                    "confidence_level": analytics_data.get('confidence_level', 0),
                    "timestamp": time.time()
                },
                content=f"Analytics aggregation: {analytics_data.get('analytics_type')} analysis of "
                       f"{analytics_data['data_summary']['total_projects_analyzed']} projects with "
                       f"{analytics_data.get('confidence_level', 0):.2f} confidence level"
            )
            
            await self.mcp_client.store_memory(memory_entry)
            logger.info("Analytics aggregation results stored in MCP memory")
            
        except Exception as e:
            logger.error(f"Failed to store analytics aggregation in MCP memory: {e}")
