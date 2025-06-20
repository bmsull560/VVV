"""
Example agent demonstrating the centralized input validation mechanism.

This module provides a simple example of how to use the BaseAgent's
centralized input validation features.
"""

import logging
from typing import Dict, Any, List
import time
from decimal import Decimal

from agents.core.agent_base import BaseAgent, AgentResult, AgentStatus

logger = logging.getLogger(__name__)

class ValidationExampleAgent(BaseAgent):
    """Example agent demonstrating centralized input validation."""

    def __init__(self, agent_id: str, mcp_client: Any, config: Dict[str, Any]):
        """
        Initialize the example agent with validation rules.
        
        Args:
            agent_id: Unique identifier for this agent
            mcp_client: MCP client instance for memory access
            config: Configuration dictionary
        """
        # Define validation rules in config
        if 'input_validation' not in config:
            config['input_validation'] = {
                # Fields that must be present
                'required_fields': ['customer_id', 'product_data'],
                
                # Type checking for fields
                'field_types': {
                    'customer_id': 'string',
                    'product_data': 'object',
                    'email': 'email',
                    'age': 'number',
                    'products': 'array'
                },
                
                # Constraints for fields
                'field_constraints': {
                    'customer_id': {
                        'pattern': r'^CUST-\d{6}$'  # Must match pattern CUST-123456
                    },
                    'age': {
                        'min': 18,
                        'max': 120
                    },
                    'products': {
                        'min_items': 1,
                        'item_type': 'object'
                    }
                }
            }
        
        super().__init__(agent_id, mcp_client, config)
    
    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """
        Perform agent-specific custom validations.
        
        Args:
            inputs: Dictionary of input values to validate
            
        Returns:
            List[str]: List of error messages (empty if all validations pass)
        """
        errors = []
        
        # Example of a complex business rule validation
        product_data = inputs.get('product_data', {})
        
        # Check that product_data has required structure
        if not product_data.get('category'):
            errors.append("Product data must include a category")
        
        if 'price' in product_data:
            price = product_data['price']
            # Convert string price to decimal if needed
            if isinstance(price, str):
                try:
                    price = Decimal(price)
                    product_data['price'] = price  # Update with converted value
                except (ValueError, TypeError):
                    errors.append("Product price must be a valid number")
            
            # Business rule: premium products must have a minimum price
            if product_data.get('category') == 'premium' and isinstance(price, (int, float, Decimal)) and price < 100:
                errors.append("Premium products must have a price of at least 100")
        
        return errors
    
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent's main functionality after validation.
        
        Args:
            inputs: Dictionary of validated input values
            
        Returns:
            AgentResult: Result of the agent execution
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
        
        # If validation passes, proceed with agent logic
        customer_id = inputs['customer_id']
        product_data = inputs['product_data']
        
        # Example agent logic
        result_data = {
            "customer_id": customer_id,
            "product_category": product_data.get('category'),
            "validation_status": "passed",
            "processing_result": "success"
        }
        
        logger.info(f"Successfully processed data for customer {customer_id}")
        
        return AgentResult(
            status=AgentStatus.COMPLETED,
            data=result_data,
            execution_time_ms=int((time.monotonic() - start_time) * 1000)
        )
