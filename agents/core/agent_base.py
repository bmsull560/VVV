from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Type, Callable, TypeVar, cast
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import time
import logging
import re
from decimal import Decimal

# Import our real MCP client
from agents.core.mcp_client import MCPClient
try:
    from agents.core.llm_client import LLMClient # Import the new LLM client
except Exception as e:
    import traceback
    print(f"Error importing LLMClient: {e}")
    traceback.print_exc()
    raise

class CircuitBreakerOpen(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.open = False
    async def __aenter__(self):
        if self.open:
            raise CircuitBreakerOpen()
        return self
    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.open = True
        else:
            self.failures = 0
            self.open = False

class RetryPolicy:
    def __init__(self, max_attempts=3, backoff_factor=2):
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
    async def execute(self, func, *args, **kwargs):
        attempt = 0
        while attempt < self.max_attempts:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                if attempt == self.max_attempts:
                    raise e
                await asyncio.sleep(self.backoff_factor ** attempt)

@dataclass
class ValidationResult:
    """Result of input validation with detailed error information."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class AgentResult:
    status: AgentStatus
    data: Dict[str, Any]
    execution_time_ms: int
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    confidence_score: Optional[float] = None
    error_details: Optional[str] = None

class BaseAgent(ABC):
    def __init__(self, agent_id: str, mcp_client: MCPClient, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.mcp_client = mcp_client
        self.config = config
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.get('failure_threshold', 5),
            reset_timeout=config.get('reset_timeout', 60)
        )
        self.retry_policy = RetryPolicy(
            max_attempts=config.get('max_retries', 3),
            backoff_factor=config.get('backoff_factor', 2)
        )
    async def validate_inputs(self, inputs: Dict[str, Any]) -> ValidationResult:
        """
        Performs generic input validation based on the agent's configuration.
        Checks for required fields, correct types, and value constraints.
        """
        errors: List[str] = []
        validation_rules = self.config.get('input_validation', {})
        if not validation_rules:
            return ValidationResult(is_valid=True, errors=[])

        # 1. Check for required fields
        required_fields = validation_rules.get('required_fields', [])
        for field in required_fields:
            if field not in inputs:
                errors.append(f"'{field}' is a required property")

        # 2. Check field constraints (length, value, etc.)
        field_constraints = validation_rules.get('field_constraints', {})
        for field, constraints in field_constraints.items():
            if field in inputs and inputs[field] is not None:
                value = inputs[field]
                if 'min_length' in constraints and isinstance(value, (str, list, dict)):
                    if len(value) < constraints['min_length']:
                        errors.append(f"{field} must be at least {constraints['min_length']} characters")
                if 'max_length' in constraints and isinstance(value, (str, list, dict)):
                    if len(value) > constraints['max_length']:
                        errors.append(f"{field} cannot exceed {constraints['max_length']} characters")
                if 'min_value' in constraints and isinstance(value, (int, float)):
                    if value < constraints['min_value']:
                        errors.append(f"{field} must be at least {constraints['min_value']}")
                if 'max_value' in constraints and isinstance(value, (int, float)):
                    if value > constraints['max_value']:
                        errors.append(f"{field} cannot exceed {constraints['max_value']}")
                if 'allowed_values' in constraints:
                    if value not in constraints['allowed_values']:
                        errors.append(f"'{value}' is not a valid value for {field}")
        
        # 3. Check field types
        field_types = validation_rules.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in inputs and inputs[field] is not None:
                type_map = {
                    'string': str, 
                    'number': (int, float, Decimal), 
                    'array': list, 
                    'object': dict,
                    'boolean': bool
                }
                if expected_type in type_map:
                    if not isinstance(inputs[field], type_map[expected_type]):
                        errors.append(f"'{field}' must be of type {expected_type}, but got {type(inputs[field]).__name__}")

        return ValidationResult(is_valid=not errors, errors=errors)

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """The core logic of the agent.

        Args:
            inputs: A dictionary of inputs for the agent.

        Returns:
            An AgentResult object with the status and output data.
        """
        pass

    async def validate_inputs(self, inputs: Dict[str, Any]) -> ValidationResult:
        """Optional input validation. Override in subclasses if needed."""
        return ValidationResult(is_valid=True)

    async def execute_with_resilience(self, inputs: Dict[str, Any]) -> AgentResult:
        start_time = time.time()
        try:
            validation_result = await self.validate_inputs(inputs)
            if not validation_result.is_valid:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    data={},
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    error_details=f"Input validation failed: {validation_result.errors}"
                )
            
            async with self.circuit_breaker:
                result = await self.retry_policy.execute(
                    self._execute_with_context,
                    inputs
                )
                if result.status == AgentStatus.COMPLETED:
                    await self.update_context(result.data)
                return result
        except CircuitBreakerOpen:
            return AgentResult(
                status=AgentStatus.FAILED,
                data={},
                execution_time_ms=int((time.time() - start_time) * 1000),
                error_details="Circuit breaker open - service unavailable"
            )
        except Exception as e:
            return AgentResult(
                status=AgentStatus.FAILED,
                data={},
                execution_time_ms=int((time.time() - start_time) * 1000),
                error_details=str(e)
            )
    async def _execute_with_context(self, inputs: Dict[str, Any]) -> AgentResult:
        context = await self.get_context()
        execution_context = {
            **inputs,
            "workflow_context": context,
            "agent_id": self.agent_id,
            "execution_timestamp": time.time()
        }
        try:
            result = await asyncio.wait_for(
                self.execute(execution_context),
                timeout=self.config.get('timeout_seconds', 300)
            )
            return result
        except asyncio.TimeoutError:
            return AgentResult(
                status=AgentStatus.TIMEOUT,
                data={},
                execution_time_ms=self.config.get('timeout_seconds', 300) * 1000,
                error_details="Agent execution timeout"
            )
    async def get_context(self) -> Dict[str, Any]:
        return await self.mcp_client.get_context()
    async def update_context(self, data: Dict[str, Any]) -> None:
        await self.mcp_client.update_context(self.agent_id, data)
    async def validate_inputs(self, inputs: Dict[str, Any]) -> ValidationResult:
        """Centralized input validation for all agents.
        
        This method provides a common validation framework that all agent subclasses
        can use. It performs standard validations based on field requirements defined
        in the agent's config and can be extended by subclasses for specific validations.
        
        Args:
            inputs: Dictionary of input values to validate
            
        Returns:
            ValidationResult: Object containing validation status and any error messages
        """
        errors = []
        
        # Get validation rules from config if available
        validation_rules = self.config.get('input_validation', {})
        required_fields = validation_rules.get('required_fields', [])
        field_types = validation_rules.get('field_types', {})
        field_constraints = validation_rules.get('field_constraints', {})
        
        # Check required fields
        for field in required_fields:
            if field not in inputs or inputs[field] is None:
                errors.append(f"Required field '{field}' is missing or null")
        
        # Check field types
        for field, expected_type in field_types.items():
            if field in inputs and inputs[field] is not None:
                if not self._validate_field_type(inputs[field], expected_type):
                    errors.append(f"Field '{field}' must be of type {expected_type}")
        
        # Check field constraints
        for field, constraints in field_constraints.items():
            if field in inputs and inputs[field] is not None:
                field_errors = self._validate_field_constraints(field, inputs[field], constraints)
                errors.extend(field_errors)
        
        # Run agent-specific validations (to be implemented by subclasses)
        custom_errors = await self._custom_validations(inputs)
        errors.extend(custom_errors)
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
        
    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validate that a field value matches the expected type.
        
        Args:
            value: The value to check
            expected_type: String representation of expected type
            
        Returns:
            bool: True if value matches expected type, False otherwise
        """
        if expected_type == 'string':
            return isinstance(value, str)
        elif expected_type == 'number':
            return isinstance(value, (int, float, Decimal))
        elif expected_type == 'integer':
            return isinstance(value, int)
        elif expected_type == 'boolean':
            return isinstance(value, bool)
        elif expected_type == 'array':
            return isinstance(value, list)
        elif expected_type == 'object':
            return isinstance(value, dict)
        elif expected_type == 'email':
            if not isinstance(value, str):
                return False
            # Simple email validation regex
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(email_pattern, value))
        return True  # Default to True for unknown types
    
    def _validate_field_constraints(self, field: str, value: Any, constraints: Dict[str, Any]) -> List[str]:
        """Validate that a field value satisfies all constraints.
        
        Args:
            field: Name of the field being validated
            value: The value to check
            constraints: Dictionary of constraints to check against
            
        Returns:
            List[str]: List of error messages (empty if all constraints are satisfied)
        """
        errors = []
        
        # Numeric constraints
        if isinstance(value, (int, float, Decimal)):
            if 'min' in constraints and value < constraints['min']:
                errors.append(f"Field '{field}' must be at least {constraints['min']}")
            if 'max' in constraints and value > constraints['max']:
                errors.append(f"Field '{field}' must be at most {constraints['max']}")
        
        # String constraints
        if isinstance(value, str):
            if 'min_length' in constraints and len(value) < constraints['min_length']:
                errors.append(f"Field '{field}' must be at least {constraints['min_length']} characters long")
            if 'max_length' in constraints and len(value) > constraints['max_length']:
                errors.append(f"Field '{field}' must be at most {constraints['max_length']} characters long")
            if 'pattern' in constraints and not re.match(constraints['pattern'], value):
                errors.append(f"Field '{field}' does not match required pattern")
        
        # Array constraints
        if isinstance(value, list):
            if 'min_items' in constraints and len(value) < constraints['min_items']:
                errors.append(f"Field '{field}' must contain at least {constraints['min_items']} items")
            if 'max_items' in constraints and len(value) > constraints['max_items']:
                errors.append(f"Field '{field}' must contain at most {constraints['max_items']} items")
            
            # Validate items in array if item_type is specified
            if 'item_type' in constraints and value:
                for i, item in enumerate(value):
                    if not self._validate_field_type(item, constraints['item_type']):
                        errors.append(f"Item {i} in field '{field}' must be of type {constraints['item_type']}")
        
        # Enum constraints
        if 'enum' in constraints and value not in constraints['enum']:
            enum_values = ', '.join(map(str, constraints['enum']))
            errors.append(f"Field '{field}' must be one of: {enum_values}")
        
        return errors
    
    async def _custom_validations(self, inputs: Dict[str, Any]) -> List[str]:
        """Perform agent-specific custom validations.
        
        This method should be overridden by subclasses to implement
        validations specific to that agent type.
        
        Args:
            inputs: Dictionary of input values to validate
            
        Returns:
            List[str]: List of error messages (empty if all validations pass)
        """
        return []  # No custom validations in base class

# Simple LRU cache for demonstration
class LRUCache(dict):
    def __init__(self, maxsize=100):
        super().__init__()
        self.maxsize = maxsize
        self._order = []
    def __getitem__(self, key):
        value = super().__getitem__(key)
        self._order.remove(key)
        self._order.append(key)
        return value
    def __setitem__(self, key, value):
        if key in self:
            self._order.remove(key)
        elif len(self._order) >= self.maxsize:
            oldest = self._order.pop(0)
            del self[oldest]
        super().__setitem__(key, value)
        self._order.append(key)
    def get(self, key, default=None):
        if key in self:
            return self[key]
        return default

# LLMAgent: for LLM-powered agents
class LLMAgent(BaseAgent):
    def __init__(self, agent_id: str, mcp_client: MCPClient, config: Dict[str, Any]):
        super().__init__(agent_id, mcp_client, config)
        self.llm_client = LLMClient(config=config.get('llm_config', {'provider': 'openai', 'model': 'gpt-4o'})) # Initialize LLM client
        self.prompt_cache = LRUCache(maxsize=config.get('prompt_cache_size', 100))
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        start_time = time.time()
        try:
            prompt = await self._build_prompt(inputs)
            cache_key = self._generate_cache_key(prompt)
            cached_result = self.prompt_cache.get(cache_key)
            if cached_result and self.config.get('enable_cache', True):
                return AgentResult(
                    status=AgentStatus.COMPLETED,
                    data=cached_result,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    tokens_used=cached_result.get('tokens_used', 0),
                    cost_usd=cached_result.get('cost_usd', 0.0)
                )
            llm_response = await self.llm_client.generate_text(prompt, temperature=self.config.get('temperature', 0.7))
            response = {"output": llm_response["text"], "confidence": 0.9} # Placeholder confidence, can be improved
            tokens_used = llm_response["tokens_used"]
            cost_usd = llm_response["cost_usd"]
            parsed_output = await self._parse_and_validate_response(response)
            if parsed_output.get('confidence', 0.0) > 0.8:
                self.prompt_cache[cache_key] = parsed_output
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=parsed_output,
                execution_time_ms=int((time.time() - start_time) * 1000),
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                confidence_score=parsed_output.get('confidence', 0.0)
            )
        except Exception as e:
            return AgentResult(
                status=AgentStatus.FAILED,
                data={},
                execution_time_ms=int((time.time() - start_time) * 1000),
                error_details=str(e)
            )
    async def _build_prompt(self, inputs: Dict[str, Any]) -> str:
        return f"Prompt with context: {inputs}"
    def _generate_cache_key(self, prompt: str) -> str:
        return str(hash(prompt))
    async def _parse_and_validate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder parsing/validation
        return response

# CalculationAgent: for rule-based/calculative agents
class CalculationAgent(BaseAgent):
    def __init__(self, agent_id: str, mcp_client: MCPClient, config: Dict[str, Any]):
        super().__init__(agent_id, mcp_client, config)
        self.rules_engine = config.get('rules_engine')  # Placeholder
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        start_time = time.time()
        try:
            context = inputs.get('workflow_context', {})
            baseline_metrics = context.get('baseline_metrics', {})
            enriched_data = context.get('enriched_data', {})
            # Placeholder for calculation logic
            calculation_result = {"result": 42, "confidence": 0.95}
            return AgentResult(
                status=AgentStatus.COMPLETED,
                data=calculation_result,
                execution_time_ms=int((time.time() - start_time) * 1000),
                confidence_score=calculation_result.get('confidence', 0.0)
            )
        except Exception as e:
            return AgentResult(
                status=AgentStatus.FAILED,
                data={},
                execution_time_ms=int((time.time() - start_time) * 1000),
                error_details=str(e)
            )
