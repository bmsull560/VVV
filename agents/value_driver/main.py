"""
Value Driver Agent

This agent identifies key business value drivers from unstructured text using a hierarchical model.
It analyzes user inputs to categorize potential business benefits into structured value pillars
with specific metrics for quantitative analysis.
"""

import logging
from typing import Dict, Any, List
import time
import re

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class ValueDriverAgent(BaseAgent):
    """
    Identifies key business value drivers from unstructured text using a hierarchical model.
    Maps business needs to quantifiable value categories for ROI analysis.
    """

    # Tier 1 -> Tier 2 -> Tier 3 hierarchical value driver model
    VALUE_HIERARCHY = {
        "Cost Savings": {
            "description": "Direct cost reduction and expense elimination opportunities",
            "tier_2_drivers": [
                {
                    "name": "Reduce Manual Labor",
                    "description": "Automating manual processes to reduce employee hours and labor costs.",
                    "keywords": ["manual process", "time-consuming", "slow", "automate", "labor intensive", "repetitive tasks", "manual work"],
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
                    "keywords": ["slow", "bottleneck", "time-consuming", "streamline", "faster", "quick", "speed up", "efficiency"],
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

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Set up validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': ['user_query'],
                'field_types': {
                    'user_query': 'string',
                    'focus_areas': 'array',
                    'minimum_confidence': 'number'
                },
                'field_constraints': {
                    'user_query': {'min_length': 10, 'max_length': 5000},
                    'minimum_confidence': {'min': 0.0, 'max': 1.0}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Perform value driver-specific validations."""
        errors = []
        
        user_query = inputs.get('user_query', '')
        if isinstance(user_query, str) and len(user_query.strip()) < 10:
            errors.append("User query must be at least 10 characters long")
        
        focus_areas = inputs.get('focus_areas', [])
        if focus_areas:
            valid_focus_areas = list(self.VALUE_HIERARCHY.keys())
            for area in focus_areas:
                if area not in valid_focus_areas:
                    errors.append(f"Invalid focus area '{area}'. Must be one of: {', '.join(valid_focus_areas)}")
        
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

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Analyzes input text to find and categorize value drivers based on a hierarchical model.

        Args:
            inputs: Dictionary containing:
                - user_query: Text describing business needs and challenges
                - focus_areas: (Optional) List of specific value driver categories to focus on
                - minimum_confidence: (Optional) Minimum confidence threshold for matches

        Returns:
            AgentResult with structured value drivers and metrics
        """
        start_time = time.monotonic()

        # Use centralized validation
        validation_result = await self.validate_inputs(inputs)
        if not validation_result.is_valid:
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": validation_result.errors[0] if validation_result.errors else "Input validation failed"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )

        try:
            user_query = inputs['user_query']
            focus_areas = inputs.get('focus_areas', [])
            minimum_confidence = inputs.get('minimum_confidence', 0.3)
            
            identified_pillars = []
            
            # Analyze each value pillar
            for pillar_name, pillar_data in self.VALUE_HIERARCHY.items():
                matched_tier_2_drivers = []
                
                for tier_2_driver in pillar_data['tier_2_drivers']:
                    keywords_found = self._extract_keywords_with_context(
                        user_query, 
                        tier_2_driver['keywords']
                    )
                    
                    if keywords_found:
                        confidence = self._calculate_confidence_score(
                            keywords_found, 
                            len(tier_2_driver['keywords'])
                        )
                        
                        if confidence >= minimum_confidence:
                            # Create driver copy with enhanced metadata
                            driver_copy = tier_2_driver.copy()
                            driver_copy['keywords_found'] = [kw['keyword'] for kw in keywords_found]
                            driver_copy['confidence_score'] = round(confidence, 3)
                            driver_copy['match_contexts'] = [kw['context'] for kw in keywords_found[:3]]  # Top 3 contexts
                            
                            # Enhance tier_3_metrics with calculated defaults
                            enhanced_metrics = {}
                            for metric in tier_2_driver['tier_3_metrics']:
                                metric_copy = metric.copy()
                                # Add confidence-based adjustment to default values
                                if metric['type'] in ['number', 'currency']:
                                    adjusted_value = metric['default_value'] * (0.5 + confidence * 0.5)
                                    metric_copy['suggested_value'] = round(adjusted_value, 2)
                                else:
                                    metric_copy['suggested_value'] = metric['default_value']
                                enhanced_metrics[metric['name']] = metric_copy
                            
                            driver_copy['tier_3_metrics'] = enhanced_metrics
                            matched_tier_2_drivers.append(driver_copy)
                
                if matched_tier_2_drivers:
                    # Calculate overall pillar confidence
                    pillar_confidence = sum(d['confidence_score'] for d in matched_tier_2_drivers) / len(matched_tier_2_drivers)
                    
                    identified_pillars.append({
                        "pillar": pillar_name,
                        "pillar_description": pillar_data['description'],
                        "confidence_score": round(pillar_confidence, 3),
                        "tier_2_drivers": matched_tier_2_drivers
                    })

            # Filter by focus areas if specified
            if focus_areas:
                identified_pillars = self._filter_by_focus_areas(identified_pillars, focus_areas)

            # Sort by confidence score
            identified_pillars.sort(key=lambda x: x['confidence_score'], reverse=True)

            if not identified_pillars:
                logger.info("No specific value drivers identified in the text.")
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={
                        "drivers": [], 
                        "message": "No specific value drivers identified with sufficient confidence.",
                        "suggestions": list(self.VALUE_HIERARCHY.keys())[:3]  # Suggest top 3 categories
                    },
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )

            # Store identified drivers in MCP for workflow coordination
            await self.mcp_client.store_memory(
                "working",
                "value_drivers",
                {
                    "identified_pillars": identified_pillars,
                    "analysis_metadata": {
                        "query_length": len(user_query),
                        "focus_areas": focus_areas,
                        "minimum_confidence": minimum_confidence,
                        "total_pillars_found": len(identified_pillars)
                    }
                },
                ["value_drivers", "workflow_step"]
            )

            result_data = {
                'drivers': identified_pillars,
                'analysis_summary': {
                    'total_pillars_identified': len(identified_pillars),
                    'highest_confidence_pillar': identified_pillars[0]['pillar'] if identified_pillars else None,
                    'average_confidence': round(sum(p['confidence_score'] for p in identified_pillars) / len(identified_pillars), 3) if identified_pillars else 0,
                    'focus_areas_applied': focus_areas,
                    'minimum_confidence_threshold': minimum_confidence
                }
            }

            logger.info(f"Identified {len(identified_pillars)} value driver pillars: {[p['pillar'] for p in identified_pillars]}")
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=result_data,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            logger.error(f"Value driver analysis failed: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Value driver analysis failed: {str(e)}"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
