"""
Report Builder Agent

This agent generates comprehensive reports and visualizations based on business case data.
It supports multiple output formats, customizable templates, and data-driven insights.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime, timezone
import json
import os
import base64
from pathlib import Path

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.types import KnowledgeEntity

logger = logging.getLogger(__name__)

class ReportFormat(Enum):
    """Supported report output formats."""
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"

class ReportTemplate(Enum):
    """Available report templates."""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_ANALYSIS = "detailed_analysis"
    FINANCIAL_DASHBOARD = "financial_dashboard"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    STAKEHOLDER_PRESENTATION = "stakeholder_presentation"
    CUSTOM = "custom"

class ChartType(Enum):
    """Supported chart and visualization types."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    HEATMAP = "heatmap"
    SANKEY = "sankey"
    TABLE = "table"
    GAUGE = "gauge"

class ReportSection(Enum):
    """Standard report sections."""
    EXECUTIVE_SUMMARY = "executive_summary"
    INTRODUCTION = "introduction"
    METHODOLOGY = "methodology"
    FINDINGS = "findings"
    FINANCIAL_ANALYSIS = "financial_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    RECOMMENDATIONS = "recommendations"
    CONCLUSION = "conclusion"
    APPENDICES = "appendices"

class ReportBuilderAgent(BaseAgent):
    """
    Production-ready agent for generating comprehensive reports and visualizations
    based on business case data, with support for multiple formats and templates.
    """

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Enhanced validation rules
        if 'input_validation' not in config:
            config['input_validation'] = {
                'required_fields': [
                    'report_type', 'data_sources'
                ],
                'field_types': {
                    'report_type': 'string',
                    'data_sources': 'array',
                    'output_format': 'string',
                    'template': 'string',
                    'sections': 'array',
                    'charts': 'array',
                    'filters': 'object',
                    'custom_styles': 'object',
                    'include_appendices': 'boolean',
                    'include_executive_summary': 'boolean'
                },
                'field_constraints': {
                    'report_type': {'enum': ['business_case', 'roi_analysis', 'risk_assessment', 'value_driver_analysis', 'custom']},
                    'output_format': {'enum': [f.value for f in ReportFormat]},
                    'template': {'enum': [t.value for t in ReportTemplate]}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Initialize template engine and chart renderer
        self._template_registry = self._initialize_templates()
        self._chart_renderers = self._initialize_chart_renderers()
        self._report_generators = self._initialize_report_generators()
        
        # Cache for previously generated reports
        self._report_cache = {}
        
    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize report templates with default configurations."""
        templates = {}
        
        # Executive Summary Template
        templates[ReportTemplate.EXECUTIVE_SUMMARY.value] = {
            'name': 'Executive Summary',
            'description': 'Concise overview for executive stakeholders',
            'sections': [
                ReportSection.EXECUTIVE_SUMMARY.value,
                ReportSection.FINANCIAL_ANALYSIS.value,
                ReportSection.RECOMMENDATIONS.value
            ],
            'max_pages': 5,
            'charts_per_section': 1,
            'style': {
                'color_scheme': 'executive',
                'font_family': 'Arial, sans-serif',
                'header_font_size': '24px',
                'body_font_size': '12px',
                'line_height': 1.5
            }
        }
        
        # Detailed Analysis Template
        templates[ReportTemplate.DETAILED_ANALYSIS.value] = {
            'name': 'Detailed Analysis',
            'description': 'Comprehensive analysis with all details',
            'sections': [
                ReportSection.EXECUTIVE_SUMMARY.value,
                ReportSection.INTRODUCTION.value,
                ReportSection.METHODOLOGY.value,
                ReportSection.FINDINGS.value,
                ReportSection.FINANCIAL_ANALYSIS.value,
                ReportSection.RISK_ASSESSMENT.value,
                ReportSection.RECOMMENDATIONS.value,
                ReportSection.CONCLUSION.value,
                ReportSection.APPENDICES.value
            ],
            'max_pages': 30,
            'charts_per_section': 3,
            'style': {
                'color_scheme': 'professional',
                'font_family': 'Georgia, serif',
                'header_font_size': '20px',
                'body_font_size': '11px',
                'line_height': 1.6
            }
        }
        
        # Financial Dashboard Template
        templates[ReportTemplate.FINANCIAL_DASHBOARD.value] = {
            'name': 'Financial Dashboard',
            'description': 'Visual dashboard focused on financial metrics',
            'sections': [
                ReportSection.EXECUTIVE_SUMMARY.value,
                ReportSection.FINANCIAL_ANALYSIS.value
            ],
            'max_pages': 10,
            'charts_per_section': 5,
            'style': {
                'color_scheme': 'financial',
                'font_family': 'Calibri, sans-serif',
                'header_font_size': '22px',
                'body_font_size': '11px',
                'line_height': 1.4
            }
        }
        
        # Technical Deep Dive Template
        templates[ReportTemplate.TECHNICAL_DEEP_DIVE.value] = {
            'name': 'Technical Deep Dive',
            'description': 'Detailed technical analysis with methodology',
            'sections': [
                ReportSection.INTRODUCTION.value,
                ReportSection.METHODOLOGY.value,
                ReportSection.FINDINGS.value,
                ReportSection.RISK_ASSESSMENT.value,
                ReportSection.APPENDICES.value
            ],
            'max_pages': 25,
            'charts_per_section': 4,
            'style': {
                'color_scheme': 'technical',
                'font_family': 'Consolas, monospace',
                'header_font_size': '18px',
                'body_font_size': '10px',
                'line_height': 1.5
            }
        }
        
        # Stakeholder Presentation Template
        templates[ReportTemplate.STAKEHOLDER_PRESENTATION.value] = {
            'name': 'Stakeholder Presentation',
            'description': 'Presentation-ready slides for stakeholders',
            'sections': [
                ReportSection.EXECUTIVE_SUMMARY.value,
                ReportSection.FINDINGS.value,
                ReportSection.FINANCIAL_ANALYSIS.value,
                ReportSection.RECOMMENDATIONS.value
            ],
            'max_pages': 15,
            'charts_per_section': 2,
            'style': {
                'color_scheme': 'presentation',
                'font_family': 'Helvetica, sans-serif',
                'header_font_size': '28px',
                'body_font_size': '18px',
                'line_height': 1.3
            }
        }
        
        # Custom Template (base configuration)
        templates[ReportTemplate.CUSTOM.value] = {
            'name': 'Custom Template',
            'description': 'Fully customizable template',
            'sections': [],
            'max_pages': 50,
            'charts_per_section': 5,
            'style': {
                'color_scheme': 'custom',
                'font_family': 'Arial, sans-serif',
                'header_font_size': '22px',
                'body_font_size': '12px',
                'line_height': 1.5
            }
        }
        
        return templates
    
    def _initialize_chart_renderers(self) -> Dict[str, Any]:
        """Initialize chart rendering functions for different chart types."""
        renderers = {}
        
        # Bar Chart Renderer
        renderers[ChartType.BAR.value] = self._render_bar_chart
        
        # Line Chart Renderer
        renderers[ChartType.LINE.value] = self._render_line_chart
        
        # Pie Chart Renderer
        renderers[ChartType.PIE.value] = self._render_pie_chart
        
        # Area Chart Renderer
        renderers[ChartType.AREA.value] = self._render_area_chart
        
        # Scatter Chart Renderer
        renderers[ChartType.SCATTER.value] = self._render_scatter_chart
        
        # Radar Chart Renderer
        renderers[ChartType.RADAR.value] = self._render_radar_chart
        
        # Heatmap Renderer
        renderers[ChartType.HEATMAP.value] = self._render_heatmap
        
        # Sankey Diagram Renderer
        renderers[ChartType.SANKEY.value] = self._render_sankey_diagram
        
        # Table Renderer
        renderers[ChartType.TABLE.value] = self._render_table
        
        # Gauge Chart Renderer
        renderers[ChartType.GAUGE.value] = self._render_gauge_chart
        
        return renderers
    
    def _initialize_report_generators(self) -> Dict[str, Any]:
        """Initialize report generation functions for different output formats."""
        generators = {}
        
        # PDF Generator
        generators[ReportFormat.PDF.value] = self._generate_pdf_report
        
        # HTML Generator
        generators[ReportFormat.HTML.value] = self._generate_html_report
        
        # Markdown Generator
        generators[ReportFormat.MARKDOWN.value] = self._generate_markdown_report
        
        # JSON Generator
        generators[ReportFormat.JSON.value] = self._generate_json_report
        
        # Excel Generator
        generators[ReportFormat.EXCEL.value] = self._generate_excel_report
        
        # PowerPoint Generator
        generators[ReportFormat.POWERPOINT.value] = self._generate_powerpoint_report
        
        return generators
    
    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Enhanced validation for report builder inputs."""
        errors = []
        
        # Validate data sources
        data_sources = inputs.get('data_sources', [])
        if not data_sources:
            errors.append("At least one data source must be specified")
        
        for i, source in enumerate(data_sources):
            if not isinstance(source, dict):
                errors.append(f"Data source {i} must be an object")
                continue
                
            if 'type' not in source:
                errors.append(f"Data source {i} must have a 'type' field")
            
            if 'source_id' not in source and 'data' not in source:
                errors.append(f"Data source {i} must have either 'source_id' or 'data' field")
        
        # Validate charts if provided
        charts = inputs.get('charts', [])
        for i, chart in enumerate(charts):
            if not isinstance(chart, dict):
                errors.append(f"Chart {i} must be an object")
                continue
                
            if 'type' not in chart:
                errors.append(f"Chart {i} must have a 'type' field")
            elif chart['type'] not in [c.value for c in ChartType]:
                errors.append(f"Chart {i} has invalid type: {chart['type']}")
                
            if 'data_source' not in chart:
                errors.append(f"Chart {i} must have a 'data_source' field")
                
            if 'title' not in chart:
                errors.append(f"Chart {i} must have a 'title' field")
        
        # Validate template and output format compatibility
        template = inputs.get('template')
        output_format = inputs.get('output_format')
        
        if template and output_format:
            # PowerPoint is only compatible with presentation templates
            if output_format == ReportFormat.POWERPOINT.value and template != ReportTemplate.STAKEHOLDER_PRESENTATION.value:
                errors.append(f"Output format '{output_format}' is only compatible with '{ReportTemplate.STAKEHOLDER_PRESENTATION.value}' template")
        
        return errors
    
    async def _fetch_data_from_sources(self, data_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fetch data from specified sources."""
        combined_data = {}
        
        for source in data_sources:
            source_type = source.get('type')
            source_id = source.get('source_id')
            
            if source_type == 'mcp_entity' and source_id:
                # Fetch from MCP memory
                try:
                    entity = await self.mcp_client.get_entity(source_id)
                    if entity:
                        combined_data[source_id] = entity.content
                except Exception as e:
                    logger.error(f"Failed to fetch data from MCP entity {source_id}: {e}")
                    combined_data[source_id] = {"error": f"Failed to fetch: {str(e)}"}
            
            elif source_type == 'workflow' and source_id:
                # Fetch workflow data
                try:
                    workflow = await self.mcp_client.get_workflow(source_id)
                    if workflow:
                        combined_data[source_id] = workflow
                except Exception as e:
                    logger.error(f"Failed to fetch workflow {source_id}: {e}")
                    combined_data[source_id] = {"error": f"Failed to fetch: {str(e)}"}
            
            elif source_type == 'direct' and 'data' in source:
                # Use directly provided data
                source_name = source.get('name', f"direct_data_{len(combined_data)}")
                combined_data[source_name] = source['data']
            
            elif source_type == 'api' and 'url' in source:
                # Fetch from external API (not implemented in this version)
                source_name = source.get('name', f"api_data_{len(combined_data)}")
                combined_data[source_name] = {"error": "External API fetching not implemented"}
        
        return combined_data
    
    def _prepare_report_structure(self, inputs: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare the report structure based on template and inputs."""
        template_name = inputs.get('template', ReportTemplate.EXECUTIVE_SUMMARY.value)
        template = self._template_registry.get(template_name, self._template_registry[ReportTemplate.EXECUTIVE_SUMMARY.value])
        
        # Start with template defaults
        report_structure = {
            'title': inputs.get('title', 'Business Value Analysis Report'),
            'subtitle': inputs.get('subtitle', 'Generated by B2BValue Platform'),
            'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'template': template_name,
            'sections': [],
            'charts': [],
            'metadata': {
                'generated_by': self.agent_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'data_sources': [s.get('name', s.get('source_id', 'unknown')) for s in inputs.get('data_sources', [])],
                'template_name': template['name'],
                'template_description': template['description']
            }
        }
        
        # Add sections based on template and inputs
        requested_sections = inputs.get('sections', [])
        template_sections = template.get('sections', [])
        
        # If specific sections are requested, use those; otherwise use template defaults
        sections_to_include = requested_sections if requested_sections else template_sections
        
        # Always include executive summary if specified
        if inputs.get('include_executive_summary', True) and ReportSection.EXECUTIVE_SUMMARY.value not in sections_to_include:
            sections_to_include.insert(0, ReportSection.EXECUTIVE_SUMMARY.value)
        
        # Add appendices if specified
        if inputs.get('include_appendices', False) and ReportSection.APPENDICES.value not in sections_to_include:
            sections_to_include.append(ReportSection.APPENDICES.value)
        
        # Process each section
        for section_name in sections_to_include:
            section = {
                'id': section_name,
                'title': section_name.replace('_', ' ').title(),
                'content': '',
                'charts': []
            }
            
            # Add section to report
            report_structure['sections'].append(section)
        
        # Process charts
        requested_charts = inputs.get('charts', [])
        for chart in requested_charts:
            chart_type = chart.get('type')
            if chart_type in self._chart_renderers:
                # Add chart to report
                report_structure['charts'].append(chart)
                
                # Also add to relevant section if specified
                section_id = chart.get('section')
                if section_id:
                    for section in report_structure['sections']:
                        if section['id'] == section_id:
                            section['charts'].append(chart)
                            break
        
        # Apply custom styles if provided
        custom_styles = inputs.get('custom_styles', {})
        if custom_styles:
            report_structure['styles'] = {**template.get('style', {}), **custom_styles}
        else:
            report_structure['styles'] = template.get('style', {})
        
        return report_structure
    
    def _generate_section_content(self, section: Dict[str, Any], data: Dict[str, Any], report_type: str) -> str:
        """Generate content for a report section based on available data."""
        section_id = section['id']
        content = ""
        
        # Executive Summary Section
        if section_id == ReportSection.EXECUTIVE_SUMMARY.value:
            content = self._generate_executive_summary(data, report_type)
        
        # Introduction Section
        elif section_id == ReportSection.INTRODUCTION.value:
            content = self._generate_introduction(data, report_type)
        
        # Methodology Section
        elif section_id == ReportSection.METHODOLOGY.value:
            content = self._generate_methodology(data, report_type)
        
        # Findings Section
        elif section_id == ReportSection.FINDINGS.value:
            content = self._generate_findings(data, report_type)
        
        # Financial Analysis Section
        elif section_id == ReportSection.FINANCIAL_ANALYSIS.value:
            content = self._generate_financial_analysis(data, report_type)
        
        # Risk Assessment Section
        elif section_id == ReportSection.RISK_ASSESSMENT.value:
            content = self._generate_risk_assessment(data, report_type)
        
        # Recommendations Section
        elif section_id == ReportSection.RECOMMENDATIONS.value:
            content = self._generate_recommendations(data, report_type)
        
        # Conclusion Section
        elif section_id == ReportSection.CONCLUSION.value:
            content = self._generate_conclusion(data, report_type)
        
        # Appendices Section
        elif section_id == ReportSection.APPENDICES.value:
            content = self._generate_appendices(data, report_type)
        
        # Default case for custom sections
        else:
            content = f"Content for {section['title']} section."
        
        return content
    
    def _generate_executive_summary(self, data: Dict[str, Any], report_type: str) -> str:
        """Generate executive summary content based on report data."""
        summary = "# Executive Summary\n\n"
        
        # Extract key metrics for the summary
        roi = None
        payback_period = None
        total_benefits = None
        total_costs = None
        
        # Look for ROI data in various possible locations
        for source_id, source_data in data.items():
            if isinstance(source_data, dict):
                # Check for ROI metrics in different possible structures
                if 'roi_metrics' in source_data:
                    metrics = source_data['roi_metrics']
                    roi = metrics.get('roi_percentage')
                    payback_period = metrics.get('payback_period_months')
                    total_benefits = metrics.get('total_benefits')
                    total_costs = metrics.get('total_costs')
                elif 'roi_summary' in source_data:
                    metrics = source_data['roi_summary']
                    roi = metrics.get('roi_percentage')
                    payback_period = metrics.get('payback_period_months')
                    total_benefits = metrics.get('total_annual_value') * 3  # Assuming 3-year period
                    total_costs = metrics.get('investment_amount') * 3 if 'investment_amount' in metrics else None
                elif 'financial_analysis' in source_data:
                    metrics = source_data['financial_analysis']
                    roi = metrics.get('roi')
                    payback_period = metrics.get('payback_period')
                    total_benefits = metrics.get('total_benefits')
                    total_costs = metrics.get('total_costs')
        
        # Add key metrics to summary if available
        if roi is not None:
            summary += f"Return on Investment (ROI): **{roi:.1f}%**\n\n"
        
        if payback_period is not None:
            summary += f"Payback Period: **{payback_period:.1f} months**\n\n"
        
        if total_benefits is not None and total_costs is not None:
            net_benefit = total_benefits - total_costs
            summary += f"Net Benefit: **${net_benefit:,.2f}**\n\n"
        
        # Add report type specific content
        if report_type == 'business_case':
            summary += "This business case analysis demonstrates a compelling opportunity for investment, with strong financial returns and strategic alignment with organizational goals. The following report details the comprehensive analysis, including value drivers, financial projections, risk assessment, and implementation recommendations.\n\n"
        elif report_type == 'roi_analysis':
            summary += "This ROI analysis provides a detailed examination of the expected financial returns from the proposed investment. The analysis considers direct and indirect benefits, implementation costs, and ongoing expenses to calculate a comprehensive return on investment figure.\n\n"
        elif report_type == 'risk_assessment':
            summary += "This risk assessment identifies and quantifies potential risks associated with the proposed initiative. Each risk is analyzed for probability, impact, and mitigation strategies, providing a clear picture of the overall risk profile.\n\n"
        elif report_type == 'value_driver_analysis':
            summary += "This value driver analysis examines the key factors that contribute to the overall business value of the proposed initiative. Each driver is quantified and its impact on the overall business case is assessed.\n\n"
        else:
            summary += "This report provides a comprehensive analysis of the proposed initiative, including financial projections, risk assessment, and strategic recommendations.\n\n"
        
        return summary
    
    def _generate_introduction(self, data: Dict[str, Any], report_type: str) -> str:
        """Generate introduction content based on report data."""
        introduction = "# Introduction\n\n"
        
        # Extract project information
        project_name = None
        project_description = None
        industry = None
        
        for source_id, source_data in data.items():
            if isinstance(source_data, dict):
                if 'project_name' in source_data:
                    project_name = source_data['project_name']
                if 'description' in source_data:
                    project_description = source_data['description']
                if 'industry' in source_data:
                    industry = source_data['industry']
                
                # Also check nested structures
                if 'project_data' in source_data and isinstance(source_data['project_data'], dict):
                    project_data = source_data['project_data']
                    if not project_name and 'project_name' in project_data:
                        project_name = project_data['project_name']
                    if not project_description and 'description' in project_data:
                        project_description = project_data['description']
                    if not industry and 'industry' in project_data:
                        industry = project_data['industry']
        
        # Add project information to introduction
        if project_name:
            introduction += f"## Project: {project_name}\n\n"
        
        if project_description:
            introduction += f"{project_description}\n\n"
        
        if industry:
            introduction += f"Industry: {industry}\n\n"
        
        # Add report type specific content
        if report_type == 'business_case':
            introduction += "This business case presents a comprehensive analysis of the proposed initiative, including the strategic context, expected benefits, costs, risks, and implementation approach. The analysis is based on industry best practices and organizational data to provide a clear picture of the expected value and return on investment.\n\n"
        elif report_type == 'roi_analysis':
            introduction += "This ROI analysis examines the financial implications of the proposed investment, considering both quantitative and qualitative factors. The analysis uses standard financial metrics such as Net Present Value (NPV), Internal Rate of Return (IRR), and Payback Period to provide a comprehensive view of the expected returns.\n\n"
        elif report_type == 'risk_assessment':
            introduction += "This risk assessment identifies and analyzes potential risks associated with the proposed initiative. Each risk is evaluated for probability, impact, and mitigation strategies, providing a comprehensive view of the overall risk profile and management approach.\n\n"
        elif report_type == 'value_driver_analysis':
            introduction += "This value driver analysis examines the key factors that contribute to the overall business value of the proposed initiative. The analysis quantifies each driver and assesses its impact on the overall business case, providing insights into the most significant sources of value.\n\n"
        else:
            introduction += "This report provides a detailed analysis of the proposed initiative, examining various aspects including financial projections, risk factors, and strategic alignment. The analysis is based on industry best practices and organizational data to provide a clear picture of the expected outcomes.\n\n"
        
        return introduction
    
    def _generate_methodology(self, data: Dict[str, Any], report_type: str) -> str:
        """Generate methodology content based on report data."""
        methodology = "# Methodology\n\n"
        
        # Add report type specific content
        if report_type == 'business_case':
            methodology += """## Business Case Methodology

This business case analysis follows a structured approach to evaluate the proposed initiative:

1. **Value Driver Identification**: Key value drivers were identified through stakeholder interviews, industry research, and organizational data analysis.

2. **Benefit Quantification**: Each value driver was quantified using historical data, industry benchmarks, and expert estimates.

3. **Cost Analysis**: Implementation and ongoing costs were estimated based on vendor quotes, resource requirements, and industry standards.

4. **Financial Modeling**: A comprehensive financial model was developed to calculate ROI, NPV, IRR, and Payback Period.

5. **Risk Assessment**: Potential risks were identified and analyzed for probability, impact, and mitigation strategies.

6. **Sensitivity Analysis**: Key variables were tested for sensitivity to provide a range of possible outcomes.

The analysis uses a 3-year time horizon with a discount rate of 10% for NPV calculations, aligning with organizational standards for investment evaluation.
"""
        elif report_type == 'roi_analysis':
            methodology += """## ROI Analysis Methodology

This ROI analysis follows a structured approach to evaluate the financial returns of the proposed investment:

1. **Benefit Identification**: Direct and indirect benefits were identified through stakeholder interviews and process analysis.

2. **Benefit Quantification**: Each benefit was quantified using historical data, industry benchmarks, and expert estimates.

3. **Cost Identification**: Implementation and ongoing costs were identified through vendor quotes and resource planning.

4. **Cost Quantification**: Each cost element was quantified based on market rates, historical data, and expert estimates.

5. **Financial Modeling**: A comprehensive financial model was developed to calculate ROI, NPV, IRR, and Payback Period.

6. **Sensitivity Analysis**: Key variables were tested for sensitivity to provide a range of possible outcomes.

The analysis uses a 3-year time horizon with a discount rate of 10% for NPV calculations, aligning with industry standards for investment evaluation.
"""
        elif report_type == 'risk_assessment':
            methodology += """## Risk Assessment Methodology

This risk assessment follows a structured approach to identify and analyze potential risks:

1. **Risk Identification**: Potential risks were identified through stakeholder interviews, historical data analysis, and industry research.

2. **Risk Categorization**: Identified risks were categorized by type (e.g., technical, financial, operational) and source.

3. **Risk Analysis**: Each risk was analyzed for probability of occurrence and potential impact.

4. **Risk Scoring**: Risks were scored based on the combination of probability and impact to prioritize mitigation efforts.

5. **Mitigation Strategy Development**: Strategies were developed to mitigate high-priority risks.

6. **Residual Risk Assessment**: Residual risk was assessed after applying mitigation strategies.

The assessment uses a 5x5 risk matrix with standardized probability and impact scales to ensure consistent evaluation across all identified risks.
"""
        elif report_type == 'value_driver_analysis':
            methodology += """## Value Driver Analysis Methodology

This value driver analysis follows a structured approach to identify and quantify key value drivers:

1. **Value Driver Identification**: Key value drivers were identified through stakeholder interviews, industry research, and process analysis.

2. **Driver Categorization**: Identified drivers were categorized by type (e.g., revenue growth, cost reduction, risk mitigation) and business area.

3. **Driver Quantification**: Each driver was quantified using historical data, industry benchmarks, and expert estimates.

4. **Sensitivity Analysis**: Key drivers were tested for sensitivity to provide a range of possible outcomes.

5. **Prioritization**: Drivers were prioritized based on their quantified impact and implementation feasibility.

6. **Implementation Planning**: Implementation strategies were developed for high-priority drivers.

The analysis uses a combination of top-down and bottom-up approaches to ensure comprehensive coverage of all potential value sources.
"""
        else:
            methodology += """## Analysis Methodology

This analysis follows a structured approach to evaluate the proposed initiative:

1. **Data Collection**: Relevant data was collected through stakeholder interviews, system analysis, and industry research.

2. **Data Analysis**: Collected data was analyzed using statistical methods and industry benchmarks.

3. **Impact Assessment**: The potential impact of the initiative was assessed across multiple dimensions.

4. **Financial Modeling**: A comprehensive financial model was developed to calculate expected returns.

5. **Risk Evaluation**: Potential risks were identified and evaluated for probability and impact.

6. **Recommendation Development**: Recommendations were developed based on the analysis findings.

The analysis uses industry-standard methodologies and tools to ensure accuracy and reliability of the results.
"""
        
        return methodology
    
    def _generate_findings(self, data: Dict[str, Any], report_type: str) -> str:
        """Generate findings content based on report data."""
        findings = "# Key Findings\n\n"
        
        # Extract value drivers and benefits
        value_drivers = []
        benefits = []
        
        for source_id, source_data in data.items():
            if isinstance(source_data, dict):
                # Look for value drivers
                if 'value_drivers' in source_data and isinstance(source_data['value_drivers'], list):
                    value_drivers.extend(source_data['value_drivers'])
                elif 'drivers' in source_data and isinstance(source_data['drivers'], list):
                    value_drivers.extend(source_data['drivers'])
                
                # Look for benefits
                if 'benefits' in source_data and isinstance(source_data['benefits'], list):
                    benefits.extend(source_data['benefits'])
                elif 'quantified_benefits' in source_data and isinstance(source_data['quantified_benefits'], list):
                    benefits.extend(source_data['quantified_benefits'])
        
        # Add value drivers to findings
        if value_drivers:
            findings += "## Value Drivers\n\n"
            for i, driver in enumerate(value_drivers[:5]):  # Limit to top 5
                if isinstance(driver, dict):
                    driver_name = driver.get('name', f"Value Driver {i+1}")
                    driver_description = driver.get('description', 'No description available')
                    findings += f"### {driver_name}\n\n{driver_description}\n\n"
                else:
                    findings += f"### Value Driver {i+1}\n\n{driver}\n\n"
        
        # Add benefits to findings
        if benefits:
            findings += "## Quantified Benefits\n\n"
            for i, benefit in enumerate(benefits[:5]):  # Limit to top 5
                if isinstance(benefit, dict):
                    benefit_name = benefit.get('name', f"Benefit {i+1}")
                    benefit_value = benefit.get('value', 'Not quantified')
                    if isinstance(benefit_value, (int, float)):
                        benefit_value = f"${benefit_value:,.2f}"
                    findings += f"### {benefit_name}\n\n**Value**: {benefit_value}\n\n"
                else:
                    findings += f"### Benefit {i+1}\n\n{benefit}\n\n"
        
        # Add report type specific content
        if report_type == 'business_case':
            findings += """## Business Case Findings

The business case analysis has identified significant potential for value creation through the proposed initiative. Key findings include:

1. **Strong Financial Returns**: The initiative demonstrates a compelling financial case with positive ROI and reasonable payback period.

2. **Strategic Alignment**: The initiative aligns well with organizational strategic objectives and priorities.

3. **Operational Improvements**: Significant operational improvements are expected in efficiency, quality, and customer satisfaction.

4. **Manageable Risks**: While risks exist, they are manageable with appropriate mitigation strategies.

5. **Implementation Feasibility**: The initiative can be implemented with available resources and within a reasonable timeframe.
"""
        elif report_type == 'roi_analysis':
            findings += """## ROI Analysis Findings

The ROI analysis has identified a strong financial case for the proposed investment. Key findings include:

1. **Positive ROI**: The investment demonstrates a positive return on investment within the analysis period.

2. **Reasonable Payback Period**: The investment is expected to pay back within a reasonable timeframe.

3. **Multiple Benefit Sources**: Benefits are derived from multiple sources, reducing dependency on any single factor.

4. **Cost Efficiency**: The implementation costs are reasonable relative to the expected benefits.

5. **Sustainable Returns**: The benefits are expected to be sustainable beyond the initial analysis period.
"""
        elif report_type == 'risk_assessment':
            findings += """## Risk Assessment Findings

The risk assessment has identified several key risks associated with the proposed initiative. Key findings include:

1. **Manageable Risk Profile**: The overall risk profile is manageable with appropriate mitigation strategies.

2. **Key Risk Areas**: Technical integration, user adoption, and vendor performance are the primary risk areas.

3. **Mitigation Opportunities**: Effective mitigation strategies exist for all identified high-priority risks.

4. **Residual Risk**: After mitigation, the residual risk is within acceptable organizational thresholds.

5. **Risk Monitoring**: Ongoing risk monitoring will be essential to ensure early identification of emerging risks.
"""
        elif report_type == 'value_driver_analysis':
            findings += """## Value Driver Analysis Findings

The value driver analysis has identified several key factors that contribute to the overall business value. Key findings include:

1. **Primary Value Sources**: Cost reduction, productivity improvement, and revenue enhancement are the primary value sources.

2. **Driver Interdependencies**: Several value drivers are interdependent, creating potential synergies.

3. **Implementation Complexity**: Value drivers vary in implementation complexity and resource requirements.

4. **Timing Considerations**: Value realization timelines vary across drivers, affecting the overall value profile.

5. **Measurement Approach**: Clear metrics and measurement approaches exist for all identified value drivers.
"""
        
        return findings
    
    def _generate_financial_analysis(self, data: Dict[str, Any], report_type: str) -> str:
        """Generate financial analysis content based on report data."""
        financial = "# Financial Analysis\n\n"
        
        # Extract financial metrics
        roi = None
        payback_period = None
        npv = None
        irr = None
        total_benefits = None
        total_costs = None
        net_benefit = None
        
        # Look for financial data in various possible locations
        for source_id, source_data in data.items():
            if isinstance(source_data, dict):
                # Check for financial metrics in different possible structures
                if 'roi_metrics' in source_data:
                    metrics = source_data['roi_metrics']
                    roi = metrics.get('roi_percentage')
                    payback_period = metrics.get('payback_period_months')
                    npv = metrics.get('npv')
                    irr = metrics.get('irr')
                    total_benefits = metrics.get('total_benefits')
                    total_costs = metrics.get('total_costs')
                    net_benefit = metrics.get('net_benefit')
                elif 'roi_summary' in source_data:
                    metrics = source_data['roi_summary']
                    roi = metrics.get('roi_percentage')
                    payback_period = metrics.get('payback_period_months')
                    total_benefits = metrics.get('total_annual_value') * 3  # Assuming 3-year period
                    total_costs = metrics.get('investment_amount') * 3 if 'investment_amount' in metrics else None
                    if total_benefits is not None and total_costs is not None:
                        net_benefit = total_benefits - total_costs
                elif 'financial_analysis' in source_data:
                    metrics = source_data['financial_analysis']
                    roi = metrics.get('roi')
                    payback_period = metrics.get('payback_period')
                    npv = metrics.get('npv')
                    irr = metrics.get('irr')
                    total_benefits = metrics.get('total_benefits')
                    total_costs = metrics.get('total_costs')
                    net_benefit = metrics.get('net_benefit')
        
        # Add financial metrics to analysis
        financial += "## Key Financial Metrics\n\n"
        
        if roi is not None:
            financial += f"- **Return on Investment (ROI)**: {roi:.1f}%\n"
        
        if payback_period is not None:
            financial += f"- **Payback Period**: {payback_period:.1f} months\n"
        
        if npv is not None:
            financial += f"- **Net Present Value (NPV)**: ${npv:,.2f}\n"
        
        if irr is not None:
            financial += f"- **Internal Rate of Return (IRR)**: {irr:.1f}%\n"
        
        if total_benefits is not None:
            financial += f"- **Total Benefits**: ${total_benefits:,.2f}\n"
        
        if total_costs is not None:
            financial += f"- **Total Costs**: ${total_costs:,.2f}\n"
        
        if net_benefit is not None:
            financial += f"- **Net Benefit**: ${net_benefit:,.2f}\n"
        
        financial += "\n## Financial Analysis\n\n"
        
        # Add report type specific content
        if report_type == 'business_case':
            financial += """The financial analysis demonstrates a strong business case for the proposed initiative. The positive ROI and reasonable payback period indicate a sound investment opportunity. The NPV calculation, which accounts for the time value of money, further supports the financial viability of the initiative.

The benefits are derived from multiple sources, including cost reduction, productivity improvement, and revenue enhancement. This diversification of benefit sources reduces the dependency on any single factor and increases the robustness of the business case.

The costs include both initial implementation expenses and ongoing operational costs. The implementation costs include software, hardware, professional services, and internal resource allocation. The ongoing costs include maintenance, support, and periodic upgrades.

Sensitivity analysis indicates that the business case remains positive even under conservative assumptions, further strengthening the investment rationale.
"""
        elif report_type == 'roi_analysis':
            financial += """The ROI analysis demonstrates a strong financial case for the proposed investment. The positive ROI and reasonable payback period indicate a sound investment opportunity. The NPV calculation, which accounts for the time value of money, further supports the financial viability of the investment.

The benefits are quantified based on historical data, industry benchmarks, and expert estimates. Each benefit has been conservatively estimated to ensure the robustness of the analysis. The costs include both initial implementation expenses and ongoing operational costs.

The analysis uses a 3-year time horizon with a discount rate of 10% for NPV calculations, aligning with industry standards for investment evaluation. The IRR exceeds the organization's hurdle rate, further supporting the investment decision.

Sensitivity analysis indicates that the ROI remains positive even when key variables are adjusted within reasonable ranges, demonstrating the robustness of the investment case.
"""
        elif report_type == 'risk_assessment':
            financial += """The financial analysis in the context of risk assessment examines the potential financial impact of identified risks. The analysis considers both the direct costs of risk events and the indirect costs of mitigation strategies.

The risk-adjusted ROI remains positive, indicating that the investment remains viable even when accounting for potential risk impacts. The risk-adjusted payback period is still within acceptable organizational thresholds.

The analysis includes quantification of risk impacts on both benefits and costs. Benefit realization risks could reduce the expected benefits, while implementation risks could increase the expected costs. The combined impact is reflected in the risk-adjusted financial metrics.

Mitigation strategies have been developed for all high-priority risks, with associated costs included in the financial analysis. The net impact of these strategies is a reduction in overall risk exposure while maintaining a positive financial case.
"""
        elif report_type == 'value_driver_analysis':
            financial += """The financial analysis in the context of value driver analysis examines the contribution of each value driver to the overall financial case. The analysis quantifies the financial impact of each driver and assesses its relative importance.

The primary value drivers, in order of financial impact, are cost reduction, productivity improvement, and revenue enhancement. Each driver has been quantified based on historical data, industry benchmarks, and expert estimates.

The analysis includes an assessment of the implementation complexity and resource requirements for each value driver. This assessment helps prioritize implementation efforts to maximize early value realization.

The financial impact of value drivers varies over time, with some delivering immediate benefits and others requiring longer realization periods. The cumulative impact over the analysis period supports a strong overall financial case.
"""
        else:
            financial += """The financial analysis examines the expected financial returns from the proposed initiative. The analysis considers both quantitative and qualitative factors to provide a comprehensive view of the expected value.

The quantitative analysis includes standard financial metrics such as ROI, NPV, IRR, and Payback Period. These metrics provide a clear picture of the expected financial returns and the timeframe for realizing those returns.

The qualitative analysis considers factors that are difficult to quantify but still contribute to the overall value proposition. These factors include strategic alignment, competitive positioning, and organizational capability development.

The combined analysis supports a strong financial case for the proposed initiative, with positive returns expected within a reasonable timeframe.
"""
        
        return financial
    
    def _generate_risk_assessment(self, data: Dict[str, Any], report_type: str) -> str:
        """Generate risk assessment content based on report data."""
        risk = "# Risk Assessment\n\n"
        
        # Extract risk data
        risks = []
        
        for source_id, source_data in data.items():
            if isinstance(source_data, dict):
                # Check for risks in different possible structures
                if 'risks' in source_data and isinstance(source_data['risks'], list):
                    risks.extend(source_data['risks'])
                elif 'risk_assessment' in source_data and isinstance(source_data['risk_assessment'], dict):
                    if 'risks' in source_data['risk_assessment'] and isinstance(source_data['risk_assessment']['risks'], list):
                        risks.extend(source_data['risk_assessment']['risks'])
                elif 'individual_assessments' in source_data and isinstance(source_data['individual_assessments'], list):
                    risks.extend(source_data['individual_assessments'])
        
        # Add risks to assessment
        if risks:
            risk += "## Identified Risks\n\n"
            for i, risk_item in enumerate(risks[:10]):  # Limit to top 10
                if isinstance(risk_item, dict):
                    risk_name = risk_item.get('name', f"Risk {i+1}")
                    risk_category = risk_item.get('category', 'Uncategorized')
                    risk_probability = risk_item.get('probability', 'Unknown')
                    risk_impact = risk_item.get('impact', 'Unknown')
                    risk_description = risk_item.get('description', 'No description available')
                    
                    risk += f"### {risk_name}\n\n"
                    risk += f"**Category**: {risk_category}\n\n"
                    risk += f"**Probability**: {risk_probability}\n\n"
                    risk += f"**Impact**: {risk_impact}\n\n"
                    risk += f"**Description**: {risk_description}\n\n"
                    
                    # Add mitigation strategy if available
                    if 'mitigation' in risk_item:
                        risk += f"**Mitigation Strategy**: {risk_item['mitigation']}\n\n"
                else:
                    risk += f"### Risk {i+1}\n\n{risk_item}\n\n"
        
        # Add report type specific content
        if report_type == 'business_case':
            risk += """## Risk Management Approach

The business case includes a comprehensive risk management approach to identify, assess, and mitigate potential risks. The approach includes:

1. **Risk Identification**: Potential risks were identified through stakeholder interviews, historical data analysis, and industry research.

2. **Risk Assessment**: Each risk was assessed for probability of occurrence and potential impact on the business case.

3. **Risk Prioritization**: Risks were prioritized based on their combined probability and impact scores.

4. **Mitigation Strategy Development**: Strategies were developed to mitigate high-priority risks.

5. **Residual Risk Assessment**: Residual risk was assessed after applying mitigation strategies.

6. **Risk Monitoring Plan**: A plan was developed for ongoing monitoring of risks throughout the initiative lifecycle.

The overall risk profile is considered manageable with the identified mitigation strategies. Regular risk reviews will be conducted throughout the implementation to ensure early identification and management of emerging risks.
"""
        elif report_type == 'roi_analysis':
            risk += """## Risk Factors in ROI Analysis

The ROI analysis includes consideration of several risk factors that could impact the expected returns:

1. **Benefit Realization Risk**: The risk that expected benefits may not be fully realized due to implementation challenges, market changes, or other factors.

2. **Cost Overrun Risk**: The risk that implementation or ongoing costs may exceed estimates.

3. **Timeline Risk**: The risk that implementation may take longer than expected, delaying benefit realization.

4. **Technology Risk**: The risk that the technology may not perform as expected or may become obsolete faster than anticipated.

5. **Market Risk**: The risk that market conditions may change, affecting the value of benefits.

These risk factors have been incorporated into the ROI analysis through conservative benefit estimates, contingency allowances in cost estimates, and sensitivity analysis of key variables. The analysis demonstrates that the investment remains viable even when accounting for these risk factors.
"""
        elif report_type == 'risk_assessment':
            risk += """## Risk Assessment Methodology

This risk assessment follows a structured methodology to identify, analyze, and evaluate risks:

1. **Risk Identification**: Risks were identified through stakeholder interviews, historical data analysis, and industry research.

2. **Risk Categorization**: Identified risks were categorized by type (e.g., technical, financial, operational) and source.

3. **Risk Analysis**: Each risk was analyzed for probability of occurrence and potential impact using standardized scales.

4. **Risk Evaluation**: Risks were evaluated using a risk matrix to determine their priority level.

5. **Mitigation Strategy Development**: Strategies were developed to mitigate high-priority risks.

6. **Residual Risk Assessment**: Residual risk was assessed after applying mitigation strategies.

The assessment uses a 5x5 risk matrix with standardized probability and impact scales to ensure consistent evaluation across all identified risks. The overall risk profile is considered manageable with the identified mitigation strategies.
"""
        elif report_type == 'value_driver_analysis':
            risk += """## Risk Factors in Value Driver Analysis

The value driver analysis includes consideration of several risk factors that could impact the expected value realization:

1. **Driver Interdependency Risk**: The risk that interdependencies between value drivers may affect overall value realization.

2. **Implementation Complexity Risk**: The risk that implementation complexity may reduce the effectiveness of value drivers.

3. **Measurement Risk**: The risk that value drivers may be difficult to measure accurately, affecting value tracking.

4. **External Factor Risk**: The risk that external factors may influence the effectiveness of value drivers.

5. **Sustainability Risk**: The risk that value drivers may not sustain their impact over the expected timeframe.

These risk factors have been incorporated into the value driver analysis through conservative value estimates and sensitivity analysis of key drivers. The analysis demonstrates that the overall value proposition remains strong even when accounting for these risk factors.
"""
        else:
            risk += """## Risk Management Approach

The analysis includes a comprehensive risk management approach to identify, assess, and mitigate potential risks. The approach includes:

1. **Risk Identification**: Potential risks were identified through stakeholder interviews, historical data analysis, and industry research.

2. **Risk Assessment**: Each risk was assessed for probability of occurrence and potential impact.

3. **Risk Prioritization**: Risks were prioritized based on their combined probability and impact scores.

4. **Mitigation Strategy Development**: Strategies were developed to mitigate high-priority risks.

5. **Residual Risk Assessment**: Residual risk was assessed after applying mitigation strategies.

6. **Risk Monitoring Plan**: A plan was developed for ongoing monitoring of risks throughout the initiative lifecycle.

The overall risk profile is considered manageable with the identified mitigation strategies. Regular risk reviews will be conducted throughout the implementation to ensure early identification and management of emerging risks.
"""
        
        return risk
    
    def _generate_recommendations(self, data: Dict[str, Any], report_type: str) -> str:
        """Generate recommendations content based on report data."""
        recommendations = "# Recommendations\n\n"
        
        # Extract recommendations
        recs = []
        
        for source_id, source_data in data.items():
            if isinstance(source_data, dict):
                # Check for recommendations in different possible structures
                if 'recommendations' in source_data and isinstance(source_data['recommendations'], list):
                    recs.extend(source_data['recommendations'])
                elif 'recommendations' in source_data and isinstance(source_data['recommendations'], dict):
                    for key, value in source_data['recommendations'].items():
                        if isinstance(value, list):
                            recs.extend(value)
                        else:
                            recs.append(f"{key}: {value}")
        
        # Add recommendations to section
        if recs:
            for i, rec in enumerate(recs[:10]):  # Limit to top 10
                recommendations += f"## Recommendation {i+1}\n\n{rec}\n\n"
        
        # Add report type specific content
        if report_type == 'business_case':
            recommendations += """## Implementation Recommendations

Based on the business case analysis, the following implementation recommendations are provided:

1. **Proceed with Investment**: The strong business case supports proceeding with the proposed investment.

2. **Phased Implementation**: Implement the initiative in phases to manage risk and allow for early value realization.

3. **Governance Structure**: Establish a clear governance structure with defined roles, responsibilities, and decision-making processes.

4. **Change Management**: Develop a comprehensive change management plan to address user adoption challenges.

5. **Performance Metrics**: Implement clear performance metrics to track benefit realization and overall success.

6. **Risk Monitoring**: Establish a risk monitoring process to identify and address emerging risks throughout the implementation.

7. **Regular Reviews**: Conduct regular reviews of the business case to ensure continued alignment with organizational objectives and market conditions.
"""
        elif report_type == 'roi_analysis':
            recommendations += """## Financial Recommendations

Based on the ROI analysis, the following financial recommendations are provided:

1. **Approve Investment**: The strong ROI supports approving the proposed investment.

2. **Funding Allocation**: Allocate funding in alignment with the implementation timeline to ensure resource availability.

3. **Benefit Tracking**: Implement a benefit tracking process to monitor actual returns against projected returns.

4. **Cost Control**: Establish cost control measures to prevent budget overruns during implementation.

5. **Contingency Reserve**: Maintain a contingency reserve to address unexpected costs or challenges.

6. **Regular Financial Reviews**: Conduct regular reviews of actual costs and benefits against projections.

7. **Value Optimization**: Continuously seek opportunities to optimize value realization throughout the implementation.
"""
        elif report_type == 'risk_assessment':
            recommendations += """## Risk Management Recommendations

Based on the risk assessment, the following risk management recommendations are provided:

1. **Risk Mitigation Implementation**: Implement the identified mitigation strategies for high-priority risks.

2. **Risk Ownership**: Assign clear ownership for each risk and mitigation strategy.

3. **Risk Monitoring**: Establish a risk monitoring process to track risk status and identify emerging risks.

4. **Contingency Planning**: Develop contingency plans for high-impact risks to enable rapid response if they occur.

5. **Risk Reviews**: Conduct regular risk reviews throughout the initiative lifecycle.

6. **Risk Communication**: Establish clear communication channels for risk-related information.

7. **Risk Culture**: Foster a risk-aware culture that encourages early identification and reporting of potential issues.
"""
        elif report_type == 'value_driver_analysis':
            recommendations += """## Value Optimization Recommendations

Based on the value driver analysis, the following value optimization recommendations are provided:

1. **Prioritize High-Impact Drivers**: Focus implementation efforts on high-impact value drivers to maximize early returns.

2. **Address Interdependencies**: Manage driver interdependencies to leverage potential synergies.

3. **Measurement Framework**: Implement a clear measurement framework to track value realization for each driver.

4. **Value Governance**: Establish a value governance process to ensure ongoing focus on value realization.

5. **Capability Development**: Develop the necessary capabilities to fully realize the potential of each value driver.

6. **Regular Value Reviews**: Conduct regular reviews of value realization against projections.

7. **Continuous Improvement**: Continuously seek opportunities to enhance value realization throughout the implementation.
"""
        else:
            recommendations += """## General Recommendations

Based on the analysis, the following general recommendations are provided:

1. **Strategic Alignment**: Ensure continued alignment with organizational strategic objectives.

2. **Stakeholder Engagement**: Maintain active engagement with key stakeholders throughout the initiative.

3. **Resource Allocation**: Allocate appropriate resources to support successful implementation.

4. **Performance Monitoring**: Implement clear performance metrics to track success.

5. **Risk Management**: Actively manage identified risks throughout the initiative lifecycle.

6. **Regular Reviews**: Conduct regular reviews to ensure the initiative remains on track.

7. **Continuous Improvement**: Continuously seek opportunities for improvement throughout the implementation.
"""
        
        return recommendations
    
    def _generate_conclusion(self, data: Dict[str, Any], report_type: str) -> str:
        """Generate conclusion content based on report data."""
        conclusion = "# Conclusion\n\n"
        
        # Add report type specific content
        if report_type == 'business_case':
            conclusion += """The business case analysis demonstrates a strong case for proceeding with the proposed initiative. The financial analysis shows a positive return on investment, with benefits exceeding costs within a reasonable timeframe. The strategic alignment with organizational objectives further strengthens the case for investment.

The identified risks are manageable with appropriate mitigation strategies, and the implementation approach is feasible with available resources. The phased implementation approach allows for early value realization while managing risk.

Based on the comprehensive analysis presented in this business case, it is recommended to proceed with the proposed initiative. The next steps include securing formal approval, establishing the project governance structure, and initiating the implementation planning process.
"""
        elif report_type == 'roi_analysis':
            conclusion += """The ROI analysis demonstrates a strong financial case for the proposed investment. The analysis shows a positive return on investment, with benefits exceeding costs within a reasonable timeframe. The NPV and IRR calculations further support the financial viability of the investment.

The analysis has considered various risk factors and conducted sensitivity analysis on key variables. The results indicate that the investment remains viable even under conservative assumptions, demonstrating the robustness of the financial case.

Based on the comprehensive financial analysis presented in this report, it is recommended to proceed with the proposed investment. The next steps include securing formal funding approval, establishing a benefit tracking process, and initiating the implementation planning process.
"""
        elif report_type == 'risk_assessment':
            conclusion += """The risk assessment has identified and analyzed potential risks associated with the proposed initiative. The assessment shows that while risks exist, they are manageable with appropriate mitigation strategies. The overall risk profile is within acceptable organizational thresholds.

The assessment has considered risks across multiple categories, including technical, financial, operational, and strategic risks. Mitigation strategies have been developed for all high-priority risks, with clear ownership and implementation timelines.

Based on the comprehensive risk assessment presented in this report, it is recommended to proceed with the proposed initiative while implementing the identified risk mitigation strategies. The next steps include finalizing the risk management plan, assigning risk ownership, and establishing the risk monitoring process.
"""
        elif report_type == 'value_driver_analysis':
            conclusion += """The value driver analysis has identified and quantified key factors that contribute to the overall business value of the proposed initiative. The analysis shows that the initiative has multiple value drivers across different business areas, creating a robust value proposition.

The analysis has considered the interdependencies between value drivers and the implementation complexity of each driver. The prioritization of drivers based on impact and feasibility provides a clear roadmap for value realization.

Based on the comprehensive value driver analysis presented in this report, it is recommended to proceed with the proposed initiative while focusing on the high-priority value drivers. The next steps include finalizing the value realization plan, establishing the measurement framework, and initiating the implementation planning process.
"""
        else:
            conclusion += """The analysis presented in this report provides a comprehensive evaluation of the proposed initiative. The findings indicate a strong case for proceeding, with expected benefits exceeding costs within a reasonable timeframe.

The analysis has considered various factors, including financial returns, strategic alignment, risk profile, and implementation feasibility. The holistic assessment supports a positive recommendation for the initiative.

Based on the comprehensive analysis presented in this report, it is recommended to proceed with the proposed initiative. The next steps include securing formal approval, establishing the implementation structure, and initiating the detailed planning process.
"""
        
        return conclusion
    
    def _generate_appendices(self, data: Dict[str, Any], report_type: str) -> str:
        """Generate appendices content based on report data."""
        appendices = "# Appendices\n\n"
        
        # Add standard appendices based on report type
        if report_type == 'business_case':
            appendices += """## Appendix A: Detailed Financial Analysis

This appendix provides detailed financial calculations supporting the business case, including:

- Detailed benefit calculations for each value driver
- Detailed cost calculations for implementation and ongoing operations
- Year-by-year financial projections
- NPV, IRR, and Payback Period calculations
- Sensitivity analysis results

## Appendix B: Risk Register

This appendix provides a comprehensive risk register, including:

- Complete list of identified risks
- Risk assessment details (probability, impact, risk score)
- Mitigation strategies for each risk
- Risk ownership assignments
- Residual risk assessment

## Appendix C: Implementation Roadmap

This appendix provides a detailed implementation roadmap, including:

- Implementation phases and timelines
- Resource requirements for each phase
- Key milestones and decision points
- Dependencies and critical path analysis
- Success criteria for each phase
"""
        elif report_type == 'roi_analysis':
            appendices += """## Appendix A: Detailed Benefit Calculations

This appendix provides detailed benefit calculations, including:

- Calculation methodology for each benefit category
- Data sources and assumptions
- Year-by-year benefit projections
- Confidence levels for each benefit estimate

## Appendix B: Detailed Cost Calculations

This appendix provides detailed cost calculations, including:

- Calculation methodology for each cost category
- Data sources and assumptions
- Year-by-year cost projections
- Confidence levels for each cost estimate

## Appendix C: Sensitivity Analysis

This appendix provides detailed sensitivity analysis results, including:

- Sensitivity of ROI to changes in key variables
- Scenario analysis (best case, worst case, most likely)
- Break-even analysis
- Monte Carlo simulation results (if applicable)
"""
        elif report_type == 'risk_assessment':
            appendices += """## Appendix A: Complete Risk Register

This appendix provides a comprehensive risk register, including:

- Complete list of identified risks
- Risk assessment details (probability, impact, risk score)
- Mitigation strategies for each risk
- Risk ownership assignments
- Residual risk assessment

## Appendix B: Risk Assessment Methodology

This appendix provides detailed information on the risk assessment methodology, including:

- Risk identification techniques
- Risk categorization framework
- Probability and impact scales
- Risk scoring methodology
- Risk prioritization approach

## Appendix C: Risk Mitigation Plans

This appendix provides detailed risk mitigation plans for high-priority risks, including:

- Mitigation strategy details
- Implementation timelines
- Resource requirements
- Success criteria
- Monitoring approach
"""
        elif report_type == 'value_driver_analysis':
            appendices += """## Appendix A: Detailed Value Driver Analysis

This appendix provides detailed analysis for each value driver, including:

- Calculation methodology
- Data sources and assumptions
- Year-by-year value projections
- Confidence levels for each value estimate

## Appendix B: Value Driver Interdependencies

This appendix provides analysis of value driver interdependencies, including:

- Dependency mapping
- Synergy opportunities
- Potential conflicts
- Optimization strategies

## Appendix C: Value Realization Roadmap

This appendix provides a detailed value realization roadmap, including:

- Implementation phases and timelines
- Value realization milestones
- Measurement approach for each value driver
- Governance structure for value management
"""
        else:
            appendices += """## Appendix A: Detailed Analysis

This appendix provides detailed analysis supporting the main report, including:

- Calculation methodologies
- Data sources and assumptions
- Detailed results
- Confidence levels for key estimates

## Appendix B: Supporting Documentation

This appendix provides supporting documentation referenced in the main report, including:

- Reference materials
- Industry benchmarks
- Relevant standards and best practices
- External research findings

## Appendix C: Implementation Considerations

This appendix provides detailed implementation considerations, including:

- Implementation approach options
- Resource requirements
- Timeline considerations
- Critical success factors
"""
        
        return appendices
    
    def _render_charts(self, report_structure: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Render all charts for the report."""
        rendered_charts = {}
        
        for chart in report_structure['charts']:
            chart_type = chart.get('type')
            chart_id = chart.get('id', f"chart_{len(rendered_charts)}")
            
            if chart_type in self._chart_renderers:
                try:
                    # Get chart data
                    chart_data = self._extract_chart_data(chart, data)
                    
                    # Render chart
                    rendered_chart = self._chart_renderers[chart_type](chart, chart_data)
                    rendered_charts[chart_id] = rendered_chart
                except Exception as e:
                    logger.error(f"Failed to render chart {chart_id} of type {chart_type}: {e}")
                    rendered_charts[chart_id] = {
                        'error': f"Failed to render chart: {str(e)}",
                        'chart_config': chart
                    }
        
        return rendered_charts
    
    def _extract_chart_data(self, chart: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data for a chart from the data sources."""
        chart_data = {}
        
        data_source = chart.get('data_source')
        data_path = chart.get('data_path')
        
        if data_source in data:
            source_data = data[data_source]
            
            # If data_path is specified, navigate to that location in the data
            if data_path and isinstance(source_data, dict):
                parts = data_path.split('.')
                current = source_data
                
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        current = None
                        break
                
                if current is not None:
                    chart_data = current
            else:
                chart_data = source_data
        
        return chart_data
    
    def _render_bar_chart(self, chart_config: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render a bar chart based on configuration and data."""
        # This is a placeholder implementation
        # In a real implementation, this would use a charting library
        return {
            'type': 'bar',
            'title': chart_config.get('title', 'Bar Chart'),
            'data': chart_data,
            'config': chart_config,
            'placeholder': 'Bar chart would be rendered here'
        }
    
    def _render_line_chart(self, chart_config: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render a line chart based on configuration and data."""
        # This is a placeholder implementation
        return {
            'type': 'line',
            'title': chart_config.get('title', 'Line Chart'),
            'data': chart_data,
            'config': chart_config,
            'placeholder': 'Line chart would be rendered here'
        }
    
    def _render_pie_chart(self, chart_config: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render a pie chart based on configuration and data."""
        # This is a placeholder implementation
        return {
            'type': 'pie',
            'title': chart_config.get('title', 'Pie Chart'),
            'data': chart_data,
            'config': chart_config,
            'placeholder': 'Pie chart would be rendered here'
        }
    
    def _render_area_chart(self, chart_config: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render an area chart based on configuration and data."""
        # This is a placeholder implementation
        return {
            'type': 'area',
            'title': chart_config.get('title', 'Area Chart'),
            'data': chart_data,
            'config': chart_config,
            'placeholder': 'Area chart would be rendered here'
        }
    
    def _render_scatter_chart(self, chart_config: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render a scatter chart based on configuration and data."""
        # This is a placeholder implementation
        return {
            'type': 'scatter',
            'title': chart_config.get('title', 'Scatter Chart'),
            'data': chart_data,
            'config': chart_config,
            'placeholder': 'Scatter chart would be rendered here'
        }
    
    def _render_radar_chart(self, chart_config: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render a radar chart based on configuration and data."""
        # This is a placeholder implementation
        return {
            'type': 'radar',
            'title': chart_config.get('title', 'Radar Chart'),
            'data': chart_data,
            'config': chart_config,
            'placeholder': 'Radar chart would be rendered here'
        }
    
    def _render_heatmap(self, chart_config: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render a heatmap based on configuration and data."""
        # This is a placeholder implementation
        return {
            'type': 'heatmap',
            'title': chart_config.get('title', 'Heatmap'),
            'data': chart_data,
            'config': chart_config,
            'placeholder': 'Heatmap would be rendered here'
        }
    
    def _render_sankey_diagram(self, chart_config: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render a sankey diagram based on configuration and data."""
        # This is a placeholder implementation
        return {
            'type': 'sankey',
            'title': chart_config.get('title', 'Sankey Diagram'),
            'data': chart_data,
            'config': chart_config,
            'placeholder': 'Sankey diagram would be rendered here'
        }
    
    def _render_table(self, chart_config: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render a table based on configuration and data."""
        # This is a placeholder implementation
        return {
            'type': 'table',
            'title': chart_config.get('title', 'Table'),
            'data': chart_data,
            'config': chart_config,
            'placeholder': 'Table would be rendered here'
        }
    
    def _render_gauge_chart(self, chart_config: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Render a gauge chart based on configuration and data."""
        # This is a placeholder implementation
        return {
            'type': 'gauge',
            'title': chart_config.get('title', 'Gauge Chart'),
            'data': chart_data,
            'config': chart_config,
            'placeholder': 'Gauge chart would be rendered here'
        }
    
    def _generate_pdf_report(self, report_structure: Dict[str, Any], rendered_charts: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a PDF report based on the report structure and rendered charts."""
        # This is a placeholder implementation
        # In a real implementation, this would use a PDF generation library
        return {
            'format': 'pdf',
            'title': report_structure['title'],
            'content': report_structure,
            'charts': rendered_charts,
            'placeholder': 'PDF report would be generated here'
        }
    
    def _generate_html_report(self, report_structure: Dict[str, Any], rendered_charts: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an HTML report based on the report structure and rendered charts."""
        # This is a placeholder implementation
        # In a real implementation, this would use an HTML template engine
        
        # Generate a simple HTML structure
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{report_structure['title']}</title>
    <style>
        body {{ font-family: {report_structure['styles'].get('font_family', 'Arial, sans-serif')}; line-height: {report_structure['styles'].get('line_height', 1.5)}; }}
        h1 {{ font-size: {report_structure['styles'].get('header_font_size', '24px')}; }}
        p {{ font-size: {report_structure['styles'].get('body_font_size', '12px')}; }}
    </style>
</head>
<body>
    <h1>{report_structure['title']}</h1>
    <h2>{report_structure['subtitle']}</h2>
    <p>Date: {report_structure['date']}</p>
    
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
"""
        
        # Add table of contents
        for section in report_structure['sections']:
            html += f'            <li><a href="#{section["id"]}">{section["title"]}</a></li>\n'
        
        html += """        </ul>
    </div>
    
"""
        
        # Add sections
        for section in report_structure['sections']:
            html += f'    <div id="{section["id"]}" class="section">\n'
            html += f'        <h2>{section["title"]}</h2>\n'
            html += f'        <div class="content">\n'
            
            # Add section content
            content_lines = section['content'].split('\n')
            for line in content_lines:
                if line.startswith('# '):
                    html += f'            <h2>{line[2:]}</h2>\n'
                elif line.startswith('## '):
                    html += f'            <h3>{line[3:]}</h3>\n'
                elif line.startswith('### '):
                    html += f'            <h4>{line[4:]}</h4>\n'
                elif line.startswith('- '):
                    html += f'            <ul><li>{line[2:]}</li></ul>\n'
                elif line.strip() == '':
                    html += '            <br>\n'
                else:
                    html += f'            <p>{line}</p>\n'
            
            html += '        </div>\n'
            
            # Add section charts
            if section['charts']:
                html += '        <div class="charts">\n'
                for chart_config in section['charts']:
                    chart_id = chart_config.get('id')
                    if chart_id in rendered_charts:
                        chart = rendered_charts[chart_id]
                        html += f'            <div class="chart">\n'
                        html += f'                <h3>{chart["title"]}</h3>\n'
                        html += f'                <div class="chart-placeholder">{chart["placeholder"]}</div>\n'
                        html += '            </div>\n'
                html += '        </div>\n'
            
            html += '    </div>\n\n'
        
        html += """    <div class="footer">
        <p>Generated by B2BValue Report Builder Agent</p>
    </div>
</body>
</html>
"""
        
        return {
            'format': 'html',
            'title': report_structure['title'],
            'content': html,
            'charts': rendered_charts
        }
    
    def _generate_markdown_report(self, report_structure: Dict[str, Any], rendered_charts: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a Markdown report based on the report structure and rendered charts."""
        # This is a placeholder implementation
        
        # Generate a simple Markdown structure
        markdown = f"# {report_structure['title']}\n\n"
        markdown += f"## {report_structure['subtitle']}\n\n"
        markdown += f"Date: {report_structure['date']}\n\n"
        
        # Add table of contents
        markdown += "## Table of Contents\n\n"
        for section in report_structure['sections']:
            markdown += f"- [{section['title']}](#{section['id'].replace('_', '-')})\n"
        
        markdown += "\n"
        
        # Add sections
        for section in report_structure['sections']:
            markdown += f"## {section['title']}\n\n"
            
            # Add section content
            markdown += section['content']
            markdown += "\n\n"
            
            # Add section charts
            if section['charts']:
                markdown += "### Charts\n\n"
                for chart_config in section['charts']:
                    chart_id = chart_config.get('id')
                    if chart_id in rendered_charts:
                        chart = rendered_charts[chart_id]
                        markdown += f"#### {chart['title']}\n\n"
                        markdown += f"*{chart['placeholder']}*\n\n"
        
        markdown += "\n\n---\n\nGenerated by B2BValue Report Builder Agent\n"
        
        return {
            'format': 'markdown',
            'title': report_structure['title'],
            'content': markdown,
            'charts': rendered_charts
        }
    
    def _generate_json_report(self, report_structure: Dict[str, Any], rendered_charts: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a JSON report based on the report structure and rendered charts."""
        # This is a straightforward implementation
        
        json_report = {
            'format': 'json',
            'title': report_structure['title'],
            'subtitle': report_structure['subtitle'],
            'date': report_structure['date'],
            'template': report_structure['template'],
            'metadata': report_structure['metadata'],
            'sections': []
        }
        
        # Add sections
        for section in report_structure['sections']:
            json_section = {
                'id': section['id'],
                'title': section['title'],
                'content': section['content'],
                'charts': []
            }
            
            # Add section charts
            for chart_config in section['charts']:
                chart_id = chart_config.get('id')
                if chart_id in rendered_charts:
                    json_section['charts'].append(rendered_charts[chart_id])
            
            json_report['sections'].append(json_section)
        
        return json_report
    
    def _generate_excel_report(self, report_structure: Dict[str, Any], rendered_charts: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an Excel report based on the report structure and rendered charts."""
        # This is a placeholder implementation
        # In a real implementation, this would use an Excel generation library
        return {
            'format': 'excel',
            'title': report_structure['title'],
            'content': report_structure,
            'charts': rendered_charts,
            'placeholder': 'Excel report would be generated here'
        }
    
    def _generate_powerpoint_report(self, report_structure: Dict[str, Any], rendered_charts: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a PowerPoint report based on the report structure and rendered charts."""
        # This is a placeholder implementation
        # In a real implementation, this would use a PowerPoint generation library
        return {
            'format': 'powerpoint',
            'title': report_structure['title'],
            'content': report_structure,
            'charts': rendered_charts,
            'placeholder': 'PowerPoint presentation would be generated here'
        }
    
    def _store_report_in_memory(self, report_id: str, report_data: Dict[str, Any]) -> None:
        """Store the generated report in memory for future reference."""
        self._report_cache[report_id] = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'report': report_data
        }
    
    async def _store_report_in_mcp(self, report_id: str, report_data: Dict[str, Any]) -> str:
        """Store the generated report in MCP for persistence."""
        try:
            # Create a knowledge entity for the report
            report_entity = KnowledgeEntity(
                id=report_id,
                title=report_data.get('title', 'Generated Report'),
                content=json.dumps(report_data),
                content_type='application/json',
                creator_id=self.agent_id,
                metadata={
                    'report_type': report_data.get('report_type', 'unknown'),
                    'output_format': report_data.get('format', 'unknown'),
                    'template': report_data.get('template', 'unknown'),
                    'generated_at': datetime.now(timezone.utc).isoformat(),
                    'agent_id': self.agent_id
                }
            )
            
            # Store the entity in MCP
            entity_id = await self.mcp_client.store_memory(report_entity)
            logger.info(f"Stored report {report_id} in MCP with entity ID {entity_id}")
            
            return entity_id
        except Exception as e:
            logger.error(f"Failed to store report {report_id} in MCP: {e}")
            return None
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Generate a report based on the provided inputs.

        Args:
            inputs: Dictionary containing:
                - report_type: Type of report to generate
                - data_sources: List of data sources to use
                - output_format: Desired output format
                - template: Report template to use
                - sections: List of sections to include
                - charts: List of charts to include
                - filters: Filters to apply to the data
                - custom_styles: Custom styling options
                - include_appendices: Whether to include appendices
                - include_executive_summary: Whether to include executive summary

        Returns:
            AgentResult with the generated report
        """
        start_time = time.monotonic()
        
        try:
            logger.info(f"Starting report generation for agent {self.agent_id}")
            
            # Validate inputs
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": f"Validation failed: {validation_result.errors[0]}"},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Extract inputs
            report_type = inputs['report_type']
            data_sources = inputs['data_sources']
            output_format = inputs.get('output_format', ReportFormat.PDF.value)
            template_name = inputs.get('template', ReportTemplate.EXECUTIVE_SUMMARY.value)
            
            # Generate a unique report ID
            report_id = f"report_{int(time.time())}_{report_type}_{output_format}"
            
            # Check cache for existing report
            cache_key = f"{report_type}_{output_format}_{template_name}_{hash(str(data_sources))}"
            if cache_key in self._report_cache:
                cached_report = self._report_cache[cache_key]
                logger.info(f"Using cached report for {cache_key}")
                
                # Update timestamp
                cached_report['timestamp'] = datetime.now(timezone.utc).isoformat()
                
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data={
                        "report_id": report_id,
                        "report": cached_report['report'],
                        "cached": True,
                        "cache_timestamp": cached_report['timestamp']
                    },
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Fetch data from sources
            data = await self._fetch_data_from_sources(data_sources)
            
            # Prepare report structure
            report_structure = self._prepare_report_structure(inputs, data)
            
            # Generate content for each section
            for section in report_structure['sections']:
                section['content'] = self._generate_section_content(section, data, report_type)
            
            # Render charts
            rendered_charts = self._render_charts(report_structure, data)
            
            # Generate report in requested format
            if output_format in self._report_generators:
                report = self._report_generators[output_format](report_structure, rendered_charts)
            else:
                # Default to PDF if format not supported
                report = self._report_generators[ReportFormat.PDF.value](report_structure, rendered_charts)
            
            # Add metadata to report
            report['report_id'] = report_id
            report['report_type'] = report_type
            report['generated_at'] = datetime.now(timezone.utc).isoformat()
            report['agent_id'] = self.agent_id
            
            # Store report in cache
            self._store_report_in_memory(report_id, report)
            
            # Store report in MCP
            mcp_entity_id = await self._store_report_in_mcp(report_id, report)
            
            # Prepare result data
            result_data = {
                "report_id": report_id,
                "report": report,
                "mcp_entity_id": mcp_entity_id,
                "metadata": {
                    "report_type": report_type,
                    "output_format": output_format,
                    "template": template_name,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "data_sources": [s.get('name', s.get('source_id', 'unknown')) for s in data_sources]
                }
            }
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"Report generation completed in {execution_time_ms}ms")
            
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=result_data,
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"Report generation failed: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Report generation failed: {str(e)}"},
                execution_time_ms=execution_time_ms
            )