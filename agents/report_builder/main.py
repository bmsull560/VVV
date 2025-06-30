"""
Report Builder Agent

This agent generates comprehensive reports and visualizations based on business case
data, supporting multiple formats, templates, and customization options to effectively
communicate business value analysis to different stakeholders.
"""

import logging
import time
import json
import hashlib
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from datetime import datetime, timezone

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from memory.memory_types import KnowledgeEntity

logger = logging.getLogger(__name__)

class ReportFormat(str, Enum):
    """Supported report output formats."""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"

class ReportTemplate(str, Enum):
    """Supported report templates."""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_ANALYSIS = "detailed_analysis"
    FINANCIAL_DASHBOARD = "financial_dashboard"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    STAKEHOLDER_PRESENTATION = "stakeholder_presentation"
    CUSTOM = "custom"

class ChartType(str, Enum):
    """Supported chart types."""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    BUBBLE = "bubble"
    TABLE = "table"
    GAUGE = "gauge"

class DataSourceType(str, Enum):
    """Supported data source types."""
    DIRECT = "direct"
    MCP_ENTITY = "mcp_entity"
    MCP_WORKFLOW = "mcp_workflow"
    DATABASE = "database"
    API = "api"
    FILE = "file"

class ReportBuilderAgent(BaseAgent):
    """
    Production-ready agent for generating comprehensive reports based on 
    business case data with support for multiple formats and templates.
    """

    def __init__(self, agent_id: str, mcp_client, config: Dict[str, Any]):
        # Set up validation rules
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
                    'custom_styles': 'object'
                },
                'field_constraints': {
                    'output_format': {'enum': [f.value for f in ReportFormat]},
                    'template': {'enum': [t.value for t in ReportTemplate]}
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Initialize report builder configuration
        self.default_format = config.get('default_format', ReportFormat.HTML.value)
        self.default_template = config.get('default_template', ReportTemplate.EXECUTIVE_SUMMARY.value)
        self.enable_caching = config.get('enable_caching', True)
        self.report_cache = {}
        self.default_color_scheme = config.get('default_color_scheme', 'blue')
        self.default_font_family = config.get('default_font_family', 'Arial, sans-serif')
        self.image_format = config.get('image_format', 'svg')

    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Enhanced validation for report builder inputs."""
        errors = []
        
        # Validate data sources
        data_sources = inputs.get('data_sources', [])
        if not data_sources:
            errors.append("At least one data source is required")
        else:
            for i, source in enumerate(data_sources):
                if not isinstance(source, dict):
                    errors.append(f"Data source {i} must be an object")
                    continue
                
                if 'type' not in source:
                    errors.append(f"Data source {i} must have a 'type' field")
                elif source['type'] not in [t.value for t in DataSourceType]:
                    errors.append(f"Data source {i} has invalid type: {source['type']}")
                
                # Validate source-specific required fields
                if source.get('type') == DataSourceType.DIRECT.value:
                    if 'name' not in source:
                        errors.append(f"Direct data source {i} must have a 'name' field")
                    if 'data' not in source:
                        errors.append(f"Direct data source {i} must have a 'data' field")
                
                elif source.get('type') in [DataSourceType.MCP_ENTITY.value, DataSourceType.MCP_WORKFLOW.value]:
                    if 'source_id' not in source:
                        errors.append(f"{source.get('type')} data source {i} must have a 'source_id' field")
                
                elif source.get('type') == DataSourceType.DATABASE.value:
                    if 'query' not in source:
                        errors.append(f"Database data source {i} must have a 'query' field")
                
                elif source.get('type') == DataSourceType.API.value:
                    if 'endpoint' not in source:
                        errors.append(f"API data source {i} must have an 'endpoint' field")
                
                elif source.get('type') == DataSourceType.FILE.value:
                    if 'file_path' not in source:
                        errors.append(f"File data source {i} must have a 'file_path' field")
        
        # Validate charts if provided
        charts = inputs.get('charts', [])
        if charts:
            for i, chart in enumerate(charts):
                if not isinstance(chart, dict):
                    errors.append(f"Chart {i} must be an object")
                    continue
                
                required_chart_fields = ['id', 'type', 'title', 'data_source']
                for field in required_chart_fields:
                    if field not in chart:
                        errors.append(f"Chart {i} missing required field: {field}")
                
                if 'type' in chart and chart['type'] not in [t.value for t in ChartType]:
                    errors.append(f"Chart {i} has invalid type: {chart['type']}")
        
        return errors

    async def _fetch_data_from_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data from a specified data source."""
        source_type = source.get('type')
        
        try:
            if source_type == DataSourceType.DIRECT.value:
                # Direct data is already provided
                return {
                    'name': source.get('name', 'direct_data'),
                    'data': source.get('data', {}),
                    'status': 'success'
                }
            
            elif source_type == DataSourceType.MCP_ENTITY.value:
                # Fetch data from MCP entity
                source_id = source.get('source_id')
                entity = await self.mcp_client.get_entity(source_id)
                
                if entity:
                    return {
                        'name': f"entity_{source_id}",
                        'data': entity.data,
                        'metadata': entity.metadata,
                        'status': 'success'
                    }
                else:
                    return {
                        'name': f"entity_{source_id}",
                        'error': f"Entity {source_id} not found",
                        'status': 'error'
                    }
            
            elif source_type == DataSourceType.MCP_WORKFLOW.value:
                # Fetch data from MCP workflow
                source_id = source.get('source_id')
                workflow = await self.mcp_client.get_workflow(source_id)
                
                if workflow:
                    return {
                        'name': f"workflow_{source_id}",
                        'data': workflow.data,
                        'metadata': workflow.metadata,
                        'status': 'success'
                    }
                else:
                    return {
                        'name': f"workflow_{source_id}",
                        'error': f"Workflow {source_id} not found",
                        'status': 'error'
                    }
            
            # Note: The following source types would be implemented in a production system
            # but are included here as placeholders for completeness
            
            elif source_type == DataSourceType.DATABASE.value:
                # Placeholder for database data source
                logger.warning("Database data source not fully implemented")
                return {
                    'name': source.get('name', 'database_data'),
                    'data': {},
                    'error': "Database data source not fully implemented",
                    'status': 'error'
                }
            
            elif source_type == DataSourceType.API.value:
                # Placeholder for API data source
                logger.warning("API data source not fully implemented")
                return {
                    'name': source.get('name', 'api_data'),
                    'data': {},
                    'error': "API data source not fully implemented",
                    'status': 'error'
                }
            
            elif source_type == DataSourceType.FILE.value:
                # Placeholder for file data source
                logger.warning("File data source not fully implemented")
                return {
                    'name': source.get('name', 'file_data'),
                    'data': {},
                    'error': "File data source not fully implemented",
                    'status': 'error'
                }
            
            else:
                return {
                    'name': 'unknown_source',
                    'error': f"Unknown data source type: {source_type}",
                    'status': 'error'
                }
        
        except Exception as e:
            logger.error(f"Error fetching data from source {source_type}: {e}")
            return {
                'name': source.get('name', 'unknown'),
                'error': f"Error fetching data: {str(e)}",
                'status': 'error'
            }

    def _generate_section_content(self, section_type: str, data: Dict[str, Any], report_format: str) -> str:
        """Generate content for a specific report section based on the data and format."""
        # Simplified logic for generating section content
        # In a full implementation, this would include complex logic for each section type
        
        if section_type == 'executive_summary':
            return self._format_content(
                f"This report provides a comprehensive analysis of the business case. "
                f"Key metrics include an ROI of {data.get('roi_metrics', {}).get('roi_percentage', 'N/A')}% "
                f"and a payback period of {data.get('roi_metrics', {}).get('payback_period_months', 'N/A')} months.",
                report_format
            )
        
        elif section_type == 'financial_analysis':
            roi = data.get('roi_metrics', {}).get('roi_percentage', 'N/A')
            npv = data.get('roi_metrics', {}).get('npv', 'N/A')
            payback = data.get('roi_metrics', {}).get('payback_period_months', 'N/A')
            total_benefits = data.get('roi_metrics', {}).get('total_benefits', 'N/A')
            total_costs = data.get('roi_metrics', {}).get('total_costs', 'N/A')
            
            content = f"Financial Analysis:\n\n"
            content += f"ROI: {roi}%\n"
            content += f"NPV: ${npv:,.2f}\n" if isinstance(npv, (int, float)) else f"NPV: {npv}\n"
            content += f"Payback Period: {payback} months\n"
            content += f"Total Benefits: ${total_benefits:,.2f}\n" if isinstance(total_benefits, (int, float)) else f"Total Benefits: {total_benefits}\n"
            content += f"Total Costs: ${total_costs:,.2f}" if isinstance(total_costs, (int, float)) else f"Total Costs: {total_costs}"
            
            return self._format_content(content, report_format)
        
        elif section_type == 'value_drivers':
            content = f"Value Drivers:\n\n"
            
            value_drivers = data.get('value_drivers', [])
            if value_drivers:
                for i, driver in enumerate(value_drivers, 1):
                    name = driver.get('name', f"Driver {i}")
                    description = driver.get('description', 'No description')
                    value = driver.get('value', 'N/A')
                    
                    content += f"{i}. {name}: {description}\n"
                    if isinstance(value, (int, float)):
                        content += f"   Value: ${value:,.2f}\n"
                    else:
                        content += f"   Value: {value}\n"
            else:
                content += "No value drivers found in the data."
            
            return self._format_content(content, report_format)
        
        elif section_type == 'risk_assessment':
            content = f"Risk Assessment:\n\n"
            
            risks = data.get('risks', [])
            if risks:
                for i, risk in enumerate(risks, 1):
                    name = risk.get('name', f"Risk {i}")
                    category = risk.get('category', 'Unknown')
                    probability = risk.get('probability', 'Unknown')
                    impact = risk.get('impact', 'Unknown')
                    
                    content += f"{i}. {name} (Category: {category})\n"
                    content += f"   Probability: {probability}, Impact: {impact}\n"
            else:
                content += "No risks found in the data."
            
            return self._format_content(content, report_format)
        
        elif section_type == 'recommendations':
            content = f"Recommendations:\n\n"
            
            recommendations = data.get('recommendations', [])
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    if isinstance(rec, str):
                        content += f"{i}. {rec}\n"
                    elif isinstance(rec, dict) and 'text' in rec:
                        content += f"{i}. {rec['text']}\n"
            else:
                content += "No specific recommendations available."
            
            return self._format_content(content, report_format)
        
        elif section_type == 'methodology':
            return self._format_content(
                f"This analysis follows a structured methodology for business value assessment, "
                f"including quantification of value drivers, ROI calculation, risk analysis, "
                f"and sensitivity testing to ensure robust results.",
                report_format
            )
        
        elif section_type == 'appendix':
            content = f"Appendix:\n\n"
            content += f"This report was generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}.\n"
            content += f"The analysis was performed using the B2BValue platform.\n"
            
            return self._format_content(content, report_format)
        
        else:
            # Default section
            return self._format_content(f"Section content for {section_type}", report_format)

    def _format_content(self, content: str, output_format: str) -> str:
        """Format content based on the desired output format."""
        if output_format == ReportFormat.MARKDOWN.value:
            # Convert basic text to Markdown
            # This is a simplified implementation; a real one would have more robust conversion
            return content
        
        elif output_format == ReportFormat.HTML.value:
            # Convert to HTML
            paragraphs = content.split('\n\n')
            html_content = ''.join([f"<p>{p.replace('\n', '<br>')}</p>" for p in paragraphs])
            return html_content
        
        elif output_format == ReportFormat.JSON.value:
            # Just return as a string for JSON
            return content
        
        else:
            # Default to plain text
            return content

    def _generate_chart(self, chart_config: Dict[str, Any], data_sources: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a chart based on the configuration and data sources."""
        chart_id = chart_config.get('id', f"chart_{int(time.time())}")
        chart_type = chart_config.get('type', 'bar')
        chart_title = chart_config.get('title', 'Chart')
        data_source_name = chart_config.get('data_source')
        data_path = chart_config.get('data_path')
        
        # Get data from the specified source
        source_data = data_sources.get(data_source_name, {}).get('data', {})
        
        # Extract data for the chart
        chart_data = source_data
        if data_path:
            for key in data_path.split('.'):
                chart_data = chart_data.get(key, {})
        
        # Basic chart generation (placeholder)
        # In a real implementation, this would generate SVG, Canvas, or other chart formats
        chart = {
            'id': chart_id,
            'type': chart_type,
            'title': chart_title,
            'data': chart_data,
            'config': chart_config.get('config', {}),
            'format': self.image_format
        }
        
        return chart

    def _apply_template(self, template: str, report_type: str, sections: List[str], format: str) -> Dict[str, Any]:
        """Apply a template to structure the report."""
        template_sections = []
        
        # Define template-specific sections
        if template == ReportTemplate.EXECUTIVE_SUMMARY.value:
            template_sections = ['executive_summary', 'financial_analysis', 'key_findings', 'recommendations']
        
        elif template == ReportTemplate.DETAILED_ANALYSIS.value:
            template_sections = ['executive_summary', 'introduction', 'methodology', 'value_drivers', 
                                'financial_analysis', 'risk_assessment', 'sensitivity_analysis', 
                                'recommendations', 'appendix']
        
        elif template == ReportTemplate.FINANCIAL_DASHBOARD.value:
            template_sections = ['financial_highlights', 'roi_summary', 'cost_benefit_analysis', 
                                'cash_flow_projections', 'sensitivity_analysis']
        
        elif template == ReportTemplate.TECHNICAL_DEEP_DIVE.value:
            template_sections = ['executive_summary', 'technical_overview', 'architecture', 
                                'implementation_details', 'performance_metrics', 
                                'security_considerations', 'technical_risks', 'appendix']
        
        elif template == ReportTemplate.STAKEHOLDER_PRESENTATION.value:
            template_sections = ['executive_summary', 'business_context', 'proposed_solution', 
                                'value_proposition', 'financial_analysis', 'timeline', 
                                'next_steps']
        
        # If custom or sections provided, use those
        final_sections = sections if sections else template_sections
        
        # Format-specific styling
        styles = {}
        if format == ReportFormat.HTML.value:
            styles = {
                'color_scheme': self.default_color_scheme,
                'font_family': self.default_font_family,
                'header_style': 'background-color: #f5f5f5; padding: 20px; border-bottom: 1px solid #ddd;',
                'section_style': 'margin: 20px 0; padding: 10px;',
                'chart_style': 'margin: 20px 0;',
                'table_style': 'border-collapse: collapse; width: 100%;',
                'footer_style': 'background-color: #f5f5f5; padding: 20px; border-top: 1px solid #ddd;'
            }
        elif format == ReportFormat.MARKDOWN.value:
            styles = {
                'header_level': 1,
                'subheader_level': 2,
                'emphasis': '**',
                'list_style': '-'
            }
        
        # Determine title based on report type
        if report_type == 'business_case':
            title = 'Business Value Analysis Report'
        elif report_type == 'roi_analysis':
            title = 'ROI Analysis Report'
        elif report_type == 'risk_assessment':
            title = 'Risk Assessment Report'
        elif report_type == 'value_driver_analysis':
            title = 'Value Driver Analysis Report'
        else:
            title = f'{report_type.replace("_", " ").title()} Report'
        
        # Return template structure
        return {
            'title': title,
            'sections': final_sections,
            'template': template,
            'styles': styles,
            'format': format
        }

    def _generate_report(self, report_type: str, template: str, format: str, 
                        sections: List[str], data_sources: Dict[str, Dict[str, Any]], 
                        charts: List[Dict[str, Any]], custom_styles: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a complete report based on the inputs."""
        # Apply template
        report_structure = self._apply_template(template, report_type, sections, format)
        
        # Apply custom styles if provided
        if custom_styles:
            report_structure['styles'].update(custom_styles)
        
        # Generate content for each section
        report_sections = []
        
        # Merge all data for general access
        all_data = {}
        for source_name, source_data in data_sources.items():
            if source_data.get('status') == 'success':
                all_data.update(source_data.get('data', {}))
        
        # Create each section
        for section_type in report_structure['sections']:
            section_content = self._generate_section_content(section_type, all_data, format)
            report_sections.append({
                'id': f"section_{section_type}",
                'type': section_type,
                'title': section_type.replace('_', ' ').title(),
                'content': section_content
            })
        
        # Generate charts
        report_charts = []
        for chart_config in charts:
            chart = self._generate_chart(chart_config, data_sources)
            report_charts.append(chart)
        
        # Build the complete report
        report = {
            'id': f"report_{int(time.time())}",
            'title': report_structure['title'],
            'type': report_type,
            'format': format,
            'template': template,
            'sections': report_sections,
            'charts': report_charts,
            'styles': report_structure['styles'],
            'metadata': {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'generator_agent': self.agent_id,
                'data_sources': list(data_sources.keys())
            }
        }
        
        # Create final content based on format
        if format == ReportFormat.JSON.value:
            report['content'] = json.dumps(report, indent=2)
        
        elif format == ReportFormat.HTML.value:
            # Generate HTML content
            html_content = f"<!DOCTYPE html>\n<html>\n<head>\n"
            html_content += f"  <title>{report['title']}</title>\n"
            html_content += f"  <style>\n"
            html_content += f"    body {{ font-family: {report_structure['styles']['font_family']}; margin: 0; padding: 0; }}\n"
            html_content += f"    .header {{ {report_structure['styles']['header_style']} }}\n"
            html_content += f"    .section {{ {report_structure['styles']['section_style']} }}\n"
            html_content += f"    .chart {{ {report_structure['styles']['chart_style']} }}\n"
            html_content += f"    .footer {{ {report_structure['styles']['footer_style']} }}\n"
            html_content += f"  </style>\n"
            html_content += f"</head>\n<body>\n"
            
            # Header
            html_content += f"  <div class='header'>\n"
            html_content += f"    <h1>{report['title']}</h1>\n"
            html_content += f"  </div>\n"
            
            # Sections
            for section in report['sections']:
                html_content += f"  <div class='section'>\n"
                html_content += f"    <h2>{section['title']}</h2>\n"
                html_content += f"    <div>{section['content']}</div>\n"
                html_content += f"  </div>\n"
            
            # Charts
            for chart in report['charts']:
                html_content += f"  <div class='chart'>\n"
                html_content += f"    <h3>{chart['title']}</h3>\n"
                html_content += f"    <div id='{chart['id']}'>Chart placeholder</div>\n"
                html_content += f"  </div>\n"
            
            # Footer
            html_content += f"  <div class='footer'>\n"
            html_content += f"    <p>Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>\n"
            html_content += f"  </div>\n"
            
            html_content += f"</body>\n</html>"
            
            report['content'] = html_content
        
        elif format == ReportFormat.MARKDOWN.value:
            # Generate Markdown content
            md_content = f"# {report['title']}\n\n"
            
            # Sections
            for section in report['sections']:
                md_content += f"## {section['title']}\n\n"
                md_content += f"{section['content']}\n\n"
            
            # Charts (reference only in Markdown)
            if report['charts']:
                md_content += f"## Charts\n\n"
                for chart in report['charts']:
                    md_content += f"### {chart['title']}\n\n"
                    md_content += f"*Chart placeholder for {chart['id']}*\n\n"
            
            # Footer
            md_content += f"---\n\n"
            md_content += f"*Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*"
            
            report['content'] = md_content
        
        return report

    def _generate_cache_key(self, inputs: Dict[str, Any]) -> str:
        """Generate a cache key based on inputs for report caching."""
        # Remove volatile elements that shouldn't affect caching
        cache_inputs = inputs.copy()
        cache_inputs.pop('timestamp', None)
        
        # Convert to JSON and hash
        input_json = json.dumps(cache_inputs, sort_keys=True)
        return hashlib.md5(input_json.encode()).hexdigest()

    async def _store_report_in_mcp(self, report: Dict[str, Any]) -> str:
        """Store the report in MCP for future reference."""
        entity = KnowledgeEntity(
            entity_type="generated_report",
            data=report,
            metadata={
                'report_id': report['id'],
                'report_type': report['type'],
                'format': report['format'],
                'template': report['template'],
                'agent_id': self.agent_id,
                'timestamp': time.time()
            }
        )
        
        entities = await self.mcp_client.create_entities([entity])
        return entities.get('entity_ids', ['unknown'])[0] if isinstance(entities, dict) else 'unknown'

    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Generate a comprehensive report based on the provided inputs.
        
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
        """
        start_time = time.monotonic()
        
        try:
            # Add timestamp for cache differentiation and tracking
            inputs['timestamp'] = time.time()
            
            # Validate inputs
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={"error": f"Validation failed: {validation_result.errors[0]}", "details": validation_result.errors},
                    execution_time_ms=int((time.monotonic() - start_time) * 1000)
                )
            
            # Check cache if enabled
            if self.enable_caching:
                cache_key = self._generate_cache_key(inputs)
                if cache_key in self.report_cache:
                    logger.info(f"Using cached report for inputs {cache_key}")
                    cached_report = self.report_cache[cache_key]
                    
                    # Update the report ID to ensure uniqueness
                    report_id = f"report_{int(time.time())}"
                    cached_report['report']['id'] = report_id
                    
                    return AgentResult(
                        status=AgentStatus.COMPLETED,
                        data={"report_id": report_id, "report": cached_report['report'], "cached": True},
                        execution_time_ms=int((time.monotonic() - start_time) * 1000)
                    )
            
            # Extract inputs
            report_type = inputs['report_type']
            data_sources = inputs['data_sources']
            output_format = inputs.get('output_format', self.default_format)
            template = inputs.get('template', self.default_template)
            sections = inputs.get('sections', [])
            charts = inputs.get('charts', [])
            filters = inputs.get('filters', {})
            custom_styles = inputs.get('custom_styles', {})
            include_executive_summary = inputs.get('include_executive_summary', True)
            
            # Fetch data from sources
            source_data = {}
            for source in data_sources:
                source_result = await self._fetch_data_from_source(source)
                source_name = source_result.get('name') or source.get('name', f"source_{len(source_data)}")
                source_data[source_name] = source_result
            
            # Generate the report
            report = self._generate_report(
                report_type=report_type,
                template=template,
                format=output_format,
                sections=sections,
                data_sources=source_data,
                charts=charts,
                custom_styles=custom_styles
            )
            
            # Store the report in MCP
            report_entity_id = await self._store_report_in_mcp(report)
            
            # Update report with entity ID
            report['entity_id'] = report_entity_id
            
            # Cache the report if caching is enabled
            if self.enable_caching:
                cache_key = self._generate_cache_key(inputs)
                self.report_cache[cache_key] = {
                    'report': report,
                    'timestamp': time.time()
                }
            
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.info(f"Generated {output_format} report of type {report_type} in {execution_time_ms}ms")
            
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data={"report_id": report['id'], "report": report},
                execution_time_ms=execution_time_ms
            )
            
        except Exception as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(f"Report generation failed: {str(e)}", exc_info=True)
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Report generation failed: {str(e)}"},
                execution_time_ms=execution_time_ms
            )