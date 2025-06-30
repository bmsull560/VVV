"""
Value Driver Agent

This agent identifies key business value drivers from unstructured text using a hierarchical model.
It analyzes user inputs to categorize potential business benefits into structured value pillars
with specific metrics for quantitative analysis.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
import re
from enum import Enum
from datetime import datetime
import statistics

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.memory_types import KnowledgeEntity
from agents.utils.validation import validate_comprehensive_input, format_validation_errors

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """Types of value driver analysis."""
    COMPREHENSIVE = "comprehensive"
    FOCUSED = "focused"
    QUICK_SCAN = "quick_scan"
    INDUSTRY_SPECIFIC = "industry_specific"

class ConfidenceLevel(Enum):
    """Confidence level thresholds."""
    HIGH = 0.8
    MEDIUM = 0.6
    LOW = 0.4

class ValueDriverAgent(BaseAgent):
    """
    Production-ready agent for identifying and quantifying business value drivers
    from unstructured text using hierarchical analysis and industry benchmarks.
    """

    # Tier 1 -> Tier 2 -> Tier 3 hierarchical value driver model
    VALUE_HIERARCHY = {
        "Cost Savings": {
            "description": "Direct cost reduction and expense elimination opportunities",
            "tier_2_drivers": [
                {
                    "name": "Reduce Manual Labor",
                    "description": "Automating manual processes to reduce employee hours and labor costs.",
                    "keywords": ["manual process", "time-consuming", "slow", "automate", "labor intensive", "repetitive tasks", "manual work", "manual data entry", "labor costs"],
                    "tier_3_metrics": [
                        {"name": "Hours saved per week", "type": "number", "default_value": 10, "unit": "hours"},
                        {"name": "Average hourly rate", "type": "currency", "default_value": 50, "unit": "USD"},
                        {"name": "Number of employees affected", "type": "number", "default_value": 5, "unit": "people"}
                    ]
                },
                {
                    "name": "Lower Operational Overhead",
                    "description": "Decreasing ongoing operational expenses and administrative costs.",
                    "keywords": ["overhead", "expense", "cost", "budget", "administrative", "operational cost", "reduce spending"],
                    "tier_3_metrics": [
                        {"name": "Monthly overhead reduction", "type": "currency", "default_value": 5000, "unit": "USD"},
                        {"name": "Annual operational savings", "type": "currency", "default_value": 60000, "unit": "USD"}
                    ]
                },
                {
                    "name": "Eliminate Software Licensing",
                    "description": "Reducing or consolidating software licensing costs.",
                    "keywords": ["software cost", "licensing", "subscriptions", "tools", "consolidate", "redundant software"],
                    "tier_3_metrics": [
                        {"name": "Annual license savings", "type": "currency", "default_value": 25000, "unit": "USD"},
                        {"name": "Number of licenses eliminated", "type": "number", "default_value": 10, "unit": "licenses"}
                    ]
                },
                {
                    "name": "Reduce Infrastructure Costs",
                    "description": "Optimizing infrastructure and hosting expenses.",
                    "keywords": ["infrastructure", "hosting", "cloud costs", "servers", "hardware", "data center"],
                    "tier_3_metrics": [
                        {"name": "Monthly infrastructure savings", "type": "currency", "default_value": 8000, "unit": "USD"},
                        {"name": "Efficiency improvement (%)", "type": "percentage", "default_value": 30, "unit": "%"}
                    ]
                }
            ]
        },
        "Productivity Gains": {
            "description": "Efficiency improvements and time savings across business processes",
            "tier_2_drivers": [
                {
                    "name": "Accelerate Task Completion",
                    "description": "Reducing the time it takes to complete key business tasks and workflows.",
                    "keywords": ["slow", "bottleneck", "time-consuming", "streamline", "faster", "quick", "speed up", "efficiency", "accelerating task completion"],
                    "tier_3_metrics": [
                        {"name": "Time saved per task (minutes)", "type": "number", "default_value": 60, "unit": "minutes"},
                        {"name": "Tasks per week", "type": "number", "default_value": 20, "unit": "tasks"},
                        {"name": "Number of people affected", "type": "number", "default_value": 8, "unit": "people"}
                    ]
                },
                {
                    "name": "Improve Decision Making Speed",
                    "description": "Faster access to data and insights for better decision making.",
                    "keywords": ["decision making", "insights", "data access", "analytics", "reporting", "visibility"],
                    "tier_3_metrics": [
                        {"name": "Decision time reduction (%)", "type": "percentage", "default_value": 40, "unit": "%"},
                        {"name": "Decisions per month", "type": "number", "default_value": 50, "unit": "decisions"},
                        {"name": "Average decision value", "type": "currency", "default_value": 5000, "unit": "USD"}
                    ]
                },
                {
                    "name": "Eliminate Duplicate Work",
                    "description": "Reducing redundant processes and duplicate efforts.",
                    "keywords": ["duplicate", "redundant", "repeated", "rework", "inefficient", "waste"],
                    "tier_3_metrics": [
                        {"name": "Hours saved per week", "type": "number", "default_value": 15, "unit": "hours"},
                        {"name": "Average hourly cost", "type": "currency", "default_value": 75, "unit": "USD"}
                    ]
                }
            ]
        },
        "Risk Mitigation": {
            "description": "Risk reduction and compliance improvements that prevent losses",
            "tier_2_drivers": [
                {
                    "name": "Improve Security Posture",
                    "description": "Reducing the risk of security breaches, data loss, and cyber attacks.",
                    "keywords": ["security", "risk", "threat", "breach", "cyber", "vulnerability", "protection", "secure"],
                    "tier_3_metrics": [
                        {"name": "Estimated cost of a breach", "type": "currency", "default_value": 100000, "unit": "USD"},
                        {"name": "Likelihood reduction (%)", "type": "percentage", "default_value": 50, "unit": "%"},
                        {"name": "Recovery time improvement (%)", "type": "percentage", "default_value": 75, "unit": "%"}
                    ]
                },
                {
                    "name": "Ensure Regulatory Compliance",
                    "description": "Avoiding fines and penalties associated with regulatory non-compliance.",
                    "keywords": ["compliance", "gdpr", "regulation", "audit", "penalty", "fine", "regulatory"],
                    "tier_3_metrics": [
                        {"name": "Potential fine amount", "type": "currency", "default_value": 50000, "unit": "USD"},
                        {"name": "Compliance improvement (%)", "type": "percentage", "default_value": 95, "unit": "%"}
                    ]
                },
                {
                    "name": "Reduce Operational Risk",
                    "description": "Minimizing business disruption and operational failures.",
                    "keywords": ["downtime", "outage", "failure", "disruption", "availability", "reliability"],
                    "tier_3_metrics": [
                        {"name": "Downtime cost per hour", "type": "currency", "default_value": 10000, "unit": "USD"},
                        {"name": "Uptime improvement (%)", "type": "percentage", "default_value": 99.9, "unit": "%"},
                        {"name": "Hours of downtime prevented", "type": "number", "default_value": 24, "unit": "hours"}
                    ]
                }
            ]
        },
        "Revenue Growth": {
            "description": "Revenue enhancement and business expansion opportunities",
            "tier_2_drivers": [
                {
                    "name": "Increase Lead Conversion",
                    "description": "Improving the rate at which leads become paying customers.",
                    "keywords": ["sales", "conversion", "leads", "customers", "pipeline", "funnel", "close rate"],
                    "tier_3_metrics": [
                        {"name": "Additional leads per month", "type": "number", "default_value": 100, "unit": "leads"},
                        {"name": "Conversion rate increase (%)", "type": "percentage", "default_value": 5, "unit": "%"},
                        {"name": "Average deal size", "type": "currency", "default_value": 10000, "unit": "USD"}
                    ]
                },
                {
                    "name": "Expand Market Reach",
                    "description": "Accessing new markets and customer segments.",
                    "keywords": ["market", "expansion", "new customers", "segments", "reach", "growth"],
                    "tier_3_metrics": [
                        {"name": "New customers per month", "type": "number", "default_value": 25, "unit": "customers"},
                        {"name": "Average customer value", "type": "currency", "default_value": 15000, "unit": "USD"},
                        {"name": "Market share increase (%)", "type": "percentage", "default_value": 3, "unit": "%"}
                    ]
                },
                {
                    "name": "Improve Customer Retention",
                    "description": "Reducing churn and increasing customer lifetime value.",
                    "keywords": ["retention", "churn", "loyalty", "satisfaction", "lifetime value", "renewal"],
                    "tier_3_metrics": [
                        {"name": "Churn reduction (%)", "type": "percentage", "default_value": 15, "unit": "%"},
                        {"name": "Average customer lifetime value", "type": "currency", "default_value": 50000, "unit": "USD"},
                        {"name": "Retention rate improvement (%)", "type": "percentage", "default_value": 20, "unit": "%"}
                    ]
                }
            ]
        },
        "Quality Improvement": {
            "description": "Quality enhancements that improve outcomes and reduce errors",
            "tier_2_drivers": [
                {
                    "name": "Reduce Error Rates",
                    "description": "Minimizing mistakes and improving accuracy in business processes.",
                    "keywords": ["error", "mistake", "accuracy", "quality", "defect", "precision", "correct"],
                    "tier_3_metrics": [
                        {"name": "Current error rate (%)", "type": "percentage", "default_value": 5, "unit": "%"},
                        {"name": "Target error rate (%)", "type": "percentage", "default_value": 1, "unit": "%"},
                        {"name": "Cost per error", "type": "currency", "default_value": 500, "unit": "USD"}
                    ]
                },
                {
                    "name": "Improve Customer Satisfaction",
                    "description": "Enhancing customer experience and satisfaction scores.",
                    "keywords": ["satisfaction", "experience", "customer service", "feedback", "rating", "nps"],
                    "tier_3_metrics": [
                        {"name": "Current satisfaction score", "type": "number", "default_value": 7.5, "unit": "score"},
                        {"name": "Target satisfaction score", "type": "number", "default_value": 9.0, "unit": "score"},
                        {"name": "Revenue impact per point", "type": "currency", "default_value": 25000, "unit": "USD"}
                    ]
                }
            ]
        },
        "Innovation and Growth": {
            "description": "Strategic advantages and competitive positioning improvements",
            "tier_2_drivers": [
                {
                    "name": "Enable Innovation",
                    "description": "Creating capabilities for new products, services, or business models.",
                    "keywords": ["innovation", "new product", "competitive advantage", "differentiation", "unique"],
                    "tier_3_metrics": [
                        {"name": "Time to market improvement (%)", "type": "percentage", "default_value": 30, "unit": "%"},
                        {"name": "Innovation project value", "type": "currency", "default_value": 200000, "unit": "USD"},
                        {"name": "Competitive advantage period (months)", "type": "number", "default_value": 18, "unit": "months"}
                    ]
                },
                {
                    "name": "Scale Business Operations",
                    "description": "Building capacity for business growth and expansion.",
                    "keywords": ["scale", "growth", "capacity", "expansion", "volume", "throughput"],
                    "tier_3_metrics": [
                        {"name": "Capacity increase (%)", "type": "percentage", "default_value": 50, "unit": "%"},
                        {"name": "Growth potential value", "type": "currency", "default_value": 500000, "unit": "USD"},
                        {"name": "Scalability factor", "type": "number", "default_value": 2.5, "unit": "multiplier"}
                    ]
                }
            ]
        }
    }

    ANALYSIS_SCHEMA = {
        'required_fields': ['agent_id', 'analysis_type', 'pillars_identified', 'average_confidence', 'timestamp'],
        'field_types': {
            'agent_id': 'string',
            'analysis_type': 'string',
            'pillars_identified': 'number',
            'average_confidence': 'number',
            'industry_context': 'string',
            'company_size': 'string',
            'timestamp': 'number'
        }
    }
    
    QUANT_SCHEMA = {
        'required_fields': ['agent_id', 'annual_cost_savings', 'annual_productivity_gains', 'annual_revenue_impact', 'roi_percentage', 'payback_months', 'timestamp'],
        'field_types': {
            'agent_id': 'string',
            'annual_cost_savings': 'number',
            'annual_productivity_gains': 'number',
            'annual_revenue_impact': 'number',
            'roi_percentage': 'number',
            'payback_months': 'number',
            'timestamp': 'number'
        }
    }

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Enhanced validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': [
                    'user_query'
                ],
                'field_types': {
                    'user_query': 'string',
                    'analysis_type': 'string',
                    'focus_areas': 'array',
                    'minimum_confidence': 'number',
                    'industry_context': 'string',
                    'company_size': 'string',
                    'include_quantification': 'boolean'
                },
                'field_constraints': {
                    'user_query': {'min_length': 10, 'max_length': 5000},
                    'analysis_type': {'enum': [t.value for t in AnalysisType]},
                    'minimum_confidence': {'min': 0.0, 'max': 1.0},
                    'company_size': {'enum': ['startup', 'small', 'medium', 'large', 'enterprise']},
                    'industry_context': {'enum': ['healthcare', 'financial_services', 'manufacturing', 
                                                'technology', 'retail', 'education', 'government']}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Industry-specific value multipliers
        self.industry_multipliers = {
            'healthcare': {'cost_savings': 1.2, 'productivity_gains': 1.1, 'revenue_growth': 0.9},
            'financial_services': {'cost_savings': 1.3, 'productivity_gains': 1.4, 'revenue_growth': 1.2},
            'manufacturing': {'cost_savings': 1.1, 'productivity_gains': 1.3, 'revenue_growth': 1.0},
            'technology': {'cost_savings': 1.0, 'productivity_gains': 1.5, 'revenue_growth': 1.4},
            'retail': {'cost_savings': 1.1, 'productivity_gains': 1.2, 'revenue_growth': 1.3}
        }
        
        # Company size factors
        self.size_factors = {
            'startup': {'complexity': 0.7, 'implementation_speed': 1.3, 'resource_availability': 0.6},
            'small': {'complexity': 0.8, 'implementation_speed': 1.2, 'resource_availability': 0.7},
            'medium': {'complexity': 1.0, 'implementation_speed': 1.0, 'resource_availability': 1.0},
            'large': {'complexity': 1.2, 'implementation_speed': 0.9, 'resource_availability': 1.3},
            'enterprise': {'complexity': 1.4, 'implementation_speed': 0.7, 'resource_availability': 1.5}
        }

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Enhanced validation for value driver analysis inputs."""
        errors = []
        
        # Validate user query content
        user_query = inputs.get('user_query', '').strip()
        if len(user_query.split()) < 3:
            errors.append("User query must contain at least 3 words for meaningful analysis")
        
        # Validate focus areas if provided
        focus_areas = inputs.get('focus_areas', [])
        if focus_areas:
            valid_focus_areas = list(self.VALUE_HIERARCHY.keys())
            invalid_areas = [area for area in focus_areas if area not in valid_focus_areas]
            if invalid_areas:
                errors.append(f"Invalid focus areas: {invalid_areas}. Valid options: {valid_focus_areas}")
        
        # Validate minimum confidence
        min_confidence = inputs.get('minimum_confidence', 0.5)
        if not isinstance(min_confidence, (int, float)) or not 0.0 <= min_confidence <= 1.0:
            errors.append("Minimum confidence must be a number between 0.0 and 1.0")
        
        return errors

    def _extract_keywords_with_context(self, text: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """Extract keywords with surrounding context for better matching."""
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            matches = list(re.finditer(pattern, text_lower))
            
            for match in matches:
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                
                found_keywords.append({
                    'keyword': keyword,
                    'context': context,
                    'position': match.start()
                })
        
        return found_keywords

    def _find_keywords_in_text(self, text: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Find keywords in text and extract context information.
        
        Args:
            text: The text to search in (should be lowercase)
            keywords: List of keywords to search for
            
        Returns:
            List of dictionaries containing keyword matches with context
        """
        matches = []
        matched_indices = []  # To keep track of matched text portions

        # Sort keywords by length in descending order to prioritize multi-word phrases
        sorted_keywords = sorted(keywords, key=len, reverse=True)

        for keyword in sorted_keywords:
        keyword_lower = keyword.lower()
        
        # Use regex for more robust matching, including word boundaries
        # This handles cases where keywords might be part of other words, e.g., 'man' in 'manual'
        # but also allows for partial matches if not strict word boundaries
        import re
        for match in re.finditer(r'\b' + re.escape(keyword_lower) + r'\b', text):
        start, end = match.span()
        
        # Check for overlap with already matched portions
        overlap = False
        for matched_start, matched_end in matched_indices:
            if max(start, matched_start) < min(end, matched_end):
                    overlap = True
                    break
            
        if not overlap:
            context_start = max(0, start - 50)
        context_end = min(len(text), end + 50)
        context = text[context_start:context_end].strip()
        
        matches.append({
            'keyword': keyword,
            'context': context,
        'position': start,
        'match_type': 'exact'
        })
        matched_indices.append((start, end))

        return matches

    def _calculate_confidence_score(self, keywords_found: List[Dict[str, Any]], total_keywords: int) -> float:
        """Calculate confidence score based on keyword matches and context."""
        if not keywords_found or total_keywords == 0:
            return 0.0
        
        # Base score from keyword ratio
        keyword_ratio = len(keywords_found) / total_keywords
        base_score = min(keyword_ratio * 0.8, 0.8)  # Max 80% from keywords
        
        # Bonus for multiple keyword matches
        if len(keywords_found) > 1:
            base_score += 0.1
        
        # Bonus for high-confidence keywords (longer matches)
        for kw in keywords_found:
            if len(kw['keyword']) > 8:  # Longer, more specific keywords
                base_score += 0.05
        
        return min(base_score, 1.0)

    def _filter_by_focus_areas(self, identified_pillars: List[Dict], focus_areas: List[str]) -> List[Dict]:
        """Filter identified pillars by user-specified focus areas."""
        if not focus_areas:
            return identified_pillars
        
        filtered_pillars = []
        for pillar in identified_pillars:
            if pillar['pillar'] in focus_areas:
                filtered_pillars.append(pillar)
        
        return filtered_pillars

    def _quantify_business_impact(self, identified_pillars: List[Dict[str, Any]], 
                                industry_context: Optional[str] = None,
                                company_size: Optional[str] = None) -> Dict[str, Any]:
        """Quantify the business impact of identified value drivers."""
        if not identified_pillars:
            return {}
        
        # Get industry and size multipliers
        industry_mult = self.industry_multipliers.get(industry_context, 
                                                    {'cost_savings': 1.0, 'productivity_gains': 1.0, 'revenue_growth': 1.0})
        size_factors = self.size_factors.get(company_size, 
                                           {'complexity': 1.0, 'implementation_speed': 1.0, 'resource_availability': 1.0})
        
        total_impact = {
            'annual_cost_savings': 0,
            'annual_productivity_gains': 0,
            'annual_revenue_impact': 0,
            'implementation_complexity': 0,
            'roi_projection': {}
        }
        
        pillar_impacts = []
        
        for pillar in identified_pillars:
            pillar_name = pillar['pillar']
            confidence = pillar['confidence_score']
            
            # Calculate pillar-specific impact
            pillar_impact = {
                'pillar': pillar_name,
                'confidence': confidence,
                'cost_savings': 0,
                'productivity_value': 0,
                'revenue_impact': 0,
                'implementation_effort': 0
            }
            
            # Process tier 2 drivers
            for driver in pillar['tier_2_drivers']:
                driver_value = self._calculate_driver_value(driver, industry_mult, size_factors, confidence)
                pillar_impact['cost_savings'] += driver_value.get('cost_savings', 0)
                pillar_impact['productivity_value'] += driver_value.get('productivity_value', 0)
                pillar_impact['revenue_impact'] += driver_value.get('revenue_impact', 0)
                pillar_impact['implementation_effort'] += driver_value.get('implementation_effort', 0)
            
            pillar_impacts.append(pillar_impact)
            
            # Add to totals
            total_impact['annual_cost_savings'] += pillar_impact['cost_savings']
            total_impact['annual_productivity_gains'] += pillar_impact['productivity_value']
            total_impact['annual_revenue_impact'] += pillar_impact['revenue_impact']
            total_impact['implementation_complexity'] += pillar_impact['implementation_effort']
        
        # Calculate ROI projections
        total_annual_benefit = (total_impact['annual_cost_savings'] + 
                              total_impact['annual_productivity_gains'] + 
                              total_impact['annual_revenue_impact'])
        
        # Estimate implementation cost based on complexity
        estimated_implementation_cost = total_impact['implementation_complexity'] * 10000  # Base cost per complexity point
        
        if estimated_implementation_cost > 0:
            roi_percentage = ((total_annual_benefit - estimated_implementation_cost) / estimated_implementation_cost) * 100
            payback_months = (estimated_implementation_cost / total_annual_benefit) * 12 if total_annual_benefit > 0 else 999
        else:
            roi_percentage = 0
            payback_months = 0
        
        total_impact['roi_projection'] = {
            'annual_benefit': total_annual_benefit,
            'implementation_cost': estimated_implementation_cost,
            'roi_percentage': round(roi_percentage, 1),
            'payback_months': round(payback_months, 1),
            'npv_3_year': self._calculate_npv(total_annual_benefit, estimated_implementation_cost, 3)
        }
        
        total_impact['pillar_breakdown'] = pillar_impacts
        
        return total_impact

    def _calculate_driver_value(self, driver: Dict[str, Any], industry_mult: Dict[str, float], 
                              size_factors: Dict[str, float], confidence: float) -> Dict[str, Any]:
        """Calculate the monetary value of a specific driver."""
        driver_value = {
            'cost_savings': 0,
            'productivity_value': 0,
            'revenue_impact': 0,
            'implementation_effort': 1  # Base complexity
        }
        
        # Extract metrics from tier 3
        metrics = driver.get('tier_3_metrics', {})
        
        # Cost Savings calculations
        if 'Hours saved per week' in metrics and 'Average hourly rate' in metrics:
            hours_saved = metrics['Hours saved per week'].get('suggested_value', 0)
            hourly_rate = metrics['Average hourly rate'].get('suggested_value', 0)
            num_employees = metrics.get('Number of employees affected', {}).get('suggested_value', 1)
            
            annual_savings = hours_saved * hourly_rate * 52 * num_employees * confidence
            driver_value['cost_savings'] = annual_savings * industry_mult.get('cost_savings', 1.0)
        
        # Direct cost savings
        if 'Monthly overhead reduction' in metrics:
            monthly_savings = metrics['Monthly overhead reduction'].get('suggested_value', 0)
            driver_value['cost_savings'] += monthly_savings * 12 * confidence * industry_mult.get('cost_savings', 1.0)
        
        if 'Annual license savings' in metrics:
            license_savings = metrics['Annual license savings'].get('suggested_value', 0)
            driver_value['cost_savings'] += license_savings * confidence * industry_mult.get('cost_savings', 1.0)
        
        # Productivity value calculations
        if 'Time saved per task (minutes)' in metrics and 'Tasks per week' in metrics:
            time_saved = metrics['Time saved per task (minutes)'].get('suggested_value', 0)
            tasks_per_week = metrics['Tasks per week'].get('suggested_value', 0)
            
            # Convert to annual productivity value
            annual_time_saved = (time_saved * tasks_per_week * 52) / 60  # Hours
            productivity_value = annual_time_saved * 75 * confidence  # $75/hour productivity value
            driver_value['productivity_value'] = productivity_value * industry_mult.get('productivity_gains', 1.0)
        
        # Revenue impact calculations
        if 'Revenue increase (%)' in metrics and 'Current annual revenue' in metrics:
            revenue_increase = metrics['Revenue increase (%)'].get('suggested_value', 0) / 100
            current_revenue = metrics['Current annual revenue'].get('suggested_value', 1000000)
            
            revenue_impact = current_revenue * revenue_increase * confidence
            driver_value['revenue_impact'] = revenue_impact * industry_mult.get('revenue_growth', 1.0)
        
        # Adjust for company size factors
        driver_value['implementation_effort'] *= size_factors.get('complexity', 1.0)
        
        return driver_value

    def _calculate_npv(self, annual_benefit: float, initial_cost: float, years: int, discount_rate: float = 0.1) -> float:
        """Calculate Net Present Value over specified years."""
        npv = -initial_cost  # Initial investment
        
        for year in range(1, years + 1):
            npv += annual_benefit / ((1 + discount_rate) ** year)
        
        return round(npv, 2)

    def _generate_business_recommendations(self, quantified_impact: Dict[str, Any], 
                                         identified_pillars: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable business recommendations based on value driver analysis."""
        recommendations = []
        
        if not quantified_impact or not identified_pillars:
            return ["Insufficient data for meaningful recommendations"]
        
        roi_projection = quantified_impact.get('roi_projection', {})
        roi_percentage = roi_projection.get('roi_percentage', 0)
        payback_months = roi_projection.get('payback_months', 999)
        
        # ROI-based recommendations
        if roi_percentage > 50:
            recommendations.append("Excellent ROI opportunity - prioritize for immediate implementation")
        elif roi_percentage > 25:
            recommendations.append("Strong business case - recommend proceeding with detailed planning")
        elif roi_percentage > 10:
            recommendations.append("Moderate returns - consider phased implementation approach")
        else:
            recommendations.append("Low ROI - reassess scope or seek additional value drivers")
        
        # Payback period recommendations
        if payback_months <= 12:
            recommendations.append("Quick payback period - ideal for budget approval")
        elif payback_months <= 24:
            recommendations.append("Reasonable payback timeline - align with annual planning cycle")
        else:
            recommendations.append("Extended payback period - ensure strong stakeholder commitment")
        
        # Pillar-specific recommendations
        pillar_breakdown = quantified_impact.get('pillar_breakdown', [])
        if pillar_breakdown:
            # Find highest value pillar
            highest_value_pillar = max(pillar_breakdown, 
                                     key=lambda x: x['cost_savings'] + x['productivity_value'] + x['revenue_impact'])
            recommendations.append(f"Focus initial efforts on '{highest_value_pillar['pillar']}' for maximum impact")
            
            # Risk assessment based on confidence
            low_confidence_pillars = [p for p in pillar_breakdown if p['confidence'] < 0.6]
            if low_confidence_pillars:
                recommendations.append("Conduct additional analysis for lower-confidence value drivers")
        
        # Implementation recommendations
        total_complexity = quantified_impact.get('implementation_complexity', 0)
        if total_complexity > 10:
            recommendations.append("High implementation complexity - consider phased rollout approach")
        
        recommendations.append("Establish baseline metrics before implementation to measure actual impact")
        recommendations.append("Plan for change management to ensure successful adoption")
        
        return recommendations

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
    
        """
        Analyzes input text to find and categorize value drivers based on a hierarchical model.
        Enhanced with business intelligence, quantification, and industry-specific analysis.
        """
        start_time = time.monotonic()
        try:
            logger.info(f"Starting value driver analysis for agent {self.agent_id}")
            
            # Validate inputs
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                logger.error(f"ValueDriverAgent input validation failed: {validation_result.errors}")
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": f"Validation failed: {validation_result.errors}"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Extract inputs with enhanced parameters
            user_query = inputs['user_query'].strip()
            analysis_type = inputs.get('analysis_type', AnalysisType.COMPREHENSIVE.value)
            focus_areas = inputs.get('focus_areas', [])
            minimum_confidence = inputs.get('minimum_confidence', 0.5)
            industry_context = inputs.get('industry_context')
            company_size = inputs.get('company_size', 'medium')
            include_quantification = inputs.get('include_quantification', True)
            
            logger.info(f"Analyzing query: '{user_query[:100]}...' with {analysis_type} analysis")
            
            # Analyze value drivers using hierarchical model
            identified_pillars = []
            
            # Determine which pillars to analyze based on analysis type
            pillars_to_analyze = self.VALUE_HIERARCHY.keys()
            if analysis_type == AnalysisType.FOCUSED.value and focus_areas:
                pillars_to_analyze = focus_areas
            elif analysis_type == AnalysisType.QUICK_SCAN.value:
                # Quick scan - analyze top 2 most likely pillars based on relevance to query
                pillars_to_analyze = self._get_top_level_pillars(user_query, num_pillars=2)
            
            # Process each pillar
            for pillar_name in pillars_to_analyze:
                if pillar_name not in self.VALUE_HIERARCHY:
                    continue
                    
                pillar_data = self.VALUE_HIERARCHY[pillar_name]
                matched_tier_2_drivers = []
                
                # Analyze tier 2 drivers within this pillar
                for tier_2_driver in pillar_data['tier_2_drivers']:
                    keywords_found = self._find_keywords_in_text(
                        user_query.lower(), 
                        tier_2_driver['keywords']
                    )
                    
                    if keywords_found:
                        confidence = self._calculate_confidence_score(
                            keywords_found, 
                            len(tier_2_driver['keywords'])
                        )
                        
                        # Apply industry-specific confidence adjustments
                        if industry_context and industry_context in self.industry_multipliers:
                            pillar_category = pillar_name.lower().replace(' ', '_')
                            if pillar_category in ['cost_savings', 'productivity_gains', 'revenue_growth']:
                                industry_boost = self.industry_multipliers[industry_context].get(pillar_category, 1.0)
                                confidence = min(1.0, confidence * industry_boost)
                        
                        if confidence >= minimum_confidence:
                            # Create enhanced driver copy
                            driver_copy = tier_2_driver.copy()
                            driver_copy['keywords_found'] = [kw['keyword'] for kw in keywords_found]
                            driver_copy['confidence_score'] = round(confidence, 3)
                            driver_copy['match_contexts'] = [kw['context'] for kw in keywords_found[:3]]
                            
                            # Enhanced tier_3_metrics with industry and size adjustments
                            enhanced_metrics = {}
                            for metric in tier_2_driver['tier_3_metrics']:
                                metric_copy = metric.copy()
                                
                                # Apply confidence-based and industry-specific adjustments
                                base_value = metric['default_value']
                                confidence_factor = 0.5 + confidence * 0.5
                                
                                if industry_context and company_size:
                                    size_factor = self.size_factors.get(company_size, {}).get('resource_availability', 1.0)
                                    adjusted_value = base_value * confidence_factor * size_factor
                                else:
                                    adjusted_value = base_value * confidence_factor
                                
                                if metric['type'] in ['number', 'currency']:
                                    metric_copy['suggested_value'] = round(adjusted_value, 2)
                                else:
                                    metric_copy['suggested_value'] = metric['default_value']
                                
                                enhanced_metrics[metric['name']] = metric_copy
                            
                            driver_copy['tier_3_metrics'] = enhanced_metrics
                            matched_tier_2_drivers.append(driver_copy)
                
                # Add pillar if we found drivers
                if matched_tier_2_drivers:
                    pillar_confidence = sum(d['confidence_score'] for d in matched_tier_2_drivers) / len(matched_tier_2_drivers)
                    
                    identified_pillars.append({
                        "pillar": pillar_name,
                        "pillar_description": pillar_data['description'],
                        "confidence_score": round(pillar_confidence, 3),
                        "tier_2_drivers": matched_tier_2_drivers,
                        "industry_context": industry_context,
                        "company_size": company_size
                    })
            
            # Filter by focus areas if specified
            if focus_areas and analysis_type != AnalysisType.FOCUSED.value:
                identified_pillars = self._filter_by_focus_areas(identified_pillars, focus_areas)
            
            # Sort by confidence score
            identified_pillars.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            # Handle no results case
            if not identified_pillars:
                logger.info("No value drivers identified with sufficient confidence")
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={
                        "message": "No specific value drivers identified with sufficient confidence.",
                        "suggestions": self._get_top_level_pillars(),
                        "value_drivers": [],
                        "quantified_impact": {},
                        "business_recommendations": [],
                        "analysis_metadata": {
                            "query_length": len(user_query),
                            "analysis_type": analysis_type,
                            "minimum_confidence": minimum_confidence,
                            "industry_context": industry_context
                        }
                    },
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Quantify business impact if requested
            quantified_impact = {}
            business_recommendations = []
            
            if include_quantification and identified_pillars:
                quantified_impact = self._quantify_business_impact(
                    identified_pillars, industry_context, company_size
                )
                business_recommendations = self._generate_business_recommendations(
                    quantified_impact, identified_pillars
                )
            
            # Prepare comprehensive response data
            response_data = {
                'drivers': identified_pillars,
                'analysis_summary': {
                    'total_pillars_identified': len(identified_pillars),
                    'highest_confidence_pillar': identified_pillars[0]['pillar'] if identified_pillars else None,
                    'average_confidence': round(sum(p['confidence_score'] for p in identified_pillars) / len(identified_pillars), 3) if identified_pillars else 0,
                    'analysis_type': analysis_type,
                    'industry_context': industry_context,
                    'company_size': company_size,
                    'focus_areas_applied': focus_areas,
                    'minimum_confidence_threshold': minimum_confidence,
                    'query_complexity': len(user_query.split()),
                    'analysis_timestamp': datetime.now().isoformat()
                },
                'business_intelligence': {
                    'quantified_impact': quantified_impact,
                    'recommendations': business_recommendations,
                    'implementation_priority': self._determine_implementation_priority(identified_pillars, quantified_impact),
                    'risk_assessment': self._assess_implementation_risk(identified_pillars, quantified_impact)
                }
            }

            logger.debug(f"include_quantification: {include_quantification}")
            logger.debug(f"identified_pillars: {identified_pillars is not None and len(identified_pillars) > 0}")
            if include_quantification and identified_pillars:
                roi_value_drivers = []
                for pillar_impact in quantified_impact.get('pillar_breakdown', []):
                    if pillar_impact['cost_savings'] > 0:
                        roi_value_drivers.append({
                            "name": f"{pillar_impact['pillar']} - Cost Savings",
                            "description": f"Quantified cost savings from {pillar_impact['pillar']}.",
                            "financial_impact": {
                                "type": "cost_savings",
                                "value_usd_per_year": pillar_impact['cost_savings']
                            }
                        })
                    if pillar_impact['productivity_value'] > 0:
                        roi_value_drivers.append({
                            "name": f"{pillar_impact['pillar']} - Productivity Gains",
                            "description": f"Quantified productivity gains from {pillar_impact['pillar']}.",
                            "financial_impact": {
                                "type": "productivity_gain",
                                "value_usd_per_year": pillar_impact['productivity_value']
                            }
                        })
                    if pillar_impact['revenue_impact'] > 0:
                        roi_value_drivers.append({
                            "name": f"{pillar_impact['pillar']} - Revenue Impact",
                            "description": f"Quantified revenue impact from {pillar_impact['pillar']}.",
                            "financial_impact": {
                                "type": "revenue_increase",
                                "value_usd_per_year": pillar_impact['revenue_impact']
                            }
                        })
                response_data['value_drivers'] = roi_value_drivers
            
            # Store comprehensive results in MCP episodic memory
            await self._store_value_driver_analysis(response_data, user_query)
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"Value driver analysis completed in {execution_time_ms}ms. Identified {len(identified_pillars)} pillars")
            
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data={
                    "value_drivers": response_data.get('value_drivers', []),
                    "quantified_impact": response_data['business_intelligence']['quantified_impact'],
                    "business_recommendations": response_data['business_intelligence']['recommendations'],
                    "message": "Value drivers identified and quantified successfully.",
                    "analysis_metadata": response_data['analysis_summary']
                },
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"Value driver analysis failed: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Value driver analysis failed: {str(e)}"},
                execution_time_ms=execution_time_ms
            )

    def _determine_implementation_priority(self, identified_pillars: List[Dict[str, Any]], 
                                         quantified_impact: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine implementation priority based on confidence, impact, and complexity."""
        if not identified_pillars:
            return []
        
        priority_list = []
        
        for pillar in identified_pillars:
            confidence = pillar['confidence_score']
            
            # Calculate potential impact score
            pillar_impact = 0
            if quantified_impact and 'pillar_breakdown' in quantified_impact:
                pillar_breakdown = quantified_impact['pillar_breakdown']
                matching_pillar = next((p for p in pillar_breakdown if p['pillar'] == pillar['pillar']), None)
                if matching_pillar:
                    pillar_impact = (matching_pillar['cost_savings'] + 
                                   matching_pillar['productivity_value'] + 
                                   matching_pillar['revenue_impact'])
            
            # Calculate priority score (confidence * impact / complexity)
            complexity = len(pillar['tier_2_drivers'])  # Simple complexity measure
            priority_score = (confidence * (pillar_impact / 100000)) / max(complexity, 1)
            
            priority_list.append({
                'pillar': pillar['pillar'],
                'priority_score': round(priority_score, 3),
                'confidence': confidence,
                'estimated_impact': pillar_impact,
                'complexity': complexity,
                'recommendation': self._get_priority_recommendation(priority_score)
            })
        
        # Sort by priority score
        priority_list.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return priority_list

    def _get_priority_recommendation(self, priority_score: float) -> str:
        """Get implementation recommendation based on priority score."""
        if priority_score > 5.0:
            return "High Priority - Immediate implementation recommended"
        elif priority_score > 2.0:
            return "Medium Priority - Plan for next quarter"
        elif priority_score > 0.5:
            return "Low Priority - Consider for future phases"
        else:
            return "Monitor - Requires further analysis"

    def _get_top_level_pillars(self, user_query: str, num_pillars: int = 2) -> List[str]:
        """
        Identifies the top N most relevant top-level value pillars based on the user query.
        """
        pillar_scores = {}
        user_query_lower = user_query.lower()

        for pillar_name, pillar_data in self.VALUE_HIERARCHY.items():
            all_pillar_keywords = []
            for tier_2_driver in pillar_data['tier_2_drivers']:
                all_pillar_keywords.extend(tier_2_driver['keywords'])

            # Use _find_keywords_in_text to find matches
            keywords_found = self._find_keywords_in_text(user_query_lower, all_pillar_keywords)
            
            # Score based on number of unique keywords found
            score = len(set([kw['keyword'] for kw in keywords_found]))
            pillar_scores[pillar_name] = score

        # Sort pillars by score in descending order
        sorted_pillars = sorted(pillar_scores.items(), key=lambda item: item[1], reverse=True)
        
        # Return the names of the top N pillars
        return [pillar for pillar, score in sorted_pillars[:num_pillars]]

    def _assess_implementation_risk(self, identified_pillars: List[Dict[str, Any]], 
                                  quantified_impact: Dict[str, Any]) -> Dict[str, Any]:
        """Assess implementation risk based on confidence levels and complexity."""
        if not identified_pillars:
            return {}
        
        # Calculate risk factors
        confidence_levels = [p['confidence_score'] for p in identified_pillars]
        avg_confidence = statistics.mean(confidence_levels)
        confidence_variance = statistics.variance(confidence_levels) if len(confidence_levels) > 1 else 0
        
        # Complexity assessment
        total_drivers = sum(len(p['tier_2_drivers']) for p in identified_pillars)
        complexity_score = min(10, total_drivers)  # Cap at 10
        
        # ROI risk assessment
        roi_risk = "Low"
        if quantified_impact and 'roi_projection' in quantified_impact:
            roi_percentage = quantified_impact['roi_projection'].get('roi_percentage', 0)
            if roi_percentage < 10:
                roi_risk = "High"
            elif roi_percentage < 25:
                roi_risk = "Medium"
        
        # Overall risk calculation
        risk_score = (1 - avg_confidence) * 0.4 + (confidence_variance * 0.3) + (complexity_score / 20 * 0.3)
        
        if risk_score < 0.3:
            overall_risk = "Low"
        elif risk_score < 0.6:
            overall_risk = "Medium"
        else:
            overall_risk = "High"
        
        return {
            'overall_risk': overall_risk,
            'risk_score': round(risk_score, 3),
            'confidence_risk': "High" if avg_confidence < 0.6 else "Low",
            'complexity_risk': "High" if complexity_score > 7 else "Low",
            'roi_risk': roi_risk,
            'risk_factors': [
                f"Average confidence: {avg_confidence:.2f}",
                f"Complexity score: {complexity_score}/10",
                f"Confidence variance: {confidence_variance:.3f}"
            ]
        }

    async def _store_value_driver_analysis(self, analysis_data: Dict[str, Any], original_query: str) -> None:
        """Store comprehensive value driver analysis in MCP episodic memory with validation."""
        try:
            # 1. Create and Validate primary analysis entity
            analysis_attributes = {
                "agent_id": self.agent_id,
                "analysis_type": analysis_data['analysis_summary']['analysis_type'],
                "pillars_identified": analysis_data['analysis_summary']['total_pillars_identified'],
                "average_confidence": analysis_data['analysis_summary']['average_confidence'],
                "industry_context": analysis_data['analysis_summary'].get('industry_context'),
                "company_size": analysis_data['analysis_summary'].get('company_size'),
                "timestamp": time.time()
            }
            
            analysis_errors = validate_comprehensive_input(analysis_attributes, self.ANALYSIS_SCHEMA)
            if not analysis_errors:
                analysis_entity = KnowledgeEntity(
                    id=f"value_driver_analysis_{int(time.time())}",
                    entity_type="value_driver_analysis",
                    attributes=analysis_attributes,
                    content=f"Value driver analysis of '{original_query[:200]}...' identified "
                           f"{analysis_data['analysis_summary']['total_pillars_identified']} value pillars "
                           f"with {analysis_data['analysis_summary']['average_confidence']:.2f} average confidence"
                )
                await self.mcp_client.store_memory(analysis_entity)
            else:
                error_str = format_validation_errors(analysis_errors, "value_driver_analysis entity")
                logger.error(f"MCP validation failed, skipping storage. {error_str}")

            # 2. Create and Validate quantified impact entity if available
            if analysis_data['business_intelligence']['quantified_impact']:
                impact_data = analysis_data['business_intelligence']['quantified_impact']
                impact_attributes = {
                    "agent_id": self.agent_id,
                    "annual_cost_savings": impact_data.get('annual_cost_savings', 0),
                    "annual_productivity_gains": impact_data.get('annual_productivity_gains', 0),
                    "annual_revenue_impact": impact_data.get('annual_revenue_impact', 0),
                    "roi_percentage": impact_data.get('roi_projection', {}).get('roi_percentage', 0),
                    "payback_months": impact_data.get('roi_projection', {}).get('payback_months', 0),
                    "timestamp": time.time()
                }
                
                quant_errors = validate_comprehensive_input(impact_attributes, self.QUANT_SCHEMA)
                if not quant_errors:
                    impact_entity = KnowledgeEntity(
                        id=f"value_quantification_{int(time.time())}",
                        entity_type="value_quantification",
                        attributes=impact_attributes,
                        content=f"Value quantification: ${impact_data.get('annual_cost_savings', 0):,.0f} cost savings, "
                               f"${impact_data.get('annual_productivity_gains', 0):,.0f} productivity gains, "
                               f"{impact_data.get('roi_projection', {}).get('roi_percentage', 0):.1f}% ROI"
                    )
                    await self.mcp_client.store_memory(impact_entity)
                else:
                    error_str = format_validation_errors(quant_errors, "value_quantification entity")
                    logger.error(f"MCP validation failed, skipping storage. {error_str}")

            logger.info("Value driver analysis results processed for MCP episodic memory")
            
        except Exception as e:
            logger.error(f"Failed to store value driver analysis in MCP memory: {e}", exc_info=True)
