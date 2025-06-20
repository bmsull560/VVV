"""
Data Integration Agent Example

This module demonstrates how to implement a Data Integration Agent
that securely connects to external data sources and retrieves
relevant business metrics as part of the business case creation workflow.
"""

import logging
import time
import re
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import asyncio

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus
from agents.core.mcp_client import MCPClient

logger = logging.getLogger(__name__)

class DataIntegrationAgent(BaseAgent):
    """
    Agent that securely connects to external data sources and retrieves business metrics.
    
    This agent demonstrates the use of the centralized input validation system,
    secure external connections, and proper handling of sensitive data
    in accordance with the B2BValue security model.
    """

    def __init__(self, agent_id: str, mcp_client: Any, config: Dict[str, Any]):
        """
        Initialize the Data Integration Agent with validation rules.
        
        Args:
            agent_id: Unique identifier for this agent
            mcp_client: MCP client instance for memory access
            config: Configuration dictionary
        """
        # Define validation rules in config
        if 'input_validation' not in config:
            config['input_validation'] = {
                # Fields that must be present
                'required_fields': ['connection_type', 'metrics_to_retrieve'],
                
                # Type checking for fields
                'field_types': {
                    'connection_type': 'string',
                    'metrics_to_retrieve': 'array',
                    'connection_credentials': 'object',
                    'source_system': 'string',
                    'query_parameters': 'object'
                },
                
                # Constraints for fields
                'field_constraints': {
                    'connection_type': {
                        'enum': ['crm', 'erp', 'database', 'api', 'file']
                    },
                    'metrics_to_retrieve': {
                        'min_items': 1,
                        'item_type': 'string'
                    }
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
        
        # Initialize supported data source connectors
        self._connectors = self._initialize_connectors()
        
        # Security settings
        self.data_sensitivity = config.get('data_sensitivity', 'high')
        self.require_encryption = config.get('require_encryption', True)
    
    def _initialize_connectors(self) -> Dict[str, Any]:
        """
        Initialize supported data source connectors.
        
        In a real implementation, this would initialize actual connector classes.
        
        Returns:
            Dict mapping connection types to connector handlers
        """
        # This is a simplified example - in production, these would be actual connector classes
        return {
            "crm": {
                "name": "CRM Connector",
                "supported_systems": ["salesforce", "dynamics365", "hubspot"],
                "required_credentials": ["api_key", "instance_url"],
                "supported_metrics": [
                    "customer_acquisition_cost", 
                    "customer_lifetime_value",
                    "sales_cycle_length",
                    "conversion_rate",
                    "lead_volume"
                ]
            },
            "erp": {
                "name": "ERP Connector",
                "supported_systems": ["sap", "oracle", "netsuite"],
                "required_credentials": ["username", "password", "instance_id"],
                "supported_metrics": [
                    "operational_cost",
                    "inventory_turnover",
                    "procurement_cost",
                    "production_efficiency",
                    "resource_utilization"
                ]
            },
            "database": {
                "name": "Database Connector",
                "supported_systems": ["mysql", "postgresql", "sqlserver", "oracle"],
                "required_credentials": ["connection_string"],
                "supported_metrics": [
                    "custom_query_results"
                ]
            },
            "api": {
                "name": "API Connector",
                "supported_systems": ["rest", "graphql", "soap"],
                "required_credentials": ["api_key", "endpoint_url"],
                "supported_metrics": [
                    "custom_api_results"
                ]
            },
            "file": {
                "name": "File Connector",
                "supported_systems": ["csv", "excel", "json"],
                "required_credentials": ["file_path"],
                "supported_metrics": [
                    "file_data"
                ]
            }
        }
    
    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Perform data integration-specific validations.
        
        Args:
            inputs: Dictionary of input values to validate
            
        Returns:
            List[str]: List of error messages (empty if all validations pass)
        """
        errors = []
        
        # Validate connection type
        connection_type = inputs.get('connection_type', '')
        if connection_type not in self._connectors:
            errors.append(f"Unsupported connection type: {connection_type}. " +
                         f"Supported types are: {', '.join(self._connectors.keys())}")
            return errors  # Early return if connection type is invalid
        
        # Validate source system if provided
        source_system = inputs.get('source_system')
        if source_system:
            supported_systems = self._connectors[connection_type].get('supported_systems', [])
            if source_system.lower() not in [s.lower() for s in supported_systems]:
                errors.append(f"Unsupported source system '{source_system}' for connection type '{connection_type}'. " +
                             f"Supported systems are: {', '.join(supported_systems)}")
        
        # Validate metrics to retrieve
        metrics_to_retrieve = inputs.get('metrics_to_retrieve', [])
        supported_metrics = self._connectors[connection_type].get('supported_metrics', [])
        
        # For database and API, we allow custom queries/endpoints
        if connection_type not in ['database', 'api', 'file']:
            for metric in metrics_to_retrieve:
                if metric not in supported_metrics:
                    errors.append(f"Unsupported metric '{metric}' for connection type '{connection_type}'. " +
                                f"Supported metrics are: {', '.join(supported_metrics)}")
        
        # Validate credentials if provided
        connection_credentials = inputs.get('connection_credentials', {})
        if connection_credentials:
            required_credentials = self._connectors[connection_type].get('required_credentials', [])
            for cred in required_credentials:
                if cred not in connection_credentials:
                    errors.append(f"Missing required credential '{cred}' for connection type '{connection_type}'")
            
            # Security validation - ensure credentials are not plaintext if require_encryption is True
            if self.require_encryption:
                for cred_name, cred_value in connection_credentials.items():
                    if cred_name in ['password', 'api_key', 'token', 'secret'] and isinstance(cred_value, str):
                        if not cred_value.startswith('enc:'):
                            errors.append(f"Credential '{cred_name}' must be encrypted")
        
        return errors
    
    async def _validate_connection(self, connection_type: str, source_system: str, 
                                  credentials: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate connection to the external data source.
        
        Args:
            connection_type: Type of connection (crm, erp, etc.)
            source_system: Specific system to connect to
            credentials: Connection credentials
            
        Returns:
            Tuple containing (success: bool, message: str)
        """
        # In a real implementation, this would attempt to establish a connection
        # For this example, we'll simulate a connection attempt
        logger.info(f"Validating connection to {source_system} ({connection_type})")
        
        # Simulate connection validation
        await asyncio.sleep(1)  # Simulate network delay
        
        # Check for required credentials
        required_credentials = self._connectors[connection_type].get('required_credentials', [])
        for cred in required_credentials:
            if cred not in credentials:
                return False, f"Missing required credential: {cred}"
        
        # In a real implementation, we would attempt to connect to the external system
        # and validate the credentials
        
        return True, "Connection validated successfully"
    
    async def _retrieve_metrics(self, connection_type: str, source_system: str, 
                               credentials: Dict[str, Any], metrics: List[str],
                               query_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve metrics from the external data source.
        
        Args:
            connection_type: Type of connection (crm, erp, etc.)
            source_system: Specific system to connect to
            credentials: Connection credentials
            metrics: List of metrics to retrieve
            query_parameters: Additional parameters for the query
            
        Returns:
            Dictionary containing retrieved metrics
        """
        # In a real implementation, this would connect to the external system and retrieve data
        # For this example, we'll simulate data retrieval with realistic sample data
        logger.info(f"Retrieving metrics from {source_system} ({connection_type}): {metrics}")
        
        # Simulate data retrieval
        await asyncio.sleep(2)  # Simulate network delay
        
        # Generate sample data based on the requested metrics
        result = {}
        
        if connection_type == "crm":
            if "customer_acquisition_cost" in metrics:
                result["customer_acquisition_cost"] = 250.75
            if "customer_lifetime_value" in metrics:
                result["customer_lifetime_value"] = 3200.50
            if "sales_cycle_length" in metrics:
                result["sales_cycle_length"] = 45.2  # days
            if "conversion_rate" in metrics:
                result["conversion_rate"] = 0.12  # 12%
            if "lead_volume" in metrics:
                result["lead_volume"] = 520  # monthly
        
        elif connection_type == "erp":
            if "operational_cost" in metrics:
                result["operational_cost"] = 1250000.00
            if "inventory_turnover" in metrics:
                result["inventory_turnover"] = 8.5  # times per year
            if "procurement_cost" in metrics:
                result["procurement_cost"] = 450000.00
            if "production_efficiency" in metrics:
                result["production_efficiency"] = 0.82  # 82%
            if "resource_utilization" in metrics:
                result["resource_utilization"] = 0.75  # 75%
        
        # Add metadata about the data source
        result["_metadata"] = {
            "source": source_system,
            "timestamp": time.time(),
            "query_parameters": query_parameters,
            "data_sensitivity": self.data_sensitivity
        }
        
        return result
    
    async def _securely_store_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Securely store connection credentials in the MCP.
        
        In a real implementation, this would store credentials in a secure vault
        and return a reference token.
        
        Args:
            credentials: Connection credentials to store
            
        Returns:
            String token referencing the stored credentials
        """
        # In a real implementation, this would use the MCP client to securely store credentials
        # For this example, we'll simulate secure storage
        logger.info("Securely storing connection credentials")
        
        # Simulate secure storage
        await asyncio.sleep(0.5)
        
        # Generate a simulated token
        token = f"cred_token_{int(time.time())}"
        
        return token
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute the data integration logic after validation.
        
        Args:
            inputs: Dictionary of validated input values
            
        Returns:
            AgentResult: Result of the agent execution with retrieved metrics
        """
        start_time = time.monotonic()
        
        # Use centralized validation
        validation_result = await self.validate_inputs(inputs)
        if not validation_result.is_valid:
            return AgentResult(
                status=AgentStatus.FAILED, 
                data={"error": validation_result.errors}, 
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
        
        # Extract validated inputs
        connection_type = inputs['connection_type']
        metrics_to_retrieve = inputs['metrics_to_retrieve']
        source_system = inputs.get('source_system', '')
        connection_credentials = inputs.get('connection_credentials', {})
        query_parameters = inputs.get('query_parameters', {})
        
        # Validate connection
        connection_valid, connection_message = await self._validate_connection(
            connection_type, source_system, connection_credentials
        )
        
        if not connection_valid:
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Connection validation failed: {connection_message}"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
        
        # If credentials are provided, securely store them
        credentials_token = None
        if connection_credentials:
            credentials_token = await self._securely_store_credentials(connection_credentials)
        
        # Retrieve metrics from the data source
        try:
            metrics_data = await self._retrieve_metrics(
                connection_type, source_system, connection_credentials,
                metrics_to_retrieve, query_parameters
            )
        except Exception as e:
            logger.error(f"Error retrieving metrics: {str(e)}")
            return AgentResult(
                status=AgentStatus.FAILED,
                data={"error": f"Failed to retrieve metrics: {str(e)}"},
                execution_time_ms=int((time.monotonic() - start_time) * 1000)
            )
        
        # Prepare result data
        result_data = {
            "metrics": metrics_data,
            "connection_status": "connected",
            "connection_type": connection_type,
            "source_system": source_system,
            "retrieved_metrics_count": len(metrics_data) - 1,  # Exclude _metadata
            "credentials_token": credentials_token
        }
        
        # Log success (excluding sensitive data)
        logger.info(f"Successfully retrieved {len(metrics_data) - 1} metrics from {source_system}")
        
        # Return successful result
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data=result_data,
            execution_time_ms=int((time.monotonic() - start_time) * 1000)
        )
